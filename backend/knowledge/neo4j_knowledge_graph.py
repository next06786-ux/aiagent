"""
Neo4j 知识图谱
使用 Neo4j 图数据库存储用户的知识图谱
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()


class Neo4jKnowledgeGraph:
    """Neo4j 知识图谱"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 从环境变量读取配置
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # 测试连接
            self.driver.verify_connectivity()
            print(f"✅ Neo4j 连接成功: {uri}")
        except Exception as e:
            print(f"❌ Neo4j 连接失败: {e}")
            print("提示: 请确保 Neo4j 已启动，或运行 'python backend/setup_neo4j.py' 初始化")
            raise
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ==================== 实体操作 ====================
    
    def add_entity(self, entity_type: str, name: str, attributes: Dict[str, Any] = None) -> str:
        """添加实体节点"""
        attributes = attributes or {}
        
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_entity,
                self.user_id,
                entity_type,
                name,
                attributes
            )
            return result
    
    @staticmethod
    def _create_entity(tx, user_id: str, entity_type: str, name: str, attributes: Dict):
        """创建实体事务"""
        # 合并属性
        props = {
            "user_id": user_id,
            "name": name,
            "entity_type": entity_type,
            "created_at": datetime.now().isoformat(),
            **attributes
        }
        
        # 使用 MERGE 避免重复
        query = f"""
        MERGE (e:{entity_type.capitalize()} {{user_id: $user_id, name: $name}})
        SET e += $props
        RETURN elementId(e) as id
        """
        
        result = tx.run(query, user_id=user_id, name=name, props=props)
        record = result.single()
        return record["id"] if record else None
    
    def get_entity(self, entity_type: str, name: str) -> Optional[Dict[str, Any]]:
        """获取实体"""
        with self.driver.session() as session:
            result = session.execute_read(
                self._find_entity,
                self.user_id,
                entity_type,
                name
            )
            return result
    
    @staticmethod
    def _find_entity(tx, user_id: str, entity_type: str, name: str):
        """查找实体事务"""
        query = f"""
        MATCH (e:{entity_type.capitalize()} {{user_id: $user_id, name: $name}})
        RETURN e
        """
        result = tx.run(query, user_id=user_id, name=name)
        record = result.single()
        return dict(record["e"]) if record else None
    
    # ==================== 关系操作 ====================
    
    def add_relationship(
        self,
        source: str,
        target: str,
        relation_type: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """添加关系"""
        properties = properties or {}
        
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_relationship,
                self.user_id,
                source,
                target,
                relation_type,
                properties
            )
            return result
    
    @staticmethod
    def _create_relationship(
        tx,
        user_id: str,
        source: str,
        target: str,
        relation_type: str,
        properties: Dict
    ):
        """创建关系事务"""
        props = {
            "created_at": datetime.now().isoformat(),
            **properties
        }
        
        # 使用节点名称匹配
        query = f"""
        MATCH (a {{user_id: $user_id, name: $source}})
        MATCH (b {{user_id: $user_id, name: $target}})
        MERGE (a)-[r:{relation_type.upper()}]->(b)
        SET r += $props
        RETURN r
        """
        
        result = tx.run(
            query,
            user_id=user_id,
            source=source,
            target=target,
            props=props
        )
        return result.single() is not None
    
    # ==================== 查询操作 ====================
    
    def query(self, question: str) -> Dict[str, Any]:
        """基于图谱回答问题"""
        question_lower = question.lower()
        
        if '为什么' in question or 'why' in question_lower:
            return self._query_causal_chain()
        elif '什么时候' in question or 'when' in question_lower:
            return self._query_temporal_patterns()
        elif '如何' in question or 'how' in question_lower:
            return self._query_recommendations()
        else:
            return self._query_general(question)
    
    def _query_causal_chain(self) -> Dict[str, Any]:
        """查询因果链"""
        with self.driver.session() as session:
            result = session.execute_read(self._find_causal_relations, self.user_id)
            return {
                "question_type": "why",
                "causal_chain": result,
                "answer": self._generate_why_answer(result)
            }
    
    @staticmethod
    def _find_causal_relations(tx, user_id: str):
        """查找因果关系"""
        query = """
        MATCH (a {user_id: $user_id})-[r:CAUSES]->(b {user_id: $user_id})
        RETURN a.name as cause, b.name as effect, r.strength as strength
        LIMIT 10
        """
        result = tx.run(query, user_id=user_id)
        return [
            {
                "cause": record["cause"],
                "effect": record["effect"],
                "strength": record.get("strength", 0.5)
            }
            for record in result
        ]
    
    def _query_temporal_patterns(self) -> Dict[str, Any]:
        """查询时序模式"""
        with self.driver.session() as session:
            result = session.execute_read(self._find_temporal_patterns, self.user_id)
            return {
                "question_type": "when",
                "patterns": result,
                "answer": self._generate_when_answer(result)
            }
    
    @staticmethod
    def _find_temporal_patterns(tx, user_id: str):
        """查找时序模式"""
        query = """
        MATCH (a {user_id: $user_id})-[r:BEFORE|AFTER]->(b {user_id: $user_id})
        RETURN a.name as first, type(r) as relation, b.name as second
        LIMIT 10
        """
        result = tx.run(query, user_id=user_id)
        return [
            {
                "description": f"{record['first']} {record['relation']} {record['second']}"
            }
            for record in result
        ]
    
    def _query_recommendations(self) -> Dict[str, Any]:
        """查询建议"""
        # 简化实现
        return {
            "question_type": "how",
            "recommendations": ["继续保持良好习惯", "注意休息"],
            "answer": "根据知识图谱分析，建议保持当前的健康习惯"
        }
    
    def _query_general(self, question: str) -> Dict[str, Any]:
        """通用查询"""
        with self.driver.session() as session:
            stats = session.execute_read(self._get_graph_stats, self.user_id)
            return {
                "question_type": "general",
                **stats
            }
    
    @staticmethod
    def _get_graph_stats(tx, user_id: str):
        """获取图谱统计"""
        query = """
        MATCH (n {user_id: $user_id})
        OPTIONAL MATCH (n)-[r]->()
        RETURN count(DISTINCT n) as node_count, count(r) as rel_count
        """
        result = tx.run(query, user_id=user_id)
        record = result.single()
        return {
            "entity_count": record["node_count"] if record else 0,
            "relation_count": record["rel_count"] if record else 0
        }
    
    # ==================== 统计和导出 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        with self.driver.session() as session:
            stats = session.execute_read(self._get_detailed_stats, self.user_id)
            return {
                "user_id": self.user_id,
                **stats
            }
    
    @staticmethod
    def _get_detailed_stats(tx, user_id: str):
        """获取详细统计"""
        # 节点统计
        node_query = """
        MATCH (n {user_id: $user_id})
        RETURN labels(n)[0] as type, count(n) as count
        """
        node_result = tx.run(node_query, user_id=user_id)
        nodes_by_type = {record["type"]: record["count"] for record in node_result}
        
        # 关系统计
        rel_query = """
        MATCH ({user_id: $user_id})-[r]->({user_id: $user_id})
        RETURN type(r) as type, count(r) as count
        """
        rel_result = tx.run(rel_query, user_id=user_id)
        rels_by_type = {record["type"]: record["count"] for record in rel_result}
        
        return {
            "entities": {
                "total": sum(nodes_by_type.values()),
                "by_type": nodes_by_type
            },
            "relations": {
                "total": sum(rels_by_type.values()),
                "by_type": rels_by_type
            }
        }
    
    def export(self) -> Dict[str, Any]:
        """导出图谱（用于3D可视化）"""
        with self.driver.session() as session:
            return session.execute_read(self._export_graph, self.user_id)
    
    @staticmethod
    def _export_graph(tx, user_id: str):
        """导出图谱数据"""
        # 导出节点
        node_query = """
        MATCH (n {user_id: $user_id})
        RETURN elementId(n) as id, labels(n)[0] as type, n.name as name, properties(n) as attributes
        """
        node_result = tx.run(node_query, user_id=user_id)
        entities = [
            {
                "id": record["id"],
                "type": record["type"],
                "name": record["name"],
                "attributes": record["attributes"]
            }
            for record in node_result
        ]
        
        # 导出关系
        rel_query = """
        MATCH (a {user_id: $user_id})-[r]->(b {user_id: $user_id})
        RETURN elementId(r) as id, type(r) as type, 
               elementId(a) as source, elementId(b) as target,
               properties(r) as properties
        """
        rel_result = tx.run(rel_query, user_id=user_id)
        relations = [
            {
                "id": record["id"],
                "type": record["type"],
                "source": record["source"],
                "target": record["target"],
                "strength": record["properties"].get("strength", 0.5)
            }
            for record in rel_result
        ]
        
        return {
            "user_id": user_id,
            "entities": entities,
            "relations": relations,
            "patterns": []  # 模式需要单独挖掘
        }
    
    # ==================== 辅助方法 ====================
    
    def _generate_why_answer(self, causal_chain: List[Dict]) -> str:
        """生成"为什么"的答案"""
        if not causal_chain:
            return "暂时没有发现明确的因果关系"
        
        answer = "根据知识图谱分析，可能的原因包括：\n"
        for i, link in enumerate(causal_chain, 1):
            answer += f"{i}. {link['cause']} 导致 {link['effect']} "
            answer += f"(置信度: {link['strength']:.2f})\n"
        
        return answer
    
    def _generate_when_answer(self, patterns: List[Dict]) -> str:
        """生成"什么时候"的答案"""
        if not patterns:
            return "暂时没有发现明显的时间模式"
        
        answer = "根据历史数据分析：\n"
        for pattern in patterns:
            answer += f"- {pattern['description']}\n"
        
        return answer
    
    # ==================== 批量操作 ====================
    
    def build(self, user_history: List[Dict[str, Any]]):
        """从用户历史构建知识图谱"""
        print(f"\n[Neo4j知识图谱] 开始构建用户 {self.user_id} 的知识图谱")
        
        entity_count = 0
        relation_count = 0
        
        for record in user_history:
            # 提取活动实体
            if 'activity' in record:
                self.add_entity(
                    'event',
                    record['activity'],
                    {'timestamp': record.get('timestamp', datetime.now()).isoformat()}
                )
                entity_count += 1
            
            # 提取地点实体
            if 'location' in record:
                self.add_entity('location', record['location'])
                entity_count += 1
                
                # 建立活动-地点关系
                if 'activity' in record:
                    self.add_relationship(
                        record['activity'],
                        record['location'],
                        'LOCATED_AT'
                    )
                    relation_count += 1
        
        print(f"  提取实体: {entity_count} 个")
        print(f"  抽取关系: {relation_count} 个")
    
    def clear_user_data(self):
        """清除用户数据（用于测试）"""
        with self.driver.session() as session:
            session.execute_write(self._delete_user_data, self.user_id)
    
    @staticmethod
    def _delete_user_data(tx, user_id: str):
        """删除用户数据事务"""
        query = """
        MATCH (n {user_id: $user_id})
        DETACH DELETE n
        """
        tx.run(query, user_id=user_id)

    # ==================== 高级查询功能 ====================
    
    def search_entities(self, keyword: str, entity_type: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """搜索实体（模糊匹配）"""
        with self.driver.session() as session:
            return session.execute_read(
                self._search_entities,
                self.user_id,
                keyword,
                entity_type,
                limit
            )
    
    @staticmethod
    def _search_entities(tx, user_id: str, keyword: str, entity_type: Optional[str], limit: int):
        """搜索实体事务"""
        if entity_type:
            query = f"""
            MATCH (e:{entity_type.capitalize()} {{user_id: $user_id}})
            WHERE e.name CONTAINS $keyword
            RETURN e, labels(e)[0] as type
            LIMIT $limit
            """
        else:
            query = """
            MATCH (e {user_id: $user_id})
            WHERE e.name CONTAINS $keyword
            RETURN e, labels(e)[0] as type
            LIMIT $limit
            """
        
        result = tx.run(query, user_id=user_id, keyword=keyword, limit=limit)
        return [
            {
                "id": record["e"].element_id,
                "type": record["type"],
                **dict(record["e"])
            }
            for record in result
        ]
    
    def get_entities_by_type(self, entity_type: str, limit: int = 100) -> List[Dict]:
        """按类型获取实体"""
        with self.driver.session() as session:
            return session.execute_read(
                self._get_entities_by_type,
                self.user_id,
                entity_type,
                limit
            )
    
    @staticmethod
    def _get_entities_by_type(tx, user_id: str, entity_type: str, limit: int):
        """按类型获取实体事务"""
        query = f"""
        MATCH (e:{entity_type.capitalize()} {{user_id: $user_id}})
        RETURN e
        ORDER BY e.created_at DESC
        LIMIT $limit
        """
        result = tx.run(query, user_id=user_id, limit=limit)
        return [dict(record["e"]) for record in result]
    
    def get_entity_relationships(self, entity_name: str) -> List[Dict]:
        """获取实体的所有关系"""
        with self.driver.session() as session:
            return session.execute_read(
                self._get_entity_relationships,
                self.user_id,
                entity_name
            )
    
    @staticmethod
    def _get_entity_relationships(tx, user_id: str, entity_name: str):
        """获取实体关系事务"""
        query = """
        MATCH (e {user_id: $user_id, name: $entity_name})-[r]-(other {user_id: $user_id})
        RETURN type(r) as relation_type, 
               e.name as source,
               other.name as target,
               labels(other)[0] as target_type,
               properties(r) as properties
        """
        result = tx.run(query, user_id=user_id, entity_name=entity_name)
        return [
            {
                "relation_type": record["relation_type"],
                "source": record["source"],
                "target": record["target"],
                "target_type": record["target_type"],
                "properties": record["properties"]
            }
            for record in result
        ]
    
    def find_path(self, source: str, target: str, max_depth: int = 3) -> List[Dict]:
        """查找两个实体之间的路径"""
        with self.driver.session() as session:
            return session.execute_read(
                self._find_path,
                self.user_id,
                source,
                target,
                max_depth
            )
    
    @staticmethod
    def _find_path(tx, user_id: str, source: str, target: str, max_depth: int):
        """查找路径事务"""
        query = """
        MATCH path = shortestPath(
            (a {user_id: $user_id, name: $source})-[*..%d]-(b {user_id: $user_id, name: $target})
        )
        RETURN [node in nodes(path) | node.name] as nodes,
               [rel in relationships(path) | type(rel)] as relations
        LIMIT 5
        """ % max_depth
        
        result = tx.run(query, user_id=user_id, source=source, target=target)
        return [
            {
                "nodes": record["nodes"],
                "relations": record["relations"]
            }
            for record in result
        ]
    
    def get_central_nodes(self, limit: int = 10) -> List[Dict]:
        """获取中心节点（连接最多的节点）"""
        with self.driver.session() as session:
            return session.execute_read(
                self._get_central_nodes,
                self.user_id,
                limit
            )
    
    @staticmethod
    def _get_central_nodes(tx, user_id: str, limit: int):
        """获取中心节点事务"""
        query = """
        MATCH (n {user_id: $user_id})-[r]-()
        WITH n, count(r) as degree
        RETURN n.name as name, 
               labels(n)[0] as type,
               degree
        ORDER BY degree DESC
        LIMIT $limit
        """
        result = tx.run(query, user_id=user_id, limit=limit)
        return [
            {
                "name": record["name"],
                "type": record["type"],
                "degree": record["degree"]
            }
            for record in result
        ]
    
    def delete_entity(self, entity_name: str) -> bool:
        """删除实体及其关系"""
        with self.driver.session() as session:
            return session.execute_write(
                self._delete_entity,
                self.user_id,
                entity_name
            )
    
    @staticmethod
    def _delete_entity(tx, user_id: str, entity_name: str):
        """删除实体事务"""
        query = """
        MATCH (e {user_id: $user_id, name: $entity_name})
        DETACH DELETE e
        RETURN count(e) as deleted
        """
        result = tx.run(query, user_id=user_id, entity_name=entity_name)
        record = result.single()
        return record["deleted"] > 0 if record else False
    
    def update_entity(self, entity_name: str, attributes: Dict[str, Any]) -> bool:
        """更新实体属性"""
        with self.driver.session() as session:
            return session.execute_write(
                self._update_entity,
                self.user_id,
                entity_name,
                attributes
            )
    
    @staticmethod
    def _update_entity(tx, user_id: str, entity_name: str, attributes: Dict):
        """更新实体事务"""
        query = """
        MATCH (e {user_id: $user_id, name: $entity_name})
        SET e += $attributes
        RETURN e
        """
        result = tx.run(query, user_id=user_id, entity_name=entity_name, attributes=attributes)
        return result.single() is not None
