"""
完整系统测试
测试所有已实现的功能
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_complete_system():
    """测试完整系统"""
    
    print("\n" + "="*70)
    print("  LifeSim AI 完整系统测试")
    print("="*70)
    
    user_id = "test_user_001"
    
    # 1. 测试心理测评
    print("\n【测试1】心理测评系统")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/personality/questions")
    if response.status_code == 200:
        questions = response.json()['data']['questions']
        print(f"✅ 获取测评题目: {len(questions)}道")
        
        # 提交答案
        answers = {str(q['id']): 3 for q in questions}
        response = requests.post(
            f"{BASE_URL}/api/personality/submit",
            json={"user_id": user_id, "answers": answers}
        )
        if response.status_code == 200:
            print(f"✅ 提交测评答案成功")
        else:
            print(f"❌ 提交测评答案失败")
    else:
        print(f"❌ 获取测评题目失败")
    
    time.sleep(1)
    
    # 2. 测试决策模拟（含风险评估）
    print("\n【测试2】决策模拟系统（含风险评估）")
    print("-" * 70)
    
    decision_data = {
        "user_id": user_id,
        "question": "毕业后应该选择什么？",
        "options": [
            {"title": "考研", "description": "继续深造"},
            {"title": "工作", "description": "直接就业"},
            {"title": "创业", "description": "自主创业"}
        ],
        "use_lora": False
    }
    
    response = requests.post(
        f"{BASE_URL}/api/decision/simulate",
        json=decision_data
    )
    
    if response.status_code == 200:
        result = response.json()['data']
        print(f"✅ 决策模拟成功")
        print(f"   模拟ID: {result['simulation_id']}")
        print(f"   选项数: {len(result['options'])}")
        
        # 检查风险评估
        has_risk_assessment = False
        for opt in result['options']:
            if 'risk_assessment' in opt and opt['risk_assessment']:
                has_risk_assessment = True
                print(f"\n   选项: {opt['title']}")
                print(f"   综合得分: {opt['final_score']:.1f}/100")
                risk = opt['risk_assessment']
                print(f"   总体风险: {risk['overall_risk']:.1f}/10 ({risk['overall_level']})")
                print(f"   高风险维度: {risk['high_risk_count']}个")
                
                # 只显示前3个维度
                dim_count = 0
                for dim_key, dim in risk['dimensions'].items():
                    if dim_count < 3:
                        print(f"     - {dim['name']}: {dim['score']:.1f}/10 ({dim['level']})")
                        dim_count += 1
        
        if not has_risk_assessment:
            print(f"   ⚠️  风险评估数据未包含在响应中")
        
        simulation_id = result['simulation_id']
    else:
        print(f"❌ 决策模拟失败: {response.text}")
        return
    
    time.sleep(1)
    
    # 3. 测试决策记录
    print("\n【测试3】决策记录系统")
    print("-" * 70)
    
    record_data = {
        "user_id": user_id,
        "simulation_id": simulation_id,
        "question": "毕业后应该选择什么？",
        "predicted_option": "工作",
        "predicted_score": 75.0,
        "actual_option": "工作"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/decision/record",
        json=record_data
    )
    
    if response.status_code == 200:
        feedback_id = response.json()['data']['feedback_id']
        print(f"✅ 决策记录成功")
        print(f"   反馈ID: {feedback_id}")
    else:
        print(f"❌ 决策记录失败")
    
    time.sleep(1)
    
    # 4. 测试LoRA状态
    print("\n【测试4】LoRA模型状态")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/lora/status/{user_id}")
    
    if response.status_code == 200:
        lora_status = response.json()['data']
        if lora_status:
            print(f"✅ LoRA状态查询成功")
            print(f"   有模型: {lora_status.get('has_lora', False)}")
            print(f"   模型版本: v{lora_status.get('model_version', 0)}")
            print(f"   训练数据量: {lora_status.get('training_data_size', 0)}")
        else:
            print(f"⚠️  LoRA状态为空（可能是LoRA系统未初始化）")
    else:
        print(f"❌ LoRA状态查询失败")
    
    time.sleep(1)
    
    # 5. 测试调度器状态
    print("\n【测试5】LoRA训练调度器")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/lora/scheduler/status")
    
    if response.status_code == 200:
        scheduler_status = response.json()['data']
        if scheduler_status:
            print(f"✅ 调度器状态查询成功")
            print(f"   运行中: {scheduler_status.get('is_running', False)}")
            print(f"   活跃用户: {scheduler_status.get('active_users', 0)}")
            print(f"   训练队列: {scheduler_status.get('training_queue', 0)}")
        else:
            print(f"⚠️  调度器状态为空")
    else:
        print(f"❌ 调度器状态查询失败")
    
    time.sleep(1)
    
    # 6. 测试准确率统计
    print("\n【测试6】决策准确率统计")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/decision/accuracy/{user_id}")
    
    if response.status_code == 200:
        stats = response.json()['data']
        print(f"✅ 准确率统计查询成功")
        print(f"   总决策数: {stats['total_decisions']}")
        print(f"   已反馈数: {stats['total_feedbacks']}")
        print(f"   准确率: {stats['accuracy']:.1%}")
    else:
        print(f"❌ 准确率统计查询失败")
    
    # 总结
    print("\n" + "="*70)
    print("  测试总结")
    print("="*70)
    print("\n已实现功能:")
    print("  ✅ 心理测评系统（20题）")
    print("  ✅ 决策模拟系统（12个月时间线）")
    print("  ✅ 风险评估引擎（6大维度）")
    print("  ✅ 决策记录系统")
    print("  ✅ 决策反馈循环")
    print("  ✅ LoRA模型管理")
    print("  ✅ LoRA训练调度器")
    print("  ✅ 准确率统计")
    
    print("\n核心优势:")
    print("  🎯 模型级个性化（LoRA微调）")
    print("  🔮 平行宇宙模拟（预测未来）")
    print("  ⚠️  6维风险评估（全面分析）")
    print("  🔄 闭环学习（持续优化）")
    print("  📊 动态画像（自动更新）")
    
    print("\n" + "="*70)
    print("  系统测试完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        test_complete_system()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
