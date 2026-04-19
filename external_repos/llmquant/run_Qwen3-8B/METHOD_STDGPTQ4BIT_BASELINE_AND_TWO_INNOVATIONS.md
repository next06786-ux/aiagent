# Qwen3-8B: stdGPTQ 4bit Baseline 与两个创新方法（数学原理与实现细节）

## 1. 文档目标与对应脚本

本文档用于系统说明你当前实验中的三条链路：

1. Baseline（标准 GPTQ 4bit，static qparams）  
   `run_stdgptq_std4bit_b128_tseq_act_static_noprune_norefill_nosvd.sh`
2. 方法一（4bit 交替迭代 + stdGPTQ）  
   `run_stdgptq_std4bit_iter20_b128_tseq_act_dynamic_noprune_norefill_nosvd.sh`
3. 方法二（row-prune 搜索 + 4bit 交替迭代 + stdGPTQ）  
   `run_stdgptq_std4bit_iter20_b128_tseq_act_dynamic_rowprune_2pass_norefill_nosvd.sh`

三者都在 no-SVD 路径上进行，即直接对完整权重残差路径处理（可理解为 `R=W` 的情况）。

---

## 2. GPTQ Baseline（stdGPTQ 4bit）的数学本质

### 2.1 问题定义

对线性层权重矩阵
\[
W\in\mathbb{R}^{d_{out}\times d_{in}}
\]
进行低比特量化，目标是在量化后保持输出误差最小。

在局部二阶近似下，典型目标可写为：
\[
\min_{\hat W}\; \| (W-\hat W)X \|_F^2
\approx
\min_{\hat W}\; \mathrm{Tr}\big((W-\hat W)H(W-\hat W)^T\big)
\]
其中：
- \(X\) 是校准数据激活；
- \(H\approx XX^T\) 是输入协方差/Hessian 近似。

### 2.2 列级 GPTQ 补偿

stdGPTQ 采用逐列量化与误差传播：

1. 先量化当前列 \(w_j\to q_j\)。
2. 定义归一化误差
\[
e_j = \frac{w_j-q_j}{(H^{-1})_{jj}}
\]
3. 把误差向后续列传播：
\[
W_{:,j:} \leftarrow W_{:,j:} - e_j (H^{-1})_{j,j:}
\]

这一步是 GPTQ 的关键，它将“当前列的量化损失”用二阶信息转移到未来列可优化空间，从而减少全局误差累积。

### 2.3 Baseline 的 qparam 机制（static groups）

baseline 使用 static qparams：
- 对每个 group（这里常与 block/分组策略绑定）预先估计 scale/zero-point；
- 后续列更新时复用该组固定 qparams，不随列内误差迭代更新。

优点：
- 速度更快；
- 过程更稳定、复现性更好。

代价：
- 对局部分布漂移适配较弱，精度潜力略低于 dynamic。

---

## 3. 方法一创新：4bit 交替迭代量化（Iterative Affine for 4bit）

> 核心思想：把传统“一次性求 qparam + 四舍五入”替换为“量化码与仿射参数交替优化”，显式最小化 masked MSE。

### 3.1 量化参数化

对每通道元素 \(x\)，4bit 量化写成：
\[
\hat x = s\cdot q + o,\quad q\in\{0,1,\dots,15\}
\]
等价地也可写为 zero-point 形式：
\[
\hat x = s\cdot (q-z)
\]

### 3.2 交替优化目标

在给定 mask \(M\)（有效位置）下，优化：
\[
\min_{s,o,q} \sum_i M_i(x_i-(s q_i+o))^2
\]

固定 \((s,o)\) 更新 \(q\)：
\[
q_i \leftarrow \mathrm{clip}\left(\mathrm{round}\left(\frac{x_i-o}{s}\right),0,15\right)
\]

固定 \(q,o\) 更新 \(s\)（近似闭式）：
\[
s \leftarrow \frac{\sum_i M_i(x_i-o)q_i}{\sum_i M_i q_i^2 + \varepsilon}
\]

固定 \(q,s\) 更新 \(o\)：
\[
o \leftarrow \frac{1}{\sum_i M_i}\sum_i M_i(x_i-sq_i)
\]

然后循环迭代（你的脚本里通常是 fixed iters=20）。

### 3.3 与 baseline 的本质差异

baseline 一般是“单次估计量化区间 + 直接量化”；方法一是“离散码本 + 仿射参数联合迭代逼近”。

收益来源：
1. 对偏移（offset）和尺度（scale）做了反复对齐；
2. 对激活/权重分布偏斜更鲁棒；
3. 在相同比特数下通常降低量化误差。

代价：
1. 量化阶段算力开销增加；
2. 参数搜索空间更大，若无 fixed-iter 约束，耗时波动更大。

---

