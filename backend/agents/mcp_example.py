"""
MCP使用示例
Demonstrates MCP Integration Usage
"""

import asyncio
from backend.agents.mcp_integration import (
    MCPHost,
    GithubMCPServer,
    DatabaseMCPServer,
    ParallelFunctionCaller
)


async def example_basic_usage():
    """示例1：基础使用"""
    print("\n" + "="*60)
    print("示例1：MCP基础使用")
    print("="*60)
    
    # 1. 创建MCP Host
    mcp_host = MCPHost(user_id="user_123")
    
    # 2. 注册MCP Servers
    github_server = GithubMCPServer(api_token="your_token")
    database_server = DatabaseMCPServer()
    
    mcp_host.register_server(github_server)
    mcp_host.register_server(database_server)
    
    # 3. 动态发现工具
    await mcp_host.discover_tools()
    
    # 4. 查看可用工具
    tools = mcp_host.get_available_tools()
    print(f"\n可用工具数量: {len(tools)}")
    
    # 5. 调用工具
    print("\n" + "-"*60)
    print("调用工具：github_search_repos")
    print("-"*60)
    
    result = await mcp_host.call_tool(
        tool_name="github_search_repos",
        parameters={"query": "langchain", "language": "python"}
    )
    print(f"结果: {result}")
    
    # 6. 调用需要授权的工具
    print("\n" + "-"*60)
    print("调用工具：github_create_issue（需要授权）")
    print("-"*60)
    
    result = await mcp_host.call_tool(
        tool_name="github_create_issue",
        parameters={
            "repo": "owner/repo",
            "title": "测试Issue",
            "body": "这是一个测试"
        }
    )
    print(f"结果: {result}")
    
    # 7. 查看审计日志
    print("\n" + "-"*60)
    print("审计日志")
    print("-"*60)
    
    logs = mcp_host.get_audit_logs()
    for log in logs:
        status = "✅" if log.success else "❌"
        approval = "🔒" if log.approved else "🔓"
        print(f"{status} {approval} {log.timestamp.strftime('%H:%M:%S')} - {log.tool_name}")


async def example_parallel_calls():
    """示例2：并行函数调用"""
    print("\n" + "="*60)
    print("示例2：并行函数调用")
    print("="*60)
    
    # 1. 创建MCP Host
    mcp_host = MCPHost(user_id="user_123")
    
    # 2. 注册Servers
    github_server = GithubMCPServer()
    database_server = DatabaseMCPServer()
    
    mcp_host.register_server(github_server)
    mcp_host.register_server(database_server)
    
    # 3. 发现工具
    await mcp_host.discover_tools()
    
    # 4. 创建并行调用器
    parallel_caller = ParallelFunctionCaller(mcp_host)
    
    # 5. 并行调用多个工具
    tool_calls = [
        {
            "tool_name": "github_search_repos",
            "parameters": {"query": "react"}
        },
        {
            "tool_name": "db_query_users",
            "parameters": {"user_id": "user_123"}
        },
        {
            "tool_name": "github_search_repos",
            "parameters": {"query": "vue"}
        }
    ]
    
    results = await parallel_caller.call_parallel(tool_calls)
    
    print("\n并行调用结果:")
    for i, result in enumerate(results):
        print(f"  工具{i+1}: {result}")


async def example_agent_integration():
    """示例3：与Agent集成"""
    print("\n" + "="*60)
    print("示例3：Agent使用MCP工具")
    print("="*60)
    
    # 模拟Agent工作流程
    
    # 1. Agent启动时，初始化MCP Host
    mcp_host = MCPHost(user_id="user_123")
    
    # 2. 注册所有MCP Servers
    mcp_host.register_server(GithubMCPServer())
    mcp_host.register_server(DatabaseMCPServer())
    
    # 3. 发现所有工具
    await mcp_host.discover_tools()
    
    # 4. 将工具注入LLM上下文
    tools = mcp_host.get_available_tools()
    tool_descriptions = []
    for tool in tools:
        tool_descriptions.append(f"- {tool.name}: {tool.description}")
    
    print("\n注入LLM的工具列表:")
    for desc in tool_descriptions:
        print(desc)
    
    # 5. 用户输入
    user_input = "帮我在Github创建一个Issue"
    print(f"\n用户输入: {user_input}")
    
    # 6. LLM判断需要调用工具（模拟）
    print("\nLLM判断: 需要调用 github_create_issue 工具")
    
    # 7. Agent通过MCP Host调用工具
    result = await mcp_host.call_tool(
        tool_name="github_create_issue",
        parameters={
            "repo": "myorg/myrepo",
            "title": "新功能请求",
            "body": "希望添加XXX功能"
        }
    )
    
    # 8. 将结果返回给LLM生成最终回答
    print(f"\n工具执行结果: {result}")
    print("\nLLM生成最终回答: 我已经在Github上创建了Issue，链接是...")


async def example_security():
    """示例4：安全机制演示"""
    print("\n" + "="*60)
    print("示例4：三层安全机制")
    print("="*60)
    
    mcp_host = MCPHost(user_id="user_123")
    
    # 注册Server
    github_server = GithubMCPServer()
    mcp_host.register_server(github_server)
    
    # 发现工具
    await mcp_host.discover_tools()
    
    print("\n第一层：能力声明")
    print("-" * 60)
    tools = mcp_host.get_available_tools()
    for tool in tools:
        print(f"✓ {tool.name} - 由 {tool.server_id} 提供")
    
    print("\n第二层：授权控制")
    print("-" * 60)
    
    # 自定义授权回调
    async def custom_approval(tool, parameters):
        print(f"⚠️  敏感操作需要确认:")
        print(f"   工具: {tool.name}")
        print(f"   参数: {parameters}")
        print(f"   是否批准? (模拟用户确认)")
        # 实际应用中，这里会等待用户输入
        return True
    
    mcp_host.set_approval_callback(custom_approval)
    
    # 调用需要授权的工具
    await mcp_host.call_tool(
        tool_name="github_create_issue",
        parameters={"repo": "test/repo", "title": "test"}
    )
    
    print("\n第三层：审计追踪")
    print("-" * 60)
    logs = mcp_host.get_audit_logs()
    for log in logs:
        print(f"[{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}]")
        print(f"  工具: {log.tool_name}")
        print(f"  Server: {log.server_id}")
        print(f"  用户: {log.user_id}")
        print(f"  授权: {'是' if log.approved else '否'}")
        print(f"  成功: {'是' if log.success else '否'}")
        print()


async def main():
    """运行所有示例"""
    await example_basic_usage()
    await example_parallel_calls()
    await example_agent_integration()
    await example_security()


if __name__ == "__main__":
    asyncio.run(main())
