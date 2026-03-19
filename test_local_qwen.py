"""
测试本地 Qwen 模型服务器
"""
import requests
import json

def test_qwen_server():
    """测试 Qwen 服务器"""
    base_url = "http://localhost:8000"
    
    print("=" * 50)
    print("测试本地 Qwen 模型服务器")
    print("=" * 50)
    
    # 1. 健康检查
    print("\n1. 健康检查...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"状态: {response.json()}")
    except Exception as e:
        print(f"❌ 服务器未启动: {e}")
        return
    
    # 2. 列出模型
    print("\n2. 列出可用模型...")
    response = requests.get(f"{base_url}/v1/models")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 3. 测试对话
    print("\n3. 测试对话...")
    chat_request = {
        "model": "qwen3.5-0.8b",
        "messages": [
            {"role": "user", "content": "你好，请介绍一下你自己"}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    response = requests.post(
        f"{base_url}/v1/chat/completions",
        json=chat_request
    )
    
    result = response.json()
    print(f"\n用户: {chat_request['messages'][0]['content']}")
    print(f"助手: {result['choices'][0]['message']['content']}")
    
    # 4. 测试多轮对话
    print("\n4. 测试多轮对话...")
    chat_request = {
        "model": "qwen3.5-0.8b",
        "messages": [
            {"role": "user", "content": "我今天心情不太好"},
            {"role": "assistant", "content": "我理解你的感受。能告诉我发生了什么吗？"},
            {"role": "user", "content": "工作压力太大了"}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    response = requests.post(
        f"{base_url}/v1/chat/completions",
        json=chat_request
    )
    
    result = response.json()
    print(f"\n用户: {chat_request['messages'][-1]['content']}")
    print(f"助手: {result['choices'][0]['message']['content']}")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    test_qwen_server()
