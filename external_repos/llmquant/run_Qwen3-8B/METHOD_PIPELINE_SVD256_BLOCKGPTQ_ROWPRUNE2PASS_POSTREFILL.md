# SVD256 + Block-GPTQ + Row-Prune 2Pass + Post-Refill Pipeline (原理版)

本文档对应实验脚本：

`run_blockgptq_svd256_2bit_iter20_b128_tseq_act_dynamic_rowprune_2pass_postrefill.sh`

核心配置语义：

- `SVD rank = 256`
- `Residual quant = std2bit (iterative affine, fixed 20 iters)`
- `blocksize = 128`
- `row-prune = 2-pass search (Pass1 no-GPTQ, Pass2 fixed-mask + GPTQ)`
- `gptq_true_sequential + gptq_act_order + dynamic qparams`
- `post-gptq refill` with `row_ratio=0.4`, `pos_ratio=0.4`

---

## 1. 统一问题建模

对任意线性层，设权重为
\[
W \in \mathbb{R}^{d_{\text{out}} \times d_{\text{in}}},\quad y = Wx.
\]

校准样本记为 \(\{x^{(n)}\}_{n=1}^N\)，令
\[
H \;=\; \frac{1}{N}\sum_{n=1}^{N} x^{(n)}x^{(n)\top}.
\]

量化后权重 \(\hat W\) 的输出误差可写为
\[
\mathcal{L}_{\text{out}}(W,\hat W)
= \frac{1}{N}\sum_{n=1}^{N}\|(W-\hat W)x^{(n)}\|_2^2
= \mathrm{Tr}\!\left((W-\hat W)H(W-\hat W)^\top\right).
\]

本 pipeline 的思想是把 \(\hat W\) 分解成“低秩分支 + 稀疏低比特残差分支”：
\[
\hat W = \hat L + \hat R,
\]
并将复杂优化分解为可控的子问题：

1. 先用 SVD 抽取主要能量（\(\hat L\)）。
2. 对残差 \(R\) 做结构搜索（行剪枝 + 2bit），确定 mask。
3. 在固定 mask 下做 Block-GPTQ 二阶补偿得到 \(\hat R\)。
4. 最后轻量回填少量剪枝位，进一步减小输出通道误差。

---

## 2. SVD 模块（低秩分支）

### 2.1 低秩分解

对 \(W\) 做截断 SVD（rank \(r=256\)）：
\[
W \approx L + R_0,\qquad \mathrm{rank}(L)\le r.
\]
可写成
\[
L = U_r\Sigma_r V_r^\top.
\]

等价地把低秩部分参数化为
\[
L = A B,\quad
A\in\mathbb{R}^{d_{\text{out}}\times r},\;
B\in\mathbb{R}^{r\times d_{\text{in}}}.
\]

### 2.2 低秩分支 4bit 量化

对 \(A,B\) 分别做 per-channel 4bit 仿射量化：
\[
\hat A = Q_{4}(A),\quad \hat B = Q_{4}(B),\quad \hat L = \hat A\hat B.
\]

### 2.3 残差吸收低秩量化误差

关键点是残差不是 \(W-L\)，而是基于量化后低秩分支重建：
\[
R \;=\; W-\hat L.
\]
这样低秩分支量化误差会被“推入残差分支”统一处理，减少分支间误差割裂。

---

## 3. 搜索剪枝模块（Row-Prune 2Pass）

设块大小 \(B=128\)。按列把残差 \(R\) 切分为块 \(R_b\in\mathbb{R}^{d_{\text{out}}\times B}\)。

候选剪枝数
\[
m\in\mathcal{M}=\{0,4,8,\dots,84\}.
\]
对每个候选 \(m\)，在每一行内剪去该块中绝对值最小的 \(m\) 个元素，得到保留掩码 \(M_b^{(m)}\)。

### 3.1 Pass-1：仅做搜索（不做 GPTQ）

对保留元素做 std2bit 量化（本实验使用“交替更新 20 次”求 qparams），得到
\[
\widetilde R_b^{(m)}.
\]

采用权重重建误差作为搜索目标：
\[
\mathcal{J}_b(m)
=
\|R_b-\widetilde R_b^{(m)}\|_F^2.
\]

选择
\[
m_b^\star = \arg\min_{m\in\mathcal{M}} \mathcal{J}_b(m),
\]
并固定该块 mask（后续不再搜索）。

说明：在该脚本中 `act_topk=0`，因此不做激活重排 rerank，纯权重重建目标。

