"""
测试流式改进效果
"""
import requests
import json
import time

BASE_URL = "http://192.168.1.192:8000"

def test_streaming_chat():
    """测试流式聊天的实时性"""
    print("=" * 60)
    print("测试流式聊天 - 观察实时推送效果")
    print("=" * 60)
    
    data = {
        "user_id": "test_user",
        "message": "我最近睡眠不好，怎么办？",
        "context": None
    }
    
    print(f"\n发送消息: {data['message']}")
    print(f"开始时间: {time.strftime('%H:%M:%S')}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json=data,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            print("开始接收流式数据...\n")
            
            event_count = 0
            thinking_received = False
            answer_received = False
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    
                    # 解析SSE数据
                    if decoded_line.startswith('event:'):
                        event_type = decoded_line.split(':', 1)[1].strip()
                    elif decoded_line.startswith('data:'):
                        event_count += 1
                        data_str = decoded_line.split(':', 1)[1].strip()
                        
                        try:
                            data_obj = json.loads(data_str)
                            msg_type = data_obj.get('type', '')
                            content = data_obj.get('content', '')
                            
                            current_time = time.strftime('%H:%M:%S')
                            
                            if msg_type == 'start':
                                print(f"[{current_time}] 🚀 会话开始: {data_obj.get('session_id', '')}")
                            elif msg_type == 'progress':
                                print(f"[{current_time}] 📊 {content}")
                            elif msg_type == 'thinking_chunk':
                                if not thinking_received:
                                    print(f"[{current_time}] 💭 开始接收思考过程...")
                                    thinking_received = True
                                print(f"    {content[:80]}")
                            elif msg_type == 'answer_chunk':
                                if not answer_received:
                                    print(f"[{current_time}] ✍️ 开始接收回答内容...")
                                    answer_received = True
                                # 只显示前几个chunk
                                if event_count < 20:
                                    print(f"    {content}")
                            elif msg_type == 'done':
                                print(f"\n[{current_time}] ✅ 对话完成")
                            elif msg_type == 'error':
                                print(f"[{current_time}] ❌ 错误: {content}")
                        except json.JSONDecodeError:
                            pass
            
            print(f"\n总共接收 {event_count} 个事件")
            print(f"结束时间: {time.strftime('%H:%M:%S')}")
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_streaming_chat()
