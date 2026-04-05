"""
人际关系决策引擎

核心组件：
- RelationshipDecisionEngine: 关系决策引擎
- 关系网络分析
- 冲突分析
- 沟通策略生成
"""

from backend.vertical.relationship.relationship_decision_engine import (
    RelationshipDecisionEngine,
    RelationshipType,
    ConflictType,
    Person,
    RelationshipDecisionContext,
)

__all__ = [
    'RelationshipDecisionEngine',
    'RelationshipType',
    'ConflictType',
    'Person',
    'RelationshipDecisionContext',
]
