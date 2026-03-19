"""
测试决策副本API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_dungeon():
    """测试创建副本"""
    print("\n=== 测试创建决策副本 ===")
    
    url = f"{BASE_URL}/api/decision/create-dungeon"
    data = {
        "user_id": "test_user",
        "title": "毕业后应该选择什么？",
        "description": "大三学生面临的人生选择",
        "context": "计算机专业，成绩中等，对创业感兴趣",
        "urgency": "medium",
        "options": ["考研", "工作", "创业"],
        "use_lora": False  # 先不使用LoRA测试
    }
    
    print(f"请求URL: {url}")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                print("\n✅ 创建副本成功！")
                return result.get("data", {}).get("dungeon_id")
            else:
                print(f"\n❌ 创建副本失败: {result.get('message')}")
                return None
        else:
            print(f"\n❌ HTTP请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"\n❌ 请求出错: {str(e)}")
        return None

def test_get_dungeon(dungeon_id):
    """测试获取副本详情"""
    if not dungeon_id:
        print("\n⚠️  跳过获取副本测试（没有dungeon_id）")
        return
    
    print(f"\n=== 测试获取副本详情 ===")
    
    url = f"{BASE_URL}/api/decision/dungeon/{dungeon_id}"
    print(f"请求URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                print("✅ 获取副本成功！")
                data = result.get("data", {})
                print(f"副本标题: {data.get('title')}")
                print(f"选项数量: {len(data.get('options', []))}")
            else:
                print(f"❌ 获取失败: {result.get('message')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求出错: {str(e)}")

def test_list_dungeons(user_id):
    """测试获取用户副本列表"""
    print(f"\n=== 测试获取用户副本列表 ===")
    
    url = f"{BASE_URL}/api/decision/dungeons/{user_id}"
    print(f"请求URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                print("✅ 获取列表成功！")
                data = result.get("data", {})
                print(f"副本总数: {data.get('total')}")
                for dungeon in data.get("dungeons", []):
                    print(f"  - {dungeon.get('title')} ({dungeon.get('dungeon_id')})")
            else:
                print(f"❌ 获取失败: {result.get('message')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求出错: {str(e)}")

def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    
    url = f"{BASE_URL}/health"
    print(f"请求URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
            return True
        else:
            print("❌ 后端服务异常")
            return False
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("  决策副本API测试")
    print("="*60)
    
    # 1. 健康检查
    if not test_health():
        print("\n⚠️  后端服务未运行，请先启动后端服务")
        exit(1)
    
    # 2. 创建副本
    dungeon_id = test_create_dungeon()
    
    # 3. 获取副本详情
    test_get_dungeon(dungeon_id)
    
    # 4. 获取用户副本列表
    test_list_dungeons("test_user")
    
    print("\n" + "="*60)
    print("  测试完成")
    print("="*60)
