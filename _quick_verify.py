"""快速验证：只跑 2 层，检查量化后权重是否正常"""
import os, sys
sys.path.insert(0, '.')
sys.path.insert(0, 'external_repos/OBR/FlatQuant')
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import torch
import torch.nn as nn
from flatquant import utils, model_utils, data_utils, flat_utils
from flatquant import obr_utils
from flatquant.quant_utils import WeightQuantizer
from backend.model_compression.obr_wrapper import OBRCompressor

model_path = '/root/autodl-tmp/models/base/Qwen3.5-9B'

c = OBRCompressor(model_name=model_path, output_dir='/tmp/qwen-obr-test',
                  w_bits=4, a_bits=16, k_bits=4, v_bits=4, nsamples=2)
args = c._build_obr_args()
args.nsamples = 2
args.epochs = 1

utils.seed_everything(seed=0)
print("加载模型...")
# 强制加载到 CPU，避免 meta tensor offload
import transformers
model = transformers.AutoModelForCausalLM.from_pretrained(
    model_path, torch_dtype='auto', device_map='cpu',
    low_cpu_mem_usage=True, trust_remote_code=True
)
model.seqlen = 2048
from flatquant.model_tools.qwen_utils import apply_flatquant_to_qwen
apply_fq = apply_flatquant_to_qwen
model.eval()

print("加载校准数据 (2 samples)...")
trainloader = data_utils.get_loaders(args, args.cali_dataset, nsamples=2,
    seed=0, model=args.model, seqlen=model.seqlen, eval_mode=False)

# 记录原始权重
orig_stats = {}
for i in [0, 3]:  # layer 0 = linear_attn, layer 3 = self_attn
    layer = model.model.layers[i]
    if hasattr(layer, 'linear_attn'):
        for name in ['in_proj_qkv', 'out_proj']:
            w = getattr(layer.linear_attn, name).weight
            orig_stats[f"L{i}.{name}"] = w.std().item()
    elif hasattr(layer, 'self_attn'):
        for name in ['q_proj', 'k_proj', 'v_proj', 'o_proj']:
            w = getattr(layer.self_attn, name).weight
            orig_stats[f"L{i}.{name}"] = w.std().item()

print("\n原始权重 std:")
for k, v in orig_stats.items():
    print(f"  {k}: {v:.6f}")

print("\nFlatQuant 包装...")
model = apply_fq(args, model)

print("校准训练 (1 epoch, 2 samples)...")
from flatquant import train_utils
train_utils.cali_flat_quant(args, model, trainloader, utils.DEV, logger=__import__('logging').getLogger())

print("重参数化...")
flat_utils.reparameterize_model(model)

print("OBR 量化 (差异化: self_attn=W8, linear_attn=W4+50%稀疏)...")
quantizers = obr_utils.obr_fwrd(model, trainloader, utils.DEV, args)

# 检查量化后权重
print("\n\n=== 量化后权重 std ===")
for i in [0, 3]:
    layer = model.model.layers[i]
    if hasattr(layer, 'linear_attn'):
        attn = layer.linear_attn
        for name in ['q_proj', 'k_proj', 'v_proj', 'out_proj']:
            if hasattr(attn, name):
                fql = getattr(attn, name)
                w = fql.linear.weight if hasattr(fql, 'linear') else fql.weight
                zeros = (w == 0).float().mean().item() * 100
                print(f"  L{i} linear_attn.{name}: std={w.std():.6f}, zeros={zeros:.1f}%")
    elif hasattr(layer, 'self_attn'):
        attn = layer.self_attn
        for name in ['q_proj', 'k_proj', 'v_proj', 'o_proj']:
            if hasattr(attn, name):
                fql = getattr(attn, name)
                w = fql.linear.weight if hasattr(fql, 'linear') else fql.weight
                zeros = (w == 0).float().mean().item() * 100
                print(f"  L{i} self_attn.{name}: std={w.std():.6f}, zeros={zeros:.1f}%")
    # MLP
    mlp = layer.mlp
    for name in ['up_proj', 'gate_proj', 'down_proj']:
        fql = getattr(mlp, name)
        w = fql.linear.weight if hasattr(fql, 'linear') else fql.weight
        zeros = (w == 0).float().mean().item() * 100
        print(f"  L{i} mlp.{name}: std={w.std():.6f}, zeros={zeros:.1f}%")

# 快速推理测试
print("\n=== 快速推理测试 ===")
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

for m in model.modules():
    if hasattr(m, '_eval_mode'):
        m._eval_mode = True
    if hasattr(m, '_ori_mode'):
        m._ori_mode = False
model = model.to('cuda').eval()

inputs = tokenizer("The capital of France is", return_tensors="pt").to("cuda")
with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=20, do_sample=False)
    print("生成:", tokenizer.decode(out[0], skip_special_tokens=True))

print("\n完成!")
