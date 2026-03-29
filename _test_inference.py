"""验证拆包后的压缩模型能否正常加载和推理"""
import os, sys
sys.path.insert(0, '.')
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = '/root/autodl-tmp/models/base/Qwen3.5-9B'
obr_weights = 'models/qwen-obr/quantized_model.pt'

if not os.path.exists(obr_weights):
    print(f"压缩模型不存在: {obr_weights}")
    print("请先跑完压缩")
    sys.exit(1)

# 直接用原始模型结构加载（拆包后 state_dict 是原始 key）
print("加载原始模型结构...")
model = AutoModelForCausalLM.from_pretrained(
    model_path, torch_dtype=torch.float16,
    device_map='auto', trust_remote_code=True
)

print("加载压缩权重...")
sd = torch.load(obr_weights, map_location='cpu')
missing, unexpected = model.load_state_dict(sd, strict=False)
print(f"missing={len(missing)}, unexpected={len(unexpected)}")
if missing:
    print(f"缺失: {missing[:5]}")
if unexpected:
    print(f"多余: {unexpected[:5]}")

model.eval()

# 权重诊断
for i in [0, 3]:
    layer = model.model.layers[i]
    if hasattr(layer, 'linear_attn'):
        w = layer.linear_attn.in_proj_qkv.weight
        print(f"L{i} linear_attn.in_proj_qkv: std={w.std():.6f}, zeros={(w==0).float().mean()*100:.1f}%")
    elif hasattr(layer, 'self_attn'):
        w = layer.self_attn.q_proj.weight
        print(f"L{i} self_attn.q_proj: std={w.std():.6f}, zeros={(w==0).float().mean()*100:.1f}%")

# 推理测试
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
inputs = tokenizer("The capital of France is", return_tensors="pt").to("cuda")
with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=20, do_sample=False)
    print(f"\n生成: {tokenizer.decode(out[0], skip_special_tokens=True)}")
