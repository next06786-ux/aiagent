"""
测试Agent工具调用和回复提取
"""
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.llm.llm_service import get_llm_service
from backend.learning.production_rag_system import ProductionRAGSystem
from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
from backend.agents.langchain_specialized_agents import create_langchain_agent
from backend.agents.mcp_integration import MCPHost
from backend.agents.specialized_mcp_servers import (
    WebSearchMCPServer,
    RelationshipMCPServer
)
import asyncio

def test_agent_with_tool_call():
    """测试Agent是否真的调用工具"""
    print("\n" + "="*70)
    print("测试Agent工具调用")
    print("="*70)
    
    user_id = "test_user_001"
    
    # 1. 初始化服务
    print("\n初始化服务...")
    llm_service = get_llm_service()
    if not llm_service or not llm_service.enabled:
        print("❌ LLM服务不可用")
        return
    print(f"✓ LLM 服务已启用: {llm_service.provider}")
    
    # 2. 初始化RAG和检索系统
    print("\n📚 初始化RAG系统...")
    rag_system = ProductionRAGSystem(user_id, use_gpu=False)
    
    print("\n🔍 初始化检索系统...")
    retrieval_system = UnifiedHybridRetrieval(user_id)
    
    # 3. 创建MCP Host并注册工具
    print("\n🔧 创建MCP Host...")
    mcp_host = MCPHost(user_id=user_id)
    mcp_host.register_server(WebSearchMCPServer())
    mcp_host.register_server(RelationshipMCPServer())
    print("✅ 已注册联网搜索和关系分析工具")
    
    # 4. 创建Agent
    print("\n🤖 创建RelationshipAgent...")
    agent = create_langchain_agent(
        agent_type='relationship',
        user_id=user_id,
        llm_service=llm_service,
        rag_system=rag_system,
        retrieval_system=retrieval_system,
        use_workflow=True,
        mcp_host=mcp_host
    )
    
    # 5. 异步初始化Agent
    print("\n⚙️  初始化Agent...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(agent.initialize())
    loop.close()
    
    print(f"✅ [Agent] 初始化完成")
    print(f"   工具总数: {len(agent.tool_module.tools)}")
    print(f"   Workflow模式: {'启用' if agent.use_workflow else '禁用'}")
    
    # 6. 测试需要工具调用的查询
    print("\n" + "="*70)
    print("测试: 需要联网搜索的查询")
    print("="*70)
    
    test_query = "清华大学在哪个城市？"
    print(f"\n用户问题: {test_query}")
    print("\n" + "-"*70)
    
    result = agent.process(test_query)
    
    print("\n" + "-"*70)
    print("\n📊 返回结果:")
    print(f"   回复类型: {type(result.get('response'))}")
    print(f"   回复内容: {result.get('response')}")
    print(f"   模式: {result.get('mode')}")
    print(f"   Agent使用: {result.get('agent_used')}")
    print(f"   工具调用数: {len(result.get('tool_calls', []))}")
    
    if result.get('tool_calls'):
        print("\n🔧 工具调用详情:")
        for i, tool_call in enumerate(result['tool_calls'], 1):
            print(f"   {i}. {tool_call['tool_name']} ({tool_call['server_name']})")
            print(f"      状态: {tool_call['status']}")
            if tool_call.get('result'):
                print(f"      结果: {tool_call['result'][:100]}...")
    
    # 7. 测试不需要工具的查询
    print("\n" + "="*70)
    print("测试: 不需要工具的简单查询")
    print("="*70)
    
    test_query2 = "你好"
    print(f"\n用户问题: {test_query2}")
    print("\n" + "-"*70)
    
    result2 = agent.process(test_query2)
    
    print("\n" + "-"*70)
    print("\n📊 返回结果:")
    print(f"   回复类型: {type(result2.get('response'))}")
    print(f"   回复内容: {result2.get('response')[:200]}...")
    print(f"   模式: {result2.get('mode')}")
    print(f"   Agent使用: {result2.get('agent_used')}")
    print(f"   工具调用数: {len(result2.get('tool_calls', []))}")
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)

if __name__ == "__main__":
    test_agent_with_tool_call()
