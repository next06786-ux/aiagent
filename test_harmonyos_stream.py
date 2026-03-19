"""
测试鸿蒙流式输出功能
验证后端SSE流式API是否正常工作
"""
import requests
import json
import time

def test_stream_chat():
    """测试流式聊天接口"""
    url = "http://localhost:8000/api/chat/stream"
    
    data = {
        "user_id": "test_user",
        "message": "请详细解释一下什么是人工智能？",
        "context": {}
    }
    
    print("=" * 60)
    print("🚀 开始测试流式聊天")
    print("=" * 60)
    print(f"📤 请求URL: {url}")
    print(f"📤 请求数据: {json.dumps(data, ensure_ascii=False)}")
    print()
    
    try:
        # 发送SSE请求
        response = requests.post(
            url,
            json=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            stream=True,  # 启用流式接收
            timeout=120
        )
        
        print(f"✅ 响应状态码: {response.status_code}")
        print()
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.text}")
            return
        
        # 逐行读取SSE数据
        chunk_count = 0
        start_time = time.time()
        
        print("📡 开始接收流式数据...")
        print("-" * 60)
        
        for line in response.iter_lines(decode_unicode=True):
            if line:
                chunk_count += 1
                elapsed = time.time() - start_time
                
                print(f"\n[数据块 #{chunk_count}] ({elapsed:.2f}s)")
                print(f"原始数据: {line[:100]}...")
                
                # 解析SSE格式
                if line.startswith('data:'):
                    json_str = line[5:].strip()
                    
                    if json_str == '[DONE]':
                        print("🏁 收到结束标记")
                        continue
                    
                    try:
                        event_data = json.loads(json_str)
                        event_type = event_data.get('type', '')
                        content = event_data.get('content', '')
                        
                        print(f"事件类型: {event_type}")
                        
                        if event_type == 'start':
                            print(f"🎬 会话开始: {event_data.get('session_id')}")
                        
                        elif event_type == 'progress':
                            print(f"📊 进度: {content}")
                        
                        elif event_type == 'thinking_chunk':
                            print(f"💭 思考块: {content[:50]}...")
                        
                        elif event_type == 'thinking':
                            print(f"💭 完整思考 (长度: {len(content)})")
                            print(f"内容: {content[:100]}...")
                        
                        elif event_type == 'answer_chunk':
                            print(f"✍️ 回答块: {content}")
                        
                        elif event_type == 'answer':
                            print(f"✍️ 完整回答 (长度: {len(content)})")
                            print(f"内容: {content[:100]}...")
                        
                        elif event_type == 'done':
                            print("🎉 对话完成")
                        
                        elif event_type == 'error':
                            print(f"❌ 错误: {content}")
                        
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON解析失败: {e}")
                        print(f"原始JSON: {json_str[:100]}...")
        
        total_time = time.time() - start_time
        print()
        print("-" * 60)
        print(f"✅ 流式传输完成")
        print(f"📊 统计:")
        print(f"   - 总数据块: {chunk_count}")
        print(f"   - 总耗时: {total_time:.2f}秒")
        print(f"   - 平均速度: {chunk_count/total_time:.2f} 块/秒")
        print("=" * 60)
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保后端服务已启动")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  鸿蒙流式输出功能测试")
    print("=" * 60 + "\n")
    
    test_stream_chat()
    
    print("\n✅ 测试完成\n")
