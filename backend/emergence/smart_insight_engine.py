"""
智能洞察引擎
整合对话分析和涌现检测，生成高级洞察
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict

from .conversation_analyzer import ConversationAnalyzer, ConversationInsight, DataType
from .emergence_detector import EmergenceDetector, EmergenceEvent, EmergenceType


class InsightLevel(Enum):
    """洞察级别"""
    INFO = "info"           # 信息性洞察
    SUGGESTION = "suggestion"  # 建议性洞察
    WARNING = "warning"     # 警告性洞察
    CRITICAL = "critical"   # 关键性洞察


class InsightCategory(Enum):
    """洞察分类"""
    CASCADE = "cascade"           # 级联效应
    SYNERGY = "synergy"           # 协同增益
    TIPPING_POINT = "tipping_point"  # 临界点
    FEEDBACK_LOOP = "feedback_loop"  # 反馈环路
    PATTERN = "pattern"           # 行为模式
    TREND = "trend"               # 趋势变化
    ANOMALY = "anomaly"           # 异常检测


@dataclass
class SmartInsight:
    """智能洞察"""
    insight_id: str
    category: InsightCategory
    level: InsightLevel
    title: str
    description: str
    evidence: List[str]  # 支撑证据
    recommendations: List[str]  # 建议行动
    confidence: float
    impact_score: float  # 影响力分数 0-100
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
        self.insight_counter = 0
        
        # 存储的洞察数据（从数据库加载）
        self.stored_insights: List[Dict[str, Any]] = []
        
        # LLM服务（可选，用于生成更智能的洞察描述）
        self.llm = None
        try:
            from backend.llm.llm_service import get_llm_service
            self.llm = get_llm_service()
        except Exception:
            pass
    
    def load_stored_insights(self, insights: List[Dict[str, Any]]):
        """
        加载已存储的洞察数据（从数据库读取的）
        
        Args:
            insights: 洞察数据列表
        """
        self.stored_insights = insights
        
        # 将数据同步到涌现检测器
        self._sync_stored_to_emergence_detector()
        
        print(f"[智能洞察引擎] 加载了 {len(insights)} 条存储的洞察数据")
    
    def _sync_stored_to_emergence_detector(self):
        """将存储的洞察数据同步到涌现检测器"""
        from collections import defaultdict
        
        # 按天聚合数据
        daily_data = defaultdict(lambda: defaultdict(list))
        
        for insight in self.stored_insights:
            timestamp_str = insight.get("timestamp")
            if not timestamp_str:
                continue
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                day_key = timestamp.strftime("%Y-%m-%d")
            except:
                continue
            
            data_type = insight.get("data_type", "")
            category = insight.get("category", "")
            value = insight.get("value")
            
            # 情绪数据
            if data_type == "emotion" and value is not None:
                daily_data[day_key]["emotion_score"].append(value)
            
            # 话题数据
            if data_type == "topic":
                daily_data[day_key][f"topic_{category}"].append(1)
            
            # 实体数据（健康、财务等）
            if data_type == "entity" and value is not None:
                metadata = insight.get("metadata", {})
                metric_type = metadata.get("metric_type", category)
                daily_data[day_key][metric_type].append(value)
            
            # 意图数据
            if data_type == "intent":
                metadata = insight.get("metadata", {})
                intent_type = metadata.get("intent_type", "unknown")
                daily_data[day_key][f"intent_{intent_type}"].append(1)
        
        # 计算每天的平均值并添加到涌现检测器
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
        """
        处理对话消息，提取洞察数据
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "...", "id": "...", "metadata": {...}}]
        
        Returns:
            提取的洞察列表
        """
        all_insights = []
        
        for msg in messages:
            insights = self.conversation_analyzer.analyze_message(
                message=msg.get("content", ""),
                role=msg.get("role", "user"),
                message_id=msg.get("id", ""),
                metadata=msg.get("metadata", {})
            )
            all_insights.extend(insights)
        
        # 将数据同步到涌现检测器
        self._sync_to_emergence_detector()
        
        return all_insights
    
    def _sync_to_emergence_detector(self):
        """将对话洞察同步到涌现检测器"""
        export_data = self.conversation_analyzer.export_for_emergence()
        
        for day, metrics in export_data.items():
            timestamp = datetime.strptime(day, "%Y-%m-%d")
            self.emergence_detector.add_data_point(metrics, timestamp)
    
    def generate_insights(self) -> List[SmartInsight]:
        """
        生成智能洞察
        
        Returns:
            智能洞察列表
        """
        new_insights = []
        
        # 1. 检测涌现现象
        emergence_events = self.emergence_detector.detect_all_emergences()
        
        # 2. 将涌现事件转换为智能洞察
        for event in emergence_events:
            insight = self._convert_emergence_to_insight(event)
            if insight:
                new_insights.append(insight)
        
        # 3. 生成级联效应洞察
        cascade_insights = self._detect_cascade_effects()
        new_insights.extend(cascade_insights)
        
        # 4. 生成协同增益洞察
        synergy_insights = self._detect_synergy_opportunities()
        new_insights.extend(synergy_insights)
        
        # 5. 生成临界点预警
        tipping_insights = self._detect_tipping_points()
        new_insights.extend(tipping_insights)
        
        # 6. 生成反馈环路洞察
        loop_insights = self._detect_feedback_loops()
        new_insights.extend(loop_insights)
        
        # 7. 生成行为模式洞察
        pattern_insights = self._detect_behavior_patterns()
        new_insights.extend(pattern_insights)
        
        # 8. 按影响力排序
        new_insights.sort(key=lambda x: x.impact_score, reverse=True)
        
        # 保存洞察
        self.insights.extend(new_insights)
        
        return new_insights
    
    def _convert_emergence_to_insight(self, event: EmergenceEvent) -> Optional[SmartInsight]:
        """将涌现事件转换为智能洞察"""
        self.insight_counter += 1
        
        # 根据涌现类型确定洞察分类和级别
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
            insight_id=f"insight_{self.insight_counter}",
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
        """生成洞察标题"""
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
        """生成建议"""
        recommendations = []
        
        if event.emergence_type == EmergenceType.FEEDBACK_LOOP:
            if event.strength > 0.7:
                recommendations.append("这是一个强反馈循环，建议主动干预打破负向循环")
            recommendations.append("关注循环中的关键节点，小改变可能带来大效果")
        
        elif event.emergence_type == EmergenceType.THRESHOLD:
            recommendations.append("你正接近一个临界点，建议提前采取行动")
            recommendations.append("监控相关指标的变化趋势")
        
        elif event.emergence_type == EmergenceType.SYNERGY:
            recommendations.append("继续保持这些行为的组合，它们产生了协同效应")
            recommendations.append("尝试增加这些活动的频率")
        
        elif event.emergence_type == EmergenceType.PATTERN:
            recommendations.append("这个模式值得关注，可能揭示了深层规律")
        
        return recommendations
    
    def _detect_cascade_effects(self) -> List[SmartInsight]:
        """检测级联效应"""
        insights = []
        
        # 获取情绪趋势
        emotion_trend = self.conversation_analyzer.get_emotion_trend(days=14)
        
        if len(emotion_trend) >= 3:
            # 检测情绪下降是否伴随其他指标变化
            recent_emotions = [d["avg_emotion"] for d in emotion_trend[-3:]]
            if all(recent_emotions[i] < recent_emotions[i-1] for i in range(1, len(recent_emotions))):
                # 情绪持续下降
                self.insight_counter += 1
                insights.append(SmartInsight(
                    insight_id=f"insight_{self.insight_counter}",
                    category=InsightCategory.CASCADE,
                    level=InsightLevel.WARNING,
                    title="情绪级联下降",
                    description="你的情绪在过去几天持续下降，这可能会影响到工作效率、社交意愿和睡眠质量",
                    evidence=[
                        f"情绪从 {recent_emotions[0]:.1f} 下降到 {recent_emotions[-1]:.1f}",
                        "连续3天呈下降趋势"
                    ],
                    recommendations=[
                        "尝试进行一些让你开心的活动",
                        "与朋友或家人聊聊天",
                        "保证充足的睡眠",
                        "适当运动可以改善情绪"
                    ],
                    confidence=0.8,
                    impact_score=75,
                    related_metrics=["emotion_score"],
                    visualization_data={
                        "type": "cascade_flow",
                        "nodes": ["情绪下降", "工作效率↓", "社交意愿↓", "睡眠质量↓"],
                        "trend": emotion_trend
                    }
                ))
        
        return insights
    
    def _detect_synergy_opportunities(self) -> List[SmartInsight]:
        """检测协同增益机会"""
        insights = []
        
        # 获取话题分布
        topic_dist = self.conversation_analyzer.get_topic_distribution(days=7)
        
        # 检测健康+社交的协同
        if topic_dist.get("health", 0) > 2 and topic_dist.get("social", 0) > 2:
            self.insight_counter += 1
            insights.append(SmartInsight(
                insight_id=f"insight_{self.insight_counter}",
                category=InsightCategory.SYNERGY,
                level=InsightLevel.SUGGESTION,
                title="健康与社交的协同机会",
                description="你最近同时关注健康和社交话题，研究表明将两者结合（如约朋友一起运动）效果更好",
                evidence=[
                    f"健康话题出现 {topic_dist.get('health', 0)} 次",
                    f"社交话题出现 {topic_dist.get('social', 0)} 次"
                ],
                recommendations=[
                    "尝试约朋友一起跑步或健身",
                    "参加团体运动活动",
                    "组织户外徒步聚会"
                ],
                confidence=0.75,
                impact_score=65,
                related_metrics=["health", "social"],
                visualization_data={
                    "type": "synergy_diagram",
                    "factors": ["健康活动", "社交活动"],
                    "combined_effect": "1+1>2"
                }
            ))
        
        return insights
    
    def _detect_tipping_points(self) -> List[SmartInsight]:
        """检测临界点"""
        insights = []
        
        # 获取情绪数据
        emotion_insights = self.conversation_analyzer.get_insights_by_category("emotion", days=7)
        
        if emotion_insights:
            emotion_values = [i.value for i in emotion_insights if i.value is not None]
            if emotion_values:
                avg_emotion = sum(emotion_values) / len(emotion_values)
                
                # 情绪临界点检测
                if avg_emotion < 4:  # 低于4分是危险区
                    self.insight_counter += 1
                    insights.append(SmartInsight(
                        insight_id=f"insight_{self.insight_counter}",
                        category=InsightCategory.TIPPING_POINT,
                        level=InsightLevel.CRITICAL,
                        title="情绪临界点预警",
                        description=f"你的平均情绪分数为 {avg_emotion:.1f}，已接近临界点。持续低迷可能导致更严重的问题",
                        evidence=[
                            f"7天平均情绪: {avg_emotion:.1f}/10",
                            f"检测到 {len(emotion_values)} 次情绪记录"
                        ],
                        recommendations=[
                            "建议与信任的人倾诉",
                            "考虑寻求专业帮助",
                            "尝试正念冥想或深呼吸",
                            "保证基本的作息规律"
                        ],
                        confidence=0.85,
                        impact_score=90,
                        related_metrics=["emotion_score"],
                        visualization_data={
                            "type": "gauge",
                            "value": avg_emotion,
                            "threshold": 4,
                            "danger_zone": [0, 4],
                            "warning_zone": [4, 6],
                            "safe_zone": [6, 10]
                        }
                    ))
        
        return insights
    
    def _detect_feedback_loops(self) -> List[SmartInsight]:
        """检测反馈环路"""
        insights = []
        
        # 从对话中检测可能的反馈循环模式
        topic_dist = self.conversation_analyzer.get_topic_distribution(days=14)
        emotion_trend = self.conversation_analyzer.get_emotion_trend(days=14)
        
        # 检测压力-情绪负向循环
        if topic_dist.get("work", 0) > 5:  # 工作话题频繁
            if emotion_trend and len(emotion_trend) >= 3:
                recent_avg = sum(d["avg_emotion"] for d in emotion_trend[-3:]) / 3
                if recent_avg < 5:  # 情绪偏低
                    self.insight_counter += 1
                    insights.append(SmartInsight(
                        insight_id=f"insight_{self.insight_counter}",
                        category=InsightCategory.FEEDBACK_LOOP,
                        level=InsightLevel.WARNING,
                        title="工作压力-情绪负向循环",
                        description="检测到可能的负向反馈循环：工作压力大 → 情绪低落 → 效率下降 → 更大压力",
                        evidence=[
                            f"工作相关话题出现 {topic_dist.get('work', 0)} 次",
                            f"近期平均情绪: {recent_avg:.1f}/10"
                        ],
                        recommendations=[
                            "尝试打破循环：先处理情绪，再处理工作",
                            "设定工作边界，避免过度投入",
                            "每天留出放松时间",
                            "将大任务分解为小步骤"
                        ],
                        confidence=0.7,
                        impact_score=80,
                        related_metrics=["work", "emotion_score"],
                        visualization_data={
                            "type": "loop_diagram",
                            "nodes": ["工作压力", "情绪低落", "效率下降", "更大压力"],
                            "loop_type": "negative",
                            "break_points": ["情绪低落"]
                        }
                    ))
        
        return insights
    
    def _detect_behavior_patterns(self) -> List[SmartInsight]:
        """检测行为模式"""
        insights = []
        
        # 获取意图分布
        intent_insights = [
            i for i in self.conversation_analyzer.insights
            if i.data_type == DataType.INTENT
        ]
        
        intent_counts = defaultdict(int)
        for insight in intent_insights:
            intent_type = insight.metadata.get("intent_type", "unknown")
            intent_counts[intent_type] += 1
        
        # 检测频繁寻求建议的模式
        if intent_counts.get("seeking_advice", 0) > 5:
            self.insight_counter += 1
            insights.append(SmartInsight(
                insight_id=f"insight_{self.insight_counter}",
                category=InsightCategory.PATTERN,
                level=InsightLevel.INFO,
                title="决策支持需求模式",
                description="你最近频繁寻求建议，这可能表示你正面临一些需要决策的事情",
                evidence=[
                    f"寻求建议的对话出现 {intent_counts.get('seeking_advice', 0)} 次"
                ],
                recommendations=[
                    "尝试使用决策副本功能进行深度分析",
                    "列出决策的利弊清单",
                    "给自己设定决策截止时间"
                ],
                confidence=0.7,
                impact_score=50,
                related_metrics=["intent_seeking_advice"],
                visualization_data={
                    "type": "intent_distribution",
                    "data": dict(intent_counts)
                }
            ))
        
        # 检测频繁抱怨的模式
        if intent_counts.get("complaining", 0) > 3:
            self.insight_counter += 1
            insights.append(SmartInsight(
                insight_id=f"insight_{self.insight_counter}",
                category=InsightCategory.PATTERN,
                level=InsightLevel.SUGGESTION,
                title="负面表达增多",
                description="最近你的对话中负面表达增多，这可能反映了一些潜在的不满或压力",
                evidence=[
                    f"抱怨类表达出现 {intent_counts.get('complaining', 0)} 次"
                ],
                recommendations=[
                    "尝试将抱怨转化为具体的问题描述",
                    "思考哪些是可以改变的，哪些需要接受",
                    "与朋友倾诉或写日记释放情绪"
                ],
                confidence=0.65,
                impact_score=55,
                related_metrics=["intent_complaining"]
            ))
        
        return insights
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘数据"""
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
        """按级别获取洞察"""
        return [i for i in self.insights if i.level == level]
    
    def get_insights_by_category(self, category: InsightCategory) -> List[SmartInsight]:
        """按分类获取洞察"""
        return [i for i in self.insights if i.category == category]


# 全局实例缓存
_engines: Dict[str, SmartInsightEngine] = {}

def get_smart_insight_engine(user_id: str) -> SmartInsightEngine:
    """获取智能洞察引擎实例"""
    if user_id not in _engines:
        _engines[user_id] = SmartInsightEngine(user_id)
    return _engines[user_id]
