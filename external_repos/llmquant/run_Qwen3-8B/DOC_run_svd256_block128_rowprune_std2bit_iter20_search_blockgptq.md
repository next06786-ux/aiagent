# Qwen3-8B: `run_svd256_block128_rowprune_std2bit_iter20_search_blockgptq.sh` 流程与原理说明

## 1. 适用范围
本文档专门对应以下脚本与同名日志：

1. 脚本：`/map-vepfs/haozhe/BiDIT/qqllm/BiLLM/run_Qwen3-8B/run_svd256_block128_rowprune_std2bit_iter20_search_blockgptq.sh`
2. 参考日志：`/map-vepfs/haozhe/BiDIT/qqllm/BiLLM/run_Qwen3-8B/log/0305_qwen3-8b_svd256_block128_rowprune_std2bit_iter20_search_blockgptq_20260305_170106.log`

这条链路是一个「SVD 低秩 + 残差分块 row-prune 搜索 + std2bit 迭代量化 + GPTQ 二阶补偿」的联合压缩流程。

## 2. 一句话概述
对每个线性层权重矩阵 \(W\)，先做 rank=256 的 SVD 把主能量放进低秩分支，再对残差 \(R\) 按 128 列分块；每个块搜索每行剪枝数 \(m\)，用标准 2bit 逐通道量化评估候选，最后用 GPTQ 的 Hessian 逆把当前列误差传播到后续列，降低误差累积。

## 3. 入口脚本做了什么
脚本核心参数如下（见脚本第 17-33 行）：

1. `2bit`: 低比特主路径使用 2bit 方案。
2. `--svd_enable --svd_rank 256`: 开启 SVD，固定 rank=256。
3. `--svd_num_iters 1 --svd_2bit_stages 1`: 单阶段 SVD+残差量化，不做多阶段展开。
4. `--svd_row_prune_search_enable`: 开启残差分块的逐行剪枝搜索。
5. `--svd_row_prune_quant_scheme std2bit`: 候选 \(m\) 的评估量化器是标准 2bit（不是 binary order）。
6. `--svd_row_prune_m_candidates 0,4,...,96`: 每行剪枝数候选集合。
7. `--iterative_2bit_iters 20 --iterative_2bit_fixed_iters`: 2bit 迭代量化固定做 20 轮。
8. `--blocksize 128`: 残差按 128 列一个 block 做 GPTQ。
9. `--salient_metric hessian`: 显著性度量设为 Hessian（本脚本未启用 salient split，但该参数仍会传入）。

日志里也会明确打印：

1. `--svd_row_prune_binary_order is ignored when --svd_row_prune_quant_scheme is std2bit/std3bit`
2. row-prune 目标函数是 `L(m)=sum((R_b-Q_b)^2)`，且 `R_b` 使用未剪枝原块。

## 4. run.py 层面的执行流程

### 4.1 参数规范化与模式判定
`run.py` 会先校验并规范化 row-prune 参数：

1. `--svd_row_prune_quant_scheme` 只能是 `binary/std2bit/std3bit`。
2. 若 scheme 是 `std2bit/std3bit`，`--svd_row_prune_binary_order` 被忽略并打印说明。
3. 候选 `m`、clip 候选等会去重和边界裁剪。

### 4.2 校准数据与 Hessian 统计
量化前会通过 calibration 数据前向收集统计量：

1. 通过 hook 把输入样本喂给 `BRAGPTQ.add_batch(...)`。
2. 内部更新 Hessian 近似矩阵 \(H\)（用于后续 GPTQ 补偿）。

### 4.3 按层按子模块量化
每个待量化模块都会创建：

1. `Binarization(...)`：包含迭代 2bit 参数。
2. `BRAGPTQ(...)`：封装 SVD/残差量化/GPTQ 流程。
3. 调用 `fasterquant(...)`，把 row-prune、SVD、blocksize 等参数传入。

## 5. fasterquant 核心方法（本脚本对应路径）

### 5.1 SVD 分解与低秩分支
对当前层权重 \(W\) 做截断 SVD：
\[
W \approx L + R,\quad \text{rank}(L)=256
\]
其中：

1. `proj_down = V^T[:rank, :]`
2. `proj_up = U[:, :rank] * S[:rank]`
3. `L = proj_up @ proj_down`
4. `R = W - L`

本模式下低秩分支默认走 4bit per-channel fake quant（`_quantize_lowrank_4bit`），即先量化 `proj_down/proj_up` 再重构 \(L\)。

### 5.2 残差分块
残差按列分块：
\[
\text{for } col\_st \in [0, blocksize, 2\cdot blocksize, ...]
\]
\[
R_b = R[:, col\_st:col\_ed],\quad blocksize=128
\]
每个 block 独立做 row-prune 搜索与 GPTQ 更新。

### 5.3 row-prune 搜索（每个 block）
对候选 \(m \in \{0,4,\dots,96\}\) 逐个评估：

1. 每行剪掉 \(|w|\) 最小的 \(m\) 个值，得到 keep-mask。
2. 用 keep-mask 后的块做量化（本脚本是 `std2bit`）。
3. 计算目标：
\[
\mathcal{L}(m)=\|R_b-Q_b^{(m)}\|_F^2
\]
4. 选最小 \(\mathcal{L}(m)\) 的 \(m^\*\)。

