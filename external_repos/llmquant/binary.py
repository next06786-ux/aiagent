from numpy import mean
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
index = 0
_ITER2BIT_CALL_ID = 0
@torch.no_grad()
def part_mean(tensor, op='-'):
    non_zero = tensor*(tensor!=0)

    mean_val = non_zero.mean(-1).view(-1, 1)

    return mean_val

@torch.no_grad()
def high_order_residual(x, mask, order=2):
    sum_order = torch.zeros_like(x)
    new_matrix = x.clone()
    new_matrix = new_matrix * mask
    global index
    index += 1
    for od in range(order):
        residual = new_matrix - sum_order
        masked_x_tensor = torch.where(mask, residual, torch.tensor(float('nan')))

        mean_tensor_all = torch.nanmean(masked_x_tensor, dim=1)
        mean_tensor_all = torch.where(torch.isnan(mean_tensor_all), torch.zeros_like(mean_tensor_all), mean_tensor_all)
        masked_x_tensor -= mean_tensor_all[:, None]
        scale_tensor_all = torch.nanmean(torch.abs(masked_x_tensor), dim=1)
        scale_tensor_all = torch.where(torch.isnan(scale_tensor_all), torch.zeros_like(scale_tensor_all), scale_tensor_all)

        binary= torch.sign(masked_x_tensor)
        binary *= scale_tensor_all[:, None]
        binary += mean_tensor_all[:, None]
        binary = torch.nan_to_num(binary, nan=0.0)
        sum_order = sum_order + binary*mask
    
    return sum_order

@torch.no_grad()
def normal_quantize(x, scale, zero, maxq):
    q = torch.clamp(torch.round(x / scale) + zero, 0, maxq)
    return scale * (q - zero)


