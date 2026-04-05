"""
人际关系决策多Agent评估框架

整合：
1. 人物关系图谱（知识图谱）- 提供真实数据
2. 人际关系决策算法 - 提供量化分析
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


class BaseRelationshipAgent:
    """人际关系评估Agent基类"""
    
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


class EmotionalBondAgent(BaseRelationshipAgent):
    """情感纽带Agent - 基于情感账户理论"""
    
    def __init__(self, user_id: str):
        super().__init__("emotional_bond", user_id)
        self.emotional_balance = 0.5  # 情感账户余额
        self.emotional_investment = 0.0  # 情感投资总额
        self.critical_relationships = []  # 需要关注的重点关系
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取情感数据"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 从上下文获取人际关系数据
            relationships = context.get('relationships', [])
            
            if not relationships:
                logger.warning(f"[EmotionalAgent] 没有关系数据，使用默认")
                self.emotional_balance = 0.5
                return
            
            # 计算平均情感余额
            total_balance = sum(r.get('emotional_bond', 0.5) for r in relationships)
            self.emotional_balance = total_balance / len(relationships)
            
            # 识别关键关系
            self.critical_relationships = [
                r['person_name'] for r in relationships
                if r.get('relationship_type') in ['family', 'partner'] and r.get('emotional_bond', 0) > 0.7
            ]
            
            logger.info(f"[EmotionalAgent] 初始化完成，情感余额: {self.emotional_balance:.2f}")
            
        except Exception as e:
            logger.error(f"[EmotionalAgent] 初始化失败: {e}")
            self.emotional_balance = 0.5
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """模拟情感纽带变化"""
        
        changes = []
        risks = []
        opportunities = []
        
        # 检查沟通状态影响情感
        communication_state = other_agents_state.get('communication')
        if communication_state:
            if communication_state.status == 'good':
                # 良好沟通增加情感投资
                deposit = 0.03 * communication_state.key_metrics.get('quality_score', 0.5)
                self.emotional_balance = min(1.0, self.emotional_balance + deposit)
                self.emotional_investment += deposit
                changes.append(f"沟通质量良好，情感存款 +{deposit:.3f}")
            elif communication_state.status == 'critical':
                # 沟通障碍导致情感消耗
                withdrawal = 0.05
                self.emotional_balance = max(0, self.emotional_balance - withdrawal)
                changes.append(f"沟通困难，情感取款 -{withdrawal:.3f}")
        
        # 检查冲突状态
        conflict_state = other_agents_state.get('conflict_resolution')
        if conflict_state and conflict_state.status == 'critical':
            # 冲突未解决导致情感快速消耗
            withdrawal = 0.08
            self.emotional_balance = max(0, self.emotional_balance - withdrawal)
            changes.append(f"冲突未解决，情感快速消耗 -{withdrawal:.3f}")
            risks.append("情感账户告急，需要立即处理关系问题")
        
        # 检查支持状态
        support_state = other_agents_state.get('social_support')
        if support_state and support_state.score >= 70:
            opportunities.append("社会支持充足，可以尝试挑战性话题")
        
        # 检查时间流逝的自然衰减
        natural_decay = 0.005  # 每月自然衰减
        if month > 1:
            self.emotional_balance = max(0, self.emotional_balance - natural_decay)
            changes.append(f"自然衰减 -{natural_decay:.3f}")
        
        # 计算得分
        score = self.emotional_balance * 100
        
        # 识别风险
        if score < 30:
            risks.append("情感账户严重透支，关系面临破裂风险")
        elif score < 50:
            risks.append("情感账户偏低，需要增加存款")
        
        # 识别机会
        if score >= 70:
            opportunities.append("情感账户健康，可以进行深度对话")
        
        if self.critical_relationships:
            opportunities.append(f"关键关系维护良好: {', '.join(self.critical_relationships)}")
        
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
                'emotional_balance': f"{self.emotional_balance:.1%}",
                'emotional_investment': f"{self.emotional_investment:.3f}",
                'critical_count': len(self.critical_relationships)
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class CommunicationQualityAgent(BaseRelationshipAgent):
    """沟通质量Agent - 基于沟通理论"""
    
    def __init__(self, user_id: str):
        super().__init__("communication", user_id)
        self.quality_score = 0.7  # 沟通质量
        self.frequency_score = 0.5  # 沟通频率
        self.effectiveness_score = 0.6  # 沟通效果
        self.barriers: List[str] = []  # 沟通障碍
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取沟通数据"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            relationships = context.get('relationships', [])
            
            if not relationships:
                logger.warning(f"[CommunicationAgent] 没有关系数据，使用默认")
                self.quality_score = 0.7
                return
            
            # 计算平均沟通质量
            total_freq = sum(r.get('communication_frequency', 0.5) for r in relationships)
            self.frequency_score = total_freq / len(relationships)
            
            # 沟通质量基于亲密度
            total_closeness = sum(r.get('closeness', 0.5) for r in relationships)
            avg_closeness = total_closeness / len(relationships)
            self.quality_score = 0.5 + avg_closeness * 0.4
            
            logger.info(f"[CommunicationAgent] 初始化完成，沟通质量: {self.quality_score:.2f}")
            
        except Exception as e:
            logger.error(f"[CommunicationAgent] 初始化失败: {e}")
            self.quality_score = 0.7
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """模拟沟通质量变化"""
        
        changes = []
        risks = []
        opportunities = []
        
        # 检查情感状态影响沟通意愿
        emotional_state = other_agents_state.get('emotional_bond')
        if emotional_state:
            if emotional_state.status == 'critical':
                self.quality_score = max(0.3, self.quality_score - 0.1)
                changes.append("情感状态差，沟通质量下降")
                self.barriers.append("情绪障碍")
            elif emotional_state.status == 'good':
                self.quality_score = min(1.0, self.quality_score + 0.05)
                changes.append("情感状态好，沟通更顺畅")
                if "情绪障碍" in self.barriers:
                    self.barriers.remove("情绪障碍")
        
        # 检查是否有计划内的沟通事件
        planned_communication = context.get('planned_communication', False)
        if planned_communication:
            self.frequency_score = min(1.0, self.frequency_score + 0.1)
            changes.append("有计划的沟通活动")
        
        # 检查沟通障碍
        active_barriers = self.barriers.copy()
        
        # 计算效果
        self.effectiveness_score = self.quality_score * self.frequency_score * (1 - len(active_barriers) * 0.2)
        
        changes.append(f"沟通效果: {self.effectiveness_score:.1%}")
        
        # 计算得分
        score = self.effectiveness_score * 100
        
        # 识别风险
        if len(self.barriers) >= 3:
            risks.append("沟通障碍较多，需要系统解决")
        elif self.effectiveness_score < 0.4:
            risks.append("沟通效率低，信息传递不畅")
        
        # 识别机会
        if self.quality_score >= 0.8 and self.frequency_score >= 0.7:
            opportunities.append("沟通质量优秀，关系发展顺利")
        
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
                'quality_score': f"{self.quality_score:.1%}",
                'frequency_score': f"{self.frequency_score:.1%}",
                'effectiveness_score': f"{self.effectiveness_score:.1%}",
                'barriers_count': len(self.barriers)
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class ConflictResolutionAgent(BaseRelationshipAgent):
    """冲突解决Agent - 基于冲突管理理论"""
    
    def __init__(self, user_id: str):
        super().__init__("conflict_resolution", user_id)
        self.conflict_count = 0  # 冲突数量
        self.resolved_count = 0  # 已解决数量
        self.escalation_level = 0.3  # 升级程度
        self.conflict_history: List[Dict] = []  # 冲突历史
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取冲突数据"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            relationships = context.get('relationships', [])
            decisions = context.get('decisions', [])
            
            # 统计历史冲突
            self.conflict_count = sum(len(r.get('conflict_history', [])) for r in relationships)
            
            # 识别当前冲突
            if decisions:
                self.conflict_count += len(decisions[0].get('current_conflicts', []))
            
            logger.info(f"[ConflictAgent] 初始化完成，冲突数: {self.conflict_count}")
            
        except Exception as e:
            logger.error(f"[ConflictAgent] 初始化失败: {e}")
            self.conflict_count = 0
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """模拟冲突解决变化"""
        
        changes = []
        risks = []
        opportunities = []
        
        # 检查其他Agent状态
        emotional_state = other_agents_state.get('emotional_bond')
        communication_state = other_agents_state.get('communication')
        
        # 冲突发生概率
        conflict_prob = 0.1
        
        # 情感状态差增加冲突概率
        if emotional_state and emotional_state.status == 'critical':
            conflict_prob += 0.2
            changes.append("情感紧张，冲突风险增加")
        
        # 沟通障碍增加冲突概率
        if communication_state and communication_state.status == 'critical':
            conflict_prob += 0.15
            changes.append("沟通不畅，误解风险增加")
        
        # 时间紧迫性
        time_urgency = context.get('time_urgency', 0.5)
        if time_urgency > 0.7:
            conflict_prob += 0.1
        
        # 模拟是否发生冲突
        import random
        if random.random() < conflict_prob:
            self.conflict_count += 1
            self.conflict_history.append({
                'month': month,
                'severity': random.uniform(0.3, 0.8),
                'type': random.choice(['interest', 'value', 'expectation', 'communication'])
            })
            changes.append(f"新冲突发生 (累计{self.conflict_count}个)")
        
        # 解决冲突的概率
        resolve_prob = 0.3
        
        # 良好沟通增加解决概率
        if communication_state and communication_state.status == 'good':
            resolve_prob += 0.2
        
        # 情感基础好增加解决概率
        if emotional_state and emotional_state.score >= 60:
            resolve_prob += 0.15
        
        # 尝试解决冲突
        if self.conflict_count > 0 and random.random() < resolve_prob:
            self.resolved_count += 1
            self.conflict_count -= 1
            changes.append("成功解决一个冲突")
            self.escalation_level = max(0, self.escalation_level - 0.1)
        
        # 未解决的冲突可能导致升级
        if self.conflict_count > 2:
            self.escalation_level = min(1.0, self.escalation_level + 0.05)
            risks.append("冲突未解决，可能升级")
        
        # 计算得分
        # 得分 = 基础分 - 冲突惩罚 - 升级惩罚 + 解决奖励
        base_score = 70
        conflict_penalty = min(30, self.conflict_count * 10)
        escalation_penalty = self.escalation_level * 20
        resolve_bonus = min(20, self.resolved_count * 5)
        
        score = base_score - conflict_penalty - escalation_penalty + resolve_bonus
        score = max(0, min(100, score))
        
        # 识别风险
        if self.conflict_count >= 3:
            risks.append("冲突数量过多，需要优先处理")
        
        if self.escalation_level > 0.7:
            risks.append("冲突升级风险高，可能失控")
        
        # 识别机会
        if self.resolved_count > 0 and self.conflict_count == 0:
            opportunities.append("所有冲突已解决，关系进入新阶段")
        
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
                'active_conflicts': self.conflict_count,
                'resolved_conflicts': self.resolved_count,
                'escalation_level': f"{self.escalation_level:.1%}"
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class SocialSupportAgent(BaseRelationshipAgent):
    """社会支持Agent - 基于社会支持理论"""
    
    def __init__(self, user_id: str):
        super().__init__("social_support", user_id)
        self.emotional_support = 0.5  # 情感支持
        self.instrumental_support = 0.5  # 工具性支持
        self.informational_support = 0.5  # 信息性支持
        self.support_network_size = 0  # 支持网络人数
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取支持数据"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            relationships = context.get('relationships', [])
            
            if not relationships:
                logger.warning(f"[SocialSupportAgent] 没有关系数据，使用默认")
                self.support_network_size = 5
                return
            
            # 统计支持网络
            self.support_network_size = len([r for r in relationships if r.get('support_level', 0) > 0])
            
            # 计算支持程度
            support_levels = [r.get('support_level', 0) for r in relationships]
            avg_support = sum(support_levels) / len(support_levels) if support_levels else 0
            
            self.emotional_support = 0.5 + avg_support * 0.4
            self.instrumental_support = 0.5 + (sum(1 for s in support_levels if s > 0.3) / max(len(support_levels), 1)) * 0.4
            self.informational_support = 0.6  # 默认值
            
            logger.info(f"[SocialSupportAgent] 初始化完成，支持网络: {self.support_network_size}人")
            
        except Exception as e:
            logger.error(f"[SocialSupportAgent] 初始化失败: {e}")
            self.support_network_size = 5
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """模拟社会支持变化"""
        
        changes = []
        risks = []
        opportunities = []
        
        # 检查情感纽带状态
        emotional_state = other_agents_state.get('emotional_bond')
        if emotional_state:
            if emotional_state.status == 'good':
                # 良好情感增加支持获取
                self.emotional_support = min(1.0, self.emotional_support + 0.03)
                changes.append("情感状态好，更容易获得支持")
            elif emotional_state.status == 'critical':
                self.emotional_support = max(0.2, self.emotional_support - 0.05)
                changes.append("情感状态差，获得支持困难")
        
        # 检查沟通质量
        communication_state = other_agents_state.get('communication')
        if communication_state and communication_state.status == 'good':
            self.instrumental_support = min(1.0, self.instrumental_support + 0.02)
            self.informational_support = min(1.0, self.informational_support + 0.02)
            changes.append("良好沟通提升工具性和信息性支持")
        
        # 检查是否主动寻求支持
        seeking_support = context.get('seeking_support', False)
        if seeking_support:
            self.emotional_support = min(1.0, self.emotional_support + 0.05)
            self.support_network_size = min(20, self.support_network_size + 1)
            changes.append("主动寻求支持，网络扩大")
        
        # 自然衰减
        self.emotional_support = max(0.2, self.emotional_support - 0.005)
        
        # 计算得分
        score = (
            self.emotional_support * 0.4 +
            self.instrumental_support * 0.3 +
            self.informational_support * 0.3
        ) * 100
        
        # 识别风险
        if self.support_network_size < 3:
            risks.append("支持网络太小，需要扩展人脉")
        
        if self.emotional_support < 0.4:
            risks.append("情感支持不足")
        
        # 识别机会
        if self.support_network_size >= 10:
            opportunities.append("支持网络强大，可以承担挑战")
        
        if all(s >= 0.6 for s in [self.emotional_support, self.instrumental_support, self.informational_support]):
            opportunities.append("各类支持充足，状态最佳")
        
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
                'emotional_support': f"{self.emotional_support:.1%}",
                'instrumental_support': f"{self.instrumental_support:.1%}",
                'informational_support': f"{self.informational_support:.1%}",
                'network_size': f"{self.support_network_size}人"
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class RelationshipBalanceAgent(BaseRelationshipAgent):
    """关系平衡Agent - 基于工作-生活平衡理论"""
    
    def __init__(self, user_id: str):
        super().__init__("relationship_balance", user_id)
        self.work_relationship_balance = 0.5  # 工作-关系平衡
        self.personal_relationship_investment = 0.5  # 人际关系投入
        self.multiple_relationship_balance: Dict[str, float] = {}  # 多关系平衡
    
    async def initialize(self, context: Dict[str, Any]):
        """初始化 - 从上下文获取平衡数据"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            relationships = context.get('relationships', [])
            decisions = context.get('decisions', [])
            
            if not relationships:
                self.work_relationship_balance = 0.5
                return
            
            # 按类型分类关系
            relationship_types = {}
            for r in relationships:
                rtype = r.get('relationship_type', 'other')
                if rtype not in relationship_types:
                    relationship_types[rtype] = []
                relationship_types[rtype].append(r.get('closeness', 0.5))
            
            # 计算多关系平衡
            for rtype, closeness_list in relationship_types.items():
                avg = sum(closeness_list) / len(closeness_list)
                self.multiple_relationship_balance[rtype] = avg
            
            # 整体平衡
            if len(relationship_types) > 1:
                balances = list(self.multiple_relationship_balance.values())
                variance = sum((b - sum(balances)/len(balances))**2 for b in balances) / len(balances)
                self.work_relationship_balance = 1.0 - min(1.0, variance * 2)
            else:
                self.work_relationship_balance = 0.7
            
            logger.info(f"[BalanceAgent] 初始化完成，平衡度: {self.work_relationship_balance:.2f}")
            
        except Exception as e:
            logger.error(f"[BalanceAgent] 初始化失败: {e}")
            self.work_relationship_balance = 0.5
    
    async def evolve(
        self,
        month: int,
        context: Dict[str, Any],
        other_agents_state: Dict[str, AgentState]
    ) -> AgentState:
        """模拟关系平衡变化"""
        
        changes = []
        risks = []
        opportunities = []
        
        # 检查其他Agent状态
        emotional_state = other_agents_state.get('emotional_bond')
        communication_state = other_agents_state.get('communication')
        support_state = other_agents_state.get('social_support')
        
        # 情感投资影响平衡
        if emotional_state:
            if emotional_state.status == 'good':
                self.personal_relationship_investment = min(1.0, self.personal_relationship_investment + 0.03)
                changes.append("情感投资增加")
            elif emotional_state.status == 'critical':
                # 过度投资导致失衡
                self.personal_relationship_investment = max(0.3, self.personal_relationship_investment - 0.05)
                changes.append("情感投资过度，关系疲劳")
        
        # 沟通效率
        if communication_state and communication_state.status == 'good':
            # 高效沟通减少投入需求
            self.personal_relationship_investment = min(1.0, self.personal_relationship_investment + 0.02)
        
        # 支持充足减少投入需求
        if support_state and support_state.score >= 70:
            self.personal_relationship_investment = min(1.0, self.personal_relationship_investment + 0.01)
        
        # 检查是否需要重新平衡
        if self.work_relationship_balance < 0.4:
            risks.append("关系平衡失调，某些关系被忽视")
        
        # 自然波动
        import random
        self.work_relationship_balance = max(0.3, min(1.0, 
            self.work_relationship_balance + random.uniform(-0.03, 0.03)))
        
        # 计算得分
        score = self.work_relationship_balance * 50 + self.personal_relationship_investment * 50
        
        # 识别风险
        if abs(self.work_relationship_balance - 0.5) > 0.3:
            risks.append("关系投入偏差过大")
        
        # 识别机会
        if 0.4 <= self.work_relationship_balance <= 0.6 and self.personal_relationship_investment >= 0.5:
            opportunities.append("关系平衡良好，精力充沛")
        
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
                'balance_score': f"{self.work_relationship_balance:.1%}",
                'investment_score': f"{self.personal_relationship_investment:.1%}",
                'type_balances': {k: f"{v:.1%}" for k, v in self.multiple_relationship_balance.items()}
            },
            changes=changes,
            risks=risks,
            opportunities=opportunities
        )
        
        self.history.append(state)
        return state


