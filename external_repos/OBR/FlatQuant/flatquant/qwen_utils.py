import math

import torch
import torch.nn as nn

from flatquant.quant_utils import ActivationQuantizer
from flatquant.utils import skip_initialization
from flatquant.function_utils import get_init_scale, get_decompose_dim
from flatquant.trans_utils import SVDSingleTransMatrix, SVDDecomposeTransMatrix
from flatquant.trans_utils import InvSingleTransMatrix, InvDecomposeTransMatrix
from flatquant.flat_linear import FlatQuantizedLinear

from transformers.models.qwen2.modeling_qwen2 import Qwen2MLP, Qwen2Attention, \
                                                     apply_rotary_pos_emb, repeat_kv


# ============================================================
# Qwen3.5 专用 FlatQuant 包装类
# Qwen3.5 使用 GatedDeltaNet 线性注意力机制
# ============================================================

class FlatQuantQwen3MLP(torch.nn.Module):
    """Qwen3.5 MLP FlatQuant 包装（结构与 Qwen2 相同）"""
    def __init__(self, args, module):
        super().__init__()
        self.args = args
        self.hidden_size = module.hidden_size
        self.intermediate_size = module.intermediate_size
        self.act_fn = module.act_fn
        self.up_proj = FlatQuantizedLinear(args, module.up_proj)
        self.gate_proj = FlatQuantizedLinear(args, module.gate_proj)
        self.down_proj = FlatQuantizedLinear(args, module.down_proj)
        self.add_fq_trans()
        self._ori_mode = False
        self._eval_mode = False
        self.diag_init = args.diag_init
        if self.diag_init == "sq_style":
            self.up_smax = torch.ones_like(self.up_proj.linear.weight.abs().max(dim=0)[0]).cuda() * 1e-5
            self.down_smax = torch.ones_like(self.down_proj.linear.weight.abs().max(dim=0)[0]).cuda() * 1e-5

    def add_fq_trans(self):
        if self.args.direct_inv:
            DecomposeTransMatrix = InvDecomposeTransMatrix
        else:
            DecomposeTransMatrix = SVDDecomposeTransMatrix
        if self.args.w_bits < 16 or self.args.a_bits < 16:
            up_dim_left, up_dim_right = get_decompose_dim(self.up_proj.linear.weight.shape[1])
            self.up_gate_trans = DecomposeTransMatrix(up_dim_left, up_dim_right, add_diag=self.args.add_diag)
            down_dim_left, down_dim_right = get_decompose_dim(self.down_proj.linear.weight.shape[1])
            self.down_trans = DecomposeTransMatrix(down_dim_left, down_dim_right, add_diag=self.args.add_diag)
        else:
            self.up_gate_trans, self.down_trans = None, None

    def forward(self, x):
        if self._ori_mode:
            return self._ori_forward(x)
        if self._eval_mode:
            # eval 模式：变换已融合进权重，直接用 linear forward
            gate = self.gate_proj.linear(x)
            up = self.up_proj.linear(x)
            gate = self.act_fn(gate)
            return self.down_proj.linear(gate * up)
        if self.up_gate_trans is not None:
            x_ts = self.up_gate_trans(x)
        else:
            x_ts = x
        gate = self.gate_proj(x_ts, qa_trans=self.up_gate_trans)
        up = self.up_proj(x_ts, qa_trans=self.up_gate_trans)
        gate = self.act_fn(gate)
        down_input = gate * up
        if self.down_trans is not None:
            down_input_ts = self.down_trans(down_input)
        else:
            down_input_ts = down_input
        down = self.down_proj(down_input_ts, qa_trans=self.down_trans)
        return down

    def _ori_forward(self, x):
        if self.diag_init == "sq_style" and hasattr(self, "up_smax"):
            self.up_smax = torch.maximum(self.up_smax,
                x.reshape(-1, x.shape[-1]).abs().max(0)[0].clone().detach())
        return self.down_proj._ori_forward(
            self.act_fn(self.gate_proj._ori_forward(x)) * self.up_proj._ori_forward(x))

    def reparameterize(self):
        if self.up_gate_trans is not None:
            self.up_gate_trans.to_eval_mode()
        if self.down_trans is not None:
            self.down_trans.to_eval_mode()
        self.gate_proj.reparameterize(qa_trans=self.up_gate_trans)
        self.up_proj.reparameterize(qa_trans=self.up_gate_trans)
        self.down_proj.reparameterize(qa_trans=self.down_trans)
        if self.up_gate_trans is not None:
            self.up_gate_trans.use_diag = False
        if self.down_trans is not None and self.down_trans.add_diag:
            up_weight = self.up_proj.linear.weight
            ori_dtype = up_weight.dtype
            up_weight = up_weight.to(torch.float64).T.mul(self.down_trans.diag_scale.to(torch.float64)).T
            self.up_proj.linear.weight.data = up_weight.to(ori_dtype)
            self.down_trans.use_diag = False
        self._eval_mode = True

    def init_diag_scale(self, alpha=0.5):
        if not hasattr(self, "up_smax"):
            return
        upw_smax = torch.cat([self.up_proj.linear.weight, self.gate_proj.linear.weight], dim=0).abs().max(dim=0)[0]
        downw_smax = self.down_proj.linear.weight.abs().max(dim=0)[0]
        if self.up_gate_trans is not None:
            self.up_gate_trans.diag_scale.data = get_init_scale(upw_smax, self.up_smax, alpha)
        if self.down_trans is not None:
            self.down_trans.diag_scale.data = get_init_scale(downw_smax, self.down_smax, alpha)
        del self.up_smax, self.down_smax
        self.diag_init = None

    def rep_matrix_only(self):
        if self.up_gate_trans is not None:
            self.up_gate_trans.to_eval_mode()
            self.down_trans.to_eval_mode()


