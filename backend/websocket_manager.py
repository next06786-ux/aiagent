"""
WebSocket连接管理器
用于Agent对话的实时状态推送
"""
from fastapi import WebSocket
from typing import Dict, Set
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃连接：{user_id: {session_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, session_id: str):
        """接受新连接"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        self.active_connections[user_id][session_id] = websocket
        print(f"✅ [WebSocket] 用户 {user_id} 连接成功 (session: {session_id})")
        
    def disconnect(self, user_id: str, session_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            if session_id in self.active_connections[user_id]:
                del self.active_connections[user_id][session_id]
                print(f"❌ [WebSocket] 用户 {user_id} 断开连接 (session: {session_id})")
                
            # 如果用户没有其他连接，删除用户记录
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_message(self, user_id: str, session_id: str, message: dict):
        """发送消息到指定会话"""
        if user_id in self.active_connections:
            if session_id in self.active_connections[user_id]:
                websocket = self.active_connections[user_id][session_id]
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"⚠️ [WebSocket] 发送消息失败: {e}")
                    self.disconnect(user_id, session_id)
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """广播消息到用户的所有会话"""
        if user_id in self.active_connections:
            disconnected = []
            for session_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"⚠️ [WebSocket] 广播失败: {e}")
                    disconnected.append(session_id)
            
            # 清理断开的连接
            for session_id in disconnected:
                self.disconnect(user_id, session_id)
    
    def get_connection_count(self, user_id: str = None) -> int:
        """获取连接数"""
        if user_id:
            return len(self.active_connections.get(user_id, {}))
        return sum(len(sessions) for sessions in self.active_connections.values())


# 全局连接管理器实例
ws_manager = ConnectionManager()


# 消息类型定义
class MessageType:
    """WebSocket消息类型"""
    TOOL_START = "tool_start"          # 工具开始执行
    TOOL_COMPLETE = "tool_complete"    # 工具执行完成
    TOOL_FAILED = "tool_failed"        # 工具执行失败
    AGENT_THINKING = "agent_thinking"  # Agent思考中
    RESPONSE = "response"              # 最终回复
    ERROR = "error"                    # 错误消息


async def send_tool_start(user_id: str, session_id: str, tool_name: str, server_name: str):
    """发送工具开始执行的消息"""
    message = {
        "type": MessageType.TOOL_START,
        "tool_name": tool_name,
        "server_name": server_name,
        "timestamp": datetime.now().isoformat()
    }
    await ws_manager.send_message(user_id, session_id, message)


async def send_tool_complete(user_id: str, session_id: str, tool_name: str, server_name: str, result: str):
    """发送工具执行完成的消息"""
    message = {
        "type": MessageType.TOOL_COMPLETE,
        "tool_name": tool_name,
        "server_name": server_name,
        "result": result[:100] if result else None,
        "timestamp": datetime.now().isoformat()
    }
    await ws_manager.send_message(user_id, session_id, message)


async def send_tool_failed(user_id: str, session_id: str, tool_name: str, server_name: str, error: str):
    """发送工具执行失败的消息"""
    message = {
        "type": MessageType.TOOL_FAILED,
        "tool_name": tool_name,
        "server_name": server_name,
        "error": error,
        "timestamp": datetime.now().isoformat()
    }
    await ws_manager.send_message(user_id, session_id, message)


async def send_response(user_id: str, session_id: str, content: str, metadata: dict = None):
    """发送最终回复"""
    message = {
        "type": MessageType.RESPONSE,
        "content": content,
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat()
    }
    await ws_manager.send_message(user_id, session_id, message)


async def send_error(user_id: str, session_id: str, error: str):
    """发送错误消息"""
    message = {
        "type": MessageType.ERROR,
        "error": error,
        "timestamp": datetime.now().isoformat()
    }
    await ws_manager.send_message(user_id, session_id, message)
