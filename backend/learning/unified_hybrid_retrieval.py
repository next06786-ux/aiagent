"""
统一混合检索系统 (Unified Hybrid Retrieval System)

设计理念：
1. 配置驱动：通过配置文件定义检索策略，而非硬编码
2. 插件化架构：支持多种检索器（Neo4j、RAG、Elasticsearch等）
3. 智能融合：基于查询类型自动选择最优检索策略
4. 可扩展性：易于添加新的检索器和融合算法
5. LLM增强：使用LLM理解查询意图，生成智能查询和排序

核心组件：
- RetrievalConfig: 检索配置
- BaseRetriever: 检索器基类
- Neo4jRetriever: Neo4j图检索器（LLM增强）
- RAGRetriever: 向量检索器
- HybridFusion: 混合融合引擎
- UnifiedHybridRetrieval: 统一检索接口

作者: AI System
版本: 3.0 (LLM增强版)
日期: 2026-04-19
"""

from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import os
from datetime import datetime


# ==================== 数据结构定义 ====================

class QueryType(Enum):
    """查询类型"""
    FACTUAL = "factual"              # 事实查询（精确匹配）
    SEMANTIC = "semantic"            # 语义查询（模糊匹配）
    RELATIONAL = "relational"        # 关系查询（图遍历）
    TEMPORAL = "temporal"            # 时序查询（时间相关）
    ANALYTICAL = "analytical"        # 分析查询（聚合统计）
    EXPLORATORY = "exploratory"      # 探索查询（发现新知识）


class RetrievalStrategy(Enum):
    """检索策略"""
    GRAPH_ONLY = "graph_only"           # 纯图检索
    VECTOR_ONLY = "vector_only"         # 纯向量检索
    HYBRID_PARALLEL = "hybrid_parallel" # 并行混合（同时检索后融合）
    HYBRID_SERIAL = "hybrid_serial"     # 串行混合（先图后向量）
    ADAPTIVE = "adaptive"               # 自适应（根据查询类型选择）


class FusionMethod(Enum):
    """融合方法"""
    WEIGHTED_SUM = "weighted_sum"       # 加权求和
    RRF = "rrf"                         # Reciprocal Rank Fusion
    BORDA_COUNT = "borda_count"         # Borda计数
    LEARNED = "learned"                 # 学习融合（基于历史反馈）


@dataclass
class RetrievalConfig:
    """检索配置"""
    # 基础配置
    max_results: int = 100  # 增加默认值从50到100，提供更多上下文
    min_confidence: float = 0.2  # 降低最小置信度，允许更多结果
    
    # 检索策略
    strategy: RetrievalStrategy = RetrievalStrategy.ADAPTIVE
    fusion_method: FusionMethod = FusionMethod.RRF
    
    # 权重配置（用于加权融合）
    graph_weight: float = 0.6
    vector_weight: float = 0.4
    
    # 领域过滤
    domain_filter: Optional[str] = None  # career/education/relationship
    
    # 时间过滤
    time_decay_enabled: bool = True
    time_decay_factor: float = 0.1  # 每天衰减10%
    
    # 关系扩展
    expand_relations: bool = True
    max_relation_depth: int = 2
    
    # 查询增强
    query_expansion: bool = True
    use_synonyms: bool = True
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 秒
    
    # 调试模式
    debug_mode: bool = False
    
    @classmethod
    def from_query_type(cls, query_type: QueryType) -> 'RetrievalConfig':
        """根据查询类型创建最优配置"""
        configs = {
            QueryType.FACTUAL: cls(
                strategy=RetrievalStrategy.GRAPH_ONLY,
                expand_relations=False,
                graph_weight=1.0,
                vector_weight=0.0
            ),
            QueryType.SEMANTIC: cls(
                strategy=RetrievalStrategy.VECTOR_ONLY,
                query_expansion=True,
                graph_weight=0.0,
                vector_weight=1.0
            ),
            QueryType.RELATIONAL: cls(
                strategy=RetrievalStrategy.GRAPH_ONLY,
                expand_relations=True,
                max_relation_depth=3,
                graph_weight=1.0,
                vector_weight=0.0
            ),
            QueryType.TEMPORAL: cls(
                strategy=RetrievalStrategy.HYBRID_PARALLEL,
                time_decay_enabled=True,
                graph_weight=0.5,
                vector_weight=0.5
            ),
            QueryType.ANALYTICAL: cls(
                strategy=RetrievalStrategy.HYBRID_PARALLEL,
                expand_relations=True,
                graph_weight=0.7,
                vector_weight=0.3
            ),
            QueryType.EXPLORATORY: cls(
                strategy=RetrievalStrategy.HYBRID_PARALLEL,
                query_expansion=True,
                expand_relations=True,
                graph_weight=0.5,
                vector_weight=0.5
            )
        }
        return configs.get(query_type, cls())


@dataclass
class RetrievalResult:
    """检索结果"""
    id: str
    content: str
    score: float
    source: str  # 'graph' or 'vector' or 'hybrid'
    node_type: str
    category: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 额外信息
    confidence: float = 0.0
    timestamp: Optional[datetime] = None
    relations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        def make_json_serializable(obj):
            """递归转换对象为JSON可序列化格式"""
            if isinstance(obj, dict):
                return {k: make_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_serializable(item) for item in obj]
            elif hasattr(obj, 'isoformat'):  # DateTime对象
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):  # 其他对象
                return str(obj)
            else:
                return obj
        
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "source": self.source,
            "node_type": self.node_type,
            "category": self.category,
            "metadata": make_json_serializable(self.metadata),
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "relations": make_json_serializable(self.relations)
        }


@dataclass
class RetrievalContext:
    """检索上下文（返回给调用者）"""
    results: List[RetrievalResult]
    query: str
    query_type: QueryType
    strategy_used: RetrievalStrategy
    fusion_method: FusionMethod
    
    # 统计信息
    total_results: int
    graph_results: int
    vector_results: int
    execution_time_ms: float
    
    # 调试信息
    debug_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "results": [r.to_dict() for r in self.results],
            "query": self.query,
            "query_type": self.query_type.value,
            "strategy_used": self.strategy_used.value,
            "fusion_method": self.fusion_method.value,
            "stats": {
                "total_results": self.total_results,
                "graph_results": self.graph_results,
                "vector_results": self.vector_results,
                "execution_time_ms": self.execution_time_ms
            },
            "debug_info": self.debug_info
        }



# ==================== 检索器基类 ====================

class BaseRetriever(ABC):
    """检索器基类"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.enabled = True
    
    @abstractmethod
    def retrieve(
        self,
        query: str,
        max_results: int = 50,  # 增加默认值
        filters: Dict[str, Any] = None
    ) -> List[RetrievalResult]:
        """
        执行检索
        
        Args:
            query: 查询字符串
            max_results: 最大结果数
            filters: 过滤条件（domain, category, time_range等）
        
        Returns:
            检索结果列表
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取检索器统计信息"""
        pass
    
    def is_available(self) -> bool:
        """检查检索器是否可用"""
        return self.enabled


class Neo4jRetriever(BaseRetriever):
    """Neo4j图检索器 - 直接使用Neo4j驱动"""
    
    def __init__(self, user_id: str, config: Dict[str, Any] = None):
        super().__init__("neo4j", config)
        self.user_id = user_id
        self.driver = None
        self._init_connection()
    
    def _init_connection(self):
        """初始化Neo4j连接"""
        try:
            from neo4j import GraphDatabase
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            
            # 从环境变量获取 Neo4j 连接信息
            neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
            neo4j_password = os.getenv('NEO4J_PASSWORD', 'your_password')
            
            self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            print(f"✅ [Neo4jRetriever] 连接成功: user={self.user_id}")
        except Exception as e:
            print(f"❌ [Neo4jRetriever] 连接失败: {e}")
            self.enabled = False
    
    def retrieve(
        self,
        query: str,
        max_results: int = 50,  # 增加默认值
        filters: Dict[str, Any] = None
    ) -> List[RetrievalResult]:
        """
        从Neo4j检索 - 支持6种节点类型和4类关系
        
        节点类型：User, Entity, Event, Concept, Pattern, Source
        关系类型：用户关系、溯源关系、实体关系、模式关系
        
        使用两阶段语义检索：
        1. 第一阶段：宽松查询，获取相关领域的候选集
        2. 第二阶段：LLM对候选集进行语义相关性判断和排序
        """
        if not self.driver or not self.enabled:
            return []
        
        filters = filters or {}
        results = []
        
        try:
            # 1. 第一阶段：使用LLM识别查询领域，获取候选集
            print(f"[Neo4jRetriever] 两阶段语义检索...")
            # 限制候选数量，避免第二阶段超时
            # 减少到30个候选，加快处理速度
            max_candidates = min(max_results * 3, 30)  # 最多30个候选
            candidates = self._get_semantic_candidates(query, filters, max_candidates)
            
            if not candidates:
                print(f"[Neo4jRetriever] 未找到候选结果，降级到传统检索...")
                return self._traditional_retrieve(query, max_results, filters)
            
            print(f"[Neo4jRetriever] 第一阶段获取 {len(candidates)} 个候选结果")
            
            # 2. 第二阶段：LLM对候选集进行语义相关性判断和排序（带超时）
            try:
                import asyncio
                # 设置15秒超时（给qwen-turbo足够时间处理排序）
                ranked_items = asyncio.run(
                    asyncio.wait_for(
                        self._llm_rank_results_async(query, candidates, max_results),
                        timeout=15.0
                    )
                )
            except asyncio.TimeoutError:
                print(f"[Neo4jRetriever] ⚠️ LLM排序超时，使用简单排序")
                # 超时时使用简单的相关性排序，只返回需要的数量
                ranked_items = [{'item': c, 'score': 0.5} for c in candidates[:max_results]]
            except Exception as e:
                print(f"[Neo4jRetriever] ⚠️ LLM排序失败: {e}，使用简单排序")
                ranked_items = [{'item': c, 'score': 0.5} for c in candidates[:max_results]]
            
            print(f"[Neo4jRetriever] 第二阶段LLM排序后保留 {len(ranked_items)} 个结果")
            
            # 3. 转换为 RetrievalResult
            for item_data in ranked_items:
                item = item_data['item']
                score = item_data['score']
                
                results.append(RetrievalResult(
                    id=item.get('id', ''),
                    content=self._format_content(item),
                    score=score,
                    source='neo4j',
                    node_type=item.get('node_label', item.get('rel_type', 'unknown')),
                    category=item.get('category', 'unknown'),
                    metadata=item,
                    confidence=score,
                    timestamp=self._parse_timestamp(item.get('extracted_at')),
                    relations=[]
                ))
            
            print(f"[Neo4jRetriever] 最终返回 {len(results)} 个结果")
            return results[:max_results]
            
        except Exception as e:
            print(f"❌ [Neo4jRetriever] 检索失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_semantic_candidates(self, query: str, filters: Dict, max_candidates: int = 100) -> List[Dict]:
        """
        第一阶段：获取语义相关的候选集
        
        策略：
        1. 使用LLM识别查询涉及的领域（教育/职业/人际等）
        2. 宽松查询该领域的所有相关节点
        3. 返回候选集供第二阶段语义排序
        """
        # 限制候选数量，避免查询过多数据
        max_candidates = min(max_candidates, 30)  # 最多30个
        
        try:
            from backend.llm.llm_service import get_llm_service
            llm_service = get_llm_service()
            
            if not llm_service or not llm_service.enabled:
                # LLM不可用，使用传统方法
                return self._get_traditional_candidates(query, filters, max_candidates)
            
            # 使用LLM识别查询领域
            system_prompt = """你是一个查询分析专家。分析用户查询，识别涉及的领域和实体类型。

