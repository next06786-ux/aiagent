"""
情绪领域分析器
分析情绪稳定性、调节能力、风险预警等指标
"""
from typing import Dict, List, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class EmotionMetrics:
    """情绪指标"""
    mood_score: float  # 心情分数（0-10）
    emotional_stability: float  # 情绪稳定性（0-100）
    regulation_ability: float  # 调节能力（0-100）
    risk_level: str  # 风险等级（low/medium/high/critical）
    mood_trend: str  # 心情趋势（improving/stable/declining）
    emotional_patterns: Dict[str, Any]  # 情绪模式
    risk_factors: List[str]  # 风险因素
    recommendations: List[str]  # 建议


class EmotionAnalyzer:
    """情绪领域分析器"""
    
    def __init__(self):
        self.mood_threshold_low = 3.0  # 低心情阈值
        self.mood_threshold_high = 8.0  # 高心情阈值
        self.stability_threshold = 2.0  # 稳定性阈值
    
    def analyze(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> EmotionMetrics:
        """分析情绪指标"""
        
        # 计算心情分数
        mood_score = self._calculate_mood_score(history)
        
        # 计算情绪稳定性
        emotional_stability = self._calculate_emotional_stability(history)
        
        # 计算调节能力
        regulation_ability = self._calculate_regulation_ability(history)
        
        # 评估风险等级
        risk_level = self._assess_risk_level(mood_score, emotional_stability, history)
        
        # 分析心情趋势
        mood_trend = self._analyze_mood_trend(history)
        
        # 识别情绪模式
        emotional_patterns = self._identify_emotional_patterns(history)
        
        # 识别风险因素
        risk_factors = self._identify_risk_factors(mood_score, emotional_stability, regulation_ability, history)
        
        # 生成建议
        recommendations = self._generate_recommendations(risk_level, risk_factors, emotional_patterns)
        
        return EmotionMetrics(
            mood_score=mood_score,
            emotional_stability=emotional_stability,
            regulation_ability=regulation_ability,
            risk_level=risk_level,
            mood_trend=mood_trend,
            emotional_patterns=emotional_patterns,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _calculate_mood_score(self, history: List[Dict[str, Any]]) -> float:
        """计算心情分数（0-10）"""
        if not history:
            return 5.0
        
        recent = history[-7:]
        mood_scores = [h.get('mood', 5) for h in recent]
        return round(np.mean(mood_scores), 1)
    
    def _calculate_emotional_stability(self, history: List[Dict[str, Any]]) -> float:
        """计算情绪稳定性（0-100）"""
        if len(history) < 7:
            return 50.0
        
        recent = history[-7:]
        mood_scores = [h.get('mood', 5) for h in recent]
        
        # 计算标准差（越小越稳定）
        std_dev = np.std(mood_scores)
        
        # 转换为稳定性分数（0-100）
        # std_dev = 0 -> 100分（完全稳定）
        # std_dev = 5 -> 0分（完全不稳定）
        stability = max(0, 100 - (std_dev / 5 * 100))
        
        return round(stability, 1)
    
    def _calculate_regulation_ability(self, history: List[Dict[str, Any]]) -> float:
        """计算调节能力（0-100）"""
        if len(history) < 7:
            return 50.0
        
        recent = history[-7:]
        
        ability = 100.0
        
        # 情绪恢复能力（40%）
        # 检查是否能从低谷恢复
        mood_scores = [h.get('mood', 5) for h in recent]
        low_points = [i for i, m in enumerate(mood_scores) if m < 4]
        
        if low_points:
            recovery_score = 0.0
            for low_idx in low_points:
                if low_idx < len(mood_scores) - 1:
                    recovery = mood_scores[low_idx + 1] - mood_scores[low_idx]
                    recovery_score += max(0, recovery)
            recovery_score = min(recovery_score / len(low_points), 5)
            recovery_ability = (recovery_score / 5) * 40
        else:
            recovery_ability = 40
        
        ability -= (40 - recovery_ability)
        
        # 情绪波动控制（30%）
        # 检查是否能控制情绪波动
        mood_changes = [abs(mood_scores[i] - mood_scores[i-1]) for i in range(1, len(mood_scores))]
        avg_change = np.mean(mood_changes)
        
        # 平均变化 < 1 -> 100分，> 3 -> 0分
        change_control = max(0, 100 - (avg_change / 3 * 100))
        control_ability = (change_control / 100) * 30
        ability -= (30 - control_ability)
        
        # 积极情绪维持（30%）
        # 检查是否能维持积极情绪
        positive_count = sum(1 for m in mood_scores if m >= 7)
        positive_ratio = positive_count / len(mood_scores)
        positive_ability = positive_ratio * 30
        ability -= (30 - positive_ability)
        
        return max(0, min(100, round(ability, 1)))
    
    def _assess_risk_level(self, mood_score: float, emotional_stability: float, history: List[Dict[str, Any]]) -> str:
        """评估风险等级"""
        
        # 检查是否有持续低谷
        if history:
            recent = history[-7:]
            low_mood_count = sum(1 for h in recent if h.get('mood', 5) < 3)
            
            if low_mood_count >= 5:
                return "critical"
            elif low_mood_count >= 3:
                return "high"
        
        # 基于心情分数和稳定性
        if mood_score < 3 or emotional_stability < 30:
            return "critical"
        elif mood_score < 4 or emotional_stability < 50:
            return "high"
        elif mood_score < 5.5 or emotional_stability < 70:
            return "medium"
        else:
            return "low"
    
    def _analyze_mood_trend(self, history: List[Dict[str, Any]]) -> str:
        """分析心情趋势"""
        if len(history) < 7:
            return "stable"
        
        recent = history[-7:]
        mood_scores = [h.get('mood', 5) for h in recent]
        
        # 计算趋势
        first_half = np.mean(mood_scores[:3])
        second_half = np.mean(mood_scores[4:])
        
        change = second_half - first_half
        
        if change > 1:
            return "improving"
        elif change < -1:
            return "declining"
        else:
            return "stable"
    
    def _identify_emotional_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """识别情绪模式"""
        patterns = {
            "dominant_mood": "neutral",
            "mood_cycle": "irregular",
            "trigger_factors": [],
            "recovery_time": 0
        }
        
        if not history:
            return patterns
        
        recent = history[-14:]  # 查看最近两周
        mood_scores = [h.get('mood', 5) for h in recent]
        
        # 主导情绪
        avg_mood = np.mean(mood_scores)
        if avg_mood >= 7:
            patterns["dominant_mood"] = "positive"
        elif avg_mood <= 4:
            patterns["dominant_mood"] = "negative"
        else:
            patterns["dominant_mood"] = "neutral"
        
        # 情绪周期
        if len(mood_scores) >= 7:
            first_week = mood_scores[:7]
            second_week = mood_scores[7:]
            
            # 简单的周期检测
            if np.corrcoef(first_week, second_week)[0, 1] > 0.7:
                patterns["mood_cycle"] = "weekly"
            else:
                patterns["mood_cycle"] = "irregular"
        
        # 触发因素（从历史数据推断）
        low_mood_indices = [i for i, m in enumerate(mood_scores) if m < 4]
        if low_mood_indices:
            for idx in low_mood_indices:
                if idx < len(history):
                    record = history[idx]
                    if record.get('stress_level', 5) > 7:
                        patterns["trigger_factors"].append("高压力")
                    if record.get('sleep_hours', 7) < 6:
                        patterns["trigger_factors"].append("睡眠不足")
                    if record.get('social_hours', 0) < 1:
                        patterns["trigger_factors"].append("社交缺乏")
        
        # 恢复时间
        recovery_times = []
        for idx in low_mood_indices:
            if idx < len(mood_scores) - 1:
                for j in range(idx + 1, len(mood_scores)):
                    if mood_scores[j] >= 6:
                        recovery_times.append(j - idx)
                        break
        
        if recovery_times:
            patterns["recovery_time"] = int(np.mean(recovery_times))
        
        return patterns
    
    def _identify_risk_factors(
        self,
        mood_score: float,
        emotional_stability: float,
        regulation_ability: float,
        history: List[Dict[str, Any]]
    ) -> List[str]:
        """识别风险因素"""
        risks = []
        
        if mood_score < 3:
            risks.append("严重抑郁倾向")
        elif mood_score < 4:
            risks.append("心情持续低落")
        elif mood_score < 5:
            risks.append("心情较差")
        
        if emotional_stability < 30:
            risks.append("情绪极度不稳定")
        elif emotional_stability < 50:
            risks.append("情绪波动较大")
        
        if regulation_ability < 30:
            risks.append("情绪调节能力严重不足")
        elif regulation_ability < 50:
            risks.append("情绪调节能力较弱")
        
        if history:
            recent = history[-7:]
            low_mood_count = sum(1 for h in recent if h.get('mood', 5) < 3)
            if low_mood_count >= 3:
                risks.append("持续低谷风险")
            
            # 检查是否有其他风险因素
            avg_stress = np.mean([h.get('stress_level', 5) for h in recent])
            if avg_stress > 8:
                risks.append("压力过高加重情绪问题")
            
            avg_sleep = np.mean([h.get('sleep_hours', 7) for h in recent])
            if avg_sleep < 6:
                risks.append("睡眠不足影响情绪")
        
        return risks
    
    def _generate_recommendations(
        self,
        risk_level: str,
        risk_factors: List[str],
        emotional_patterns: Dict[str, Any]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if risk_level == "critical":
            recommendations.append("立即寻求专业心理咨询")
            recommendations.append("考虑进行心理治疗")
            recommendations.append("告知信任的人，获得支持")
        elif risk_level == "high":
            recommendations.append("主动寻求心理咨询")
            recommendations.append("增加社交活动，获得情感支持")
        elif risk_level == "medium":
            recommendations.append("进行放松活动（冥想、瑜伽）")
            recommendations.append("增加户外活动时间")
        
        if "严重抑郁倾向" in risk_factors:
            recommendations.append("立即咨询医生或心理医生")
        elif "心情持续低落" in risk_factors:
            recommendations.append("进行积极的心理干预")
            recommendations.append("参加兴趣小组或社区活动")
        
        if "情绪极度不稳定" in risk_factors:
            recommendations.append("建立规律的日常作息")
            recommendations.append("避免过度刺激的环境")
        elif "情绪波动较大" in risk_factors:
            recommendations.append("学习情绪管理技巧")
            recommendations.append("进行冥想或深呼吸练习")
        
        if "压力过高加重情绪问题" in risk_factors:
            recommendations.append("减少工作压力，合理安排时间")
            recommendations.append("进行压力释放活动")
        
        if "睡眠不足影响情绪" in risk_factors:
            recommendations.append("改善睡眠质量，每晚至少7小时")
            recommendations.append("建立规律的睡眠时间表")
        
        # 基于情绪模式的建议
        if "高压力" in emotional_patterns.get("trigger_factors", []):
            recommendations.append("识别压力来源，制定应对策略")
        
        if "社交缺乏" in emotional_patterns.get("trigger_factors", []):
            recommendations.append("主动安排社交活动，扩展社交圈子")
        
        return recommendations

