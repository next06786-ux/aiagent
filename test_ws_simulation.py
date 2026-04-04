#!/usr/bin/env python3
"""测试WebSocket推演的节点发送"""

import asyncio
import websockets
import json

async def test_simulation():
    uri = "ws://localhost:8000/api/decision/simulate-ws"
    
    test_data = {
        "session_id": "test_session_debug",
        "options": [
            {"title": "测试选项A", "description": "测试描述A"}
        ]
    }
    
    print("=" * 60)
    print("连接到 WebSocket...")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            # 发送推演请求
            await websocket.send(json.dumps(test_data))
            print(f"✓ 已发送推演请求")
            
            node_count = 0
            thinking_chars = 0
            
            # 接收消息
            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if msg_type == 'status':
                    print(f"[状态] {data.get('content')}")
                
                elif msg_type == 'option_start':
                    print(f"\n[选项开始] {data.get('option_title')}")
                
                elif msg_type == 'thinking_chunk':
                    thinking_chars += len(data.get('content', ''))
                    if thinking_chars % 100 == 0:
                        print(f"[思考] 已收到 {thinking_chars} 字符")
                
                elif msg_type == 'node':
                    node_count += 1
                    node = data.get('node', {})
                    print(f"\n[节点 #{node_count}] M{node.get('month')}: {node.get('event', '')[:50]}...")
                    print(f"  影响: {node.get('impact_vector')}")
                
                elif msg_type == 'option_complete':
                    print(f"\n[选项完成] 得分: {data.get('final_score')}")
                
                elif msg_type == 'done':
                    print(f"\n[推演完成] 总节点数: {node_count}")
                    break
                
                elif msg_type == 'error':
                    print(f"\n[错误] {data.get('content')}")
                    break
    
    except Exception as e:
        print(f"\n[异常] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simulation())
