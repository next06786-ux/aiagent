"""
测试联网搜索功能
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.specialized_mcp_servers import WebSearchMCPServer
from backend.agents.mcp_integration import MCPHost
from backend.agents.langchain_specialized_agents import create_langchain_agent
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


async def test_basic_search():
    """测试基础搜索"""
    print("\n" + "="*60)
    print("测试1: 基础联网搜索")
    print("="*60)
    
    search_server = WebSearchMCPServer()
    
    # 测试搜索
    result = await search_server.call_tool(
        "web_search",
        {"query": "人工智能最新发展趋势"}
    )
    
    print(f"\n搜索成功: {result.get('success')}")
    print(f"查询词: {result.get('query')}")
    print(f"结果数: {result.get('total_results')}")
    print(f"\n搜索摘要:\n{result.get('summary')}")
    
    if result.get('results'):
        print(f"\n详细结果:")
        for i, r in enumerate(result['results'][:3], 1):
            print(f"\n{i}. {r['title']}")
            print(f"   来源: {r['site'] or '未知'}")
            print(f"   日期: {r['date']}")
            print(f"   链接: {r['url']}")
            print(f"   摘要: {r['snippet'][:150]}...")


async def test_time_search():
    """测试时间范围搜索"""
    print("\n" + "="*60)
    print("测试2: 时间范围搜索")
    print("="*60)
    
    search_server = WebSearchMCPServer()
    
    result = await search_server.call_tool(
        "web_search_with_time",
        {
            "query": "考研政策变化",
            "from_time": "一个月前",
            "to_time": "今天"
        }
    )
    
    print(f"\n搜索成功: {result.get('success')}")
    print(f"查询词: {result.get('query')}")
    print(f"结果数: {result.get('total_results')}")
    print(f"\n搜索摘要:\n{result.get('summary')}")


async def test_site_search():
    """测试指定网站搜索"""
    print("\n" + "="*60)
    print("测试3: 指定网站搜索")
    print("="*60)
    
    search_server = WebSearchMCPServer()
    
    result = await search_server.call_tool(
        "web_search_site",
        {
            "query": "职业规划",
            "site": "zhihu.com"
        }
    )
    
    print(f"\n搜索成功: {result.get('success')}")
    print(f"查询词: {result.get('query')}")
    print(f"结果数: {result.get('total_results')}")
    print(f"\n搜索摘要:\n{result.get('summary')}")


async def test_agent_with_search():
    """测试Agent集成搜索"""
    print("\n" + "="*60)
    print("测试4: Agent集成联网搜索")
    print("="*60)
    
    # 创建MCP Host并注册搜索服务器
    mcp_host = MCPHost(user_id="test_user")
    mcp_host.register_server(WebSearchMCPServer())
    
    # 创建Career Agent（模拟，需要真实的服务）
    print("\n✅ 搜索服务器已注册到MCP Host")
    print("✅ Agent可以通过MCP调用web_search工具")
    print("\n使用示例:")
    print("  用户: '帮我查一下最新的AI行业薪资水平'")
    print("  Agent: 调用 web_search('AI行业薪资 2025')")
    print("  Agent: 基于搜索结果给出分析和建议")
    
    # 列出可用工具
    tools = await mcp_host.list_all_tools()
    print(f"\n可用工具数: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")


async def main():
    """运行所有测试"""
    print("\n🚀 开始测试联网搜索功能")
    
    try:
        await test_basic_search()
        await asyncio.sleep(1)  # 避免请求过快
        
        await test_time_search()
        await asyncio.sleep(1)
        
        await test_site_search()
        await asyncio.sleep(1)
        
        await test_agent_with_search()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
