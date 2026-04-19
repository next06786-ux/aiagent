"""
智能日程推荐API - 集成RAG和对话功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.schedule.schedule_recommender import (
    SmartScheduleRecommender,
    Task,
    ScheduleRecommendation
)
from backend.schedule.schedule_rag_integration import (
    ScheduleRAGIntegration,
    ScheduleConversationalInterface
)

router = APIRouter(prefix="/api/v5/schedule", tags=["schedule"])


class TaskRequest(BaseModel):
    """任务请求"""
    task_id: str
    title: str
    task_type: str
    duration_minutes: int
    priority: str = "medium"
    deadline: Optional[str] = None
    flexibility: float = 0.5
    energy_required: float = 0.5
    focus_required: float = 0.5


class OptimalTimeRequest(BaseModel):
    """最佳时间推荐请求"""
    user_id: str
    task: TaskRequest
    date: Optional[str] = None
    num_alternatives: int = 3


class DailyScheduleRequest(BaseModel):
    """每日日程请求"""
    user_id: str
    tasks: List[TaskRequest]
    date: Optional[str] = None


class WeeklyScheduleRequest(BaseModel):
    """每周日程请求"""
    user_id: str
    tasks: List[TaskRequest]
    start_date: Optional[str] = None


@router.post("/recommend-time")
async def recommend_optimal_time(request: OptimalTimeRequest):
    """
    为单个任务推荐最佳时间
    
    示例请求:
    ```json
    {
        "user_id": "user_001",
        "task": {
            "task_id": "task_1",
            "title": "完成项目报告",
            "task_type": "work",
            "duration_minutes": 120,
            "priority": "high",
            "deadline": "2026-04-07T18:00:00"
        },
        "num_alternatives": 3
    }
    ```
    """
    try:
        # 创建推荐器
        recommender = SmartScheduleRecommender(request.user_id)
        
        # 转换任务
        task = Task(
            task_id=request.task.task_id,
            title=request.task.title,
            task_type=request.task.task_type,
            duration_minutes=request.task.duration_minutes,
            priority=request.task.priority,
            deadline=datetime.fromisoformat(request.task.deadline) if request.task.deadline else None,
            flexibility=request.task.flexibility,
            energy_required=request.task.energy_required,
            focus_required=request.task.focus_required
        )
        
        # 解析日期
        date = datetime.fromisoformat(request.date) if request.date else None
        
        # 获取推荐
        recommendation = recommender.recommend_optimal_time(
            task, date, request.num_alternatives
        )
        
        return {
            "success": True,
            "data": {
                "task": {
                    "task_id": recommendation.task.task_id,
                    "title": recommendation.task.title,
                    "type": recommendation.task.task_type
                },
                "recommended_slot": recommendation.recommended_slot.to_dict(),
                "score": round(recommendation.score, 2),
                "reason": recommendation.reason,
                "alternatives": recommendation.alternatives
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-daily")
async def recommend_daily_schedule(request: DailyScheduleRequest):
    """
    生成每日完整日程
    
    示例请求:
    ```json
    {
        "user_id": "user_001",
        "tasks": [
            {
                "task_id": "task_1",
                "title": "晨练",
                "task_type": "exercise",
                "duration_minutes": 30,
                "priority": "high"
            },
            {
                "task_id": "task_2",
                "title": "项目开发",
                "task_type": "work",
                "duration_minutes": 180,
                "priority": "high"
            }
        ],
        "date": "2026-04-07"
    }
    ```
    """
    try:
        recommender = SmartScheduleRecommender(request.user_id)
        
        # 转换任务列表
        tasks = []
        for task_req in request.tasks:
            tasks.append(Task(
                task_id=task_req.task_id,
                title=task_req.title,
                task_type=task_req.task_type,
                duration_minutes=task_req.duration_minutes,
                priority=task_req.priority,
                deadline=datetime.fromisoformat(task_req.deadline) if task_req.deadline else None,
                flexibility=task_req.flexibility,
                energy_required=task_req.energy_required,
                focus_required=task_req.focus_required
            ))
        
        # 解析日期
        date = datetime.fromisoformat(request.date) if request.date else None
        
        # 生成日程
        schedule = recommender.recommend_daily_schedule(tasks, date)
        
        # 格式化输出
        formatted_schedule = []
        for item in schedule['schedule']:
            formatted_schedule.append({
                "task": {
                    "task_id": item['task'].task_id,
                    "title": item['task'].title,
                    "type": item['task'].task_type,
                    "priority": item['task'].priority
                },
                "time_slot": item['slot'].to_dict(),
                "reason": item['reason']
            })
        
        return {
            "success": True,
            "data": {
                "date": schedule['date'],
                "schedule": formatted_schedule,
                "timeline": schedule['timeline'],
                "summary": schedule['summary'],
                "optimization_tips": schedule['optimization_tips']
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-weekly")
async def recommend_weekly_schedule(request: WeeklyScheduleRequest):
    """生成每周日程"""
    try:
        recommender = SmartScheduleRecommender(request.user_id)
        
        # 转换任务
        tasks = []
        for task_req in request.tasks:
            tasks.append(Task(
                task_id=task_req.task_id,
                title=task_req.title,
                task_type=task_req.task_type,
                duration_minutes=task_req.duration_minutes,
                priority=task_req.priority,
                deadline=datetime.fromisoformat(task_req.deadline) if task_req.deadline else None
            ))
        
        # 解析日期
        start_date = datetime.fromisoformat(request.start_date) if request.start_date else None
        
        # 生成周日程
        weekly = recommender.recommend_weekly_schedule(tasks, start_date)
        
        return {
            "success": True,
            "data": weekly
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{user_id}")
async def get_user_patterns(user_id: str):
    """
    获取用户的时间使用模式分析（基于决策数据）
    使用缓存避免频繁分析
    """
    try:
        from backend.schedule.decision_based_analyzer import DecisionBasedAnalyzer
        import time
        
        # 简单的内存缓存（5分钟有效期）
        cache_key = f"patterns_{user_id}"
        cache_timeout = 300  # 5分钟
        
        # 检查缓存
        if not hasattr(get_user_patterns, '_cache'):
            get_user_patterns._cache = {}
        
        if cache_key in get_user_patterns._cache:
            cached_data, cached_time = get_user_patterns._cache[cache_key]
            if time.time() - cached_time < cache_timeout:
                print(f"[决策日程] 使用缓存数据 for {user_id}")
                return cached_data
        
        print(f"[决策日程] 初始化用户 {user_id} 的决策导向日程分析器")
        analyzer = DecisionBasedAnalyzer(user_id)
        
        # 分析决策上下文
        context = analyzer.analyze_decision_context()
        
        # 格式化返回数据，兼容前端期望的结构
        result = {
            "success": True,
            "data": {
                # 决策相关数据
                "action_items": context.get('action_items', []),
                "priorities": context.get('priorities', []),
                "constraints": context.get('constraints', []),
                "goals": context.get('goals', []),
                "active_decisions": context.get('active_decisions', []),
                "user_context": context.get('user_context', {}),
                
                # 为了向后兼容，提供空的传统字段
                "productivity_curve": [],
                "peak_hours": [],
                "low_hours": [],
                "typical_schedule": {},
                "habits": []
            }
        }
        
        # 缓存结果
        get_user_patterns._cache[cache_key] = (result, time.time())
        
        return result
    
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[决策日程] ❌ 错误: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))



# ==================== RAG集成API ====================

class NaturalLanguageRequest(BaseModel):
    """自然语言请求"""
    user_id: str
    message: str


class TaskCompletionRequest(BaseModel):
    """任务完成记录"""
    user_id: str
    task: TaskRequest
    completed: bool
    actual_duration: Optional[int] = None
    notes: str = ""


@router.post("/chat")
async def schedule_chat(request: NaturalLanguageRequest):
    """
    自然语言日程对话
    
    示例：
    - "帮我安排明天的日程"
    - "我什么时候适合做深度工作"
    - "查看上周的日程安排"
    """
    try:
        interface = ScheduleConversationalInterface(request.user_id)
        result = interface.process_natural_language_request(request.message)
        
        return {
            "success": True,
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-with-context")
async def recommend_with_rag_context(request: DailyScheduleRequest):
    """
    基于RAG上下文的智能日程推荐
    
    考虑用户的历史完成情况和习惯
    """
    try:
        rag_integration = ScheduleRAGIntegration(request.user_id)
        
        # 转换任务
        tasks = []
        for task_req in request.tasks:
            tasks.append(Task(
                task_id=task_req.task_id,
                title=task_req.title,
                task_type=task_req.task_type,
                duration_minutes=task_req.duration_minutes,
                priority=task_req.priority,
                deadline=datetime.fromisoformat(task_req.deadline) if task_req.deadline else None,
                flexibility=task_req.flexibility,
                energy_required=task_req.energy_required,
                focus_required=task_req.focus_required
            ))
        
        # 解析日期
        date = datetime.fromisoformat(request.date) if request.date else None
        
        # 生成带上下文的推荐
        schedule = rag_integration.get_smart_recommendations_with_context(tasks, date)
        
        # 格式化输出
        formatted_schedule = []
        for item in schedule['schedule']:
            formatted_schedule.append({
                "task": {
                    "task_id": item['task'].task_id,
                    "title": item['task'].title,
                    "type": item['task'].task_type,
                    "priority": item['task'].priority
                },
                "time_slot": item['slot'].to_dict(),
                "reason": item['reason']
            })
        
        return {
            "success": True,
            "data": {
                "date": schedule['date'],
                "schedule": formatted_schedule,
                "timeline": schedule['timeline'],
                "summary": schedule['summary'],
                "optimization_tips": schedule['optimization_tips'],
                "rag_insights": schedule.get('rag_insights', []),
                "completion_rate": schedule.get('completion_rate', 0)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task-completion")
async def record_task_completion(request: TaskCompletionRequest):
    """
    记录任务完成情况
    
    用于学习用户习惯，优化未来推荐
    """
    try:
        rag_integration = ScheduleRAGIntegration(request.user_id)
        
        # 转换任务
        task = Task(
            task_id=request.task.task_id,
            title=request.task.title,
            task_type=request.task.task_type,
            duration_minutes=request.task.duration_minutes,
            priority=request.task.priority
        )
        
        # 存储完成记录
        rag_integration.store_task_completion(
            task,
            request.completed,
            request.actual_duration,
            request.notes
        )
        
        return {
            "success": True,
            "message": "任务完成记录已保存"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}")
async def get_schedule_history(user_id: str, query: str = "最近的日程", limit: int = 5):
    """
    查询历史日程
    
    支持自然语言查询
    """
    try:
        rag_integration = ScheduleRAGIntegration(user_id)
        schedules = rag_integration.query_schedule_history(query, limit)
        
        return {
            "success": True,
            "data": {
                "query": query,
                "schedules": schedules
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/completion-analysis/{user_id}")
async def get_completion_analysis(user_id: str):
    """
    获取任务完成模式分析
    """
    try:
        rag_integration = ScheduleRAGIntegration(user_id)
        patterns = rag_integration.analyze_completion_patterns()
        
        return {
            "success": True,
            "data": patterns
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ==================== 时间决策API ====================

class TimeDecisionRequest(BaseModel):
    """时间决策请求"""
    user_id: str
    tasks: List[TaskRequest]
    date: Optional[str] = None
    available_hours: float = 16.0  # 可用时间（小时）
    current_energy: float = 0.7  # 当前能量水平
    current_stress: float = 0.3  # 当前压力水平
    goals: List[Dict[str, Any]] = []  # 用户目标


@router.post("/time-decision")
async def make_time_decision(request: TimeDecisionRequest):
    """
    时间决策 - 将日程安排视为智能决策问题
    
    生成多个可行方案（激进/平衡/保守），并基于用户状态推荐最佳方案
    
    示例请求:
    ```json
    {
        "user_id": "user_001",
        "tasks": [
            {
                "task_id": "task_1",
                "title": "项目开发",
                "task_type": "work",
                "duration_minutes": 180,
                "priority": "high"
            },
            {
                "task_id": "task_2",
                "title": "学习新技术",
                "task_type": "study",
                "duration_minutes": 90,
                "priority": "medium"
            }
        ],
        "available_hours": 12,
        "current_energy": 0.8,
        "current_stress": 0.4
    }
    ```
    """
    try:
        from backend.vertical.time import (
            TimeDecisionEngine,
            TimeDecisionContext
        )
        from backend.schedule.schedule_recommender import Task
        
        # 转换任务
        tasks = []
        for task_req in request.tasks:
            tasks.append(Task(
                task_id=task_req.task_id,
                title=task_req.title,
                task_type=task_req.task_type,
                duration_minutes=task_req.duration_minutes,
                priority=task_req.priority,
                deadline=datetime.fromisoformat(task_req.deadline) if task_req.deadline else None,
                flexibility=task_req.flexibility,
                energy_required=task_req.energy_required,
                focus_required=task_req.focus_required
            ))
        
        # 构建决策上下文
        decision_date = datetime.fromisoformat(request.date) if request.date else datetime.now()
        
        context = TimeDecisionContext(
            user_id=request.user_id,
            decision_date=decision_date,
            available_hours=request.available_hours,
            energy_level=request.current_energy,
            stress_level=request.current_stress,
            pending_tasks=tasks,
            goals=request.goals,
            constraints={}
        )
        
        # 执行时间决策
        engine = TimeDecisionEngine(request.user_id)
        result = engine.make_time_decision(context, num_options=3)
        
        # 格式化输出
        return {
            "success": True,
            "data": {
                "decision_id": result.decision_id,
                "timestamp": result.timestamp.isoformat(),
                "context": {
                    "available_hours": context.available_hours,
                    "energy_level": context.energy_level,
                    "stress_level": context.stress_level,
                    "task_count": len(context.pending_tasks)
                },
                "recommended_option": {
                    "option_id": result.recommended_option.option_id,
                    "description": result.recommended_option.description,
                    "expected_completion_rate": round(result.recommended_option.expected_completion_rate, 2),
                    "expected_efficiency": round(result.recommended_option.expected_efficiency, 2),
                    "expected_stress": round(result.recommended_option.expected_stress, 2),
                    "expected_satisfaction": round(result.recommended_option.expected_satisfaction, 2),
                    "risk_level": round(result.recommended_option.risk_level, 2),
                    "schedule": result.recommended_option.schedule
                },
                "alternative_options": [
                    {
                        "option_id": opt.option_id,
                        "description": opt.description,
                        "expected_completion_rate": round(opt.expected_completion_rate, 2),
                        "expected_efficiency": round(opt.expected_efficiency, 2),
                        "expected_stress": round(opt.expected_stress, 2),
                        "risk_level": round(opt.risk_level, 2)
                    }
                    for opt in result.options
                    if opt.option_id != result.recommended_option.option_id
                ],
                "reasoning": result.reasoning,
                "trade_offs": result.trade_offs,
                "confidence": round(result.confidence, 2)
            }
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decision-history/{user_id}")
async def get_decision_history(user_id: str, limit: int = 10):
    """
    获取用户的时间决策历史
    
    用于分析决策模式和优化建议
    """
    try:
        # TODO: 从数据库获取历史决策记录
        # 这里返回模拟数据
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "decisions": [],
                "statistics": {
                    "total_decisions": 0,
                    "avg_completion_rate": 0.0,
                    "avg_confidence": 0.0,
                    "most_chosen_option": "balanced"
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ==================== 异步任务系统 ====================

from backend.schedule.schedule_task_manager import task_manager, TaskType
from fastapi import BackgroundTasks


class AsyncScheduleRequest(BaseModel):
    """异步日程生成请求"""
    user_id: str
    description: Optional[str] = None  # 用户描述
    tasks: Optional[List[TaskRequest]] = None  # 或直接提供任务列表
    date: Optional[str] = None


class AsyncDecisionRequest(BaseModel):
    """异步决策请求"""
    user_id: str
    tasks: List[TaskRequest]
    available_hours: float = 12.0
    energy_level: float = 0.7
    stress_level: float = 0.3


@router.post("/async/generate")
async def create_schedule_generation_task(
    request: AsyncScheduleRequest,
    background_tasks: BackgroundTasks
):
    """
    创建异步日程生成任务
    
    用户通过AI对话触发，后台异步生成日程
    """
    # 创建任务
    task_id = task_manager.create_task(
        user_id=request.user_id,
        task_type=TaskType.SCHEDULE_GENERATION,
        params={
            "description": request.description,
            "tasks": [t.dict() for t in request.tasks] if request.tasks else [],
            "date": request.date
        }
    )
    
    # 后台执行
    background_tasks.add_task(
        task_manager.execute_schedule_generation,
        task_id,
        request.user_id,
        {
            "description": request.description,
            "tasks": [t.dict() for t in request.tasks] if request.tasks else [],
            "date": request.date
        }
    )
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "日程生成任务已创建，正在后台执行"
    }


@router.post("/async/decision")
async def create_decision_task(
    request: AsyncDecisionRequest,
    background_tasks: BackgroundTasks
):
    """
    创建异步时间决策任务
    """
    # 转换任务格式
    tasks = []
    for t in request.tasks:
        tasks.append({
            "task_id": t.task_id,
            "title": t.title,
            "task_type": t.task_type,
            "duration_minutes": t.duration_minutes,
            "priority": t.priority,
            "flexibility": t.flexibility,
            "energy_required": 0.7,
            "focus_required": 0.7
        })
    
    # 创建任务
    task_id = task_manager.create_task(
        user_id=request.user_id,
        task_type=TaskType.TIME_DECISION,
        params={
            "tasks": tasks,
            "available_hours": request.available_hours,
            "energy_level": request.energy_level,
            "stress_level": request.stress_level
        }
    )
    
    # 后台执行
    background_tasks.add_task(
        task_manager.execute_time_decision,
        task_id,
        request.user_id,
        {
            "tasks": tasks,
            "available_hours": request.available_hours,
            "energy_level": request.energy_level,
            "stress_level": request.stress_level
        }
    )
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "时间决策任务已创建，正在后台执行"
    }


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    查询任务状态和结果
    
    前端轮询此接口获取实时进度
    """
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task.to_dict()