## 4. 方法二创新：row-prune 搜索 + 4bit 交替迭代 + stdGPTQ

> 核心思想：先在每个 block 内搜索“按行剪多少个元素最优”，再对保留元素做 4bit 交替迭代量化，最后继续走 GPTQ 二阶补偿。

### 4.1 两阶段框架（2-pass）

#### Pass-1: 每个 block 的 m-search

对 block \(R_b\in\mathbb{R}^{r\times c}\)（此处 no-SVD 可视作 \(R_b=W_b\)），
候选集合 \(m\in\mathcal{M}\)（如 `0,4,8,...,84`）。

对每个 \(m\)：
1. 每行按 score（magnitude/WANDA）剪掉最小的 \(m\) 个位置，得 keep-mask \(K^{(m)}\)；
2. 对保留部分做 `std4bit` 迭代量化，得到 \(Q_b^{(m)}\)；
3. 计算候选目标
\[
\mathcal{L}(m)=\|R_b-Q_b^{(m)}\|_F^2
\]
4. 选 \(m^*=\arg\min_m \mathcal{L}(m)\)。

得到每个 block 的最优结构（mask）。

#### Pass-2: 固定 mask 后的 stdGPTQ

使用 Pass-1 选出的固定 mask，进入标准列级 GPTQ 补偿过程：
- 只对 active/保留位置进行量化写入；
- 仍利用 \(H^{-1}\) 做列间误差传播；
- 最终形成“结构稀疏 + 4bit 量化 + 二阶补偿”的联合结果。

### 4.2 为什么这是有效创新

传统低比特常仅优化“量化误差”，方法二同时优化：
1. **结构稀疏误差**（剪枝引入）；
2. **低比特逼近误差**（4bit迭代量化引入）；
3. **列间耦合误差**（通过 GPTQ 二阶传播修正）。

它本质上把“结构搜索 + 量化 + 二阶补偿”联动起来，而不是分离处理。

---

## 5. 两个创新点相对 baseline 的贡献总结

### 创新点 A：4bit 交替迭代量化

- 从单步量化升级为交替最优化（\(q,s,o\) 迭代）；
- 在同等4bit预算下通常降低局部 MSE；
- 与 GPTQ 结合时，前向列误差更小，后续传播链更“干净”。

### 创新点 B：row-prune 搜索 + 交替迭代

- 在 block 层引入可学习稀疏结构（m-search）；
- 每个候选结构都用 4bit iterative 精细拟合，再用统一目标选优；
- 形成“先结构选择、再二阶补偿”的更强误差控制链路。

---

## 6. 复杂度与工程细节（答辩常用）

### 6.1 复杂度趋势

设 block 宽度为 \(B\)，候选数 \(|\mathcal{M}|\)，迭代轮数 \(T\)：

1. baseline stdGPTQ：主要开销在 Hessian 相关运算 + 列补偿；
2. 方法一：额外引入 \(O(T)\) 的每组迭代拟合；
3. 方法二：额外引入 \(O(|\mathcal{M}|\cdot T)\) 的 pass-1 搜索，再加 pass-2 GPTQ。

### 6.2 稳定性策略

1. 使用 damping 与数值下界 \(\varepsilon\) 防止不稳定；
2. fixed iters 保证不同层行为可控可复现；
3. row-prune 候选可按层统计逐步收缩，避免无效搜索。

### 6.3 与 static/dynamic qparam 的关系

- baseline 你当前设为 static；
- 两个创新实验脚本当前是 dynamic（可随列更新刷新 qparams）；
- 若要做“纯方法对比”，建议把 static/dynamic 固定一致，只改“是否 iterative、是否 row-prune”。

---

## 7. 建议写进论文/报告的方法章节模板

可用如下表述：

1. 我们首先采用 stdGPTQ 4bit 作为 baseline，保证二阶误差补偿框架一致。  
2. 在此基础上，提出方法一：4bit 交替仿射量化。该方法通过离散码值与仿射参数交替更新，显式最小化 masked 重建误差。  
3. 进一步提出方法二：row-prune 2-pass 搜索与4bit交替量化联合。我们在 block 内搜索最优行剪枝强度，并在固定结构下执行 GPTQ 列补偿，实现结构与量化误差的联合优化。  
4. 两种方法均不改变推理图主干，仅修改离线量化流程，具有较强工程可迁移性。

---

## 8. 你后续可直接对比的消融设置

1. Baseline: stdGPTQ 4bit (static, no-prune)。
2. +Iter: stdGPTQ 4bit + iterative (dynamic, no-prune)。
3. +Iter+SearchPrune: stdGPTQ 4bit + iterative + row-prune search (dynamic)。

建议同时报告：
- ppl（wikitext2/ptb/c4）；
- 平均有效位宽（若统计了prune后有效bit）；
- 量化耗时；
- 关键层误差统计（可选）。

