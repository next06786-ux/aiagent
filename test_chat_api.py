"""
测试聊天API
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_chat():
    print("=" * 60)
    print("测试聊天API")
    print("=" * 60)
    
    # 1. 发起聊天
    print("\n1. 发起聊天请求...")
    start_response = requests.post(
        f"{BASE_URL}/api/chat/start",
        json={
            "user_id": "test_user",
            "message": "你好，我想了解一下健康建议",
            "context": {}
        }
    )
    
    print(f"状态码: {start_response.status_code}")
    print(f"响应: {start_response.json()}")
    
    if start_response.status_code != 200:
        print("❌ 聊天启动失败")
        return
    
    result = start_response.json()
    if result.get("code") != 200:
        print(f"❌ 返回错误: {result.get('message')}")
        return
    
    session_id = result["data"]["session_id"]
    print(f"✅ 会话ID: {session_id}")
    
    # 2. 轮询进度
    print("\n2. 开始轮询进度...")
    poll_count = 0
    max_polls = 100
    
    while poll_count < max_polls:
        poll_count += 1
        time.sleep(0.1)  # 100ms
        
        poll_response = requests.get(f"{BASE_URL}/api/chat/poll/{session_id}")
        
        if poll_response.status_code != 200:
            print(f"❌ 轮询失败: {poll_response.status_code}")
            break
        
        poll_result = poll_response.json()
        if poll_result.get("code") != 200:
            print(f"❌ 轮询错误: {poll_result.get('message')}")
            break
        
        data = poll_result["data"]
        
        # 显示进度
        if data.get("progress"):
            print(f"📊 进度 [{poll_count}]: {data['progress']}")
        
        # 显示思考过程
        if data.get("thinking"):
            thinking_len = len(data["thinking"])
            print(f"💭 思考过程长度: {thinking_len}")
        
        # 显示回复
        if data.get("answer"):
            answer_len = len(data["answer"])
            print(f"📝 回复长度: {answer_len}")
        
        # 检查是否完成
        if data.get("done"):
            print("\n✅ 对话完成!")
            print(f"\n思考过程:\n{data.get('thinking', '')}")
            print(f"\n回复内容:\n{data.get('answer', '')}")
            break
        
        # 检查错误
        if data.get("error"):
            print(f"\n❌ 错误: {data['error']}")
            break
    
    if poll_count >= max_polls:
        print(f"\n⚠️ 达到最大轮询次数 ({max_polls})")

if __name__ == "__main__":
    test_chat()
