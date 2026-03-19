"""
统一分析引擎
整合6大领域的分析，提供综合生活分析
"""
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from .health_analyzer import HealthAnalyzer, HealthMetrics
from .time_analyzer import TimeAnalyzer, TimeMetrics
from .emotion_analyzer import EmotionAnalyzer, EmotionMetrics
from .social_analyzer import SocialAnalyzer, SocialMetrics
from .finance_analyzer import FinanceAnalyzer, FinanceMetrics
from .learning_analyzer import LearningAnalyzer, LearningMetrics


@dataclass
class LifeAnalysis:
    """生活分析结果"""
    user_id: str
    timestamp: str
    health: Dict[str, Any]
    time: Dict[str, Any]
    emotion: Dict[str, Any]
    social: Dict[str, Any]
    finance: Dict[str, Any]
    learning: Dict[str, Any]
    overall_score: float  # 综合生活质量分数（0-100）
    key_insights: List[str]  # 关键洞察
    priority_actions: List[str]  # 优先行动


class UnifiedAnalysisEngine:
    """统一分析引擎"""
    
    def __init__(self):
        self.health_analyzer = HealthAnalyzer()
        self.time_analyzer = TimeAnalyzer()
        self.emotion_analyzer = EmotionAnalyzer()
        self.social_analyzer = SocialAnalyzer()
        self.finance_analyzer = FinanceAnalyzer()
        self.learning_analyzer = LearningAnalyzer()
        
        print("[OK] Unified analysis engine initialized")
    
    def analyze(self, user_id: str, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> LifeAnalysis:
        """
        进行综合生活分析
        
        Args:
            user_id: 用户ID
            user_data: 用户当前数据
            history: 用户历史数据（最近30天）
        
        Returns:
            生活分析结果
        """
        
        print(f"\n[分析引擎] 开始分析用户 {user_id} 的生活数据...")
        
        # 1. 分析各个领域
        health_metrics = self.health_analyzer.analyze(user_data, history)
        time_metrics = self.time_analyzer.analyze(user_data, history)
        emotion_metrics = self.emotion_analyzer.analyze(user_data, history)
        social_metrics = self.social_analyzer.analyze(user_data, history)
        finance_metrics = self.finance_analyzer.analyze(user_data, history)
        learning_metrics = self.learning_analyzer.analyze(user_data, history)
        
        # 2. 计算综合分数
        overall_score = self._calculate_overall_score(
            health_metrics, time_metrics, emotion_metrics,
            social_metrics, finance_metrics, learning_metrics
        )
        
        # 3. 生成关键洞察
        key_insights = self._generate_key_insights(
            health_metrics, time_metrics, emotion_metrics,
            social_metrics, finance_metrics, learning_metrics
        )
        
        # 4. 生成优先行动
        priority_actions = self._generate_priority_actions(
            health_metrics, time_metrics, emotion_metrics,
            social_metrics, finance_metrics, learning_metrics
        )
        
        # 5. 构建分析结果
        analysis = LifeAnalysis(
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            health=self._metrics_to_dict(health_metrics),
            time=self._metrics_to_dict(time_metrics),
            emotion=self._metrics_to_dict(emotion_metrics),
            social=self._metrics_to_dict(social_metrics),
            finance=self._metrics_to_dict(finance_metrics),
            learning=self._metrics_to_dict(learning_metrics),
            overall_score=overall_score,
            key_insights=key_insights,
            priority_actions=priority_actions
        )
        
        print(f"[分析引擎] 分析完成! 综合分数: {overall_score:.1f}/100")
        print(f"[分析引擎] 关键洞察数: {len(key_insights)}")
        print(f"[分析引擎] 优先行动数: {len(priority_actions)}\n")
        
        return analysis
    
    def _calculate_overall_score(
        self,
        health: HealthMetrics,
        time: TimeMetrics,
        emotion: EmotionMetrics,
        social: SocialMetrics,
        finance: FinanceMetrics,
        learning: LearningMetrics
    ) -> float:
        """计算综合生活质量分数"""
        
        # 各领域权重
        weights = {
            'health': 0.25,      # 健康最重要
            'emotion': 0.20,     # 情绪次之
            'time': 0.15,        # 时间管理
            'social': 0.15,      # 社交关系
            'finance': 0.15,     # 财务状况
            'learning': 0.10     # 学习发展
        }
        
        # 计算各领域的标准化分数
        scores = {
            'health': health.health_score,
            'emotion': self._normalize_emotion_score(emotion),
            'time': time.efficiency_score,
            'social': social.satisfaction_score,
            'finance': finance.financial_health,
            'learning': learning.learning_efficiency
        }
        
        # 加权平均
        overall = sum(scores[domain] * weights[domain] for domain in scores)
        
        return round(overall, 1)
    
    def _normalize_emotion_score(self, emotion: EmotionMetrics) -> float:
        """将情绪指标标准化为0-100分"""
        # 基础分数：情绪稳定性
        base_score = emotion.emotional_stability
        
        # 调整：基于心情分数
        mood_adjustment = (emotion.mood_score / 10) * 20 - 10
        
        # 调整：基于调节能力
        regulation_adjustment = (emotion.regulation_ability / 100) * 10 - 5
        
        score = base_score + mood_adjustment + regulation_adjustment
        return max(0, min(100, round(score, 1)))
    
    def _generate_key_insights(
        self,
        health: HealthMetrics,
        time: TimeMetrics,
        emotion: EmotionMetrics,
        social: SocialMetrics,
        finance: FinanceMetrics,
        learning: LearningMetrics
    ) -> List[str]:
        """生成关键洞察"""
        insights = []
        
        # 健康洞察
        if health.recovery_status == "excellent":
            insights.append("[HEALTH] Excellent health status, maintain current lifestyle")
        elif health.recovery_status == "poor":
            insights.append("[HEALTH] Health status needs immediate improvement, increase sleep and exercise")
        
        if health.sleep_debt > 10:
            insights.append(f"[SLEEP] Sleep debt accumulated {health.sleep_debt} hours, need to supplement sleep")
        
        # 时间洞察
        if time.efficiency_score < 50:
            insights.append("[TIME] Low work efficiency, recommend time management optimization")
        
        if time.procrastination_level > 7:
            insights.append("[TIME] Serious procrastination problem, recommend task decomposition method")
        
        # 情绪洞察
        if emotion.risk_level == "critical":
            insights.append("[EMOTION] Critical emotion risk level, recommend seeking professional help immediately")
        elif emotion.risk_level == "high":
            insights.append("[EMOTION] High emotion risk, recommend increasing social and relaxation activities")
        
        if emotion.mood_trend == "declining":
            insights.append("[MOOD] Mood is declining, need attention and action")
        
        # 社交洞察
        if social.loneliness_score > 8:
            insights.append("[SOCIAL] Severe loneliness, recommend actively contacting friends and attending social activities")
        
        if social.satisfaction_score < 50:
            insights.append("[SOCIAL] Low social satisfaction, recommend improving relationship quality")
        
        # 财务洞察
        if finance.savings_rate < 0.1:
            insights.append("[FINANCE] Savings rate too low, recommend making a savings plan")
        
        if finance.risk_level == "high":
            insights.append("[FINANCE] High financial risk, recommend financial planning")
        
        # 学习洞察
        if learning.learning_efficiency < 50:
            insights.append("[LEARNING] Low learning efficiency, recommend improving learning methods")
        
        if learning.knowledge_retention < 60:
            insights.append("[LEARNING] Low knowledge retention rate, recommend increasing review frequency")
        
        # 跨领域洞察
        if health.health_score > 80 and emotion.mood_score > 7 and social.satisfaction_score > 70:
            insights.append("[LIFE] Good life status, multiple domains performing excellently")
        
        if health.sleep_debt > 5 and time.efficiency_score < 60 and emotion.mood_score < 5:
            insights.append("[PATTERN] Sleep deprivation leads to efficiency decline and mood deterioration, prioritize sleep improvement")
        
        return insights[:10]  # 返回前10个最重要的洞察
    
    def _generate_priority_actions(
        self,
        health: HealthMetrics,
        time: TimeMetrics,
        emotion: EmotionMetrics,
        social: SocialMetrics,
        finance: FinanceMetrics,
        learning: LearningMetrics
    ) -> List[str]:
        """生成优先行动"""
        actions = []
        
        # 收集所有建议
        all_recommendations = []
        
        all_recommendations.extend([
            ("health", rec, 1) for rec in health.recommendations
        ])
        all_recommendations.extend([
            ("time", rec, 2) for rec in time.recommendations
        ])
        all_recommendations.extend([
            ("emotion", rec, 3) for rec in emotion.recommendations
        ])
        all_recommendations.extend([
            ("social", rec, 4) for rec in social.recommendations
        ])
        all_recommendations.extend([
            ("finance", rec, 5) for rec in finance.recommendations
        ])
        all_recommendations.extend([
            ("learning", rec, 6) for rec in learning.recommendations
        ])
        
        # 按优先级排序
        # 优先级：健康 > 情绪 > 时间 > 社交 > 财务 > 学习
        priority_order = {"health": 1, "emotion": 2, "time": 3, "social": 4, "finance": 5, "learning": 6}
        
        all_recommendations.sort(key=lambda x: priority_order.get(x[0], 10))
        
        # 取前10个最重要的行动
        for domain, action, _ in all_recommendations[:10]:
            actions.append(f"[{domain.upper()}] {action}")
        
        return actions
    
    def _metrics_to_dict(self, metrics) -> Dict[str, Any]:
        """将指标对象转换为字典"""
        return asdict(metrics)
    
    def get_domain_summary(self, analysis: LifeAnalysis) -> Dict[str, Any]:
        """获取各领域的总结"""
        return {
            "health": {
                "score": analysis.health.get("health_score", 0),
                "status": analysis.health.get("recovery_status", "unknown"),
                "risks": analysis.health.get("risk_factors", [])
            },
            "time": {
                "score": analysis.time.get("efficiency_score", 0),
                "pressure": analysis.time.get("time_pressure", 0),
                "risks": analysis.time.get("risk_factors", [])
            },
            "emotion": {
                "score": analysis.emotion.get("mood_score", 0),
                "stability": analysis.emotion.get("emotional_stability", 0),
                "risk_level": analysis.emotion.get("risk_level", "unknown"),
                "risks": analysis.emotion.get("risk_factors", [])
            },
            "social": {
                "score": analysis.social.get("satisfaction_score", 0),
                "loneliness": analysis.social.get("loneliness_score", 0),
                "risks": analysis.social.get("risk_factors", [])
            },
            "finance": {
                "score": analysis.finance.get("financial_health", 0),
                "savings_rate": analysis.finance.get("savings_rate", 0),
                "risk_level": analysis.finance.get("risk_level", "unknown"),
                "risks": analysis.finance.get("risk_factors", [])
            },
            "learning": {
                "score": analysis.learning.get("learning_efficiency", 0),
                "retention": analysis.learning.get("knowledge_retention", 0),
                "risks": analysis.learning.get("risk_factors", [])
            }
        }


# 全局实例
_engine = None

def get_analysis_engine() -> UnifiedAnalysisEngine:
    """获取全局分析引擎实例"""
    global _engine
    if _engine is None:
        _engine = UnifiedAnalysisEngine()
    return _engine