@router.get("/user/{user_id}/tasks")
async def get_user_tasks(user_id: str, limit: int = 10):
    """
    获取用户的任务列表
    """
    tasks = task_manager.get_user_tasks(user_id, limit)
    return [t.to_dict() for t in tasks]


@router.get("/user/{user_id}/latest-schedule")
async def get_latest_schedule(user_id: str):
    """
    获取用户最新的日程生成结果
    
    前端页面加载时调用，显示最新生成的日程
    """
    task = task_manager.get_latest_task(user_id, TaskType.SCHEDULE_GENERATION)
    
    if not task:
        return {"status": "no_data", "message": "暂无日程数据"}
    
    return task.to_dict()


@router.get("/user/{user_id}/latest-decision")
async def get_latest_decision(user_id: str):
    """
    获取用户最新的时间决策结果
    """
    task = task_manager.get_latest_task(user_id, TaskType.TIME_DECISION)
    
    if not task:
        return {"status": "no_data", "message": "暂无决策数据"}
    
    return task.to_dict()


@router.get("/auto-generator/status")
async def get_auto_generator_status():
    """
    获取智能日程自动生成器状态
    
    Returns:
        {
            "running": true/false,
            "jobs": [
                {
                    "id": "daily_schedule_generation",
                    "name": "每日日程自动生成",
                    "next_run": "2024-01-01T02:00:00",
                    "trigger": "cron[hour='2', minute='0']"
                }
            ]
        }
    """
    try:
        from backend.schedule.schedule_auto_generator import get_auto_generator
        
        generator = get_auto_generator()
        status = generator.get_scheduler_status()
        
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-generator/trigger")
async def trigger_auto_generation(user_id: Optional[str] = None):
    """
    手动触发日程自动生成
    
    Args:
        user_id: 可选，指定用户ID。如果不指定，为所有活跃用户生成
    
    Returns:
        {
            "success": true,
            "message": "日程生成已触发"
        }
    """
    try:
        from backend.schedule.schedule_auto_generator import get_auto_generator
        from datetime import datetime, timedelta
        
        generator = get_auto_generator()
        
        if user_id:
            # 为指定用户生成明天的日程
            target_date = datetime.now().date() + timedelta(days=1)
            await generator._generate_schedule_for_user(user_id, target_date)
            message = f"已为用户 {user_id} 生成 {target_date} 的日程"
        else:
            # 为所有活跃用户生成
            await generator._generate_daily_schedules()
            message = "已为所有活跃用户生成日程"
        
        return {
            "success": True,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
