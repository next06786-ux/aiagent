"""
数字孪生系统 - Phase 2.5
实现决策追踪、反事实分析、决策对比、可视化
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class DecisionType(Enum):
    """决策类型"""
    HEALTH = "health"  # 健康决策
    TIME = "time"  # 时间管理决策
    EMOTION = "emotion"  # 情绪管理决策
    SOCIAL = "social"  # 社交决策
    FINANCE = "finance"  # 财务决策
    LEARNING = "learning"  # 学习决策


class DecisionOutcome(Enum):
    """决策结果"""
    POSITIVE = "positive"  # 积极结果
    NEUTRAL = "neutral"  # 中立结果
    NEGATIVE = "negative"  # 消极结果
    UNKNOWN = "unknown"  # 未知结果


@dataclass
class Decision:
    """决策记录"""
    decision_id: str
    user_id: str
    decision_type: DecisionType
    description: str
    context: Dict[str, Any]  # 决策背景
    options: List[str]  # 可选方案
    chosen_option: str  # 选择的方案
    
    # 结果追踪
    outcome: Optional[DecisionOutcome] = None
    actual_impact: Dict[str, float] = field(default_factory=dict)  # 实际影响
    expected_impact: Dict[str, float] = field(default_factory=dict)  # 预期影响
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.5  # 决策置信度


@dataclass
class CounterfactualScenario:
    """反事实场景"""
    scenario_id: str
    original_decision: Decision
    alternative_option: str
    
    # 模拟结果
    simulated_impact: Dict[str, float]  # 模拟影响
    confidence: float  # 模拟置信度
    
    # 对比
    impact_difference: Dict[str, float]  # 与实际的差异
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DecisionComparison:
    """决策对比"""
    comparison_id: str
    decision1: Decision
    decision2: Decision
    
    # 对比指标
    similarity: float  # 相似度
    outcome_alignment: float  # 结果一致性
    impact_correlation: float  # 影响相关性
    
    # 洞察
    insights: List[str]  # 对比洞察
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class DecisionTracker:
    """决策追踪器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.decisions = {}  # decision_id -> Decision
        self.decision_history = []
        self.decision_outcomes = defaultdict(list)  # decision_type -> [outcomes]
    
    def record_decision(
        self,
        decision_type: DecisionType,
        description: str,
        context: Dict[str, Any],
        options: List[str],
        chosen_option: str,
        expected_impact: Dict[str, float]
    ) -> Decision:
        """记录决策"""
        from collections import defaultdict
        
        decision = Decision(
            decision_id=f"dec_{datetime.now().timestamp()}",
            user_id=self.user_id,
            decision_type=decision_type,
            description=description,
            context=context,
            options=options,
            chosen_option=chosen_option,
            expected_impact=expected_impact
        )
        
        self.decisions[decision.decision_id] = decision
        self.decision_history.append(decision)
        
        return decision
    
    def update_decision_outcome(
        self,
        decision_id: str,
        outcome: DecisionOutcome,
        actual_impact: Dict[str, float]
    ) -> Optional[Decision]:
        """更新决策结果"""
        if decision_id not in self.decisions:
            return None
        
        decision = self.decisions[decision_id]
        decision.outcome = outcome
        decision.actual_impact = actual_impact
        decision.updated_at = datetime.now().isoformat()
        
        # 记录结果
        self.decision_outcomes[decision.decision_type.value].append({
            "outcome": outcome.value,
            "impact": actual_impact,
            "timestamp": datetime.now().isoformat()
        })
        
        return decision
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """获取决策统计"""
        total_decisions = len(self.decisions)
        
        # 按类型统计
        by_type = {}
        for dec_type in DecisionType:
            type_decisions = [
                d for d in self.decisions.values()
                if d.decision_type == dec_type
            ]
            by_type[dec_type.value] = len(type_decisions)
        
        # 按结果统计
        by_outcome = {}
        for outcome in DecisionOutcome:
            outcome_decisions = [
                d for d in self.decisions.values()
                if d.outcome == outcome
            ]
            by_outcome[outcome.value] = len(outcome_decisions)
        
        # 计算成功率
        positive_count = by_outcome.get(DecisionOutcome.POSITIVE.value, 0)
        decided_count = sum(1 for d in self.decisions.values() if d.outcome is not None)
        success_rate = positive_count / decided_count if decided_count > 0 else 0
        
        return {
            "total_decisions": total_decisions,
            "by_type": by_type,
            "by_outcome": by_outcome,
            "success_rate": success_rate,
            "average_confidence": sum(d.confidence for d in self.decisions.values()) / total_decisions if total_decisions > 0 else 0
        }
    
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取决策历史"""
        return [
            {
                "decision_id": d.decision_id,
                "type": d.decision_type.value,
                "description": d.description,
                "chosen_option": d.chosen_option,
                "outcome": d.outcome.value if d.outcome else None,
                "created_at": d.created_at
            }
            for d in self.decision_history[-limit:]
        ]


class CounterfactualAnalyzer:
    """反事实分析器"""
    
    def __init__(self, tracker: DecisionTracker):
        self.tracker = tracker
        self.scenarios = {}  # scenario_id -> CounterfactualScenario
    
    def generate_counterfactual(
        self,
        decision_id: str,
        alternative_option: str,
        impact_model: Optional[callable] = None
    ) -> Optional[CounterfactualScenario]:
        """
        生成反事实场景
        模拟如果选择了不同的选项会发生什么
        """
        if decision_id not in self.tracker.decisions:
            return None
        
        original_decision = self.tracker.decisions[decision_id]
        
        # 模拟替代选项的影响
        if impact_model:
            simulated_impact = impact_model(alternative_option, original_decision.context)
        else:
            # 简化的模拟：基于选项相似度调整影响
            simulated_impact = self._simulate_impact(
                alternative_option,
                original_decision.chosen_option,
                original_decision.expected_impact
            )
        
        # 计算与实际的差异
        impact_difference = {}
        if original_decision.actual_impact:
            for key in original_decision.actual_impact:
                actual = original_decision.actual_impact.get(key, 0)
                simulated = simulated_impact.get(key, 0)
                impact_difference[key] = simulated - actual
        
        scenario = CounterfactualScenario(
            scenario_id=f"cf_{datetime.now().timestamp()}",
            original_decision=original_decision,
            alternative_option=alternative_option,
            simulated_impact=simulated_impact,
            confidence=0.7,
            impact_difference=impact_difference
        )
        
        self.scenarios[scenario.scenario_id] = scenario
        return scenario
    
    def _simulate_impact(
        self,
        alternative_option: str,
        chosen_option: str,
        expected_impact: Dict[str, float]
    ) -> Dict[str, float]:
        """模拟替代选项的影响"""
        # 简化实现：基于选项相似度调整
        similarity = self._calculate_option_similarity(alternative_option, chosen_option)
        
        simulated = {}
        for key, value in expected_impact.items():
            # 相似度越高，影响越接近
            simulated[key] = value * (0.5 + similarity * 0.5)
        
        return simulated
    
    def _calculate_option_similarity(self, opt1: str, opt2: str) -> float:
        """计算选项相似度"""
        # 简化实现：基于字符串相似度
        if opt1 == opt2:
            return 1.0
        
        # Jaccard相似度
        set1 = set(opt1.lower().split())
        set2 = set(opt2.lower().split())
        
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0
    
    def analyze_counterfactual(
        self,
        scenario: CounterfactualScenario
    ) -> Dict[str, Any]:
        """分析反事实场景"""
        analysis = {
            "scenario_id": scenario.scenario_id,
            "original_option": scenario.original_decision.chosen_option,
            "alternative_option": scenario.alternative_option,
            "impact_comparison": {}
        }
        
        # 对比影响
        for key in scenario.simulated_impact:
            actual = scenario.original_decision.actual_impact.get(key, 0)
            simulated = scenario.simulated_impact.get(key, 0)
            
            analysis["impact_comparison"][key] = {
                "actual": actual,
                "simulated": simulated,
                "difference": simulated - actual,
                "better": simulated > actual
            }
        
        # 生成洞察
        insights = []
        for key, comparison in analysis["impact_comparison"].items():
            if comparison["better"]:
                insights.append(f"选择'{scenario.alternative_option}'在{key}上会更好")
            else:
                insights.append(f"选择'{scenario.alternative_option}'在{key}上会更差")
        
        analysis["insights"] = insights
        
        return analysis
    
    def get_counterfactual_scenarios(self, decision_id: str) -> List[CounterfactualScenario]:
        """获取特定决策的所有反事实场景"""
        return [
            s for s in self.scenarios.values()
            if s.original_decision.decision_id == decision_id
        ]


class DecisionComparator:
    """决策对比器"""
    
    def __init__(self, tracker: DecisionTracker):
        self.tracker = tracker
        self.comparisons = {}  # comparison_id -> DecisionComparison
    
    def compare_decisions(
        self,
        decision1_id: str,
        decision2_id: str
    ) -> Optional[DecisionComparison]:
        """对比两个决策"""
        if decision1_id not in self.tracker.decisions or decision2_id not in self.tracker.decisions:
            return None
        
        decision1 = self.tracker.decisions[decision1_id]
        decision2 = self.tracker.decisions[decision2_id]
        
        # 计算相似度
        similarity = self._calculate_similarity(decision1, decision2)
        
        # 计算结果一致性
        outcome_alignment = self._calculate_outcome_alignment(decision1, decision2)
        
        # 计算影响相关性
        impact_correlation = self._calculate_impact_correlation(decision1, decision2)
        
        # 生成洞察
        insights = self._generate_insights(decision1, decision2, similarity, outcome_alignment)
        
        comparison = DecisionComparison(
            comparison_id=f"cmp_{datetime.now().timestamp()}",
            decision1=decision1,
            decision2=decision2,
            similarity=similarity,
            outcome_alignment=outcome_alignment,
            impact_correlation=impact_correlation,
            insights=insights
        )
        
        self.comparisons[comparison.comparison_id] = comparison
        return comparison
    
    def _calculate_similarity(self, d1: Decision, d2: Decision) -> float:
        """计算决策相似度"""
        score = 0.0
        
        # 类型相同
        if d1.decision_type == d2.decision_type:
            score += 0.3
        
        # 选项相同
        if d1.chosen_option == d2.chosen_option:
            score += 0.3
        
        # 背景相似
        context_similarity = self._calculate_context_similarity(d1.context, d2.context)
        score += context_similarity * 0.4
        
        return min(score, 1.0)
    
    def _calculate_context_similarity(self, ctx1: Dict, ctx2: Dict) -> float:
        """计算背景相似度"""
        if not ctx1 or not ctx2:
            return 0.0
        
        keys1 = set(ctx1.keys())
        keys2 = set(ctx2.keys())
        
        if not keys1 and not keys2:
            return 1.0
        
        common_keys = keys1 & keys2
        all_keys = keys1 | keys2
        
        return len(common_keys) / len(all_keys) if all_keys else 0
    
    def _calculate_outcome_alignment(self, d1: Decision, d2: Decision) -> float:
        """计算结果一致性"""
        if d1.outcome is None or d2.outcome is None:
            return 0.0
        
        if d1.outcome == d2.outcome:
            return 1.0
        elif d1.outcome == DecisionOutcome.POSITIVE and d2.outcome == DecisionOutcome.NEUTRAL:
            return 0.7
        elif d1.outcome == DecisionOutcome.NEUTRAL and d2.outcome == DecisionOutcome.POSITIVE:
            return 0.7
        else:
            return 0.0
    
    def _calculate_impact_correlation(self, d1: Decision, d2: Decision) -> float:
        """计算影响相关性"""
        if not d1.actual_impact or not d2.actual_impact:
            return 0.0
        
        # 计算影响向量的相关性
        keys = set(d1.actual_impact.keys()) & set(d2.actual_impact.keys())
        
        if not keys:
            return 0.0
        
        # 简化：计算影响方向的一致性
        consistent = 0
        for key in keys:
            v1 = d1.actual_impact[key]
            v2 = d2.actual_impact[key]
            
            if (v1 > 0 and v2 > 0) or (v1 < 0 and v2 < 0):
                consistent += 1
        
        return consistent / len(keys)
    
    def _generate_insights(
        self,
        d1: Decision,
        d2: Decision,
        similarity: float,
        outcome_alignment: float
    ) -> List[str]:
        """生成对比洞察"""
        insights = []
        
        if similarity > 0.7:
            insights.append("这两个决策非常相似")
        elif similarity > 0.4:
            insights.append("这两个决策有一定的相似性")
        else:
            insights.append("这两个决策差异较大")
        
        if outcome_alignment > 0.7:
            insights.append("两个决策的结果一致")
        elif outcome_alignment > 0.3:
            insights.append("两个决策的结果部分一致")
        else:
            insights.append("两个决策的结果不一致")
        
        if d1.decision_type == d2.decision_type:
            insights.append(f"都是{d1.decision_type.value}类型的决策")
        
        return insights
    
    def get_comparison_report(self, comparison_id: str) -> Optional[Dict[str, Any]]:
        """获取对比报告"""
        if comparison_id not in self.comparisons:
            return None
        
        comparison = self.comparisons[comparison_id]
        
        return {
            "comparison_id": comparison_id,
            "decision1": {
                "id": comparison.decision1.decision_id,
                "type": comparison.decision1.decision_type.value,
                "description": comparison.decision1.description,
                "outcome": comparison.decision1.outcome.value if comparison.decision1.outcome else None
            },
            "decision2": {
                "id": comparison.decision2.decision_id,
                "type": comparison.decision2.decision_type.value,
                "description": comparison.decision2.description,
                "outcome": comparison.decision2.outcome.value if comparison.decision2.outcome else None
            },
            "metrics": {
                "similarity": comparison.similarity,
                "outcome_alignment": comparison.outcome_alignment,
                "impact_correlation": comparison.impact_correlation
            },
            "insights": comparison.insights
        }


class DigitalTwinSystem:
    """数字孪生系统"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.tracker = DecisionTracker(user_id)
        self.counterfactual_analyzer = CounterfactualAnalyzer(self.tracker)
        self.comparator = DecisionComparator(self.tracker)
    
    def record_decision(
        self,
        decision_type: str,
        description: str,
        context: Dict[str, Any],
        options: List[str],
        chosen_option: str,
        expected_impact: Dict[str, float]
    ) -> Dict[str, Any]:
        """记录决策"""
        try:
            dec_type = DecisionType[decision_type.upper()]
        except KeyError:
            dec_type = DecisionType.HEALTH
        
        decision = self.tracker.record_decision(
            dec_type, description, context, options, chosen_option, expected_impact
        )
        
        return {
            "decision_id": decision.decision_id,
            "type": decision.decision_type.value,
            "description": decision.description,
            "created_at": decision.created_at
        }
    
    def update_decision_outcome(
        self,
        decision_id: str,
        outcome: str,
        actual_impact: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """更新决策结果"""
        try:
            outcome_type = DecisionOutcome[outcome.upper()]
        except KeyError:
            outcome_type = DecisionOutcome.UNKNOWN
        
        decision = self.tracker.update_decision_outcome(decision_id, outcome_type, actual_impact)
        
        if decision:
            return {
                "decision_id": decision.decision_id,
                "outcome": decision.outcome.value,
                "actual_impact": decision.actual_impact,
                "updated_at": decision.updated_at
            }
        
        return None
    
    def analyze_counterfactual(
        self,
        decision_id: str,
        alternative_option: str
    ) -> Optional[Dict[str, Any]]:
        """分析反事实场景"""
        scenario = self.counterfactual_analyzer.generate_counterfactual(
            decision_id, alternative_option
        )
        
        if scenario:
            analysis = self.counterfactual_analyzer.analyze_counterfactual(scenario)
            return analysis
        
        return None
    
    def compare_decisions(
        self,
        decision1_id: str,
        decision2_id: str
    ) -> Optional[Dict[str, Any]]:
        """对比决策"""
        comparison = self.comparator.compare_decisions(decision1_id, decision2_id)
        
        if comparison:
            return self.comparator.get_comparison_report(comparison.comparison_id)
        
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        stats = self.tracker.get_decision_statistics()
        
        return {
            "user_id": self.user_id,
            "statistics": stats,
            "recent_decisions": self.tracker.get_decision_history(limit=5),
            "counterfactual_scenarios": len(self.counterfactual_analyzer.scenarios),
            "comparisons": len(self.comparator.comparisons)
        }


# 全局实例管理
from collections import defaultdict
_systems = {}

def get_digital_twin_system(user_id: str) -> DigitalTwinSystem:
    """获取数字孪生系统实例"""
    if user_id not in _systems:
        _systems[user_id] = DigitalTwinSystem(user_id)
    return _systems[user_id]

