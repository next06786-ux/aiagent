"""
测试个性化 LoRA 决策分析
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

USER_ID = "2c2139f7-bab4-483d-9882-ae83ce8734cd"

async def test_lora_decision():
    """测试使用 LoRA 模型的决策分析"""
    from backend.decision.lora_decision_analyzer import LoRADecisionAnalyzer
    
    print("="*80)
    print("🧠 测试个性化 LoRA 决策分析")
    print("="*80)
    
    # 初始化分析器
    analyzer = LoRADecisionAnalyzer(USER_ID)
    
    # 测试决策场景
    decision = "是否应该换一份新工作？"
    context = {
        "current_job": "稳定但成长空间有限",
        "new_opportunity": "更高薪资但需要搬家",
        "family_situation": "有家庭需要考虑"
    }
    
    print(f"\n📋 决策问题: {decision}")
    print(f"📝 背景信息:")
    for key, value in context.items():
        print(f"   - {key}: {value}")
    
    print(f"\n🤖 开始分析...")
    print(f"   使用模型: LoRA v1 (基于你的 6 对对话训练)")
    print(f"   模型路径: ./models/lora/{USER_ID}/v1/final")
    
    try:
        # 生成个性化分析
        result = await analyzer.analyze_with_lora(
            decision=decision,
            context=context
        )
        
        print(f"\n" + "="*80)
        print(f"✅ 分析完成！")
        print(f"="*80)
        
        print(f"\n💡 个性化建议:")
        print(result.get('analysis', ''))
        
        if 'confidence' in result:
            print(f"\n📊 置信度: {result['confidence']*100:.1f}%")
        
        if 'reasoning' in result:
            print(f"\n🔍 推理过程:")
            print(result['reasoning'])
        
        print(f"\n" + "="*80)
        print(f"🎯 这个分析是基于你的对话风格和偏好生成的！")
        print(f"="*80)
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

async def test_parallel_universe():
    """测试平行宇宙模拟（使用 LoRA）"""
    from backend.decision.parallel_universe_simulator import ParallelUniverseSimulator
    
    print("\n\n" + "="*80)
    print("🌌 测试平行宇宙模拟")
    print("="*80)
    
    simulator = ParallelUniverseSimulator(USER_ID)
    
    decision = "是否应该创业？"
    options = [
        {"id": "A", "name": "继续打工", "description": "保持稳定收入"},
        {"id": "B", "name": "全职创业", "description": "追求梦想但有风险"}
    ]
    
    print(f"\n📋 决策: {decision}")
    print(f"📝 选项:")
    for opt in options:
        print(f"   {opt['id']}. {opt['name']} - {opt['description']}")
    
    print(f"\n🌟 生成平行宇宙时间线...")
    print(f"   使用你的个性化 LoRA 模型")
    
    try:
        result = await simulator.simulate_decision(
            decision=decision,
            options=options,
            time_horizon_years=5
        )
        
        print(f"\n✅ 模拟完成！")
        print(f"\n🌍 生成了 {len(result.get('universes', []))} 个平行宇宙")
        
        for i, universe in enumerate(result.get('universes', []), 1):
            print(f"\n--- 宇宙 {i}: {universe.get('name', '')} ---")
            print(f"选择: {universe.get('choice', '')}")
            print(f"概率: {universe.get('probability', 0)*100:.1f}%")
            
            if 'timeline' in universe:
                print(f"时间线事件:")
                for event in universe['timeline'][:3]:  # 只显示前3个事件
                    print(f"  • {event.get('time', '')}: {event.get('event', '')}")
        
        print(f"\n💡 这些时间线是根据你的性格和偏好生成的！")
        
    except Exception as e:
        print(f"\n❌ 模拟失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主测试流程"""
    print("\n🚀 开始测试个性化决策系统\n")
    
    # 测试 1: LoRA 决策分析
    await test_lora_decision()
    
    # 测试 2: 平行宇宙模拟
    await test_parallel_universe()
    
    print("\n\n" + "="*80)
    print("🎉 测试完成！")
    print("="*80)
    print("\n💡 提示:")
    print("   - 继续与 AI 对话，积累更多数据")
    print("   - 每周系统会自动重新训练模型")
    print("   - 模型会随着使用不断改进")
    print("   - 现在可以在前端使用决策模拟功能了！")

if __name__ == "__main__":
    asyncio.run(main())
