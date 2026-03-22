"""
实时对话分析器
在用户发送消息时实时分析并存储洞察数据
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict
import json

from .conversation_analyzer import ConversationAnalyzer, ConversationInsight, DataType


class RealtimeInsightStorage:
    """实时洞察存储 - 将分析结果存入数据库"""
    
    @staticmethod
    def save_insights(user_id: str, insights: List[ConversationInsight], 
                     message_id: str = "") -> bool:
        """
        保存洞察到数据库
        
        Args:
            user_id: 用户ID
            insights: 洞察列表
            message_id: 关联的消息ID
        
        Returns:
            是否保存成功
        """
        if not insights:
            return True
            
        try:
            from backend.database.connection import db_connection
            from backend.database.models import UserInsight
            
            db = db_connection.get_session()
            
            for insight in insights:
                db_insight = UserInsight(
                    user_id=user_id,
                    insight_id=insight.insight_id,
                    data_type=insight.data_type.value,
                    category=insight.category,
                    content=insight.content,
                    value=insight.value,
                    confidence=insight.confidence,
                    source_message_id=insight.source_message_id or message_id,
                    extra_data=json.dumps(insight.metadata) if insight.metadata else None,
                    timestamp=insight.timestamp
                )
                db.add(db_insight)
            
            db.commit()
            db.close()
            
            print(f"[实时分析] 用户 {user_id} 保存了 {len(insights)} 条洞察")
            return True
            
        except Exception as e:
            print(f"[实时分析] 保存洞察失败: {e}")
            return False
    
    @staticmethod
    def get_user_insights(user_id: str, days: int = 30, 
                         category: str = None) -> List[Dict[str, Any]]:
        """
        获取用户的洞察数据
        
        Args:
            user_id: 用户ID
            days: 最近多少天
            category: 分类筛选
        
        Returns:
            洞察列表
        """
        try:
            from backend.database.connection import db_connection
            from backend.database.models import UserInsight
            from datetime import timedelta
            from sqlalchemy import and_
            
            db = db_connection.get_session()
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            query = db.query(UserInsight).filter(
                and_(
                    UserInsight.user_id == user_id,
                    UserInsight.timestamp >= cutoff
                )
            )
            
            if category:
                query = query.filter(UserInsight.category == category)
            
            results = query.order_by(UserInsight.timestamp.desc()).all()
            
            insights = []
            for r in results:
                insights.append({
                    "insight_id": r.insight_id,
                    "data_type": r.data_type,
                    "category": r.category,
                    "content": r.content,
                    "value": r.value,
                    "confidence": r.confidence,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "metadata": json.loads(r.extra_data) if r.extra_data else {}
                })
            
            db.close()
            return insights
            
        except Exception as e:
            print(f"[实时分析] 获取洞察失败: {e}")
            return []
    
    @staticmethod
    def get_emotion_trend(user_id: str, days: int = 14) -> List[Dict[str, Any]]:
        """获取情绪趋势（按天聚合）"""
        try:
            from backend.database.connection import db_connection
            from backend.database.models import UserInsight
            from datetime import timedelta
            from sqlalchemy import and_, func
            from collections import defaultdict
            
            db = db_connection.get_session()
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            results = db.query(UserInsight).filter(
                and_(
                    UserInsight.user_id == user_id,
                    UserInsight.data_type == "emotion",
                    UserInsight.timestamp >= cutoff,
                    UserInsight.value.isnot(None)
                )
            ).all()
            
            db.close()
            
            # 按天聚合
            daily_data = defaultdict(list)
            for r in results:
                if r.timestamp and r.value is not None:
                    day_key = r.timestamp.strftime("%Y-%m-%d")
                    daily_data[day_key].append(r.value)
            
            trend = []
            for day in sorted(daily_data.keys()):
                values = daily_data[day]
                trend.append({
                    "date": day,
                    "avg_emotion": sum(values) / len(values),
                    "count": len(values)
                })
            
            return trend
            
        except Exception as e:
            print(f"[实时分析] 获取情绪趋势失败: {e}")
            return []
    
    @staticmethod
    def get_topic_distribution(user_id: str, days: int = 7) -> Dict[str, int]:
        """获取话题分布"""
        try:
            from backend.database.connection import db_connection
            from backend.database.models import UserInsight
            from datetime import timedelta
            from sqlalchemy import and_
            from collections import defaultdict
            
            db = db_connection.get_session()
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            results = db.query(UserInsight).filter(
                and_(
                    UserInsight.user_id == user_id,
                    UserInsight.data_type == "topic",
                    UserInsight.timestamp >= cutoff
                )
            ).all()
            
            db.close()
            
            distribution = defaultdict(int)
            for r in results:
                distribution[r.category] += 1
            
            return dict(distribution)
            
        except Exception as e:
            print(f"[实时分析] 获取话题分布失败: {e}")
            return {}


# 全局分析器缓存
_analyzers: Dict[str, ConversationAnalyzer] = {}


def get_realtime_analyzer(user_id: str) -> ConversationAnalyzer:
    """获取用户的实时分析器"""
    if user_id not in _analyzers:
        _analyzers[user_id] = ConversationAnalyzer(user_id)
    return _analyzers[user_id]


def analyze_message_realtime(user_id: str, message: str, message_id: str = "",
                            metadata: Dict = None) -> List[Dict[str, Any]]:
    """
    实时分析用户消息并存储
    
    这个函数应该在用户发送消息时被调用
    
    Args:
        user_id: 用户ID
        message: 消息内容
        message_id: 消息ID
        metadata: 元数据（图像描述、语音情感等）
    
    Returns:
        提取的洞察列表
    """
    if not message or not message.strip():
        return []
    
    try:
        # 获取分析器
        analyzer = get_realtime_analyzer(user_id)
        
        # 分析消息
        insights = analyzer.analyze_message(
            message=message,
            role="user",
            message_id=message_id,
            metadata=metadata,
            timestamp=datetime.now()
        )
        
        # 存储到数据库
        if insights:
            RealtimeInsightStorage.save_insights(user_id, insights, message_id)
        
        # 返回结果
        return [
            {
                "insight_id": i.insight_id,
                "data_type": i.data_type.value,
                "category": i.category,
                "content": i.content,
                "value": i.value,
                "confidence": i.confidence
            }
            for i in insights
        ]
        
    except Exception as e:
        print(f"[实时分析] 分析消息失败: {e}")
        return []
