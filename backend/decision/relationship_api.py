"""
人际关系决策API路由

提供人际关系决策的完整API：
1. 人物关系图谱视图
2. 人际关系决策分析
3. 关系演变推演
4. 沟通策略生成
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.decision.multi_agent_relationship_evaluator import (
    MultiAgentRelationshipEvaluator
)
from backend.decision_algorithm.relationship_decision_algorithm import (
    Relationship,
    RelationshipDecision,
    RelationshipDecisionAlgorithm,
    KnowledgeGraphRelationshipIntegration
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v5/relationship", tags=["relationship"])


# ==================== 请求模型 ====================

class PersonInput(BaseModel):
    """人物输入"""
    id: str = Field(..., description="人物ID")
    name: str = Field(..., description="人物名称")
    type: str = Field(default="friend", description="关系类型: family, friend, colleague, partner, mentor")
    closeness: float = Field(default=0.5, ge=0, le=1, description="亲密度 0-1")
    trust_level: float = Field(default=0.5, ge=0, le=1, description="信任度 0-1")
    support_level: float = Field(default=0.5, ge=-1, le=1, description="支持度 -1到1")
    influence_weight: float = Field(default=0.5, ge=0, le=1, description="影响力权重 0-1")
    emotional_bond: float = Field(default=0.5, ge=0, le=1, description="情感纽带 0-1")
    key_concerns: List[str] = Field(default_factory=list, description="关键顾虑")
    shared_experiences: List[str] = Field(default_factory=list, description="共同经历")
    communication_frequency: float = Field(default=0.5, ge=0, le=1, description="沟通频率 0-1")
    last_interaction_days: int = Field(default=30, ge=0, description="上次互动天数")


class RelationshipDecisionRequest(BaseModel):
    """人际关系决策请求"""
    user_id: str
    topic: str = Field(..., description="决策主题")
    people: List[PersonInput] = Field(..., description="涉及的人物列表")
    involved_people: List[str] = Field(..., description="涉及的人物ID列表")
    current_conflicts: List[str] = Field(default_factory=list, description="当前冲突")
    stakeholder_positions: Dict[str, float] = Field(default_factory=dict, description="各方立场 -1到1")
    time_urgency: float = Field(default=0.5, ge=0, le=1, description="时间紧迫性 0-1")
    relationship_health: float = Field(default=0.5, ge=0, le=1, description="当前关系健康度 0-1")


class CommunicationStrategyRequest(BaseModel):
    """沟通策略请求"""
    user_id: str
    person: PersonInput
    goal: str = Field(..., description="目标: resolve_conflict, strengthen_bond, seek_support, general")


class RelationshipSimulationRequest(BaseModel):
    """关系演变模拟请求"""
    user_id: str
    people: List[PersonInput]
    decision_topic: str = Field(..., description="决策主题")
    involved_people: List[str] = Field(default_factory=list, description="涉及的人物ID")
    current_conflicts: List[str] = Field(default_factory=list, description="当前冲突")
    stakeholder_positions: Dict[str, float] = Field(default_factory=dict, description="各方立场")
    time_urgency: float = Field(default=0.5, ge=0, le=1, description="时间紧迫性")
    months: int = Field(default=6, ge=1, le=24, description="模拟月数")


class UpdateRelationshipRequest(BaseModel):
    """更新关系请求"""
    user_id: str
    person_id: str
    updates: Dict[str, Any] = Field(..., description="更新的字段")


# ==================== 辅助函数 ====================

def convert_person_input(person: PersonInput) -> Relationship:
    """将PersonInput转换为Relationship"""
    return Relationship(
        person_id=person.id,
        person_name=person.name,
        relationship_type=person.type,
        closeness=person.closeness,
        trust_level=person.trust_level,
        support_level=person.support_level,
        influence_weight=person.influence_weight,
        emotional_bond=person.emotional_bond,
        key_concerns=person.key_concerns,
        shared_experiences=person.shared_experiences,
        communication_frequency=person.communication_frequency,
        last_interaction_days=person.last_interaction_days
    )


def serialize_agent_state(state: Dict) -> Dict:
    """序列化Agent状态"""
    return {
        'month': state.get('month'),
        'score': round(state.get('score', 0), 2),
        'status': state.get('status', 'unknown'),
        'key_metrics': state.get('key_metrics', {}),
        'changes': state.get('changes', []),
        'risks': state.get('risks', []),
        'opportunities': state.get('opportunities', [])
    }


# ==================== API路由 ====================

@router.get("/people/{user_id}")
async def get_relationship_people(user_id: str):
    """
    获取用户的人物关系列表
    
    从知识图谱获取用户的人物关系数据
    """
    try:
        # TODO: 从知识图谱实际获取数据
        # 这里先用模拟数据
        return {
            "success": True,
            "data": {
                "people": [
                    {
                        "id": "father",
                        "name": "父亲",
                        "type": "family",
                        "closeness": 0.8,
                        "trust_level": 0.7,
                        "support_level": -0.3,
                        "influence_weight": 0.9,
                        "emotional_bond": 0.8,
                        "key_concerns": ["担心我离家太远", "希望我稳定"],
                        "shared_experiences": ["一起旅行", "春节团聚"]
                    },
                    {
                        "id": "girlfriend",
                        "name": "女友",
                        "type": "partner",
                        "closeness": 0.9,
                        "trust_level": 0.85,
                        "support_level": 0.5,
                        "influence_weight": 0.9,
                        "emotional_bond": 0.9,
                        "key_concerns": ["异地恋困难", "希望一起发展"],
                        "shared_experiences": ["一起看电影", "周年纪念"]
                    },
                    {
                        "id": "mentor",
                        "name": "导师",
                        "type": "mentor",
                        "closeness": 0.6,
                        "trust_level": 0.8,
                        "support_level": 0.8,
                        "influence_weight": 0.7,
                        "emotional_bond": 0.5,
                        "key_concerns": ["希望我学有所成"],
                        "shared_experiences": ["学术讨论"]
                    }
                ],
                "summary": {
                    "total_count": 3,
                    "by_type": {
                        "family": 1,
                        "partner": 1,
                        "mentor": 1
                    }
                }
            }
        }
    except Exception as e:
        logger.error(f"[RelationshipAPI] 获取人物关系失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": {"people": [], "summary": {}}
        }


@router.post("/analyze")
async def analyze_relationship_decision(request: RelationshipDecisionRequest):
    """
    分析人际关系决策
    
    综合分析影响力、冲突、演变和策略
    """
    try:
        # 转换人物数据
        relationships = [convert_person_input(p) for p in request.people]
        
        # 创建决策
        decision = RelationshipDecision(
            decision_id=f"decision_{request.user_id}",
            topic=request.topic,
            involved_people=request.involved_people,
            current_conflicts=request.current_conflicts,
            stakeholder_positions=request.stakeholder_positions,
            time_urgency=request.time_urgency,
            relationship_health=request.relationship_health
        )
        
        # 分析
        integration = KnowledgeGraphRelationshipIntegration(request.user_id)
        result = integration.analyze_relationship_decision(relationships, decision)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"[RelationshipAPI] 分析决策失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/strategy")
async def generate_communication_strategy(request: CommunicationStrategyRequest):
    """
    生成沟通策略
    
    针对特定人物生成个性化沟通策略
    """
    try:
        # 转换人物数据
        relationship = convert_person_input(request.person)
        
        # 生成策略
        algorithm = RelationshipDecisionAlgorithm()
        strategy = algorithm.generate_communication_strategy(
            relationship,
            request.goal,
            {}
        )
        
        return {
            "success": True,
            "data": strategy
        }
        
    except Exception as e:
        logger.error(f"[RelationshipAPI] 生成策略失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/simulate")
async def simulate_relationship_evolution(request: RelationshipSimulationRequest):
    """
    模拟关系演变
    
    使用多Agent系统模拟人际关系在时间线上的变化
    """
    try:
        # 转换人物数据
        relationships = [convert_person_input(p) for p in request.people]
        
        # 构建上下文
        context = {
            'relationships': [
                {
                    'person_id': p.id,
                    'person_name': p.name,
                    'relationship_type': p.type,
                    'closeness': p.closeness,
                    'trust_level': p.trust_level,
                    'support_level': p.support_level,
                    'emotional_bond': p.emotional_bond,
                    'communication_frequency': p.communication_frequency
                }
                for p in request.people
            ],
            'decisions': [
                {
                    'topic': request.decision_topic,
                    'involved_people': request.involved_people,
                    'current_conflicts': request.current_conflicts,
                    'stakeholder_positions': request.stakeholder_positions
                }
            ],
            'time_urgency': request.time_urgency
        }
        
        # 创建评估器
        evaluator = MultiAgentRelationshipEvaluator(request.user_id)
        
        # 执行模拟
        import asyncio
        result = asyncio.run(evaluator.simulate_full_timeline(context, request.months))
        
        # 序列化结果
        serialized_timeline = []
        for month_data in result['timeline']:
            serialized_timeline.append({
                'month': month_data['month'],
                'agents_state': {
                    name: serialize_agent_state(state)
                    for name, state in month_data['agents_state'].items()
                },
                'interactions': [
                    {
                        'month': i.month,
                        'agents': i.agents,
                        'type': i.interaction_type,
                        'description': i.description,
                        'impact': i.impact
                    }
                    for i in month_data.get('interactions', [])
                ],
                'decision_points': [
                    {
                        'month': dp.month,
                        'trigger': dp.trigger_agent,
                        'description': dp.description,
                        'options': dp.options,
                        'recommendation': dp.recommendation,
                        'votes': dp.agent_votes
                    }
                    for dp in month_data.get('decision_points', [])
                ],
                'overall_assessment': month_data['overall_assessment']
            })
        
        return {
            "success": True,
            "data": {
                "timeline": serialized_timeline,
                "summary": result['summary'],
                "total_interactions": len(result['all_interactions']),
                "total_decision_points": len(result['all_decision_points'])
            }
        }
        
    except Exception as e:
        logger.error(f"[RelationshipAPI] 模拟演变失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/influence")
async def calculate_influence(request: RelationshipDecisionRequest):
    """
    计算人物影响力
    
    分析各人物对决策的影响力
    """
    try:
        # 转换人物数据
        relationships = [convert_person_input(p) for p in request.people]
        
        # 计算影响力
        algorithm = RelationshipDecisionAlgorithm()
        results = []
        total_influence = 0
        
        for rel in relationships:
            score = algorithm.calculate_relationship_influence_score(rel, {})
            total_influence += score['total_influence']
            results.append({
                'person_id': rel.person_id,
                'person_name': rel.person_name,
                'relationship_type': rel.relationship_type,
                'influence_score': score
            })
        
        # 计算权重
        for r in results:
            r['influence_weight'] = round(r['influence_score']['total_influence'] / total_influence, 3) if total_influence > 0 else 0
        
        # 按影响力排序
        results.sort(key=lambda x: x['influence_score']['total_influence'], reverse=True)
        
        return {
            "success": True,
            "data": {
                "influences": results,
                "total_influence": round(total_influence, 3),
                "key_supporters": [r for r in results if r.get('person_id') in request.involved_people and r.get('influence_weight', 0) > 0.2],
                "key_opponents": [r for r in results if r.get('influence_weight', 0) < 0]
            }
        }
        
    except Exception as e:
        logger.error(f"[RelationshipAPI] 计算影响力失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/conflict")
async def analyze_conflicts(request: RelationshipDecisionRequest):
    """
    分析冲突
    
    评估冲突类型、影响和解决方案
    """
    try:
        # 转换人物数据
        relationships = [convert_person_input(p) for p in request.people]
        
        # 获取涉及的人物
        involved = [r for r in relationships if r.person_id in request.involved_people]
        
        if not involved:
            involved = relationships
        
        # 分析冲突
        algorithm = RelationshipDecisionAlgorithm()
        
        # 分析每种冲突类型
        conflict_types = ['interest', 'value', 'expectation', 'communication']
        results = []
        
        for conflict_type in conflict_types:
            impact = algorithm.calculate_conflict_impact(
                conflict_type,
                involved,
                duration_months=1
            )
            results.append({
                'type': conflict_type,
                'analysis': impact
            })
        
        # 识别关键冲突
        key_conflicts = []
        for person in involved:
            if person.support_level < -0.3:
                key_conflicts.append({
                    'person_id': person.person_id,
                    'person_name': person.person_name,
                    'relationship_type': person.relationship_type,
                    'severity': abs(person.support_level),
                    'concerns': person.key_concerns
                })
        
        return {
            "success": True,
            "data": {
                "conflict_analysis": results,
                "key_conflicts": key_conflicts,
                "total_affected": len(key_conflicts),
                "highest_priority": key_conflicts[0] if key_conflicts else None
            }
        }
        
    except Exception as e:
        logger.error(f"[RelationshipAPI] 分析冲突失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/emotional-account")
async def analyze_emotional_accounts(request: RelationshipDecisionRequest):
    """
    分析情感账户
    
    评估各关系的情感账户余额和健康度
    """
    try:
        # 转换人物数据
        relationships = [convert_person_input(p) for p in request.people]
        
        # 模拟最近互动
        algorithm = RelationshipDecisionAlgorithm()
        results = []
        
        for rel in relationships:
            # 模拟最近的互动记录
            recent_interactions = [
                {'type': 'deposit', 'amount': 0.05},  # 上次支持的互动
                {'type': 'deposit', 'amount': 0.03},  # 上上次沟通
            ]
            
            # 检查是否有负面历史
            if rel.conflict_history:
                recent_interactions.append({'type': 'withdrawal', 'amount': 0.1})
            
            balance = algorithm.calculate_emotional_account_balance(rel, recent_interactions)
            results.append({
                'person_id': rel.person_id,
                'person_name': rel.person_name,
                'relationship_type': rel.relationship_type,
                'account_analysis': balance
            })
        
        # 按余额排序
        results.sort(key=lambda x: x['account_analysis']['current_balance'], reverse=True)
        
        # 统计状态分布
        status_counts = {
            'healthy': 0,
            'normal': 0,
            'warning': 0,
            'critical': 0
        }
        for r in results:
            status_counts[r['account_analysis']['status']] += 1
        
        return {
            "success": True,
            "data": {
                "accounts": results,
                "status_distribution": status_counts,
                "overall_health": round(
                    sum(r['account_analysis']['current_balance'] for r in results) / len(results), 3
                ) if results else 0
            }
        }
        
    except Exception as e:
        logger.error(f"[RelationshipAPI] 分析情感账户失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/update")
async def update_relationship(request: UpdateRelationshipRequest):
    """
    更新人物关系
    
    更新特定人物的关系属性
    """
    try:
        # TODO: 实际更新知识图谱中的数据
        # 这里先用模拟响应
        
        return {
            "success": True,
            "data": {
                "person_id": request.person_id,
                "updates_applied": request.updates,
                "message": "关系更新成功"
            }
        }
        
    except Exception as e:
        logger.error(f"[RelationshipAPI] 更新关系失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.get("/summary/{user_id}")
async def get_relationship_summary(user_id: str):
    """
    获取人际关系总览
    
    获取用户人际关系网络的整体概况
    """
    try:
        # TODO: 从知识图谱实际获取数据
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "total_relationships": 3,
                "by_type": {
                    "family": 1,
                    "friend": 0,
                    "colleague": 0,
                    "partner": 1,
                    "mentor": 1
                },
                "average_closeness": 0.77,
                "average_trust": 0.78,
                "key_relationships": [
                    {"id": "father", "name": "父亲", "type": "family"},
                    {"id": "girlfriend", "name": "女友", "type": "partner"}
                ],
                "relationship_health_score": 0.68,
                "recommendations": [
                    "增加与家人的沟通频率",
                    "关注异地恋关系的维护",
                    "珍惜导师的职业指导机会"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"[RelationshipAPI] 获取总览失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
