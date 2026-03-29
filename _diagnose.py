"""诊断：检查每个阶段的权重状态"""
import os, sys
sys.path.insert(0, '.')
sys.path.insert(0, 'external_repos/OBR/FlatQuant')
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import torch
from flatquant import model_utils, flat_utils
from backend.model_compression.obr_wrapper import OBRCompressor

model_path = '/root/autodl-tmp/models/base/Qwen3.5-9B'

c = OBRCompressor(model_name=model_path, output_dir='models/qwen-obr',
                  w_bits=4, a_bits=16, k_bits=4, v_bits=4)
args = c._build_obr_args()

print("=== 阶段 1: 加载原始模型 ===")
model, apply_fq = model_utils.get_model(args.model, None)
model.eval()

# 记录原始权重
orig_l3_qkvo = {}
l3 = model.model.layers[3]
for name in ['q_proj', 'k_proj', 'v_proj', 'o_proj']:
    w = getattr(l3.self_attn, name).weight.data
    orig_l3_qkvo[name] = w.clone()
    print(f"  原始 layer3.self_attn.{name}: shape={w.shape}, std={w.std():.6f}")

print("\n=== 阶段 2: FlatQuant 包装 ===")
model = apply_fq(args, model)

# 包装后的权重（应该跟原始一样，只是被 FlatQuantizedLinear 包了一层）
l3 = model.model.layers[3]
attn = l3.self_attn  # FlatQuantQwen3_5StdAttention
print(f"  包装类型: {type(attn).__name__}")
for name in ['q_proj', 'k_proj', 'v_proj', 'o_proj']:
    fql = getattr(attn, name)  # FlatQuantizedLinear
    w = fql.linear.weight.data
    diff = (w - orig_l3_qkvo[name].to(w.device)).abs().max().item()
    print(f"  包装后 {name}: std={w.std():.6f}, 与原始差异={diff:.8f}")

print("\n=== 阶段 3: 重参数化 ===")
flat_utils.reparameterize_model(model)

l3 = model.model.layers[3]
attn = l3.self_attn
for name in ['q_proj', 'k_proj', 'v_proj', 'o_proj']:
    fql = getattr(attn, name)
    w = fql.linear.weight.data
    diff = (w - orig_l3_qkvo[name].to(w.device)).abs().max().item()
    print(f"  重参数化后 {name}: std={w.std():.6f}, 与原始差异={diff:.8f}, eval_mode={fql._eval_mode}")

print("\n=== 阶段 4: 加载压缩权重 ===")
sd = torch.load('models/qwen-obr/quantized_model.pt', map_location='cpu')
# 只看 layer 3 的权重
for k in sorted(sd.keys()):
    if 'layers.3.' in k and 'proj' in k and 'linear.weight' in k:
        w = sd[k]
        print(f"  压缩文件 {k}: std={w.std():.6f}, zeros={((w==0).float().mean()*100):.1f}%")

# 加载
missing, unexpected = model.load_state_dict(sd, strict=False)
print(f"  missing={len(missing)}, unexpected={len(unexpected)}")

l3 = model.model.layers[3]
attn = l3.self_attn
for name in ['q_proj', 'k_proj', 'v_proj', 'o_proj']:
    fql = getattr(attn, name)
    w = fql.linear.weight.data
    print(f"  加载后 {name}: std={w.std():.6f}, zeros={((w==0).float().mean()*100):.1f}%")
