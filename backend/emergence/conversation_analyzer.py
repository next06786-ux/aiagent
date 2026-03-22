"""
对话数据分析器
从用户与AI的对话中提取洞察数据
支持文本、图像描述、语音转文字等多模态数据
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
import json
from collections import defaultdict


class DataType(Enum):
    """数据类型"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    EMOTION = "emotion"
    INTENT = "intent"
    ENTITY = "entity"
    TOPIC = "topic"


@dataclass
class ConversationInsight:
    """对话洞察"""
    insight_id: str
    data_type: DataType
    category: str  # health, emotion, social, work, finance, learning
    content: str
    value: Optional[float] = None  # 量化值（如情绪分数）
    confidence: float = 0.8
    timestamp: datetime = field(default_factory=datetime.now)
    source_message_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationAnalyzer:
    """对话分析器 - 从对话中提取生活数据"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.insights: List[ConversationInsight] = []
        self.insight_counter = 0
        
        # 情绪关键词映射
        self.emotion_keywords = {
            "positive": {
                "开心": 0.8, "高兴": 0.8, "快乐": 0.9, "兴奋": 0.85,
                "满足": 0.7, "感谢": 0.6, "期待": 0.7, "幸福": 0.95,
                "棒": 0.75, "好": 0.6, "不错": 0.55, "喜欢": 0.7,
                "爱": 0.85, "舒服": 0.65, "放松": 0.6, "平静": 0.5,
                "happy": 0.8, "great": 0.75, "good": 0.6, "love": 0.85,
                "excited": 0.85, "wonderful": 0.9, "amazing": 0.9
            },
            "negative": {
                "难过": -0.7, "伤心": -0.8, "焦虑": -0.75, "担心": -0.6,
                "压力": -0.65, "累": -0.5, "疲惫": -0.7, "烦": -0.6,
                "生气": -0.8, "愤怒": -0.9, "失望": -0.7, "沮丧": -0.75,
                "孤独": -0.7, "无聊": -0.4, "迷茫": -0.55, "害怕": -0.7,
                "sad": -0.7, "angry": -0.8, "tired": -0.5, "stressed": -0.65,
                "anxious": -0.75, "worried": -0.6, "lonely": -0.7
            }
        }
        
        # 话题关键词映射
        self.topic_keywords = {
            "health": ["睡眠", "运动", "健身", "吃饭", "饮食", "身体", "生病", "医院", 
                      "头疼", "感冒", "锻炼", "跑步", "健康", "sleep", "exercise", "health"],
            "work": ["工作", "上班", "加班", "项目", "会议", "老板", "同事", "任务",
                    "deadline", "工资", "升职", "work", "job", "meeting", "project"],
            "social": ["朋友", "家人", "父母", "聚会", "约会", "社交", "聊天", "见面",
                      "friend", "family", "party", "date", "relationship"],
            "finance": ["钱", "花费", "消费", "存款", "投资", "工资", "账单", "贷款",
                       "money", "spend", "save", "invest", "budget"],
            "learning": ["学习", "读书", "课程", "考试", "技能", "知识", "培训",
                        "learn", "study", "book", "course", "skill"],
            "emotion": ["心情", "感觉", "情绪", "开心", "难过", "焦虑", "压力",
                       "mood", "feel", "emotion", "happy", "sad"]
        }
        
        # 意图模式
        self.intent_patterns = {
            "seeking_advice": [r"怎么办", r"该怎么", r"如何", r"建议", r"帮我", r"what should"],
            "sharing_experience": [r"今天", r"刚才", r"昨天", r"最近", r"我.*了"],
            "expressing_emotion": [r"我觉得", r"我感觉", r"心情", r"i feel", r"i'm feeling"],
            "asking_question": [r"\?$", r"？$", r"吗$", r"呢$", r"什么", r"为什么", r"how", r"why", r"what"],
            "planning": [r"打算", r"计划", r"准备", r"想要", r"plan to", r"going to"],
            "complaining": [r"烦死", r"受不了", r"讨厌", r"hate", r"annoying"]
        }
    
    def analyze_message(self, message: str, role: str = "user", 
                       message_id: str = "", metadata: Dict = None,
                       timestamp: datetime = None) -> List[ConversationInsight]:
        """
        分析单条消息，提取洞察
        
        Args:
            message: 消息内容
            role: 角色 (user/assistant)
            message_id: 消息ID
            metadata: 元数据（可包含图像描述、语音情感等）
            timestamp: 消息时间戳
        
        Returns:
            提取的洞察列表
        """
        if role != "user":  # 只分析用户消息
            return []
        
        if not message or not message.strip():
            return []
        
        insights = []
        metadata = metadata or {}
        msg_timestamp = timestamp or datetime.now()
        
        # 1. 情绪分析
        emotion_insight = self._analyze_emotion(message, message_id, metadata, msg_timestamp)
        if emotion_insight:
            insights.append(emotion_insight)
        
        # 2. 话题识别
        topic_insights = self._identify_topics(message, message_id, msg_timestamp)
        insights.extend(topic_insights)
        
        # 3. 意图识别
        intent_insight = self._identify_intent(message, message_id, msg_timestamp)
        if intent_insight:
            insights.append(intent_insight)
        
        # 4. 实体提取
        entity_insights = self._extract_entities(message, message_id, msg_timestamp)
        insights.extend(entity_insights)
        
        # 5. 多模态数据处理
        if metadata.get("image_description"):
            image_insight = self._analyze_image_description(
                metadata["image_description"], message_id, msg_timestamp)
            if image_insight:
                insights.append(image_insight)
        
        if metadata.get("voice_emotion"):
            voice_insight = self._analyze_voice_emotion(
                metadata["voice_emotion"], message_id, msg_timestamp)
            if voice_insight:
                insights.append(voice_insight)
        
        # 保存洞察
        self.insights.extend(insights)
        
        return insights
    
    def _analyze_emotion(self, message: str, message_id: str, 
                        metadata: Dict, timestamp: datetime) -> Optional[ConversationInsight]:
        """分析情绪"""
        emotion_score = 0.0
        emotion_count = 0
        detected_emotions = []
        
        message_lower = message.lower()
        
        # 检测正面情绪
        for keyword, score in self.emotion_keywords["positive"].items():
            if keyword in message_lower:
                emotion_score += score
                emotion_count += 1
                detected_emotions.append(keyword)
        
        # 检测负面情绪
        for keyword, score in self.emotion_keywords["negative"].items():
            if keyword in message_lower:
                emotion_score += score
                emotion_count += 1
                detected_emotions.append(keyword)
        
        # 考虑语音情感（如果有）
        if metadata.get("voice_emotion"):
            voice_score = metadata["voice_emotion"].get("score", 0)
            emotion_score = (emotion_score + voice_score) / 2 if emotion_count > 0 else voice_score
            emotion_count += 1
        
        if emotion_count > 0:
            avg_score = emotion_score / emotion_count
            # 归一化到 0-10
            normalized_score = (avg_score + 1) * 5
            
            self.insight_counter += 1
            insight = ConversationInsight(
                insight_id=f"emotion_{self.insight_counter}",
                data_type=DataType.EMOTION,
                category="emotion",
                content=f"情绪状态: {', '.join(detected_emotions)}",
                value=normalized_score,
                confidence=min(0.5 + emotion_count * 0.1, 0.95),
                source_message_id=message_id,
                metadata={"detected_emotions": detected_emotions, "raw_score": avg_score}
            )
            insight.timestamp = timestamp
            return insight
        
        return None
    
    def _identify_topics(self, message: str, message_id: str, 
                        timestamp: datetime) -> List[ConversationInsight]:
        """识别话题"""
        insights = []
        message_lower = message.lower()
        
        for topic, keywords in self.topic_keywords.items():
            matched_keywords = [kw for kw in keywords if kw in message_lower]
            if matched_keywords:
                self.insight_counter += 1
                insight = ConversationInsight(
                    insight_id=f"topic_{self.insight_counter}",
                    data_type=DataType.TOPIC,
                    category=topic,
                    content=f"话题: {topic}",
                    confidence=min(0.5 + len(matched_keywords) * 0.15, 0.95),
                    source_message_id=message_id,
                    metadata={"matched_keywords": matched_keywords}
                )
                insight.timestamp = timestamp
                insights.append(insight)
        
        return insights
    
    def _identify_intent(self, message: str, message_id: str,
                        timestamp: datetime) -> Optional[ConversationInsight]:
        """识别意图"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    self.insight_counter += 1
                    insight = ConversationInsight(
                        insight_id=f"intent_{self.insight_counter}",
                        data_type=DataType.INTENT,
                        category="intent",
                        content=f"意图: {intent}",
                        confidence=0.75,
                        source_message_id=message_id,
                        metadata={"intent_type": intent}
                    )
                    insight.timestamp = timestamp
                    return insight
        return None
    
    def _extract_entities(self, message: str, message_id: str,
                         timestamp: datetime) -> List[ConversationInsight]:
        """提取实体（人物、地点、时间等）"""
        insights = []
        
        # 时间实体
        time_patterns = [
            (r"(\d{1,2})[点时]", "time"),
            (r"(早上|上午|中午|下午|晚上|凌晨)", "time_period"),
            (r"(今天|昨天|明天|后天|前天)", "relative_day"),
            (r"(\d+)小时", "duration_hours"),
            (r"(\d+)分钟", "duration_minutes"),
        ]
        
        for pattern, entity_type in time_patterns:
            matches = re.findall(pattern, message)
            for match in matches:
                self.insight_counter += 1
                insight = ConversationInsight(
                    insight_id=f"entity_{self.insight_counter}",
                    data_type=DataType.ENTITY,
                    category="time",
                    content=f"时间实体: {match}",
                    confidence=0.9,
                    source_message_id=message_id,
                    metadata={"entity_type": entity_type, "value": match}
                )
                insight.timestamp = timestamp
                insights.append(insight)
        
        # 数值实体（可能是健康数据）
        number_patterns = [
            (r"睡了?(\d+\.?\d*)小时", "sleep_hours"),
            (r"跑了?(\d+\.?\d*)公里", "run_distance"),
            (r"走了?(\d+)步", "steps"),
            (r"体重(\d+\.?\d*)", "weight"),
            (r"花了?(\d+)块?元?", "expense"),
        ]
        
        for pattern, metric_type in number_patterns:
            match = re.search(pattern, message)
            if match:
                self.insight_counter += 1
                value = float(match.group(1))
                insight = ConversationInsight(
                    insight_id=f"entity_{self.insight_counter}",
                    data_type=DataType.ENTITY,
                    category=self._get_category_for_metric(metric_type),
                    content=f"{metric_type}: {value}",
                    value=value,
                    confidence=0.95,
                    source_message_id=message_id,
                    metadata={"metric_type": metric_type}
                )
                insight.timestamp = timestamp
                insights.append(insight)
        
        return insights
    
    def _get_category_for_metric(self, metric_type: str) -> str:
        """根据指标类型获取分类"""
        category_map = {
            "sleep_hours": "health",
            "run_distance": "health",
            "steps": "health",
            "weight": "health",
            "expense": "finance",
        }
        return category_map.get(metric_type, "general")
    
    def _analyze_image_description(self, description: str, 
                                   message_id: str) -> Optional[ConversationInsight]:
        """分析图像描述"""
        self.insight_counter += 1
        
        # 从图像描述中推断场景和情绪
        scene_keywords = {
            "outdoor": ["户外", "公园", "山", "海", "天空", "outdoor", "park", "nature"],
            "food": ["食物", "餐", "吃", "美食", "food", "meal", "restaurant"],
            "social": ["朋友", "聚会", "合影", "people", "friends", "party"],
            "work": ["办公", "电脑", "会议", "office", "computer", "meeting"],
        }
        
        detected_scenes = []
        for scene, keywords in scene_keywords.items():
            if any(kw in description.lower() for kw in keywords):
                detected_scenes.append(scene)
        
        return ConversationInsight(
            insight_id=f"image_{self.insight_counter}",
            data_type=DataType.IMAGE,
            category="activity" if detected_scenes else "general",
            content=f"图像场景: {', '.join(detected_scenes) if detected_scenes else '未识别'}",
            confidence=0.7,
            source_message_id=message_id,
            metadata={"description": description, "scenes": detected_scenes}
        )
    
    def _analyze_voice_emotion(self, voice_data: Dict, 
                               message_id: str) -> Optional[ConversationInsight]:
        """分析语音情感"""
        self.insight_counter += 1
        
        emotion = voice_data.get("emotion", "neutral")
        intensity = voice_data.get("intensity", 0.5)
        
        return ConversationInsight(
            insight_id=f"voice_{self.insight_counter}",
            data_type=DataType.VOICE,
            category="emotion",
            content=f"语音情感: {emotion}",
            value=intensity * 10,  # 归一化到0-10
            confidence=voice_data.get("confidence", 0.7),
            source_message_id=message_id,
            metadata=voice_data
        )
    
    def get_insights_by_category(self, category: str, 
                                 days: int = 7) -> List[ConversationInsight]:
        """获取指定分类的洞察"""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            insight for insight in self.insights
            if insight.category == category and insight.timestamp > cutoff
        ]
    
    def get_emotion_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取情绪趋势"""
        cutoff = datetime.now() - timedelta(days=days)
        emotion_insights = [
            insight for insight in self.insights
            if insight.data_type == DataType.EMOTION and insight.timestamp > cutoff
        ]
        
        # 按天聚合
        daily_emotions = defaultdict(list)
        for insight in emotion_insights:
            day_key = insight.timestamp.strftime("%Y-%m-%d")
            if insight.value is not None:
                daily_emotions[day_key].append(insight.value)
        
        trend = []
        for day, values in sorted(daily_emotions.items()):
            trend.append({
                "date": day,
                "avg_emotion": sum(values) / len(values),
                "count": len(values)
            })
        
        return trend
    
    def get_topic_distribution(self, days: int = 7) -> Dict[str, int]:
        """获取话题分布"""
        cutoff = datetime.now() - timedelta(days=days)
        topic_insights = [
            insight for insight in self.insights
            if insight.data_type == DataType.TOPIC and insight.timestamp > cutoff
        ]
        
        distribution = defaultdict(int)
        for insight in topic_insights:
            distribution[insight.category] += 1
        
        return dict(distribution)
    
    def export_for_emergence(self) -> Dict[str, List[float]]:
        """导出数据供涌现检测使用"""
        # 按天聚合各类指标
        daily_data = defaultdict(lambda: defaultdict(list))
        
        for insight in self.insights:
            day_key = insight.timestamp.strftime("%Y-%m-%d")
            
            if insight.data_type == DataType.EMOTION and insight.value is not None:
                daily_data[day_key]["emotion_score"].append(insight.value)
            
            if insight.data_type == DataType.ENTITY and insight.value is not None:
                metric_type = insight.metadata.get("metric_type", "unknown")
                daily_data[day_key][metric_type].append(insight.value)
            
            if insight.data_type == DataType.TOPIC:
                daily_data[day_key][f"topic_{insight.category}"].append(1)
        
        # 计算每天的平均值
        result = {}
        for day, metrics in daily_data.items():
            result[day] = {}
            for metric, values in metrics.items():
                result[day][metric] = sum(values) / len(values)
        
        return result
