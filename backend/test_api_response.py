"""
测试Agent API响应格式
"""
import requests
import json

# 测试配置
API_URL = "http://localhost:8000/api/agent-chat"
TOKEN = "test_token_for_test_user_001"  # 需要先登录获取真实token

def test_agent_api():
    """测试Agent API响应"""
    print("\n" + "="*70)
    print("测试Agent API响应格式")
    print("="*70)
    
    # 准备请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }
    
    data = {
        "agent_type": "relationship",
        "message": "2024年最新的AI技术趋势有哪些？"
    }
    
    print(f"\n📤 发送请求:")
    print(f"   URL: {API_URL}")
    print(f"   消息: {data['message']}")
    
    try:
        response = requests.post(API_URL, json=data, headers=headers, timeout=60)
        
        print(f"\n📥 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ 响应成功!")
            print(f"\n📊 响应数据结构:")
            print(f"   - success: {result.get('success')}")
            print(f"   - response: {result.get('response', '')[:100]}...")
            print(f"   - mode: {result.get('mode')}")
            print(f"   - agent_used: {result.get('agent_used')}")
            
            # 重点检查tool_calls
            tool_calls = result.get('tool_calls', [])
            print(f"\n🔧 工具调用信息:")
            print(f"   - 数量: {len(tool_calls)}")
            
            if tool_calls:
                print(f"\n   详细信息:")
                for i, tool in enumerate(tool_calls, 1):
                    print(f"\n   {i}. {tool.get('tool_name')}")
                    print(f"      - server_name: {tool.get('server_name')}")
                    print(f"      - status: {tool.get('status')}")
                    print(f"      - result: {tool.get('result', '')[:50]}...")
                
                # 输出完整JSON（用于前端调试）
                print(f"\n📋 完整tool_calls JSON:")
                print(json.dumps(tool_calls, ensure_ascii=False, indent=2))
            else:
                print(f"   ⚠️  没有工具调用记录")
            
            # 检查retrieval_stats
            retrieval_stats = result.get('retrieval_stats', {})
            print(f"\n📈 检索统计:")
            print(f"   - intent: {retrieval_stats.get('intent')}")
            print(f"   - complexity: {retrieval_stats.get('complexity')}")
            
        else:
            print(f"\n❌ 请求失败: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"\n⏱️  请求超时")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)

if __name__ == "__main__":
    print("\n⚠️  注意: 需要先启动后端服务 (python backend/main.py)")
    print("⚠️  注意: 需要先登录获取真实token")
    print("\n按Enter继续...")
    input()
    
    test_agent_api()
