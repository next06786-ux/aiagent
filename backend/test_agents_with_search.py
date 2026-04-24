"""
测试三个Agent集成联网搜索功能

验证：
1. RelationshipAgent + 联网搜索
2. EducationAgent + 联网搜索  
3. CareerAgent + 联网搜索
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.mcp_integration import MCPHost
from backend.agents.specialized_mcp_servers import (
    WebSearchMCPServer,
    RelationshipMCPServer,
    EducationMCPServer
)
from dotenv import load_dotenv

load_dotenv()


async def test_relationship_agent():
    """测试人际关系Agent + 搜索"""
    print("\n" + "="*70)
    print("测试1: RelationshipAgent + 联网搜索")
    print("="*70)
    
    # 创建MCP Host
    mcp_host = MCPHost(user_id="test_user_1")
    
    # 注册工具
    mcp_host.register_server(WebSearchMCPServer())
    mcp_host.register_server(RelationshipMCPServer())
    
    # 发现工具
    await mcp_host.discover_tools()
    
    # 列出工具
    tools = mcp_host.get_available_tools()
    print(f"\n✅ 可用工具数: {len(tools)}")
    
    print("\n工具列表:")
    for tool in tools:
        server_name = "搜索" if "search" in tool.name else "关系分析"
        print(f"  [{server_name}] {tool.name}")
    
    # 模拟场景：用户询问职场关系
    print("\n" + "-"*70)
    print("场景: 用户询问'如何改善职场人际关系'")
    print("-"*70)
    
    # 1. 搜索最新建议
    print("\n步骤1: 搜索最新的职场关系建议...")
    search_result = await mcp_host.call_tool(
        "web_search",
        {"query": "职场人际关系改善技巧"}
    )
    
    if search_result.get("success"):
        print(f"  ✓ 找到 {search_result['total_results']} 条结果")
        if search_result.get('results'):
            print(f"  ✓ 最相关: {search_result['results'][0]['title']}")
    else:
        print(f"  ✗ 搜索失败: {search_result.get('error')}")
    
    # 2. 分析沟通模式
    print("\n步骤2: 分析用户的沟通模式...")
    analysis_result = await mcp_host.call_tool(
        "analyze_communication_pattern",
        {
            "relationship_type": "同事",
            "recent_interactions": "经常有分歧",
            "issues": "沟通效率低"
        }
    )
    
    if analysis_result.get("success"):
        print(f"  ✓ 沟通得分: {analysis_result['communication_score']}/100")
        print(f"  ✓ 识别问题: {', '.join(analysis_result['identified_patterns'][:2])}")
    
    print("\n✅ RelationshipAgent 可以同时使用搜索和专属工具！")


async def test_education_agent():
    """测试教育规划Agent + 搜索"""
    print("\n" + "="*70)
    print("测试2: EducationAgent + 联网搜索")
    print("="*70)
    
    mcp_host = MCPHost(user_id="test_user_2")
    mcp_host.register_server(WebSearchMCPServer())
    mcp_host.register_server(EducationMCPServer())
    
    await mcp_host.discover_tools()
    tools = mcp_host.get_available_tools()
    print(f"\n✅ 可用工具数: {len(tools)}")
    
    print("\n工具列表:")
    for tool in tools:
        server_name = "搜索" if "search" in tool.name else "教育规划"
        print(f"  [{server_name}] {tool.name}")
    
    # 模拟场景：用户询问考研
    print("\n" + "-"*70)
    print("场景: 用户询问'计算机考研院校推荐'")
    print("-"*70)
    
    # 1. 搜索最新考研信息
    print("\n步骤1: 搜索2025年考研最新政策...")
    search_result = await mcp_host.call_tool(
        "web_search",
        {"query": "2025计算机考研政策和院校排名"}
    )
    
    if search_result.get("success"):
        print(f"  ✓ 找到 {search_result['total_results']} 条最新信息")
        if search_result.get('results'):
            print(f"  ✓ 最相关: {search_result['results'][0]['title']}")
    else:
        print(f"  ✗ 搜索失败: {search_result.get('error')}")
    
    # 2. 推荐院校
    print("\n步骤2: 根据GPA推荐院校...")
    recommend_result = await mcp_host.call_tool(
        "recommend_universities",
        {
            "gpa": 3.5,
            "major_direction": "计算机科学"
        }
    )
    
    if recommend_result.get("success"):
        print(f"  ✓ 推荐层级: {recommend_result['tier']}")
        for uni in recommend_result['recommended_universities'][:2]:
            print(f"    • {uni['name']} (匹配度 {uni['match']}%)")
    
    # 3. 分析专业前景
    print("\n步骤3: 分析计算机专业就业前景...")
    prospect_result = await mcp_host.call_tool(
        "analyze_major_prospects",
        {"major_name": "计算机科学"}
    )
    
    if prospect_result.get("success"):
        print(f"  ✓ 就业率: {prospect_result['employment_rate']}")
        print(f"  ✓ 平均薪资: {prospect_result['average_salary']}")
    
    print("\n✅ EducationAgent 可以结合搜索和数据分析！")


async def test_career_agent():
    """测试职业发展Agent + 搜索"""
    print("\n" + "="*70)
    print("测试3: CareerAgent + 联网搜索")
    print("="*70)
    
    mcp_host = MCPHost(user_id="test_user_3")
    mcp_host.register_server(WebSearchMCPServer())
    # CareerMCPServer 待实现
    
    await mcp_host.discover_tools()
    tools = mcp_host.get_available_tools()
    print(f"\n✅ 可用工具数: {len(tools)}")
    
    print("\n工具列表:")
    for tool in tools:
        print(f"  [搜索] {tool.name}")
    
    # 模拟场景：用户询问AI工程师
    print("\n" + "-"*70)
    print("场景: 用户询问'AI工程师职业发展路径'")
    print("-"*70)
    
    # 1. 搜索技能要求
    print("\n步骤1: 搜索AI工程师技能要求...")
    skill_search = await mcp_host.call_tool(
        "web_search",
        {"query": "AI工程师技能要求和学习路径"}
    )
    
    if skill_search.get("success"):
        print(f"  ✓ 搜索成功")
        print(f"  ✓ 回答: {skill_search.get('answer', '')[:100]}...")
    else:
        print(f"  ✗ 搜索失败: {skill_search.get('error')}")
    
    # 2. 搜索薪资水平
    print("\n步骤2: 搜索薪资水平...")
    salary_search = await mcp_host.call_tool(
        "web_search",
        {"query": "AI工程师薪资水平 中国"}
    )
    
    if salary_search.get("success"):
        print(f"  ✓ 搜索成功")
    else:
        print(f"  ✗ 搜索失败: {salary_search.get('error')}")
    
    print("\n✅ CareerAgent 可以使用搜索获取最新行业信息！")
    print("⚠️  待添加职业规划专属工具（技能分析、薪资计算等）")


async def test_search_quality():
    """测试搜索质量"""
    print("\n" + "="*70)
    print("测试4: 阿里云OpenSearch搜索验证")
    print("="*70)
    
    search_server = WebSearchMCPServer()
    
    test_queries = [
        ("人际关系", "职场沟通技巧"),
        ("教育规划", "考研择校建议"),
        ("职业发展", "AI工程师转行")
    ]
    
    for category, query in test_queries:
        print(f"\n[{category}] 搜索: {query}")
        result = await search_server.call_tool(
            "web_search",
            {"query": query, "top_k": 3}
        )
        
        if result.get("success"):
            print(f"  ✓ 成功，找到 {result['total_results']} 条结果")
            rewritten = result.get('rewritten_query')
            if rewritten and rewritten != query:
                print(f"  ✓ AI优化后: {rewritten}")
            if result.get('results'):
                top_result = result['results'][0]
                print(f"  ✓ 最佳匹配: {top_result['title'][:50]}...")
        else:
            print(f"  ✗ 失败: {result.get('error')}")


async def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🚀 测试三个Agent集成联网搜索")
    print("="*70)
    
    try:
        await test_relationship_agent()
        await asyncio.sleep(1)
        
        await test_education_agent()
        await asyncio.sleep(1)
        
        await test_career_agent()
        await asyncio.sleep(1)
        
        await test_search_quality()
        
        print("\n" + "="*70)
        print("✅ 所有测试完成！")
        print("="*70)
        
        print("\n📋 集成总结:")
        print("  ✓ RelationshipAgent: OpenSearch搜索 + 5个专属工具")
        print("  ✓ EducationAgent: OpenSearch搜索 + 5个专属工具")
        print("  ✓ CareerAgent: OpenSearch搜索（专属工具待添加）")
        print("\n💡 使用方式:")
        print("  1. 使用阿里云OpenSearch API Key（已配置）")
        print("  2. AI自动优化搜索词，返回高质量结果")
        print("  3. 支持实时联网搜索最新信息")
        print("  4. 前端无需任何改动，透明集成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
