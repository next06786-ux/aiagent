"""
测试WebSocket Agent对话
"""
import asyncio
import websockets
import json
from datetime import datetime


async def test_websocket_agent():
    """测试WebSocket Agent对话"""
    
    # 连接WebSocket
    uri = "ws://localhost:8000/ws/agent-chat"
    
    print(f"连接到: {uri}")
    
    async with websockets.connect(uri) as websocket:
        print("✅ WebSocket连接已建立")
        
        # 接收连接确认
        response = await websocket.recv()
        data = json.loads(response)
        print(f"收到: {data}")
        
        if data['type'] == 'connected':
            session_id = data['session_id']
            print(f"会话ID: {session_id}")
        
        # 发送测试消息
        test_message = {
            "token": "test_token_123",  # 需要替换为真实token
            "agent_type": "relationship",
            "message": "搜索2023年诺贝尔奖得主",
            "conversation_id": None
        }
        
        print(f"\n发送消息: {test_message['message']}")
        await websocket.send(json.dumps(test_message))
        
        # 接收响应
        print("\n等待响应...")
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 收到消息:")
                print(f"  类型: {data['type']}")
                
                if data['type'] == 'tool_start':
                    print(f"  🔧 工具开始: {data['tool_name']}")
                    print(f"     服务器: {data['server_name']}")
                
                elif data['type'] == 'tool_complete':
                    print(f"  ✅ 工具完成: {data['tool_name']}")
                    print(f"     结果: {data.get('result', '')[:100]}")
                
                elif data['type'] == 'tool_failed':
                    print(f"  ❌ 工具失败: {data['tool_name']}")
                    print(f"     错误: {data['error']}")
                
                elif data['type'] == 'response':
                    print(f"  💬 最终响应:")
                    print(f"     内容: {data['content'][:200]}...")
                    print(f"     工具调用数: {len(data['metadata'].get('tool_calls', []))}")
                    break
                
                elif data['type'] == 'error':
                    print(f"  ❌ 错误: {data['error']}")
                    break
                
            except websockets.exceptions.ConnectionClosed:
                print("\n连接已关闭")
                break
        
        print("\n✅ 测试完成")


if __name__ == "__main__":
    print("="*60)
    print("WebSocket Agent对话测试")
    print("="*60)
    print()
    
    try:
        asyncio.run(test_websocket_agent())
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
