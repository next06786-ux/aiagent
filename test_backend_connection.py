"""
测试后端连接
"""
import requests
import socket

print("=" * 60)
print("测试后端连接")
print("=" * 60)

# 1. 测试端口是否开放
print("\n1. 测试端口 8000 是否开放...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
result = sock.connect_ex(('127.0.0.1', 8000))
sock.close()

if result == 0:
    print("   ✅ 端口 8000 已开放")
else:
    print("   ❌ 端口 8000 未开放")
    print("   请确保后端服务正在运行")
    exit(1)

# 2. 测试 localhost
print("\n2. 测试 http://localhost:8000/health ...")
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.text}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 3. 测试 127.0.0.1
print("\n3. 测试 http://127.0.0.1:8000/health ...")
try:
    response = requests.get("http://127.0.0.1:8000/health", timeout=5)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.text}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 4. 测试 192.168.1.192
print("\n4. 测试 http://192.168.1.192:8000/health ...")
try:
    response = requests.get("http://192.168.1.192:8000/health", timeout=5)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.text}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
