#!/usr/bin/env python3
"""
测试Agent导入功能的token验证修复
"""
import requests
import json

# 服务器配置
BASE_URL = "http://47.115.230.195:8000"

def test_login():
    """测试登录获取token"""
    print("\n=== 测试登录 ===")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get('success'):
        token = result['data']['token']
        print(f"\n✅ 登录成功，Token: {token[:20]}...")
        return token
    else:
        print(f"\n❌ 登录失败: {result.get('message')}")
        return None

def test_text_import(token):
    """测试文本导入"""
    print("\n=== 测试文本导入 ===")
    
    response = requests.post(
        f"{BASE_URL}/api/agent-import",
        json={
            "token": token,
            "agent_type": "education",
            "content": "这是一条测试导入的教育相关记忆\n这是第二条测试记忆"
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get('success'):
        print(f"\n✅ 文本导入成功，导入了 {result.get('count')} 条记忆")
        return True
    else:
        print(f"\n❌ 文本导入失败: {result.get('message')}")
        return False

def test_file_import(token):
    """测试文件导入"""
    print("\n=== 测试文件导入 ===")
    
    # 创建测试文件
    test_content = """这是测试文件的第一行内容
这是测试文件的第二行内容
关于职业规划的一些建议"""
    
    files = {
        'file': ('test_career.txt', test_content.encode('utf-8'), 'text/plain')
    }
    
    data = {
        'token': token,
        'agent_type': 'career'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/agent-import-file",
        files=files,
        data=data
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get('success'):
        print(f"\n✅ 文件导入成功，导入了 {result.get('count')} 条记忆")
        return True
    else:
        print(f"\n❌ 文件导入失败: {result.get('message')}")
        return False

def test_agent_chat(token):
    """测试Agent对话"""
    print("\n=== 测试Agent对话 ===")
    
    response = requests.post(
        f"{BASE_URL}/api/agent-chat",
        json={
            "token": token,
            "agent_type": "education",
            "message": "你好，我想了解一下考研的建议",
            "conversation_history": []
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get('success'):
        print(f"\n✅ Agent对话成功")
        print(f"回复: {result.get('reply', '')[:100]}...")
        return True
    else:
        print(f"\n❌ Agent对话失败: {result.get('message')}")
        return False

def main():
    """主测试流程"""
    print("=" * 60)
    print("Agent导入功能Token验证修复测试")
    print("=" * 60)
    
    # 1. 登录获取token
    token = test_login()
    if not token:
        print("\n❌ 无法获取token，测试终止")
        return
    
    # 2. 测试文本导入
    test_text_import(token)
    
    # 3. 测试文件导入
    test_file_import(token)
    
    # 4. 测试Agent对话
    test_agent_chat(token)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
