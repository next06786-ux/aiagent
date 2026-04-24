"""
Agent模块 - LangChain ReAct实现
LangChain-based ReAct Agent Architecture

导出：
- LangChainReActAgent: Agent基类
- RelationshipAgent: 人际关系Agent
- EducationAgent: 教育规划Agent
- CareerAgent: 职业规划Agent
- create_langchain_agent: Agent工厂函数
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
    RelationshipAgent,
    EducationAgent,
    CareerAgent,
    create_langchain_agent
)

__all__ = [
    'LangChainReActAgent',
    'LLMModule',
    'MemoryModule',
    'ToolModule',
    'AgentMessage',
    'ReActStep',
    'DashScopeLLM',
    'RelationshipAgent',
    'EducationAgent',
    'CareerAgent',
    'create_langchain_agent'
]
