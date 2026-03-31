"""
智能洞察引擎
整合对话分析和涌现检测，生成高级洞察
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from collections import defaultdict

from .conversation_analyzer import ConversationAnalyzer, ConversationInsight, DataType
from .emergence_detector import EmergenceDetector, EmergenceEvent, EmergenceType


class InsightLevel(Enum):
    """洞察级别"""
    INFO = "info"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    CRITICAL = "critical"


class InsightCategory(Enum):
    """洞察分类"""
    CASCADE = "cascade"
    SYNERGY = "synergy"
    TIPPING_POINT = "tipping_point"
    FEEDBACK_LOOP = "feedback_loop"
    PATTERN = "pattern"
    TREND = "trend"
    ANOMALY = "anomaly"


@dataclass
class SmartInsight:
    """智能洞察"""
    insight_id: str
    category: InsightCategory
    level: InsightLevel
    title: str
    description: str
    evidence: List[str]
    recommendations: List[str]
    confidence: float
    impact_score: float
    created_at: datetime = field(default_factory=datetime.now)
    related_metrics: List[str] = field(default_factory=list)
    visualization_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "category": self.category.value,
            "level": self.level.value,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "impact_score": self.impact_score,
            "created_at": self.created_at.isoformat(),
            "related_metrics": self.related_metrics,
            "visualization_data": self.visualization_data
        }


class SmartInsightEngine:
    """智能洞察引擎"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.conversation_analyzer = ConversationAnalyzer(user_id)
        self.emergence_detector = EmergenceDetector(user_id)
        self.insights: List[SmartInsight] = []
        self.stored_insights: List[Dict[str, Any]] = []
        self.llm = None
        try:
            from backend.llm.llm_service import get_llm_service
            self.llm = get_llm_service()
        except Exception:
            pass

    def _gen_insight_id(self) -> str:
        return f"insight_{uuid.uuid4().hex[:12]}"

    def load_stored_insights(self, insights: List[Dict[str, Any]]):
        self.stored_insights = insights
        self._sync_stored_to_emergence_detector()
        print(f"[智能洞察引擎] 加载了 {len(insights)} 条存储的洞察数据")

    def _sync_stored_to_emergence_detector(self):
        daily_data = defaultdict(lambda: defaultdict(list))
        for insight in self.stored_insights:
            ts = insight.get("timestamp")
            if not ts:
                continue
            try:
                timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                day_key = timestamp.strftime("%Y-%m-%d")
            except:
                continue
            data_type = insight.get("data_type", "")
            category = insight.get("category", "")
            value = insight.get("value")
            if data_type == "emotion" and value is not None:
                daily_data[day_key]["emotion_score"].append(value)
            if data_type == "topic":
                daily_data[day_key][f"topic_{category}"].append(1)
            if data_type == "entity" and value is not None:
                metadata = insight.get("metadata", {})
                metric_type = metadata.get("metric_type", category)
                daily_data[day_key][metric_type].append(value)
            if data_type == "intent":
                metadata = insight.get("metadata", {})
                intent_type = metadata.get("intent_type", "unknown")
                daily_data[day_key][f"intent_{intent_type}"].append(1)
        for day, metrics in sorted(daily_data.items()):
            try:
                timestamp = datetime.strptime(day, "%Y-%m-%d")
            except:
                continue
            aggregated = {}
            for metric, values in metrics.items():
                aggregated[metric] = sum(values) / len(values)
            self.emergence_detector.add_data_point(aggregated, timestamp)

    def process_conversation(self, messages: List[Dict[str, Any]]) -> List[ConversationInsight]:
        all_insights = []
        for msg in messages:
            insights = self.conversation_analyzer.analyze_message(
                message=msg.get("content", ""),
                role=msg.get("role", "user"),
                message_id=msg.get("id", ""),
                metadata=msg.get("metadata", {})
            )
            all_insights.extend(insights)
        self._sync_to_emergence_detector()
        return all_insights

    def _sync_to_emergence_detector(self):
        export_data = self.conversation_analyzer.export_for_emergence()
        for day, metrics in export_data.items():
            timestamp = datetime.strptime(day, "%Y-%m-%d")
            self.emergence_detector.add_data_point(metrics, timestamp)

    def generate_insights(self) -> List[SmartInsight]:
        """生成智能洞察"""
        new_insights = []
        emergence_events = self.emergence_detector.detect_all_emergences()
        for event in emergence_events:
            insight = self._convert_emergence_to_insight(event)
            if insight:
                new_insights.append(insight)
        new_insights.extend(self._detect_cascade_effects())
        new_insights.extend(self._detect_synergy_opportunities())
        new_insights.extend(self._detect_tipping_points())
        new_insights.extend(self._detect_feedback_loops())
        new_insights.extend(self._detect_behavior_patterns())
        new_insights.sort(key=lambda x: x.impact_score, reverse=True)
        self.insights.extend(new_insights)
        return new_insights

    def _convert_emergence_to_insight(self, event: EmergenceEvent) -> Optional[SmartInsight]:
        category_map = {
            EmergenceType.PATTERN: InsightCategory.PATTERN,
            EmergenceType.NONLINEAR: InsightCategory.ANOMALY,
            EmergenceType.SYNERGY: InsightCategory.SYNERGY,
            EmergenceType.FEEDBACK_LOOP: InsightCategory.FEEDBACK_LOOP,
            EmergenceType.THRESHOLD: InsightCategory.TIPPING_POINT,
            EmergenceType.BIFURCATION: InsightCategory.ANOMALY,
        }
        level = InsightLevel.INFO
        if event.strength > 0.8:
            level = InsightLevel.WARNING
        elif event.strength > 0.6:
            level = InsightLevel.SUGGESTION
        return SmartInsight(
            insight_id=self._gen_insight_id(),
            category=category_map.get(event.emergence_type, InsightCategory.PATTERN),
            level=level,
            title=self._generate_insight_title(event),
            description=event.description,
            evidence=[f"检测到{event.emergence_type.value}类型的涌现现象"],
            recommendations=self._generate_recommendations(event),
            confidence=event.confidence,
            impact_score=event.strength * 100,
            related_metrics=event.involved_metrics
        )

    def _generate_insight_title(self, event: EmergenceEvent) -> str:
        type_titles = {
            EmergenceType.PATTERN: "发现新模式",
            EmergenceType.NONLINEAR: "非线性变化",
            EmergenceType.SYNERGY: "协同效应",
            EmergenceType.FEEDBACK_LOOP: "反馈循环",
            EmergenceType.THRESHOLD: "临界点预警",
            EmergenceType.BIFURCATION: "行为分化",
        }
        return type_titles.get(event.emergence_type, "新发现")

    def _generate_recommendations(self, event: EmergenceEvent) -> List[str]:
        recs = []
        if event.emergence_type == EmergenceType.FEEDBACK_LOOP:
            if event.strength > 0.7:
                recs.append("这是一个强反馈循环，建议主动干预打破负向循环")
            recs.append("关注循环中的关键节点，小改变可能带来大效果")
        elif event.emergence_type == EmergenceType.THRESHOLD:
            recs.append("你正接近一个临界点，建议提前采取行动")
            recs.append("监控相关指标的变化趋势")
        elif event.emergence_type == EmergenceType.SYNERGY:
            recs.append("继续保持这些行为的组合，它们产生了协同效应")
            recs.append("尝试增加这些活动的频率")
        elif event.emergence_type == EmergenceType.PATTERN:
            recs.append("这个模式值得关注，可能揭示了深层规律")
        return recs

    def _detect_cascade_effects(self) -> List[SmartInsight]:
        """检测级联效应"""
        insights = []
        emotion_trend = self.conversation_analyzer.get_emotion_trend(days=14)
        if len(emotion_trend) >= 3:
            recent_emotions = [d["avg_emotion"] for d in emotion_trend[-3:]]
            if all(recent_emotions[i] < recent_emotions[i-1] for i in range(1, len(recent_emotions))):
                insights.append(SmartInsight(
                    insight_id=self._gen_insight_id(),
                    category=InsightCategory.CASCADE,
                    level=InsightLevel.WARNING,
                    title="情绪级联下降",
                    description="你的情绪在过去几天持续下降，这可能会影响到工作效率、社交意愿和睡眠质量",
                    evidence=[
                        f"情绪从 {recent_emotions[0]:.1f} 下降到 {recent_emotions[-1]:.1f}",
                        "连续3天呈下降趋势"
                    ],
                    recommendations=["尝试进行一些让你开心的活动", "与朋友或家人聊聊天", "保证充足的睡眠", "适当运动可以改善情绪"],
                    confidence=0.8, impact_score=75,
                    related_metrics=["emotion_score"],
                    visualization_data={"type": "cascade_flow", "trend": emotion_trend}
                ))
        return insights

    def _detect_synergy_opportunities(self) -> List[SmartInsight]:
        """检测协同增益机会"""
        insights = []
        topic_dist = self.conversation_analyzer.get_topic_distribution(days=7)
        if topic_dist.get("health", 0) > 2 and topic_dist.get("social", 0) > 2:
            insights.append(SmartInsight(
                insight_id=self._gen_insight_id(),
                category=InsightCategory.SYNERGY,
                level=InsightLevel.SUGGESTION,
                title="健康与社交的协同机会",
                description="你最近同时关注健康和社交话题，研究表明将两者结合（如约朋友一起运动）效果更好",
                evidence=[f"健康话题出现 {topic_dist.get('health', 0)} 次", f"社交话题出现 {topic_dist.get('social', 0)} 次"],
                recommendations=["尝试约朋友一起跑步或健身", "参加团体运动活动", "组织户外徒步聚会"],
                confidence=0.75, impact_score=65,
                related_metrics=["health", "social"]
            ))
        return insights

    def _detect_tipping_points(self) -> List[SmartInsight]:
        """检测临界点"""
        insights = []
        emotion_insights = self.conversation_analyzer.get_insights_by_category("emotion", days=7)
        if emotion_insights:
            emotion_values = [i.value for i in emotion_insights if i.value is not None]
            if emotion_values:
                avg_emotion = sum(emotion_values) / len(emotion_values)
                if avg_emotion < 4:
                    insights.append(SmartInsight(
                        insight_id=self._gen_insight_id(),
                        category=InsightCategory.TIPPING_POINT,
                        level=InsightLevel.CRITICAL,
                        title="情绪临界点预警",
                        description=f"你的平均情绪分数为 {avg_emotion:.1f}，已接近临界点。持续低迷可能导致更严重的问题",
                        evidence=[f"7天平均情绪: {avg_emotion:.1f}/10", f"检测到 {len(emotion_values)} 次情绪记录"],
                        recommendations=["建议与信任的人倾诉", "尝试正念冥想或深呼吸", "保证基本的作息规律"],
                        confidence=0.85, impact_score=90,
                        related_metrics=["emotion_score"],
                        visualization_data={"type": "gauge", "value": avg_emotion, "threshold": 4}
                    ))
        return insights

    def _detect_feedback_loops(self) -> List[SmartInsight]:
        """检测反馈环路"""
        insights = []
        topic_dist = self.conversation_analyzer.get_topic_distribution(days=14)
        emotion_trend = self.conversation_analyzer.get_emotion_trend(days=14)
        if topic_dist.get("work", 0) > 5:
            if emotion_trend and len(emotion_trend) >= 3:
                recent_avg = sum(d["avg_emotion"] for d in emotion_trend[-3:]) / 3
                if recent_avg < 5:
                    insights.append(SmartInsight(
                        insight_id=self._gen_insight_id(),
                        category=InsightCategory.FEEDBACK_LOOP,
                        level=InsightLevel.WARNING,
                        title="工作压力-情绪负向循环",
                        description="检测到可能的负向反馈循环：工作压力大 -> 情绪低落 -> 效率下降 -> 更大压力",
                        evidence=[f"工作相关话题出现 {topic_dist.get('work', 0)} 次", f"近期平均情绪: {recent_avg:.1f}/10"],
                        recommendations=["尝试打破循环：先处理情绪，再处理工作", "设定工作边界，避免过度投入", "每天留出放松时间", "将大任务分解为小步骤"],
                        confidence=0.7, impact_score=80,
                        related_metrics=["work", "emotion_score"]
                    ))
        return insights

    def _detect_behavior_patterns(self) -> List[SmartInsight]:
        """检测行为模式"""
        insights = []
        intent_insights = [i for i in self.conversation_analyzer.insights if i.data_type == DataType.INTENT]
        intent_counts = defaultdict(int)
        for insight in intent_insights:
            intent_type = insight.metadata.get("intent_type", "unknown")
            intent_counts[intent_type] += 1
        if intent_counts.get("seeking_advice", 0) > 5:
            insights.append(SmartInsight(
                insight_id=self._gen_insight_id(),
                category=InsightCategory.PATTERN, level=InsightLevel.INFO,
                title="决策支持需求模式",
                description="你最近频繁寻求建议，这可能表示你正面临一些需要决策的事情",
                evidence=[f"寻求建议的对话出现 {intent_counts.get('seeking_advice', 0)} 次"],
                recommendations=["尝试使用决策副本功能进行深度分析", "列出决策的利弊清单", "给自己设定决策截止时间"],
                confidence=0.7, impact_score=50, related_metrics=["intent_seeking_advice"]
            ))
        if intent_counts.get("complaining", 0) > 3:
            insights.append(SmartInsight(
                insight_id=self._gen_insight_id(),
                category=InsightCategory.PATTERN, level=InsightLevel.SUGGESTION,
                title="负面表达增多",
                description="最近你的对话中负面表达增多，这可能反映了一些潜在的不满或压力",
                evidence=[f"抱怨类表达出现 {intent_counts.get('complaining', 0)} 次"],
                recommendations=["尝试将抱怨转化为具体的问题描述", "思考哪些是可以改变的，哪些需要接受", "与朋友倾诉或写日记释放情绪"],
                confidence=0.65, impact_score=55, related_metrics=["intent_complaining"]
            ))
        return insights

    def get_dashboard_data(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_insights": len(self.insights),
                "critical_count": len([i for i in self.insights if i.level == InsightLevel.CRITICAL]),
                "warning_count": len([i for i in self.insights if i.level == InsightLevel.WARNING]),
                "suggestion_count": len([i for i in self.insights if i.level == InsightLevel.SUGGESTION]),
            },
            "emotion_trend": self.conversation_analyzer.get_emotion_trend(days=14),
            "topic_distribution": self.conversation_analyzer.get_topic_distribution(days=7),
            "top_insights": [i.to_dict() for i in self.insights[:5]],
            "emergence_stats": self.emergence_detector.get_emergence_statistics()
        }

    def get_insights_by_level(self, level: InsightLevel) -> List[SmartInsight]:
        return [i for i in self.insights if i.level == level]

    def get_insights_by_category(self, category: InsightCategory) -> List[SmartInsight]:
        return [i for i in self.insights if i.category == category]


# 全局实例缓存
_engines: Dict[str, SmartInsightEngine] = {}

def get_smart_insight_engine(user_id: str) -> SmartInsightEngine:
    """获取智能洞察引擎实例"""
    if user_id not in _engines:
        _engines[user_id] = SmartInsightEngine(user_id)
    return _engines[user_id]
