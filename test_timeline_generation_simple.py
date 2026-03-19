"""
测试简化后的时间线生成
"""
from backend.decision.lora_decision_analyzer import LoRADecisionAnalyzer
from backend.personality.personality_test import PersonalityTest

def test_timeline():
    """测试时间线生成"""
    user_id = "a113a299-ecff-4363-8d44-aff979dfc547"
    
    print(f"\n{'='*80}")
    print(f"测试简化后的时间线生成")
    print(f"{'='*80}\n")
    
    # 初始化
    analyzer = LoRADecisionAnalyzer()
    personality_test = PersonalityTest()
    
    # 加载性格画像
    profile = personality_test.load_profile(user_id)
    
    # 测试选项
    option = {
        "title": "继续读研",
        "description": "攻读硕士学位"
    }
    
    question = "毕业后干嘛"
    
    print(f"问题: {question}")
    print(f"选项: {option['title']}")
    print(f"生成事件数: 3\n")
    
    # 生成时间线
    try:
        timeline = analyzer.generate_timeline_with_lora(
            user_id=user_id,
            question=question,
            option=option,
            profile=profile,
            num_events=3
        )
        
        if timeline:
            print(f"✅ 成功生成 {len(timeline)} 个事件\n")
            for i, event in enumerate(timeline, 1):
                print(f"事件 {i}:")
                print(f"  月份: {event['month']}")
                print(f"  描述: {event['event']}")
                print(f"  概率: {event['probability']}")
                print(f"  影响: {event.get('impact', {})}\n")
        else:
            print("❌ 生成失败，返回空列表")
            
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_timeline()
