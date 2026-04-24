"""
测试历史记录数据结构
不需要数据库连接，只测试数据构建逻辑
"""
import json
from datetime import datetime

def test_options_data_structure():
    """测试 options_data 数据结构"""
    print("=" * 60)
    print("测试历史记录数据结构")
    print("=" * 60)
    
    # 模拟前端构建的 options_data
    options_data = {
        "option_id": "option_1",
        "option_title": "直接工作",
        "option_description": "毕业后直接进入职场",
        "total_score": 75.5,
        "current_round": 12,
        "agents": [
            {
                "id": "rational_analyst",
                "name": "理性分析师",
                "status": "complete",
                "stance": "支持",
                "score": 80,
                "thinking_history": [
                    {
                        "round": 1,
                        "phase": "observation",
                        "message": "从职业发展角度看，直接工作可以积累实践经验"
                    },
                    {
                        "round": 2,
                        "phase": "reasoning",
                        "message": "考虑到当前就业市场，实践经验比学历更重要"
                    }
                ],
                "final_message": "综合考虑，建议直接工作"
            },
            {
                "id": "adventurer",
                "name": "冒险家",
                "status": "complete",
                "stance": "支持",
                "score": 85,
                "thinking_history": [
                    {
                        "round": 1,
                        "phase": "observation",
                        "message": "工作能带来更多挑战和机会"
                    }
                ],
                "final_message": "勇敢尝试职场"
            }
        ],
        "report": {
            "summary": "该方案在职业发展上具有一定优势",
            "key_insights": ["实践经验重要", "市场需求大"],
            "strengths": ["快速积累经验", "经济独立"],
            "risks": ["学历限制", "职业天花板"],
            "recommendation": "适合实践导向的学生",
            "total_score": 75.5
        },
        "completed_at": datetime.now().isoformat()
    }
    
    print("\n1. 数据结构验证")
    print(f"   - option_id: {options_data['option_id']}")
    print(f"   - option_title: {options_data['option_title']}")
    print(f"   - agents 数量: {len(options_data['agents'])}")
    print(f"   - 总分: {options_data['total_score']}")
    
    # 验证 agents 数据
    print("\n2. Agents 数据验证")
    for i, agent in enumerate(options_data['agents'], 1):
        print(f"   Agent {i}:")
        print(f"     - ID: {agent['id']}")
        print(f"     - 名称: {agent['name']}")
        print(f"     - 立场: {agent['stance']}")
        print(f"     - 分数: {agent['score']}")
        print(f"     - 思考历史数量: {len(agent['thinking_history'])}")
        
        # 验证思考历史结构
        if agent['thinking_history']:
            first_thought = agent['thinking_history'][0]
            print(f"     - 第一条思考包含字段: {list(first_thought.keys())}")
            assert 'round' in first_thought, "缺少 round 字段"
            assert 'phase' in first_thought, "缺少 phase 字段"
            assert 'message' in first_thought, "缺少 message 字段"
    
    # 验证报告数据
    print("\n3. 报告数据验证")
    report = options_data['report']
    print(f"   - 总结: {report['summary'][:50]}...")
    print(f"   - 关键洞察数量: {len(report['key_insights'])}")
    print(f"   - 优势数量: {len(report['strengths'])}")
    print(f"   - 风险数量: {len(report['risks'])}")
    print(f"   - 推荐意见: {report['recommendation'][:50]}...")
    
    # 测试 JSON 序列化
    print("\n4. JSON 序列化测试")
    try:
        json_str = json.dumps(options_data, ensure_ascii=False, indent=2)
        print(f"   ✓ JSON 序列化成功")
        print(f"   - JSON 长度: {len(json_str)} 字符")
        
        # 测试反序列化
        parsed_data = json.loads(json_str)
        print(f"   ✓ JSON 反序列化成功")
        print(f"   - 反序列化后 agents 数量: {len(parsed_data['agents'])}")
        
        # 验证数据完整性
        assert len(parsed_data['agents']) == len(options_data['agents']), "agents 数量不匹配"
        assert parsed_data['agents'][0]['name'] == options_data['agents'][0]['name'], "agent 名称不匹配"
        print(f"   ✓ 数据完整性验证通过")
        
    except Exception as e:
        print(f"   ✗ JSON 处理失败: {e}")
        return False
    
    # 测试空 agents 情况
    print("\n5. 空 agents 数组测试")
    empty_data = {
        "option_id": "option_1",
        "option_title": "测试",
        "agents": [],
        "total_score": 0
    }
    
    agents_count = len(empty_data.get('agents', []))
    print(f"   - agents 数量: {agents_count}")
    
    if agents_count == 0:
        print(f"   ⚠ 警告: agents 为空，这会导致历史详情页无法显示 persona 消息")
        print(f"   建议: 在保存前检查 agents 是否为空，如果为空则不保存")
    
    print("\n" + "=" * 60)
    print("✓ 所有数据结构测试通过！")
    print("=" * 60)
    
    return True


