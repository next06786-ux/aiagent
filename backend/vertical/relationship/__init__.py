"""
人际关系知识图谱

核心组件：
- Neo4jRelationshipKnowledgeGraph: 人际关系知识图谱构建器（基于Neo4j 3.0架构）
- RelationshipUserProfile: 用户关系画像
- 关系网络可视化
"""

from backend.vertical.relationship.neo4j_relationship_kg import (
    Neo4jRelationshipKnowledgeGraph,
    RelationshipUserProfile,
    get_neo4j_relationship_kg
)

__all__ = [
    'Neo4jRelationshipKnowledgeGraph',
    'RelationshipUserProfile',
    'get_neo4j_relationship_kg',
]