@torch.no_grad()
def iterative_affine_quantize_perchannel(
    tensor,
    bits=2,
    mask=None,
    n_iter=5,
    eps=1e-8,
    update_offset=True,
    fixed_iters=False,
    print_mse=False,
    return_info=False,
):
    """
    Per-channel affine quantization with alternating optimization on masked elements.
    Quantized values are written back only where mask=True.
    """
    if tensor.ndim < 2:
        raise ValueError("iterative_affine_quantize_perchannel expects tensor.ndim >= 2")

    dev = tensor.device
    dtype = tensor.dtype
    x = tensor.float().flatten(1)  # [channels, n]

    if mask is None:
        mask_2d = torch.ones_like(x, dtype=torch.bool, device=dev)
    else:
        mask_2d = mask.reshape_as(tensor).flatten(1).to(device=dev, dtype=torch.bool)

    mask_f = mask_2d.float()
    valid_count = mask_f.sum(dim=1)  # [channels]
    has_valid = valid_count > 0

    pos_inf = torch.full_like(x, float("inf"))
    neg_inf = torch.full_like(x, float("-inf"))
    xmin = torch.where(mask_2d, x, pos_inf).amin(dim=1)
    xmax = torch.where(mask_2d, x, neg_inf).amax(dim=1)

    # Fallback for rows without valid elements.
    xmin = torch.where(has_valid, xmin, torch.full_like(xmin, -1.0))
    xmax = torch.where(has_valid, xmax, torch.full_like(xmax, 1.0))

    zero_ref = torch.zeros_like(xmin)
    xmin = torch.minimum(xmin, zero_ref)
    xmax = torch.maximum(xmax, zero_ref)

    maxq = float(2**bits - 1)
    scale = (xmax - xmin) / maxq
    scale = torch.clamp(scale, min=eps)
    zero_point = torch.round(-xmin / scale).clamp(0, maxq)
    offset = -scale * zero_point  # x_hat = scale * q + offset

    call_id = None
    if print_mse:
        global _ITER2BIT_CALL_ID
        _ITER2BIT_CALL_ID += 1
        call_id = _ITER2BIT_CALL_ID

    def _masked_mse(cur_scale, cur_offset):
        q_eval = torch.round((x - cur_offset[:, None]) / cur_scale[:, None]).clamp(0, maxq)
        q_eval = torch.where(mask_2d, q_eval, torch.zeros_like(q_eval))
        recon = cur_scale[:, None] * q_eval + cur_offset[:, None]
        sqerr = ((x - recon) ** 2) * mask_f
        return (sqerr.sum() / valid_count.sum().clamp(min=1.0)).item()

    tau = 1e-5
    fixed_iters = bool(fixed_iters)
    min_iters = max(int(n_iter), 1) if fixed_iters else max(int(n_iter), 5)
    log_every = 50
    prev_mse = _masked_mse(scale, offset)
    best_mse = prev_mse
    best_scale = scale.clone()
    best_offset = offset.clone()

    if print_mse:
        print(
            f"[iter2bit][call={call_id}] init_mse={prev_mse:.8e}, "
            f"iters={min_iters}, fixed={str(fixed_iters).lower()}, tau={tau:.1e}, log_every={log_every}, "
            f"active={int(valid_count.sum().item())}"
        )

    it = 0
    cur_mse = prev_mse
    stop_reason = ""
    while True:
        it += 1
        q = torch.round((x - offset[:, None]) / scale[:, None]).clamp(0, maxq)
        q = torch.where(mask_2d, q, torch.zeros_like(q))

        denom = (q * q).sum(dim=1)
        numer = ((x - offset[:, None]) * q).sum(dim=1)
        can_update_scale = denom > eps

        new_scale = torch.where(can_update_scale, numer / (denom + eps), scale)
        new_scale = torch.clamp(new_scale.abs(), min=eps)

        if update_offset:
            recon = new_scale[:, None] * q
            new_offset = ((x - recon) * mask_f).sum(dim=1) / valid_count.clamp(min=1.0)
        else:
            new_offset = offset

        scale = torch.where(has_valid, new_scale, scale)
        offset = torch.where(has_valid, new_offset, offset)

        cur_mse = _masked_mse(scale, offset)
        if cur_mse < best_mse:
            best_mse = cur_mse
            best_scale = scale.clone()
            best_offset = offset.clone()

        stop = False
        if fixed_iters:
            if it >= min_iters:
                stop = True
                stop_reason = "fixed_iters_reached"
        else:
            if it >= min_iters:
                # Stop when objective gets worse or improves by less than tau ratio.
                if cur_mse >= prev_mse * (1.0 - tau):
                    stop = True
                    stop_reason = "no_significant_improvement_or_worse"

        if print_mse and ((it % log_every == 0) or stop):
            improve = prev_mse - cur_mse
            print(
                f"[iter2bit][call={call_id}] iter={it} mse={cur_mse:.8e} "
                f"improve={improve:.8e}"
            )

        if stop:
            scale = best_scale
            offset = best_offset
            if print_mse:
                print(
                    f"[iter2bit][call={call_id}] final iter={it} "
                    f"stop={stop_reason} best_mse={best_mse:.8e} last_mse={cur_mse:.8e}"
                )
            break

        prev_mse = cur_mse

    q = torch.round((x - offset[:, None]) / scale[:, None]).clamp(0, maxq)
    q = torch.where(mask_2d, q, torch.zeros_like(q))
    x_hat = scale[:, None] * q + offset[:, None]
    out = torch.where(mask_2d, x_hat, x)
    out = out.reshape_as(tensor).to(dtype)
    if return_info:
        # Export final affine qparams so caller can consistently reuse the same codebook.
        zp = (-offset / scale).to(dtype=torch.float32)
        info = {
            "iters": int(it),
            "best_mse": float(best_mse),
            "last_mse": float(cur_mse),
            "stop_reason": str(stop_reason or "unknown"),
            "scale": scale.to(dtype=torch.float32).clone(),
            "offset": offset.to(dtype=torch.float32).clone(),
            "zero_point": zp.clone(),
            "maxq": float(maxq),
        }
        return out, info
    return out