返回JSON格式：
{
  "domains": ["education", "career", "relationship", "skill", "event"],  // 涉及的领域
  "entity_types": ["School", "Job", "Person", "Concept"],  // 相关的实体类型
  "should_include_relations": true/false,  // 是否需要包含关系
  "explanation": "分析说明"
}

领域映射：
- education: 教育相关（学校、专业、学历等）
- career: 职业相关（工作、公司、职位等）
- relationship: 人际关系（朋友、家人、同事等）
- skill: 技能兴趣（技能、兴趣、价值观等）
- event: 事件经历

实体类型：
- School: 学校
- Job: 工作职位
- Person: 人物
- Organization: 组织机构
- Concept: 概念（技能、兴趣等）
- Event: 事件

只返回JSON，不要其他内容。"""
            
            user_prompt = f"用户查询：{query}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = llm_service.chat(messages, temperature=0.3, response_format="json_object", model="qwen-turbo")
            analysis = json.loads(response)
            
            domains = analysis.get('domains', [])
            entity_types = analysis.get('entity_types', [])
            include_relations = analysis.get('should_include_relations', False)
            
            print(f"[Neo4jRetriever] 查询领域: {domains}, 实体类型: {entity_types}")
            
            # 构建宽松的Cypher查询
            candidates = []
            
            with self.driver.session() as session:
                # 查询相关实体节点
                if entity_types:
                    type_conditions = " OR ".join([f"n.type = '{t}'" for t in entity_types])
                    node_query = f"""
                    MATCH (n:Entity)
                    WHERE n.user_id = $user_id AND ({type_conditions})
                    RETURN elementId(n) as id, labels(n) as labels, properties(n) as props
                    LIMIT {max_candidates}
                    """
                else:
                    # 如果没有明确类型，查询所有Entity
                    node_query = f"""
                    MATCH (n:Entity)
                    WHERE n.user_id = $user_id
                    RETURN elementId(n) as id, labels(n) as labels, properties(n) as props
                    LIMIT {max_candidates}
                    """
                
                result = session.run(node_query, user_id=self.user_id)
                
                for record in result:
                    item_data = self._parse_query_result(record)
                    if item_data:
                        candidates.append(item_data)
                
                # 如果需要，也查询关系
                if include_relations and len(candidates) < max_candidates:
                    rel_query = f"""
                    MATCH (n)-[r]->(m)
                    WHERE n.user_id = $user_id OR m.user_id = $user_id
                    RETURN 
                        elementId(r) as id,
                        type(r) as rel_type,
                        properties(r) as props,
                        labels(n) as source_labels,
                        properties(n) as source_props,
                        labels(m) as target_labels,
                        properties(m) as target_props
                    LIMIT {max_candidates // 2}
                    """
                    
                    rel_result = session.run(rel_query, user_id=self.user_id)
                    
                    for record in rel_result:
                        rel_props = dict(record['props'])
                        source_props = dict(record['source_props'])
                        target_props = dict(record['target_props'])
                        
                        source_name = source_props.get('name', 'Unknown')
                        target_name = target_props.get('name', 'Unknown')
                        rel_type = record['rel_type']
                        
                        rel_data = {
                            'id': record['id'],
                            'item_type': 'relationship',
                            'rel_type': rel_type,
                            'source_label': record['source_labels'][0] if record['source_labels'] else 'Unknown',
                            'target_label': record['target_labels'][0] if record['target_labels'] else 'Unknown',
                            'source_name': source_name,
                            'target_name': target_name,
                            'name': f"{source_name}-{rel_type}->{target_name}",
                            **rel_props
                        }
                        candidates.append(rel_data)
            
            return candidates
            
        except Exception as e:
            print(f"⚠️ [Neo4jRetriever] 获取候选集失败: {e}")
            return self._get_traditional_candidates(query, filters, max_candidates)
    
    def _get_traditional_candidates(self, query: str, filters: Dict, max_candidates: int) -> List[Dict]:
        """传统方法获取候选集（降级方案）"""
        candidates = []
        
        try:
            with self.driver.session() as session:
                # 查询所有Entity节点
                node_query = f"""
                MATCH (n:Entity)
                WHERE n.user_id = $user_id
                RETURN elementId(n) as id, labels(n) as labels, properties(n) as props
                LIMIT {max_candidates}
                """
                
                result = session.run(node_query, user_id=self.user_id)
                
                for record in result:
                    item_data = self._parse_query_result(record)
                    if item_data:
                        candidates.append(item_data)
        
        except Exception as e:
            print(f"❌ [Neo4jRetriever] 传统候选集获取失败: {e}")
        
        return candidates
    
    def _generate_smart_cypher(self, query: str, filters: Dict) -> tuple:
        """
        使用 LLM 生成智能 Cypher 查询
        
        Returns:
            (cypher_query, search_strategy)
        """
        try:
            from backend.llm.llm_service import get_llm_service
            llm_service = get_llm_service()
            
            if not llm_service or not llm_service.enabled:
                return None, None
            
            # 构建提示词
            system_prompt = """你是一个 Neo4j Cypher 查询专家。根据用户的自然语言查询，生成最优的 Cypher 查询语句。

数据库架构：
- 节点类型：User, Entity (Person/Job/School/Organization/Location), Event, Concept (Skill/Interest/Value/Goal), Pattern, Source
- 关系类型：HAS_PROFILE, KNOWS, INTERESTED_IN, APPLIED_TO, PARTICIPATED_IN, EXTRACTED_FROM, MENTIONED_IN, CREATED_BY, RELATED_TO, PART_OF, INVOLVES, REQUIRES, LOCATED_IN, HAPPENED_AT, EXHIBITS, SUPPORTS, INFLUENCES

**实际数据结构**：
- 所有节点都有 user_id 属性用于过滤用户数据
- Entity节点的常见属性：name, type, category, description, attributes, confidence, weight
- School类型的Entity：type='School', category='university', attributes包含JSON格式的详细信息（如major, level, tier, ranking）
- Person类型的Entity：type='Person', category可能是friends/family/colleagues
- Job类型的Entity：type='Job', category='position'
- **重要**：详细信息（如年级、专业、薪资等）通常存储在attributes JSON字段中，不是独立属性
- **数据完整性**：数据库可能不包含查询中的所有信息，应该使用宽松的条件

**重要语法规则**：
- ❌ 不要使用 `exists(n.property)` 语法（已废弃）
- ✅ 使用 `n.property IS NOT NULL` 检查属性存在
- ✅ 使用 `n.property = 'value'` 检查属性值
- ✅ 使用 `n.attributes =~ '.*关键词.*'` 在JSON字段中搜索

**查询策略**：
- 提取查询中的**核心关键词**（如"985"、"学校"、"工作"等）
- **优先匹配核心关键词**，不要同时要求所有细节都匹配
- 例如："985大三学生" → 重点是"985"和"学校"，"大三"可能没有数据，不要强制要求
- 使用OR条件组合多个可能的匹配方式，提高召回率

返回 JSON 格式：
{
  "cypher": "MATCH ... WHERE ... RETURN ...",
  "strategy": "描述检索策略",
  "explanation": "为什么这样查询"
}

要求：
1. 查询必须包含 WHERE n.user_id = $user_id 过滤条件
2. 理解查询意图，提取核心关键词
3. **必须包含 RETURN 子句**：RETURN elementId(n) as id, labels(n) as labels, properties(n) as props
4. LIMIT 100 必须在 RETURN 之后
5. 只返回 JSON，不要其他内容
6. **不要使用 exists() 函数，使用 IS NOT NULL 代替**
7. **不要过度限制条件**：优先匹配核心关键词，不要同时要求所有细节

示例：
- ❌ 错误：WHERE n.type = 'School' AND n.attributes =~ '.*985.*' AND n.attributes =~ '.*大三.*' （过度限制）
- ✅ 正确：WHERE n.type = 'School' AND n.attributes =~ '.*985.*' （只匹配核心关键词）
- ❌ 错误：WHERE n.type = 'School' AND n.grade IS NOT NULL （grade不是独立属性）
- ✅ 正确：WHERE n.type = 'School' AND n.attributes =~ '.*985.*'
- ❌ 错误：WHERE exists(n.grade)
- ✅ 正确：WHERE n.type = 'School'
- ❌ 错误：MATCH (n) WHERE ... LIMIT 100
- ✅ 正确：MATCH (n) WHERE ... RETURN elementId(n) as id, labels(n) as labels, properties(n) as props LIMIT 100"""
            
            user_prompt = f"""用户查询：{query}

请生成 Cypher 查询。"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = llm_service.chat(messages, temperature=0.3, response_format="json_object", model="qwen-turbo")
            result = json.loads(response)
            
            cypher_query = result.get('cypher')
            strategy = result.get('strategy', 'LLM智能检索')
            
            if not cypher_query:
                return None, None
            
            # 自动修复旧的 exists() 语法
            if 'exists(' in cypher_query:
                import re
                # 将 exists(n.property) 替换为 n.property IS NOT NULL
                cypher_query = re.sub(
                    r'exists\((\w+)\.(\w+)\)',
                    r'\1.\2 IS NOT NULL',
                    cypher_query
                )
                print(f"[Neo4jRetriever] 自动修复了 exists() 语法")
            
            # 自动修复缺少 RETURN 子句的查询
            if 'RETURN' not in cypher_query.upper():
                # 在 LIMIT 之前添加 RETURN 子句
                if 'LIMIT' in cypher_query.upper():
                    cypher_query = cypher_query.replace('LIMIT', 'RETURN elementId(n) as id, labels(n) as labels, properties(n) as props LIMIT')
                else:
                    # 在查询末尾添加 RETURN 子句
                    cypher_query += ' RETURN elementId(n) as id, labels(n) as labels, properties(n) as props LIMIT 100'
                print(f"[Neo4jRetriever] 自动添加了 RETURN 子句")
            
            return cypher_query, strategy
            
        except Exception as e:
            print(f"⚠️ [Neo4jRetriever] LLM 生成查询失败: {e}")
            return None, None
    
    def _parse_query_result(self, record) -> Optional[Dict]:
        """解析查询结果"""
        try:
            labels = record.get('labels', [])
            props = dict(record.get('props', {}))
            
            return {
                'id': record.get('id', ''),
                'node_label': labels[0] if labels else 'Unknown',
                'item_type': 'node',
                **props
            }
        except Exception as e:
            print(f"⚠️ 解析结果失败: {e}")
            return None
    
    def _llm_rank_results(self, query: str, items: List[Dict], max_results: int) -> List[Dict]:
        """
        使用 LLM 对结果进行语义相关性排序
        
        重点：理解查询意图，评估语义相关性，而不是简单的关键词匹配
        
        Args:
            query: 用户查询
            items: 候选结果列表
            max_results: 最大返回数量
        
        Returns:
            排序后的结果列表 [{'item': ..., 'score': ...}, ...]
        """
        try:
            from backend.llm.llm_service import get_llm_service
            llm_service = get_llm_service()
            
            if not llm_service or not llm_service.enabled:
                # 降级：返回所有结果，分数为 0.5
                return [{'item': item, 'score': 0.5} for item in items[:max_results]]
            
            # 限制候选数量（避免 token 过多和处理时间过长）
            # 减少到20个以加快LLM处理速度
            candidates = items[:min(20, len(items))]  # 最多20个候选
            
            # 构建候选列表描述（包含更多上下文信息）
            candidates_desc = []
            for i, item in enumerate(candidates):
                node_label = item.get('node_label', 'Unknown')
                name = item.get('name', '')
                item_type = item.get('type', '')
                category = item.get('category', '')
                desc = item.get('description', '')
                
                # 尝试解析attributes字段
                attrs_str = ""
                if 'attributes' in item:
                    try:
                        attrs = json.loads(item['attributes']) if isinstance(item['attributes'], str) else item['attributes']
                        # 提取关键属性
                        key_attrs = []
                        for key in ['tier', 'level', 'major', 'location', 'company', 'salary']:
                            if key in attrs:
                                key_attrs.append(f"{key}={attrs[key]}")
                        if key_attrs:
                            attrs_str = f" [{', '.join(key_attrs)}]"
                    except:
                        pass
                
                candidates_desc.append(
                    f"{i}. [{node_label}/{item_type}] {name} - {desc[:80]}{attrs_str}"
                )
            
            candidates_text = "\n".join(candidates_desc[:30])  # 最多30个
            
            # 构建提示词
            system_prompt = """你是一个语义检索专家。根据用户查询的意图，评估候选结果的语义相关性。

**重要原则**：
1. 理解查询的核心意图，而不是简单匹配关键词
2. 评估候选结果是否能帮助回答用户的问题或需求
3. 考虑上下文相关性，即使没有直接关键词匹配
4. 优先返回对用户有实际价值的信息

**示例**：
- 查询"我是985大三学生" → 985学校高度相关（即使没有"大三"信息）
- 查询"想找Python工作" → Python相关职位高度相关，其他技术职位中等相关
- 查询"我的朋友" → Person类型且category=friends高度相关

返回 JSON 格式：
{
  "query_intent": "查询意图分析",
  "rankings": [
    {"index": 0, "score": 0.95, "reason": "985学校，与用户教育背景高度相关"},
    {"index": 2, "score": 0.85, "reason": "相关专业，可能对决策有帮助"},
    ...
  ]
}

评分标准：
- 0.9-1.0: 高度相关，直接匹配查询意图
- 0.7-0.9: 相关，提供有价值的上下文信息
- 0.5-0.7: 中等相关，可能有帮助
- 0.3-0.5: 弱相关
- 0.0-0.3: 不相关

只返回相关性 >= 0.5 的结果，最多返回 {max_results} 个。"""
            
            user_prompt = f"""用户查询：{query}

候选结果：
{candidates_text}

请分析查询意图，并对这些结果进行语义相关性评分和排序。"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = llm_service.chat(messages, temperature=0.3, response_format="json_object", model="qwen-turbo")
            result = json.loads(response)
            
            query_intent = result.get('query_intent', '')
            if query_intent:
                print(f"[Neo4jRetriever] 查询意图: {query_intent}")
            
            # 解析排序结果
            rankings = result.get('rankings', [])
            ranked_items = []
            
            for rank in rankings[:max_results]:
                idx = rank.get('index')
                score = rank.get('score', 0.5)
                reason = rank.get('reason', '')
                
                if idx is not None and 0 <= idx < len(candidates):
                    ranked_items.append({
                        'item': candidates[idx],
                        'score': score,
                        'reason': reason
                    })
            
            return ranked_items
            
        except Exception as e:
            print(f"⚠️ [Neo4jRetriever] LLM 排序失败: {e}")
            # 降级：返回所有结果，分数为 0.5
            return [{'item': item, 'score': 0.5} for item in items[:max_results]]
    
    async def _llm_rank_results_async(self, query: str, items: List[Dict], max_results: int) -> List[Dict]:
        """
        使用 LLM 对结果进行语义相关性排序（异步版本，支持超时控制）
        """
        import asyncio
        
        # 在线程池中运行同步方法
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._llm_rank_results, query, items, max_results)
    
    def _traditional_retrieve(self, query: str, max_results: int, filters: Dict) -> List[RetrievalResult]:
        """传统检索方法（降级方案）"""
        results = []
        
        try:
            with self.driver.session() as session:
                # 查询所有与用户相关的节点
                nodes_query = """
                MATCH (n)
                WHERE n.user_id = $user_id
                RETURN 
                    elementId(n) as id,
                    labels(n) as labels,
                    properties(n) as props
                LIMIT 1000
                """
                
                node_result = session.run(nodes_query, user_id=self.user_id)
                all_nodes = []
                
                for record in node_result:
                    node_labels = record['labels']
                    props = dict(record['props'])
                    
                    node_data = {
                        'id': record['id'],
                        'node_label': node_labels[0] if node_labels else 'Unknown',
                        'item_type': 'node',
                        **props
                    }
                    all_nodes.append(node_data)
                
                # 查询所有与用户相关的关系
                relations_query = """
                MATCH (n)-[r]->(m)
                WHERE n.user_id = $user_id OR m.user_id = $user_id
                RETURN 
                    elementId(r) as id,
                    type(r) as rel_type,
                    properties(r) as props,
                    labels(n) as source_labels,
                    properties(n) as source_props,
                    labels(m) as target_labels,
                    properties(m) as target_props
                LIMIT 500
                """
                
                rel_result = session.run(relations_query, user_id=self.user_id)
                all_relations = []
                
                for record in rel_result:
                    rel_props = dict(record['props'])
                    source_props = dict(record['source_props'])
                    target_props = dict(record['target_props'])
                    
                    source_name = source_props.get('name', 'Unknown')
                    target_name = target_props.get('name', 'Unknown')
                    rel_type = record['rel_type']
                    
                    rel_data = {
                        'id': record['id'],
                        'item_type': 'relationship',
                        'rel_type': rel_type,
                        'source_label': record['source_labels'][0] if record['source_labels'] else 'Unknown',
                        'target_label': record['target_labels'][0] if record['target_labels'] else 'Unknown',
                        'source_name': source_name,
                        'target_name': target_name,
                        'name': f"{source_name}-{rel_type}->{target_name}",
                        **rel_props
                    }
                    all_relations.append(rel_data)
            
            all_items = all_nodes + all_relations
            print(f"[Neo4jRetriever] 传统检索找到 {len(all_nodes)} 个节点, {len(all_relations)} 个关系")
            
            # 关键词匹配评分
            scored_results = []
            keywords = self._extract_keywords(query)
            
            for item in all_items:
                if item['item_type'] == 'node':
                    score = self._calculate_relevance_score(item, query, keywords)
                else:
                    score = self._calculate_relationship_relevance_score(item, query, keywords)
                
                if score > 0.1:
                    scored_results.append({
                        'item': item,
                        'score': score
                    })
            
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            print(f"[Neo4jRetriever] 传统检索到 {len(scored_results)} 个相关结果")
            
            # 转换为 RetrievalResult
            for item_data in scored_results[:max_results]:
                item = item_data['item']
                score = item_data['score']
                
                if not self._apply_filters(item, filters):
                    continue
                
                results.append(RetrievalResult(
                    id=item.get('id', ''),
                    content=self._format_content(item),
                    score=score,
                    source='neo4j',
                    node_type=item.get('node_label', item.get('rel_type', 'unknown')),
                    category=item.get('category', 'unknown'),
                    metadata=item,
                    confidence=score,
                    timestamp=self._parse_timestamp(item.get('extracted_at')),
                    relations=[]
                ))
            
            return results
            
        except Exception as e:
            print(f"❌ [Neo4jRetriever] 传统检索失败: {e}")
            return []
            
        except Exception as e:
            print(f"❌ [Neo4jRetriever] 检索失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        import re
        
        # 移除标点
        query = re.sub(r'[，。！？、；：""''（）【】《》]', ' ', query)
        
        # 停用词
        stop_words = {
            '我', '你', '他', '她', '它', '的', '了', '是', '在', '和', '与',
            '还是', '应该', '要不要', '怎么', '什么', '哪个', '这个', '那个'
        }
        
        # 提取词语
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', query)
        keywords = [w for w in words if w not in stop_words]
        
        # 如果没有提取到，使用原始查询
        if not keywords:
            keywords = [query.strip()]
        
        return keywords[:5]
    
    def _calculate_relevance_score(
        self, 
        node: Dict[str, Any], 
        query: str, 
        keywords: List[str]
    ) -> float:
        """
        计算节点与查询的相关性分数
        
        支持6种节点类型：User, Entity, Event, Concept, Pattern, Source
        
        评分维度：
        1. 名称匹配（权重 0.4）
        2. 类型匹配（权重 0.2）
        3. 属性匹配（权重 0.3）
        4. 时间新鲜度（权重 0.1）
        """
        score = 0.0
        
        # 获取节点信息
        name = str(node.get('name', '')).lower()
        node_type = str(node.get('type', '')).lower()  # Entity/Concept的type属性
        category = str(node.get('category', '')).lower()
        description = str(node.get('description', '')).lower()
        
        # 获取节点标签（User/Entity/Event/Concept/Pattern/Source）
        node_label = node.get('node_label', 'Unknown')
        
        # 合并所有文本用于搜索
        all_text = f"{name} {node_type} {category} {description}"
        
        # 1. 名称匹配（权重 0.4）
        name_score = 0.0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in name:
                name_score += 1.0
            elif keyword_lower in all_text:
                name_score += 0.5
        
        if keywords:
            name_score = min(name_score / len(keywords), 1.0) * 0.4
        
        # 2. 类型匹配（权重 0.2）
        type_score = 0.0
        query_lower = query.lower()
        
        # 根据节点标签和查询内容匹配
        type_keywords = {
            'User': ['我', '用户', '个人', '自己'],
            'Entity': {
                'Person': ['人', '朋友', '同事', '家人', '关系', '认识'],
                'Job': ['工作', '职位', '岗位', '职业', '公司', '招聘'],
                'School': ['学校', '大学', '教育', '升学', '专业', '院校'],
                'Organization': ['组织', '机构', '公司', '团队', '企业'],
                'Location': ['地点', '位置', '城市', '地方']
            },
            'Event': ['事件', '活动', '会议', '面试', '聚会', '发生'],
            'Concept': {
                'Skill': ['技能', '能力', '掌握', '学习', '擅长'],
                'Interest': ['兴趣', '爱好', '喜欢', '关注'],
                'Value': ['价值观', '理念', '信念', '原则'],
                'Goal': ['目标', '计划', '打算', '想要']
            },
            'Pattern': ['模式', '习惯', '偏好', '倾向', '规律'],
            'Source': ['来源', '对话', '照片', '记录']
        }
        
        # 匹配节点标签
        if node_label == 'User':
            for word in type_keywords.get('User', []):
                if word in query_lower:
                    type_score = 0.2
                    break
        
        elif node_label == 'Entity':
            # Entity需要进一步根据type属性匹配
            entity_keywords = type_keywords.get('Entity', {})
            
            for etype, words in entity_keywords.items():
                if etype.lower() in node_type:
                    for word in words:
                        if word in query_lower:
                            type_score = 0.2
                            break
        
        elif node_label == 'Event':
            for word in type_keywords.get('Event', []):
                if word in query_lower:
                    type_score = 0.2
                    break
        
        elif node_label == 'Concept':
            # Concept需要进一步根据type属性匹配
            concept_keywords = type_keywords.get('Concept', {})
            
            for ctype, words in concept_keywords.items():
                if ctype.lower() in node_type:
                    for word in words:
                        if word in query_lower:
                            type_score = 0.2
                            break
        
        elif node_label == 'Pattern':
            for word in type_keywords.get('Pattern', []):
                if word in query_lower:
                    type_score = 0.2
                    break
        
        # 3. 属性匹配（权重 0.3）
        attr_score = 0.0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # 检查所有属性
            for key, value in node.items():
                if key in ['id', 'user_id', 'created_at', 'updated_at', 'node_label', 'item_type']:
                    continue
                if isinstance(value, str) and keyword_lower in str(value).lower():
                    attr_score += 0.1
                elif isinstance(value, dict):
                    # 检查嵌套属性（如Entity的attributes字段）
                    for k, v in value.items():
                        if isinstance(v, str) and keyword_lower in str(v).lower():
                            attr_score += 0.05
        
        attr_score = min(attr_score, 0.3)
        
        # 4. 时间新鲜度（权重 0.1）
        time_score = 0.1  # 默认给一个基础分
        
        # 总分
        score = name_score + type_score + attr_score + time_score
        
        return min(score, 1.0)
    
    def _calculate_relationship_relevance_score(
        self,
        rel: Dict[str, Any],
        query: str,
        keywords: List[str]
    ) -> float:
        """
        计算关系与查询的相关性分数
        
        支持4类关系：
        1. 用户关系：HAS_PROFILE, KNOWS, INTERESTED_IN, APPLIED_TO, PARTICIPATED_IN
        2. 溯源关系：EXTRACTED_FROM, MENTIONED_IN, CREATED_BY
        3. 实体关系：RELATED_TO, PART_OF, INVOLVES, REQUIRES, LOCATED_IN, HAPPENED_AT
        4. 模式关系：EXHIBITS, SUPPORTS, INFLUENCES
        """
        score = 0.0
        
        # 获取关系信息
        rel_type = rel.get('rel_type', '').lower()
        source_name = str(rel.get('source_name', '')).lower()
        target_name = str(rel.get('target_name', '')).lower()
        
        # 合并文本
        all_text = f"{source_name} {rel_type} {target_name}"
        
        # 1. 关键词匹配（权重 0.5）
        keyword_score = 0.0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in all_text:
                keyword_score += 1.0
        
        if keywords:
            keyword_score = min(keyword_score / len(keywords), 1.0) * 0.5
        
        # 2. 关系类型匹配（权重 0.3）
        rel_type_score = 0.0
        query_lower = query.lower()
        
        # 关系类型关键词
        rel_keywords = {
            'knows': ['认识', '朋友', '同事', '关系'],
            'has_profile': ['拥有', '技能', '属性'],
            'interested_in': ['感兴趣', '关注', '喜欢'],
            'applied_to': ['申请', '投递', '应聘'],
            'participated_in': ['参与', '参加', '出席'],
            'related_to': ['相关', '关联', '联系'],
            'part_of': ['属于', '部分', '成员'],
            'involves': ['涉及', '包含', '参与'],
            'requires': ['需要', '要求', '必须'],
            'located_in': ['位于', '在', '地点'],
            'happened_at': ['发生在', '举行在'],
            'exhibits': ['展现', '表现', '显示'],
            'supports': ['支持', '证明', '佐证'],
            'influences': ['影响', '作用于']
        }
        
        for rel_key, words in rel_keywords.items():
            if rel_key in rel_type:
                for word in words:
                    if word in query_lower:
                        rel_type_score = 0.3
                        break
        
        # 3. 属性匹配（权重 0.2）
        attr_score = 0.0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for key, value in rel.items():
                if key in ['id', 'item_type', 'rel_type', 'source_label', 'target_label']:
                    continue
                if isinstance(value, str) and keyword_lower in str(value).lower():
                    attr_score += 0.1
        
        attr_score = min(attr_score, 0.2)
        
        # 总分
        score = keyword_score + rel_type_score + attr_score
        
        return min(score, 1.0)
    
    def _get_entities_by_type(self, entity_type: str, limit: int = 50) -> List[Dict]:
        """
        根据 Entity 的 type 属性获取节点
        
        根据 NEO4J_SCHEMA.md:
        - Entity 节点：统一的实体节点，通过 type 属性区分
        - type 可以是: Person, Job, School, Organization, Location 等
        - category 是更细粒度的分类（friend/colleague/family/position/university等）
        
        Args:
            entity_type: Entity 的 type 属性值（Person/Job/School）
            limit: 返回数量限制
            
        Returns:
            节点列表，格式为 [{'information': {...}}, ...]
        """
        try:
            # 导出所有节点
            export = self.info_kg.export()
            all_nodes = export.get('information', [])
            
            # 过滤指定 type 的 Entity 节点
            filtered_nodes = []
            for node in all_nodes:
                # 检查是否是 Entity 节点且 type 匹配
                if node.get('type') == entity_type:
                    filtered_nodes.append({'information': node})
            
            print(f"[Neo4jRetriever] 找到 {len(filtered_nodes)} 个 Entity(type='{entity_type}') 节点")
            return filtered_nodes[:limit]
            
        except Exception as e:
            print(f"❌ [Neo4jRetriever] 获取 Entity 节点失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _apply_filters(self, node_data: Dict, filters: Dict) -> bool:
        """应用过滤条件"""
        # 领域过滤
        if filters.get('domain_filter'):
            domain_filter = filters['domain_filter']
            node_type = node_data.get('type', '')
            node_category = node_data.get('category', '')
            
            # 根据领域映射到节点类型
            domain_type_mapping = {
                'relationship': 'Person',
                'career': 'Job',
                'education': 'School'
            }
            
            # 检查节点类型是否匹配领域
            expected_type = domain_type_mapping.get(domain_filter)
            if expected_type and node_type != expected_type:
                return False
        
        # 置信度过滤
        if filters.get('min_confidence'):
            if node_data.get('confidence', 0) < filters['min_confidence']:
                return False
        
        # 时间过滤
        if filters.get('time_range'):
            node_time = self._parse_timestamp(node_data.get('extracted_at'))
            if node_time:
                start, end = filters['time_range']
                if not (start <= node_time <= end):
                    return False
        
        return True
    
    def _calculate_score(
        self,
        node_data: Dict,
        query: str,
        keywords: List[str]
    ) -> float:
        """计算节点分数"""
        score = 0.0
        
        # 1. 基础分数：置信度
        score += node_data.get('confidence', 0.5) * 0.3
        
        # 2. 关键词匹配分数
        node_name = node_data.get('name', '')
        node_desc = node_data.get('description', '')
        search_text = f"{node_name} {node_desc}".lower()
        
        keyword_matches = sum(1 for kw in keywords if kw.lower() in search_text)
        score += (keyword_matches / len(keywords)) * 0.4
        
        # 3. 重要性分数
        importance = node_data.get('importance', 0.5)
        score += importance * 0.2
        
        # 4. 时间衰减
        timestamp = self._parse_timestamp(node_data.get('extracted_at'))
        if timestamp:
            days_old = (datetime.now() - timestamp).days
            time_factor = max(0, 1 - days_old * 0.01)  # 每天衰减1%
            score *= time_factor
        
        # 5. 类型加权
        node_type = node_data.get('type', '')
        type_weights = {
            'entity': 1.0,
            'event': 0.9,
            'concept': 0.8,
            'pattern': 0.7
        }
        score *= type_weights.get(node_type, 0.5)
        
        return min(score, 1.0)
    
    def _get_relations(self, node_name: str, max_depth: int) -> List[Dict]:
        """获取节点关系"""
        try:
            related = self.info_kg.get_related_information(
                info_name=node_name,
                max_depth=max_depth
            )
            
            relations = []
            for rel in related[:10]:  # 最多10个关系
                rel_info = rel.get('information', {})
                if rel_info:
                    relations.append({
                        'target': rel_info.get('name', ''),
                        'type': rel_info.get('type', 'unknown'),
                        'path': ' -> '.join(rel.get('path', []))
                    })
            
            return relations
        except:
            return []
    
    def _format_content(self, item: Dict) -> str:
        """格式化节点或关系内容"""
        item_type = item.get('item_type', 'node')
        
        if item_type == 'relationship':
            # 格式化关系
            source_name = item.get('source_name', 'Unknown')
            target_name = item.get('target_name', 'Unknown')
            rel_type = item.get('rel_type', 'RELATED')
            
            # 将关系类型转换为中文描述
            rel_type_cn = {
                'HAS_PROFILE': '拥有',
                'KNOWS': '认识',
                'INTERESTED_IN': '感兴趣',
                'APPLIED_TO': '申请了',
                'PARTICIPATED_IN': '参与了',
                'EXTRACTED_FROM': '提取自',
                'MENTIONED_IN': '提及于',
                'CREATED_BY': '创建于',
                'RELATED_TO': '相关于',
                'PART_OF': '属于',
                'INVOLVES': '涉及',
                'REQUIRES': '需要',
                'LOCATED_IN': '位于',
                'HAPPENED_AT': '发生在',
                'EXHIBITS': '展现',
                'SUPPORTS': '支持',
                'INFLUENCES': '影响'
            }.get(rel_type, rel_type)
            
            return f"【关系】{source_name} {rel_type_cn} {target_name}"
        
        else:
            # 格式化节点
            node_label = item.get('node_label', 'Unknown')
            name = item.get('name', '')
            node_type = item.get('type', '')  # Entity/Concept的type属性
            desc = item.get('description', '')
            
            # 根据节点标签格式化
            if node_label == 'User':
                content = f"【用户】{name}"
            elif node_label == 'Entity':
                content = f"【{node_type or '实体'}】{name}"
            elif node_label == 'Event':
                content = f"【事件】{name}"
            elif node_label == 'Concept':
                content = f"【{node_type or '概念'}】{name}"
            elif node_label == 'Pattern':
                content = f"【模式】{name}"
            elif node_label == 'Source':
                content = f"【来源】{item.get('type', '未知')}"
            else:
                content = f"【{node_label}】{name}"
            
            if desc:
                content += f": {desc}"
            
            return content
    
    def _parse_timestamp(self, timestamp_str: Any) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp_str:
            return None
        
        try:
            if isinstance(timestamp_str, datetime):
                return timestamp_str
            elif isinstance(timestamp_str, str):
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif isinstance(timestamp_str, (int, float)):
                return datetime.fromtimestamp(timestamp_str)
        except:
            pass
        
        return None
    
    def _deduplicate(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """去重"""
        seen = set()
        unique_results = []
        
        for result in results:
            if result.id not in seen:
                seen.add(result.id)
                unique_results.append(result)
        
        return unique_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "user_id": self.user_id,
            "connected": self.driver is not None
        }
    
    def __del__(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.close()
            except:
                pass



class RAGRetriever(BaseRetriever):
    """RAG向量检索器 - 使用 FAISS + 并发优化"""
    
    def __init__(self, user_id: str, config: Dict[str, Any] = None):
        super().__init__("rag", config)
        self.user_id = user_id
        self.rag_system = None
        # 暂时禁用并发优化器，因为GPU编码慢导致队列堵塞
        self.use_concurrent_optimizer = False
        self._init_connection()
    
    def _init_connection(self):
        """初始化RAG连接 - 使用统一的 RAG 管理器（FAISS）"""
        try:
            from backend.learning.rag_manager import RAGManager
            
            # 使用统一的 RAG 管理器获取实例（使用CPU模式）
            self.rag_system = RAGManager.get_system(self.user_id, use_gpu=False)
            print(f"✅ [RAGRetriever] 连接成功 (FAISS): user={self.user_id}")
            
            if self.use_concurrent_optimizer:
                print(f"   并发优化: 已启用")
        except Exception as e:
            print(f"❌ [RAGRetriever] 连接失败: {e}")
            import traceback
            traceback.print_exc()
            self.enabled = False
    
    def retrieve(
        self,
        query: str,
        max_results: int = 50,  # 增加默认值
        filters: Dict[str, Any] = None
    ) -> List[RetrievalResult]:
        """
        从RAG检索 - 使用 ProductionRAGSystem (FAISS)
        
        支持并发优化：
        - 如果启用并发优化，使用全局优化器控制并发
        - 否则直接调用RAG系统
        """
        if not self.rag_system or not self.enabled:
            return []
        
        # 快速检查：如果FAISS索引为空，直接返回空结果
        if not self.rag_system.memory_ids:
            return []
        
        filters = filters or {}
        
        # 如果启用并发优化，使用优化器
        if self.use_concurrent_optimizer:
            try:
                import asyncio
                from backend.learning.concurrent_retrieval_optimizer import get_global_optimizer, RequestPriority
                
                optimizer = get_global_optimizer(
                    max_concurrent=8,  # GPU模式：提高到8个并发
                    cache_size=1000,   # 增加缓存
                    cache_ttl=300,
                    default_timeout=10.0
                )
                
                # 设置检索器（如果还没设置）
                if optimizer.vector_retriever is None:
                    optimizer.set_retrievers(
                        vector_retriever=self,
                        graph_retriever=None  # 图检索不需要优化
                    )
                
                # 使用优化器执行检索
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    results = loop.run_until_complete(
                        optimizer.retrieve(
                            query=query,
                            user_id=self.user_id,
                            max_results=max_results,
                            filters=filters,
                            priority=RequestPriority.NORMAL,
                            timeout=10.0,
                            use_cache=True
                        )
                    )
                    return results
                finally:
                    loop.close()
                    
            except Exception as e:
                print(f"⚠️ [RAGRetriever] 并发优化失败，降级到直接检索: {e}")
                # 降级到直接检索
                return self._direct_retrieve(query, max_results, filters)
        else:
            # 直接检索
            return self._direct_retrieve(query, max_results, filters)
    
    def _direct_retrieve(
        self,
        query: str,
        max_results: int = 20,
        filters: Dict[str, Any] = None
    ) -> List[RetrievalResult]:
        """直接检索（不使用并发优化）"""
        filters = filters or {}
        results = []
        
        try:
            from backend.learning.production_rag_system import MemoryType
            
            # 1. 确定检索的记忆类型
            memory_types = self._determine_memory_types(filters)
            
            # 2. 查询扩展（如果启用）
            queries = [query]
            if filters.get('query_expansion', False):
                queries.extend(self._expand_query(query))
            
            # 3. 执行检索 - 使用 ProductionRAGSystem API
            all_memories = []
            for q in queries:
                memories = self.rag_system.search(
                    query=q,
                    memory_types=memory_types,
                    top_k=max_results,
                    min_importance=filters.get('min_confidence', 0.0)
                )
                all_memories.extend(memories)
            
            # 4. 去重并转换为RetrievalResult
            seen_ids = set()
            for mem in all_memories:
                if mem.id in seen_ids:
                    continue
                seen_ids.add(mem.id)
                
                # 应用过滤器
                if not self._apply_filters(mem, filters):
                    continue
                
                # 计算分数
                score = self._calculate_score(mem, query, filters)
                
                results.append(RetrievalResult(
                    id=mem.id,
                    content=mem.content,
                    score=score,
                    source='vector',
                    node_type=mem.memory_type.value,
                    category=mem.metadata.get('category', 'unknown'),
                    metadata=mem.metadata,
                    confidence=mem.importance,
                    timestamp=mem.timestamp,
                    relations=[]
                ))
            
            # 排序
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results[:max_results]
            
        except Exception as e:
            print(f"❌ [RAGRetriever] 检索失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _determine_memory_types(self, filters: Dict) -> List:
        """确定要检索的记忆类型 - 使用 ProductionRAGSystem.MemoryType"""
        from backend.learning.production_rag_system import MemoryType
        
        # 如果指定了领域，选择相关的记忆类型
        domain = filters.get('domain_filter')
        
        if domain == 'career':
            return [MemoryType.KNOWLEDGE, MemoryType.EXPERIENCE, MemoryType.INSIGHT]
        elif domain == 'education':
            return [MemoryType.KNOWLEDGE, MemoryType.EXPERIENCE]
        elif domain == 'relationship':
            return [MemoryType.CONVERSATION, MemoryType.EXPERIENCE]
        else:
            # 默认检索所有类型
            return [MemoryType.KNOWLEDGE, MemoryType.EXPERIENCE, MemoryType.INSIGHT, MemoryType.CONVERSATION]
    
    def _expand_query(self, query: str) -> List[str]:
        """查询扩展（生成同义查询）"""
        # 简单实现：提取关键词并生成变体
        import re
        
        expanded = []
        
        # 提取关键词
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', query)
        
        # 同义词映射（可以扩展）
        synonyms = {
            '工作': ['职业', '岗位', '就业'],
            '学习': ['学业', '教育', '进修'],
            '朋友': ['好友', '同学', '伙伴'],
            '公司': ['企业', '单位', '组织'],
            '技能': ['能力', '专长', '特长']
        }
        
        for word in words:
            if word in synonyms:
                for syn in synonyms[word]:
                    expanded.append(query.replace(word, syn))
        
        return expanded[:3]  # 最多3个扩展查询
    
    def _apply_filters(self, memory, filters: Dict) -> bool:
        """应用过滤条件"""
        # 领域过滤
        if filters.get('domain_filter'):
            mem_domain = memory.metadata.get('domain', '')
            if filters['domain_filter'] not in mem_domain:
                return False
        
        # 置信度过滤
        if filters.get('min_confidence'):
            if memory.importance < filters['min_confidence']:
                return False
        
        # 时间过滤
        if filters.get('time_range'):
            if memory.timestamp:
                start, end = filters['time_range']
                if not (start <= memory.timestamp <= end):
                    return False
        
        return True
    
    def _calculate_score(self, memory, query: str, filters: Dict) -> float:
        """计算记忆分数"""
        # 基础分数：重要性
        score = memory.importance * 0.5
        
        # 相似度分数（由FAISS计算，已经按相似度排序）
        # 这里假设FAISS已经按相似度排序，越靠前分数越高
        score += 0.5
        
        # 时间衰减（如果启用）
        if filters.get('time_decay_enabled', True) and memory.timestamp:
            days_old = (datetime.now() - memory.timestamp).days
            decay_factor = filters.get('time_decay_factor', 0.01)
            time_factor = max(0, 1 - days_old * decay_factor)
            score *= time_factor
        
        return min(score, 1.0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "name": self.name,
            "enabled": self.enabled,
            "user_id": self.user_id,
            "connected": self.rag_system is not None,
            "backend": "ProductionRAGSystem (FAISS)"
        }
        
        if self.rag_system:
            try:
                stats["rag_stats"] = self.rag_system.get_statistics()
            except:
                pass
        
        return stats



# ==================== 混合融合引擎 ====================

class HybridFusion:
    """混合融合引擎 - 合并多个检索器的结果"""
    
    @staticmethod
    def fuse(
        graph_results: List[RetrievalResult],
        vector_results: List[RetrievalResult],
        method: FusionMethod,
        config: RetrievalConfig
    ) -> List[RetrievalResult]:
        """
        融合检索结果
        
        Args:
            graph_results: 图检索结果
            vector_results: 向量检索结果
            method: 融合方法
            config: 检索配置
        
        Returns:
            融合后的结果列表
        """
        if method == FusionMethod.WEIGHTED_SUM:
            return HybridFusion._weighted_sum_fusion(
                graph_results, vector_results, config
            )
        elif method == FusionMethod.RRF:
            return HybridFusion._rrf_fusion(
                graph_results, vector_results, config
            )
        elif method == FusionMethod.BORDA_COUNT:
            return HybridFusion._borda_count_fusion(
                graph_results, vector_results, config
            )
        elif method == FusionMethod.LEARNED:
            return HybridFusion._learned_fusion(
                graph_results, vector_results, config
            )
        else:
            # 默认使用RRF
            return HybridFusion._rrf_fusion(
                graph_results, vector_results, config
            )
    
    @staticmethod
    def _weighted_sum_fusion(
        graph_results: List[RetrievalResult],
        vector_results: List[RetrievalResult],
        config: RetrievalConfig
    ) -> List[RetrievalResult]:
        """
        加权求和融合 - 改进版
        
        改进点：
        1. 先对每个检索器的分数进行归一化（Min-Max Normalization）
        2. 然后再进行加权求和
        3. 这样可以避免不同检索器分数量纲不同的问题
        
        公式: score = w_graph * norm(score_graph) + w_vector * norm(score_vector)
        """
        # 创建ID到结果的映射
        result_map: Dict[str, Dict[str, Any]] = {}
        
        # 1. 归一化图检索分数
        if graph_results:
            graph_scores = [r.score for r in graph_results]
            min_graph = min(graph_scores)
            max_graph = max(graph_scores)
            score_range_graph = max_graph - min_graph if max_graph > min_graph else 1.0
            
            for result in graph_results:
                # Min-Max 归一化到 [0, 1]
                normalized_score = (result.score - min_graph) / score_range_graph
                weighted_score = normalized_score * config.graph_weight
                
                result_map[result.id] = {
                    'result': result,
                    'score': weighted_score,
                    'graph_score': result.score,
                    'graph_normalized': normalized_score,
                    'vector_score': None,
                    'vector_normalized': None
                }
                result.source = 'graph'
        
        # 2. 归一化向量检索分数
        if vector_results:
            vector_scores = [r.score for r in vector_results]
            min_vector = min(vector_scores)
            max_vector = max(vector_scores)
            score_range_vector = max_vector - min_vector if max_vector > min_vector else 1.0
            
            for result in vector_results:
                # Min-Max 归一化到 [0, 1]
                normalized_score = (result.score - min_vector) / score_range_vector
                weighted_score = normalized_score * config.vector_weight
                
                if result.id in result_map:
                    # 已存在，累加分数
                    result_map[result.id]['score'] += weighted_score
                    result_map[result.id]['vector_score'] = result.score
                    result_map[result.id]['vector_normalized'] = normalized_score
                    result_map[result.id]['result'].source = 'hybrid'
                else:
                    # 新结果
                    result_map[result.id] = {
                        'result': result,
                        'score': weighted_score,
                        'graph_score': None,
                        'graph_normalized': None,
                        'vector_score': result.score,
                        'vector_normalized': normalized_score
                    }
                    result.source = 'vector'
        
        # 3. 更新分数并排序
        fused_results = []
        for item in result_map.values():
            result = item['result']
            result.score = item['score']
            
            # 保存融合信息
            result.metadata['fusion_info'] = {
                'method': 'WeightedSum',
                'graph_original_score': item['graph_score'],
                'graph_normalized_score': item['graph_normalized'],
                'vector_original_score': item['vector_score'],
                'vector_normalized_score': item['vector_normalized'],
                'final_score': item['score'],
                'weights': {
                    'graph': config.graph_weight,
                    'vector': config.vector_weight
                }
            }
            fused_results.append(result)
        
        fused_results.sort(key=lambda x: x.score, reverse=True)
        
        return fused_results[:config.max_results]
    
    @staticmethod
    def _rrf_fusion(
        graph_results: List[RetrievalResult],
        vector_results: List[RetrievalResult],
        config: RetrievalConfig,
        k: int = 60
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion (RRF) - 改进版
        
        标准 RRF 公式: RRF(d) = Σ 1/(k + rank(d))
        
        改进点：
        1. 标准 RRF 不使用原始分数，只使用排名
        2. 对于同时出现在两个列表中的结果，RRF 分数会更高
        3. k 值控制排名的影响程度（k 越大，排名差异影响越小）
        
        优势：
        - 不依赖于原始分数的量纲
        - 自动平衡不同检索器的贡献
        - 对排名靠前的结果给予更高权重
        """
        result_map: Dict[str, Dict[str, Any]] = {}
        
        # 处理图检索结果
        for rank, result in enumerate(graph_results, 1):
            # 标准 RRF：不乘以权重，让算法自然平衡
            rrf_score = 1.0 / (k + rank)
            result_map[result.id] = {
                'result': result,
                'rrf_score': rrf_score,
                'graph_rank': rank,
                'vector_rank': None,
                'graph_original_score': result.score
            }
        
        # 处理向量检索结果
        for rank, result in enumerate(vector_results, 1):
            rrf_score = 1.0 / (k + rank)
            
            if result.id in result_map:
                # 已存在，累加 RRF 分数（这是 RRF 的核心优势）
                result_map[result.id]['rrf_score'] += rrf_score
                result_map[result.id]['vector_rank'] = rank
                result_map[result.id]['vector_original_score'] = result.score
                result_map[result.id]['result'].source = 'hybrid'
            else:
                # 新结果
                result_map[result.id] = {
                    'result': result,
                    'rrf_score': rrf_score,
                    'graph_rank': None,
                    'vector_rank': rank,
                    'vector_original_score': result.score
                }
                result.source = 'vector'
        
        # 更新分数并排序
        fused_results = []
        for item in result_map.values():
            result = item['result']
            result.score = item['rrf_score']
            
            # 保存融合信息用于调试
            result.metadata['fusion_info'] = {
                'method': 'RRF',
                'graph_rank': item['graph_rank'],
                'vector_rank': item['vector_rank'],
                'rrf_score': item['rrf_score'],
                'graph_original_score': item.get('graph_original_score'),
                'vector_original_score': item.get('vector_original_score'),
                'appears_in_both': item['graph_rank'] is not None and item['vector_rank'] is not None
            }
            fused_results.append(result)
        
        fused_results.sort(key=lambda x: x.score, reverse=True)
        
        return fused_results[:config.max_results]
    
    @staticmethod
    def _borda_count_fusion(
        graph_results: List[RetrievalResult],
        vector_results: List[RetrievalResult],
        config: RetrievalConfig
    ) -> List[RetrievalResult]:
        """Borda计数融合"""
        result_map: Dict[str, Dict[str, Any]] = {}
        
        n_graph = len(graph_results)
        n_vector = len(vector_results)
        
        # 处理图检索结果（倒序计分）
        for rank, result in enumerate(graph_results, 1):
            borda_score = (n_graph - rank) * config.graph_weight
            result_map[result.id] = {
                'result': result,
                'borda_score': borda_score,
                'graph_rank': rank,
                'vector_rank': None
            }
        
        # 处理向量检索结果
        for rank, result in enumerate(vector_results, 1):
            borda_score = (n_vector - rank) * config.vector_weight
            
            if result.id in result_map:
                result_map[result.id]['borda_score'] += borda_score
                result_map[result.id]['vector_rank'] = rank
                result_map[result.id]['result'].source = 'hybrid'
            else:
                result_map[result.id] = {
                    'result': result,
                    'borda_score': borda_score,
                    'graph_rank': None,
                    'vector_rank': rank
                }
                result.source = 'vector'
        
        # 更新分数并排序
        fused_results = []
        for item in result_map.values():
            result = item['result']
            result.score = item['borda_score'] / max(n_graph, n_vector)  # 归一化
            result.metadata['fusion_info'] = {
                'graph_rank': item['graph_rank'],
                'vector_rank': item['vector_rank'],
                'borda_score': item['borda_score']
            }
            fused_results.append(result)
        
        fused_results.sort(key=lambda x: x.score, reverse=True)
        
        return fused_results[:config.max_results]
    
    @staticmethod
    def _learned_fusion(
        graph_results: List[RetrievalResult],
        vector_results: List[RetrievalResult],
        config: RetrievalConfig
    ) -> List[RetrievalResult]:
        """
        学习融合（基于历史反馈）
        
        TODO: 实现基于用户反馈的学习融合算法
        目前降级为RRF融合
        """
        print("⚠️ [HybridFusion] 学习融合尚未实现，降级为RRF融合")
        return HybridFusion._rrf_fusion(graph_results, vector_results, config)



# ==================== 统一检索接口 ====================

class UnifiedHybridRetrieval:
    """
    统一混合检索系统
    
    使用示例：
    ```python
    # 1. 创建检索器
    retriever = UnifiedHybridRetrieval(user_id="user_123")
    
    # 2. 简单检索
    context = retriever.retrieve("我想了解职业发展")
    
    # 3. 高级检索（指定配置）
    config = RetrievalConfig(
        strategy=RetrievalStrategy.HYBRID_PARALLEL,
        fusion_method=FusionMethod.RRF,
        domain_filter="career",
        max_results=15
    )
    context = retriever.retrieve("Python工程师职位", config=config)
    
    # 4. 自适应检索（根据查询类型自动选择策略）
    context = retriever.retrieve_adaptive(
        query="我认识的人中谁在阿里工作？",
        query_type=QueryType.RELATIONAL
    )
    ```
    """
    
    def __init__(self, user_id: str, enable_cache: bool = True):
        self.user_id = user_id
        self.enable_cache = enable_cache
        
        # 初始化检索器
        self.retrievers: Dict[str, BaseRetriever] = {}
        self._init_retrievers()
        
        # 缓存
        self.cache: Dict[str, Tuple[RetrievalContext, datetime]] = {}
        
        print(f"✅ [UnifiedHybridRetrieval] 初始化完成: user={user_id}")
        print(f"   可用检索器: {list(self.retrievers.keys())}")
    
    def _init_retrievers(self):
        """初始化所有检索器"""
        # Neo4j检索器
        neo4j_retriever = Neo4jRetriever(self.user_id)
        if neo4j_retriever.is_available():
            self.retrievers['neo4j'] = neo4j_retriever
        
        # RAG检索器（启用GPU和并发优化）
        rag_config = {
            'use_concurrent_optimizer': True,  # 启用并发优化
            'use_gpu': True  # 启用GPU加速
        }
        rag_retriever = RAGRetriever(self.user_id, config=rag_config)
        if rag_retriever.is_available():
            self.retrievers['rag'] = rag_retriever
        
        # 可以在这里添加更多检索器
        # self.retrievers['elasticsearch'] = ElasticsearchRetriever(...)
    
    def retrieve(
        self,
        query: str,
        config: Optional[RetrievalConfig] = None
    ) -> RetrievalContext:
        """
        执行检索
        
        Args:
            query: 查询字符串
            config: 检索配置（可选，默认使用自适应配置）
        
        Returns:
            RetrievalContext: 检索上下文
        """
        # 使用默认配置
        if config is None:
            config = RetrievalConfig()
        
        # 检查缓存
        if self.enable_cache and config.cache_enabled:
            cached = self._get_from_cache(query, config)
            if cached:
                return cached
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 根据策略执行检索
        if config.strategy == RetrievalStrategy.GRAPH_ONLY:
            results = self._retrieve_graph_only(query, config)
            graph_count = len(results)
            vector_count = 0
        
        elif config.strategy == RetrievalStrategy.VECTOR_ONLY:
            results = self._retrieve_vector_only(query, config)
            graph_count = 0
            vector_count = len(results)
        
        elif config.strategy == RetrievalStrategy.HYBRID_PARALLEL:
            results, graph_count, vector_count = self._retrieve_hybrid_parallel(query, config)
        
        elif config.strategy == RetrievalStrategy.HYBRID_SERIAL:
            results, graph_count, vector_count = self._retrieve_hybrid_serial(query, config)
        
        elif config.strategy == RetrievalStrategy.ADAPTIVE:
            # 自适应：根据查询特征选择策略
            query_type = self._infer_query_type(query)
            adaptive_config = RetrievalConfig.from_query_type(query_type)
            # 合并用户配置
            adaptive_config.max_results = config.max_results
            adaptive_config.domain_filter = config.domain_filter
            return self.retrieve(query, adaptive_config)
        
        else:
            # 默认使用混合并行
            results, graph_count, vector_count = self._retrieve_hybrid_parallel(query, config)
        
        # 计算执行时间
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 构建上下文
        context = RetrievalContext(
            results=results,
            query=query,
            query_type=self._infer_query_type(query),
            strategy_used=config.strategy,
            fusion_method=config.fusion_method,
            total_results=len(results),
            graph_results=graph_count,
            vector_results=vector_count,
            execution_time_ms=execution_time,
            debug_info={
                'config': {
                    'strategy': config.strategy.value,
                    'fusion_method': config.fusion_method.value,
                    'graph_weight': config.graph_weight,
                    'vector_weight': config.vector_weight
                }
            } if config.debug_mode else {}
        )
        
        # 缓存结果
        if self.enable_cache and config.cache_enabled:
            self._save_to_cache(query, config, context)
        
        return context
    
    def retrieve_adaptive(
        self,
        query: str,
        query_type: Optional[QueryType] = None,
        **kwargs
    ) -> RetrievalContext:
        """
        自适应检索（推荐使用）
        
        Args:
            query: 查询字符串
            query_type: 查询类型（可选，自动推断）
            **kwargs: 其他配置参数
        
        Returns:
            RetrievalContext: 检索上下文
        """
        # 推断查询类型
        if query_type is None:
            query_type = self._infer_query_type(query)
        
        # 根据查询类型创建配置
        config = RetrievalConfig.from_query_type(query_type)
        
        # 应用用户自定义配置
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return self.retrieve(query, config)
    
    def _retrieve_graph_only(
        self,
        query: str,
        config: RetrievalConfig
    ) -> List[RetrievalResult]:
        """纯图检索"""
        if 'neo4j' not in self.retrievers:
            print("⚠️ [UnifiedHybridRetrieval] Neo4j检索器不可用")
            return []
        
        filters = self._build_filters(config)
        return self.retrievers['neo4j'].retrieve(query, config.max_results, filters)
    
    def _retrieve_vector_only(
        self,
        query: str,
        config: RetrievalConfig
    ) -> List[RetrievalResult]:
        """纯向量检索"""
        if 'rag' not in self.retrievers:
            print("⚠️ [UnifiedHybridRetrieval] RAG检索器不可用")
            return []
        
        filters = self._build_filters(config)
        return self.retrievers['rag'].retrieve(query, config.max_results, filters)
    
    def _retrieve_hybrid_parallel(
        self,
        query: str,
        config: RetrievalConfig
    ) -> Tuple[List[RetrievalResult], int, int]:
        """混合并行检索 - 真正的并行执行"""
        import concurrent.futures
        import time
        
        start_time = time.time()
        filters = self._build_filters(config)
        
        graph_results = []
        vector_results = []
        
        # 使用线程池并行执行图检索和向量检索
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            
            # 提交图检索任务
            if 'neo4j' in self.retrievers:
                futures['graph'] = executor.submit(
                    self.retrievers['neo4j'].retrieve,
                    query, config.max_results, filters
                )
            
            # 提交向量检索任务
            if 'rag' in self.retrievers:
                futures['vector'] = executor.submit(
                    self.retrievers['rag'].retrieve,
                    query, config.max_results, filters
                )
            
            # 等待所有任务完成
            for key, future in futures.items():
                try:
                    # 增加超时时间：Neo4j的两阶段LLM语义检索需要更长时间
                    # 第一阶段LLM识别领域(2-3秒) + 第二阶段LLM排序(15秒超时) + 查询时间(1-2秒) = 约20秒
                    result = future.result(timeout=22.0)  # 22秒超时，给LLM增强检索足够时间
                    if key == 'graph':
                        graph_results = result
                    elif key == 'vector':
                        vector_results = result
                except concurrent.futures.TimeoutError:
                    print(f"[混合检索] ⚠️ {key}检索超时(22秒)，跳过该检索器")
                except Exception as e:
                    print(f"[混合检索] ❌ {key}检索失败: {e}")
        
        elapsed = time.time() - start_time
        print(f"[混合检索] 并行检索完成: 图{len(graph_results)}条, 向量{len(vector_results)}条, 耗时{elapsed:.2f}秒")
        
        # 融合结果
        fused_results = HybridFusion.fuse(
            graph_results, vector_results, config.fusion_method, config
        )
        
        return fused_results, len(graph_results), len(vector_results)
    
    def _retrieve_hybrid_serial(
        self,
        query: str,
        config: RetrievalConfig
    ) -> Tuple[List[RetrievalResult], int, int]:
        """混合串行检索（先图后向量）"""
        filters = self._build_filters(config)
        
        # 1. 先执行图检索
        graph_results = []
        if 'neo4j' in self.retrievers:
            graph_results = self.retrievers['neo4j'].retrieve(
                query, config.max_results // 2, filters
            )
        
        # 2. 如果图检索结果不足，用向量补充
        vector_results = []
        if len(graph_results) < config.max_results // 2 and 'rag' in self.retrievers:
            vector_results = self.retrievers['rag'].retrieve(
                query, config.max_results // 2, filters
            )
        
        # 3. 融合结果
        fused_results = HybridFusion.fuse(
            graph_results, vector_results, config.fusion_method, config
        )
        
        return fused_results, len(graph_results), len(vector_results)
    
    def _build_filters(self, config: RetrievalConfig) -> Dict[str, Any]:
        """构建过滤条件"""
        filters = {
            'domain_filter': config.domain_filter,
            'min_confidence': config.min_confidence,
            'expand_relations': config.expand_relations,
            'max_relation_depth': config.max_relation_depth,
            'query_expansion': config.query_expansion
        }
        
        # 时间过滤
        if config.time_decay_enabled:
            # 可以添加时间范围过滤
            pass
        
        return filters
    
    def _infer_query_type(self, query: str) -> QueryType:
        """推断查询类型"""
        query_lower = query.lower()
        
        # 关系查询特征
        relation_keywords = ['谁', '认识', '朋友', '同事', '关系', '人脉']
        if any(kw in query_lower for kw in relation_keywords):
            return QueryType.RELATIONAL
        
        # 时序查询特征
        temporal_keywords = ['最近', '今天', '昨天', '上周', '去年', '什么时候']
        if any(kw in query_lower for kw in temporal_keywords):
            return QueryType.TEMPORAL
        
        # 分析查询特征
        analytical_keywords = ['分析', '统计', '总结', '趋势', '对比']
        if any(kw in query_lower for kw in analytical_keywords):
            return QueryType.ANALYTICAL
        
        # 事实查询特征
        factual_keywords = ['是什么', '在哪', '多少', '哪个']
        if any(kw in query_lower for kw in factual_keywords):
            return QueryType.FACTUAL
        
        # 默认为语义查询
        return QueryType.SEMANTIC
    
    def _get_from_cache(
        self,
        query: str,
        config: RetrievalConfig
    ) -> Optional[RetrievalContext]:
        """从缓存获取"""
        cache_key = f"{query}_{config.strategy.value}_{config.domain_filter}"
        
        if cache_key in self.cache:
            context, timestamp = self.cache[cache_key]
            # 检查是否过期
            if (datetime.now() - timestamp).seconds < config.cache_ttl:
                print(f"✓ [Cache] 命中缓存: {query[:30]}...")
                return context
        
        return None
    
    def _save_to_cache(
        self,
        query: str,
        config: RetrievalConfig,
        context: RetrievalContext
    ):
        """保存到缓存"""
        cache_key = f"{query}_{config.strategy.value}_{config.domain_filter}"
        self.cache[cache_key] = (context, datetime.now())
        
        # 限制缓存大小
        if len(self.cache) > 100:
            # 删除最旧的缓存
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "user_id": self.user_id,
            "retrievers": {},
            "cache": {
                "enabled": self.enable_cache,
                "size": len(self.cache)
            }
        }
        
        for name, retriever in self.retrievers.items():
            stats["retrievers"][name] = retriever.get_statistics()
        
        return stats
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        print("✓ [UnifiedHybridRetrieval] 缓存已清空")


