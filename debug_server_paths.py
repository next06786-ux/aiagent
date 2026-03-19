"""
调试服务器路径
"""
import requests

BASE_URL = "http://localhost:8000"

# 添加一个临时调试端点
print("请求服务器工作目录信息...")

try:
    # 先测试健康检查
    response = requests.get(f"{BASE_URL}/health", timeout=2)
    print(f"✅ 服务器在线")
    print()
    
    # 测试 LoRA 状态，看看错误信息
    print("测试 LoRA 状态 API...")
    response = requests.get(f"{BASE_URL}/api/lora/status/test_user_001")
    result = response.json()
    
    if result['code'] == 200:
        print(f"✅ API 正常")
        print(f"   数据: {result['data']}")
    else:
        print(f"❌ API 错误: {result['message']}")
    
    print()
    print("💡 提示：")
    print("   1. 确认已重启后端服务（Ctrl+C 然后重新运行）")
    print("   2. 检查服务器启动日志中的 '📁 工作目录' 信息")
    print("   3. 应该显示: E:\\ai")
    
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到服务器")
    print()
    print("请先启动后端服务:")
    print("   cd backend")
    print("   python start_server.py")
except Exception as e:
    print(f"❌ 错误: {e}")
