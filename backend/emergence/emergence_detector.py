"""
涌现检测系统
检测系统中的新兴模式、非线性效应和涌现现象
"""

from typing import Dict, List, Any, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import json
import math
from collections import defaultdict


class EmergenceType(Enum):
    """涌现类型"""
    PATTERN = "pattern"  # 新兴模式
    NONLINEAR = "nonlinear"  # 非线性效应
    SYNERGY = "synergy"  # 协同效应
    FEEDBACK_LOOP = "feedback_loop"  # 反馈循环
    THRESHOLD = "threshold"  # 阈值效应
    BIFURCATION = "bifurcation"  # 分岔现象


class EmergenceEvent:
    """涌现事件"""
    
    def __init__(self, event_id: str, emergence_type: EmergenceType,
                 description: str, involved_metrics: List[str],
                 strength: float, confidence: float):
        """
        初始化涌现事件
        
        Args:
            event_id: 事件ID
            emergence_type: 涌现类型
            description: 描述
            involved_metrics: 涉及的指标
            strength: 强度
            confidence: 置信度
        """
        self.event_id = event_id
        self.emergence_type = emergence_type
        self.description = description
        self.involved_metrics = involved_metrics
        self.strength = strength
        self.confidence = confidence
        self.detected_at = datetime.now()
        self.impact_score = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "emergence_type": self.emergence_type.value,
            "description": self.description,
            "involved_metrics": self.involved_metrics,
            "strength": self.strength,
            "confidence": self.confidence,
            "impact_score": self.impact_score,
            "detected_at": self.detected_at.isoformat()
        }