class MultiAgentRelationshipEvaluator:
    """多Agent人际关系决策评估器 - 协调5个Agent"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 初始化5个Agent
        self.agents = {
            'emotional_bond': EmotionalBondAgent(user_id),
            'communication': CommunicationQualityAgent(user_id),
            'conflict_resolution': ConflictResolutionAgent(user_id),
            'social_support': SocialSupportAgent(user_id),
            'relationship_balance': RelationshipBalanceAgent(user_id)
        }
        
        self.interactions: List[AgentInteraction] = []
        self.decision_points: List[DecisionPoint] = []
    
    async def initialize_all_agents(self, context: Dict[str, Any]):
        """初始化所有Agent"""
        for agent_name, agent in self.agents.items():
            try:
                await agent.initialize(context)
                logger.info(f"[MultiAgentRelationship] {agent_name} 初始化成功")
            except Exception as e:
                logger.error(f"[MultiAgentRelationship] {agent_name} 初始化失败: {e}")
    
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
                'agents_state': {'emotional_bond': AgentState, ...},
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
        
        emotional = agents_state.get('emotional_bond')
        communication = agents_state.get('communication')
        conflict = agents_state.get('conflict_resolution')
        support = agents_state.get('social_support')
        balance = agents_state.get('relationship_balance')
        
        # 情感-沟通协同
        if emotional and communication:
            if emotional.status == 'good' and communication.status == 'good':
                interactions.append(AgentInteraction(
                    month=month,
                    agents=['emotional_bond', 'communication'],
                    interaction_type='synergy',
                    description='情感和沟通形成正向循环',
                    impact='关系发展加速'
                ))
            elif emotional.status == 'critical' and communication.status == 'critical':
                interactions.append(AgentInteraction(
                    month=month,
                    agents=['emotional_bond', 'communication'],
                    interaction_type='conflict',
                    description='情感和沟通双重困难',
                    impact='关系危机加剧'
                ))
        
        # 冲突-情感对抗
        if conflict and emotional and conflict.conflict_count > 0:
            if emotional.status == 'good':
                interactions.append(AgentInteraction(
                    month=month,
                    agents=['conflict_resolution', 'emotional_bond'],
                    interaction_type='dependency',
                    description='情感基础帮助解决冲突',
                    impact='冲突解决更顺利'
                ))
            elif emotional.status == 'critical':
                interactions.append(AgentInteraction(
                    month=month,
                    agents=['conflict_resolution', 'emotional_bond'],
                    interaction_type='conflict',
                    description='情感透支影响冲突处理',
                    impact='冲突可能升级'
                ))
        
        # 支持-平衡协同
        if support and balance and support.score >= 70:
            interactions.append(AgentInteraction(
                month=month,
                agents=['social_support', 'relationship_balance'],
                interaction_type='synergy',
                description='社会支持帮助维持平衡',
                impact='关系投入更可持续'
            ))
        
        return interactions
    
    def _identify_decision_points(
        self,
        month: int,
        agents_state: Dict[str, AgentState]
    ) -> List[DecisionPoint]:
        """识别关键决策点"""
        decision_points = []
        
        emotional = agents_state.get('emotional_bond')
        communication = agents_state.get('communication')
        conflict = agents_state.get('conflict_resolution')
        
        # 决策点1：是否进行深度对话
        if month >= 2 and emotional and emotional.score >= 60:
            agent_votes = {}
            
            if emotional.score >= 70:
                agent_votes['emotional'] = '支持：情感基础良好'
            else:
                agent_votes['emotional'] = '谨慎：需要更多积累'
            
            if communication and communication.score >= 60:
                agent_votes['communication'] = '支持：沟通质量良好'
            else:
                agent_votes['communication'] = '反对：沟通需要改善'
            
            if conflict and conflict.conflict_count > 0:
                agent_votes['conflict'] = '警告：存在未解决冲突'
            
            support_count = sum(1 for v in agent_votes.values() if '支持' in v)
            oppose_count = sum(1 for v in agent_votes.values() if '反对' in v)
            
            if support_count >= 2 and oppose_count == 0:
                recommendation = '建议进行深度对话'
            elif oppose_count >= 1:
                recommendation = '建议先改善沟通基础'
            else:
                recommendation = '可以尝试，但需谨慎'
            
            decision_points.append(DecisionPoint(
                month=month,
                trigger_agent='emotional_bond',
                description='情感基础良好，是否进行深度对话？',
                options=[
                    '立即进行深度对话',
                    '再积累一段时间',
                    '先处理未解决的冲突'
                ],
                recommendation=recommendation,
                agent_votes=agent_votes
            ))
        
        # 决策点2：冲突处理
        if conflict and conflict.conflict_count >= 2:
            decision_points.append(DecisionPoint(
                month=month,
                trigger_agent='conflict_resolution',
                description=f'存在{conflict.conflict_count}个未解决冲突',
                options=[
                    '立即处理所有冲突',
                    '按重要性排序处理',
                    '先稳定关系再处理'
                ],
                recommendation='建议优先处理最严重的冲突',
                agent_votes={
                    'conflict': '紧急：需要立即处理',
                    'emotional': '谨慎：避免透支情感',
                    'communication': '配合：改善沟通方式'
                }
            ))
        
        # 决策点3：关系平衡调整
        if balance := agents_state.get('relationship_balance'):
            if balance.score < 40:
                decision_points.append(DecisionPoint(
                    month=month,
                    trigger_agent='relationship_balance',
                    description='关系投入失衡，需要调整',
                    options=[
                        '增加人际关系投入',
                        '优化投入方式提高效率',
                        '重新分配各关系时间'
                    ],
                    recommendation='建议优化投入方式',
                    agent_votes={
                        'balance': '需要调整',
                        'emotional': '支持：增加投入',
                        'communication': '建议提高沟通效率'
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
            'emotional_bond': 0.30,
            'communication': 0.25,
            'conflict_resolution': 0.20,
            'social_support': 0.15,
            'relationship_balance': 0.10
        }
        
        total_score = 0
        for agent_name, weight in weights.items():
            state = agents_state.get(agent_name)
            if state:
                total_score += state.score * weight
        
        # 确定整体状态
        if total_score >= 70:
            overall_status = 'good'
            status_text = '关系健康'
        elif total_score >= 50:
            overall_status = 'warning'
            status_text = '需要关注'
        else:
            overall_status = 'critical'
            status_text = '关系紧张'
        
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
            'key_risks': all_risks[:3],
            'key_opportunities': all_opportunities[:3]
        }
    
    async def simulate_full_timeline(
        self,
        context: Dict[str, Any],
        months: int = 6
    ) -> Dict[str, Any]:
        """
        模拟完整的时间线（默认6个月，人际关系变化更快）
        
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
                f"[MultiAgentRelationship] 第{month}月模拟完成 - "
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
            'overall_trend': 'improving' if score_change > 5 else 'declining' if score_change < -5 else 'stable',
            'score_change': score_change,
            'final_score': last_score,
            'agent_trends': agent_trends,
            'total_interactions': len(self.interactions),
            'total_decision_points': len(self.decision_points),
            'key_milestones': milestones,
            'success_probability': self._estimate_success_probability(timeline)
        }
    
    def _estimate_success_probability(self, timeline: List[Dict]) -> float:
        """估算成功概率（关系改善）"""
        
        if not timeline:
            return 0.5
        
        last_month = timeline[-1]
        overall_score = last_month['overall_assessment']['overall_score']
        
        # 基础概率
        base_prob = overall_score / 100
        
        # 调整因素
        agents_state = last_month['agents_state']
        
        # 情感是关键
        emotional_state = agents_state.get('emotional_bond')
        if emotional_state and emotional_state.score >= 70:
            base_prob += 0.1
        elif emotional_state and emotional_state.score < 40:
            base_prob -= 0.2
        
        # 冲突影响大
        conflict_state = agents_state.get('conflict_resolution')
        if conflict_state and conflict_state.conflict_count > 0:
            base_prob -= conflict_state.conflict_count * 0.1
        
        return max(0.1, min(0.95, base_prob))
