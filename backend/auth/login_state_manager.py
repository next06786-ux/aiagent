"""
登录状态管理器
自动检测登录状态并加载用户系统（RAG、知识图谱等）
"""
import asyncio
import logging
from typing import Dict, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class LoginStateManager:
    """登录状态管理器 - 自动加载用户系统"""
    
    def __init__(self):
        # 已加载系统的用户集合
        self.loaded_users: Set[str] = set()
        # 加载锁，避免重复加载
        self.loading_locks: Dict[str, asyncio.Lock] = {}
        # 加载状态
        self.loading_status: Dict[str, Dict[str, bool]] = {}
    
    async def check_and_load_user_systems(self, user_id: str) -> Dict[str, bool]:
        """
        检查并加载用户系统（RAG、知识图谱）
        
        Args:
            user_id: 用户ID
        
        Returns:
            加载状态字典 {'rag': True, 'kg': True, 'info_kg': True}
        """
        # 如果已经加载过，直接返回
        if user_id in self.loaded_users:
            logger.info(f"用户 {user_id} 的系统已加载，跳过")
            return self.loading_status.get(user_id, {})
        
        # 获取或创建加载锁
        if user_id not in self.loading_locks:
            self.loading_locks[user_id] = asyncio.Lock()
        
        async with self.loading_locks[user_id]:
            # 双重检查，避免并发加载
            if user_id in self.loaded_users:
                return self.loading_status.get(user_id, {})
            
            logger.info(f"🔄 开始为用户 {user_id} 加载系统...")
            start_time = datetime.now()
            
            status = {
                'rag': False,
                'kg': False,
                'info_kg': False
            }
            
            # 1. 加载 RAG 系统
            try:
                status['rag'] = await self._load_rag_system(user_id)
            except Exception as e:
                logger.error(f"❌ 用户 {user_id} RAG系统加载失败: {e}")
            
            # 2. 加载信息知识图谱
            try:
                status['info_kg'] = await self._load_info_kg(user_id)
            except Exception as e:
                logger.error(f"❌ 用户 {user_id} 信息知识图谱加载失败: {e}")
            
            # 标记为已加载
            self.loaded_users.add(user_id)
            self.loading_status[user_id] = status
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ 用户 {user_id} 系统加载完成，耗时 {elapsed:.2f}秒")
            logger.info(f"   RAG: {'✅' if status['rag'] else '❌'}, "
                       f"KG: {'✅' if status['kg'] else '❌'}, "
                       f"InfoKG: {'✅' if status['info_kg'] else '❌'}")
            
            return status
    
    async def _load_rag_system(self, user_id: str) -> bool:
        """加载 RAG 系统"""
        try:
            from backend.startup_manager import _systems, _init_status
            import os
            
            # 检查是否已加载
            if user_id in _systems.get('rag_systems', {}):
                logger.info(f"   RAG系统已存在，跳过加载")
                return True
            
            logger.info(f"   ⏳ 加载 RAG 系统...")
            
            # 设置离线模式
            os.environ['HF_HUB_OFFLINE'] = '1'
            
            # 尝试加载生产级 RAG
            try:
                from backend.learning.production_rag_system import ProductionRAGSystem
                # 使用CPU模式，GPU模式在4GB显存下不稳定
                _systems['rag_systems'][user_id] = ProductionRAGSystem(user_id, use_gpu=False)
                logger.info(f"   ✅ RAG 系统加载完成（生产级）")
            except (ImportError, RuntimeError) as e:
                # 降级到轻量级 RAG
                from backend.learning.unified_rag_system import UnifiedRAGSystem
                _systems['rag_systems'][user_id] = UnifiedRAGSystem(user_id)
                logger.info(f"   ✅ RAG 系统加载完成（轻量模式）")
            
            # 更新全局状态
            _init_status['rag_system'] = True
            return True
            
        except Exception as e:
            logger.error(f"   ❌ RAG 系统加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _load_info_kg(self, user_id: str) -> bool:
        """加载信息知识图谱"""
        try:
            from backend.startup_manager import _systems
            
            # 检查是否已加载
            if user_id in _systems.get('info_kg_systems', {}):
                logger.info(f"   信息知识图谱已存在，跳过加载")
                return True
            
            logger.info(f"   ⏳ 加载信息知识图谱...")
            
            from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
            _systems['info_kg_systems'][user_id] = InformationKnowledgeGraph(user_id)
            
            logger.info(f"   ✅ 信息知识图谱加载完成")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ 信息知识图谱加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def is_user_loaded(self, user_id: str) -> bool:
        """检查用户系统是否已加载"""
        return user_id in self.loaded_users
    
    def get_user_status(self, user_id: str) -> Optional[Dict[str, bool]]:
        """获取用户系统加载状态"""
        return self.loading_status.get(user_id)
    
    async def unload_user_systems(self, user_id: str):
        """卸载用户系统（登出时调用）"""
        if user_id not in self.loaded_users:
            return
        
        logger.info(f"🔄 卸载用户 {user_id} 的系统...")
        
        try:
            from backend.startup_manager import _systems
            
            # 清理 RAG 系统
            if user_id in _systems.get('rag_systems', {}):
                del _systems['rag_systems'][user_id]
                logger.info(f"   ✅ RAG 系统已卸载")
            
            # 清理信息知识图谱
            if user_id in _systems.get('info_kg_systems', {}):
                del _systems['info_kg_systems'][user_id]
                logger.info(f"   ✅ 信息知识图谱已卸载")
            
            # 清理信息知识图谱
            if user_id in _systems.get('info_kg_systems', {}):
                del _systems['info_kg_systems'][user_id]
                logger.info(f"   ✅ 信息知识图谱已卸载")
            
            # 移除加载标记
            self.loaded_users.discard(user_id)
            if user_id in self.loading_status:
                del self.loading_status[user_id]
            
            logger.info(f"✅ 用户 {user_id} 系统卸载完成")
            
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 系统卸载失败: {e}")


# 全局单例
_login_state_manager: Optional[LoginStateManager] = None


def get_login_state_manager() -> LoginStateManager:
    """获取登录状态管理器单例"""
    global _login_state_manager
    if _login_state_manager is None:
        _login_state_manager = LoginStateManager()
    return _login_state_manager
