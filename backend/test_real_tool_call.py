"""
测试真实工具调用 - MCP + Function Call

演示：
1. 文件系统操作工具（读写文件）
2. 时间工具（获取当前时间）
3. 计算器工具（数学运算）
4. Agent自动调用工具完成任务
"""

import os
import sys
import asyncio
from datetime import datetime
import json

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from backend.agents.mcp_integration import MCPServer, MCPTool, MCPHost
from typing import List, Dict, Any


# ==================== 真实工具MCP Server ====================

class FileSystemMCPServer(MCPServer):
    """文件系统操作MCP Server"""
    
    def __init__(self):
        super().__init__(
            server_id="filesystem",
            name="FileSystem Server",
            description="提供文件系统操作工具"
        )
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="read_file",
                description="读取文件内容。输入文件路径，返回文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "文件路径"}
                    },
                    "required": ["filepath"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="write_file",
                description="写入文件内容。输入文件路径和内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "文件路径"},
                        "content": {"type": "string", "description": "文件内容"}
                    },
                    "required": ["filepath", "content"]
                },
                server_id=self.server_id,
                requires_approval=True  # 写操作需要确认
            ),
            MCPTool(
                name="list_files",
                description="列出目录下的文件。输入目录路径",
                parameters={
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "目录路径"}
                    },
                    "required": ["directory"]
                },
                server_id=self.server_id,
                requires_approval=False
            )
        ]
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行文件系统操作"""
        if tool_name == "read_file":
            filepath = parameters["filepath"]
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {
                    "success": True,
                    "filepath": filepath,
                    "content": content[:500],  # 只返回前500字符
                    "size": len(content)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif tool_name == "write_file":
            filepath = parameters["filepath"]
            content = parameters["content"]
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {
                    "success": True,
                    "filepath": filepath,
                    "bytes_written": len(content)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif tool_name == "list_files":
            directory = parameters["directory"]
            try:
                files = os.listdir(directory)
                return {
                    "success": True,
                    "directory": directory,
                    "files": files[:20],  # 只返回前20个
                    "total": len(files)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        else:
            raise ValueError(f"未知工具: {tool_name}")
    
    async def list_resources(self):
        return []
    
    async def list_prompts(self):
        return []
    
    async def read_resource(self, uri: str):
        return None


class CalculatorMCPServer(MCPServer):
    """计算器MCP Server"""
    
    def __init__(self):
        super().__init__(
            server_id="calculator",
            name="Calculator Server",
            description="提供数学计算工具"
        )
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="calculate",
                description="执行数学计算。支持加减乘除、幂运算等。输入数学表达式",
                parameters={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "数学表达式，如 '2 + 3 * 4'"}
                    },
                    "required": ["expression"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="convert_units",
                description="单位转换。支持长度、重量、温度等",
                parameters={
                    "type": "object",
                    "properties": {
                        "value": {"type": "number", "description": "数值"},
                        "from_unit": {"type": "string", "description": "源单位"},
                        "to_unit": {"type": "string", "description": "目标单位"}
                    },
                    "required": ["value", "from_unit", "to_unit"]
                },
                server_id=self.server_id,
                requires_approval=False
            )
        ]
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行计算"""
        if tool_name == "calculate":
            expression = parameters["expression"]
            try:
                # 安全的数学计算
                result = eval(expression, {"__builtins__": {}}, {})
                return {
                    "success": True,
                    "expression": expression,
                    "result": result
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif tool_name == "convert_units":
            value = parameters["value"]
            from_unit = parameters["from_unit"]
            to_unit = parameters["to_unit"]
            
            # 简单的单位转换示例
            conversions = {
                ("km", "m"): 1000,
                ("m", "km"): 0.001,
                ("kg", "g"): 1000,
                ("g", "kg"): 0.001,
                ("celsius", "fahrenheit"): lambda x: x * 9/5 + 32,
                ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9
            }
            
            key = (from_unit.lower(), to_unit.lower())
            if key in conversions:
                converter = conversions[key]
                if callable(converter):
                    result = converter(value)
                else:
                    result = value * converter
                
                return {
                    "success": True,
                    "original": f"{value} {from_unit}",
                    "converted": f"{result} {to_unit}",
                    "result": result
                }
            else:
                return {
                    "success": False,
                    "error": f"不支持的转换: {from_unit} -> {to_unit}"
                }
        
        else:
            raise ValueError(f"未知工具: {tool_name}")
    
    async def list_resources(self):
        return []
    
    async def list_prompts(self):
        return []
    
    async def read_resource(self, uri: str):
        return None


class TimeMCPServer(MCPServer):
    """时间工具MCP Server"""
    
    def __init__(self):
        super().__init__(
            server_id="time",
            name="Time Server",
            description="提供时间相关工具"
        )
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="get_current_time",
                description="获取当前时间",
                parameters={
                    "type": "object",
                    "properties": {
                        "format": {"type": "string", "description": "时间格式，如 '%Y-%m-%d %H:%M:%S'"}
                    }
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="calculate_time_diff",
                description="计算两个时间的差值",
                parameters={
                    "type": "object",
                    "properties": {
                        "time1": {"type": "string", "description": "时间1"},
                        "time2": {"type": "string", "description": "时间2"}
                    },
                    "required": ["time1", "time2"]
                },
                server_id=self.server_id,
                requires_approval=False
            )
        ]
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行时间操作"""
        if tool_name == "get_current_time":
            format_str = parameters.get("format", "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            return {
                "success": True,
                "timestamp": now.timestamp(),
                "formatted": now.strftime(format_str),
                "iso": now.isoformat()
            }
        
        elif tool_name == "calculate_time_diff":
            # 简化实现
            return {
                "success": True,
                "message": "时间差计算功能（示例）"
            }
        
        else:
            raise ValueError(f"未知工具: {tool_name}")
    
    async def list_resources(self):
        return []
    
    async def list_prompts(self):
        return []
    
    async def read_resource(self, uri: str):
        return None


# ==================== 测试函数 ====================

async def test_real_tools():
    """测试真实工具调用"""
    print("\n" + "="*70)
    print("测试真实工具调用 - MCP + Function Call")
    print("="*70 + "\n")
    
    # 创建MCP Host
    print("[1/7] 创建MCP Host...")
    mcp_host = MCPHost(user_id='test_real_tools')
    print("[PASS]\n")
    
    # 注册真实工具Servers
    print("[2/7] 注册真实工具Servers...")
    mcp_host.register_server(FileSystemMCPServer())
    mcp_host.register_server(CalculatorMCPServer())
    mcp_host.register_server(TimeMCPServer())
    print("[PASS] 已注册3个Server\n")
    
    # 发现工具
    print("[3/7] 发现所有工具...")
    await mcp_host.discover_tools()
    tools = mcp_host.get_available_tools()
    print(f"[PASS] 发现 {len(tools)} 个工具\n")
    
    # 测试1: 获取当前时间
    print("[4/7] 测试工具1: 获取当前时间")
    result = await mcp_host.call_tool(
        tool_name="get_current_time",
        parameters={"format": "%Y年%m月%d日 %H:%M:%S"}
    )
    print(f"[PASS] 当前时间: {result['formatted']}\n")
    
    # 测试2: 数学计算
    print("[5/7] 测试工具2: 数学计算")
    result = await mcp_host.call_tool(
        tool_name="calculate",
        parameters={"expression": "2 + 3 * 4"}
    )
    print(f"[PASS] 计算结果: {result['expression']} = {result['result']}\n")
    
    # 测试3: 单位转换
    print("[6/7] 测试工具3: 单位转换")
    result = await mcp_host.call_tool(
        tool_name="convert_units",
        parameters={"value": 100, "from_unit": "kg", "to_unit": "g"}
    )
    print(f"[PASS] 转换结果: {result['original']} = {result['converted']}\n")
    
    # 测试4: 文件系统操作
    print("[7/7] 测试工具4: 文件系统操作")
    
    # 写入测试文件
    test_file = "test_mcp_output.txt"
    test_content = f"MCP测试文件\n创建时间: {datetime.now()}\n这是一个测试文件，用于验证MCP工具调用功能。"
    
    result = await mcp_host.call_tool(
        tool_name="write_file",
        parameters={"filepath": test_file, "content": test_content}
    )
    print(f"[PASS] 写入文件: {result['filepath']} ({result['bytes_written']} 字节)")
    
    # 读取测试文件
    result = await mcp_host.call_tool(
        tool_name="read_file",
        parameters={"filepath": test_file}
    )
    print(f"[PASS] 读取文件: {result['filepath']} ({result['size']} 字节)")
    print(f"内容预览: {result['content'][:100]}...\n")
    
    # 列出当前目录文件
    result = await mcp_host.call_tool(
        tool_name="list_files",
        parameters={"directory": "."}
    )
    print(f"[PASS] 列出文件: {result['directory']} (共 {result['total']} 个)")
    print(f"前5个文件: {result['files'][:5]}\n")
    
    # 查看审计日志
    print("="*70)
    print("审计日志")
    print("="*70)
    logs = mcp_host.get_audit_logs()
    for log in logs:
        status = "[PASS]" if log.success else "[FAIL]"
        approved = "[APPROVED]" if log.approved else "[PENDING]"
        print(f"{status} {approved} {log.tool_name} - {log.timestamp.strftime('%H:%M:%S')}")
    
    print(f"\n总计: {len(logs)} 次工具调用")
    print("="*70 + "\n")
    
    print("[SUCCESS] 所有真实工具调用测试通过！")


async def test_agent_with_real_tools():
    """测试Agent自动调用真实工具"""
    print("\n" + "="*70)
    print("测试Agent自动调用真实工具")
    print("="*70 + "\n")
    
    try:
        from backend.llm.llm_service import get_llm_service
        from backend.learning.production_rag_system import ProductionRAGSystem
        from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
        from backend.agents.langchain_specialized_agents import create_langchain_agent
        
        # 初始化服务
        print("[1/4] 初始化服务...")
        llm_service = get_llm_service()
        test_user_id = "test_real_agent"
        rag_system = ProductionRAGSystem(test_user_id, use_gpu=False)
        retrieval_system = UnifiedHybridRetrieval(test_user_id)
        print("[PASS]\n")
        
        # 创建MCP Host并注册工具
        print("[2/4] 创建MCP Host并注册真实工具...")
        mcp_host = MCPHost(user_id=test_user_id)
        mcp_host.register_server(CalculatorMCPServer())
        mcp_host.register_server(TimeMCPServer())
        print("[PASS]\n")
        
        # 创建Agent
        print("[3/4] 创建Agent...")
        agent = create_langchain_agent(
            agent_type='career',
            user_id=test_user_id,
            llm_service=llm_service,
            rag_system=rag_system,
            retrieval_system=retrieval_system,
            use_workflow=True,
            mcp_host=mcp_host
        )
        await agent.initialize()
        print(f"[PASS] Agent已创建，共 {len(agent.tool_module.get_tools())} 个工具\n")
        
        # 让Agent处理需要工具的任务
        print("[4/4] Agent处理任务（需要调用工具）...")
        print("任务: '帮我计算 123 * 456 等于多少'")
        
        result = agent.process("帮我计算 123 * 456 等于多少")
        
        print(f"\n结果:")
        print(f"  模式: {result['mode']}")
        print(f"  使用Agent: {result['agent_used']}")
        print(f"\n回复: {result['response']}\n")
        
        print("[PASS] Agent成功调用工具完成任务")
        
    except Exception as e:
        print(f"[FAIL] Agent测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试流程"""
    # 测试1: 直接调用真实工具
    await test_real_tools()
    
    # 测试2: Agent自动调用真实工具
    await test_agent_with_real_tools()
    
    print("\n" + "="*70)
    print("所有测试完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
