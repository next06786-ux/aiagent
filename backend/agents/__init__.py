"""
Agent模块 - LangChain ReAct实现（MCP架构）
LangChain-based ReAct Agent Architecture (MCP-based)

导出：
- LangChainReActAgent: Agent基类
- ConfigurableAgent: 可配置Agent（基于配置文件）
- create_langchain_agent: Agent工厂函数（配置驱动）
- load_agent_config: 配置加载函数
"""

from backend.agents.langchain_agent_framework import (
    LangChainReActAgent,
    LLMModule,
    MemoryModule,
    ToolModule,
    AgentMessage,
    ReActStep,
    DashScopeLLM
)

from backend.agents.langchain_specialized_agents import (
    ConfigurableAgent,
    create_langchain_agent,
    load_agent_config
)

__all__ = [
    'LangChainReActAgent',
    'LLMModule',
    'MemoryModule',
    'ToolModule',
    'AgentMessage',
    'ReActStep',
    'DashScopeLLM',
    'ConfigurableAgent',
    'create_langchain_agent',
    'load_agent_config'
]