实现里还包含两个关键机制：

1. `zero-gate`：若最优 \(m^\*\) 不优于 \(m=0\)，强制回退到 \(m=0\)。
2. clip 二阶段搜索能力存在，但本脚本未开启，日志中 `best_clip_p` 因此基本是 `1.0`。

### 5.4 std2bit 迭代量化（固定 20 轮）
row-prune 的 `std2bit` 候选评估会调用 masked 的迭代仿射量化：

1. 量化形式：
\[
\hat x = s\cdot q + o,\quad q \in \{0,1,2,3\}
\]
2. 交替优化：
\[
q \leftarrow \text{round}\left(\frac{x-o}{s}\right),\quad
s \leftarrow \frac{\sum (x-o)q}{\sum q^2+\epsilon}
\]
\[
o \leftarrow \text{mean}(x-sq)\quad (\text{若允许更新 offset})
\]

本脚本设置了 `--iterative_2bit_fixed_iters` 且 `--iterative_2bit_iters 20`，因此每次量化固定做 20 轮，不走提前停止；日志对应 `avg_iter=20.00`。

### 5.5 GPTQ 二阶误差补偿
得到每列量化值后，执行标准 GPTQ 误差传播：

1. 当前列误差归一化：
\[
e_i=\frac{r_i-q_i}{d_i},\quad d_i=H^{-1}_{ii}
\]
2. 写回当前块量化结果。
3. 对后续列补偿：
\[
R_{\text{future}} \leftarrow R_{\text{future}} - E\cdot H^{-1}_{\text{cross}}
\]

这里传播的是「剪枝 + 量化」后的组合误差，因此不需要拆两套补偿链。

## 6. 位宽与剪枝率统计的计算口径
本模式下会输出每层：

1. `avg_weight_bits`
2. `residual_avg_bits`
3. `lowrank_avg_bits`
4. `residual_pruned_ratio`

其中残差平均位宽按保留比例计算：
\[
residual\_avg\_bits = 2.0 \times \frac{\#kept}{\#total}
\]
低秩分支平均位宽来自各 stage 的参数量与位宽累计（本脚本 stage=1，通常是 4bit 低秩 fake quant）。

## 7. 与日志对照（本次运行）
从 `20260305_170106` 日志可看到以下一致性证据：

1. 17:01:11 参数确认：row-prune 已启用，目标函数为 `L(m)=sum((R_b-Q_b)^2)`。
2. 17:02:00 首层 `self_attn.q_proj` 进入量化，模式打印为：
   `1-stage SVD + GPTQ row-prune residual quantization (standard 2bit per-channel, no salient split)`。
3. block 日志反复出现 `best_m=32/36`、`prune_ratio=25%~28.12%`、`avg_iter=20.00`，符合候选集合与固定 20 轮设置。
4. 全局汇总（17:57:24）：
   `avg_weight_bits=1.830835, residual_avg_bits=1.428661, lowrank_avg_bits=0.402174, residual_pruned_ratio=28.57%`。
5. 评测结果（同一日志尾部）：
   `wikitext2 ppl=14.715405`，`ptb ppl=21.930769`，`c4 ppl=19.825703`。

## 8. 你可以怎么调参

### 8.1 想要更高压缩
1. 增大 `m` 候选上限或扩大大 `m` 候选密度（例如加入 100、104...，前提是块宽允许）。
2. 减小 `svd_rank`（例如 256 -> 192/128）。
3. 适度增大 blocksize（会改变局部拟合与传播行为，需复测）。

### 8.2 想要更稳精度
1. 缩小可选 `m` 区间，避免过高剪枝率。
2. 保持 `iterative_2bit_fixed_iters`，必要时增加 `iterative_2bit_iters`。
3. 提升 `svd_rank` 或改为多 stage（`svd_2bit_stages>1`）做更细粒度残差递减。

### 8.3 想要更快速度
1. 减少 `m` 候选数量（例如步长从 4 改为 8）。
2. 降低 `iterative_2bit_iters`（例如 20 -> 10）。
3. 评估是否能使用更大的 blocksize 来减少 block 数。

## 9. 常见问题与排查
1. 如果日志提示 row-prune 被禁用，优先检查是否误开了 pure GPTQ、OBR 或 salient split 相关模式（这些和当前路径互斥或受限）。
2. 如果 `avg_iter` 不是 20，检查是否遗漏了 `--iterative_2bit_fixed_iters`。
3. 如果出现 Hessian/Cholesky 不稳定，代码里会自动增加 damping 并重试。
4. 脚本里当前把 `HF_TOKEN` 明文写在环境变量，建议迁移为外部注入（例如 shell 启动前 `export HF_TOKEN=...`），避免泄漏风险。

## 10. 对外讲解模板（可直接复用）
我们不是直接把全矩阵做低比特，而是先做 SVD 把主要信息放到低秩分支，再对残差做 block 级搜索式剪枝和 2bit 量化。  
每个 block 里，按行尝试多个剪枝强度 \(m\)，并且对每个候选都做迭代 2bit 拟合，最终用原残差块重建误差选出最优 \(m\)。  
选好之后再用 GPTQ 的二阶信息把当前误差传播到后续列，减少误差连锁放大。  
这条链路的本质是：低秩降复杂度 + 搜索式稀疏 + 迭代低比特拟合 + Hessian 引导补偿。

