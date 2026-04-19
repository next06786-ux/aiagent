"""
智能日程推荐 - RAG系统集成
将日程数据存入RAG记忆，支持自然语言查询和智能推荐
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType
from backend.schedule.schedule_recommender import SmartScheduleRecommender, Task
from backend.schedule.schedule_analyzer import ScheduleAnalyzer


class ScheduleRAGIntegration:
    """日程推荐与RAG系统集成"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.recommender = SmartScheduleRecommender(user_id)
        self.analyzer = ScheduleAnalyzer(user_id)
        
    def get_rag_system(self) -> ProductionRAGSystem:
        """获取用户的RAG系统"""
        from backend.startup_manager import StartupManager
        return StartupManager.get_user_system("default_user", 'rag')
    
    def store_schedule_to_rag(
        self,
        schedule: Dict[str, Any],
        context: str = ""
    ):
        """
        将生成的日程存入RAG记忆
        
        Args:
            schedule: 日程数据
            context: 额外上下文信息
        """
        rag = self.get_rag_system()
        
        # 构建记忆内容
        date = schedule.get('date', datetime.now().date().isoformat())
        timeline = schedule.get('timeline', [])
        summary = schedule.get('summary', {})
        
        # 生成可读的日程描述
        content = f"日程安排 - {date}\n\n"
        
        for item in timeline:
            content += f"{item['start']}-{item['end']}: {item['title']} ({item['type']}, {item['priority']}优先级)\n"
        
        content += f"\n总计: {summary.get('total_tasks', 0)}个任务, "
        content += f"工作{summary.get('total_work_minutes', 0)}分钟, "
        content += f"休息{summary.get('total_break_minutes', 0)}分钟"
        
        if context:
            content += f"\n\n背景: {context}"
        
        # 存入RAG
        rag.add_memory(
            memory_type=MemoryType.SCHEDULE,
            content=content,
            metadata={
                "date": date,
                "schedule_data": schedule,
                "total_tasks": summary.get('total_tasks', 0),
                "total_work_minutes": summary.get('total_work_minutes', 0)
            },
            importance=0.7
        )
        
        print(f"[RAG集成] 日程已存入RAG: {date}")
    
    def store_task_completion(
        self,
        task: Task,
        completed: bool,
        actual_duration: Optional[int] = None,
        notes: str = ""
    ):
        """
        存储任务完成情况到RAG
        
        用于学习用户的实际执行情况，优化未来推荐
        """
        rag = self.get_rag_system()
        
        status = "已完成" if completed else "未完成"
        content = f"任务{status}: {task.title}\n"
        content += f"类型: {task.task_type}, 优先级: {task.priority}\n"
        content += f"计划时长: {task.duration_minutes}分钟\n"
        
        if actual_duration:
            content += f"实际时长: {actual_duration}分钟\n"
            diff = actual_duration - task.duration_minutes
            if abs(diff) > 10:
                content += f"时长偏差: {'+' if diff > 0 else ''}{diff}分钟\n"
        
        if notes:
            content += f"备注: {notes}\n"
        
        rag.add_memory(
            memory_type=MemoryType.TASK_COMPLETION,
            content=content,
            metadata={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "completed": completed,
                "planned_duration": task.duration_minutes,
                "actual_duration": actual_duration,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.6
        )
        
        print(f"[RAG集成] 任务完成记录已存入RAG: {task.title}")
    
    def query_schedule_history(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查询历史日程记录
        
        Args:
            query: 自然语言查询，如"上周的工作安排"
            limit: 返回结果数量
        
        Returns:
            相关的历史日程记录
        """
        rag = self.get_rag_system()
        
        # 从RAG检索相关记忆
        results = rag.retrieve_memories(
            query=query,
            memory_types=[MemoryType.SCHEDULE],
            top_k=limit
        )
        
        schedules = []
        for result in results:
            metadata = result.get('metadata', {})
            schedules.append({
                "date": metadata.get('date'),
                "content": result.get('content'),
                "schedule_data": metadata.get('schedule_data'),
                "relevance_score": result.get('score', 0)
            })
        
        return schedules
    
    def analyze_completion_patterns(self) -> Dict[str, Any]:
        """
        分析任务完成模式
        
        从RAG中提取任务完成记录，分析用户的执行习惯
        """
        rag = self.get_rag_system()
        
        # 检索最近的任务完成记录
        results = rag.retrieve_memories(
            query="任务完成情况",
            memory_types=[MemoryType.TASK_COMPLETION],
            top_k=50
        )
        
        # 统计分析
        total_tasks = len(results)
        completed_tasks = 0
        duration_diffs = []
        task_type_stats = {}
        
        for result in results:
            metadata = result.get('metadata', {})
            
            if metadata.get('completed'):
                completed_tasks += 1
            
            # 时长偏差
            planned = metadata.get('planned_duration', 0)
            actual = metadata.get('actual_duration', 0)
            if actual > 0:
                diff = actual - planned
                duration_diffs.append(diff)
            
            # 任务类型统计
            task_type = metadata.get('task_type', 'unknown')
            if task_type not in task_type_stats:
                task_type_stats[task_type] = {"total": 0, "completed": 0}
            task_type_stats[task_type]["total"] += 1
            if metadata.get('completed'):
                task_type_stats[task_type]["completed"] += 1
        
        # 计算平均时长偏差
        avg_duration_diff = sum(duration_diffs) / len(duration_diffs) if duration_diffs else 0
        
        # 完成率
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completion_rate, 2),
            "avg_duration_diff_minutes": round(avg_duration_diff, 1),
            "task_type_stats": task_type_stats,
            "insights": self._generate_insights(
                completion_rate,
                avg_duration_diff,
                task_type_stats
            )
        }
    
    def _generate_insights(
        self,
        completion_rate: float,
        avg_duration_diff: float,
        task_type_stats: Dict
    ) -> List[str]:
        """生成洞察建议"""
        insights = []
        
        if completion_rate < 0.6:
            insights.append("任务完成率较低，建议减少每日任务量或延长任务时间")
        elif completion_rate > 0.9:
            insights.append("任务完成率很高，可以适当增加挑战性任务")
        
        if avg_duration_diff > 15:
            insights.append(f"任务平均超时{int(avg_duration_diff)}分钟，建议预留更多缓冲时间")
        elif avg_duration_diff < -15:
            insights.append(f"任务平均提前{int(-avg_duration_diff)}分钟完成，可以安排更多任务")
        
        # 分析各类型任务
        for task_type, stats in task_type_stats.items():
            if stats["total"] >= 5:
                type_rate = stats["completed"] / stats["total"]
                if type_rate < 0.5:
                    insights.append(f"{task_type}类型任务完成率较低，需要调整安排策略")
        
        return insights
    
    def get_smart_recommendations_with_context(
        self,
        tasks: List[Task],
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        结合RAG上下文生成智能推荐
        
        考虑历史数据和用户习惯
        """
        # 分析完成模式
        patterns = self.analyze_completion_patterns()
        
        # 调整任务时长（基于历史偏差）
        avg_diff = patterns.get('avg_duration_diff_minutes', 0)
        if abs(avg_diff) > 5:
            for task in tasks:
                # 根据历史偏差调整预估时长
                adjustment = int(avg_diff * 0.5)  # 保守调整
                task.duration_minutes += adjustment
                task.duration_minutes = max(15, task.duration_minutes)  # 最少15分钟
        
        # 生成日程
        schedule = self.recommender.recommend_daily_schedule(tasks, date)
        
        # 添加基于历史的额外建议
        schedule['rag_insights'] = patterns.get('insights', [])
        schedule['completion_rate'] = patterns.get('completion_rate', 0)
        
        # 存入RAG
        self.store_schedule_to_rag(
            schedule,
            context=f"基于{patterns['total_tasks']}条历史记录生成，完成率{patterns['completion_rate']}"
        )
        
        return schedule


class ScheduleConversationalInterface:
    """日程推荐的对话式接口"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.rag_integration = ScheduleRAGIntegration(user_id)
        
    def process_natural_language_request(
        self,
        user_message: str
    ) -> Dict[str, Any]:
        """
        处理自然语言日程请求
        
        示例：
        - "帮我安排明天的日程"
        - "我什么时候适合做深度工作"
        - "查看上周的日程安排"
        """
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return {"error": "LLM服务不可用"}
        
        # 构建提示词
        prompt = f"""你是一个智能日程助手。用户说："{user_message}"

请分析用户的需求，判断是以下哪种类型：
1. schedule_request - 需要生成日程安排
2. time_query - 查询最佳时间
3. history_query - 查询历史日程
4. pattern_analysis - 分析时间使用模式
5. general_chat - 普通聊天

返回JSON格式：
{{
  "intent": "类型",
  "parameters": {{
    "date": "日期（如果提到）",
    "task_type": "任务类型（如果提到）",
    "query": "查询内容"
  }},
  "response": "给用户的回复"
}}

只返回JSON，不要其他内容。"""
        
        try:
            response = llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format="json_object"
            )
            
            result = json.loads(response)
            intent = result.get("intent")
            params = result.get("parameters", {})
            
            # 根据意图执行相应操作
            if intent == "schedule_request":
                return self._handle_schedule_request(params)
            elif intent == "time_query":
                return self._handle_time_query(params)
            elif intent == "history_query":
                return self._handle_history_query(params)
            elif intent == "pattern_analysis":
                return self._handle_pattern_analysis()
            else:
                return {"response": result.get("response", "我可以帮你安排日程，请告诉我你的任务")}
                
        except Exception as e:
            print(f"[对话接口] 处理失败: {e}")
            return {"error": str(e)}
    
    def _handle_schedule_request(self, params: Dict) -> Dict[str, Any]:
        """处理日程生成请求"""
        from backend.schedule.schedule_task_manager import task_manager, TaskType
        from datetime import datetime
        import asyncio
        
        # 从参数中提取日期
        date_str = params.get("date")
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # TODO: 从对话中提取任务列表，目前使用默认任务
        default_tasks = [
            {
                "task_id": f"task_{datetime.now().timestamp()}",
                "title": "工作任务",
                "task_type": "work",
                "duration_minutes": 120,
                "priority": "high",
                "flexibility": 0.3,
                "energy_required": 0.7,
                "focus_required": 0.8
            }
        ]
        
        # 创建异步日程生成任务
        task_id = task_manager.create_task(
            user_id=self.user_id,
            task_type=TaskType.SCHEDULE_GENERATION,
            params={
                "tasks": default_tasks,
                "date": date_str,
                "description": params.get("query", "")
            }
        )
        
        # 在后台执行任务
        async def execute_task():
            await task_manager.execute_schedule_generation(
                task_id,
                self.user_id,
                {
                    "tasks": default_tasks,
                    "date": date_str
                }
            )
        
        # 启动后台任务
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(execute_task())
        except RuntimeError:
            # 如果没有运行的事件循环，创建一个新的
            import threading
            def run_task():
                asyncio.run(execute_task())
            thread = threading.Thread(target=run_task)
            thread.start()
        
        return {
            "action": "schedule_generation_started",
            "task_id": task_id,
            "message": f"正在为你生成{date_str}的日程安排，请稍候查看智能日程页面..."
        }
    
    def _handle_time_query(self, params: Dict) -> Dict[str, Any]:
        """处理时间查询"""
        task_type = params.get("task_type", "work")
        
        # 分析用户模式
        patterns = self.rag_integration.analyzer.analyze_historical_patterns()
        peak_hours = patterns['peak_hours']
        
        if task_type in ["work", "study"]:
            slots = [f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}" 
                    for slot in peak_hours[:3]]
            return {
                "action": "time_recommendation",
                "recommended_times": slots,
                "message": f"根据你的习惯，{task_type}类型任务最适合在以下时段进行：{', '.join(slots)}"
            }
        
        return {"message": "请提供更多信息"}
    
    def _handle_history_query(self, params: Dict) -> Dict[str, Any]:
        """处理历史查询"""
        query = params.get("query", "最近的日程")
        schedules = self.rag_integration.query_schedule_history(query, limit=5)
        
        return {
            "action": "history_query",
            "schedules": schedules,
            "message": f"找到{len(schedules)}条相关日程记录"
        }
    
    def _handle_pattern_analysis(self) -> Dict[str, Any]:
        """处理模式分析"""
        patterns = self.rag_integration.analyze_completion_patterns()
        
        return {
            "action": "pattern_analysis",
            "patterns": patterns,
            "message": f"你的任务完成率为{patterns['completion_rate']*100:.0f}%，{patterns['insights'][0] if patterns['insights'] else '继续保持'}"
        }
