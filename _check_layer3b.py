import torch
from transformers import AutoModelForCausalLM
m = AutoModelForCausalLM.from_pretrained(
    "/root/autodl-tmp/models/base/Qwen3.5-9B",
    torch_dtype=torch.float16, device_map="cpu", trust_remote_code=True
)
l3 = m.model.layers[3]
attn = l3.self_attn
print("type:", type(attn).__name__)
print("config attrs:")
for attr in ['hidden_size', 'num_heads', 'num_key_value_heads', 'head_dim',
             'num_attention_heads', 'config']:
    if hasattr(attn, attr):
        val = getattr(attn, attr)
        if attr == 'config':
            print(f"  config.num_attention_heads: {val.num_attention_heads}")
            print(f"  config.num_key_value_heads: {val.num_key_value_heads}")
            print(f"  config.head_dim: {val.head_dim}")
            print(f"  config.hidden_size: {val.hidden_size}")
        else:
            print(f"  {attr}: {val}")
    else:
        print(f"  {attr}: NOT FOUND")
print("all non-private attrs:")
for a in sorted(dir(attn)):
    if not a.startswith('_') and not callable(getattr(attn, a, None)):
        try:
            v = getattr(attn, a)
            if not isinstance(v, (torch.nn.Module, torch.nn.Parameter, torch.Tensor)):
                print(f"  {a}: {v}")
        except:
            pass
