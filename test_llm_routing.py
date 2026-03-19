"""
测试LLM智能路由功能
"""

from backend.llm.meta_agent_router import get_meta_agent_router

def test_llm_routing():
    """测试LLM路由"""
    router = get_meta_agent_router()
    
    # 测试用例
    test_cases = [
        "你好吗",
        "我最近睡眠不好，总是失眠",
        "我想学习Python编程",
        "我的工作效率很低，总是拖延",
        "我感觉很焦虑，压力很大",
        "我想存钱买房子",
        "我最近很孤独，没有朋友",
        "今天天气怎么样",
        "帮我分析一下我的健康状况和时间管理"
    ]
    
    print("=" * 80)
    print("测试LLM智能路由功能")
    print("=" * 80)
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n【测试 {i}】")
        print(f"用户问题: {message}")
        print("-" * 80)
        
        try:
            primary_domains, domain_scores = router.route(message)
            
            print(f"\n主要领域: {[d.value for d in primary_domains]}")
            print(f"\n领域评分:")
            for domain, score in sorted(domain_scores.items(), key=lambda x: x[1], reverse=True):
                if score > 0:
                    print(f"  {domain.value:12s}: {score:.2f} {'█' * int(score * 20)}")
            
            print(f"\n路由解释:")
            explanation = router.get_routing_explanation(message, primary_domains, domain_scores)
            print(explanation)
            
        except Exception as e:
            print(f"❌ 路由失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 80)

if __name__ == "__main__":
    test_llm_routing()
