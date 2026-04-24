"""
测试Agent API - 验证新架构是否正常工作
"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

import asyncio
from backend.llm.llm_service import get_llm_service
from backend.learning.production_rag_system import ProductionRAGSystem
from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
from backend.agents.langchain_specialized_agents import create_langchain_agent


async def test_three_agents():
    """测试三个Agent是否都能正常工作"""
    print("\n" + "="*70)
    print("测试智慧洞察三个Agent - 新架构")
    print("="*70 + "\n")
    
    # 初始化服务
    print("[1/4] 初始化服务...")
    llm_service = get_llm_service()
    test_user_id = "test_api_user"
    rag_system = ProductionRAGSystem(test_user_id, use_gpu=False)
    retrieval_system = UnifiedHybridRetrieval(test_user_id)
    print("[PASS]\n")
    
    # 测试消息
    test_cases = {
        'relationship': "我和朋友最近关系有点紧张，怎么办？",
        'education': "我应该考研还是直接工作？",
        'career': "如何提升我的职业竞争力？"
    }
    
    results = {}
    
    for agent_type, message in test_cases.items():
        print(f"[{agent_type.upper()}] 测试 {agent_type} Agent")
        print(f"消息: {message}")
        
        try:
            # 创建Agent
            agent = create_langchain_agent(
                agent_type=agent_type,
                user_id=test_user_id,
                llm_service=llm_service,
                rag_system=rag_system,
                retrieval_system=retrieval_system,
                use_workflow=True
            )
            
            # 初始化
            await agent.initialize()
            
            # 处理消息
            result = agent.process(message)
            
            print(f"\n结果:")
            print(f"  模式: {result['mode']}")
            print(f"  使用Agent: {result['agent_used']}")
            print(f"  复杂度: {result['retrieval_stats'].get('complexity')}")
            print(f"  回复: {result['response'][:200]}...")
            print(f"\n[PASS] {agent_type} Agent 测试通过\n")
            
            results[agent_type] = True
            
        except Exception as e:
            print(f"[FAIL] {agent_type} Agent 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results[agent_type] = False
        
        print("-" * 70 + "\n")
    
    # 汇总结果
    print("="*70)
    print("测试结果汇总")
    print("="*70)
    
    for agent_type, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} - {agent_type} Agent")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n总计: {passed}/{total} 通过")
    print(f"成功率: {passed/total*100:.1f}%")
    print("="*70 + "\n")
    
    if passed == total:
        print("[SUCCESS] 所有Agent都已接入新架构并正常工作！")
    else:
        print("[WARNING] 部分Agent测试失败")


if __name__ == "__main__":
    asyncio.run(test_three_agents())
