"""
测试工具回调功能 - 验证 running 和 completed 状态的实时发送
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.llm.llm_service import get_llm_service
from backend.learning.production_rag_system import ProductionRAGSystem
from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
from backend.agents.langchain_specialized_agents import create_langchain_agent
from backend.agents.mcp_integration import MCPHost
from backend.agents.specialized_mcp_servers import WebSearchMCPServer

# 模拟 WebSocket 回调函数
def mock_websocket_callback(event_type: str, data: dict):
    """模拟 WebSocket 回调"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    if event_type == "tool_call":
        status = data.get("status")
        tool_name = data.get("tool_name")
        
        if status == "running":
            print(f"[{timestamp}] 🔧 工具开始: {tool_name}")
            print(f"           输入: {data.get('input', '')[:100]}")
        elif status == "completed":
            duration = data.get("duration", 0)
            print(f"[{timestamp}] ✅ 工具完成: {tool_name} (耗时: {duration:.2f}s)")
            print(f"           输出: {data.get('output', '')[:100]}")
        elif status == "error":
            print(f"[{timestamp}] ❌ 工具错误: {tool_name}")
            print(f"           错误: {data.get('error', '')}")
    
    print()  # 空行分隔


async def test_tool_callback():
    """测试工具回调功能"""
    print("=" * 60)
    print("测试工具回调功能 - 验证 running 和 completed 状态")
    print("=" * 60)
    print()
    
    # 1. 初始化服务
    print("1️⃣ 初始化服务...")
    user_id = "test_user_callback"
    
    llm_service = get_llm_service()
    if not llm_service or not llm_service.enabled:
        print("❌ LLM服务不可用")
        return
    
    rag_system = ProductionRAGSystem(user_id, use_gpu=False)
    retrieval_system = UnifiedHybridRetrieval(user_id)
    print("✅ 服务初始化完成\n")
    
    # 2. 创建 MCP Host 并注册搜索工具
    print("2️⃣ 创建 MCP Host...")
    mcp_host = MCPHost(user_id=user_id)
    mcp_host.register_server(WebSearchMCPServer())
    print("✅ MCP Host 创建完成\n")
    
    # 3. 创建 Agent（传入 WebSocket 回调）
    print("3️⃣ 创建 Agent（启用工具回调）...")
    agent = create_langchain_agent(
        agent_type='relationship',
        user_id=user_id,
        llm_service=llm_service,
        rag_system=rag_system,
        retrieval_system=retrieval_system,
        use_workflow=True,
        mcp_host=mcp_host,
        websocket_callback=mock_websocket_callback  # 传入回调函数
    )
    
    # 初始化 Agent（发现 MCP 工具）
    await agent.initialize()
    print("✅ Agent 创建完成\n")
    
    # 4. 测试需要工具调用的问题
    print("4️⃣ 测试工具调用...")
    print("-" * 60)
    
    test_message = "清华大学在哪个城市？"
    print(f"用户问题: {test_message}\n")
    
    print("【预期行为】")
    print("1. 立即显示 '🔧 工具开始: web_search'")
    print("2. 工具执行中...")
    print("3. 显示 '✅ 工具完成: web_search'\n")
    
    print("【实际输出】")
    print("-" * 60)
    
    # 执行 Agent
    result = agent.process(test_message)
    
    print("-" * 60)
    print()
    
    # 5. 显示结果
    print("5️⃣ Agent 回复:")
    print(result['response'])
    print()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tool_callback())
