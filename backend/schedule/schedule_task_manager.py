"""
日程生成任务管理器 - 异步任务系统
支持后台生成日程和决策，前端实时查询状态
"""
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class TaskType(Enum):
    """任务类型"""
    SCHEDULE_GENERATION = "schedule_generation"  # 日程生成
    TIME_DECISION = "time_decision"  # 时间决策


class ScheduleTask:
    """日程任务"""
    
    def __init__(
        self,
        task_id: str,
        user_id: str,
        task_type: TaskType,
        params: Dict[str, Any]
    ):
        self.task_id = task_id
        self.user_id = user_id
        self.task_type = task_type
        self.params = params
        self.status = TaskStatus.PENDING
        self.progress = 0  # 0-100
        self.progress_message = "任务已创建"
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ScheduleTaskManager:
    """日程任务管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.tasks: Dict[str, ScheduleTask] = {}
        self.user_tasks: Dict[str, List[str]] = {}  # user_id -> [task_ids]
        self._initialized = True
    
    def create_task(
        self,
        user_id: str,
        task_type: TaskType,
        params: Dict[str, Any]
    ) -> str:
        """
        创建新任务
        
        Returns:
            task_id
        """
        task_id = str(uuid.uuid4())
        task = ScheduleTask(task_id, user_id, task_type, params)
        
        self.tasks[task_id] = task
        
        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = []
        self.user_tasks[user_id].append(task_id)
        
        print(f"[任务管理] 创建任务 {task_id} for 用户 {user_id}, 类型: {task_type.value}")
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[ScheduleTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_user_tasks(self, user_id: str, limit: int = 10) -> List[ScheduleTask]:
        """获取用户的任务列表"""
        task_ids = self.user_tasks.get(user_id, [])
        # 返回最新的任务
        recent_ids = task_ids[-limit:]
        return [self.tasks[tid] for tid in recent_ids if tid in self.tasks]
    
    def get_latest_task(self, user_id: str, task_type: Optional[TaskType] = None) -> Optional[ScheduleTask]:
        """获取用户最新的任务"""
        tasks = self.get_user_tasks(user_id, limit=50)
        
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        if not tasks:
            return None
        
        # 返回最新的任务
        return max(tasks, key=lambda t: t.created_at)
    
    def update_progress(
        self,
        task_id: str,
        progress: int,
        message: str
    ):
        """更新任务进度"""
        task = self.get_task(task_id)
        if task:
            task.progress = progress
            task.progress_message = message
            print(f"[任务进度] {task_id}: {progress}% - {message}")
    
    def start_task(self, task_id: str):
        """开始执行任务"""
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.progress = 10
            task.progress_message = "任务开始执行"
            print(f"[任务管理] 任务 {task_id} 开始执行")
    
    def complete_task(
        self,
        task_id: str,
        result: Any
    ):
        """完成任务"""
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 100
            task.progress_message = "任务完成"
            task.result = result
            print(f"[任务管理] 任务 {task_id} 完成")
    
    def fail_task(
        self,
        task_id: str,
        error: str
    ):
        """任务失败"""
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.progress_message = "任务失败"
            task.error = error
            print(f"[任务管理] 任务 {task_id} 失败: {error}")
    
    async def execute_schedule_generation(
        self,
        task_id: str,
        user_id: str,
        params: Dict[str, Any]
    ):
        """
        执行日程生成任务
        """
        from backend.schedule.schedule_recommender import SmartScheduleRecommender
        from backend.schedule.schedule_analyzer import ScheduleAnalyzer
        
        try:
            self.start_task(task_id)
            
            # 步骤1: 分析用户模式
            self.update_progress(task_id, 20, "分析历史时间模式...")
            analyzer = ScheduleAnalyzer(user_id)
            patterns = analyzer.analyze_historical_patterns()
            
            # 步骤2: 提取任务（从用户输入或RAG）
            self.update_progress(task_id, 40, "提取待完成任务...")
            tasks = params.get('tasks', [])
            
            if not tasks:
                # 从RAG或其他来源提取任务
                # TODO: 实现从用户描述中提取任务
                tasks = self._extract_tasks_from_description(
                    user_id,
                    params.get('description', '')
                )
            
            # 步骤3: 生成日程
            self.update_progress(task_id, 60, "生成智能日程...")
            recommender = SmartScheduleRecommender(user_id)
            
            # 解析日期
            from datetime import datetime
            date_obj = None
            if params.get('date'):
                try:
                    date_obj = datetime.strptime(params.get('date'), "%Y-%m-%d")
                except:
                    date_obj = datetime.now()
            
            # 将字典转换为 Task 对象
            from backend.schedule.schedule_recommender import Task
            task_objects = []
            for task_dict in tasks:
                task_obj = Task(
                    task_id=task_dict.get('task_id', ''),
                    title=task_dict.get('title', ''),
                    task_type=task_dict.get('task_type', 'work'),
                    duration_minutes=task_dict.get('duration_minutes', 60),
                    priority=task_dict.get('priority', 'medium'),
                    deadline=task_dict.get('deadline'),
                    flexibility=task_dict.get('flexibility', 0.5),
                    energy_required=task_dict.get('energy_required', 0.5),
                    focus_required=task_dict.get('focus_required', 0.5)
                )
                task_objects.append(task_obj)
            
            schedule = recommender.recommend_daily_schedule(
                task_objects,
                date=date_obj
            )
            
            # 步骤4: 完成
            self.update_progress(task_id, 90, "优化日程安排...")
            await asyncio.sleep(0.5)  # 模拟优化过程
            
            self.complete_task(task_id, schedule)
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.fail_task(task_id, error_msg)
    
    async def execute_time_decision(
        self,
        task_id: str,
        user_id: str,
        params: Dict[str, Any]
    ):
        """
        执行时间决策任务
        """
        from backend.vertical.time.time_decision_engine import (
            TimeDecisionEngine,
            TimeDecisionContext
        )
        from datetime import datetime
        
        try:
            self.start_task(task_id)
            
            # 步骤1: 准备决策上下文
            self.update_progress(task_id, 20, "分析当前状态...")
            
            context = TimeDecisionContext(
                user_id=user_id,
                decision_date=datetime.now(),
                available_hours=params.get('available_hours', 12),
                energy_level=params.get('energy_level', 0.7),
                stress_level=params.get('stress_level', 0.3),
                pending_tasks=params.get('tasks', []),
                goals=[],
                constraints={}
            )
            
            # 步骤2: 生成决策方案
            self.update_progress(task_id, 50, "生成决策方案...")
            engine = TimeDecisionEngine(user_id)
            decision = engine.make_time_decision(context)
            
            # 步骤3: LLM推理
            self.update_progress(task_id, 80, "生成决策推理...")
            await asyncio.sleep(0.5)
            
            self.complete_task(task_id, decision)
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.fail_task(task_id, error_msg)
    
    def _extract_tasks_from_description(
        self,
        user_id: str,
        description: str
    ) -> List[Dict]:
        """从用户描述中提取任务（使用LLM）"""
        # TODO: 使用LLM从自然语言描述中提取任务
        # 暂时返回示例任务
        return [
            {
                "task_id": f"task_{uuid.uuid4()}",
                "title": "项目开发",
                "task_type": "work",
                "duration_minutes": 180,
                "priority": "high",
                "flexibility": 0.3,
                "energy_required": 0.8,
                "focus_required": 0.9
            }
        ]


# 全局单例
task_manager = ScheduleTaskManager()
