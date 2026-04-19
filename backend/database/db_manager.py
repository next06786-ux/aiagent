"""
数据库管理器
负责数据持久化和查询
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from .models import (
    db, User, VisualMemory, HealthRecord, 
    TimeRecord, Prediction, EmergentPattern
)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.db = db
        # 延迟创建表，避免启动时阻塞
        self._tables_created = False
    
    def _ensure_tables(self):
        """确保表已创建（延迟初始化）"""
        if not self._tables_created:
            try:
                self.db.create_tables()
                self._tables_created = True
            except Exception as e:
                print(f"⚠️ 数据库表创建失败: {e}")
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        self._ensure_tables()
        return self.db.get_session()
    
    # ========== 用户管理 ==========
    
    def create_user(self, user_id: str) -> User:
        """创建用户"""
        session = self.get_session()
        try:
            user = User(id=user_id)
            session.add(user)
            session.commit()
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()
    
    # ========== 健康记录 ==========
    
    def save_health_record(self, user_id: str, data: Dict) -> HealthRecord:
        """保存健康记录"""
        session = self.get_session()
        try:
            record = HealthRecord(
                user_id=user_id,
                sleep_hours=data.get('sleep_hours', 0),
                sleep_quality=data.get('sleep_quality', 0),
                steps=data.get('steps', 0),
                heart_rate=data.get('heart_rate', 0),
                exercise_minutes=data.get('exercise_minutes', 0),
                stress_level=data.get('stress_level', 0),
                health_score=data.get('health_score', 0)
            )
            session.add(record)
            session.commit()
            session.refresh(record)  # 刷新对象以获取ID
            record_id = record.id  # 在Session关闭前获取ID
            session.expunge(record)  # 从Session中分离对象
            return record
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_health_records(
        self, 
        user_id: str, 
        limit: int = 100
    ) -> List[HealthRecord]:
        """获取健康记录"""
        session = self.get_session()
        try:
            return session.query(HealthRecord)\
                .filter(HealthRecord.user_id == user_id)\
                .order_by(HealthRecord.timestamp.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    # ========== 视觉记忆 ==========
    
    def save_visual_memory(self, user_id: str, memory_data: Dict) -> VisualMemory:
        """保存视觉记忆"""
        session = self.get_session()
        try:
            memory = VisualMemory(
                user_id=user_id,
                features=memory_data.get('features'),
                scene=memory_data.get('scene'),
                objects=memory_data.get('objects'),
                activities=memory_data.get('activities'),
                timestamp=memory_data.get('timestamp'),
                location_lat=memory_data.get('location', {}).get('lat'),
                location_lng=memory_data.get('location', {}).get('lng'),
                confidence=memory_data.get('confidence', 1.0)
            )
            session.add(memory)
            session.commit()
            session.refresh(memory)  # 刷新对象以获取ID
            session.expunge(memory)  # 从Session中分离对象
            return memory
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_visual_memories(
        self, 
        user_id: str, 
        limit: int = 100
    ) -> List[VisualMemory]:
        """获取视觉记忆"""
        session = self.get_session()
        try:
            return session.query(VisualMemory)\
                .filter(VisualMemory.user_id == user_id)\
                .order_by(VisualMemory.timestamp.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    # ========== 预测记录 ==========
    
    def save_prediction(
        self, 
        user_id: str, 
        prediction_type: str,
        time_horizon: str,
        prediction_data: Dict,
        confidence: float
    ) -> Prediction:
        """保存预测"""
        session = self.get_session()
        try:
            prediction = Prediction(
                user_id=user_id,
                prediction_type=prediction_type,
                time_horizon=time_horizon,
                prediction_data=prediction_data,
                confidence=confidence
            )
            session.add(prediction)
            session.commit()
            session.refresh(prediction)
            session.expunge(prediction)
            return prediction
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_predictions(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Prediction]:
        """获取预测记录"""
        session = self.get_session()
        try:
            return session.query(Prediction)\
                .filter(Prediction.user_id == user_id)\
                .order_by(Prediction.created_at.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    # ========== 涌现模式 ==========
    
    def save_emergent_pattern(
        self, 
        user_id: str, 
        pattern_data: Dict
    ) -> EmergentPattern:
        """保存涌现模式"""
        session = self.get_session()
        try:
            pattern = EmergentPattern(
                user_id=user_id,
                pattern_type=pattern_data.get('pattern_type'),
                domain=pattern_data.get('domain'),
                description=pattern_data.get('description'),
                confidence=pattern_data.get('confidence'),
                impact_score=pattern_data.get('impact_score'),
                involved_agents=pattern_data.get('involved_agents'),
                details=pattern_data.get('details')
            )
            session.add(pattern)
            session.commit()
            session.refresh(pattern)
            session.expunge(pattern)
            return pattern
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_emergent_patterns(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[EmergentPattern]:
        """获取涌现模式"""
        session = self.get_session()
        try:
            return session.query(EmergentPattern)\
                .filter(EmergentPattern.user_id == user_id)\
                .order_by(EmergentPattern.detected_at.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()

    # ==================== 对话历史管理 ====================
    
    def save_conversation(self, user_id: str, role: str, content: str, 
                         context: Optional[Dict] = None, thinking: Optional[str] = None,
                         session_id: Optional[str] = None):
        """保存对话记录"""
        from .models import ConversationHistory
        
        session = self.get_session()
        try:
            conversation = ConversationHistory(
                user_id=user_id,
                role=role,
                content=content,
                thinking=thinking,
                context=context,
                session_id=session_id
            )
            
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            session.expunge(conversation)
            return conversation
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_conversation_history(self, user_id: str, limit: int = 50, session_id: Optional[str] = None):
        """获取对话历史"""
        from .models import ConversationHistory
        
        session = self.get_session()
        try:
            query = session.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id
            )
            
            if session_id:
                query = query.filter(ConversationHistory.session_id == session_id)
            
            return query.order_by(ConversationHistory.timestamp.desc()).limit(limit).all()
        finally:
            session.close()
    
    def update_conversation_feedback(self, user_id: str, session_id: str,
                                    rating: int, helpful: bool, action_taken: bool):
        """更新对话反馈"""
        from .models import ConversationHistory
        
        session = self.get_session()
        try:
            # 找到该会话的最后一条assistant消息
            conversation = session.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.session_id == session_id,
                ConversationHistory.role == 'assistant'
            ).order_by(ConversationHistory.timestamp.desc()).first()
            
            if conversation:
                conversation.rating = rating
                conversation.helpful = helpful
                conversation.action_taken = action_taken
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # ==================== 用户配置管理 ====================
    
    def get_user_config(self, user_id: str):
        """获取用户配置"""
        from .models import UserConfig
        
        session = self.get_session()
        try:
            config = session.query(UserConfig).filter(
                UserConfig.user_id == user_id
            ).first()
            
            if not config:
                # 创建默认配置
                config = UserConfig(user_id=user_id)
                session.add(config)
                session.commit()
                session.refresh(config)
                session.expunge(config)
            
            return config
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_user_config(self, user_id: str, **kwargs):
        """更新用户配置"""
        from .models import UserConfig
        
        session = self.get_session()
        try:
            config = self.get_user_config(user_id)
            
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            session.commit()
            session.refresh(config)
            session.expunge(config)
            return config
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # ==================== 进化指标管理 ====================
    
    def save_evolution_metrics(self, user_id: str, total_samples: int,
                              confidence_score: float, accuracy: float,
                              domain_metrics: Dict, recommended_strategy: str):
        """保存进化指标"""
        from .models import EvolutionMetrics
        
        session = self.get_session()
        try:
            metrics = EvolutionMetrics(
                user_id=user_id,
                total_samples=total_samples,
                confidence_score=confidence_score,
                accuracy=accuracy,
                domain_metrics=domain_metrics,
                recommended_strategy=recommended_strategy
            )
            
            session.add(metrics)
            session.commit()
            session.refresh(metrics)
            session.expunge(metrics)
            return metrics
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_latest_evolution_metrics(self, user_id: str):
        """获取最新的进化指标"""
        from .models import EvolutionMetrics
        
        session = self.get_session()
        try:
            return session.query(EvolutionMetrics).filter(
                EvolutionMetrics.user_id == user_id
            ).order_by(EvolutionMetrics.timestamp.desc()).first()
        finally:
            session.close()
    
    def get_latest_predictions(self, user_id: str, limit: int = 5):
        """获取最新的预测"""
        from .models import Prediction
        
        session = self.get_session()
        try:
            return session.query(Prediction).filter(
                Prediction.user_id == user_id
            ).order_by(Prediction.created_at.desc()).limit(limit).all()
        finally:
            session.close()
    
    def get_active_users(self, days: int = 7) -> List[User]:
        """
        获取活跃用户列表
        
        Args:
            days: 最近N天内有活动的用户
        
        Returns:
            活跃用户列表
        """
        from datetime import timedelta
        
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 查询最近有健康记录的用户
            active_user_ids = session.query(HealthRecord.user_id)\
                .filter(HealthRecord.timestamp >= cutoff_date)\
                .distinct()\
                .all()
            
            # 获取用户对象
            user_ids = [uid[0] for uid in active_user_ids]
            users = session.query(User).filter(User.id.in_(user_ids)).all()
            
            return users
        finally:
            session.close()
    
    def get_users_with_recent_updates(self, hours: int = 1) -> List[User]:
        """
        获取最近有数据更新的用户
        
        Args:
            hours: 最近N小时内有更新的用户
        
        Returns:
            有更新的用户列表
        """
        from datetime import timedelta
        
        session = self.get_session()
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 查询最近有健康记录更新的用户
            updated_user_ids = session.query(HealthRecord.user_id)\
                .filter(HealthRecord.timestamp >= cutoff_time)\
                .distinct()\
                .all()
            
            # 获取用户对象
            user_ids = [uid[0] for uid in updated_user_ids]
            users = session.query(User).filter(User.id.in_(user_ids)).all()
            
            return users
        finally:
            session.close()


# 全局数据库管理器实例
db_manager = DatabaseManager()
