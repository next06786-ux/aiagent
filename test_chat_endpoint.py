"""
测试聊天端点是否正常工作
"""
import requests
import json

BASE_URL = "http://192.168.1.192:8000"

def test_health():
    """测试健康检查"""
    print("=" * 60)
    print("1. 测试健康检查")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def test_chat_stream():
    """测试流式聊天"""
    print("\n" + "=" * 60)
    print("2. 测试流式聊天 /api/chat/stream")
    print("=" * 60)
    
    try:
        data = {
            "user_id": "test_user",
            "message": "你好",
            "context": None
        }
        
        print(f"发送请求: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json=data,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\n接收到的数据流:")
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    print(f"  {decoded_line}")
            return True
        else:
            print(f"❌ 错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 流式聊天测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_normal():
    """测试普通聊天"""
    print("\n" + "=" * 60)
    print("3. 测试普通聊天 /api/chat")
    print("=" * 60)
    
    try:
        data = {
            "user_id": "test_user",
            "message": "你好",
            "context": None
        }
        
        print(f"发送请求: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 普通聊天测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试后端聊天接口...")
    print(f"目标服务器: {BASE_URL}\n")
    
    # 测试健康检查
    health_ok = test_health()
    
    if not health_ok:
        print("\n❌ 健康检查失败，后端可能未正常运行")
        exit(1)
    
    # 测试流式聊天
    stream_ok = test_chat_stream()
    
    # 测试普通聊天
    normal_ok = test_chat_normal()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"健康检查: {'✅ 通过' if health_ok else '❌ 失败'}")
    print(f"流式聊天: {'✅ 通过' if stream_ok else '❌ 失败'}")
    print(f"普通聊天: {'✅ 通过' if normal_ok else '❌ 失败'}")
