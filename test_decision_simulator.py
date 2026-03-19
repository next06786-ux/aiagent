"""
测试决策模拟 API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_decision_simulator():
    """测试决策模拟完整流程"""
    
    print("="*60)
    print("测试决策模拟 API")
    print("="*60)
    
    # 1. 模拟决策
    print("\n1. 提交决策问题...")
    
    decision_data = {
        "user_id": "test_user_001",
        "question": "大三学生，毕业后应该选择什么？",
        "options": [
            {
                "title": "考研",
                "description": "继续深造，提升学历，为未来发展打基础"
            },
            {
                "title": "直接工作",
                "description": "进入职场，积累实战经验，开始赚钱"
            },
            {
                "title": "创业",
                "description": "自主创业，追求梦想，挑战自我"
            }
        ],
        "use_lora": False
    }
    
    response = requests.post(
        f"{BASE_URL}/api/decision/simulate",
        json=decision_data
    )
    print(f"状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 模拟失败: {response.text}")
        return
    
    data = response.json()
    print(f"✅ 模拟完成")
    
    simulation_id = data['data']['simulation_id']
    print(f"模拟ID: {simulation_id}")
    
    # 2. 显示结果
    print(f"\n问题: {data['data']['question']}\n")
    
    for option in data['data']['options']:
        print(f"\n{'='*50}")
        print(f"选项: {option['title']}")
        print(f"描述: {option['description']}")
        print(f"综合得分: {option['final_score']:.1f}/100")
        print(f"风险等级: {option['risk_level']:.2f}")
        
        print(f"\n时间线预测:")
        for event in option['timeline']:
            print(f"\n  第{event['month']}个月:")
            print(f"  事件: {event['event']}")
            print(f"  发生概率: {event['probability']:.0%}")
            print(f"  影响:")
            for dimension, impact in event['impact'].items():
                sign = "+" if impact > 0 else ""
                print(f"    {dimension}: {sign}{impact:.1f}")
    
    print(f"\n{'='*50}")
    print(f"\nAI 推荐:")
    print(data['data']['recommendation'])
    
    # 3. 获取模拟结果
    print(f"\n2. 重新获取模拟结果...")
    response = requests.get(f"{BASE_URL}/api/decision/result/{simulation_id}")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ 结果获取成功")
    else:
        print(f"❌ 获取失败: {response.text}")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

if __name__ == "__main__":
    test_decision_simulator()
