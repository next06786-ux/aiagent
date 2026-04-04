"""
知识图谱 - 统一的知识图谱系统
Knowledge Graph

支持三种视图模式:
- 人物关系视图：展示人际网络和社交关系
- 升学规划视图：展示学习路径和教育规划
- 职业发展视图：展示职业技能和发展路径

核心理念:
- 信息（概念/实体/事件）是节点
- 照片/记录是来源，用于溯源
- 关系是信息之间的语义连接
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()


class InformationKnowledgeGraph:
    """知识图谱 - 支持人物关系、升学规划、职业发展三种视图"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 从环境变量读取配置
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print(f"✅ 知识图谱连接成功: {uri}")
        except Exception as e:
            print(f"❌ Neo4j 连接失败: {e}")
            raise
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ==================== 信息节点操作 ====================
    
    def add_information(
        self,
        name: str,
        info_type: str,  # concept, entity, event, pattern
        category: str,
        confidence: float = 0.8,
        attributes: Dict[str, Any] = None
    ) -> str:
        """添加信息节点"""
        attributes = attributes or {}
        
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_information,
                self.user_id,
                name,
                info_type,
                category,
                confidence,
                attributes
            )
            return result
    
    @staticmethod
    def _create_information(tx, user_id, name, info_type, category, confidence, attributes):
        """创建信息节点事务"""
        # 确定节点标签
        label_map = {
            "concept": "Concept",
            "entity": "Entity",
            "event": "Event",
            "pattern": "Pattern"
        }
        label = label_map.get(info_type, "Information")
        
        props = {
            "user_id": user_id,
            "name": name,
            "type": info_type,
            "category": category,
            "confidence": confidence,
            "created_at": datetime.now().isoformat(),
            "mention_count": 1,
            **attributes
        }
        
        # 使用 MERGE 避免重复，如果存在则更新
        query = f"""
        MERGE (i:{label} {{user_id: $user_id, name: $name}})
        ON CREATE SET i += $props, i.first_mentioned = $created_at
        ON MATCH SET 
            i.mention_count = i.mention_count + 1,
            i.confidence = CASE 
                WHEN $confidence > i.confidence THEN $confidence 
                ELSE i.confidence 
            END,
            i.last_mentioned = $created_at
        RETURN elementId(i) as id
        """
        
        result = tx.run(
            query,
            user_id=user_id,
            name=name,
            props=props,
            created_at=datetime.now().isoformat(),
            confidence=confidence
        )
        record = result.single()
        return record["id"] if record else None
    
    # ==================== 来源节点操作 ====================
    
    def add_source(
        self,
        source_type: str,  # photo, sensor_record, conversation, manual_input
        source_id: str,
        timestamp: int,
        metadata: Dict[str, Any] = None
    ) -> str:
        """添加来源节点（用于溯源）"""
        metadata = metadata or {}
        
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_source,
                self.user_id,
                source_type,
                source_id,
                timestamp,
                metadata
            )
            return result
    
    @staticmethod
    def _create_source(tx, user_id, source_type, source_id, timestamp, metadata):
        """创建来源节点事务"""
        props = {
            "user_id": user_id,
            "source_id": source_id,
            "type": source_type,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            **metadata
        }
        
        query = """
        MERGE (s:Source {user_id: $user_id, source_id: $source_id})
        SET s += $props
        RETURN elementId(s) as id
        """
        
        result = tx.run(query, user_id=user_id, source_id=source_id, props=props)
        record = result.single()
        return record["id"] if record else None
    
    # ==================== 关系操作 ====================
    
    def add_information_relationship(
        self,
        source_name: str,
        target_name: str,
        relation_type: str,  # INCLUDES, CAUSES, REQUIRES, OCCURS_AT, etc.
        properties: Dict[str, Any] = None
    ) -> bool:
        """添加信息之间的关系"""
        properties = properties or {}
        
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_info_relationship,
                self.user_id,
                source_name,
                target_name,
                relation_type,
                properties
            )
            return result
    
    @staticmethod
    def _create_info_relationship(tx, user_id, source_name, target_name, relation_type, properties):
        """创建信息关系事务"""
        props = {
            "created_at": datetime.now().isoformat(),
            **properties
        }
        
        query = f"""
        MATCH (a {{user_id: $user_id, name: $source_name}})
        MATCH (b {{user_id: $user_id, name: $target_name}})
        MERGE (a)-[r:{relation_type}]->(b)
        SET r += $props
        RETURN r
        """
        
        result = tx.run(
            query,
            user_id=user_id,
            source_name=source_name,
            target_name=target_name,
            props=props
        )
        return result.single() is not None
    
    def add_source_relationship(
        self,
        info_name: str,
        source_id: str,
        relation_type: str = "EXTRACTED_FROM",  # EXTRACTED_FROM, RECORDED_IN, MENTIONED_IN
        confidence: float = 0.8
    ) -> bool:
        """添加信息到来源的溯源关系"""
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_source_relationship,
                self.user_id,
                info_name,
                source_id,
                relation_type,
                confidence
            )
            return result
    
    @staticmethod
    def _create_source_relationship(tx, user_id, info_name, source_id, relation_type, confidence):
        """创建溯源关系事务"""
        query = f"""
        MATCH (i {{user_id: $user_id, name: $info_name}})
        MATCH (s:Source {{user_id: $user_id, source_id: $source_id}})
        MERGE (i)-[r:{relation_type}]->(s)
        SET r.confidence = $confidence, r.created_at = $created_at
        RETURN r
        """
        
        result = tx.run(
            query,
            user_id=user_id,
            info_name=info_name,
            source_id=source_id,
            confidence=confidence,
            created_at=datetime.now().isoformat()
        )
        return result.single() is not None
    
    # ==================== 查询操作 ====================
    
    def get_information_sources(self, info_name: str) -> List[Dict]:
        """获取信息的所有来源（溯源）"""
        with self.driver.session() as session:
            return session.execute_read(
                self._find_information_sources,
                self.user_id,
                info_name
            )
    
    @staticmethod
    def _find_information_sources(tx, user_id, info_name):
        """查找信息来源事务"""
        query = """
        MATCH (i {user_id: $user_id, name: $info_name})-[r:EXTRACTED_FROM|RECORDED_IN|MENTIONED_IN]->(s:Source)
        RETURN s, type(r) as relation_type, r.confidence as confidence
        ORDER BY s.timestamp DESC
        """
        
        result = tx.run(query, user_id=user_id, info_name=info_name)
        return [
            {
                "source": dict(record["s"]),
                "relation_type": record["relation_type"],
                "confidence": record.get("confidence", 0.8)
            }
            for record in result
        ]
    
    def get_related_information(self, info_name: str, max_depth: int = 2) -> List[Dict]:
        """获取相关信息"""
        with self.driver.session() as session:
            return session.execute_read(
                self._find_related_information,
                self.user_id,
                info_name,
                max_depth
            )
    
    @staticmethod
    def _find_related_information(tx, user_id, info_name, max_depth):
        """查找相关信息事务"""
        query = f"""
        MATCH (i {{user_id: $user_id, name: $info_name}})-[r*1..{max_depth}]-(related)
        WHERE related.user_id = $user_id AND NOT related:Source
        RETURN DISTINCT related, [rel in r | type(rel)] as path
        LIMIT 20
        """
        
        result = tx.run(query, user_id=user_id, info_name=info_name)
        return [
            {
                "information": dict(record["related"]),
                "path": record["path"]
            }
            for record in result
        ]
    
    def search_information(
        self,
        keyword: str,
        info_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """搜索信息"""
        with self.driver.session() as session:
            return session.execute_read(
                self._search_information,
                self.user_id,
                keyword,
                info_type,
                category,
                limit
            )
    
    @staticmethod
    def _search_information(tx, user_id, keyword, info_type, category, limit):
        """搜索信息事务"""
        conditions = ["i.user_id = $user_id", "i.name CONTAINS $keyword"]
        
        if info_type:
            conditions.append("i.type = $info_type")
        if category:
            conditions.append("i.category = $category")
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        MATCH (i)
        WHERE {where_clause} AND NOT i:Source
        RETURN i
        ORDER BY i.confidence DESC, i.mention_count DESC
        LIMIT $limit
        """
        
        result = tx.run(
            query,
            user_id=user_id,
            keyword=keyword,
            info_type=info_type,
            category=category,
            limit=limit
        )
        return [dict(record["i"]) for record in result]
    
    # ==================== 统计和导出 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.driver.session() as session:
            return session.execute_read(self._get_statistics, self.user_id)
    
    @staticmethod
    def _get_statistics(tx, user_id):
        """获取统计事务"""
        # 信息节点统计
        info_query = """
        MATCH (i {user_id: $user_id})
        WHERE NOT i:Source
        RETURN i.type as type, i.category as category, count(i) as count
        """
        info_result = tx.run(info_query, user_id=user_id)
        
        info_stats = {}
        category_stats = {}
        total_info = 0
        
        for record in info_result:
            info_type = record["type"]
            category = record["category"]
            count = record["count"]
            
            info_stats[info_type] = info_stats.get(info_type, 0) + count
            category_stats[category] = category_stats.get(category, 0) + count
            total_info += count
        
        # 来源节点统计
        source_query = """
        MATCH (s:Source {user_id: $user_id})
        RETURN s.type as type, count(s) as count
        """
        source_result = tx.run(source_query, user_id=user_id)
        
        source_stats = {record["type"]: record["count"] for record in source_result}
        total_sources = sum(source_stats.values())
        
        # 关系统计
        rel_query = """
        MATCH ({user_id: $user_id})-[r]->({user_id: $user_id})
        RETURN type(r) as type, count(r) as count
        """
        rel_result = tx.run(rel_query, user_id=user_id)
        
        rel_stats = {record["type"]: record["count"] for record in rel_result}
        total_relations = sum(rel_stats.values())
        
        return {
            "user_id": user_id,
            "information": {
                "total": total_info,
                "by_type": info_stats,
                "by_category": category_stats
            },
            "sources": {
                "total": total_sources,
                "by_type": source_stats
            },
            "relationships": {
                "total": total_relations,
                "by_type": rel_stats
            }
        }
    
    def export(self) -> Dict[str, Any]:
        """导出知识图谱"""
        with self.driver.session() as session:
            return session.execute_read(self._export_graph, self.user_id)
    
    @staticmethod
    def _export_graph(tx, user_id):
        """导出图谱事务"""
        # 导出信息节点
        info_query = """
        MATCH (i {user_id: $user_id})
        WHERE NOT i:Source
        RETURN elementId(i) as id, labels(i) as labels, properties(i) as props
        """
        info_result = tx.run(info_query, user_id=user_id)
        
        information = [
            {
                "id": record["id"],
                "type": record["labels"][0] if record["labels"] else "Information",
                **record["props"]
            }
            for record in info_result
        ]
        
        # 导出来源节点
        source_query = """
        MATCH (s:Source {user_id: $user_id})
        RETURN elementId(s) as id, properties(s) as props
        """
        source_result = tx.run(source_query, user_id=user_id)
        
        sources = [
            {
                "id": record["id"],
                **record["props"]
            }
            for record in source_result
        ]
        
        # 导出关系
        rel_query = """
        MATCH (a {user_id: $user_id})-[r]->(b {user_id: $user_id})
        RETURN elementId(a) as source, elementId(b) as target, 
               type(r) as type, properties(r) as props
        """
        rel_result = tx.run(rel_query, user_id=user_id)
        
        relationships = [
            {
                "source": record["source"],
                "target": record["target"],
                "type": record["type"],
                **record["props"]
            }
            for record in rel_result
        ]
        
        return {
            "user_id": user_id,
            "information": information,
            "sources": sources,
            "relationships": relationships
        }
    
    def clear_user_data(self):
        """清除用户数据"""
        with self.driver.session() as session:
            session.execute_write(self._delete_user_data, self.user_id)
    
    @staticmethod
    def _delete_user_data(tx, user_id):
        """删除用户数据事务"""
        query = """
        MATCH (n {user_id: $user_id})
        DETACH DELETE n
        """
        tx.run(query, user_id=user_id)
