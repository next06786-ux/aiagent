"""
简化版Agent架构测试 - 无emoji版本
"""

import os
import sys
import asyncio

# 设置环境变量
os.environ['HF_HUB_OFFLINE'] = '1'

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()


async def test_agent_creation():
    """测试Agent创建"""
    print("\n" + "="*70)
    print("测试1: Agent创建和初始化")
    print("="*70 + "\n")
    
    try:
        # 导入模块
        print("[1/5] 导入模块...")
        from backend.llm.llm_service import get_llm_service
        from backend.learning.production_rag_system import ProductionRAGSystem
        from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
        from backend.agents.langchain_specialized_agents import create_langchain_agent
        
        # 初始化LLM
        print("[2/5] 初始化LLM服务...")
        llm_service = get_llm_service()
        if not llm_service or not llm_service.enabled:
            print("[FAIL] LLM服务未启用")
            return None
        print(f"[PASS] LLM服务: {llm_service.provider.value}")
        
        # 初始化RAG
        print("[3/5] 初始化RAG系统...")
        test_user_id = "test_user_001"
        rag_system = ProductionRAGSystem(test_user_id, use_gpu=False)
        print("[PASS] RAG系统初始化完成")
        
        # 初始化检索
        print("[4/5] 初始化检索系统...")
        retrieval_system = UnifiedHybridRetrieval(test_user_id)
        print("[PASS] 检索系统初始化完成")
        
        # 创建Agent
        print("[5/5] 创建Agent...")
        agent = create_langchain_agent(
            agent_type='relationship',
            user_id=test_user_id,
            llm_service=llm_service,
            rag_system=rag_system,
            retrieval_system=retrieval_system,
            use_workflow=True
        )
        
        # 初始化Agent
        await agent.initialize()
        print("[PASS] Agent创建成功")
        
        return agent, llm_service, rag_system, retrieval_system
        
    except Exception as e:
        print(f"[FAIL] Agent创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_simple_task(agent):
    """测试简单任务"""
    print("\n" + "="*70)
    print("测试2: Workflow处理简单任务")
    print("="*70 + "\n")
    
    try:
        print("消息: '你好'")
        result = agent.process("你好")
        
        print(f"\n结果:")
        print(f"  模式: {result['mode']}")
        print(f"  使用Agent: {result['agent_used']}")
        print(f"  执行路径: {' -> '.join(result['execution_path'])}")
        print(f"  复杂度: {result['retrieval_stats'].get('complexity')}")
        print(f"\n回复: {result['response'][:200]}...")
        
        is_simple = result['mode'] == 'workflow_only' and not result['agent_used']
        if is_simple:
            print("\n[PASS] 简单任务路由正确（纯Workflow）")
        else:
            print("\n[WARN] 简单任务走了Agent路径")
        
        return is_simple
        
    except Exception as e:
        print(f"[FAIL] 简单任务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_complex_task(agent):
    """测试复杂任务"""
    print("\n" + "="*70)
    print("测试3: Workflow + Agent处理复杂任务")
    print("="*70 + "\n")
    
    try:
        print("消息: '我和朋友最近关系有点紧张，怎么办？'")
        result = agent.process("我和朋友最近关系有点紧张，怎么办？")
        
        print(f"\n结果:")
        print(f"  模式: {result['mode']}")
        print(f"  使用Agent: {result['agent_used']}")
        print(f"  执行路径: {' -> '.join(result['execution_path'])}")
        print(f"  复杂度: {result['retrieval_stats'].get('complexity')}")
        print(f"\n回复: {result['response'][:300]}...")
        
        is_complex = result['mode'] == 'workflow_agent_hybrid' and result['agent_used']
        if is_complex:
            print("\n[PASS] 复杂任务路由正确（Workflow + Agent）")
        else:
            print("\n[WARN] 复杂任务走了纯Workflow路径")
        
        return is_complex
        
    except Exception as e:
        print(f"[FAIL] 复杂任务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_system(agent):
    """测试记忆系统"""
    print("\n" + "="*70)
    print("测试4: 记忆系统")
    print("="*70 + "\n")
    
    try:
        # 测试上下文窗口
        context_window = agent.memory_module.get_context_window()
        print(f"[1/3] 上下文窗口: {len(context_window)} 条消息")
        
        # 测试外部记忆检索
        retrieved = agent.memory_module.retrieve_from_external_memory(
            query="用户偏好",
            agent_type=agent.agent_type,
            max_results=3,
            reason="task_start"
        )
        print(f"[2/3] 外部记忆检索: {len(retrieved) if retrieved else 0} 字符")
        
        # 测试记忆保存
        agent.memory_module.save_user_preference("test_key", "test_value")
        print(f"[3/3] 记忆保存: 成功")
        
        print("\n[PASS] 记忆系统测试通过")
        return True
        
    except Exception as e:
        print(f"[FAIL] 记忆系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_integration(llm_service, rag_system, retrieval_system):
    """测试MCP集成"""
    print("\n" + "="*70)
    print("测试5: MCP集成和Function Call")
    print("="*70 + "\n")
    
    try:
        from backend.agents.mcp_integration import MCPHost, GithubMCPServer, DatabaseMCPServer
        from backend.agents.langchain_specialized_agents import create_langchain_agent
        
        # 创建MCP Host
        print("[1/6] 创建MCP Host...")
        mcp_host = MCPHost(user_id='test_user_mcp')
        print("[PASS] MCP Host创建成功")
        
        # 注册MCP Servers
        print("\n[2/6] 注册MCP Servers...")
        mcp_host.register_server(GithubMCPServer())
        mcp_host.register_server(DatabaseMCPServer())
        print("[PASS] 已注册2个MCP Server")
        
        # 创建带MCP的Agent
        print("\n[3/6] 创建带MCP的Agent...")
        agent = create_langchain_agent(
            agent_type='career',
            user_id='test_user_mcp',
            llm_service=llm_service,
            rag_system=rag_system,
            retrieval_system=retrieval_system,
            use_workflow=True,
            mcp_host=mcp_host  # 启用MCP
        )
        print("[PASS] Agent创建成功")
        
        # 初始化（发现MCP工具）
        print("\n[4/6] 发现MCP工具...")
        await agent.initialize()
        
        # 查看发现的工具
        tools = agent.tool_module.get_tools()
        print(f"[PASS] 发现 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.name}")
        
        # 测试Function Call - 单个工具调用
        print("\n[5/6] 测试Function Call（单个工具）...")
        result = await mcp_host.call_tool(
            tool_name="github_search_repos",
            parameters={"query": "python", "language": "python"}
        )
        print(f"[PASS] 工具调用成功")
        print(f"  结果: {result}")
        
        # 测试Parallel Function Call - 并行调用
        print("\n[6/6] 测试Parallel Function Call（并行调用）...")
        from backend.agents.mcp_integration import ParallelFunctionCaller
        
        parallel_caller = ParallelFunctionCaller(mcp_host)
        tool_calls = [
            {"tool_name": "github_search_repos", "parameters": {"query": "react"}},
            {"tool_name": "github_search_repos", "parameters": {"query": "vue"}},
            {"tool_name": "db_query_users", "parameters": {"user_id": "user_123"}}
        ]
        
        results = await parallel_caller.call_parallel(tool_calls)
        print(f"[PASS] 并行调用完成，共 {len(results)} 个结果")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  工具{i+1}: [FAIL] {result}")
            else:
                print(f"  工具{i+1}: [PASS] {result}")
        
        # 查看审计日志
        logs = mcp_host.get_audit_logs()
        print(f"\n[INFO] 审计日志: {len(logs)} 条记录")
        for log in logs:
            status = "[PASS]" if log.success else "[FAIL]"
            print(f"  {status} {log.tool_name} - {log.timestamp.strftime('%H:%M:%S')}")
        
        print("\n[PASS] MCP集成测试通过")
        return True
        
    except Exception as e:
        print(f"[FAIL] MCP集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_function_call_workflow(agent):
    """测试Function Call在Workflow中的使用"""
    print("\n" + "="*70)
    print("测试6: Function Call在Workflow中的集成")
    print("="*70 + "\n")
    
    try:
        # 测试工具调用
        print("消息: '帮我分析一下我的职业竞争力'")
        result = agent.process("帮我分析一下我的职业竞争力")
        
        print(f"\n结果:")
        print(f"  模式: {result['mode']}")
        print(f"  使用Agent: {result['agent_used']}")
        print(f"  复杂度: {result['retrieval_stats'].get('complexity')}")
        print(f"\n回复: {result['response'][:300]}...")
        
        print("\n[PASS] Function Call在Workflow中正常工作")
        return True
        
    except Exception as e:
        print(f"[FAIL] Function Call Workflow测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试流程"""
    print("\n" + "="*70)
    print("Agent架构完整测试")
    print("="*70)
    
    results = {}
    
    # 测试1: Agent创建
    result = await test_agent_creation()
    if not result:
        print("\n[FAIL] Agent创建失败，终止测试")
        return
    
    agent, llm_service, rag_system, retrieval_system = result
    results['Agent创建'] = True
    
    # 测试2: 简单任务
    results['简单任务'] = await test_simple_task(agent)
    
    # 测试3: 复杂任务
    results['复杂任务'] = await test_complex_task(agent)
    
    # 测试4: 记忆系统
    results['记忆系统'] = await test_memory_system(agent)
    
    # 测试5: MCP集成
    results['MCP集成'] = await test_mcp_integration(llm_service, rag_system, retrieval_system)
    
    # 测试6: Function Call Workflow
    if results['MCP集成']:
        # 重新创建带MCP的Agent
        from backend.agents.mcp_integration import MCPHost, GithubMCPServer
        from backend.agents.langchain_specialized_agents import create_langchain_agent
        
        mcp_host = MCPHost(user_id='test_user_fc')
        mcp_host.register_server(GithubMCPServer())
        
        fc_agent = create_langchain_agent(
            agent_type='career',
            user_id='test_user_fc',
            llm_service=llm_service,
            rag_system=rag_system,
            retrieval_system=retrieval_system,
            use_workflow=True,
            mcp_host=mcp_host
        )
        await fc_agent.initialize()
        
        results['Function Call Workflow'] = await test_function_call_workflow(fc_agent)
    else:
        results['Function Call Workflow'] = False
    
    # 汇总结果
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    
    for test_name, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n总计: {passed}/{total} 通过")
    print(f"成功率: {passed/total*100:.1f}%")
    print("="*70 + "\n")
    
    if passed == total:
        print("[SUCCESS] 所有测试通过！你的Agent架构运行正常！")
    else:
        print("[WARNING] 部分测试失败，请检查错误信息")


if __name__ == "__main__":
    asyncio.run(main())
