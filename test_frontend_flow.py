"""
测试前端完整流程
模拟前端从创建副本到查看副本的完整流程
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_complete_flow():
    """测试完整流程"""
    print("\n" + "="*60)
    print("  测试前端完整流程")
    print("="*60)
    
    # 步骤1: 创建副本
    print("\n步骤1: 创建决策副本")
    print("-" * 60)
    
    create_url = f"{BASE_URL}/api/decision/create-dungeon"
    create_data = {
        "user_id": "test_user_frontend",
        "title": "毕业后应该选择什么？",
        "description": "大三学生面临的人生选择",
        "context": "计算机专业，成绩中等，对创业感兴趣",
        "urgency": "medium",
        "options": ["考研", "工作", "创业"],
        "use_lora": False
    }
    
    print(f"请求URL: {create_url}")
    print(f"请求数据: {json.dumps(create_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(create_url, json=create_data, timeout=30)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
        
        result = response.json()
        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get("code") != 200:
            print(f"\n❌ 创建副本失败: {result.get('message')}")
            return
        
        dungeon_id = result.get("data", {}).get("dungeon_id")
        if not dungeon_id:
            print("\n❌ 未获取到dungeon_id")
            return
        
        print(f"\n✅ 创建副本成功！")
        print(f"副本ID: {dungeon_id}")
        
        # 步骤2: 获取副本详情（模拟前端导航后加载数据）
        print("\n步骤2: 获取副本详情")
        print("-" * 60)
        
        time.sleep(0.5)  # 模拟页面跳转延迟
        
        detail_url = f"{BASE_URL}/api/decision/dungeon/{dungeon_id}"
        print(f"请求URL: {detail_url}")
        
        response = requests.get(detail_url, timeout=10)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
        
        result = response.json()
        
        if result.get("code") != 200:
            print(f"❌ 获取副本失败: {result.get('message')}")
            return
        
        data = result.get("data", {})
        print(f"\n✅ 获取副本成功！")
        print(f"副本标题: {data.get('title')}")
        print(f"副本描述: {data.get('description')}")
        print(f"选项数量: {len(data.get('options', []))}")
        
        # 显示选项详情
        print("\n选项详情:")
        for i, option in enumerate(data.get('options', [])):
            print(f"\n  选项 {i+1}: {option.get('title')}")
            print(f"    描述: {option.get('description')}")
            print(f"    综合得分: {option.get('final_score'):.1f}")
            print(f"    风险等级: {option.get('risk_level'):.2f}")
            print(f"    时间线事件数: {len(option.get('timeline', []))}")
        
        print("\nAI推荐:")
        print(f"  {data.get('recommendation')}")
        
        print("\n" + "="*60)
        print("  ✅ 完整流程测试成功！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_flow()
