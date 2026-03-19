"""
测试决策模拟API
"""
import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

from decision.parallel_universe_simulator import ParallelUniverseSimulator

def test_simulation():
    print("="*60)
    print("测试平行宇宙模拟器")
    print("="*60)
    
    simulator = ParallelUniverseSimulator()
    
    # 测试模拟
    result = simulator.simulate_decision(
        user_id="test_user_001",
        question="大三学生，毕业后应该选择什么？",
        options=[
            {"title": "考研", "description": "继续深造，提升学历"},
            {"title": "工作", "description": "直接就业，积累经验"},
            {"title": "创业", "description": "自主创业，追求梦想"}
        ],
        use_lora=False  # 不使用LoRA，避免依赖问题
    )
    
    print(f"\n✅ 模拟ID: {result.simulation_id}")
    print(f"✅ 问题: {result.question}")
    print(f"✅ 选项数量: {len(result.options)}")
    
    for i, option in enumerate(result.options):
        print(f"\n选项 {i+1}: {option.title}")
        print(f"  综合得分: {option.final_score:.1f}")
        print(f"  风险等级: {option.risk_level:.2f}")
        print(f"  时间线事件数: {len(option.timeline)}")
        
        if option.risk_assessment:
            print(f"  总体风险: {option.risk_assessment['overall_risk']:.1f}/10")
            print(f"  风险等级: {option.risk_assessment['overall_level']}")
    
    print(f"\n推荐:\n{result.recommendation}")
    print("\n" + "="*60)
    print("✅ 测试成功！")
    print("="*60)

if __name__ == "__main__":
    test_simulation()
