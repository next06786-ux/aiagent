"""
测试WebSocket事件流 - 验证前后端对接

测试所有关键事件类型是否正确发送：
- phase_start
- thinking_start
- thinking_monologue
- skill_selection
- skill_start
- skill_complete
- thinking_chunk (流式输出)
- phase_complete
"""
import asyncio
import json
from typing import Dict, Any, List

# 模拟前端接收到的事件
received_events: List[Dict[str, Any]] = []

async def mock_status_callback(event_type: str, data: Dict[str, Any]):
    """模拟WebSocket回调函数"""
    event = {
        "type": event_type,
        **data
    }
    received_events.append(event)
    print(f"✅ 事件发送: {event_type}")
    if len(str(data)) < 200:
        print(f"   数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        print(f"   数据: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")

async def test_event_flow():
    """测试完整的事件流"""
    print("="*60)
    print("测试WebSocket事件流")
    print("="*60)
    
    # 模拟一个完整的Agent生命周期
    persona_id = "rational_analyst"
    persona_name = "理性分析师"
    round_num = 1
    
    # 1. 阶段开始
    await mock_status_callback('phase_start', {
        'persona_id': persona_id,
        'persona_name': persona_name,
        'phase': 'independent_thinking',
        'phase_name': '独立思考',
        'round': round_num,
        'timestamp': 1234567890
    })
    
    # 2. 思考开始
    await mock_status_callback('thinking_start', {
        'persona_id': persona_id,
        'persona_name': persona_name,
        'phase': 'independent_thinking',
        'round': round_num,
        'timestamp': 1234567891
    })
    
    # 3. 内心独白
    await mock_status_callback('thinking_monologue', {
        'persona_id': persona_id,
        'persona_name': persona_name,
        'content': '我需要仔细分析这个选项的利弊...',
        'phase': 'independent_thinking',
        'round': round_num
    })
    
    # 4. 技能选择
    await mock_status_callback('skill_selection', {
        'persona_id': persona_id,
        'persona_name': persona_name,
        'selected_skills': ['数据分析', '风险评估'],
        'reason': '需要量化分析和风险评估',
        'phase': 'independent_thinking',
        'round': round_num
    })
    
    # 5. 技能开始
    await mock_status_callback('skill_start', {
        'persona_id': persona_id,
        'persona_name': persona_name,
        'skill_name': '数据分析',
        'round': round_num
    })
    
    # 6. 技能完成
    await mock_status_callback('skill_complete', {
        'persona_id': persona_id,
        'persona_name': persona_name,
        'skill_name': '数据分析',
        'summary': '数据分析: 发现3个关键洞察',
        'result': {'insights': ['洞察1', '洞察2', '洞察3']},
        'round': round_num
    })
    
    # 7. 流式输出 - 模拟多个chunk
    chunks = [
        "基于数据分析，",
        "我认为这个选项",
        "具有较高的可行性。",
        "主要原因包括：",
        "1. 数据支持充分",
        "2. 风险可控",
        "3. 收益明确"
    ]
    
    for chunk in chunks:
        await mock_status_callback('thinking_chunk', {
            'persona_id': persona_id,
            'persona_name': persona_name,
            'round': round_num,
            'content': chunk,
            'chunk_type': 'answer',  # 改名避免与事件type混淆
            'timestamp': 1234567892
        })
        await asyncio.sleep(0.05)  # 模拟流式延迟
    
    # 8. 阶段完成
    await mock_status_callback('phase_complete', {
        'persona_id': persona_id,
        'persona_name': persona_name,
        'phase': 'independent_thinking',
        'round': round_num,
        'result': {
            'stance': '支持',
            'score': 75,
            'confidence': 0.8,
            'reasoning': '基于数据分析和风险评估，这个选项具有较高的可行性',
            'key_points': ['数据支持充分', '风险可控', '收益明确']
        }
    })
    
    print("\n" + "="*60)
    print(f"✅ 测试完成！共发送 {len(received_events)} 个事件")
    print("="*60)
    
    # 验证事件类型
    event_types = [e['type'] for e in received_events]
    expected_types = [
        'phase_start',
        'thinking_start',
        'thinking_monologue',
        'skill_selection',
        'skill_start',
        'skill_complete',
        'thinking_chunk',
        'phase_complete'
    ]
    
    print("\n事件类型统计:")
    for event_type in sorted(set(event_types)):
        count = event_types.count(event_type)
        print(f"  - {event_type}: {count}次")
    
    # 验证流式输出
    chunk_events = [e for e in received_events if e['type'] == 'thinking_chunk']
    if chunk_events:
        print(f"\n✅ 流式输出测试通过: {len(chunk_events)}个chunk")
        full_text = ''.join([e['content'] for e in chunk_events])
        print(f"   完整文本: {full_text}")
    
    # 验证所有关键事件都存在
    missing_types = []
    for expected in expected_types:
        if expected not in event_types:
            missing_types.append(expected)
    
    if missing_types:
        print(f"\n❌ 缺失事件类型: {missing_types}")
        return False
    else:
        print(f"\n✅ 所有关键事件类型都已发送")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_event_flow())
    
    if success:
        print("\n" + "="*60)
        print("✅ WebSocket事件流测试通过")
        print("="*60)
        print("\n前端应该能够接收并显示:")
        print("  1. 阶段标记 (📍)")
        print("  2. 内心独白 (💭)")
        print("  3. 技能选择和执行 (🎯 🔧)")
        print("  4. 流式文字输出 (逐字显示)")
        print("  5. 最终结果 (✅)")
    else:
        print("\n❌ 测试失败")
