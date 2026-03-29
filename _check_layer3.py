import torch
from transformers import AutoModelForCausalLM
m = AutoModelForCausalLM.from_pretrained(
    "/root/autodl-tmp/models/base/Qwen3.5-9B",
    torch_dtype=torch.float16, device_map="cpu", trust_remote_code=True
)
l3 = m.model.layers[3]
print("type:", type(l3.self_attn).__name__)
for n, p in l3.self_attn.named_parameters():
    if "proj" in n:
        print(f"  {n}: {p.shape}")
print("num_heads:", l3.self_attn.num_heads)
print("num_kv_heads:", l3.self_attn.num_key_value_heads)
print("head_dim:", l3.self_attn.head_dim)
