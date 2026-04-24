"""
三个Agent集成联网搜索的完整示例

展示如何为RelationshipAgent、EducationAgent、CareerAgent添加联网搜索能力
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
from backend.agents.langchain_specialized_agents import create_langchain_agent
from dotenv import load_dotenv

load_dotenv()


async def demo_relationship_agent_with_search():
    """
    示例1: 人际关系Agent + 联网搜索
    
    场景：用户询问"如何改善职场人际关系"
    Agent可以：
    1. 搜索最新的职场关系建议
    2. 使用专属工具分析用户情况
    3. 结合搜索结果和分析给出建议
    """
    print("\n" + "="*60)
    print("示例1: 人际关系Agent + 联网搜索")
    print("="*60)
    
    # 创建MCP Host
    mcp_host = MCPHost(user_id="user_001")
    
    # 注册搜索服务器和专属工具
    mcp_host.register_server(WebSearchMCPServer())
    mcp_host.register_server(RelationshipMCPServer())
    
    # 列出所有可用工具
    tools = await mcp_host.list_all_tools()
    print(f"\n✅ RelationshipAgent 可用工具数: {len(tools)}")
    print("\n工具列表:")
    for tool in tools:
        print(f"  • {tool.name}")
        print(f"    {tool.description[:60]}...")
    
    # 模拟Agent工作流程
    print("\n" + "-"*60)
    print("模拟对话:")
    print("-"*60)
    print("\n用户: 我在职场上总是和同事产生矛盾，怎么办？")
    print("\nAgent思考过程:")
    print("  1. 先搜索最新的职场关系建议")
    
    # 调用搜索
    search_result = await mcp_host.call_tool(
        "web_search_tools",
        "web_search",
        {"query": "职场人际关系改善技巧 2025"}
    )
    
    if search_result.get("success"):
        print(f"     ✓ 找到 {search_result['total_results']} 条相关信息")
        print(f"     摘要: {search_result['summary'][:100]}...")
    
    print("\n  2. 分析用户的沟通模式")
    
    # 调用专属工具
    analysis_result = await mcp_host.call_tool(
        "relationship_tools",
        "analyze_communication_pattern",
        {
            "relationship_type": "同事",
            "recent_interactions": "经常产生矛盾",
            "issues": "沟通不畅"
        }
    )
    
    if analysis_result.get("success"):
        print(f"     ✓ 识别到的沟通模式: {', '.join(analysis_result['identified_patterns'])}")
        print(f"     沟通得分: {analysis_result['communication_score']}/100")
    
    print("\n  3. 综合搜索结果和分析，生成个性化建议")
    print("\nAgent回复:")
    print("  根据最新的职场关系研究和你的情况分析，我建议：")
    print("  1. 改善沟通方式：使用'我感受到...'的表达")
    print("  2. 主动倾听：给同事充分表达的机会")
    print("  3. 建立信任：通过小事积累信任账户")


async def demo_education_agent_with_search():
    """
    示例2: 教育规划Agent + 联网搜索
    
    场景：用户询问"计算机专业考研院校推荐"
    Agent可以：
    1. 搜索最新的院校排名和录取信息
    2. 使用专属工具计算录取概率
    3. 给出数据驱动的建议
    """
    print("\n" + "="*60)
    print("示例2: 教育规划Agent + 联网搜索")
    print("="*60)
    
    mcp_host = MCPHost(user_id="user_002")
    mcp_host.register_server(WebSearchMCPServer())
    mcp_host.register_server(EducationMCPServer())
    
    tools = await mcp_host.list_all_tools()
    print(f"\n✅ EducationAgent 可用工具数: {len(tools)}")
    
    print("\n" + "-"*60)
    print("模拟对话:")
    print("-"*60)
    print("\n用户: 我想考计算机专业的研究生，GPA 3.5，有什么推荐？")
    print("\nAgent思考过程:")
    print("  1. 搜索2025年计算机考研最新政策和院校信息")
    
    search_result = await mcp_host.call_tool(
        "web_search_tools",
        "web_search",
        {"query": "2025计算机考研院校排名 录取分数"}
    )
    
    if search_result.get("success"):
        print(f"     ✓ 找到 {search_result['total_results']} 条最新信息")
    
    print("\n  2. 根据GPA推荐合适的院校")
    
    recommend_result = await mcp_host.call_tool(
        "education_tools",
        "recommend_universities",
        {
            "gpa": 3.5,
            "major_direction": "计算机科学",
            "region_preference": "不限"
        }
    )
    
    if recommend_result.get("success"):
        print(f"     ✓ 推荐院校层级: {recommend_result['tier']}")
        print(f"     推荐院校:")
        for uni in recommend_result['recommended_universities'][:3]:
            print(f"       • {uni['name']} (匹配度: {uni['match']}%)")
    
    print("\n  3. 分析计算机专业就业前景")
    
    prospect_result = await mcp_host.call_tool(
        "education_tools",
        "analyze_major_prospects",
        {"major_name": "计算机科学"}
    )
    
    if prospect_result.get("success"):
        print(f"     ✓ 就业率: {prospect_result['employment_rate']}")
        print(f"     平均薪资: {prospect_result['average_salary']}")
    
    print("\nAgent回复:")
    print("  基于最新数据和你的GPA，我推荐以下策略：")
    print("  • 冲刺院校：浙江大学、上海交通大学")
    print("  • 目标院校：南京大学、武汉大学、华中科技大学")
    print("  • 保底院校：苏州大学、南京师范大学")


async def demo_career_agent_with_search():
    """
    示例3: 职业发展Agent + 联网搜索
    
    场景：用户询问"AI工程师的职业发展路径"
    Agent可以：
    1. 搜索最新的AI行业趋势和薪资
    2. 分析技能要求
    3. 给出职业规划建议
    """
    print("\n" + "="*60)
    print("示例3: 职业发展Agent + 联网搜索")
    print("="*60)
    
    mcp_host = MCPHost(user_id="user_003")
    mcp_host.register_server(WebSearchMCPServer())
    # CareerMCPServer 待实现
    
    tools = await mcp_host.list_all_tools()
    print(f"\n✅ CareerAgent 可用工具数: {len(tools)}")
    
    print("\n" + "-"*60)
    print("模拟对话:")
    print("-"*60)
    print("\n用户: 我想转行做AI工程师，需要准备什么？")
    print("\nAgent思考过程:")
    print("  1. 搜索AI工程师的最新技能要求和薪资")
    
    # 搜索技能要求
    skill_search = await mcp_host.call_tool(
        "web_search_tools",
        "web_search",
        {"query": "AI工程师技能要求 2025"}
    )
    
    if skill_search.get("success"):
        print(f"     ✓ 找到 {skill_search['total_results']} 条技能信息")
    
    # 搜索薪资水平
    salary_search = await mcp_host.call_tool(
        "web_search_tools",
        "web_search",
        {"query": "AI工程师薪资水平 2025 中国"}
    )
    
    if salary_search.get("success"):
        print(f"     ✓ 找到 {salary_search['total_results']} 条薪资数据")
    
    print("\n  2. 分析行业趋势")
    
    trend_search = await mcp_host.call_tool(
        "web_search_tools",
        "web_search_with_time",
        {
            "query": "AI行业发展趋势",
            "from_time": "三个月前",
            "to_time": "今天"
        }
    )
    
    if trend_search.get("success"):
        print(f"     ✓ 找到 {trend_search['total_results']} 条最新趋势")
    
    print("\nAgent回复:")
    print("  基于最新的行业数据，AI工程师转行路径：")
    print("  ")
    print("  必备技能：")
    print("  • Python编程（PyTorch/TensorFlow）")
    print("  • 机器学习算法基础")
    print("  • 大模型应用开发")
    print("  ")
    print("  薪资范围：15-40万/年（根据经验）")
    print("  ")
    print("  学习路线（6个月）：")
    print("  1-2月：Python + 数学基础")
    print("  3-4月：机器学习 + 深度学习")
    print("  5-6月：大模型 + 项目实战")


async def main():
    """运行所有示例"""
    print("\n🚀 三个Agent集成联网搜索完整示例")
    print("="*60)
    
    try:
        await demo_relationship_agent_with_search()
        await asyncio.sleep(1)
        
        await demo_education_agent_with_search()
        await asyncio.sleep(1)
        
        await demo_career_agent_with_search()
        
        print("\n" + "="*60)
        print("✅ 所有示例运行完成！")
        print("="*60)
        print("\n💡 使用说明:")
        print("  1. 在.env中配置 JUHE_SEARCH_API_KEY")
        print("  2. 在创建Agent时传入配置好的MCP Host")
        print("  3. Agent会自动发现并使用搜索工具")
        print("  4. 搜索结果会融入Agent的推理过程")
        
    except Exception as e:
        print(f"\n❌ 示例运行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
