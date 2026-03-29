"""压缩后立即评估（模拟 OBR 原版 main.py 的流程）"""
import os, sys
sys.path.insert(0, '.')
sys.path.insert(0, 'external_repos/OBR/FlatQuant')
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import torch
import math
from flatquant import utils, model_utils, data_utils, train_utils, flat_utils
from flatquant import obr_utils
from backend.model_compression.obr_wrapper import OBRCompressor
import transformers

model_path = '/root/autodl-tmp/models/base/Qwen3.5-9B'

c = OBRCompressor(model_name=model_path, output_dir='models/qwen-obr',
                  w_bits=4, a_bits=16, k_bits=4, v_bits=4, nsamples=2)
args = c._build_obr_args()
args.nsamples = 2
args.epochs = 1

utils.seed_everything(seed=0)
print("加载模型...")
model, apply_fq = model_utils.get_model(args.model, None)
model.eval()

tokenizer = transformers.AutoTokenizer.from_pretrained(args.model, use_fast=False, trust_remote_code=True)

print("加载校准数据...")
trainloader = data_utils.get_loaders(args, args.cali_dataset, nsamples=2,
    seed=0, model=args.model, seqlen=model.seqlen, eval_mode=False)

print("FlatQuant 包装...")
model = apply_fq(args, model)

print("校准训练 (1 epoch, 2 samples)...")
train_utils.cali_flat_quant(args, model, trainloader, utils.DEV, logger=__import__('logging').getLogger())

print("重参数化...")
flat_utils.reparameterize_model(model)

print("OBR 量化...")
quantizers = obr_utils.obr_fwrd(model, trainloader, utils.DEV, args)

# 直接在同一个 model 对象上评估（不保存/加载）
print("\n=== 直接评估（不保存/加载）===")
from datasets import load_dataset

dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
texts = dataset["text"][:128]
text = "\n\n".join(texts)
encodings = tokenizer(text, return_tensors="pt")
input_ids = encodings.input_ids

model.eval()
device = next(model.parameters()).device

# 确保 rotary_emb 在正确设备上
if hasattr(model.model, 'rotary_emb'):
    model.model.rotary_emb = model.model.rotary_emb.to(device)

nlls = []
stride = 1024
max_length = 2048

for begin_loc in range(0, min(input_ids.size(1) - max_length, 20000), stride):
    end_loc = begin_loc + max_length
    input_chunk = input_ids[:, begin_loc:end_loc].to(device)
    target_chunk = input_chunk.clone()
    target_chunk[:, :stride] = -100
    
    with torch.no_grad():
        outputs = model(input_chunk, labels=target_chunk)
        neg_log_likelihood = outputs.loss
    
    nlls.append(neg_log_likelihood.item())

ppl = math.exp(sum(nlls) / len(nlls)) if nlls else 0
print(f"直接评估 PPL: {ppl:.4f}")

# 然后保存再加载评估
print("\n=== 保存后重新加载评估 ===")
torch.save(model.state_dict(), '/tmp/test_model.pt')

# 重建模型
model2, apply_fq2 = model_utils.get_model(args.model, None)
model2.eval()
model2 = apply_fq2(args, model2)

# 方案 D：只 to_eval_mode，不 reparameterize
for m in model2.modules():
    if hasattr(m, 'to_eval_mode') and hasattr(m, '_eval_mode') and not m._eval_mode:
        m.to_eval_mode()

sd = torch.load('/tmp/test_model.pt', map_location='cpu')
missing, unexpected = model2.load_state_dict(sd, strict=False)
print(f"missing={len(missing)}, unexpected={len(unexpected)}")

for m in model2.modules():
    if hasattr(m, '_eval_mode'):
        m._eval_mode = True
    if hasattr(m, '_ori_mode'):
        m._ori_mode = False

model2 = model2.to(device).eval()

nlls2 = []
for begin_loc in range(0, min(input_ids.size(1) - max_length, 20000), stride):
    end_loc = begin_loc + max_length
    input_chunk = input_ids[:, begin_loc:end_loc].to(device)
    target_chunk = input_chunk.clone()
    target_chunk[:, :stride] = -100
    
    with torch.no_grad():
        outputs = model2(input_chunk, labels=target_chunk)
        neg_log_likelihood = outputs.loss
    
    nlls2.append(neg_log_likelihood.item())

ppl2 = math.exp(sum(nlls2) / len(nlls2)) if nlls2 else 0
print(f"重新加载后 PPL: {ppl2:.4f}")

print(f"\n直接评估: {ppl:.4f}")
print(f"重新加载: {ppl2:.4f}")
print(f"差异: {abs(ppl2 - ppl):.4f}")
