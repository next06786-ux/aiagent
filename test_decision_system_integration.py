"""
测试AI决策系统集成
完整流程：心理测评 -> 决策模拟
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_full_workflow():
    """测试完整工作流"""
    
    print("\n" + "="*70)
    print("  AI决策系统集成测试")
    print("="*70)
    
    user_id = "test_user_001"
    
    # ========== 步骤1: 心理测评 ==========
    print("\n【步骤1】心理测评")
    print("-" * 70)
    
    # 1.1 获取题目
    print("\n1.1 获取测评题目...")
    response = requests.get(f"{BASE_URL}/api/personality/questions")
    
    if response.status_code != 200:
        print(f"❌ 获取题目失败")
        return
    
    questions_data = response.json()['data']
    print(f"✅ 获取到 {len(questions_data['questions'])} 道题目")
    
    # 1.2 模拟答题（模拟一个理性、风险规避、重视健康的用户）
    print("\n1.2 提交测评答案...")
    answers = {}
    for q in questions_data['questions']:
        # 根据维度给出不同答案
        if 'rational' in q['subdimension']:
            answers[str(q['id'])] = 4  # 理性
        elif 'financial' in q['subdimension'] or 'career' in q['subdimension']:
            answers[str(q['id'])] = 2  # 风险规避
        elif 'health' in q['subdimension']:
            answers[str(q['id'])] = 4  # 重视健康
        else:
            answers[str(q['id'])] = 3  # 中等
    
    response = requests.post(
        f"{BASE_URL}/api/personality/submit",
        json={"user_id": user_id, "answers": answers}
    )
    
    if response.status_code != 200:
        print(f"❌ 提交失败")
        return
    
    profile_data = response.json()['data']
    summary = profile_data['summary']
    
    print(f"✅ 测评完成")
    print(f"\n性格画像:")
    print(f"  类型: {summary['personality_type']}")
    print(f"  决策风格: {summary['decision_style']}")
    print(f"  风险偏好: {summary['risk_preference']}")
    print(f"  生活优先级: {summary['life_priority']}")
    
    time.sleep(1)
    
    # ========== 步骤2: 决策模拟 ==========
    print("\n【步骤2】决策模拟")
    print("-" * 70)
    
    print("\n2.1 提交决策问题...")
    decision_data = {
        "user_id": user_id,
        "question": "大三学生，毕业后应该选择什么？",
        "options": [
            {"title": "考研", "description": "继续深造，提升学历"},
            {"title": "直接工作", "description": "进入职场，积累经验"},
            {"title": "创业", "description": "自主创业，追求梦想"}
        ],
        "use_lora": False
    }
    
    response = requests.post(
        f"{BASE_URL}/api/decision/simulate",
        json=decision_data
    )
    
    if response.status_code != 200:
        print(f"❌ 模拟失败: {response.text}")
        return
    
    response_json = response.json()
    print(f"✅ 模拟完成")
    print(f"调试: 响应数据 = {response_json}")
    
    result = response_json.get('data')
    if not result:
        print(f"❌ 错误: API返回的data字段为空")
        print(f"完整响应: {response_json}")
        return
    
    # ========== 步骤3: 展示结果 ==========
    print("\n【步骤3】模拟结果")
    print("-" * 70)
    
    print(f"\n问题: {result['question']}")
    print(f"\n基于你的性格画像（{summary['decision_style']}、{summary['risk_preference']}）")
    print(f"为你模拟了3个平行宇宙的未来：\n")
    
    # 按得分排序
    sorted_options = sorted(result['options'], key=lambda x: x['final_score'], reverse=True)
    
    for i, option in enumerate(sorted_options, 1):
        print(f"\n{i}. 【{option['title']}】")
        print(f"   综合得分: {option['final_score']:.1f}/100")
        print(f"   风险等级: {option['risk_level']:.2f}")
        print(f"   关键时间点:")
        
        # 只显示前3个关键事件
        for event in option['timeline'][:3]:
            print(f"     • 第{event['month']}月: {event['event']}")
    
    print(f"\n{'='*70}")
    print(f"AI 推荐:")
    print(f"{result['recommendation']}")
    print(f"{'='*70}")
    
    # ========== 总结 ==========
    print("\n【测试总结】")
    print("-" * 70)
    print("✅ 心理测评系统 - 正常")
    print("✅ 决策模拟系统 - 正常")
    print("✅ 性格画像集成 - 正常")
    print("✅ 平行宇宙模拟 - 正常")
    
    print("\n" + "="*70)
    print("  测试完成！系统运行正常")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        test_full_workflow()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
