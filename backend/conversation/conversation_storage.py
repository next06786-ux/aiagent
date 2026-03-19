"""
对话历史存储管理器
负责将对话持久化到数据库
"""
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from backend.database.models import ConversationHistory
from backend.database.connection import db_connection


class ConversationStorage:
    """对话历史存储管理器"""
    
    @staticmethod
    def save_message(
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        thinking: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> bool:
        """
        保存单条消息到数据库
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            role: 角色 (user/assistant)
            content: 消息内容
            thinking: AI思考过程（可选）
            context: 上下文数据（可选）
        
        Returns:
            是否保存成功
        """
        db = None
        try:
            db = db_connection.get_session()
            
            message = ConversationHistory(
                user_id=user_id,
                session_id=session_id,
                role=role,
                content=content,
                thinking=thinking,
                context=context,
                timestamp=datetime.utcnow()
            )
            
            db.add(message)
            db.commit()
            
            return True
        except Exception as e:
            print(f"❌ 保存消息到数据库失败: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    @staticmethod
    def get_session_messages(user_id: str, session_id: str) -> List[Dict]:
        """
        获取指定会话的所有消息
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
        
        Returns:
            消息列表
        """
        db = None
        try:
            db = db_connection.get_session()
            
            messages = db.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.session_id == session_id
            ).order_by(ConversationHistory.timestamp.asc()).all()
            
            result = []
            for msg in messages:
                message_dict = {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                if msg.thinking:
                    message_dict["thinking"] = msg.thinking
                result.append(message_dict)
            
            return result
        except Exception as e:
            print(f"❌ 从数据库获取消息失败: {e}")
            return []
        finally:
            if db:
                db.close()
    
    @staticmethod
    def get_user_sessions(user_id: str) -> List[Dict]:
        """
        获取用户的所有会话列表
        
        Args:
            user_id: 用户ID
        
        Returns:
            会话列表
        """
        db = None
        try:
            db = db_connection.get_session()
            
            # 查询所有会话，按最后消息时间分组
            from sqlalchemy import func
            
            sessions = db.query(
                ConversationHistory.session_id,
                func.count(ConversationHistory.id).label('message_count'),
                func.max(ConversationHistory.timestamp).label('last_message_time')
            ).filter(
                ConversationHistory.user_id == user_id
            ).group_by(
                ConversationHistory.session_id
            ).order_by(
                func.max(ConversationHistory.timestamp).desc()
            ).all()
            
            result = []
            for session in sessions:
                # 获取第一条用户消息作为标题
                first_user_msg = db.query(ConversationHistory).filter(
                    ConversationHistory.user_id == user_id,
                    ConversationHistory.session_id == session.session_id,
                    ConversationHistory.role == 'user'
                ).order_by(ConversationHistory.timestamp.asc()).first()
                
                title = "新对话"
                if first_user_msg and first_user_msg.content:
                    title = first_user_msg.content[:30] + "..."
                
                # 获取最后一条消息作为预览
                last_msg = db.query(ConversationHistory).filter(
                    ConversationHistory.user_id == user_id,
                    ConversationHistory.session_id == session.session_id
                ).order_by(ConversationHistory.timestamp.desc()).first()
                
                preview = ""
                if last_msg and last_msg.content:
                    preview = last_msg.content[:50] + "..."
                
                result.append({
                    "id": session.session_id,
                    "title": title,
                    "preview": preview,
                    "message_count": session.message_count,
                    "last_message_time": session.last_message_time.isoformat()
                })
            
            return result
        except Exception as e:
            print(f"❌ 从数据库获取会话列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if db:
                db.close()
    
    @staticmethod
    def delete_session(user_id: str, session_id: str) -> bool:
        """
        删除指定会话的所有消息
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
        
        Returns:
            是否删除成功
        """
        db = None
        try:
            db = db_connection.get_session()
            
            db.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.session_id == session_id
            ).delete()
            
            db.commit()
            return True
        except Exception as e:
            print(f"❌ 删除会话失败: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
