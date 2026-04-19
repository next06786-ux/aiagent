# OBR + llmquant 融合压缩方案

## 1. 背景

项目中有两个模型压缩技术：

- **OBR (FlatQuant)**：FlatQuant 变换矩阵学习 + GPTQ 量化 + WANDA 稀疏化。优势在于通过学习线性变换让权重分布更均匀，量化误差更小。当前配置 W4 + 50% 稀疏，平均约 2-3 bit/权重。
- **llmquant (BiLLM/BRAGPTQ)**：SVD 低秩分解 + 二值/多比特残差量化 + 自适应 rank 分配 + 行剪枝搜索 + Hessian 补偿。优势在于极低比特量化（1-2 bit），通过 SVD 把权重拆成低秩+残差两部分分别处理。

两者单独使用都有效，但各有局限：
- OBR 单独用：W4 已经是它的下限，无法进一步压缩
- llmquant 单独用：没有 FlatQuant 的变换优化，直接量化的误差更大

## 2. 融合核心思路

**用 OBR 的 FlatQuant 变换优化权重分布，再用 llmquant 的 SVD + 残差量化做极低比特压缩。**

具体流程（逐层执行）：

```
原始权重 W
    │
    ▼
[阶段 1] FlatQuant 变换学习（来自 OBR）
    │  学习最优线性变换矩阵 T，使 T·W 的分布更均匀
    │  校准训练 15 epochs，逐层优化
    ▼
变换后权重 W' = T·W
    │
    ▼
[阶段 2] 重参数化（来自 OBR）
    │  把变换矩阵 T 融合进权重：W_flat = reparameterize(W')
    ▼
平坦化权重 W_flat（分布更均匀，量化友好）
    │
    ▼
[阶段 3] SVD 低秩分解（来自 llmquant）
    │  W_flat = L + R
    │  L = U·S·V^T（低秩部分，rank 自适应分配）
    │  R = W_flat - L（残差部分）
    ▼
低秩部分 L          残差部分 R
    │                    │
    ▼                    ▼
[阶段 4a]            [阶段 4b]
4-bit 量化            GPTQ 列补偿量化（来自 llmquant）
L_q = quant_4bit(L)   + 行剪枝搜索
                      + 二值残差逼近（显著列 4-bit，非显著列 2-bit）
                      + Hessian 误差补偿
                      R_q = BRAGPTQ(R)
    │                    │
    ▼                    ▼
[阶段 5] 合并：W_compressed = L_q + R_q
    │
    ▼
最终压缩权重（平均 ~1.5-2.5 bit/权重）
```

## 3. 为什么融合比单独用更好

| 对比维度 | OBR 单独 | llmquant 单独 | 融合方案 |
|---------|---------|-------------|---------|
| 平均比特 | ~2-3 bit (W4+稀疏) | ~1.1-2 bit | ~1.5-2.5 bit |
| 权重分布优化 | ✅ FlatQuant | ❌ 无 | ✅ FlatQuant |
| SVD 低秩分解 | ❌ 无 | ✅ 自适应 rank | ✅ 自适应 rank |
| 残差精细量化 | GPTQ 4-bit | 二值+Hessian 补偿 | 二值+Hessian 补偿 |
| 显存占用 (9B) | ~3-5 GB | ~2-3 GB | ~2-3 GB |
| PPL 增长 | <0.5 | ~1-2 | <1.0 (预期) |

融合的关键收益：FlatQuant 让权重分布更均匀后，SVD 分解的低秩部分能捕获更多能量（因为奇异值分布更集中），残差更小，二值量化的误差也更小。


## 4. 技术实现细节

### 4.1 阶段 1-2：FlatQuant 变换（复用现有 OBR 代码）

完全复用当前 `qwen_utils.py` 中的 FlatQuant 包装和校准训练流程：

```python
# 已有代码，无需修改
model, apply_flatquant = model_utils.get_model(args.model, None)
model = apply_flatquant(args, model)                    # 包装 FlatQuantizedLinear
train_utils.cali_flat_quant(args, model, trainloader)   # 校准训练
flat_utils.reparameterize_model(model)                  # 融合变换到权重
```

执行完后，模型权重已经是"平坦化"的，分布更均匀。

### 4.2 阶段 3-4：SVD + 残差量化（调用 llmquant 的 BRAGPTQ）

在 FlatQuant 重参数化之后，替换 OBR 原来的 `obr_utils.obr_fwrd`，改用 llmquant 的 `quant_sequential`：

```python
# 核心改动：用 llmquant 的逐层量化替代 OBR 的 obr_fwrd
from llmquant.bigptq import BRAGPTQ
from llmquant.binary import Binarization
from llmquant.run import quant_sequential

# FlatQuant 重参数化后的模型
# 现在用 llmquant 做 SVD + 残差量化
quant_sequential(model, trainloader, device)
```

BRAGPTQ.fasterquant 的关键参数配置：

