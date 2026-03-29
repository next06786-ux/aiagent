import json
with open('/root/autodl-tmp/models/base/Qwen3.5-9B/config.json') as f:
    c = json.load(f)
for k in ['hidden_size', 'num_attention_heads', 'num_key_value_heads', 'head_dim',
          'intermediate_size', 'num_hidden_layers']:
    print(f'{k}: {c.get(k)}')
