"""
职业决策多Agent评估框架

整合：
1. 职业星图（知识图谱）- 提供真实数据
2. 职业决策算法 - 提供量化分析
3. 三条路径推演 - 提供时间线模拟

架构：
每条决策路径 → 5个评估Agent独立演化 → 在关键节点交互 → 生成综合评估
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """单个Agent在某个时间点的状态"""
    month: int
    score: float  # 0-100
    status: str  # 'good' | 'warning' | 'critical'
    key_metrics: Dict[str, Any]
    changes: List[str]  # 本月变化
    risks: List[str]  # 风险点
    opportunities: List[str]  # 机会点


@dataclass
class AgentInteraction:
    """Agent之间的交互"""
    month: int
    agents: List[str]  # 参与交互的Agent
    interaction_type: str  # 'conflict' | 'synergy' | 'dependency'
    description: str
    impact: str  # 对决策的影响


@dataclass
class DecisionPoint:
    """关键决策点"""
    month: int
    trigger_agent: str  # 触发的Agent
    description: str
    options: List[str]  # 可选行动
    recommendation: str
    agent_votes: Dict[str, str]  # 各Agent的建议


class BaseCareerAgent:
    """职业评估Agent基类"""
    
    def __init__(self, agent_name: str, user_id: str):
        self.agent_name = agent_name
        self.user_id = user_id
        self.history: List[AgentState] = []
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """
        演化到下一个月
        
        Args:
            month: 当前月份
            context: 决策上下文（选项、用户信息等）
            other_agents_state: 其他Agent的当前状态
        
        Returns:
            当前月的状态
        """
        raise NotImplementedError
    
    def get_current_state(self) -> Optional[AgentState]:
        """获取当前状态"""
        return self.history[-1] if self.history else None
    
    def calculate_trend(self, months: int = 3) -> str:
        """计算趋势"""
        if len(self.history) < months:
            return "insufficient_data"
        
        recent = self.history[-months:]
        scores = [s.score for s in recent]
        
        if all(scores[i] <= scores[i+1] for i in range(len(scores)-1)):
            return "improving"
        elif all(scores[i] >= scores[i+1] for i in range(len(scores)-1)):
            return "declining"
        else:
            return "fluctuating"



class SkillDevelopmentAgent(BaseCareerAgent):
    """技能发展Agent - 基于技能树和学习曲线"""
    
    def __init__(self, user_id: str):
        super().__init__("skill_development", user_id)
        self.current_skills = {}  # {skill_name: level}
        self.target_skills = {}  # {skill_name: target_level}
        self.learning_progress = {}  # {skill_name: progress}
        self.skill_gap = 0.0
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取个人资本数据"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 从上下文获取已提取的个人资本，避免重复提取
            personal_capital = context.get('personal_capital')
            
            if personal_capital is None:
                # 如果上下文中没有，才自己提取（兼容旧代码）
                logger.warning(f"[SkillAgent] personal_capital为None，将重新提取（不应该发生！）")
                from backend.decision_algorithm.career_decision_algorithm import (
                    KnowledgeGraphCareerIntegration
                )
                kg_integration = KnowledgeGraphCareerIntegration(self.user_id)
                personal_capital = kg_integration.extract_personal_capital_from_kg()
            else:
                logger.info(f"[SkillAgent] 使用共享的personal_capital，跳过提取")
            
            # 提取当前技能
            for skill in personal_capital.skills:
                self.current_skills[skill.name] = skill.level
            
            # 从上下文获取目标技能
            required_skills = context.get('required_skills', [])
            for skill_name in required_skills:
                self.target_skills[skill_name] = 8.0  # 目标水平
                current_level = self.current_skills.get(skill_name, 0)
                self.learning_progress[skill_name] = current_level / 8.0
            
            # 计算技能差距
            if self.target_skills:
                gaps = []
                for skill_name, target_level in self.target_skills.items():
                    current = self.current_skills.get(skill_name, 0)
                    gaps.append(max(0, target_level - current))
                self.skill_gap = sum(gaps) / len(gaps)
            
        except Exception as e:
            logger.error(f"[SkillAgent] 初始化失败: {e}")
            self.skill_gap = 5.0
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """模拟技能发展"""
        
        changes = []
        risks = []
        opportunities = []
        
        # 学习进度（每月提升）
        learning_hours_per_month = context.get('learning_hours_per_month', 40)
        learning_efficiency = 1.0
        
        # 检查其他Agent状态影响学习效率
        psychological_state = other_agents_state.get('psychological')
        if psychological_state:
            if psychological_state.status == 'critical':
                learning_efficiency *= 0.5
                changes.append("心理压力大，学习效率降低50%")
            elif psychological_state.status == 'good':
                learning_efficiency *= 1.2
                changes.append("心理状态好，学习效率提升20%")
        
        financial_state = other_agents_state.get('financial')
        if financial_state and financial_state.status == 'critical':
            learning_efficiency *= 0.7
            changes.append("财务压力影响学习专注度")
        
        # 更新技能进度
        for skill_name, target_level in self.target_skills.items():
            current_level = self.current_skills.get(skill_name, 0)
            
            if current_level < target_level:
                # 学习曲线：前期快，后期慢
                learning_rate = 0.3 * (1 - current_level / 10) * learning_efficiency
                progress = learning_rate * (learning_hours_per_month / 40)
                
                new_level = min(target_level, current_level + progress)
                self.current_skills[skill_name] = new_level
                self.learning_progress[skill_name] = new_level / target_level
                
                changes.append(
                    f"{skill_name}: {current_level:.1f} → {new_level:.1f} "
                    f"(进度{self.learning_progress[skill_name]:.0%})"
                )
        
        # 重新计算技能差距
        if self.target_skills:
            gaps = []
            for skill_name, target_level in self.target_skills.items():
                current = self.current_skills.get(skill_name, 0)
                gaps.append(max(0, target_level - current))
            self.skill_gap = sum(gaps) / len(gaps)
        
        # 计算得分（基于技能达标程度）
        avg_completion = 0.0
        if self.target_skills:
            completion_rates = [
                self.learning_progress.get(skill, 0)
                for skill in self.target_skills.keys()
            ]
            avg_completion = sum(completion_rates) / len(completion_rates)
            score = avg_completion * 100
        else:
            score = 50
        
        # 识别风险
        if score < 30:
            risks.append("技能差距过大，需要加速学习")
        elif score < 50:
            risks.append("技能进度偏慢，可能影响求职时机")
        
        if month >= 6 and score < 70:
            risks.append("学习时间已过半，但技能未达标")
        
        # 识别机会
        if score >= 70:
            opportunities.append("技能基本达标，可以开始投简历")
        
        if score >= 85:
            opportunities.append("技能优势明显，竞争力强")
        
        # 检查与其他Agent的协同
        network_state = other_agents_state.get('career_network')
        if network_state and network_state.opportunities and score >= 60:
            opportunities.append("技能+人脉双优势，求职成功率高")
        
        # 状态
        if score >= 70:
            status = 'good'
        elif score >= 40:
            status = 'warning'
        else:
            status = 'critical'
        
        state = AgentState(
            month=month,
            score=score,
            status=status,
            key_metrics={
                'skill_gap': f"{self.skill_gap:.1f}",
                'avg_completion': f"{avg_completion:.0%}",
                'learning_efficiency': f"{learning_efficiency:.0%}",
                'skills_count': len(self.target_skills)
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class CareerNetworkAgent(BaseCareerAgent):
    """职业人脉Agent - 基于社会资本理论"""
    
    def __init__(self, user_id: str):
        super().__init__("career_network", user_id)
        self.network_size = 0
        self.network_quality = 0.5
        self.referral_opportunities = 0
        self.industry_connections = 0
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取人脉数据"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 从上下文获取已提取的个人资本，避免重复提取
            personal_capital = context.get('personal_capital')
            
            if personal_capital is None:
                # 如果上下文中没有，才自己提取（兼容旧代码）
                logger.warning(f"[NetworkAgent] personal_capital为None，将重新提取（不应该发生！）")
                from backend.decision_algorithm.career_decision_algorithm import (
                    KnowledgeGraphCareerIntegration
                )
                kg_integration = KnowledgeGraphCareerIntegration(self.user_id)
                personal_capital = kg_integration.extract_personal_capital_from_kg()
            else:
                logger.info(f"[NetworkAgent] 使用共享的personal_capital，跳过提取")
            
            self.network_size = personal_capital.network_size
            self.network_quality = personal_capital.network_quality
            
            # 估算行业人脉
            target_industry = context.get('target_industry', '')
            if target_industry:
                self.industry_connections = int(self.network_size * 0.3)
            
        except Exception as e:
            logger.error(f"[NetworkAgent] 初始化失败: {e}")
            self.network_size = 50
            self.network_quality = 0.5
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """模拟人脉发展"""
        
        changes = []
        risks = []
        opportunities = []
        
        # 人脉拓展（每月）
        networking_effort = context.get('networking_hours_per_month', 10)
        
        # 检查心理状态影响社交意愿
        psychological_state = other_agents_state.get('psychological')
        if psychological_state:
            if psychological_state.status == 'critical':
                networking_effort *= 0.5
                changes.append("心理压力大，社交意愿降低")
            elif psychological_state.status == 'good':
                networking_effort *= 1.3
                changes.append("心理状态好，社交活跃")
        
        # 人脉增长
        new_connections = int(networking_effort / 5)  # 每5小时认识1人
        self.network_size += new_connections
        
        if new_connections > 0:
            changes.append(f"新增人脉: {new_connections}人，总计{self.network_size}人")
        
        # 人脉质量提升（通过深度交流）
        if networking_effort >= 10:
            self.network_quality = min(1.0, self.network_quality + 0.02)
            changes.append(f"人脉质量提升至{self.network_quality:.0%}")
        
        # 行业人脉增长
        target_industry = context.get('target_industry', '')
        if target_industry and new_connections > 0:
            industry_new = int(new_connections * 0.4)
            self.industry_connections += industry_new
            if industry_new > 0:
                changes.append(f"行业人脉+{industry_new}，总计{self.industry_connections}人")
        
        # 内推机会（基于人脉质量和数量）
        referral_prob = self.network_quality * min(1.0, self.industry_connections / 20)
        
        import random
        if random.random() < referral_prob:
            self.referral_opportunities += 1
            opportunities.append(f"获得内推机会 (累计{self.referral_opportunities}个)")
        
        # 计算得分
        network_score = min(100, (self.network_size / 100) * 40)
        quality_score = self.network_quality * 30
        industry_score = min(30, (self.industry_connections / 20) * 30)
        
        score = network_score + quality_score + industry_score
        
        # 识别风险
        if self.network_size < 30:
            risks.append("人脉规模太小，求职渠道有限")
        
        if self.industry_connections < 5:
            risks.append("行业人脉不足，缺少内推机会")
        
        if self.network_quality < 0.4:
            risks.append("人脉质量低，需要深度经营")
        
        # 识别机会
        if self.referral_opportunities > 0:
            opportunities.append(f"有{self.referral_opportunities}个内推机会，求职成功率提升")
        
        if self.industry_connections >= 15:
            opportunities.append("行业人脉充足，信息渠道畅通")
        
        if self.network_quality >= 0.7:
            opportunities.append("人脉质量高，可获得高质量推荐")
        
        # 检查与技能Agent的协同
        skill_state = other_agents_state.get('skill_development')
        if skill_state and skill_state.score >= 70 and self.referral_opportunities > 0:
            opportunities.append("技能+内推双优势，强烈建议开始求职")
        
        # 状态
        if score >= 60:
            status = 'good'
        elif score >= 35:
            status = 'warning'
        else:
            status = 'critical'
        
        state = AgentState(
            month=month,
            score=score,
            status=status,
            key_metrics={
                'network_size': f"{self.network_size}人",
                'network_quality': f"{self.network_quality:.0%}",
                'industry_connections': f"{self.industry_connections}人",
                'referral_opportunities': self.referral_opportunities
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class FinancialStatusAgent(BaseCareerAgent):
    """财务状况Agent - 基于ROI算法"""
    
    def __init__(self, user_id: str):
        super().__init__("financial", user_id)
        self.savings = 0.0
        self.monthly_income = 0.0
        self.monthly_expenses = 0.0
        self.runway_months = 0.0
        self.total_investment = 0.0
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取财务数据"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 从上下文获取已提取的个人资本，避免重复提取
            personal_capital = context.get('personal_capital')
            
            if personal_capital is None:
                # 如果上下文中没有，才自己提取（兼容旧代码）
                logger.warning(f"[FinancialAgent] personal_capital为None，将重新提取（不应该发生！）")
                from backend.decision_algorithm.career_decision_algorithm import (
                    KnowledgeGraphCareerIntegration
                )
                kg_integration = KnowledgeGraphCareerIntegration(self.user_id)
                personal_capital = kg_integration.extract_personal_capital_from_kg()
            else:
                logger.info(f"[FinancialAgent] 使用共享的personal_capital，跳过提取")
            
            self.savings = personal_capital.savings
            self.monthly_expenses = personal_capital.monthly_expenses
            self.runway_months = personal_capital.financial_runway_months
            
            # 从上下文获取当前收入
            self.monthly_income = context.get('current_salary', 25000)
            
        except Exception as e:
            logger.error(f"[FinancialAgent] 初始化失败: {e}")
            self.savings = 50000
            self.monthly_income = 25000
            self.monthly_expenses = 15000
            self.runway_months = 6
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """模拟财务状况变化"""
        
        changes = []
        risks = []
        opportunities = []
        
        # 学习成本
        learning_cost = context.get('learning_cost_per_month', 2000)
        self.total_investment += learning_cost
        
        # 收入变化（转换期可能降低）
        if month <= 6:
            # 转换期收入可能降低30%
            income_reduction = self.monthly_income * 0.3
            actual_income = self.monthly_income - income_reduction
            changes.append(f"转换期收入降低 ¥{income_reduction:.0f}")
        else:
            actual_income = self.monthly_income
        
        # 月度现金流
        monthly_cashflow = actual_income - self.monthly_expenses - learning_cost
        self.savings += monthly_cashflow
        
        changes.append(
            f"本月现金流: ¥{monthly_cashflow:.0f} "
            f"(收入¥{actual_income:.0f} - 支出¥{self.monthly_expenses:.0f} - 学习¥{learning_cost:.0f})"
        )
        changes.append(f"储蓄余额: ¥{self.savings:.0f}")
        
        # 更新跑道
        if self.monthly_expenses > 0:
            self.runway_months = self.savings / self.monthly_expenses
        
        # 计算得分
        runway_score = min(100, (self.runway_months / 12) * 100)
        cashflow_score = 50 if monthly_cashflow >= 0 else 20
        score = (runway_score * 0.6 + cashflow_score * 0.4)
        
        # 识别风险
        if self.runway_months < 3:
            risks.append(f"财务跑道仅剩{self.runway_months:.1f}个月，建议暂停转换")
        elif self.runway_months < 6:
            risks.append(f"财务跑道{self.runway_months:.1f}个月，需要控制支出")
        
        if monthly_cashflow < 0:
            risks.append(f"月度现金流为负 ¥{monthly_cashflow:.0f}，储蓄在减少")
        
        # 识别机会
        if self.savings > self.monthly_expenses * 12:
            opportunities.append("财务储备充足，可以承担更大风险")
        
        # 检查其他Agent状态
        skill_state = other_agents_state.get('skill_development')
        if skill_state and skill_state.score >= 70 and self.runway_months >= 6:
            opportunities.append("技能达标且财务稳定，建议开始求职")
        
        # 状态
        if score >= 60:
            status = 'good'
        elif score >= 30:
            status = 'warning'
        else:
            status = 'critical'
        
        state = AgentState(
            month=month,
            score=score,
            status=status,
            key_metrics={
                'savings': f"¥{self.savings:.0f}",
                'runway_months': f"{self.runway_months:.1f}个月",
                'monthly_cashflow': f"¥{monthly_cashflow:.0f}",
                'total_investment': f"¥{self.total_investment:.0f}"
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class PsychologicalCapitalAgent(BaseCareerAgent):
    """心理资本Agent - 基于心理资本模型"""
    
    def __init__(self, user_id: str):
        super().__init__("psychological", user_id)
        self.self_efficacy = 0.7  # 自我效能感
        self.resilience = 0.7  # 韧性
        self.stress_level = 0.3  # 压力水平
        self.motivation = 0.8  # 动力
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取心理资本数据"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 从上下文获取已提取的个人资本，避免重复提取
            personal_capital = context.get('personal_capital')
            
            if personal_capital is None:
                # 如果上下文中没有，才自己提取（兼容旧代码）
                logger.warning(f"[PsychologicalAgent] personal_capital为None，将重新提取（不应该发生！）")
                from backend.decision_algorithm.career_decision_algorithm import (
                    KnowledgeGraphCareerIntegration
                )
                kg_integration = KnowledgeGraphCareerIntegration(self.user_id)
                personal_capital = kg_integration.extract_personal_capital_from_kg()
            else:
                logger.info(f"[PsychologicalAgent] 使用共享的personal_capital，跳过提取")
            
            self.self_efficacy = personal_capital.self_efficacy
            self.resilience = personal_capital.resilience
            
        except Exception as e:
            logger.error(f"[PsychologicalAgent] 初始化失败: {e}")
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """模拟心理状态变化"""
        
        changes = []
        risks = []
        opportunities = []
        
        # 检查其他Agent状态影响心理
        skill_state = other_agents_state.get('skill_development')
        financial_state = other_agents_state.get('financial')
        network_state = other_agents_state.get('career_network')
        
        # 技能进展影响自信心
        if skill_state:
            if skill_state.status == 'good':
                self.self_efficacy = min(1.0, self.self_efficacy + 0.05)
                changes.append("技能进展顺利，自信心提升")
            elif skill_state.status == 'critical':
                self.self_efficacy = max(0.3, self.self_efficacy - 0.05)
                changes.append("技能进展缓慢，自信心下降")
        
        # 财务压力影响压力水平
        if financial_state:
            if financial_state.status == 'critical':
                self.stress_level = min(1.0, self.stress_level + 0.1)
                changes.append("财务压力增大")
            elif financial_state.status == 'good':
                self.stress_level = max(0.1, self.stress_level - 0.05)
                changes.append("财务稳定，压力减轻")
        
        # 人脉进展影响动力
        if network_state and network_state.opportunities:
            self.motivation = min(1.0, self.motivation + 0.05)
            changes.append("获得人脉机会，动力增强")
        
        # 时间因素
        if month >= 6:
            # 长期转换可能降低动力
            self.motivation = max(0.4, self.motivation - 0.02)
            if self.motivation < 0.6:
                changes.append("转换时间较长，动力有所下降")
        
        # 计算得分
        efficacy_score = self.self_efficacy * 30
        resilience_score = self.resilience * 30
        stress_score = (1 - self.stress_level) * 20
        motivation_score = self.motivation * 20
        
        score = efficacy_score + resilience_score + stress_score + motivation_score
        
        # 识别风险
        if self.stress_level > 0.7:
            risks.append("压力过大，可能影响决策质量")
        
        if self.self_efficacy < 0.5:
            risks.append("自信心不足，建议寻求支持")
        
        if self.motivation < 0.5:
            risks.append("动力不足，可能中途放弃")
        
        # 识别机会
        if self.self_efficacy > 0.8 and self.stress_level < 0.4:
            opportunities.append("心理状态良好，适合迎接挑战")
        
        # 状态
        if score >= 70:
            status = 'good'
        elif score >= 50:
            status = 'warning'
        else:
            status = 'critical'
        
        state = AgentState(
            month=month,
            score=score,
            status=status,
            key_metrics={
                'self_efficacy': f"{self.self_efficacy:.1%}",
                'resilience': f"{self.resilience:.1%}",
                'stress_level': f"{self.stress_level:.1%}",
                'motivation': f"{self.motivation:.1%}"
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class MarketEnvironmentAgent(BaseCareerAgent):
    """市场环境Agent - 基于外部数据"""
    
    def __init__(self, user_id: str):
        super().__init__("market_environment", user_id)
        self.job_demand_index = 0.7
        self.salary_trend = 0.0
        self.industry_growth = 0.15
        self.competition_level = 0.5
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从外部数据源获取市场数据"""
        target_role = context.get('target_role', '')
        
        # TODO: 集成真实的招聘API数据
        # 这里使用模拟数据
        self.job_demand_index = 0.75
        self.industry_growth = 0.15
        self.competition_level = 0.6
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """模拟市场环境变化"""
        
        changes = []
        risks = []
        opportunities = []
        
        # 模拟市场波动
        import random
        market_change = random.uniform(-0.05, 0.1)
        self.job_demand_index = max(0.3, min(1.0, self.job_demand_index + market_change))
        
        if market_change > 0.05:
            changes.append(f"岗位需求增长 {market_change:.1%}")
            opportunities.append("市场需求旺盛，求职时机好")
        elif market_change < -0.03:
            changes.append(f"岗位需求下降 {market_change:.1%}")
            risks.append("市场需求下降，竞争加剧")
        
        # 薪资趋势
        salary_change = random.uniform(-0.02, 0.03)
        self.salary_trend += salary_change
        changes.append(f"薪资趋势: {self.salary_trend:+.1%}")
        
        # 季节性因素
        if month in [3, 4, 9, 10]:  # 招聘旺季
            opportunities.append("当前是招聘旺季，机会较多")
        
        # 计算得分
        demand_score = self.job_demand_index * 40
        growth_score = min(30, self.industry_growth * 100)
        competition_score = (1 - self.competition_level) * 30
        
        score = demand_score + growth_score + competition_score
        
        # 识别风险
        if self.job_demand_index < 0.5:
            risks.append("市场需求低迷，求职困难")
        
        if self.competition_level > 0.7:
            risks.append("竞争激烈，需要更强的竞争力")
        
        # 状态
        if score >= 70:
            status = 'good'
        elif score >= 50:
            status = 'warning'
        else:
            status = 'critical'
        
        state = AgentState(
            month=month,
            score=score,
            status=status,
            key_metrics={
                'job_demand_index': f"{self.job_demand_index:.1%}",
                'salary_trend': f"{self.salary_trend:+.1%}",
                'industry_growth': f"{self.industry_growth:.1%}",
                'competition_level': f"{self.competition_level:.1%}"
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state



class MultiAgentCareerEvaluator:
    """多Agent职业决策评估器 - 协调5个Agent"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.personal_capital = None  # 缓存个人资本，避免重复提取
        
        # 初始化5个Agent
        self.agents = {
            'skill_development': SkillDevelopmentAgent(user_id),
            'career_network': CareerNetworkAgent(user_id),
            'financial': FinancialStatusAgent(user_id),
            'psychological': PsychologicalCapitalAgent(user_id),
            'market_environment': MarketEnvironmentAgent(user_id)
        }
        
        self.interactions: List[AgentInteraction] = []
        self.decision_points: List[DecisionPoint] = []
    
    async def initialize_all_agents(self, context: Dict[str, Any]):
        """初始化所有Agent - 优化：只提取一次个人资本"""
        # 只提取一次个人资本
        if self.personal_capital is None:
            try:
                from backend.decision_algorithm.career_decision_algorithm import (
                    KnowledgeGraphCareerIntegration
                )
                logger.info(f"[MultiAgent] 开始提取个人资本...")
                kg_integration = KnowledgeGraphCareerIntegration(self.user_id)
                self.personal_capital = kg_integration.extract_personal_capital_from_kg()
                logger.info(f"[MultiAgent] 个人资本提取完成")
            except Exception as e:
                logger.error(f"[MultiAgent] 个人资本提取失败: {e}")
                self.personal_capital = None
        
        # 将个人资本传递给所有Agent
        context_with_capital = {**context, 'personal_capital': self.personal_capital}
        
        for agent_name, agent in self.agents.items():
            try:
                await agent.initialize(context_with_capital)
                logger.info(f"[MultiAgent] {agent_name} 初始化成功")
            except Exception as e:
                logger.error(f"[MultiAgent] {agent_name} 初始化失败: {e}")
    
    async def simulate_month(
        self,
        month: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        模拟某个月的所有Agent状态
        
        Returns:
            {
                'month': 1,
                'agents_state': {'skill_development': AgentState, ...},
                'interactions': [...],
                'decision_points': [...],
                'overall_assessment': {...}
            }
        """
        
        # 第一轮：所有Agent独立演化
        agents_state = {}
        for agent_name, agent in self.agents.items():
            state = await agent.evolve(month, context, agents_state)
            agents_state[agent_name] = state
        
        # 第二轮：检测Agent间的交互
        interactions = self._detect_interactions(month, agents_state)
        self.interactions.extend(interactions)
        
        # 第三轮：识别关键决策点
        decision_points = self._identify_decision_points(month, agents_state)
        self.decision_points.extend(decision_points)
        
        # 综合评估
        overall_assessment = self._calculate_overall_assessment(agents_state)
        
        return {
            'month': month,
            'agents_state': agents_state,
            'interactions': interactions,
            'decision_points': decision_points,
            'overall_assessment': overall_assessment
        }
    
    def _detect_interactions(
        self,
        month: int,
        agents_state: Dict[str, AgentState]
    ) -> List[AgentInteraction]:
        """检测Agent之间的交互"""
        interactions = []
        
        skill = agents_state.get('skill_development')
        network = agents_state.get('career_network')
        financial = agents_state.get('financial')
        psychological = agents_state.get('psychological')
        market = agents_state.get('market_environment')
        
        # 冲突检测
        if skill and skill.score >= 70 and financial and financial.score < 30:
            interactions.append(AgentInteraction(
                month=month,
                agents=['skill_development', 'financial'],
                interaction_type='conflict',
                description='技能已达标但财务压力大',
                impact='建议延迟求职，先积累储蓄'
            ))
        
        if psychological and psychological.score < 40 and skill and skill.score < 50:
            interactions.append(AgentInteraction(
                month=month,
                agents=['psychological', 'skill_development'],
                interaction_type='conflict',
                description='心理压力大且技能进展慢',
                impact='双重压力，建议调整节奏或暂停'
            ))
        
        # 协同检测
        if skill and skill.score >= 70 and network and network.score >= 60:
            interactions.append(AgentInteraction(
                month=month,
                agents=['skill_development', 'career_network'],
                interaction_type='synergy',
                description='技能达标且人脉充足',
                impact='求职成功率高，建议积极行动'
            ))
        
        if financial and financial.score >= 70 and psychological and psychological.score >= 70:
            interactions.append(AgentInteraction(
                month=month,
                agents=['financial', 'psychological'],
                interaction_type='synergy',
                description='财务稳定且心理状态好',
                impact='可以承担更大风险，尝试更好的机会'
            ))
        
        # 依赖检测
        if market and market.score < 50 and skill and skill.score >= 80:
            interactions.append(AgentInteraction(
                month=month,
                agents=['market_environment', 'skill_development'],
                interaction_type='dependency',
                description='市场低迷但技能优势明显',
                impact='需要更强的技能优势来对抗市场不利'
            ))
        
        return interactions
    
    def _identify_decision_points(
        self,
        month: int,
        agents_state: Dict[str, AgentState]
    ) -> List[DecisionPoint]:
        """识别关键决策点"""
        decision_points = []
        
        skill = agents_state.get('skill_development')
        network = agents_state.get('career_network')
        financial = agents_state.get('financial')
        psychological = agents_state.get('psychological')
        market = agents_state.get('market_environment')
        
        # 决策点1：是否开始投简历
        if month >= 3 and skill and skill.score >= 70:
            agent_votes = {}
            
            if skill.score >= 70:
                agent_votes['skill'] = '支持：技能已达标'
            
            if financial and financial.score >= 50:
                agent_votes['financial'] = '支持：财务可承受'
            elif financial and financial.score < 30:
                agent_votes['financial'] = '反对：财务压力太大'
            
            if network and network.score >= 60:
                agent_votes['network'] = '支持：有内推机会'
            
            if psychological and psychological.score >= 60:
                agent_votes['psychological'] = '支持：心理准备充分'
            elif psychological and psychological.score < 40:
                agent_votes['psychological'] = '反对：心理压力过大'
            
            if market and market.score >= 60:
                agent_votes['market'] = '支持：市场时机好'
            
            # 统计投票
            support_count = sum(1 for v in agent_votes.values() if '支持' in v)
            oppose_count = sum(1 for v in agent_votes.values() if '反对' in v)
            
            if support_count >= 3:
                recommendation = '建议开始投简历'
            elif oppose_count >= 2:
                recommendation = '建议再等待1-2个月'
            else:
                recommendation = '可以尝试投少量简历测试市场'
            
            decision_points.append(DecisionPoint(
                month=month,
                trigger_agent='skill_development',
                description='技能达标，是否开始求职？',
                options=[
                    '立即开始投简历',
                    '再学习1个月',
                    '先投少量简历测试'
                ],
                recommendation=recommendation,
                agent_votes=agent_votes
            ))
        
        # 决策点2：财务危机
        if financial and financial.score < 20:
            decision_points.append(DecisionPoint(
                month=month,
                trigger_agent='financial',
                description='财务跑道不足，需要紧急决策',
                options=[
                    '暂停转换，先工作积累',
                    '降低学习投入，延长跑道',
                    '寻求家人支持',
                    '加速求职进程'
                ],
                recommendation='建议暂停或降低投入',
                agent_votes={
                    'financial': '紧急：必须采取行动',
                    'psychological': '警告：财务压力影响心理',
                    'skill': '建议：可以降低学习强度'
                }
            ))
        
        # 决策点3：心理崩溃风险
        if psychological and psychological.score < 30:
            decision_points.append(DecisionPoint(
                month=month,
                trigger_agent='psychological',
                description='心理压力过大，需要调整',
                options=[
                    '暂停1个月休息',
                    '降低目标和压力',
                    '寻求心理咨询',
                    '调整学习节奏'
                ],
                recommendation='建议暂停或寻求支持',
                agent_votes={
                    'psychological': '紧急：需要休息',
                    'skill': '理解：可以放慢节奏',
                    'financial': '关注：休息会增加财务压力'
                }
            ))
        
        return decision_points
    
    def _calculate_overall_assessment(
        self,
        agents_state: Dict[str, AgentState]
    ) -> Dict[str, Any]:
        """计算综合评估"""
        
        # 计算加权平均分
        weights = {
            'skill_development': 0.3,
            'career_network': 0.2,
            'financial': 0.2,
            'psychological': 0.15,
            'market_environment': 0.15
        }
        
        total_score = 0
        for agent_name, weight in weights.items():
            state = agents_state.get(agent_name)
            if state:
                total_score += state.score * weight
        
        # 确定整体状态
        if total_score >= 70:
            overall_status = 'good'
            status_text = '进展顺利'
        elif total_score >= 50:
            overall_status = 'warning'
            status_text = '需要关注'
        else:
            overall_status = 'critical'
            status_text = '存在风险'
        
        # 收集所有风险和机会
        all_risks = []
        all_opportunities = []
        
        for state in agents_state.values():
            all_risks.extend(state.risks)
            all_opportunities.extend(state.opportunities)
        
        # 找出最弱的环节
        weakest_agent = min(
            agents_state.items(),
            key=lambda x: x[1].score
        )
        
        # 找出最强的环节
        strongest_agent = max(
            agents_state.items(),
            key=lambda x: x[1].score
        )
        
        return {
            'overall_score': total_score,
            'overall_status': overall_status,
            'status_text': status_text,
            'weakest_dimension': {
                'name': weakest_agent[0],
                'score': weakest_agent[1].score,
                'status': weakest_agent[1].status
            },
            'strongest_dimension': {
                'name': strongest_agent[0],
                'score': strongest_agent[1].score,
                'status': strongest_agent[1].status
            },
            'total_risks': len(all_risks),
            'total_opportunities': len(all_opportunities),
            'key_risks': all_risks[:3],  # 前3个风险
            'key_opportunities': all_opportunities[:3]  # 前3个机会
        }
    
    async def simulate_full_timeline(
        self,
        context: Dict[str, Any],
        months: int = 12
    ) -> Dict[str, Any]:
        """
        模拟完整的时间线（12个月）
        
        Returns:
            {
                'timeline': [月度数据],
                'summary': 总结,
                'all_interactions': 所有交互,
                'all_decision_points': 所有决策点
            }
        """
        
        # 初始化所有Agent
        await self.initialize_all_agents(context)
        
        timeline = []
        
        for month in range(1, months + 1):
            month_data = await self.simulate_month(month, context)
            timeline.append(month_data)
            
            logger.info(
                f"[MultiAgent] 第{month}月模拟完成 - "
                f"综合得分: {month_data['overall_assessment']['overall_score']:.1f}"
            )
        
        # 生成总结
        summary = self._generate_summary(timeline)
        
        return {
            'timeline': timeline,
            'summary': summary,
            'all_interactions': self.interactions,
            'all_decision_points': self.decision_points
        }
    
    def _generate_summary(self, timeline: List[Dict]) -> Dict[str, Any]:
        """生成总结"""
        
        if not timeline:
            return {}
        
        first_month = timeline[0]
        last_month = timeline[-1]
        
        # 计算趋势
        first_score = first_month['overall_assessment']['overall_score']
        last_score = last_month['overall_assessment']['overall_score']
        score_change = last_score - first_score
        
        # 统计各Agent的趋势
        agent_trends = {}
        for agent_name in self.agents.keys():
            first_state = first_month['agents_state'].get(agent_name)
            last_state = last_month['agents_state'].get(agent_name)
            
            if first_state and last_state:
                change = last_state.score - first_state.score
                if change > 10:
                    trend = 'improving'
                elif change < -10:
                    trend = 'declining'
                else:
                    trend = 'stable'
                
                agent_trends[agent_name] = {
                    'trend': trend,
                    'change': change,
                    'final_score': last_state.score
                }
        
        # 关键里程碑
        milestones = []
        for month_data in timeline:
            if month_data['decision_points']:
                for dp in month_data['decision_points']:
                    milestones.append({
                        'month': dp.month,
                        'description': dp.description,
                        'recommendation': dp.recommendation
                    })
        
        return {
            'overall_trend': 'improving' if score_change > 10 else 'declining' if score_change < -10 else 'stable',
            'score_change': score_change,
            'final_score': last_score,
            'agent_trends': agent_trends,
            'total_interactions': len(self.interactions),
            'total_decision_points': len(self.decision_points),
            'key_milestones': milestones,
            'success_probability': self._estimate_success_probability(timeline)
        }
    
    def _estimate_success_probability(self, timeline: List[Dict]) -> float:
        """估算成功概率"""
        
        if not timeline:
            return 0.5
        
        last_month = timeline[-1]
        overall_score = last_month['overall_assessment']['overall_score']
        
        # 基础概率
        base_prob = overall_score / 100
        
        # 调整因素
        agents_state = last_month['agents_state']
        
        # 技能是关键
        skill_state = agents_state.get('skill_development')
        if skill_state and skill_state.score >= 80:
            base_prob += 0.1
        elif skill_state and skill_state.score < 50:
            base_prob -= 0.1
        
        # 财务和心理是约束
        financial_state = agents_state.get('financial')
        psychological_state = agents_state.get('psychological')
        
        if financial_state and financial_state.score < 30:
            base_prob -= 0.15
        
        if psychological_state and psychological_state.score < 30:
            base_prob -= 0.15
        
        return max(0.1, min(0.95, base_prob))
