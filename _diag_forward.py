"""诊断：逐层检查 forward 输出是否合理"""
import os, sys
sys.path.insert(0, '.')
sys.path.insert(0, 'external_repos/OBR/FlatQuant')
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import torch
from flatquant import model_utils, flat_utils
from backend.model_compression.obr_wrapper import OBRCompressor

model_path = '/root/autodl-tmp/models/base/Qwen3.5-9B'

# 加载压缩模型
c = OBRCompressor(model_name=model_path, output_dir='models/qwen-obr',
                  w_bits=4, a_bits=16, k_bits=4, v_bits=4)
args = c._build_obr_args()

print("加载模型 + FlatQuant 包装 + reparameterize...")
model, apply_fq = model_utils.get_model(args.model, None)
model.eval()
model = apply_fq(args, model)
flat_utils.reparameterize_model(model)

print("加载压缩权重...")
sd = torch.load('models/qwen-obr/quantized_model.pt', map_location='cpu')
model.load_state_dict(sd, strict=False)

for m in model.modules():
    if hasattr(m, '_eval_mode'):
        m._eval_mode = True
    if hasattr(m, '_ori_mode'):
        m._ori_mode = False

# 也加载一个纯 FP16 模型做对比（不加载压缩权重）
print("加载 FP16 对比模型...")
model_fp16, _ = model_utils.get_model(args.model, None)
model_fp16.eval()

# 逐层对比 forward 输出
print("\n=== 逐层 forward 对比 ===")
dev = torch.device('cuda')
model.model.embed_tokens = model.model.embed_tokens.to(dev)
model_fp16.model.embed_tokens = model_fp16.model.embed_tokens.to(dev)
if hasattr(model.model, 'rotary_emb'):
    model.model.rotary_emb = model.model.rotary_emb.to(dev)
if hasattr(model_fp16.model, 'rotary_emb'):
    model_fp16.model.rotary_emb = model_fp16.model.rotary_emb.to(dev)

from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
inputs = tokenizer("Hello world", return_tensors="pt").to(dev)

# 获取 embedding 输出
with torch.no_grad():
    emb_obr = model.model.embed_tokens(inputs['input_ids'])
    emb_fp16 = model_fp16.model.embed_tokens(inputs['input_ids'])
    print(f"Embedding diff: {(emb_obr - emb_fp16).abs().max():.6f}")

# 逐层 forward
hidden_obr = emb_obr.clone()
hidden_fp16 = emb_fp16.clone()

for i in range(min(4, len(model.model.layers))):
    layer_obr = model.model.layers[i].to(dev)
    layer_fp16 = model_fp16.model.layers[i].to(dev)
    
    with torch.no_grad():
        try:
            pos_ids = torch.arange(hidden_obr.shape[1], device=dev).unsqueeze(0)
            if hasattr(model.model, 'rotary_emb'):
                pe = model.model.rotary_emb(hidden_obr, pos_ids)
                out_obr = layer_obr(hidden_obr, position_ids=pos_ids, position_embeddings=pe)[0]
            else:
                out_obr = layer_obr(hidden_obr, position_ids=pos_ids)[0]
        except Exception as e:
            print(f"Layer {i} OBR forward 失败: {e}")
            break
        
        try:
            if hasattr(model_fp16.model, 'rotary_emb'):
                pe_fp16 = model_fp16.model.rotary_emb(hidden_fp16, pos_ids)
                out_fp16 = layer_fp16(hidden_fp16, position_ids=pos_ids, position_embeddings=pe_fp16)[0]
            else:
                out_fp16 = layer_fp16(hidden_fp16, position_ids=pos_ids)[0]
        except Exception as e:
            print(f"Layer {i} FP16 forward 失败: {e}")
            break
    
    diff = (out_obr - out_fp16).abs()
    layer_type = "linear_attn" if hasattr(layer_obr, 'linear_attn') else "self_attn"
    print(f"Layer {i} ({layer_type}): max_diff={diff.max():.4f}, mean_diff={diff.mean():.6f}, "
          f"obr_std={out_obr.std():.6f}, fp16_std={out_fp16.std():.6f}")
    
    hidden_obr = out_obr
    hidden_fp16 = out_fp16
    
    model.model.layers[i] = layer_obr.cpu()
    model_fp16.model.layers[i] = layer_fp16.cpu()
    torch.cuda.empty_cache()
