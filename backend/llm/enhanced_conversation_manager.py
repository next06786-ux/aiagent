"""
增强对话管理器 - 支持数据库持久化和健康数据集成
Enhanced Conversation Manager with DB persistence and health data integration
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from .llm_service import get_llm_service


class EnhancedConversationManager:
    """
    增强对话管理器
    - 支持对话历史持久化
    - 集成用户健康数据
    - 提供上下文感知对话
    - 支持多用户独立对话历史
    """
    
    def __init__(self, user_id: str = "default_user", use_db: bool = True, session_id: Optional[str] = None):
        self.user_id = user_id
        self.llm = get_llm_service()
        self.conversation_history = []
        self.session_id = session_id or str(uuid.uuid4())
        self.use_db = use_db
        
        # 如果使用数据库，加载历史对话
        if self.use_db:
            self._load_history_from_db()
    
    def _load_history_from_db(self):
        """从数据库加载对话历史（仅加载当前会话）"""
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            
            # 只加载当前会话的对话历史
            history = db.get_conversation_history(self.user_id, limit=50, session_id=self.session_id)
            
            # 按时间正序排列（最早的在前）
            history.reverse()
            
            for record in history:
                self.conversation_history.append({
                    'role': record.role,
                    'content': record.content,
                    'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                    'thinking': record.thinking
                })
                
        except Exception as e:
            print(f"加载对话历史失败: {e}")
    
    def _save_to_db(self, role: str, content: str, context: Optional[Dict] = None, thinking: Optional[str] = None):
        """保存对话到数据库"""
        if not self.use_db:
            return
            
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            
            db.save_conversation(
                user_id=self.user_id,
                role=role,
                content=content,
                context=context,
                thinking=thinking,
                session_id=self.session_id
            )
        except Exception as e:
            print(f"保存对话失败: {e}")
    
    def _get_user_health_data(self) -> Optional[Dict]:
        """获取用户健康数据"""
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            
            # 获取最近7天的健康数据
            health_records = db.get_health_records(self.user_id, days=7)
            
            if not health_records:
                return None
            
            # 汇总数据
            summary = {
                'total_records': len(health_records),
                'avg_sleep_hours': sum(r.sleep_hours or 0 for r in health_records) / len(health_records),
                'avg_exercise_minutes': sum(r.exercise_minutes or 0 for r in health_records) / len(health_records),
                'avg_stress_level': sum(r.stress_level or 0 for r in health_records) / len(health_records),
                'latest_record': {
                    'date': health_records[-1].date.isoformat(),
                    'sleep_hours': health_records[-1].sleep_hours,
                    'exercise_minutes': health_records[-1].exercise_minutes,
                    'stress_level': health_records[-1].stress_level,
                    'mood': health_records[-1].mood
                }
            }
            
            return summary
            
        except Exception as e:
            print(f"获取健康数据失败: {e}")
            return None
    
    def _get_user_predictions(self) -> Optional[Dict]:
        """获取用户预测数据"""
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            
            # 获取最新的预测
            predictions = db.get_latest_predictions(self.user_id, limit=5)
            
            if not predictions:
                return None
            
            return {
                'total_predictions': len(predictions),
                'predictions': [
                    {
                        'domain': p.domain,
                        'description': p.description,
                        'confidence': p.confidence,
                        'time_horizon': p.time_horizon
                    }
                    for p in predictions
                ]
            }
            
        except Exception as e:
            print(f"获取预测数据失败: {e}")
            return None
    
    def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        对话
        
        Args:
            message: 用户消息
            context: 额外的上下文信息
            
        Returns:
            AI回复
        """
        # 构建增强上下文
        enhanced_context = context or {}
        
        # 添加健康数据
        health_data = self._get_user_health_data()
        if health_data:
            enhanced_context['health_data'] = health_data
        
        # 添加预测数据
        predictions = self._get_user_predictions()
        if predictions:
            enhanced_context['predictions'] = predictions
        
        # 添加对话历史（最近10条）
        if len(self.conversation_history) > 0:
            enhanced_context['recent_conversation'] = self.conversation_history[-10:]
        
        # 保存用户消息
        self.conversation_history.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        self._save_to_db('user', message, enhanced_context)
        
        # 构建系统提示
        system_prompt = self._build_system_prompt(enhanced_context)
        
        # 调用LLM
        response = self.llm.chat(
            message=message,
            system_prompt=system_prompt,
            context=enhanced_context
        )
        
        # 保存AI回复
        self.conversation_history.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        self._save_to_db('assistant', response, enhanced_context)
        
        return response
    
    def _build_system_prompt(self, context: Dict) -> str:
        """构建系统提示"""
        prompt_parts = [
            "你是LifeSwarm AI助手，专注于帮助用户管理健康和生活。",
            ""
        ]
        
        # 添加健康数据上下文
        if 'health_data' in context:
            health = context['health_data']
            prompt_parts.append("用户健康数据：")
            prompt_parts.append(f"- 最近7天平均睡眠：{health['avg_sleep_hours']:.1f}小时")
            prompt_parts.append(f"- 最近7天平均运动：{health['avg_exercise_minutes']:.0f}分钟")
            prompt_parts.append(f"- 最近7天平均压力：{health['avg_stress_level']:.1f}/10")
            
            latest = health['latest_record']
            prompt_parts.append(f"\n最新记录（{latest['date']}）：")
            prompt_parts.append(f"- 睡眠：{latest['sleep_hours']}小时")
            prompt_parts.append(f"- 运动：{latest['exercise_minutes']}分钟")
            prompt_parts.append(f"- 压力：{latest['stress_level']}/10")
            prompt_parts.append(f"- 心情：{latest['mood']}")
            prompt_parts.append("")
        
        # 添加预测数据上下文
        if 'predictions' in context:
            preds = context['predictions']
            prompt_parts.append("系统预测：")
            for pred in preds['predictions'][:3]:  # 只显示前3个
                prompt_parts.append(f"- {pred['description']} (置信度: {pred['confidence']:.0%})")
            prompt_parts.append("")
        
        prompt_parts.append("请基于以上数据，提供个性化的建议和分析。")
        
        return "\n".join(prompt_parts)
    
    def analyze_health_data(self) -> str:
        """分析用户健康数据"""
        health_data = self._get_user_health_data()
        
        if not health_data:
            return "暂无健康数据可供分析。请先输入一些健康数据。"
        
        # 构建分析请求
        analysis_request = f"""
请分析以下健康数据：

最近7天平均：
- 睡眠：{health_data['avg_sleep_hours']:.1f}小时
- 运动：{health_data['avg_exercise_minutes']:.0f}分钟
- 压力：{health_data['avg_stress_level']:.1f}/10

最新记录：
- 睡眠：{health_data['latest_record']['sleep_hours']}小时
- 运动：{health_data['latest_record']['exercise_minutes']}分钟
- 压力：{health_data['latest_record']['stress_level']}/10
- 心情：{health_data['latest_record']['mood']}

请提供：
1. 健康状况评估
2. 发现的问题
3. 改善建议
"""
        
        return self.chat(analysis_request)
    
    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history
    
    def clear_history(self):
        """清空对话历史（开始新会话）"""
        self.conversation_history = []
        self.session_id = str(uuid.uuid4())
    
    def get_all_sessions(self) -> List[Dict]:
        """获取用户的所有会话列表"""
        if not self.use_db:
            return []
        
        try:
            from database.db_manager import DatabaseManager
            from database.models import ConversationHistory
            from sqlalchemy import func
            
            db = DatabaseManager()
            session = db.get_session()
            
            # 按session_id分组，获取每个会话的第一条消息和最后一条消息
            sessions = session.query(
                ConversationHistory.session_id,
                func.min(ConversationHistory.timestamp).label('start_time'),
                func.max(ConversationHistory.timestamp).label('last_time'),
                func.count(ConversationHistory.id).label('message_count')
            ).filter(
                ConversationHistory.user_id == self.user_id
            ).group_by(
                ConversationHistory.session_id
            ).order_by(
                func.max(ConversationHistory.timestamp).desc()
            ).all()
            
            result = []
            for sess in sessions:
                # 获取第一条用户消息作为会话标题
                first_message = session.query(ConversationHistory).filter(
                    ConversationHistory.user_id == self.user_id,
                    ConversationHistory.session_id == sess.session_id,
                    ConversationHistory.role == 'user'
                ).order_by(ConversationHistory.timestamp.asc()).first()
                
                title = first_message.content[:50] + '...' if first_message and len(first_message.content) > 50 else (first_message.content if first_message else '新对话')
                
                result.append({
                    'session_id': sess.session_id,
                    'title': title,
                    'start_time': sess.start_time.isoformat() if sess.start_time else None,
                    'last_time': sess.last_time.isoformat() if sess.last_time else None,
                    'message_count': sess.message_count,
                    'is_current': sess.session_id == self.session_id
                })
            
            session.close()
            return result
            
        except Exception as e:
            print(f"获取会话列表失败: {e}")
            return []
    
    def load_session(self, session_id: str):
        """加载指定会话"""
        self.session_id = session_id
        self.conversation_history = []
        self._load_history_from_db()
    
    def delete_session(self, session_id: str):
        """删除指定会话"""
        if not self.use_db:
            return
        
        try:
            from database.db_manager import DatabaseManager
            from database.models import ConversationHistory
            
            db = DatabaseManager()
            session = db.get_session()
            
            # 删除该会话的所有消息
            session.query(ConversationHistory).filter(
                ConversationHistory.user_id == self.user_id,
                ConversationHistory.session_id == session_id
            ).delete()
            
            session.commit()
            session.close()
            
            # 如果删除的是当前会话，创建新会话
            if session_id == self.session_id:
                self.clear_history()
                
        except Exception as e:
            print(f"删除会话失败: {e}")
    
    def submit_feedback(self, rating: int, helpful: bool, action_taken: bool, comments: Optional[str] = None):
        """提交反馈"""
        if not self.use_db or len(self.conversation_history) == 0:
            return
        
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            
            # 更新最后一条AI回复的反馈
            db.update_conversation_feedback(
                user_id=self.user_id,
                session_id=self.session_id,
                rating=rating,
                helpful=helpful,
                action_taken=action_taken
            )
            
        except Exception as e:
            print(f"提交反馈失败: {e}")


# 全局实例管理
_conversation_managers = {}


def get_conversation_manager(user_id: str = "default_user", session_id: Optional[str] = None) -> EnhancedConversationManager:
    """
    获取对话管理器实例
    
    Args:
        user_id: 用户ID
        session_id: 会话ID（可选，如果不提供则使用该用户的当前会话）
    
    Returns:
        对话管理器实例
    """
    # 如果指定了session_id，创建新的管理器实例
    if session_id:
        return EnhancedConversationManager(user_id, session_id=session_id)
    
    # 否则使用缓存的实例
    if user_id not in _conversation_managers:
        _conversation_managers[user_id] = EnhancedConversationManager(user_id)
    return _conversation_managers[user_id]


def clear_conversation_manager_cache(user_id: str = None):
    """
    清除对话管理器缓存
    
    Args:
        user_id: 用户ID（可选，如果不提供则清除所有缓存）
    """
    global _conversation_managers
    if user_id:
        _conversation_managers.pop(user_id, None)
    else:
        _conversation_managers = {}
