"""
测试基于配置的MCP Agent架构
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.langchain_specialized_agents import create_langchain_agent, load_agent_config
from agents.mcp_integration import MCPHost


async def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试1: 配置加载")
    print("=" * 60)
    
    config = load_agent_config()
    
    print(f"\n可用的Agent类型: {list(config['agents'].keys())}")
    print(f"可用的MCP服务器: {list(config['mcp_servers'].keys())}")
    
    # 显示每个Agent的配置
    for agent_type, agent_config in config['agents'].items():
        print(f"\n{agent_type}:")
        print(f"  名称: {agent_config['name']}")
        print(f"  MCP服务器: {agent_config['mcp_servers']}")
    
    print("\n✅ 配置加载成功")


async def test_mcp_server_creation():
    """测试MCP服务器创建"""
    print("\n" + "=" * 60)
    print("测试2: MCP服务器动态创建")
    print("=" * 60)
    
    from agents.langchain_specialized_agents import create_mcp_server
    
    config = load_agent_config()
    mcp_servers_config = config['mcp_servers']
    
    # 测试创建每个MCP服务器
    for server_id, server_config in mcp_servers_config.items():
        try:
            print(f"\n创建 {server_id}...")
            server = create_mcp_server(server_config, dict(os.environ))
            print(f"  ✓ 类型: {type(server).__name__}")
            print(f"  ✓ Server ID: {server.server_id}")
            
            # 列出工具
            tools = await server.list_tools()
            print(f"  ✓ 工具数量: {len(tools)}")
            for tool in tools:
                print(f"    - {tool.name}: {tool.description[:50]}...")
        
        except Exception as e:
            print(f"  ✗ 创建失败: {e}")
    
    print("\n✅ MCP服务器创建测试完成")


async def test_agent_creation():
    """测试Agent创建（配置驱动）"""
    print("\n" + "=" * 60)
    print("测试3: 配置驱动的Agent创建")
    print("=" * 60)
    
    # 创建一个简单的LLM服务mock
    class MockLLMService:
        def __init__(self):
            self.model_name = "qwen-plus"
    
    llm_service = MockLLMService()
    
    # 测试创建每种类型的Agent
    for agent_type in ['relationship', 'education', 'career']:
        print(f"\n创建 {agent_type} Agent...")
        
        try:
            agent = create_langchain_agent(
                agent_type=agent_type,
                user_id="test_user",
                llm_service=llm_service,
                rag_system=None,
                retrieval_system=None,
                use_workflow=False  # 纯Agent模式测试
            )
            
            print(f"  ✓ Agent类型: {type(agent).__name__}")
            print(f"  ✓ 配置名称: {agent.config.get('name')}")
            
            # 初始化Agent（发现MCP工具）
            await agent.initialize()
            
            # 显示可用工具
            tools = agent.mcp_host.get_available_tools() if agent.mcp_host else []
            print(f"  ✓ 可用工具数量: {len(tools)}")
            for tool in tools[:5]:  # 只显示前5个
                print(f"    - {tool.name}")
            if len(tools) > 5:
                print(f"    ... 还有 {len(tools) - 5} 个工具")
        
        except Exception as e:
            import traceback
            print(f"  ✗ 创建失败: {e}")
            traceback.print_exc()
    
    print("\n✅ Agent创建测试完成")


async def test_tool_call():
    """测试工具调用"""
    print("\n" + "=" * 60)
    print("测试4: 工具调用测试")
    print("=" * 60)
    
    class MockLLMService:
        def __init__(self):
            self.model_name = "qwen-plus"
    
    llm_service = MockLLMService()
    
    # 创建relationship agent
    agent = create_langchain_agent(
        agent_type='relationship',
        user_id="test_user",
        llm_service=llm_service,
        rag_system=None,
        retrieval_system=None,
        use_workflow=False
    )
    
    await agent.initialize()
    
    # 测试调用一个工具
    print("\n测试调用 analyze_communication_pattern 工具...")
    
    try:
        result = await agent.mcp_host.call_tool(
            tool_name="analyze_communication_pattern",
            parameters={
                "relationship_description": "我和朋友小明",
                "recent_interactions": "最近3个月他总是找借口推脱见面"
            }
        )
        
        print(f"  ✓ 调用成功")
        print(f"  结果: {result}")
    
    except Exception as e:
        print(f"  ✗ 调用失败: {e}")
    
    print("\n✅ 工具调用测试完成")


async def main():
    """运行所有测试"""
    print("\n🚀 开始测试基于配置的MCP Agent架构\n")
    
    await test_config_loading()
    await test_mcp_server_creation()
    await test_agent_creation()
    await test_tool_call()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
