#!/usr/bin/env python3
"""快速测试流式聊天API"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/api/chat/health")
        print(f"✅ 状态: {response.json()}\n")
        return True
    except Exception as e:
        print(f"❌ 错误: {e}\n")
        return False

def test_stream():
    """测试流式聊天"""
    print("🔍 测试流式聊天...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={"message": "你好，请解释流式输出", "stream": True},
            stream=True,
            timeout=30
        )
        
        print("📡 接收流式数据:")
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data['type'] == 'thinking':
                            print(f"  💭 {data['content']}", end='')
                        elif data['type'] == 'content':
                            print(data['content'], end='', flush=True)
                        elif data['type'] == 'done':
                            print("\n✅ 完成\n")
                    except:
                        pass
        return True
    except Exception as e:
        print(f"❌ 错误: {e}\n")
        return False

def test_complete():
    """测试完整聊天"""
    print("🔍 测试完整聊天...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/chat",
            json={"message": "你好", "stream": False},
            timeout=30
        )
        data = response.json()
        print(f"✅ 思考过程:\n{data['thinking']}")
        print(f"✅ 回答内容:\n{data['content']}\n")
        return True
    except Exception as e:
        print(f"❌ 错误: {e}\n")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  流式聊天 API 测试")
    print("="*60 + "\n")
    
    # 测试健康检查
    if not test_health():
        print("❌ 后端未运行，请先启动: python -m uvicorn main:app --reload")
        exit(1)
    
    # 测试流式聊天
    test_stream()
    
    # 测试完整聊天
    test_complete()
    
    print("="*60)
    print("✅ 所有测试完成")
    print("="*60)

