"""
测试LoRA时间线生成
验证决策模拟是否正确使用本地模型+LoRA
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.decision.parallel_universe_simulator import ParallelUniverseSimulator
from backend.personality.personality_test import PersonalityTest
from backend.lora.lora_model_manager import lora_manager


def test_lora_timeline_generation():
    """测试LoRA时间线生成"""
    print("="*80)
    print("测试 LoRA 时间线生成")
    print("="*80)
    
    # 1. 检查LoRA模型状态
    user_id = "test_user"
    print(f"\n1. 检查用户 {user_id} 的LoRA模型状态...")
    
    has_lora = lora_manager.has_lora_model(user_id)
    print(f"   有LoRA模型: {has_lora}")
    
    if has_lora:
        model_info = lora_manager.get_model_info(user_id)
        print(f"   模型版本: v{model_info.get('model_version', 0)}")
        print(f"   训练数据量: {model_info.get('current_data_size', 0)}")
    else:
        print("   ⚠️ 用户还没有LoRA模型")
        print("   💡 提示: 运行 test_lora_training.py 来训练模型")
        print("\n   继续测试（将使用规则生成）...")
    
    # 2. 创建模拟器
    print("\n2. 创建平行宇宙模拟器...")
    simulator = ParallelUniverseSimulator()
    
    # 3. 准备测试数据
    question = "大三学生，毕业后应该考研还是工作？"
    options = [
        {
            "title": "考研",
            "description": "继续深造，提升学历，为未来发展打基础"
        },
        {
            "title": "工作",
            "description": "直接就业，积累实战经验，开始赚钱"
        }
    ]
    
    print(f"\n3. 测试决策问题: {question}")
    print(f"   选项数量: {len(options)}")
    
    # 4. 使用LoRA进行模拟
    print("\n4. 开始决策模拟（use_lora=True）...")
    print("   这将使用本地模型 Qwen3.5-0.8B + LoRA 生成时间线")
    
    result = simulator.simulate_decision(
        user_id=user_id,
        question=question,
        options=options,
        use_lora=True  # 启用LoRA
    )
    
    # 5. 显示结果
    print("\n" + "="*80)
    print("模拟结果")
    print("="*80)
    
    for i, option in enumerate(result.options, 1):
        print(f"\n【选项 {i}】{option.title}")
        print(f"描述: {option.description}")
        print(f"综合得分: {option.final_score:.1f}/100")
        print(f"风险等级: {option.risk_level:.2f}")
        
        print(f"\n时间线（共{len(option.timeline)}个事件）:")
        for event in option.timeline:
            print(f"\n  第 {event.month} 月:")
            print(f"  事件: {event.event}")
            print(f"  影响: {event.impact}")
            print(f"  概率: {event.probability:.0%}")
        
        if option.risk_assessment:
            risk = option.risk_assessment
            print(f"\n  风险评估:")
            print(f"  - 总体风险: {risk['overall_risk']:.2f}")
            print(f"  - 风险等级: {risk['overall_level']}")
            print(f"  - 高风险维度数: {risk['high_risk_count']}")
    
    print("\n" + "="*80)
    print("AI 推荐")
    print("="*80)
    print(result.recommendation)
    
    # 6. 验证是否使用了LoRA
    print("\n" + "="*80)
    print("验证结果")
    print("="*80)
    
    if has_lora:
        print("✅ 用户有LoRA模型")
        print("✅ 时间线应该是由 Qwen3.5-0.8B + LoRA 生成的个性化内容")
        print("✅ 推荐应该是由 LoRA 生成的个性化建议")
    else:
        print("⚠️ 用户没有LoRA模型")
        print("⚠️ 时间线使用规则生成（降级方案）")
        print("⚠️ 推荐使用基础模板生成")
    
    print(f"\n模拟ID: {result.simulation_id}")
    print(f"保存位置: ./data/simulations/{result.simulation_id}.json")
    
    return result


def test_with_and_without_lora():
    """对比使用和不使用LoRA的差异"""
    print("\n" + "="*80)
    print("对比测试：使用 vs 不使用 LoRA")
    print("="*80)
    
    user_id = "test_user"
    question = "应该换工作吗？"
    options = [
        {"title": "换工作", "description": "寻找更好的机会"},
        {"title": "留下来", "description": "继续在当前公司发展"}
    ]
    
    simulator = ParallelUniverseSimulator()
    
    # 不使用LoRA
    print("\n【测试1】不使用LoRA (use_lora=False)")
    result_no_lora = simulator.simulate_decision(
        user_id=user_id,
        question=question,
        options=options,
        use_lora=False
    )
    
    print(f"选项1时间线事件数: {len(result_no_lora.options[0].timeline)}")
    print(f"推荐长度: {len(result_no_lora.recommendation)} 字符")
    
    # 使用LoRA
    print("\n【测试2】使用LoRA (use_lora=True)")
    result_with_lora = simulator.simulate_decision(
        user_id=user_id,
        question=question,
        options=options,
        use_lora=True
    )
    
    print(f"选项1时间线事件数: {len(result_with_lora.options[0].timeline)}")
    print(f"推荐长度: {len(result_with_lora.recommendation)} 字符")
    
    # 对比
    print("\n" + "="*80)
    print("对比结果")
    print("="*80)
    
    if lora_manager.has_lora_model(user_id):
        print("✅ 用户有LoRA模型，两次测试应该有明显差异")
        print(f"\n不使用LoRA的推荐:\n{result_no_lora.recommendation[:200]}...")
        print(f"\n使用LoRA的推荐:\n{result_with_lora.recommendation[:200]}...")
    else:
        print("⚠️ 用户没有LoRA模型，两次测试结果应该相同（都使用规则）")


if __name__ == "__main__":
    try:
        # 基础测试
        result = test_lora_timeline_generation()
        
        # 对比测试
        print("\n\n")
        test_with_and_without_lora()
        
        print("\n" + "="*80)
        print("测试完成！")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
