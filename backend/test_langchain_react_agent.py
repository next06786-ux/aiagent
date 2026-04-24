"""
测试LangChain ReAct Agent
Test LangChain ReAct Agent
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.llm.llm_service import get_llm_service
from backend.learning.production_rag_system import ProductionRAGSystem
from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
from backend.agents.langchain_specialized_agents import create_langchain_agent

async def test_langchain_react_agent():
    """测试LangChain ReAct Agent"""
    print("="*70)
    print("测试LangChain ReAct Agent")
    print("="*70)
    
    # 1. 初始化服务
    print("\n初始化服务...")
    user_id = "test_user_001"
    
    llm_service = get_llm_service()
    if not llm_service or not llm_service.enabled:
        print("❌ LLM服务不可用")
        return
    
    print("✅ LLM服务已启动")
    
    # 2. 初始化RAG系统（使用CPU模式）
    print("\n📚 初始化RAG系统...")
    rag_system = ProductionRAGSystem(user_id, use_gpu=False)
    print("✅ RAG系统已初始化")
    
    # 3. 初始化检索系统
    print("\n🔍 初始化检索系统...")
    retrieval_system = UnifiedHybridRetrieval(user_id)
    print("✅ 检索系统已初始化")
    
    # 4. 创建Agent（不使用MCP，先测试基础功能）
    print("\n🤖 创建RelationshipAgent...")
    agent = create_langchain_agent(
        agent_type='relationship',
        user_id=user_id,
        llm_service=llm_service,
        rag_system=rag_system,
        retrieval_system=retrieval_system,
        use_workflow=True,
        mcp_host=None  # 先不使用MCP
    )
    
    # 5. 初始化Agent
    print("\n⚙️  初始化Agent...")
    await agent.initialize()
    
    # 6. 测试简单对话
    print("\n" + "="*70)
    print("测试1: 简单问候")
    print("="*70)
    
    result = agent.process("你好")
    print(f"\n✅ 回复: {result['response']}")
    print(f"   模式: {result['mode']}")
    print(f"   Agent使用: {result['agent_used']}")
    
    # 7. 测试需要工具的查询
    print("\n" + "="*70)
    print("测试2: 需要工具的查询")
    print("="*70)
    
    result = agent.process("帮我分析一下我和同事的沟通模式")
    print(f"\n✅ 回复: {result['response']}")
    print(f"   模式: {result['mode']}")
    print(f"   Agent使用: {result['agent_used']}")
    
    # 8. 检查工具调用
    if result.get('tool_calls'):
        print(f"\n🔧 工具调用:")
        for tool_call in result['tool_calls']:
            print(f"   - {tool_call['tool_name']} ({tool_call['status']})")
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_langchain_react_agent())
