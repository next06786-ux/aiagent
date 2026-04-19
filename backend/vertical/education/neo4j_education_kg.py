"""
基于Neo4j的教育知识图谱构建器
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
class EducationUserProfile:
    """学生学业档案"""
    student_id: str  # 用户ID，必需
    
    # 当前教育背景
    current_school: str = "未知大学"
    major: str = "计算机科学"
    gpa: float = 3.5
    gpa_max: float = 4.0
    ranking_percent: float = 0.2  # 排名百分比（前20%）
    
    # 标化成绩
    toefl_score: int = 100
    gre_score: int = 320
    sat_act: int = 1400
    
    # 各科成绩（百分制）
    math_score: float = 85.0
    english_score: float = 80.0
    professional_score: float = 82.0
    
    # 科研背景
    research_experience: float = 0.5  # 科研经历（0-1，0.5表示中等）
    publications: int = 0
    
    # 申请意向
    target_degree: str = "硕士"  # 硕士/博士/本科
    target_major: str = "计算机科学"
    target_level: str = "master"  # master/phd/bachelor
    preferred_locations: List[str] = None  # ["北京", "上海", "深圳"]
    
    def __post_init__(self):
        if self.preferred_locations is None:
            self.preferred_locations = []


class Neo4jEducationKnowledgeGraph:
    """基于Neo4j的教育知识图谱构建器"""
    
    def __init__(self):
        # 连接Neo4j（用于information_kg）
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.unified_query = UnifiedKGQuery(self.driver)
    
    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.close()
    
    def get_complete_education_data(self, user_id: str) -> Dict[str, Any]:
        """
        使用统一框架获取完整的教育数据
        包含所有6种节点和4类关系
        """
        return self.unified_query.query_complete_domain_data(user_id, 'education')
    
    def _get_schools_from_information_kg(self, user_id: str, keyword: str = "", limit: int = 50) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        从Neo4j获取完整的教育数据
        充分利用6种节点和4类关系
        
        Returns:
            (schools, concepts, patterns): 学校列表、概念列表（兴趣/目标）、模式列表
        """
        try:
            with self.driver.session() as session:
                # 1. 查询User-INTERESTED_IN->School关系（用户相关关系）
                schools_query = """
                MATCH (u:User {user_id: $user_id})-[r:INTERESTED_IN]->(s:Entity)
                WHERE s.type = 'School'
                OPTIONAL MATCH (s)-[:EXTRACTED_FROM]->(src:Source)
                RETURN s.name as name,
                       elementId(s) as school_id,
                       s.category as category,
                       s.description as description,
                       s.attributes as attributes,
                       s.confidence as confidence,
                       r.interest_level as interest_level,
                       collect(DISTINCT src.source_id) as sources
                ORDER BY r.interest_level DESC
                LIMIT $limit
                """
                
                schools_result = session.run(schools_query, user_id=user_id, limit=limit)
                schools = []
                
                for record in schools_result:
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
                    
                    schools.append({
                        'name': record['name'],
                        'school_id': record['school_id'],
                        'location': attributes.get('location', ''),
                        'major': attributes.get('major', ''),
                        'level': attributes.get('level', 'master'),
                        'description': record['description'] or '',
                        'strength': record['interest_level'] or 0.5,
                        'confidence': record['confidence'] or 0.5,
                        'sources': record['sources'],
                        'source': 'neo4j_graph'
                    })
                
                print(f"[Neo4jEducationKG] 从Neo4j获取到 {len(schools)} 所学校（通过INTERESTED_IN关系）")
                
                # 2. 查询User-HAS_PROFILE->Concept关系（学习兴趣和目标）
                concepts_query = """
                MATCH (u:User {user_id: $user_id})-[r:HAS_PROFILE|INTERESTED_IN]->(c:Concept)
                WHERE c.type IN ['Interest', 'Goal']
                OPTIONAL MATCH (c)-[:EXTRACTED_FROM]->(s:Source)
                RETURN c.name as concept_name,
                       elementId(c) as concept_id,
                       c.type as concept_type,
                       c.description as description,
                       c.confidence as confidence,
                       collect(DISTINCT s.source_id) as sources
                ORDER BY c.confidence DESC
                LIMIT 20
                """
                
                concepts_result = session.run(concepts_query, user_id=user_id)
                concepts = []
                
                for record in concepts_result:
                    concepts.append({
                        'name': record['concept_name'],
                        'concept_id': record['concept_id'],
                        'type': record['concept_type'] or 'Interest',
                        'description': record['description'] or '',
                        'confidence': record['confidence'] or 0.5,
                        'sources': record['sources']
                    })
                
                print(f"[Neo4jEducationKG] 获取到 {len(concepts)} 个学习兴趣/目标（通过HAS_PROFILE/INTERESTED_IN关系）")
                
                # 3. 查询User-EXHIBITS->Pattern关系（学习模式）
                patterns_query = """
                MATCH (u:User {user_id: $user_id})-[r:EXHIBITS]->(pat:Pattern)
                WHERE pat.type IN ['Habit', 'Preference']
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
                        'type': record['pattern_type'] or 'Habit',
                        'description': record['description'] or '',
                        'frequency': record['frequency'] or 1,
                        'confidence': record['confidence'] or 0.5,
                        'evidence': record['evidence_list']
                    })
                
                print(f"[Neo4jEducationKG] 获取到 {len(patterns)} 个学习模式（通过EXHIBITS关系）")
                
                return schools, concepts, patterns
                
        except Exception as e:
            print(f"[Neo4jEducationKG] 从Neo4j获取数据失败: {e}")
            import traceback
            traceback.print_exc()
            return [], [], []

    def _get_schools_with_hybrid_retrieval(
        self, 
        user_id: str, 
        keyword: str = "", 
        location: str = "",
        limit: int = 50
    ) -> List[Dict]:
        """
        使用混合检索获取学校信息
        融合Neo4j图谱和RAG向量检索的结果
        """
        try:
            from backend.learning.kg_rag_integration import KGRAGIntegration
            
            # 构建查询
            query_parts = []
            if keyword:
                query_parts.append(f"专业：{keyword}")
            if location:
                query_parts.append(f"地区：{location}")
            query_parts.append("学校信息")
            
            query = "，".join(query_parts)
            
            print(f"[Neo4jEducationKG] 使用混合检索查询学校: {query}")
            
            # 使用混合检索
            kg_rag = KGRAGIntegration(user_id)
            results = kg_rag.hybrid_retrieve(
                query=query,
                query_type="FACTUAL",  # 查询事实信息
                domain="education",
                top_k=limit
            )
            
            # 转换为学校格式
            schools = []
            for result in results:
                # 检查是否是学校相关信息
                content = result.get('content', '')
                metadata = result.get('metadata', {})
                
                # 从内容中提取学校信息
                if 'School' in content or '学校' in content or '大学' in content:
                    school_name = metadata.get('entity_name', '')
                    if not school_name:
                        # 尝试从内容中提取
                        if '】' in content:
                            school_name = content.split('】')[1].split('，')[0]
                    
                    if school_name:
                        schools.append({
                            'name': school_name,
                            'school_id': metadata.get('neo4j_node_name', ''),
                            'location': metadata.get('location', location),
                            'major': keyword,
                            'description': content,
                            'strength': result.get('score', 0.5),
                            'confidence': result.get('score', 0.5),
                            'source': result.get('source', 'hybrid')
                        })
            
            print(f"[Neo4jEducationKG] 混合检索获取到 {len(schools)} 所学校")
            return schools[:limit]
            
        except Exception as e:
            print(f"[Neo4jEducationKG] 混合检索失败，降级到Neo4j查询: {e}")
            import traceback
            traceback.print_exc()
            # 降级到传统方法
            return self._get_schools_from_information_kg(user_id, keyword, limit)


    def build_education_graph(self, user_profile: EducationUserProfile, 
                             search_keyword: str = "", location: str = "",
                             use_hybrid: bool = False) -> Dict[str, Any]:
        """
        构建教育知识图谱 - 完全基于Neo4j架构规范（6种节点+4类关系）
        
        图谱结构（3D立体布局）：
        - 中心：User（我）
        - 第1层：兴趣/目标层（Concept节点，type='Interest/Goal'）
        - 第2层：学校层（Entity节点，type='School'）
        - 第3层：事件层（Event节点，申请/访校等）
        - 模式层：学习模式（Pattern节点）
        
        关系链：
        - User-HAS_PROFILE/INTERESTED_IN->Concept
        - User-INTERESTED_IN/APPLIED_TO->Entity(School)
        - User-PARTICIPATED_IN->Event
        - User-EXHIBITS->Pattern
        
        Args:
            user_profile: 学生学业档案
            search_keyword: 搜索关键词（专业）
            location: 地区
            use_hybrid: 是否使用混合检索（Neo4j + RAG）
        """
        # 使用统一框架获取完整数据
        complete_data = self.get_complete_education_data(user_profile.student_id)
        
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
                "student_id": user_profile.student_id,
                "node_type": "User",
                # 添加用户的详细信息
                "current_school": user_profile.current_school,
                "major": user_profile.major,
                "gpa": user_profile.gpa,
                "ranking_percent": user_profile.ranking_percent,
                "toefl_score": user_profile.toefl_score,
                "gre_score": user_profile.gre_score,
                "research_experience": user_profile.research_experience,
                "target_degree": user_profile.target_degree,
                "target_major": user_profile.target_major,
                "description": f"{user_profile.current_school} {user_profile.major}专业，GPA {user_profile.gpa}，目标：{user_profile.target_degree} {user_profile.target_major}"
            }
        }]
        edges = []
        
        # 提取数据
        entities = complete_data.get('entities', [])
        events = complete_data.get('events', [])
        concepts = complete_data.get('concepts', [])
        patterns = complete_data.get('patterns', [])
        
        # 分离学校
        schools = [e for e in entities if e.get('type') == 'School']
        
        # 第一圈：学校层（Entity(School)节点）- 只在3D图谱显示院校
        school_nodes, school_edges = self._build_school_layer_from_entities(schools, user_profile)
        
        # 为每个学校节点附加相关信息
        for school_node in school_nodes:
            school_name = school_node['label']
            
            # 附加与该学校相关的兴趣/目标
            related_concepts = []
            for concept in concepts:
                # 如果概念与学校相关(通过专业、兴趣匹配)
                related_concepts.append({
                    'name': concept.get('name'),
                    'type': concept.get('type'),
                    'description': concept.get('description', ''),
                    'confidence': concept.get('confidence', 0.5)
                })
            
            # 附加与该学校相关的事件
            related_events = []
            for event in events:
                # 检查事件是否涉及该学校
                school_full = next((s for s in schools if s.get('name') == school_name), None)
                if school_full and any(
                    r.get('relation') in ['APPLIED_TO', 'ADMITTED_TO', 'VISITED'] and 
                    r.get('target', {}).get('name') == school_name
                    for r in event.get('entity_relations', [])
                ):
                    related_events.append({
                        'name': event.get('name'),
                        'type': event.get('type'),
                        'description': event.get('description', ''),
                        'time': event.get('time', '')
                    })
            
            # 附加到节点metadata
            school_node['metadata']['related_concepts'] = related_concepts[:5]  # 最多5个
            school_node['metadata']['related_events'] = related_events
            school_node['metadata']['concept_count'] = len(related_concepts)
            school_node['metadata']['event_count'] = len(related_events)
        
        nodes.extend(school_nodes)
        edges.extend(school_edges)
        
        # 附加用户级别的学习模式信息
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
                "schools": [n["id"] for n in school_nodes]
            },
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": {
                    "User": 1,
                    "Entity_School": len(school_nodes)
                },
                "relationship_types": {
                    "INTERESTED_IN": len([e for e in edges if e['type'] == 'INTERESTED_IN']),
                    "APPLIED_TO": len([e for e in edges if e['type'] == 'APPLIED_TO'])
                },
                "user_patterns": user_patterns,  # 用户的学习模式
                "total_concepts": len(concepts),
                "total_events": len(events),
                "data_source": "unified_kg_query",
                "architecture_compliant": True,
                "display_mode": "schools_only_in_3d"
            }
        }
    
    def _build_concept_layer_from_data(self, concepts: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Concept数据构建兴趣/目标层"""
        if not concepts:
            return [], []
        
        concept_nodes = []
        concept_edges = []
        
        radius = 28  # 在学业层和学校层之间
        n = len(concepts)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, concept in enumerate(concepts):
            # Fibonacci球面算法
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            concept_id = f"concept_{i}"
            
            # 根据类型着色
            if concept['type'] == 'Interest':
                color = "#13C2C2"  # 青色
            else:  # Goal
                color = "#722ED1"  # 紫色
            
            concept_nodes.append({
                "id": concept_id,
                "label": concept['name'],
                "type": "concept",
                "layer": 1.5,
                "position": {"x": x, "y": y, "z": z},
                "size": 9,
                "color": color,
                "metadata": {
                    "node_type": "Concept",
                    "concept_type": concept['type'],
                    "description": concept['description'],
                    "confidence": concept['confidence'],
                    "sources": concept['sources']
                }
            })
            
            # User-HAS_PROFILE->Concept关系
            concept_edges.append({
                "source": "__me__",
                "target": concept_id,
                "type": "HAS_PROFILE",
                "strength": concept['confidence'],
                "metadata": {
                    "relationship_category": "user_related"
                }
            })
        
        return concept_nodes, concept_edges
    
    def _build_pattern_layer(self, patterns: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        构建模式层 - Pattern节点 + EXHIBITS关系
        展示学习习惯和偏好
        """
        if not patterns:
            return [], []
        
        pattern_nodes = []
        pattern_edges = []
        
        radius = 75  # 模式层半径（最外层）
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
                "layer": 4,
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
                    "frequency": pattern['frequency']
                }
            })
        
        return pattern_nodes, pattern_edges


    def _build_school_layer_from_information_kg(self, user_profile: EducationUserProfile, 
                                                academic_nodes: List[Dict]):
        """从information_kg构建学校层 - 3D球面分布"""
        # 从information_kg获取用户提取的学校信息（不使用关键词过滤）
        schools = self._get_schools_from_information_kg(
            user_id=user_profile.student_id,
            keyword="",  # 不使用关键词过滤，在后面的匹配阶段处理
            limit=50
        )
        
        if not schools:
            print("[Neo4jEducationKG] 未找到符合条件的学校")
            return [], []
        
        print(f"[Neo4jEducationKG] 共获取 {len(schools)} 所候选学校")
        
        # 使用简单的匹配算法（基于专业匹配度和用户关注度）
        schools_with_match = []
        for school in schools:
            # 计算匹配度
            match_score = school.get('strength', 0.5)
            
            # 如果学校的专业与目标专业匹配，提高分数
            if user_profile.target_major and user_profile.target_major in school.get('major', ''):
                match_score = min(match_score + 0.3, 1.0)
            
            # 如果学校位置与意向地区匹配，提高分数
            if user_profile.preferred_locations:
                if any(loc in school.get('location', '') for loc in user_profile.preferred_locations):
                    match_score = min(match_score + 0.2, 1.0)
            
            # 分类
            if match_score >= 0.7:
                category = 'safety'
            elif match_score >= 0.4:
                category = 'match'
            else:
                category = 'reach'
            
            school['match_score'] = match_score
            school['match_category'] = category
            school['match_reasons'] = [f"匹配度 {match_score*100:.0f}%"]
            schools_with_match.append(school)
        
        # 按匹配分数排序，选择top 20
        schools_with_match.sort(key=lambda x: x['match_score'], reverse=True)
        top_schools = schools_with_match[:20]
        
        print(f"[Neo4jEducationKG] 匹配完成，推荐 {len(top_schools)} 所学校")
        print(f"  - 保底学校: {sum(1 for s in top_schools if s['match_category'] == 'safety')} 所")
        print(f"  - 匹配学校: {sum(1 for s in top_schools if s['match_category'] == 'match')} 所")
        print(f"  - 冲刺学校: {sum(1 for s in top_schools if s['match_category'] == 'reach')} 所")
        
        school_nodes = []
        school_edges = []
        
        radius = 38
        n = len(top_schools)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, school in enumerate(top_schools):
            # Fibonacci球面算法
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            school_id = f"school_{i}"
            
            # 根据匹配类别着色
            if school['match_category'] == 'safety':
                color = "#52C41A"  # 保底 - 绿色
                tier_label = "保底"
                size = 10
            elif school['match_category'] == 'match':
                color = "#1890FF"  # 匹配 - 蓝色
                tier_label = "匹配"
                size = 12
            else:  # reach
                color = "#FF4D4F"  # 冲刺 - 红色
                tier_label = "冲刺"
                size = 14
            
            school_nodes.append({
                "id": school_id,
                "label": school['name'],
                "type": "school",
                "layer": 2,
                "position": {"x": x, "y": y, "z": z},
                "size": size,
                "color": color,
                "metadata": {
                    "location": school.get('location', ''),
                    "tier": tier_label,
                    "major": school.get('major', ''),
                    "description": school.get('description', ''),
                    "match_score": school['match_score'],
                    "match_category": school['match_category'],
                    "match_reasons": school['match_reasons'],
                    "source": "information_kg"
                }
            })
            
            # 连接到第一个学业成就节点
            if academic_nodes:
                school_edges.append({
                    "source": academic_nodes[0]["id"],
                    "target": school_id,
                    "type": "qualifies_for",
                    "strength": school['match_score']
                })
        
        return school_nodes, school_edges

    def _build_school_layer_with_hybrid(
        self, 
        user_profile: EducationUserProfile,
        academic_nodes: List[Dict],
        search_keyword: str = "",
        location: str = ""
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        使用混合检索构建学校层
        融合Neo4j和RAG的数据
        """
        # 使用混合检索获取学校
        schools = self._get_schools_with_hybrid_retrieval(
            user_id=user_profile.student_id,
            keyword=search_keyword or user_profile.target_major,
            location=location or (user_profile.preferred_locations[0] if user_profile.preferred_locations else ""),
            limit=50
        )
        
        # 使用通用方法构建节点和边
        return self._build_school_nodes_and_edges(schools, user_profile, academic_nodes)

    def _build_school_nodes_and_edges(
        self,
        schools: List[Dict],
        user_profile: EducationUserProfile,
        academic_nodes: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        通用方法：从学校列表构建节点和边
        支持任何来源的学校数据（Neo4j、混合检索等）
        """
        if not schools:
            print("[Neo4jEducationKG] 未找到符合条件的学校")
            return [], []
        
        print(f"[Neo4jEducationKG] 共获取 {len(schools)} 所候选学校")
        
        # 使用简单的匹配算法
        schools_with_match = []
        for school in schools:
            # 计算匹配度
            match_score = school.get('strength', 0.5)
            
            # 如果有confidence字段（来自混合检索），也考虑进去
            if 'confidence' in school:
                match_score = (match_score + school['confidence']) / 2
            
            # 如果学校的专业与目标专业匹配，提高分数
            if user_profile.target_major and user_profile.target_major in school.get('major', ''):
                match_score = min(match_score + 0.3, 1.0)
            
            # 如果学校位置与意向地区匹配，提高分数
            if user_profile.preferred_locations:
                if any(loc in school.get('location', '') for loc in user_profile.preferred_locations):
                    match_score = min(match_score + 0.2, 1.0)
            
            # 分类
            if match_score >= 0.7:
                category = 'safety'
            elif match_score >= 0.4:
                category = 'match'
            else:
                category = 'reach'
            
            school['match_score'] = match_score
            school['match_category'] = category
            school['match_reasons'] = [f"匹配度 {match_score*100:.0f}%"]
            schools_with_match.append(school)
        
        # 按匹配分数排序，选择top 20
        schools_with_match.sort(key=lambda x: x['match_score'], reverse=True)
        top_schools = schools_with_match[:20]
        
        print(f"[Neo4jEducationKG] 匹配完成，推荐 {len(top_schools)} 所学校")
        print(f"  - 保底学校: {sum(1 for s in top_schools if s['match_category'] == 'safety')} 所")
        print(f"  - 匹配学校: {sum(1 for s in top_schools if s['match_category'] == 'match')} 所")
        print(f"  - 冲刺学校: {sum(1 for s in top_schools if s['match_category'] == 'reach')} 所")
        
        school_nodes = []
        school_edges = []
        
        radius = 38
        n = len(top_schools)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, school in enumerate(top_schools):
            # Fibonacci球面算法
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            school_id = f"school_{i}"
            
            # 根据匹配类别着色
            if school['match_category'] == 'safety':
                color = "#52C41A"  # 保底 - 绿色
                tier_label = "保底"
                size = 10
            elif school['match_category'] == 'match':
                color = "#1890FF"  # 匹配 - 蓝色
                tier_label = "匹配"
                size = 12
            else:  # reach
                color = "#FF4D4F"  # 冲刺 - 红色
                tier_label = "冲刺"
                size = 14
            
            school_nodes.append({
                "id": school_id,
                "label": school['name'],
                "type": "school",
                "layer": 2,
                "position": {"x": x, "y": y, "z": z},
                "size": size,
                "color": color,
                "metadata": {
                    "location": school.get('location', ''),
                    "tier": tier_label,
                    "major": school.get('major', ''),
                    "description": school.get('description', ''),
                    "match_score": school['match_score'],
                    "match_category": school['match_category'],
                    "match_reasons": school['match_reasons'],
                    "source": school.get('source', 'unknown')
                }
            })
            
            # 连接到第一个学业成就节点
            if academic_nodes:
                school_edges.append({
                    "source": academic_nodes[0]["id"],
                    "target": school_id,
                    "type": "qualifies_for",
                    "strength": school['match_score']
                })
        
        return school_nodes, school_edges
    
    def _build_action_layer(self, school_nodes: List[Dict]):
        """构建行动层 - 3D球面分布"""
        actions = [
            {"label": "提升GPA", "type": "academic"},
            {"label": "发表论文", "type": "research"},
            {"label": "准备考试", "type": "exam"},
            {"label": "联系导师", "type": "networking"}
        ]
        
        action_nodes = []
        action_edges = []
        
        radius = 58
        n = len(actions)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, action in enumerate(actions):
            # Fibonacci球面算法
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            action_nodes.append({
                "id": f"action_{i}",
                "label": action['label'],
                "type": "action",
                "layer": 3,
                "position": {"x": x, "y": y, "z": z},
                "size": 8,
                "color": "#722ED1"
            })
            
            # 连接到前3所学校
            for school in school_nodes[:3]:
                action_edges.append({
                    "source": school["id"],
                    "target": f"action_{i}",
                    "type": "requires_action",
                    "strength": 0.4
                })
        
        return action_nodes, action_edges


# 新的构建方法（使用统一框架）
    def _build_concept_layer_from_data(self, concepts: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Concept数据构建兴趣/目标层"""
        if not concepts:
            return [], []
        
        concept_nodes = []
        concept_edges = []
        
        radius = 18
        n = len(concepts)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, concept in enumerate(concepts):
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            user_relation = concept.get('user_relation', {})
            confidence = user_relation.get('properties', {}).get('confidence', 0.5)
            
            concept_nodes.append({
                "id": f"concept_{concept.get('name')}",
                "label": concept.get('name'),
                "type": "concept",
                "layer": 1,
                "position": {"x": x, "y": y, "z": z},
                "size": 10,
                "color": "#FAAD14",
                "metadata": {
                    "node_type": "Concept",
                    "concept_type": concept.get('type'),
                    "description": concept.get('description', ''),
                    "confidence": confidence
                }
            })
            
            concept_edges.append({
                "source": "__me__",
                "target": f"concept_{concept.get('name')}",
                "type": user_relation.get('type', 'INTERESTED_IN'),
                "strength": confidence,
                "metadata": {"relationship_category": "user_related"}
            })
        
        return concept_nodes, concept_edges
    
    def _build_school_layer_from_entities(self, schools: List[Dict], user_profile: EducationUserProfile) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Entity(School)数据构建学校层 - 只显示目标院校"""
        if not schools:
            return [], []
        
        # 过滤掉当前学校，只保留目标院校
        target_schools = []
        for school in schools:
            school_name = school.get('name', '')
            # 如果学校名称与当前学校相同，跳过
            if school_name == user_profile.current_school:
                continue
            # 只保留INTERESTED_IN或APPLIED_TO关系的学校（目标院校）
            user_relation = school.get('user_relation', {})
            relation_type = user_relation.get('type', '')
            if relation_type in ['INTERESTED_IN', 'APPLIED_TO', 'ADMITTED_TO']:
                target_schools.append(school)
        
        if not target_schools:
            return [], []
        
        school_nodes = []
        school_edges = []
        
        radius = 38
        n = len(target_schools)
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, school in enumerate(target_schools):
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            school_id = f"school_{i}"
            user_relation = school.get('user_relation', {})
            relation_type = user_relation.get('type', 'INTERESTED_IN')
            interest_level = user_relation.get('properties', {}).get('interest_level', 0.5)
            
            attributes = school.get('attributes', {})
            if isinstance(attributes, str):
                try:
                    import json
                    attributes = json.loads(attributes)
                except:
                    attributes = {}
            
            school_nodes.append({
                "id": school_id,
                "label": school.get('name'),
                "type": "school",
                "layer": 2,
                "position": {"x": x, "y": y, "z": z},
                "size": 14,
                "color": "#1890FF",
                "metadata": {
                    "node_type": "Entity",
                    "entity_type": "School",
                    "location": attributes.get('location', ''),
                    "major": attributes.get('major', ''),
                    "level": attributes.get('level', 'master'),
                    "tier": attributes.get('tier', ''),
                    "ranking": attributes.get('ranking', 0),
                    "description": school.get('description', ''),
                    "confidence": school.get('confidence', 0.5)
                }
            })
            
            school_edges.append({
                "source": "__me__",
                "target": school_id,
                "type": relation_type,
                "strength": interest_level,
                "metadata": {"relationship_category": "user_related"}
            })
        
        return school_nodes, school_edges
    
    def _build_event_layer_from_data(self, events: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Event数据构建事件层"""
        if not events:
            return [], []
        
        event_nodes = []
        event_edges = []
        
        radius = 58
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
                "layer": 3,
                "position": {"x": x, "y": y, "z": z},
                "size": 10,
                "color": "#13C2C2",
                "metadata": {
                    "node_type": "Event",
                    "event_type": event.get('type'),
                    "description": event.get('description', ''),
                    "start_time": str(event.get('start_time', ''))
                }
            })
            
            event_edges.append({
                "source": "__me__",
                "target": event_id,
                "type": "PARTICIPATED_IN",
                "strength": 0.7,
                "metadata": {"relationship_category": "user_related"}
            })
        
        return event_nodes, event_edges
    
    def _build_pattern_layer_from_data(self, patterns: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """从统一框架返回的Pattern数据构建模式层"""
        if not patterns:
            return [], []
        
        pattern_nodes = []
        pattern_edges = []
        
        radius = 75
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
                "size": 8,
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
_neo4j_education_kg = None

def get_neo4j_education_kg():
    """获取Neo4j教育知识图谱实例"""
    global _neo4j_education_kg
    if _neo4j_education_kg is None:
        _neo4j_education_kg = Neo4jEducationKnowledgeGraph()
    return _neo4j_education_kg
