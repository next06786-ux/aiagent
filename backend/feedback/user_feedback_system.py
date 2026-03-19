"""
用户反馈系统 - Phase 2
收集、处理和分析用户反馈，驱动系统改进
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict
import json


class FeedbackType(Enum):
    """反馈类型"""
    ADOPTION = "adoption"  # 采纳反馈
    REJECTION = "rejection"  # 拒绝反馈
    PARTIAL = "partial"  # 部分采纳
    RATING = "rating"  # 评分反馈
    COMMENT = "comment"  # 评论反馈
    BUG_REPORT = "bug_report"  # 错误报告
    FEATURE_REQUEST = "feature_request"  # 功能请求


class FeedbackSentiment(Enum):
    """反馈情感"""
    VERY_POSITIVE = 1.0
    POSITIVE = 0.5
    NEUTRAL = 0.0
    NEGATIVE = -0.5
    VERY_NEGATIVE = -1.0


@dataclass
class UserFeedback:
    """用户反馈"""
    feedback_id: str
    user_id: str
    feedback_type: FeedbackType
    content: str
    rating: Optional[float] = None  # 0-5
    sentiment: Optional[FeedbackSentiment] = None
    related_pattern_id: Optional[str] = None  # 相关的涌现模式ID
    related_recommendation_id: Optional[str] = None  # 相关的建议ID
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 元数据
    device_info: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "feedback_id": self.feedback_id,
            "user_id": self.user_id,
            "feedback_type": self.feedback_type.value,
            "content": self.content,
            "rating": self.rating,
            "sentiment": self.sentiment.value if self.sentiment else None,
            "related_pattern_id": self.related_pattern_id,
            "related_recommendation_id": self.related_recommendation_id,
            "timestamp": self.timestamp.isoformat(),
            "device_info": self.device_info,
            "context": self.context
        }


@dataclass
class FeedbackAnalysis:
    """反馈分析结果"""
    total_feedback: int
    average_rating: float
    sentiment_distribution: Dict[str, int]
    feedback_type_distribution: Dict[str, int]
    key_themes: List[Tuple[str, int]]  # (主题, 出现次数)
    improvement_areas: List[str]
    positive_aspects: List[str]
    action_items: List[str]


class FeedbackCollector:
    """反馈收集器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.feedbacks: List[UserFeedback] = []
        self.feedback_index = defaultdict(list)  # 按类型索引
    
    def collect_feedback(
        self,
        feedback_type: FeedbackType,
        content: str,
        rating: Optional[float] = None,
        related_pattern_id: Optional[str] = None,
        related_recommendation_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """收集用户反馈"""
        
        # 生成反馈ID
        feedback_id = f"fb_{datetime.now().timestamp()}"
        
        # 分析情感
        sentiment = self._analyze_sentiment(content, rating)
        
        # 创建反馈对象
        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=self.user_id,
            feedback_type=feedback_type,
            content=content,
            rating=rating,
            sentiment=sentiment,
            related_pattern_id=related_pattern_id,
            related_recommendation_id=related_recommendation_id,
            device_info=device_info or {},
            context=context or {}
        )
        
        # 存储反馈
        self.feedbacks.append(feedback)
        self.feedback_index[feedback_type.value].append(feedback)
        
        return feedback
    
    def _analyze_sentiment(
        self,
        content: str,
        rating: Optional[float] = None
    ) -> FeedbackSentiment:
        """分析反馈情感"""
        
        # 如果有评分，使用评分
        if rating is not None:
            if rating >= 4.5:
                return FeedbackSentiment.VERY_POSITIVE
            elif rating >= 3.5:
                return FeedbackSentiment.POSITIVE
            elif rating >= 2.5:
                return FeedbackSentiment.NEUTRAL
            elif rating >= 1.5:
                return FeedbackSentiment.NEGATIVE
            else:
                return FeedbackSentiment.VERY_NEGATIVE
        
        # 基于内容的简单情感分析
        positive_words = ['好', '很好', '棒', '喜欢', '有帮助', '改进', '满意']
        negative_words = ['差', '不好', '讨厌', '没用', '问题', '错误', '不满意']
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return FeedbackSentiment.POSITIVE if positive_count > 1 else FeedbackSentiment.POSITIVE
        elif negative_count > positive_count:
            return FeedbackSentiment.NEGATIVE if negative_count > 1 else FeedbackSentiment.NEGATIVE
        else:
            return FeedbackSentiment.NEUTRAL
    
    def get_feedbacks(
        self,
        feedback_type: Optional[FeedbackType] = None,
        days: int = 30
    ) -> List[UserFeedback]:
        """获取反馈"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if feedback_type:
            feedbacks = self.feedback_index[feedback_type.value]
        else:
            feedbacks = self.feedbacks
        
        return [f for f in feedbacks if f.timestamp >= cutoff_date]
    
    def get_feedback_count(self) -> int:
        """获取反馈总数"""
        return len(self.feedbacks)


class FeedbackAnalyzer:
    """反馈分析器"""
    
    def __init__(self):
        self.theme_keywords = {
            "准确性": ["准确", "精准", "错误", "不准", "偏差"],
            "有用性": ["有用", "有帮助", "没用", "无用", "浪费"],
            "易用性": ["简单", "容易", "复杂", "困难", "不好用"],
            "性能": ["快", "慢", "卡", "响应", "延迟"],
            "界面": ["界面", "UI", "设计", "美观", "丑陋"],
            "功能": ["功能", "特性", "缺少", "需要", "建议"],
            "稳定性": ["稳定", "崩溃", "错误", "问题", "异常"],
            "隐私": ["隐私", "安全", "数据", "泄露", "保护"]
        }
    
    def analyze_feedbacks(self, feedbacks: List[UserFeedback]) -> FeedbackAnalysis:
        """分析反馈"""
        
        if not feedbacks:
            return FeedbackAnalysis(
                total_feedback=0,
                average_rating=0.0,
                sentiment_distribution={},
                feedback_type_distribution={},
                key_themes=[],
                improvement_areas=[],
                positive_aspects=[],
                action_items=[]
            )
        
        # 1. 基本统计
        total_feedback = len(feedbacks)
        
        # 2. 平均评分
        ratings = [f.rating for f in feedbacks if f.rating is not None]
        average_rating = np.mean(ratings) if ratings else 0.0
        
        # 3. 情感分布
        sentiment_distribution = defaultdict(int)
        for f in feedbacks:
            if f.sentiment:
                sentiment_distribution[f.sentiment.name] += 1
        
        # 4. 反馈类型分布
        feedback_type_distribution = defaultdict(int)
        for f in feedbacks:
            feedback_type_distribution[f.feedback_type.value] += 1
        
        # 5. 提取主题
        key_themes = self._extract_themes(feedbacks)
        
        # 6. 识别改进领域
        improvement_areas = self._identify_improvement_areas(feedbacks)
        
        # 7. 识别正面方面
        positive_aspects = self._identify_positive_aspects(feedbacks)
        
        # 8. 生成行动项
        action_items = self._generate_action_items(feedbacks, improvement_areas)
        
        return FeedbackAnalysis(
            total_feedback=total_feedback,
            average_rating=average_rating,
            sentiment_distribution=dict(sentiment_distribution),
            feedback_type_distribution=dict(feedback_type_distribution),
            key_themes=key_themes,
            improvement_areas=improvement_areas,
            positive_aspects=positive_aspects,
            action_items=action_items
        )
    
    def _extract_themes(self, feedbacks: List[UserFeedback]) -> List[Tuple[str, int]]:
        """提取主题"""
        theme_counts = defaultdict(int)
        
        for feedback in feedbacks:
            content = feedback.content.lower()
            
            for theme, keywords in self.theme_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        theme_counts[theme] += 1
                        break
        
        # 按出现次数排序
        themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        return themes[:5]  # 返回前5个主题
    
    def _identify_improvement_areas(self, feedbacks: List[UserFeedback]) -> List[str]:
        """识别改进领域"""
        improvement_areas = []
        
        # 找出负面反馈最多的领域
        negative_feedbacks = [
            f for f in feedbacks
            if f.sentiment and f.sentiment.value < 0
        ]
        
        if negative_feedbacks:
            themes = self._extract_themes(negative_feedbacks)
            improvement_areas = [theme[0] for theme in themes[:3]]
        
        return improvement_areas
    
    def _identify_positive_aspects(self, feedbacks: List[UserFeedback]) -> List[str]:
        """识别正面方面"""
        positive_aspects = []
        
        # 找出正面反馈最多的领域
        positive_feedbacks = [
            f for f in feedbacks
            if f.sentiment and f.sentiment.value > 0
        ]
        
        if positive_feedbacks:
            themes = self._extract_themes(positive_feedbacks)
            positive_aspects = [theme[0] for theme in themes[:3]]
        
        return positive_aspects
    
    def _generate_action_items(
        self,
        feedbacks: List[UserFeedback],
        improvement_areas: List[str]
    ) -> List[str]:
        """生成行动项"""
        action_items = []
        
        for area in improvement_areas:
            if area == "准确性":
                action_items.append("改进算法准确度，目标90%+")
            elif area == "有用性":
                action_items.append("增加更多实用功能和建议")
            elif area == "易用性":
                action_items.append("简化用户界面，改进交互流程")
            elif area == "性能":
                action_items.append("优化系统性能，减少延迟")
            elif area == "界面":
                action_items.append("改进UI设计，提升视觉体验")
            elif area == "功能":
                action_items.append("实现用户请求的新功能")
            elif area == "稳定性":
                action_items.append("修复已知问题，提高系统稳定性")
            elif area == "隐私":
                action_items.append("加强隐私保护和数据安全")
        
        return action_items


class FeedbackProcessor:
    """反馈处理器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.collector = FeedbackCollector(user_id)
        self.analyzer = FeedbackAnalyzer()
        
        # 反馈处理历史
        self.processing_history: List[Dict[str, Any]] = []
    
    def process_feedback(
        self,
        feedback_type: FeedbackType,
        content: str,
        rating: Optional[float] = None,
        related_pattern_id: Optional[str] = None,
        related_recommendation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理反馈"""
        
        # 1. 收集反馈
        feedback = self.collector.collect_feedback(
            feedback_type=feedback_type,
            content=content,
            rating=rating,
            related_pattern_id=related_pattern_id,
            related_recommendation_id=related_recommendation_id
        )
        
        # 2. 分析反馈
        all_feedbacks = self.collector.get_feedbacks()
        analysis = self.analyzer.analyze_feedbacks(all_feedbacks)
        
        # 3. 生成处理结果
        result = {
            "feedback_id": feedback.feedback_id,
            "status": "processed",
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "total_feedback": analysis.total_feedback,
                "average_rating": analysis.average_rating,
                "sentiment_distribution": analysis.sentiment_distribution,
                "key_themes": analysis.key_themes,
                "improvement_areas": analysis.improvement_areas,
                "positive_aspects": analysis.positive_aspects,
                "action_items": analysis.action_items
            }
        }
        
        # 4. 记录处理历史
        self.processing_history.append(result)
        
        return result
    
    def get_feedback_summary(self, days: int = 30) -> Dict[str, Any]:
        """获取反馈总结"""
        
        feedbacks = self.collector.get_feedbacks(days=days)
        analysis = self.analyzer.analyze_feedbacks(feedbacks)
        
        return {
            "period_days": days,
            "total_feedback": analysis.total_feedback,
            "average_rating": analysis.average_rating,
            "sentiment_distribution": analysis.sentiment_distribution,
            "feedback_type_distribution": analysis.feedback_type_distribution,
            "key_themes": analysis.key_themes,
            "improvement_areas": analysis.improvement_areas,
            "positive_aspects": analysis.positive_aspects,
            "action_items": analysis.action_items,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """获取改进建议"""
        
        feedbacks = self.collector.get_feedbacks()
        analysis = self.analyzer.analyze_feedbacks(feedbacks)
        
        recommendations = []
        
        for area in analysis.improvement_areas:
            # 找出该领域的具体反馈
            related_feedbacks = [
                f for f in feedbacks
                if area.lower() in f.content.lower()
            ]
            
            recommendation = {
                "area": area,
                "priority": "high" if len(related_feedbacks) > 3 else "medium",
                "feedback_count": len(related_feedbacks),
                "average_sentiment": np.mean([
                    f.sentiment.value for f in related_feedbacks if f.sentiment
                ]) if related_feedbacks else 0.0,
                "suggested_actions": self._get_suggested_actions(area),
                "estimated_impact": self._estimate_impact(area)
            }
            
            recommendations.append(recommendation)
        
        # 按优先级排序
        recommendations.sort(key=lambda x: (x["priority"] == "high", x["feedback_count"]), reverse=True)
        
        return recommendations
    
    def _get_suggested_actions(self, area: str) -> List[str]:
        """获取建议的行动"""
        actions = {
            "准确性": [
                "收集更多训练数据",
                "改进算法模型",
                "增加验证机制",
                "进行A/B测试"
            ],
            "有用性": [
                "增加新功能",
                "改进建议质量",
                "个性化推荐",
                "用户教育"
            ],
            "易用性": [
                "简化界面",
                "改进导航",
                "添加帮助文档",
                "用户测试"
            ],
            "性能": [
                "优化算法",
                "缓存优化",
                "数据库优化",
                "并发处理"
            ],
            "界面": [
                "重新设计UI",
                "改进配色",
                "优化排版",
                "响应式设计"
            ],
            "功能": [
                "实现新功能",
                "扩展现有功能",
                "集成第三方服务",
                "API开放"
            ],
            "稳定性": [
                "错误处理",
                "异常恢复",
                "监控告警",
                "压力测试"
            ],
            "隐私": [
                "加密存储",
                "访问控制",
                "审计日志",
                "合规检查"
            ]
        }
        
        return actions.get(area, ["进行用户研究", "收集更多反馈"])
    
    def _estimate_impact(self, area: str) -> str:
        """估计改进的影响"""
        high_impact_areas = ["准确性", "有用性", "稳定性"]
        
        if area in high_impact_areas:
            return "high"
        elif area in ["易用性", "性能"]:
            return "medium"
        else:
            return "low"
    
    def export_feedback_report(self, filepath: str):
        """导出反馈报告"""
        
        summary = self.get_feedback_summary()
        recommendations = self.get_improvement_recommendations()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "user_id": self.user_id,
            "summary": summary,
            "recommendations": recommendations,
            "processing_history": self.processing_history[-10:]  # 最近10条
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


# 全局实例
_feedback_processors = {}

def get_feedback_processor(user_id: str) -> FeedbackProcessor:
    """获取反馈处理器实例"""
    if user_id not in _feedback_processors:
        _feedback_processors[user_id] = FeedbackProcessor(user_id)
    return _feedback_processors[user_id]

