"""
基于Neo4j的职业知识图谱构建器
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
class UserSkillProfile:
    """用户技能档案"""
    user_id: str  # 用户ID，必需
    mastered_skills: List[str]
    partial_skills: List[str]
    missing_skills: List[str]
    target_direction: str


class Neo4jCareerKnowledgeGraph:
    """基于Neo4j的职业知识图谱构建器"""
    
    def __init__(self):
        # 连接Neo4j（用于information_kg）
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.unified_query = UnifiedKGQuery(self.driver)
        
        self.skill_dependencies = {
            "Python": [], "Django": ["Python"], "Flask": ["Python"], "FastAPI": ["Python"],
            "JavaScript": [], "React": ["JavaScript"], "Vue": ["JavaScript"],
            "Node.js": ["JavaScript"], "TypeScript": ["JavaScript"],
            "Java": [], "Spring": ["Java"], "MySQL": [], "PostgreSQL": [],
            "MongoDB": [], "Redis": [], "Docker": [], "Kubernetes": ["Docker"],
            "Git": [], "Linux": [], "AWS": ["Linux"],
            "机器学习": ["Python"], "深度学习": ["机器学习", "Python"],
            "数据分析": ["Python"], "算法": [], "数据结构": []
        }
    
    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.close()
    
    def get_complete_career_data(self, user_id: str) -> Dict[str, Any]:
        """
        使用统一框架获取完整的职业数据
        包含所有6种节点和4类关系
        """
        return self.unified_query.query_complete_domain_data(user_id, 'career')
    
    def _get_jobs_from_information_kg(self, user_id: str, keyword: str = "", limit: int = 50) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
        """
        从Neo4j获取完整的职业数据
        完全基于Neo4j架构规范（6种节点+4类关系）
        
        Returns:
            (jobs, skills, patterns, companies): 职位列表、技能列表、模式列表、公司列表
        """
        try:
            with self.driver.session() as session:
                # 1. 查询用户的技能（Concept节点，type='Skill'）
                # 关系：User-HAS_PROFILE->Concept(Skill)
                skills_query = """
                MATCH (u:User {user_id: $user_id})-[r:HAS_PROFILE]->(c:Concept)
                WHERE c.type = 'Skill'
                OPTIONAL MATCH (c)-[:EXTRACTED_FROM]->(s:Source)
                RETURN c.name as skill_name,
                       elementId(c) as skill_id,
                       c.level as level,
                       c.description as description,
                       c.confidence as confidence,
                       r.confidence as user_confidence,
                       collect(DISTINCT s.source_id) as sources
                ORDER BY r.confidence DESC
                LIMIT 50
                """
                
                skills_result = session.run(skills_query, user_id=user_id)
                skills = []
                
                for record in skills_result:
                    level = record['level'] or 'intermediate'
                    user_conf = record['user_confidence'] or 0.5
                    
                    # 根据置信度判断掌握程度
                    if user_conf >= 0.8:
                        mastery = 'mastered'
                    elif user_conf >= 0.5:
                        mastery = 'partial'
                    else:
                        mastery = 'missing'
                    
                    skills.append({
                        'name': record['skill_name'],
                        'skill_id': record['skill_id'],
                        'level': level,
                        'description': record['description'] or '',
                        'confidence': user_conf,
                        'mastery': mastery,
                        'sources': record['sources']
                    })
                
                if os.getenv("DEBUG_MODE") == "true":
                    print(f"[Neo4jCareerKG] 获取到 {len(skills)} 个用户技能（通过HAS_PROFILE关系）")
                
                # 2. 查询用户感兴趣的职位（Entity节点，type='Job'）
                # 关系：User-INTERESTED_IN->Entity(Job)
                jobs_query = """
                MATCH (u:User {user_id: $user_id})-[r:INTERESTED_IN]->(j:Entity)
                WHERE j.type = 'Job'
                OPTIONAL MATCH (j)-[:EXTRACTED_FROM]->(s:Source)
                OPTIONAL MATCH (j)-[:REQUIRES]->(skill:Concept)
                WHERE skill.type = 'Skill'
                RETURN j.name as position_name,
                       elementId(j) as job_id,
                       j.category as category,
                       j.description as description,
                       j.attributes as attributes,
                       j.confidence as confidence,
                       r.interest_level as interest_level,
                       collect(DISTINCT s.source_id) as sources,
                       collect(DISTINCT skill.name) as required_skills
                ORDER BY r.interest_level DESC
                LIMIT $limit
                """
                
                jobs_result = session.run(jobs_query, user_id=user_id, limit=limit)
                jobs = []
                
                for record in jobs_result:
                    # 安全处理attributes（可能是字典、字符串或None）
                    attributes = record['attributes']
                    if isinstance(attributes, str):
                        try:
                            import json
                            attributes = json.loads(attributes)
                        except:
                            attributes = {}
                    elif not isinstance(attributes, dict):
                        attributes = {}
                    
                    jobs.append({
                        'position_name': record['position_name'],
                        'job_id': record['job_id'],
                        'company_name': attributes.get('company', '未知公司'),
                        'salary': attributes.get('salary', 0),
                        'city': attributes.get('location', ''),
                        'requirements': record['required_skills'] or [],
                        'description': record['description'] or '',
                        'strength': record['interest_level'] or 0.5,
                        'confidence': record['confidence'] or 0.5,
                        'sources': record['sources'],
                        'source': 'neo4j_graph'
                    })
                
                if os.getenv("DEBUG_MODE") == "true":
                    print(f"[Neo4jCareerKG] 从Neo4j获取到 {len(jobs)} 个职位（通过INTERESTED_IN关系）")
                
                # 3. 查询用户相关的公司（Entity节点，type='Organization'）
                # 多种关系路径：
                # - User-PARTICIPATED_IN->Event-HAPPENED_AT->Entity(Organization)
                # - User-INTERESTED_IN->Entity(Job)-PART_OF->Entity(Organization)
                # - User直接提到的公司
                companies_query = """
                MATCH (u:User {user_id: $user_id})
                OPTIONAL MATCH (u)-[:PARTICIPATED_IN]->(e:Event)-[:HAPPENED_AT]->(org1:Entity)
                WHERE org1.type = 'Organization'
                OPTIONAL MATCH (u)-[:INTERESTED_IN]->(j:Entity)-[:PART_OF]->(org2:Entity)
                WHERE j.type = 'Job' AND org2.type = 'Organization'
                WITH u, 
                     collect(DISTINCT org1) + collect(DISTINCT org2) as all_orgs
                UNWIND all_orgs as org
                WHERE org IS NOT NULL
                OPTIONAL MATCH (org)-[:EXTRACTED_FROM]->(s:Source)
                OPTIONAL MATCH (e:Event)-[:HAPPENED_AT]->(org)
                OPTIONAL MATCH (u)-[:PARTICIPATED_IN]->(e)
                RETURN DISTINCT org.name as company_name,
                       elementId(org) as company_id,
                       org.description as description,
                       org.confidence as confidence,
                       org.attributes as attributes,
                       collect(DISTINCT e.name) as related_events,
                       collect(DISTINCT s.source_id) as sources
                LIMIT 20
                """
                
                companies_result = session.run(companies_query, user_id=user_id)
                companies = []
                
                for record in companies_result:
                    # 安全处理attributes
                    attributes = record['attributes']
                    if isinstance(attributes, str):
                        try:
                            import json
                            attributes = json.loads(attributes)
                        except:
                            attributes = {}
                    elif not isinstance(attributes, dict):
                        attributes = {}
                    
                    companies.append({
                        'name': record['company_name'],
                        'company_id': record['company_id'],
                        'description': record['description'] or '',
                        'confidence': record['confidence'] or 0.8,
                        'related_events': [e for e in record['related_events'] if e],
                        'sources': record['sources'],
                        'attributes': attributes,
                        'source': 'user_related'
                    })
                
                if os.getenv("DEBUG_MODE") == "true":
                    print(f"[Neo4jCareerKG] 获取到 {len(companies)} 个用户相关公司（多种关系路径）")
                
                # 4. 查询职业相关的模式（Pattern节点）
                # 关系：User-EXHIBITS->Pattern
                patterns_query = """
                MATCH (u:User {user_id: $user_id})-[r:EXHIBITS]->(pat:Pattern)
                WHERE pat.type IN ['Preference', 'DecisionPattern', 'CareerPattern']
                OPTIONAL MATCH (evidence)-[:SUPPORTS]->(pat)
                RETURN pat.name as pattern_name,
                       elementId(pat) as pattern_id,
                       pat.type as pattern_type,
                       pat.description as description,
                       pat.frequency as frequency,
                       pat.confidence as confidence,
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
                        'type': record['pattern_type'] or 'Preference',
                        'description': record['description'] or '',
                        'frequency': record['frequency'] or 1,
                        'confidence': record['confidence'] or 0.5,
                        'evidence': record['evidence_list']
                    })
                
                if os.getenv("DEBUG_MODE") == "true":
                    print(f"[Neo4jCareerKG] 获取到 {len(patterns)} 个职业模式（通过EXHIBITS关系）")
                
                return jobs, skills, patterns, companies
                
        except Exception as e:
            print(f"[Neo4jCareerKG] 从Neo4j获取数据失败: {e}")
            import traceback
            traceback.print_exc()
            return [], [], [], []
    
    def _get_jobs_with_hybrid_retrieval(
        self,
        user_id: str,
        user_profile: UserSkillProfile,
        keyword: str = "",
        limit: int = 50
    ) -> List[Dict]:
        """
        使用混合检索获取职位信息（推荐）
        结合Neo4j图检索和RAG向量检索
        """
        try:
            from backend.learning.unified_hybrid_retrieval import (
                UnifiedHybridRetrieval, RetrievalConfig, RetrievalStrategy, FusionMethod
            )
            
            # 创建检索器
            retriever = UnifiedHybridRetrieval(user_id)
            
            # 构建查询
            query_parts = [user_profile.target_direction or "职业发展"]
            if keyword:
                query_parts.append(keyword)
            query_parts.extend(user_profile.mastered_skills[:3])  # 添加核心技能
            query = " ".join(query_parts)
            
            # 配置混合检索
            config = RetrievalConfig(
                strategy=RetrievalStrategy.HYBRID_PARALLEL,
                fusion_method=FusionMethod.RRF,
                max_results=limit,
                domain_filter="career",
                expand_relations=True,
                query_expansion=True,
                graph_weight=0.7,  # 职位信息更依赖图结构
                vector_weight=0.3
            )
            
            # 执行检索
            context = retriever.retrieve(query, config)
            
            # 转换为职位格式
            jobs = []
            for result in context.results:
                # 只处理职位相关的结果
                if result.node_type in ['Job', 'entity'] and result.category in ['job', 'position', 'career']:
                    metadata = result.metadata
                    
                    jobs.append({
                        'position_name': result.content[:100] if 'Job' in result.content else metadata.get('name', result.content[:50]),
                        'job_id': result.id,
                        'company_name': metadata.get('company', metadata.get('organization', '未知公司')),
                        'salary': metadata.get('salary', 0),
                        'city': metadata.get('location', metadata.get('city', '')),
                        'requirements': metadata.get('requirements', metadata.get('skills', [])),
                        'description': metadata.get('description', result.content),
                        'strength': result.score,
                        'source': result.source,  # 'graph', 'vector', or 'hybrid'
                        'confidence': result.confidence
                    })
            
            print(f"[Neo4jCareerKG] 混合检索获取到 {len(jobs)} 个职位")
            print(f"  - 图检索: {context.graph_results}个")
            print(f"  - 向量检索: {context.vector_results}个")
            print(f"  - 执行时间: {context.execution_time_ms:.2f}ms")
            
            return jobs[:limit]
            
        except Exception as e:
            print(f"[Neo4jCareerKG] 混合检索失败，降级到Neo4j检索: {e}")
            import traceback
            traceback.print_exc()
            # 降级到旧方法
            return self._get_jobs_from_information_kg(user_id, keyword, limit)
    
    def build_career_graph(self, user_profile: UserSkillProfile, use_hybrid: bool = False) -> Dict[str, Any]:
        """
        构建职业知识图谱 - 完全基于Neo4j架构规范（6种节点+4类关系）
        
        图谱结构（3D立体布局）：
        - 中心：User（我）
        - 第1层：技能层（Concept节点，type='Skill'）
        - 第2层：岗位层（Entity节点，type='Job'）
        - 第3层：公司层（Entity节点，type='Organization'）
        - 事件层：职业相关事件（Event节点）
        - 模式层：职业模式（Pattern节点）
        
        关系链：
        - User-HAS_PROFILE->Concept(Skill)
        - User-INTERESTED_IN->Entity(Job)
        - Entity(Job)-REQUIRES->Concept(Skill)
        - Entity(Job)-PART_OF->Entity(Organization)
        - User-PARTICIPATED_IN->Event
        - Event-INVOLVES->Entity
        - User-EXHIBITS->Pattern
        
        Args:
            user_profile: 用户技能档案
            use_hybrid: 是否使用混合检索（默认False，使用纯Neo4j）
        """
        # 使用统一框架获取完整数据
        complete_data = self.get_complete_career_data(user_profile.user_id)
        
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
                "node_type": "User"
            }
        }]
        edges = []
        
        # 提取数据
        entities = complete_data.get('entities', [])
        events = complete_data.get('events', [])
        concepts = complete_data.get('concepts', [])
        patterns = complete_data.get('patterns', [])
        
        # 分离职位和公司
        jobs = [e for e in entities if e.get('type') == 'Job']
        companies = [e for e in entities if e.get('type') == 'Organization']
        
        # 第一圈：技能层（Concept节点）
        skill_nodes, skill_edges = self._build_skill_layer_from_concepts(concepts)
        
        # 为技能节点附加相关信息
        for skill_node in skill_nodes:
            skill_name = skill_node['label']
            
            # 附加需要该技能的岗位
            related_jobs = []
            for job in jobs:
                if any(
                    r.get('relation') == 'REQUIRES' and r.get('target', {}).get('name') == skill_name
                    for r in job.get('entity_relations', [])
                ):
                    related_jobs.append(job.get('name'))
            
            skill_node['metadata']['related_jobs'] = related_jobs[:10]
            skill_node['metadata']['job_count'] = len(related_jobs)
        
        nodes.extend(skill_nodes)
        edges.extend(skill_edges)
        
        # 第二圈：岗位层（Entity(Job)节点）
        job_nodes, job_edges = self._build_job_layer_from_entities(jobs, skill_nodes, user_profile)
        
        # 为岗位节点附加相关信息
        for job_node in job_nodes:
            job_name = job_node['label']
            
            # 附加该岗位相关的事件
            related_events = []
            for event in events:
                if any(
                    r.get('relation') == 'INVOLVES' and r.get('target', {}).get('name') == job_name
                    for r in event.get('entity_relations', [])
                ):
                    related_events.append({
                        'name': event.get('name'),
                        'type': event.get('type'),
                        'description': event.get('description', ''),
                        'time': event.get('time', '')
                    })
            
            job_node['metadata']['related_events'] = related_events
            job_node['metadata']['event_count'] = len(related_events)
        
        nodes.extend(job_nodes)
        edges.extend(job_edges)
        
        # 第三圈：公司层（Entity(Organization)节点）
        company_nodes, company_edges = self._build_company_layer_from_entities(companies, job_nodes)
        
        # 为公司节点附加相关信息
        for company_node in company_nodes:
            company_name = company_node['label']
            
            # 附加该公司相关的事件
            related_events = []
            for event in events:
                if any(
                    r.get('relation') == 'HAPPENED_AT' and r.get('target', {}).get('name') == company_name
                    for r in event.get('entity_relations', [])
                ):
                    related_events.append({
                        'name': event.get('name'),
                        'type': event.get('type'),
                        'description': event.get('description', ''),
                        'time': event.get('time', '')
                    })
            
            # 附加该公司的岗位
            company_jobs = [j['label'] for j in job_nodes if j['metadata'].get('company') == company_name]
            
            company_node['metadata']['related_events'] = related_events
            company_node['metadata']['event_count'] = len(related_events)
            company_node['metadata']['available_jobs'] = company_jobs
            company_node['metadata']['job_count'] = len(company_jobs)
        
        nodes.extend(company_nodes)
        edges.extend(company_edges)
        
        # 附加用户级别的职业模式信息
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
                "skills": [n["id"] for n in skill_nodes],
                "jobs": [n["id"] for n in job_nodes],
                "companies": [n["id"] for n in company_nodes]
            },
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": {
                    "User": 1,
                    "Concept_Skill": len(skill_nodes),
                    "Entity_Job": len(job_nodes),
                    "Entity_Organization": len(company_nodes)
                },
                "relationship_types": {
                    "HAS_PROFILE": len([e for e in edges if e['type'] == 'HAS_PROFILE']),
                    "INTERESTED_IN": len([e for e in edges if e['type'] == 'INTERESTED_IN']),
                    "REQUIRES": len([e for e in edges if e['type'] == 'REQUIRES']),
                    "PART_OF": len([e for e in edges if e['type'] == 'PART_OF'])
                },
                "user_patterns": user_patterns,  # 用户的职业模式
                "total_events": len(events),
                "data_source": "unified_kg_query",
                "architecture_compliant": True,
                "display_mode": "career_path_in_3d"
            }
        }
    
    def _build_skill_layer_from_concepts(self, concepts: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Concept数据构建技能层"""
        skill_nodes = []
        skill_edges = []
        
        if not concepts:
            return [], []
        
        radius = 18
        
        radius = 18
        n = len(concepts)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, concept in enumerate(concepts):
            # Fibonacci球面算法
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            # 获取用户关系信息
            user_relation = concept.get('user_relation', {})
            relation_props = user_relation.get('properties', {})
            confidence = relation_props.get('confidence', concept.get('confidence', 0.5))
            
            # 根据置信度设置颜色
            if confidence >= 0.8:
                color = "#52C41A"
                size = 12
            elif confidence >= 0.5:
                color = "#FAAD14"
                size = 10
            else:
                color = "#FF4D4F"
                size = 8
            
            skill_nodes.append({
                "id": f"skill_{concept.get('name')}",
                "label": concept.get('name'),
                "type": "skill",
                "layer": 1,
                "position": {"x": x, "y": y, "z": z},
                "size": size,
                "color": color,
                "metadata": {
                    "node_type": "Concept",
                    "concept_type": "Skill",
                    "confidence": confidence,
                    "sources": concept.get('sources', []),
                    "description": concept.get('description', '')
                }
            })
            
            # User-HAS_PROFILE->Skill关系
            skill_edges.append({
                "source": "__me__",
                "target": f"skill_{concept.get('name')}",
                "type": user_relation.get('type', 'HAS_PROFILE'),
                "strength": confidence,
                "metadata": {
                    "relationship_category": "user_related",
                    "confidence": confidence
                }
            })
        
        return skill_nodes, skill_edges
    
    def _build_job_layer_from_entities(
        self,
        jobs: List[Dict],
        skill_nodes: List[Dict],
        user_profile: UserSkillProfile
    ) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Entity(Job)数据构建岗位层"""
        if not jobs:
            return [], []
        
        job_nodes = []
        job_edges = []
        
        radius = 38
        n = len(jobs)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, job in enumerate(jobs):
            # Fibonacci球面算法
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            job_id = f"job_{i}"
            
            # 获取用户关系信息
            user_relation = job.get('user_relation', {})
            relation_props = user_relation.get('properties', {})
            interest_level = relation_props.get('interest_level', 0.5)
            
            # 根据兴趣度设置颜色
            if interest_level >= 0.7:
                color = "#52C41A"
                size = 14
            elif interest_level >= 0.4:
                color = "#1890FF"
                size = 12
            else:
                color = "#FAAD14"
                size = 10
            
            # 解析attributes
            attributes = job.get('attributes', {})
            if isinstance(attributes, str):
                try:
                    import json
                    attributes = json.loads(attributes)
                except:
                    attributes = {}
            
            job_nodes.append({
                "id": job_id,
                "label": job.get('name'),
                "type": "job",
                "layer": 2,
                "position": {"x": x, "y": y, "z": z},
                "size": size,
                "color": color,
                "metadata": {
                    "node_type": "Entity",
                    "entity_type": "Job",
                    "company": attributes.get('company', '未知公司'),
                    "salary": attributes.get('salary', 0),
                    "location": attributes.get('location', ''),
                    "description": job.get('description', ''),
                    "confidence": job.get('confidence', 0.5),
                    "interest_level": interest_level,
                    "sources": [s.get('source_id') for s in job.get('sources', []) if s]
                }
            })
            
            # User-INTERESTED_IN->Job关系
            job_edges.append({
                "source": "__me__",
                "target": job_id,
                "type": user_relation.get('type', 'INTERESTED_IN'),
                "strength": interest_level,
                "metadata": {
                    "relationship_category": "user_related",
                    "interest_level": interest_level
                }
            })
            
            # Job-REQUIRES->Skill关系（从entity_relations中提取）
            for rel in job.get('entity_relations', []):
                if rel.get('relation') == 'REQUIRES':
                    target_skill = rel.get('target', {})
                    skill_name = target_skill.get('name')
                    if skill_name:
                        skill_id = f"skill_{skill_name}"
                        # 检查技能节点是否存在
                        if any(s['id'] == skill_id for s in skill_nodes):
                            job_edges.append({
                                "source": skill_id,
                                "target": job_id,
                                "type": "REQUIRES",
                                "strength": 0.7,
                                "metadata": {
                                    "relationship_category": "entity_related"
                                }
                            })
        
        return job_nodes, job_edges
    
    def _build_company_layer_from_entities(
        self,
        companies: List[Dict],
        job_nodes: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Entity(Organization)数据构建公司层"""
        company_nodes = []
        company_edges = []
        
        # 合并从职位提取的公司和用户直接相关的公司
        company_map = {}
        
        # 1. 从职位节点提取公司
        for job_node in job_nodes:
            company_name = job_node['metadata'].get('company')
            if company_name and company_name != '未知公司':
                if company_name not in company_map:
                    company_map[company_name] = {
                        'name': company_name,
                        'jobs': [],
                        'source': 'from_jobs',
                        'related_events': [],
                        'confidence': 0.5
                    }
                company_map[company_name]['jobs'].append(job_node['id'])
        
        # 2. 添加用户直接相关的公司
        for company in companies:
            company_name = company.get('name')
            user_relation = company.get('user_relation', {})
            relation_props = user_relation.get('properties', {})
            
            if company_name not in company_map:
                company_map[company_name] = {
                    'name': company_name,
                    'jobs': [],
                    'source': 'user_related',
                    'related_events': [],
                    'confidence': company.get('confidence', 0.8)
                }
            else:
                company_map[company_name]['source'] = 'both'
            
            # 添加相关事件信息
            for rel in company.get('entity_relations', []):
                if rel.get('relation') == 'HAPPENED_AT':
                    company_map[company_name]['related_events'].append(rel.get('target', {}).get('name'))
        
        if not company_map:
            return [], []
        
        # 构建公司节点
        radius = 58
        n = len(company_map)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, (company_name, company_data) in enumerate(company_map.items()):
            # Fibonacci球面算法
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            company_id = f"company_{i}"
            source = company_data['source']
            
            # 用户直接相关的公司用红色标记
            if source in ['user_related', 'both']:
                color = "#FF6B6B"
                size = 18
            else:
                color = "#722ED1"
                size = 16
            
            company_nodes.append({
                "id": company_id,
                "label": company_name,
                "type": "company",
                "layer": 3,
                "position": {"x": x, "y": y, "z": z},
                "size": size,
                "color": color,
                "metadata": {
                    "node_type": "Entity",
                    "entity_type": "Organization",
                    "source": source,
                    "job_count": len(company_data['jobs']),
                    "related_events": company_data['related_events'],
                    "is_user_related": source in ['user_related', 'both']
                }
            })
            
            # Job-PART_OF->Company关系
            for job_id in company_data['jobs']:
                company_edges.append({
                    "source": job_id,
                    "target": company_id,
                    "type": "PART_OF",
                    "strength": 0.8,
                    "metadata": {
                        "relationship_category": "entity_related"
                    }
                })
            
            # 如果是用户直接相关的公司，添加User->Company连接
            if source in ['user_related', 'both'] and company_data['related_events']:
                company_edges.append({
                    "source": "__me__",
                    "target": company_id,
                    "type": "RELATED_TO",
                    "strength": 0.9,
                    "metadata": {
                        "relationship_category": "user_related",
                        "events": company_data['related_events']
                    }
                })
        
        return company_nodes, company_edges
    
    def _build_event_layer(self, events: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Event数据构建事件层"""
        if not events:
            return [], []
        
        event_nodes = []
        event_edges = []
        
        # 事件节点放在外层
        radius = 75
        n = len(events)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, event in enumerate(events):
            # Fibonacci球面算法
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
                "layer": 4,
                "position": {"x": x, "y": y, "z": z},
                "size": 10,
                "color": "#13C2C2",
                "metadata": {
                    "node_type": "Event",
                    "event_type": event.get('type'),
                    "description": event.get('description', ''),
                    "start_time": str(event.get('start_time', '')),
                    "location": event.get('location', {}).get('name') if event.get('location') else '',
                    "sources": [s.get('source_id') for s in event.get('sources', []) if s]
                }
            })
            
            # User-PARTICIPATED_IN->Event关系
            event_edges.append({
                "source": "__me__",
                "target": event_id,
                "type": "PARTICIPATED_IN",
                "strength": 0.7,
                "metadata": {
                    "relationship_category": "user_related"
                }
            })
        
        return event_nodes, event_edges
    
    def _build_pattern_layer_from_data(self, patterns: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Pattern数据构建模式层"""
        if not patterns:
            return [], []
        
        pattern_nodes = []
        pattern_edges = []
        
        radius = 90
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
            
            pattern_nodes.append({
                "id": pattern_id,
                "label": pattern.get('name'),
                "type": "pattern",
                "layer": 5,
                "position": {"x": x, "y": y, "z": z},
                "size": 8,
                "color": "#EB2F96",
                "metadata": {
                    "node_type": "Pattern",
                    "pattern_type": pattern.get('type'),
                    "description": pattern.get('description', ''),
                    "frequency": pattern.get('frequency', 1),
                    "confidence": pattern.get('confidence', 0.5)
                }
            })
            
            # User-EXHIBITS->Pattern关系
            exhibition = pattern.get('exhibition', {})
            pattern_edges.append({
                "source": "__me__",
                "target": pattern_id,
                "type": "EXHIBITS",
                "strength": pattern.get('confidence', 0.5),
                "metadata": {
                    "relationship_category": "pattern_related",
                    "frequency": pattern.get('frequency', 1)
                }
            })
        
        return pattern_nodes, pattern_edges


# 创建全局实例
_neo4j_career_kg = None

def get_neo4j_career_kg():
    """获取Neo4j职业知识图谱实例"""
    global _neo4j_career_kg
    if _neo4j_career_kg is None:
        _neo4j_career_kg = Neo4jCareerKnowledgeGraph()
    return _neo4j_career_kg
