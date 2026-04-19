"""
启动时登录状态检测器
在后端启动时自动检测活跃的登录会话并加载对应的用户系统
"""
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StartupLoginChecker:
    """启动时登录状态检测器"""
    
    @staticmethod
    async def check_and_load_active_sessions():
        """
        检测所有活跃的登录会话并加载对应的用户系统
        在后端启动时调用
        """
        logger.info("🔍 检测活跃的登录会话...")
        
        try:
            from backend.auth.auth_service import get_auth_service
            from backend.auth.login_state_manager import get_login_state_manager
            
            auth_service = get_auth_service()
            login_manager = get_login_state_manager()
            
            # 获取所有活跃的token
            active_tokens = auth_service.active_tokens
            
            if not active_tokens:
                logger.info("   没有活跃的登录会话")
                return
            
            # 提取所有活跃用户ID（去重）
            active_user_ids = set()
            expired_tokens = []
            
            for token, token_data in active_tokens.items():
                # 检查是否过期
                if datetime.now() > token_data['expires_at']:
                    expired_tokens.append(token)
                    continue
                
                user_id = token_data['user_id']
                active_user_ids.add(user_id)
            
            # 清理过期token
            for token in expired_tokens:
                del active_tokens[token]
            
            if not active_user_ids:
                logger.info("   没有有效的活跃会话")
                return
            
            logger.info(f"   发现 {len(active_user_ids)} 个活跃用户会话")
            
            # 并行加载所有活跃用户的系统
            tasks = []
            for user_id in active_user_ids:
                logger.info(f"   准备加载用户 {user_id} 的系统...")
                tasks.append(login_manager.check_and_load_user_systems(user_id))
            
            # 等待所有加载任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计加载结果
            success_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"   用户系统加载失败: {result}")
                else:
                    success_count += 1
            
            logger.info(f"✅ 活跃会话系统加载完成: {success_count}/{len(active_user_ids)} 成功")
            
        except Exception as e:
            logger.error(f"❌ 活跃会话检测失败: {e}")
            import traceback
            traceback.print_exc()
    
    @staticmethod
    async def check_persistent_sessions():
        """
        检查持久化的会话信息（如果使用Redis等持久化存储）
        这是一个扩展点，当前使用内存存储，重启后会话会丢失
        """
        # TODO: 如果将来使用Redis等持久化存储token，可以在这里实现
        # 从持久化存储中恢复会话信息
        pass
    
    @staticmethod
    def get_active_sessions_summary() -> Dict[str, Any]:
        """
        获取活跃会话摘要
        
        Returns:
            {
                'total_sessions': int,
                'active_users': int,
                'sessions': [...]
            }
        """
        try:
            from backend.auth.auth_service import get_auth_service
            
            auth_service = get_auth_service()
            active_tokens = auth_service.active_tokens
            
            # 统计活跃用户
            active_user_ids = set()
            sessions = []
            
            for token, token_data in active_tokens.items():
                # 检查是否过期
                if datetime.now() > token_data['expires_at']:
                    continue
                
                user_id = token_data['user_id']
                active_user_ids.add(user_id)
                
                sessions.append({
                    'user_id': user_id,
                    'created_at': token_data['created_at'].isoformat(),
                    'expires_at': token_data['expires_at'].isoformat()
                })
            
            return {
                'total_sessions': len(sessions),
                'active_users': len(active_user_ids),
                'sessions': sessions
            }
            
        except Exception as e:
            logger.error(f"获取会话摘要失败: {e}")
            return {
                'total_sessions': 0,
                'active_users': 0,
                'sessions': []
            }


async def startup_check_and_load():
    """
    启动时检测并加载活跃会话
    在 FastAPI 的 startup 事件中调用
    """
    checker = StartupLoginChecker()
    await checker.check_and_load_active_sessions()
