"""
完整决策流程测试
测试从信息收集到决策模拟的完整流程
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.decision.decision_info_collector import DecisionInfoCollector
from backend.decision.parallel_universe_simulator import ParallelUniverseSimulator
from backend.lora.lora_model_manager import lora_manager


def test_complete_flow():
    """测试完整的决策流程"""
    print("="*80)
    print("完整决策流程测试")
    print("="*80)
    
    user_id = "test_user"
    
    # 阶段1: 检查LoRA状态
    print("\n【阶段1】检查LoRA模型状态")
    print("-"*80)
    
    has_lora = lora_manager.has_lora_model(user_id)
    print(f"用户 {user_id} 有LoRA模型: {has_lora}")
    
    if has_lora:
        model_info = lora_manager.get_model_info(user_id)
        print(f"模型版本: v{model_info.get('model_version', 0)}")
        print(f"训练数据量: {model_info.get('current_data_size', 0)}")
        print(f"是否已加载: {model_info.get('is_loaded', False)}")
    else:
        print("⚠️ 用户还没有LoRA模型")
        print("💡 提示: 运行以下命令训练模型:")
        print("   python test_lora_training.py")
        print("\n继续测试（将使用规则生成）...")
    
    # 阶段2: 信息收集（使用Qwen3.5-plus API）
    print("\n【阶段2】信息收集阶段（使用 Qwen3.5-plus API）")
    print("-"*80)
    
    collector = DecisionInfoCollector()
    
    initial_question = "我是一名大三学生，毕业后应该考研还是直接工作？"
    print(f"初始问题: {initial_question}")
    
    # 开始收集
    result = collector.start_collection(
        user_id=user_id,
        initial_question=initial_question
    )
    
    session_id = result['session_id']
    print(f"会话ID: {session_id}")
    print(f"AI回复: {result['ai_question']}")
    
    # 模拟用户回答
    user_responses = [
        "我比较喜欢学习，但是家里经济条件一般，需要考虑经济因素。",
        "我的专业是计算机科学，成绩中等偏上。",
        "没有了，这些就是我的主要考虑。"
    ]
    
    for i, response in enumerate(user_responses, 1):
        print(f"\n用户回答 {i}: {response}")
        
        result = collector.continue_collection(
            session_id=session_id,
            user_response=response
        )
        
        if result.get('is_complete'):
            print("\n✅ 信息收集完成！")
            print(f"收集轮次: {result['round']}")
            print(f"\n收集的信息:")
            collected_info = result.get('collected_info', {})
            print(json.dumps(collected_info, ensure_ascii=False, indent=2))
            break
        else:
            print(f"AI继续提问: {result['ai_question']}")
    
    # 阶段3: 生成选项
    print("\n【阶段3】生成决策选项")
    print("-"*80)
    
    options = [
        {"title": "考研", "description": "继续深造，提升学历"},
        {"title": "工作", "description": "直接就业，积累经验"}
    ]
    
    print(f"决策选项:")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt['title']}: {opt['description']}")
    
    # 阶段4: 决策模拟（使用本地模型+LoRA）
    print("\n【阶段4】决策模拟阶段（使用 Qwen3.5-0.8B + LoRA）")
    print("-"*80)
    
    simulator = ParallelUniverseSimulator()
    
    print("开始模拟...")
    if has_lora:
        print("✅ 将使用个性化LoRA模型生成时间线")
    else:
        print("⚠️ 将使用规则生成时间线（降级方案）")
    
    simulation_result = simulator.simulate_decision(
        user_id=user_id,
        question=initial_question,
        options=options,
        use_lora=True  # 启用LoRA
    )
    
    # 显示结果
    print("\n" + "="*80)
    print("模拟结果")
    print("="*80)
    
    for i, option in enumerate(simulation_result.options, 1):
        print(f"\n【选项 {i}】{option.title}")
        print(f"描述: {option.description}")
        print(f"综合得分: {option.final_score:.1f}/100")
        print(f"风险等级: {option.risk_level:.2f}")
        
        print(f"\n时间线（共 {len(option.timeline)} 个事件）:")
        for event in option.timeline:
            print(f"\n  第 {event.month} 月:")
            print(f"  事件: {event.event}")
            
            # 显示主要影响
            positive_impacts = {k: v for k, v in event.impact.items() if v > 0.1}
            negative_impacts = {k: v for k, v in event.impact.items() if v < -0.1}
            
            if positive_impacts:
                print(f"  正面影响: {', '.join([f'{k}+{v:.1f}' for k, v in positive_impacts.items()])}")
            if negative_impacts:
                print(f"  负面影响: {', '.join([f'{k}{v:.1f}' for k, v in negative_impacts.items()])}")
            
            print(f"  概率: {event.probability:.0%}")
    
    print("\n" + "="*80)
    print("AI 推荐")
    print("="*80)
    print(simulation_result.recommendation)
    
    # 验证
    print("\n" + "="*80)
    print("流程验证")
    print("="*80)
    
    print("✅ 阶段1: 信息收集 - 使用 Qwen3.5-plus API")
    
    if has_lora:
        print("✅ 阶段2: 决策模拟 - 使用 Qwen3.5-0.8B + LoRA")
        print("   - 时间线生成: LoRA个性化生成")
        print("   - 推荐生成: LoRA个性化生成")
    else:
        print("⚠️ 阶段2: 决策模拟 - 使用规则生成（降级）")
        print("   - 时间线生成: 规则模板")
        print("   - 推荐生成: 基础模板")
    
    print(f"\n模拟ID: {simulation_result.simulation_id}")
    print(f"保存位置: ./data/simulations/{simulation_result.simulation_id}.json")
    
    return simulation_result


def test_lora_vs_rules():
    """对比LoRA生成和规则生成的差异"""
    print("\n" + "="*80)
    print("对比测试：LoRA vs 规则生成")
    print("="*80)
    
    user_id = "test_user"
    question = "应该换工作吗？"
    options = [
        {"title": "换工作", "description": "寻找更好的机会"},
        {"title": "留下来", "description": "继续在当前公司发展"}
    ]
    
    simulator = ParallelUniverseSimulator()
    
    # 测试1: 不使用LoRA
    print("\n【测试1】不使用LoRA (use_lora=False)")
    print("-"*80)
    
    result_no_lora = simulator.simulate_decision(
        user_id=user_id,
        question=question,
        options=options,
        use_lora=False
    )
    
    print(f"选项1: {result_no_lora.options[0].title}")
    print(f"  时间线事件数: {len(result_no_lora.options[0].timeline)}")
    print(f"  第1个事件: {result_no_lora.options[0].timeline[0].event}")
    print(f"  推荐长度: {len(result_no_lora.recommendation)} 字符")
    
    # 测试2: 使用LoRA
    print("\n【测试2】使用LoRA (use_lora=True)")
    print("-"*80)
    
    result_with_lora = simulator.simulate_decision(
        user_id=user_id,
        question=question,
        options=options,
        use_lora=True
    )
    
    print(f"选项1: {result_with_lora.options[0].title}")
    print(f"  时间线事件数: {len(result_with_lora.options[0].timeline)}")
    print(f"  第1个事件: {result_with_lora.options[0].timeline[0].event}")
    print(f"  推荐长度: {len(result_with_lora.recommendation)} 字符")
    
    # 对比
    print("\n" + "="*80)
    print("对比结果")
    print("="*80)
    
    has_lora = lora_manager.has_lora_model(user_id)
    
    if has_lora:
        print("✅ 用户有LoRA模型")
        print("\n不使用LoRA的第1个事件:")
        print(f"  {result_no_lora.options[0].timeline[0].event}")
        print("\n使用LoRA的第1个事件:")
        print(f"  {result_with_lora.options[0].timeline[0].event}")
        
        if result_no_lora.options[0].timeline[0].event != result_with_lora.options[0].timeline[0].event:
            print("\n✅ 两次生成的内容不同，LoRA生成了个性化内容")
        else:
            print("\n⚠️ 两次生成的内容相同，可能LoRA未正确调用")
    else:
        print("⚠️ 用户没有LoRA模型")
        print("两次测试都使用规则生成，结果应该相同")


if __name__ == "__main__":
    try:
        # 完整流程测试
        result = test_complete_flow()
        
        # 对比测试
        print("\n\n")
        test_lora_vs_rules()
        
        print("\n" + "="*80)
        print("测试完成！")
        print("="*80)
        print("\n总结:")
        print("1. 信息收集阶段使用 Qwen3.5-plus API（在线）")
        print("2. 决策模拟阶段使用 Qwen3.5-0.8B + LoRA（本地）")
        print("3. 如果用户没有LoRA模型，自动降级到规则生成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
