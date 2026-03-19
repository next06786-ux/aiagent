"""
学习领域分析器
分析学习效率、知识保持、进度评估等指标
"""
from typing import Dict, List, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class LearningMetrics:
    """学习指标"""
    learning_efficiency: float  # 学习效率（0-100）
    knowledge_retention: float  # 知识保持率（0-100）
    progress_score: float  # 进度分数（0-100）
    learning_consistency: float  # 学习一致性（0-100）
    skill_development: Dict[str, float]  # 技能发展
    learning_patterns: Dict[str, Any]  # 学习模式
    risk_factors: List[str]  # 风险因素
    recommendations: List[str]  # 建议


class LearningAnalyzer:
    """学习领域分析器"""
    
    def __init__(self):
        self.learning_target = 1.0  # 目标学习时间（小时/天）
        self.retention_target = 0.8  # 目标知识保持率
    
    def analyze(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> LearningMetrics:
        """分析学习指标"""
        
        # 计算学习效率
        learning_efficiency = self._calculate_learning_efficiency(history)
        
        # 计算知识保持率
        knowledge_retention = self._calculate_knowledge_retention(history)
        
        # 计算进度分数
        progress_score = self._calculate_progress_score(history)
        
        # 计算学习一致性
        learning_consistency = self._calculate_learning_consistency(history)
        
        # 分析技能发展
        skill_development = self._analyze_skill_development(history)
        
        # 识别学习模式
        learning_patterns = self._identify_learning_patterns(history)
        
        # 识别风险因素
        risk_factors = self._identify_risk_factors(learning_efficiency, knowledge_retention, progress_score, learning_consistency)
        
        # 生成建议
        recommendations = self._generate_recommendations(risk_factors, learning_patterns, skill_development)
        
        return LearningMetrics(
            learning_efficiency=learning_efficiency,
            knowledge_retention=knowledge_retention,
            progress_score=progress_score,
            learning_consistency=learning_consistency,
            skill_development=skill_development,
            learning_patterns=learning_patterns,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _calculate_learning_efficiency(self, history: List[Dict[str, Any]]) -> float:
        """计算学习效率（0-100）"""
        if not history:
            return 50.0
        
        recent = history[-30:]
        
        efficiency = 100.0
        
        # 学习时间充足性（40%）
        learning_hours = [h.get('learning_hours', 0) for h in recent]
        avg_learning = np.mean(learning_hours)
        time_score = min((avg_learning / self.learning_target) * 40, 40)
        efficiency -= (40 - time_score)
        
        # 学习质量（30%）
        quality_ratings = [h.get('learning_quality', 5) for h in recent]
        avg_quality = np.mean(quality_ratings)
        quality_score = (avg_quality / 10) * 30
        efficiency -= (30 - quality_score)
        
        # 完成度（30%）
        completion_rates = [h.get('task_completion_rate', 0.5) for h in recent]
        avg_completion = np.mean(completion_rates)
        completion_score = avg_completion * 30
        efficiency -= (30 - completion_score)
        
        return max(0, min(100, round(efficiency, 1)))
    
    def _calculate_knowledge_retention(self, history: List[Dict[str, Any]]) -> float:
        """计算知识保持率（0-100）"""
        if not history:
            return 50.0
        
        recent = history[-30:]
        
        retention = 100.0
        
        # 复习频率（40%）
        review_counts = [h.get('review_count', 0) for h in recent]
        avg_reviews = np.mean(review_counts)
        review_score = min((avg_reviews / 3) * 40, 40)
        retention -= (40 - review_score)
        
        # 测试成绩（40%）
        test_scores = [h.get('test_score', 70) for h in recent]
        avg_test = np.mean(test_scores)
        test_score = (avg_test / 100) * 40
        retention -= (40 - test_score)
        
        # 应用能力（20%）
        application_scores = [h.get('application_score', 5) for h in recent]
        avg_application = np.mean(application_scores)
        application_score = (avg_application / 10) * 20
        retention -= (20 - application_score)
        
        return max(0, min(100, round(retention, 1)))
    
    def _calculate_progress_score(self, history: List[Dict[str, Any]]) -> float:
        """计算进度分数（0-100）"""
        if not history:
            return 50.0
        
        recent = history[-30:]
        
        progress = 100.0
        
        # 目标完成度（50%）
        goal_progress = [h.get('goal_progress', 0.5) for h in recent]
        avg_progress = np.mean(goal_progress)
        progress_score = avg_progress * 50
        progress -= (50 - progress_score)
        
        # 学习速度（30%）
        learning_speeds = [h.get('learning_speed', 5) for h in recent]
        avg_speed = np.mean(learning_speeds)
        speed_score = (avg_speed / 10) * 30
        progress -= (30 - speed_score)
        
        # 里程碑达成（20%）
        milestones = [h.get('milestones_achieved', 0) for h in recent]
        avg_milestones = np.mean(milestones)
        milestone_score = min((avg_milestones / 2) * 20, 20)
        progress -= (20 - milestone_score)
        
        return max(0, min(100, round(progress, 1)))
    
    def _calculate_learning_consistency(self, history: List[Dict[str, Any]]) -> float:
        """计算学习一致性（0-100）"""
        if not history:
            return 50.0
        
        recent = history[-30:]
        
        consistency = 100.0
        
        # 学习频率一致性（40%）
        learning_hours = [h.get('learning_hours', 0) for h in recent]
        if len(learning_hours) > 1 and np.mean(learning_hours) > 0:
            learning_cv = np.std(learning_hours) / np.mean(learning_hours)
            frequency_consistency = max(0, 40 - (learning_cv * 40))
        else:
            frequency_consistency = 40
        consistency -= (40 - frequency_consistency)
        
        # 学习时间稳定性（30%）
        study_times = [h.get('study_time', 0) for h in recent]
        if len(study_times) > 1 and np.mean(study_times) > 0:
            time_cv = np.std(study_times) / np.mean(study_times)
            time_consistency = max(0, 30 - (time_cv * 30))
        else:
            time_consistency = 30
        consistency -= (30 - time_consistency)
        
        # 学习质量稳定性（30%）
        quality_ratings = [h.get('learning_quality', 5) for h in recent]
        if len(quality_ratings) > 1:
            quality_std = np.std(quality_ratings)
            quality_consistency = max(0, 30 - (quality_std / 5 * 30))
        else:
            quality_consistency = 30
        consistency -= (30 - quality_consistency)
        
        return max(0, min(100, round(consistency, 1)))
    
    def _analyze_skill_development(self, history: List[Dict[str, Any]]) -> Dict[str, float]:
        """分析技能发展"""
        skills = {
            "technical_skills": 0.0,
            "soft_skills": 0.0,
            "domain_knowledge": 0.0,
            "problem_solving": 0.0,
            "creativity": 0.0
        }
        
        if not history:
            return skills
        
        recent = history[-30:]
        
        # 技术技能
        technical = [h.get('technical_skill_level', 5) for h in recent]
        skills["technical_skills"] = round(np.mean(technical) / 10 * 100, 1)
        
        # 软技能
        soft = [h.get('soft_skill_level', 5) for h in recent]
        skills["soft_skills"] = round(np.mean(soft) / 10 * 100, 1)
        
        # 领域知识
        domain = [h.get('domain_knowledge_level', 5) for h in recent]
        skills["domain_knowledge"] = round(np.mean(domain) / 10 * 100, 1)
        
        # 问题解决能力
        problem_solving = [h.get('problem_solving_level', 5) for h in recent]
        skills["problem_solving"] = round(np.mean(problem_solving) / 10 * 100, 1)
        
        # 创意能力
        creativity = [h.get('creativity_level', 5) for h in recent]
        skills["creativity"] = round(np.mean(creativity) / 10 * 100, 1)
        
        return skills
    
    def _identify_learning_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """识别学习模式"""
        patterns = {
            "learning_style": "balanced",
            "preferred_time": "morning",
            "learning_pace": "moderate",
            "focus_areas": []
        }
        
        if not history:
            return patterns
        
        recent = history[-30:]
        
        # 学习风格
        learning_hours = [h.get('learning_hours', 0) for h in recent]
        avg_learning = np.mean(learning_hours)
        
        if avg_learning > 2:
            patterns["learning_style"] = "intensive"
        elif avg_learning < 0.5:
            patterns["learning_style"] = "casual"
        else:
            patterns["learning_style"] = "balanced"
        
        # 偏好时间（简化实现）
        patterns["preferred_time"] = "morning"
        
        # 学习速度
        speeds = [h.get('learning_speed', 5) for h in recent]
        avg_speed = np.mean(speeds)
        
        if avg_speed > 7:
            patterns["learning_pace"] = "fast"
        elif avg_speed < 4:
            patterns["learning_pace"] = "slow"
        else:
            patterns["learning_pace"] = "moderate"
        
        # 关注领域
        focus_areas = []
        for h in recent:
            areas = h.get('focus_areas', [])
            focus_areas.extend(areas)
        
        # 统计最常见的领域
        if focus_areas:
            from collections import Counter
            area_counts = Counter(focus_areas)
            patterns["focus_areas"] = [area for area, _ in area_counts.most_common(3)]
        
        return patterns
    
    def _identify_risk_factors(
        self,
        learning_efficiency: float,
        knowledge_retention: float,
        progress_score: float,
        learning_consistency: float
    ) -> List[str]:
        """识别风险因素"""
        risks = []
        
        if learning_efficiency < 40:
            risks.append("学习效率严重不足")
        elif learning_efficiency < 60:
            risks.append("学习效率较低")
        
        if knowledge_retention < 50:
            risks.append("知识保持率严重不足")
        elif knowledge_retention < 70:
            risks.append("知识保持率较低")
        
        if progress_score < 40:
            risks.append("学习进度严重滞后")
        elif progress_score < 60:
            risks.append("学习进度较慢")
        
        if learning_consistency < 40:
            risks.append("学习不够一致")
        elif learning_consistency < 60:
            risks.append("学习一致性需要改进")
        
        return risks
    
    def _generate_recommendations(
        self,
        risk_factors: List[str],
        learning_patterns: Dict[str, Any],
        skill_development: Dict[str, float]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if "学习效率严重不足" in risk_factors:
            recommendations.append("进行学习方法评估，寻找更有效的方式")
            recommendations.append("减少干扰，创建专注的学习环境")
            recommendations.append("考虑寻求学习指导或辅导")
        elif "学习效率较低" in risk_factors:
            recommendations.append("优化学习计划和方法")
            recommendations.append("增加学习时间或改进学习质量")
        
        if "知识保持率严重不足" in risk_factors:
            recommendations.append("增加复习频率")
            recommendations.append("使用间隔重复法加强记忆")
            recommendations.append("将知识应用到实践中")
        elif "知识保持率较低" in risk_factors:
            recommendations.append("定期复习已学内容")
            recommendations.append("尝试不同的记忆技巧")
        
        if "学习进度严重滞后" in risk_factors:
            recommendations.append("重新评估学习目标，制定现实的计划")
            recommendations.append("分解大目标为小目标")
            recommendations.append("寻求外部支持和鼓励")
        elif "学习进度较慢" in risk_factors:
            recommendations.append("加快学习速度，但保证质量")
            recommendations.append("优先学习关键内容")
        
        if "学习不够一致" in risk_factors:
            recommendations.append("建立每日学习习惯")
            recommendations.append("设定固定的学习时间")
            recommendations.append("使用学习追踪工具")
        elif "学习一致性需要改进" in risk_factors:
            recommendations.append("提高学习的规律性")
            recommendations.append("避免学习中断")
        
        # 基于学习模式的建议
        if learning_patterns["learning_style"] == "intensive":
            recommendations.append("保持高强度学习，但注意休息")
        elif learning_patterns["learning_style"] == "casual":
            recommendations.append("逐步增加学习投入")
        
        if learning_patterns["learning_pace"] == "slow":
            recommendations.append("尝试加快学习速度")
            recommendations.append("使用更高效的学习方法")
        
        # 基于技能发展的建议
        weakest_skill = min(skill_development.items(), key=lambda x: x[1])
        if weakest_skill[1] < 50:
            recommendations.append(f"重点加强{weakest_skill[0]}的发展")
        
        return recommendations