```python
fasterquant_kwargs = {
    # SVD 低秩分解
    "svd_enable": True,
    "svd_rank": 256,                    # 默认 rank，自适应时会被覆盖
    
    # 自适应 rank 分配（基于激活熵和稳定秩）
    # 由 run.py 的 adaptive_rank 逻辑在外层控制
    
    # 残差量化方法
    "quant_method": "4bit",             # 残差基础量化位数
    "block_gptq_enable": True,          # 启用 GPTQ 列补偿
    "gptq_groupsize": 128,             # 量化分组大小
    "gptq_act_order": True,            # 按激活重要性排序列
    
    # 行剪枝搜索（进一步压缩残差）
    "svd_row_prune_search_enable": True,
    "svd_row_prune_m_candidates": [0, 4, 8, 16, 32, 64],
    "svd_row_prune_score_metric": "wanda",
    "svd_row_prune_quant_scheme": "std4bit",
    
    # OBR 两组残差策略
    "svd_2bit_obr_twogroup_adaptive_enable": True,
    "svd_2bit_obr_twogroup_adaptive_max_stages": 3,
    "svd_2bit_obr_twogroup_adaptive_e128_threshold": 0.2,
    "svd_2bit_obr_twogroup_adaptive_base_ratio": 0.1,
    
    # Hessian 补偿
    "obr": True,
    
    # 后处理 refill
    "post_gptq_refill_enable": True,
    "post_gptq_refill_row_ratio": 0.2,
    "post_gptq_refill_pos_ratio": 0.2,
}
```

### 4.3 自适应 Rank 分配

llmquant 的自适应 rank 分配算法（`allocate_ranks`）基于：

1. **激活熵**：每层收集激活值的特征标准差，计算几何平均作为激活熵。激活熵高的层（信息复杂）分配更多 rank。
2. **稳定秩**：`r_stable = ||W||_F^2 / ||W||_2^2`。稳定秩高的层（谱分布平缓）需要更多 rank 才能捕获足够能量。
3. **SVD 能量表**：预计算每层在不同 rank 下的 MSE，构建熵减表，用贪心算法在总预算约束下分配最优 rank。

分配策略：
- 总预算 = 层数 × 平均 rank（如 32 × 256 = 8192）
- 每层 rank 范围：[128, 512]
- q_proj/k_proj 通常分配较低 rank（信息简单，稳定秩低）
- v_proj/mlp 通常分配较高 rank（信息复杂，稳定秩高）

### 4.4 Qwen3.5-9B 混合架构适配

Qwen3.5-9B 有两种层：
- 24 层 GatedDeltaNet（linear_attn）：拆分后的 q/k/v_proj + in_proj_z/b/a + out_proj
- 8 层标准 self_attn：q/k/v/o_proj

llmquant 的 `quant_sequential` 通过 `find_layers` 自动发现所有 `nn.Linear` 层，不区分层类型。但需要确保：

1. FlatQuant 重参数化后，拆分的 q/k/v_proj 权重已正确融合变换矩阵
2. GatedDeltaNet 的 conv1d 不参与量化（它不是 Linear 层）
3. `forward_layer_with_position` 能正确处理两种层类型的 forward 签名

## 5. 新增文件和修改

### 5.1 新增文件

```
backend/model_compression/
├── fusion_compressor.py          # 融合压缩器（核心）
└── compress_base_model_fusion.py # 融合压缩入口脚本
```

### 5.2 修改文件

```
backend/model_compression/obr_wrapper.py   # 添加 fusion 模式
backend/llm/model_config.py                # 添加融合压缩模型配置
backend/main.py                            # 添加融合压缩 API 端点
```


## 6. fusion_compressor.py 核心设计

务实方案的关键：修正激活统计，确保 Hessian 和激活收集基于 FlatQuant 变换后的分布。

```
具体执行顺序（逐层）：

1. FlatQuant 包装（apply_flatquant_to_model）
   → 所有 Linear 被 FlatQuantizedLinear 包装
   → 变换矩阵 ln_trans/out_trans/vcache_trans/kcache_trans 已创建

2. FlatQuant 校准训练（cali_flat_quant）
   → 逐层优化变换矩阵，最小化量化重建误差
   → 此时模型 forward 经过 ln_trans 变换

3. 用 FlatQuant 包装后的模型跑 forward 收集激活
   → 激活经过了 ln_trans 变换，统计准确
   → 收集 Hessian 矩阵 H = X^T X
   → 收集激活熵、稳定秩（用于自适应 rank）

4. FlatQuant 重参数化（reparameterize_model）
   → 变换矩阵融合进权重
   → 权重变成"平坦化"的

5. llmquant 逐层量化（用步骤 3 收集的 Hessian）
   → SVD 分解平坦化权重
   → BRAGPTQ 残差量化 + 行剪枝 + Hessian 补偿
   → 自适应 rank 分配

6. 保存压缩模型
```

