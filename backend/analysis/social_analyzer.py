"""
社交领域分析器
分析孤独感、满意度、关系质量等指标
"""
from typing import Dict, List, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class SocialMetrics:
    """社交指标"""
    loneliness_score: float  # 孤独感分数（0-10）
    satisfaction_score: float  # 满意度分数（0-100）
    relationship_quality: float  # 关系质量（0-100）
    social_engagement: float  # 社交参与度（0-100）
    support_network_strength: float  # 支持网络强度（0-100）
    social_patterns: Dict[str, Any]  # 社交模式
    risk_factors: List[str]  # 风险因素
    recommendations: List[str]  # 建议


class SocialAnalyzer:
    """社交领域分析器"""
    
    def __init__(self):
        self.social_target = 2.0  # 目标社交时间（小时/天）
        self.interaction_target = 5  # 目标互动次数（次/天）
    
    def analyze(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> SocialMetrics:
        """分析社交指标"""
        
        # 计算孤独感
        loneliness_score = self._calculate_loneliness_score(history)
        
        # 计算满意度
        satisfaction_score = self._calculate_satisfaction_score(history)
        
        # 计算关系质量
        relationship_quality = self._calculate_relationship_quality(history)
        
        # 计算社交参与度
        social_engagement = self._calculate_social_engagement(history)
        
        # 计算支持网络强度
        support_network_strength = self._calculate_support_network_strength(history)
        
        # 识别社交模式
        social_patterns = self._identify_social_patterns(history)
        
        # 识别风险因素
        risk_factors = self._identify_risk_factors(loneliness_score, satisfaction_score, relationship_quality, social_engagement)
        
        # 生成建议
        recommendations = self._generate_recommendations(risk_factors, social_patterns)
        
        return SocialMetrics(
            loneliness_score=loneliness_score,
            satisfaction_score=satisfaction_score,
            relationship_quality=relationship_quality,
            social_engagement=social_engagement,
            support_network_strength=support_network_strength,
            social_patterns=social_patterns,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _calculate_loneliness_score(self, history: List[Dict[str, Any]]) -> float:
        """计算孤独感分数（0-10）"""
        if not history:
            return 5.0
        
        recent = history[-7:]
        
        loneliness = 0.0
        
        # 社交时间不足（最多4分）
        social_hours = [h.get('social_hours', 0) for h in recent]
        avg_social = np.mean(social_hours)
        if avg_social < self.social_target:
            loneliness += (self.social_target - avg_social) / self.social_target * 4
        
        # 互动频率不足（最多3分）
        interactions = [h.get('social_interactions', 0) for h in recent]
        avg_interactions = np.mean(interactions)
        if avg_interactions < self.interaction_target:
            loneliness += (self.interaction_target - avg_interactions) / self.interaction_target * 3
        
        # 主观孤独感（最多3分）
        loneliness_ratings = [h.get('loneliness', 5) for h in recent]
        avg_loneliness = np.mean(loneliness_ratings)
        loneliness += (avg_loneliness / 10) * 3
        
        return min(10, round(loneliness, 1))
    
    def _calculate_satisfaction_score(self, history: List[Dict[str, Any]]) -> float:
        """计算满意度分数（0-100）"""
        if not history:
            return 50.0
        
        recent = history[-7:]
        
        score = 100.0
        
        # 社交质量（40%）
        quality_ratings = [h.get('social_quality', 5) for h in recent]
        avg_quality = np.mean(quality_ratings)
        quality_score = (avg_quality / 10) * 40
        score -= (40 - quality_score)
        
        # 社交频率（30%）
        social_hours = [h.get('social_hours', 0) for h in recent]
        avg_social = np.mean(social_hours)
        frequency_score = min((avg_social / self.social_target) * 30, 30)
        score -= (30 - frequency_score)
        
        # 关系深度（30%）
        depth_ratings = [h.get('relationship_depth', 5) for h in recent]
        avg_depth = np.mean(depth_ratings)
        depth_score = (avg_depth / 10) * 30
        score -= (30 - depth_score)
        
        return max(0, min(100, round(score, 1)))
    
    def _calculate_relationship_quality(self, history: List[Dict[str, Any]]) -> float:
        """计算关系质量（0-100）"""
        if not history:
            return 50.0
        
        recent = history[-7:]
        
        quality = 100.0
        
        # 信任度（30%）
        trust_ratings = [h.get('trust_level', 7) for h in recent]
        avg_trust = np.mean(trust_ratings)
        trust_score = (avg_trust / 10) * 30
        quality -= (30 - trust_score)
        
        # 支持度（30%）
        support_ratings = [h.get('support_level', 7) for h in recent]
        avg_support = np.mean(support_ratings)
        support_score = (avg_support / 10) * 30
        quality -= (30 - support_score)
        
        # 冲突频率（20%）
        conflicts = [h.get('conflicts', 0) for h in recent]
        avg_conflicts = np.mean(conflicts)
        conflict_penalty = min((avg_conflicts / 5) * 20, 20)
        quality -= conflict_penalty
        
        # 互动质量（20%）
        interaction_quality = [h.get('interaction_quality', 7) for h in recent]
        avg_interaction = np.mean(interaction_quality)
        interaction_score = (avg_interaction / 10) * 20
        quality -= (20 - interaction_score)
        
        return max(0, min(100, round(quality, 1)))
    
    def _calculate_social_engagement(self, history: List[Dict[str, Any]]) -> float:
        """计算社交参与度（0-100）"""
        if not history:
            return 50.0
        
        recent = history[-7:]
        
        engagement = 100.0
        
        # 活动参与（40%）
        activities = [h.get('social_activities', 0) for h in recent]
        avg_activities = np.mean(activities)
        activity_score = min((avg_activities / 3) * 40, 40)
        engagement -= (40 - activity_score)
        
        # 主动性（30%）
        initiative = [h.get('social_initiative', 5) for h in recent]
        avg_initiative = np.mean(initiative)
        initiative_score = (avg_initiative / 10) * 30
        engagement -= (30 - initiative_score)
        
        # 多样性（30%）
        diversity = [h.get('social_diversity', 5) for h in recent]
        avg_diversity = np.mean(diversity)
        diversity_score = (avg_diversity / 10) * 30
        engagement -= (30 - diversity_score)
        
        return max(0, min(100, round(engagement, 1)))
    
    def _calculate_support_network_strength(self, history: List[Dict[str, Any]]) -> float:
        """计算支持网络强度（0-100）"""
        if not history:
            return 50.0
        
        recent = history[-7:]
        
        strength = 100.0
        
        # 网络规模（30%）
        network_size = [h.get('network_size', 5) for h in recent]
        avg_size = np.mean(network_size)
        size_score = min((avg_size / 10) * 30, 30)
        strength -= (30 - size_score)
        
        # 关系紧密度（40%）
        closeness = [h.get('relationship_closeness', 5) for h in recent]
        avg_closeness = np.mean(closeness)
        closeness_score = (avg_closeness / 10) * 40
        strength -= (40 - closeness_score)
        
        # 可用性（30%）
        availability = [h.get('support_availability', 7) for h in recent]
        avg_availability = np.mean(availability)
        availability_score = (avg_availability / 10) * 30
        strength -= (30 - availability_score)
        
        return max(0, min(100, round(strength, 1)))
    
    def _identify_social_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """识别社交模式"""
        patterns = {
            "social_type": "balanced",
            "preferred_time": "evening",
            "interaction_style": "moderate",
            "network_trend": "stable"
        }
        
        if not history:
            return patterns
        
        recent = history[-14:]
        
        # 社交类型
        social_hours = [h.get('social_hours', 0) for h in recent]
        avg_social = np.mean(social_hours)
        
        if avg_social > 4:
            patterns["social_type"] = "extroverted"
        elif avg_social < 1:
            patterns["social_type"] = "introverted"
        else:
            patterns["social_type"] = "balanced"
        
        # 偏好时间（简化实现）
        patterns["preferred_time"] = "evening"
        
        # 互动风格
        interactions = [h.get('social_interactions', 0) for h in recent]
        avg_interactions = np.mean(interactions)
        
        if avg_interactions > 10:
            patterns["interaction_style"] = "highly_active"
        elif avg_interactions < 3:
            patterns["interaction_style"] = "reserved"
        else:
            patterns["interaction_style"] = "moderate"
        
        # 网络趋势
        if len(social_hours) >= 7:
            first_week = np.mean(social_hours[:7])
            second_week = np.mean(social_hours[7:])
            
            change = second_week - first_week
            if change > 1:
                patterns["network_trend"] = "expanding"
            elif change < -1:
                patterns["network_trend"] = "shrinking"
            else:
                patterns["network_trend"] = "stable"
        
        return patterns
    
    def _identify_risk_factors(
        self,
        loneliness_score: float,
        satisfaction_score: float,
        relationship_quality: float,
        social_engagement: float
    ) -> List[str]:
        """识别风险因素"""
        risks = []
        
        if loneliness_score > 8:
            risks.append("严重孤独感")
        elif loneliness_score > 6:
            risks.append("孤独感较强")
        
        if satisfaction_score < 30:
            risks.append("社交满意度极低")
        elif satisfaction_score < 50:
            risks.append("社交满意度较低")
        
        if relationship_quality < 40:
            risks.append("关系质量严重不佳")
        elif relationship_quality < 60:
            risks.append("关系质量较差")
        
        if social_engagement < 30:
            risks.append("社交参与度极低")
        elif social_engagement < 50:
            risks.append("社交参与度不足")
        
        return risks
    
    def _generate_recommendations(
        self,
        risk_factors: List[str],
        social_patterns: Dict[str, Any]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if "严重孤独感" in risk_factors:
            recommendations.append("立即主动联系朋友或家人")
            recommendations.append("参加社区活动或兴趣小组")
            recommendations.append("考虑寻求心理咨询")
        elif "孤独感较强" in risk_factors:
            recommendations.append("增加社交活动频率")
            recommendations.append("主动安排与朋友的聚会")
        
        if "社交满意度极低" in risk_factors:
            recommendations.append("重新评估社交关系，寻找更有意义的连接")
            recommendations.append("尝试新的社交方式或圈子")
        elif "社交满意度较低" in risk_factors:
            recommendations.append("提升社交质量，深化现有关系")
        
        if "关系质量严重不佳" in risk_factors:
            recommendations.append("与重要的人进行深度沟通")
            recommendations.append("考虑关系咨询或调解")
        elif "关系质量较差" in risk_factors:
            recommendations.append("增加与亲密朋友的互动时间")
            recommendations.append("学习沟通技巧，改善关系")
        
        if "社交参与度极低" in risk_factors:
            recommendations.append("设定每周社交目标，逐步增加")
            recommendations.append("从小型活动开始，逐步扩展")
        elif "社交参与度不足" in risk_factors:
            recommendations.append("主动参加感兴趣的活动")
            recommendations.append("扩展社交圈子，认识新朋友")
        
        # 基于社交模式的建议
        if social_patterns["social_type"] == "introverted":
            recommendations.append("选择小型、深度的社交活动")
        elif social_patterns["social_type"] == "extroverted":
            recommendations.append("保持社交活力，但注意休息")
        
        if social_patterns["network_trend"] == "shrinking":
            recommendations.append("主动维护现有关系，防止疏远")
        
        return recommendations

