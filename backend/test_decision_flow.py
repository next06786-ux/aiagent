"""
测试决策流程 - 验证4阶段流程
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

async def test_decision_flow():
    """测试完整的4阶段决策流程"""
    
    print("="*60)
    print("测试决策流程 - 4阶段模式")
    print("="*60)
    
    # 模拟WebSocket回调
    events = []
    
    async def mock_callback(event_type: str, data: dict):
        """模拟WebSocket回调，记录所有事件"""
        event = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            **data
        }
        events.append(event)
        
        # 打印关键事件
        if event_type == 'round_start':
            print(f"\n🔄 [{data.get('persona_name')}] 开始第{data.get('round')}/{data.get('total_rounds')}轮")
        elif event_type == 'phase_start':
            print(f"  📍 阶段: {data.get('phase_name')}")
        elif event_type == 'phase_complete':
            phase = data.get('phase')
            if phase == 'independent_thinking':
                result = data.get('result', {})
                print(f"  ✅ 独立思考完成: {result.get('stance')} (得分: {result.get('score')})")
            elif phase == 'observe_others':
                print(f"  ✅ 观察到{data.get('observed_count')}个其他Agent的观点")
            elif phase == 'deep_reflection':
                result = data.get('result', {})
                print(f"  ✅ 深度反思完成: {result.get('stance')} (得分: {result.get('score')})")
                if result.get('stance_changed'):
                    print(f"     ⚠️  立场已改变")
            elif phase == 'decision':
                decision = data.get('decision', {})
                print(f"  ⚖️  决策: {decision.get('stance')} (得分: {decision.get('score')}, 信心: {decision.get('confidence'):.2f})")
        elif event_type == 'round_complete':
            print(f"  ⏱️  第{data.get('round')}轮完成 (耗时: {data.get('duration'):.2f}s)")
    
    # 准备测试数据
    from backend.decision.decision_personas import PersonaCouncil
    
    user_id = "test_user_001"
    question = "是否应该接受新的工作机会？"
    option = {
        "title": "接受新工作",
        "description": "薪资提升30%，但需要搬到新城市",
        "pros": ["薪资更高", "职业发展机会", "新的挑战"],
        "cons": ["需要搬家", "远离家人", "新环境适应"]
    }
    
    collected_info = {
        "concerns": ["家庭关系", "职业发展", "生活成本"],
        "constraints": {
            "time": "3个月内决定",
            "budget": "搬家预算有限"
        }
    }
    
    # 创建决策委员会
    print("\n创建决策委员会...")
    council = PersonaCouncil(user_id)
    
    # 初始化记忆系统
    print("初始化记忆系统...")
    decision_id = f"test_decision_{int(datetime.now().timestamp())}"
    await council.initialize_for_decision(
        decision_id=decision_id,
        question=question,
        options=[option],
        collected_info=collected_info
    )
    
    # 准备上下文
    decision_context = {
        "question": question,
        "collected_info": collected_info,
        "option_title": option["title"],
        "decision_type": "career",
        "status_callback": mock_callback
    }
    
    # 设置轮数（测试用，只运行2轮）
    persona_rounds = {
        "rational_analyst": 2,
        "adventurer": 2,
        "pragmatist": 2,
        "idealist": 2,
        "conservative": 2,
        "social_navigator": 2,
        "innovator": 2
    }
    
    print(f"\n开始分析决策...")
    print(f"问题: {question}")
    print(f"选项: {option['title']}")
    print(f"轮数配置: 每个Agent执行{persona_rounds['rational_analyst']}轮")
    print()
    
    # 执行分析
    result = await council.analyze_decision(
        decision_context=decision_context,
        options=[option],
        persona_rounds=persona_rounds
    )
    
    print("\n" + "="*60)
    print("分析完成")
    print("="*60)
    
    # 统计事件
    print(f"\n📊 事件统计:")
    event_types = {}
    for event in events:
        event_type = event['event_type']
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    for event_type, count in sorted(event_types.items()):
        print(f"  - {event_type}: {count}次")
    
    # 验证流程完整性
    print(f"\n✅ 流程验证:")
    
    # 每个Agent应该有：
    # - 1次 agent_start
    # - N次 round_start (N=轮数)
    # - N*4次 phase_start (每轮4个阶段)
    # - N*4次 phase_complete
    # - N次 round_complete
    # - 1次 agent_complete
    
    expected_per_agent = {
        'agent_start': 1,
        'round_start': 2,
        'phase_start': 8,  # 2轮 * 4阶段
        'phase_complete': 8,
        'round_complete': 2,
        'agent_complete': 1
    }
    
    num_agents = len(council.personas)
    for event_type, expected_count in expected_per_agent.items():
        actual_count = event_types.get(event_type, 0)
        expected_total = expected_count * num_agents
        status = "✅" if actual_count == expected_total else "❌"
        print(f"  {status} {event_type}: {actual_count}/{expected_total}")
    
    # 显示最终结果
    print(f"\n📋 最终结果:")
    option_analyses = result['all_analyses'].get('option_1', {}).get('final_analyses', {})
    for persona_id, analysis in option_analyses.items():
        persona = council.personas[persona_id]
        print(f"  [{persona.name}] {analysis.get('stance')} (得分: {analysis.get('score')}, 信心: {analysis.get('confidence', 0.7):.2f})")
    
    # 保存事件日志
    log_file = f"decision_flow_test_{int(datetime.now().timestamp())}.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'question': question,
            'option': option,
            'rounds': persona_rounds,
            'events': events,
            'result': {
                'personas_count': len(option_analyses),
                'analyses': {
                    pid: {
                        'name': council.personas[pid].name,
                        'stance': analysis.get('stance'),
                        'score': analysis.get('score'),
                        'confidence': analysis.get('confidence', 0.7)
                    }
                    for pid, analysis in option_analyses.items()
                }
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 事件日志已保存: {log_file}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_decision_flow())
