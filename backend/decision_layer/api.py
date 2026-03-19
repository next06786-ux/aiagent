"""
决策层 API 接口
提供决策相关的 REST API 端点
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/decisions", tags=["decisions"])


# ==================== 数据模型 ====================

class HealthMetricsRequest:
    """健康指标请求"""
    def __init__(self, heart_rate: float, blood_oxygen: float, temperature: float,
                 blood_pressure_systolic: float, blood_pressure_diastolic: float,
                 sleep_hours: float, exercise_minutes: int, stress_level: float):
        self.heart_rate = heart_rate
        self.blood_oxygen = blood_oxygen
        self.temperature = temperature
        self.blood_pressure_systolic = blood_pressure_systolic
        self.blood_pressure_diastolic = blood_pressure_diastolic
        self.sleep_hours = sleep_hours
        self.exercise_minutes = exercise_minutes
        self.stress_level = stress_level


class ContextRequest:
    """上下文请求"""
    def __init__(self, work_hours: float = 0, social_interaction_hours: float = 0,
                 meal_count: int = 0, location: str = "", activity: str = ""):
        self.work_hours = work_hours
        self.social_interaction_hours = social_interaction_hours
        self.meal_count = meal_count
        self.location = location
        self.activity = activity


class DecisionResponse:
    """决策响应"""
    def __init__(self, decision_dict: Dict[str, Any]):
        self.decision_id = decision_dict.get('decision_id')
        self.user_id = decision_dict.get('user_id')
        self.decision_type = decision_dict.get('decision_type')
        self.priority = decision_dict.get('priority')
        self.recommendation = decision_dict.get('recommendation')
        self.reasoning = decision_dict.get('reasoning')
        self.confidence = decision_dict.get('confidence')
        self.expected_impact = decision_dict.get('expected_impact')
        self.created_at = decision_dict.get('created_at')


# ==================== 依赖注入 ====================

async def get_decision_engine():
    """获取决策引擎"""
    # 这里应该从应用上下文获取
    from backend.decision_layer.decision_engine import DecisionEngine
    # 返回已初始化的决策引擎实例
    pass


async def get_decision_executor():
    """获取决策执行器"""
    from backend.decision_layer.decision_engine import DecisionExecutor
    # 返回已初始化的决策执行器实例
    pass


# ==================== API 端点 ====================

@router.post("/analyze-health")
async def analyze_health_metrics(
    user_id: str,
    heart_rate: float,
    blood_oxygen: float,
    temperature: float,
    blood_pressure_systolic: float,
    blood_pressure_diastolic: float,
    sleep_hours: float,
    exercise_minutes: int,
    stress_level: float,
    decision_engine = Depends(get_decision_engine)
) -> Dict[str, Any]:
    """
    分析健康指标并生成决策
    
    Args:
        user_id: 用户ID
        heart_rate: 心率 (bpm)
        blood_oxygen: 血氧 (%)
        temperature: 体温 (°C)
        blood_pressure_systolic: 收缩压 (mmHg)
        blood_pressure_diastolic: 舒张压 (mmHg)
        sleep_hours: 睡眠时间 (小时)
        exercise_minutes: 运动时间 (分钟)
        stress_level: 压力水平 (0-100)
    
    Returns:
        决策列表
    """
    try:
        from backend.decision_layer.decision_engine import HealthMetrics
        
        metrics = HealthMetrics(
            heart_rate=heart_rate,
            blood_oxygen=blood_oxygen,
            temperature=temperature,
            blood_pressure_systolic=blood_pressure_systolic,
            blood_pressure_diastolic=blood_pressure_diastolic,
            sleep_hours=sleep_hours,
            exercise_minutes=exercise_minutes,
            stress_level=stress_level
        )
        
        decisions = decision_engine.analyze_health_metrics(user_id, metrics)
        filtered_decisions = decision_engine.filter_decisions(decisions)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'decisions': [d.to_dict() for d in filtered_decisions],
            'count': len(filtered_decisions),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error analyzing health metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-context")
async def analyze_context(
    user_id: str,
    work_hours: float = Query(0),
    social_interaction_hours: float = Query(0),
    meal_count: int = Query(0),
    location: str = Query(""),
    activity: str = Query(""),
    decision_engine = Depends(get_decision_engine)
) -> Dict[str, Any]:
    """
    基于上下文分析生成决策
    
    Args:
        user_id: 用户ID
        work_hours: 工作时间 (小时)
        social_interaction_hours: 社交互动时间 (小时)
        meal_count: 进食次数
        location: 位置
        activity: 活动
    
    Returns:
        决策列表
    """
    try:
        context = {
            'work_hours': work_hours,
            'social_interaction_hours': social_interaction_hours,
            'meal_count': meal_count,
            'location': location,
            'activity': activity,
            'timestamp': datetime.now().isoformat()
        }
        
        decisions = decision_engine.analyze_context(user_id, context)
        filtered_decisions = decision_engine.filter_decisions(decisions)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'decisions': [d.to_dict() for d in filtered_decisions],
            'count': len(filtered_decisions),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error analyzing context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/{user_id}")
async def get_user_decisions(
    user_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    decision_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    data_service = Depends(lambda: None)  # 应该注入数据服务
) -> Dict[str, Any]:
    """
    获取用户的决策历史
    
    Args:
        user_id: 用户ID
        limit: 返回数量限制
        offset: 偏移量
        decision_type: 决策类型过滤
        priority: 优先级过滤
    
    Returns:
        决策列表
    """
    try:
        # 这里应该从数据库查询
        decisions = []
        
        return {
            'status': 'success',
            'user_id': user_id,
            'decisions': decisions,
            'total': len(decisions),
            'limit': limit,
            'offset': offset
        }
    except Exception as e:
        logger.error(f"Error getting user decisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/{decision_id}")
async def get_decision_details(
    decision_id: str,
    data_service = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    获取决策详情
    
    Args:
        decision_id: 决策ID
    
    Returns:
        决策详情
    """
    try:
        # 这里应该从数据库查询
        decision = None
        
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        return {
            'status': 'success',
            'decision': decision
        }
    except Exception as e:
        logger.error(f"Error getting decision details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decisions/{decision_id}/feedback")
