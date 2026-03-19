"""
测试 SSE 流式聊天功能
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"

def test_sse_chat():
    """测试 SSE 流式聊天"""
    
    print("\n" + "="*60)
    print("  测试 SSE 流式聊天功能")
    print("="*60 + "\n")
    
    chat_data = {
        "user_id": "test_user",
        "message": "你好，请介绍一下你自己",
        "context": {}
    }
    
    print("📨 发送聊天请求...")
    print(f"   消息: {chat_data['message']}\n")
    
    try:
        # 发送 SSE 请求
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json=chat_data,
            headers={
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            },
            stream=True,  # 启用流式接收
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return
        
        print("✅ 连接已建立，开始接收流式数据...\n")
        
        message_count = 0
        buffer = ""
        
        # 逐行读取 SSE 数据
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            
            line = line.strip()
            
            # SSE 格式: data: {...}
            if line.startswith('data: '):
                message_count += 1
                data_str = line[6:]  # 移除 "data: " 前缀
                
                if data_str == '[DONE]':
                    print("\n📩 收到结束信号")
                    break
                
                try:
                    data = json.loads(data_str)
                    msg_type = data.get('type')
                    
                    print(f"📩 消息 #{message_count} - 类型: {msg_type}")
                    
                    if msg_type == 'start':
                        print(f"   会话ID: {data.get('session_id', '')}")
                    
                    elif msg_type == 'progress':
                        content = data.get('content', '')
                        print(f"   进度: {content}")
                    
                    elif msg_type == 'thinking':
                        content = data.get('content', '')
                        print(f"   思考过程长度: {len(content)} 字符")
                        print(f"   思考内容预览: {content[:100]}...")
                    
                    elif msg_type == 'answer':
                        content = data.get('content', '')
                        print(f"   回复内容长度: {len(content)} 字符")
                        print(f"   回复内容预览: {content[:100]}...")
                    
                    elif msg_type == 'done':
                        print("   ✅ 对话完成")
                        break
                    
                    elif msg_type == 'error':
                        error = data.get('content', '未知错误')
                        print(f"   ❌ 错误: {error}")
                        break
                    
                    print()
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ 解析 JSON 失败: {e}")
                    print(f"   原始数据: {data_str[:100]}")
        
        print(f"\n📊 总共接收到 {message_count} 条消息")
        print("\n✅ SSE 测试完成")
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保后端服务已启动")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n⚠️ 请确保后端服务已启动（python backend/start_server.py）\n")
    
    try:
        test_sse_chat()
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
