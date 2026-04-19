"""
智能日程推荐器 - 基于分析结果生成推荐
支持LLM增强的推理生成
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, time
from dataclasses import dataclass
import logging

from backend.schedule.schedule_analyzer import (
    ScheduleAnalyzer,
    TimeSlot,
    ProductivityPattern
)

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """任务"""
    task_id: str
    title: str
    task_type: str  # work, study, exercise, social, rest
    duration_minutes: int
    priority: str  # high, medium, low
    deadline: Optional[datetime] = None
    flexibility: float = 0.5  # 0-1, 时间灵活度
    energy_required: float = 0.5  # 0-1, 所需能量
    focus_required: float = 0.5  # 0-1, 所需专注度


@dataclass
class ScheduleRecommendation:
    """日程推荐"""
    task: Task
    recommended_slot: TimeSlot
    score: float
    reason: str
    alternatives: List[Dict[str, Any]]


class SmartScheduleRecommender:
    """智能日程推荐器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.analyzer = ScheduleAnalyzer(user_id)
        
    def recommend_optimal_time(
        self,
        task: Task,
        date: Optional[datetime] = None,
        num_alternatives: int = 3
    ) -> ScheduleRecommendation:
        """
        为单个任务推荐最佳时间
        
        Args:
            task: 任务信息
            date: 目标日期（默认今天）
            num_alternatives: 备选方案数量
        
        Returns:
            推荐结果
        """
        if date is None:
            date = datetime.now()
        
        logger.info(f"[日程推荐] 为任务 {task.title} 推荐时间")
        
        # 分析用户模式
        patterns = self.analyzer.analyze_historical_patterns()
        productivity_curve = patterns['productivity_curve']
        
        # 获取可用时间段
        available_slots = self._get_available_slots(date, task.duration_minutes)
        
        # 评分所有时间段
        scored_slots = []
        for slot in available_slots:
            score = self._calculate_slot_score(
                slot, task, productivity_curve, patterns
            )
            scored_slots.append((slot, score))
        
        # 排序
        scored_slots.sort(key=lambda x: x[1], reverse=True)
        
        if not scored_slots:
            raise ValueError("没有可用的时间段")
        
        # 最佳推荐
        best_slot, best_score = scored_slots[0]
        reason = self._generate_reason(best_slot, task, productivity_curve)
        
        # 备选方案
        alternatives = []
        for slot, score in scored_slots[1:num_alternatives+1]:
            alternatives.append({
                "slot": slot.to_dict(),
                "score": round(score, 2),
                "reason": self._generate_reason(slot, task, productivity_curve)
            })
        
        return ScheduleRecommendation(
            task=task,
            recommended_slot=best_slot,
            score=best_score,
            reason=reason,
            alternatives=alternatives
        )
    
    def recommend_daily_schedule(
        self,
        tasks: List[Task],
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        为一天的所有任务生成完整日程
        
        Args:
            tasks: 任务列表
            date: 目标日期
        
        Returns:
            完整日程安排
        """
        if date is None:
            date = datetime.now()
        
        logger.info(f"[日程推荐] 生成 {date.date()} 的完整日程")
        
        # 分析用户模式
        patterns = self.analyzer.analyze_historical_patterns()
        
        # 按优先级和截止时间排序任务
        sorted_tasks = self._prioritize_tasks(tasks)
        
        # 分配时间段
        schedule = []
        used_slots = []
        
        for task in sorted_tasks:
            try:
                # 获取可用时间段（排除已使用的）
                available_slots = self._get_available_slots(
                    date, task.duration_minutes, exclude=used_slots
                )
                
                if not available_slots:
                    logger.warning(f"任务 {task.title} 没有可用时间段")
                    continue
                
                # 找到最佳时间段
                best_slot = self._find_best_slot(
                    available_slots, task, patterns['productivity_curve']
                )
                
                schedule.append({
                    "task": task,
                    "slot": best_slot,
                    "reason": self._generate_reason(
                        best_slot, task, patterns['productivity_curve']
                    )
                })
                
                used_slots.append(best_slot)
                
            except Exception as e:
                logger.error(f"为任务 {task.title} 分配时间失败: {e}")
        
        # 添加休息时间
        schedule_with_breaks = self._add_break_times(schedule, patterns)
        
        # 生成时间线视图
        timeline = self._generate_timeline(schedule_with_breaks, date)
        
        return {
            "date": date.date().isoformat(),
            "schedule": schedule_with_breaks,
            "timeline": timeline,
            "summary": self._generate_summary(schedule_with_breaks),
            "optimization_tips": self._generate_tips(schedule_with_breaks, patterns)
        }
    
    def recommend_weekly_schedule(
        self,
        tasks: List[Task],
        start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """生成一周的日程推荐"""
        if start_date is None:
            start_date = datetime.now()
        
        weekly_schedule = {}
        
        for i in range(7):
            date = start_date + timedelta(days=i)
            day_name = date.strftime("%A")
            
            # 为每天生成日程
            daily_schedule = self.recommend_daily_schedule(tasks, date)
            weekly_schedule[day_name] = daily_schedule
        
        return {
            "week_start": start_date.date().isoformat(),
            "weekly_schedule": weekly_schedule,
            "weekly_summary": self._generate_weekly_summary(weekly_schedule)
        }
    
    def _get_available_slots(
        self,
        date: datetime,
        duration_minutes: int,
        exclude: List[TimeSlot] = None
    ) -> List[TimeSlot]:
        """获取可用时间段"""
        if exclude is None:
            exclude = []
        
        # 工作时间：9:00-22:00
        available_slots = []
        
        # 每30分钟一个时间段
        current_time = time(6, 0)
        end_time = time(23, 0)
        
        while current_time < end_time:
            # 计算结束时间
            current_datetime = datetime.combine(date.date(), current_time)
            end_datetime = current_datetime + timedelta(minutes=duration_minutes)
            
            if end_datetime.time() <= end_time:
                slot = TimeSlot(
                    current_time,
                    end_datetime.time(),
                    duration_minutes
                )
                
                # 检查是否与已使用时段冲突
                if not self._is_conflicting(slot, exclude):
                    available_slots.append(slot)
            
            # 下一个时间段（30分钟间隔）
            current_datetime += timedelta(minutes=30)
            current_time = current_datetime.time()
        
        return available_slots
    
    def _is_conflicting(
        self,
        slot: TimeSlot,
        used_slots: List[TimeSlot]
    ) -> bool:
        """检查时间段是否冲突"""
        for used in used_slots:
            # 简化的冲突检测
            if not (slot.end_time <= used.start_time or 
                   slot.start_time >= used.end_time):
                return True
        return False
    
    def _calculate_slot_score(
        self,
        slot: TimeSlot,
        task: Task,
        productivity_curve: List[ProductivityPattern],
        patterns: Dict[str, Any]
    ) -> float:
        """计算时间段得分"""
        # 基础得分：基于生产力曲线
        base_score = self.analyzer.calculate_time_slot_score(
            slot, task.task_type, productivity_curve
        )
        
        # 能量匹配度
        hour = slot.start_time.hour
        pattern = productivity_curve[hour]
        energy_match = 1.0 - abs(pattern.energy_level - task.energy_required)
        
        # 专注度匹配
        focus_match = 1.0 - abs(pattern.focus_level - task.focus_required)
        
        # 优先级加权
        priority_weight = {
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8
        }.get(task.priority, 1.0)
        
        # 截止时间压力
        deadline_pressure = 1.0
        if task.deadline:
            days_until = (task.deadline - datetime.now()).days
            if days_until <= 1:
                deadline_pressure = 1.3
            elif days_until <= 3:
                deadline_pressure = 1.1
        
        # 综合得分
        final_score = (
            base_score * 0.4 +
            energy_match * 0.2 +
            focus_match * 0.2 +
            task.flexibility * 0.1
        ) * priority_weight * deadline_pressure
        
        return min(1.0, final_score)
    
    def _find_best_slot(
        self,
        slots: List[TimeSlot],
        task: Task,
        productivity_curve: List[ProductivityPattern]
    ) -> TimeSlot:
        """找到最佳时间段"""
        best_slot = None
        best_score = -1
        
        for slot in slots:
            score = self.analyzer.calculate_time_slot_score(
                slot, task.task_type, productivity_curve
            )
            
            if score > best_score:
                best_score = score
                best_slot = slot
        
        return best_slot
    
    def _prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """任务优先级排序"""
        def priority_key(task: Task) -> tuple:
            priority_order = {"high": 0, "medium": 1, "low": 2}
            deadline_score = 0
            if task.deadline:
                days_until = (task.deadline - datetime.now()).days
                deadline_score = max(0, 100 - days_until)
            
            return (
                priority_order.get(task.priority, 1),
                -deadline_score,
                -task.duration_minutes
            )
        
        return sorted(tasks, key=priority_key)
    
    def _add_break_times(
        self,
        schedule: List[Dict],
        patterns: Dict[str, Any]
    ) -> List[Dict]:
        """添加休息时间"""
        schedule_with_breaks = []
        
        for i, item in enumerate(schedule):
            schedule_with_breaks.append(item)
            
            # 每90分钟工作后添加15分钟休息
            if i < len(schedule) - 1:
                current_end = item['slot'].end_time
                next_start = schedule[i + 1]['slot'].start_time
                
                # 如果间隔足够，添加休息
                gap_minutes = self._calculate_time_gap(current_end, next_start)
                if gap_minutes >= 15:
                    break_task = Task(
                        task_id=f"break_{i}",
                        title="休息",
                        task_type="rest",
                        duration_minutes=15,
                        priority="medium"
                    )
                    
                    break_slot = TimeSlot(
                        current_end,
                        self._add_minutes_to_time(current_end, 15),
                        15
                    )
                    
                    schedule_with_breaks.append({
                        "task": break_task,
                        "slot": break_slot,
                        "reason": "工作间隙，适当休息"
                    })
        
        return schedule_with_breaks
    
    def _calculate_time_gap(self, time1: time, time2: time) -> int:
        """计算两个时间点的间隔（分钟）"""
        dt1 = datetime.combine(datetime.today(), time1)
        dt2 = datetime.combine(datetime.today(), time2)
        return int((dt2 - dt1).total_seconds() / 60)
    
    def _add_minutes_to_time(self, t: time, minutes: int) -> time:
        """给时间加上分钟数"""
        dt = datetime.combine(datetime.today(), t)
        dt += timedelta(minutes=minutes)
        return dt.time()
    
    def _generate_timeline(
        self,
        schedule: List[Dict],
        date: datetime
    ) -> List[Dict[str, Any]]:
        """生成时间线视图"""
        timeline = []
        
        for item in schedule:
            timeline.append({
                "start": item['slot'].start_time.strftime("%H:%M"),
                "end": item['slot'].end_time.strftime("%H:%M"),
                "title": item['task'].title,
                "type": item['task'].task_type,
                "priority": item['task'].priority,
                "duration": item['slot'].duration_minutes
            })
        
        return timeline
    
    def _generate_reason(
        self,
        slot: TimeSlot,
        task: Task,
        productivity_curve: List[ProductivityPattern]
    ) -> str:
        """生成推荐理由 - 优先使用LLM"""
        
        # 尝试使用LLM生成推理
        try:
            llm_reason = self._generate_llm_reason(slot, task, productivity_curve)
            if llm_reason:
                return llm_reason
        except Exception as e:
            logger.debug(f"LLM推理失败，使用规则推理: {e}")
        
        # 降级：使用规则生成
        return self._generate_rule_based_reason(slot, task, productivity_curve)
    
    def _generate_llm_reason(
        self,
        slot: TimeSlot,
        task: Task,
        productivity_curve: List[ProductivityPattern]
    ) -> Optional[str]:
        """使用LLM生成推荐理由"""
        from backend.llm.llm_service import get_llm_service
        
        llm = get_llm_service()
        if not llm or not llm.enabled:
            return None
        
        hour = slot.start_time.hour
        pattern = productivity_curve[hour]
        
        prompt = f"""为用户的任务安排生成简短的推荐理由（30字以内）。

任务信息：
- 任务名称：{task.title}
- 任务类型：{task.task_type}
- 时长：{task.duration_minutes}分钟
- 优先级：{task.priority}

推荐时间：{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}

该时段特征：
- 生产力：{pattern.productivity_score:.0%}
- 专注度：{pattern.focus_level:.0%}
- 能量：{pattern.energy_level:.0%}

请用一句话（30字以内）说明为什么这个时间适合做这个任务。要温暖、实用。"""

        try:
            response = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.strip()
        except:
            return None
    
    def _generate_rule_based_reason(
        self,
        slot: TimeSlot,
        task: Task,
        productivity_curve: List[ProductivityPattern]
    ) -> str:
        """基于规则生成推荐理由（降级方案）"""
        hour = slot.start_time.hour
        pattern = productivity_curve[hour]
        
        reasons = []
        
        if pattern.productivity_score >= 0.8:
            reasons.append("这是你的高效时段")
        
        if pattern.energy_level >= 0.7 and task.task_type == "exercise":
            reasons.append("此时精力充沛，适合运动")
        
        if pattern.focus_level >= 0.8 and task.task_type in ["work", "study"]:
            reasons.append("此时专注度高，适合深度工作")
        
        if 12 <= hour <= 14 and task.task_type == "rest":
            reasons.append("午休时间，适当休息")
        
        if not reasons:
            reasons.append("根据你的习惯，这个时间比较合适")
        
        return "；".join(reasons)
    
    def _generate_summary(self, schedule: List[Dict]) -> Dict[str, Any]:
        """生成日程摘要"""
        total_tasks = len([s for s in schedule if s['task'].task_type != "rest"])
        total_work_time = sum(
            s['slot'].duration_minutes 
            for s in schedule 
            if s['task'].task_type in ["work", "study"]
        )
        total_break_time = sum(
            s['slot'].duration_minutes 
            for s in schedule 
            if s['task'].task_type == "rest"
        )
        
        return {
            "total_tasks": total_tasks,
            "total_work_minutes": total_work_time,
            "total_break_minutes": total_break_time,
            "work_break_ratio": round(total_work_time / max(1, total_break_time), 1)
        }
    
    def _generate_tips(
        self,
        schedule: List[Dict],
        patterns: Dict[str, Any]
    ) -> List[str]:
        """生成优化建议"""
        tips = []
        
        # 检查工作时长
        total_work = sum(
            s['slot'].duration_minutes 
            for s in schedule 
            if s['task'].task_type in ["work", "study"]
        )
        
        if total_work > 480:  # 超过8小时
            tips.append("今天的工作安排较满，注意劳逸结合")
        
        # 检查是否有运动
        has_exercise = any(
            s['task'].task_type == "exercise" 
            for s in schedule
        )
        if not has_exercise:
            tips.append("建议安排30分钟运动时间")
        
        # 检查是否有学习
        has_learning = any(
            s['task'].task_type == "study" 
            for s in schedule
        )
        if not has_learning:
            tips.append("可以安排一些学习时间，持续成长")
        
        return tips
    
    def _generate_weekly_summary(
        self,
        weekly_schedule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成周总结"""
        total_tasks = sum(
            day['summary']['total_tasks'] 
            for day in weekly_schedule.values()
        )
        
        total_work_hours = sum(
            day['summary']['total_work_minutes'] 
            for day in weekly_schedule.values()
        ) / 60
        
        return {
            "total_tasks": total_tasks,
            "total_work_hours": round(total_work_hours, 1),
            "average_daily_tasks": round(total_tasks / 7, 1),
            "average_daily_work_hours": round(total_work_hours / 7, 1)
        }
