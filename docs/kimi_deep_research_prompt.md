# OBR FlatQuant 适配 Qwen3.5-9B 的推理加载问题

## 背景

我在将 OBR（Optimal Brain Restoration）模型压缩技术从 Qwen2 适配到 Qwen3.5-9B 上。OBR 原版仓库地址：https://github.com/csguoh/OBR.git ，论文基于 FlatQuant 变换 + GPTQ 量化 + WANDA 稀疏化。

## Qwen3.5-9B 的特殊架构

Qwen3.5-9B 是混合架构，32 层中：
- 24 层是 GatedDeltaNet（`linear_attn`）：使用 `in_proj_qkv`（合并的 QKV 投影）、`in_proj_z`、`in_proj_b`、`in_proj_a`、`out_proj`、`conv1d` 等
- 8 层是标准 self_attn（`Qwen3_5Attention`）：使用 `q_proj`（输出维度 8192，不是 4096）、`k_proj`、`v_proj`、`o_proj`，还有 `q_norm`、`k_norm`、`attn_output_gate` 等特殊组件

层类型分布：每 4 层中前 3 层是 linear_attn，第 4 层是 self_attn（layer 3, 7, 11, 15, 19, 23, 27, 31）。

## 已完成的工作

### 压缩阶段（已成功）

1. 为 GatedDeltaNet 层写了 `FlatQuantQwen3Attention`（继承 `nn.Module`），拆分 `in_proj_qkv` 为独立的 `q_proj/k_proj/v_proj`，所有 7 个 Linear 层用 `FlatQuantizedLinear` 包装
2. 为标准 self_attn 层写了 `FlatQuantQwen3_5StdAttention`（继承 `nn.Module`），用委托模式调用原始 `Qwen3_5Attention` 的 forward
3. MLP 层用 `FlatQuantQwen3MLP` 包装
4. 修改了 `flat_utils.reparameterize_model` 兼容混合架构
5. 修改了 `obr_utils.obr_fwrd` 兼容混合架构，并实现差异化量化（self_attn 层用 W8+不稀疏，linear_attn 层用 W4+50%稀疏）
6. 校准训练 32 层 × 15 epochs 已完成，参数已保存
7. 重参数化 + OBR 量化已完成，`quantized_model.pt`（16.7GB）已保存

### 推理加载阶段（失败）

加载方式：加载原始模型 → FlatQuant 包装 → reparameterize → load_state_dict → eval forward

结果：`missing=0, unexpected=0`，但 PPL 从 9.27 崩到 250 万。

## 核心问题

### 问题 1：eval forward 路径

OBR 原版在 Qwen2 上的 `FlatQuantQwen2Attention` 继承了 `Qwen2Attention`，forward 是完整重写的。但 Qwen3.5 的 `Qwen3_5Attention` 有 QK norm、partial rotary（`partial_rotary_factor=0.25`）、`attn_output_gate` 等特殊逻辑，无法简单重写。

我用了委托模式：`FlatQuantQwen3_5StdAttention` 保存 `_module`（原始 `Qwen3_5Attention`），forward 时调用 `_module.forward`。投影层被替换为 `FlatQuantizedLinear`。

reparameterize 后，`FlatQuantizedLinear._eval_mode=True`，`_eval_forward` 做 `act_quantizer(x)` + `self.linear(x)`。`a_bits=16` 时 act_quantizer 透传。

### 问题 2：reparameterize + load_state_dict 的交互

reparameterize 做了两件事：
1. 把变换矩阵从训练结构（`linear_u/v/diag`）切换到 eval 结构（`matrix/matrix_inv_t`）
2. 把变换矩阵融合进 `linear.weight` 和 `layernorm.weight`

加载时，我先 reparameterize（用随机初始化的变换矩阵融合），然后 load_state_dict 覆盖所有参数。理论上 load_state_dict 会覆盖被融合的值，但实际 PPL 崩了。

### 问题 3：逐层诊断结果

Layer 0（GatedDeltaNet）的 forward 输出：`obr_std=33.0` vs `fp16_std=0.135`，差了 250 倍。说明 GatedDeltaNet 层的 eval forward 输出就已经错了。

GatedDeltaNet 层的 eval forward 路径：
```python
if self._eval_mode:
    q = self.q_proj.linear(hidden_states)  # 直接用 nn.Linear
    k = self.k_proj.linear(hidden_states)
    v = self.v_proj.linear(hidden_states)
    mixed_qkv = torch.cat([q, k, v], dim=-1)
    z = self.in_proj_z.linear(hidden_states)
    b = self.in_proj_b.linear(hidden_states)
    a = self.in_proj_a.linear(hidden_states)
```

然后经过 conv1d → split → kcache_trans → chunk_gated_delta_rule → norm → out_proj。

## 关键文件

- `external_repos/OBR/FlatQuant/flatquant/model_tools/qwen_utils.py` — FlatQuant 包装类
- `external_repos/OBR/FlatQuant/flatquant/flat_utils.py` — reparameterize_model
- `external_repos/OBR/FlatQuant/flatquant/obr_utils.py` — obr_fwrd 量化
- `external_repos/OBR/FlatQuant/flatquant/flat_linear.py` — FlatQuantizedLinear
- `external_repos/OBR/FlatQuant/flatquant/trans_utils.py` — SVDSingleTransMatrix/SVDDecomposeTransMatrix
- `backend/model_compression/eval_compression_quality.py` — 评估脚本

## 需要解决的问题

1. 为什么 reparameterize + load_state_dict 后，GatedDeltaNet 层的 forward 输出 std 从 0.135 变成 33.0？load_state_dict 应该覆盖了所有被 reparameterize 修改的参数。

2. OBR 原版在 Qwen2 上是怎么处理推理加载的？原版的 `main.py` 中压缩后直接用同一个模型对象跑 `eval_ppl`，不需要重新加载。但我的场景需要从 state_dict 重建模型。

3. 正确的推理加载流程应该是什么？是否应该：
   - 方案 A：FlatQuant 包装 → reparameterize → load_state_dict（当前方案，PPL 崩）
   - 方案 B：FlatQuant 包装 → load_state_dict（不 reparameterize，但 key 不匹配）
   - 方案 C：不用 FlatQuant 包装，直接用原始模型结构加载（但 state_dict key 有 `.linear.` 等 FlatQuant 前缀）
   - 方案 D：其他方案？

## 补充信息

- OBR 原版仓库：https://github.com/csguoh/OBR.git
- FlatQuant 论文：FlatQuant: Flatness Matters for LLM Quantization
- Qwen3.5 模型：transformers 库中的 `Qwen3_5ForConditionalGeneration`
- 配置：W4A16K4V4 + 50% 稀疏（linear_attn 层），W8A16 + 不稀疏（self_attn 层）
