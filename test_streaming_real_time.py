"""
测试真正的流式输出 - 验证思考过程和回答内容的实时推送
"""

import requests
import json
import time

def test_streaming_chat():
    """测试流式聊天接口"""
    url = "http://localhost:8000/api/chat/stream"
    
    data = {
        "user_id": "test_user_001",
        "message": "我最近睡眠不好，感觉压力很大，怎么办？",
        "context": None
    }
    
    print("=" * 80)
    print("🚀 开始测试真正的流式输出")
    print("=" * 80)
    print(f"📤 发送消息: {data['message']}")
    print("-" * 80)
    
    start_time = time.time()
    first_chunk_time = None
    thinking_start_time = None
    answer_start_time = None
    
    thinking_chunks = []
    answer_chunks = []
    
    try:
        # 发送流式请求
        response = requests.post(
            url,
            json=data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            stream=True,  # 关键：启用流式接收
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            return
        
        print("✅ 连接成功，开始接收流式数据...\n")
        
        # 逐行读取SSE数据
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            
            # 记录第一个数据块的时间
            if first_chunk_time is None:
                first_chunk_time = time.time()
                elapsed = first_chunk_time - start_time
                print(f"⏱️  首个数据块到达时间: {elapsed:.2f}秒\n")
            
            # 解析SSE格式: data: {...}
            if line.startswith('data: '):
                json_str = line[6:].strip()
                
                if json_str == '[DONE]':
                    print("\n✅ 流式传输完成")
                    break
                
                try:
                    event = json.loads(json_str)
                    event_type = event.get('type', '')
                    content = event.get('content', '')
                    
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    # 处理不同类型的事件
                    if event_type == 'start':
                        session_id = event.get('session_id', '')
                        print(f"🎬 [{elapsed:.2f}s] 会话开始: {session_id}\n")
                    
                    elif event_type == 'progress':
                        print(f"📊 [{elapsed:.2f}s] 进度: {content}")
                    
                    elif event_type == 'thinking_chunk':
                        if thinking_start_time is None:
                            thinking_start_time = current_time
                            print(f"\n💭 [{elapsed:.2f}s] 思考过程开始流式输出:")
                            print("-" * 80)
                        thinking_chunks.append(content)
                        print(content, end='', flush=True)
                    
                    elif event_type == 'thinking':
                        if thinking_start_time is None:
                            thinking_start_time = current_time
                            print(f"\n💭 [{elapsed:.2f}s] 思考过程（完整）:")
                            print("-" * 80)
                            print(content)
                        print("-" * 80)
                    
                    elif event_type == 'answer_chunk':
                        if answer_start_time is None:
                            answer_start_time = current_time
                            print(f"\n\n✍️  [{elapsed:.2f}s] 回答内容开始流式输出:")
                            print("-" * 80)
                        answer_chunks.append(content)
                        print(content, end='', flush=True)
                    
                    elif event_type == 'answer':
                        if answer_start_time is None:
                            answer_start_time = current_time
                            print(f"\n\n✍️  [{elapsed:.2f}s] 回答内容（完整）:")
                            print("-" * 80)
                            print(content)
                        print("\n" + "-" * 80)
                    
                    elif event_type == 'done':
                        print(f"\n🎉 [{elapsed:.2f}s] 对话完成")
                    
                    elif event_type == 'error':
                        print(f"\n❌ [{elapsed:.2f}s] 错误: {content}")
                
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON解析失败: {e}")
                    print(f"   原始数据: {json_str[:100]}")
        
        # 统计信息
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "=" * 80)
        print("📊 流式输出统计")
        print("=" * 80)
        print(f"总耗时: {total_time:.2f}秒")
        
        if first_chunk_time:
            print(f"首个数据块延迟: {first_chunk_time - start_time:.2f}秒")
        
        if thinking_start_time:
            print(f"思考过程开始时间: {thinking_start_time - start_time:.2f}秒")
            print(f"思考过程数据块数量: {len(thinking_chunks)}")
        
        if answer_start_time:
            print(f"回答内容开始时间: {answer_start_time - start_time:.2f}秒")
            print(f"回答内容数据块数量: {len(answer_chunks)}")
        
        # 评估用户体验
        print("\n" + "=" * 80)
        print("🎯 用户体验评估")
        print("=" * 80)
        
        if first_chunk_time and (first_chunk_time - start_time) < 2.0:
            print("✅ 首个数据块延迟 < 2秒 - 优秀")
        elif first_chunk_time and (first_chunk_time - start_time) < 5.0:
            print("⚠️  首个数据块延迟 2-5秒 - 一般")
        else:
            print("❌ 首个数据块延迟 > 5秒 - 需要优化")
        
        if thinking_start_time and (thinking_start_time - start_time) < 2.0:
            print("✅ 思考过程延迟 < 2秒 - 优秀（类似千问/豆包）")
        elif thinking_start_time and (thinking_start_time - start_time) < 5.0:
            print("⚠️  思考过程延迟 2-5秒 - 一般")
        else:
            print("❌ 思考过程延迟 > 5秒 - 需要优化")
        
        if len(thinking_chunks) > 0:
            print(f"✅ 思考过程采用流式输出 - 共{len(thinking_chunks)}个数据块")
        else:
            print("⚠️  思考过程未采用流式输出")
        
        if len(answer_chunks) > 0:
            print(f"✅ 回答内容采用流式输出 - 共{len(answer_chunks)}个数据块")
        else:
            print("⚠️  回答内容未采用流式输出")
        
        print("=" * 80)
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保后端服务正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🧪 真正的流式输出测试")
    print("=" * 80)
    print("目标：验证思考过程和回答内容能在1-2秒内开始流式输出")
    print("=" * 80 + "\n")
    
    test_streaming_chat()
