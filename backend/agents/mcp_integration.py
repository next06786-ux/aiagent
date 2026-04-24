"""
MCP (Model Context Protocol) 集成
MCP Integration for Dynamic Tool Discovery

架构：
- MCP Host: Agent系统（本文件）
- MCP Client: 工具调用客户端
- MCP Server: 外部工具服务器（Github、Database等）

三类资源：
1. Tools: 可调用的函数
2. Resources: 可读取的数据
3. Prompts: 可复用的提示词模板
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json
import asyncio
from abc import ABC, abstractmethod


# ==================== MCP数据结构 ====================

class MCPResourceType(Enum):
    """MCP资源类型"""
    TOOL = "tool"
    RESOURCE = "resource"
    PROMPT = "prompt"


@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    server_id: str
    requires_approval: bool = False  # 是否需要人工确认
    
    def to_langchain_tool(self, executor: Callable):
        """转换为LangChain Tool"""
        from langchain.tools import Tool
        return Tool(
            name=self.name,
            description=self.description,
            func=executor
        )


@dataclass
class MCPResource:
    """MCP资源定义"""
    uri: str
    name: str
    description: str
    mime_type: str
    server_id: str


@dataclass
class MCPPrompt:
    """MCP提示词模板"""
    name: str
    description: str
    template: str
    parameters: List[str]
    server_id: str


@dataclass
class MCPCallLog:
    """MCP调用日志（审计追踪）"""
    timestamp: datetime
    tool_name: str
    server_id: str
    parameters: Dict[str, Any]
    result: Any
    success: bool
    user_id: str
    approved: bool = True  # 是否经过人工确认


# ==================== MCP Server接口 ====================

class MCPServer(ABC):
    """
    MCP Server抽象基类
    
    每个Server提供一组工具、资源和提示词
    """
    
    def __init__(self, server_id: str, name: str, description: str):
        self.server_id = server_id
        self.name = name
        self.description = description
        self.enabled = True
    
    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        """列出所有可用工具"""
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[MCPResource]:
        """列出所有可用资源"""
        pass
    
    @abstractmethod
    async def list_prompts(self) -> List[MCPPrompt]:
        """列出所有可用提示词"""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """调用工具"""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> Any:
        """读取资源"""
        pass


# ==================== 示例MCP Server ====================

class GithubMCPServer(MCPServer):
    """Github MCP Server示例"""
    
    def __init__(self, api_token: str = None):
        super().__init__(
            server_id="github",
            name="Github Server",
            description="提供Github API工具"
        )
        self.api_token = api_token
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="github_create_issue",
                description="在Github仓库创建Issue",
                parameters={
                    "type": "object",
                    "properties": {
                        "repo": {"type": "string", "description": "仓库名称（owner/repo）"},
                        "title": {"type": "string", "description": "Issue标题"},
                        "body": {"type": "string", "description": "Issue内容"}
                    },
                    "required": ["repo", "title"]
                },
                server_id=self.server_id,
                requires_approval=True  # 需要人工确认
            ),
            MCPTool(
                name="github_search_repos",
                description="搜索Github仓库",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"},
                        "language": {"type": "string", "description": "编程语言"}
                    },
                    "required": ["query"]
                },
                server_id=self.server_id,
                requires_approval=False
            )
        ]
    
    async def list_resources(self) -> List[MCPResource]:
        return []
    
    async def list_prompts(self) -> List[MCPPrompt]:
        return []
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """调用Github API"""
        if tool_name == "github_create_issue":
            # 实际实现会调用Github API
            return {
                "success": True,
                "issue_url": f"https://github.com/{parameters['repo']}/issues/123",
                "message": f"Issue创建成功: {parameters['title']}"
            }
        elif tool_name == "github_search_repos":
            return {
                "success": True,
                "repos": [
                    {"name": "example-repo", "stars": 1000}
                ]
            }
        else:
            raise ValueError(f"未知工具: {tool_name}")
    
    async def read_resource(self, uri: str) -> Any:
        return None


class DatabaseMCPServer(MCPServer):
    """数据库MCP Server示例"""
    
    def __init__(self):
        super().__init__(
            server_id="database",
            name="Database Server",
            description="提供数据库查询工具"
        )
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="db_query_users",
                description="查询用户信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "用户ID"}
                    },
                    "required": ["user_id"]
                },
                server_id=self.server_id,
                requires_approval=False
            ),
            MCPTool(
                name="db_update_profile",
                description="更新用户资料",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "data": {"type": "object"}
                    },
                    "required": ["user_id", "data"]
                },
                server_id=self.server_id,
                requires_approval=True  # 写操作需要确认
            )
        ]
    
    async def list_resources(self) -> List[MCPResource]:
        return []
    
    async def list_prompts(self) -> List[MCPPrompt]:
        return []
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        if tool_name == "db_query_users":
            return {"user_id": parameters["user_id"], "name": "示例用户"}
        elif tool_name == "db_update_profile":
            return {"success": True, "message": "资料更新成功"}
        else:
            raise ValueError(f"未知工具: {tool_name}")
    
    async def read_resource(self, uri: str) -> Any:
        return None


# ==================== MCP Client ====================

class MCPClient:
    """
    MCP Client - 负责与MCP Server通信
    
    功能：
    1. 发送工具调用请求
    2. 处理响应
    3. 错误处理
    """
    
    def __init__(self):
        self.call_logs: List[MCPCallLog] = []
    
    async def call_tool(
        self,
        server: MCPServer,
        tool_name: str,
        parameters: Dict[str, Any],
        user_id: str,
        approved: bool = True
    ) -> Any:
        """
        调用MCP Server的工具
        
        Args:
            server: MCP Server实例
            tool_name: 工具名称
            parameters: 参数
            user_id: 用户ID
            approved: 是否已获得授权
        """
        print(f"🔧 [MCP Client] 调用工具: {tool_name}")
        print(f"   Server: {server.name}")
        print(f"   参数: {json.dumps(parameters, ensure_ascii=False)}")
        
        try:
            result = await server.call_tool(tool_name, parameters)
            
            # 记录审计日志
            log = MCPCallLog(
                timestamp=datetime.now(),
                tool_name=tool_name,
                server_id=server.server_id,
                parameters=parameters,
                result=result,
                success=True,
                user_id=user_id,
                approved=approved
            )
            self.call_logs.append(log)
            
            # 打印返回结果（用于调试）
            result_preview = str(result)[:500] if result else "None"
            print(f"   ✅ 调用成功")
            print(f"   📦 返回结果: {result_preview}")
            return result
            
        except Exception as e:
            print(f"   ❌ 调用失败: {e}")
            
            # 记录失败日志
            log = MCPCallLog(
                timestamp=datetime.now(),
                tool_name=tool_name,
                server_id=server.server_id,
                parameters=parameters,
                result=str(e),
                success=False,
                user_id=user_id,
                approved=approved
            )
            self.call_logs.append(log)
            
            raise
    
    def get_audit_logs(self, user_id: str = None) -> List[MCPCallLog]:
        """获取审计日志"""
        if user_id:
            return [log for log in self.call_logs if log.user_id == user_id]
        return self.call_logs


# ==================== MCP Host ====================

class MCPHost:
    """
    MCP Host - Agent系统的MCP管理器
    
    职责：
    1. 管理MCP Server列表
    2. 动态发现工具
    3. 授权控制
    4. 审计追踪
    
    三层安全机制：
    1. 能力声明：Server明确声明工具
    2. 授权控制：敏感操作需要确认
    3. 审计追踪：所有调用都有日志
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.servers: Dict[str, MCPServer] = {}
        self.client = MCPClient()
        self.discovered_tools: Dict[str, MCPTool] = {}
        self.approval_callback: Optional[Callable] = None
    
    def register_server(self, server: MCPServer):
        """注册MCP Server"""
        self.servers[server.server_id] = server
        print(f"✅ [MCP Host] 注册Server: {server.name} ({server.server_id})")
    
    async def discover_tools(self):
        """
        动态发现所有Server的工具
        
        Agent启动时调用，扫描所有Server
        """
        print(f"\n{'='*60}")
        print(f"[MCP Host] 开始工具发现")
        print(f"{'='*60}\n")
        
        self.discovered_tools = {}
        
        for server_id, server in self.servers.items():
            if not server.enabled:
                continue
            
            print(f"📡 扫描Server: {server.name}")
            
            try:
                # 发送tools/list请求
                tools = await server.list_tools()
                
                for tool in tools:
                    self.discovered_tools[tool.name] = tool
                    approval_mark = "🔒" if tool.requires_approval else "🔓"
                    print(f"   {approval_mark} {tool.name}: {tool.description}")
                
                print(f"   发现 {len(tools)} 个工具\n")
                
            except Exception as e:
                print(f"   ❌ 扫描失败: {e}\n")
        
        print(f"{'='*60}")
        print(f"[MCP Host] 工具发现完成")
        print(f"总计: {len(self.discovered_tools)} 个工具")
        print(f"{'='*60}\n")
    
    def get_available_tools(self) -> List[MCPTool]:
        """获取所有可用工具"""
        return list(self.discovered_tools.values())
    
    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Any:
        """
        调用工具（带授权控制）
        
        Args:
            tool_name: 工具名称
            parameters: 参数
        
        Returns:
            工具执行结果
        """
        # 1. 查找工具
        tool = self.discovered_tools.get(tool_name)
        if not tool:
            raise ValueError(f"工具不存在: {tool_name}")
        
        # 2. 授权控制（第二层安全）
        if tool.requires_approval:
            approved = await self._request_approval(tool, parameters)
            if not approved:
                raise PermissionError(f"工具调用未获授权: {tool_name}")
        else:
            approved = True
        
        # 3. 查找Server
        server = self.servers.get(tool.server_id)
        if not server:
            raise ValueError(f"Server不存在: {tool.server_id}")
        
        # 4. 调用工具（通过MCP Client）
        result = await self.client.call_tool(
            server=server,
            tool_name=tool_name,
            parameters=parameters,
            user_id=self.user_id,
            approved=approved
        )
        
        return result
    
    async def _request_approval(
        self,
        tool: MCPTool,
        parameters: Dict[str, Any]
    ) -> bool:
        """
        请求人工授权
        
        实际应用中，这里会：
        1. 发送通知给用户
        2. 等待用户确认
        3. 返回授权结果
        
        当前简化实现：自动批准
        """
        print(f"🔐 [授权请求] 工具: {tool.name}")
        print(f"   描述: {tool.description}")
        print(f"   参数: {json.dumps(parameters, ensure_ascii=False)}")
        
        if self.approval_callback:
            return await self.approval_callback(tool, parameters)
        
        # 简化实现：自动批准
        print(f"   ✅ 自动批准（生产环境应等待人工确认）")
        return True
    
    def set_approval_callback(self, callback: Callable):
        """设置授权回调函数"""
        self.approval_callback = callback
    
    def get_audit_logs(self) -> List[MCPCallLog]:
        """获取审计日志（第三层安全）"""
        return self.client.get_audit_logs(self.user_id)
    
    def export_audit_logs(self, filepath: str):
        """导出审计日志"""
        logs = self.get_audit_logs()
        with open(filepath, 'w', encoding='utf-8') as f:
            for log in logs:
                f.write(json.dumps({
                    'timestamp': log.timestamp.isoformat(),
                    'tool_name': log.tool_name,
                    'server_id': log.server_id,
                    'parameters': log.parameters,
                    'success': log.success,
                    'approved': log.approved
                }, ensure_ascii=False) + '\n')
        print(f"📝 审计日志已导出: {filepath}")


# ==================== Parallel Function Call ====================

class ParallelFunctionCaller:
    """
    并行函数调用器
    
    支持同时调用多个工具，提高效率
    """
    
    def __init__(self, mcp_host: MCPHost):
        self.mcp_host = mcp_host
    
    async def call_parallel(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        并行调用多个工具
        
        Args:
            tool_calls: [
                {"tool_name": "xxx", "parameters": {...}},
                {"tool_name": "yyy", "parameters": {...}}
            ]
        
        Returns:
            结果列表（顺序与输入对应）
        """
        print(f"\n⚡ [并行调用] 同时调用 {len(tool_calls)} 个工具")
        
        # 创建异步任务
        tasks = []
        for call in tool_calls:
            task = self.mcp_host.call_tool(
                tool_name=call['tool_name'],
                parameters=call['parameters']
            )
            tasks.append(task)
        
        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"   ❌ 工具{i+1}失败: {result}")
            else:
                print(f"   ✅ 工具{i+1}成功")
        
        return results
