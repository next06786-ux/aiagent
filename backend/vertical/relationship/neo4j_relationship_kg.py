"""
基于Neo4j的人际关系知识图谱构建器
完全基于Neo4j架构规范（6种节点+4类关系）
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import math
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from backend.vertical.unified_kg_query import UnifiedKGQuery

load_dotenv()

@dataclass
class RelationshipUserProfile:
    """用户人际关系档案"""
    user_id: str
    name: str = "我"
    question: str = ""  # 用户问题（用于聚焦子图）
    session_id: str = None  # 会话ID
    # 关系分类（用于筛选）
    focus_categories: List[str] = None  # ["family", "friends", "colleagues"]
    
    def __post_init__(self):
        if self.focus_categories is None:
            self.focus_categories = []


class Neo4jRelationshipKnowledgeGraph:
    """基于Neo4j的人际关系知识图谱构建器"""
    
    def __init__(self):
        # 连接Neo4j
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.unified_query = UnifiedKGQuery(self.driver)
    
    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.close()
    
    def get_complete_relationship_data(self, user_id: str) -> Dict[str, Any]:
        """
        使用统一框架获取完整的人际关系数据
        包含所有6种节点和4类关系
        """
        return self.unified_query.query_complete_domain_data(user_id, 'relationship')
    
    def _get_people_from_neo4j(self, user_id: str, categories: List[str] = None, limit: int = 50) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        从Neo4j获取完整的人际关系数据
        充分利用6种节点和4类关系
        
        Returns:
            (people, events, patterns): 人物列表、事件列表、模式列表
        """
        try:
            with self.driver.session() as session:
                # 1. 查询User-KNOWS->Person关系（用户相关关系）
                people_query = """
                MATCH (u:User {user_id: $user_id})-[r:KNOWS]->(p:Entity)
                WHERE p.type = 'Person'
                OPTIONAL MATCH (p)-[:EXTRACTED_FROM]->(s:Source)
                RETURN p.name as name,
                       elementId(p) as person_id,
                       p.category as category,
                       p.description as description,
                       p.attributes as attributes,
                       p.confidence as confidence,
                       r.relationship_type as relationship_type,
                       r.closeness as closeness,
                       r.since as since,
                       collect(DISTINCT s.source_id) as sources
                ORDER BY r.closeness DESC
                LIMIT $limit
                """
                
                people_result = session.run(people_query, user_id=user_id, limit=limit)
                people = []
                
                for record in people_result:
                    category = record['category'] or 'weak_ties'
                    
                    # 如果指定了类别筛选，则过滤
                    if categories and category not in categories:
                        continue
                    
                    # 安全处理attributes（可能是字典、字符串或None）
                    attributes = record['attributes']
                    if isinstance(attributes, str):
                        # 如果是字符串，尝试解析为字典
                        try:
                            import json
                            attributes = json.loads(attributes)
                        except:
                            attributes = {}
                    elif not isinstance(attributes, dict):
                        attributes = {}
                    
                    people.append({
                        'name': record['name'],
                        'person_id': record['person_id'],
                        'relationship_type': record['relationship_type'] or 'KNOWS',
                        'category': category,
                        'strength': record['closeness'] or 0.5,
                        'frequency': record['confidence'] or 0.5,
                        'occupation': attributes.get('company', attributes.get('role', '')),
                        'location': attributes.get('location', ''),
                        'description': record['description'] or '',
                        'since': record['since'],
                        'sources': record['sources'],
                        'source': 'neo4j_graph'
                    })
                
                # 只在调试模式下打印
                if os.getenv("DEBUG_MODE") == "true":
                    print(f"[Neo4jRelationshipKG] 从Neo4j获取到 {len(people)} 个人际关系（通过KNOWS关系）")
                
                # 2. 查询Event-INVOLVES->Person关系（实体间关系）
                events_query = """
                MATCH (u:User {user_id: $user_id})-[:PARTICIPATED_IN]->(e:Event)-[:INVOLVES]->(p:Entity)
                WHERE p.type = 'Person'
                RETURN e.name as event_name,
                       elementId(e) as event_id,
                       e.type as event_type,
                       e.description as description,
                       e.start_time as start_time,
                       e.location as location,
                       e.participants as participants,
                       collect(DISTINCT p.name) as involved_people
                ORDER BY e.start_time DESC
                LIMIT $limit
                """
                
                events_result = session.run(events_query, user_id=user_id, limit=limit)
                events = []
                
                for record in events_result:
                    events.append({
                        'name': record['event_name'],
                        'event_id': record['event_id'],
                        'type': record['event_type'] or 'Activity',
                        'description': record['description'] or '',
                        'start_time': record['start_time'],
                        'location': record['location'] or '',
                        'participants': record['participants'] or [],
                        'involved_people': record['involved_people']
                    })
                
                if os.getenv("DEBUG_MODE") == "true":
                    print(f"[Neo4jRelationshipKG] 获取到 {len(events)} 个相关事件（通过PARTICIPATED_IN和INVOLVES关系）")
                
                # 3. 查询User-EXHIBITS->Pattern关系（模式关系）
                patterns_query = """
                MATCH (u:User {user_id: $user_id})-[r:EXHIBITS]->(pat:Pattern)
                WHERE pat.type IN ['Habit', 'Preference', 'DecisionPattern']
                OPTIONAL MATCH (evidence)-[:SUPPORTS]->(pat)
                RETURN pat.name as pattern_name,
                       elementId(pat) as pattern_id,
                       pat.type as pattern_type,
                       pat.description as description,
                       pat.frequency as frequency,
                       pat.confidence as confidence,
                       r.frequency as user_frequency,
                       collect(DISTINCT evidence.name) as evidence_list
                ORDER BY pat.frequency DESC
                LIMIT 10
                """
                
                patterns_result = session.run(patterns_query, user_id=user_id)
                patterns = []
                
                for record in patterns_result:
                    patterns.append({
                        'name': record['pattern_name'],
                        'pattern_id': record['pattern_id'],
                        'type': record['pattern_type'] or 'Habit',
                        'description': record['description'] or '',
                        'frequency': record['frequency'] or 1,
                        'confidence': record['confidence'] or 0.5,
                        'user_frequency': record['user_frequency'] or 1,
                        'evidence': record['evidence_list']
                    })
                
                if os.getenv("DEBUG_MODE") == "true":
                    print(f"[Neo4jRelationshipKG] 获取到 {len(patterns)} 个行为模式（通过EXHIBITS关系）")
                
                return people, events, patterns
                
        except Exception as e:
            print(f"[Neo4jRelationshipKG] 从Neo4j获取数据失败: {e}")
            import traceback
            traceback.print_exc()
            return [], [], []

    def _get_people_with_hybrid_retrieval(
        self,
        user_id: str,
        query: str = "",
        categories: List[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        使用混合检索获取人际关系信息
        融合Neo4j图谱和RAG向量检索的结果
        """
        try:
            from backend.learning.kg_rag_integration import KGRAGIntegration
            
            # 构建查询
            if not query:
                query = "人际关系信息"
            
            print(f"[Neo4jRelationshipKG] 使用混合检索查询人际关系: {query}")
            
            # 使用混合检索
            kg_rag = KGRAGIntegration(user_id)
            results = kg_rag.hybrid_retrieve(
                query=query,
                query_type="RELATIONAL",  # 查询关系信息
                domain="relationship",
                top_k=limit
            )
            
            # 转换为人物格式
            people = []
            for result in results:
                # 检查是否是人物相关信息
                content = result.get('content', '')
                metadata = result.get('metadata', {})
                
                # 从内容中提取人物信息
                if 'Person' in content or '人物' in content:
                    person_name = metadata.get('entity_name', '')
                    if not person_name:
                        # 尝试从内容中提取
                        if '】' in content:
                            person_name = content.split('】')[1].split('，')[0]
                    
                    if person_name:
                        # 推断关系类型
                        relationship_type = "KNOWS"
                        category = "weak_ties"
                        
                        if '家人' in content or '父母' in content or '兄弟' in content or '姐妹' in content:
                            relationship_type = "FAMILY"
                            category = "family"
                        elif '朋友' in content or '好友' in content or '闺蜜' in content:
                            relationship_type = "FRIEND"
                            category = "close_friends"
                        elif '同事' in content or '同学' in content or '导师' in content:
                            relationship_type = "COLLEAGUE"
                            category = "colleagues"
                        
                        # 如果指定了类别筛选，则过滤
                        if categories and category not in categories:
                            continue
                        
                        people.append({
                            'name': person_name,
                            'person_id': metadata.get('neo4j_node_name', ''),
                            'relationship_type': relationship_type,
                            'category': category,
                            'strength': result.get('score', 0.5),
                            'frequency': result.get('score', 0.5),
                            'confidence': result.get('score', 0.5),
                            'occupation': '',
                            'location': '',
                            'source': result.get('source', 'hybrid')
                        })
            
            print(f"[Neo4jRelationshipKG] 混合检索获取到 {len(people)} 个人际关系")
            return people[:limit]
            
        except Exception as e:
            print(f"[Neo4jRelationshipKG] 混合检索失败，降级到Neo4j查询: {e}")
            import traceback
            traceback.print_exc()
            # 降级到传统方法
            return self._get_people_from_neo4j(user_id, categories, limit)
    
    def build_relationship_graph(self, user_profile: RelationshipUserProfile, 
                                use_hybrid: bool = False) -> Dict[str, Any]:
        """
        构建人际关系知识图谱 - 完全基于Neo4j架构规范（6种节点+4类关系）
        
        图谱结构（3D立体布局）：
        - 中心：User（我）
        - 第1层：人物层（Entity节点，type='Person'）
        - 第2层：事件层（Event节点，社交活动）
        - 第3层：地点层（Entity节点，type='Location'）
        - 模式层：社交模式（Pattern节点）
        
        关系链：
        - User-KNOWS->Entity(Person)
        - User-PARTICIPATED_IN->Event
        - Event-INVOLVES->Entity(Person)
        - Event-HAPPENED_AT->Entity(Location)
        - User-EXHIBITS->Pattern
        
        Args:
            user_profile: 用户人际关系档案
            use_hybrid: 是否使用混合检索（Neo4j + RAG）
        """
        # 使用统一框架获取完整数据
        complete_data = self.get_complete_relationship_data(user_profile.user_id)
        
        # 初始化节点和边
        nodes = [{
            "id": "__me__", 
            "label": "我", 
            "type": "center", 
            "layer": 0,
            "position": {"x": 0, "y": 0, "z": 0}, 
            "size": 20, 
            "color": "#e8f4ff",
            "is_self": True,
            "metadata": {
                "user_id": user_profile.user_id,
                "name": user_profile.name,
                "node_type": "User"
            }
        }]
        edges = []
        
        # 提取数据
        entities = complete_data.get('entities', [])
        events = complete_data.get('events', [])
        concepts = complete_data.get('concepts', [])
        patterns = complete_data.get('patterns', [])
        
        # 分离人物和地点
        people = [e for e in entities if e.get('type') == 'Person']
        locations = [e for e in entities if e.get('type') == 'Location']
        
        # 第一圈：人物层（Entity(Person)节点）
        people_nodes, people_edges = self._build_people_layer_from_entities(people, events)
        
        # 为每个人物节点附加相关信息
        for person_node in people_nodes:
            person_name = person_node['label']
            
            # 附加与该人物相关的事件
            related_events = []
            for event in events:
                # 检查事件是否涉及该人物
                if any(
                    r.get('relation') == 'INVOLVES' and r.get('target', {}).get('name') == person_name
                    for r in event.get('entity_relations', [])
                ):
                    related_events.append({
                        'name': event.get('name'),
                        'type': event.get('type'),
                        'description': event.get('description', ''),
                        'time': event.get('time', '')
                    })
            
            # 附加与该人物相关的地点
            related_locations = []
            for event in related_events:
                for loc in locations:
                    # 查找事件发生的地点
                    event_full = next((e for e in events if e.get('name') == event['name']), None)
                    if event_full and any(
                        r.get('relation') == 'HAPPENED_AT' and r.get('target', {}).get('name') == loc.get('name')
                        for r in event_full.get('entity_relations', [])
                    ):
                        if loc.get('name') not in [l['name'] for l in related_locations]:
                            related_locations.append({
                                'name': loc.get('name'),
                                'description': loc.get('description', '')
                            })
            
            # 附加到节点metadata
            person_node['metadata']['related_events'] = related_events
            person_node['metadata']['related_locations'] = related_locations
            person_node['metadata']['event_count'] = len(related_events)
            person_node['metadata']['location_count'] = len(related_locations)
        
        nodes.extend(people_nodes)
        edges.extend(people_edges)
        
        # 附加用户级别的模式信息(不作为节点,作为全局信息)
        user_patterns = []
        for pattern in patterns:
            user_patterns.append({
                'name': pattern.get('name'),
                'type': pattern.get('type'),
                'description': pattern.get('description', ''),
                'frequency': pattern.get('frequency', 1),
                'confidence': pattern.get('confidence', 0.5)
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layers": {
                "people": [n["id"] for n in people_nodes]
            },
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": {
                    "User": 1,
                    "Entity_Person": len(people_nodes)
                },
                "relationship_types": {
                    "KNOWS": len([e for e in edges if e['type'] == 'KNOWS'])
                },
                "user_patterns": user_patterns,  # 用户的社交模式
                "total_events": len(events),
                "total_locations": len(locations),
                "total_concepts": len(concepts),
                "data_source": "unified_kg_query",
                "architecture_compliant": True,
                "display_mode": "people_only_in_3d"
            }
        }
        edges.extend(family_edges)
        
        # 第二圈：好友层
        close_friend_nodes, close_friend_edges = self._build_people_layer(close_friends, 2, 38, "#52C41A", "close_friends")
        nodes.extend(close_friend_nodes)
        edges.extend(close_friend_edges)
        
        # 第三圈：朋友层
        friend_nodes, friend_edges = self._build_people_layer(friends, 2, 38, "#1890FF", "friends")
        nodes.extend(friend_nodes)
        edges.extend(friend_edges)
        
        # 第四圈：同事层
        colleague_nodes, colleague_edges = self._build_people_layer(colleagues, 3, 58, "#722ED1", "colleagues")
        nodes.extend(colleague_nodes)
        edges.extend(colleague_edges)
        
        # 第五圈：其他关系层
        other_nodes, other_edges = self._build_people_layer(others, 4, 78, "#FAAD14", "others")
        nodes.extend(other_nodes)
        edges.extend(other_edges)
        
        # 事件不作为独立节点显示（已整合到人物的stories中）
        event_nodes, event_edges = self._build_event_layer(events, nodes)
        nodes.extend(event_nodes)
        edges.extend(event_edges)
        
        # 添加模式节点（Pattern节点 + EXHIBITS关系）
        pattern_nodes, pattern_edges = self._build_pattern_layer(patterns)
        nodes.extend(pattern_nodes)
        edges.extend(pattern_edges)
        
        # 合并所有朋友节点
        all_friend_nodes = close_friend_nodes + friend_nodes
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layers": {
                "family": [n["id"] for n in family_nodes],
                "friends": [n["id"] for n in all_friend_nodes],
                "colleagues": [n["id"] for n in colleague_nodes],
                "others": [n["id"] for n in other_nodes],
                "events": [n["id"] for n in event_nodes],
                "patterns": [n["id"] for n in pattern_nodes]
            },
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": {
                    "User": 1,
                    "Entity_Person": len(people),
                    "Event": 0,  # 事件不作为独立节点
                    "Pattern": len(patterns)
                },
                "relationship_types": {
                    "KNOWS": len(people),
                    "PARTICIPATED_IN": 0,  # 事件不显示
                    "INVOLVES": 0,  # 事件不显示
                    "EXHIBITS": len(patterns)
                },
                "data_sources": {
                    "neo4j_graph": len(people),
                    "events_as_stories": len(events),  # 事件作为故事信息
                    "patterns": len(patterns)
                },
                "retrieval_method": "hybrid" if use_hybrid else "neo4j_graph",
                "layer_info": {
                    "layer1": {"name": "家人层", "radius": 18, "count": len(family_nodes)},
                    "layer2": {"name": "朋友层", "radius": 38, "count": len(all_friend_nodes)},
                    "layer3": {"name": "同事层", "radius": 58, "count": len(colleague_nodes)},
                    "layer4": {"name": "其他层", "radius": 78, "count": len(other_nodes)},
                    "events": {"name": "事件信息", "count": len(events), "note": "作为人物关系描述"},
                    "patterns": {"name": "模式层", "count": len(pattern_nodes)}
                }
            }
        }
    
    def _build_empty_graph(self, user_profile: RelationshipUserProfile, use_hybrid: bool) -> Dict[str, Any]:
        """构建空图谱"""
        return {
            "nodes": [{
                "id": "__me__", 
                "label": "我", 
                "type": "center", 
                "layer": 0,
                "position": {"x": 0, "y": 0, "z": 0}, 
                "size": 20, 
                "color": "#e8f4ff",
                "is_self": True,
                "metadata": {
                    "user_id": user_profile.user_id,
                    "name": user_profile.name
                }
            }],
            "edges": [],
            "layers": {
                "family": [],
                "friends": [],
                "colleagues": [],
                "others": [],
                "events": [],
                "patterns": []
            },
            "metadata": {
                "total_nodes": 1,
                "total_edges": 0,
                "node_types": {"User": 1, "Entity_Person": 0, "Event": 0, "Pattern": 0},
                "relationship_types": {"KNOWS": 0, "PARTICIPATED_IN": 0, "INVOLVES": 0, "EXHIBITS": 0},
                "data_sources": {"neo4j_graph": 0, "events": 0, "patterns": 0},
                "retrieval_method": "hybrid" if use_hybrid else "neo4j_graph",
                "layer_info": {
                    "layer1": {"name": "家人层", "radius": 18, "count": 0},
                    "layer2": {"name": "朋友层", "radius": 38, "count": 0},
                    "layer3": {"name": "同事层", "radius": 58, "count": 0},
                    "layer4": {"name": "其他层", "radius": 78, "count": 0},
                    "events": {"name": "事件层", "count": 0},
                    "patterns": {"name": "模式层", "count": 0}
                }
            }
        }
    
    def _build_people_layer(self, people: List[Dict], layer: int, radius: float, color: str, category: str):
        """构建人物层 - 3D球面分布（Entity节点）"""
        if not people:
            return [], []
        
        people_nodes = []
        people_edges = []
        
        n = len(people)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, person in enumerate(people):
            # Fibonacci球面算法
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            person_id = f"{category}_{i}"
            strength = person.get('strength', 0.5)
            
            # 根据关系强度调整大小
            size = 8 + int(strength * 6)
            
            # 获取相关故事/事件
            stories = person.get('stories', [])
            if stories:
                print(f"[Neo4jRelationshipKG] 节点 {person['name']} 包含 {len(stories)} 个故事")
            
            people_nodes.append({
                "id": person_id,
                "label": person['name'],
                "type": category,
                "layer": layer,
                "position": {"x": x, "y": y, "z": z},
                "size": size,
                "color": color,
                "stories": stories,  # 添加stories字段到节点顶层
                "metadata": {
                    "node_type": "Entity",
                    "entity_type": "Person",
                    "occupation": person.get('occupation', ''),
                    "location": person.get('location', ''),
                    "description": person.get('description', ''),
                    "strength": strength,
                    "frequency": person.get('frequency', 0.5),
                    "relationship_type": person['relationship_type'],
                    "since": person.get('since', ''),
                    "sources": person.get('sources', []),
                    "source": person.get('source', 'neo4j_graph'),
                    "stories": stories  # 也添加到metadata中
                }
            })
            
            # User-KNOWS->Person关系
            people_edges.append({
                "source": "__me__",
                "target": person_id,
                "type": person['relationship_type'],  # KNOWS/FRIEND/COLLEAGUE/FAMILY
                "strength": strength,
                "metadata": {
                    "relationship_category": "user_related",
                    "closeness": strength
                }
            })
        
        return people_nodes, people_edges
    
    def _build_event_layer(self, events: List[Dict], existing_nodes: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        构建事件层 - Event节点 + INVOLVES关系
        
        重要：事件不作为独立节点显示在人际关系视图中
        而是作为人物之间的关系信息（边的描述）
        
        Returns:
            空列表 - 人际关系视图不显示事件节点
        """
        if not events:
            return [], []
        
        # 人际关系视图中，事件不作为节点显示
        # 事件信息会作为人物之间的关系描述
        # 例如："和小明一起散步" 会作为 User-KNOWS->小明 关系的描述
        
        print(f"[Neo4jRelationshipKG] 跳过 {len(events)} 个事件节点（人际关系视图不显示事件）")
        
        return [], []
    
    def _build_pattern_layer(self, patterns: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        构建模式层 - Pattern节点 + EXHIBITS关系
        模式节点放置在外围
        """
        if not patterns:
            return [], []
        
        pattern_nodes = []
        pattern_edges = []
        
        radius = 95  # 模式层半径（最外层）
        n = len(patterns)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, pattern in enumerate(patterns):
            # Fibonacci球面算法
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            pattern_id = f"pattern_{i}"
            
            # 根据频率调整大小
            size = 6 + int(min(pattern['frequency'] / 5, 1.0) * 6)
            
            pattern_nodes.append({
                "id": pattern_id,
                "label": pattern['name'],
                "type": "pattern",
                "layer": 5,
                "position": {"x": x, "y": y, "z": z},
                "size": size,
                "color": "#EB2F96",  # 粉色
                "metadata": {
                    "node_type": "Pattern",
                    "pattern_type": pattern['type'],
                    "description": pattern['description'],
                    "frequency": pattern['frequency'],
                    "confidence": pattern['confidence'],
                    "evidence": pattern['evidence']
                }
            })
            
            # User-EXHIBITS->Pattern关系
            pattern_edges.append({
                "source": "__me__",
                "target": pattern_id,
                "type": "EXHIBITS",
                "strength": pattern['confidence'],
                "metadata": {
                    "relationship_category": "pattern_related",
                    "frequency": pattern['user_frequency']
                }
            })
        
        return pattern_nodes, pattern_edges


# 新的构建方法（使用统一框架）
    def _build_people_layer_from_entities(self, people: List[Dict], events: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Entity(Person)数据构建人物层"""
        if not people:
            return [], []
        
        # 为每个人物添加相关事件信息（作为stories）
        person_events_map = {}
        for event in events:
            for involved in event.get('involved_entities', []):
                if involved.get('type') == 'Person':
                    person_name = involved.get('name')
                    if person_name not in person_events_map:
                        person_events_map[person_name] = []
                    person_events_map[person_name].append(event.get('name'))
        
        people_nodes = []
        people_edges = []
        
        radius = 25
        n = len(people)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, person in enumerate(people):
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            person_name = person.get('name')
            user_relation = person.get('user_relation', {})
            relation_props = user_relation.get('properties', {})
            
            # 获取关系类型和亲密度
            relationship_type = relation_props.get('relationship_type', 'friend')
            closeness = relation_props.get('closeness', 0.5)
            
            # 根据关系类型设置颜色
            color_map = {
                'family': '#FF4D4F',
                'close_friend': '#52C41A',
                'friend': '#1890FF',
                'colleague': '#FAAD14',
                'acquaintance': '#D9D9D9'
            }
            color = color_map.get(relationship_type, '#1890FF')
            
            # 获取stories
            stories = person_events_map.get(person_name, [])
            
            # 解析attributes
            attributes = person.get('attributes', {})
            if isinstance(attributes, str):
                try:
                    import json
                    attributes = json.loads(attributes)
                except:
                    attributes = {}
            
            people_nodes.append({
                "id": f"person_{person_name}",
                "label": person_name,
                "type": "person",
                "layer": 1,
                "position": {"x": x, "y": y, "z": z},
                "size": 10 + int(closeness * 5),
                "color": color,
                "stories": stories,
                "metadata": {
                    "node_type": "Entity",
                    "entity_type": "Person",
                    "relationship_type": relationship_type,
                    "closeness": closeness,
                    "description": person.get('description', ''),
                    "stories": stories,
                    **attributes
                }
            })
            
            # User-KNOWS->Person关系
            people_edges.append({
                "source": "__me__",
                "target": f"person_{person_name}",
                "type": "KNOWS",
                "strength": closeness,
                "metadata": {
                    "relationship_category": "user_related",
                    "relationship_type": relationship_type,
                    "closeness": closeness
                }
            })
        
        return people_nodes, people_edges
    
    def _build_event_layer_from_data(self, events: List[Dict], people_nodes: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Event数据构建事件层"""
        if not events:
            return [], []
        
        event_nodes = []
        event_edges = []
        
        radius = 45
        n = len(events)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, event in enumerate(events):
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            event_id = f"event_{i}"
            
            event_nodes.append({
                "id": event_id,
                "label": event.get('name'),
                "type": "event",
                "layer": 2,
                "position": {"x": x, "y": y, "z": z},
                "size": 8,
                "color": "#13C2C2",
                "metadata": {
                    "node_type": "Event",
                    "event_type": event.get('type'),
                    "description": event.get('description', ''),
                    "start_time": str(event.get('start_time', ''))
                }
            })
            
            # User-PARTICIPATED_IN->Event关系
            event_edges.append({
                "source": "__me__",
                "target": event_id,
                "type": "PARTICIPATED_IN",
                "strength": 0.7,
                "metadata": {"relationship_category": "user_related"}
            })
            
            # Event-INVOLVES->Person关系
            for involved in event.get('involved_entities', []):
                if involved.get('type') == 'Person':
                    person_name = involved.get('name')
                    person_id = f"person_{person_name}"
                    # 检查人物节点是否存在
                    if any(p['id'] == person_id for p in people_nodes):
                        event_edges.append({
                            "source": event_id,
                            "target": person_id,
                            "type": "INVOLVES",
                            "strength": 0.6,
                            "metadata": {"relationship_category": "entity_related"}
                        })
        
        return event_nodes, event_edges
    
    def _build_location_layer_from_entities(self, locations: List[Dict], event_nodes: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Entity(Location)数据构建地点层"""
        if not locations:
            return [], []
        
        location_nodes = []
        location_edges = []
        
        radius = 65
        n = len(locations)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, location in enumerate(locations):
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            location_id = f"location_{i}"
            
            location_nodes.append({
                "id": location_id,
                "label": location.get('name'),
                "type": "location",
                "layer": 3,
                "position": {"x": x, "y": y, "z": z},
                "size": 8,
                "color": "#722ED1",
                "metadata": {
                    "node_type": "Entity",
                    "entity_type": "Location",
                    "description": location.get('description', '')
                }
            })
        
        return location_nodes, location_edges
    
    def _build_pattern_layer_from_data(self, patterns: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Pattern数据构建模式层"""
        if not patterns:
            return [], []
        
        pattern_nodes = []
        pattern_edges = []
        
        radius = 85
        n = len(patterns)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, pattern in enumerate(patterns):
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            pattern_id = f"pattern_{i}"
            
            pattern_nodes.append({
                "id": pattern_id,
                "label": pattern.get('name'),
                "type": "pattern",
                "layer": 4,
                "position": {"x": x, "y": y, "z": z},
                "size": 6,
                "color": "#EB2F96",
                "metadata": {
                    "node_type": "Pattern",
                    "pattern_type": pattern.get('type'),
                    "description": pattern.get('description', ''),
                    "frequency": pattern.get('frequency', 1)
                }
            })
            
            pattern_edges.append({
                "source": "__me__",
                "target": pattern_id,
                "type": "EXHIBITS",
                "strength": pattern.get('confidence', 0.5),
                "metadata": {"relationship_category": "pattern_related"}
            })
        
        return pattern_nodes, pattern_edges


# 创建全局实例
_neo4j_relationship_kg = None

def get_neo4j_relationship_kg():
    """获取Neo4j人际关系知识图谱实例"""
    global _neo4j_relationship_kg
    if _neo4j_relationship_kg is None:
        _neo4j_relationship_kg = Neo4jRelationshipKnowledgeGraph()
    return _neo4j_relationship_kg
