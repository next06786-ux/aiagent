"""最小测试：只测 layer 0 的 forward 是否正常"""
import os, sys
sys.path.insert(0, '.')
sys.path.insert(0, 'external_repos/OBR/FlatQuant')
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import torch
from flatquant import model_utils, flat_utils
from backend.model_compression.obr_wrapper import OBRCompressor

model_path = '/root/autodl-tmp/models/base/Qwen3.5-9B'
dev = torch.device('cuda')

c = OBRCompressor(model_name=model_path, output_dir='models/qwen-obr',
                  w_bits=4, a_bits=16, k_bits=4, v_bits=4)
args = c._build_obr_args()

# 加载 state_dict，看 layer 0 的 key
print("读取 state_dict keys...")
sd = torch.load('models/qwen-obr/quantized_model.pt', map_location='cpu')
l0_keys = sorted([k for k in sd.keys() if 'layers.0.' in k])
print(f"Layer 0 共 {len(l0_keys)} 个 key:")
for k in l0_keys[:5]:
    print(f"  {k}: {sd[k].shape}")
print("  ...")

# 加载 FP16 模型，取 layer 0 的输出作为参考
print("\n加载 FP16 模型...")
from transformers import AutoModelForCausalLM, AutoTokenizer
model_fp16 = AutoModelForCausalLM.from_pretrained(
    model_path, torch_dtype=torch.float16, device_map='cpu', trust_remote_code=True
)
model_fp16.eval()

# 构造测试输入
torch.manual_seed(42)
x = torch.randn(1, 4, 4096, dtype=torch.float16)
layer0_fp16 = model_fp16.model.layers[0]

# FP16 layer 0 forward
with torch.no_grad():
    try:
        pos_ids = torch.arange(4).unsqueeze(0)
        pe = model_fp16.model.rotary_emb(x, pos_ids)
        out_fp16 = layer0_fp16(x, position_ids=pos_ids, position_embeddings=pe)[0]
    except Exception as e:
        print(f"FP16 forward 失败: {e}")
        out_fp16 = None

if out_fp16 is not None:
    print(f"FP16 layer 0 output: std={out_fp16.std():.6f}, mean={out_fp16.mean():.6f}")

del model_fp16
torch.cuda.empty_cache()

# 加载压缩模型，测试不同加载方式
print("\n加载压缩模型...")
import transformers as _tf
model = _tf.AutoModelForCausalLM.from_pretrained(
    model_path, torch_dtype=torch.float16, device_map='cpu', trust_remote_code=True
)
model.seqlen = 2048
from flatquant.model_tools.qwen_utils import apply_flatquant_to_qwen
apply_fq = apply_flatquant_to_qwen
model.eval()
model = apply_fq(args, model)

# 方案 D：只 to_eval_mode，不 reparameterize
for m in model.modules():
    if hasattr(m, 'to_eval_mode') and hasattr(m, '_eval_mode') and not m._eval_mode:
        m.to_eval_mode()

# 方案 D：只 to_eval_mode，不 reparameterize
for m in model.modules():
    if hasattr(m, 'to_eval_mode') and hasattr(m, '_eval_mode') and not m._eval_mode:
        m.to_eval_mode()

# 先测不加载 state_dict 的 forward（只有 FlatQuant 包装 + to_eval_mode）
layer0_noload = model.model.layers[0].to(dev)
model.model.rotary_emb = model.model.rotary_emb.to(dev)
x_gpu = x.to(dev)
with torch.no_grad():
    try:
        pos_ids = torch.arange(4).unsqueeze(0).to(dev)
        pe = model.model.rotary_emb(x_gpu, pos_ids)
        out_noload = layer0_noload(x_gpu, position_ids=pos_ids, position_embeddings=pe)[0]
        print(f"不加载state_dict layer 0: std={out_noload.std():.6f}")
    except Exception as e:
        print(f"不加载state_dict forward 失败: {e}")
model.model.layers[0] = layer0_noload.cpu()
torch.cuda.empty_cache()

# 过滤形状不匹配的 key，然后加载
current_sd = model.state_dict()
filtered_sd = {}
skipped = []
for k, v in sd.items():
    if k in current_sd and current_sd[k].shape != v.shape:
        skipped.append(f"{k}: ckpt={v.shape} vs model={current_sd[k].shape}")
    else:
        filtered_sd[k] = v

if skipped:
    print(f"跳过 {len(skipped)} 个形状不匹配的 key:")
    for s in skipped[:5]:
        print(f"  {s}")

# 检查 layernorm 权重
ln_w = sd.get('model.layers.0.input_layernorm.weight')
if ln_w is not None:
    print(f"\nstate_dict input_layernorm.weight: std={ln_w.std():.6f}, max={ln_w.abs().max():.6f}")
    print(f"  (FP16 原始值应该接近 1.0)")

missing, unexpected = model.load_state_dict(filtered_sd, strict=False)
print(f"方案D加载: missing={len(missing)}, unexpected={len(unexpected)}")
if missing:
    print(f"  缺失: {missing[:3]}")

for m in model.modules():
    if hasattr(m, '_eval_mode'):
        m._eval_mode = True
    if hasattr(m, '_ori_mode'):
        m._ori_mode = False

# 把 layer 0 搬到 GPU 测试
layer0 = model.model.layers[0].to(dev)
model.model.rotary_emb = model.model.rotary_emb.to(dev)
x_gpu = x.to(dev)

with torch.no_grad():
    try:
        pos_ids = torch.arange(4).unsqueeze(0).to(dev)
        pe = model.model.rotary_emb(x_gpu, pos_ids)
        out_obr = layer0(x_gpu, position_ids=pos_ids, position_embeddings=pe)[0]
        print(f"方案D layer 0 output: std={out_obr.std():.6f}, mean={out_obr.mean():.6f}")
        if out_fp16 is not None:
            diff = (out_obr.cpu() - out_fp16).abs()
            print(f"  与FP16差异: max={diff.max():.4f}, mean={diff.mean():.6f}")
    except Exception as e:
        print(f"方案D forward 失败: {e}")
        import traceback; traceback.print_exc()
