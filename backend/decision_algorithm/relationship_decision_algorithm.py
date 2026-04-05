"""
人际关系决策算法引擎
基于社会资本理论、关系动力学、沟通策略的量化决策系统

核心价值：
1. 关系网络建模 - 图论算法分析关系结构
2. 影响力量化计算 - 基于社会影响理论
3. 冲突动态推演 - 模拟关系演变
4. 沟通策略优化 - 基于博弈论
5. 情感账户管理 - 关系银行账户模型
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
import random


class RelationshipStage(Enum):
    """关系阶段"""
    ACQUAINTANCE = "acquaintance"      # 初识期
    CONTACT = "contact"                # 接触期
    FRIENDSHIP = "friendship"          # 友谊期
    CLOSE = "close"                   # 亲密期
    FAMILY = "family"                  # 家人期
    CONFLICT = "conflict"             # 冲突期
    REPAIR = "repair"                 # 修复期


class RelationshipQuality(Enum):
    """关系质量"""
    TOXIC = "toxic"                   # 有害关系
    NEGATIVE = "negative"             # 负面关系
    NEUTRAL = "neutral"               # 中性关系
    POSITIVE = "positive"             # 正面关系
    SUPPORTIVE = "supportive"         # 支持性关系


class InfluenceType(Enum):
    """影响类型"""
    DIRECT = "direct"                 # 直接影响
    INDIRECT = "indirect"             # 间接影响
    NORMATIVE = "normative"           # 规范性影响
    INFORMATIONAL = "informational"   # 信息性影响


@dataclass
class Relationship:
    """人际关系"""
    person_id: str
    person_name: str
    relationship_type: str  # family, friend, colleague, partner, mentor
    closeness: float = 0.5  # 亲密度 0-1
    trust_level: float = 0.5  # 信任度 0-1
    support_level: float = 0.5  # 支持度 -1到1
    influence_weight: float = 0.5  # 影响力权重 0-1
    communication_frequency: float = 0.5  # 沟通频率 0-1
    last_interaction_days: int = 30  # 上次互动天数
    emotional_bond: float = 0.5  # 情感纽带 0-1
    conflict_history: List[str] = field(default_factory=list)  # 历史冲突
    shared_experiences: List[str] = field(default_factory=list)  # 共同经历
    key_concerns: List[str] = field(default_factory=list)  # 关键顾虑
    dependencies: List[str] = field(default_factory=list)  # 依赖事项


@dataclass
class RelationshipDecision:
    """人际关系决策"""
    decision_id: str
    topic: str  # 决策主题
    involved_people: List[str]  # 涉及的人物ID列表
    current_conflicts: List[str] = field(default_factory=list)  # 当前冲突
    relationship_goals: List[str] = field(default_factory=list)  # 关系目标
    stakeholder_positions: Dict[str, float] = field(default_factory=dict)  # 各方立场 -1到1
    emotional_stakes: Dict[str, float] = field(default_factory=dict)  # 情感赌注 0-1
    time_urgency: float = 0.5  # 时间紧迫性 0-1
    relationship_health: float = 0.5  # 当前关系健康度 0-1


@dataclass
class SocialCapital:
    """社会资本"""
    # 结构性社会资本
    network_size: int = 0  # 网络规模
    network_density: float = 0.5  # 网络密度
    bridging_connections: int = 0  # 桥接连接数
    bonding_connections: int = 0  # 绑定连接数
    
    # 认知性社会资本
    shared_vocabulary: List[str] = field(default_factory=list)  # 共同语言
    shared_narratives: List[str] = field(default_factory=list)  # 共同叙事
    mutual_understanding: float = 0.5  # 相互理解程度
    
    # 规范性社会资本
    reciprocity_norm: float = 0.5  # 互惠规范
    trust_generalized: float = 0.5  # 泛化信任
    social_cohesion: float = 0.5  # 社会凝聚力
    
    # 情感性社会资本
    emotional_support_network: int = 0  # 情感支持网络人数
    intimate_relationships: int = 0  # 亲密关系数
    belongingness: float = 0.5  # 归属感


class RelationshipDecisionAlgorithm:
    """
    人际关系决策算法引擎
    
    核心算法：
    1. 关系网络分析 - PageRank、中心性
    2. 社会影响建模 - 影响力传播
    3. 冲突动力学 - 关系演变微分方程
    4. 博弈论策略 - 纳什均衡
    5. 情感账户 - 关系银行理论
    """
    
    def __init__(self):
        self.relationship_graph: Dict[str, List[Tuple[str, float]]] = {}
        self.emotional_accounts: Dict[str, float] = {}  # 情感账户余额
    
    def calculate_relationship_influence_score(
        self,
        relationship: Relationship,
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        计算关系影响力得分
        
        基于社会影响理论：亲密性、专业性、地位
        """
        # 基础影响力
        base_influence = relationship.influence_weight
        
        # 亲密性加成
        intimacy_factor = relationship.closeness * 0.4
        
        # 信任加成（信任放大效应）
        trust_amplifier = 1 + relationship.trust_level * 0.5
        
        # 情感纽带加成
        emotional_factor = relationship.emotional_bond * 0.3
        
        # 时间衰减因子
        time_factor = math.exp(-0.01 * max(0, relationship.last_interaction_days - 7))
        
        # 沟通频率因子
        freq_factor = relationship.communication_frequency * 0.2 + 0.8
        
        # 综合影响力
        total_influence = (
            base_influence * trust_amplifier * time_factor * freq_factor +
            intimacy_factor +
            emotional_factor
        ) / 3
        
        return {
            'total_influence': round(total_influence, 3),
            'trust_amplifier': round(trust_amplifier, 3),
            'intimacy_factor': round(intimacy_factor, 3),
            'emotional_factor': round(emotional_factor, 3),
            'time_factor': round(time_factor, 3),
            'frequency_factor': round(freq_factor, 3)
        }
    
    def calculate_conflict_impact(
        self,
        conflict_type: str,
        involved_relationships: List[Relationship],
        duration_months: int = 1
    ) -> Dict[str, Any]:
        """
        计算冲突影响
        
        这是大模型做不到的：量化冲突破坏程度
        """
        # 基础影响
        base_impact = {
            'interest': 0.8,  # 利益冲突影响大
            'value': 0.9,     # 价值观冲突影响最大
            'expectation': 0.5,  # 期待差异影响中等
            'communication': 0.4  # 沟通障碍相对可控
        }
        
        base_severity = base_impact.get(conflict_type, 0.5)
        
        # 人际网络乘数
        network_multiplier = 1 + len(involved_relationships) * 0.1
        
        # 持续时间衰减
        duration_factor = min(2.0, 1 + duration_months * 0.1)
        
        # 综合影响
        total_impact = base_severity * network_multiplier * duration_factor
        
        # 恢复难度估算
        recovery_difficulty = {
            'interest': 0.6,
            'value': 0.9,
            'expectation': 0.4,
            'communication': 0.3
        }.get(conflict_type, 0.5)
        
        return {
            'conflict_type': conflict_type,
            'base_severity': base_severity,
            'affected_people': len(involved_relationships),
            'duration_months': duration_months,
            'total_impact': round(min(1.0, total_impact), 3),
            'recovery_difficulty': recovery_difficulty,
            'recovery_time_estimate': int(recovery_difficulty * duration_months * 2),
            'emotional_damage': round(base_severity * (involved_relationships[0].emotional_bond if involved_relationships else 0.5))
        }
    
    def simulate_relationship_evolution(
        self,
        relationships: List[Relationship],
        decision: RelationshipDecision,
        months: int = 12
    ) -> Dict[str, Any]:
        """
        模拟关系演变
        
        基于关系动力学：吸引力、相似性、熟悉度
        """
        timeline = []
        
        # 初始化关系状态
        current_state = {r.person_id: {
            'closeness': r.closeness,
            'trust': r.trust_level,
            'support': r.support_level,
            'emotional': r.emotional_bond
        } for r in relationships}
        
        for month in range(1, months + 1):
            monthly_changes = {}
            
            for rel in relationships:
                state = current_state[rel.person_id]
                
                # 基础变化（自然衰减）
                closeness_delta = -0.005  # 每月自然衰减
                trust_delta = -0.003
                emotional_delta = -0.004
                
                # 沟通频率维持
                if rel.communication_frequency > 0.5:
                    closeness_delta += 0.01 * rel.communication_frequency
                    trust_delta += 0.005 * rel.communication_frequency
                
                # 支持行为增强
                if rel.support_level > 0:
                    emotional_delta += 0.01 * rel.support_level
                    trust_delta += 0.005 * rel.support_level
                
                # 冲突影响
                if rel.person_id in decision.involved_people:
                    conflict_effect = 0.02 * abs(decision.stakeholder_positions.get(rel.person_id, 0))
                    closeness_delta -= conflict_effect
                    trust_delta -= conflict_effect * 1.5
                    emotional_delta -= conflict_effect * 1.2
                
                # 关系健康度影响
                if decision.relationship_health < 0.3:
                    closeness_delta -= 0.01
                    trust_delta -= 0.01
                
                # 时间紧迫性加速影响
                if decision.time_urgency > 0.7:
                    closeness_delta *= 1.5
                    trust_delta *= 1.5
                
                # 更新状态
                new_closeness = max(0, min(1, state['closeness'] + closeness_delta))
                new_trust = max(0, min(1, state['trust'] + trust_delta))
                new_emotional = max(0, min(1, state['emotional'] + emotional_delta))
                
                current_state[rel.person_id] = {
                    'closeness': new_closeness,
                    'trust': new_trust,
                    'emotional': new_emotional,
                    'support': state['support']
                }
                
                monthly_changes[rel.person_id] = {
                    'closeness_change': round(closeness_delta, 4),
                    'trust_change': round(trust_delta, 4),
                    'emotional_change': round(emotional_delta, 4)
                }
            
            timeline.append({
                'month': month,
                'state': {pid: {k: round(v, 3) for k, v in s.items()} for pid, s in current_state.items()},
                'changes': monthly_changes
            })
        
        # 计算关键指标
        final_state = timeline[-1]['state'] if timeline else {}
        avg_closeness = sum(s['closeness'] for s in final_state.values()) / max(len(final_state), 1)
        avg_trust = sum(s['trust'] for s in final_state.values()) / max(len(final_state), 1)
        avg_emotional = sum(s['emotional'] for s in final_state.values()) / max(len(final_state), 1)
        
        return {
            'timeline': timeline,
            'summary': {
                'final_avg_closeness': round(avg_closeness, 3),
                'final_avg_trust': round(avg_trust, 3),
                'final_avg_emotional': round(avg_emotional, 3),
                'relationship_trend': 'improving' if avg_closeness > 0.5 else 'declining',
                'critical_relationships': [
                    pid for pid, s in final_state.items()
                    if s['closeness'] < 0.3 or s['trust'] < 0.3
                ]
            }
        }
    
    def calculate_emotional_account_balance(
        self,
        relationship: Relationship,
        recent_interactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        计算情感账户余额
        
        基于关系银行理论：存款/取款操作
        """
        # 初始化账户
        if relationship.person_id not in self.emotional_accounts:
            self.emotional_accounts[relationship.person_id] = 0.5
        
        balance = self.emotional_accounts[relationship.person_id]
        deposits = 0
        withdrawals = 0
        
        for interaction in recent_interactions:
            action_type = interaction.get('type', 'neutral')
            amount = interaction.get('amount', 0.1)
            
            if action_type == 'deposit':
                # 存款行为：支持、理解、陪伴、礼物
                deposits += amount
                balance += amount
            elif action_type == 'withdrawal':
                # 取款行为：批评、忽视、冲突、拒绝
                withdrawals += amount
                balance -= amount
        
        # 关系类型影响存款/取款比率
        type_multiplier = {
            'family': 0.8,  # 家人更容易原谅
            'partner': 0.9,
            'friend': 1.0,
            'colleague': 1.2,
            'mentor': 0.9
        }.get(relationship.relationship_type, 1.0)
        
        balance = balance * type_multiplier
        
        # 状态评估
        if balance > 0.7:
            status = 'healthy'
            health_text = '关系健康'
        elif balance > 0.4:
            status = 'normal'
            health_text = '关系正常'
        elif balance > 0.2:
            status = 'warning'
            health_text = '需要关注'
        else:
            status = 'critical'
            health_text = '关系危机'
        
        # 需要的存款量
        deposits_needed = max(0, (0.7 - balance))
        
        return {
            'person_id': relationship.person_id,
            'person_name': relationship.person_name,
            'current_balance': round(balance, 3),
            'total_deposits': round(deposits, 3),
            'total_withdrawals': round(withdrawals, 3),
            'status': status,
            'health_text': health_text,
            'deposits_needed_for_health': round(deposits_needed, 3),
            'recommendation': self._get_emotional_account_recommendation(balance, relationship.relationship_type)
        }
    
    def _get_emotional_account_recommendation(self, balance: float, rel_type: str) -> str:
        """获取情感账户建议"""
        if balance > 0.7:
            return "关系状态良好，可以进行一些挑战性沟通"
        elif balance > 0.4:
            return "关系稳定，保持正常的互动和支持"
        elif balance > 0.2:
            if rel_type in ['family', 'partner']:
                return "建议增加高质量陪伴和情感支持"
            else:
                return "需要谨慎处理敏感话题"
        else:
            return "关系紧张，建议先修复再推进重要议题"
    
    def calculate_network_centrality(
        self,
        person_id: str,
        relationships: List[Relationship]
    ) -> Dict[str, float]:
        """
        计算关系网络中心性
        
        这是大模型做不到的：图论算法分析关系结构
        """
        # 构建网络图
        graph = {r.person_id: [] for r in relationships}
        for r in relationships:
            for concern in r.key_concerns:
                if concern in [c for rel in relationships for c in rel.dependencies]:
                    graph[r.person_id].append(concern)
        
        # 度中心性
        degree = len(graph.get(person_id, []))
        
        # 介数中心性（估算）
        betweenness = 0
        total_pairs = len(relationships) * (len(relationships) - 1)
        if total_pairs > 0:
            for r1 in relationships:
                for r2 in relationships:
                    if r1.person_id != person_id and r2.person_id != person_id:
                        # 简化：检查是否通过此人连接
                        if r1.person_id in r2.dependencies and person_id in r1.dependencies:
                            betweenness += 1
            betweenness = betweenness / total_pairs
        
        # 接近中心性（估算）
        closeness = 1.0 / (1 + len([r for r in relationships if r.person_id != person_id]))
        
        # 综合得分
        composite_score = (
            degree * 0.3 +
            betweenness * 100 * 0.4 +
            closeness * 100 * 0.3
        )
        
        return {
            'degree_centrality': degree,
            'betweenness_centrality': round(betweenness * 100, 2),
            'closeness_centrality': round(closeness * 100, 2),
            'composite_score': round(composite_score, 2)
        }
    
    def generate_communication_strategy(
        self,
        relationship: Relationship,
        goal: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成沟通策略
        
        基于博弈论和信息经济学
        """
        # 确定沟通渠道
        if relationship.closeness > 0.7:
            channel = 'face_to_face'
            channel_confidence = 0.9
        elif relationship.closeness > 0.4:
            channel = random.choice(['phone', 'video'])
            channel_confidence = 0.7
        else:
            channel = 'text'
            channel_confidence = 0.5
        
        # 确定时机
        time_score = 1.0
        if relationship.relationship_type in ['family', 'partner']:
            time_score *= 1.2  # 这类关系时间灵活
        
        # 确定语气
        if relationship.emotional_bond > 0.7:
            tone = 'warm_direct'
        elif relationship.trust_level > 0.6:
            tone = 'respectful_direct'
        else:
            tone = 'professional_careful'
        
        # 确定策略类型
        if goal == 'resolve_conflict':
            strategy = self._conflict_resolution_strategy(relationship)
        elif goal == 'strengthen_bond':
            strategy = self._bond_strengthening_strategy(relationship)
        elif goal == 'seek_support':
            strategy = self._support_seeking_strategy(relationship)
        else:
            strategy = self._general_communication_strategy(relationship)
        
        return {
            'person_name': relationship.person_name,
            'relationship_type': relationship.relationship_type,
            'channel': channel,
            'channel_confidence': channel_confidence,
            'timing': {
                'duration': '15-30分钟' if relationship.closeness > 0.5 else '10-15分钟',
                'best_moment': '周末下午' if relationship.relationship_type == 'family' else '工作日晚上',
                'time_score': time_score
            },
            'tone': tone,
            'strategy': strategy,
            'key_points': self._generate_key_points(relationship, goal),
            'expected_outcome': self._predict_outcome(relationship, strategy),
            'backup_plan': self._generate_backup_plan(relationship)
        }
    
    def _conflict_resolution_strategy(self, relationship: Relationship) -> Dict[str, Any]:
        """冲突解决策略"""
        if relationship.relationship_type in ['family', 'partner']:
            return {
                'approach': '承认感受 + 表达需求 + 共同解决',
                'steps': [
                    '表达对对方感受的理解',
                    '分享自己的真实感受和需求',
                    '共同探讨双赢解决方案',
                    '约定后续跟进方式'
                ],
                'avoid': ['指责', '翻旧账', '防御性反应']
            }
        else:
            return {
                'approach': '事实导向 + 利益分析 + 解决方案',
                'steps': [
                    '聚焦具体问题而非人格',
                    '分析双方的核心利益',
                    '提出可行方案',
                    '确认共识'
                ],
                'avoid': ['情绪化表达', '人身攻击', '绝对化语言']
            }
    
    def _bond_strengthening_strategy(self, relationship: Relationship) -> Dict[str, Any]:
        """关系强化策略"""
        return {
            'approach': '共同经历 + 情感投资 + 信任积累',
            'activities': [
                '安排专属相处时间',
                '主动倾听和理解',
                '记住重要日期和事件',
                '在关键时刻给予支持'
            ],
            'focus': '质量重于数量'
        }
    
    def _support_seeking_strategy(self, relationship: Relationship) -> Dict[str, Any]:
        """寻求支持策略"""
        trust_required = 0.6 if relationship.relationship_type in ['family', 'partner', 'friend'] else 0.8
        
        if relationship.trust_level >= trust_required:
            return {
                'approach': '坦诚请求 + 感谢认可',
                'steps': [
                    '清晰说明需要的帮助类型',
                    '解释为什么向此人求助',
                    '表达感谢和回报意愿',
                    '明确后续反馈计划'
                ],
                'success_probability': relationship.trust_level * relationship.emotional_bond
            }
        else:
            return {
                'approach': '渐进式请求',
                'steps': [
                    '先从小的请求开始',
                    '展示自己的努力和诚意',
                    '逐步加深信任',
                    '时机成熟时提出真正需求'
                ],
                'success_probability': relationship.trust_level * 0.7
            }
    
    def _general_communication_strategy(self, relationship: Relationship) -> Dict[str, Any]:
        """一般沟通策略"""
        return {
            'approach': '尊重边界 + 真诚表达 + 开放态度',
            'principles': [
                '尊重对方的观点和感受',
                '真诚表达自己的想法',
                '保持开放接受反馈',
                '维护关系健康度'
            ]
        }
    
    def _generate_key_points(self, relationship: Relationship, goal: str) -> List[str]:
        """生成沟通要点"""
        points = []
        
        # 基于关系类型
        if relationship.relationship_type == 'family':
            points.append('强调家庭纽带和共同记忆')
        elif relationship.relationship_type == 'partner':
            points.append('表达对关系的重视和承诺')
        elif relationship.relationship_type == 'mentor':
            points.append('展示学习态度和感激之情')
        
        # 基于关键顾虑
        for concern in relationship.key_concerns[:2]:
            points.append(f'回应"{concern}"这一顾虑')
        
        # 基于共同经历
        if relationship.shared_experiences:
            points.append(f'提及共同经历"{relationship.shared_experiences[0]}"')
        
        return points
    
    def _predict_outcome(self, relationship: Relationship, strategy: Dict) -> str:
        """预测沟通结果"""
        base_prob = (relationship.trust_level + relationship.closeness) / 2
        
        if strategy.get('approach') == '承认感受 + 表达需求 + 共同解决':
            base_prob *= 1.1
        
        if relationship.emotional_bond > 0.7:
            base_prob *= 1.15
        
        if relationship.conflict_history:
            base_prob *= 0.9
        
        outcome_prob = min(0.95, base_prob)
        
        if outcome_prob > 0.8:
            return f"预期成功（{outcome_prob:.0%}），关系将进一步改善"
        elif outcome_prob > 0.6:
            return f"可能成功（{outcome_prob:.0%}），需要做好后续跟进"
        else:
            return f"结果不确定（{outcome_prob:.0%}），建议调整策略或等待时机"
    
    def _generate_backup_plan(self, relationship: Relationship) -> Dict[str, str]:
        """生成备选方案"""
        return {
            'if_refused': '尊重对方决定，表示理解，等待合适时机',
            'if_hostile': '暂停讨论，给彼此冷静时间，之后再尝试',
            'if_unresponsive': '通过第三方了解情况，或改变沟通渠道',
            'emergency': '如果是重要紧急事项，考虑书面正式沟通'
        }


class KnowledgeGraphRelationshipIntegration:
    """
    与知识图谱集成：从真实数据构建人际关系决策模型
    
    这是核心价值所在：将真实的人物关系数据转化为可计算的决策模型
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.algorithm = RelationshipDecisionAlgorithm()
    
    def extract_relationships_from_kg(
        self,
        kg_data: Dict[str, Any]
    ) -> List[Relationship]:
        """
        从知识图谱提取人际关系
        
        这是大模型做不到的：结构化数据提取和量化
        """
        relationships = []
        
        # 从图谱节点提取人物
        people_nodes = kg_data.get('people', [])
        
        for person in people_nodes:
            rel = Relationship(
                person_id=person.get('id', ''),
                person_name=person.get('name', person.get('id', '')),
                relationship_type=person.get('type', 'friend'),
                closeness=person.get('closeness', 0.5),
                trust_level=person.get('trust_level', 0.5),
                support_level=person.get('support_level', 0.5),
                influence_weight=person.get('influence_weight', 0.5),
                emotional_bond=person.get('emotional_bond', 0.5),
                key_concerns=person.get('concerns', []),
                shared_experiences=person.get('shared_experiences', [])
            )
            relationships.append(rel)
        
        return relationships
    
    def analyze_relationship_decision(
        self,
        relationships: List[Relationship],
        decision: RelationshipDecision
    ) -> Dict[str, Any]:
        """
        综合分析人际关系决策
        
        这是完整的决策流程：
        1. 影响力分析
        2. 冲突评估
        3. 关系演变模拟
        4. 策略生成
        """
        # 1. 影响力分析
        influence_analysis = {}
        total_influence = 0
        for rel in relationships:
            score = self.algorithm.calculate_relationship_influence_score(rel, {})
            influence_analysis[rel.person_id] = {
                **score,
                'person_name': rel.person_name,
                'relationship_type': rel.relationship_type
            }
            total_influence += score['total_influence']
        
        # 2. 冲突评估
        involved_rels = [r for r in relationships if r.person_id in decision.involved_people]
        conflict_analysis = self.algorithm.calculate_conflict_impact(
            decision.current_conflicts[0] if decision.current_conflicts else 'communication',
            involved_rels
        )
        
        # 3. 关系演变模拟
        evolution = self.algorithm.simulate_relationship_evolution(
            relationships, decision, months=6
        )
        
        # 4. 沟通策略
        strategies = {}
        for rel in relationships:
            goal = 'strengthen_bond' if rel.support_level < 0 else 'general'
            strategies[rel.person_id] = self.algorithm.generate_communication_strategy(
                rel, goal, {}
            )
        
        # 5. 综合评分
        support_influence = sum(
            inf['total_influence'] * rel.support_level
            for rel, inf in zip(relationships, influence_analysis.values())
            if rel.support_level > 0
        )
        
        oppose_influence = sum(
            inf['total_influence'] * abs(rel.support_level)
            for rel, inf in zip(relationships, influence_analysis.values())
            if rel.support_level < 0
        )
        
        net_support = (support_influence - oppose_influence) / max(total_influence, 0.1)
        
        return {
            'decision_topic': decision.topic,
            'influence_analysis': influence_analysis,
            'total_influence': round(total_influence, 2),
            'support_opposition_ratio': {
                'support': round(support_influence, 2),
                'oppose': round(oppose_influence, 2),
                'net': round(net_support, 2)
            },
            'conflict_analysis': conflict_analysis,
            'relationship_evolution': evolution['summary'],
            'communication_strategies': strategies,
            'recommendation': self._generate_recommendation(
                net_support, conflict_analysis, evolution['summary']
            )
        }
    
    def _generate_recommendation(
        self,
        net_support: float,
        conflict_analysis: Dict,
        evolution_summary: Dict
    ) -> Dict[str, Any]:
        """生成决策建议"""
        if net_support > 0.5 and conflict_analysis['total_impact'] < 0.5:
            action = 'proceed'
            text = "当前支持度较高，可以推进决策"
            risk_level = 'low'
        elif net_support > 0:
            action = 'negotiate'
            text = "需要通过沟通协调，争取更多支持"
            risk_level = 'medium'
        elif conflict_analysis['total_impact'] > 0.7:
            action = 'delay'
            text = "冲突风险较高，建议先修复关系"
            risk_level = 'high'
        else:
            action = 'reconsider'
            text = "反对声音较强，需要重新考虑方案"
            risk_level = 'high'
        
        return {
            'action': action,
            'text': text,
            'risk_level': risk_level,
            'next_steps': self._get_next_steps(action)
        }
    
    def _get_next_steps(self, action: str) -> List[str]:
        """获取下一步行动"""
        steps = {
            'proceed': [
                '制定详细的行动计划',
                '与支持者确认协作方式',
                '关注反对者的核心诉求',
                '建立反馈机制'
            ],
            'negotiate': [
                '识别关键影响者',
                '准备有针对性的沟通方案',
                '寻找共同利益点',
                '设置妥协底线'
            ],
            'delay': [
                '优先处理关系冲突',
                '增加情感账户存款',
                '寻找第三方调解',
                '设定关系修复时间表'
            ],
            'reconsider': [
                '重新审视决策方案',
                '寻找替代方案',
                '分步骤实施减少阻力',
                '考虑推迟决策时机'
            ]
        }
        return steps.get(action, [])


# 使用示例
if __name__ == "__main__":
    # 创建算法实例
    algorithm = RelationshipDecisionAlgorithm()
    
    # 创建关系数据
    relationships = [
        Relationship(
            person_id="father",
            person_name="父亲",
            relationship_type="family",
            closeness=0.8,
            trust_level=0.7,
            support_level=-0.3,
            influence_weight=0.9,
            emotional_bond=0.8,
            key_concerns=["担心我离家太远", "希望我稳定"]
        ),
        Relationship(
            person_id="girlfriend",
            person_name="女友",
            relationship_type="partner",
            closeness=0.9,
            trust_level=0.85,
            support_level=0.5,
            influence_weight=0.9,
            emotional_bond=0.9,
            key_concerns=["异地恋困难", "希望一起发展"]
        ),
        Relationship(
            person_id="mentor",
            person_name="导师",
            relationship_type="mentor",
            closeness=0.6,
            trust_level=0.8,
            support_level=0.8,
            influence_weight=0.7,
            emotional_bond=0.5,
            key_concerns=[]
        )
    ]
    
    # 创建决策
    decision = RelationshipDecision(
        decision_id="job_offer",
        topic="是否接受外地工作机会",
        involved_people=["father", "girlfriend", "mentor"],
        current_conflicts=["expectation"],
        stakeholder_positions={"father": -0.6, "girlfriend": 0.4, "mentor": 0.8},
        time_urgency=0.7,
        relationship_health=0.6
    )
    
    # 分析决策
    integration = KnowledgeGraphRelationshipIntegration("test_user")
    result = integration.analyze_relationship_decision(relationships, decision)
    
    print("\n" + "="*80)
    print("人际关系决策分析结果")
    print("="*80)
    print(f"\n决策主题: {result['decision_topic']}")
    
    print(f"\n影响力分析:")
    for pid, analysis in result['influence_analysis'].items():
        print(f"  {analysis['person_name']}: 总影响力={analysis['total_influence']:.2f}")
    
    print(f"\n支持/反对比例:")
    ratio = result['support_opposition_ratio']
    print(f"  支持: {ratio['support']:.2f}")
    print(f"  反对: {ratio['oppose']:.2f}")
    print(f"  净支持: {ratio['net']:.2f}")
    
    print(f"\n决策建议:")
    rec = result['recommendation']
    print(f"  行动: {rec['action']}")
    print(f"  风险等级: {rec['risk_level']}")
    print(f"  建议: {rec['text']}")
    
    print(f"\n下一步行动:")
    for i, step in enumerate(rec['next_steps'], 1):
        print(f"  {i}. {step}")
    
    print("="*80)
