"""
测试MCP工具调用追踪
Test MCP Tool Call Tracking
"""
import asyncio
from backend.agents.mcp_integration import MCPHost
from backend.agents.specialized_mcp_servers import (
    WebSearchMCPServer,
    RelationshipMCPServer,
    EducationMCPServer
)

async def test_tool_tracking():
    """测试工具调用追踪"""
    print("="*70)
    print("🧪 测试MCP工具调用追踪")
    print("="*70)
    
    # 创建MCP Host
    mcp_host = MCPHost(user_id="test_user")
    
    # 注册服务器
    print("\n📡 注册MCP服务器...")
    mcp_host.register_server(WebSearchMCPServer())
    mcp_host.register_server(RelationshipMCPServer())
    mcp_host.register_server(EducationMCPServer())
    
    # 发现工具
    print("\n🔍 发现工具...")
    await mcp_host.discover_tools()
    
    print(f"\n✅ 发现 {len(mcp_host.discovered_tools)} 个工具")
    
    # 测试1: 调用搜索工具
    print("\n" + "="*70)
    print("测试1: 调用联网搜索工具")
    print("="*70)
    
    try:
        result = await mcp_host.call_tool(
            tool_name="web_search",
            parameters={"query": "人工智能发展趋势"}
        )
        print(f"✅ 搜索成功")
        print(f"   结果数: {len(result.get('results', []))}")
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
    
    # 测试2: 调用关系分析工具
    print("\n" + "="*70)
    print("测试2: 调用关系分析工具")
    print("="*70)
    
    try:
        result = await mcp_host.call_tool(
            tool_name="analyze_communication_pattern",
            parameters={
                "relationship_type": "同事",
                "recent_interactions": "经常有分歧",
                "issues": "沟通效率低"
            }
        )
        print(f"✅ 分析成功")
        print(f"   沟通得分: {result.get('communication_score')}/100")
    except Exception as e:
        print(f"❌ 分析失败: {e}")
    
    # 测试3: 调用教育规划工具
    print("\n" + "="*70)
    print("测试3: 调用教育规划工具")
    print("="*70)
    
    try:
        result = await mcp_host.call_tool(
            tool_name="recommend_universities",
            parameters={
                "gpa": 3.5,
                "major_direction": "计算机科学",
                "region_preference": "华东"
            }
        )
        print(f"✅ 推荐成功")
        print(f"   推荐院校数: {len(result.get('recommendations', []))}")
    except Exception as e:
        print(f"❌ 推荐失败: {e}")
    
    # 查看调用日志
    print("\n" + "="*70)
    print("📋 工具调用日志")
    print("="*70)
    
    if hasattr(mcp_host, 'client') and hasattr(mcp_host.client, 'call_logs'):
        for i, log in enumerate(mcp_host.client.call_logs, 1):
            status = "✅ 成功" if log.success else "❌ 失败"
            print(f"\n{i}. {log.tool_name}")
            print(f"   Server: {log.server_id}")
            print(f"   状态: {status}")
            print(f"   时间: {log.timestamp.strftime('%H:%M:%S')}")
            
            # 模拟前端需要的格式
            tool_call_info = {
                'tool_name': log.tool_name,
                'server_name': _get_server_name(mcp_host, log.server_id),
                'status': 'completed' if log.success else 'failed',
                'result': str(log.result)[:100] if log.result else None
            }
            print(f"   前端格式: {tool_call_info}")
    else:
        print("⚠️  没有调用日志")
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)

def _get_server_name(mcp_host, server_id: str) -> str:
    """获取Server名称"""
    for server in mcp_host.servers.values():
        if server.server_id == server_id:
            return server.name
    return server_id

if __name__ == "__main__":
    asyncio.run(test_tool_tracking())
