"""
智能洞察 API
提供前端调用的接口

数据流程：
1. 用户发消息时 → 后端实时分析并存储洞察数据到数据库（realtime_analyzer）
2. 用户打开智能洞察页面时 → 读取已存储的数据，进行涌现发现分析
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .smart_insight_engine import (
    get_smart_insight_engine, 
    SmartInsight, 
    InsightLevel, 
    InsightCategory
)
from .conversation_analyzer import ConversationInsight
from .realtime_analyzer import RealtimeInsightStorage


router = APIRouter(prefix="/api/v1/insights", tags=["智能洞察"])


class MessageInput(BaseModel):
    """消息输入"""
    role: str = "user"
    content: str
    id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessMessagesRequest(BaseModel):
    """处理消息请求"""
    user_id: str
    messages: List[MessageInput]


class ProcessMessagesResponse(BaseModel):
    """处理消息响应"""
    success: bool
    insights_count: int
    insights: List[Dict[str, Any]]


class GenerateInsightsRequest(BaseModel):
    """生成洞察请求"""
    user_id: str


class InsightResponse(BaseModel):
    """洞察响应"""
    success: bool
    data: Dict[str, Any]


class DashboardResponse(BaseModel):
    """仪表盘响应"""
    success: bool
    data: Dict[str, Any]


@router.post("/process", response_model=ProcessMessagesResponse)
async def process_messages(request: ProcessMessagesRequest):
    """
    手动处理对话消息（一般不需要调用，消息会实时分析）
    """
    try:
        from .realtime_analyzer import analyze_message_realtime
        
        all_insights = []
        for msg in request.messages:
            insights = analyze_message_realtime(
                user_id=request.user_id,
                message=msg.content,
                message_id=msg.id or str(datetime.now().timestamp()),
                metadata=msg.metadata or {}
            )
            all_insights.extend(insights)
        
        return ProcessMessagesResponse(
            success=True,
            insights_count=len(all_insights),
            insights=all_insights
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=InsightResponse)
async def generate_insights(request: GenerateInsightsRequest):
    """
    生成智能洞察（涌现发现分析）
    """
    try:
        # 确保数据库表存在
        try:
            from backend.database.connection import db_connection
            from backend.database.models import Base
            from sqlalchemy import inspect
            engine = db_connection.engine
            Base.metadata.create_all(engine, checkfirst=True)
        except Exception as init_err:
            print(f"[洞察] 数据库表初始化: {init_err}")

        # 1. 从数据库读取已存储的洞察数据
        stored_insights = RealtimeInsightStorage.get_user_insights(
            request.user_id, days=30
        )
        
        if not stored_insights:
            # 尝试从对话历史中补充分析
            try:
                from backend.database.connection import db_connection
                from backend.database.models import ConversationHistory
                from sqlalchemy import and_
                from datetime import timedelta
                
                db = db_connection.get_session()
                cutoff = datetime.utcnow() - timedelta(days=30)
                recent_msgs = db.query(ConversationHistory).filter(
                    and_(
                        ConversationHistory.user_id == request.user_id,
                        ConversationHistory.role == "user",
                        ConversationHistory.timestamp >= cutoff
                    )
                ).order_by(ConversationHistory.timestamp.desc()).limit(50).all()
                db.close()
                
                if recent_msgs:
                    from .realtime_analyzer import analyze_message_realtime
                    for msg in recent_msgs:
                        analyze_message_realtime(
                            user_id=request.user_id,
                            message=msg.content,
                            message_id=str(msg.id) if hasattr(msg, 'id') else "",
                        )
                    # 重新读取
                    stored_insights = RealtimeInsightStorage.get_user_insights(
                        request.user_id, days=30
                    )
            except Exception as backfill_err:
                print(f"[洞察] 回填分析失败: {backfill_err}")
        
        if not stored_insights:
            return InsightResponse(
                success=True,
                data={
                    "total_insights": 0,
                    "insights": [],
                    "message": "暂无数据，请先与AI助手对话积累数据"
                }
            )
        
        # 2. 获取涌现分析引擎
        engine = get_smart_insight_engine(request.user_id)
        
        # 3. 将存储的洞察数据加载到引擎中
        engine.load_stored_insights(stored_insights)
        
        # 4. 进行涌现发现分析
        insights = engine.generate_insights()
        
        # 5. 保存生成的涌现洞察到数据库
        save_emergence_insights(request.user_id, insights)
        
        return InsightResponse(
            success=True,
            data={
                "total_insights": len(insights),
                "data_points_analyzed": len(stored_insights),
                "insights": [i.to_dict() for i in insights],
                "by_level": {
                    "critical": len([i for i in insights if i.level == InsightLevel.CRITICAL]),
                    "warning": len([i for i in insights if i.level == InsightLevel.WARNING]),
                    "suggestion": len([i for i in insights if i.level == InsightLevel.SUGGESTION]),
                    "info": len([i for i in insights if i.level == InsightLevel.INFO]),
                },
                "by_category": {
                    "cascade": len([i for i in insights if i.category == InsightCategory.CASCADE]),
                    "synergy": len([i for i in insights if i.category == InsightCategory.SYNERGY]),
                    "tipping_point": len([i for i in insights if i.category == InsightCategory.TIPPING_POINT]),
                    "feedback_loop": len([i for i in insights if i.category == InsightCategory.FEEDBACK_LOOP]),
                    "pattern": len([i for i in insights if i.category == InsightCategory.PATTERN]),
                }
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def save_emergence_insights(user_id: str, insights: List[SmartInsight]):
    """保存涌现洞察到数据库"""
    try:
        from backend.database.connection import db_connection
        from backend.database.models import EmergenceInsight
        import json
        
        db = db_connection.get_session()
        
        for insight in insights:
            try:
                db_insight = EmergenceInsight(
                    user_id=user_id,
                    insight_id=insight.insight_id,
                    category=insight.category.value,
                    level=insight.level.value,
                    title=insight.title,
                    description=insight.description,
                    evidence=json.dumps(insight.evidence) if insight.evidence else None,
                    recommendations=json.dumps(insight.recommendations) if insight.recommendations else None,
                    confidence=insight.confidence,
                    impact_score=insight.impact_score,
                    related_metrics=json.dumps(insight.related_metrics) if insight.related_metrics else None,
                    visualization_data=json.dumps(insight.visualization_data) if insight.visualization_data else None
                )
                db.merge(db_insight)
                db.flush()
            except Exception as item_err:
                db.rollback()
                # 跳过这条，继续下一条
                continue
        
        try:
            db.commit()
        except Exception:
            db.rollback()
        db.close()
        print(f"[涌现洞察] 保存了 {len(insights)} 条涌现洞察")
        
    except Exception as e:
        print(f"[涌现洞察] 保存失败: {e}")


@router.get("/dashboard/{user_id}", response_model=DashboardResponse)
async def get_dashboard(user_id: str, days: int = Query(30, description="分析最近多少天的数据")):
    """
    获取智能洞察仪表盘数据
    
    从数据库读取已存储的洞察数据，返回：
    - 情绪趋势
    - 话题分布
    - 涌现洞察统计
    - 顶级洞察列表
    """
    try:
        # 确保数据库表存在
        try:
            from backend.database.connection import db_connection as _dbc
            from backend.database.models import Base as _Base
            _engine = _dbc.engine
            _Base.metadata.create_all(_engine, checkfirst=True)
        except Exception:
            pass

        # 1. 获取情绪趋势
        emotion_trend = RealtimeInsightStorage.get_emotion_trend(user_id, days=14)
        
        # 2. 获取话题分布
        topic_distribution = RealtimeInsightStorage.get_topic_distribution(user_id, days=7)
        
        # 3. 获取已存储的洞察数据统计
        all_insights = RealtimeInsightStorage.get_user_insights(user_id, days=days)
        
        # 4. 获取已生成的涌现洞察
        emergence_insights = get_stored_emergence_insights(user_id)
        
        # 统计
        summary = {
            "total_insights": len(emergence_insights),
            "critical_count": len([i for i in emergence_insights if i.get("level") == "critical"]),
            "warning_count": len([i for i in emergence_insights if i.get("level") == "warning"]),
            "suggestion_count": len([i for i in emergence_insights if i.get("level") == "suggestion"]),
        }
        
        return DashboardResponse(
            success=True,
            data={
                "user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                "summary": summary,
                "emotion_trend": emotion_trend,
                "topic_distribution": topic_distribution,
                "top_insights": emergence_insights[:5],
                "data_points": len(all_insights),
                "analysis_period_days": days
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def get_stored_emergence_insights(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """获取已存储的涌现洞察"""
    try:
        from backend.database.connection import db_connection
        from backend.database.models import EmergenceInsight
        import json
        
        db = db_connection.get_session()
        
        results = db.query(EmergenceInsight).filter(
            EmergenceInsight.user_id == user_id,
            EmergenceInsight.status == 'active'
        ).order_by(EmergenceInsight.impact_score.desc()).limit(limit).all()
        
        insights = []
        for r in results:
            insights.append({
                "insight_id": r.insight_id,
                "category": r.category,
                "level": r.level,
                "title": r.title,
                "description": r.description,
                "evidence": json.loads(r.evidence) if r.evidence else [],
                "recommendations": json.loads(r.recommendations) if r.recommendations else [],
                "confidence": r.confidence,
                "impact_score": r.impact_score,
                "related_metrics": json.loads(r.related_metrics) if r.related_metrics else [],
                "visualization_data": json.loads(r.visualization_data) if r.visualization_data else {},
                "created_at": r.created_at.isoformat() if r.created_at else None
            })
        
        db.close()
        return insights
        
    except Exception as e:
        print(f"[涌现洞察] 获取失败: {e}")
        return []


@router.get("/list/{user_id}")
async def list_insights(
    user_id: str,
    level: Optional[str] = Query(None, description="筛选级别: critical, warning, suggestion, info"),
    category: Optional[str] = Query(None, description="筛选分类: cascade, synergy, tipping_point, feedback_loop, pattern, trend, anomaly"),
    limit: int = Query(10, description="返回数量限制")
):
    """
    获取洞察列表
    
    支持按级别和分类筛选
    """
    try:
        engine = get_smart_insight_engine(user_id)
        
        insights = engine.insights
        
        # 按级别筛选
        if level:
            try:
                level_enum = InsightLevel(level)
                insights = [i for i in insights if i.level == level_enum]
            except ValueError:
                pass
        
        # 按分类筛选
        if category:
            try:
                category_enum = InsightCategory(category)
                insights = [i for i in insights if i.category == category_enum]
            except ValueError:
                pass
        
        # 限制数量
        insights = insights[:limit]
        
        return {
            "success": True,
            "total": len(insights),
            "insights": [i.to_dict() for i in insights]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotion-trend/{user_id}")
async def get_emotion_trend(user_id: str, days: int = Query(14, description="天数")):
    """
    获取情绪趋势
    """
    try:
        engine = get_smart_insight_engine(user_id)
        trend = engine.conversation_analyzer.get_emotion_trend(days=days)
        
        return {
            "success": True,
            "data": trend
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topic-distribution/{user_id}")
async def get_topic_distribution(user_id: str, days: int = Query(7, description="天数")):
    """
    获取话题分布
    """
    try:
        engine = get_smart_insight_engine(user_id)
        distribution = engine.conversation_analyzer.get_topic_distribution(days=days)
        
        return {
            "success": True,
            "data": distribution
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-single")
async def analyze_single_message(
    user_id: str,
    content: str,
    role: str = "user",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    分析单条消息
    
    实时分析用户发送的消息，提取情绪、话题、意图等
    """
    try:
        engine = get_smart_insight_engine(user_id)
        
        insights = engine.conversation_analyzer.analyze_message(
            message=content,
            role=role,
            message_id=str(datetime.now().timestamp()),
            metadata=metadata or {}
        )
        
        return {
            "success": True,
            "insights": [
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
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
