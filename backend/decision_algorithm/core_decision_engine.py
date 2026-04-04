"""
核心决策算法引擎
不依赖预测，基于真实数据和成熟决策理论
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class DecisionDimension(Enum):
    """决策评估维度"""
    FEASIBILITY = "feasibility"      # 可行性
    BENEFIT = "benefit"              # 收益
    RISK = "risk"                    # 风险
    REVERSIBILITY = "reversibility"  # 可逆性
    ALIGNMENT = "alignment"          # 目标一致性
    RESOURCE = "resource"            # 资源充足度


@dataclass
class DecisionOption:
    """决策选项"""
    id: str
    title: str
    description: str
    
    # 核心评分（0-1）
    feasibility_score: float = 0.5
    benefit_score: float = 0.5
    risk_score: float = 0.5
    reversibility_score: float = 0.5
    alignment_score: float = 0.5
    resource_score: float = 0.5
    
    # 支撑数据
    evidence: Dict[str, Any] = None
    assumptions: List[str] = None
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = {}
        if self.assumptions is None:
            self.assumptions = []


class CoreDecisionEngine:
    """
    核心决策算法引擎
    
    基于成熟的决策理论：
    1. 多属性效用理论 (MAUT)
    2. 层次分析法 (AHP)
    3. 前景理论 (Prospect Theory)
    4. 信息差距理论 (Info-Gap Theory)
    """
    
    def __init__(self):
        # 默认权重（可根据用户偏好调整）
        self.default_weights = {
            DecisionDimension.FEASIBILITY: 0.25,
            DecisionDimension.BENEFIT: 0.20,
            DecisionDimension.RISK: 0.20,
            DecisionDimension.REVERSIBILITY: 0.15,
            DecisionDimension.ALIGNMENT: 0.15,
            DecisionDimension.RESOURCE: 0.05
        }
    
    def calculate_option_score(
        self,
        option: DecisionOption,
        user_weights: Optional[Dict[DecisionDimension, float]] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        计算选项综合得分
        
        Returns:
            (总分, 各维度得分详情)
        """
        weights = user_weights or self.default_weights
        
        # 各维度得分
        dimension_scores = {
            'feasibility': option.feasibility_score,
            'benefit': option.benefit_score,
            'risk': 1 - option.risk_score,  # 风险越低越好
            'reversibility': option.reversibility_score,
            'alignment': option.alignment_score,
            'resource': option.resource_score
        }
        
        # 加权求和
        total_score = sum(
            dimension_scores[dim.value] * weight
            for dim, weight in weights.items()
        )
        
        return total_score, dimension_scores
    
    def calculate_feasibility(
        self,
        required_skills: List[str],
        current_skills: List[str],
        required_resources: Dict[str, float],
        available_resources: Dict[str, float],
        time_required: int,  # 天数
        time_available: int  # 天数
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算可行性得分
        
        基于：
        1. 技能匹配度
        2. 资源充足度
        3. 时间合理性
        
        Returns:
            (可行性得分 0-1, 详细分析)
        """
        # 1. 技能匹配度
        if not required_skills:
            skill_match = 1.0
        else:
            matched_skills = set(required_skills) & set(current_skills)
            skill_match = len(matched_skills) / len(required_skills)
        
        # 2. 资源充足度
        resource_scores = []
        resource_details = {}
        for resource, required in required_resources.items():
            available = available_resources.get(resource, 0)
            if required == 0:
                score = 1.0
            else:
                score = min(1.0, available / required)
            resource_scores.append(score)
            resource_details[resource] = {
                'required': required,
                'available': available,
                'sufficiency': score
            }
        
        resource_sufficiency = sum(resource_scores) / len(resource_scores) if resource_scores else 1.0
        
        # 3. 时间合理性
        if time_required == 0:
            time_feasibility = 1.0
        else:
            time_feasibility = min(1.0, time_available / time_required)
        
        # 综合可行性（加权平均）
        feasibility = (
            skill_match * 0.4 +
            resource_sufficiency * 0.4 +
            time_feasibility * 0.2
        )
        
        details = {
            'skill_match': skill_match,
            'matched_skills': list(set(required_skills) & set(current_skills)),
            'missing_skills': list(set(required_skills) - set(current_skills)),
            'resource_sufficiency': resource_sufficiency,
            'resource_details': resource_details,
            'time_feasibility': time_feasibility,
            'time_required_days': time_required,
            'time_available_days': time_available
        }
        
        return feasibility, details
    
    def calculate_benefit(
        self,
        short_term_gains: Dict[str, float],  # 短期收益（1-6个月）
        long_term_gains: Dict[str, float],   # 长期收益（6个月+）
        opportunity_cost: float = 0.0,       # 机会成本
        discount_rate: float = 0.1           # 时间折扣率
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算收益得分
        
        基于：
        1. 短期收益
        2. 长期收益（考虑时间折扣）
        3. 机会成本
        
        Returns:
            (收益得分 0-1, 详细分析)
        """
        # 短期收益（权重0.4）
        short_term_value = sum(short_term_gains.values())
        
        # 长期收益（权重0.6，但要折现）
        long_term_value = sum(long_term_gains.values()) * (1 - discount_rate)
        
        # 总收益
        total_gain = short_term_value * 0.4 + long_term_value * 0.6
        
        # 扣除机会成本
        net_benefit = total_gain - opportunity_cost
        
        # 归一化到0-1（假设最大收益为10）
        benefit_score = min(1.0, max(0.0, net_benefit / 10.0))
        
        details = {
            'short_term_value': short_term_value,
            'long_term_value': long_term_value,
            'total_gain': total_gain,
            'opportunity_cost': opportunity_cost,
            'net_benefit': net_benefit,
            'short_term_gains': short_term_gains,
            'long_term_gains': long_term_gains
        }
        
        return benefit_score, details
    
    def calculate_risk(
        self,
        failure_probability: float,      # 失败概率 0-1
        failure_cost: float,             # 失败代价
        uncertainty_factors: List[str],  # 不确定因素
        mitigation_plans: List[str]      # 风险缓解措施
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算风险得分
        
        基于：
        1. 失败概率
        2. 失败代价
        3. 不确定性
        4. 风险缓解能力
        
        Returns:
            (风险得分 0-1，越高风险越大, 详细分析)
        """
        # 基础风险 = 失败概率 × 失败代价
        base_risk = failure_probability * min(1.0, failure_cost / 10.0)
        
        # 不确定性惩罚
        uncertainty_penalty = len(uncertainty_factors) * 0.05
        
        # 缓解措施折扣
        mitigation_discount = len(mitigation_plans) * 0.1
        
        # 综合风险
        total_risk = base_risk + uncertainty_penalty - mitigation_discount
        total_risk = min(1.0, max(0.0, total_risk))
        
        details = {
            'failure_probability': failure_probability,
            'failure_cost': failure_cost,
            'base_risk': base_risk,
            'uncertainty_count': len(uncertainty_factors),
            'uncertainty_factors': uncertainty_factors,
            'mitigation_count': len(mitigation_plans),
            'mitigation_plans': mitigation_plans,
            'risk_level': self._get_risk_level(total_risk)
        }
        
        return total_risk, details
    
    def calculate_reversibility(
        self,
        can_undo: bool,                  # 是否可撤销
        undo_cost: float,                # 撤销成本
        time_to_undo: int,               # 撤销所需时间（天）
        reputation_impact: float         # 对声誉的影响 0-1
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算可逆性得分
        
        可逆性越高，决策风险越低
        
        Returns:
            (可逆性得分 0-1, 详细分析)
        """
        if not can_undo:
            reversibility = 0.0
        else:
            # 撤销成本越低越好
            cost_factor = 1 - min(1.0, undo_cost / 10.0)
            
            # 撤销时间越短越好
            time_factor = 1 - min(1.0, time_to_undo / 365.0)
            
            # 声誉影响越小越好
            reputation_factor = 1 - reputation_impact
            
            reversibility = (
                cost_factor * 0.4 +
                time_factor * 0.3 +
                reputation_factor * 0.3
            )
        
        details = {
            'can_undo': can_undo,
            'undo_cost': undo_cost,
            'time_to_undo_days': time_to_undo,
            'reputation_impact': reputation_impact,
            'reversibility_level': self._get_reversibility_level(reversibility)
        }
        
        return reversibility, details
    
    def calculate_alignment(
        self,
        user_goals: List[str],           # 用户目标
        option_outcomes: List[str],      # 选项可能结果
        user_values: Dict[str, float],   # 用户价值观权重
        option_values: Dict[str, float]  # 选项体现的价值
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算目标一致性得分
        
        基于：
        1. 与用户目标的匹配度
        2. 与用户价值观的一致性
        
        Returns:
            (一致性得分 0-1, 详细分析)
        """
        # 1. 目标匹配度（简单文本匹配）
        goal_matches = []
        for goal in user_goals:
            for outcome in option_outcomes:
                if any(word in outcome.lower() for word in goal.lower().split()):
                    goal_matches.append(goal)
                    break
        
        goal_alignment = len(goal_matches) / len(user_goals) if user_goals else 0.5
        
        # 2. 价值观一致性
        value_alignment_scores = []
        for value, user_weight in user_values.items():
            option_weight = option_values.get(value, 0)
            # 计算加权差异
            alignment = 1 - abs(user_weight - option_weight)
            value_alignment_scores.append(alignment * user_weight)
        
        value_alignment = sum(value_alignment_scores) / sum(user_values.values()) if user_values else 0.5
        
        # 综合一致性
        total_alignment = goal_alignment * 0.6 + value_alignment * 0.4
        
        details = {
            'goal_alignment': goal_alignment,
            'matched_goals': goal_matches,
            'unmatched_goals': list(set(user_goals) - set(goal_matches)),
            'value_alignment': value_alignment,
            'value_details': {
                value: {
                    'user_weight': user_weight,
                    'option_weight': option_values.get(value, 0),
                    'alignment': 1 - abs(user_weight - option_values.get(value, 0))
                }
                for value, user_weight in user_values.items()
            }
        }
        
        return total_alignment, details
    
    def compare_options(
        self,
        options: List[DecisionOption],
        user_weights: Optional[Dict[DecisionDimension, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        对比多个选项
        
        Returns:
            排序后的选项列表，包含得分和详细分析
        """
        results = []
        
        for option in options:
            total_score, dimension_scores = self.calculate_option_score(option, user_weights)
            
            results.append({
                'option': option,
                'total_score': total_score,
                'dimension_scores': dimension_scores,
                'rank': 0  # 稍后填充
            })
        
        # 按总分排序
        results.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 填充排名
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        return results
    
    def identify_dominant_option(
        self,
        options: List[DecisionOption]
    ) -> Optional[str]:
        """
        识别占优选项（在所有维度都不差于其他选项）
        
        Returns:
            占优选项的ID，如果没有则返回None
        """
        if len(options) < 2:
            return options[0].id if options else None
        
        for option_a in options:
            is_dominant = True
            
            for option_b in options:
                if option_a.id == option_b.id:
                    continue
                
                # 检查是否在所有维度都不差于option_b
                if (option_a.feasibility_score < option_b.feasibility_score or
                    option_a.benefit_score < option_b.benefit_score or
                    option_a.risk_score > option_b.risk_score or
                    option_a.reversibility_score < option_b.reversibility_score or
                    option_a.alignment_score < option_b.alignment_score or
                    option_a.resource_score < option_b.resource_score):
                    is_dominant = False
                    break
            
            if is_dominant:
                return option_a.id
        
        return None
    
    def calculate_regret_matrix(
        self,
        options: List[DecisionOption],
        scenarios: List[Dict[str, float]]  # 不同情景下的收益
    ) -> Dict[str, Any]:
        """
        计算后悔矩阵（Minimax Regret）
        
        用于不确定性决策
        
        Returns:
            后悔分析结果
        """
        regret_matrix = {}
        
        for scenario_idx, scenario in enumerate(scenarios):
            scenario_name = f"scenario_{scenario_idx + 1}"
            
            # 找出该情景下的最佳收益
            max_benefit = max(scenario.get(opt.id, 0) for opt in options)
            
            # 计算每个选项的后悔值
            for option in options:
                benefit = scenario.get(option.id, 0)
                regret = max_benefit - benefit
                
                if option.id not in regret_matrix:
                    regret_matrix[option.id] = {}
                
                regret_matrix[option.id][scenario_name] = regret
        
        # 计算每个选项的最大后悔值
        max_regrets = {
            option_id: max(regrets.values())
            for option_id, regrets in regret_matrix.items()
        }
        
        # 找出最小化最大后悔的选项
        minimax_option = min(max_regrets.items(), key=lambda x: x[1])
        
        return {
            'regret_matrix': regret_matrix,
            'max_regrets': max_regrets,
            'recommended_option': minimax_option[0],
            'min_max_regret': minimax_option[1]
        }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """获取风险等级"""
        if risk_score < 0.3:
            return "低风险"
        elif risk_score < 0.6:
            return "中等风险"
        else:
            return "高风险"
    
    def _get_reversibility_level(self, reversibility_score: float) -> str:
        """获取可逆性等级"""
        if reversibility_score > 0.7:
            return "高度可逆"
        elif reversibility_score > 0.4:
            return "部分可逆"
        else:
            return "难以撤销"


# 示例使用
if __name__ == "__main__":
    engine = CoreDecisionEngine()
    
    # 创建两个决策选项
    option1 = DecisionOption(
        id="opt1",
        title="转行做产品经理",
        description="从技术转产品",
        feasibility_score=0.6,
        benefit_score=0.7,
        risk_score=0.5,
        reversibility_score=0.6,
        alignment_score=0.8,
        resource_score=0.5
    )
    
    option2 = DecisionOption(
        id="opt2",
        title="继续做技术深耕",
        description="在当前领域深入发展",
        feasibility_score=0.9,
        benefit_score=0.6,
        risk_score=0.3,
        reversibility_score=0.8,
        alignment_score=0.6,
        resource_score=0.8
    )
    
    # 对比选项
    results = engine.compare_options([option1, option2])
    
    print("=" * 60)
    print("决策对比结果")
    print("=" * 60)
    
    for result in results:
        option = result['option']
        print(f"\n排名 {result['rank']}: {option.title}")
        print(f"总分: {result['total_score']:.2f}")
        print(f"各维度得分:")
        for dim, score in result['dimension_scores'].items():
            print(f"  {dim}: {score:.2f}")