```python
class FusionCompressor:
    """
    OBR + llmquant 融合压缩器（务实方案）
    
    核心改进：在 FlatQuant 包装状态下收集激活统计，
    确保 Hessian 和激活熵基于变换后的分布计算。
    """
    
    def __init__(self, model_name, output_dir, **kwargs):
        self.model_name = model_name
        self.output_dir = output_dir
        # FlatQuant 参数（复用 OBR）
        self.w_bits = kwargs.get('w_bits', 4)
        self.a_bits = kwargs.get('a_bits', 16)
        self.k_bits = kwargs.get('k_bits', 4)
        self.v_bits = kwargs.get('v_bits', 4)
        self.nsamples = kwargs.get('nsamples', 128)
        self.cali_dataset = kwargs.get('cali_dataset', 'wikitext2')
        # llmquant 参数
        self.svd_rank = kwargs.get('svd_rank', 256)
        self.adaptive_rank = kwargs.get('adaptive_rank', True)
        self.avg_rank = kwargs.get('avg_rank', 256)
        self.min_rank = kwargs.get('min_rank', 128)
        self.max_rank = kwargs.get('max_rank', 512)
        self.quant_method = kwargs.get('quant_method', '4bit')
        self.blocksize = kwargs.get('blocksize', 128)
    
    def compress(self):
        """执行融合压缩"""
        # 阶段 1: 加载模型 + FlatQuant 包装
        model, trainloader = self._load_and_wrap()
        
        # 阶段 2: FlatQuant 校准训练
        self._flatquant_calibrate(model, trainloader)
        
        # 阶段 3: 收集变换后的激活统计（关键改进）
        hessians, activation_stats = self._collect_transformed_stats(
            model, trainloader
        )
        
        # 阶段 4: 重参数化
        self._reparameterize(model)
        
        # 阶段 5: llmquant SVD + 残差量化（使用步骤 3 的统计）
        self._llmquant_quantize(model, trainloader, hessians, activation_stats)
        
        # 阶段 6: 保存
        self._save_model(model)
```

## 7. 压缩入口脚本使用方式

```bash
# 融合压缩（推荐）
HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python backend/model_compression/compress_base_model_fusion.py \
  --model /root/autodl-tmp/models/base/Qwen3.5-9B \
  --output models/qwen-fusion \
  --svd-rank 256 \
  --adaptive-rank \
  --avg-rank 256 \
  --quant-method 4bit \
  --blocksize 128 \
  --nsamples 128

# 对比：纯 OBR 压缩（当前方案）
python backend/model_compression/compress_base_model.py \
  --model /root/autodl-tmp/models/base/Qwen3.5-9B \
  --output models/qwen-obr \
  --w-bits 4 --sparsity 0.5 --nsamples 128
```

## 8. 预期效果对比

| 指标 | 纯 OBR | 纯 llmquant | 融合方案 |
|------|--------|------------|---------|
| 显存占用 (9B) | 3-5 GB | 2-3 GB | 2-3 GB |
| 平均 bit/权重 | ~2-3 | ~1.5-2.5 | ~1.5-2.5 |
| PPL 增长 (WikiText2) | <0.5 | ~1-2 | <1.0 |
| 压缩耗时 | ~1-2 小时 | ~1-2 小时 | ~2-3 小时 |
| 推理速度提升 | ~30-40% | ~40-60% | ~40-60% |

融合方案的 PPL 预期比纯 llmquant 更低（因为 FlatQuant 优化了权重分布），同时保持 llmquant 的极致压缩比。

## 9. 实施步骤

### Phase 1：先跑完纯 OBR 压缩（当前进行中）
- 验证 OBR 压缩模型可用
- 记录 PPL 基线

### Phase 2：实现 fusion_compressor.py
- 复用 OBR 的 FlatQuant 阶段
- 集成 llmquant 的 quant_sequential
- 适配 Qwen3.5-9B 混合架构

### Phase 3：跑融合压缩
- 对比纯 OBR vs 融合方案的 PPL
- 如果融合方案 PPL 更优，切换为默认压缩方案

### Phase 4：推理集成
- 更新 inference_integration.py 支持融合压缩模型格式
- 更新 model_config.py 添加融合模型配置

## 10. 风险和注意事项

1. **FlatQuant 重参数化后的权重格式**：重参数化会修改权重值但不改变形状，llmquant 的 `find_layers` 能正常发现所有 Linear 层。但拆分后的 GatedDeltaNet q/k/v_proj 是新创建的 Linear，需要确保它们在重参数化后被正确注册到模型中。

2. **校准数据一致性**：FlatQuant 和 llmquant 都需要校准数据。应使用同一份 wikitext2 数据，避免分布不一致。

3. **显存峰值**：融合压缩的峰值显存 = 模型 FP16 + FlatQuant 变换矩阵 + llmquant 的 Hessian 矩阵。对 9B 模型约需 25-30GB，4080 SUPER 32GB 够用。

4. **llmquant 的 `quant_sequential` 依赖全局 `args`**：需要构造一个兼容的 args 对象，或者重构为参数传递方式。

---

**维护者**：LifeSwarm 开发团队
**最后更新**：2026 年 3 月
**相关文件**：`external_repos/llmquant/`, `external_repos/OBR/`, `backend/model_compression/`
