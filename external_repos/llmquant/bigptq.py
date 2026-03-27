import math
import time
import torch
import torch.nn as nn
import transformers
from utils.structure import structural_guassian_distribution
from binary import (
    quantize_to_2bit_perchannel,
    quantize_to_3bit_perchannel,
    quantize_to_4bit_perchannel,
    quantize_to_8bit_perchannel,
    iterative_affine_quantize_perchannel,
    high_order_residual,
)
from loguru import logger
import torch.nn.functional as F

DEBUG = False

torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False


def _std_gptq_quantize(x, scale, zero, maxq):
    # Use affine form compatible with iterative_affine_quantize_perchannel:
    # q_int = round(x / scale + zero), x_hat = scale * (q_int - zero).
    q = torch.clamp(torch.round(x / scale + zero), 0, maxq)
    return scale * (q - zero)


def _std_gptq_find_params_weight_perchannel(w, bits, sym=False):
    # w: [out_features, in_features]
    dev = w.device
    maxq = torch.tensor(2 ** int(bits) - 1, device=dev, dtype=w.dtype)

    x = w.float().flatten(1)
    tmp = torch.zeros(x.shape[0], device=dev, dtype=x.dtype)
    xmin = torch.minimum(x.min(1)[0], tmp)
    xmax = torch.maximum(x.max(1)[0], tmp)

    if bool(sym):
        xmax = torch.maximum(torch.abs(xmin), xmax)
        neg = xmin < 0
        if torch.any(neg):
            xmin[neg] = -xmax[neg]

    zero_span = (xmin == 0) & (xmax == 0)
    xmin[zero_span] = -1
    xmax[zero_span] = +1

    scale = (xmax - xmin) / maxq
    scale = torch.clamp(scale, min=1e-8)
    if bool(sym):
        zero = torch.full_like(scale, (maxq + 1) / 2)
    else:
        zero = torch.round(-xmin / scale)

    return scale.view(-1, 1), zero.view(-1, 1), maxq

'''
BRAGPTQ is the meaning of GPTQ used Binary Residual Approximation in paper to realize 1-bit quantization
BRAGPTQ uses structural mask to distinguish outliers and other data, and takes advantage of part of GPTQ to lower error
'''