### 3.2 Pass-2：固定 mask 后做真实 Block-GPTQ

在每个块中，按照固定掩码只量化保留权重，并执行逐列 GPTQ 误差补偿。核心是二阶近似下的顺序更新：

\[
\delta_t = w_t-\hat w_t,
\]
\[
W_{:,\,t+1:B}
\,\leftarrow\,
W_{:,\,t+1:B}
-\frac{\delta_t}{(H_b^{-1})_{tt}}(H_b^{-1})_{t,\,t+1:B}.
\]

这里 \(H_b\) 是块内输入相关的 Hessian 子矩阵。  
`gptq_act_order` 对列顺序进行重排，`gptq_true_sequential` 按 Transformer 子模块顺序分组执行，`dynamic_groups` 表示 qparams 在更新过程中动态重估，不静态缓存。

---

## 4. 交替更新 2bit 模块（Iterative Affine 2bit）

对某一行（或一个待量化向量）记为 \(x\in\mathbb{R}^{K}\)，码本整数为
\[
q_i\in\{0,1,2,3\}.
\]
仿射重建：
\[
\hat x_i = s\,q_i + o,
\]
其中 \(s>0\) 是 scale，\(o\) 是 offset（等价于 zero-point 参数化）。

在掩码 \(\Omega\)（仅保留元素）上最小化
\[
\min_{s,o,\{q_i\}} \sum_{i\in\Omega}(x_i-sq_i-o)^2.
\]

采用交替优化（本实验固定 20 次）：

1. **量化步（离散）**
\[
q_i \leftarrow \mathrm{clip}\!\left(\mathrm{round}\!\left(\frac{x_i-o}{s}\right),\,0,\,3\right).
\]

2. **scale 更新（闭式）**
\[
s \leftarrow
\frac{\sum_{i\in\Omega}(x_i-o)q_i}{\sum_{i\in\Omega} q_i^2 + \varepsilon}.
\]

3. **offset 更新（闭式）**
\[
o \leftarrow
\frac{1}{|\Omega|}\sum_{i\in\Omega}(x_i-sq_i).
\]

最后得到该组 2bit 仿射 qparams（\(s,o\) 或 \(s,zp\)）。

---

## 5. 权重回填模块（Post-GPTQ Refill）

该模块在 GPTQ 之后执行，目标是用极小额外非零权重减少输出通道误差。

### 5.1 误差定义

记：

- \(R^{\text{tgt}}\)：进入 GPTQ 前的残差目标（固定参考）
- \(R\)：GPTQ + 剪枝后当前残差
- \(\bar x\)：校准输入按 token 均值得到的激活均值向量

每个输出通道（行）误差代理：
\[
e_r
=
\sum_j \left(R^{\text{tgt}}_{rj}-R_{rj}\right)\bar x_j.
\]

### 5.2 两级筛选（节省开销）

1. 在“存在剪枝位”的行中，按 \(|e_r|\) 选 top \(40\%\) 行（`row_ratio=0.4`）。
2. 在每个选中行内，对剪枝位置 \(j\) 计算 proxy
\[
\mathrm{proxy}_{rj}
=
\max_{c\in\mathcal{C}_{r,g(j)}}|c|\cdot|\bar x_j|,
\]
再选 top \(40\%\) 位置（`pos_ratio=0.4`）。

其中 \(\mathcal{C}_{r,g}\) 是该行该组的量化码本实值集合（2bit 下 4 个值）：
\[
\mathcal{C}_{r,g}

=
\left\{s_{r,g}(k-z_{r,g})\mid k=0,1,2,3\right\}.
\]

### 5.3 单位置最优回填

对候选位置 \((r,j)\)，固定当前行误差 \(e_r\)，求
\[
c^\star
=
\arg\min_{c\in\mathcal{C}_{r,g(j)}}|e_r-c\bar x_j|.
\]

若
\[
|e_r-c^\star\bar x_j| < |e_r|,
\]
则接受回填并更新
\[
R_{rj}\leftarrow c^\star,\qquad
e_r\leftarrow e_r-c^\star\bar x_j.
\]

若 \(c^\star=0\) 或无改进，则该位置仍视作剪枝位。  
平均比特统计时，仅“回填为非零”的位置计入非剪枝权重。

---

## 6. 整体 Pipeline（数学视角）

可写成分阶段优化：

