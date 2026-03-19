"""
快速测试 LoRA API
"""
import requests

BASE_URL = "http://localhost:8000"

print("测试 LoRA API...")
print()

# 1. 测试状态
print("1. 获取状态:")
response = requests.get(f"{BASE_URL}/api/lora/status/test_user_001")
result = response.json()
print(f"   Code: {result['code']}")
if result['code'] == 200:
    data = result['data']
    print(f"   ✅ 有模型: {data['has_model']}")
    print(f"   ✅ 版本: {data['model_version']}")
    print(f"   ✅ 数据量: {data['current_data_size']}/{data['min_data_size']}")
    
    # 显示调试信息
    if 'debug' in data:
        debug = data['debug']
        print(f"\n   🔍 调试信息:")
        print(f"      工作目录: {debug['cwd']}")
        print(f"      models 目录存在: {debug['models_dir_exists']}")
        print(f"      data 目录存在: {debug['data_dir_exists']}")
else:
    print(f"   ❌ {result['message']}")

print()

# 2. 测试列表
print("2. 列出模型:")
response = requests.get(f"{BASE_URL}/api/lora/models")
result = response.json()
print(f"   Code: {result['code']}")
if result['code'] == 200:
    models = result['data']['models']
    print(f"   ✅ 找到 {len(models)} 个模型")
    for model in models:
        print(f"      - {model['user_id']}: {model['version']}")
else:
    print(f"   ❌ {result['message']}")
