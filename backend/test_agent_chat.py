"""
测试Agent对话API
"""
import requests
import json
import sys

# 配置
# 如果使用Docker，使用服务器IP；如果本地开发，使用localhost
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://47.115.230.195:8000")

def get_test_token():
    """获取测试token - 使用admin账号登录"""
    url = f"{API_BASE_URL}/api/auth/login"
    payload = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                token = data['data']['token']
                print(f"✅ 登录成功，获取到token")
                return token
        print(f"❌ 登录失败: {response.text}")
        return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None


def test_agent_chat(token, agent_type="education", message="我适合考研还是就业？"):
    """测试Agent对话"""
    
    url = f"{API_BASE_URL}/api/agent-chat"
    
    payload = {
        "token": token,
        "agent_type": agent_type,
        "message": message,
        "conversation_history": []
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n{'='*60}")
    print(f"测试 {agent_type} Agent")
    print(f"{'='*60}")
    print(f"问题: {message}")
    print(f"\n发送请求到: {url}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print(f"\n✅ 对话成功!")
                print(f"\n{'='*60}")
                print(f"Agent回复:")
                print(f"{'='*60}")
                print(data.get('response'))
                print(f"\n{'='*60}")
                print(f"检索统计:")
                print(f"{'='*60}")
                stats = data.get('retrieval_stats', {})
                print(f"  总计: {stats.get('total_results', 0)} 条")
                print(f"  RAG记忆: {stats.get('rag_results', 0)} 条")
                print(f"  知识图谱: {stats.get('neo4j_results', 0)} 条")
                print(f"  使用上下文: {'是' if data.get('context_used') else '否'}")
                return True
            else:
                print(f"\n❌ 对话失败: {data.get('message')}")
                print(f"完整响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
                return False
        else:
            print(f"\n❌ 请求失败 (状态码: {response.status_code})")
            print(f"响应内容: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时（30秒）")
        return False
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Agent对话API测试")
    print("=" * 60)
    
    # 1. 获取token
    print("\n步骤1: 登录获取token...")
    token = get_test_token()
    
    if not token:
        print("\n❌ 无法获取token，测试终止")
        sys.exit(1)
    
    # 2. 测试三个Agent
    print("\n步骤2: 测试Agent对话...")
    
    tests = [
        ("education", "我适合考研还是就业？"),
        ("career", "我需要提升哪些技能？"),
        ("relationship", "如何改善人际关系？")
    ]
    
    results = []
    for agent_type, message in tests:
        success = test_agent_chat(token, agent_type, message)
        results.append((agent_type, success))
        print("\n" + "-" * 60)
    
    # 3. 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for agent_type, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{agent_type.ljust(15)} {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败")


if __name__ == "__main__":
    main()