# ==================== 便捷函数 ====================

def create_retriever(user_id: str, **kwargs) -> UnifiedHybridRetrieval:
    """创建检索器的便捷函数"""
    return UnifiedHybridRetrieval(user_id, **kwargs)


def quick_retrieve(
    user_id: str,
    query: str,
    domain: Optional[str] = None,
    max_results: int = 100  # 增加默认值
) -> RetrievalContext:
    """快速检索的便捷函数"""
    retriever = UnifiedHybridRetrieval(user_id)
    return retriever.retrieve_adaptive(
        query=query,
        domain_filter=domain,
        max_results=max_results
    )


# ==================== 示例用法 ====================

if __name__ == "__main__":
    # 示例1：简单检索
    retriever = UnifiedHybridRetrieval(user_id="test_user")
    context = retriever.retrieve("我想了解Python工程师职位")
    
    print(f"\n检索结果: {context.total_results} 个")
    for i, result in enumerate(context.results[:5], 1):
        print(f"{i}. [{result.source}] {result.content[:50]}... (分数: {result.score:.3f})")
    
    # 示例2：自适应检索
    context = retriever.retrieve_adaptive(
        query="我认识的人中谁在阿里工作？",
        query_type=QueryType.RELATIONAL
    )
    
    # 示例3：自定义配置
    config = RetrievalConfig(
        strategy=RetrievalStrategy.HYBRID_PARALLEL,
        fusion_method=FusionMethod.RRF,
        domain_filter="career",
        max_results=15,
        expand_relations=True
    )
    context = retriever.retrieve("职业发展建议", config=config)
    
    # 统计信息
    stats = retriever.get_statistics()
    print(f"\n统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")
