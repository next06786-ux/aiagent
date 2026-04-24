"""
测试智能技能选择系统
"""
import asyncio
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decision.decision_personas import create_persona_council

async def test_skill_selection():
    """测试技能选择系统"""
    print("="*60)
    print("测试智能技能选择系统")
    print("="*60)
    
    # 创建人格委员会
    council = create_persona_council("test_user")
    
    # 准备测试数据
    option = {
        "title": "换工作到大厂",
        "description": "有机会去大厂工作，薪资翻倍，但工作压力大"
    }
    
    context = {
        "question": "是否应该换工作？",
        "collected_info": {
            "age": 28,
            "career_stage": "中级工程师",
            "concerns": ["工作压力", "职业发展"]
        }
    }
    
    # 测试理性分析师的技能选择
    rational_analyst = council.personas["rational_analyst"]
    
    print(f"\n测试 {rational_analyst.name} 的智能技能选择...")
    print(f"可用技能: {rational_analyst.skill_names}")
    
    try:
        # 测试独立思考阶段的技能选择
        selected_skills = await rational_analyst._intelligent_skill_selection(
            option=option,
            context=context,
            phase="independent_thinking"
        )
        
        print(f"✅ 独立思考阶段选择的技能: {selected_skills}")
        
        # 测试深度反思阶段的技能选择
        previous_result = {
            "stance": "支持",
            "score": 75,
            "reasoning": "薪资提升明显"
        }
        
        other_views = {
            "adventurer": {
                "name": "冒险家",
                "stance": "强烈支持",
                "score": 90
            },
            "conservative": {
                "name": "保守派",
                "stance": "反对",
                "score": 40
            }
        }
        
        selected_skills_reflection = await rational_analyst._intelligent_skill_selection(
            option=option,
            context=context,
            phase="deep_reflection",
            other_views=other_views,
            previous_result=previous_result
        )
        
        print(f"✅ 深度反思阶段选择的技能: {selected_skills_reflection}")
        
        print("\n" + "="*60)
        print("✅ 测试通过！智能技能选择系统工作正常")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_skill_selection())
    sys.exit(0 if success else 1)
