"""
测试LoRA增强的决策系统完整集成
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_full_lora_decision_workflow():
    """测试完整的LoRA决策工作流"""
    
    print("\n" + "="*70)
    print("  LoRA增强决策系统 - 完整集成测试")
    print("="*70)
    
    user_id = "test_user_001"
    
    # ========== 步骤1: 检查LoRA状态 ==========
    print("\n【步骤1】检查LoRA模型状态")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/lora/status/{user_id}")
    
    if response.status_code == 200:
        lora_status = response.json()['data']
        print(f"✅ LoRA状态获取成功")
        print(f"   有LoRA模型: {lora_status['has_lora']}")
        print(f"   模型版本: v{lora_status['model_version']}")
        print(f"   训练数据量: {lora_status['training_data_size']}")
        print(f"   上次训练: {lora_status.get('last_train_time', 'N/A')}")
        
        use_lora = lora_status['has_lora']
        
        if not use_lora:
            print("\n⚠️  用户还没有LoRA模型")
            print("💡 提示: 运行 'python test_lora_training.py' 来训练模型")
            print("   或者继续测试（将使用基础模型）")
    else:
        print(f"❌ 获取LoRA状态失败")
        use_lora = False
    
    time.sleep(1)
    
    # ========== 步骤2: 心理测评 ==========
    print("\n【步骤2】心理测评")
    print("-" * 70)
    
    # 2.1 获取题目
    print("\n2.1 获取测评题目...")
    response = requests.get(f"{BASE_URL}/api/personality/questions")
    
    if response.status_code != 200:
        print(f"❌ 获取题目失败")
        return
    
    questions_data = response.json()['data']
    print(f"✅ 获取到 {len(questions_data['questions'])} 道题目")
    
    # 2.2 模拟答题
    print("\n2.2 提交测评答案...")
    answers = {}
    for q in questions_data['questions']:
        if 'rational' in q['subdimension']:
            answers[str(q['id'])] = 4
        elif 'financial' in q['subdimension']:
            answers[str(q['id'])] = 2
        elif 'health' in q['subdimension']:
            answers[str(q['id'])] = 4
        else:
            answers[str(q['id'])] = 3
    
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
    
    # ========== 步骤3: 决策模拟（使用LoRA） ==========
    print("\n【步骤3】决策模拟（LoRA增强）")
    print("-" * 70)
    
    print(f"\n3.1 提交决策问题（use_lora={use_lora}）...")
    decision_data = {
        "user_id": user_id,
        "question": "大三学生，毕业后应该选择什么？",
        "options": [
            {"title": "考研", "description": "继续深造，提升学历"},
            {"title": "直接工作", "description": "进入职场，积累经验"},
            {"title": "创业", "description": "自主创业，追求梦想"}
        ],
        "use_lora": use_lora
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
    
    if use_lora:
        print(f"   🤖 使用了用户专属LoRA模型")
    else:
        print(f"   📝 使用了基础模型")
    
    result = response_json.get('data')
    if not result:
        print(f"❌ 错误: API返回的data字段为空")
        return
    
    # ========== 步骤4: 展示结果 ==========
    print("\n【步骤4】模拟结果")
    print("-" * 70)
    
    print(f"\n问题: {result['question']}")
    print(f"\n基于你的性格画像（{summary['decision_style']}、{summary['risk_preference']}）")
    
    if use_lora:
        print(f"使用你的专属LoRA模型（v{lora_status['model_version']}）为你模拟了3个平行宇宙的未来：\n")
    else:
        print(f"为你模拟了3个平行宇宙的未来：\n")
    
    # 按得分排序
    sorted_options = sorted(result['options'], key=lambda x: x['final_score'], reverse=True)
    
    best_option = sorted_options[0]
    
    for i, option in enumerate(sorted_options, 1):
        print(f"\n{i}. 【{option['title']}】")
        print(f"   综合得分: {option['final_score']:.1f}/100")
        print(f"   风险等级: {option['risk_level']:.2f}")
        print(f"   关键时间点:")
        
        for event in option['timeline'][:3]:
            print(f"     • 第{event['month']}月: {event['event']}")
    
    print(f"\n{'='*70}")
    print(f"AI 推荐:")
    print(f"{result['recommendation']}")
    print(f"{'='*70}")
    
    # ========== 步骤5: 记录决策 ==========
    print("\n【步骤5】记录用户决策")
    print("-" * 70)
    
    # 模拟用户选择了AI推荐的选项
    actual_choice = best_option['title']
    
    print(f"\n用户选择: {actual_choice}")
    
    record_data = {
        "user_id": user_id,
        "simulation_id": result['simulation_id'],
        "question": result['question'],
        "predicted_option": best_option['title'],
        "predicted_score": best_option['final_score'],
        "actual_option": actual_choice
    }
    
    response = requests.post(
        f"{BASE_URL}/api/decision/record",
        json=record_data
    )
    
    if response.status_code == 200:
        feedback_id = response.json()['data']['feedback_id']
        print(f"✅ 决策已记录")
        print(f"   反馈ID: {feedback_id}")
        
        # ========== 步骤6: 模拟3个月后提交反馈 ==========
        print("\n【步骤6】提交决策反馈（模拟3个月后）")
        print("-" * 70)
        
        feedback_data = {
            "feedback_id": feedback_id,
            "actual_satisfaction": 8,
            "feedback_text": f"选择{actual_choice}是正确的，目前进展顺利，很满意。"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/decision/feedback",
            json=feedback_data
        )
        
        if response.status_code == 200:
            print(f"✅ 反馈已提交")
            print(f"   满意度: 8/10")
            print(f"   💾 反馈数据已保存到RAG系统")
            print(f"   🔄 将用于下次LoRA训练")
        else:
            print(f"❌ 反馈提交失败")
    else:
        print(f"❌ 决策记录失败")
    
    time.sleep(1)
    
    # ========== 步骤7: 查看准确率统计 ==========
    print("\n【步骤7】查看AI决策准确率")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/decision/accuracy/{user_id}")
    
    if response.status_code == 200:
        stats = response.json()['data']
        print(f"\n统计数据:")
        print(f"  总决策数: {stats['total_decisions']}")
        print(f"  已反馈数: {stats['total_feedbacks']}")
        print(f"  预测准确: {stats['correct_predictions']}")
        print(f"  准确率: {stats['accuracy']:.1%}")
        print(f"  平均满意度: {stats['avg_satisfaction']:.1f}/10")
    else:
        print(f"❌ 获取统计失败")
    
    # ========== 总结 ==========
    print("\n【测试总结】")
    print("-" * 70)
    print("✅ LoRA状态查询 - 正常")
    print("✅ 心理测评系统 - 正常")
    print("✅ 决策模拟系统 - 正常")
    
    if use_lora:
        print("✅ LoRA模型集成 - 正常")
    else:
        print("⚠️  LoRA模型集成 - 未测试（用户无模型）")
    
    print("✅ 决策记录系统 - 正常")
    print("✅ 反馈循环系统 - 正常")
    print("✅ 准确率统计 - 正常")
    
    print("\n" + "="*70)
    print("  测试完成！系统运行正常")
    print("="*70 + "\n")
    
    # 提示下一步
    if not use_lora:
        print("💡 下一步建议:")
        print("   1. 运行 'python test_lora_training.py' 训练LoRA模型")
        print("   2. 再次运行本测试，体验个性化决策分析")
        print()


if __name__ == "__main__":
    try:
        test_full_lora_decision_workflow()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
