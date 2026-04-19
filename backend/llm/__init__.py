"""
大模型服务模块
"""
from .llm_service import LLMService, LLMProvider, get_llm_service

__all__ = ['LLMService', 'LLMProvider', 'get_llm_service']
