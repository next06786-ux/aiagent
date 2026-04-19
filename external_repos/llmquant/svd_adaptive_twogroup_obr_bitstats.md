# Adaptive Multi-Stage SVD + OBR 2-Group Residual (No GPTQ)

## 1. Idea Summary
This mode targets a simple and controllable pipeline:

1. Low-rank branch: up to 3 stages of SVD, each stage rank=128, low-rank factor path uses 4bit fake quantization.
2. Adaptive stopping rule: continue to next stage only when current stage `E(128) >= 0.2`; otherwise stop.
3. Residual branch `R`: OBR 2-group split only (no GPTQ residual path).
4. Dynamic residual strength by layer:
   - if the layer used `n` SVD stages (`n in [1,3]`), then
   - `p_sal = max(1, 4 - n) * 0.1`
   - top-`p_sal` columns (by Wanda/Hessian/magnitude score in each block) use 4bit per-channel,
   - remaining columns use binary residual approximation (`order=2`),
   - error is transferred from non-salient group to 4bit group via Hessian OBR.

Intuition: if a layer cannot sustain many useful SVD stages (small low-rank gain), increase residual 4bit capacity for that layer.

## 2. Pipeline Per Layer
For each weight matrix `W`:

1. Stage-1 SVD on current matrix, rank=128.
2. Quantize low-rank stage (4bit factors), subtract from current residual.
3. Read stage energy `E(128)`.
4. If `E(128) >= 0.2` and stage count < 3, continue next stage; else stop.
5. Let final stage count be `n`.
6. Set residual salient ratio:
   - `p_sal = max(1, 4 - n) * 0.1`.
7. Run OBR 2-group residual quantization block-wise (blocksize=128):
   - group-0 (top columns): 4bit per-channel
   - group-1 (rest): binary residual approximation (`order=2`)
   - OBR transfer: group-1 error -> group-0.
8. Merge quantized low-rank + quantized residual.

## 3. Residual Average Bit Formula
Residual average data bits:

`b_R = 4 * p_sal + b_bin * (1 - p_sal)`

where:
- `p_sal` is actual 4bit column ratio (per layer after block rounding),
- `b_bin` is effective binary-branch data bits (default accounting value: `2.0`).

The implementation logs both:
- formula-equivalent residual average bits,
- measured residual average bits from counted weights.

## 4. Scale/Zero-Point Overhead Accounting
Current accounting assumptions (matching your requirement):

- Quantization granularity for residual metadata: per `(block, row)`.
- For 4bit residual group: `1 scale + 1 zero-point`.
- For binary residual approximation group: `2 scales + 1 zero-point`.

If scale bits = `b_s`, zero-point bits = `b_z`:

- residual 4bit metadata bits:
  - `meta_4 = N_row_block_4 * (b_s + b_z)`
- residual binary metadata bits:
  - `meta_bin = N_row_block_bin * (2*b_s + b_z)`

where:
- `N_row_block_4`: total count of `(block,row)` where 4bit group exists,
- `N_row_block_bin`: total count of `(block,row)` where binary group exists.

## 5. Low-Rank Branch Bit Accounting
For each used low-rank stage with rank `r` on matrix `[rows, cols]`:

- low-rank parameters: `r*(rows + cols)`
- low-rank data bits (4bit):
  - `data_L_stage = 4 * r*(rows + cols)`
- low-rank metadata (per-channel fake-quant style):
  - `meta_L_stage = (rows + r) * (b_s + b_z)`

Total low-rank bits are summed over all used stages.

## 6. Final Layer/Model Metrics
Per layer, logs include:

- `avg_weight_bits`: data-only average bits over original layer weight count
- `avg_total_bits`: (data + metadata) average bits
- `avg_meta_overhead_bits`
- `residual_avg_data_bits`, `residual_avg_total_bits`
- `p_sal_real`, `svd_stage_count`

Model-level summary uses parameter-count weighted average across layers.

## 7. Recommended Run Script
Use:

- `BiLLM/run_llama7b_rank128_adp4svd_obr_twogroup_bitstats.sh` (inter-block GPTQ propagation disabled)
- `BiLLM/run_llama7b_rank128_adp4svd_obr_twogroup_bitstats_gptqprop.sh` (inter-block GPTQ propagation enabled)

Key flags:

- `--svd_2bit_obr_twogroup_adaptive_enable`
- `--svd_2bit_obr_twogroup_adaptive_max_stages 3`
- `--svd_2bit_obr_twogroup_adaptive_e128_threshold 0.2`
- `--svd_2bit_obr_twogroup_adaptive_base_ratio 0.1`
- `--obr --disable_gptq`
- `--svd_obr_interblock_gptq_propagation_disable` (only for the no-propagation variant; omit it for gptqprop)
- `--svd_bit_stats_enable`
