"""
深化AI处理系统测试脚本
测试6层AI处理流程
"""

import sys
sys.path.insert(0, '/e:/ai')

from backend.llm.deep_ai_processor import get_deep_ai_processor
from backend.llm.meta_agent_router import DomainType
from datetime import datetime


def test_deep_ai_processor():
    """测试深化AI处理器"""
    
    print("=" * 80)
    print("LifeSwarm 深化AI处理系统测试")
    print("=" * 80)
    print()
    
    # 创建处理器
    user_id = "test_user_001"
    processor = get_deep_ai_processor(user_id)
    
    # 测试用例
    test_cases = [
        {
            "message": "我最近睡眠不足，应该怎么办？",
            "context": {"recent_focus": DomainType.HEALTH}
        },
        {
            "message": "工作效率下降，感到压力很大",
            "context": {"problem_domain": DomainType.TIME}
        },
        {
            "message": "最近心情不好，感到孤独",
            "context": {"anomaly_domain": DomainType.EMOTION}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试用例 {i}")
        print(f"{'='*80}")
        print(f"用户消息: {test_case['message']}")
        print()
        
        # 执行处理
        result = processor.process(test_case['message'], test_case['context'])
        
        # 打印结果
        print_processing_result(result)
        print()


def print_processing_result(result):
    """打印处理结果"""
    
    print("【第1层：元智能体路由】")
    print("-" * 80)
    layer1 = result["layers"]["meta_agent"]
    print(f"主要领域: {', '.join(layer1['primary_domains'])}")
    print(f"领域分数:")
    for domain, score in layer1['domain_scores'].items():
        print(f"  - {domain}: {score:.2%}")
    print()
    
    print("【第2层：历史记忆检索】")
    print("-" * 80)
    layer2 = result["layers"]["memory"]
    print(f"相似记忆数: {len(layer2['similar_memories'])}")
    print(f"对话历史数: {len(layer2['conversation_history'])}")
    print(f"决策历史数: {len(layer2['decision_history'])}")
    print(f"重要记忆数: {len(layer2['important_memories'])}")
    print(f"总记忆数: {layer2['memory_statistics']['total_memories']}")
    print()
    
    print("【第3层：6领域分析】")
    print("-" * 80)
    layer3 = result["layers"]["domain_analysis"]
    print(f"分析领域数: {len(layer3['domain_analyses'])}")
    print(f"主要关注: {layer3['primary_focus']}")
    for domain, analysis in layer3['domain_analyses'].items():
        print(f"\n{analysis['domain_name']}:")
        print(f"  关键指标: {', '.join(analysis['key_metrics'][:2])}")
        print(f"  洞察:")
        for insight in analysis['insights'][:2]:
            print(f"    - {insight}")
        print(f"  建议:")
        for rec in analysis['recommendations'][:2]:
            print(f"    - {rec}")
    print()
    
    print("【第4层：知识图谱推理】")
    print("-" * 80)
    layer4 = result["layers"]["knowledge_graph"]
    print(f"因果链数: {len(layer4['causal_chains'])}")
    for chain in layer4['causal_chains'][:2]:
        print(f"  - {chain}")
    print(f"推理路径数: {len(layer4['reasoning_paths'])}")
    for path in layer4['reasoning_paths'][:1]:
        print(f"  - {path['path']} (置信度: {path['confidence']:.1%})")
    print()
    
    print("【第5层：混合智能选择】")
    print("-" * 80)
    layer5 = result["layers"]["hybrid_intelligence"]
    print(f"选择策略: {layer5['selected_strategy']}")
    print(f"策略理由: {layer5['strategy_rationale']}")
    print(f"LLM权重: {layer5['llm_weight']:.1%}")
    print(f"个人模型权重: {layer5['personal_model_weight']:.1%}")
    print()
    
    print("【第6层：回复生成】")
    print("-" * 80)
    layer6 = result["layers"]["response_generation"]
    print(f"置信度: {layer6['confidence']:.1%}")
    print(f"\n生成的回复:")
    print("-" * 80)
    print(layer6['response'])
    print("-" * 80)
    print()
    
    print("【思考过程】")
    print("-" * 80)
    print(result['thinking_process'])
    print()


def test_memory_retriever():
    """测试记忆检索器"""
    
    print("\n" + "=" * 80)
    print("记忆检索器测试")
    print("=" * 80)
    print()
    
    from backend.llm.enhanced_memory_retriever import get_enhanced_memory_retriever, MemoryType
    
    user_id = "test_user_002"
    retriever = get_enhanced_memory_retriever(user_id)
    
    # 添加一些测试记忆
    print("添加测试记忆...")
    retriever.add_memory(
        MemoryType.CONVERSATION,
        "我最近睡眠不足，感到很疲劳",
        {"domain": "health"},
        importance=0.8
    )
    retriever.add_memory(
        MemoryType.CONVERSATION,
        "工作压力很大，效率下降",
        {"domain": "time"},
        importance=0.7
    )
    retriever.add_memory(
        MemoryType.DECISION,
        "决定每天早起运动30分钟",
        {"domain": "health", "action": "exercise"},
        importance=0.9
    )
    
    print(f"已添加3条记忆\n")
    
    # 测试相似度检索
    print("测试相似度检索...")
    query = "睡眠和疲劳"
    similar = retriever.retrieve_by_similarity(query, top_k=2)
    print(f"查询: '{query}'")
    print(f"找到{len(similar)}条相似记忆:")
    for memory, score in similar:
        print(f"  - {memory.content} (相似度: {score:.2%})")
    print()
    
    # 测试类型检索
    print("测试类型检索...")
    conversations = retriever.retrieve_by_type(MemoryType.CONVERSATION, top_k=2)
    print(f"对话记忆数: {len(conversations)}")
    for memory in conversations:
        print(f"  - {memory.content}")
    print()
    
    # 测试重要记忆检索
    print("测试重要记忆检索...")
    important = retriever.retrieve_important_memories(top_k=2)
    print(f"重要记忆数: {len(important)}")
    for memory in important:
        print(f"  - {memory.content} (重要性: {memory.importance:.1%})")
    print()
    
    # 打印统计信息
    print("记忆统计信息:")
    stats = retriever.get_memory_statistics()
    print(f"  总记忆数: {stats['total_memories']}")
    print(f"  平均重要性: {stats['average_importance']:.2%}")
    print(f"  总访问次数: {stats['total_access_count']}")
    print()


def test_meta_agent_router():
    """测试元智能体路由器"""
    
    print("\n" + "=" * 80)
    print("元智能体路由器测试")
    print("=" * 80)
    print()
    
    from backend.llm.meta_agent_router import get_meta_agent_router
    
    router = get_meta_agent_router()
    
    # 测试用例
    test_messages = [
        "我最近睡眠不足，应该怎么办？",
        "工作效率下降，感到压力很大",
        "最近心情不好，感到孤独",
        "想要改善财务状况，应该如何理财？",
        "学习效率不高，如何提高？"
    ]
    
    for message in test_messages:
        print(f"消息: {message}")
        primary_domains, domain_scores = router.route(message)
        print(f"主要领域: {[d.value for d in primary_domains]}")
        print(f"领域分数:")
        for domain, score in sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"  - {domain.value}: {score:.2%}")
        print()


if __name__ == "__main__":
    try:
        # 运行测试
        test_meta_agent_router()
        test_memory_retriever()
        test_deep_ai_processor()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

