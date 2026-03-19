"""
增强的Neo4j知识图谱 - Phase 2
添加更多关系类型、推理能力和高级查询功能
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()


class RelationshipType(Enum):
    """关系类型枚举"""
    # 因果关系
    CAUSES = "CAUSES"  # A导致B
    CAUSED_BY = "CAUSED_BY"  # A被B导致
    INFLUENCES = "INFLUENCES"  # A影响B
    
    # 时间关系
    BEFORE = "BEFORE"  # A在B之前
    AFTER = "AFTER"  # A在B之后
    DURING = "DURING"  # A在B期间
    CONCURRENT = "CONCURRENT"  # A与B同时发生
    
    # 相似关系
    SIMILAR_TO = "SIMILAR_TO"  # A与B相似
    OPPOSITE_TO = "OPPOSITE_TO"  # A与B相反
    
    # 包含关系
    CONTAINS = "CONTAINS"  # A包含B
    PART_OF = "PART_OF"  # A是B的一部分
    
    # 位置关系
    LOCATED_AT = "LOCATED_AT"  # A位于B
    NEAR = "NEAR"  # A靠近B
    
    # 关联关系
    ASSOCIATED_WITH = "ASSOCIATED_WITH"  # A与B关联
    RELATED_TO = "RELATED_TO"  # A与B相关
    
    # 强度关系
    STRENGTHENS = "STRENGTHENS"  # A强化B
    WEAKENS = "WEAKENS"  # A削弱B
    
    # 依赖关系
    DEPENDS_ON = "DEPENDS_ON"  # A依赖B
    REQUIRED_FOR = "REQUIRED_FOR"  # A是B所需的
    
    # 对比关系
    BETTER_THAN = "BETTER_THAN"  # A比B更好
    WORSE_THAN = "WORSE_THAN"  # A比B更差
    
    # 转换关系
    TRANSFORMS_TO = "TRANSFORMS_TO"  # A转变为B
    EVOLVES_INTO = "EVOLVES_INTO"  # A进化为B


class EnhancedNeo4jKnowledgeGraph:
    """增强的Neo4j知识图谱"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 从环境变量读取配置
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print(f"✅ Neo4j 连接成功: {uri}")
        except Exception as e:
            print(f"❌ Neo4j 连接失败: {e}")
            raise
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
    
    # ==================== 增强的关系操作 ====================
    
    def add_causal_relationship(
        self,
        cause: str,
        effect: str,
        strength: float = 0.5,
        confidence: float = 0.8,
        evidence: str = ""
    ) -> bool:
        """添加因果关系"""
        return self._add_typed_relationship(
            cause,
            effect,
            RelationshipType.CAUSES,
            {
                "strength": strength,
                "confidence": confidence,
                "evidence": evidence,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def add_temporal_relationship(
        self,
        first: str,
        second: str,
        relation_type: str,  # "BEFORE", "AFTER", "DURING", "CONCURRENT"
        time_gap: Optional[int] = None  # 时间间隔（秒）
    ) -> bool:
        """添加时间关系"""
        properties = {
            "timestamp": datetime.now().isoformat()
        }
        if time_gap is not None:
            properties["time_gap"] = time_gap
        
        return self._add_typed_relationship(
            first,
            second,
            relation_type,
            properties
        )
    
    def add_similarity_relationship(
        self,
        entity1: str,
        entity2: str,
        similarity_score: float = 0.5,
        reason: str = ""
    ) -> bool:
        """添加相似关系"""
        return self._add_typed_relationship(
            entity1,
            entity2,
            RelationshipType.SIMILAR_TO,
            {
                "similarity_score": similarity_score,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def add_strength_relationship(
        self,
        source: str,
        target: str,
        strengthens: bool = True,
        magnitude: float = 0.5
    ) -> bool:
        """添加强化/削弱关系"""
        rel_type = RelationshipType.STRENGTHENS if strengthens else RelationshipType.WEAKENS
        return self._add_typed_relationship(
            source,
            target,
            rel_type,
            {
                "magnitude": magnitude,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _add_typed_relationship(
        self,
        source: str,
        target: str,
        relation_type: RelationshipType,
        properties: Dict[str, Any]
    ) -> bool:
        """添加类型化关系"""
        with self.driver.session() as session:
            return session.execute_write(
                self._create_typed_relationship,
                self.user_id,
                source,
                target,
                relation_type.value,
                properties
            )
    
    @staticmethod
    def _create_typed_relationship(
        tx,
        user_id: str,
        source: str,
        target: str,
        relation_type: str,
        properties: Dict
    ):
        """创建类型化关系事务"""
        query = f"""
        MATCH (a {{user_id: $user_id, name: $source}})
        MATCH (b {{user_id: $user_id, name: $target}})
        MERGE (a)-[r:{relation_type}]->(b)
        SET r += $props
        RETURN r
        """
        
        result = tx.run(
            query,
            user_id=user_id,
            source=source,
            target=target,
            props=properties
        )
        return result.single() is not None
    
    # ==================== 推理功能 ====================
    
    def infer_transitive_relationships(self, max_depth: int = 3) -> List[Dict[str, Any]]:
        """推理传递关系"""
        with self.driver.session() as session:
            return session.execute_read(
                self._infer_transitive,
                self.user_id,
                max_depth
            )
    
    @staticmethod
    def _infer_transitive(tx, user_id: str, max_depth: int):
        """推理传递关系事务"""
        query = f"""
        MATCH path = (a {{user_id: $user_id}})-[*2..{max_depth}]->(c {{user_id: $user_id}})
        WHERE a <> c
        WITH a, c, relationships(path) as rels
        RETURN a.name as source, c.name as target, 
               [r in rels | type(r)] as path_types,
               length(rels) as depth
        LIMIT 50
        """
        
        result = tx.run(query, user_id=user_id)
        return [
            {
                "source": record["source"],
                "target": record["target"],
                "path": " -> ".join(record["path_types"]),
                "depth": record["depth"]
            }
            for record in result
        ]
    
    def infer_inverse_relationships(self) -> List[Dict[str, Any]]:
        """推理反向关系"""
        with self.driver.session() as session:
            return session.execute_read(
                self._infer_inverse,
                self.user_id
            )
    
    @staticmethod
    def _infer_inverse(tx, user_id: str):
        """推理反向关系事务"""
        query = """
        MATCH (a {user_id: $user_id})-[r:CAUSES]->(b {user_id: $user_id})
        RETURN a.name as cause, b.name as effect, r.strength as strength
        UNION
        MATCH (a {user_id: $user_id})-[r:BEFORE]->(b {user_id: $user_id})
        RETURN a.name as first, b.name as second, 1.0 as strength
        """
        
        result = tx.run(query, user_id=user_id)
        return [dict(record) for record in result]
    
    def detect_cycles(self) -> List[Dict[str, Any]]:
        """检测循环关系（反馈环）"""
        with self.driver.session() as session:
            return session.execute_read(
                self._detect_cycles,
                self.user_id
            )
    
    @staticmethod
    def _detect_cycles(tx, user_id: str):
        """检测循环事务"""
        query = """
        MATCH (a {user_id: $user_id})
        MATCH path = (a)-[*2..5]->(a)
        WITH a, path, relationships(path) as rels
        RETURN a.name as node,
               [r in rels | type(r)] as cycle_path,
               length(rels) as cycle_length
        LIMIT 20
        """
        
        result = tx.run(query, user_id=user_id)
        return [
            {
                "node": record["node"],
                "cycle": " -> ".join(record["cycle_path"]),
                "length": record["cycle_length"]
            }
            for record in result
        ]
    
    # ==================== 高级查询 ====================
    
    def find_influencers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """找出最有影响力的节点"""
        with self.driver.session() as session:
            return session.execute_read(
                self._find_influencers,
                self.user_id,
                limit
            )
    
    @staticmethod
    def _find_influencers(tx, user_id: str, limit: int):
        """找出影响力节点事务"""
        query = """
        MATCH (n {user_id: $user_id})-[r:INFLUENCES|CAUSES|STRENGTHENS]->(m {user_id: $user_id})
        WITH n, count(r) as out_degree, avg(r.strength) as avg_strength
        MATCH (n)<-[r2:INFLUENCED_BY|CAUSED_BY|WEAKENS]-(m2 {user_id: $user_id})
        WITH n, out_degree, avg_strength, count(r2) as in_degree
        RETURN n.name as name, 
               out_degree as influences_count,
               in_degree as influenced_by_count,
               avg_strength as avg_influence_strength,
               out_degree + in_degree as total_degree
        ORDER BY total_degree DESC
        LIMIT $limit
        """
        
        result = tx.run(query, user_id=user_id, limit=limit)
        return [
            {
                "name": record["name"],
                "influences": record["influences_count"],
                "influenced_by": record["influenced_by_count"],
                "avg_strength": record["avg_influence_strength"],
                "total_degree": record["total_degree"]
            }
            for record in result
        ]
    
    def find_clusters(self) -> List[Dict[str, Any]]:
        """找出知识图谱中的聚类"""
        with self.driver.session() as session:
            return session.execute_read(
                self._find_clusters,
                self.user_id
            )
    
    @staticmethod
    def _find_clusters(tx, user_id: str):
        """找出聚类事务"""
        query = """
        MATCH (n {user_id: $user_id})-[r]-(m {user_id: $user_id})
        WITH n, m, count(r) as connection_strength
        WHERE connection_strength > 1
        RETURN n.name as node1, m.name as node2, connection_strength
        LIMIT 50
        """
        
        result = tx.run(query, user_id=user_id)
        return [
            {
                "node1": record["node1"],
                "node2": record["node2"],
                "strength": record["connection_strength"]
            }
            for record in result
        ]
    
    def get_entity_context(self, entity_name: str, depth: int = 2) -> Dict[str, Any]:
        """获取实体的上下文（周围节点和关系）"""
        with self.driver.session() as session:
            return session.execute_read(
                self._get_entity_context,
                self.user_id,
                entity_name,
                depth
            )
    
    @staticmethod
    def _get_entity_context(tx, user_id: str, entity_name: str, depth: int):
        """获取实体上下文事务"""
        query = f"""
        MATCH (center {{user_id: $user_id, name: $entity_name}})
        MATCH (center)-[r*1..{depth}]-(neighbor {{user_id: $user_id}})
        WITH center, neighbor, r
        RETURN center.name as center_entity,
               neighbor.name as related_entity,
               labels(neighbor)[0] as entity_type,
               [rel in r | type(rel)] as relationship_path,
               length(r) as distance
        ORDER BY distance
        """
        
        result = tx.run(query, user_id=user_id, entity_name=entity_name)
        
        context = {
            "center": entity_name,
            "neighbors": []
        }
        
        for record in result:
            context["neighbors"].append({
                "name": record["related_entity"],
                "type": record["entity_type"],
                "path": " -> ".join(record["relationship_path"]),
                "distance": record["distance"]
            })
        
        return context
    
    # ==================== 时间分析 ====================
    
    def analyze_temporal_patterns(self, days: int = 30) -> Dict[str, Any]:
        """分析时间模式"""
        with self.driver.session() as session:
            return session.execute_read(
                self._analyze_temporal_patterns,
                self.user_id,
                days
            )
    
    @staticmethod
    def _analyze_temporal_patterns(tx, user_id: str, days: int):
        """分析时间模式事务"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = """
        MATCH (n {user_id: $user_id})
        WHERE n.created_at > $cutoff_date
        WITH n, n.created_at as created_time
        RETURN labels(n)[0] as entity_type,
               count(n) as count,
               min(created_time) as earliest,
               max(created_time) as latest
        """
        
        result = tx.run(query, user_id=user_id, cutoff_date=cutoff_date)
        
        patterns = {}
        for record in result:
            patterns[record["entity_type"]] = {
                "count": record["count"],
                "earliest": record["earliest"],
                "latest": record["latest"]
            }
        
        return {
            "period_days": days,
            "patterns": patterns
        }
    
    # ==================== 统计和分析 ====================
    
    def get_graph_metrics(self) -> Dict[str, Any]:
        """获取图谱指标"""
        with self.driver.session() as session:
            return session.execute_read(
                self._get_graph_metrics,
                self.user_id
            )
    
    @staticmethod
    def _get_graph_metrics(tx, user_id: str):
        """获取图谱指标事务"""
        # 节点数
        node_query = "MATCH (n {user_id: $user_id}) RETURN count(n) as count"
        node_result = tx.run(node_query, user_id=user_id)
        node_count = node_result.single()["count"]
        
        # 关系数
        rel_query = "MATCH ({user_id: $user_id})-[r]->({user_id: $user_id}) RETURN count(r) as count"
        rel_result = tx.run(rel_query, user_id=user_id)
        rel_count = rel_result.single()["count"]
        
        # 平均度数
        degree_query = """
        MATCH (n {user_id: $user_id})-[r]-()
        WITH n, count(r) as degree
        RETURN avg(degree) as avg_degree, max(degree) as max_degree, min(degree) as min_degree
        """
        degree_result = tx.run(degree_query, user_id=user_id)
        degree_record = degree_result.single()
        
        # 关系类型分布
        rel_type_query = """
        MATCH ({user_id: $user_id})-[r]->({user_id: $user_id})
        RETURN type(r) as rel_type, count(r) as count
        """
        rel_type_result = tx.run(rel_type_query, user_id=user_id)
        rel_types = {record["rel_type"]: record["count"] for record in rel_type_result}
        
        return {
            "node_count": node_count,
            "relationship_count": rel_count,
            "density": (2 * rel_count) / (node_count * (node_count - 1)) if node_count > 1 else 0,
            "average_degree": degree_record["avg_degree"] or 0,
            "max_degree": degree_record["max_degree"] or 0,
            "min_degree": degree_record["min_degree"] or 0,
            "relationship_types": rel_types
        }
    
    # ==================== 推荐功能 ====================
    
    def get_recommendations(self, entity_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """基于知识图谱获取推荐"""
        with self.driver.session() as session:
            return session.execute_read(
                self._get_recommendations,
                self.user_id,
                entity_name,
                limit
            )
    
    @staticmethod
    def _get_recommendations(tx, user_id: str, entity_name: str, limit: int):
        """获取推荐事务"""
        query = """
        MATCH (source {user_id: $user_id, name: $entity_name})
        MATCH (source)-[r1:SIMILAR_TO|RELATED_TO]->(similar {user_id: $user_id})
        MATCH (similar)-[r2:STRENGTHENS|INFLUENCES]->(recommended {user_id: $user_id})
        WHERE recommended <> source
        RETURN recommended.name as recommendation,
               labels(recommended)[0] as type,
               r1.similarity_score as similarity,
               r2.strength as strength,
               (r1.similarity_score * r2.strength) as score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        result = tx.run(query, user_id=user_id, entity_name=entity_name, limit=limit)
        return [
            {
                "recommendation": record["recommendation"],
                "type": record["type"],
                "score": record["score"]
            }
            for record in result
        ]
    
    # ==================== 导出和可视化 ====================
    
    def export_for_visualization(self) -> Dict[str, Any]:
        """导出用于可视化的数据"""
        with self.driver.session() as session:
            return session.execute_read(
                self._export_for_visualization,
                self.user_id
            )
    
    @staticmethod
    def _export_for_visualization(tx, user_id: str):
        """导出可视化数据事务"""
        # 导出节点
        node_query = """
        MATCH (n {user_id: $user_id})
        RETURN elementId(n) as id, labels(n)[0] as type, n.name as name
        """
        node_result = tx.run(node_query, user_id=user_id)
        nodes = [
            {
                "id": record["id"],
                "label": record["name"],
                "type": record["type"]
            }
            for record in node_result
        ]
        
        # 导出关系
        rel_query = """
        MATCH (a {user_id: $user_id})-[r]->(b {user_id: $user_id})
        RETURN elementId(a) as source, elementId(b) as target, type(r) as type, r.strength as strength
        """
        rel_result = tx.run(rel_query, user_id=user_id)
        edges = [
            {
                "source": record["source"],
                "target": record["target"],
                "label": record["type"],
                "weight": record["strength"] or 1.0
            }
            for record in rel_result
        ]
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }


# 全局实例
_kg_instance = None

def get_enhanced_knowledge_graph(user_id: str) -> EnhancedNeo4jKnowledgeGraph:
    """获取增强知识图谱实例"""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = EnhancedNeo4jKnowledgeGraph(user_id)
    return _kg_instance