class Binarization(nn.Module):
    def __init__(
        self,
        weight,
        method="2bit",
        groupsize=-1,
        iterative_2bit_enable=True,
        iterative_2bit_iters=5,
        iterative_2bit_eps=1e-8,
        iterative_2bit_update_offset=True,
        iterative_2bit_fixed_iters=False,
        iterative_2bit_print_mse=False,
    ):
        super().__init__()
        oc,ic=weight.shape
        if groupsize==-1:
            groupsize=ic
        self.groupsize=groupsize
        self.n_groups=math.ceil(ic/groupsize)
        self.method=method
        self.mean = 0
        self.iterative_2bit_enable = bool(iterative_2bit_enable)
        self.iterative_2bit_iters = int(iterative_2bit_iters)
        self.iterative_2bit_eps = float(iterative_2bit_eps)
        self.iterative_2bit_update_offset = bool(iterative_2bit_update_offset)
        self.iterative_2bit_fixed_iters = bool(iterative_2bit_fixed_iters)
        self.iterative_2bit_print_mse = bool(iterative_2bit_print_mse)

    def quantize(self, w, mask, order=2, groupi=0):
        if self.method=="xnor":
            w_mean = self.mean[groupi]
            w = w - w_mean  # oc, ic
            w = w.sign()
            w = w * self.scale[groupi]
            w+=w_mean
        elif self.method=="braq": # The method used in paper
            w = high_order_residual(w, mask, order=order)  
        elif self.method=="sign":
            w=(w>0).float()
            w*=self.scale[groupi]
        elif self.method=="rtn":
            w=F.relu(w)
            w_int=(w/self.scale[groupi]).round().clamp(0,1)
            w=w_int*self.scale[groupi]



        elif self.method == 'block_2bit':
            w =  quantize_to_2bit_perchannel(w)
        elif self.method in ['2bit','3bit','4bit']:
            if self.method in ['2bit', '3bit', '4bit'] and self.iterative_2bit_enable:
                bits_iter = int(self.method[0])
                return iterative_affine_quantize_perchannel(
                    w,
                    bits=bits_iter,
                    mask=mask,
                    n_iter=self.iterative_2bit_iters,
                    eps=self.iterative_2bit_eps,
                    update_offset=self.iterative_2bit_update_offset,
                    fixed_iters=self.iterative_2bit_fixed_iters,
                    print_mse=self.iterative_2bit_print_mse,
                )

            bits = int(self.method[0])
            perchannel = True
            weight = True
            dev = w.device
            maxq = torch.tensor(2 ** bits - 1)
            scale = torch.zeros(1)
            zero = torch.zeros(1)

            if dev != scale.device:
                scale=scale.to(dev)
                zero=zero.to(dev)
                maxq=maxq.to(dev)

            x = w.clone()
            shape = x.shape

            if perchannel:
                if weight:
                    x = x.flatten(1)
                else:
                    if len(shape) == 4:
                        x = x.permute([1, 0, 2, 3])
                        x = x.flatten(1)
                    if len(shape) == 3:
                        x = x.reshape((-1, shape[-1])).t()
                    if len(shape) == 2:
                        x = x.t()
            else:
                x = x.flatten().unsqueeze(0)
            tmp = torch.zeros(x.shape[0], device=dev)
            xmin = torch.minimum(x.min(1)[0], tmp)
            xmax = torch.maximum(x.max(1)[0], tmp)

            tmp = (xmin == 0) & (xmax == 0)
            xmin[tmp] = -1
            xmax[tmp] = +1
            scale = (xmax - xmin) / maxq
            zero = torch.round(-xmin / scale)
            if not perchannel:
                if weight:
                    tmp = shape[0]
                else:
                    tmp = shape[1] if len(shape) != 3 else shape[2]
                scale = scale.repeat(tmp)
                zero = zero.repeat(tmp)

            if weight:
                shape = [-1] + [1] * (len(shape) - 1)
                scale = scale.reshape(shape)
                zero = zero.reshape(shape)
            w = normal_quantize(w, scale, zero, maxq)

        elif self.method=="prune":
            return torch.zeros_like(w)
        return w


@torch.no_grad()
def quantize_to_4bit_perchannel(tensor):

    bits = 4
    dev = tensor.device
    maxq = torch.tensor(2 ** bits - 1).to(dev)
    
    # Process input
    x = tensor.clone()
    shape = x.shape
    x = x.flatten(1)  # [..., features] -> [..., features]
    
    # Calculate per-channel min/max
    tmp = torch.zeros(x.shape[0], device=dev)
    xmin = torch.minimum(x.min(1)[0], tmp)
    xmax = torch.maximum(x.max(1)[0], tmp)
    
    # Handle all-zero case
    tmp = (xmin == 0) & (xmax == 0)
    xmin[tmp] = -1
    xmax[tmp] = +1
    
    # Calculate scale and zero
    scale = (xmax - xmin) / maxq
    scale = torch.clamp(scale, min=1e-8)  # Prevent division by zero
    zero = torch.round(-xmin / scale)
    zero = torch.clamp(zero, 0, maxq)  # Limit range
    
    # Reshape scale and zero to match original shape
    scale = scale.view(-1, 1)  # [..., 1]
    zero = zero.view(-1, 1)    # [..., 1]
    
    # Quantize (fake quantization, return FP16)
    quantized = normal_quantize(tensor, scale, zero, maxq)
    quantized = quantized.half()  # Convert to FP16
    
    return quantized, scale, zero

