"""
鏅鸿兘娲炲療寮曟搸
鏁村悎瀵硅瘽鍒嗘瀽鍜屾秾鐜版娴嬶紝鐢熸垚楂樼骇娲炲療
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
    """娲炲療绾у埆"""
    INFO = "info"           # 淇℃伅鎬ф礊瀵?
    SUGGESTION = "suggestion"  # 寤鸿鎬ф礊瀵?
    WARNING = "warning"     # 璀﹀憡鎬ф礊瀵?
    CRITICAL = "critical"   # 鍏抽敭鎬ф礊瀵?


class InsightCategory(Enum):
    """娲炲療鍒嗙被"""
    CASCADE = "cascade"           # 绾ц仈鏁堝簲
    SYNERGY = "synergy"           # 鍗忓悓澧炵泭
    TIPPING_POINT = "tipping_point"  # 涓寸晫鐐?
    FEEDBACK_LOOP = "feedback_loop"  # 鍙嶉鐜矾
    PATTERN = "pattern"           # 琛屼负妯″紡
    TREND = "trend"               # 瓒嬪娍鍙樺寲
    ANOMALY = "anomaly"           # 寮傚父妫€娴?


@dataclass
class SmartInsight:
    """鏅鸿兘娲炲療"""
    insight_id: str
    category: InsightCategory
    level: InsightLevel
    title: str
    description: str
    evidence: List[str]  # 鏀拺璇佹嵁
    recommendations: List[str]  # 寤鸿琛屽姩
    confidence: float
    impact_score: float  # 褰卞搷鍔涘垎鏁?0-100
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
    """鏅鸿兘娲炲療寮曟搸"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.conversation_analyzer = ConversationAnalyzer(user_id)
        self.emergence_detector = EmergenceDetector(user_id)
        self.insights: List[SmartInsight] = []
        
        # 瀛樺偍鐨勬礊瀵熸暟鎹紙浠庢暟鎹簱鍔犺浇锛?
        self.stored_insights: List[Dict[str, Any]] = []
    
    def _gen_insight_id(self) -> str:
        """鐢熸垚鍞竴鐨?insight_id"""
        import uuid
        return f"insight_{uuid.uuid4().hex[:12]}"
        
        # LLM鏈嶅姟锛堝彲閫夛紝鐢ㄤ簬鐢熸垚鏇存櫤鑳界殑娲炲療鎻忚堪锛?
        self.llm = None
        try:
            from backend.llm.llm_service import get_llm_service
            self.llm = get_llm_service()
        except Exception:
            pass
    
    def load_stored_insights(self, insights: List[Dict[str, Any]]):
        """
        鍔犺浇宸插瓨鍌ㄧ殑娲炲療鏁版嵁锛堜粠鏁版嵁搴撹鍙栫殑锛?
        
        Args:
            insights: 娲炲療鏁版嵁鍒楄〃
        """
        self.stored_insights = insights
        
        # 灏嗘暟鎹悓姝ュ埌娑岀幇妫€娴嬪櫒
        self._sync_stored_to_emergence_detector()
        
        print(f"[鏅鸿兘娲炲療寮曟搸] 鍔犺浇浜?{len(insights)} 鏉″瓨鍌ㄧ殑娲炲療鏁版嵁")
    
    def _sync_stored_to_emergence_detector(self):
        """灏嗗瓨鍌ㄧ殑娲炲療鏁版嵁鍚屾鍒版秾鐜版娴嬪櫒"""
        from collections import defaultdict
        
        # 鎸夊ぉ鑱氬悎鏁版嵁
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
            
            # 鎯呯华鏁版嵁
            if data_type == "emotion" and value is not None:
                daily_data[day_key]["emotion_score"].append(value)
            
            # 璇濋鏁版嵁
            if data_type == "topic":
                daily_data[day_key][f"topic_{category}"].append(1)
            
            # 瀹炰綋鏁版嵁锛堝仴搴枫€佽储鍔＄瓑锛?
            if data_type == "entity" and value is not None:
                metadata = insight.get("metadata", {})
                metric_type = metadata.get("metric_type", category)
                daily_data[day_key][metric_type].append(value)
            
            # 鎰忓浘鏁版嵁
            if data_type == "intent":
                metadata = insight.get("metadata", {})
                intent_type = metadata.get("intent_type", "unknown")
                daily_data[day_key][f"intent_{intent_type}"].append(1)
        
        # 璁＄畻姣忓ぉ鐨勫钩鍧囧€煎苟娣诲姞鍒版秾鐜版娴嬪櫒
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
        澶勭悊瀵硅瘽娑堟伅锛屾彁鍙栨礊瀵熸暟鎹?
        
        Args:
            messages: 娑堟伅鍒楄〃 [{"role": "user", "content": "...", "id": "...", "metadata": {...}}]
        
        Returns:
            鎻愬彇鐨勬礊瀵熷垪琛?
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
        
        # 灏嗘暟鎹悓姝ュ埌娑岀幇妫€娴嬪櫒
        self._sync_to_emergence_detector()
        
        return all_insights
    
    def _sync_to_emergence_detector(self):
        """灏嗗璇濇礊瀵熷悓姝ュ埌娑岀幇妫€娴嬪櫒"""
        export_data = self.conversation_analyzer.export_for_emergence()
        
        for day, metrics in export_data.items():
            timestamp = datetime.strptime(day, "%Y-%m-%d")
            self.emergence_detector.add_data_point(metrics, timestamp)
    
    def generate_insights(self) -> List[SmartInsight]:
        """
        鐢熸垚鏅鸿兘娲炲療
        
        Returns:
            鏅鸿兘娲炲療鍒楄〃
        """
        new_insights = []
        
        # 1. 妫€娴嬫秾鐜扮幇璞?
        emergence_events = self.emergence_detector.detect_all_emergences()
        
        # 2. 灏嗘秾鐜颁簨浠惰浆鎹负鏅鸿兘娲炲療
        for event in emergence_events:
            insight = self._convert_emergence_to_insight(event)
            if insight:
                new_insights.append(insight)
        
        # 3. 鐢熸垚绾ц仈鏁堝簲娲炲療
        cascade_insights = self._detect_cascade_effects()
        new_insights.extend(cascade_insights)
        
        # 4. 鐢熸垚鍗忓悓澧炵泭娲炲療
        synergy_insights = self._detect_synergy_opportunities()
        new_insights.extend(synergy_insights)
        
        # 5. 鐢熸垚涓寸晫鐐归璀?
        tipping_insights = self._detect_tipping_points()
        new_insights.extend(tipping_insights)
        
        # 6. 鐢熸垚鍙嶉鐜矾娲炲療
        loop_insights = self._detect_feedback_loops()
        new_insights.extend(loop_insights)
        
        # 7. 鐢熸垚琛屼负妯″紡娲炲療
        pattern_insights = self._detect_behavior_patterns()
        new_insights.extend(pattern_insights)
        
        # 8. 鎸夊奖鍝嶅姏鎺掑簭
        new_insights.sort(key=lambda x: x.impact_score, reverse=True)
        
        # 淇濆瓨娲炲療
        self.insights.extend(new_insights)
        
        return new_insights
    
    def _convert_emergence_to_insight(self, event: EmergenceEvent) -> Optional[SmartInsight]:
        """灏嗘秾鐜颁簨浠惰浆鎹负鏅鸿兘娲炲療"""
        self.insight_counter += 1
        
        # 鏍规嵁娑岀幇绫诲瀷纭畾娲炲療鍒嗙被鍜岀骇鍒?
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
            evidence=[f"妫€娴嬪埌{event.emergence_type.value}绫诲瀷鐨勬秾鐜扮幇璞?],
            recommendations=self._generate_recommendations(event),
            confidence=event.confidence,
            impact_score=event.strength * 100,
            related_metrics=event.involved_metrics
        )
    
    def _generate_insight_title(self, event: EmergenceEvent) -> str:
        """鐢熸垚娲炲療鏍囬"""
        type_titles = {
            EmergenceType.PATTERN: "鍙戠幇鏂版ā寮?,
            EmergenceType.NONLINEAR: "闈炵嚎鎬у彉鍖?,
            EmergenceType.SYNERGY: "鍗忓悓鏁堝簲",
            EmergenceType.FEEDBACK_LOOP: "鍙嶉寰幆",
            EmergenceType.THRESHOLD: "涓寸晫鐐归璀?,
            EmergenceType.BIFURCATION: "琛屼负鍒嗗寲",
        }
        return type_titles.get(event.emergence_type, "鏂板彂鐜?)
    
    def _generate_recommendations(self, event: EmergenceEvent) -> List[str]:
        """鐢熸垚寤鸿"""
        recommendations = []
        
        if event.emergence_type == EmergenceType.FEEDBACK_LOOP:
            if event.strength > 0.7:
                recommendations.append("杩欐槸涓€涓己鍙嶉寰幆锛屽缓璁富鍔ㄥ共棰勬墦鐮磋礋鍚戝惊鐜?)
            recommendations.append("鍏虫敞寰幆涓殑鍏抽敭鑺傜偣锛屽皬鏀瑰彉鍙兘甯︽潵澶ф晥鏋?)
        
        elif event.emergence_type == EmergenceType.THRESHOLD:
            recommendations.append("浣犳鎺ヨ繎涓€涓复鐣岀偣锛屽缓璁彁鍓嶉噰鍙栬鍔?)
            recommendations.append("鐩戞帶鐩稿叧鎸囨爣鐨勫彉鍖栬秼鍔?)
        
        elif event.emergence_type == EmergenceType.SYNERGY:
            recommendations.append("缁х画淇濇寔杩欎簺琛屼负鐨勭粍鍚堬紝瀹冧滑浜х敓浜嗗崗鍚屾晥搴?)
            recommendations.append("灏濊瘯澧炲姞杩欎簺娲诲姩鐨勯鐜?)
        
        elif event.emergence_type == EmergenceType.PATTERN:
            recommendations.append("杩欎釜妯″紡鍊煎緱鍏虫敞锛屽彲鑳芥彮绀轰簡娣卞眰瑙勫緥")
        
        return recommendations
    
    def _detect_cascade_effects(self) -> List[SmartInsight]:
        """妫€娴嬬骇鑱旀晥搴?""
        insights = []
        
        # 鑾峰彇鎯呯华瓒嬪娍
        emotion_trend = self.conversation_analyzer.get_emotion_trend(days=14)
        
        if len(emotion_trend) >= 3:
            # 妫€娴嬫儏缁笅闄嶆槸鍚︿即闅忓叾浠栨寚鏍囧彉鍖?
            recent_emotions = [d["avg_emotion"] for d in emotion_trend[-3:]]
            if all(recent_emotions[i] < recent_emotions[i-1] for i in range(1, len(recent_emotions))):
                # 鎯呯华鎸佺画涓嬮檷
                self.insight_counter += 1
                insights.append(SmartInsight(
                    insight_id=self._gen_insight_id(),
                    category=InsightCategory.CASCADE,
                    level=InsightLevel.WARNING,
                    title="鎯呯华绾ц仈涓嬮檷",
                    description="浣犵殑鎯呯华鍦ㄨ繃鍘诲嚑澶╂寔缁笅闄嶏紝杩欏彲鑳戒細褰卞搷鍒板伐浣滄晥鐜囥€佺ぞ浜ゆ剰鎰垮拰鐫＄湢璐ㄩ噺",
                    evidence=[
                        f"鎯呯华浠?{recent_emotions[0]:.1f} 涓嬮檷鍒?{recent_emotions[-1]:.1f}",
                        "杩炵画3澶╁憟涓嬮檷瓒嬪娍"
                    ],
                    recommendations=[
                        "灏濊瘯杩涜涓€浜涜浣犲紑蹇冪殑娲诲姩",
                        "涓庢湅鍙嬫垨瀹朵汉鑱婅亰澶?,
                        "淇濊瘉鍏呰冻鐨勭潯鐪?,
                        "閫傚綋杩愬姩鍙互鏀瑰杽鎯呯华"
                    ],
                    confidence=0.8,
                    impact_score=75,
                    related_metrics=["emotion_score"],
                    visualization_data={
                        "type": "cascade_flow",
                        "nodes": ["鎯呯华涓嬮檷", "宸ヤ綔鏁堢巼鈫?, "绀句氦鎰忔効鈫?, "鐫＄湢璐ㄩ噺鈫?],
                        "trend": emotion_trend
                    }
                ))
        
        return insights
    
    def _detect_synergy_opportunities(self) -> List[SmartInsight]:
        """妫€娴嬪崗鍚屽鐩婃満浼?""
        insights = []
        
        # 鑾峰彇璇濋鍒嗗竷
        topic_dist = self.conversation_analyzer.get_topic_distribution(days=7)
        
        # 妫€娴嬪仴搴?绀句氦鐨勫崗鍚?
        if topic_dist.get("health", 0) > 2 and topic_dist.get("social", 0) > 2:
            self.insight_counter += 1
            insights.append(SmartInsight(
                insight_id=self._gen_insight_id(),
                category=InsightCategory.SYNERGY,
                level=InsightLevel.SUGGESTION,
                title="鍋ュ悍涓庣ぞ浜ょ殑鍗忓悓鏈轰細",
                description="浣犳渶杩戝悓鏃跺叧娉ㄥ仴搴峰拰绀句氦璇濋锛岀爺绌惰〃鏄庡皢涓よ€呯粨鍚堬紙濡傜害鏈嬪弸涓€璧疯繍鍔級鏁堟灉鏇村ソ",
                evidence=[
                    f"鍋ュ悍璇濋鍑虹幇 {topic_dist.get('health', 0)} 娆?,
                    f"绀句氦璇濋鍑虹幇 {topic_dist.get('social', 0)} 娆?
                ],
                recommendations=[
                    "灏濊瘯绾︽湅鍙嬩竴璧疯窇姝ユ垨鍋ヨ韩",
                    "鍙傚姞鍥綋杩愬姩娲诲姩",
                    "缁勭粐鎴峰寰掓鑱氫細"
                ],
                confidence=0.75,
                impact_score=65,
                related_metrics=["health", "social"],
                visualization_data={
                    "type": "synergy_diagram",
                    "factors": ["鍋ュ悍娲诲姩", "绀句氦娲诲姩"],
                    "combined_effect": "1+1>2"
                }
            ))
        
        return insights
    
    def _detect_tipping_points(self) -> List[SmartInsight]:
        """妫€娴嬩复鐣岀偣"""
        insights = []
        
        # 鑾峰彇鎯呯华鏁版嵁
        emotion_insights = self.conversation_analyzer.get_insights_by_category("emotion", days=7)
        
        if emotion_insights:
            emotion_values = [i.value for i in emotion_insights if i.value is not None]
            if emotion_values:
                avg_emotion = sum(emotion_values) / len(emotion_values)
                
                # 鎯呯华涓寸晫鐐规娴?
                if avg_emotion < 4:  # 浣庝簬4鍒嗘槸鍗遍櫓鍖?
                    self.insight_counter += 1
                    insights.append(SmartInsight(
                        insight_id=self._gen_insight_id(),
                        category=InsightCategory.TIPPING_POINT,
                        level=InsightLevel.CRITICAL,
                        title="鎯呯华涓寸晫鐐归璀?,
                        description=f"浣犵殑骞冲潎鎯呯华鍒嗘暟涓?{avg_emotion:.1f}锛屽凡鎺ヨ繎涓寸晫鐐广€傛寔缁綆杩峰彲鑳藉鑷存洿涓ラ噸鐨勯棶棰?,
                        evidence=[
                            f"7澶╁钩鍧囨儏缁? {avg_emotion:.1f}/10",
                            f"妫€娴嬪埌 {len(emotion_values)} 娆℃儏缁褰?
                        ],
                        recommendations=[
                            "寤鸿涓庝俊浠荤殑浜哄€捐瘔",
                            "鑰冭檻瀵绘眰涓撲笟甯姪",
                            "灏濊瘯姝ｅ康鍐ユ兂鎴栨繁鍛煎惛",
                            "淇濊瘉鍩烘湰鐨勪綔鎭寰?
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
        """妫€娴嬪弽棣堢幆璺?""
        insights = []
        
        # 浠庡璇濅腑妫€娴嬪彲鑳界殑鍙嶉寰幆妯″紡
        topic_dist = self.conversation_analyzer.get_topic_distribution(days=14)
        emotion_trend = self.conversation_analyzer.get_emotion_trend(days=14)
        
        # 妫€娴嬪帇鍔?鎯呯华璐熷悜寰幆
        if topic_dist.get("work", 0) > 5:  # 宸ヤ綔璇濋棰戠箒
            if emotion_trend and len(emotion_trend) >= 3:
                recent_avg = sum(d["avg_emotion"] for d in emotion_trend[-3:]) / 3
                if recent_avg < 5:  # 鎯呯华鍋忎綆
                    self.insight_counter += 1
                    insights.append(SmartInsight(
                        insight_id=self._gen_insight_id(),
                        category=InsightCategory.FEEDBACK_LOOP,
                        level=InsightLevel.WARNING,
                        title="宸ヤ綔鍘嬪姏-鎯呯华璐熷悜寰幆",
                        description="妫€娴嬪埌鍙兘鐨勮礋鍚戝弽棣堝惊鐜細宸ヤ綔鍘嬪姏澶?鈫?鎯呯华浣庤惤 鈫?鏁堢巼涓嬮檷 鈫?鏇村ぇ鍘嬪姏",
                        evidence=[
                            f"宸ヤ綔鐩稿叧璇濋鍑虹幇 {topic_dist.get('work', 0)} 娆?,
                            f"杩戞湡骞冲潎鎯呯华: {recent_avg:.1f}/10"
                        ],
                        recommendations=[
                            "灏濊瘯鎵撶牬寰幆锛氬厛澶勭悊鎯呯华锛屽啀澶勭悊宸ヤ綔",
                            "璁惧畾宸ヤ綔杈圭晫锛岄伩鍏嶈繃搴︽姇鍏?,
                            "姣忓ぉ鐣欏嚭鏀炬澗鏃堕棿",
                            "灏嗗ぇ浠诲姟鍒嗚В涓哄皬姝ラ"
                        ],
                        confidence=0.7,
                        impact_score=80,
                        related_metrics=["work", "emotion_score"],
                        visualization_data={
                            "type": "loop_diagram",
                            "nodes": ["宸ヤ綔鍘嬪姏", "鎯呯华浣庤惤", "鏁堢巼涓嬮檷", "鏇村ぇ鍘嬪姏"],
                            "loop_type": "negative",
                            "break_points": ["鎯呯华浣庤惤"]
                        }
                    ))
        
        return insights
    
    def _detect_behavior_patterns(self) -> List[SmartInsight]:
        """妫€娴嬭涓烘ā寮?""
        insights = []
        
        # 鑾峰彇鎰忓浘鍒嗗竷
        intent_insights = [
            i for i in self.conversation_analyzer.insights
            if i.data_type == DataType.INTENT
        ]
        
        intent_counts = defaultdict(int)
        for insight in intent_insights:
            intent_type = insight.metadata.get("intent_type", "unknown")
            intent_counts[intent_type] += 1
        
        # 妫€娴嬮绻佸姹傚缓璁殑妯″紡
        if intent_counts.get("seeking_advice", 0) > 5:
            self.insight_counter += 1
            insights.append(SmartInsight(
                insight_id=self._gen_insight_id(),
                category=InsightCategory.PATTERN,
                level=InsightLevel.INFO,
                title="鍐崇瓥鏀寔闇€姹傛ā寮?,
                description="浣犳渶杩戦绻佸姹傚缓璁紝杩欏彲鑳借〃绀轰綘姝ｉ潰涓翠竴浜涢渶瑕佸喅绛栫殑浜嬫儏",
                evidence=[
                    f"瀵绘眰寤鸿鐨勫璇濆嚭鐜?{intent_counts.get('seeking_advice', 0)} 娆?
                ],
                recommendations=[
                    "灏濊瘯浣跨敤鍐崇瓥鍓湰鍔熻兘杩涜娣卞害鍒嗘瀽",
                    "鍒楀嚭鍐崇瓥鐨勫埄寮婃竻鍗?,
                    "缁欒嚜宸辫瀹氬喅绛栨埅姝㈡椂闂?
                ],
                confidence=0.7,
                impact_score=50,
                related_metrics=["intent_seeking_advice"],
                visualization_data={
                    "type": "intent_distribution",
                    "data": dict(intent_counts)
                }
            ))
        
        # 妫€娴嬮绻佹姳鎬ㄧ殑妯″紡
        if intent_counts.get("complaining", 0) > 3:
            self.insight_counter += 1
            insights.append(SmartInsight(
                insight_id=self._gen_insight_id(),
                category=InsightCategory.PATTERN,
                level=InsightLevel.SUGGESTION,
                title="璐熼潰琛ㄨ揪澧炲",
                description="鏈€杩戜綘鐨勫璇濅腑璐熼潰琛ㄨ揪澧炲锛岃繖鍙兘鍙嶆槧浜嗕竴浜涙綔鍦ㄧ殑涓嶆弧鎴栧帇鍔?,
                evidence=[
                    f"鎶辨€ㄧ被琛ㄨ揪鍑虹幇 {intent_counts.get('complaining', 0)} 娆?
                ],
                recommendations=[
                    "灏濊瘯灏嗘姳鎬ㄨ浆鍖栦负鍏蜂綋鐨勯棶棰樻弿杩?,
                    "鎬濊€冨摢浜涙槸鍙互鏀瑰彉鐨勶紝鍝簺闇€瑕佹帴鍙?,
                    "涓庢湅鍙嬪€捐瘔鎴栧啓鏃ヨ閲婃斁鎯呯华"
                ],
                confidence=0.65,
                impact_score=55,
                related_metrics=["intent_complaining"]
            ))
        
        return insights
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """鑾峰彇浠〃鐩樻暟鎹?""
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
        """鎸夌骇鍒幏鍙栨礊瀵?""
        return [i for i in self.insights if i.level == level]
    
    def get_insights_by_category(self, category: InsightCategory) -> List[SmartInsight]:
        """鎸夊垎绫昏幏鍙栨礊瀵?""
        return [i for i in self.insights if i.category == category]


# 鍏ㄥ眬瀹炰緥缂撳瓨
_engines: Dict[str, SmartInsightEngine] = {}

def get_smart_insight_engine(user_id: str) -> SmartInsightEngine:
    """鑾峰彇鏅鸿兘娲炲療寮曟搸瀹炰緥"""
    if user_id not in _engines:
        _engines[user_id] = SmartInsightEngine(user_id)
    return _engines[user_id]
