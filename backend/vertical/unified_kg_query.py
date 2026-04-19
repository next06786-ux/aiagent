"""
统一的知识图谱查询框架
确保三个视图（职业、教育、人际关系）都完整利用Neo4j架构的6种节点和4类关系
"""

from typing import Dict, List, Any, Tuple
from neo4j import GraphDatabase
import os

class UnifiedKGQuery:
    """
    统一的知识图谱查询类
    
    Neo4j架构规范：
    - 6种节点：User, Entity, Event, Concept, Pattern, Source
    - 4类关系：用户相关、信息溯源、实体间、模式关系
    """
    
    def __init__(self, driver: GraphDatabase.driver):
        self.driver = driver
    
    def query_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        查询用户完整画像
        
        包含：
        1. User节点基本信息
        2. User-HAS_PROFILE->Concept（技能、兴趣等）
        3. User-INTERESTED_IN->Entity/Concept（感兴趣的内容）
        4. User-EXHIBITS->Pattern（行为模式）
        """
        with self.driver.session() as session:
            query = """
            MATCH (u:User {user_id: $user_id})
            OPTIONAL MATCH (u)-[r1:HAS_PROFILE]->(c:Concept)
            OPTIONAL MATCH (u)-[r2:INTERESTED_IN]->(target)
            OPTIONAL MATCH (u)-[r3:EXHIBITS]->(p:Pattern)
            RETURN u,
                   collect(DISTINCT {concept: c, relation: r1}) as concepts,
                   collect(DISTINCT {target: target, relation: r2}) as interests,
                   collect(DISTINCT {pattern: p, relation: r3}) as patterns
            """
            result = session.run(query, user_id=user_id)
            record = result.single()
            
            if not record:
                return None
            
            return {
                'user': dict(record['u']),
                'concepts': [r for r in record['concepts'] if r['concept']],
                'interests': [r for r in record['interests'] if r['target']],
                'patterns': [r for r in record['patterns'] if r['pattern']]
            }
    
    def query_entities_by_type(
        self, 
        user_id: str, 
        entity_types: List[str],
        include_relations: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        查询特定类型的实体及其关系
        
        Args:
            user_id: 用户ID
            entity_types: 实体类型列表（如['Job', 'Organization']）
            include_relations: 是否包含实体间关系
            limit: 返回数量限制
        
        Returns:
            实体列表，每个实体包含：
            - 节点信息
            - 用户关系（INTERESTED_IN, APPLIED_TO等）
            - 来源信息（EXTRACTED_FROM）
            - 实体间关系（PART_OF, REQUIRES等）
        """
        with self.driver.session() as session:
            # 基础查询：获取实体及用户关系
            query = """
            MATCH (u:User {user_id: $user_id})-[ur]->(e:Entity)
            WHERE e.type IN $entity_types
            
            // 查询来源信息（信息溯源关系）
            OPTIONAL MATCH (e)-[:EXTRACTED_FROM]->(s:Source)
            
            // 查询实体间关系
            OPTIONAL MATCH (e)-[er]->(related:Entity)
            WHERE type(er) IN ['PART_OF', 'REQUIRES', 'LOCATED_IN', 'RELATED_TO']
            
            RETURN e,
                   type(ur) as user_relation_type,
                   properties(ur) as user_relation_props,
                   collect(DISTINCT s) as sources,
                   collect(DISTINCT {relation: type(er), target: related, props: properties(er)}) as entity_relations
            ORDER BY user_relation_props.interest_level DESC, e.confidence DESC
            LIMIT $limit
            """
            
            result = session.run(query, user_id=user_id, entity_types=entity_types, limit=limit)
            
            entities = []
            for record in result:
                entity_data = dict(record['e'])
                entity_data['user_relation'] = {
                    'type': record['user_relation_type'],
                    'properties': record['user_relation_props']
                }
                entity_data['sources'] = [dict(s) for s in record['sources'] if s]
                entity_data['entity_relations'] = [
                    r for r in record['entity_relations'] 
                    if r['relation'] and r['target']
                ]
                entities.append(entity_data)
            
            return entities
    
    def query_events_by_user(
        self,
        user_id: str,
        event_types: List[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        查询用户相关的事件
        
        包含：
        1. User-PARTICIPATED_IN->Event（用户参与的事件）
        2. Event-HAPPENED_AT->Entity(Location)（事件地点）
        3. Event-INVOLVES->Entity(Person/Organization)（事件涉及的实体）
        4. Event-EXTRACTED_FROM->Source（事件来源）
        """
        with self.driver.session() as session:
            query = """
            MATCH (u:User {user_id: $user_id})-[r:PARTICIPATED_IN]->(ev:Event)
            WHERE $event_types IS NULL OR ev.type IN $event_types
            
            // 查询事件地点（实体间关系）
            OPTIONAL MATCH (ev)-[:HAPPENED_AT]->(loc:Entity)
            WHERE loc.type = 'Location'
            
            // 查询事件涉及的实体（实体间关系）
            OPTIONAL MATCH (ev)-[:INVOLVES]->(involved:Entity)
            
            // 查询来源信息（信息溯源关系）
            OPTIONAL MATCH (ev)-[:EXTRACTED_FROM]->(s:Source)
            
            RETURN ev,
                   properties(r) as participation,
                   loc,
                   collect(DISTINCT involved) as involved_entities,
                   collect(DISTINCT s) as sources
            ORDER BY ev.start_time DESC
            LIMIT $limit
            """
            
            result = session.run(query, user_id=user_id, event_types=event_types, limit=limit)
            
            events = []
            for record in result:
                event_data = dict(record['ev'])
                event_data['participation'] = record['participation']
                event_data['location'] = dict(record['loc']) if record['loc'] else None
                event_data['involved_entities'] = [dict(e) for e in record['involved_entities'] if e]
                event_data['sources'] = [dict(s) for s in record['sources'] if s]
                events.append(event_data)
            
            return events
    
    def query_concepts_by_type(
        self,
        user_id: str,
        concept_types: List[str],
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        查询特定类型的概念
        
        包含：
        1. User-HAS_PROFILE->Concept（用户拥有的概念）
        2. User-INTERESTED_IN->Concept（用户感兴趣的概念）
        3. Concept-EXTRACTED_FROM->Source（概念来源）
        """
        with self.driver.session() as session:
            query = """
            MATCH (u:User {user_id: $user_id})-[r]->(c:Concept)
            WHERE c.type IN $concept_types
            AND type(r) IN ['HAS_PROFILE', 'INTERESTED_IN']
            
            // 查询来源信息（信息溯源关系）
            OPTIONAL MATCH (c)-[:EXTRACTED_FROM]->(s:Source)
            
            RETURN c,
                   type(r) as relation_type,
                   properties(r) as relation_props,
                   collect(DISTINCT s) as sources
            ORDER BY relation_props.confidence DESC, c.confidence DESC
            LIMIT $limit
            """
            
            result = session.run(query, user_id=user_id, concept_types=concept_types, limit=limit)
            
            concepts = []
            for record in result:
                concept_data = dict(record['c'])
                concept_data['user_relation'] = {
                    'type': record['relation_type'],
                    'properties': record['relation_props']
                }
                concept_data['sources'] = [dict(s) for s in record['sources'] if s]
                concepts.append(concept_data)
            
            return concepts
    
    def query_patterns_by_user(
        self,
        user_id: str,
        pattern_types: List[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        查询用户的行为模式
        
        包含：
        1. User-EXHIBITS->Pattern（用户展现的模式）
        2. Entity/Event-SUPPORTS->Pattern（支持模式的证据）
        3. Pattern-INFLUENCES->Pattern（模式间影响）
        """
        with self.driver.session() as session:
            query = """
            MATCH (u:User {user_id: $user_id})-[r:EXHIBITS]->(p:Pattern)
            WHERE $pattern_types IS NULL OR p.type IN $pattern_types
            
            // 查询支持证据（模式关系）
            OPTIONAL MATCH (evidence)-[:SUPPORTS]->(p)
            
            RETURN p,
                   properties(r) as exhibition,
                   collect(DISTINCT {node: evidence, labels: labels(evidence)}) as evidence_list
            ORDER BY p.frequency DESC, p.confidence DESC
            LIMIT $limit
            """
            
            result = session.run(query, user_id=user_id, pattern_types=pattern_types, limit=limit)
            
            patterns = []
            for record in result:
                pattern_data = dict(record['p'])
                pattern_data['exhibition'] = record['exhibition']
                pattern_data['evidence'] = [
                    e for e in record['evidence_list'] 
                    if e['node']
                ]
                
                # 单独查询模式影响关系
                pattern_id = record['p'].element_id
                influences_query = """
                MATCH (p:Pattern)-[inf:INFLUENCES]->(influenced:Pattern)
                WHERE elementId(p) = $pattern_id
                RETURN influenced, properties(inf) as influence_props
                """
                influences_result = session.run(influences_query, pattern_id=pattern_id)
                pattern_data['influences'] = [
                    {
                        'pattern': dict(inf_record['influenced']),
                        'influence': inf_record['influence_props']
                    }
                    for inf_record in influences_result
                ]
                patterns.append(pattern_data)
            
            return patterns
    
    def query_complete_domain_data(
        self,
        user_id: str,
        domain: str
    ) -> Dict[str, Any]:
        """
        查询特定领域的完整数据（包含所有6种节点和4类关系）
        
        Args:
            user_id: 用户ID
            domain: 领域类型（'career', 'education', 'relationship'）
        
        Returns:
            包含所有相关节点和关系的完整数据
        """
        # 根据领域确定查询的实体类型
        domain_config = {
            'career': {
                'entity_types': ['Job', 'Organization'],
                'concept_types': ['Skill', 'Interest', 'Goal'],
                'event_types': ['Interview', 'Meeting', 'JobOffer'],
                'pattern_types': ['Preference', 'DecisionPattern', 'CareerPattern']
            },
            'education': {
                'entity_types': ['School', 'Organization'],
                'concept_types': ['Interest', 'Goal', 'Skill'],
                'event_types': ['Application', 'Visit', 'Exam'],
                'pattern_types': ['Preference', 'LearningPattern']
            },
            'relationship': {
                'entity_types': ['Person', 'Organization', 'Location'],
                'concept_types': ['Interest', 'Value'],
                'event_types': ['Meeting', 'Party', 'Travel', 'Activity'],
                'pattern_types': ['SocialPattern', 'Preference']
            }
        }
        
        config = domain_config.get(domain, domain_config['career'])
        
        # 查询所有相关数据
        return {
            'user_profile': self.query_user_profile(user_id),
            'entities': self.query_entities_by_type(user_id, config['entity_types']),
            'events': self.query_events_by_user(user_id, config['event_types']),
            'concepts': self.query_concepts_by_type(user_id, config['concept_types']),
            'patterns': self.query_patterns_by_user(user_id, config['pattern_types'])
        }
