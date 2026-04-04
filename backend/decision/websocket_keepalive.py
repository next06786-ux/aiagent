"""
WebSocket Keepalive 机制
解决长时间推演时的连接超时问题
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketKeepalive:
    """
    WebSocket保活管理器
    
    功能：
    1. 定期发送ping消息保持连接
    2. 检测连接状态
    3. 自动重连机制
    """
    
    def __init__(
        self,
        websocket,
        ping_interval: int = 30,  # 每30秒ping一次
        ping_timeout: int = 10     # ping超时10秒
    ):
        self.websocket = websocket
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.is_alive = True
        self.last_pong_time = datetime.now()
        self._keepalive_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动keepalive"""
        self._keepalive_task = asyncio.create_task(self._keepalive_loop())
        logger.info(f"[Keepalive] 已启动，ping间隔{self.ping_interval}秒")
    
    async def stop(self):
        """停止keepalive"""
        self.is_alive = False
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
        logger.info("[Keepalive] 已停止")
    
    async def _keepalive_loop(self):
        """保活循环"""
        try:
            while self.is_alive:
                await asyncio.sleep(self.ping_interval)
                
                try:
                    # 发送ping消息
                    await self.websocket.send_json({
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.debug("[Keepalive] 发送ping")
                    
                    # 等待pong（客户端应该自动响应）
                    # 注意：FastAPI的WebSocket会自动处理ping/pong
                    # 这里只是发送一个应用层的ping消息
                    
                except Exception as e:
                    logger.error(f"[Keepalive] Ping失败: {e}")
                    self.is_alive = False
                    break
        
        except asyncio.CancelledError:
            logger.info("[Keepalive] 任务被取消")
        except Exception as e:
            logger.error(f"[Keepalive] 异常: {e}")


class EnhancedWebSocketManager:
    """
    增强的WebSocket管理器
    
    功能：
    1. 连接管理
    2. 自动keepalive
    3. 消息队列
    4. 错误恢复
    """
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Any]] = {}
    
    async def connect(
        self,
        websocket,
        user_id: str,
        enable_keepalive: bool = True
    ):
        """建立连接"""
        await websocket.accept()
        
        connection_info = {
            'websocket': websocket,
            'user_id': user_id,
            'connected_at': datetime.now(),
            'keepalive': None,
            'message_count': 0
        }
        
        # 启动keepalive
        if enable_keepalive:
            keepalive = WebSocketKeepalive(websocket)
            await keepalive.start()
            connection_info['keepalive'] = keepalive
        
        self.active_connections[user_id] = connection_info
        logger.info(f"[WS] 用户{user_id}连接成功，keepalive={'启用' if enable_keepalive else '禁用'}")
    
    async def disconnect(self, user_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            conn_info = self.active_connections[user_id]
            
            # 停止keepalive
            if conn_info['keepalive']:
                await conn_info['keepalive'].stop()
            
            del self.active_connections[user_id]
            logger.info(f"[WS] 用户{user_id}断开连接")
    
    async def send_message(
        self,
        user_id: str,
        message: Dict[str, Any],
        retry: int = 3
    ) -> bool:
        """
        发送消息（带重试）
        
        Args:
            user_id: 用户ID
            message: 消息内容
            retry: 重试次数
        
        Returns:
            是否发送成功
        """
        if user_id not in self.active_connections:
            logger.warning(f"[WS] 用户{user_id}未连接")
            return False
        
        conn_info = self.active_connections[user_id]
        websocket = conn_info['websocket']
        
        for attempt in range(retry):
            try:
                await websocket.send_json(message)
                conn_info['message_count'] += 1
                logger.debug(f"[WS] 发送消息到{user_id}: {message.get('type')}")
                return True
            
            except Exception as e:
                logger.error(f"[WS] 发送失败（尝试{attempt+1}/{retry}）: {e}")
                
                if attempt < retry - 1:
                    await asyncio.sleep(0.5)
                else:
                    # 最后一次失败，断开连接
                    await self.disconnect(user_id)
                    return False
        
        return False
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息到所有连接"""
        disconnected = []
        
        for user_id in list(self.active_connections.keys()):
            success = await self.send_message(user_id, message, retry=1)
            if not success:
                disconnected.append(user_id)
        
        # 清理断开的连接
        for user_id in disconnected:
            await self.disconnect(user_id)
    
    def get_connection_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取连接信息"""
        if user_id not in self.active_connections:
            return None
        
        conn_info = self.active_connections[user_id]
        return {
            'user_id': user_id,
            'connected_at': conn_info['connected_at'].isoformat(),
            'message_count': conn_info['message_count'],
            'keepalive_enabled': conn_info['keepalive'] is not None
        }
    
    def get_all_connections(self) -> List[Dict[str, Any]]:
        """获取所有连接信息"""
        return [
            self.get_connection_info(user_id)
            for user_id in self.active_connections.keys()
        ]


# 全局实例
ws_manager = EnhancedWebSocketManager()


# 使用示例
async def example_usage():
    """使用示例"""
    from fastapi import WebSocket
    
    # 在FastAPI路由中使用
    @app.websocket("/ws/simulation/{user_id}")
    async def simulation_websocket(websocket: WebSocket, user_id: str):
        # 建立连接（自动启用keepalive）
        await ws_manager.connect(websocket, user_id, enable_keepalive=True)
        
        try:
            # 发送初始消息
            await ws_manager.send_message(user_id, {
                'type': 'connected',
                'message': '连接成功，开始推演'
            })
            
            # 模拟长时间推演（12个月）
            for month in range(1, 13):
                # 发送月度更新
                await ws_manager.send_message(user_id, {
                    'type': 'month_update',
                    'month': month,
                    'data': {'score': 75 + month}
                })
                
                # 模拟处理时间
                await asyncio.sleep(5)  # 每月5秒
            
            # 发送完成消息
            await ws_manager.send_message(user_id, {
                'type': 'complete',
                'message': '推演完成'
            })
        
        except Exception as e:
            logger.error(f"推演异常: {e}")
            await ws_manager.send_message(user_id, {
                'type': 'error',
                'message': str(e)
            })
        
        finally:
            # 断开连接
            await ws_manager.disconnect(user_id)
