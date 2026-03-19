"""
健康领域分析器
分析睡眠债务、免疫力、健康分数等指标
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass


@dataclass
class HealthMetrics:
    """健康指标"""
    sleep_debt: float  # 睡眠债务（小时）
    immunity_score: float  # 免疫力分数（0-100）
    health_score: float  # 健康分数（0-100）
    fatigue_level: float  # 疲劳程度（0-10）
    recovery_status: str  # 恢复状态（excellent/good/fair/poor）
    risk_factors: List[str]  # 风险因素
    recommendations: List[str]  # 建议


class HealthAnalyzer:
    """健康领域分析器"""
    
    def __init__(self):
        self.sleep_target = 7.5  # 目标睡眠时间（小时）
        self.exercise_target = 150  # 目标运动时间（分钟/周）
        self.stress_threshold = 6.0  # 压力阈值
    
    def analyze(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> HealthMetrics:
        """分析健康指标"""
        
        # 计算睡眠债务
        sleep_debt = self._calculate_sleep_debt(history)
        
        # 计算免疫力分数
        immunity_score = self._calculate_immunity_score(user_data, history)
        
        # 计算健康分数
        health_score = self._calculate_health_score(user_data, history, sleep_debt, immunity_score)
        
        # 计算疲劳程度
        fatigue_level = self._calculate_fatigue_level(history, sleep_debt)
        
        # 判断恢复状态
        recovery_status = self._assess_recovery_status(health_score, fatigue_level, sleep_debt)
        
        # 识别风险因素
        risk_factors = self._identify_risk_factors(user_data, history, sleep_debt, immunity_score)
        
        # 生成建议
        recommendations = self._generate_recommendations(risk_factors, sleep_debt, immunity_score)
        
        return HealthMetrics(
            sleep_debt=sleep_debt,
            immunity_score=immunity_score,
            health_score=health_score,
            fatigue_level=fatigue_level,
            recovery_status=recovery_status,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _calculate_sleep_debt(self, history: List[Dict[str, Any]]) -> float:
        """计算睡眠债务"""
        if len(history) < 7:
            return 0.0
        
        recent_7_days = history[-7:]
        total_sleep = sum(h.get('sleep_hours', 0) for h in recent_7_days)
        target_sleep = self.sleep_target * 7
        
        sleep_debt = max(0, target_sleep - total_sleep)
        return round(sleep_debt, 1)
    
    def _calculate_immunity_score(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> float:
        """计算免疫力分数"""
        score = 100.0
        
        # 睡眠质量影响（30%）
        if history:
            avg_sleep_quality = np.mean([h.get('sleep_quality', 7) for h in history[-7:]])
            sleep_quality_score = (avg_sleep_quality / 10) * 30
            score -= (30 - sleep_quality_score)
        
        # 运动量影响（25%）
        if history:
            avg_exercise = np.mean([h.get('exercise_minutes', 0) for h in history[-7:]])
            exercise_score = min((avg_exercise / 30) * 25, 25)
            score -= (25 - exercise_score)
        
        # 压力水平影响（25%）
        if history:
            avg_stress = np.mean([h.get('stress_level', 5) for h in history[-7:]])
            stress_score = max(0, (10 - avg_stress) / 10 * 25)
            score -= (25 - stress_score)
        
        # 心率变异性影响（20%）
        if history:
            heart_rates = [h.get('heart_rate', 70) for h in history[-7:]]
            if len(heart_rates) > 1:
                hrv = np.std(heart_rates)
                hrv_score = min((hrv / 20) * 20, 20)
                score -= (20 - hrv_score)
        
        return max(0, min(100, round(score, 1)))
    
    def _calculate_health_score(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]],
        sleep_debt: float,
        immunity_score: float
    ) -> float:
        """计算综合健康分数"""
        score = 100.0
        
        # 睡眠债务惩罚（最多-30分）
        sleep_penalty = min(sleep_debt / 10 * 30, 30)
        score -= sleep_penalty
        
        # 免疫力贡献（最多-20分）
        immunity_penalty = (100 - immunity_score) / 100 * 20
        score -= immunity_penalty
        
        # 运动量贡献（最多-15分）
        if history:
            avg_exercise = np.mean([h.get('exercise_minutes', 0) for h in history[-7:]])
            exercise_penalty = max(0, (self.exercise_target / 7 - avg_exercise) / (self.exercise_target / 7) * 15)
            score -= exercise_penalty
        
        # 压力水平贡献（最多-20分）
        if history:
            avg_stress = np.mean([h.get('stress_level', 5) for h in history[-7:]])
            stress_penalty = max(0, (avg_stress - 5) / 5 * 20)
            score -= stress_penalty
        
        # 心率正常性贡献（最多-15分）
        if history:
            heart_rates = [h.get('heart_rate', 70) for h in history[-7:]]
            abnormal_count = sum(1 for hr in heart_rates if hr < 50 or hr > 100)
            abnormal_penalty = (abnormal_count / len(heart_rates)) * 15
            score -= abnormal_penalty
        
        return max(0, min(100, round(score, 1)))
    
    def _calculate_fatigue_level(self, history: List[Dict[str, Any]], sleep_debt: float) -> float:
        """计算疲劳程度（0-10）"""
        fatigue = 0.0
        
        # 睡眠债务贡献（最多5分）
        fatigue += min(sleep_debt / 10 * 5, 5)
        
        # 压力水平贡献（最多3分）
        if history:
            avg_stress = np.mean([h.get('stress_level', 5) for h in history[-3:]])
            fatigue += (avg_stress / 10) * 3
        
        # 运动过度贡献（最多2分）
        if history:
            recent_exercise = [h.get('exercise_minutes', 0) for h in history[-3:]]
            if np.mean(recent_exercise) > 60:
                fatigue += 2
        
        return min(10, round(fatigue, 1))
    
    def _assess_recovery_status(self, health_score: float, fatigue_level: float, sleep_debt: float) -> str:
        """判断恢复状态"""
        if health_score >= 85 and fatigue_level <= 2 and sleep_debt <= 2:
            return "excellent"
        elif health_score >= 70 and fatigue_level <= 4 and sleep_debt <= 5:
            return "good"
        elif health_score >= 50 and fatigue_level <= 6 and sleep_debt <= 10:
            return "fair"
        else:
            return "poor"
    
    def _identify_risk_factors(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]],
        sleep_debt: float,
        immunity_score: float
    ) -> List[str]:
        """识别风险因素"""
        risks = []
        
        if sleep_debt > 10:
            risks.append("严重睡眠不足")
        elif sleep_debt > 5:
            risks.append("睡眠债务累积")
        
        if immunity_score < 50:
            risks.append("免疫力严重下降")
        elif immunity_score < 70:
            risks.append("免疫力较弱")
        
        if history:
            avg_stress = np.mean([h.get('stress_level', 5) for h in history[-7:]])
            if avg_stress > 8:
                risks.append("压力过高")
            elif avg_stress > 6:
                risks.append("压力较高")
            
            avg_exercise = np.mean([h.get('exercise_minutes', 0) for h in history[-7:]])
            if avg_exercise < 30:
                risks.append("运动不足")
            
            heart_rates = [h.get('heart_rate', 70) for h in history[-7:]]
            abnormal_count = sum(1 for hr in heart_rates if hr < 50 or hr > 100)
            if abnormal_count > 2:
                risks.append("心率异常")
        
        return risks
    
    def _generate_recommendations(
        self,
        risk_factors: List[str],
        sleep_debt: float,
        immunity_score: float
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if "严重睡眠不足" in risk_factors:
            recommendations.append("立即改善睡眠，每晚至少8小时")
            recommendations.append("建立规律的睡眠时间表")
        elif "睡眠债务累积" in risk_factors:
            recommendations.append("逐步增加睡眠时间，每周增加30分钟")
        
        if "免疫力严重下降" in risk_factors:
            recommendations.append("增加运动强度和频率")
            recommendations.append("改善饮食，增加营养摄入")
            recommendations.append("考虑进行健康检查")
        elif "免疫力较弱" in risk_factors:
            recommendations.append("增加适度运动")
            recommendations.append("保证充足睡眠")
        
        if "压力过高" in risk_factors:
            recommendations.append("进行放松活动（冥想、瑜伽）")
            recommendations.append("减少工作压力，合理安排时间")
        
        if "运动不足" in risk_factors:
            recommendations.append("每天至少进行30分钟中等强度运动")
            recommendations.append("尝试新的运动方式，保持兴趣")
        
        if "心率异常" in risk_factors:
            recommendations.append("咨询医生进行心脏检查")
            recommendations.append("避免过度运动和压力")
        
        return recommendations

