"""
教育升学决策多Agent评估框架

整合：
1. 学校数据库（知识图谱）- 提供真实学校数据
2. 教育决策算法 - 提供量化分析
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
class EducationAgentState:
    """单个Agent在某个时间点的状态"""
    month: int
    score: float  # 0-100
    status: str  # 'good' | 'warning' | 'critical'
    key_metrics: Dict[str, Any]
    changes: List[str]
    risks: List[str]
    opportunities: List[str]


@dataclass
class AdmissionResult:
    """录取结果"""
    month: int
    school: str
    admitted: bool
    scholarship_offered: float  # 奖学金金额
    conditions: List[str]       # 录取条件


@dataclass
class ApplicationMilestone:
    """申请关键里程碑"""
    month: int
    milestone_type: str  # 'deadline' | 'interview' | 'result' | 'decision'
    school: str
    description: str
    status: str  # 'pending' | 'completed' | 'missed'


class BaseEducationAgent:
    """教育评估Agent基类"""
    
    def __init__(self, agent_name: str, user_id: str):
        self.agent_name = agent_name
        self.user_id = user_id
        self.history: List[EducationAgentState] = []
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, EducationAgentState]
    ) -> EducationAgentState:
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
    
    def get_current_state(self) -> Optional[EducationAgentState]:
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


class AcademicStrengthAgent(BaseEducationAgent):
    """学业实力Agent - 评估学业准备程度"""
    
    def __init__(self, user_id: str):
        super().__init__("academic_strength", user_id)
        self.gpa_score = 80.0
        self.test_score = 75.0
        self.research_score = 70.0
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取学业数据"""
        academic = context.get('academic_profile', {})
        self.gpa_score = academic.get('gpa', 80.0)
        self.test_score = academic.get('test_score', 75.0)
        self.research_score = academic.get('research_score', 70.0)
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, EducationAgentState]
    ) -> EducationAgentState:
        """每月演化"""
        # 模拟学习效果
        if month <= 3:  # 准备期
            self.gpa_score = min(100, self.gpa_score + 0.5)
            self.test_score = min(100, self.test_score + 1.0)
        elif month <= 6:  # 深化期
            self.research_score = min(100, self.research_score + 0.8)
        
        # 计算综合得分
        total_score = (
            self.gpa_score * 0.35 +
            self.test_score * 0.25 +
            self.research_score * 0.40
        )
        
        # 识别变化和风险
        changes = []
        risks = []
        opportunities = []
        
        if month == 3 and self.test_score > 90:
            changes.append("标准化考试成绩显著提升")
            opportunities.append("可以申请更高层次的学校")
        
        if month == 6 and self.research_score > 85:
            changes.append("科研能力达到优秀水平")
            opportunities.append("可以争取科研型奖学金")
        
        if self.test_score < 70:
            risks.append("标准化考试成绩不足，可能影响申请")
        
        # 确定状态
        if total_score >= 80:
            status = "good"
        elif total_score >= 60:
            status = "warning"
        else:
            status = "critical"
        
        state = EducationAgentState(
            month=month,
            score=round(total_score, 1),
            status=status,
            key_metrics={
                "gpa_score": round(self.gpa_score, 1),
                "test_score": round(self.test_score, 1),
                "research_score": round(self.research_score, 1)
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class AdmissionProbabilityAgent(BaseEducationAgent):
    """录取概率Agent - 实时跟踪各学校录取概率"""
    
    def __init__(self, user_id: str):
        super().__init__("admission_probability", user_id)
        self.school_probabilities: Dict[str, float] = {}
        self.current_round: int = 1
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取学校数据"""
        options = context.get('options', [])
        academic = context.get('academic_profile', {})
        gpa = academic.get('gpa', 80.0) / 100
        
        for opt in options:
            school = opt.get('school_name', '')
            base_prob = opt.get('base_probability', 0.5)
            # 根据GPA调整概率
            adjustment = (gpa - 0.75) * 0.5
            self.school_probabilities[school] = min(0.95, max(0.05, base_prob + adjustment))
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, EducationAgentState]
    ) -> EducationAgentState:
        """每月演化"""
        # 获取学业实力Agent的状态
        academic_state = other_agents_state.get('academic_strength')
        if academic_state:
            academic_score = academic_state.score
            
            # 根据学业实力调整概率
            for school in self.school_probabilities:
                base = self.school_probabilities[school]
                # 学业实力越高，概率越高
                adjustment = (academic_score - 75) / 100 * 0.2
                self.school_probabilities[school] = min(0.95, max(0.05, base + adjustment))
        
        # 识别关键变化
        changes = []
        risks = []
        opportunities = []
        
        # 检查是否有学校概率突破关键阈值
        for school, prob in self.school_probabilities.items():
            if prob >= 0.7:
                opportunities.append(f"{school}录取概率上升至{prob:.0%}")
            elif prob < 0.2:
                risks.append(f"{school}录取概率较低({prob:.0%})，需要备选方案")
        
        # 综合得分
        if self.school_probabilities:
            avg_prob = sum(self.school_probabilities.values()) / len(self.school_probabilities)
            total_score = avg_prob * 100
        else:
            total_score = 50.0
        
        # 确定状态
        if total_score >= 60:
            status = "good"
        elif total_score >= 40:
            status = "warning"
        else:
            status = "critical"
        
        state = EducationAgentState(
            month=month,
            score=round(total_score, 1),
            status=status,
            key_metrics=dict(self.school_probabilities),
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class FinancialPlanningAgent(BaseEducationAgent):
    """财务规划Agent - 管理教育投资和奖学金"""
    
    def __init__(self, user_id: str):
        super().__init__("financial_planning", user_id)
        self.total_budget = 0.0
        self.scholarship_fund = 0.0
        self.spending_score = 70.0
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取财务数据"""
        financial = context.get('financial_profile', {})
        self.total_budget = financial.get('total_budget', 200000)
        self.scholarship_fund = financial.get('scholarship_need', 50000)
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, EducationAgentState]
    ) -> EducationAgentState:
        """每月演化"""
        # 模拟奖学金申请进展
        if month >= 4:  # 奖学金申请期
            academic_state = other_agents_state.get('academic_strength')
            if academic_state and academic_state.score > 80:
                self.scholarship_fund = min(self.total_budget * 0.8, 
                                           self.scholarship_fund + 5000 * (month - 3))
        
        # 模拟支出
        monthly_spending = 5000  # 申请相关支出
        remaining = self.total_budget - self.scholarship_fund - (monthly_spending * month)
        
        # 计算得分
        if remaining > 0:
            budget_score = min(100, (remaining / 100000) * 100)
        else:
            budget_score = max(0, 100 + (remaining / 10000) * 100)
        
        self.spending_score = (budget_score + self.scholarship_fund / 1000) / 2
        
        # 识别变化和风险
        changes = []
        risks = []
        opportunities = []
        
        if month == 4 and self.scholarship_fund > 30000:
            changes.append("已申请多项奖学金")
        
        if remaining < 50000:
            risks.append("预算紧张，可能需要调整申请策略")
        
        if self.scholarship_fund > 100000:
            opportunities.append("奖学金充足，经济压力大幅降低")
        
        # 确定状态
        if self.spending_score >= 70:
            status = "good"
        elif self.spending_score >= 50:
            status = "warning"
        else:
            status = "critical"
        
        state = EducationAgentState(
            month=month,
            score=round(self.spending_score, 1),
            status=status,
            key_metrics={
                "total_budget": self.total_budget,
                "scholarship_fund": self.scholarship_fund,
                "remaining": round(remaining, 0),
                "budget_score": round(budget_score, 1)
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class StrategyExecutionAgent(BaseEducationAgent):
    """策略执行Agent - 跟踪申请策略执行情况"""
    
    def __init__(self, user_id: str):
        super().__init__("strategy_execution", user_id)
        self.tasks_completed = 0
        self.total_tasks = 10
        self.execution_score = 60.0
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取策略数据"""
        strategy = context.get('application_strategy', {})
        self.total_tasks = strategy.get('total_tasks', 10)
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, EducationAgentState]
    ) -> EducationAgentState:
        """每月演化"""
        # 模拟任务完成进度
        if month == 1:
            self.tasks_completed = 2
        elif month == 2:
            self.tasks_completed = 4
        elif month == 3:
            self.tasks_completed = 7
        elif month == 4:
            self.tasks_completed = 9
        elif month >= 5:
            self.tasks_completed = self.total_tasks
        
        # 计算执行得分
        self.execution_score = (self.tasks_completed / self.total_tasks) * 100
        
        # 识别变化和风险
        changes = []
        risks = []
        opportunities = []
        
        if month == 3 and self.tasks_completed >= 5:
            changes.append("申请材料准备进度良好")
        
        if month == 4 and self.tasks_completed < 8:
            risks.append("材料准备滞后，可能影响申请")
        
        if self.tasks_completed == self.total_tasks:
            opportunities.append("所有材料准备就绪，可以提交申请")
        
        # 确定状态
        if self.execution_score >= 80:
            status = "good"
        elif self.execution_score >= 50:
            status = "warning"
        else:
            status = "critical"
        
        state = EducationAgentState(
            month=month,
            score=round(self.execution_score, 1),
            status=status,
            key_metrics={
                "tasks_completed": self.tasks_completed,
                "total_tasks": self.total_tasks,
                "completion_rate": round(self.execution_score, 1)
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class OutcomePredictionAgent(BaseEducationAgent):
    """结果预测Agent - 综合预测最终录取结果"""
    
    def __init__(self, user_id: str):
        super().__init__("outcome_prediction", user_id)
        self.predicted_outcomes: Dict[str, float] = {}
        self.confidence = 50.0
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取预测数据"""
        options = context.get('options', [])
        for opt in options:
            school = opt.get('school_name', '')
            prob = opt.get('base_probability', 0.5)
            self.predicted_outcomes[school] = prob
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, EducationAgentState]
    ) -> EducationAgentState:
        """每月演化"""
        # 综合各Agent的状态更新预测
        academic_state = other_agents_state.get('academic_strength')
        admission_state = other_agents_state.get('admission_probability')
        financial_state = other_agents_state.get('financial_planning')
        strategy_state = other_agents_state.get('strategy_execution')
        
        # 根据各Agent状态调整预测
        for school in self.predicted_outcomes:
            base_prob = self.predicted_outcomes[school]
            
            # 学业实力加成
            if academic_state and academic_state.score > 80:
                base_prob *= 1.1
            elif academic_state and academic_state.score < 60:
                base_prob *= 0.9
            
            # 申请概率加成
            if admission_state and school in admission_state.key_metrics:
                school_prob = admission_state.key_metrics[school]
                if school_prob > base_prob:
                    base_prob = (base_prob + school_prob) / 2
            
            # 策略执行加成
            if strategy_state and strategy_state.score >= 80:
                base_prob *= 1.05
            
            self.predicted_outcomes[school] = min(0.95, max(0.05, base_prob))
        
        # 计算置信度
        if academic_state and financial_state and strategy_state:
            avg_status_score = (
                academic_state.score +
                financial_state.score +
                strategy_state.score
            ) / 3
            self.confidence = min(95, avg_status_score)
        
        # 计算综合得分
        if self.predicted_outcomes:
            # 期望值
            expected_value = sum(self.predicted_outcomes.values()) / len(self.predicted_outcomes)
            total_score = expected_value * 100
        else:
            total_score = 50.0
        
        # 识别变化和风险
        changes = []
        risks = []
        opportunities = []
        
        # 检查是否有重大变化
        for school, prob in self.predicted_outcomes.items():
            if prob >= 0.7:
                opportunities.append(f"{school}预测录取概率上升至{prob:.0%}")
            elif prob < 0.15:
                risks.append(f"{school}风险较高({prob:.0%})，建议作为保底")
        
        # 确定状态
        if total_score >= 60:
            status = "good"
        elif total_score >= 40:
            status = "warning"
        else:
            status = "critical"
        
        state = EducationAgentState(
            month=month,
            score=round(total_score, 1),
            status=status,
            key_metrics={
                "predictions": {k: round(v, 3) for k, v in self.predicted_outcomes.items()},
                "confidence": round(self.confidence, 1),
                "expected_schools": len([p for p in self.predicted_outcomes.values() if p >= 0.5])
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class MultiAgentEducationEvaluator:
    """
    教育升学决策多Agent评估器
    
    使用多Agent系统模拟升学决策的全过程推演
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 初始化5个Agent
        self.agents: Dict[str, BaseEducationAgent] = {
            'academic_strength': AcademicStrengthAgent(user_id),
            'admission_probability': AdmissionProbabilityAgent(user_id),
            'financial_planning': FinancialPlanningAgent(user_id),
            'strategy_execution': StrategyExecutionAgent(user_id),
            'outcome_prediction': OutcomePredictionAgent(user_id),
        }
        
        self.timeline: List[Dict[str, EducationAgentState]] = []
    
    async def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化所有Agent"""
        try:
            for agent in self.agents.values():
                if hasattr(agent, 'initialize'):
                    await agent.initialize(context)
            return True
        except Exception as e:
            logger.error(f"[EducationEvaluator] 初始化失败: {e}")
            return False
    
    async def simulate_full_timeline(
        self,
        context: Dict[str, Any],
        months: int = 6
    ) -> Dict[str, Any]:
        """
        模拟完整时间线
        
        Args:
            context: 决策上下文
            months: 模拟月数
        
        Returns:
            模拟结果
        """
        # 初始化
        if not await self.initialize(context):
            return {"error": "初始化失败"}
        
        all_interactions = []
        all_milestones = []
        
        # 逐月演化
        for month in range(1, months + 1):
            month_state = {}
            month_interactions = []
            
            # 每个Agent演化
            for agent_name, agent in self.agents.items():
                # 获取其他Agent的状态
                other_states = {k: v for k, v in month_state.items() if k != agent_name}
                
                # 演化
                state = await agent.evolve(month, context, other_states)
                month_state[agent_name] = state
            
            self.timeline.append(month_state)
            
            # 生成月度交互
            month_interactions = self._generate_monthly_interactions(month, month_state)
            all_interactions.extend(month_interactions)
            
            # 生成关键里程碑
            milestones = self._generate_milestones(month, month_state, context)
            all_milestones.extend(milestones)
        
        # 生成综合评估
        overall_assessment = self._generate_overall_assessment(months)
        
        # 生成关键时间点
        key_milestones = self._identify_key_milestones(all_milestones, all_interactions)
        
        return {
            "timeline": [
                {
                    "month": month + 1,
                    "agents_state": {k: self._serialize_state(v) for k, v in states.items()},
                    "milestones": self._serialize_milestones([
                        m for m in all_milestones if m.month == month + 1
                    ])
                }
                for month, states in enumerate(self.timeline)
            ],
            "summary": {
                "overall_trend": self._calculate_overall_trend(),
                "score_change": (
                    self.timeline[-1]["outcome_prediction"].score -
                    self.timeline[0]["outcome_prediction"].score
                ) if self.timeline else 0,
                "final_score": self.timeline[-1]["outcome_prediction"].score if self.timeline else 0,
                "agent_trends": {
                    name: agent.calculate_trend(3)
                    for name, agent in self.agents.items()
                },
                "total_interactions": len(all_interactions),
                "total_milestones": len(all_milestones),
                "key_milestones": key_milestones
            },
            "all_interactions": all_interactions,
            "all_milestones": all_milestones
        }
    
    def _serialize_state(self, state: EducationAgentState) -> Dict[str, Any]:
        """序列化Agent状态"""
        return {
            "month": state.month,
            "score": round(state.score, 2),
            "status": state.status,
            "key_metrics": state.key_metrics,
            "changes": state.changes,
            "risks": state.risks,
            "opportunities": state.opportunities
        }
    
    def _serialize_milestones(self, milestones: List[ApplicationMilestone]) -> List[Dict]:
        """序列化里程碑"""
        return [
            {
                "month": m.month,
                "type": m.milestone_type,
                "school": m.school,
                "description": m.description,
                "status": m.status
            }
            for m in milestones
        ]
    
    def _generate_monthly_interactions(
        self,
        month: int,
        states: Dict[str, EducationAgentState]
    ) -> List[Dict[str, Any]]:
        """生成月度交互"""
        interactions = []
        
        # 学业实力与录取概率的交互
        academic = states.get('academic_strength')
        admission = states.get('admission_probability')
        if academic and admission:
            if academic.score > 80 and admission.score > 60:
                interactions.append({
                    "month": month,
                    "agents": ["academic_strength", "admission_probability"],
                    "type": "synergy",
                    "description": "学业实力提升带动录取概率上升",
                    "impact": "positive"
                })
            elif academic.score < 60:
                interactions.append({
                    "month": month,
                    "agents": ["academic_strength", "admission_probability"],
                    "type": "risk",
                    "description": "学业实力不足，录取概率承压",
                    "impact": "negative"
                })
        
        # 策略执行与其他Agent的交互
        strategy = states.get('strategy_execution')
        if strategy and strategy.score < 50:
            interactions.append({
                "month": month,
                "agents": ["strategy_execution", "outcome_prediction"],
                "type": "risk",
                "description": "申请材料准备滞后，影响最终结果预测",
                "impact": "negative"
            })
        
        return interactions
    
    def _generate_milestones(
        self,
        month: int,
        states: Dict[str, EducationAgentState],
        context: Dict[str, Any]
    ) -> List[ApplicationMilestone]:
        """生成关键里程碑"""
        milestones = []
        options = context.get('options', [])
        
        # 根据月份生成典型里程碑
        if month == 1:
            milestones.append(ApplicationMilestone(
                month=month,
                milestone_type="deadline",
                school=options[0].get('school_name', '目标学校') if options else '目标学校',
                description="确定申请学校清单",
                status="completed"
            ))
        elif month == 2:
            milestones.append(ApplicationMilestone(
                month=month,
                milestone_type="deadline",
                school="各学校",
                description="开始准备申请材料",
                status="completed"
            ))
        elif month == 3:
            for opt in options[:2]:
                milestones.append(ApplicationMilestone(
                    month=month,
                    milestone_type="deadline",
                    school=opt.get('school_name', '目标学校'),
                    description="提交第一批申请",
                    status="pending"
                ))
        elif month == 5:
            milestones.append(ApplicationMilestone(
                month=month,
                milestone_type="result",
                school="各学校",
                description="开始收到录取通知",
                status="pending"
            ))
        
        return milestones
    
    def _generate_overall_assessment(self, months: int) -> Dict[str, Any]:
        """生成综合评估"""
        if not self.timeline:
            return {
                "overall_score": 50,
                "overall_status": "warning",
                "status_text": "数据不足",
                "weakest_dimension": {"name": "unknown", "score": 0, "status": "unknown"},
                "strongest_dimension": {"name": "unknown", "score": 0, "status": "unknown"},
                "total_risks": 0,
                "total_opportunities": 0,
                "key_risks": [],
                "key_opportunities": []
            }
        
        final_states = self.timeline[-1]
        
        # 找最强和最弱维度
        scores = {k: v.score for k, v in final_states.items()}
        strongest = max(scores.items(), key=lambda x: x[1])
        weakest = min(scores.items(), key=lambda x: x[1])
        
        # 统计风险和机会
        all_risks = []
        all_opportunities = []
        for state in final_states.values():
            all_risks.extend(state.risks)
            all_opportunities.extend(state.opportunities)
        
        # 计算综合得分
        avg_score = sum(scores.values()) / len(scores)
        
        # 确定状态
        if avg_score >= 70:
            status = "good"
        elif avg_score >= 50:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "overall_score": round(avg_score, 1),
            "overall_status": status,
            "status_text": self._get_status_text(status),
            "weakest_dimension": {
                "name": weakest[0],
                "score": weakest[1],
                "status": final_states[weakest[0]].status
            },
            "strongest_dimension": {
                "name": strongest[0],
                "score": strongest[1],
                "status": final_states[strongest[0]].status
            },
            "total_risks": len(all_risks),
            "total_opportunities": len(all_opportunities),
            "key_risks": list(set(all_risks))[:5],
            "key_opportunities": list(set(all_opportunities))[:5]
        }
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        mapping = {
            "good": "申请准备充分，有望获得理想结果",
            "warning": "申请准备一般，需要密切关注进度",
            "critical": "申请准备不足，建议调整策略"
        }
        return mapping.get(status, "状态未知")
    
    def _calculate_overall_trend(self) -> str:
        """计算整体趋势"""
        if len(self.timeline) < 2:
            return "stable"
        
        outcome_agent = self.agents.get('outcome_prediction')
        if not outcome_agent:
            return "stable"
        
        return outcome_agent.calculate_trend(3)
    
    def _identify_key_milestones(
        self,
        milestones: List[ApplicationMilestone],
        interactions: List[Dict]
    ) -> List[Dict[str, Any]]:
        """识别关键里程碑"""
        key = []
        
        # 筛选重要里程碑
        for m in milestones:
            if m.milestone_type in ["result", "decision"]:
                key.append({
                    "month": m.month,
                    "description": m.description,
                    "recommendation": f"关注{m.school}的{m.milestone_type}通知"
                })
        
        # 添加重大交互作为里程碑
        for i in interactions:
            if i.get("impact") == "negative" or i.get("type") == "decision_point":
                key.append({
                    "month": i["month"],
                    "description": i["description"],
                    "recommendation": "需要及时调整策略"
                })
        
        # 按月份排序
        key.sort(key=lambda x: x["month"])
        
        return key[:10]  # 最多返回10个


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        evaluator = MultiAgentEducationEvaluator(user_id="test_user")
        
        context = {
            "academic_profile": {
                "gpa": 85,
                "test_score": 320,
                "research_score": 75
            },
            "financial_profile": {
                "total_budget": 300000,
                "scholarship_need": 100000
            },
            "application_strategy": {
                "total_tasks": 10
            },
            "options": [
                {"school_name": "清华大学", "base_probability": 0.4},
                {"school_name": "MIT", "base_probability": 0.15},
                {"school_name": "复旦大学", "base_probability": 0.6}
            ]
        }
        
        result = await evaluator.simulate_full_timeline(context, months=6)
        
        print("=" * 60)
        print("教育升学推演结果")
        print("=" * 60)
        
        print(f"\n整体趋势: {result['summary']['overall_trend']}")
        print(f"最终得分: {result['summary']['final_score']}")
        
        print("\n各Agent趋势:")
        for name, trend in result['summary']['agent_trends'].items():
            print(f"  {name}: {trend}")
        
        print("\n关键里程碑:")
        for m in result['summary']['key_milestones'][:5]:
            print(f"  第{m['month']}月: {m['description']}")
    
    asyncio.run(main())
