"""
日程分析器 - 分析用户的时间使用习惯和生产力曲线
基于RAG系统和数据库的真实数据
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, time
from collections import defaultdict
import numpy as np
from dataclasses import dataclass


@dataclass
class TimeSlot:
    """时间段"""
    start_time: time
    end_time: time
    duration_minutes: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time.strftime("%H:%M"),
            "end_time": self.end_time.strftime("%H:%M"),
            "duration_minutes": self.duration_minutes
        }


@dataclass
class ProductivityPattern:
    """生产力模式"""
    hour: int  # 0-23
    productivity_score: float  # 0-1
    focus_level: float  # 0-1
    energy_level: float  # 0-1
    typical_activities: List[str]


class ScheduleAnalyzer:
    """日程分析器 - 基于真实数据"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 获取RAG系统和数据库
        from backend.startup_manager import StartupManager
        from backend.database.db_manager import db_manager
        
        # 使用决策导向的分析器
        from backend.schedule.decision_based_analyzer import DecisionBasedAnalyzer
        self.decision_analyzer = DecisionBasedAnalyzer(user_id)
        
        # 使用全局的 default_user RAG 系统（所有用户共享）
        self.rag_system = None
        try:
            # 优先尝试获取用户特定的RAG系统
            self.rag_system = StartupManager.get_user_system(user_id, 'rag')
            
            # 如果用户没有专属RAG，使用default_user的RAG（启动时已初始化）
            if not self.rag_system:
                self.rag_system = StartupManager.get_user_system('default_user', 'rag')
                if self.rag_system:
                    print(f"[日程分析] 使用全局RAG系统（default_user）")
                else:
                    print(f"[日程分析] ⚠️ RAG系统未初始化")
            else:
                print(f"[日程分析] 成功获取用户 {user_id} 的RAG系统")
        except Exception as e:
            print(f"[日程分析] RAG系统获取失败: {e}")
            import traceback
            traceback.print_exc()
            self.rag_system = None
        
        self.db_manager = db_manager
        
    def analyze_historical_patterns(
        self,
        history_days: int = 30
    ) -> Dict[str, Any]:
        """
        分析历史时间使用模式 - 优先使用决策导向分析
        
        Returns:
            {
                'decision_context': 决策上下文（优先）,
                'productivity_curve': 每小时生产力曲线（备用）,
                'peak_hours': 高效时段,
                'low_hours': 低效时段,
                'typical_schedule': 典型日程,
                'habits': 习惯分析
            }
        """
        print(f"[日程分析] 开始分析用户 {self.user_id} 的决策和时间模式...")
        
        # 1. 优先使用决策导向分析
        decision_context = self.decision_analyzer.analyze_decision_context()
        
        # 2. 如果有决策数据，基于决策生成日程
        if decision_context['action_items']:
            print(f"[日程分析] ✅ 基于决策数据: {len(decision_context['action_items'])} 个行动项")
            
            return {
                'decision_context': decision_context,
                'analysis_type': 'decision_based',
                'productivity_curve': self._get_default_productivity_curve(),  # 添加默认曲线
                'peak_hours': self._get_default_peak_hours(),
                'low_hours': self._get_default_low_hours(),
                'typical_schedule': self._generate_decision_based_schedule(decision_context),
                'habits': self._analyze_decision_habits(decision_context)
            }
        
        # 3. 如果没有决策数据，回退到传统分析（但仍然避免健康数据）
        print(f"[日程分析] ⚠️ 无决策数据，使用默认分析")
        
        return {
            'decision_context': decision_context,
            'analysis_type': 'default',
            'productivity_curve': self._get_default_productivity_curve(),
            'peak_hours': self._get_default_peak_hours(),
            'low_hours': self._get_default_low_hours(),
            'typical_schedule': self._get_default_schedule(),
            'habits': self._get_default_habits()
        }
    
    def _generate_decision_based_schedule(self, decision_context: Dict) -> Dict[str, Any]:
        """基于决策上下文生成典型日程"""
        priorities = decision_context.get('priorities', {})
        
        return {
            "wake_time": "07:00",
            "work_start": "09:00",
            "work_end": "18:00",
            "focus_time": "09:00-12:00",  # 高优先级决策任务
            "review_time": "14:00-16:00",  # 决策复盘和调整
            "planning_time": "20:00-21:00",  # 决策规划
            "priorities": priorities
        }
    
    def _analyze_decision_habits(self, decision_context: Dict) -> Dict[str, Any]:
        """基于决策上下文分析习惯"""
        action_items = decision_context.get('action_items', [])
        
        # 分析任务类型分布
        task_types = defaultdict(int)
        for item in action_items:
            category = item.get('category', 'other')
            task_types[category] += 1
        
        return {
            "decision_focused": True,
            "task_distribution": dict(task_types),
            "preferred_work_duration": 90,
            "preferred_break_duration": 15,
            "planning_frequency": "daily"
        }
    
    def _get_default_peak_hours(self) -> List[TimeSlot]:
        """获取默认高效时段"""
        return [
            TimeSlot(time(9, 0), time(12, 0), 180),
            TimeSlot(time(14, 0), time(17, 0), 180)
        ]
    
    def _get_default_low_hours(self) -> List[TimeSlot]:
        """获取默认低效时段"""
        return [
            TimeSlot(time(12, 0), time(14, 0), 120),
            TimeSlot(time(22, 0), time(6, 0), 480)
        ]
    
    def _get_default_productivity_curve(self) -> List[ProductivityPattern]:
        """获取默认生产力曲线"""
        curve = []
        base_pattern = {
            9: 0.9, 10: 0.95, 11: 0.9,
            14: 0.8, 15: 0.85, 16: 0.8,
            20: 0.6, 21: 0.5
        }
        
        for hour in range(24):
            productivity = base_pattern.get(hour, 0.3)
            curve.append(ProductivityPattern(
                hour=hour,
                productivity_score=productivity,
                focus_level=productivity,
                energy_level=productivity,
                typical_activities=self._get_typical_activities(hour)
            ))
        
        return curve
    
    def _get_default_schedule(self) -> Dict[str, Any]:
        """获取默认日程"""
        return {
            "wake_time": "07:00",
            "work_start": "09:00",
            "work_end": "18:00",
            "lunch_time": "12:00",
            "focus_time": "09:00-12:00",
            "planning_time": "20:00"
        }
    
    def _get_default_habits(self) -> Dict[str, Any]:
        """获取默认习惯"""
        return {
            "decision_focused": False,
            "preferred_work_duration": 90,
            "preferred_break_duration": 15,
            "planning_frequency": "weekly"
        }
    
    def _get_health_records(self, days: int = 30) -> List[Any]:
        """从数据库获取健康记录"""
        try:
            records = self.db_manager.get_health_records(self.user_id, limit=days * 10)
            print(f"[数据获取] 从数据库获取了 {len(records)} 条健康记录")
            return records
        except Exception as e:
            print(f"[数据获取] 获取健康记录失败: {e}")
            return []
    
    def _get_task_completions_from_rag(self) -> List[Dict]:
        """从RAG获取任务完成记录"""
        try:
            from backend.learning.production_rag_system import MemoryType
            
            if self.rag_system is None:
                print("[数据获取] RAG系统未初始化，跳过任务完成记录查询")
                return []
            
            # 查询任务完成记录
            results = self.rag_system.search(
                query="任务完成记录",
                memory_types=[MemoryType.TASK_COMPLETION],
                top_k=50
            )
            
            completions = []
            for result in results:
                # RAG返回的是UnifiedMemory对象，需要访问其属性
                if hasattr(result, 'content'):
                    completions.append({
                        'content': result.content,
                        'metadata': result.metadata if hasattr(result, 'metadata') else {},
                        'timestamp': result.metadata.get('timestamp') if hasattr(result, 'metadata') else None
                    })
                else:
                    # 如果是字典格式
                    completions.append({
                        'content': result.get('content', ''),
                        'metadata': result.get('metadata', {}),
                        'timestamp': result.get('metadata', {}).get('timestamp')
                    })
            
            print(f"[数据获取] 从RAG获取了 {len(completions)} 条任务完成记录")
            return completions
        except Exception as e:
            print(f"[数据获取] 从RAG获取任务完成记录失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_conversations_from_rag(self) -> List[Dict]:
        """从RAG获取对话记录"""
        try:
            from backend.learning.production_rag_system import MemoryType
            
            if self.rag_system is None:
                print("[数据获取] RAG系统未初始化，跳过对话记录查询")
                return []
            
            # 查询对话记录
            results = self.rag_system.search(
                query="日程 时间 安排",
                memory_types=[MemoryType.CONVERSATION],
                top_k=30
            )
            
            conversations = []
            for result in results:
                # RAG返回的是UnifiedMemory对象，需要访问其属性
                if hasattr(result, 'content'):
                    conversations.append({
                        'content': result.content,
                        'metadata': result.metadata if hasattr(result, 'metadata') else {},
                        'timestamp': result.metadata.get('timestamp') if hasattr(result, 'metadata') else None
                    })
                else:
                    # 如果是字典格式
                    conversations.append({
                        'content': result.get('content', ''),
                        'metadata': result.get('metadata', {}),
                        'timestamp': result.get('metadata', {}).get('timestamp')
                    })
            
            print(f"[数据获取] 从RAG获取了 {len(conversations)} 条相关对话")
            return conversations
        except Exception as e:
            print(f"[数据获取] 从RAG获取对话记录失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _calculate_productivity_curve_from_data(
        self,
        health_records: List[Any],
        task_completions: List[Dict],
        conversations: List[Dict]
    ) -> List[ProductivityPattern]:
        """基于真实数据计算生产力曲线"""
        
        # 初始化每小时的统计数据
        hourly_stats = defaultdict(lambda: {
            'energy_sum': 0,
            'focus_sum': 0,
            'task_count': 0,
            'activities': set()
        })
        
        # 数据来源标记
        has_health_data = len(health_records) > 0
        has_task_data = len(task_completions) > 0
        
        # 1. 从健康记录分析能量水平
        for record in health_records:
            try:
                timestamp = record.timestamp
                hour = timestamp.hour
                
                # 基于睡眠质量、运动、压力计算能量水平
                sleep_quality = getattr(record, 'sleep_quality', 7) / 10.0
                exercise = getattr(record, 'exercise_minutes', 0)
                stress = getattr(record, 'stress_level', 5)
                
                energy = (sleep_quality * 0.4 + 
                         min(1.0, exercise / 60) * 0.3 + 
                         (10 - stress) / 10 * 0.3)
                
                hourly_stats[hour]['energy_sum'] += energy
                hourly_stats[hour]['task_count'] += 1
                
            except Exception as e:
                continue
        
        # 2. 从任务完成记录分析专注度
        for completion in task_completions:
            try:
                metadata = completion.get('metadata', {})
                timestamp = metadata.get('timestamp')
                
                if timestamp:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromtimestamp(timestamp / 1000)
                    
                    hour = dt.hour
                    
                    # 任务完成表示该时段专注度高
                    completed = metadata.get('completed', True)
                    if completed:
                        hourly_stats[hour]['focus_sum'] += 1.0
                        hourly_stats[hour]['task_count'] += 1
                        
                        # 记录活动类型
                        task_type = metadata.get('task_type', 'work')
                        hourly_stats[hour]['activities'].add(task_type)
                
            except Exception as e:
                continue
        
        # 3. 生成生产力曲线
        curve = []
        hours_with_real_data = 0
        
        for hour in range(24):
            stats = hourly_stats[hour]
            count = stats['task_count']
            
            # 判断是否有真实数据
            has_real_data = count > 0
            if has_real_data:
                hours_with_real_data += 1
            
            # 计算平均值
            if has_real_data:
                energy = stats['energy_sum'] / count
                focus = stats['focus_sum'] / count
            else:
                # 使用默认值
                energy = self._get_default_energy(hour)
                focus = self._get_default_focus(hour)
            
            # 生产力 = 能量 * 0.5 + 专注度 * 0.5
            productivity = (energy * 0.5 + focus * 0.5)
            
            # 获取典型活动
            activities = list(stats['activities']) if stats['activities'] else self._get_typical_activities(hour)
            
            curve.append(ProductivityPattern(
                hour=hour,
                productivity_score=min(1.0, productivity),
                focus_level=min(1.0, focus),
                energy_level=min(1.0, energy),
                typical_activities=activities
            ))
        
        # 数据质量报告
        data_coverage = hours_with_real_data / 24 * 100
        if data_coverage < 30:
            print(f"⚠️  [数据质量] 仅 {data_coverage:.1f}% 的时段有真实数据，其余使用默认值")
            print(f"   健康记录: {len(health_records)} 条, 任务记录: {len(task_completions)} 条")
        else:
            print(f"✅ [数据质量] {data_coverage:.1f}% 的时段基于真实数据")
        
        return curve
    
    def _get_default_energy(self, hour: int) -> float:
        """获取默认能量水平（当没有数据时）"""
        # 基于生理规律的默认值
        if 6 <= hour < 10:
            return 0.7 + (hour - 6) * 0.05  # 早晨逐渐提升
        elif 10 <= hour < 12:
            return 0.9  # 上午高峰
        elif 12 <= hour < 14:
            return 0.5  # 午餐后低谷
        elif 14 <= hour < 17:
            return 0.8  # 下午恢复
        elif 17 <= hour < 20:
            return 0.6  # 傍晚下降
        elif 20 <= hour < 23:
            return 0.4  # 晚上
        else:
            return 0.1  # 夜间
    
    def _get_default_focus(self, hour: int) -> float:
        """获取默认专注度（当没有数据时）"""
        if 9 <= hour < 11:
            return 0.9  # 上午专注度高
        elif 14 <= hour < 16:
            return 0.8  # 下午次高
        elif 20 <= hour < 22:
            return 0.6  # 晚上中等
        else:
            return 0.3  # 其他时段较低
    
    def _analyze_typical_schedule_from_data(
        self,
        health_records: List[Any]
    ) -> Dict[str, Any]:
        """基于真实数据分析典型日程"""
        
        wake_times = []
        sleep_times = []
        
        for record in health_records:
            try:
                # 从睡眠数据推断作息时间
                sleep_hours = getattr(record, 'sleep_hours', 7)
                timestamp = record.timestamp
                
                # 简化推断：假设记录时间是醒来时间
                wake_times.append(timestamp.hour)
                
                # 推断睡眠时间
                sleep_hour = (timestamp.hour - int(sleep_hours)) % 24
                sleep_times.append(sleep_hour)
                
            except Exception as e:
                continue
        
        # 计算平均值
        if wake_times and sleep_times:
            avg_wake = int(np.mean(wake_times))
            avg_sleep = int(np.mean(sleep_times))
            print(f"✅ [作息分析] 基于 {len(wake_times)} 条记录: 平均起床 {avg_wake:02d}:00, 睡觉 {avg_sleep:02d}:00")
        else:
            avg_wake = 7
            avg_sleep = 23
            print(f"⚠️  [作息分析] 无真实数据，使用默认作息时间")
        
        return {
            "wake_time": f"{avg_wake:02d}:00",
            "sleep_time": f"{avg_sleep:02d}:00",
            "work_start": f"{avg_wake + 2:02d}:00",
            "work_end": "18:00",
            "lunch_time": "12:00",
            "dinner_time": "19:00",
            "exercise_time": f"{avg_wake:02d}:30",
            "learning_time": "20:00"
        }
    
    def _analyze_habits_from_data(
        self,
        health_records: List[Any],
        task_completions: List[Dict]
    ) -> Dict[str, Any]:
        """基于真实数据分析用户习惯"""
        
        # 分析运动频率
        exercise_days = 0
        total_days = len(set(r.timestamp.date() for r in health_records)) if health_records else 1
        
        for record in health_records:
            exercise_minutes = getattr(record, 'exercise_minutes', 0)
            if exercise_minutes > 0:
                exercise_days += 1
        
        exercise_freq = exercise_days / total_days if total_days > 0 else 0
        
        # 判断是否是早起型
        morning_tasks = sum(1 for c in task_completions 
                          if self._get_hour_from_completion(c) < 12)
        evening_tasks = sum(1 for c in task_completions 
                          if self._get_hour_from_completion(c) >= 18)
        
        is_morning_person = morning_tasks > evening_tasks
        is_night_owl = evening_tasks > morning_tasks * 1.5
        
        return {
            "morning_person": is_morning_person,
            "night_owl": is_night_owl,
            "exercise_frequency": "daily" if exercise_freq > 0.7 else "weekly" if exercise_freq > 0.3 else "rarely",
            "learning_frequency": "daily",
            "social_frequency": "weekly",
            "preferred_work_duration": 90,
            "preferred_break_duration": 15
        }
    
    def _get_hour_from_completion(self, completion: Dict) -> int:
        """从任务完成记录中提取小时"""
        try:
            metadata = completion.get('metadata', {})
            timestamp = metadata.get('timestamp')
            
            if timestamp:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromtimestamp(timestamp / 1000)
                return dt.hour
        except:
            pass
        return 12  # 默认值
    
    
    def _calculate_productivity_curve(self) -> List[ProductivityPattern]:
        """
        【已废弃】使用 _calculate_productivity_curve_from_data 替代
        保留此方法作为后备方案
        """
        curve = []
        base_pattern = {
            6: 0.3, 7: 0.5, 8: 0.7, 9: 0.9, 10: 0.95,
            11: 0.9, 12: 0.7, 13: 0.5, 14: 0.6, 15: 0.8,
            16: 0.85, 17: 0.8, 18: 0.6, 19: 0.5, 20: 0.4,
            21: 0.3, 22: 0.2, 23: 0.1, 0: 0.05, 1: 0.05,
            2: 0.05, 3: 0.05, 4: 0.1, 5: 0.2
        }
        
        for hour in range(24):
            productivity = base_pattern.get(hour, 0.5)
            focus = min(1.0, productivity + np.random.uniform(-0.1, 0.1))
            energy = min(1.0, productivity + np.random.uniform(-0.15, 0.15))
            activities = self._get_typical_activities(hour)
            
            curve.append(ProductivityPattern(
                hour=hour,
                productivity_score=productivity,
                focus_level=max(0, focus),
                energy_level=max(0, energy),
                typical_activities=activities
            ))
        
        return curve
    
    def _get_typical_activities(self, hour: int) -> List[str]:
        """获取该时段的典型活动"""
        if 6 <= hour < 9:
            return ["晨练", "早餐", "通勤"]
        elif 9 <= hour < 12:
            return ["深度工作", "会议", "学习"]
        elif 12 <= hour < 14:
            return ["午餐", "休息"]
        elif 14 <= hour < 18:
            return ["工作", "会议", "协作"]
        elif 18 <= hour < 20:
            return ["晚餐", "通勤", "休闲"]
        elif 20 <= hour < 23:
            return ["学习", "娱乐", "社交"]
        else:
            return ["睡眠"]
    
    def _identify_peak_hours(
        self,
        curve: List[ProductivityPattern]
    ) -> List[TimeSlot]:
        """识别高效时段（生产力>0.8）"""
        peak_slots = []
        
        for pattern in curve:
            if pattern.productivity_score >= 0.8:
                start = time(pattern.hour, 0)
                end = time((pattern.hour + 1) % 24, 0)
                peak_slots.append(TimeSlot(start, end, 60))
        
        # 合并连续时段
        return self._merge_time_slots(peak_slots)
    
    def _identify_low_hours(
        self,
        curve: List[ProductivityPattern]
    ) -> List[TimeSlot]:
        """识别低效时段（生产力<0.3）"""
        low_slots = []
        
        for pattern in curve:
            if pattern.productivity_score < 0.3:
                start = time(pattern.hour, 0)
                end = time((pattern.hour + 1) % 24, 0)
                low_slots.append(TimeSlot(start, end, 60))
        
        return self._merge_time_slots(low_slots)
    
    def _merge_time_slots(self, slots: List[TimeSlot]) -> List[TimeSlot]:
        """合并连续的时间段"""
        if not slots:
            return []
        
        merged = []
        current = slots[0]
        
        for next_slot in slots[1:]:
            # 检查是否连续
            if self._is_consecutive(current, next_slot):
                # 合并
                current = TimeSlot(
                    current.start_time,
                    next_slot.end_time,
                    current.duration_minutes + next_slot.duration_minutes
                )
            else:
                merged.append(current)
                current = next_slot
        
        merged.append(current)
        return merged
    
    def _is_consecutive(self, slot1: TimeSlot, slot2: TimeSlot) -> bool:
        """检查两个时间段是否连续"""
        # 简化处理：检查结束时间是否等于开始时间
        return slot1.end_time == slot2.start_time
    
    
    def _analyze_typical_schedule(self) -> Dict[str, Any]:
        """【已废弃】使用 _analyze_typical_schedule_from_data 替代"""
        return {
            "wake_time": "07:00",
            "sleep_time": "23:00",
            "work_start": "09:00",
            "work_end": "18:00",
            "lunch_time": "12:00",
            "dinner_time": "19:00",
            "exercise_time": "07:30",
            "learning_time": "20:00"
        }
    
    def _analyze_habits(self) -> Dict[str, Any]:
        """【已废弃】使用 _analyze_habits_from_data 替代"""
        return {
            "morning_person": True,
            "night_owl": False,
            "exercise_frequency": "daily",
            "learning_frequency": "daily",
            "social_frequency": "weekly",
            "preferred_work_duration": 90,
            "preferred_break_duration": 15
        }
    
    def calculate_time_slot_score(
        self,
        slot: TimeSlot,
        task_type: str,
        productivity_curve: List[ProductivityPattern]
    ) -> float:
        """
        计算时间段对特定任务类型的适配分数
        
        Args:
            slot: 时间段
            task_type: 任务类型（work, study, exercise, social, rest）
            productivity_curve: 生产力曲线
        
        Returns:
            适配分数 0-1
        """
        # 获取该时段的生产力数据
        hour = slot.start_time.hour
        pattern = productivity_curve[hour]
        
        # 根据任务类型计算分数
        if task_type in ["work", "study", "learning"]:
            # 需要高专注度和生产力
            score = (pattern.productivity_score * 0.5 + 
                    pattern.focus_level * 0.3 + 
                    pattern.energy_level * 0.2)
        
        elif task_type == "exercise":
            # 需要高能量
            score = pattern.energy_level
            # 早晨和傍晚加分
            if hour in [7, 8, 17, 18]:
                score += 0.2
        
        elif task_type == "social":
            # 晚上和周末更适合
            if 18 <= hour <= 22:
                score = 0.8
            else:
                score = 0.4
        
        elif task_type == "rest":
            # 低生产力时段更适合休息
            score = 1.0 - pattern.productivity_score
        
        else:
            score = 0.5
        
        return min(1.0, max(0.0, score))