async def submit_decision_feedback(
    decision_id: str,
    feedback: str,
    rating: int = Query(1, ge=1, le=5),
    actual_impact: Optional[Dict[str, Any]] = None,
    decision_engine = Depends(get_decision_engine),
    decision_executor = Depends(get_decision_executor)
) -> Dict[str, Any]:
    """
    提交决策反馈
    
    Args:
        decision_id: 决策ID
        feedback: 反馈文本
        rating: 评分 (1-5)
        actual_impact: 实际影响
    
    Returns:
        反馈提交结果
    """
    try:
        decision_engine.update_decision_with_feedback(
            decision_id,
            feedback,
            actual_impact or {}
        )
        
        return {
            'status': 'success',
            'decision_id': decision_id,
            'message': 'Feedback submitted successfully',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decisions/{decision_id}/execute")
async def execute_decision(
    decision_id: str,
    decision_executor = Depends(get_decision_executor)
) -> Dict[str, Any]:
    """
    执行决策
    
    Args:
        decision_id: 决策ID
    
    Returns:
        执行结果
    """
    try:
        # 这里应该从缓存或数据库获取决策
        decision = None
        
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        success = decision_executor.execute_decision(decision)
        
        return {
            'status': 'success' if success else 'failed',
            'decision_id': decision_id,
            'message': 'Decision executed successfully' if success else 'Failed to execute decision',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{user_id}")
async def get_decision_statistics(
    user_id: str,
    days: int = Query(7, ge=1, le=365),
    data_service = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    获取决策统计信息
    
    Args:
        user_id: 用户ID
        days: 统计天数
    
    Returns:
        统计信息
    """
    try:
        # 这里应该从数据库查询统计数据
        stats = {
            'total_decisions': 0,
            'decisions_by_type': {},
            'decisions_by_priority': {},
            'average_confidence': 0,
            'user_feedback_count': 0,
            'average_rating': 0
        }
        
        return {
            'status': 'success',
            'user_id': user_id,
            'period_days': days,
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{user_id}")
async def get_personalized_recommendations(
    user_id: str,
    limit: int = Query(5, ge=1, le=20),
    decision_engine = Depends(get_decision_engine)
) -> Dict[str, Any]:
    """
    获取个性化建议
    
    Args:
        user_id: 用户ID
        limit: 建议数量限制
    
    Returns:
        个性化建议列表
    """
    try:
        # 这里应该基于用户历史和当前状态生成建议
        recommendations = []
        
        return {
            'status': 'success',
            'user_id': user_id,
            'recommendations': recommendations,
            'count': len(recommendations),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze")
async def batch_analyze_decisions(
    user_id: str,
    health_metrics: Dict[str, Any],
    context: Dict[str, Any],
    decision_engine = Depends(get_decision_engine)
) -> Dict[str, Any]:
    """
    批量分析健康指标和上下文，生成综合决策
    
    Args:
        user_id: 用户ID
        health_metrics: 健康指标
        context: 上下文信息
    
    Returns:
        综合决策列表
    """
    try:
        from backend.decision_layer.decision_engine import HealthMetrics
        
        # 解析健康指标
        metrics = HealthMetrics(
            heart_rate=health_metrics.get('heart_rate', 0),
            blood_oxygen=health_metrics.get('blood_oxygen', 0),
            temperature=health_metrics.get('temperature', 0),
            blood_pressure_systolic=health_metrics.get('blood_pressure_systolic', 0),
            blood_pressure_diastolic=health_metrics.get('blood_pressure_diastolic', 0),
            sleep_hours=health_metrics.get('sleep_hours', 0),
            exercise_minutes=health_metrics.get('exercise_minutes', 0),
            stress_level=health_metrics.get('stress_level', 0)
        )
        
        # 分析健康指标
        health_decisions = decision_engine.analyze_health_metrics(user_id, metrics)
        
        # 分析上下文
        context_decisions = decision_engine.analyze_context(user_id, context)
        
        # 合并并过滤决策
        all_decisions = health_decisions + context_decisions
        filtered_decisions = decision_engine.filter_decisions(all_decisions, max_count=10)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'decisions': [d.to_dict() for d in filtered_decisions],
            'count': len(filtered_decisions),
            'health_decisions_count': len(health_decisions),
            'context_decisions_count': len(context_decisions),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