class BRAGPTQ:
    def __init__(
        self, layer, braq_quantizer,salient_metric, disable_gptq=False,
        bass_proxy_metric="linf", linf_sigma_weight=1.0, linf_vh_weight=1.0
    ):
        self.layer = layer
        self.dev = self.layer.weight.device
        W = layer.weight.data.clone()
        if isinstance(self.layer, nn.Conv2d):
            W = W.flatten(1)
        if isinstance(self.layer, transformers.Conv1D):
            W = W.t()
        self.rows = W.shape[0]
        self.columns = W.shape[1]
        self.H = torch.zeros((self.columns, self.columns), device=self.dev)
        self.nsamples = 0
        # Mean activation statistics for lightweight post-GPTQ refill scoring.
        self.act_sum = torch.zeros(self.columns, device=self.dev)
        self.act_count = 0.0
        # ⭐ 添加激活统计（用于Wanda分数）
        self.act_square_sum = torch.zeros(self.columns, device=self.dev)  # [hidden_dim]
        # ⭐ 添加正向 SmoothQuant 的激活数据收集
        self.smooth_activations = []  # 存储原始激活数据用于正向 SmoothQuant
        # ⭐ 添加自适应 rank 的探针模式支持
        self.profiling_mode = False  # 是否为探针模式（只收集激活范数，不收集完整激活）
        self.activation_norms = []  # 存储激活的 L2 范数（用于敏感度计算）
        self.probe_error = None  # 存储快速量化误差（用于敏感度计算）
        self.braq_quantizer = braq_quantizer
        self.salient_metric = salient_metric  # "magnitude", "hessian", or "wanda"
        self.disable_gptq = disable_gptq

    def _compute_probe_error(self, W):
        scale = W.abs().mean(dim=1, keepdim=True)  # [out_features, 1]
        W_quantized = scale * W.sign()  # [out_features, in_features]
        R_probe = W - W_quantized  # [out_features, in_features]
        return torch.norm(R_probe, p='fro').item()

    def _apply_nm_pruning_to_tensor(self, target_tensor, act_norm=None, n=4, m=8):
        # 确保 target_tensor 是二维的 (out_features, in_features)
        metric = target_tensor.abs()
        
        if act_norm is not None:
            metric = metric * act_norm.view(1, -1)
            
        mask = torch.zeros_like(metric, dtype=torch.bool)
        
        # 修复 1：明确遍历第二个维度（列维度）
        for ii in range(0, metric.shape[1], m):
            col_end = min(ii + m, metric.shape[1])
            # 修复 2：正确切片获取当前大小为 m 的块
            group_metric = metric[:, ii:col_end]
            
            # 找到该组中最小的 n 个元素（注意：这里 n 代表你要裁剪的数量）
            # 如果常规的 N:M (如 2:4) 指的是“保留 N 个”，这里 n 应传入 m-保留数。
            _, indices = torch.topk(group_metric, n, dim=1, largest=False)
            
            # 在 mask 对应的位置打上 True 标记
            mask.scatter_(1, ii + indices, True)
            
        pruned_tensor = target_tensor.clone()
        
        # 修复 3：仅将 mask 为 True 的位置置 0
        pruned_tensor[mask] = 0
        
        sparsity = mask.float().mean().item()
        logger.info(f" Applied {n}:{m} pruning, sparsity: {sparsity:.4f}")
        
        return pruned_tensor

    def _compute_svd_energy_stats(self, singular_values, probe_rank=128, thresholds=(0.9,)):
        """Compute energy-at-rank and rank-at-energy stats from singular values."""
        if singular_values.numel() == 0:
            return {
                "probe_rank": int(probe_rank),
                "energy_at_probe_rank": 0.0,
                "rank_for_threshold": {},
            }

        s2 = singular_values.float().pow(2)
        total_energy = torch.sum(s2).item()
        max_rank = int(s2.numel())
        probe_rank = max(0, int(probe_rank))
        probe_rank_eff = min(probe_rank, max_rank)

        if total_energy <= 0.0:
            rank_for_threshold = {}
            for tau in thresholds:
                tau_val = float(tau)
                rank_for_threshold[tau_val] = 0
            return {
                "probe_rank": int(probe_rank),
                "energy_at_probe_rank": 0.0,
                "rank_for_threshold": rank_for_threshold,
            }

        cumsum_energy = torch.cumsum(s2, dim=0)
        if probe_rank_eff <= 0:
            energy_at_probe = 0.0
        else:
            energy_at_probe = float((cumsum_energy[probe_rank_eff - 1] / total_energy).item())

        rank_for_threshold = {}
        for tau in thresholds:
            tau_val = float(tau)
            tau_clamped = min(max(tau_val, 0.0), 1.0)
            target = total_energy * tau_clamped
            idx = int(
                torch.searchsorted(
                    cumsum_energy,
                    torch.tensor(target, device=cumsum_energy.device),
                    right=False,
                ).item()
            )
            rank_for_threshold[tau_val] = min(max_rank, idx + 1)

        return {
            "probe_rank": int(probe_rank),
            "energy_at_probe_rank": energy_at_probe,
            "rank_for_threshold": rank_for_threshold,
        }

    def _svd_decompose(self, W, rank=8, energy_stats_cfg=None):
        # ⭐ 检查 rank 是否超过矩阵最小维度
        max_rank = min(W.shape[0], W.shape[1])
        if rank > max_rank:
            logger.warning(
                f"SVD rank ({rank}) exceeds matrix min dimension ({max_rank}), "
                f"clamping to {max_rank}. Matrix shape: {W.shape}"
            )
            rank = max_rank
        
        # SVD decomposition with double precision for numerical stability
        u, s, vh = torch.linalg.svd(W.float(), full_matrices=False)        
        # Numerical stability checks
        assert not torch.isnan(u).any(), "NaN in U"
        assert not torch.isnan(s).any(), "NaN in S"
        assert not torch.isnan(vh).any(), "NaN in V^T"
        assert not torch.isinf(u).any(), "Inf in U"
        assert not torch.isinf(s).any(), "Inf in S"
        assert not torch.isinf(vh).any(), "Inf in V^T"

        svd_energy_stats = None
        if energy_stats_cfg is not None:
            probe_rank = int(energy_stats_cfg.get("probe_rank", 128))
            thresholds = tuple(energy_stats_cfg.get("thresholds", (0.9,)))
            svd_energy_stats = self._compute_svd_energy_stats(
                singular_values=s,
                probe_rank=probe_rank,
                thresholds=thresholds,
            )
            svd_energy_stats["matrix_shape"] = [int(W.shape[0]), int(W.shape[1])]
            svd_energy_stats["used_rank"] = int(rank)
            svd_energy_stats["max_rank"] = int(max_rank)
        
        # Clamp singular values to prevent division issues
        s = torch.clamp(s, min=1e-8)
        
        # Extract low-rank components
        proj_down = vh[:rank, :].float()  # [rank, in_features] FP32
        proj_up = (u[:, :rank] * s[:rank]).float()  # [out_features, rank] FP32
        L = proj_up @ proj_down  # [out_features, in_features] FP32
        
        # Calculate residual
        R = W - L  # [out_features, in_features] FP32
        
        if energy_stats_cfg is None:
            return L, R, proj_down, proj_up
        return L, R, proj_down, proj_up, svd_energy_stats

    def _search_single_svd_rank_by_delta_norm_error(
        self,
        W,
        H,
        svd_lowrank_fp16=False,
        start_rank=16,
        rank_step=16,
        delta_norm_threshold=0.05,
    ):
        # Search single-stage SVD rank with normalized activation-error improvement:
        # E(r) = ((R_r @ H) * R_r).sum / baseline_energy
        # DeltaE = E(r_prev) - E(r_cur)
        # Stop when DeltaE < delta_norm_threshold and keep previous accepted rank.
        max_rank = int(min(W.shape[0], W.shape[1]))
        if max_rank <= 0:
            return 1, []

        start_rank = max(1, int(start_rank))
        rank_step = max(1, int(rank_step))
        delta_norm_threshold = float(delta_norm_threshold)

        candidate_ranks = list(range(start_rank, max_rank + 1, rank_step))
        if not candidate_ranks:
            candidate_ranks = [max_rank]
        elif candidate_ranks[-1] != max_rank:
            candidate_ranks.append(max_rank)

        H_eval = H.float()
        baseline_energy = torch.sum((W @ H_eval) * W).item()
        if baseline_energy <= 1e-12:
            baseline_energy = torch.sum(W * W).item() + 1e-12

        # One full SVD, then reuse top-r slices for all candidates.
        u, s, vh = torch.linalg.svd(W.float(), full_matrices=False)
        s = torch.clamp(s, min=1e-8)

        trace = []
        prev_norm_error = None
        prev_rank = None
        selected_rank = int(candidate_ranks[-1])

        for rank in candidate_ranks:
            rank = int(min(max(rank, 1), max_rank))
            proj_down = vh[:rank, :].float()
            proj_up = (u[:, :rank] * s[:rank]).float()

            if svd_lowrank_fp16:
                l_quantized = self._compose_lowrank_fp16(proj_down, proj_up)
            else:
                l_quantized = self._quantize_lowrank_4bit(proj_down, proj_up)

            residual = (W - l_quantized.float()).float()
            act_error = torch.sum((residual @ H_eval) * residual).item()
            if act_error < 0 and abs(act_error) < 1e-9:
                act_error = 0.0
            norm_error = float(act_error / baseline_energy)

            delta_norm_error = None
            if prev_norm_error is not None:
                delta_norm_error = float(prev_norm_error - norm_error)

            stop_on_current = bool(
                (delta_norm_error is not None) and (delta_norm_error < delta_norm_threshold)
            )
            trace.append(
                {
                    "rank": int(rank),
                    "normalized_error": float(norm_error),
                    "delta_normalized_error": None if delta_norm_error is None else float(delta_norm_error),
                    "stop_threshold": float(delta_norm_threshold),
                    "accepted": bool(not stop_on_current),
                }
            )

            if stop_on_current:
                # User-requested rule: if gain is too small, discard current rank and keep previous rank.
                selected_rank = int(prev_rank if prev_rank is not None else rank)
                break

                selected_rank = int(prev_rank if prev_rank is not None else rank)
                break

            prev_norm_error = norm_error
            prev_rank = int(rank)
            selected_rank = int(rank)

        del u, s, vh
        return selected_rank, trace
  

    def _quantize_lowrank_4bit(self, proj_down, proj_up):

        # Quantize proj_down
        proj_down_quantized, _, _ = quantize_to_4bit_perchannel(proj_down)
        
        # Quantize proj_up
        proj_up_quantized, _, _ = quantize_to_4bit_perchannel(proj_up)
        
        # Compute fake-quantized L with FP32 accumulation for better numerical stability.
        L_quantized = (proj_up_quantized.float() @ proj_down_quantized.float()).half()
        
        return L_quantized

    def _quantize_lowrank_8bit(self, proj_down, proj_up):

        # Quantize proj_down
        proj_down_quantized, _, _ = quantize_to_8bit_perchannel(proj_down)

        # Quantize proj_up
        proj_up_quantized, _, _ = quantize_to_8bit_perchannel(proj_up)

        # Compute fake-quantized L with FP32 accumulation for better numerical stability.
        L_quantized = (proj_up_quantized.float() @ proj_down_quantized.float()).half()

        return L_quantized

    def _compose_lowrank_fp16(self, proj_down, proj_up):
        # Keep low-rank branch in FP16 without 4bit fake quantization.
        return (proj_up.float() @ proj_down.float()).half()

    def _quantize_2bit_masked_perchannel(self, x, mask):

        q = torch.zeros_like(x)
        if x.numel() == 0 or (not bool(mask.any())):
            return q
        active_cols = mask[0].nonzero(as_tuple=False).flatten()
        if active_cols.numel() == 0:
            return q
        q_part = quantize_to_2bit_perchannel(x[:, active_cols])
        q[:, active_cols] = q_part.float()
        return q

    def _quantize_ternary_twn_masked(self, x, mask, delta_factor=0.7):

        q = torch.zeros_like(x)
        if x.numel() == 0 or (not bool(mask.any())):
            return q

        mask_f = mask.float()
        abs_x = x.abs()

        # Row-wise masked mean(|x|).
        masked_count = mask_f.sum(dim=1).clamp(min=1.0)
        mean_abs = (abs_x * mask_f).sum(dim=1) / masked_count
        delta = max(float(delta_factor), 0.0) * mean_abs

        selected = mask & (abs_x > delta.unsqueeze(1))
        selected_f = selected.float()
        selected_count = selected_f.sum(dim=1).clamp(min=1.0)
        alpha = (abs_x * selected_f).sum(dim=1) / selected_count

        # If no selected elements in a row, force alpha=0 to avoid artifacts.
        alpha = torch.where(selected_f.sum(dim=1) > 0, alpha, torch.zeros_like(alpha))

        q = torch.sign(x) * alpha.unsqueeze(1)
        q = q * selected_f
        return q

    def _compute_reconstruction_error(self, W, L_quantized, R_quantized):

        W_reconstructed = L_quantized + R_quantized  # FP16 + FP16 = FP16
        error = torch.sum((W - W_reconstructed) ** 2).item()
        return error

    def _build_row_prune_keep_mask(self, r_block, m, score_metric="magnitude", col_score=None):
        # Per-row keep mask by pruning m smallest entries based on selected score metric.
        n_cols = int(r_block.shape[1]) if r_block.ndim >= 2 else 0
        m_val = min(max(int(m), 0), n_cols)
        if m_val <= 0:
            return torch.ones_like(r_block, dtype=torch.bool)
        if m_val >= n_cols:
            return torch.zeros_like(r_block, dtype=torch.bool)

        score_metric = str(score_metric).strip().lower()
        score = r_block.abs()
        if score_metric == "wanda":
            if (col_score is None) or (not isinstance(col_score, torch.Tensor)) or (int(col_score.numel()) != int(n_cols)):
                raise ValueError(
                    "WANDA row-prune score requires a valid per-column score tensor with length equal to block columns."
                )
            score = score * col_score.reshape(1, -1).to(device=score.device, dtype=score.dtype)
        elif score_metric != "magnitude":
            raise ValueError(f"Unsupported row-prune score_metric='{score_metric}'. Expected magnitude/wanda.")

        smallest_idx = torch.topk(score, k=m_val, dim=1, largest=False).indices
        mask_prune = torch.zeros_like(r_block, dtype=torch.bool)
        mask_prune.scatter_(1, smallest_idx, True)
        return ~mask_prune

    def _search_row_prune_m_for_binary_block(
        self,
        r_block,
        candidate_ms=(0, 4, 8, 16, 32, 64),
        score_metric="magnitude",
        col_score=None,
        order=2,
        quant_scheme="binary",
        clip_search_enable=False,
        clip_candidates=(1.0, 0.999, 0.995, 0.99, 0.98, 0.96),
        clip_min_value=1e-8,
        h_block=None,
        act_topk=0,
        column_compensate=False,
        h_inv_block=None,
    ):
        # Per-block row-prune search:
        # 1) For each row, prune m smallest entries by selected score metric.
        # 2) Quantize pruned block by selected scheme.
        # 3) Stage-A: rank m by weight reconstruction loss sum((R_b - Q_b)^2).
        # 4) Optional Stage-B: top-K rerank with one-shot RTN refill on pruned entries,
        #    then pick m by activation score S_act = sum((E @ H_b) * E), E=R_b-Q_refill.
        # 5) If Stage-B is disabled, keep previous weight-objective + zero-gate behavior.
        # 6) Optional clip-search remains only on Stage-B disabled path.
        if r_block.numel() == 0:
            return r_block, {
                "best_m": 0,
                "best_prune_ratio": 0.0,
                "best_weight_loss_sum": 0.0,
                "best_activation_loss_sum": 0.0,
                "best_prune_error_sum": 0.0,
                "best_quant_error_sum": 0.0,
                "best_avg_iter": 0.0,
                "best_clip_p": 1.0,
                "best_clip_value": 0.0,
                "best_clip_weight_loss_sum": 0.0,
                "zero_gate_applied": False,
                "act_rerank_enable": False,
                "act_topk_requested": int(act_topk),
                "act_topk_evaluated": 0,
                "best_act_score": 0.0,
                "best_refill_nonzero_ratio": 0.0,
                "best_refill_nonzero": 0,
                "best_refill_total_pruned": 0,
                "act_topk_trace": [],
            }

        _, n_cols = r_block.shape
        score_metric = str(score_metric).strip().lower()
        if score_metric not in {"magnitude", "wanda"}:
            raise ValueError(f"Unsupported row-prune score_metric='{score_metric}'. Expected magnitude/wanda.")

        ms = []
        for m in candidate_ms:
            try:
                m_val = int(m)
            except Exception:
                continue
            m_val = min(max(m_val, 0), int(n_cols))
            if m_val not in ms:
                ms.append(m_val)
        if len(ms) == 0:
            ms = [0]
        if 0 not in ms:
            ms = [0] + ms

        quant_scheme = str(quant_scheme).strip().lower()
        if quant_scheme not in {"binary", "std2bit", "std3bit", "std4bit"}:
            logger.warning(
                f"Unsupported row-prune quant_scheme='{quant_scheme}', fallback to 'binary'."
            )
            quant_scheme = "binary"
        act_topk = max(int(act_topk), 0)
        h_block_valid = isinstance(h_block, torch.Tensor) and h_block.numel() > 0
        act_rerank_enable = bool(
            (act_topk > 0)
            and h_block_valid
            and (quant_scheme in {"std2bit", "std3bit", "std4bit"})
        )
        column_compensate_enable = bool(
            column_compensate
            and isinstance(h_inv_block, torch.Tensor)
            and (h_inv_block.ndim == 2)
            and (h_inv_block.shape[0] == h_inv_block.shape[1])
            and (int(h_inv_block.shape[0]) == int(n_cols))
        )
        clip_search_enable = bool(clip_search_enable)
        if act_rerank_enable and clip_search_enable:
            # Keep selection logic deterministic: Stage-B picks m directly by S_act.
            clip_search_enable = False
        clip_min_value = max(float(clip_min_value), 0.0)
        clip_ps = []
        for p in clip_candidates:
            try:
                p_val = float(p)
            except Exception:
                continue
            p_val = min(max(p_val, 0.0), 1.0)
            if all(abs(p_val - x) > 1e-12 for x in clip_ps):
                clip_ps.append(p_val)
        if len(clip_ps) == 0:
            clip_ps = [1.0]
        if all(abs(x - 1.0) > 1e-12 for x in clip_ps):
            clip_ps = [1.0] + clip_ps

        def _quantize_masked_perrow_std(r_src, keep_mask, bits=2, return_qparams=False):
            q_out = torch.zeros_like(r_src)
            keep_counts = keep_mask.sum(dim=1)
            if keep_counts.numel() == 0:
                if return_qparams:
                    return q_out, 0.0, None
                return q_out, 0.0

            iter_counts = []

            def _quantize_kept_vals_std_lowbit(kept_vals, bits, return_qparams=False):
                # Keep row-prune std2bit/std3bit/std4bit consistent with iterative low-bit fitting.
                has_braq_quant = hasattr(self, "braq_quantizer") and (self.braq_quantizer is not None)
                iterative_enable = bool(getattr(self.braq_quantizer, "iterative_2bit_enable", True)) if has_braq_quant else True
                n_iter = int(getattr(self.braq_quantizer, "iterative_2bit_iters", 5)) if has_braq_quant else 5
                eps = float(getattr(self.braq_quantizer, "iterative_2bit_eps", 1e-8)) if has_braq_quant else 1e-8
                update_offset = bool(getattr(self.braq_quantizer, "iterative_2bit_update_offset", True)) if has_braq_quant else True
                fixed_iters = bool(getattr(self.braq_quantizer, "iterative_2bit_fixed_iters", False)) if has_braq_quant else False

                if not iterative_enable and bits in (2, 3, 4):
                    raise RuntimeError(
                        "std_gptq row-prune std2bit/std3bit/std4bit requires iterative affine quantization; "
                        "fallback quantization is disabled."
                    )

                mask_all = torch.ones_like(kept_vals, dtype=torch.bool)
                q_it, q_info = iterative_affine_quantize_perchannel(
                    kept_vals,
                    bits=int(bits),
                    mask=mask_all,
                    n_iter=n_iter,
                    eps=eps,
                    update_offset=update_offset,
                    fixed_iters=fixed_iters,
                    print_mse=False,
                    return_info=True,
                )
                iter_val = None
                if isinstance(q_info, dict) and (q_info.get("iters") is not None):
                    iter_val = float(q_info["iters"])
                if return_qparams:
                    qparams = None
                    if isinstance(q_info, dict):
                        scale_it = q_info.get("scale", None)
                        zero_it = q_info.get("zero_point", None)
                        maxq_it = q_info.get("maxq", None)
                        if (scale_it is not None) and (zero_it is not None):
                            qparams = {
                                "scale": scale_it.reshape(-1, 1).to(device=kept_vals.device, dtype=torch.float32),
                                "zero": zero_it.reshape(-1, 1).to(device=kept_vals.device, dtype=torch.float32),
                                "maxq": float(maxq_it) if maxq_it is not None else float((2 ** int(bits)) - 1),
                            }
                    return q_it.float(), iter_val, qparams
                return q_it.float(), iter_val

            min_k = int(keep_counts.min().item())
            max_k = int(keep_counts.max().item())
            if max_k == 0:
                if return_qparams:
                    # Fallback: if all positions are pruned, derive affine params from full row.
                    scale, zero, maxq = _std_gptq_find_params_weight_perchannel(
                        r_src.float(),
                        bits=int(bits),
                        sym=False,
                    )
                    qparams = {
                        "scale": scale.float(),
                        "zero": zero.float(),
                        "maxq": float(maxq.item()),
                    }
                    return q_out, 0.0, qparams
                return q_out, 0.0

            # Row-prune path normally keeps exactly (n_cols - m) values per row.
            # Fast path: batch quantize all kept values together once.
            if min_k == max_k:
                k = max_k
                kept_vals = r_src[keep_mask].reshape(r_src.shape[0], k)
                iter_qparams = None
                if return_qparams:
                    q_kept, iter_k, iter_qparams = _quantize_kept_vals_std_lowbit(
                        kept_vals,
                        bits=bits,
                        return_qparams=True,
                    )
                else:
                    q_kept, iter_k = _quantize_kept_vals_std_lowbit(kept_vals, bits=bits)
                if iter_k is not None:
                    iter_counts.append(float(iter_k))
                q_out[keep_mask] = q_kept.float().reshape(-1)
                avg_iter = float(sum(iter_counts) / len(iter_counts)) if len(iter_counts) > 0 else 0.0
                if return_qparams:
                    # Prefer iterative final affine params for refill codebook reuse.
                    if (
                        isinstance(iter_qparams, dict)
                        and (iter_qparams.get("scale", None) is not None)
                        and (iter_qparams.get("zero", None) is not None)
                    ):
                        qparams = {
                            "scale": iter_qparams["scale"].float(),
                            "zero": iter_qparams["zero"].float(),
                            "maxq": float(iter_qparams.get("maxq", (2 ** int(bits)) - 1)),
                        }
                    else:
                        # Fallback when iterative qparams are unavailable.
                        scale, zero, maxq = _std_gptq_find_params_weight_perchannel(
                            kept_vals.float(),
                            bits=int(bits),
                            sym=False,
                        )
                        qparams = {
                            "scale": scale.float(),
                            "zero": zero.float(),
                            "maxq": float(maxq.item()),
                        }
                    return q_out, avg_iter, qparams
                return q_out, avg_iter

            # Fallback for any non-uniform mask pattern.
            row_scale = None
            row_zero = None
            row_maxq = float((2 ** int(bits)) - 1)
            if return_qparams:
                row_scale = torch.zeros((r_src.shape[0], 1), device=r_src.device, dtype=torch.float32)
                row_zero = torch.zeros((r_src.shape[0], 1), device=r_src.device, dtype=torch.float32)
            for row_idx in range(r_src.shape[0]):
                keep_idx = torch.where(keep_mask[row_idx])[0]
                if keep_idx.numel() > 0:
                    row_vals = r_src[row_idx:row_idx + 1, keep_idx]
                    qparams_row = None
                    if return_qparams:
                        q_row, iter_row, qparams_row = _quantize_kept_vals_std_lowbit(
                            row_vals,
                            bits=bits,
                            return_qparams=True,
                        )
                    else:
                        q_row, iter_row = _quantize_kept_vals_std_lowbit(row_vals, bits=bits)
                    if iter_row is not None:
                        iter_counts.append(float(iter_row))
                    q_out[row_idx, keep_idx] = q_row.float().reshape(-1)
                    if return_qparams:
                        if (
                            isinstance(qparams_row, dict)
                            and (qparams_row.get("scale", None) is not None)
                            and (qparams_row.get("zero", None) is not None)
                        ):
                            row_scale[row_idx:row_idx + 1, :] = qparams_row["scale"].float()
                            row_zero[row_idx:row_idx + 1, :] = qparams_row["zero"].float()
                            row_maxq = float(qparams_row.get("maxq", row_maxq))
                        else:
                            scale_row, zero_row, _ = _std_gptq_find_params_weight_perchannel(
                                row_vals.float(),
                                bits=int(bits),
                                sym=False,
                            )
                            row_scale[row_idx:row_idx + 1, :] = scale_row.float()
                            row_zero[row_idx:row_idx + 1, :] = zero_row.float()
                elif return_qparams:
                    # If this row has no kept entries, fallback to full-row stats.
                    row_src = r_src[row_idx:row_idx + 1, :].float()
                    scale_row, zero_row, _ = _std_gptq_find_params_weight_perchannel(
                        row_src,
                        bits=int(bits),
                        sym=False,
                    )
                    row_scale[row_idx:row_idx + 1, :] = scale_row.float()
                    row_zero[row_idx:row_idx + 1, :] = zero_row.float()
            avg_iter = float(sum(iter_counts) / len(iter_counts)) if len(iter_counts) > 0 else 0.0
            if return_qparams:
                qparams = {
                    "scale": row_scale,
                    "zero": row_zero,
                    "maxq": float(row_maxq),
                }
                return q_out, avg_iter, qparams
            return q_out, avg_iter

        def _quantize_with_scheme(r_src, keep_mask, return_qparams=False):
            if not bool(keep_mask.any()):
                if return_qparams and quant_scheme in {"std2bit", "std3bit", "std4bit"}:
                    bits_local = {"std2bit": 2, "std3bit": 3, "std4bit": 4}[quant_scheme]
                    scale, zero, maxq = _std_gptq_find_params_weight_perchannel(
                        r_src.float(),
                        bits=int(bits_local),
                        sym=False,
                    )
                    qparams = {
                        "scale": scale.float(),
                        "zero": zero.float(),
                        "maxq": float(maxq.item()),
                    }
                    return torch.zeros_like(r_src), 0.0, qparams
                if return_qparams:
                    return torch.zeros_like(r_src), 0.0, None
                return torch.zeros_like(r_src), 0.0
            if quant_scheme == "binary":
                q_block_local = high_order_residual(r_src, keep_mask, order=order)
                if return_qparams:
                    return q_block_local * keep_mask.float(), 0.0, None
                return q_block_local * keep_mask.float(), 0.0
            if quant_scheme == "std2bit":
                return _quantize_masked_perrow_std(
                    r_src,
                    keep_mask,
                    bits=2,
                    return_qparams=return_qparams,
                )
            if quant_scheme == "std3bit":
                return _quantize_masked_perrow_std(
                    r_src,
                    keep_mask,
                    bits=3,
                    return_qparams=return_qparams,
                )
            return _quantize_masked_perrow_std(
                r_src,
                keep_mask,
                bits=4,
                return_qparams=return_qparams,
            )

        def _quantize_with_scheme_column_compensated(r_src, keep_mask, h_inv_local):
            # GPTQ-style in-block column compensation for row-prune search.
            q_init, _ = _quantize_with_scheme(r_src, keep_mask, return_qparams=False)
            if (
                (h_inv_local is None)
                or (not isinstance(h_inv_local, torch.Tensor))
                or (h_inv_local.ndim != 2)
                or (h_inv_local.shape[0] != h_inv_local.shape[1])
                or (int(h_inv_local.shape[0]) != int(r_src.shape[1]))
            ):
                return q_init.float(), 0.0

            r_work = r_src.clone().float()
            q_out = torch.zeros_like(r_work)
            iter_counts = []
            h_inv_eval = h_inv_local.float()
            for col_idx in range(int(r_work.shape[1])):
                r_col = r_work[:, col_idx:col_idx + 1]
                keep_col = keep_mask[:, col_idx:col_idx + 1]
                if quant_scheme == "binary":
                    q_col = high_order_residual(r_col, keep_col, order=order)
                    if isinstance(q_col, (tuple, list)):
                        q_col = q_col[0]
                    q_col = q_col.float() * keep_col.float()
                    iter_col = 0.0
                elif quant_scheme == "std2bit":
                    q_col, iter_col = _quantize_masked_perrow_std(
                        r_col,
                        keep_col,
                        bits=2,
                        return_qparams=False,
                    )
                elif quant_scheme == "std3bit":
                    q_col, iter_col = _quantize_masked_perrow_std(
                        r_col,
                        keep_col,
                        bits=3,
                        return_qparams=False,
                    )
                else:
                    q_col, iter_col = _quantize_masked_perrow_std(
                        r_col,
                        keep_col,
                        bits=4,
                        return_qparams=False,
                    )
                q_col = q_col.float()
                q_out[:, col_idx:col_idx + 1] = q_col
                if iter_col is not None:
                    iter_counts.append(float(iter_col))

                d = torch.clamp(h_inv_eval[col_idx, col_idx], min=1e-8)
                err_col = (r_work[:, col_idx] - q_col.flatten()) / d
                r_work[:, col_idx:] -= err_col.unsqueeze(1).matmul(h_inv_eval[col_idx, col_idx:].unsqueeze(0))

            avg_iter = float(sum(iter_counts) / len(iter_counts)) if len(iter_counts) > 0 else 0.0
            return q_out.to(dtype=r_src.dtype), avg_iter

        def _rtn_refill_pruned_once(r_src, q_kept, keep_mask, bits, kept_qparams=None):
            q_out = q_kept.clone().float()
            pruned_mask = ~keep_mask
            pruned_total = int(pruned_mask.sum().item())
            if pruned_total <= 0:
                return q_out, {
                    "refilled_nonzero": 0,
                    "refilled_total_pruned": 0,
                    "refilled_nonzero_ratio": 0.0,
                }

            n_rows = int(r_src.shape[0])
            keep_counts = keep_mask.sum(dim=1)
            prune_counts = pruned_mask.sum(dim=1)
            keep_uniform = int(keep_counts.min().item()) == int(keep_counts.max().item())
            prune_uniform = int(prune_counts.min().item()) == int(prune_counts.max().item())
            reuse_qparams = (
                isinstance(kept_qparams, dict)
                and (kept_qparams.get("scale", None) is not None)
                and (kept_qparams.get("zero", None) is not None)
            )
            reused_scale = None
            reused_zero = None
            reused_maxq = None
            if reuse_qparams:
                reused_scale = kept_qparams["scale"].to(device=r_src.device, dtype=torch.float32)
                reused_zero = kept_qparams["zero"].to(device=r_src.device, dtype=torch.float32)
                reused_maxq = torch.tensor(
                    float(kept_qparams.get("maxq", (2 ** int(bits)) - 1)),
                    device=r_src.device,
                    dtype=torch.float32,
                )

            if keep_uniform and prune_uniform:
                k = int(keep_counts[0].item())
                p = int(prune_counts[0].item())
                if p > 0:
                    if reuse_qparams:
                        scale = reused_scale
                        zero = reused_zero
                    else:
                        if k > 0:
                            src_for_params = r_src[keep_mask].reshape(n_rows, k)
                        else:
                            src_for_params = r_src
                        scale, zero, reused_maxq = _std_gptq_find_params_weight_perchannel(
                            src_for_params.float(),
                            bits=int(bits),
                            sym=False,
                        )
                        scale = scale.float()
                        zero = zero.float()
                    pruned_vals = r_src[pruned_mask].reshape(n_rows, p).float()
                    q_pruned = _std_gptq_quantize(pruned_vals, scale, zero, reused_maxq).float()
                    q_out[pruned_mask] = q_pruned.reshape(-1)
            else:
                for row_idx in range(n_rows):
                    row_pruned_idx = torch.where(pruned_mask[row_idx])[0]
                    if row_pruned_idx.numel() == 0:
                        continue
                    if reuse_qparams:
                        scale = reused_scale[row_idx:row_idx + 1, :]
                        zero = reused_zero[row_idx:row_idx + 1, :]
                    else:
                        row_keep_idx = torch.where(keep_mask[row_idx])[0]
                        if row_keep_idx.numel() > 0:
                            src_for_params = r_src[row_idx:row_idx + 1, row_keep_idx].float()
                        else:
                            src_for_params = r_src[row_idx:row_idx + 1, :].float()
                        scale, zero, reused_maxq = _std_gptq_find_params_weight_perchannel(
                            src_for_params,
                            bits=int(bits),
                            sym=False,
                        )
                        scale = scale.float()
                        zero = zero.float()
                    row_pruned_vals = r_src[row_idx:row_idx + 1, row_pruned_idx].float()
                    q_row = _std_gptq_quantize(row_pruned_vals, scale, zero, reused_maxq).float()
                    q_out[row_idx, row_pruned_idx] = q_row.reshape(-1)

            refilled_vals = q_out[pruned_mask]
            refilled_nonzero = int((refilled_vals != 0).sum().item())
            refilled_ratio = float(refilled_nonzero / max(pruned_total, 1))
            return q_out, {
                "refilled_nonzero": refilled_nonzero,
                "refilled_total_pruned": pruned_total,
                "refilled_nonzero_ratio": refilled_ratio,
            }

        candidates = []
        m0_snapshot = None

        for m in ms:
            mask_keep = self._build_row_prune_keep_mask(
                r_block,
                m,
                score_metric=score_metric,
                col_score=col_score,
            )
            r_pruned = r_block * mask_keep.float()
            kept_qparams = None
            if act_rerank_enable and (quant_scheme in {"std2bit", "std3bit", "std4bit"}):
                q_block, avg_iter, kept_qparams = _quantize_with_scheme(
                    r_pruned,
                    mask_keep,
                    return_qparams=True,
                )
            else:
                if column_compensate_enable:
                    q_block, avg_iter = _quantize_with_scheme_column_compensated(
                        r_pruned,
                        mask_keep,
                        h_inv_block,
                    )
                else:
                    q_block, avg_iter = _quantize_with_scheme(r_pruned, mask_keep)

            # Logging compatibility: keep weight-space losses.
            total_loss = float(torch.sum((r_block - q_block) ** 2).item())
            prune_error = float(torch.sum((r_block - r_pruned) ** 2).item())
            quant_error = float(torch.sum((r_pruned - q_block) ** 2).item())
            # Selection objective: pure weight reconstruction loss.
            objective_loss = total_loss

            info = {
                "m": int(m),
                "prune_ratio": float(m / max(int(n_cols), 1)),
                "weight_loss_sum": float(total_loss),
                "activation_loss_sum": float(objective_loss),
                "prune_error_sum": float(prune_error),
                "quant_error_sum": float(quant_error),
                "avg_iter": float(avg_iter),
                "mask_keep": mask_keep.clone(),
                "r_pruned": r_pruned.clone(),
                "q_block": q_block.clone().float(),
                "kept_qparams": kept_qparams,
            }
            if int(m) == 0:
                m0_snapshot = info
            candidates.append(info)

        if len(candidates) == 0:
            full_mask = torch.ones_like(r_block, dtype=torch.bool)
            best_q, fallback_avg_iter = _quantize_with_scheme(r_block, full_mask)
            best_mask_keep = full_mask
            best_r_pruned = r_block.clone()
            fallback_weight_loss = float(torch.sum((r_block - best_q) ** 2).item())
            best_info = {
                "best_m": 0,
                "best_prune_ratio": 0.0,
                "best_weight_loss_sum": fallback_weight_loss,
                "best_activation_loss_sum": fallback_weight_loss,
                "best_prune_error_sum": 0.0,
                "best_quant_error_sum": fallback_weight_loss,
                "best_avg_iter": float(fallback_avg_iter),
                "act_rerank_enable": False,
                "act_topk_requested": int(act_topk),
                "act_topk_evaluated": 0,
                "best_act_score": float(fallback_weight_loss),
                "best_refill_nonzero_ratio": 0.0,
                "best_refill_nonzero": 0,
                "best_refill_total_pruned": 0,
                "act_topk_trace": [],
                "column_compensate_enable": bool(column_compensate_enable),
            }
            best_avg_iter = float(fallback_avg_iter)
            zero_gate_applied = False
        else:
            zero_gate_applied = False
            best_avg_iter = 0.0
            best_mask_keep = None
            best_r_pruned = None
            best_q = None
            best_info = None

            sorted_by_weight = sorted(candidates, key=lambda x: float(x["weight_loss_sum"]))

            if act_rerank_enable:
                h_eval = h_block.float()
                bits_for_rtn = {"std2bit": 2, "std3bit": 3, "std4bit": 4}[quant_scheme]
                topk_eff = min(max(int(act_topk), 1), len(sorted_by_weight))
                rerank_pool = list(sorted_by_weight[:topk_eff])
                force_include_m0 = False
                if (m0_snapshot is not None) and all(int(x["m"]) != 0 for x in rerank_pool):
                    rerank_pool.append(m0_snapshot)
                    force_include_m0 = True

                weight_rank_map = {int(item["m"]): idx + 1 for idx, item in enumerate(sorted_by_weight)}
                best_rerank = None
                rerank_trace = []
                for item in rerank_pool:
                    q_refill, refill_stats = _rtn_refill_pruned_once(
                        r_src=r_block,
                        q_kept=item["q_block"],
                        keep_mask=item["mask_keep"],
                        bits=bits_for_rtn,
                        kept_qparams=item.get("kept_qparams", None),
                    )
                    err_block = (r_block - q_refill).float()
                    act_score = float(torch.sum((err_block @ h_eval) * err_block).item())
                    if act_score < 0.0 and abs(act_score) < 1e-9:
                        act_score = 0.0
                    weight_loss_refill = float(torch.sum(err_block ** 2).item())
                    quant_error_refill = float(torch.sum((item["r_pruned"] - q_refill) ** 2).item())
                    cand = {
                        "m": int(item["m"]),
                        "prune_ratio": float(item["prune_ratio"]),
                        "weight_loss_sum": float(weight_loss_refill),
                        "activation_loss_sum": float(act_score),
                        "prune_error_sum": float(item["prune_error_sum"]),
                        "quant_error_sum": float(quant_error_refill),
                        "avg_iter": float(item["avg_iter"]),
                        "mask_keep": item["mask_keep"].clone(),
                        "r_pruned": item["r_pruned"].clone(),
                        "q_block": q_refill.clone().float(),
                        "act_weight_rank": int(weight_rank_map.get(int(item["m"]), -1)),
                        "refilled_nonzero": int(refill_stats["refilled_nonzero"]),
                        "refilled_total_pruned": int(refill_stats["refilled_total_pruned"]),
                        "refilled_nonzero_ratio": float(refill_stats["refilled_nonzero_ratio"]),
                    }
                    rerank_trace.append(
                        {
                            "m": int(cand["m"]),
                            "weight_rank": int(cand["act_weight_rank"]),
                            "weight_loss_sum": float(cand["weight_loss_sum"]),
                            "act_score": float(cand["activation_loss_sum"]),
                            "refilled_nonzero": int(cand["refilled_nonzero"]),
                            "refilled_total_pruned": int(cand["refilled_total_pruned"]),
                            "refilled_nonzero_ratio": float(cand["refilled_nonzero_ratio"]),
                        }
                    )
                    if (best_rerank is None) or (
                        float(cand["activation_loss_sum"]) < float(best_rerank["activation_loss_sum"])
                    ):
                        best_rerank = cand

                if best_rerank is None:
                    best_rerank = sorted_by_weight[0]
                    best_rerank = {
                        "m": int(best_rerank["m"]),
                        "prune_ratio": float(best_rerank["prune_ratio"]),
                        "weight_loss_sum": float(best_rerank["weight_loss_sum"]),
                        "activation_loss_sum": float(best_rerank["weight_loss_sum"]),
                        "prune_error_sum": float(best_rerank["prune_error_sum"]),
                        "quant_error_sum": float(best_rerank["quant_error_sum"]),
                        "avg_iter": float(best_rerank["avg_iter"]),
                        "mask_keep": best_rerank["mask_keep"].clone(),
                        "r_pruned": best_rerank["r_pruned"].clone(),
                        "q_block": best_rerank["q_block"].clone().float(),
                        "act_weight_rank": 1,
                        "refilled_nonzero": 0,
                        "refilled_total_pruned": int((~best_rerank["mask_keep"]).sum().item()),
                        "refilled_nonzero_ratio": 0.0,
                    }

                best_q = best_rerank["q_block"]
                best_mask_keep = best_rerank["mask_keep"]
                best_r_pruned = best_rerank["r_pruned"]
                best_avg_iter = float(best_rerank["avg_iter"])
                best_info = {
                    "best_m": int(best_rerank["m"]),
                    "best_prune_ratio": float(best_rerank["prune_ratio"]),
                    "best_weight_loss_sum": float(best_rerank["weight_loss_sum"]),
                    "best_activation_loss_sum": float(best_rerank["activation_loss_sum"]),
                    "best_prune_error_sum": float(best_rerank["prune_error_sum"]),
                    "best_quant_error_sum": float(best_rerank["quant_error_sum"]),
                    "best_avg_iter": float(best_rerank["avg_iter"]),
                    "act_rerank_enable": True,
                    "act_topk_requested": int(act_topk),
                    "act_topk_evaluated": int(len(rerank_pool)),
                    "act_topk_force_include_m0": bool(force_include_m0),
                    "best_act_score": float(best_rerank["activation_loss_sum"]),
                    "best_act_weight_rank": int(best_rerank.get("act_weight_rank", -1)),
                    "best_refill_nonzero_ratio": float(best_rerank["refilled_nonzero_ratio"]),
                    "best_refill_nonzero": int(best_rerank["refilled_nonzero"]),
                    "best_refill_total_pruned": int(best_rerank["refilled_total_pruned"]),
                    "act_topk_trace": rerank_trace,
                    "column_compensate_enable": bool(column_compensate_enable),
                }
            else:
                best_weight = sorted_by_weight[0]
                if (best_weight is not None) and (m0_snapshot is not None) and (int(best_weight.get("m", 0)) != 0):
                    best_obj = float(best_weight["weight_loss_sum"])
                    m0_obj = float(m0_snapshot["weight_loss_sum"])
                    if best_obj >= (m0_obj - 1e-12):
                        best_weight = m0_snapshot
                        zero_gate_applied = True

                best_q = best_weight["q_block"].clone().float()
                best_mask_keep = best_weight["mask_keep"].clone()
                best_r_pruned = best_weight["r_pruned"].clone()
                best_avg_iter = float(best_weight["avg_iter"])
                best_info = {
                    "best_m": int(best_weight["m"]),
                    "best_prune_ratio": float(best_weight["prune_ratio"]),
                    "best_weight_loss_sum": float(best_weight["weight_loss_sum"]),
                    "best_activation_loss_sum": float(best_weight["weight_loss_sum"]),
                    "best_prune_error_sum": float(best_weight["prune_error_sum"]),
                    "best_quant_error_sum": float(best_weight["quant_error_sum"]),
                    "best_avg_iter": float(best_weight["avg_iter"]),
                    "act_rerank_enable": False,
                    "act_topk_requested": int(act_topk),
                    "act_topk_evaluated": 0,
                    "best_act_score": float(best_weight["weight_loss_sum"]),
                    "best_refill_nonzero_ratio": 0.0,
                    "best_refill_nonzero": 0,
                    "best_refill_total_pruned": int((~best_weight["mask_keep"]).sum().item()),
                    "act_topk_trace": [],
                    "column_compensate_enable": bool(column_compensate_enable),
                }

        best_clip_p = 1.0
        if best_mask_keep is not None and bool(best_mask_keep.any()):
            best_clip_value = float(best_r_pruned[best_mask_keep].abs().max().item())
        else:
            best_clip_value = 0.0
        best_clip_weight_loss_sum = float(best_info["best_weight_loss_sum"])
        best_clip_objective_sum = float(best_info["best_weight_loss_sum"])

        if (not act_rerank_enable) and clip_search_enable and (best_mask_keep is not None) and bool(best_mask_keep.any()):
            keep_abs = best_r_pruned[best_mask_keep].abs().reshape(-1)
            if keep_abs.numel() > 0:
                tiny = max(clip_min_value, 1e-8)
                best_q_clip = best_q
                for p in clip_ps:
                    if p >= 1.0 - 1e-12:
                        r_clip = best_r_pruned
                        c_val = float(keep_abs.max().item())
                    else:
                        q_tensor = torch.tensor(float(p), device=best_r_pruned.device, dtype=best_r_pruned.dtype)
                        c = torch.quantile(keep_abs, q_tensor)
                        c = torch.clamp(c, min=tiny)
                        c_val = float(c.item())
                        r_clip = torch.clamp(best_r_pruned, min=-c, max=c)
                        r_clip = r_clip * best_mask_keep.float()

                    q_clip, avg_iter_clip = _quantize_with_scheme(r_clip, best_mask_keep)
                    weight_loss_clip = float(torch.sum((r_block - q_clip) ** 2).item())
                    obj_loss_clip = weight_loss_clip
                    if obj_loss_clip < best_clip_objective_sum:
                        best_clip_objective_sum = obj_loss_clip
                        best_clip_weight_loss_sum = weight_loss_clip
                        best_q_clip = q_clip
                        best_clip_p = float(p)
                        best_clip_value = float(c_val)
                        best_avg_iter = float(avg_iter_clip)

                best_q = best_q_clip
                best_info["best_weight_loss_sum"] = float(best_clip_weight_loss_sum)
                best_info["best_quant_error_sum"] = float(torch.sum((best_r_pruned - best_q) ** 2).item())

        if bool(best_info.get("act_rerank_enable", False)):
            best_activation_loss_sum = float(best_info.get("best_act_score", best_info["best_weight_loss_sum"]))
        else:
            best_activation_loss_sum = float(best_info["best_weight_loss_sum"])

        best_info["best_clip_p"] = float(best_clip_p)
        best_info["best_clip_value"] = float(best_clip_value)
        best_info["best_clip_weight_loss_sum"] = float(best_clip_weight_loss_sum)
        best_info["best_avg_iter"] = float(best_avg_iter)
        best_info["best_activation_loss_sum"] = float(best_activation_loss_sum)
        best_info["zero_gate_applied"] = bool(zero_gate_applied)
        if best_mask_keep is None:
            best_mask_keep = torch.ones_like(r_block, dtype=torch.bool)
        best_info["best_keep_mask"] = best_mask_keep.clone()
        best_info["best_pruned_mask"] = (~best_mask_keep).clone()

        return best_q, best_info

    def _offline_row_prune_refill_fullfill(
        self,
        target_residual,
        quantized_residual,
        hessian_input,
        pruned_mask,
        blocksize=128,
        sweeps=1,
        max_positions=-1,
        include_zero=True,
        improve_tol=1e-12,
    ):
        """
        Offline row-prune refill with full-row activation objective:
            min_z (t - z)^T H (t - z)
        where t is the pre-quantized residual row, and z is the current quantized row.

        Coordinate update for one position j:
            e = t - z, g = H e, Delta = z_new - z_old
            DeltaLoss = -2 * Delta * g_j + Delta^2 * H_jj
            g <- g - Delta * H[:, j]
        """
        refill_stats = {
            "enabled": False,
            "supported": True,
            "total_pruned_count": 0.0,
            "attempted_candidate_count": 0.0,
            "accepted_update_count": 0.0,
            "refilled_nonzero_count": 0.0,
            "refilled_nonzero_ratio": 0.0,
            "activation_obj_before": 0.0,
            "activation_obj_after": 0.0,
            "activation_obj_delta": 0.0,
            "effective_max_positions": int(max_positions),
            "sweeps": int(sweeps),
            "include_zero": bool(include_zero),
        }

        if (
            target_residual is None
            or quantized_residual is None
            or hessian_input is None
            or pruned_mask is None
        ):
            refill_stats["supported"] = False
            return quantized_residual, refill_stats

        T = target_residual.float()
        Z = quantized_residual.float().clone()
        H = hessian_input.float()
        P = pruned_mask.bool()

        if T.shape != Z.shape or Z.shape[1] != H.shape[0] or H.shape[0] != H.shape[1]:
            refill_stats["supported"] = False
            logger.warning(
                "Offline refill skipped due to shape mismatch: "
                f"T={tuple(T.shape)}, Z={tuple(Z.shape)}, H={tuple(H.shape)}."
            )
            return quantized_residual, refill_stats

        rows, cols = Z.shape
        blocksize = max(int(blocksize), 1)
        sweeps = max(int(sweeps), 1)
        max_positions = int(max_positions)
        improve_tol = max(float(improve_tol), 0.0)
        include_zero = bool(include_zero)

        total_pruned = int(P.sum().item())
        refill_stats["total_pruned_count"] = float(total_pruned)
        refill_stats["enabled"] = bool(total_pruned > 0)
        refill_stats["sweeps"] = int(sweeps)
        refill_stats["effective_max_positions"] = int(max_positions)
        refill_stats["include_zero"] = bool(include_zero)
        if total_pruned <= 0:
            logger.info("  [RowPrune Refill] skipped: total_pruned=0")
            return Z.to(dtype=quantized_residual.dtype), refill_stats

        active_rows = int(P.any(dim=1).sum().item())
        refill_tick = time.time()
        report_every = max(1, active_rows // 20) if active_rows > 0 else 1
        processed_active_rows = 0
        logger.info(
            "  [RowPrune Refill] start: "
            f"shape={tuple(Z.shape)}, active_rows={active_rows}, total_pruned={total_pruned}, "
            f"sweeps={sweeps}, max_positions={max_positions}, include_zero={include_zero}, "
            f"report_every={report_every}"
        )

        total_obj_before = 0.0
        total_obj_after = 0.0
        accepted_update_count = 0
        attempted_candidate_count = 0

        for row_idx in range(rows):
            pruned_row = P[row_idx]
            if not bool(pruned_row.any()):
                continue
            processed_active_rows += 1

            t_row = T[row_idx].float()
            z_row = Z[row_idx].float()
            e_row = (t_row - z_row).float()
            g_row = (H @ e_row).float()

            obj_before = float(torch.dot(e_row, g_row).item())
            total_obj_before += obj_before

            position_list = []
            candidate_list = []

            for col_st in range(0, cols, blocksize):
                col_ed = min(col_st + blocksize, cols)
                pruned_block = pruned_row[col_st:col_ed]
                if not bool(pruned_block.any()):
                    continue

                keep_block = ~pruned_block
                kept_vals = z_row[col_st:col_ed][keep_block]
                if kept_vals.numel() > 0:
                    cand_vals = torch.unique(kept_vals.float())
                else:
                    cand_vals = torch.empty(0, device=z_row.device, dtype=torch.float32)
                if include_zero:
                    cand_vals = torch.unique(
                        torch.cat(
                            (
                                cand_vals,
                                torch.zeros(1, device=z_row.device, dtype=torch.float32),
                            ),
                            dim=0,
                        )
                    )
                if cand_vals.numel() <= 0:
                    cand_vals = torch.zeros(1, device=z_row.device, dtype=torch.float32)

                pruned_local_idx = torch.where(pruned_block)[0]
                for local_idx in pruned_local_idx.tolist():
                    position_list.append(int(col_st + int(local_idx)))
                    candidate_list.append(cand_vals)

            if len(position_list) == 0:
                total_obj_after += obj_before
                continue

            if max_positions > 0 and len(position_list) > max_positions:
                pos_tensor = torch.tensor(position_list, device=z_row.device, dtype=torch.long)
                pos_scores = torch.abs(e_row.index_select(0, pos_tensor))
                top_idx = torch.topk(pos_scores, k=max_positions, largest=True).indices.tolist()
                position_list = [position_list[idx] for idx in top_idx]
                candidate_list = [candidate_list[idx] for idx in top_idx]

            for _ in range(sweeps):
                pos_tensor = torch.tensor(position_list, device=z_row.device, dtype=torch.long)
                pos_order = torch.argsort(
                    torch.abs(e_row.index_select(0, pos_tensor)), descending=True
                ).tolist()
                has_change = False

                for ord_idx in pos_order:
                    col_idx = int(position_list[ord_idx])
                    cand_vals = candidate_list[ord_idx]

                    z_old = float(z_row[col_idx].item())
                    g_j = float(g_row[col_idx].item())
                    h_jj = float(H[col_idx, col_idx].item())
                    if abs(h_jj) < 1e-12:
                        h_jj = 1e-12

                    best_delta_loss = 0.0
                    best_value = z_old
                    for cand_val_t in cand_vals:
                        z_new = float(cand_val_t.item())
                        delta = float(z_new - z_old)
                        if abs(delta) <= 1e-12:
                            continue

                        delta_loss = float((-2.0 * delta * g_j) + (delta * delta * h_jj))
                        attempted_candidate_count += 1
                        if delta_loss < (best_delta_loss - improve_tol):
                            best_delta_loss = delta_loss
                            best_value = z_new

                    if abs(best_value - z_old) > 1e-12:
                        delta = float(best_value - z_old)
                        z_row[col_idx] = best_value
                        e_row[col_idx] = e_row[col_idx] - delta
                        g_row = g_row - delta * H[:, col_idx]
                        accepted_update_count += 1
                        has_change = True

                if not has_change:
                    break

            Z[row_idx] = z_row
            obj_after = float(torch.dot(e_row, g_row).item())
            if obj_after < 0.0 and abs(obj_after) < 1e-9:
                obj_after = 0.0
            total_obj_after += obj_after

            if (
                processed_active_rows == 1
                or processed_active_rows == active_rows
                or (processed_active_rows % report_every == 0)
            ):
                elapsed = time.time() - refill_tick
                eta = 0.0
                if processed_active_rows > 0 and active_rows > processed_active_rows:
                    eta = elapsed / float(processed_active_rows) * float(active_rows - processed_active_rows)
                logger.info(
                    "  [RowPrune Refill] progress: "
                    f"{processed_active_rows}/{active_rows} rows, "
                    f"accepted_updates={accepted_update_count}, "
                    f"attempted={attempted_candidate_count}, "
                    f"elapsed={elapsed:.3f}s, eta={eta:.3f}s"
                )

        refilled_nonzero_count = int((torch.abs(Z) > 1e-12).logical_and(P).sum().item())
        refilled_nonzero_ratio = float(refilled_nonzero_count / max(total_pruned, 1))

        refill_stats["attempted_candidate_count"] = float(attempted_candidate_count)
        refill_stats["accepted_update_count"] = float(accepted_update_count)
        refill_stats["refilled_nonzero_count"] = float(refilled_nonzero_count)
        refill_stats["refilled_nonzero_ratio"] = float(refilled_nonzero_ratio)
        refill_stats["activation_obj_before"] = float(total_obj_before)
        refill_stats["activation_obj_after"] = float(total_obj_after)
        refill_stats["activation_obj_delta"] = float(total_obj_after - total_obj_before)

        logger.info(
            "  [RowPrune Refill] done: "
            f"accepted_updates={accepted_update_count}, attempted={attempted_candidate_count}, "
            f"refilled_nonzero={refilled_nonzero_count}/{total_pruned} "
            f"({refilled_nonzero_ratio * 100:.2f}%), "
            f"obj_before={total_obj_before:.6e}, obj_after={total_obj_after:.6e}, "
            f"delta={float(total_obj_after - total_obj_before):.6e}, "
            f"time={time.time() - refill_tick:.3f}s"
        )

        return Z.to(dtype=quantized_residual.dtype), refill_stats

    def add_batch(self, inp, out):
        if inp is None:
            return
        with torch.no_grad():
            x = inp.detach()
            if x.dim() == 2:
                x = x.unsqueeze(0)
            tmp = int(x.shape[0])

            if isinstance(self.layer, nn.Linear) or isinstance(self.layer, transformers.Conv1D):
                if x.dim() == 3:
                    x = x.reshape((-1, x.shape[-1]))
                x = x.t()
            elif isinstance(self.layer, nn.Conv2d):
                unfold = nn.Unfold(
                    self.layer.kernel_size,
                    dilation=self.layer.dilation,
                    padding=self.layer.padding,
                    stride=self.layer.stride,
                )
                x = unfold(x)
                x = x.permute(1, 0, 2).flatten(1)

            if x.numel() == 0:
                return

            x = x.float()

            # Follow GPTQ reference Hessian accumulation rule.
            prev_nsamples = float(self.nsamples)
            self.H *= prev_nsamples / max(prev_nsamples + float(tmp), 1.0)
            self.nsamples += int(tmp)
            x_scaled = math.sqrt(2.0 / max(float(self.nsamples), 1.0)) * x
            self.H += x_scaled.matmul(x_scaled.t())

            # Keep token-level activation stats for refill scoring.
            token_count = int(x.shape[1])
            self.act_sum += x.sum(dim=1)
            self.act_square_sum += (x * x).sum(dim=1)
            self.act_count += float(token_count)

            if (not self.profiling_mode) and len(self.smooth_activations) < 4:
                take = min(token_count, 256)
                self.smooth_activations.append(x[:, :take].t().contiguous())

            try:
                norm_val = float(torch.norm(x, p=2).item() / max(token_count, 1))
                self.activation_norms.append(norm_val)
            except Exception:
                pass

    def _safe_hinv(self, H, percdamp=0.01):
        out_dtype = H.dtype
        H = H.to(dtype=torch.float64).clone()
        diag = torch.diag(H)
        dead = diag == 0
        if bool(dead.any()):
            H[dead, dead] = 1.0

        damp = float(percdamp) * float(torch.mean(torch.diag(H)).item())
        damp = max(damp, 1e-8)
        eye = torch.eye(H.shape[0], device=H.device, dtype=H.dtype)

        cur_damp = damp
        last_exc = None
        for _ in range(6):
            H_damped = H + eye * cur_damp
            try:
                chol = torch.linalg.cholesky(H_damped)
                # Match reference GPTQ:
                # Hinv_factor = chol(inv(H_damped), upper=True)
                Hinv_full = torch.cholesky_inverse(chol)
                Hinv_factor = torch.linalg.cholesky(Hinv_full, upper=True)
                return H_damped.to(dtype=out_dtype), Hinv_factor.to(dtype=out_dtype)
            except Exception as e:
                last_exc = e
                cur_damp *= 10.0

        diag_h = torch.diag(H)
        min_diag = float(diag_h.min().item()) if diag_h.numel() > 0 else float("nan")
        max_diag = float(diag_h.max().item()) if diag_h.numel() > 0 else float("nan")
        mean_diag = float(diag_h.mean().item()) if diag_h.numel() > 0 else float("nan")
        raise RuntimeError(
            "GPTQ H inverse-factor construction failed after damping retries. "
            f"percdamp={float(percdamp):.6g}, last_damp={float(cur_damp):.6g}, "
            f"H_shape={tuple(H.shape)}, dead_cols={int(dead.sum().item())}, "
            f"diag(min/mean/max)=({min_diag:.6e}/{mean_diag:.6e}/{max_diag:.6e}). "
            f"Last error: {repr(last_exc)}"
        )

    def _build_group_plan(self, n_cols, groupsize):
        if groupsize is None:
            groupsize = -1
        groupsize = int(groupsize)
        if groupsize <= 0:
            return [(0, n_cols)]
        groups = []
        for st in range(0, n_cols, groupsize):
            ed = min(st + groupsize, n_cols)
            groups.append((st, ed))
        return groups

    def _compute_group_qparams(self, src_block, keep_mask_block, bits, groupsize, sym=False):
        rows, n_cols = src_block.shape
        groups = self._build_group_plan(n_cols, groupsize)

        col_gid = torch.full((n_cols,), -1, device=src_block.device, dtype=torch.long)
        qparams_by_gid = {}

        gid_base = 0
        for g_local, (gst, ged) in enumerate(groups):
            gid = gid_base + g_local
            col_gid[gst:ged] = gid

            full_group_vals = src_block[:, gst:ged].float()
            if keep_mask_block is None:
                keep_group_mask = torch.ones_like(full_group_vals, dtype=torch.bool)
            else:
                keep_group_mask = keep_mask_block[:, gst:ged].bool()

            bitwidth = int(bits)
            if bitwidth in (2, 3, 4):
                if bool(sym):
                    raise RuntimeError("iterative affine qparams path only supports sym=False for bits in {2,3,4}.")
                if (not hasattr(self, "braq_quantizer")) or (self.braq_quantizer is None):
                    raise RuntimeError("iterative affine qparams requires self.braq_quantizer for bits in {2,3,4}.")
                if not bool(getattr(self.braq_quantizer, "iterative_2bit_enable", True)):
                    raise RuntimeError("iterative affine qparams is required for bits in {2,3,4}, but iterative_2bit_enable=False.")

                _, q_info = iterative_affine_quantize_perchannel(
                    full_group_vals,
                    bits=bitwidth,
                    mask=keep_group_mask,
                    n_iter=int(getattr(self.braq_quantizer, "iterative_2bit_iters", 5)),
                    eps=float(getattr(self.braq_quantizer, "iterative_2bit_eps", 1e-8)),
                    update_offset=bool(getattr(self.braq_quantizer, "iterative_2bit_update_offset", True)),
                    fixed_iters=bool(getattr(self.braq_quantizer, "iterative_2bit_fixed_iters", False)),
                    print_mse=bool(getattr(self.braq_quantizer, "iterative_2bit_print_mse", False)),
                    return_info=True,
                )
                if not isinstance(q_info, dict):
                    raise RuntimeError("iterative affine qparams failed: q_info is not a dict.")
                if q_info.get("scale", None) is None:
                    raise RuntimeError("iterative affine qparams failed: missing scale.")
                if q_info.get("zero_point", None) is None:
                    raise RuntimeError("iterative affine qparams failed: missing zero_point.")
                if q_info.get("maxq", None) is None:
                    raise RuntimeError("iterative affine qparams failed: missing maxq.")

                s = q_info["scale"].reshape(rows, 1).to(device=full_group_vals.device, dtype=torch.float32)
                z = q_info["zero_point"].reshape(rows, 1).to(device=full_group_vals.device, dtype=torch.float32)
                maxq_val = float(q_info["maxq"])
            else:
                can_vectorize = bool(keep_group_mask.all().item())
                if can_vectorize:
                    s, z, maxq_r = _std_gptq_find_params_weight_perchannel(
                        full_group_vals,
                        bits=int(bits),
                        sym=bool(sym),
                    )
                    s = s.float()
                    z = z.float()
                    maxq_val = float(maxq_r.item())
                else:
                    has_kept = keep_group_mask.any(dim=1)

                    pos_inf = torch.tensor(float("inf"), device=full_group_vals.device, dtype=full_group_vals.dtype)
                    neg_inf = torch.tensor(float("-inf"), device=full_group_vals.device, dtype=full_group_vals.dtype)

                    masked_min = torch.where(keep_group_mask, full_group_vals, pos_inf).amin(dim=1)
                    masked_max = torch.where(keep_group_mask, full_group_vals, neg_inf).amax(dim=1)
                    full_min = full_group_vals.amin(dim=1)
                    full_max = full_group_vals.amax(dim=1)

                    row_min = torch.where(has_kept, masked_min, full_min)
                    row_max = torch.where(has_kept, masked_max, full_max)

                    zero_ref = torch.zeros_like(row_min)
                    xmin = torch.minimum(row_min, zero_ref)
                    xmax = torch.maximum(row_max, zero_ref)

                    if bool(sym):
                        xmax = torch.maximum(torch.abs(xmin), xmax)
                        neg = xmin < 0
                        if bool(neg.any()):
                            xmin = xmin.clone()
                            xmin[neg] = -xmax[neg]

                    zero_span = (xmin == 0) & (xmax == 0)
                    if bool(zero_span.any()):
                        xmin = xmin.clone()
                        xmax = xmax.clone()
                        xmin[zero_span] = -1.0
                        xmax[zero_span] = +1.0

                    maxq_val = float((2 ** int(bits)) - 1)
                    scale = (xmax - xmin) / maxq_val
                    scale = torch.clamp(scale, min=1e-8)
                    if bool(sym):
                        zero = torch.full_like(scale, (maxq_val + 1.0) / 2.0)
                    else:
                        zero = torch.round(-xmin / scale)

                    s = scale.reshape(rows, 1).float()
                    z = zero.reshape(rows, 1).float()

            qparams_by_gid[int(gid)] = (
                s,
                z,
                maxq_val,
            )

        return col_gid, qparams_by_gid

    def _quantize_vector_by_bits(self, x, bits):
        if bits == 2:
            q = quantize_to_2bit_perchannel(x)
        elif bits == 3:
            q = quantize_to_3bit_perchannel(x)
        elif bits == 4:
            q = quantize_to_4bit_perchannel(x)
        elif bits == 8:
            q = quantize_to_8bit_perchannel(x)
        else:
            q = quantize_to_2bit_perchannel(x)
        if isinstance(q, (tuple, list)):
            q = q[0]
        return q.float()

    def fasterquant(
        self,
        percdamp=0.01,
        blocksize=128,
        svd_rank=256,
        svd_enable=False,
        svd_auto_rank_deltae_stop=False,
        svd_lowrank_fp16=False,
        svd_num_iters=1,
        svd_2bit_stages=1,
        svd_2bit_extra_8bit_stage_enable=False,
        svd_2bit_extra_8bit_stage_rank=64,
        svd_binary_refit_enable=False,
        svd_binary_refit_epochs=5,
        svd_binary_refit_fp_epochs=3,
        svd_binary_refit_lr=1e-3,
        svd_binary_refit_min_lr=1e-4,
        svd_binary_refit_weight_decay=1e-5,
        svd_binary_refit_grad_clip=1.0,
        svd_binary_refit_patience=2,
        svd_binary_refit_max_tokens=128,
        svd_2bit_salient_3bit_enable=False,
        svd_2bit_salient_4bit_enable=False,
        svd_2bit_obr_cascade_enable=False,
        svd_2bit_obr_cascade_4bit_ratio=0.1,
        svd_2bit_obr_cascade_3bit_ratio=0.1,
        svd_2bit_obr_twogroup_enable=False,
        svd_2bit_obr_twogroup_4bit_ratio=0.1,
        svd_2bit_obr_twogroup_adaptive_enable=False,
        svd_2bit_obr_twogroup_adaptive_max_stages=3,
        svd_2bit_obr_twogroup_adaptive_e128_threshold=0.2,
        svd_2bit_obr_twogroup_adaptive_base_ratio=0.1,
        svd_2bit_obr_twogroup_adaptive_fixed_4bit_ratio=False,
        svd_2bit_obr_twogroup_adaptive_linked_ratio_no_floor=False,
        svd_2bit_obr_4group_enable=False,
        svd_2bit_obr_4group_4bit_ratio=0.1,
        svd_2bit_obr_4group_2bit_ratio_1=0.3,
        svd_2bit_obr_4group_2bit_ratio_2=0.3,
        svd_2bit_obr_4group_non4bit_scheme="order2",
        svd_2bit_obr_ternary_delta_factor=0.7,
        svd_obr_interblock_gptq_propagation_disable=False,
        svd_obr_cascade_lowrank_8bit_enable=False,
        svd_obr_cascade_lowrank_gamma=1.0,
        svd_obr_cascade_lowrank_damp=0.01,
        svd_2bit_salient_3bit_up_lim=50,
        svd_2bit_salient_3bit_ratio=0.1,
        svd_2bit_salient_4bit_alpha=0.4,
        svd_2bit_salient_4bit_adaptive=False,
        svd_early_stop=True,
        use_bass=False,
        bass_pool_factor=None,
        bass_batch_size=None,
        bass_selection_mode="greedy",
        bass_proxy_metric="linf",
        disable_salient_mask=False,
        row_wise_split=False,
        column=False,
        quant_method="2bit",
        obr=False,
        binary_residual=False,
        svd_drop_residual=False,
        smoothquant_enable=False,
        smoothquant_alpha=0.5,
        smoothquant_beta=-1,
        smoothquant_span_mode="absmax",
        salient_first_enable=False,
        salient_first_ratio=0.1,
        non_salient_svd_rank=512,
        bias_correction=False,
        linf_sigma_weight=1.0,
        linf_vh_weight=1.0,
        svd_one_opt=False,
        svd_r_first=False,
        svd_r_first_refit_l=False,
        structure_prune=False,
        prune_n=4,
        prune_m=8,
        rotation=False,
        svd_energy_stats_enable=False,
        svd_energy_probe_rank=128,
        svd_energy_thresholds=(0.9,),
        svd_bit_stats_enable=False,
        svd_bit_stats_scale_bits=16,
        svd_bit_stats_zp_bits=8,
        svd_bit_stats_binary_data_bits=2.0,
        svd_lwc_enable=False,
        svd_lwc_candidates=(1.0, 0.999, 0.995, 0.99, 0.98),
        svd_row_prune_search_enable=False,
        svd_row_prune_m_candidates=(0, 4, 8, 16, 32, 64),
        svd_row_prune_score_metric="magnitude",
        svd_row_prune_binary_order=2,
        svd_row_prune_quant_scheme="binary",
        svd_row_prune_clip_search_enable=False,
        svd_row_prune_clip_candidates=(1.0, 0.999, 0.995, 0.99, 0.98, 0.96),
        svd_row_prune_clip_min_value=1e-8,
        svd_row_prune_act_topk=3,
        svd_row_prune_offline_refill_enable=False,
        svd_row_prune_offline_refill_sweeps=1,
        svd_row_prune_offline_refill_max_positions=-1,
        svd_row_prune_offline_refill_include_zero=True,
        svd_then_pure_gptq=False,
        pure_gptq=False,
        gptq_groupsize=-1,
        gptq_static_groups=False,
        gptq_act_order=False,
        gptq_sym=False,
        gptq2bit_prune_search_enable=False,
        gptq2bit_prune_m_candidates=tuple(range(0, 97, 4)),
        gptq3bit_prune_search_enable=False,
        gptq3bit_prune_m_candidates=tuple(range(0, 97, 4)),
        block_gptq_enable=False,
        block_gptq_static_groups=True,
        post_gptq_refill_enable=False,
        post_gptq_refill_row_ratio=0.2,
        post_gptq_refill_pos_ratio=0.2,
        in_gptq_refill_enable=False,
        in_gptq_refill_row_ratio=0.2,
        in_gptq_refill_pos_ratio=0.2,
        search_trial_mode=False,
        **unused_kwargs,
    ):
        W = self.layer.weight.data.clone()
        if isinstance(self.layer, nn.Conv2d):
            W = W.flatten(1)
        if isinstance(self.layer, transformers.Conv1D):
            W = W.t()
        W = W.float()

        tick = time.time()
        trial_mode = bool(search_trial_mode)

        if self.nsamples <= 0:
            H_real = torch.eye(self.columns, device=W.device, dtype=W.dtype)
        else:
            # add_batch already follows GPTQ reference accumulation scaling.
            # Do not divide by nsamples again here, otherwise activation error is under-scaled.
            H_real = self.H.float()

        # Match reference GPTQ dead-column behavior.
        dead = torch.diag(H_real) == 0
        if bool(dead.any()):
            W[:, dead] = 0.0

        H_orig = H_real.clone()
        H_for_gptq = H_real.clone()
        if bool(dead.any()):
            H_for_gptq[dead, dead] = 1.0

        quant_method = str(quant_method).strip().lower()
        if quant_method.endswith("bit") and len(quant_method) >= 1 and quant_method[0].isdigit():
            qbits = int(quant_method[0])
        else:
            raise ValueError(
                f"Invalid quant_method='{quant_method}'. Expected one of: 2bit, 3bit, 4bit, 8bit."
            )
        if qbits not in (2, 3, 4, 8):
            raise ValueError(
                f"Unsupported quant_method='{quant_method}' (qbits={qbits}). "
                "Expected one of: 2bit, 3bit, 4bit, 8bit."
            )

        pure_gptq = bool(pure_gptq)
        std_gptq_enable = bool(unused_kwargs.pop("std_gptq_enable", block_gptq_enable))
        std_gptq_static_groups = bool(
            unused_kwargs.pop("std_gptq_static_groups", block_gptq_static_groups)
        )
        block_gptq_enable = bool(block_gptq_enable or std_gptq_enable or pure_gptq)
        block_gptq_static_groups = bool(std_gptq_static_groups)
        if pure_gptq:
            logger.warning(
                "pure_gptq is deprecated and now routed to std_gptq (column-wise compensated GPTQ)."
            )

        selected_svd_rank = int(svd_rank)
        auto_rank_trace = []
        L_quantized = torch.zeros_like(W)
        lowrank_stage_specs = []

        if bool(svd_enable):
            if bool(svd_auto_rank_deltae_stop):
                selected_svd_rank, auto_rank_trace = self._search_single_svd_rank_by_delta_norm_error(
                    W=W,
                    H=H_orig,
                    svd_lowrank_fp16=bool(svd_lowrank_fp16),
                    start_rank=max(1, min(16, int(svd_rank))),
                    rank_step=16,
                    delta_norm_threshold=0.05,
                )
            selected_svd_rank = max(1, int(selected_svd_rank))
            L, _, proj_down, proj_up = self._svd_decompose(W, rank=selected_svd_rank)
            if bool(svd_lowrank_fp16):
                L_quantized = self._compose_lowrank_fp16(proj_down, proj_up).float()
                lowrank_bits = 16.0
            else:
                L_quantized = self._quantize_lowrank_4bit(proj_down, proj_up).float()
                lowrank_bits = 4.0
            lowrank_stage_specs = [{"rank": int(selected_svd_rank), "bits": float(lowrank_bits)}]
            R_target = (W - L_quantized).float()
        else:
            R_target = W.clone().float()

        gptq_perm = None
        gptq_invperm = None
        if bool(gptq_act_order):
            # Match reference GPTQ order: permute H first, then build inverse factor.
            d = torch.diag(H_for_gptq)
            gptq_perm = torch.argsort(d, descending=True)
            gptq_invperm = torch.argsort(gptq_perm)
            H_perm = H_for_gptq[gptq_perm][:, gptq_perm]
            H_work, Hinv_work = self._safe_hinv(H_perm, percdamp=percdamp)
            R_work = R_target[:, gptq_perm].clone()
        else:
            H_work, Hinv_work = self._safe_hinv(H_for_gptq, percdamp=percdamp)
            R_work = R_target.clone()

        use_block_gptq_row_prune = bool(block_gptq_enable and svd_row_prune_search_enable)
        row_prune_score_metric = str(svd_row_prune_score_metric).strip().lower()
        if row_prune_score_metric not in {"magnitude", "wanda"}:
            raise ValueError(
                f"Unsupported svd_row_prune_score_metric='{row_prune_score_metric}'. "
                "Expected one of: magnitude/wanda."
            )
        in_gptq_refill_enable = bool(in_gptq_refill_enable)
        post_gptq_refill_enable = bool(post_gptq_refill_enable)
        in_gptq_refill_row_ratio = min(max(float(in_gptq_refill_row_ratio), 0.0), 1.0)
        in_gptq_refill_pos_ratio = min(max(float(in_gptq_refill_pos_ratio), 0.0), 1.0)
        post_gptq_refill_row_ratio = min(max(float(post_gptq_refill_row_ratio), 0.0), 1.0)
        post_gptq_refill_pos_ratio = min(max(float(post_gptq_refill_pos_ratio), 0.0), 1.0)
        if in_gptq_refill_enable and post_gptq_refill_enable:
            raise ValueError(
                "in_gptq_refill_enable and post_gptq_refill_enable are mutually exclusive."
            )
        if in_gptq_refill_enable and (not use_block_gptq_row_prune):
            logger.warning(
                "in-GPTQ refill requires row-prune 2-pass path. Disabling in_gptq_refill_enable."
            )
            in_gptq_refill_enable = False
        if in_gptq_refill_enable and self.act_count <= 0.0:
            logger.warning(
                "in-GPTQ refill requires activation statistics (act_count>0). "
                "Disabling in_gptq_refill_enable."
            )
            in_gptq_refill_enable = False
        if in_gptq_refill_enable:
            # In-GPTQ refill mode uses full refill on all pruned positions.
            # Keep args for backward compatibility but force effective ratios to 1.0.
            if (abs(float(in_gptq_refill_row_ratio) - 1.0) > 1e-12) or (
                abs(float(in_gptq_refill_pos_ratio) - 1.0) > 1e-12
            ):
                logger.info(
                    "in-GPTQ refill: forcing full refill on pruned positions "
                    "(effective row_ratio=1.0, pos_ratio=1.0)."
                )
            in_gptq_refill_row_ratio = 1.0
            in_gptq_refill_pos_ratio = 1.0
        block_groupsize = int(getattr(self.braq_quantizer, "groupsize", -1))
        if block_groupsize == 0 or block_groupsize < -1:
            block_groupsize = -1
        qparam_groupsize = int(gptq_groupsize)
        if qparam_groupsize == 0 or qparam_groupsize < -1:
            raise ValueError(
                f"Invalid gptq_groupsize={qparam_groupsize}. "
                "Expected -1 or a positive integer."
            )
        if qparam_groupsize == -1:
            qparam_groupsize = int(block_groupsize)
        qparam_static_groups = bool(block_gptq_static_groups and (qparam_groupsize != -1))
        if bool(block_gptq_static_groups) and (qparam_groupsize == -1):
            raise ValueError(
                "std_gptq static groups requested but resolved groupsize=-1. "
                "Set --gptq_groupsize to a positive integer when using static groups."
            )

        if bool(block_gptq_enable):
            logger.info(
                "Block-GPTQ mode enabled: standard GPTQ column-wise update "
                f"(wbits={int(qbits)}, groupsize={int(qparam_groupsize)}, "
                f"act_order={bool(gptq_act_order)}, static_groups={bool(qparam_static_groups)})."
            )

        iterative_enable_cfg = bool(getattr(self.braq_quantizer, "iterative_2bit_enable", True))
        iterative_iters_cfg = int(getattr(self.braq_quantizer, "iterative_2bit_iters", 5))
        iterative_fixed_cfg = bool(getattr(self.braq_quantizer, "iterative_2bit_fixed_iters", False))

        if bool(block_gptq_enable) and int(qbits) in (2, 3, 4):
            if not iterative_enable_cfg:
                raise ValueError(
                    f"std_gptq {int(qbits)}bit requires iterative affine quantization; "
                    "disable_iterative_2bit is not allowed."
                )
            logger.info(
                f"Block-GPTQ {int(qbits)}bit qparams: iterative affine enabled "
                f"(iters={int(iterative_iters_cfg)}, fixed_iters={bool(iterative_fixed_cfg)})."
            )

        if use_block_gptq_row_prune:
            score_rule_desc = (
                "prune smallest |w| per row"
                if row_prune_score_metric == "magnitude"
                else "prune smallest WANDA score per row (|w|*sqrt(E[x^2]))"
            )
            logger.info(
                "Block-GPTQ row-prune search enabled for residual quantization: "
                f"candidate m per row={list(svd_row_prune_m_candidates)}, "
                "objective=L(m)=sum((R_b-Q_b)^2) on ORIGINAL residual block, "
                f"mask rule={score_rule_desc}, "
                f"selection=weight reconstruction objective only (act_topk={int(svd_row_prune_act_topk)}), "
                f"offline refill={'enabled' if bool(svd_row_prune_offline_refill_enable) else 'disabled'}."
            )
            logger.info(
                "Block-GPTQ row-prune two-pass pipeline: "
                f"pass1=mask search (no GPTQ, quant_scheme={str(svd_row_prune_quant_scheme).strip().lower()}), "
                "pass2=fixed-mask Block-GPTQ."
            )
            if in_gptq_refill_enable:
                logger.info(
                    "In-GPTQ refill enabled (inside GPTQ column loop): "
                    f"row_ratio={float(in_gptq_refill_row_ratio):.4f}, "
                    f"pos_ratio={float(in_gptq_refill_pos_ratio):.4f}. "
                    "This mode is mutually exclusive with post-GPTQ refill."
                )
            elif post_gptq_refill_enable:
                logger.info(
                    "Post-GPTQ refill enabled (after GPTQ loop): "
                    f"row_ratio={float(post_gptq_refill_row_ratio):.4f}, "
                    f"pos_ratio={float(post_gptq_refill_pos_ratio):.4f}."
                )

        row_prune_kept_weight_count = 0.0
        row_prune_pruned_weight_count = 0.0
        block_gptq_row_pruned_mask_plan = {}
        row_prune_keep_mask_plan = {}
        row_prune_pass1_stats = []
        row_prune_pass1_stats_by_block = {}
        in_gptq_refill_mask_plan = {}
        in_gptq_refill_selected_count = 0.0
        in_gptq_refill_candidate_count = 0.0
        block_gptq_col_group_id = torch.full((self.columns,), -1, device=R_work.device, dtype=torch.long)
        block_gptq_group_qparams_by_id = {}
        next_gid = 0

        R_quantized = torch.zeros_like(R_work)
        W_progress = R_work.clone()
        R_static_for_qparams = R_work.clone() if qparam_static_groups else None
        global_static_col_gid = None

        # Standard GPTQ semantics:
        # with act-order + static-groups, group assignment is based on original column order.
        if qparam_static_groups and (not use_block_gptq_row_prune):
            static_src = R_target.float() if (bool(gptq_act_order) and (gptq_perm is not None)) else R_work.float()
            static_keep = torch.ones_like(static_src, dtype=torch.bool)
            global_static_col_gid, global_static_qparams = self._compute_group_qparams(
                src_block=static_src,
                keep_mask_block=static_keep,
                bits=int(qbits),
                groupsize=qparam_groupsize,
                sym=bool(gptq_sym),
            )
            block_gptq_group_qparams_by_id = {
                int(gid): qparam for gid, qparam in global_static_qparams.items()
            }
            next_gid = int(global_static_col_gid.max().item()) + 1 if global_static_col_gid.numel() > 0 else 0

        block_starts = list(range(0, self.columns, int(blocksize)))
        blocksize_int = int(blocksize)
        dynamic_group_gid_by_start = {}
        row_prune_wanda_col_score = None
        if use_block_gptq_row_prune and row_prune_score_metric == "wanda":
            if self.act_count <= 0.0:
                raise ValueError(
                    "svd_row_prune_score_metric=wanda requires valid activation statistics (act_count>0)."
                )
            row_prune_wanda_col_score = torch.sqrt(
                torch.clamp(
                    (self.act_square_sum / max(self.act_count, 1.0)).float(),
                    min=0.0,
                )
            ).to(device=R_work.device, dtype=torch.float32)
            if bool(gptq_act_order) and (gptq_perm is not None):
                row_prune_wanda_col_score = row_prune_wanda_col_score[gptq_perm]

        def _get_keep_mask_for_global_slice(col_start, col_end):
            # Build keep-mask for an arbitrary global column slice.
            # Needed by dynamic_groups so qparams can be refreshed per group boundary.
            col_start = int(col_start)
            col_end = int(col_end)
            if col_end <= col_start:
                return torch.zeros((self.rows, 0), device=R_work.device, dtype=torch.bool)
            if not use_block_gptq_row_prune:
                return torch.ones((self.rows, col_end - col_start), device=R_work.device, dtype=torch.bool)

            parts = []
            cur = col_start
            while cur < col_end:
                blk_idx = int(cur // blocksize_int)
                blk_st = int(blk_idx * blocksize_int)
                blk_ed = int(min(blk_st + blocksize_int, self.columns))
                seg_ed = int(min(col_end, blk_ed))
                seg_w = int(seg_ed - cur)

                blk_keep = row_prune_keep_mask_plan.get(int(blk_idx), None)
                if isinstance(blk_keep, torch.Tensor) and blk_keep.ndim == 2 and int(blk_keep.shape[0]) == int(self.rows):
                    local_st = int(cur - blk_st)
                    local_ed = int(seg_ed - blk_st)
                    seg_keep = blk_keep[:, local_st:local_ed].bool()
                    if int(seg_keep.shape[1]) != seg_w:
                        seg_keep = torch.ones((self.rows, seg_w), device=R_work.device, dtype=torch.bool)
                else:
                    seg_keep = torch.ones((self.rows, seg_w), device=R_work.device, dtype=torch.bool)

                parts.append(seg_keep.to(device=R_work.device))
                cur = seg_ed

            if len(parts) == 1:
                return parts[0]
            return torch.cat(parts, dim=1)

        if use_block_gptq_row_prune:
            pass1_tick = time.time()
            for blocki, col_st in enumerate(block_starts):
                col_ed = min(col_st + int(blocksize), self.columns)
                src_block_target = R_work[:, col_st:col_ed].float()
                hinv_block = Hinv_work[col_st:col_ed, col_st:col_ed].float()
                h_block = H_work[col_st:col_ed, col_st:col_ed].float()
                n_cols = int(col_ed - col_st)

                keep_mask = torch.ones_like(src_block_target, dtype=torch.bool)
                col_score_block = (
                    row_prune_wanda_col_score[col_st:col_ed]
                    if row_prune_wanda_col_score is not None
                    else None
                )
                _, rp_info = self._search_row_prune_m_for_binary_block(
                    r_block=src_block_target,
                    candidate_ms=svd_row_prune_m_candidates,
                    score_metric=row_prune_score_metric,
                    col_score=col_score_block,
                    order=int(svd_row_prune_binary_order),
                    quant_scheme=str(svd_row_prune_quant_scheme),
                    clip_search_enable=bool(svd_row_prune_clip_search_enable),
                    clip_candidates=svd_row_prune_clip_candidates,
                    clip_min_value=float(svd_row_prune_clip_min_value),
                    h_block=h_block,
                    act_topk=int(svd_row_prune_act_topk),
                    # Search stage: no GPTQ compensation, pure reconstruction objective.
                    column_compensate=False,
                    h_inv_block=hinv_block,
                )
                keep_mask = rp_info.get("best_keep_mask", keep_mask)
                if not isinstance(keep_mask, torch.Tensor):
                    keep_mask = torch.ones_like(src_block_target, dtype=torch.bool)
                keep_mask = keep_mask.bool()

                row_prune_keep_mask_plan[int(blocki)] = keep_mask.clone()

                best_m = int(rp_info.get("best_m", 0))
                prune_ratio = float(rp_info.get("best_prune_ratio", 0.0))
                if not math.isfinite(prune_ratio):
                    prune_ratio = float(best_m / max(n_cols, 1))
                avg_iter = float(rp_info.get("best_avg_iter", 0.0))
                weight_loss_sum = float(rp_info.get("best_weight_loss_sum", 0.0))

                pass1_item = {
                    "block": int(blocki),
                    "n_cols": int(n_cols),
                    "best_m": int(best_m),
                    "prune_ratio": float(prune_ratio),
                    "avg_iter": float(avg_iter),
                    "weight_loss_sum": float(weight_loss_sum),
                }
                row_prune_pass1_stats.append(pass1_item)
                row_prune_pass1_stats_by_block[int(blocki)] = pass1_item

                logger.info(
                    f"  [Pass1][Block {int(blocki)}] best_m={int(best_m)}/{int(n_cols)}, "
                    f"prune_ratio={float(prune_ratio) * 100.0:.2f}%, "
                    f"avg_iter={float(avg_iter):.2f}, "
                    f"weight_loss_sum={float(weight_loss_sum):.6e}"
                )

            pass1_time = time.time() - pass1_tick
            if len(row_prune_pass1_stats) > 0:
                avg_prune_ratio = float(
                    sum(item["prune_ratio"] for item in row_prune_pass1_stats) / len(row_prune_pass1_stats)
                )
                avg_iter = float(
                    sum(item["avg_iter"] for item in row_prune_pass1_stats) / len(row_prune_pass1_stats)
                )
                avg_weight_loss_sum = float(
                    sum(item["weight_loss_sum"] for item in row_prune_pass1_stats) / len(row_prune_pass1_stats)
                )
                logger.info(
                    f"  [Pass1][Summary] blocks={len(row_prune_pass1_stats)}, "
                    f"avg_prune_ratio={avg_prune_ratio * 100.0:.2f}%, "
                    f"avg_iter={avg_iter:.2f}, "
                    f"avg_weight_loss_sum={avg_weight_loss_sum:.6e}, "
                    f"time={pass1_time:.4f}s"
                )

                row_prune_quant_scheme = str(svd_row_prune_quant_scheme).strip().lower()
                if iterative_enable_cfg and row_prune_quant_scheme in {"std2bit", "std3bit", "std4bit"}:
                    if iterative_fixed_cfg:
                        mismatch_blocks = [
                            int(item["block"])
                            for item in row_prune_pass1_stats
                            if abs(float(item["avg_iter"]) - float(iterative_iters_cfg)) > 0.05
                        ]
                        if len(mismatch_blocks) > 0:
                            logger.warning(
                                "  [Pass1][IterCheck] fixed_iters mismatch detected: "
                                f"target_iters={int(iterative_iters_cfg)}, "
                                f"mismatch_blocks={mismatch_blocks}"
                            )
                        else:
                            logger.info(
                                "  [Pass1][IterCheck] fixed_iters check passed: "
                                f"target_iters={int(iterative_iters_cfg)}, "
                                f"observed_avg_iter={avg_iter:.2f}."
                            )
                    else:
                        logger.info(
                            "  [Pass1][IterCheck] iterative affine enabled with early-stop: "
                            f"configured_min_iters={int(iterative_iters_cfg)}, "
                            f"observed_avg_iter={avg_iter:.2f}."
                        )

        if in_gptq_refill_enable and use_block_gptq_row_prune:
            # Full refill mode: directly refill all row-pruned positions inside GPTQ loop.
            for blocki_refill, _ in enumerate(block_starts):
                keep_mask_blk = row_prune_keep_mask_plan.get(int(blocki_refill), None)
                if not isinstance(keep_mask_blk, torch.Tensor):
                    continue
                keep_mask_blk = keep_mask_blk.bool()
                if keep_mask_blk.numel() == 0:
                    continue

                refill_mask_blk = ~keep_mask_blk
                refill_count = float(refill_mask_blk.sum().item())
                in_gptq_refill_candidate_count += refill_count
                in_gptq_refill_selected_count += refill_count
                if refill_count > 0.0:
                    in_gptq_refill_mask_plan[int(blocki_refill)] = refill_mask_blk

            logger.info(
                "  [In-GPTQ Refill][Plan] "
                f"selected={int(in_gptq_refill_selected_count)}/{int(in_gptq_refill_candidate_count)} "
                f"({(100.0 * in_gptq_refill_selected_count / max(in_gptq_refill_candidate_count, 1.0)):.2f}%), "
                f"blocks_with_refill={len(in_gptq_refill_mask_plan)}."
            )

        residual_quant_tick = time.time()
        for blocki, col_st in enumerate(block_starts):
            col_ed = min(col_st + int(blocksize), self.columns)
            src_block_target = R_work[:, col_st:col_ed].float()
            hinv_block = Hinv_work[col_st:col_ed, col_st:col_ed].float()
            n_cols = int(col_ed - col_st)

            keep_mask = torch.ones_like(src_block_target, dtype=torch.bool)
            if use_block_gptq_row_prune:
                keep_mask = row_prune_keep_mask_plan.get(int(blocki), keep_mask)
                if not isinstance(keep_mask, torch.Tensor):
                    keep_mask = torch.ones_like(src_block_target, dtype=torch.bool)
                keep_mask = keep_mask.bool()

            refill_mask = torch.zeros_like(keep_mask, dtype=torch.bool)
            if in_gptq_refill_enable and use_block_gptq_row_prune:
                refill_mask = in_gptq_refill_mask_plan.get(int(blocki), refill_mask)
                if not isinstance(refill_mask, torch.Tensor):
                    refill_mask = torch.zeros_like(keep_mask, dtype=torch.bool)
                refill_mask = refill_mask.bool()
                if refill_mask.shape != keep_mask.shape:
                    refill_mask = torch.zeros_like(keep_mask, dtype=torch.bool)
            active_mask = keep_mask | refill_mask

            block_gptq_row_pruned_mask_plan[int(blocki)] = (~active_mask).clone()
            kept_now = float(active_mask.sum().item())
            total_now = float(active_mask.numel())
            row_prune_kept_weight_count += kept_now
            row_prune_pruned_weight_count += max(total_now - kept_now, 0.0)

            if qparam_static_groups and (global_static_col_gid is not None) and (not use_block_gptq_row_prune):
                if bool(gptq_act_order) and (gptq_perm is not None):
                    orig_cols = gptq_perm[col_st:col_ed]
                    block_gptq_col_group_id[col_st:col_ed] = global_static_col_gid[orig_cols]
                else:
                    block_gptq_col_group_id[col_st:col_ed] = global_static_col_gid[col_st:col_ed]
            elif qparam_static_groups:
                # Row-prune + static-groups: keep fixed qparams computed from a static snapshot.
                src_block_for_qparams = (
                    R_static_for_qparams[:, col_st:col_ed].float()
                    if R_static_for_qparams is not None
                    else W_progress[:, col_st:col_ed].float()
                )
                col_gid_local, qparams_local = self._compute_group_qparams(
                    src_block=src_block_for_qparams,
                    keep_mask_block=keep_mask,
                    bits=int(qbits),
                    groupsize=qparam_groupsize,
                    sym=bool(gptq_sym),
                )

                for local_idx in range(n_cols):
                    gid_local = int(col_gid_local[local_idx].item())
                    gid_global = next_gid + gid_local
                    block_gptq_col_group_id[col_st + local_idx] = int(gid_global)

                for gid_local, qparam in qparams_local.items():
                    gid_global = int(next_gid + int(gid_local))
                    block_gptq_group_qparams_by_id[gid_global] = qparam

                next_gid += max(int(col_gid_local.max().item()) + 1, 1)
            # Dynamic-groups path intentionally does not precompute qparams here.
            # To match standard GPTQ semantics, qparams are refreshed in the column
            # loop whenever entering a new quantization group boundary.

            W1 = W_progress[:, col_st:col_ed].clone()
            Q1 = torch.zeros_like(src_block_target)
            Err1 = torch.zeros_like(src_block_target)
            maxq_tensor_cache = {}

            for j in range(n_cols):
                global_col = int(col_st + j)

                if not qparam_static_groups:
                    if qparam_groupsize == -1:
                        group_st = 0
                        group_ed = int(self.columns)
                        at_group_boundary = (global_col == 0)
                    else:
                        group_st = int((global_col // int(qparam_groupsize)) * int(qparam_groupsize))
                        group_ed = int(min(group_st + int(qparam_groupsize), int(self.columns)))
                        at_group_boundary = (global_col % int(qparam_groupsize) == 0)

                    need_refresh = bool(
                        at_group_boundary
                        or (group_st not in dynamic_group_gid_by_start)
                    )
                    if need_refresh:
                        gid_dyn = dynamic_group_gid_by_start.get(group_st, None)
                        if gid_dyn is None:
                            gid_dyn = int(next_gid)
                            dynamic_group_gid_by_start[group_st] = int(gid_dyn)
                            next_gid += 1

                        src_group_for_qparams = W_progress[:, group_st:group_ed].float()
                        keep_group_for_qparams = _get_keep_mask_for_global_slice(group_st, group_ed)
                        _, qparams_dyn = self._compute_group_qparams(
                            src_block=src_group_for_qparams,
                            keep_mask_block=keep_group_for_qparams,
                            bits=int(qbits),
                            groupsize=-1,
                            sym=bool(gptq_sym),
                        )
                        if 0 in qparams_dyn:
                            block_gptq_group_qparams_by_id[int(gid_dyn)] = qparams_dyn[0]
                        else:
                            block_gptq_group_qparams_by_id[int(gid_dyn)] = next(iter(qparams_dyn.values()))
                        block_gptq_col_group_id[group_st:group_ed] = int(gid_dyn)

                gid = int(block_gptq_col_group_id[global_col].item())
                scale, zero, maxq = block_gptq_group_qparams_by_id[gid]

                w_col = W1[:, j:j + 1]
                maxq_t = maxq_tensor_cache.get(gid, None)
                if maxq_t is None:
                    maxq_t = torch.tensor(maxq, device=w_col.device, dtype=w_col.dtype)
                    maxq_tensor_cache[gid] = maxq_t
                keep_col = active_mask[:, j]
                q_col = _std_gptq_quantize(w_col, scale, zero, maxq_t)
                q_col = q_col.float().reshape(-1)
                q_col = q_col * keep_col.float()
                Q1[:, j] = q_col

                if (not self.disable_gptq) and (not bool(obr)):
                    d = torch.clamp(hinv_block[j, j], min=1e-8)
                    err_col = (W1[:, j] - q_col) / d
                    W1[:, j:] -= err_col.unsqueeze(1).matmul(hinv_block[j, j:].unsqueeze(0))
                    Err1[:, j] = err_col

            R_quantized[:, col_st:col_ed] = Q1.float()

            if col_ed < self.columns and (not self.disable_gptq) and (not bool(obr)):
                W_progress[:, col_ed:] -= Err1.matmul(Hinv_work[col_st:col_ed, col_ed:])

        residual_quant_time = time.time() - residual_quant_tick
        if use_block_gptq_row_prune:
            logger.info(f"    [Time] Residual Quantization Loop: {residual_quant_time:.4f}s")
            if len(row_prune_pass1_stats) > 0:
                prune_ratios = [float(item["prune_ratio"]) for item in row_prune_pass1_stats]
                best_ms = [int(item["best_m"]) for item in row_prune_pass1_stats]
                weight_losses = [float(item["weight_loss_sum"]) for item in row_prune_pass1_stats]
                avg_prune = float(sum(prune_ratios) / len(prune_ratios))
                min_prune = float(min(prune_ratios))
                max_prune = float(max(prune_ratios))
                avg_best_m = float(sum(best_ms) / len(best_ms))
                min_best_m = int(min(best_ms))
                max_best_m = int(max(best_ms))
                avg_loss = float(sum(weight_losses) / len(weight_losses))
                min_loss = float(min(weight_losses))
                max_loss = float(max(weight_losses))
                logger.info(
                    f"    [RowPrune Summary] blocks={len(row_prune_pass1_stats)}, "
                    f"prune_ratio(avg/min/max)={avg_prune * 100.0:.2f}/{min_prune * 100.0:.2f}/{max_prune * 100.0:.2f}%, "
                    f"best_m(avg/min/max)={avg_best_m:.2f}/{min_best_m}/{max_best_m}, "
                    f"weight_loss_sum(avg/min/max)={avg_loss:.6e}/{min_loss:.6e}/{max_loss:.6e}"
                )
            if in_gptq_refill_enable:
                logger.info(
                    "    [In-GPTQ Refill] "
                    f"selected={int(in_gptq_refill_selected_count)}/{int(in_gptq_refill_candidate_count)} "
                    f"({(100.0 * in_gptq_refill_selected_count / max(in_gptq_refill_candidate_count, 1.0)):.2f}%), "
                    f"blocks_with_refill={len(in_gptq_refill_mask_plan)}."
                )

        post_gptq_refill_nonzero_count = 0.0
        post_gptq_refill_candidate_count = 0.0
        post_gptq_refill_total_pruned_count = 0.0
        post_gptq_refill_selected_row_count = 0.0
        post_gptq_refill_error_before = 0.0
        post_gptq_refill_error_after = 0.0
        use_post_gptq_refill = bool(post_gptq_refill_enable) and (not bool(in_gptq_refill_enable))
        in_gptq_refill_ratio = 0.0
        if in_gptq_refill_candidate_count > 0.0:
            in_gptq_refill_ratio = float(
                in_gptq_refill_selected_count / max(in_gptq_refill_candidate_count, 1.0)
            )

        if (
            bool(use_post_gptq_refill)
            and bool(block_gptq_enable)
            and bool(use_block_gptq_row_prune)
            and self.act_count > 0.0
        ):
            tick_post = time.time()
            x_mean = (self.act_sum / max(self.act_count, 1.0)).float().to(device=R_quantized.device)
            if bool(gptq_act_order) and (gptq_perm is not None):
                x_mean = x_mean[gptq_perm]

            pruned_mask_all = torch.zeros_like(R_quantized, dtype=torch.bool)
            for blocki_refill, col_st_refill in enumerate(range(0, self.columns, int(blocksize))):
                col_ed_refill = min(col_st_refill + int(blocksize), self.columns)
                blk_mask = block_gptq_row_pruned_mask_plan.get(int(blocki_refill), None)
                if isinstance(blk_mask, torch.Tensor):
                    blk_mask = blk_mask.bool()
                    if blk_mask.shape == pruned_mask_all[:, col_st_refill:col_ed_refill].shape:
                        pruned_mask_all[:, col_st_refill:col_ed_refill] = blk_mask

            post_gptq_refill_total_pruned_count = float(pruned_mask_all.sum().item())

            if (
                post_gptq_refill_total_pruned_count > 0.0
                and float(post_gptq_refill_row_ratio) > 0.0
                and float(post_gptq_refill_pos_ratio) > 0.0
            ):
                err_matrix = (R_target - R_quantized).float()
                row_err = torch.sum(err_matrix * x_mean.reshape(1, -1), dim=1)
                row_abs = row_err.abs()
                valid_rows = torch.where(pruned_mask_all.any(dim=1))[0]

                if valid_rows.numel() > 0:
                    n_select_rows = int(math.ceil(float(valid_rows.numel()) * float(post_gptq_refill_row_ratio)))
                    n_select_rows = min(max(n_select_rows, 1), int(valid_rows.numel()))
                    if n_select_rows < int(valid_rows.numel()):
                        local_idx = torch.topk(row_abs[valid_rows], k=n_select_rows, largest=True).indices
                        selected_rows = valid_rows[local_idx]
                    else:
                        selected_rows = valid_rows

                    post_gptq_refill_selected_row_count = float(selected_rows.numel())
                    post_gptq_refill_error_before = float(row_abs[selected_rows].sum().item())

                    codebook_cache = {}

                    def _get_row_codebook(row_idx, gid):
                        key = (int(row_idx), int(gid))
                        if key in codebook_cache:
                            return codebook_cache[key]
                        qparam = block_gptq_group_qparams_by_id.get(int(gid), None)
                        if not (
                            isinstance(qparam, tuple)
                            and len(qparam) == 3
                            and isinstance(qparam[0], torch.Tensor)
                            and isinstance(qparam[1], torch.Tensor)
                        ):
                            return None
                        scale_all, zero_all, maxq_val = qparam
                        if int(row_idx) >= int(scale_all.shape[0]) or int(row_idx) >= int(zero_all.shape[0]):
                            return None
                        maxq_i = max(int(round(float(maxq_val))), 0)
                        q_levels = torch.arange(maxq_i + 1, device=R_quantized.device, dtype=torch.float32)
                        scale_r = scale_all[int(row_idx), 0].to(device=R_quantized.device, dtype=torch.float32)
                        zero_r = zero_all[int(row_idx), 0].to(device=R_quantized.device, dtype=torch.float32)
                        values = scale_r * (q_levels - zero_r)
                        max_abs_val = float(values.abs().max().item()) if values.numel() > 0 else 0.0
                        codebook_cache[key] = (values, max_abs_val)
                        return codebook_cache[key]

                    for row_idx in selected_rows.tolist():
                        pruned_cols = torch.where(pruned_mask_all[row_idx])[0]
                        if pruned_cols.numel() == 0:
                            continue

                        proxy_triplets = []
                        for col_idx_t in pruned_cols.tolist():
                            gid = int(block_gptq_col_group_id[col_idx_t].item())
                            if gid < 0:
                                continue
                            codebook = _get_row_codebook(row_idx, gid)
                            if codebook is None:
                                continue
                            _, max_abs_code = codebook
                            proxy = float(max_abs_code) * abs(float(x_mean[col_idx_t].item()))
                            proxy_triplets.append((proxy, int(col_idx_t), gid))

                        if len(proxy_triplets) == 0:
                            continue

                        proxy_triplets.sort(key=lambda x: x[0], reverse=True)
                        n_select_pos = int(math.ceil(float(len(proxy_triplets)) * float(post_gptq_refill_pos_ratio)))
                        n_select_pos = min(max(n_select_pos, 1), len(proxy_triplets))
                        selected_pos = proxy_triplets[:n_select_pos]

                        e_row = float(row_err[row_idx].item())
                        for _, col_idx_t, gid in selected_pos:
                            xj = float(x_mean[col_idx_t].item())
                            if abs(xj) <= 1e-12:
                                continue
                            codebook = _get_row_codebook(row_idx, gid)
                            if codebook is None:
                                continue
                            code_vals = codebook[0]
                            if code_vals.numel() == 0:
                                continue

                            post_gptq_refill_candidate_count += 1.0
                            cur_abs = abs(e_row)
                            cand_abs = torch.abs(code_vals - (e_row / xj))
                            best_idx = int(torch.argmin(cand_abs).item())
                            best_c = float(code_vals[best_idx].item())
                            new_abs = abs(e_row - best_c * xj)
                            if new_abs + 1e-12 < cur_abs:
                                R_quantized[row_idx, col_idx_t] = best_c
                                e_row = e_row - (best_c * xj)
                                if abs(best_c) > 1e-12:
                                    post_gptq_refill_nonzero_count += 1.0
                        row_err[row_idx] = e_row

                    post_gptq_refill_error_after = float(row_err[selected_rows].abs().sum().item())

                    if post_gptq_refill_nonzero_count > 0.0:
                        row_prune_kept_weight_count += float(post_gptq_refill_nonzero_count)
                        row_prune_pruned_weight_count = max(
                            float(row_prune_pruned_weight_count) - float(post_gptq_refill_nonzero_count),
                            0.0,
                        )
                    else:
                        logger.info(
                            "  [Post-GPTQ Refill] searched candidates but accepted nonzero refill count is 0, skip applying refill stats update."
                        )

            refill_ratio = 0.0
            if post_gptq_refill_candidate_count > 0.0:
                refill_ratio = float(post_gptq_refill_nonzero_count / max(post_gptq_refill_candidate_count, 1.0))
            logger.info(
                "  [Post-GPTQ Refill] "
                f"time={time.time() - tick_post:.4f}s, "
                f"selected_rows={int(post_gptq_refill_selected_row_count)}, "
                f"refilled_nonzero={int(post_gptq_refill_nonzero_count)}/{int(post_gptq_refill_candidate_count)} "
                f"({refill_ratio * 100:.2f}%), "
                f"total_pruned={int(post_gptq_refill_total_pruned_count)}, "
                f"row_abs_error_before={float(post_gptq_refill_error_before):.6e}, "
                f"row_abs_error_after={float(post_gptq_refill_error_after):.6e}"
            )

        if bool(gptq_act_order) and gptq_invperm is not None:
            R_quantized = R_quantized[:, gptq_invperm]

        if bool(svd_enable):
            W_quantized = (L_quantized + R_quantized).float()
        else:
            W_quantized = R_quantized.float()

        delta_W = (W - W_quantized).float()
        layer_error = float(torch.sum(delta_W * delta_W).item())
        activation_error = float(torch.sum((delta_W @ H_orig) * delta_W).item())
        if activation_error < 0 and abs(activation_error) < 1e-9:
            activation_error = 0.0

        if not trial_mode:
            W_store = W_quantized
            if isinstance(self.layer, transformers.Conv1D):
                W_store = W_store.t()
            self.layer.weight.data = W_store.reshape(self.layer.weight.shape).to(self.layer.weight.data.dtype)

        total_weights = float(max(self.rows * self.columns, 1))
        kept_weights = float(min(max(row_prune_kept_weight_count, 0.0), total_weights))
        pruned_weights = float(min(max(row_prune_pruned_weight_count, 0.0), total_weights))

        if not use_block_gptq_row_prune:
            kept_weights = total_weights
            pruned_weights = 0.0

        residual_avg_bits = float(qbits) * (kept_weights / total_weights)
        lowrank_avg_bits = 0.0
        for spec in lowrank_stage_specs:
            rank_i = max(int(spec.get("rank", 0)), 0)
            bits_i = float(spec.get("bits", 4.0))
            if rank_i <= 0:
                continue
            lowrank_avg_bits += float(rank_i * (self.rows + self.columns) * bits_i) / total_weights

        layer_avg_weight_bits = residual_avg_bits + lowrank_avg_bits
        layer_residual_pruned_ratio = float(pruned_weights / total_weights)

        nonzero_count = float((torch.abs(W_quantized) > 1e-12).sum().item())
        zero_count = float(max(total_weights - nonzero_count, 0.0))
        nonzero_ratio = float(nonzero_count / total_weights)

        post_gptq_refill_ratio = 0.0
        if post_gptq_refill_candidate_count > 0.0:
            post_gptq_refill_ratio = float(
                post_gptq_refill_nonzero_count / max(post_gptq_refill_candidate_count, 1.0)
            )

        logger.info(
            f"  [Layer Avg Weight Bits] avg_weight_bits={layer_avg_weight_bits:.6f}, "
            f"residual_avg_bits={residual_avg_bits:.6f}, "
            f"lowrank_avg_bits={lowrank_avg_bits:.6f}, "
            f"residual_pruned_ratio={layer_residual_pruned_ratio * 100.0:.2f}%"
        )

        logger.info(f"time {time.time() - tick:.2f}")
        logger.info(f"error (Weight SSE-sum): {layer_error:.4f}")
        logger.info(f"error (Activation Quadratic Error): {activation_error:.4f}")

        return {
            "error": float(layer_error),
            "activation_error": float(activation_error),
            "svd_selected_rank": int(selected_svd_rank),
            "svd_auto_rank_trace": list(auto_rank_trace),
            "svd_energy_trace": [],
            "svd_bit_stats": None,
            "layer_avg_weight_bits": float(layer_avg_weight_bits),
            "layer_avg_residual_bits": float(residual_avg_bits),
            "layer_avg_lowrank_bits": float(lowrank_avg_bits),
            "layer_residual_pruned_ratio": float(layer_residual_pruned_ratio),
            "row_prune_offline_refill_stats": None,
            "layer_nonzero_count": float(nonzero_count),
            "layer_zero_count": float(zero_count),
            "layer_total_weight_count": float(total_weights),
            "layer_nonzero_ratio": float(nonzero_ratio),
            "layer_refillable_pruned_total": float(post_gptq_refill_total_pruned_count),
            "post_gptq_refill_enabled": bool(use_post_gptq_refill and block_gptq_enable and use_block_gptq_row_prune),
            "post_gptq_refill_nonzero_count": float(post_gptq_refill_nonzero_count),
            "post_gptq_refill_candidate_count": float(post_gptq_refill_candidate_count),
            "post_gptq_refill_ratio": float(post_gptq_refill_ratio),
            "post_gptq_refill_total_pruned_count": float(post_gptq_refill_total_pruned_count),
            "post_gptq_refill_selected_row_count": float(post_gptq_refill_selected_row_count),
            "post_gptq_refill_error_before": float(post_gptq_refill_error_before),
            "post_gptq_refill_error_after": float(post_gptq_refill_error_after),
            "in_gptq_refill_enabled": bool(in_gptq_refill_enable and block_gptq_enable and use_block_gptq_row_prune),
            "in_gptq_refill_selected_count": float(in_gptq_refill_selected_count),
            "in_gptq_refill_candidate_count": float(in_gptq_refill_candidate_count),
            "in_gptq_refill_ratio": float(in_gptq_refill_ratio),
        }

    def free(self):
        self.H = None
        self.act_sum = None
        self.act_square_sum = None
        self.smooth_activations = []
        self.inp1 = None
        self.out1 = None
        torch.cuda.empty_cache()