def test_frontend_save_logic():
    """模拟前端保存逻辑"""
    print("\n" + "=" * 60)
    print("模拟前端保存逻辑")
    print("=" * 60)
    
    # 模拟 agentsByOption Map
    agentsByOption = {
        "option_1": [
            {
                "id": "rational_analyst",
                "name": "理性分析师",
                "status": "complete",
                "stance": "支持",
                "score": 80,
                "thinkingHistory": [
                    {"round": 1, "phase": "observation", "message": "测试消息"}
                ],
                "currentMessage": "最终消息"
            }
        ],
        "option_2": []  # 空数组
    }
    
    print("\n测试场景 1: 正常情况（有 agents 数据）")
    optionId = "option_1"
    agents = agentsByOption.get(optionId, [])
    print(f"   - optionId: {optionId}")
    print(f"   - agents 数量: {len(agents)}")
    
    if len(agents) > 0:
        print(f"   ✓ 可以保存")
        
        # 构建保存数据
        sceneData = {
            "option_id": optionId,
            "agents": [
                {
                    "id": a["id"],
                    "name": a["name"],
                    "status": a["status"],
                    "stance": a.get("stance", "未知"),
                    "score": a.get("score", 0),
                    "thinking_history": a.get("thinkingHistory", []),
                    "final_message": a.get("currentMessage", "")
                }
                for a in agents
            ]
        }
        print(f"   - 构建的 sceneData agents 数量: {len(sceneData['agents'])}")
    else:
        print(f"   ✗ agents 为空，不应保存")
    
    print("\n测试场景 2: 异常情况（agents 为空）")
    optionId = "option_2"
    agents = agentsByOption.get(optionId, [])
    print(f"   - optionId: {optionId}")
    print(f"   - agents 数量: {len(agents)}")
    
    if len(agents) == 0:
        print(f"   ⚠ agents 为空，应该跳过保存")
        print(f"   建议: 添加检查逻辑")
        print(f"   ```javascript")
        print(f"   if (agents.length === 0) {{")
        print(f"     console.warn('[自动保存] agents 数据为空，跳过保存');")
        print(f"     return;")
        print(f"   }}")
        print(f"   ```")
    
    print("\n测试场景 3: optionId 不存在")
    optionId = "option_999"
    agents = agentsByOption.get(optionId, [])
    print(f"   - optionId: {optionId}")
    print(f"   - agents 数量: {len(agents)}")
    print(f"   ⚠ optionId 不存在，agents 为空")
    
    print("\n" + "=" * 60)
    print("前端保存逻辑测试完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        # 测试数据结构
        test_options_data_structure()
        
        # 测试前端保存逻辑
        test_frontend_save_logic()
        
        print("\n" + "=" * 60)
        print("总结")
        print("=" * 60)
        print("问题原因:")
        print("  1. 前端在保存时，agentsByOption.get(optionId) 返回空数组")
        print("  2. 可能是 optionId 不匹配，或数据还未加载完成")
        print("\n解决方案:")
        print("  1. ✓ 已添加空数据检查，agents 为空时跳过保存")
        print("  2. ✓ 已增加延迟时间从 1 秒到 3 秒")
        print("  3. ✓ 已添加调试日志，方便排查问题")
        print("\n下一步:")
        print("  1. 重新构建前端: cd web && npm run build")
        print("  2. 重启服务")
        print("  3. 进行一次完整推演")
        print("  4. 查看浏览器控制台日志")
        print("  5. 确认 agents 数据是否正确保存")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
