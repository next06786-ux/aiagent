"""
测试后端修复 - WebSocket和API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_hybrid_strategy():
    """测试混合智能策略API"""
    print("\n=== 测试 /api/hybrid/strategy ===")
    try:
        response = requests.get(f"{BASE_URL}/api/hybrid/strategy/test_user")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_quick_analyze():
    """测试快速分析API"""
    print("\n=== 测试 /api/decision/quick-analyze ===")
    try:
        data = {
            "user_id": "test_user",
            "user_input": "我不知道毕业后应该考研还是工作"
        }
        response = requests.post(
            f"{BASE_URL}/api/decision/quick-analyze",
            json=data,
            timeout=60
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("code") == 200:
            dungeon_id = result.get("data", {}).get("dungeon_id")
            print(f"\n✅ 副本创建成功: {dungeon_id}")
            return dungeon_id
        return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_get_dungeon(dungeon_id):
    """测试获取副本详情"""
    print(f"\n=== 测试 /api/decision/dungeon/{dungeon_id} ===")
    try:
        response = requests.get(f"{BASE_URL}/api/decision/dungeon/{dungeon_id}")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"副本标题: {result.get('data', {}).get('title')}")
        print(f"选项数量: {len(result.get('data', {}).get('options', []))}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试后端修复...")
    
    # 测试1: 混合智能策略
    test1 = test_hybrid_strategy()
    
    # 测试2: 快速分析
    dungeon_id = test_quick_analyze()
    
    # 测试3: 获取副本
    test3 = False
    if dungeon_id:
        test3 = test_get_dungeon(dungeon_id)
    
    print("\n" + "="*50)
    print("测试结果:")
    print(f"  混合智能策略: {'✅' if test1 else '❌'}")
    print(f"  快速分析: {'✅' if dungeon_id else '❌'}")
    print(f"  获取副本: {'✅' if test3 else '❌'}")
    print("="*50)
