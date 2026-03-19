"""
涌现检测系统 - LifeSwarm的核心创新
检测跨领域的级联效应、反馈环、临界点和协同效应
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict


class PatternType(Enum):
    """涌现模式类型"""
    CASCADE = "cascade"  # 级联效应：A→B→C
    FEEDBACK_LOOP = "feedback_loop"  # 反馈环：循环因果
    TIPPING_POINT = "tipping_point"  # 临界点：突变行为
    SYNERGY = "synergy"  # 协同效应：多因素叠加


@dataclass
class EmergentPattern:
    """涌现模式"""
    pattern_id: str
    pattern_type: PatternType
    domains: List[str]  # 涉及的领域
    description: str
    confidence: float  # 0-1
    impact_score: float  # 0-1，影响程度
    evidence: Dict[str, Any]  # 证据
    timestamp: datetime
    affected_metrics: List[str]  # 受影响的指标
    recommendations: List[str]  # 建议


class CascadeDetector:
    """级联检测器 - 检测A→B→C的链式反应"""
    
    def __init__(self):
        self.causal_graph = defaultdict(list)  # 因果关系图
        self.time_windows = {
            'health_to_time': 3600,  # 健康变化到时间管理的时间窗口（秒）
            'time_to_emotion': 3600,  # 时间压力到情绪的时间窗口
            'emotion_to_social': 7200,  # 情绪到社交的时间窗口
        }
    
    def detect_cascades(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> List[EmergentPattern]:
        """检测级联效应"""
        cascades = []
        
        if len(history) < 3:
            return cascades
        
        # 检测健康→时间→情绪的级联
        cascade = self._detect_health_time_emotion_cascade(user_data, history)
        if cascade:
            cascades.append(cascade)
        
        # 检测时间→情绪→社交的级联
        cascade = self._detect_time_emotion_social_cascade(user_data, history)
        if cascade:
            cascades.append(cascade)
        
        # 检测睡眠→健康→工作效率的级联
        cascade = self._detect_sleep_health_work_cascade(user_data, history)
        if cascade:
            cascades.append(cascade)
        
        return cascades
    
    def _detect_health_time_emotion_cascade(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测健康→时间→情绪的级联"""
        if len(history) < 3:
            return None
        
        # 获取最近3条记录
        recent = history[-3:]
        
        # 检查健康指标是否下降
        health_declining = False
        if recent[0].get('health_score', 100) > recent[1].get('health_score', 100):
            health_declining = True
        
        # 检查时间压力是否增加
        time_pressure_increasing = False
        if recent[1].get('time_pressure', 0) > recent[0].get('time_pressure', 0):
            time_pressure_increasing = True
        
        # 检查情绪是否下降
        mood_declining = False
        if recent[2].get('mood', 5) < recent[1].get('mood', 5):
            mood_declining = True
        
        # 如果三个条件都满足，则检测到级联
        if health_declining and time_pressure_increasing and mood_declining:
            return EmergentPattern(
                pattern_id=f"cascade_health_time_emotion_{datetime.now().timestamp()}",
                pattern_type=PatternType.CASCADE,
                domains=["health", "time", "emotion"],
                description="检测到级联效应：健康下降 → 时间压力增加 → 情绪恶化",
                confidence=0.8,
                impact_score=0.7,
                evidence={
                    "health_decline": recent[0].get('health_score', 100) - recent[1].get('health_score', 100),
                    "time_pressure_increase": recent[1].get('time_pressure', 0) - recent[0].get('time_pressure', 0),
                    "mood_decline": recent[1].get('mood', 5) - recent[2].get('mood', 5)
                },
                timestamp=datetime.now(),
                affected_metrics=["health_score", "time_pressure", "mood"],
                recommendations=[
                    "优先改善睡眠质量，恢复健康状态",
                    "减少工作压力，合理安排时间",
                    "进行放松活动，调节情绪"
                ]
            )
        
        return None
    
    def _detect_time_emotion_social_cascade(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测时间→情绪→社交的级联"""
        if len(history) < 3:
            return None
        
        recent = history[-3:]
        
        # 检查时间压力
        time_pressure_high = recent[0].get('time_pressure', 0) > 0.7
        
        # 检查情绪
        mood_low = recent[1].get('mood', 5) < 4
        
        # 检查社交
        social_low = recent[2].get('social_satisfaction', 5) < 4
        
        if time_pressure_high and mood_low and social_low:
            return EmergentPattern(
                pattern_id=f"cascade_time_emotion_social_{datetime.now().timestamp()}",
                pattern_type=PatternType.CASCADE,
                domains=["time", "emotion", "social"],
                description="检测到级联效应：时间压力 → 情绪低落 → 社交减少",
                confidence=0.75,
                impact_score=0.65,
                evidence={
                    "time_pressure": recent[0].get('time_pressure', 0),
                    "mood": recent[1].get('mood', 5),
                    "social_satisfaction": recent[2].get('social_satisfaction', 5)
                },
                timestamp=datetime.now(),
                affected_metrics=["time_pressure", "mood", "social_satisfaction"],
                recommendations=[
                    "主动安排社交活动，改善情绪",
                    "合理分配时间，减少压力",
                    "与朋友交流，获得情感支持"
                ]
            )
        
        return None
    
    def _detect_sleep_health_work_cascade(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测睡眠→健康→工作效率的级联"""
        if len(history) < 3:
            return None
        
        recent = history[-3:]
        
        # 检查睡眠
        sleep_poor = recent[0].get('sleep_hours', 8) < 6
        
        # 检查健康
        health_declining = recent[1].get('health_score', 100) < 70
        
        # 检查工作效率
        efficiency_low = recent[2].get('efficiency_score', 70) < 60
        
        if sleep_poor and health_declining and efficiency_low:
            return EmergentPattern(
                pattern_id=f"cascade_sleep_health_work_{datetime.now().timestamp()}",
                pattern_type=PatternType.CASCADE,
                domains=["health", "time", "learning"],
                description="检测到级联效应：睡眠不足 → 健康下降 → 工作效率低",
                confidence=0.85,
                impact_score=0.8,
                evidence={
                    "sleep_hours": recent[0].get('sleep_hours', 8),
                    "health_score": recent[1].get('health_score', 100),
                    "efficiency_score": recent[2].get('efficiency_score', 70)
                },
                timestamp=datetime.now(),
                affected_metrics=["sleep_hours", "health_score", "efficiency_score"],
                recommendations=[
                    "立即改善睡眠，每晚至少7小时",
                    "进行适度运动，增强体质",
                    "调整工作计划，循序渐进恢复效率"
                ]
            )
        
        return None


class FeedbackLoopDetector:
    """反馈环检测器 - 检测循环因果关系"""
    
    def detect_feedback_loops(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> List[EmergentPattern]:
        """检测反馈环"""
        loops = []
        
        if len(history) < 5:
            return loops
        
        # 检测压力→睡眠→压力的负反馈环
        loop = self._detect_stress_sleep_loop(user_data, history)
        if loop:
            loops.append(loop)
        
        # 检测运动→心情→运动的正反馈环
        loop = self._detect_exercise_mood_loop(user_data, history)
        if loop:
            loops.append(loop)
        
        # 检测孤独→社交→孤独的负反馈环
        loop = self._detect_loneliness_social_loop(user_data, history)
        if loop:
            loops.append(loop)
        
        return loops
    
    def _detect_stress_sleep_loop(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测压力→睡眠→压力的负反馈环"""
        recent = history[-5:]
        
        # 计算趋势
        stress_trend = [h.get('stress_level', 5) for h in recent]
        sleep_trend = [h.get('sleep_hours', 8) for h in recent]
        
        # 检查是否存在反向相关性（压力高时睡眠少，睡眠少时压力高）
        stress_increasing = stress_trend[-1] > stress_trend[0]
        sleep_decreasing = sleep_trend[-1] < sleep_trend[0]
        
        if stress_increasing and sleep_decreasing:
            # 计算相关性
            correlation = np.corrcoef(stress_trend, sleep_trend)[0, 1]
            
            if correlation < -0.5:  # 负相关
                return EmergentPattern(
                    pattern_id=f"feedback_stress_sleep_{datetime.now().timestamp()}",
                    pattern_type=PatternType.FEEDBACK_LOOP,
                    domains=["emotion", "health"],
                    description="检测到负反馈环：压力增加 → 睡眠减少 → 压力进一步增加",
                    confidence=0.8,
                    impact_score=0.75,
                    evidence={
                        "stress_trend": stress_trend,
                        "sleep_trend": sleep_trend,
                        "correlation": float(correlation)
                    },
                    timestamp=datetime.now(),
                    affected_metrics=["stress_level", "sleep_hours"],
                    recommendations=[
                        "使用放松技巧（冥想、深呼吸）降低压力",
                        "建立规律的睡眠时间表",
                        "避免睡前使用电子设备",
                        "考虑寻求专业心理咨询"
                    ]
                )
        
        return None
    
    def _detect_exercise_mood_loop(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测运动→心情→运动的正反馈环"""
        recent = history[-5:]
        
        exercise_trend = [h.get('exercise_minutes', 0) for h in recent]
        mood_trend = [h.get('mood', 5) for h in recent]
        
        # 检查是否存在正相关性
        exercise_increasing = exercise_trend[-1] > exercise_trend[0]
        mood_improving = mood_trend[-1] > mood_trend[0]
        
        if exercise_increasing and mood_improving:
            correlation = np.corrcoef(exercise_trend, mood_trend)[0, 1]
            
            if correlation > 0.5:  # 正相关
                return EmergentPattern(
                    pattern_id=f"feedback_exercise_mood_{datetime.now().timestamp()}",
                    pattern_type=PatternType.FEEDBACK_LOOP,
                    domains=["health", "emotion"],
                    description="检测到正反馈环：运动增加 → 心情改善 → 更愿意运动",
                    confidence=0.85,
                    impact_score=0.8,
                    evidence={
                        "exercise_trend": exercise_trend,
                        "mood_trend": mood_trend,
                        "correlation": float(correlation)
                    },
                    timestamp=datetime.now(),
                    affected_metrics=["exercise_minutes", "mood"],
                    recommendations=[
                        "继续保持运动习惯，享受运动带来的快乐",
                        "尝试新的运动方式，保持新鲜感",
                        "邀请朋友一起运动，增加社交互动",
                        "记录运动成就，增强成就感"
                    ]
                )
        
        return None
    
    def _detect_loneliness_social_loop(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测孤独→社交→孤独的负反馈环"""
        recent = history[-5:]
        
        loneliness_trend = [h.get('loneliness', 5) for h in recent]
        social_trend = [h.get('social_hours', 0) for h in recent]
        
        loneliness_increasing = loneliness_trend[-1] > loneliness_trend[0]
        social_decreasing = social_trend[-1] < social_trend[0]
        
        if loneliness_increasing and social_decreasing:
            correlation = np.corrcoef(loneliness_trend, social_trend)[0, 1]
            
            if correlation < -0.5:
                return EmergentPattern(
                    pattern_id=f"feedback_loneliness_social_{datetime.now().timestamp()}",
                    pattern_type=PatternType.FEEDBACK_LOOP,
                    domains=["emotion", "social"],
                    description="检测到负反馈环：孤独感增加 → 社交减少 → 孤独感进一步增加",
                    confidence=0.8,
                    impact_score=0.7,
                    evidence={
                        "loneliness_trend": loneliness_trend,
                        "social_trend": social_trend,
                        "correlation": float(correlation)
                    },
                    timestamp=datetime.now(),
                    affected_metrics=["loneliness", "social_hours"],
                    recommendations=[
                        "主动联系朋友，安排社交活动",
                        "加入兴趣小组或社区活动",
                        "参加线上社区，扩展社交圈子",
                        "考虑寻求心理咨询支持"
                    ]
                )
        
        return None


class TippingPointDetector:
    """临界点检测器 - 检测系统行为的突变"""
    
    def detect_tipping_points(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> List[EmergentPattern]:
        """检测临界点"""
        tipping_points = []
        
        if len(history) < 7:
            return tipping_points
        
        # 检测健康临界点
        tp = self._detect_health_tipping_point(user_data, history)
        if tp:
            tipping_points.append(tp)
        
        # 检测情绪临界点
        tp = self._detect_emotion_tipping_point(user_data, history)
        if tp:
            tipping_points.append(tp)
        
        # 检测工作效率临界点
        tp = self._detect_efficiency_tipping_point(user_data, history)
        if tp:
            tipping_points.append(tp)
        
        return tipping_points
    
    def _detect_health_tipping_point(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测健康临界点"""
        recent = history[-7:]
        health_scores = [h.get('health_score', 100) for h in recent]
        
        # 检查是否有突变
        changes = [health_scores[i] - health_scores[i-1] for i in range(1, len(health_scores))]
        max_change = max(abs(c) for c in changes)
        
        if max_change > 15:  # 健康分数突变超过15分
            # 找到突变点
            change_idx = changes.index(max(changes, key=abs))
            
            if health_scores[change_idx + 1] < 60:  # 健康分数低于60
                return EmergentPattern(
                    pattern_id=f"tipping_health_{datetime.now().timestamp()}",
                    pattern_type=PatternType.TIPPING_POINT,
                    domains=["health"],
                    description=f"检测到健康临界点：健康分数突然下降到{health_scores[-1]}",
                    confidence=0.85,
                    impact_score=0.9,
                    evidence={
                        "health_scores": health_scores,
                        "max_change": max_change,
                        "current_score": health_scores[-1]
                    },
                    timestamp=datetime.now(),
                    affected_metrics=["health_score"],
                    recommendations=[
                        "立即进行全面健康检查",
                        "增加睡眠时间，每晚至少8小时",
                        "进行适度运动，增强体质",
                        "改善饮食，增加营养摄入",
                        "如症状持续，请咨询医生"
                    ]
                )
        
        return None
    
    def _detect_emotion_tipping_point(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测情绪临界点"""
        recent = history[-7:]
        mood_scores = [h.get('mood', 5) for h in recent]
        
        changes = [mood_scores[i] - mood_scores[i-1] for i in range(1, len(mood_scores))]
        max_change = max(abs(c) for c in changes)
        
        if max_change > 3 and mood_scores[-1] < 3:  # 情绪突变且当前情绪很低
            return EmergentPattern(
                pattern_id=f"tipping_emotion_{datetime.now().timestamp()}",
                pattern_type=PatternType.TIPPING_POINT,
                domains=["emotion"],
                description=f"检测到情绪临界点：情绪分数突然下降到{mood_scores[-1]}/10",
                confidence=0.8,
                impact_score=0.85,
                evidence={
                    "mood_scores": mood_scores,
                    "max_change": max_change,
                    "current_mood": mood_scores[-1]
                },
                timestamp=datetime.now(),
                affected_metrics=["mood"],
                recommendations=[
                    "进行放松活动（冥想、瑜伽、散步）",
                    "与信任的人倾诉",
                    "参加喜欢的活动，转移注意力",
                    "如情绪持续低落，请寻求专业心理咨询"
                ]
            )
        
        return None
    
    def _detect_efficiency_tipping_point(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测工作效率临界点"""
        recent = history[-7:]
        efficiency_scores = [h.get('efficiency_score', 70) for h in recent]
        
        changes = [efficiency_scores[i] - efficiency_scores[i-1] for i in range(1, len(efficiency_scores))]
        max_change = max(abs(c) for c in changes)
        
        if max_change > 20 and efficiency_scores[-1] < 40:
            return EmergentPattern(
                pattern_id=f"tipping_efficiency_{datetime.now().timestamp()}",
                pattern_type=PatternType.TIPPING_POINT,
                domains=["time"],
                description=f"检测到效率临界点：工作效率突然下降到{efficiency_scores[-1]}%",
                confidence=0.8,
                impact_score=0.75,
                evidence={
                    "efficiency_scores": efficiency_scores,
                    "max_change": max_change,
                    "current_efficiency": efficiency_scores[-1]
                },
                timestamp=datetime.now(),
                affected_metrics=["efficiency_score"],
                recommendations=[
                    "检查是否过度疲劳，需要休息",
                    "简化任务列表，专注于重要任务",
                    "使用番茄工作法，提高专注力",
                    "考虑是否需要调整工作计划"
                ]
            )
        
        return None


class SynergyDetector:
    """协同效应检测器 - 检测多因素叠加效应"""
    
    def detect_synergies(self, user_data: Dict[str, Any], history: List[Dict[str, Any]]) -> List[EmergentPattern]:
        """检测协同效应"""
        synergies = []
        
        if len(history) < 3:
            return synergies
        
        # 检测健康+时间+情绪的协同
        synergy = self._detect_health_time_emotion_synergy(user_data, history)
        if synergy:
            synergies.append(synergy)
        
        # 检测运动+睡眠+心情的协同
        synergy = self._detect_exercise_sleep_mood_synergy(user_data, history)
        if synergy:
            synergies.append(synergy)
        
        return synergies
    
    def _detect_health_time_emotion_synergy(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测健康+时间+情绪的协同"""
        recent = history[-3:]
        
        # 检查三个因素是否都在良好状态
        health_good = recent[-1].get('health_score', 100) > 80
        time_good = recent[-1].get('time_pressure', 0) < 0.3
        emotion_good = recent[-1].get('mood', 5) > 7
        
        if health_good and time_good and emotion_good:
            return EmergentPattern(
                pattern_id=f"synergy_health_time_emotion_{datetime.now().timestamp()}",
                pattern_type=PatternType.SYNERGY,
                domains=["health", "time", "emotion"],
                description="检测到协同效应：健康状态好 + 时间压力小 + 情绪积极 = 生活质量优秀",
                confidence=0.85,
                impact_score=0.8,
                evidence={
                    "health_score": recent[-1].get('health_score', 100),
                    "time_pressure": recent[-1].get('time_pressure', 0),
                    "mood": recent[-1].get('mood', 5)
                },
                timestamp=datetime.now(),
                affected_metrics=["health_score", "time_pressure", "mood"],
                recommendations=[
                    "继续保持当前的生活方式",
                    "定期进行健康检查，维持健康状态",
                    "保持合理的工作-生活平衡",
                    "分享你的成功经验，帮助他人"
                ]
            )
        
        return None
    
    def _detect_exercise_sleep_mood_synergy(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[EmergentPattern]:
        """检测运动+睡眠+心情的协同"""
        recent = history[-3:]
        
        exercise_good = recent[-1].get('exercise_minutes', 0) > 30
        sleep_good = recent[-1].get('sleep_hours', 8) >= 7
        mood_good = recent[-1].get('mood', 5) > 7
        
        if exercise_good and sleep_good and mood_good:
            return EmergentPattern(
                pattern_id=f"synergy_exercise_sleep_mood_{datetime.now().timestamp()}",
                pattern_type=PatternType.SYNERGY,
                domains=["health", "emotion"],
                description="检测到协同效应：充足运动 + 充足睡眠 + 积极心态 = 最佳身心状态",
                confidence=0.9,
                impact_score=0.85,
                evidence={
                    "exercise_minutes": recent[-1].get('exercise_minutes', 0),
                    "sleep_hours": recent[-1].get('sleep_hours', 8),
                    "mood": recent[-1].get('mood', 5)
                },
                timestamp=datetime.now(),
                affected_metrics=["exercise_minutes", "sleep_hours", "mood"],
                recommendations=[
                    "保持这个健康的生活方式",
                    "考虑增加运动强度，进一步提升效果",
                    "邀请朋友加入，共同享受健康生活",
                    "记录这段时期的经验，作为参考"
                ]
            )
        
        return None


class EmergenceDetector:
    """涌现检测系统 - 整合所有检测器"""
    
    def __init__(self):
        self.cascade_detector = CascadeDetector()
        self.feedback_detector = FeedbackLoopDetector()
        self.tipping_detector = TippingPointDetector()
        self.synergy_detector = SynergyDetector()
    
    def detect_all_patterns(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> List[EmergentPattern]:
        """检测所有涌现模式"""
        patterns = []
        
        # 检测级联
        patterns.extend(self.cascade_detector.detect_cascades(user_data, history))
        
        # 检测反馈环
        patterns.extend(self.feedback_detector.detect_feedback_loops(user_data, history))
        
        # 检测临界点
        patterns.extend(self.tipping_detector.detect_tipping_points(user_data, history))
        
        # 检测协同效应
        patterns.extend(self.synergy_detector.detect_synergies(user_data, history))
        
        # 按影响程度排序
        patterns.sort(key=lambda p: p.impact_score, reverse=True)
        
        return patterns
    
    def get_pattern_summary(self, patterns: List[EmergentPattern]) -> Dict[str, Any]:
        """获取模式总结"""
        return {
            "total_patterns": len(patterns),
            "by_type": {
                "cascade": len([p for p in patterns if p.pattern_type == PatternType.CASCADE]),
                "feedback_loop": len([p for p in patterns if p.pattern_type == PatternType.FEEDBACK_LOOP]),
                "tipping_point": len([p for p in patterns if p.pattern_type == PatternType.TIPPING_POINT]),
                "synergy": len([p for p in patterns if p.pattern_type == PatternType.SYNERGY])
            },
            "high_impact": len([p for p in patterns if p.impact_score > 0.7]),
            "patterns": [
                {
                    "id": p.pattern_id,
                    "type": p.pattern_type.value,
                    "domains": p.domains,
                    "description": p.description,
                    "confidence": p.confidence,
                    "impact_score": p.impact_score,
                    "recommendations": p.recommendations
                }
                for p in patterns[:5]  # 返回前5个最重要的模式
            ]
        }


# 全局实例
_detector = None

def get_emergence_detector() -> EmergenceDetector:
    """获取全局涌现检测器实例"""
    global _detector
    if _detector is None:
        _detector = EmergenceDetector()
    return _detector