class EmergenceDetector:
    """涌现检测器"""
    
    def __init__(self, user_id: str, window_size: int = 30):
        """
        初始化涌现检测器
        
        Args:
            user_id: 用户ID
            window_size: 时间窗口大小（天数）
        """
        self.user_id = user_id
        self.window_size = window_size
        
        # 数据历史
        self.data_history: List[Dict[str, Any]] = []
        
        # 检测到的涌现事件
        self.emergence_events: Dict[str, EmergenceEvent] = {}
        self.event_history: List[EmergenceEvent] = []
        
        # 检测统计
        self.detection_stats = {
            "total_events": 0,
            "pattern_events": 0,
            "nonlinear_events": 0,
            "synergy_events": 0,
            "feedback_loop_events": 0,
            "threshold_events": 0,
            "bifurcation_events": 0
        }
    
    def add_data_point(self, data: Dict[str, float], timestamp: datetime = None):
        """
        添加数据点
        
        Args:
            data: 数据字典
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        data_point = {
            "data": data,
            "timestamp": timestamp
        }
        self.data_history.append(data_point)
        
        # 保持窗口大小
        cutoff_time = datetime.now() - timedelta(days=self.window_size)
        self.data_history = [dp for dp in self.data_history if dp["timestamp"] > cutoff_time]
    
    def detect_patterns(self) -> List[EmergenceEvent]:
        """
        检测新兴模式
        
        Returns:
            检测到的模式事件列表
        """
        events = []
        
        if len(self.data_history) < 3:
            return events
        
        # 提取所有指标
        all_metrics = set()
        for dp in self.data_history:
            all_metrics.update(dp["data"].keys())
        
        # 检测相关性模式
        for metric1 in all_metrics:
            for metric2 in all_metrics:
                if metric1 < metric2:  # 避免重复
                    correlation = self._calculate_correlation(metric1, metric2)
                    
                    if abs(correlation) > 0.7:  # 强相关
                        event_id = f"pat_{metric1}_{metric2}_{datetime.now().timestamp()}"
                        event = EmergenceEvent(
                            event_id=event_id,
                            emergence_type=EmergenceType.PATTERN,
                            description=f"{metric1} 和 {metric2} 显示强相关性 (r={correlation:.2f})",
                            involved_metrics=[metric1, metric2],
                            strength=abs(correlation),
                            confidence=0.8
                        )
                        events.append(event)
        
        return events
    
    def detect_nonlinear_effects(self) -> List[EmergenceEvent]:
        """
        检测非线性效应
        
        Returns:
            检测到的非线性效应事件列表
        """
        events = []
        
        if len(self.data_history) < 5:
            return events
        
        # 提取所有指标
        all_metrics = set()
        for dp in self.data_history:
            all_metrics.update(dp["data"].keys())
        
        # 检测非线性关系
        for metric in all_metrics:
            values = [dp["data"].get(metric, 0) for dp in self.data_history]
            
            # 计算二阶导数（加速度）
            if len(values) >= 3:
                accelerations = []
                for i in range(1, len(values) - 1):
                    acceleration = (values[i+1] - values[i]) - (values[i] - values[i-1])
                    accelerations.append(acceleration)
                
                # 如果加速度变化大，表示非线性
                if accelerations:
                    acceleration_variance = sum(a**2 for a in accelerations) / len(accelerations)
                    
                    if acceleration_variance > 1.0:  # 阈值
                        event_id = f"nl_{metric}_{datetime.now().timestamp()}"
                        event = EmergenceEvent(
                            event_id=event_id,
                            emergence_type=EmergenceType.NONLINEAR,
                            description=f"{metric} 显示非线性变化模式",
                            involved_metrics=[metric],
                            strength=min(math.sqrt(acceleration_variance), 1.0),
                            confidence=0.7
                        )
                        events.append(event)
        
        return events
    
    def detect_synergy_effects(self) -> List[EmergenceEvent]:
        """
        检测协同效应
        
        Returns:
            检测到的协同效应事件列表
        """
        events = []
        
        if len(self.data_history) < 3:
            return events
        
        # 预定义的协同效应规则
        synergy_rules = [
            {
                "metrics": ["exercise_minutes", "sleep_hours"],
                "description": "运动和睡眠的协同效应",
                "expected_effect": "health_score"
            },
            {
                "metrics": ["meditation", "stress_level"],
                "description": "冥想和压力管理的协同效应",
                "expected_effect": "mood"
            },
            {
                "metrics": ["social_hours", "mood"],
                "description": "社交和心情的协同效应",
                "expected_effect": "happiness"
            },
            {
                "metrics": ["focus_time", "task_completion_rate"],
                "description": "专注时间和任务完成的协同效应",
                "expected_effect": "efficiency_score"
            }
        ]
        
        for rule in synergy_rules:
            metrics = rule["metrics"]
            expected_effect = rule["expected_effect"]
            
            # 检查这些指标是否都存在
            if all(any(metric in dp["data"] for dp in self.data_history) for metric in metrics):
                # 计算协同效应强度
                synergy_strength = self._calculate_synergy_strength(metrics, expected_effect)
                
                if synergy_strength > 0.6:
                    event_id = f"syn_{datetime.now().timestamp()}"
                    event = EmergenceEvent(
                        event_id=event_id,
                        emergence_type=EmergenceType.SYNERGY,
                        description=rule["description"],
                        involved_metrics=metrics + [expected_effect],
                        strength=synergy_strength,
                        confidence=0.75
                    )
                    events.append(event)
        
        return events
    
    def detect_feedback_loops(self) -> List[EmergenceEvent]:
        """
        检测反馈循环
        
        Returns:
            检测到的反馈循环事件列表
        """
        events = []
        
        if len(self.data_history) < 5:
            return events
        
        # 预定义的反馈循环
        feedback_loops = [
            {
                "name": "压力-睡眠循环",
                "metrics": ["stress_level", "sleep_hours"],
                "description": "高压力导致睡眠不足，睡眠不足又增加压力"
            },
            {
                "name": "运动-能量循环",
                "metrics": ["exercise_minutes", "energy_level"],
                "description": "运动增加能量，能量增加导致更多运动"
            },
            {
                "name": "社交-心情循环",
                "metrics": ["social_hours", "mood"],
                "description": "社交改善心情，好心情促进更多社交"
            }
        ]
        
        for loop in feedback_loops:
            metrics = loop["metrics"]
            
            # 检查是否存在反馈循环
            if self._detect_feedback_loop_pattern(metrics):
                event_id = f"fb_{datetime.now().timestamp()}"
                event = EmergenceEvent(
                    event_id=event_id,
                    emergence_type=EmergenceType.FEEDBACK_LOOP,
                    description=loop["description"],
                    involved_metrics=metrics,
                    strength=0.7,
                    confidence=0.8
                )
                events.append(event)
        
        return events
    
    def detect_threshold_effects(self) -> List[EmergenceEvent]:
        """
        检测阈值效应
        
        Returns:
            检测到的阈值效应事件列表
        """
        events = []
        
        if len(self.data_history) < 3:
            return events
        
        # 预定义的阈值
        thresholds = {
            "sleep_hours": {"low": 6, "high": 9},
            "stress_level": {"low": 3, "high": 7},
            "exercise_minutes": {"low": 30, "high": 120},
            "mood": {"low": 4, "high": 8},
            "health_score": {"low": 50, "high": 90}
        }
        
        for metric, threshold_values in thresholds.items():
            values = [dp["data"].get(metric, 0) for dp in self.data_history[-5:]]
            
            if values:
                # 检查是否跨越阈值
                for i in range(len(values) - 1):
                    if values[i] <= threshold_values["low"] < values[i+1]:
                        event_id = f"th_{metric}_low_{datetime.now().timestamp()}"
                        event = EmergenceEvent(
                            event_id=event_id,
                            emergence_type=EmergenceType.THRESHOLD,
                            description=f"{metric} 超过低阈值 ({threshold_values['low']})",
                            involved_metrics=[metric],
                            strength=0.8,
                            confidence=0.9
                        )
                        events.append(event)
                    
                    elif values[i] >= threshold_values["high"] > values[i+1]:
                        event_id = f"th_{metric}_high_{datetime.now().timestamp()}"
                        event = EmergenceEvent(
                            event_id=event_id,
                            emergence_type=EmergenceType.THRESHOLD,
                            description=f"{metric} 低于高阈值 ({threshold_values['high']})",
                            involved_metrics=[metric],
                            strength=0.8,
                            confidence=0.9
                        )
                        events.append(event)
        
        return events
    
    def detect_bifurcation(self) -> List[EmergenceEvent]:
        """
        检测分岔现象
        
        Returns:
            检测到的分岔事件列表
        """
        events = []
        
        if len(self.data_history) < 10:
            return events
        
        # 提取所有指标
        all_metrics = set()
        for dp in self.data_history:
            all_metrics.update(dp["data"].keys())
        
        # 检测分岔
        for metric in all_metrics:
            values = [dp["data"].get(metric, 0) for dp in self.data_history]
            
            # 计算方差变化
            if len(values) >= 10:
                first_half_var = sum((v - sum(values[:5])/5)**2 for v in values[:5]) / 5
                second_half_var = sum((v - sum(values[-5:])/5)**2 for v in values[-5:]) / 5
                
                # 如果方差显著增加，可能是分岔
                if second_half_var > first_half_var * 2:
                    event_id = f"bf_{metric}_{datetime.now().timestamp()}"
                    event = EmergenceEvent(
                        event_id=event_id,
                        emergence_type=EmergenceType.BIFURCATION,
                        description=f"{metric} 显示分岔现象，行为变得更加多样化",
                        involved_metrics=[metric],
                        strength=min(second_half_var / first_half_var, 1.0),
                        confidence=0.7
                    )
                    events.append(event)
        
        return events
    
    def detect_all_emergences(self) -> List[EmergenceEvent]:
        """
        检测所有涌现现象
        
        Returns:
            检测到的所有涌现事件列表
        """
        all_events = []
        
        # 运行所有检测器
        all_events.extend(self.detect_patterns())
        all_events.extend(self.detect_nonlinear_effects())
        all_events.extend(self.detect_synergy_effects())
        all_events.extend(self.detect_feedback_loops())
        all_events.extend(self.detect_threshold_effects())
        all_events.extend(self.detect_bifurcation())
        
        # 记录事件
        for event in all_events:
            self.emergence_events[event.event_id] = event
            self.event_history.append(event)
            
            # 更新统计
            self.detection_stats["total_events"] += 1
            event_type = event.emergence_type.value
            if event_type in self.detection_stats:
                self.detection_stats[f"{event_type}_events"] += 1
        
        return all_events
    
    def _calculate_correlation(self, metric1: str, metric2: str) -> float:
        """
        计算两个指标的相关系数
        
        Args:
            metric1: 指标1
            metric2: 指标2
        
        Returns:
            相关系数
        """
        values1 = [dp["data"].get(metric1, 0) for dp in self.data_history]
        values2 = [dp["data"].get(metric2, 0) for dp in self.data_history]
        
        if len(values1) < 2 or len(values2) < 2:
            return 0.0
        
        mean1 = sum(values1) / len(values1)
        mean2 = sum(values2) / len(values2)
        
        numerator = sum((values1[i] - mean1) * (values2[i] - mean2) for i in range(len(values1)))
        denominator = math.sqrt(
            sum((v - mean1)**2 for v in values1) * sum((v - mean2)**2 for v in values2)
        )
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_synergy_strength(self, metrics: List[str], expected_effect: str) -> float:
        """
        计算协同效应强度
        
        Args:
            metrics: 指标列表
            expected_effect: 预期效果指标
        
        Returns:
            协同效应强度
        """
        # 简化计算：计算指标与预期效果的平均相关性
        correlations = []
        for metric in metrics:
            corr = self._calculate_correlation(metric, expected_effect)
            correlations.append(abs(corr))
        
        return sum(correlations) / len(correlations) if correlations else 0.0
    
    def _detect_feedback_loop_pattern(self, metrics: List[str]) -> bool:
        """
        检测反馈循环模式
        
        Args:
            metrics: 指标列表
        
        Returns:
            是否存在反馈循环
        """
        if len(metrics) != 2:
            return False
        
        # 检查两个指标之间是否存在相互影响
        corr1 = self._calculate_correlation(metrics[0], metrics[1])
        corr2 = self._calculate_correlation(metrics[1], metrics[0])
        
        # 如果两个方向都有强相关，可能存在反馈循环
        return abs(corr1) > 0.6 and abs(corr2) > 0.6
    
    def get_emergence_statistics(self) -> Dict[str, Any]:
        """
        获取涌现统计信息
        
        Returns:
            统计信息
        """
        return {
            "total_events": self.detection_stats["total_events"],
            "pattern_events": self.detection_stats["pattern_events"],
            "nonlinear_events": self.detection_stats["nonlinear_events"],
            "synergy_events": self.detection_stats["synergy_events"],
            "feedback_loop_events": self.detection_stats["feedback_loop_events"],
            "threshold_events": self.detection_stats["threshold_events"],
            "bifurcation_events": self.detection_stats["bifurcation_events"]
        }
    
    def get_recent_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近的涌现事件
        
        Args:
            limit: 限制数量
        
        Returns:
            事件列表
        """
        return [e.to_dict() for e in self.event_history[-limit:]]
    
    def export_emergence_data(self) -> Dict[str, Any]:
        """
        导出涌现数据
        
        Returns:
            涌现数据
        """
        return {
            "user_id": self.user_id,
            "events": [e.to_dict() for e in self.event_history],
            "statistics": self.get_emergence_statistics(),
            "exported_at": datetime.now().isoformat()
        }


def get_emergence_detector(user_id: str) -> EmergenceDetector:
    """获取涌现检测器实例"""
    return EmergenceDetector(user_id)

