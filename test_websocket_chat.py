"""
测试WebSocket聊天功能
"""
import asyncio
import websockets
import json

async def test_websocket_chat():
    """测试WebSocket聊天"""
    uri = "ws://localhost:8000/ws/chat"
    
    print("🔌 连接到WebSocket...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 发送消息
            message = {
                "user_id": "test_user",
                "message": "你好吗",
                "context": None
            }
            
            print(f"\n📤 发送消息: {message['message']}")
            await websocket.send(json.dumps(message))
            
            # 接收响应
            print("\n📥 接收响应:")
            full_thinking = ""
            full_response = ""
            current_section = None
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30)
                    data = json.loads(response)
                    
                    if data['type'] == 'start':
                        print(f"  🎬 开始 - 会话ID: {data['session_id']}")
                    
                    elif data['type'] == 'progress':
                        print(f"\n  {data['content']}")
                        if '思考中' in data['content']:
                            current_section = 'thinking'
                            print("  ", end='', flush=True)
                        elif '生成回答' in data['content']:
                            current_section = 'answer'
                            print("\n  ", end='', flush=True)
                    
                    elif data['type'] == 'thinking_chunk':
                        chunk = data['content']
                        full_thinking += chunk
                        print(chunk, end='', flush=True)
                    
                    elif data['type'] == 'answer_chunk':
                        chunk = data['content']
                        full_response += chunk
                        print(chunk, end='', flush=True)
                    
                    elif data['type'] == 'done':
                        print("\n\n  ✅ 完成")
                        break
                    
                    elif data['type'] == 'error':
                        print(f"\n  ❌ 错误: {data['content']}")
                        break
                
                except asyncio.TimeoutError:
                    print("\n  ⏱️ 超时")
                    break
            
            print("\n" + "="*60)
            if full_thinking:
                print(f"💭 思考过程:\n{full_thinking}")
            print(f"\n💬 完整回复:\n{full_response}")
            print("="*60)
            return True
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 测试WebSocket聊天功能\n")
    result = asyncio.run(test_websocket_chat())
    
    if result:
        print("\n✅ 测试成功！")
    else:
        print("\n❌ 测试失败！")
