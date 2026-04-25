#!/usr/bin/env python3
"""
测试远程GPU服务器连接
"""
import os
import sys
import httpx

# 从环境变量读取
REMOTE_URL = os.getenv("REMOTE_MODEL_URL", "https://u821458-b49a-bdca5515.westc.seetacloud.com:8443")

print("=" * 60)
print("测试远程GPU服务器连接")
print("=" * 60)
print(f"服务器地址: {REMOTE_URL}")
print()

# 创建客户端（支持HTTPS）
client = httpx.Client(
    timeout=httpx.Timeout(10.0, connect=5.0),
    verify=False  # AutoDL的自签名证书，需要禁用验证
)

# 测试1: 根路径
print("测试1: 根路径 /")
try:
    response = client.get(f"{REMOTE_URL}/")
    print(f"  状态码: {response.status_code}")
    print(f"  响应: {response.text[:200]}")
except Exception as e:
    print(f"  ❌ 失败: {e}")

print()

# 测试2: 健康检查
print("测试2: 健康检查 /health")
try:
    response = client.get(f"{REMOTE_URL}/health")
    print(f"  状态码: {response.status_code}")
    print(f"  响应: {response.text[:200]}")
except Exception as e:
    print(f"  ❌ 失败: {e}")

print()

# 测试3: 模型信息
print("测试3: 模型信息 /model/info")
try:
    response = client.get(f"{REMOTE_URL}/model/info")
    print(f"  状态码: {response.status_code}")
    print(f"  响应: {response.text[:200]}")
except Exception as e:
    print(f"  ❌ 失败: {e}")

print()

# 测试4: 聊天接口
print("测试4: 聊天接口 /chat")
try:
    response = client.post(
        f"{REMOTE_URL}/chat",
        json={
            "messages": [{"role": "user", "content": "你好"}],
            "temperature": 0.7,
            "max_tokens": 50
        }
    )
    print(f"  状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  响应: {data.get('content', '')[:100]}")
        print(f"  推理时间: {data.get('inference_time', 0):.3f}秒")
    else:
        print(f"  响应: {response.text[:200]}")
except Exception as e:
    print(f"  ❌ 失败: {e}")

print()
print("=" * 60)
print("诊断建议:")
print("=" * 60)
print("1. 如果所有测试都返回404，说明AutoDL端口映射配置有问题")
print("2. 请在AutoDL控制台检查:")
print("   - 容器内端口: 6006")
print("   - 映射到外部端口: 8443")
print("3. 确保在GPU服务器上启动了模型服务:")
print("   python -m backend.llm.remote_model_server --host 0.0.0.0 --port 6006 --model-path /root/autodl-tmp/quarot_qwen3-8b_w4a16kv16_s50.pt")
print()

client.close()
