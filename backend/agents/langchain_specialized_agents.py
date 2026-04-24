"""
基于LangChain的专业化Agent实现（MCP架构）
LangChain-based Specialized Agent Implementations (MCP Architecture)

完全基于MCP协议的Agent实现：
- 工具通过MCP服务器动态发现
- 配置驱动的Agent创建
- 解耦的工具与Agent架构
"""

from backend.agents.langchain_agent_framework import LangChainReActAgent
from typing import Dict, Any
import json
import os
import importlib


class ConfigurableAgent(LangChainReActAgent):
    """可配置的Agent基类 - 通过配置文件定义行为"""
    
    def __init__(
        self,
        agent_type: str,
        user_id: str,
        llm_service,
        rag_system,
        retrieval_system,
        use_workflow: bool = True,
        mcp_host = None,
        websocket_callback = None,
        config: Dict[str, Any] = None
    ):
        """
        初始化可配置Agent
        
        Args:
            config: Agent配置字典，包含：
                - name: Agent名称
                - description: Agent描述
                - system_prompt: 系统提示词
                - mcp_servers: 使用的MCP服务器列表
        """
        self.config = config or {}
        super().__init__(
            agent_type=agent_type,
            user_id=user_id,
            llm_service=llm_service,
            rag_system=rag_system,
            retrieval_system=retrieval_system,
            use_workflow=use_workflow,
            mcp_host=mcp_host,
            websocket_callback=websocket_callback
        )
    
    def _register_agent_tools(self):
        """不再硬编码工具 - 工具通过MCP动态发现"""
        # 工具由MCP Host在initialize()时自动发现和注册
        # 不需要在这里手动注册
        pass
    
    def get_system_prompt(self) -> str:
        """从配置获取系统提示词"""
        return self.config.get('system_prompt', '你是一个AI助手。')


# ==================== 配置加载器 ====================

def load_agent_config(config_path: str = None) -> Dict[str, Any]:
    """
    加载Agent配置文件
    
    Args:
        config_path: 配置文件路径，默认为 backend/agents/agent_config.json
    
    Returns:
        配置字典
    """
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__),
            'agent_config.json'
        )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_mcp_server(server_config: Dict[str, Any], env_vars: Dict[str, str] = None) -> Any:
    """
    根据配置创建MCP服务器实例
    
    Args:
        server_config: 服务器配置，包含 class, module, init_params
        env_vars: 环境变量字典（用于替换 ${VAR} 格式的变量）
    
    Returns:
        MCP服务器实例
    """
    module_name = server_config['module']
    class_name = server_config['class']
    
    # 动态导入模块
    module = importlib.import_module(module_name)
    server_class = getattr(module, class_name)
    
    # 处理初始化参数（替换环境变量）
    init_params = server_config.get('init_params', {})
    if env_vars:
        for key, value in init_params.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var_name = value[2:-1]
                init_params[key] = env_vars.get(env_var_name, '')
    
    # 创建实例
    return server_class(**init_params)


# ==================== Agent工厂 ====================

def create_langchain_agent(
    agent_type: str,
    user_id: str,
    llm_service,
    rag_system,
    retrieval_system,
    use_workflow: bool = True,
    mcp_host = None,
    websocket_callback = None,
    config_path: str = None
) -> LangChainReActAgent:
    """
    创建基于LangChain的Agent实例（配置驱动）
    
    Args:
        agent_type: 'relationship', 'education', 'career'
        user_id: 用户ID
        llm_service: LLM服务
        rag_system: RAG系统
        retrieval_system: 混合检索系统
        use_workflow: 是否启用Workflow混合模式
        mcp_host: MCP Host实例（可选）
            - 如果为None，将自动创建并注册配置中的MCP服务器
        websocket_callback: WebSocket回调函数（可选）
        config_path: 配置文件路径（可选）
    
    Returns:
        ConfigurableAgent实例
    """
    # 加载配置
    config = load_agent_config(config_path)
    
    # 获取Agent配置
    agent_config = config['agents'].get(agent_type)
    if not agent_config:
        raise ValueError(f"未知的Agent类型: {agent_type}，可用类型: {list(config['agents'].keys())}")
    
    # 如果没有提供MCP Host，创建一个新的
    from backend.agents.mcp_integration import MCPHost
    if mcp_host is None:
        mcp_host = MCPHost(user_id=user_id)
        
        # 根据配置注册MCP服务器
        mcp_servers_config = config.get('mcp_servers', {})
        env_vars = dict(os.environ)  # 获取环境变量
        
        for server_id in agent_config.get('mcp_servers', []):
            if server_id in mcp_servers_config:
                server_config = mcp_servers_config[server_id]
                try:
                    server_instance = create_mcp_server(server_config, env_vars)
                    mcp_host.register_server(server_instance)
                    print(f"   ✓ 已注册MCP服务器: {server_id}")
                except Exception as e:
                    print(f"   ⚠️  注册MCP服务器失败 ({server_id}): {e}")
    
    # 创建Agent实例
    agent = ConfigurableAgent(
        agent_type=agent_type,
        user_id=user_id,
        llm_service=llm_service,
        rag_system=rag_system,
        retrieval_system=retrieval_system,
        use_workflow=use_workflow,
        mcp_host=mcp_host,
        websocket_callback=websocket_callback,
        config=agent_config
    )
    
    return agent
