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
            i += $props,
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
    
    # ==================== User节点操作 ====================
    
    def ensure_user_exists(self) -> str:
        """确保User节点存在，如果不存在则创建"""
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_or_get_user,
                self.user_id
            )
            return result
    
    @staticmethod
    def _create_or_get_user(tx, user_id):
        """创建或获取User节点"""
        query = """
        MERGE (u:User {user_id: $user_id})
        ON CREATE SET 
            u.created_at = datetime(),
            u.updated_at = datetime()
        ON MATCH SET
            u.updated_at = datetime()
        RETURN elementId(u) as id
        """
        result = tx.run(query, user_id=user_id)
        record = result.single()
        return record["id"] if record else None
    
    # ==================== 关系操作 ====================
    
    def add_user_relationship(
        self,
        target_name: str,
        relation_type: str,  # HAS_PROFILE, PARTICIPATED_IN, INTERESTED_IN, KNOWS, APPLIED_TO
        properties: Dict[str, Any] = None
    ) -> bool:
        """添加User到信息节点的关系"""
        properties = properties or {}
        
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_user_relationship,
                self.user_id,
                target_name,
                relation_type,
                properties
            )
            return result
    
    @staticmethod
    def _create_user_relationship(tx, user_id, target_name, relation_type, properties):
        """创建User关系事务"""
        props = {
            "created_at": datetime.now().isoformat(),
            **properties
        }
        
        query = f"""
        MATCH (u:User {{user_id: $user_id}})
        MATCH (target {{user_id: $user_id, name: $target_name}})
        MERGE (u)-[r:{relation_type}]->(target)
        SET r += $props
        RETURN r
        """
        
        result = tx.run(
            query,
            user_id=user_id,
            target_name=target_name,
            props=props
        )
        return result.single() is not None
    
    def add_information_relationship(
        self,
        source_name: str,
        target_name: str,
        relation_type: str,  # RELATED_TO, PART_OF, HAPPENED_AT, INVOLVES, REQUIRES, LOCATED_IN
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
    
    
    def add_pattern_relationship(
        self,
        pattern_name: str,
        target_name: str,
        relation_type: str,  # EXHIBITS, SUPPORTS, INFLUENCES
        properties: Dict[str, Any] = None
    ) -> bool:
        """添加模式相关的关系"""
        properties = properties or {}
        
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_pattern_relationship,
                self.user_id,
                pattern_name,
                target_name,
                relation_type,
                properties
            )
            return result
    
    @staticmethod
    def _create_pattern_relationship(tx, user_id, pattern_name, target_name, relation_type, properties):
        """创建模式关系事务"""
        props = {
            "created_at": datetime.now().isoformat(),
            **properties
        }
        
        # 根据关系类型确定方向
        if relation_type == "EXHIBITS":
            # User-EXHIBITS->Pattern
            query = f"""
            MATCH (u:User {{user_id: $user_id}})
            MATCH (p {{user_id: $user_id, name: $pattern_name}})
            MERGE (u)-[r:{relation_type}]->(p)
            SET r += $props
            RETURN r
            """
            result = tx.run(query, user_id=user_id, pattern_name=pattern_name, props=props)
        elif relation_type == "SUPPORTS":
            # Entity/Event-SUPPORTS->Pattern
            query = f"""
            MATCH (source {{user_id: $user_id, name: $target_name}})
            MATCH (p {{user_id: $user_id, name: $pattern_name}})
            MERGE (source)-[r:{relation_type}]->(p)
            SET r += $props
            RETURN r
            """
            result = tx.run(query, user_id=user_id, pattern_name=pattern_name, target_name=target_name, props=props)
        else:  # INFLUENCES
            # Pattern-INFLUENCES->Pattern
            query = f"""
            MATCH (p1 {{user_id: $user_id, name: $pattern_name}})
            MATCH (p2 {{user_id: $user_id, name: $target_name}})
            MERGE (p1)-[r:{relation_type}]->(p2)
            SET r += $props
            RETURN r
            """
            result = tx.run(query, user_id=user_id, pattern_name=pattern_name, target_name=target_name, props=props)
        
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
        from datetime import datetime as dt
        
        def serialize_value(value):
            """序列化Neo4j值为JSON兼容格式"""
            if hasattr(value, 'iso_format'):  # Neo4j DateTime
                return value.iso_format()
            elif isinstance(value, dt):
                return value.isoformat()
            elif isinstance(value, (list, tuple)):
                return [serialize_value(v) for v in value]
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            else:
                return value
        
        # 导出信息节点
        info_query = """
        MATCH (i {user_id: $user_id})
        WHERE NOT i:Source
        RETURN elementId(i) as id, labels(i) as labels, properties(i) as props
        """
        info_result = tx.run(info_query, user_id=user_id)
        
        information = []
        for record in info_result:
            props = {k: serialize_value(v) for k, v in record["props"].items()}
            information.append({
                "id": record["id"],
                "type": record["labels"][0] if record["labels"] else "Information",
                **props
            })
        
        # 导出来源节点
        source_query = """
        MATCH (s:Source {user_id: $user_id})
        RETURN elementId(s) as id, properties(s) as props
        """
        source_result = tx.run(source_query, user_id=user_id)
        
        sources = []
        for record in source_result:
            props = {k: serialize_value(v) for k, v in record["props"].items()}
            sources.append({
                "id": record["id"],
                **props
            })
        
        # 导出关系
        rel_query = """
        MATCH (a {user_id: $user_id})-[r]->(b {user_id: $user_id})
        RETURN elementId(a) as source, elementId(b) as target, 
               type(r) as type, properties(r) as props
        """
        rel_result = tx.run(rel_query, user_id=user_id)
        
        relationships = []
        for record in rel_result:
            props = {k: serialize_value(v) for k, v in record["props"].items()}
            relationships.append({
                "source": record["source"],
                "target": record["target"],
                "type": record["type"],
                **props
            })
        
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
    
    # ==================== 人际关系查询 ====================
    
    def get_relationships(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取用户的人际关系
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            人际关系列表，每个关系包含 relationship_type 和 person_name
        """
        with self.driver.session() as session:
            return session.execute_read(
                self._find_relationships,
                user_id,
                limit
            )
    
    @staticmethod
    def _find_relationships(tx, user_id: str, limit: int):
        """查找人际关系事务"""
        # 查询Person类型的实体节点及其关系
        query = """
        MATCH (u:Entity {user_id: $user_id, category: 'person'})
        OPTIONAL MATCH (u)-[r:RELATES_TO]->(other:Entity {category: 'person'})
        RETURN u.name as person_name, 
               type(r) as relationship_type,
               other.name as related_person,
               u.confidence as confidence
        LIMIT $limit
        """
        
        result = tx.run(query, user_id=user_id, limit=limit)
        relationships = []
        
        for record in result:
            person_name = record.get('person_name')
            relationship_type = record.get('relationship_type', '认识')
            related_person = record.get('related_person')
            confidence = record.get('confidence', 0.8)
            
            if person_name:
                relationships.append({
                    'person_name': person_name,
                    'relationship_type': relationship_type or '认识',
                    'related_person': related_person,
                    'confidence': confidence
                })
        
        return relationships
    
    def get_nodes_by_type(self, user_id: str, node_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        根据类型获取节点
        
        Args:
            user_id: 用户ID
            node_type: 节点类型（如 School, Company 等）
            limit: 返回数量限制
            
        Returns:
            节点列表
        """
        with self.driver.session() as session:
            return session.execute_read(
                self._find_nodes_by_type,
                user_id,
                node_type,
                limit
            )
    
    @staticmethod
    def _find_nodes_by_type(tx, user_id: str, node_type: str, limit: int):
        """根据类型查找节点事务"""
        # 根据category查找实体节点
        query = """
        MATCH (n:Entity {user_id: $user_id})
        WHERE n.category = $category OR n.type = $category
        RETURN n.name as name,
               n.category as category,
               n.type as type,
               n.confidence as confidence,
               n.attributes as attributes
        LIMIT $limit
        """
        
        # 将节点类型转换为小写的category
        category = node_type.lower()
        
        result = tx.run(query, user_id=user_id, category=category, limit=limit)
        nodes = []
        
        for record in result:
            nodes.append({
                'name': record.get('name'),
                'category': record.get('category'),
                'type': record.get('type'),
                'confidence': record.get('confidence', 0.8),
                'attributes': record.get('attributes', {})
            })
        
        return nodes

    def update_node_metadata(self, node_id: str, metadata: Dict[str, Any]) -> bool:
        """
        更新节点的metadata
        
        Args:
            node_id: 节点ID
            metadata: 要更新的metadata字典
            
        Returns:
            是否更新成功
        """
        with self.driver.session() as session:
            return session.execute_write(
                self._update_node_metadata,
                self.user_id,
                node_id,
                metadata
            )
    
    @staticmethod
    def _update_node_metadata(tx, user_id: str, node_id: str, metadata: Dict[str, Any]):
        """更新节点metadata事务"""
        query = """
        MATCH (n:Entity {user_id: $user_id})
        WHERE elementId(n) = $node_id
        SET n += $metadata
        RETURN n
        """
        
        result = tx.run(query, user_id=user_id, node_id=node_id, metadata=metadata)
        return result.single() is not None

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

    def delete_node(self, node_id: str, node_type: str = None) -> Dict[str, Any]:
        """
        删除指定节点及其所有关系
        
        Args:
            node_id: 节点的唯一标识（通常是name属性）
            node_type: 节点类型（Entity, Event, Concept, Pattern等），可选
        
        Returns:
            删除结果字典，包含删除的节点和关系数量
        """
        with self.driver.session() as session:
            return session.execute_write(
                self._delete_node,
                self.user_id,
                node_id,
                node_type
            )
    
    @staticmethod
    def _delete_node(tx, user_id: str, node_id: str, node_type: str = None):
        """删除节点事务"""
        # 先查询节点是否存在
        if node_type:
            check_query = f"""
            MATCH (n:{node_type} {{user_id: $user_id, name: $node_id}})
            RETURN count(n) as count
            """
        else:
            check_query = """
            MATCH (n {user_id: $user_id, name: $node_id})
            RETURN count(n) as count, labels(n)[0] as node_type
            """
        
        check_result = tx.run(check_query, user_id=user_id, node_id=node_id)
        check_record = check_result.single()
        
        if not check_record or check_record["count"] == 0:
            return {
                "success": False,
                "message": f"节点不存在: {node_id}",
                "deleted_nodes": 0,
                "deleted_relationships": 0
            }
        
        # 统计要删除的关系数量
        if node_type:
            count_query = f"""
            MATCH (n:{node_type} {{user_id: $user_id, name: $node_id}})-[r]-()
            RETURN count(r) as rel_count
            """
        else:
            count_query = """
            MATCH (n {user_id: $user_id, name: $node_id})-[r]-()
            RETURN count(r) as rel_count
            """
        
        count_result = tx.run(count_query, user_id=user_id, node_id=node_id)
        rel_count = count_result.single()["rel_count"]
        
        # 删除节点及其所有关系
        if node_type:
            delete_query = f"""
            MATCH (n:{node_type} {{user_id: $user_id, name: $node_id}})
            DETACH DELETE n
            RETURN count(n) as deleted_count
            """
        else:
            delete_query = """
            MATCH (n {user_id: $user_id, name: $node_id})
            DETACH DELETE n
            RETURN count(n) as deleted_count
            """
        
        delete_result = tx.run(delete_query, user_id=user_id, node_id=node_id)
        deleted_count = delete_result.single()["deleted_count"]
        
        return {
            "success": True,
            "message": f"成功删除节点: {node_id}",
            "deleted_nodes": deleted_count,
            "deleted_relationships": rel_count,
            "node_id": node_id,
            "node_type": node_type or check_record.get("node_type", "Unknown")
        }
