"""
反事实决策分析系统
分析"如果...会怎样"的场景，支持更好的决策
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from enum import Enum
import json
import math


class CounterfactualScenario(Enum):
    """反事实场景"""
    WHAT_IF = "what_if"  # 如果...会怎样
    REGRET_ANALYSIS = "regret_analysis"  # 后悔分析
    OPPORTUNITY_COST = "opportunity_cost"  # 机会成本
    BEST_CASE = "best_case"  # 最好情况
    WORST_CASE = "worst_case"  # 最坏情况


class CounterfactualAnalysis:
    """反事实分析"""
    
    def __init__(self, analysis_id: str, scenario_type: CounterfactualScenario,
                 original_decision: str, alternative_decision: str,
                 original_outcome: Dict[str, float], alternative_outcome: Dict[str, float]):
        """
        初始化反事实分析
        
        Args:
            analysis_id: 分析ID
            scenario_type: 场景类型
            original_decision: 原始决策
            alternative_decision: 替代决策
            original_outcome: 原始结果
            alternative_outcome: 替代结果
        """
        self.analysis_id = analysis_id
        self.scenario_type = scenario_type
        self.original_decision = original_decision
        self.alternative_decision = alternative_decision
        self.original_outcome = original_outcome
        self.alternative_outcome = alternative_outcome
        self.created_at = datetime.now()
        self.insights = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "analysis_id": self.analysis_id,
            "scenario_type": self.scenario_type.value,
            "original_decision": self.original_decision,
            "alternative_decision": self.alternative_decision,
            "original_outcome": self.original_outcome,
            "alternative_outcome": self.alternative_outcome,
            "insights": self.insights,
            "created_at": self.created_at.isoformat()
        }


class CounterfactualAnalyzer:
    """反事实分析器"""
    
    def __init__(self, user_id: str):
        """
        初始化反事实分析器
        
        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        self.analyses: Dict[str, CounterfactualAnalysis] = {}
        self.analysis_history: List[CounterfactualAnalysis] = []
        
        # 分析统计
        self.analysis_stats = {
            "total_analyses": 0,
            "what_if_analyses": 0,
            "regret_analyses": 0,
            "opportunity_cost_analyses": 0,
            "best_case_analyses": 0,
            "worst_case_analyses": 0
        }
    
    def analyze_what_if(self, original_decision: str, alternative_decision: str,
                       current_state: Dict[str, float],
                       decision_impact: Dict[str, float]) -> CounterfactualAnalysis:
        """
        分析"如果...会怎样"
        
        Args:
            original_decision: 原始决策
            alternative_decision: 替代决策
            current_state: 当前状态
            decision_impact: 决策影响
        
        Returns:
            分析结果
        """
        analysis_id = f"cf_whatif_{datetime.now().timestamp()}"
        
        # 计算原始结果
        original_outcome = self._simulate_outcome(current_state, original_decision, decision_impact)
        
        # 计算替代结果
        alternative_outcome = self._simulate_outcome(current_state, alternative_decision, decision_impact)
        
        # 创建分析
        analysis = CounterfactualAnalysis(
            analysis_id=analysis_id,
            scenario_type=CounterfactualScenario.WHAT_IF,
            original_decision=original_decision,
            alternative_decision=alternative_decision,
            original_outcome=original_outcome,
            alternative_outcome=alternative_outcome
        )
        
        # 生成洞察
        analysis.insights = self._generate_what_if_insights(
            original_decision, alternative_decision,
            original_outcome, alternative_outcome
        )
        
        # 记录分析
        self.analyses[analysis_id] = analysis
        self.analysis_history.append(analysis)
        self.analysis_stats["total_analyses"] += 1
        self.analysis_stats["what_if_analyses"] += 1
        
        return analysis
    
    def analyze_regret(self, past_decision: str, actual_outcome: Dict[str, float],
                      alternative_decision: str, alternative_outcome: Dict[str, float]) -> CounterfactualAnalysis:
        """
        分析后悔 - 如果当时做了不同的选择会怎样
        
        Args:
            past_decision: 过去的决策
            actual_outcome: 实际结果
            alternative_decision: 替代决策
            alternative_outcome: 替代结果
        
        Returns:
            分析结果
        """
        analysis_id = f"cf_regret_{datetime.now().timestamp()}"
        
        # 创建分析
        analysis = CounterfactualAnalysis(
            analysis_id=analysis_id,
            scenario_type=CounterfactualScenario.REGRET_ANALYSIS,
            original_decision=past_decision,
            alternative_decision=alternative_decision,
            original_outcome=actual_outcome,
            alternative_outcome=alternative_outcome
        )
        
        # 生成洞察
        analysis.insights = self._generate_regret_insights(
            past_decision, alternative_decision,
            actual_outcome, alternative_outcome
        )
        
        # 记录分析
        self.analyses[analysis_id] = analysis
        self.analysis_history.append(analysis)
        self.analysis_stats["total_analyses"] += 1
        self.analysis_stats["regret_analyses"] += 1
        
        return analysis
    
    def analyze_opportunity_cost(self, chosen_action: str, foregone_action: str,
                                current_state: Dict[str, float]) -> CounterfactualAnalysis:
        """
        分析机会成本
        
        Args:
            chosen_action: 选择的行动
            foregone_action: 放弃的行动
            current_state: 当前状态
        
        Returns:
            分析结果
        """
        analysis_id = f"cf_opp_{datetime.now().timestamp()}"
        
        # 计算选择行动的结果
        chosen_outcome = self._simulate_action_outcome(current_state, chosen_action)
        
        # 计算放弃行动的结果
        foregone_outcome = self._simulate_action_outcome(current_state, foregone_action)
        
        # 创建分析
        analysis = CounterfactualAnalysis(
            analysis_id=analysis_id,
            scenario_type=CounterfactualScenario.OPPORTUNITY_COST,
            original_decision=chosen_action,
            alternative_decision=foregone_action,
            original_outcome=chosen_outcome,
            alternative_outcome=foregone_outcome
        )
        
        # 生成洞察
        analysis.insights = self._generate_opportunity_cost_insights(
            chosen_action, foregone_action,
            chosen_outcome, foregone_outcome
        )
        
        # 记录分析
        self.analyses[analysis_id] = analysis
        self.analysis_history.append(analysis)
        self.analysis_stats["total_analyses"] += 1
        self.analysis_stats["opportunity_cost_analyses"] += 1
        
        return analysis
    
    def analyze_best_case(self, decision: str, current_state: Dict[str, float]) -> CounterfactualAnalysis:
        """
        分析最好情况
        
        Args:
            decision: 决策
            current_state: 当前状态
        
        Returns:
            分析结果
        """
        analysis_id = f"cf_best_{datetime.now().timestamp()}"
        
        # 计算实际结果
        actual_outcome = self._simulate_outcome(current_state, decision, {})
        
        # 计算最好情况
        best_outcome = self._simulate_best_case(current_state, decision)
        
        # 创建分析
        analysis = CounterfactualAnalysis(
            analysis_id=analysis_id,
            scenario_type=CounterfactualScenario.BEST_CASE,
            original_decision=decision,
            alternative_decision=f"{decision} (最好情况)",
            original_outcome=actual_outcome,
            alternative_outcome=best_outcome
        )
        
        # 生成洞察
        analysis.insights = self._generate_best_case_insights(
            decision, actual_outcome, best_outcome
        )
        
        # 记录分析
        self.analyses[analysis_id] = analysis
        self.analysis_history.append(analysis)
        self.analysis_stats["total_analyses"] += 1
        self.analysis_stats["best_case_analyses"] += 1
        
        return analysis
    
    def analyze_worst_case(self, decision: str, current_state: Dict[str, float]) -> CounterfactualAnalysis:
        """
        分析最坏情况
        
        Args:
            decision: 决策
            current_state: 当前状态
        
        Returns:
            分析结果
        """
        analysis_id = f"cf_worst_{datetime.now().timestamp()}"
        
        # 计算实际结果
        actual_outcome = self._simulate_outcome(current_state, decision, {})
        
        # 计算最坏情况
        worst_outcome = self._simulate_worst_case(current_state, decision)
        
        # 创建分析
        analysis = CounterfactualAnalysis(
            analysis_id=analysis_id,
            scenario_type=CounterfactualScenario.WORST_CASE,
            original_decision=decision,
            alternative_decision=f"{decision} (最坏情况)",
            original_outcome=actual_outcome,
            alternative_outcome=worst_outcome
        )
        
        # 生成洞察
        analysis.insights = self._generate_worst_case_insights(
            decision, actual_outcome, worst_outcome
        )
        
        # 记录分析
        self.analyses[analysis_id] = analysis
        self.analysis_history.append(analysis)
        self.analysis_stats["total_analyses"] += 1
        self.analysis_stats["worst_case_analyses"] += 1
        
        return analysis
    
    def _simulate_outcome(self, state: Dict[str, float], decision: str,
                         impact: Dict[str, float]) -> Dict[str, float]:
        """
        模拟决策结果
        
        Args:
            state: 当前状态
            decision: 决策
            impact: 影响
        
        Returns:
            结果
        """
        outcome = state.copy()
        
        # 根据决策类型应用影响
        decision_impacts = {
            "exercise": {"health_score": 10, "stress_level": -5, "mood": 5},
            "sleep": {"health_score": 15, "stress_level": -10, "mood": 5},
            "meditation": {"stress_level": -15, "mood": 10},
            "social": {"mood": 15, "stress_level": -5},
            "work": {"stress_level": 5, "mood": -5}
        }
        
        if decision in decision_impacts:
            for metric, change in decision_impacts[decision].items():
                if metric in outcome:
                    outcome[metric] = outcome[metric] + change
        
        # 应用自定义影响
        for metric, change in impact.items():
            if metric in outcome:
                outcome[metric] = outcome[metric] + change
        
        return outcome
    
    def _simulate_action_outcome(self, state: Dict[str, float], action: str) -> Dict[str, float]:
        """模拟行动结果"""
        return self._simulate_outcome(state, action, {})
    
    def _simulate_best_case(self, state: Dict[str, float], decision: str) -> Dict[str, float]:
        """模拟最好情况"""
        outcome = self._simulate_outcome(state, decision, {})
        
        # 增加所有正面指标
        for metric in outcome:
            if metric in ["health_score", "mood", "happiness"]:
                outcome[metric] = min(outcome[metric] * 1.5, 100)
            elif metric in ["stress_level", "anxiety_level"]:
                outcome[metric] = max(outcome[metric] * 0.5, 0)
        
        return outcome
    
    def _simulate_worst_case(self, state: Dict[str, float], decision: str) -> Dict[str, float]:
        """模拟最坏情况"""
        outcome = self._simulate_outcome(state, decision, {})
        
        # 减少所有正面指标
        for metric in outcome:
            if metric in ["health_score", "mood", "happiness"]:
                outcome[metric] = max(outcome[metric] * 0.5, 0)
            elif metric in ["stress_level", "anxiety_level"]:
                outcome[metric] = min(outcome[metric] * 1.5, 100)
        
        return outcome
    
    def _generate_what_if_insights(self, original: str, alternative: str,
                                   original_outcome: Dict[str, float],
                                   alternative_outcome: Dict[str, float]) -> List[str]:
        """生成"如果...会怎样"的洞察"""
        insights = []
        
        # 比较结果
        differences = {}
        for metric in original_outcome:
            if metric in alternative_outcome:
                diff = alternative_outcome[metric] - original_outcome[metric]
                if abs(diff) > 0.1:
                    differences[metric] = diff
        
        # 生成洞察
        if differences:
            best_metric = max(differences.items(), key=lambda x: x[1])
            worst_metric = min(differences.items(), key=lambda x: x[1])
            
            insights.append(f"如果选择{alternative}而不是{original}，{best_metric[0]}会增加{best_metric[1]:.1f}")
            insights.append(f"但{worst_metric[0]}会减少{abs(worst_metric[1]):.1f}")
        
        return insights
    
    def _generate_regret_insights(self, past: str, alternative: str,
                                 actual: Dict[str, float],
                                 alternative_outcome: Dict[str, float]) -> List[str]:
        """生成后悔分析的洞察"""
        insights = []
        
        # 计算后悔程度
        regret_score = 0
        for metric in actual:
            if metric in alternative_outcome:
                if alternative_outcome[metric] > actual[metric]:
                    regret_score += alternative_outcome[metric] - actual[metric]
        
        if regret_score > 10:
            insights.append(f"如果当时选择了{alternative}而不是{past}，结果会更好")
            insights.append(f"后悔程度：{regret_score:.1f}（较高）")
        elif regret_score > 0:
            insights.append(f"选择{alternative}可能会有轻微的改善")
        else:
            insights.append(f"当时的选择{past}是正确的")
        
        return insights
    
    def _generate_opportunity_cost_insights(self, chosen: str, foregone: str,
                                           chosen_outcome: Dict[str, float],
                                           foregone_outcome: Dict[str, float]) -> List[str]:
        """生成机会成本的洞察"""
        insights = []
        
        # 计算机会成本
        opportunity_cost = 0
        for metric in foregone_outcome:
            if metric in chosen_outcome:
                if foregone_outcome[metric] > chosen_outcome[metric]:
                    opportunity_cost += foregone_outcome[metric] - chosen_outcome[metric]
        
        insights.append(f"选择{chosen}的机会成本是放弃{foregone}")
        insights.append(f"机会成本评分：{opportunity_cost:.1f}")
        
        if opportunity_cost > 15:
            insights.append("机会成本较高，可能需要重新考虑")
        
        return insights
    
    def _generate_best_case_insights(self, decision: str,
                                    actual: Dict[str, float],
                                    best: Dict[str, float]) -> List[str]:
        """生成最好情况的洞察"""
        insights = []
        
        # 计算最好情况的潜力
        potential = 0
        for metric in best:
            if metric in actual:
                potential += best[metric] - actual[metric]
        
        insights.append(f"在最好的情况下，{decision}可以带来{potential:.1f}的改善")
        insights.append("这代表了该决策的最大潜力")
        
        return insights
    
    def _generate_worst_case_insights(self, decision: str,
                                     actual: Dict[str, float],
                                     worst: Dict[str, float]) -> List[str]:
        """生成最坏情况的洞察"""
        insights = []
        
        # 计算最坏情况的风险
        risk = 0
        for metric in worst:
            if metric in actual:
                risk += actual[metric] - worst[metric]
        
        insights.append(f"在最坏的情况下，{decision}可能导致{risk:.1f}的恶化")
        insights.append("这代表了该决策的最大风险")
        
        return insights
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """获取分析统计"""
        return self.analysis_stats
    
    def get_recent_analyses(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近的分析"""
        return [a.to_dict() for a in self.analysis_history[-limit:]]
    
    def export_analyses(self) -> Dict[str, Any]:
        """导出分析"""
        return {
            "user_id": self.user_id,
            "analyses": [a.to_dict() for a in self.analysis_history],
            "statistics": self.get_analysis_statistics(),
            "exported_at": datetime.now().isoformat()
        }


def get_counterfactual_analyzer(user_id: str) -> CounterfactualAnalyzer:
    """获取反事实分析器实例"""
    return CounterfactualAnalyzer(user_id)