class FlatQuantQwen3Attention(torch.nn.Module):
    """
    Qwen3.5 GatedDeltaNet 线性注意力 FlatQuant 完整包装
    
    GatedDeltaNet 计算流程:
      hidden_states → in_proj_qkv → conv1d → split(q,k,v) → chunk_gated_delta_rule → norm → out_proj
                    → in_proj_z ─────────────────────────────────────────────────────→ norm(gate)
                    → in_proj_b → sigmoid → beta
                    → in_proj_a → softplus → g (decay)
    
    FlatQuant 策略:
      1. ln_trans: 输入变换矩阵，应用在 hidden_states 进入所有投影层之前
      2. out_trans: 输出变换矩阵，应用在 out_proj 之前
      3. 所有 Linear 层用 FlatQuantizedLinear 包装（权重量化+激活量化）
    """
    def __init__(self, args, module):
        super().__init__()
        self.args = args
        
        # 保留原模块的非 Linear 组件
        self.hidden_size = module.hidden_size
        self.num_v_heads = module.num_v_heads
        self.num_k_heads = module.num_k_heads
        self.head_k_dim = module.head_k_dim
        self.head_v_dim = module.head_v_dim
        self.key_dim = module.key_dim
        self.value_dim = module.value_dim
        self.conv_kernel_size = module.conv_kernel_size
        self.layer_idx = module.layer_idx
        self.activation = module.activation
        self.act = module.act
        
        # 非 Linear 组件直接引用
        self.conv1d = module.conv1d
        self.dt_bias = module.dt_bias
        self.A_log = module.A_log
        self.norm = module.norm
        self.causal_conv1d_fn = module.causal_conv1d_fn
        self.causal_conv1d_update = module.causal_conv1d_update
        self.chunk_gated_delta_rule = module.chunk_gated_delta_rule
        self.recurrent_gated_delta_rule = module.recurrent_gated_delta_rule
        
        # 拆分 in_proj_qkv 为独立的 q_proj/k_proj/v_proj
        # 这样 v_proj 可以单独做 vcache_trans 融合（与 Qwen2 对齐）
        orig_qkv_weight = module.in_proj_qkv.weight.data  # [key_dim*2+value_dim, hidden_size]
        q_weight = orig_qkv_weight[:self.key_dim, :]
        k_weight = orig_qkv_weight[self.key_dim:self.key_dim*2, :]
        v_weight = orig_qkv_weight[self.key_dim*2:, :]
        
        q_linear = torch.nn.Linear(self.hidden_size, self.key_dim, bias=False)
        k_linear = torch.nn.Linear(self.hidden_size, self.key_dim, bias=False)
        v_linear = torch.nn.Linear(self.hidden_size, self.value_dim, bias=False)
        q_linear.weight = torch.nn.Parameter(q_weight)
        k_linear.weight = torch.nn.Parameter(k_weight)
        v_linear.weight = torch.nn.Parameter(v_weight)
        
        self.q_proj = FlatQuantizedLinear(args, q_linear)
        self.k_proj = FlatQuantizedLinear(args, k_linear)
        self.v_proj = FlatQuantizedLinear(args, v_linear)
        
        # 其他投影层
        self.in_proj_z = FlatQuantizedLinear(args, module.in_proj_z)
        self.in_proj_b = FlatQuantizedLinear(args, module.in_proj_b)
        self.in_proj_a = FlatQuantizedLinear(args, module.in_proj_a)
        self.out_proj = FlatQuantizedLinear(args, module.out_proj)
        
        # FlatQuant 变换矩阵
        self.add_fq_trans()
        
        # KV/Q 量化器（对应 Qwen2 的 KV cache 量化，应用在 split 后的 q/k/v 上）
        if args.k_bits < 16:
            self.k_quantizer = ActivationQuantizer(bits=args.k_bits, sym=not args.k_asym, lac=args.lac, groupsize=-1)
        if args.v_bits < 16:
            self.v_quantizer = ActivationQuantizer(bits=args.v_bits, sym=not args.v_asym, lac=args.lac, groupsize=-1)
        if args.q_bits < 16:
            self.q_quantizer = ActivationQuantizer(bits=args.q_bits, sym=not args.q_asym, lac=args.lac, groupsize=-1)
        
        self._ori_mode = False
        self._eval_mode = False
        self.diag_init = args.diag_init
        if self.diag_init == "sq_style":
            self.ln_smax = torch.ones(self.hidden_size).cuda() * 1e-5

    def add_fq_trans(self):
        if self.args.direct_inv:
            SingleTransMatrix, DecomposeTransMatrix = InvSingleTransMatrix, InvDecomposeTransMatrix
        else:
            SingleTransMatrix, DecomposeTransMatrix = SVDSingleTransMatrix, SVDDecomposeTransMatrix
        
        if self.args.w_bits < 16 or self.args.a_bits < 16:
            # 输入变换矩阵
            ln_dim_left, ln_dim_right = get_decompose_dim(self.hidden_size)
            self.ln_trans = DecomposeTransMatrix(ln_dim_left, ln_dim_right, add_diag=self.args.add_diag)
            # 输出变换矩阵
            self.out_trans = SingleTransMatrix(self.num_v_heads)
        else:
            self.ln_trans = None
            self.out_trans = None
        
        # kcache_trans: key 变换矩阵（与 Qwen2 对齐）
        if self.args.k_bits < 16 or self.args.q_bits < 16:
            self.kcache_trans = SingleTransMatrix(self.head_k_dim)
        else:
            self.kcache_trans = None
        
        # vcache_trans: value 变换矩阵（与 Qwen2 对齐）
        if self.args.v_bits < 16 or self.args.w_bits < 16 or self.args.a_bits < 16:
            self.vcache_trans = SingleTransMatrix(self.head_v_dim)
        else:
            self.vcache_trans = None

    def _trans_forward_projs(self, hidden_states):
        """应用变换矩阵后执行投影（拆分的 q/k/v）"""
        if self.ln_trans is not None:
            hidden_states_t = self.ln_trans(hidden_states)
        else:
            hidden_states_t = hidden_states
        
        q = self.q_proj(hidden_states_t, qa_trans=self.ln_trans)
        k = self.k_proj(hidden_states_t, qa_trans=self.ln_trans)
        if self.args.separate_vtrans:
            v = self.v_proj(hidden_states_t, qa_trans=self.ln_trans)
        else:
            v = self.v_proj(hidden_states_t, qa_trans=self.ln_trans, out_trans=self.vcache_trans)
        z = self.in_proj_z(hidden_states_t, qa_trans=self.ln_trans)
        b = self.in_proj_b(hidden_states_t, qa_trans=self.ln_trans)
        a = self.in_proj_a(hidden_states_t, qa_trans=self.ln_trans)
        
        # 拼回 mixed_qkv 给 conv1d（conv1d 需要合并的 qkv）
        mixed_qkv = torch.cat([q, k, v], dim=-1)
        return mixed_qkv, z, b, a

    def _ori_forward_projs(self, hidden_states):
        """原始模式投影（用于校准阶段收集激活统计）"""
        if self.diag_init == "sq_style" and hasattr(self, "ln_smax"):
            self.ln_smax = torch.maximum(self.ln_smax,
                hidden_states.reshape(-1, hidden_states.shape[-1]).abs().max(0)[0].clone().detach())
        
        q = self.q_proj._ori_forward(hidden_states)
        k = self.k_proj._ori_forward(hidden_states)
        v = self.v_proj._ori_forward(hidden_states)
        z = self.in_proj_z._ori_forward(hidden_states)
        b = self.in_proj_b._ori_forward(hidden_states)
        a = self.in_proj_a._ori_forward(hidden_states)
        
        mixed_qkv = torch.cat([q, k, v], dim=-1)
        return mixed_qkv, z, b, a

    def forward(
        self,
        hidden_states,
        cache_params=None,
        cache_position=None,
        attention_mask=None,
    ):
        # 应用 padding mask
        if attention_mask is not None:
            # apply_mask_to_padding_states
            non_padding = (attention_mask.sum(dim=-1, keepdim=True) > 0).to(hidden_states.dtype)
            if non_padding.dim() == 3:
                hidden_states = hidden_states * non_padding
        
        batch_size, seq_len, _ = hidden_states.shape
        
        use_precomputed_states = (
            cache_params is not None
            and cache_params.has_previous_state
            and seq_len == 1
            and cache_position is not None
        )
        
        if cache_params is not None:
            conv_state = cache_params.conv_states[self.layer_idx]
            recurrent_state = cache_params.recurrent_states[self.layer_idx]
        
        # 投影：应用 FlatQuant 变换
        if self._ori_mode:
            mixed_qkv, z, b, a = self._ori_forward_projs(hidden_states)
        elif self._eval_mode:
            # eval 模式：变换已融合进权重，直接用 linear forward
            q = self.q_proj.linear(hidden_states)
            k = self.k_proj.linear(hidden_states)
            v = self.v_proj.linear(hidden_states)
            mixed_qkv = torch.cat([q, k, v], dim=-1)
            z = self.in_proj_z.linear(hidden_states)
            b = self.in_proj_b.linear(hidden_states)
            a = self.in_proj_a.linear(hidden_states)
        else:
            mixed_qkv, z, b, a = self._trans_forward_projs(hidden_states)
        
        mixed_qkv = mixed_qkv.transpose(1, 2)
        z = z.reshape(batch_size, seq_len, -1, self.head_v_dim)
        
        # Conv1d
        if use_precomputed_states:
            mixed_qkv = self.causal_conv1d_update(
                mixed_qkv, conv_state,
                self.conv1d.weight.squeeze(1), self.conv1d.bias,
                self.activation,
            )
        else:
            if cache_params is not None:
                conv_state = torch.nn.functional.pad(mixed_qkv, (self.conv_kernel_size - mixed_qkv.shape[-1], 0))
                cache_params.conv_states[self.layer_idx] = conv_state
            if self.causal_conv1d_fn is not None:
                mixed_qkv = self.causal_conv1d_fn(
                    x=mixed_qkv,
                    weight=self.conv1d.weight.squeeze(1),
                    bias=self.conv1d.bias,
                    activation=self.activation,
                    seq_idx=None,
                )
            else:
                mixed_qkv = torch.nn.functional.silu(self.conv1d(mixed_qkv)[:, :, :seq_len])
        
        mixed_qkv = mixed_qkv.transpose(1, 2)
        query, key, value = torch.split(
            mixed_qkv,
            [self.key_dim, self.key_dim, self.value_dim],
            dim=-1,
        )
        
        query = query.reshape(batch_size, seq_len, -1, self.head_k_dim)
        key = key.reshape(batch_size, seq_len, -1, self.head_k_dim)
        value = value.reshape(batch_size, seq_len, -1, self.head_v_dim)
        
        # 应用 kcache_trans 和量化（与 Qwen2 的 quant_kcache/quant_vcache 对齐）
        if not self._ori_mode:
            # key 变换和量化
            if self.kcache_trans is not None:
                query = self.kcache_trans(query, inv_t=True)
                key = self.kcache_trans(key)
            if hasattr(self, 'q_quantizer') and self.args.q_bits < 16:
                query = self.q_quantizer(query).to(query)
            if hasattr(self, 'k_quantizer') and self.args.k_bits < 16:
                key = self.k_quantizer(key).to(query)
            # value 变换和量化
            if self.args.separate_vtrans and self.vcache_trans is not None:
                value = self.vcache_trans(value)
            if hasattr(self, 'v_quantizer') and self.args.v_bits < 16:
                value = self.v_quantizer(value)
        
        beta = b.sigmoid()
        g = -self.A_log.float().exp() * torch.nn.functional.softplus(a.float() + self.dt_bias)
        if self.num_v_heads // self.num_k_heads > 1:
            query = query.repeat_interleave(self.num_v_heads // self.num_k_heads, dim=2)
            key = key.repeat_interleave(self.num_v_heads // self.num_k_heads, dim=2)
        
        if not use_precomputed_states:
            core_attn_out, last_recurrent_state = self.chunk_gated_delta_rule(
                query, key, value, g=g, beta=beta,
                initial_state=None,
                output_final_state=cache_params is not None,
                use_qk_l2norm_in_kernel=True,
            )
        else:
            core_attn_out, last_recurrent_state = self.recurrent_gated_delta_rule(
                query, key, value, g=g, beta=beta,
                initial_state=recurrent_state,
                output_final_state=cache_params is not None,
                use_qk_l2norm_in_kernel=True,
            )
        
        if cache_params is not None:
            cache_params.recurrent_states[self.layer_idx] = last_recurrent_state
        
        core_attn_out = core_attn_out.reshape(-1, self.head_v_dim)
        z = z.reshape(-1, self.head_v_dim)
        core_attn_out = self.norm(core_attn_out, z)
        core_attn_out = core_attn_out.reshape(batch_size, seq_len, -1)
        
        # 输出投影：应用 FlatQuant 变换
        if self._ori_mode:
            output = self.out_proj._ori_forward(core_attn_out)
        elif self._eval_mode:
            # eval 模式：变换已融合进权重，直接用 linear forward
            output = self.out_proj.linear(core_attn_out)
        else:
            # 应用 vcache_trans（让 value 分布更均匀，对应 Qwen2 的 vcache_trans）
            if self.vcache_trans is not None:
                init_shape = core_attn_out.shape
                core_attn_out_r = core_attn_out.reshape(-1, self.num_v_heads, self.head_v_dim)
                core_attn_out_r = torch.matmul(core_attn_out_r, self.vcache_trans.get_matrix(inv_t=True).T.to(core_attn_out_r))
                core_attn_out = core_attn_out_r.reshape(init_shape)
            
            if self.out_trans is not None:
                init_shape = core_attn_out.shape
                core_attn_out = core_attn_out.reshape(-1, self.num_v_heads, self.head_v_dim)
                core_attn_out = torch.matmul(
                    self.out_trans.get_matrix().T.to(core_attn_out),
                    core_attn_out
                ).reshape(init_shape)
                if not self._eval_mode:
                    out_og_it = self.out_trans.get_matrix(inv_t=True)
                    vcache_og_it = self.vcache_trans.get_matrix(inv_t=True) if self.vcache_trans is not None else None
                    if vcache_og_it is not None:
                        output = self.out_proj(core_attn_out, qa_trans=[out_og_it, vcache_og_it])
                    else:
                        output = self.out_proj(core_attn_out, qa_trans=out_og_it)
                else:
                    output = self.out_proj(core_attn_out)
            else:
                output = self.out_proj(core_attn_out)
        
        return output

    def reparameterize(self):
        """把变换矩阵融合进权重"""
        if self.ln_trans is not None:
            self.ln_trans.to_eval_mode()
        if self.out_trans is not None:
            self.out_trans.to_eval_mode()
        if self.kcache_trans is not None:
            self.kcache_trans.to_eval_mode()
        if self.vcache_trans is not None:
            self.vcache_trans.to_eval_mode()
        
        # 融合输入变换到投影层权重
        self.q_proj.reparameterize(qa_trans=self.ln_trans)
        self.k_proj.reparameterize(qa_trans=self.ln_trans)
        if self.args.separate_vtrans:
            self.v_proj.reparameterize(qa_trans=self.ln_trans)
        else:
            self.v_proj.reparameterize(qa_trans=self.ln_trans, out_trans=self.vcache_trans)
        self.in_proj_z.reparameterize(qa_trans=self.ln_trans)
        self.in_proj_b.reparameterize(qa_trans=self.ln_trans)
        self.in_proj_a.reparameterize(qa_trans=self.ln_trans)
        
        # 融合输出变换和 value 变换到 out_proj 权重
        if self.out_trans is not None and self.vcache_trans is not None:
            out_og_it = self.out_trans.get_matrix(inv_t=True)
            vcache_og_it = self.vcache_trans.get_matrix(inv_t=True)
            self.out_proj.reparameterize(qa_trans=[out_og_it, vcache_og_it])
        elif self.out_trans is not None:
            out_og_it = self.out_trans.get_matrix(inv_t=True)
            self.out_proj.reparameterize(qa_trans=out_og_it)
        
        self._eval_mode = True

    def init_diag_scale(self, alpha=0.5):
        if not hasattr(self, "ln_smax"):
            return
        # 综合所有输入投影层的权重统计（拆分后的 q/k/v + z/b/a）
        all_weights = torch.cat([
            self.q_proj.linear.weight,
            self.k_proj.linear.weight,
            self.v_proj.linear.weight,
            self.in_proj_z.linear.weight,
            self.in_proj_b.linear.weight,
            self.in_proj_a.linear.weight,
        ], dim=0).abs().max(dim=0)[0]
        if self.ln_trans is not None:
            self.ln_trans.diag_scale.data = get_init_scale(all_weights, self.ln_smax, alpha)
        del self.ln_smax
        self.diag_init = None

    def rep_matrix_only(self):
        if self.ln_trans is not None:
            self.ln_trans.to_eval_mode()
        if self.out_trans is not None:
            self.out_trans.to_eval_mode()
        if self.kcache_trans is not None:
            self.kcache_trans.to_eval_mode()
        if self.vcache_trans is not None:
            self.vcache_trans.to_eval_mode()


class FlatQuantQwen3_5StdAttention(torch.nn.Module):
    """
    Qwen3.5 标准 self_attn 的 FlatQuant 包装
    不继承 Qwen2Attention，避免 super().__init__ 重新分配权重导致卡死
    """
    def __init__(self, args, module):
        super().__init__()
        self.args = args
        self._module = module  # 保留原始 Qwen3_5Attention 模块

        # 从 config 读取配置（Qwen3_5Attention 的属性在 config 上）
        self.config = module.config
        self.layer_idx = module.layer_idx
        self.hidden_size = module.config.hidden_size
        self.num_heads = module.config.num_attention_heads
        self.head_dim = module.head_dim  # 这个是直接属性
        self.num_key_value_heads = module.config.num_key_value_heads
        self.num_key_value_groups = module.num_key_value_groups
        self.scaling = module.scaling
        self.is_causal = module.is_causal

        # Qwen3.5 的 q_proj 输出维度是 num_heads * 2 * head_dim（包含 QK norm）
        # 不能用 hidden_size 来 reshape，要用实际的 proj 输出维度
        self.q_proj_out_dim = module.q_proj.weight.shape[0]  # 8192
        self.k_proj_out_dim = module.k_proj.weight.shape[0]  # 1024
        self.v_proj_out_dim = module.v_proj.weight.shape[0]  # 1024

        # 用 FlatQuantizedLinear 包装投影层
        self.q_proj = FlatQuantizedLinear(args, module.q_proj)
        self.k_proj = FlatQuantizedLinear(args, module.k_proj)
        self.v_proj = FlatQuantizedLinear(args, module.v_proj)
        self.o_proj = FlatQuantizedLinear(args, module.o_proj)

        # 保留原模块的其他组件（rotary_emb, q_norm, k_norm, attn_output_gate 等）
        for attr_name in ['rotary_emb', 'q_norm', 'k_norm', 'attn_output_gate']:
            if hasattr(module, attr_name):
                setattr(self, attr_name, getattr(module, attr_name))
        self.attention_dropout = module.attention_dropout if hasattr(module, 'attention_dropout') else 0.0

        # 添加 FlatQuant 变换矩阵
        self.add_fq_trans()

        # KV cache 量化器
        if args.q_bits < 16:
            self.q_cache_quantizer = ActivationQuantizer(bits=args.q_bits, sym=not args.q_asym, lac=args.lac, groupsize=-1)
        if args.k_bits < 16:
            self.k_cache_quantizer = ActivationQuantizer(bits=args.k_bits, sym=not args.k_asym, lac=args.lac, groupsize=-1)
        if args.v_bits < 16:
            self.v_cache_quantizer = ActivationQuantizer(bits=args.v_bits, sym=not args.v_asym, lac=args.lac, groupsize=-1)

        self._ori_mode = False
        self._eval_mode = False
        self.diag_init = args.diag_init
        if self.diag_init == "sq_style":
            self.ln_smax = torch.ones_like(self.q_proj.linear.weight.abs().max(dim=0)[0]).cuda() * 1e-5

    def add_fq_trans(self):
        if self.args.direct_inv:
            SingleTransMatrix, DecomposeTransMatrix = InvSingleTransMatrix, InvDecomposeTransMatrix
        else:
            SingleTransMatrix, DecomposeTransMatrix = SVDSingleTransMatrix, SVDDecomposeTransMatrix
        if self.args.w_bits < 16 or self.args.a_bits < 16:
            ln_dim_left, ln_dim_right = get_decompose_dim(self.q_proj.linear.weight.shape[1])
            self.ln_trans = DecomposeTransMatrix(ln_dim_left, ln_dim_right, add_diag=self.args.add_diag)
            self.o_trans = SingleTransMatrix(self.num_heads)
        else:
            self.ln_trans, self.o_trans = None, None

        if self.args.k_bits < 16 or self.args.q_bits < 16:
            self.kcache_trans = SingleTransMatrix(self.head_dim)
        else:
            self.kcache_trans = None
        if self.args.v_bits < 16 or self.args.w_bits < 16 or self.args.a_bits < 16:
            self.vcache_trans = SingleTransMatrix(self.head_dim)
        else:
            self.vcache_trans = None

    def _trans_forward_after_ln(self, hidden_states):
        if self.ln_trans is not None:
            hidden_states = self.ln_trans(hidden_states)
        query_states = self.q_proj(hidden_states, qa_trans=self.ln_trans)
        key_states = self.k_proj(hidden_states, qa_trans=self.ln_trans)
        if self.args.separate_vtrans:
            value_states = self.v_proj(hidden_states, qa_trans=self.ln_trans)
        else:
            value_states = self.v_proj(hidden_states, qa_trans=self.ln_trans, out_trans=self.vcache_trans)
        return query_states, key_states, value_states

    def _ori_forward_after_ln(self, hidden_states):
        if self.diag_init == "sq_style" and hasattr(self, "ln_smax"):
            self.ln_smax = torch.maximum(self.ln_smax,
                hidden_states.reshape(-1, hidden_states.shape[-1]).abs().max(0)[0].clone().detach())
        query_states = self.q_proj._ori_forward(hidden_states)
        key_states = self.k_proj._ori_forward(hidden_states)
        value_states = self.v_proj._ori_forward(hidden_states)
        return query_states, key_states, value_states

    def quant_vcache(self, value_states):
        if self.args.separate_vtrans:
            value_states = self.vcache_trans(value_states)
        if self.args.v_bits < 16:
            value_states = self.v_cache_quantizer(value_states)
        return value_states

    def quant_kcache(self, q, k):
        if not (self.args.k_bits < 16 or self.args.q_bits < 16):
            return q, k
        if self.kcache_trans is not None:
            q = self.kcache_trans(q, inv_t=True)
            k = self.kcache_trans(k)
        if self.args.q_bits < 16:
            q = self.q_cache_quantizer(q).to(q)
        if self.args.k_bits < 16:
            k = self.k_cache_quantizer(k).to(q)
        return q, k

    def forward(self, hidden_states, attention_mask=None, position_ids=None, past_key_value=None,
                output_attentions=False, use_cache=False, cache_position=None, position_embeddings=None, **kwargs):
        """
        委托给原始 Qwen3_5Attention 的 forward。
        关键：先把我们的 FlatQuantizedLinear 注入到原模块中，
        这样原模块的 forward 会自动使用量化后的投影层。
        """
        # 注入 FlatQuantizedLinear 到原模块
        self._module.q_proj = self.q_proj
        self._module.k_proj = self.k_proj
        self._module.v_proj = self.v_proj
        self._module.o_proj = self.o_proj
        
        return self._module.forward(
            hidden_states,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_value=past_key_value,
            output_attentions=output_attentions,
            use_cache=use_cache,
            cache_position=cache_position,
            position_embeddings=position_embeddings,
            **kwargs
        )

    def reparameterize(self):
        if self.ln_trans is not None:
            self.ln_trans.to_eval_mode()
        if hasattr(self, 'kcache_trans') and self.kcache_trans is not None:
            self.kcache_trans.to_eval_mode()
        if hasattr(self, 'vcache_trans') and self.vcache_trans is not None:
            self.vcache_trans.to_eval_mode()
        if hasattr(self, 'o_trans') and self.o_trans is not None:
            self.o_trans.to_eval_mode()
        # 融合变换到投影层权重
        self.q_proj.reparameterize(qa_trans=self.ln_trans)
        self.k_proj.reparameterize(qa_trans=self.ln_trans)
        self.v_proj.reparameterize(qa_trans=self.ln_trans)
        self.o_proj.reparameterize()
        # 同步回原模块
        self._module.q_proj = self.q_proj
        self._module.k_proj = self.k_proj
        self._module.v_proj = self.v_proj
        self._module.o_proj = self.o_proj
        self._eval_mode = True

    def init_diag_scale(self, alpha=0.5):
        if not hasattr(self, "ln_smax"):
            return
        qkvw_smax = torch.cat([
            self.q_proj.linear.weight, self.k_proj.linear.weight, self.v_proj.linear.weight
        ], dim=0).abs().max(dim=0)[0]
        if self.ln_trans is not None:
            self.ln_trans.diag_scale.data = get_init_scale(qkvw_smax, self.ln_smax, alpha)
        del self.ln_smax
        self.diag_init = None

    def rep_matrix_only(self):
        if self.ln_trans is not None:
            self.ln_trans.to_eval_mode()
        if hasattr(self, 'kcache_trans') and self.kcache_trans is not None:
            self.kcache_trans.to_eval_mode()
        if hasattr(self, 'vcache_trans') and self.vcache_trans is not None:
            self.vcache_trans.to_eval_mode()
        if hasattr(self, 'o_trans') and self.o_trans is not None:
            self.o_trans.to_eval_mode()



class FlatQuantQwen2MLP(torch.nn.Module):
    def __init__(self, args, module: Qwen2MLP):
        super().__init__()
        self.args = args
        self.hidden_size = module.hidden_size
        self.intermediate_size = module.intermediate_size
        self.act_fn = module.act_fn
        self.up_proj = FlatQuantizedLinear(args, module.up_proj)
        self.gate_proj = FlatQuantizedLinear(args, module.gate_proj)
        self.down_proj = FlatQuantizedLinear(args, module.down_proj)
        self.add_fq_trans()

        self._ori_mode = False
        self.diag_init = args.diag_init
        if self.diag_init == "sq_style":
            self.up_smax = torch.ones_like(self.up_proj.linear.weight.abs().max(dim=0)[0]).cuda() * 1e-5
            self.down_smax = torch.ones_like(self.down_proj.linear.weight.abs().max(dim=0)[0]).cuda() * 1e-5
        
    def add_fq_trans(self):
        if self.args.direct_inv:
            DecomposeTransMatrix = InvDecomposeTransMatrix
        else:
            DecomposeTransMatrix = SVDDecomposeTransMatrix
        if self.args.w_bits < 16 or self.args.a_bits < 16:
            up_dim_left, up_dim_right = get_decompose_dim(self.up_proj.linear.weight.shape[1])
            self.up_gate_trans = DecomposeTransMatrix(up_dim_left, up_dim_right, add_diag=self.args.add_diag)
            down_dim_left, down_dim_right = get_decompose_dim(self.down_proj.linear.weight.shape[1])
            self.down_trans = DecomposeTransMatrix(down_dim_left, down_dim_right, add_diag=self.args.add_diag)
        else:
            self.up_gate_trans, self.down_trans = None, None

    def _trans_forward(self, x):
        if self.up_gate_trans is not None:
            x_ts = self.up_gate_trans(x)
        else:
            x_ts = x
        up_states = self.up_proj(x_ts, qa_trans=self.up_gate_trans)
        gate_states = self.gate_proj(x_ts, qa_trans=self.up_gate_trans)

        x_act_fn = self.act_fn(gate_states) * up_states
        if self.down_trans is not None:
            x_ts_2 = self.down_trans(x_act_fn)
        else:
            x_ts_2 = x_act_fn
        down_states = self.down_proj(x_ts_2, qa_trans=self.down_trans)
        return down_states

    def _ori_forward(self, x):
        '''origin implement: down_proj = self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))'''
        if self.diag_init == "sq_style":
            self.up_smax = torch.maximum(self.up_smax, x.reshape(-1, x.shape[-1]).abs().max(0)[0].clone().detach())
        x = self.act_fn(self.gate_proj._ori_forward(x)) * self.up_proj._ori_forward(x)
        if self.diag_init == "sq_style":
            self.down_smax = torch.maximum(self.down_smax, x.reshape(-1, x.shape[-1]).abs().max(0)[0].clone().detach())
        down_states = self.down_proj._ori_forward(x)
        return down_states

    def forward(self, x):
        if self._ori_mode:
            return self._ori_forward(x)
        return self._trans_forward(x)

    def reparameterize(self, ):
        if self.up_gate_trans is not None:
            self.up_gate_trans.to_eval_mode()
            self.down_trans.to_eval_mode()
        self.gate_proj.reparameterize(qa_trans=self.up_gate_trans)
        self.up_proj.reparameterize(qa_trans=self.up_gate_trans)
        self.down_proj.reparameterize(qa_trans=self.down_trans)
        if self.up_gate_trans is not None:
            self.up_gate_trans.use_diag = False
        # merge trans's diag scale
        if self.down_trans is not None and self.down_trans.add_diag:
            up_weight = self.up_proj.linear.weight
            ori_dtype = up_weight.dtype
            up_weight = up_weight.to(torch.float64).T.mul(self.down_trans.diag_scale.to(torch.float64)).T
            self.up_proj.linear.weight.data = up_weight.to(ori_dtype)
            self.down_trans.use_diag = False

    def init_diag_scale(self, alpha=0.5):
        assert hasattr(self, "up_smax") and hasattr(self, "down_smax")
        upw_smax = torch.cat([self.up_proj.linear.weight, self.gate_proj.linear.weight], dim=0).abs().max(dim=0)[0]
        downw_smax = self.down_proj.linear.weight.abs().max(dim=0)[0]
        if self.up_gate_trans is not None:
            self.up_gate_trans.diag_scale.data = get_init_scale(upw_smax, self.up_smax, alpha)
        if self.down_trans is not None:
            self.down_trans.diag_scale.data = get_init_scale(downw_smax, self.down_smax, alpha)
        del self.up_smax, self.down_smax
        self.diag_init = None

    def rep_matrix_only(self, ):
        if self.up_gate_trans is not None:
            self.up_gate_trans.to_eval_mode()
            self.down_trans.to_eval_mode()


class FlatQuantQwen2Attention(Qwen2Attention):
    def __init__(self, args, module: Qwen2Attention):
        super().__init__(module.config, module.layer_idx)
        self.args = args
        
        self.q_proj = FlatQuantizedLinear(args, module.q_proj)
        self.k_proj = FlatQuantizedLinear(args, module.k_proj)
        self.v_proj = FlatQuantizedLinear(args, module.v_proj)
        self.o_proj = FlatQuantizedLinear(args, module.o_proj)
        self.add_fq_trans()

        if args.q_bits < 16:
            self.q_cache_quantizer = ActivationQuantizer(bits=args.q_bits, \
                                        sym=not(args.q_asym), lac=args.lac, groupsize=-1, )
        if args.k_bits < 16:
            self.k_cache_quantizer = ActivationQuantizer(bits=args.k_bits, \
                                        sym=not(args.k_asym), lac=args.lac, groupsize=-1, )
        if args.v_bits < 16:
            self.v_cache_quantizer = ActivationQuantizer(bits=args.v_bits, \
                                        sym=not(args.v_asym), lac=args.lac, groupsize=-1, )

        self._ori_mode = False
        self._eval_mode = False
        self.diag_init = args.diag_init
        if self.diag_init == "sq_style":
            self.ln_smax = torch.ones_like(self.q_proj.linear.weight.abs().max(dim=0)[0]).cuda() * 1e-5

    def add_fq_trans(self):
        if self.args.direct_inv:
            SingleTransMatrix, DecomposeTransMatrix = InvSingleTransMatrix, InvDecomposeTransMatrix
        else:
            SingleTransMatrix, DecomposeTransMatrix = SVDSingleTransMatrix, SVDDecomposeTransMatrix
        if self.args.w_bits < 16 or self.args.a_bits < 16:
            ln_dim_left, ln_dim_right = get_decompose_dim(self.q_proj.linear.weight.shape[1])
            self.ln_trans = DecomposeTransMatrix(ln_dim_left, ln_dim_right, add_diag=self.args.add_diag)
            self.o_trans = SingleTransMatrix(self.config.num_attention_heads)
        else:
            self.ln_trans, self.o_trans = None, None

        head_dim = self.config.hidden_size // self.config.num_attention_heads
        if self.args.k_bits < 16 or self.args.q_bits < 16:
            self.kcache_trans = SingleTransMatrix(head_dim)
        else:
            self.kcache_trans = None
        if self.args.v_bits < 16 or self.args.w_bits < 16 or self.args.a_bits < 16:
            self.vcache_trans = SingleTransMatrix(head_dim)
        else:
            self.vcache_trans = None

    def _trans_forward_after_ln(self, hidden_states):
        if self.ln_trans is not None:
            hidden_states = self.ln_trans(hidden_states)
        query_states = self.q_proj(hidden_states, qa_trans=self.ln_trans)
        key_states = self.k_proj(hidden_states, qa_trans=self.ln_trans)
        if self.args.separate_vtrans:
            value_states = self.v_proj(hidden_states, qa_trans=self.ln_trans)
        else:
            value_states = self.v_proj(hidden_states, qa_trans=self.ln_trans, out_trans=self.vcache_trans)
        return query_states, key_states, value_states

    def _ori_forward_after_ln(self, hidden_states):
        if self.diag_init == "sq_style" and hasattr(self, "ln_smax"):
            self.ln_smax = torch.maximum(self.ln_smax, \
                hidden_states.reshape(-1, hidden_states.shape[-1]).abs().max(0)[0].clone().detach())
        query_states = self.q_proj._ori_forward(hidden_states)
        key_states = self.k_proj._ori_forward(hidden_states)
        value_states = self.v_proj._ori_forward(hidden_states)
        return query_states, key_states, value_states

    def quant_vcache(self, value_states):
        if self.args.separate_vtrans:
            value_states = self.vcache_trans(value_states)
        if self.args.v_bits < 16:
            value_states = self.v_cache_quantizer(value_states)
        return value_states

    def quant_kcache(self, q, k):
        if not (self.args.k_bits < 16 or self.args.q_bits < 16):
            return q, k
        # Q/K transform
        if self.kcache_trans is not None:
            q = self.kcache_trans(q, inv_t=True)
            k = self.kcache_trans(k)
        if self.args.q_bits < 16:
            q = self.q_cache_quantizer(q).to(q)
        # TODO: by default do the per-head quantizaion for k-v-cache
        if self.args.k_bits < 16:
            k = self.k_cache_quantizer(k).to(q)
        return q, k

    def forward(self, hidden_states, attention_mask, position_ids, past_key_value, 
            output_attentions, use_cache, cache_position=None, position_embeddings=None, **kwargs):
        bsz, q_len, _ = hidden_states.size()
        if self._ori_mode:
            query_states, key_states, value_states = self._ori_forward_after_ln(hidden_states)
        else:
            query_states, key_states, value_states = self._trans_forward_after_ln(hidden_states)

        query_states = query_states.view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
        key_states = key_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
        value_states = value_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)

        if position_embeddings is None:
            # logger.warning_once(
            #     "The attention layers in this model are transitioning from computing the RoPE embeddings internally "
            #     "through `position_ids` (2D tensor with the indexes of the tokens), to using externally computed "
            #     "`position_embeddings` (Tuple of tensors, containing cos and sin). In v4.46 `position_ids` will be "
            #     "removed and `position_embeddings` will be mandatory."
            # )
            cos, sin = self.rotary_emb(value_states, position_ids)
        else:
            cos, sin = position_embeddings
        query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)
        # ---- here do the quantization ----
        if not self._ori_mode:
            query_states, key_states = self.quant_kcache(query_states, key_states)
            value_states = self.quant_vcache(value_states)

        if past_key_value is not None:
            cache_kwargs = {"sin": sin, "cos": cos, "cache_position": cache_position}  # Specific to RoPE models
            key_states, value_states = past_key_value.update(key_states, value_states, self.layer_idx, cache_kwargs)

        # repeat k/v heads if n_kv_heads < n_heads
        key_states = repeat_kv(key_states, self.num_key_value_groups)
        value_states = repeat_kv(value_states, self.num_key_value_groups) # bnsh
        attn_weights = torch.matmul(query_states, key_states.transpose(2, 3)) / math.sqrt(self.head_dim)

        if attention_mask is not None:  # no matter the length, we just slice it
            causal_mask = attention_mask[:, :, :, : key_states.shape[-2]]
            attn_weights = attn_weights + causal_mask

        # upcast attention to fp32
        attn_weights = nn.functional.softmax(attn_weights, dim=-1, dtype=torch.float32).to(query_states.dtype)
        attn_weights = nn.functional.dropout(attn_weights, p=self.attention_dropout, training=self.training)
        attn_output = torch.matmul(attn_weights, value_states)

        if attn_output.size() != (bsz, self.num_heads, q_len, self.head_dim):
            raise ValueError(
                f"`attn_output` should be of size {(bsz, self.num_heads, q_len, self.head_dim)}, but is"
                f" {attn_output.size()}"
            )

        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.reshape(bsz, q_len, self.hidden_size)
        if self._ori_mode:
            attn_output = self.o_proj._ori_forward(attn_output)
        else:
            # new foward: 
            if self.o_trans is None and self.vcache_trans is not None:
                # attn_output = self.vcache_trans(value_states)
                init_shape = attn_output.shape
                attn_output = attn_output.reshape(-1, self.config.num_attention_heads, self.config.hidden_size//self.config.num_attention_heads)
                attn_output = torch.matmul(attn_output, self.vcache_trans.get_matrix(inv_t=True).T.to(attn_output)).reshape(init_shape)
                attn_output = self.o_proj(attn_output)
            else:
                init_shape = attn_output.shape
                attn_output = attn_output.reshape(-1, self.config.num_attention_heads, self.config.hidden_size//self.config.num_attention_heads)
                attn_output = torch.matmul(self.o_trans.get_matrix().T.to(attn_output), attn_output).reshape(init_shape)
                if not self._eval_mode:
                    attn_o_og_it = self.o_trans.get_matrix(inv_t=True)
                    attn_v_og_it = self.vcache_trans.get_matrix(inv_t=True)
                    attn_output = self.o_proj(attn_output, qa_trans=[attn_o_og_it, attn_v_og_it])
                else:
                    attn_output = self.o_proj(attn_output)

        if not output_attentions:
            attn_weights = None
        return attn_output, attn_weights, past_key_value

    def reparameterize(self):
        if self.ln_trans is not None:
            self.ln_trans.to_eval_mode()
        if self.kcache_trans is not None:
            self.kcache_trans.to_eval_mode()
        if self.vcache_trans is not None:
            self.vcache_trans.to_eval_mode()
        if self.o_trans is not None:
            self.o_trans.to_eval_mode()
        self.q_proj.reparameterize(qa_trans=self.ln_trans)
        self.k_proj.reparameterize(qa_trans=self.ln_trans)
        if self.args.separate_vtrans:
            self.v_proj.reparameterize(qa_trans=self.ln_trans)
        else:
            self.v_proj.reparameterize(qa_trans=self.ln_trans, out_trans=self.vcache_trans)
        if self.o_trans is not None and self.vcache_trans is not None:
            attn_o_og_it = self.o_trans.get_matrix(inv_t=True)
            attn_v_og_it = self.vcache_trans.get_matrix(inv_t=True)
            self.o_proj.reparameterize(qa_trans=[attn_o_og_it, attn_v_og_it])
        self._eval_mode = True

    def init_diag_scale(self, alpha=0.5):
        assert hasattr(self, "ln_smax")
        qkvw_smax = torch.cat([self.q_proj.linear.weight, self.k_proj.linear.weight, self.v_proj.linear.weight], dim=0).abs().max(dim=0)[0]
        if self.ln_trans is not None:
            self.ln_trans.diag_scale.data = get_init_scale(qkvw_smax, self.ln_smax, alpha)
        del self.ln_smax
        self.diag_init = None

    def rep_matrix_only(self, ):
        if self.ln_trans is not None:
            self.ln_trans.to_eval_mode()
        if self.kcache_trans is not None:
            self.kcache_trans.to_eval_mode()
        if self.vcache_trans is not None:
            self.vcache_trans.to_eval_mode()
        if self.o_trans is not None:
            self.o_trans.to_eval_mode()


def apply_flatquant_to_qwen(args, model):
    """为 Qwen2 和 Qwen3.5 应用 FlatQuant"""
    skip_initialization()
    
    # 检测模型注意力结构
    first_layer = model.model.layers[0]
    has_linear_attn = hasattr(first_layer, 'linear_attn')
    has_self_attn = hasattr(first_layer, 'self_attn')
    
    # Qwen3.5 是混合架构：部分层用 linear_attn (GatedDeltaNet)，部分层用 self_attn
    # 必须逐层检测，不能假设所有层结构一样
    for layer in range(model.config.num_hidden_layers):
        layer_obj = model.model.layers[layer]
        
        # 包装注意力层
        if hasattr(layer_obj, 'linear_attn'):
            print(f"  FlatQuant 包装 layer {layer}/{model.config.num_hidden_layers} (linear_attn)...", flush=True)
            layer_obj.linear_attn = FlatQuantQwen3Attention(args, layer_obj.linear_attn)
        elif hasattr(layer_obj, 'self_attn'):
            attn_cls = type(layer_obj.self_attn).__name__
            if 'Qwen2' in attn_cls and 'Qwen3' not in attn_cls:
                print(f"  FlatQuant 包装 layer {layer}/{model.config.num_hidden_layers} (Qwen2 self_attn)...", flush=True)
                layer_obj.self_attn = FlatQuantQwen2Attention(args, layer_obj.self_attn)
            else:
                print(f"  FlatQuant 包装 layer {layer}/{model.config.num_hidden_layers} (Qwen3.5 self_attn)...", flush=True)
                layer_obj.self_attn = FlatQuantQwen3_5StdAttention(args, layer_obj.self_attn)
        else:
            print(f"  ⚠ layer {layer} 无法识别注意力类型，跳过", flush=True)
            continue
        
        # 包装 MLP 层
        layer_obj.mlp = FlatQuantQwen3MLP(args, layer_obj.mlp)
    
    return model
