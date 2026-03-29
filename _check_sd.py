import torch
sd = torch.load('models/qwen-obr/quantized_model.pt', map_location='cpu')
# 检查 norm/layernorm 相关 key
norm_keys = [k for k in sd.keys() if 'norm' in k or 'layernorm' in k]
print("norm keys count:", len(norm_keys))
for k in norm_keys[:10]:
    print(" ", k, sd[k].shape)

# 检查 layer 0 的所有 key
l0_keys = [k for k in sd.keys() if 'layers.0.' in k]
print("\nlayer 0 keys count:", len(l0_keys))
for k in l0_keys:
    print(" ", k, sd[k].shape)

# 对比原始模型的 layer 0 key
from transformers import AutoModelForCausalLM
orig = AutoModelForCausalLM.from_pretrained(
    '/root/autodl-tmp/models/base/Qwen3.5-9B',
    torch_dtype=torch.float16, device_map='cpu', trust_remote_code=True
)
orig_l0 = [k for k in orig.state_dict().keys() if 'layers.0.' in k]
print("\norig layer 0 keys count:", len(orig_l0))
for k in orig_l0:
    print(" ", k, orig.state_dict()[k].shape)

# 检查权重值是否合理
w = sd.get('model.layers.0.linear_attn.q_proj.linear.weight')
if w is not None:
    print("\nq_proj weight stats: min={:.4f} max={:.4f} mean={:.4f} std={:.4f}".format(
        w.min().item(), w.max().item(), w.mean().item(), w.std().item()))
    print("zeros ratio: {:.4f}".format((w == 0).float().mean().item()))
