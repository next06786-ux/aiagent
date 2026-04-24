"""
测试 personas_init 事件是否正确发送
"""
import asyncio
import json
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decision.decision_personas import PersonaCouncil

async def test_personas_init():
    """测试创建 PersonaCouncil 并检查 personas 列表"""
    
    print("=" * 60)
    print("测试 PersonaCouncil 初始化")
    print("=" * 60)
    
    # 创建决策人格委员会
    user_id = "test_user_123"
    council = PersonaCouncil(user_id)
    
    print(f"\n✅ PersonaCouncil 已创建")
    print(f"Personas 数量: {len(council.personas)}")
    print(f"Personas IDs: {list(council.personas.keys())}")
    
    # 模拟 personas_init 事件数据
    personas_list = [
        {
            "id": pid,
            "name": p.name,
            "description": p.description,
            "risk_tolerance": p.value_system.risk_tolerance
        }
        for pid, p in council.personas.items()
    ]
    
    print(f"\n📤 模拟 personas_init 事件:")
    print(json.dumps({
        "type": "personas_init",
        "option_id": "option_1",
        "personas": personas_list
    }, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_personas_init())