@torch.no_grad()
def quantize_to_8bit_perchannel(tensor):

    bits = 8
    dev = tensor.device
    maxq = torch.tensor(2 ** bits - 1).to(dev)

    # Process input
    x = tensor.clone()
    x = x.flatten(1)

    # Calculate per-channel min/max
    tmp = torch.zeros(x.shape[0], device=dev)
    xmin = torch.minimum(x.min(1)[0], tmp)
    xmax = torch.maximum(x.max(1)[0], tmp)

    # Handle all-zero case
    tmp = (xmin == 0) & (xmax == 0)
    xmin[tmp] = -1
    xmax[tmp] = +1

    # Calculate scale and zero
    scale = (xmax - xmin) / maxq
    scale = torch.clamp(scale, min=1e-8)
    zero = torch.round(-xmin / scale)
    zero = torch.clamp(zero, 0, maxq)

    # Reshape scale and zero to match original shape
    scale = scale.view(-1, 1)
    zero = zero.view(-1, 1)

    # Fake quantization and cast to FP16
    quantized = normal_quantize(tensor, scale, zero, maxq)
    quantized = quantized.half()

    return quantized, scale, zero

@torch.no_grad()
def quantize_to_2bit_perchannel(tensor):

    bits = 2
    dev = tensor.device
    maxq = torch.tensor(2 ** bits - 1).to(dev)
    
    # Process input
    x = tensor.clone()
    shape = x.shape
    x = x.flatten(1)  # [..., features] -> [..., features]
    
    # Calculate per-channel min/max
    tmp = torch.zeros(x.shape[0], device=dev)
    xmin = torch.minimum(x.min(1)[0], tmp)
    xmax = torch.maximum(x.max(1)[0], tmp)
    
    # Handle all-zero case
    tmp = (xmin == 0) & (xmax == 0)
    xmin[tmp] = -1
    xmax[tmp] = +1
    
    # Calculate scale and zero
    scale = (xmax - xmin) / maxq
    scale = torch.clamp(scale, min=1e-8)  # Prevent division by zero
    zero = torch.round(-xmin / scale)
    zero = torch.clamp(zero, 0, maxq)  # Limit range
    
    # Reshape scale and zero to match original shape
    scale = scale.view(-1, 1)  # [..., 1]
    zero = zero.view(-1, 1)    # [..., 1]
    
    # Quantize (fake quantization, return FP16)
    quantized = normal_quantize(tensor, scale, zero, maxq)
    quantized = quantized.half()  # Convert to FP16
    
    return quantized


@torch.no_grad()
def quantize_to_3bit_perchannel(tensor):

    bits = 3
    dev = tensor.device
    maxq = torch.tensor(2 ** bits - 1).to(dev)
    
    # Process input
    x = tensor.clone()
    shape = x.shape
    x = x.flatten(1)  # [..., features] -> [..., features]
    
    # Calculate per-channel min/max
    tmp = torch.zeros(x.shape[0], device=dev)
    xmin = torch.minimum(x.min(1)[0], tmp)
    xmax = torch.maximum(x.max(1)[0], tmp)
    
    # Handle all-zero case
    tmp = (xmin == 0) & (xmax == 0)
    xmin[tmp] = -1
    xmax[tmp] = +1
    
    # Calculate scale and zero
    scale = (xmax - xmin) / maxq
    scale = torch.clamp(scale, min=1e-8)  # Prevent division by zero
    zero = torch.round(-xmin / scale)
    zero = torch.clamp(zero, 0, maxq)  # Limit range
    
    # Reshape scale and zero to match original shape
    scale = scale.view(-1, 1)  # [..., 1]
    zero = zero.view(-1, 1)    # [..., 1]
    
    # Quantize (fake quantization, return FP16)
    quantized = normal_quantize(tensor, scale, zero, maxq)
    quantized = quantized.half()  # Convert to FP16
    
    return quantized, scale, zero
