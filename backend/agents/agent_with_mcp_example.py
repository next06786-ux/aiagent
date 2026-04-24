"""
Agent + MCP 完整集成示例
Complete Integration Example: Agent with MCP
"""

import asyncio
from backend.agents.mcp_integration import MCPHost, GithubMCPServer, DatabaseMCPServer
from backend.agents.langchain_specialized_agents import create_langchain_agent


async def example_agent_with_mcp():
    """
    示例：Agent使用MCP动态工具
    
    演示完整流程：
    1. 创建MCP Host
    2. 注册MCP Servers
    3. 创建Agent（传入MCP Host）
    4. 初始化Agent（发现MCP工具）
    5. 处理用户请求（自动调用MCP工具）
    """
    print("\n" + "="*60)
    print("Agent + MCP 完整集成示例")
    print("="*60)
    
    # ===== 1. 创建MCP Host =====
    print("\n步骤1: 创建MCP Host")
    mcp_host = MCPHost(user_id="user_123")
    
    # ===== 2. 注册MCP Servers =====
    print("\n步骤2: 注册MCP Servers")
    github_server = GithubMCPServer(api_token="your_token")
    database_server = DatabaseMCPServer()
    
    mcp_host.register_server(github_server)
    mcp_host.register_server(database_server)
    
    # ===== 3. 创建Agent（传入MCP Host）=====
    print("\n步骤3: 创建Agent")
    
    # 模拟LLM服务和其他依赖
    class MockLLMService:
        def chat(self, messages, **kwargs):
            # 简化实现
            return '{"intent": "查询信息", "complexity": "simple"}'
    
    class MockRAGSystem:
        def add_memory(self, *args, **kwargs):
            pass
    
    class MockRetrievalSystem:
        def retrieve(self, *args, **kwargs):
            class Result:
                results = []
            return Result()
    
    agent = create_langchain_agent(
        agent_type='career',
        user_id='user_123',
        llm_service=MockLLMService(),
        rag_system=MockRAGSystem(),
        retrieval_system=MockRetrievalSystem(),
        use_workflow=True,
        mcp_host=mcp_host  # 传入MCP Host
    )
    
    # ===== 4. 初始化Agent（发现MCP工具）=====
    print("\n步骤4: 初始化Agent（发现MCP工具）")
    await agent.initialize()
    
    # ===== 5. 查看可用工具 =====
    print("\n步骤5: 查看所有可用工具")
    tools = agent.tool_module.get_tools()
    print(f"\n可用工具总数: {len(tools)}")
    print("\n工具列表:")
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool.name}")
        print(f"     {tool.description[:80]}...")
    
    # ===== 6. 模拟用户请求 =====
    print("\n" + "="*60)
    print("步骤6: 模拟用户请求")
    print("="*60)
    
    user_requests = [
        "帮我在Github搜索Python相关的仓库",
        "查询我的用户信息",
        "帮我在Github创建一个Issue"
    ]
    
    for request in user_requests:
        print(f"\n用户: {request}")
        print("-" * 60)
        
        # 这里Agent会自动：
        # 1. 判断需要使用哪个工具
        # 2. 通过MCP Client调用工具
        # 3. 获取结果并生成回复
        
        print("Agent: (模拟) 我会使用相应的MCP工具来处理...")
        
        # 实际使用时：
        # result = await agent.process(request)
        # print(f"Agent: {result['response']}")
    
    # ===== 7. 查看审计日志 =====
    print("\n" + "="*60)
    print("步骤7: 查看MCP审计日志")
    print("="*60)
    
    logs = mcp_host.get_audit_logs()
    if logs:
        for log in logs:
            status = "✅" if log.success else "❌"
            approval = "🔒" if log.approved else "🔓"
            print(f"{status} {approval} [{log.timestamp.strftime('%H:%M:%S')}] {log.tool_name}")
            print(f"   Server: {log.server_id}")
            print(f"   参数: {log.parameters}")
            print()
    else:
        print("暂无调用记录")
    
    print("\n" + "="*60)
    print("集成示例完成！")
    print("="*60)


async def example_workflow_routing():
    """
    示例：Workflow智能路由 + MCP工具
    
    演示：
    - 简单任务 → 纯Workflow（不调用MCP工具）
    - 复杂任务 → Workflow + Agent + MCP工具
    """
    print("\n" + "="*60)
    print("Workflow智能路由 + MCP工具")
    print("="*60)
    
    # 创建带MCP的Agent
    mcp_host = MCPHost(user_id="user_123")
    mcp_host.register_server(GithubMCPServer())
    
    # ... (创建Agent的代码同上)
    
    print("\n场景1: 简单问候")
    print("-" * 60)
    print("用户: 你好")
    print("路由: simple → 纯Workflow")
    print("Agent: 你好！我是职业规划Agent，有什么可以帮你的吗？")
    print("MCP工具调用: 0次")
    
    print("\n场景2: 复杂任务")
    print("-" * 60)
    print("用户: 帮我搜索Github上的机器学习项目，并创建一个学习计划")
    print("路由: complex → Workflow + Agent + MCP")
    print("步骤:")
    print("  1. Workflow: MEMORY_LOAD → 加载用户背景")
    print("  2. Workflow: INTENT_CLASSIFY → 判断为complex")
    print("  3. Workflow: AGENT_DECISION → 调用Agent")
    print("  4. Agent: 使用MCP工具 github_search_repos")
    print("  5. Agent: 分析结果并生成学习计划")
    print("  6. Workflow: MEMORY_SAVE → 保存对话")
    print("MCP工具调用: 1次 (github_search_repos)")


async def example_parallel_mcp_calls():
    """
    示例：Agent并行调用多个MCP工具
    
    演示：
    - 一次性调用多个MCP工具
    - 提高响应速度
    """
    print("\n" + "="*60)
    print("并行调用多个MCP工具")
    print("="*60)
    
    mcp_host = MCPHost(user_id="user_123")
    mcp_host.register_server(GithubMCPServer())
    mcp_host.register_server(DatabaseMCPServer())
    
    await mcp_host.discover_tools()
    
    print("\n用户: 同时帮我搜索React和Vue的Github仓库，并查询我的用户信息")
    print("\nAgent判断: 需要并行调用3个工具")
    print("  1. github_search_repos (query=react)")
    print("  2. github_search_repos (query=vue)")
    print("  3. db_query_users (user_id=user_123)")
    
    from backend.agents.mcp_integration import ParallelFunctionCaller
    
    parallel_caller = ParallelFunctionCaller(mcp_host)
    
    tool_calls = [
        {"tool_name": "github_search_repos", "parameters": {"query": "react"}},
        {"tool_name": "github_search_repos", "parameters": {"query": "vue"}},
        {"tool_name": "db_query_users", "parameters": {"user_id": "user_123"}}
    ]
    
    print("\n⚡ 并行执行...")
    results = await parallel_caller.call_parallel(tool_calls)
    
    print("\n结果:")
    for i, result in enumerate(results, 1):
        print(f"  工具{i}: {result}")


async def main():
    """运行所有示例"""
    await example_agent_with_mcp()
    await example_workflow_routing()
    await example_parallel_mcp_calls()


if __name__ == "__main__":
    asyncio.run(main())
