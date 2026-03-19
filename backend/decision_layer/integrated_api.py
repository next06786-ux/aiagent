"""
决策层完整集成 API
整合所有决策层功能的 REST API 端点
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/decision-layer", tags=["decision-layer"])


# ==================== 依赖注入 ====================

async def get_decision_layer_system():
    """获取决策层系统"""
    from backend.decision_layer import get_decision_layer_system
    return get_decision_layer_system()


async def get_real_data_bridge():
    """获取真实数据决策桥接器"""
    # 这里应该从应用上下文获取
    pass


# ==================== 综合决策 API ====================

@router.post("/comprehensive-analysis")
async def comprehensive_analysis(
    user_id: str,
    sensor_data: Optional[Dict[str, Any]] = None,
    health_data: Optional[Dict[str, Any]] = None,
    context_data: Optional[Dict[str, Any]] = None,
    decision_layer = Depends(get_decision_layer_system)
) -> Dict[str, Any]:
    """
    综合分析：结合传感器、健康和上下文数据生成决策
    
    Args:
        user_id: 用户ID
        sensor_data: 传感器数据
        health_data: 健康数据
        context_data: 上下文数据
    
    Returns:
        综合分析结果
    """
    try:
        if not decision_layer or not decision_layer.is_initialized():
            raise HTTPException(status_code=503, detail="Decision layer not initialized")
        
        decision_engine = decision_layer.get_decision_engine()
        all_decisions = []
        
        # 1. 分析传感器数据
        if sensor_data:
            from backend.decision_layer.decision_engine import HealthMetrics
            
            metrics = HealthMetrics(
                heart_rate=sensor_data.get('heart_rate', 0),
                blood_oxygen=sensor_data.get('blood_oxygen', 0),
                temperature=sensor_data.get('temperature', 0),
                blood_pressure_systolic=sensor_data.get('blood_pressure_systolic', 0),
                blood_pressure_diastolic=sensor_data.get('blood_pressure_diastolic', 0),
                sleep_hours=sensor_data.get('sleep_hours', 0),
                exercise_minutes=sensor_data.get('exercise_minutes', 0),
                stress_level=sensor_data.get('stress_level', 0)
            )
            
            sensor_decisions = decision_engine.analyze_health_metrics(user_id, metrics)
            all_decisions.extend(sensor_decisions)
        
        # 2. 分析上下文数据
        if context_data:
            context_decisions = decision_engine.analyze_context(user_id, context_data)
            all_decisions.extend(context_decisions)
        
        # 3. 排序和过滤
        ranked = decision_engine.rank_decisions(all_decisions)
        filtered = decision_engine.filter_decisions(ranked, max_count=10)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'total_decisions': len(all_decisions),
            'filtered_decisions': len(filtered),
            'decisions': [d.to_dict() for d in filtered],
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-harmonyos-data")
async def process_harmonyos_data(
    user_id: str,
    sensor_data: Dict[str, Any],
    real_data_bridge = Depends(get_real_data_bridge)
) -> Dict[str, Any]:
    """
    处理HarmonyOS前端传感器数据
    
    Args:
        user_id: 用户ID
        sensor_data: 传感器数据
            {
                'heart_rate': 72,
                'steps': 1250,
                'temperature': 36.8,
                'blood_oxygen': 97,
                'timestamp': '2026-03-15T10:30:00'
            }
    
    Returns:
        处理结果和生成的决策
    """
    try:
        decisions = real_data_bridge.process_harmonyos_sensor_data(user_id, sensor_data)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'decisions_generated': len(decisions),
            'decisions': [d.to_dict() for d in decisions],
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing HarmonyOS data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health-summary/{user_id}")
async def get_health_summary(
    user_id: str,
    days: int = Query(7, ge=1, le=365),
    real_data_bridge = Depends(get_real_data_bridge)
) -> Dict[str, Any]:
    """
    获取用户健康摘要
    
    Args:
        user_id: 用户ID
        days: 统计天数
    
    Returns:
        健康摘要
    """
    try:
        summary = real_data_bridge.get_user_health_summary(user_id, days)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting health summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cached-data/{user_id}")
async def get_cached_data(
    user_id: str,
    real_data_bridge = Depends(get_real_data_bridge)
) -> Dict[str, Any]:
    """
    获取缓存的最新数据
    
    Args:
        user_id: 用户ID
    
    Returns:
        缓存数据
    """
    try:
        cached_data = real_data_bridge.get_cached_latest_data(user_id)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'data': cached_data,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cached data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-graph/{user_id}")
async def query_knowledge_graph(
    user_id: str,
    query_type: str = Query("health_status"),
    real_data_bridge = Depends(get_real_data_bridge)
) -> Dict[str, Any]:
    """
    查询知识图谱
    
    Args:
        user_id: 用户ID
        query_type: 查询类型 (health_status, sensor_readings, relationships)
    
    Returns:
        查询结果
    """
    try:
        results = real_data_bridge.query_knowledge_graph(user_id, query_type)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'query_type': query_type,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error querying knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 数据分析 API ====================

@router.post("/daily-statistics")
async def calculate_daily_statistics(
    user_id: str,
    date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$"),
    analytics_service = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    计算每日统计
    
    Args:
        user_id: 用户ID
        date: 日期 (YYYY-MM-DD)
    
    Returns:
        每日统计
    """
    try:
        stats = analytics_service.calculate_daily_statistics(user_id, date)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'date': date,
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating daily statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/{user_id}")
async def detect_anomalies(
    user_id: str,
    days: int = Query(7, ge=1, le=365),
    analytics_service = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    检测异常数据
    
    Args:
        user_id: 用户ID
        days: 统计天数
    
    Returns:
        异常列表
    """
    try:
        anomalies = analytics_service.detect_anomalies(user_id, days)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'period_days': days,
            'anomalies_count': len(anomalies),
            'anomalies': anomalies,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend-analysis/{user_id}")
async def get_trend_analysis(
    user_id: str,
    metric: str = Query("heart_rate"),
    days: int = Query(30, ge=1, le=365),
    analytics_service = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    获取趋势分析
    
    Args:
        user_id: 用户ID
        metric: 指标 (heart_rate, temperature, blood_oxygen, steps)
        days: 统计天数
    
    Returns:
        趋势分析
    """
    try:
        trend = analytics_service.get_trend_analysis(user_id, metric, days)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'trend': trend,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting trend analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 通知 API ====================

@router.post("/send-health-alert")
async def send_health_alert(
    user_id: str,
    alert_type: str,
    message: str,
    severity: str = Query("high"),
    notification_service = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    发送健康警报
    
    Args:
        user_id: 用户ID
        alert_type: 警报类型
        message: 消息
        severity: 严重程度 (critical, high, medium, low)
    
    Returns:
        发送结果
    """
    try:
        notification_service.send_health_alert(user_id, alert_type, message, severity)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'alert_type': alert_type,
            'severity': severity,
            'message': 'Alert sent successfully',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error sending health alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-daily-summary")
async def send_daily_summary(
    user_id: str,
    summary: Dict[str, Any],
    notification_service = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    发送每日摘要
    
    Args:
        user_id: 用户ID
        summary: 摘要数据
    
    Returns:
        发送结果
    """
    try:
        notification_service.send_daily_summary(user_id, summary)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'message': 'Daily summary sent successfully',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error sending daily summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 系统状态 API ====================

@router.get("/status")
async def get_decision_layer_status(
    decision_layer = Depends(get_decision_layer_system)
) -> Dict[str, Any]:
    """
    获取决策层系统状态
    
    Returns:
        系统状态
    """
    try:
        if not decision_layer:
            return {
                'status': 'error',
                'initialized': False,
                'message': 'Decision layer not initialized'
            }
        
        return {
            'status': 'success',
            'initialized': decision_layer.is_initialized(),
            'components': {
                'decision_engine': decision_layer.get_decision_engine() is not None,
                'decision_executor': decision_layer.get_decision_executor() is not None,
                'sensor_collector': decision_layer.get_sensor_collector() is not None,
                'frontend_bridge': decision_layer.get_frontend_bridge() is not None
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize")
async def initialize_decision_layer(
    data_service = Depends(lambda: None),
    knowledge_graph = Depends(lambda: None),
    rl_agent = Depends(lambda: None),
    notification_service = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    初始化决策层系统
    
    Returns:
        初始化结果
    """
    try:
        from backend.decision_layer import initialize_decision_layer
        
        success = initialize_decision_layer(
            data_service,
            knowledge_graph,
            rl_agent,
            notification_service
        )
        
        return {
            'status': 'success' if success else 'failed',
            'initialized': success,
            'message': 'Decision layer initialized successfully' if success else 'Failed to initialize decision layer',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error initializing decision layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shutdown")
async def shutdown_decision_layer() -> Dict[str, Any]:
    """
    关闭决策层系统
    
    Returns:
        关闭结果
    """
    try:
        from backend.decision_layer import shutdown_decision_layer
        
        shutdown_decision_layer()
        
        return {
            'status': 'success',
            'message': 'Decision layer shut down successfully',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error shutting down decision layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

