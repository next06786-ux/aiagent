"""
测试心理测评 API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_personality_api():
    """测试心理测评完整流程"""
    
    print("="*60)
    print("测试心理测评 API")
    print("="*60)
    
    # 1. 获取题目
    print("\n1. 获取测评题目...")
    response = requests.get(f"{BASE_URL}/api/personality/questions")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 题目数量: {len(data['data']['questions'])}")
        print(f"测评信息: {data['data']['test_info']['name']}")
        print(f"预计时间: {data['data']['test_info']['estimated_time']}")
    else:
        print(f"❌ 获取题目失败: {response.text}")
        return
    
    # 2. 模拟答题（所有题选3 - 中等偏上）
    print("\n2. 提交测评答案...")
    answers = {str(i): 3 for i in range(1, 21)}
    
    submit_data = {
        "user_id": "test_user_001",
        "answers": answers
    }
    
    response = requests.post(
        f"{BASE_URL}/api/personality/submit",
        json=submit_data
    )
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 测评完成")
        
        summary = data['data']['summary']
        print(f"\n性格类型: {summary['personality_type']}")
        print(f"决策风格: {summary['decision_style']}")
        print(f"风险偏好: {summary['risk_preference']}")
        print(f"生活优先级: {summary['life_priority']}")
        print(f"\n个性化描述:")
        print(summary['description'])
    else:
        print(f"❌ 提交失败: {response.text}")
        return
    
    # 3. 获取画像
    print("\n3. 获取用户画像...")
    response = requests.get(f"{BASE_URL}/api/personality/profile/test_user_001")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 画像获取成功")
        
        profile = data['data']['profile']
        print(f"\n大五人格:")
        print(f"  开放性: {profile['openness']:.2f}")
        print(f"  尽责性: {profile['conscientiousness']:.2f}")
        print(f"  外向性: {profile['extraversion']:.2f}")
        print(f"  宜人性: {profile['agreeableness']:.2f}")
        print(f"  神经质: {profile['neuroticism']:.2f}")
        
        print(f"\n决策风格:")
        print(f"  风格: {profile['decision_style']}")
        print(f"  速度: {profile['decision_speed']:.2f}")
        print(f"  咨询倾向: {profile['consultation_tendency']:.2f}")
        
        print(f"\n风险偏好:")
        print(f"  偏好: {profile['risk_preference']}")
        print(f"  财务风险: {profile['financial_risk']:.2f}")
        print(f"  职业风险: {profile['career_risk']:.2f}")
        
        print(f"\n生活优先级:")
        print(f"  优先级: {profile['life_priority']}")
        print(f"  健康: {profile['health_priority']:.2f}")
        print(f"  事业: {profile['career_priority']:.2f}")
        print(f"  关系: {profile['relationship_priority']:.2f}")
    else:
        print(f"❌ 获取画像失败: {response.text}")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

if __name__ == "__main__":
    test_personality_api()
