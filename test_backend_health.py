"""
测试后端健康状态
"""
import requests

def test_backend():
    """测试后端是否正常运行"""
    try:
        # 测试 HTTP 端点
        response = requests.get('http://192.168.1.192:8000/health', timeout=5)
        print(f"✅ HTTP 端点正常: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"❌ HTTP 端点失败: {e}")
    
    try:
        # 测试根路径
        response = requests.get('http://192.168.1.192:8000/', timeout=5)
        print(f"✅ 根路径正常: {response.status_code}")
    except Exception as e:
        print(f"❌ 根路径失败: {e}")

if __name__ == '__main__':
    test_backend()
