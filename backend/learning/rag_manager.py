"""
统一 RAG 管理器
确保整个系统使用同一个 RAG 实例（ProductionRAGSystem with FAISS）
"""
from typing import Dict
from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType


class RAGManager:
    """RAG 系统管理器 - 单例模式"""
    
    _instances: Dict[str, ProductionRAGSystem] = {}
    
    @classmethod
    def get_system(cls, user_id: str, use_gpu: bool = False) -> ProductionRAGSystem:
        """
        获取或创建用户的 RAG 系统
        
        Args:
            user_id: 用户ID
            use_gpu: 是否使用GPU加速（默认False，4GB显存不稳定）
        """
        if user_id not in cls._instances:
            cls._instances[user_id] = ProductionRAGSystem(
                user_id=user_id,
                storage_path="./data/production_rag",
                use_gpu=use_gpu  # 默认启用GPU，会自动检测并降级
            )
            print(f"✅ [RAGManager] 为用户 {user_id} 创建 RAG 系统 (GPU={use_gpu})")
        else:
            print(f"♻️ [RAGManager] 复用已有 RAG 系统: user={user_id}")
        
        return cls._instances[user_id]
    
    @classmethod
    def add_conversation_memory(cls, user_id: str, conversation: str, importance: float = 0.7):
        """快捷方法：添加对话记忆"""
        system = cls.get_system(user_id)
        return system.add_memory(
            memory_type=MemoryType.CONVERSATION,
            content=conversation,
            metadata={"source": "conversation"},
            importance=importance
        )
    
    @classmethod
    def clear_cache(cls, user_id: str = None):
        """清除缓存"""
        if user_id:
            if user_id in cls._instances:
                del cls._instances[user_id]
        else:
            cls._instances.clear()


# 导出兼容接口
class MemorySystemManager:
    """兼容旧代码的接口"""
    
    @staticmethod
    def get_system(user_id: str, use_gpu: bool = False) -> ProductionRAGSystem:
        """获取RAG系统（兼容接口）- 默认CPU模式"""
        return RAGManager.get_system(user_id, use_gpu=use_gpu)
    
    @staticmethod
    def add_conversation_memory(user_id: str, conversation: str, importance: float = 0.7):
        return RAGManager.add_conversation_memory(user_id, conversation, importance)
