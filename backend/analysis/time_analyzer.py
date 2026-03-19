"""
时间领域分析器
分析效率分数、认知负荷、时间压力等指标
"""
from typing import Dict, List, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class TimeMetrics:
    """时间指标"""
    efficiency_score: float  # 效率分数（0-100）
    cognitive_load: float  # 认知负荷（0-10）
    time_pressure: float  # 时间压力（0-1）
    focus_time: float  # 专注时间（小时/天）
    procrastination_level: float  # 拖延程度（0-10）
    time_allocation: Dict[str, float]  # 时间分配
    risk_factors: List[str]  # 风险因素
    recommendations: List[str]  # 建议


class TimeAnalyzer:
    """时间领域分析器"""
    
    def __init__(self):
        self.work_target = 8  # 目标工作时间（小时/天）
        self.focus_target = 6  # 目标专注时间（小时/天）
        self.break_target = 1  # 目标休息时间（小时/天）
    
    def analyze(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> TimeMetrics:
        """分析时间指标"""
        
        # 计算效率分数
        efficiency_score = self._calculate_efficiency_score(history)
        
        # 计算认知负荷
        cognitive_load = self._calculate_cognitive_load(user_data, history)
        
        # 计算时间压力
        time_pressure = self._calculate_time_pressure(history, cognitive_load)
        
        # 计算专注时间
        focus_time = self._calculate_focus_time(history)
        
        # 计算拖延程度
        procrastination_level = self._calculate_procrastination_level(history)
        
        # 分析时间分配
        time_allocation = self._analyze_time_allocation(history)
        
        # 识别风险因素
        risk_factors = self._identify_risk_factors(efficiency_score, cognitive_load, time_pressure, procrastination_level)
        
        # 生成建议
        recommendations = self._generate_recommendations(risk_factors, efficiency_score, time_allocation)
        
        return TimeMetrics(
            efficiency_score=efficiency_score,
            cognitive_load=cognitive_load,
            time_pressure=time_pressure,
            focus_time=focus_time,
            procrastination_level=procrastination_level,
            time_allocation=time_allocation,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _calculate_efficiency_score(self, history: List[Dict[str, Any]]) -> float:
        """计算效率分数"""
        if not history:
            return 50.0
        
        recent = history[-7:]
        
        # 基础分数
        score = 100.0
        
        # 工作时间充足性（30%）
        work_hours = [h.get('work_hours', 0) for h in recent]
        avg_work = np.mean(work_hours)
        work_score = min((avg_work / self.work_target) * 30, 30)
        score -= (30 - work_score)
        
        # 专注时间充足性（30%）
        focus_hours = [h.get('focus_time', 0) for h in recent]
        avg_focus = np.mean(focus_hours)
        focus_score = min((avg_focus / self.focus_target) * 30, 30)
        score -= (30 - focus_score)
        
        # 任务完成率（20%）
        completion_rates = [h.get('task_completion_rate', 0.5) for h in recent]
        avg_completion = np.mean(completion_rates)
        completion_score = avg_completion * 20
        score -= (20 - completion_score)
        
        # 中断次数（20%）
        interruptions = [h.get('interruptions', 0) for h in recent]
        avg_interruptions = np.mean(interruptions)
        interruption_penalty = min((avg_interruptions / 10) * 20, 20)
        score -= interruption_penalty
        
        return max(0, min(100, round(score, 1)))
    
    def _calculate_cognitive_load(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> float:
        """计算认知负荷（0-10）"""
        load = 0.0
        
        if not history:
            return 5.0
        
        recent = history[-7:]
        
        # 任务数量贡献（最多3分）
        task_counts = [h.get('task_count', 0) for h in recent]
        avg_tasks = np.mean(task_counts)
        task_load = min((avg_tasks / 10) * 3, 3)
        load += task_load
        
        # 工作时间贡献（最多3分）
        work_hours = [h.get('work_hours', 0) for h in recent]
        avg_work = np.mean(work_hours)
        work_load = min((avg_work / 12) * 3, 3)
        load += work_load
        
        # 中断频率贡献（最多2分）
        interruptions = [h.get('interruptions', 0) for h in recent]
        avg_interruptions = np.mean(interruptions)
        interruption_load = min((avg_interruptions / 10) * 2, 2)
        load += interruption_load
        
        # 压力水平贡献（最多2分）
        stress_levels = [h.get('stress_level', 5) for h in recent]
        avg_stress = np.mean(stress_levels)
        stress_load = (avg_stress / 10) * 2
        load += stress_load
        
        return min(10, round(load, 1))
    
    def _calculate_time_pressure(self, history: List[Dict[str, Any]], cognitive_load: float) -> float:
        """计算时间压力（0-1）"""
        if not history:
            return 0.5
        
        recent = history[-7:]
        
        # 基础压力
        pressure = 0.0
        
        # 工作时间超标（最多0.4）
        work_hours = [h.get('work_hours', 0) for h in recent]
        avg_work = np.mean(work_hours)
        if avg_work > self.work_target:
            pressure += min((avg_work - self.work_target) / self.work_target * 0.4, 0.4)
        
        # 任务堆积（最多0.3）
        task_counts = [h.get('task_count', 0) for h in recent]
        avg_tasks = np.mean(task_counts)
        if avg_tasks > 5:
            pressure += min((avg_tasks - 5) / 10 * 0.3, 0.3)
        
        # 认知负荷贡献（最多0.3）
        pressure += (cognitive_load / 10) * 0.3
        
        return min(1.0, round(pressure, 2))
    
    def _calculate_focus_time(self, history: List[Dict[str, Any]]) -> float:
        """计算专注时间（小时/天）"""
        if not history:
            return 0.0
        
        focus_times = [h.get('focus_time', 0) for h in history[-7:]]
        return round(np.mean(focus_times), 1)
    
    def _calculate_procrastination_level(self, history: List[Dict[str, Any]]) -> float:
        """计算拖延程度（0-10）"""
        if not history:
            return 5.0
        
        recent = history[-7:]
        
        procrastination = 0.0
        
        # 任务延迟率（最多5分）
        delay_rates = [h.get('task_delay_rate', 0) for h in recent]
        avg_delay = np.mean(delay_rates)
        procrastination += avg_delay * 5
        
        # 最后期限前完成率（最多3分）
        completion_rates = [h.get('last_minute_completion_rate', 0) for h in recent]
        avg_last_minute = np.mean(completion_rates)
        procrastination += avg_last_minute * 3
        
        # 计划执行率（最多2分）
        plan_adherence = [h.get('plan_adherence_rate', 1) for h in recent]
        avg_adherence = np.mean(plan_adherence)
        procrastination += (1 - avg_adherence) * 2
        
        return min(10, round(procrastination, 1))
    
    def _analyze_time_allocation(self, history: List[Dict[str, Any]]) -> Dict[str, float]:
        """分析时间分配"""
        if not history:
            return {
                "work": 0,
                "sleep": 0,
                "exercise": 0,
                "social": 0,
                "leisure": 0,
                "other": 0
            }
        
        recent = history[-7:]
        
        return {
            "work": round(np.mean([h.get('work_hours', 0) for h in recent]), 1),
            "sleep": round(np.mean([h.get('sleep_hours', 0) for h in recent]), 1),
            "exercise": round(np.mean([h.get('exercise_minutes', 0) / 60 for h in recent]), 1),
            "social": round(np.mean([h.get('social_hours', 0) for h in recent]), 1),
            "leisure": round(np.mean([h.get('leisure_hours', 0) for h in recent]), 1),
            "other": round(24 - np.mean([h.get('work_hours', 0) + h.get('sleep_hours', 0) + h.get('exercise_minutes', 0) / 60 + h.get('social_hours', 0) + h.get('leisure_hours', 0) for h in recent]), 1)
        }
    
    def _identify_risk_factors(
        self,
        efficiency_score: float,
        cognitive_load: float,
        time_pressure: float,
        procrastination_level: float
    ) -> List[str]:
        """识别风险因素"""
        risks = []
        
        if efficiency_score < 50:
            risks.append("效率严重下降")
        elif efficiency_score < 70:
            risks.append("效率较低")
        
        if cognitive_load > 8:
            risks.append("认知负荷过高")
        elif cognitive_load > 6:
            risks.append("认知负荷较高")
        
        if time_pressure > 0.8:
            risks.append("时间压力极大")
        elif time_pressure > 0.6:
            risks.append("时间压力较大")
        
        if procrastination_level > 7:
            risks.append("严重拖延")
        elif procrastination_level > 5:
            risks.append("拖延倾向明显")
        
        return risks
    
    def _generate_recommendations(
        self,
        risk_factors: List[str],
        efficiency_score: float,
        time_allocation: Dict[str, float]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if "效率严重下降" in risk_factors:
            recommendations.append("进行深度分析，找出效率下降的原因")
            recommendations.append("尝试番茄工作法，提高专注力")
        elif "效率较低" in risk_factors:
            recommendations.append("优化工作流程，减少不必要的步骤")
            recommendations.append("增加休息时间，恢复精力")
        
        if "认知负荷过高" in risk_factors:
            recommendations.append("减少同时进行的任务数量")
            recommendations.append("优先完成重要任务")
        
        if "时间压力极大" in risk_factors:
            recommendations.append("重新评估任务优先级")
            recommendations.append("考虑寻求帮助或委派任务")
        
        if "严重拖延" in risk_factors:
            recommendations.append("将大任务分解为小任务")
            recommendations.append("设置明确的截止时间")
        elif "拖延倾向明显" in risk_factors:
            recommendations.append("建立每日计划，按时执行")
            recommendations.append("使用任务管理工具追踪进度")
        
        if time_allocation["sleep"] < 7:
            recommendations.append("增加睡眠时间，改善精力")
        
        if time_allocation["exercise"] < 0.5:
            recommendations.append("增加运动时间，提升活力")
        
        return recommendations

