"""
测试WebSocket思考过程流式输出
"""
import asyncio
import websockets
import json

async def test_chat_with_thinking(question: str):
    """测试单个问题的思考过程"""
    uri = "ws://localhost:8000/ws/chat"
    
    print(f"\n{'='*70}")
    print(f"问题: {question}")
    print('='*70)
    
    try:
        async with websockets.connect(uri) as websocket:
            # 发送消息
            message = {
                "user_id": "test_user",
                "message": question,
                "context": None
            }
            
            await websocket.send(json.dumps(message))
            
            # 接收响应
            full_thinking = ""
            full_response = ""
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30)
                    data = json.loads(response)
                    
                    if data['type'] == 'start':
                        print(f"🎬 会话开始: {data['session_id']}\n")
                    
                    elif data['type'] == 'progress':
                        print(f"{data['content']}")
                    
                    elif data['type'] == 'thinking_chunk':
                        chunk = data['content']
                        full_thinking += chunk
                        print(chunk, end='', flush=True)
                    
                    elif data['type'] == 'answer_chunk':
                        chunk = data['content']
                        full_response += chunk
                        print(chunk, end='', flush=True)
                    
                    elif data['type'] == 'done':
                        print("\n\n✅ 完成")
                        break
                    
                    elif data['type'] == 'error':
                        print(f"\n❌ 错误: {data['content']}")
                        return False
                
                except asyncio.TimeoutError:
                    print("\n⏱️ 超时")
                    return False
            
            # 显示总结
            print(f"\n{'─'*70}")
            print(f"💭 思考过程 ({len(full_thinking)} 字):")
            print(f"   {full_thinking}")
            print(f"\n💬 完整回复 ({len(full_response)} 字):")
            print(f"   {full_response}")
            print('='*70)
            
            return True
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

async def main():
    """测试多个问题"""
    print("🚀 测试WebSocket思考过程流式输出\n")
    
    questions = [
        "你好吗",
        "什么是人工智能",
        "如何保持健康的生活方式"
    ]
    
    results = []
    for question in questions:
        result = await test_chat_with_thinking(question)
        results.append(result)
        await asyncio.sleep(1)  # 间隔1秒
    
    # 总结
    print(f"\n\n{'='*70}")
    print("测试总结:")
    for i, (question, result) in enumerate(zip(questions, results), 1):
        status = "✅ 成功" if result else "❌ 失败"
        print(f"  {i}. {question[:30]:30s} {status}")
    print('='*70)

if __name__ == "__main__":
    asyncio.run(main())