\[
\textbf{Stage A:}\quad
W \xrightarrow{\text{SVD+4bit low-rank}} \hat L,\; R=W-\hat L.
\]
\[
\textbf{Stage B:}\quad
\forall b,\;
m_b^\star=\arg\min_{m\in\mathcal M}
\|R_b-\widetilde R_b^{(m)}\|_F^2
\quad(\text{Pass-1, no GPTQ}).
\]
\[
\textbf{Stage C:}\quad
\hat R=\text{Block-GPTQ}(R,\{M_b^\star\})
\quad(\text{Pass-2, fixed mask}).
\]
\[
\textbf{Stage D:}\quad
\hat R_{\text{refill}}
=
\text{GreedyRefill}(\hat R, R^{\text{tgt}}, \bar x).
\]
\[
\hat W = \hat L + \hat R_{\text{refill}}.
\]

该分解把“低秩近似、结构稀疏、低比特量化、二阶补偿、轻量回填”拆成可控模块：

- SVD：先抽主能量，降低残差难度；
- 搜索剪枝：先定结构，再做二阶补偿，减少分支耦合；
- 交替 2bit：给每组更稳定的仿射 qparams；
- 回填：用很少的新非零权重，定向修复高误差通道。

---

## 7. Overleaf 可直接使用的算法块

建议在 Overleaf 导言区加入：

```latex
\usepackage{amsmath,amssymb}
\usepackage{algorithm}
\usepackage{algpseudocode}
```

### 7.1 交替更新 2bit（固定 20 次）

```latex
\begin{algorithm}[t]
\caption{Masked Iterative Affine 2-bit Quantization (Fixed 20 Iterations)}
\label{alg:iter2bit}
\begin{algorithmic}[1]
\Require vector (or row) $x$, mask $\Omega$, bit-width $b=2$, iterations $T=20$
\Ensure quantized $\hat{x}$ and affine parameters $(s,o)$
\State Initialize $s,o$ from masked min/max affine mapping
\For{$t=1$ to $T$}
  \State $q_i \leftarrow \mathrm{clip}\!\left(\mathrm{round}\!\left(\frac{x_i-o}{s}\right),0,2^b-1\right),\ \forall i\in\Omega$
  \State $s \leftarrow \dfrac{\sum_{i\in\Omega}(x_i-o)q_i}{\sum_{i\in\Omega}q_i^2+\varepsilon}$
  \State $o \leftarrow \dfrac{1}{|\Omega|}\sum_{i\in\Omega}(x_i-sq_i)$
\EndFor
\State $\hat{x}_i \leftarrow s q_i + o,\ \forall i\in\Omega$; keep unmasked entries unchanged
\State \Return $\hat{x}, s, o$
\end{algorithmic}
\end{algorithm}
```

### 7.2 搜索剪枝（2Pass，先选 m 再 GPTQ）

```latex
\begin{algorithm}[t]
\caption{Two-Pass Block Row-Prune Search with Fixed-Mask Block-GPTQ}
\label{alg:rowprune2pass}
\begin{algorithmic}[1]
\Require residual matrix $R$, block size $B=128$, candidate set $\mathcal{M}$
\Ensure quantized residual $\hat{R}$ and fixed masks $\{M_b^\star\}$
\For{each block $b$ in columns of $R$}
  \For{each $m \in \mathcal{M}$}
    \State Prune $m$ smallest $|R_{rj}|$ per row in block $b$ to form mask $M_b^{(m)}$
    \State Quantize kept entries by iterative 2-bit (no GPTQ) to get $\widetilde{R}_b^{(m)}$
    \State $J_b(m) \leftarrow \|R_b-\widetilde{R}_b^{(m)}\|_F^2$
  \EndFor
  \State $m_b^\star \leftarrow \arg\min_{m\in\mathcal{M}} J_b(m)$
  \State Fix $M_b^\star \leftarrow M_b^{(m_b^\star)}$
\EndFor
\State Run Block-GPTQ on $R$ under fixed masks $\{M_b^\star\}$ to obtain $\hat{R}$
\State \Return $\hat{R}, \{M_b^\star\}$
\end{algorithmic}
\end{algorithm}
```

---

## 8. 一句话总结

这个方法的本质是：  
**用 SVD 把“主能量”先拿走，再在残差上先搜索结构（不带 GPTQ）后做二阶补偿（带 GPTQ），最后用小比例回填做定向误差修复。**  
它不是单一量化技巧，而是一个分阶段、可解释、可控计算开销的联合优化 pipeline。

