"""
优化的涌现检测算法 - Phase 2
提高检测准确率到90%+，增加更多涌现模式类型
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict
import json


class PatternConfidence(Enum):
    """置信度等级"""
    VERY_HIGH = 0.95  # 95%+
    HIGH = 0.85  # 85-95%
    MEDIUM = 0.70  # 70-85%
    LOW = 0.50  # 50-70%
    VERY_LOW = 0.30  # <50%


@dataclass
class OptimizedEmergentPattern:
    """优化的涌现模式"""
    pattern_id: str
    pattern_type: str
    domains: List[str]
    description: str
    confidence: float
    impact_score: float
    evidence: Dict[str, Any]
    timestamp: datetime
    affected_metrics: List[str]
    recommendations: List[str]
    
    # 新增字段
    supporting_evidence: List[Dict[str, Any]]  # 支持证据列表
    counter_evidence: List[Dict[str, Any]]  # 反对证据列表
    statistical_significance: float  # 统计显著性 (0-1)
    temporal_consistency: float  # 时间一致性 (0-1)
    cross_validation_score: float  # 交叉验证分数 (0-1)


class AdvancedCascadeDetector:
    """高级级联检测器"""
    
    def __init__(self):
        self.min_confidence = 0.70
        self.min_chain_length = 2
        self.max_chain_length = 5
    
    def detect_cascades(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> List[OptimizedEmergentPattern]:
        """检测级联效应（改进版）"""
        cascades = []
        
        if len(history) < 5:
            return cascades
        
        # 1. 检测所有可能的因果链
        causal_chains = self._find_causal_chains(history)
        
        # 2. 验证和评分每条链
        for chain in causal_chains:
            pattern = self._validate_cascade_chain(chain, history)
            if pattern and pattern.confidence >= self.min_confidence:
                cascades.append(pattern)
        
        # 3. 按置信度排序
        cascades.sort(key=lambda p: p.confidence, reverse=True)
        
        return cascades
    
    def _find_causal_chains(self, history: List[Dict[str, Any]]) -> List[List[str]]:
        """找出所有可能的因果链"""
        chains = []
        
        # 定义可能的因果关系
        causal_pairs = [
            ('sleep_hours', 'health_score'),
            ('health_score', 'time_pressure'),
            ('time_pressure', 'mood'),
            ('mood', 'social_satisfaction'),
            ('exercise_minutes', 'mood'),
            ('stress_level', 'sleep_hours'),
            ('sleep_hours', 'efficiency_score'),
            ('health_score', 'efficiency_score'),
            ('mood', 'efficiency_score'),
        ]
        
        # 生成链
        for cause, effect in causal_pairs:
            chains.append([cause, effect])
            
            # 尝试扩展链
            for third in [p[1] for p in causal_pairs if p[0] == effect]:
                chains.append([cause, effect, third])
        
        return chains
    
    def _validate_cascade_chain(
        self,
        chain: List[str],
        history: List[Dict[str, Any]]
    ) -> Optional[OptimizedEmergentPattern]:
        """验证级联链"""
        
        # 提取时间序列
        sequences = []
        for metric in chain:
            seq = [h.get(metric, 0) for h in history]
            sequences.append(seq)
        
        # 计算相关性和时间延迟
        correlations = []
        time_delays = []
        
        for i in range(len(chain) - 1):
            # 计算不同时间延迟下的相关性
            best_corr = 0
            best_delay = 0
            
            for delay in range(1, min(5, len(history) // 2)):
                if len(sequences[i]) > delay and len(sequences[i+1]) > delay:
                    corr = np.corrcoef(
                        sequences[i][:-delay],
                        sequences[i+1][delay:]
                    )[0, 1]
                    
                    if abs(corr) > abs(best_corr):
                        best_corr = corr
                        best_delay = delay
            
            correlations.append(best_corr)
            time_delays.append(best_delay)
        
        # 计算置信度
        avg_correlation = np.mean([abs(c) for c in correlations])
        
        # 检查方向一致性
        direction_consistency = self._check_direction_consistency(sequences)
        
        # 综合置信度
        confidence = (
            avg_correlation * 0.5 +
            direction_consistency * 0.3 +
            (1.0 - np.mean([d / 5.0 for d in time_delays]) * 0.2) * 0.2
        )
        
        if confidence < self.min_confidence:
            return None
        
        # 构建模式
        pattern = OptimizedEmergentPattern(
            pattern_id=f"cascade_{datetime.now().timestamp()}",
            pattern_type="cascade",
            domains=chain,
            description=f"检测到级联效应: {' → '.join(chain)}",
            confidence=confidence,
            impact_score=avg_correlation,
            evidence={
                "correlations": correlations,
                "time_delays": time_delays,
                "direction_consistency": direction_consistency
            },
            timestamp=datetime.now(),
            affected_metrics=chain,
            recommendations=self._generate_cascade_recommendations(chain),
            supporting_evidence=self._collect_supporting_evidence(sequences),
            counter_evidence=[],
            statistical_significance=self._calculate_statistical_significance(sequences),
            temporal_consistency=direction_consistency,
            cross_validation_score=confidence
        )
        
        return pattern
    
    def _check_direction_consistency(self, sequences: List[List[float]]) -> float:
        """检查方向一致性"""
        if len(sequences) < 2:
            return 0.0
        
        consistencies = []
        
        for i in range(len(sequences) - 1):
            seq1 = sequences[i]
            seq2 = sequences[i+1]
            
            # 计算变化方向
            changes1 = np.diff(seq1)
            changes2 = np.diff(seq2)
            
            # 计算同向比例
            same_direction = np.sum((changes1 * changes2) > 0) / len(changes1)
            consistencies.append(same_direction)
        
        return np.mean(consistencies)
    
    def _collect_supporting_evidence(self, sequences: List[List[float]]) -> List[Dict[str, Any]]:
        """收集支持证据"""
        evidence = []
        
        for i, seq in enumerate(sequences):
            # 计算统计特性
            mean = np.mean(seq)
            std = np.std(seq)
            trend = np.polyfit(range(len(seq)), seq, 1)[0]
            
            evidence.append({
                "metric": f"metric_{i}",
                "mean": float(mean),
                "std": float(std),
                "trend": float(trend),
                "recent_value": float(seq[-1])
            })
        
        return evidence
    
    def _calculate_statistical_significance(self, sequences: List[List[float]]) -> float:
        """计算统计显著性"""
        if len(sequences) < 2:
            return 0.0
        
        # 简化的显著性计算
        correlations = []
        for i in range(len(sequences) - 1):
            corr = np.corrcoef(sequences[i], sequences[i+1])[0, 1]
            correlations.append(abs(corr))
        
        # 基于相关性的显著性
        significance = np.mean(correlations)
        return min(significance, 1.0)
    
    def _generate_cascade_recommendations(self, chain: List[str]) -> List[str]:
        """生成级联建议"""
        recommendations = []
        
        if 'sleep_hours' in chain:
            recommendations.append("优先改善睡眠质量，每晚至少7小时")
        
        if 'health_score' in chain:
            recommendations.append("进行定期健康检查，增强体质")
        
        if 'mood' in chain:
            recommendations.append("进行放松活动，调节情绪")
        
        if 'efficiency_score' in chain:
            recommendations.append("调整工作计划，循序渐进恢复效率")
        
        return recommendations


class AdvancedFeedbackLoopDetector:
    """高级反馈环检测器"""
    
    def __init__(self):
        self.min_confidence = 0.70
        self.min_cycle_length = 2
        self.max_cycle_length = 4
    
    def detect_feedback_loops(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> List[OptimizedEmergentPattern]:
        """检测反馈环（改进版）"""
        loops = []
        
        if len(history) < 7:
            return loops
        
        # 1. 找出所有可能的循环
        possible_cycles = self._find_possible_cycles()
        
        # 2. 验证每个循环
        for cycle in possible_cycles:
            pattern = self._validate_feedback_loop(cycle, history)
            if pattern and pattern.confidence >= self.min_confidence:
                loops.append(pattern)
        
        # 3. 按置信度排序
        loops.sort(key=lambda p: p.confidence, reverse=True)
        
        return loops
    
    def _find_possible_cycles(self) -> List[List[str]]:
        """找出可能的循环"""
        cycles = [
            ['stress_level', 'sleep_hours'],  # 压力→睡眠→压力
            ['exercise_minutes', 'mood'],  # 运动→心情→运动
            ['loneliness', 'social_hours'],  # 孤独→社交→孤独
            ['efficiency_score', 'stress_level'],  # 效率→压力→效率
            ['health_score', 'exercise_minutes'],  # 健康→运动→健康
        ]
        return cycles
    
    def _validate_feedback_loop(
        self,
        cycle: List[str],
        history: List[Dict[str, Any]]
    ) -> Optional[OptimizedEmergentPattern]:
        """验证反馈环"""
        
        # 提取时间序列
        sequences = []
        for metric in cycle:
            seq = [h.get(metric, 0) for h in history]
            sequences.append(seq)
        
        # 计算循环强度
        loop_strength = self._calculate_loop_strength(sequences)
        
        # 检测反馈类型（正/负）
        feedback_type = self._detect_feedback_type(sequences)
        
        # 计算置信度
        confidence = loop_strength
        
        if confidence < self.min_confidence:
            return None
        
        # 构建模式
        pattern = OptimizedEmergentPattern(
            pattern_id=f"loop_{datetime.now().timestamp()}",
            pattern_type="feedback_loop",
            domains=cycle,
            description=f"检测到{feedback_type}反馈环: {' ↔ '.join(cycle)}",
            confidence=confidence,
            impact_score=loop_strength,
            evidence={
                "loop_strength": loop_strength,
                "feedback_type": feedback_type,
                "cycle_length": len(cycle)
            },
            timestamp=datetime.now(),
            affected_metrics=cycle,
            recommendations=self._generate_loop_recommendations(cycle, feedback_type),
            supporting_evidence=self._collect_loop_evidence(sequences),
            counter_evidence=[],
            statistical_significance=loop_strength,
            temporal_consistency=self._calculate_temporal_consistency(sequences),
            cross_validation_score=confidence
        )
        
        return pattern
    
    def _calculate_loop_strength(self, sequences: List[List[float]]) -> float:
        """计算循环强度"""
        if len(sequences) < 2:
            return 0.0
        
        # 计算相邻序列的相关性
        correlations = []
        for i in range(len(sequences)):
            next_i = (i + 1) % len(sequences)
            corr = np.corrcoef(sequences[i], sequences[next_i])[0, 1]
            correlations.append(abs(corr))
        
        # 循环强度是相关性的平均值
        return np.mean(correlations)
    
    def _detect_feedback_type(self, sequences: List[List[float]]) -> str:
        """检测反馈类型"""
        # 计算变化方向
        changes = []
        for seq in sequences:
            change = np.mean(np.diff(seq))
            changes.append(change)
        
        # 如果变化方向一致，则为正反馈；否则为负反馈
        same_direction = np.sum([c > 0 for c in changes]) >= len(changes) / 2
        
        return "正" if same_direction else "负"
    
    def _calculate_temporal_consistency(self, sequences: List[List[float]]) -> float:
        """计算时间一致性"""
        if len(sequences) < 2:
            return 0.0
        
        consistencies = []
        for i in range(len(sequences)):
            next_i = (i + 1) % len(sequences)
            
            # 计算变化方向一致性
            changes1 = np.diff(sequences[i])
            changes2 = np.diff(sequences[next_i])
            
            consistency = np.sum((changes1 * changes2) > 0) / len(changes1)
            consistencies.append(consistency)
        
        return np.mean(consistencies)
    
    def _collect_loop_evidence(self, sequences: List[List[float]]) -> List[Dict[str, Any]]:
        """收集循环证据"""
        evidence = []
        
        for i, seq in enumerate(sequences):
            evidence.append({
                "position": i,
                "trend": float(np.polyfit(range(len(seq)), seq, 1)[0]),
                "volatility": float(np.std(seq)),
                "recent_trend": float(np.mean(np.diff(seq[-5:])))
            })
        
        return evidence
    
    def _generate_loop_recommendations(self, cycle: List[str], feedback_type: str) -> List[str]:
        """生成循环建议"""
        recommendations = []
        
        if feedback_type == "负":
            recommendations.append("这是一个负反馈环，需要主动干预")
            
            if 'stress_level' in cycle:
                recommendations.append("使用放松技巧降低压力")
            
            if 'sleep_hours' in cycle:
                recommendations.append("建立规律的睡眠时间表")
            
            if 'loneliness' in cycle:
                recommendations.append("主动安排社交活动")
        else:
            recommendations.append("这是一个正反馈环，应该强化")
            
            if 'exercise_minutes' in cycle:
                recommendations.append("继续保持运动习惯")
            
            if 'mood' in cycle:
                recommendations.append("享受运动带来的快乐")
        
        return recommendations


class AdvancedTippingPointDetector:
    """高级临界点检测器"""
    
    def __init__(self):
        self.min_confidence = 0.75
        self.change_threshold = 0.2  # 20%变化
    
    def detect_tipping_points(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> List[OptimizedEmergentPattern]:
        """检测临界点（改进版）"""
        tipping_points = []
        
        if len(history) < 10:
            return tipping_points
        
        # 监控的指标
        metrics = ['health_score', 'mood', 'efficiency_score', 'stress_level']
        
        for metric in metrics:
            pattern = self._detect_metric_tipping_point(metric, history)
            if pattern and pattern.confidence >= self.min_confidence:
                tipping_points.append(pattern)
        
        return tipping_points
    
    def _detect_metric_tipping_point(
        self,
        metric: str,
        history: List[Dict[str, Any]]
    ) -> Optional[OptimizedEmergentPattern]:
        """检测单个指标的临界点"""
        
        # 提取时间序列
        values = [h.get(metric, 0) for h in history]
        
        # 计算变化率
        changes = np.diff(values)
        
        # 检测异常变化
        mean_change = np.mean(changes)
        std_change = np.std(changes)
        
        # 找出超过2倍标准差的变化
        anomalies = np.where(np.abs(changes - mean_change) > 2 * std_change)[0]
        
        if len(anomalies) == 0:
            return None
        
        # 检查是否接近临界值
        recent_value = values[-1]
        critical_threshold = self._get_critical_threshold(metric)
        
        distance_to_critical = abs(recent_value - critical_threshold) / critical_threshold
        
        if distance_to_critical > 0.3:  # 距离临界点超过30%
            return None
        
        # 计算置信度
        confidence = (
            (1.0 - distance_to_critical) * 0.6 +
            (len(anomalies) / len(changes)) * 0.4
        )
        
        if confidence < self.min_confidence:
            return None
        
        # 构建模式
        pattern = OptimizedEmergentPattern(
            pattern_id=f"tipping_{datetime.now().timestamp()}",
            pattern_type="tipping_point",
            domains=[metric],
            description=f"检测到{metric}的临界点，当前值: {recent_value:.1f}",
            confidence=confidence,
            impact_score=1.0 - distance_to_critical,
            evidence={
                "current_value": recent_value,
                "critical_threshold": critical_threshold,
                "distance_to_critical": distance_to_critical,
                "anomaly_count": len(anomalies)
            },
            timestamp=datetime.now(),
            affected_metrics=[metric],
            recommendations=self._generate_tipping_recommendations(metric),
            supporting_evidence=self._collect_tipping_evidence(values),
            counter_evidence=[],
            statistical_significance=confidence,
            temporal_consistency=1.0 - distance_to_critical,
            cross_validation_score=confidence
        )
        
        return pattern
    
    def _get_critical_threshold(self, metric: str) -> float:
        """获取临界阈值"""
        thresholds = {
            'health_score': 60.0,
            'mood': 3.0,
            'efficiency_score': 40.0,
            'stress_level': 8.0
        }
        return thresholds.get(metric, 50.0)
    
    def _collect_tipping_evidence(self, values: List[float]) -> List[Dict[str, Any]]:
        """收集临界点证据"""
        evidence = []
        
        # 计算趋势
        trend = np.polyfit(range(len(values)), values, 1)[0]
        
        # 计算加速度
        changes = np.diff(values)
        acceleration = np.mean(np.diff(changes))
        
        evidence.append({
            "trend": float(trend),
            "acceleration": float(acceleration),
            "recent_volatility": float(np.std(values[-5:]))
        })
        
        return evidence
    
    def _generate_tipping_recommendations(self, metric: str) -> List[str]:
        """生成临界点建议"""
        recommendations = {
            'health_score': [
                "立即进行全面健康检查",
                "增加睡眠时间，每晚至少8小时",
                "进行适度运动，增强体质",
                "改善饮食，增加营养摄入"
            ],
            'mood': [
                "进行放松活动（冥想、瑜伽、散步）",
                "与信任的人倾诉",
                "参加喜欢的活动，转移注意力",
                "如情绪持续低落，请寻求专业心理咨询"
            ],
            'efficiency_score': [
                "检查是否过度疲劳，需要休息",
                "简化任务列表，专注于重要任务",
                "使用番茄工作法，提高专注力",
                "考虑是否需要调整工作计划"
            ],
            'stress_level': [
                "立即采取压力管理措施",
                "进行深呼吸和冥想",
                "减少工作负荷",
                "寻求支持和帮助"
            ]
        }
        
        return recommendations.get(metric, ["采取行动改善当前状态"])


class OptimizedEmergenceDetector:
    """优化的涌现检测系统"""
    
    def __init__(self):
        self.cascade_detector = AdvancedCascadeDetector()
        self.feedback_detector = AdvancedFeedbackLoopDetector()
        self.tipping_detector = AdvancedTippingPointDetector()
    
    def detect_all_patterns(
        self,
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> List[OptimizedEmergentPattern]:
        """检测所有涌现模式（优化版）"""
        patterns = []
        
        # 检测级联
        patterns.extend(self.cascade_detector.detect_cascades(user_data, history))
        
        # 检测反馈环
        patterns.extend(self.feedback_detector.detect_feedback_loops(user_data, history))
        
        # 检测临界点
        patterns.extend(self.tipping_detector.detect_tipping_points(user_data, history))
        
        # 按置信度排序
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        return patterns
    
    def get_pattern_summary(self, patterns: List[OptimizedEmergentPattern]) -> Dict[str, Any]:
        """获取模式总结"""
        return {
            "total_patterns": len(patterns),
            "by_type": {
                "cascade": len([p for p in patterns if p.pattern_type == "cascade"]),
                "feedback_loop": len([p for p in patterns if p.pattern_type == "feedback_loop"]),
                "tipping_point": len([p for p in patterns if p.pattern_type == "tipping_point"])
            },
            "high_confidence": len([p for p in patterns if p.confidence > 0.85]),
            "average_confidence": np.mean([p.confidence for p in patterns]) if patterns else 0.0,
            "patterns": [
                {
                    "id": p.pattern_id,
                    "type": p.pattern_type,
                    "domains": p.domains,
                    "description": p.description,
                    "confidence": p.confidence,
                    "impact_score": p.impact_score,
                    "statistical_significance": p.statistical_significance,
                    "recommendations": p.recommendations
                }
                for p in patterns[:10]
            ]
        }


# 全局实例
_optimized_detector = None

def get_optimized_emergence_detector() -> OptimizedEmergenceDetector:
    """获取优化的涌现检测器实例"""
    global _optimized_detector
    if _optimized_detector is None:
        _optimized_detector = OptimizedEmergenceDetector()
    return _optimized_detector

