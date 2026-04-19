"""
实时智慧洞察Agent系统 - 三层混合AI架构 + 多Agent协作
通过RAG和Neo4j混合检索实时生成智慧洞察报告和决策逻辑分析

架构设计：
【三层混合AI】
第1层：规则引擎 - 快速响应（基于数据的规则判断和统计分析）
第2层：机器学习 - 量化评估（模型预测、评分、趋势分析）
第3层：LLM深度解读 - Owen-Plus（深度洞察生成、个性化建议）

【多Agent协作】
- 共享记忆空间：所有Agent共用RAG+Neo4j混合检索数据
- 任务链传递：一个Agent的输出自动成为下一个Agent的输入
- 冲突仲裁：Gateway协调多个Agent对同一资源的访问
- 状态广播：Agent完成工作后通知相关方

三个专业领域Agent:
1. RelationshipInsightAgent - 人际关系洞察Agent
2. EducationInsightAgent - 教育升学洞察Agent  
3. CareerInsightAgent - 职业规划洞察Agent

每个Agent都能:
- 第1层：实时从RAG和Neo4j混合检索相关数据，应用规则引擎快速分析
- 第2层：使用机器学习模型进行量化评估和预测
- 第3层：调用LLM进行深度解读，生成个性化洞察和建议
- 协作：与其他Agent共享数据、传递任务、广播状态
"""
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入RAG和Neo4j相关模块
from learning.kg_rag_integration import get_kg_rag_system
from learning.unified_hybrid_retrieval import QueryType, RetrievalStrategy
from knowledge.information_knowledge_graph import InformationKnowledgeGraph

# 导入LLM服务
from llm.llm_service import LLMService

# 导入多Agent协作系统
from insights.multi_agent_system import CollaborativeAgent, AgentGateway, AgentStatus


@dataclass
class InsightReport:
    """
    洞察报告 - 三层混合AI架构输出
    
    第1层：规则引擎 - key_findings（基于数据的快速分析）
    第2层：机器学习 - ml_evaluation（量化评估和预测）
    第3层：LLM深度解读 - recommendations + summary（深度洞察）
    """
    insight_id: str
    agent_type: str  # relationship/education/career
    title: str
    summary: str  # 第3层LLM生成的深度摘要
    key_findings: List[Dict[str, Any]]  # 第1层规则引擎生成
    ml_evaluation: Dict[str, Any]  # 第2层机器学习评估
    recommendations: List[Dict[str, Any]]  # 第3层LLM生成的深度建议
    decision_logic: Dict[str, Any]
    data_sources: Dict[str, Any]
    confidence_score: float
    generated_at: datetime
    layer_timing: Dict[str, float] = None  # 三层处理时间统计



class BaseInsightAgent(CollaborativeAgent):
    """
    基础洞察Agent - 三层混合AI架构 + 多Agent协作
    
    【三层混合AI架构】
    第1层：规则引擎 - 快速响应（数据检索、统计分析、规则匹配）
    第2层：机器学习 - 量化评估（风险评估、趋势预测、匹配度评分）
    第3层：LLM深度解读 - Owen-Plus（深度洞察、个性化建议）
    
    【多Agent协作】
    - 继承CollaborativeAgent，支持消息传递和共享数据
    - 从共享记忆空间获取混合检索数据
    - 输出传递给下一个Agent
    """
    
    def __init__(self, user_id: str, name: str, agent_type: str):
        # 初始化协作Agent基类
        super().__init__(name=name, agent_type=agent_type)
        
        self.user_id = user_id
        self.llm_service = None
        
        print(f"[{name}] 初始化用户 {user_id}")
        
        # 初始化LLM服务
        try:
            self.llm_service = LLMService()
            print(f"  ✅ LLM服务连接成功")
        except Exception as e:
            print(f"  ⚠️ LLM服务连接失败: {e}")
    
    def _retrieve_from_rag(self, query: str, max_nodes: int = 10) -> Dict[str, Any]:
        """
        从RAG系统检索（已废弃，使用_retrieve_hybrid代替）
        保留此方法以兼容旧代码
        """
        return self._retrieve_hybrid(query, max_nodes, use_rag_only=True)
    
    def _retrieve_from_neo4j(self, query: str, category: str = None, max_nodes: int = 20) -> Dict[str, Any]:
        """
        从Neo4j知识图谱检索（已废弃，使用_retrieve_hybrid代替）
        保留此方法以兼容旧代码
        """
        return self._retrieve_hybrid(query, max_nodes, use_neo4j_only=True, category=category)
    
    def _retrieve_hybrid(
        self,
        query: str,
        max_nodes: int = 20,
        use_rag_only: bool = False,
        use_neo4j_only: bool = False,
        category: str = None
    ) -> Dict[str, Any]:
        """
        统一混合检索接口
        
        Args:
            query: 查询字符串
            max_nodes: 最大结果数
            use_rag_only: 仅使用RAG检索
            use_neo4j_only: 仅使用Neo4j检索
            category: 类别过滤
        
        Returns:
            统一格式的检索结果
        """
        if not self.kg_rag:
            return {"nodes": [], "relationships": [], "reasoning_path": "", "influence_summary": {}}
        
        try:
            from backend.learning.unified_hybrid_retrieval import (
                RetrievalConfig, RetrievalStrategy, FusionMethod, QueryType
            )
            
            # 根据agent类型和参数构建配置
            if use_rag_only:
                strategy = RetrievalStrategy.VECTOR_ONLY
            elif use_neo4j_only:
                strategy = RetrievalStrategy.GRAPH_ONLY
            else:
                # 使用混合并行策略
                strategy = RetrievalStrategy.HYBRID_PARALLEL
            
            # 根据agent类型推断查询类型和领域
            query_type, domain = self._infer_query_context(query)
            
            # 构建配置
            config = RetrievalConfig(
                strategy=strategy,
                fusion_method=FusionMethod.RRF,  # 使用RRF融合
                max_results=max_nodes,
                domain_filter=domain or category,
                expand_relations=True,
                max_relation_depth=2,
                query_expansion=True,
                graph_weight=0.6,
                vector_weight=0.4
            )
            
            # 执行检索
            context = self.kg_rag.retrieve(query, config)
            
            # 转换为统一格式
            unified_result = {
                "nodes": [
                    {
                        "id": result.id,
                        "name": result.content[:100],
                        "type": result.node_type,
                        "category": result.category,
                        "confidence": result.confidence,
                        "influence_score": result.score,
                        "source": result.source,
                        "metadata": result.metadata
                    }
                    for result in context.results
                ],
                "relationships": self._extract_relationships(context.results),
                "reasoning_path": f"使用{context.strategy_used.value}策略，融合方法：{context.fusion_method.value}",
                "influence_summary": self._calculate_influence(context.results),
                "stats": {
                    "total": context.total_results,
                    "graph": context.graph_results,
                    "vector": context.vector_results,
                    "execution_time_ms": context.execution_time_ms
                }
            }
            
            print(f"  ✓ 混合检索: {context.total_results} 个节点 (图:{context.graph_results}, 向量:{context.vector_results})")
            
            return unified_result
            
        except Exception as e:
            print(f"  ✗ 混合检索失败: {e}")
            import traceback
            traceback.print_exc()
            return {"nodes": [], "relationships": [], "reasoning_path": "", "influence_summary": {}}
    
    def _infer_query_context(self, query: str) -> Tuple[Any, Optional[str]]:
        """推断查询类型和领域"""
        from backend.learning.unified_hybrid_retrieval import QueryType
        
        # 根据agent类型确定领域
        domain_map = {
            "relationship": "relationship",
            "education": "education",
            "career": "career"
        }
        domain = domain_map.get(self.agent_type)
        
        # 推断查询类型
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ['谁', '认识', '朋友', '关系']):
            query_type = QueryType.RELATIONAL
        elif any(kw in query_lower for kw in ['分析', '统计', '趋势']):
            query_type = QueryType.ANALYTICAL
        elif any(kw in query_lower for kw in ['最近', '什么时候']):
            query_type = QueryType.TEMPORAL
        else:
            query_type = QueryType.SEMANTIC
        
        return query_type, domain
    
    def _extract_relationships(self, results: List) -> List[Dict]:
        """从检索结果中提取关系"""
        relationships = []
        
        for result in results:
            if result.relations:
                for rel in result.relations:
                    relationships.append({
                        "source": result.content[:50],
                        "target": rel.get('target', ''),
                        "type": rel.get('type', 'RELATED_TO'),
                        "path": rel.get('path', '')
                    })
        
        return relationships[:20]  # 最多20条关系
    
    def _calculate_influence(self, results: List) -> Dict[str, float]:
        """计算影响力汇总"""
        summary = {}
        for result in results:
            category = result.category or 'unknown'
            if category not in summary:
                summary[category] = 0
            summary[category] += result.score
        
        # 归一化
        total = sum(summary.values())
        if total > 0:
            summary = {k: v / total for k, v in summary.items()}
        
        return summary
    
    def _retrieve_from_neo4j(self, query: str, category: str = None, max_nodes: int = 20) -> Dict[str, Any]:
        """从Neo4j知识图谱检索"""
        if not self.info_kg:
            return {"nodes": [], "relationships": []}
        
        nodes = []
        relationships = []
        
        try:
            search_results = self.info_kg.search_information(
                keyword=query,
                limit=max_nodes
            )
            
            for result in search_results:
                info = result.get('information', {})
                if info and (not category or info.get('category') == category):
                    nodes.append({
                        "id": info.get('id', ''),
                        "name": info.get('name', ''),
                        "type": info.get('type', 'unknown'),
                        "category": info.get('category', 'unknown'),
                        "confidence": info.get('confidence', 0.5),
                        "metadata": info
                    })
                    
                    related = self.info_kg.get_related_information(
                        info_name=info.get('name', ''),
                        max_depth=2
                    )
                    
                    for rel in related[:5]:
                        rel_info = rel.get('information', {})
                        if rel_info:
                            relationships.append({
                                "source": info.get('name', ''),
                                "target": rel_info.get('name', ''),
                                "path": " -> ".join(rel.get('path', []))
                            })
            
            print(f"  ✓ Neo4j检索: {len(nodes)} 个节点, {len(relationships)} 条关系")
            
        except Exception as e:
            print(f"  ✗ Neo4j检索失败: {e}")
        
        return {"nodes": nodes, "relationships": relationships}
    
    def _generate_insight_with_llm(
        self,
        query: str,
        rag_data: Dict[str, Any],
        neo4j_data: Dict[str, Any],
        domain_context: str
    ) -> str:
        """使用LLM生成洞察"""
        prompt = f"""你是一个专业的{self.agent_type}领域分析师。请基于以下数据生成深度洞察分析。

【用户查询】
{query}

【领域背景】
{domain_context}

【RAG检索结果】
节点数: {len(rag_data.get('nodes', []))}
影响力分析: {json.dumps(rag_data.get('influence_summary', {}), ensure_ascii=False)}
推理路径: {rag_data.get('reasoning_path', '无')}

【Neo4j知识图谱】
节点数: {len(neo4j_data.get('nodes', []))}
关系数: {len(neo4j_data.get('relationships', []))}

关键节点:
{self._format_nodes_for_prompt(rag_data.get('nodes', [])[:5] + neo4j_data.get('nodes', [])[:5])}

请生成一份专业的洞察分析报告（300-500字），包括：
1. 整体评估
2. 关键发现（3-5个要点）
3. 深层原因分析
4. 战略建议

要求：
- 语言专业但易懂
- 观点明确，有理有据
- 结合具体数据支持观点
- 给出可执行的建议
"""
        
        try:
            response = get_ai_response(prompt=prompt, max_tokens=1000, temperature=0.7)
            return response
        except Exception as e:
            print(f"  ✗ LLM生成失败: {e}")
            return "洞察生成失败，请稍后重试"
    
    def _format_nodes_for_prompt(self, nodes: List[Dict]) -> str:
        """格式化节点用于prompt"""
        lines = []
        for i, node in enumerate(nodes[:10], 1):
            lines.append(
                f"{i}. [{node.get('type', 'unknown')}] {node.get('name', 'unknown')} "
                f"(置信度: {node.get('confidence', 0):.2f})"
            )
        return "\n".join(lines) if lines else "无"
    
    def _calculate_confidence(self, rag_data: Dict, neo4j_data: Dict) -> float:
        """计算置信度"""
        rag_score = min(len(rag_data.get('nodes', [])) / 10, 1.0) * 0.5
        neo4j_score = min(len(neo4j_data.get('nodes', [])) / 20, 1.0) * 0.5
        return rag_score + neo4j_score
    
    # ==================== 三层混合AI架构核心方法 ====================
    
    def _layer1_rule_engine(
        self,
        rag_data: Dict,
        neo4j_data: Dict,
        domain_context: str
    ) -> List[Dict[str, Any]]:
        """
        第1层：规则引擎 - 快速响应
        
        基于数据的规则判断和统计分析，快速生成关键发现
        - 数据统计（数量、分布、密度等）
        - 阈值判断（过多、过少、适中）
        - 规则匹配（类别分布、关系密度等）
        
        由子类实现具体的规则逻辑
        """
        raise NotImplementedError("子类必须实现_layer1_rule_engine方法")
    
    def _layer2_ml_evaluation(
        self,
        rag_data: Dict,
        neo4j_data: Dict,
        key_findings: List[Dict]
    ) -> Dict[str, Any]:
        """
        第2层：机器学习 - 量化评估
        
        使用机器学习模型进行量化评估和预测
        - 风险评估（低/中/高）
        - 趋势预测（上升/稳定/下降）
        - 匹配度评分（0-100分）
        - 优先级排序
        
        返回格式：
        {
            "risk_level": "low/medium/high",
            "trend": "rising/stable/declining",
            "match_score": 0-100,
            "priority_ranking": [...],
            "predictions": {...}
        }
        """
        from backend.insights.ml_models import get_risk_assessor, get_trend_predictor
        
        node_count = len(neo4j_data.get('nodes', []))
        relationship_count = len(neo4j_data.get('relationships', []))
        
        # 构建当前状态数据
        current_status = {
            "node_count": node_count,
            "relationship_count": relationship_count,
            "data_completeness": min(node_count / 20, 1.0),
            "network_density": relationship_count / max(node_count, 1)
        }
        
        # 使用 ML 模型进行风险评估
        try:
            risk_assessor = get_risk_assessor()
            risk_result = risk_assessor.assess_risks(
                decision_context={},
                current_status=current_status
            )
            risk_level = risk_result.get('overall_risk_level', 'medium')
            risk_score = risk_result.get('overall_risk_score', 50)
        except Exception as e:
            print(f"  [ML] 风险评估失败: {e}")
            risk_level = "medium" if node_count < 15 else "low"
            risk_score = 50
        
        # 趋势预测
        trend = "stable"
        if node_count > 30:
            trend = "rising"
        elif node_count < 10:
            trend = "declining"
        
        # 匹配度评分（基于数据完整性和质量）
        match_score = min(int(node_count * 2 + relationship_count * 5), 100)
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "trend": trend,
            "match_score": match_score,
            "data_quality": {
                "node_count": node_count,
                "relationship_count": relationship_count,
                "completeness": current_status["data_completeness"],
                "density": current_status["network_density"]
            },
            "model_version": "ml_enhanced_v1.0"
        }
    
    def _layer3_llm_deep_insight(
        self,
        query: str,
        rag_data: Dict,
        neo4j_data: Dict,
        key_findings: List[Dict],
        ml_evaluation: Dict,
        domain_context: str
    ) -> Dict[str, Any]:
        """
        第3层：LLM深度解读 - Owen-Plus
        
        调用大语言模型进行深度洞察生成
        - 深度摘要（整合所有信息的综合分析）
        - 个性化建议（基于用户具体情况）
        - 决策逻辑分析（为什么这样建议）
        
        返回格式：
        {
            "summary": "深度摘要文本",
            "recommendations": [建议列表],
            "reasoning": "推理过程"
        }
        """
        if not self.llm_service:
            # LLM服务不可用时的降级处理
            return {
                "summary": self._generate_fallback_summary(key_findings, ml_evaluation),
                "recommendations": self._generate_fallback_recommendations(key_findings, ml_evaluation),
                "reasoning": "LLM服务不可用，使用规则生成"
            }
        
        # 构建LLM prompt
        prompt = self._build_llm_prompt(
            query, rag_data, neo4j_data, key_findings, ml_evaluation, domain_context
        )
        
        try:
            # 调用LLM生成深度洞察
            response = self.llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            # 解析LLM响应
            return self._parse_llm_response(response)
            
        except Exception as e:
            print(f"  ⚠️ LLM调用失败: {e}")
            return {
                "summary": self._generate_fallback_summary(key_findings, ml_evaluation),
                "recommendations": self._generate_fallback_recommendations(key_findings, ml_evaluation),
                "reasoning": f"LLM调用失败: {str(e)}"
            }
    
    def _build_llm_prompt(
        self,
        query: str,
        rag_data: Dict,
        neo4j_data: Dict,
        key_findings: List[Dict],
        ml_evaluation: Dict,
        domain_context: str
    ) -> str:
        """构建LLM prompt"""
        # 格式化关键发现
        findings_text = "\n".join([
            f"- {f['title']}: {f['description']}"
            for f in key_findings
        ])
        
        # 格式化ML评估
        ml_text = f"""
风险等级: {ml_evaluation.get('risk_level', 'unknown')}
发展趋势: {ml_evaluation.get('trend', 'unknown')}
匹配度评分: {ml_evaluation.get('match_score', 0)}/100
"""
        
        # 提取具体的人物信息（用于人际关系分析）
        people_info = ""
        neo4j_nodes = neo4j_data.get('nodes', [])
        person_nodes = [n for n in neo4j_nodes if n.get('type') == 'Person']
        
        if person_nodes:
            people_info = "\n【人际关系详细信息】\n"
            people_info += f"总人数: {len(person_nodes)} 人\n\n"
            
            # 按类别分组
            categories = {}
            for node in person_nodes:
                category = node.get('category', 'unknown')
                if category not in categories:
                    categories[category] = []
                categories[category].append(node.get('name', '未知'))
            
            # 输出分类信息
            category_display = {
                'friends': '朋友',
                'colleagues': '同事',
                'family': '家人',
                'mentors': '导师',
                'classmates': '同学',
                'close_friends': '密友',
                'unknown': '其他'
            }
            
            for category, names in categories.items():
                display_name = category_display.get(category, category)
                people_info += f"{display_name} ({len(names)}人): {', '.join(names[:10])}"
                if len(names) > 10:
                    people_info += f" 等{len(names)}人"
                people_info += "\n"
        
        # 提取关系信息
        relationships_info = ""
        relationships = neo4j_data.get('relationships', [])
        if relationships:
            relationships_info = f"\n【关系连接】\n共 {len(relationships)} 条关系连接\n"
        
        prompt = f"""你是一个专业的{self.agent_type}领域分析师。请基于以下数据生成深度洞察分析。

【用户查询】
{query}

【领域背景】
{domain_context}

【第1层：规则引擎分析结果】
{findings_text}

【第2层：机器学习评估结果】
{ml_text}

【数据统计】
- Neo4j节点数: {len(neo4j_data.get('nodes', []))}
- Neo4j关系数: {len(neo4j_data.get('relationships', []))}
- RAG检索节点数: {len(rag_data.get('nodes', []))}
{people_info}{relationships_info}

请生成一份专业的洞察分析报告，包括：

1. 【深度摘要】（200-300字）
   - 整合第1层和第2层的分析结果
   - 给出整体评估和核心洞察
   - 语言专业但易懂
   - 必须基于上面提供的实际数据（人数、分类等）

2. 【个性化建议】（3-5条）
   每条建议包括：
   - priority: high/medium/low
   - category: 建议类别
   - action: 具体行动建议
   - expected_impact: 预期影响
   - timeline: 时间线
   - reasoning: 为什么这样建议

3. 【决策逻辑】
   - 说明推理过程和依据

请以JSON格式返回：
{{
    "summary": "深度摘要文本",
    "recommendations": [
        {{
            "priority": "high",
            "category": "类别",
            "action": "具体行动",
            "expected_impact": "预期影响",
            "timeline": "时间线",
            "reasoning": "推理依据"
        }}
    ],
    "reasoning": "整体决策逻辑"
}}
"""
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试解析JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 如果不是JSON格式，返回原始文本
                return {
                    "summary": response[:500],
                    "recommendations": [],
                    "reasoning": "LLM返回非JSON格式"
                }
        except Exception as e:
            return {
                "summary": response[:500] if response else "解析失败",
                "recommendations": [],
                "reasoning": f"解析失败: {str(e)}"
            }
    
    def _generate_fallback_summary(self, key_findings: List[Dict], ml_evaluation: Dict) -> str:
        """生成降级摘要（LLM不可用时）"""
        findings_count = len(key_findings)
        risk_level = ml_evaluation.get('risk_level', 'unknown')
        match_score = ml_evaluation.get('match_score', 0)
        
        return f"基于数据分析，识别到{findings_count}个关键发现。" \
               f"当前风险等级为{risk_level}，匹配度评分{match_score}/100。" \
               f"建议关注关键发现中的高优先级项目，并采取相应行动。"
    
    def _generate_fallback_recommendations(self, key_findings: List[Dict], ml_evaluation: Dict) -> List[Dict]:
        """生成降级建议（LLM不可用时）"""
        recommendations = []
        
        # 基于风险等级生成建议
        risk_level = ml_evaluation.get('risk_level', 'medium')
        if risk_level == 'high':
            recommendations.append({
                "priority": "high",
                "category": "风险应对",
                "action": "当前风险等级较高，建议立即采取行动改善现状",
                "expected_impact": "降低风险，改善整体状况",
                "timeline": "立即执行",
                "reasoning": "基于风险评估结果"
            })
        
        # 基于关键发现生成建议
        for finding in key_findings[:2]:
            if finding.get('importance') == 'high':
                recommendations.append({
                    "priority": "high",
                    "category": "关键改进",
                    "action": f"针对'{finding.get('title', '')}'，建议采取改进措施",
                    "expected_impact": "提升整体表现",
                    "timeline": "1-3个月",
                    "reasoning": "基于关键发现"
                })
        
        return recommendations[:3]



class RelationshipInsightAgent(BaseInsightAgent):
    """
    人际关系洞察Agent - 三层混合AI + 多Agent协作
    
    专注于分析人际关系网络、社交模式、关系质量等
    
    协作特点：
    - 从共享记忆获取混合检索数据
    - 输出传递给Education Agent
    - 接收其他Agent的状态通知
    """
    
    def __init__(self, user_id: str):
        super().__init__(user_id, name="relationship", agent_type="人际关系")
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行人际关系分析（协作模式）
        
        Args:
            input_data: {
                "query": 用户查询,
                "hybrid_data": 共享的混合检索数据,
                "prev_agent_output": 上一个Agent的输出（如果有）,
                "context": 任务链上下文
            }
        
        Returns:
            {
                "agent_name": "relationship",
                "summary": "摘要",
                "key_findings": [...],
                "ml_evaluation": {...},
                "recommendations": [...],
                "confidence_score": 0.8
            }
        """
        print(f"\n{'='*60}")
        print(f"[{self.name}] 开始执行任务")
        print(f"{'='*60}\n")
        
        query = input_data.get("query", "分析我的人际关系网络")
        hybrid_data = input_data.get("hybrid_data", {})
        prev_output = input_data.get("prev_agent_output")
        
        # 设置状态为工作中
        self.status = AgentStatus.WORKING
        if self.gateway:
            self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.WORKING)
        
        start_time = datetime.now()
        layer_timing = {}
        
        try:
            # 数据整合（不再分离，统一使用混合数据）
            # neo4j_data 包含所有节点，用于统计分析
            neo4j_data = {
                "nodes": hybrid_data.get("nodes", []),
                "relationships": hybrid_data.get("relationships", [])
            }
            
            # rag_data 包含影响力分析等元数据
            rag_data = {
                "nodes": hybrid_data.get("nodes", []),
                "relationships": hybrid_data.get("relationships", []),
                "influence_summary": hybrid_data.get("influence_summary", {}),
                "stats": hybrid_data.get("stats", {})
            }
            
            # 统计不同来源的节点数（用于前端显示）
            all_nodes = hybrid_data.get("nodes", [])
            neo4j_node_count = len([n for n in all_nodes if n.get("source") in ["neo4j", "graph", "hybrid"]])
            rag_node_count = len([n for n in all_nodes if n.get("source") in ["faiss", "vector", "hybrid"]])
            
            # 第1层：规则引擎
            print("📊 第1层：规则引擎分析...")
            print(f"  [调试] hybrid_data 节点数: {len(hybrid_data.get('nodes', []))}")
            print(f"  [调试] neo4j_data 节点数: {len(neo4j_data.get('nodes', []))}")
            print(f"  [调试] 统计 - Neo4j来源: {neo4j_node_count}, RAG来源: {rag_node_count}")
            print(f"  [调试] rag_data 节点数: {len(rag_data.get('nodes', []))}")
            
            # 打印前3个节点的详细信息
            for i, node in enumerate(hybrid_data.get('nodes', [])[:3], 1):
                print(f"  [调试] 节点{i}: type={node.get('type')}, node_type={node.get('node_type')}, name={node.get('name')}, content={node.get('content', '')[:50]}")
            
            layer1_start = datetime.now()
            key_findings = self._extract_relationship_findings(rag_data, neo4j_data)
            layer_timing["layer1_ms"] = (datetime.now() - layer1_start).total_seconds() * 1000
            print(f"  ✓ 完成，发现 {len(key_findings)} 个关键点，耗时 {layer_timing['layer1_ms']:.2f}ms")
            
            # 第2层：机器学习评估
            print("🤖 第2层：机器学习评估...")
            layer2_start = datetime.now()
            ml_evaluation = self._layer2_ml_evaluation(rag_data, neo4j_data, key_findings)
            layer_timing["layer2_ms"] = (datetime.now() - layer2_start).total_seconds() * 1000
            print(f"  ✓ 完成，耗时 {layer_timing['layer2_ms']:.2f}ms")
            
            # 第3层：LLM深度解读
            print("🧠 第3层：LLM深度解读...")
            layer3_start = datetime.now()
            domain_context = """
人际关系领域分析重点：
- 关系网络的广度和深度
- 关系质量和互动频率
- 关键人物的影响力
- 社交模式和偏好
- 潜在的关系风险和机会
"""
            llm_output = self._layer3_llm_deep_insight(
                query, rag_data, neo4j_data, key_findings, ml_evaluation, domain_context
            )
            layer_timing["layer3_ms"] = (datetime.now() - layer3_start).total_seconds() * 1000
            print(f"  ✓ 完成，耗时 {layer_timing['layer3_ms']:.2f}ms")
            
            # 构建输出
            print(f"\n  [调试] 构建输出:")
            print(f"    rag_node_count = {rag_node_count}")
            print(f"    neo4j_node_count = {neo4j_node_count}")
            print(f"    key_findings 数量 = {len(key_findings)}")
            print(f"    recommendations 数量 = {len(llm_output.get('recommendations', []))}")
            
            output = {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "summary": llm_output.get("summary", ""),
                "key_findings": key_findings,
                "ml_evaluation": ml_evaluation,
                "recommendations": llm_output.get("recommendations", []),
                "confidence_score": self._calculate_confidence(rag_data, neo4j_data),
                "layer_timing": layer_timing,
                "data_sources": {
                    "rag_nodes": rag_node_count,
                    "neo4j_nodes": neo4j_node_count
                },
                "debug_info": {
                    "hybrid_data_nodes": len(hybrid_data.get('nodes', [])),
                    "neo4j_data_nodes": len(neo4j_data.get('nodes', [])),
                    "rag_data_nodes": len(rag_data.get('nodes', [])),
                    "all_node_types": list(set([n.get('type') or n.get('node_type', 'unknown') for n in hybrid_data.get('nodes', [])])),
                    "person_node_count": len([n for n in hybrid_data.get('nodes', []) if (n.get('type') or n.get('node_type')) == 'Person']),
                    "sample_nodes": [
                        {
                            "type": n.get('type'),
                            "node_type": n.get('node_type'),
                            "name": n.get('name'),
                            "content_preview": n.get('content', '')[:50],
                            "source": n.get('source'),
                            "category": n.get('category')
                        }
                        for n in hybrid_data.get('nodes', [])[:5]
                    ]
                }
            }
            
            print(f"    output['data_sources'] = {output['data_sources']}")
            print(f"    output['debug_info'] keys = {list(output['debug_info'].keys())}")
            
            # 设置状态为完成
            self.status = AgentStatus.COMPLETED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.COMPLETED)
            
            print(f"\n✅ [{self.name}] 任务完成")
            print(f"  - 关键发现: {len(key_findings)} 个")
            print(f"  - 建议: {len(output['recommendations'])} 条")
            print(f"  - 总耗时: {sum(layer_timing.values()):.2f}ms\n")
            
            return output
            
        except Exception as e:
            print(f"\n❌ [{self.name}] 任务失败: {e}")
            self.status = AgentStatus.FAILED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.FAILED)
            raise
    
    def generate_insight_report(
        self,
        query: str = "分析我的人际关系网络",
        focus_area: Optional[str] = None
    ) -> InsightReport:
        """
        生成人际关系洞察报告
        
        Args:
            query: 分析查询
            focus_area: 关注领域 (family/friend/colleague/mentor等)
        """
        self._ensure_connections()
        
        print(f"\n{'='*60}")
        print(f"[人际关系Agent] 开始生成洞察报告")
        print(f"  查询: {query}")
        print(f"  关注领域: {focus_area or '全部'}")
        print(f"{'='*60}\n")
        
        # 使用统一混合检索（自动融合RAG和Neo4j）
        print("🔍 步骤1: 混合检索（RAG + Neo4j）...")
        hybrid_data = self._retrieve_hybrid(
            query=query,
            max_nodes=30,
            category=focus_area or "relationship"
        )
        
        # 为了兼容旧代码，分离数据
        rag_data = {
            "nodes": [n for n in hybrid_data["nodes"] if n.get("source") in ["vector", "hybrid"]],
            "relationships": hybrid_data["relationships"],
            "reasoning_path": hybrid_data["reasoning_path"],
            "influence_summary": hybrid_data["influence_summary"]
        }
        
        neo4j_data = {
            "nodes": [n for n in hybrid_data["nodes"] if n.get("source") in ["graph", "hybrid"]],
            "relationships": hybrid_data["relationships"]
        }
        
        print(f"  ✓ 混合检索完成: 总计{len(hybrid_data['nodes'])}个节点")
        print(f"    - 图检索: {hybrid_data['stats']['graph']}个")
        print(f"    - 向量检索: {hybrid_data['stats']['vector']}个")
        print(f"    - 执行时间: {hybrid_data['stats']['execution_time_ms']:.2f}ms")
        
        # 3. 生成洞察
        print("\n🧠 步骤2: LLM生成深度洞察...")
        domain_context = f"""
人际关系领域分析重点：
- 关系网络的广度和深度
- 关系质量和互动频率
- 关键人物的影响力
- 社交模式和偏好
- 潜在的关系风险和机会
{f'- 特别关注: {focus_area}' if focus_area else ''}
"""
        
        insight_summary = self._generate_insight_with_llm(
            query, rag_data, neo4j_data, domain_context
        )
        
        # 4. 提取关键发现
        key_findings = self._extract_relationship_findings(rag_data, neo4j_data)
        
        # 5. 生成建议
        recommendations = self._generate_relationship_recommendations(key_findings, rag_data, neo4j_data)
        
        # 6. 决策逻辑分析
        decision_logic = self._analyze_relationship_decision_logic(rag_data, neo4j_data)
        
        report = InsightReport(
            insight_id=f"relationship_{datetime.now().timestamp()}",
            agent_type="relationship",
            title=f"人际关系洞察报告 - {focus_area or '综合分析'}",
            summary=insight_summary,
            key_findings=key_findings,
            recommendations=recommendations,
            decision_logic=decision_logic,
            data_sources={
                "rag_nodes": len(rag_data.get('nodes', [])),
                "neo4j_nodes": len(neo4j_data.get('nodes', [])),
            },
            confidence_score=self._calculate_confidence(rag_data, neo4j_data),
            generated_at=datetime.now()
        )
        
        print(f"\n✅ 人际关系洞察报告生成完成")
        print(f"  关键发现: {len(key_findings)} 个")
        print(f"  建议: {len(recommendations)} 条")
        print(f"  置信度: {report.confidence_score:.2f}")
        print(f"{'='*60}\n")
        
        return report
    
    def _extract_relationship_findings(self, rag_data: Dict, neo4j_data: Dict) -> List[Dict[str, Any]]:
        """
        提取人际关系关键发现 - 基于实际检索数据动态生成
        
        数据来源：
        - neo4j_data['nodes']: Entity(type='Person') 节点列表
        - neo4j_data['relationships']: 人物之间的关系
        - rag_data['influence_summary']: 影响力分析
        """
        findings = []
        
        neo4j_nodes = neo4j_data.get('nodes', [])
        relationships = neo4j_data.get('relationships', [])
        influence_summary = rag_data.get('influence_summary', {})
        
        # 添加调试发现
        findings.append({
            "type": "debug_info",
            "title": f"调试信息：数据统计",
            "description": f"neo4j_nodes总数: {len(neo4j_nodes)}, 前3个节点类型: {[n.get('type') or n.get('node_type', 'unknown') for n in neo4j_nodes[:3]]}",
            "importance": "low",
            "debug_data": {
                "total_nodes": len(neo4j_nodes),
                "node_types": list(set([n.get('type') or n.get('node_type', 'unknown') for n in neo4j_nodes])),
                "sample_nodes": [
                    {
                        "type": n.get('type'),
                        "node_type": n.get('node_type'),
                        "name": n.get('name'),
                        "content": n.get('content', '')[:50]
                    }
                    for n in neo4j_nodes[:3]
                ]
            }
        })
        
        # 1. 人物分类统计
        person_categories = {}
        person_names = []
        
        # 调试：打印节点类型统计
        all_types = [n.get('type', 'unknown') for n in neo4j_nodes]
        type_counts = {}
        for t in all_types:
            type_counts[t] = type_counts.get(t, 0) + 1
        print(f"  [调试] 节点类型统计: {type_counts}")
        
        for node in neo4j_nodes:
            # 直接从 Neo4j 查询的数据结构
            node_type = node.get('type', '')
            
            if node_type == 'Person':
                category = node.get('category', 'unknown')
                person_categories[category] = person_categories.get(category, 0) + 1
                name = node.get('name', '')
                if name:
                    person_names.append(name)
        
        print(f"  [调试] Person节点统计: 总数={len(person_names)}, 分类={person_categories}")
        
        # 2. 关系网络规模分析
        total_people = len(person_names)
        if total_people > 0:
            # 根据人数规模给出不同的发现
            if total_people >= 20:
                findings.append({
                    "type": "network_size",
                    "title": f"关系网络规模: {total_people} 人（丰富）",
                    "description": f"你的人际网络包含{total_people}位重要人物，网络规模较为丰富，有利于资源整合和机会获取",
                    "importance": "high",
                    "count": total_people,
                    "people_sample": person_names[:5]  # 前5个人名作为样本
                })
            elif total_people >= 10:
                findings.append({
                    "type": "network_size",
                    "title": f"关系网络规模: {total_people} 人（适中）",
                    "description": f"你的人际网络包含{total_people}位重要人物，网络规模适中，可以考虑进一步拓展",
                    "importance": "medium",
                    "count": total_people,
                    "people_sample": person_names[:5]
                })
            else:
                findings.append({
                    "type": "network_size",
                    "title": f"关系网络规模: {total_people} 人（较小）",
                    "description": f"你的人际网络包含{total_people}位重要人物，建议主动拓展人际关系，增加社交机会",
                    "importance": "high",
                    "count": total_people,
                    "people_sample": person_names
                })
        
        # 3. 人物类别分布分析
        if person_categories:
            # 找出最多的类别
            top_category = max(person_categories.items(), key=lambda x: x[1])
            category_name, category_count = top_category
            
            # 类别名称映射
            category_display = {
                'friend': '朋友',
                'colleague': '同事',
                'family': '家人',
                'mentor': '导师',
                'classmate': '同学',
                'unknown': '其他'
            }
            display_name = category_display.get(category_name, category_name)
            
            findings.append({
                "type": "category_distribution",
                "title": f"关系类型分布: {display_name}占主导",
                "description": f"你的人际网络中，{display_name}类关系最多（{category_count}人），占比{category_count/total_people*100:.1f}%。" + 
                              (f"建议平衡发展其他类型的关系" if category_count/total_people > 0.6 else "关系类型分布较为均衡"),
                "importance": "medium",
                "distribution": person_categories
            })
        
        # 4. 关系密度分析
        if relationships:
            connection_count = len(relationships)
            # 计算关系密度（实际连接数 / 可能的最大连接数）
            max_connections = total_people * (total_people - 1) / 2 if total_people > 1 else 1
            density = connection_count / max_connections if max_connections > 0 else 0
            
            if density > 0.3:
                findings.append({
                    "type": "connection_density",
                    "title": f"关系密度: {connection_count} 条连接（紧密）",
                    "description": f"你的人际网络中存在{connection_count}条互动连接，关系密度{density*100:.1f}%，网络较为紧密",
                    "importance": "medium",
                    "count": connection_count,
                    "density": density
                })
            elif density > 0.1:
                findings.append({
                    "type": "connection_density",
                    "title": f"关系密度: {connection_count} 条连接（适中）",
                    "description": f"你的人际网络中存在{connection_count}条互动连接，关系密度{density*100:.1f}%，可以加强人物之间的联系",
                    "importance": "medium",
                    "count": connection_count,
                    "density": density
                })
            else:
                findings.append({
                    "type": "connection_density",
                    "title": f"关系密度: {connection_count} 条连接（稀疏）",
                    "description": f"你的人际网络中存在{connection_count}条互动连接，关系密度{density*100:.1f}%，建议促进人物之间的互动",
                    "importance": "high",
                    "count": connection_count,
                    "density": density
                })
        
        # 5. 影响力分析
        if influence_summary:
            top_factor = max(influence_summary.items(), key=lambda x: x[1])
            factor_name, factor_value = top_factor
            
            findings.append({
                "type": "influence_analysis",
                "title": f"主要影响因素: {factor_name}",
                "description": f"在人际关系决策中，{factor_name}的影响力最大，占比{factor_value*100:.1f}%",
                "importance": "high",
                "factor": factor_name,
                "value": factor_value
            })
        
        # 6. 如果没有数据，给出提示
        if not findings:
            findings.append({
                "type": "no_data",
                "title": "人际关系数据较少",
                "description": "当前系统中记录的人际关系信息较少，建议多与我交流你的朋友、同事、家人等人际关系，以便提供更精准的分析",
                "importance": "medium"
            })
        
        return findings
    
    def _generate_relationship_recommendations(
        self,
        key_findings: List[Dict],
        rag_data: Dict,
        neo4j_data: Dict
    ) -> List[Dict[str, Any]]:
        """
        生成人际关系建议 - 基于实际检索数据动态生成
        
        数据来源：
        - key_findings: 从混合检索中提取的关键发现
        - neo4j_data: 人物节点和关系数据
        - rag_data: 影响力分析数据
        """
        recommendations = []
        
        neo4j_nodes = neo4j_data.get('nodes', [])
        relationships = neo4j_data.get('relationships', [])
        # 直接从 Neo4j 查询的数据，type 字段就是真实类型
        network_size = len([n for n in neo4j_nodes if n.get('type') == 'Person'])
        connection_count = len(relationships)
        
        # 1. 基于关键发现生成建议
        for finding in key_findings:
            finding_type = finding.get('type', '')
            
            if finding_type == 'network_size':
                # 网络规模发现 -> 拓展或优化建议
                count = finding.get('count', 0)
                if count < 10:
                    recommendations.append({
                        "priority": "high",
                        "category": "网络拓展",
                        "action": f"当前人际网络规模较小（{count}人），建议主动拓展，每月认识2-3位新朋友",
                        "expected_impact": "扩大社交圈，增加机会和资源",
                        "timeline": "持续进行",
                        "data_source": "network_size_analysis"
                    })
                elif count > 50:
                    recommendations.append({
                        "priority": "medium",
                        "category": "关系优化",
                        "action": f"当前人际网络规模较大（{count}人），建议识别并重点维护10-15个核心关系",
                        "expected_impact": "提升关系质量，建立深度信任",
                        "timeline": "3-6个月",
                        "data_source": "network_size_analysis"
                    })
            
            elif finding_type == 'category_distribution':
                # 类别分布发现 -> 平衡建议
                distribution = finding.get('distribution', {})
                if distribution:
                    # 检查是否过于集中
                    total = sum(distribution.values())
                    max_category = max(distribution.values())
                    if max_category / total > 0.6:
                        # 找出缺失或较少的类别
                        all_categories = {'friend', 'colleague', 'mentor', 'classmate'}
                        missing_categories = all_categories - set(distribution.keys())
                        
                        category_display = {
                            'friend': '朋友',
                            'colleague': '同事',
                            'mentor': '导师',
                            'classmate': '同学'
                        }
                        
                        if missing_categories:
                            missing_display = '、'.join([category_display.get(c, c) for c in missing_categories])
                            recommendations.append({
                                "priority": "medium",
                                "category": "关系平衡",
                                "action": f"当前人际关系类型较为集中，建议拓展{missing_display}类关系",
                                "expected_impact": "丰富人际网络结构，获得多元化支持",
                                "timeline": "3-6个月",
                                "data_source": "category_distribution"
                            })
            
            elif finding_type == 'connection_density':
                # 关系密度发现 -> 互动建议
                density = finding.get('density', 0)
                if density < 0.1:
                    recommendations.append({
                        "priority": "high",
                        "category": "关系维护",
                        "action": "当前人际网络中互动较少，建议定期组织聚会或活动，促进人物之间的联系",
                        "expected_impact": "提升关系密度和网络凝聚力",
                        "timeline": "1-3个月",
                        "data_source": "connection_density"
                    })
                elif density > 0.3:
                    recommendations.append({
                        "priority": "low",
                        "category": "关系深化",
                        "action": "当前人际网络较为紧密，建议在现有基础上深化核心关系",
                        "expected_impact": "建立更深层次的信任和合作",
                        "timeline": "持续进行",
                        "data_source": "connection_density"
                    })
            
            elif finding_type == 'influence_analysis':
                # 影响力分析 -> 决策建议
                factor = finding.get('factor', '')
                if factor:
                    recommendations.append({
                        "priority": "medium",
                        "category": "决策优化",
                        "action": f"在人际关系决策中，{factor}影响最大，建议在此基础上综合考虑其他因素",
                        "expected_impact": "做出更全面的人际关系决策",
                        "timeline": "随时应用",
                        "data_source": "influence_analysis"
                    })
        
        # 2. 基于网络规模和连接密度的通用建议
        if network_size > 0 and connection_count < network_size * 0.3:
            recommendations.append({
                "priority": "medium",
                "category": "互动频率",
                "action": "建议加强现有关系的互动频率，每周至少联系2-3位重要人物",
                "expected_impact": "提升关系质量和稳定性",
                "timeline": "持续进行",
                "data_source": "general_analysis"
            })
        
        # 3. 核心关系培养建议（通用）
        if network_size >= 5:
            recommendations.append({
                "priority": "medium",
                "category": "核心关系",
                "action": "识别并培养3-5个核心关系，投入更多时间和精力深度交流",
                "expected_impact": "建立深度信任关系，获得关键支持",
                "timeline": "3-6个月",
                "data_source": "general"
            })
        
        # 4. 如果没有足够的数据
        if len(recommendations) < 2:
            recommendations.append({
                "priority": "medium",
                "category": "信息收集",
                "action": "建议多与我交流你的人际关系情况，包括朋友、同事、家人等，以便提供更精准的建议",
                "expected_impact": "获得个性化人际关系指导",
                "timeline": "随时进行",
                "data_source": "general"
            })
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))
        
        return recommendations[:5]  # 最多返回5条建议
    
    def _analyze_relationship_decision_logic(self, rag_data: Dict, neo4j_data: Dict) -> Dict[str, Any]:
        """分析人际关系决策逻辑"""
        return {
            "reasoning_path": [
                {"step": 1, "description": "分析现有关系网络规模和质量"},
                {"step": 2, "description": "识别关键人物和影响力节点"},
                {"step": 3, "description": "评估关系互动频率和深度"},
                {"step": 4, "description": "发现潜在的关系机会和风险"}
            ],
            "influence_factors": rag_data.get('influence_summary', {}),
            "data_quality": {
                "rag_coverage": len(rag_data.get('nodes', [])) / 15,
                "neo4j_coverage": len(neo4j_data.get('nodes', [])) / 25
            }
        }



class EducationInsightAgent(BaseInsightAgent):
    """
    教育升学洞察Agent
    专注于分析升学路径、学校选择、专业匹配、学业规划等
    """
    
    def __init__(self, user_id: str):
        super().__init__(user_id, "education", "教育升学")
    
    def generate_insight_report(
        self,
        query: str = "分析我的升学路径",
        target_school: Optional[str] = None,
        target_major: Optional[str] = None
    ) -> InsightReport:
        """
        生成教育升学洞察报告
        
        Args:
            query: 分析查询
            target_school: 目标学校
            target_major: 目标专业
        """
        self._ensure_connections()
        
        print(f"\n{'='*60}")
        print(f"[教育升学Agent] 开始生成洞察报告")
        print(f"  查询: {query}")
        print(f"  目标学校: {target_school or '未指定'}")
        print(f"  目标专业: {target_major or '未指定'}")
        print(f"{'='*60}\n")
        
        # 使用统一混合检索
        print("🔍 步骤1: 混合检索（RAG + Neo4j）...")
        hybrid_data = self._retrieve_hybrid(
            query=query,
            max_nodes=30,
            category="education"
        )
        
        # 为了兼容旧代码，分离数据
        rag_data = {
            "nodes": [n for n in hybrid_data["nodes"] if n.get("source") in ["vector", "hybrid"]],
            "relationships": hybrid_data["relationships"],
            "reasoning_path": hybrid_data["reasoning_path"],
            "influence_summary": hybrid_data["influence_summary"]
        }
        
        neo4j_data = {
            "nodes": [n for n in hybrid_data["nodes"] if n.get("source") in ["graph", "hybrid"]],
            "relationships": hybrid_data["relationships"]
        }
        
        print(f"  ✓ 混合检索完成: 总计{len(hybrid_data['nodes'])}个节点")
        print(f"    - 图检索: {hybrid_data['stats']['graph']}个")
        print(f"    - 向量检索: {hybrid_data['stats']['vector']}个")
        print(f"    - 执行时间: {hybrid_data['stats']['execution_time_ms']:.2f}ms")
        
        # 3. 生成洞察
        print("\n🧠 步骤2: LLM生成深度洞察...")
        domain_context = f"""
教育升学领域分析重点：
- 学业成绩和学术能力评估
- 目标学校和专业的匹配度
- 升学路径的可行性分析
- 竞争力和差距分析
- 提升策略和时间规划
{f'- 目标学校: {target_school}' if target_school else ''}
{f'- 目标专业: {target_major}' if target_major else ''}
"""
        
        insight_summary = self._generate_insight_with_llm(
            query, rag_data, neo4j_data, domain_context
        )
        
        # 4. 提取关键发现
        key_findings = self._extract_education_findings(rag_data, neo4j_data)
        
        # 5. 生成建议
        recommendations = self._generate_education_recommendations(
            key_findings, target_school, target_major
        )
        
        # 6. 决策逻辑分析
        decision_logic = self._analyze_education_decision_logic(rag_data, neo4j_data)
        
        report = InsightReport(
            insight_id=f"education_{datetime.now().timestamp()}",
            agent_type="education",
            title=f"教育升学洞察报告 - {target_school or target_major or '综合分析'}",
            summary=insight_summary,
            key_findings=key_findings,
            recommendations=recommendations,
            decision_logic=decision_logic,
            data_sources={
                "rag_nodes": len(rag_data.get('nodes', [])),
                "neo4j_nodes": len(neo4j_data.get('nodes', [])),
                "hybrid_retrieval": True
            },
            confidence_score=self._calculate_confidence(rag_data, neo4j_data),
            generated_at=datetime.now()
        )
        
        print(f"\n✅ 教育升学洞察报告生成完成")
        print(f"  关键发现: {len(key_findings)} 个")
        print(f"  建议: {len(recommendations)} 条")
        print(f"  置信度: {report.confidence_score:.2f}")
        print(f"{'='*60}\n")
        
        return report
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行教育升学分析（协作模式）
        
        Args:
            input_data: {
                "query": 用户查询,
                "hybrid_data": 共享的混合检索数据,
                "prev_agent_output": 上一个Agent的输出（如果有）,
                "context": 任务链上下文
            }
        
        Returns:
            {
                "agent_name": "education",
                "summary": "摘要",
                "key_findings": [...],
                "ml_evaluation": {...},
                "recommendations": [...],
                "confidence_score": 0.8
            }
        """
        print(f"\n{'='*60}")
        print(f"[{self.name}] 开始执行任务")
        print(f"{'='*60}\n")
        
        query = input_data.get("query", "分析我的教育升学路径")
        hybrid_data = input_data.get("hybrid_data", {})
        prev_output = input_data.get("prev_agent_output")
        
        # 设置状态为工作中
        self.status = AgentStatus.WORKING
        if self.gateway:
            self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.WORKING)
        
        start_time = datetime.now()
        layer_timing = {}
        
        try:
            # 数据整合
            neo4j_data = {
                "nodes": hybrid_data.get("nodes", []),
                "relationships": hybrid_data.get("relationships", [])
            }
            
            rag_data = {
                "nodes": hybrid_data.get("nodes", []),
                "relationships": hybrid_data.get("relationships", []),
                "influence_summary": hybrid_data.get("influence_summary", {}),
                "stats": hybrid_data.get("stats", {})
            }
            
            # 统计不同来源的节点数
            all_nodes = hybrid_data.get("nodes", [])
            neo4j_node_count = len([n for n in all_nodes if n.get("source") in ["neo4j", "graph", "hybrid"]])
            rag_node_count = len([n for n in all_nodes if n.get("source") in ["faiss", "vector", "hybrid"]])
            
            # 第1层：规则引擎
            print("📊 第1层：规则引擎分析...")
            layer1_start = datetime.now()
            key_findings = self._extract_education_findings(rag_data, neo4j_data)
            layer_timing["layer1_ms"] = (datetime.now() - layer1_start).total_seconds() * 1000
            print(f"  ✓ 完成，发现 {len(key_findings)} 个关键点，耗时 {layer_timing['layer1_ms']:.2f}ms")
            
            # 第2层：机器学习评估
            print("🤖 第2层：机器学习评估...")
            layer2_start = datetime.now()
            ml_evaluation = self._layer2_ml_evaluation(rag_data, neo4j_data, key_findings)
            layer_timing["layer2_ms"] = (datetime.now() - layer2_start).total_seconds() * 1000
            print(f"  ✓ 完成，耗时 {layer_timing['layer2_ms']:.2f}ms")
            
            # 第3层：LLM深度解读
            print("🧠 第3层：LLM深度解读...")
            layer3_start = datetime.now()
            domain_context = """
教育升学领域分析重点：
- 学业成绩和学术能力评估
- 目标学校和专业的匹配度
- 升学路径的可行性分析
- 竞争力和差距分析
- 提升策略和时间规划
"""
            llm_output = self._layer3_llm_deep_insight(
                query, rag_data, neo4j_data, key_findings, ml_evaluation, domain_context
            )
            layer_timing["layer3_ms"] = (datetime.now() - layer3_start).total_seconds() * 1000
            print(f"  ✓ 完成，生成 {len(llm_output.get('recommendations', []))} 条建议，耗时 {layer_timing['layer3_ms']:.2f}ms")
            
            # 构建输出
            output = {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "summary": llm_output.get("summary", ""),
                "key_findings": key_findings,
                "ml_evaluation": ml_evaluation,
                "recommendations": llm_output.get("recommendations", []),
                "confidence_score": self._calculate_confidence(rag_data, neo4j_data),
                "layer_timing": layer_timing,
                "data_sources": {
                    "rag_nodes": rag_node_count,
                    "neo4j_nodes": neo4j_node_count
                },
                "debug_info": {
                    "hybrid_data_nodes": len(hybrid_data.get('nodes', [])),
                    "neo4j_data_nodes": len(neo4j_data.get('nodes', [])),
                    "rag_data_nodes": len(rag_data.get('nodes', [])),
                    "all_node_types": list(set([n.get('type') or n.get('node_type', 'unknown') for n in hybrid_data.get('nodes', [])])),
                    "school_node_count": len([n for n in hybrid_data.get('nodes', []) if (n.get('type') or n.get('node_type')) == 'School']),
                    "sample_nodes": [
                        {
                            "type": n.get('type'),
                            "node_type": n.get('node_type'),
                            "name": n.get('name'),
                            "content_preview": n.get('content', '')[:50],
                            "source": n.get('source'),
                            "category": n.get('category')
                        }
                        for n in hybrid_data.get('nodes', [])[:5]
                    ]
                }
            }
            
            # 设置状态为完成
            self.status = AgentStatus.COMPLETED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.COMPLETED)
            
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            print(f"\n✅ [{self.name}] 任务完成，总耗时: {total_time:.2f}ms")
            
            return output
            
        except Exception as e:
            print(f"\n❌ [{self.name}] 执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 设置状态为失败
            self.status = AgentStatus.FAILED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.FAILED)
            
            # 返回降级输出
            return {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "summary": f"分析过程中出现错误: {str(e)}",
                "key_findings": [],
                "ml_evaluation": {},
                "recommendations": [],
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_education_findings(
        self,
        rag_data: Dict,
        neo4j_data: Dict,
        user_academic_data: Dict = None
    ) -> List[Dict[str, Any]]:
        """提取教育升学关键发现 - 基于实际检索数据"""
        findings = []
        
        if user_academic_data is None:
            user_academic_data = {}
        
        # 1. 分析检索到的学校数据
        neo4j_nodes = neo4j_data.get('nodes', [])
        if neo4j_nodes:
            # 统计学校类型分布
            school_types = {}
            top_schools = []
            
            for node in neo4j_nodes[:10]:  # 分析前10所学校
                school_name = node.get('name', '')
                confidence = node.get('confidence', 0)
                category = node.get('category', 'unknown')
                
                # 统计类型
                school_types[category] = school_types.get(category, 0) + 1
                
                # 收集高置信度学校
                if confidence > 0.6:
                    top_schools.append(school_name)
            
            findings.append({
                "type": "school_analysis",
                "title": f"识别到 {len(neo4j_nodes)} 所相关学校",
                "description": f"高匹配度学校: {', '.join(top_schools[:5]) if top_schools else '暂无'}。类型分布: {', '.join([f'{k}({v}所)' for k, v in school_types.items()])}",
                "importance": "high",
                "data": {
                    "total": len(neo4j_nodes),
                    "high_match": len(top_schools),
                    "types": school_types
                }
            })
        
        # 2. 分析RAG记忆中的教育相关内容
        rag_nodes = rag_data.get('nodes', [])
        if rag_nodes:
            # 提取关键主题
            topics = {}
            for node in rag_nodes:
                category = node.get('category', 'general')
                topics[category] = topics.get(category, 0) + 1
            
            # 找出最关注的主题
            if topics:
                top_topic = max(topics.items(), key=lambda x: x[1])
                findings.append({
                    "type": "interest_analysis",
                    "title": f"教育兴趣分析: 主要关注 {top_topic[0]}",
                    "description": f"从历史记录中发现你对{top_topic[0]}相关内容提及{top_topic[1]}次，这可能影响你的升学选择",
                    "importance": "medium",
                    "data": {
                        "topics": topics,
                        "top_topic": top_topic[0]
                    }
                })
        
        # 3. 分析关系网络
        relationships = neo4j_data.get('relationships', [])
        if relationships:
            rel_types = {}
            for rel in relationships:
                rel_type = rel.get('type', 'RELATED_TO')
                rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
            
            findings.append({
                "type": "relationship_analysis",
                "title": f"发现 {len(relationships)} 个相关连接",
                "description": f"关系类型: {', '.join([f'{k}({v})' for k, v in rel_types.items()])}",
                "importance": "low",
                "data": rel_types
            })
        
        # 4. 影响力分析
        influence_summary = rag_data.get('influence_summary', {})
        if influence_summary:
            sorted_factors = sorted(influence_summary.items(), key=lambda x: x[1], reverse=True)
            if sorted_factors:
                top_3 = sorted_factors[:3]
                findings.append({
                    "type": "influence_factors",
                    "title": "关键影响因素",
                    "description": f"前三大影响因素: {', '.join([f'{k}({v*100:.0f}%)' for k, v in top_3])}",
                    "importance": "high",
                    "data": dict(sorted_factors)
                })
        
        return findings if findings else [{
            "type": "no_data",
            "title": "数据不足",
            "description": "暂无足够的教育相关数据进行分析",
            "importance": "low"
        }]
    
    def _generate_education_recommendations(
        self,
        key_findings: List[Dict],
        target_school: Optional[str] = None,
        target_major: Optional[str] = None,
        user_academic_data: Dict = None
    ) -> List[Dict[str, Any]]:
        """
        生成教育升学建议 - 基于实际检索数据动态生成
        
        数据来源：
        - key_findings: 从混合检索中提取的关键发现
        - target_school/target_major: 用户目标
        - user_academic_data: 用户学术数据（从检索结果中提取）
        """
        recommendations = []
        
        if user_academic_data is None:
            user_academic_data = {}
        
        # 1. 基于关键发现生成建议
        for finding in key_findings:
            finding_type = finding.get('type', '')
            
            # 根据不同类型的发现生成针对性建议
            if finding_type == 'school_distribution':
                # 院校分布发现 -> 建议拓展选择范围
                school_count = finding.get('count', 0)
                if school_count < 5:
                    recommendations.append({
                        "priority": "high",
                        "category": "选校策略",
                        "action": f"当前关注{school_count}所院校，建议扩展到8-10所不同层次的学校",
                        "expected_impact": "降低申请风险，提高录取概率",
                        "timeline": "申请季前1-2个月",
                        "data_source": "school_distribution_analysis"
                    })
                elif school_count > 15:
                    recommendations.append({
                        "priority": "medium",
                        "category": "选校优化",
                        "action": f"当前关注{school_count}所院校较多，建议聚焦5-8所最匹配的学校",
                        "expected_impact": "提高申请质量，节省时间精力",
                        "timeline": "申请季前",
                        "data_source": "school_distribution_analysis"
                    })
            
            elif finding_type == 'school_tier_analysis':
                # 院校层次分析 -> 建议平衡选校
                tier_distribution = finding.get('tier_distribution', {})
                if tier_distribution:
                    top_tier_count = tier_distribution.get('top', 0)
                    mid_tier_count = tier_distribution.get('mid', 0)
                    safe_tier_count = tier_distribution.get('safe', 0)
                    
                    if top_tier_count > mid_tier_count + safe_tier_count:
                        recommendations.append({
                            "priority": "high",
                            "category": "选校平衡",
                            "action": "当前过于关注顶尖院校，建议增加2-3所匹配院校和1-2所保底院校",
                            "expected_impact": "确保有学可上，降低申请风险",
                            "timeline": "立即调整",
                            "data_source": "tier_analysis"
                        })
                    elif safe_tier_count == 0:
                        recommendations.append({
                            "priority": "medium",
                            "category": "保底选择",
                            "action": "建议添加1-2所保底院校，确保申请安全",
                            "expected_impact": "降低申请风险",
                            "timeline": "申请季前",
                            "data_source": "tier_analysis"
                        })
            
            elif finding_type == 'major_focus':
                # 专业关注度 -> 建议深入了解
                major_name = finding.get('major', '')
                if major_name:
                    recommendations.append({
                        "priority": "medium",
                        "category": "专业准备",
                        "action": f"针对{major_name}专业，建议深入了解课程设置、就业前景和申请要求",
                        "expected_impact": "提高申请针对性和成功率",
                        "timeline": "申请季前3-6个月",
                        "data_source": "major_analysis"
                    })
            
            elif finding_type == 'event_activity':
                # 活动事件 -> 建议参与类似活动
                event_count = finding.get('count', 0)
                if event_count < 3:
                    recommendations.append({
                        "priority": "high",
                        "category": "背景提升",
                        "action": "当前学术活动较少，建议参与2-3个科研项目、竞赛或实习",
                        "expected_impact": "丰富申请背景，增强竞争力",
                        "timeline": "持续进行",
                        "data_source": "activity_analysis"
                    })
        
        # 2. 基于目标院校生成建议
        if target_school:
            recommendations.append({
                "priority": "high",
                "category": "目标准备",
                "action": f"针对目标院校{target_school}，建议研究其录取要求、申请材料和面试流程",
                "expected_impact": "提高目标院校录取概率",
                "timeline": "申请季前3-6个月",
                "data_source": "target_school"
            })
        
        # 3. 基于目标专业生成建议
        if target_major:
            recommendations.append({
                "priority": "high",
                "category": "专业匹配",
                "action": f"针对{target_major}专业，建议准备相关课程成绩、项目经验和推荐信",
                "expected_impact": "提高专业匹配度",
                "timeline": "申请季前",
                "data_source": "target_major"
            })
        
        # 4. 基于用户学术数据生成建议
        gpa = user_academic_data.get('gpa', 0)
        if gpa > 0:
            if gpa < 3.0:
                recommendations.append({
                    "priority": "high",
                    "category": "学业提升",
                    "action": f"当前GPA {gpa:.2f}偏低，建议重点提升到3.0以上",
                    "expected_impact": "达到基本申请门槛",
                    "timeline": "1-2学期",
                    "data_source": "academic_data"
                })
            elif gpa < 3.5:
                recommendations.append({
                    "priority": "medium",
                    "category": "学业优化",
                    "action": f"当前GPA {gpa:.2f}，建议提升到3.5以上以增强竞争力",
                    "expected_impact": "提高申请竞争力",
                    "timeline": "1-2学期",
                    "data_source": "academic_data"
                })
        
        # 5. 通用建议（如果没有足够的数据）
        if len(recommendations) < 2:
            recommendations.append({
                "priority": "medium",
                "category": "信息收集",
                "action": "建议多与我交流你的升学想法、目标院校和专业偏好，以便提供更精准的建议",
                "expected_impact": "获得个性化升学指导",
                "timeline": "随时进行",
                "data_source": "general"
            })
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))
        
        return recommendations[:5]  # 最多返回5条建议
    
    def _analyze_education_decision_logic(
        self,
        rag_data: Dict,
        neo4j_data: Dict,
        user_academic_data: Dict = None
    ) -> Dict[str, Any]:
        """分析教育升学决策逻辑"""
        if user_academic_data is None:
            user_academic_data = {}
        
        return {
            "reasoning_path": [
                {"step": 1, "description": "评估当前学业水平和竞争力"},
                {"step": 2, "description": "分析目标学校和专业的匹配度"},
                {"step": 3, "description": "识别提升空间和关键短板"},
                {"step": 4, "description": "制定分层申请策略"}
            ],
            "influence_factors": rag_data.get('influence_summary', {}),
            "academic_metrics": {
                "gpa": user_academic_data.get('gpa', 0),
                "academic_score": user_academic_data.get('academic_score', 0)
            },
            "data_quality": {
                "rag_coverage": len(rag_data.get('nodes', [])) / 15,
                "neo4j_coverage": len(neo4j_data.get('nodes', [])) / 25
            }
        }



class CareerInsightAgent(BaseInsightAgent):
    """
    职业规划洞察Agent
    专注于分析职业发展路径、技能匹配、岗位选择、职业规划等
    """
    
    def __init__(self, user_id: str):
        super().__init__(user_id, "career", "职业规划")
    
    def generate_insight_report(
        self,
        query: str = "分析我的职业发展路径",
        target_position: Optional[str] = None,
        target_industry: Optional[str] = None
    ) -> InsightReport:
        """
        生成职业规划洞察报告
        
        Args:
            query: 分析查询
            target_position: 目标职位
            target_industry: 目标行业
        """
        self._ensure_connections()
        
        print(f"\n{'='*60}")
        print(f"[职业规划Agent] 开始生成洞察报告")
        print(f"  查询: {query}")
        print(f"  目标职位: {target_position or '未指定'}")
        print(f"  目标行业: {target_industry or '未指定'}")
        print(f"{'='*60}\n")
        
        # 构建增强查询
        search_query = query
        if target_position:
            search_query += f" {target_position}"
        if target_industry:
            search_query += f" {target_industry}"
        
        # 使用统一混合检索
        print("🔍 步骤1: 混合检索（RAG + Neo4j）...")
        hybrid_data = self._retrieve_hybrid(
            query=search_query,
            max_nodes=30,
            category="career"
        )
        
        # 为了兼容旧代码，分离数据
        rag_data = {
            "nodes": [n for n in hybrid_data["nodes"] if n.get("source") in ["vector", "hybrid"]],
            "relationships": hybrid_data["relationships"],
            "reasoning_path": hybrid_data["reasoning_path"],
            "influence_summary": hybrid_data["influence_summary"]
        }
        
        neo4j_data = {
            "nodes": [n for n in hybrid_data["nodes"] if n.get("source") in ["graph", "hybrid"]],
            "relationships": hybrid_data["relationships"]
        }
        
        print(f"  ✓ 混合检索完成: 总计{len(hybrid_data['nodes'])}个节点")
        print(f"    - 图检索: {hybrid_data['stats']['graph']}个")
        print(f"    - 向量检索: {hybrid_data['stats']['vector']}个")
        print(f"    - 执行时间: {hybrid_data['stats']['execution_time_ms']:.2f}ms")
        
        # 3. 生成洞察
        print("\n🧠 步骤2: LLM生成深度洞察...")
        domain_context = f"""
职业规划领域分析重点：
- 技能匹配度和竞争力评估
- 职业发展路径和晋升空间
- 目标职位的要求和差距
- 行业趋势和机会分析
- 技能提升和转型策略
{f'- 目标职位: {target_position}' if target_position else ''}
{f'- 目标行业: {target_industry}' if target_industry else ''}
"""
        
        insight_summary = self._generate_insight_with_llm(
            query, rag_data, neo4j_data, domain_context
        )
        
        # 4. 提取关键发现
        key_findings = self._extract_career_findings(rag_data, neo4j_data)
        
        # 5. 生成建议
        recommendations = self._generate_career_recommendations(
            key_findings, target_position, target_industry
        )
        
        # 6. 决策逻辑分析
        decision_logic = self._analyze_career_decision_logic(rag_data, neo4j_data)
        
        report = InsightReport(
            insight_id=f"career_{datetime.now().timestamp()}",
            agent_type="career",
            title=f"职业规划洞察报告 - {target_position or target_industry or '综合分析'}",
            summary=insight_summary,
            key_findings=key_findings,
            recommendations=recommendations,
            decision_logic=decision_logic,
            data_sources={
                "rag_nodes": len(rag_data.get('nodes', [])),
                "neo4j_nodes": len(neo4j_data.get('nodes', []))
            },
            confidence_score=self._calculate_confidence(rag_data, neo4j_data),
            generated_at=datetime.now()
        )
        
        print(f"\n✅ 职业规划洞察报告生成完成")
        print(f"  关键发现: {len(key_findings)} 个")
        print(f"  建议: {len(recommendations)} 条")
        print(f"  置信度: {report.confidence_score:.2f}")
        print(f"{'='*60}\n")
        
        return report
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行职业规划分析（协作模式）
        
        Args:
            input_data: {
                "query": 用户查询,
                "hybrid_data": 共享的混合检索数据,
                "prev_agent_output": 上一个Agent的输出（如果有）,
                "context": 任务链上下文
            }
        
        Returns:
            {
                "agent_name": "career",
                "summary": "摘要",
                "key_findings": [...],
                "ml_evaluation": {...},
                "recommendations": [...],
                "confidence_score": 0.8
            }
        """
        print(f"\n{'='*60}")
        print(f"[{self.name}] 开始执行任务")
        print(f"{'='*60}\n")
        
        query = input_data.get("query", "分析我的职业发展路径")
        hybrid_data = input_data.get("hybrid_data", {})
        prev_output = input_data.get("prev_agent_output")
        
        # 设置状态为工作中
        self.status = AgentStatus.WORKING
        if self.gateway:
            self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.WORKING)
        
        start_time = datetime.now()
        layer_timing = {}
        
        try:
            # 数据整合
            neo4j_data = {
                "nodes": hybrid_data.get("nodes", []),
                "relationships": hybrid_data.get("relationships", [])
            }
            
            rag_data = {
                "nodes": hybrid_data.get("nodes", []),
                "relationships": hybrid_data.get("relationships", []),
                "influence_summary": hybrid_data.get("influence_summary", {}),
                "stats": hybrid_data.get("stats", {})
            }
            
            # 统计不同来源的节点数
            all_nodes = hybrid_data.get("nodes", [])
            neo4j_node_count = len([n for n in all_nodes if n.get("source") in ["neo4j", "graph", "hybrid"]])
            rag_node_count = len([n for n in all_nodes if n.get("source") in ["faiss", "vector", "hybrid"]])
            
            # 第1层：规则引擎
            print("📊 第1层：规则引擎分析...")
            layer1_start = datetime.now()
            key_findings = self._extract_career_findings(rag_data, neo4j_data)
            layer_timing["layer1_ms"] = (datetime.now() - layer1_start).total_seconds() * 1000
            print(f"  ✓ 完成，发现 {len(key_findings)} 个关键点，耗时 {layer_timing['layer1_ms']:.2f}ms")
            
            # 第2层：机器学习评估
            print("🤖 第2层：机器学习评估...")
            layer2_start = datetime.now()
            ml_evaluation = self._layer2_ml_evaluation(rag_data, neo4j_data, key_findings)
            layer_timing["layer2_ms"] = (datetime.now() - layer2_start).total_seconds() * 1000
            print(f"  ✓ 完成，耗时 {layer_timing['layer2_ms']:.2f}ms")
            
            # 第3层：LLM深度解读
            print("🧠 第3层：LLM深度解读...")
            layer3_start = datetime.now()
            domain_context = """
职业规划领域分析重点：
- 技能匹配度和竞争力评估
- 职业发展路径和晋升空间
- 目标职位的要求和差距
- 行业趋势和机会分析
- 技能提升和转型策略
"""
            llm_output = self._layer3_llm_deep_insight(
                query, rag_data, neo4j_data, key_findings, ml_evaluation, domain_context
            )
            layer_timing["layer3_ms"] = (datetime.now() - layer3_start).total_seconds() * 1000
            print(f"  ✓ 完成，生成 {len(llm_output.get('recommendations', []))} 条建议，耗时 {layer_timing['layer3_ms']:.2f}ms")
            
            # 构建输出
            output = {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "summary": llm_output.get("summary", ""),
                "key_findings": key_findings,
                "ml_evaluation": ml_evaluation,
                "recommendations": llm_output.get("recommendations", []),
                "confidence_score": self._calculate_confidence(rag_data, neo4j_data),
                "layer_timing": layer_timing,
                "data_sources": {
                    "rag_nodes": rag_node_count,
                    "neo4j_nodes": neo4j_node_count
                },
                "debug_info": {
                    "hybrid_data_nodes": len(hybrid_data.get('nodes', [])),
                    "neo4j_data_nodes": len(neo4j_data.get('nodes', [])),
                    "rag_data_nodes": len(rag_data.get('nodes', [])),
                    "all_node_types": list(set([n.get('type') or n.get('node_type', 'unknown') for n in hybrid_data.get('nodes', [])])),
                    "job_node_count": len([n for n in hybrid_data.get('nodes', []) if (n.get('type') or n.get('node_type')) == 'Job']),
                    "sample_nodes": [
                        {
                            "type": n.get('type'),
                            "node_type": n.get('node_type'),
                            "name": n.get('name'),
                            "content_preview": n.get('content', '')[:50],
                            "source": n.get('source'),
                            "category": n.get('category')
                        }
                        for n in hybrid_data.get('nodes', [])[:5]
                    ]
                }
            }
            
            # 设置状态为完成
            self.status = AgentStatus.COMPLETED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.COMPLETED)
            
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            print(f"\n✅ [{self.name}] 任务完成，总耗时: {total_time:.2f}ms")
            
            return output
            
        except Exception as e:
            print(f"\n❌ [{self.name}] 执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 设置状态为失败
            self.status = AgentStatus.FAILED
            if self.gateway:
                self.gateway.shared_memory.set_agent_status(self.name, AgentStatus.FAILED)
            
            # 返回降级输出
            return {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "summary": f"分析过程中出现错误: {str(e)}",
                "key_findings": [],
                "ml_evaluation": {},
                "recommendations": [],
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _get_user_skill_data(self) -> Dict[str, Any]:
        """获取用户技能数据"""
        # 这里可以从数据库或其他来源获取用户技能
        # 暂时返回模拟数据
        return {
            "mastered_skills": ["Python", "JavaScript", "SQL"],
            "partial_skills": ["React", "Docker"],
            "missing_skills": ["Kubernetes", "AWS"]
        }
    
    def _extract_career_findings(
        self,
        rag_data: Dict,
        neo4j_data: Dict
    ) -> List[Dict[str, Any]]:
        """
        提取职业规划关键发现 - 基于实际检索数据动态生成
        
        数据来源：
        - neo4j_data['nodes']: Entity(type='Job') 节点列表
        - neo4j_data['relationships']: 岗位之间的关系
        - rag_data['influence_summary']: 影响力分析
        """
        findings = []
        
        neo4j_nodes = neo4j_data.get('nodes', [])
        relationships = neo4j_data.get('relationships', [])
        influence_summary = rag_data.get('influence_summary', {})
        
        # 1. 岗位机会统计
        job_nodes = [n for n in neo4j_nodes if n.get('type') == 'Job']
        job_names = [n.get('name', '') for n in job_nodes]
        job_categories = {}
        
        for node in job_nodes:
            category = node.get('category', 'unknown')
            job_categories[category] = job_categories.get(category, 0) + 1
        
        total_jobs = len(job_nodes)
        if total_jobs > 0:
            # 根据岗位数量给出不同的发现
            if total_jobs >= 20:
                findings.append({
                    "type": "job_opportunities",
                    "title": f"职位机会: {total_jobs} 个匹配岗位（丰富）",
                    "description": f"识别到{total_jobs}个潜在匹配岗位，职业选择空间较大，建议聚焦3-5个最感兴趣的方向",
                    "importance": "high",
                    "count": total_jobs,
                    "job_sample": job_names[:5]
                })
            elif total_jobs >= 10:
                findings.append({
                    "type": "job_opportunities",
                    "title": f"职位机会: {total_jobs} 个匹配岗位（适中）",
                    "description": f"识别到{total_jobs}个潜在匹配岗位，可以进一步了解各岗位的要求和发展前景",
                    "importance": "medium",
                    "count": total_jobs,
                    "job_sample": job_names[:5]
                })
            else:
                findings.append({
                    "type": "job_opportunities",
                    "title": f"职位机会: {total_jobs} 个匹配岗位（较少）",
                    "description": f"识别到{total_jobs}个潜在匹配岗位，建议拓展职业探索范围，了解更多可能性",
                    "importance": "high",
                    "count": total_jobs,
                    "job_sample": job_names
                })
        
        # 2. 岗位类别分布分析
        if job_categories:
            # 找出最多的类别
            top_category = max(job_categories.items(), key=lambda x: x[1])
            category_name, category_count = top_category
            
            # 类别名称映射
            category_display = {
                'position': '技术岗位',
                'management': '管理岗位',
                'research': '研发岗位',
                'unknown': '其他岗位'
            }
            display_name = category_display.get(category_name, category_name)
            
            findings.append({
                "type": "job_category_distribution",
                "title": f"岗位类型分布: {display_name}占主导",
                "description": f"你关注的岗位中，{display_name}最多（{category_count}个），占比{category_count/total_jobs*100:.1f}%。" +
                              (f"建议也了解其他类型的岗位" if category_count/total_jobs > 0.7 else "岗位类型分布较为均衡"),
                "importance": "medium",
                "distribution": job_categories
            })
        
        # 3. 技能匹配分析（从节点metadata中提取）
        skill_mentions = {}
        for node in job_nodes:
            metadata = node.get('metadata', {})
            required_skills = metadata.get('required_skills', [])
            for skill in required_skills:
                skill_mentions[skill] = skill_mentions.get(skill, 0) + 1
        
        if skill_mentions:
            # 找出最常见的技能要求
            top_skills = sorted(skill_mentions.items(), key=lambda x: x[1], reverse=True)[:5]
            skill_list = [f"{skill}({count}次)" for skill, count in top_skills]
            
            findings.append({
                "type": "skill_requirements",
                "title": f"核心技能要求: {', '.join([s[0] for s in top_skills[:3]])}",
                "description": f"在关注的岗位中，最常见的技能要求是：{', '.join(skill_list)}",
                "importance": "high",
                "skills": dict(top_skills)
            })
        
        # 4. 公司分布分析（从节点metadata中提取）
        company_mentions = {}
        for node in job_nodes:
            metadata = node.get('metadata', {})
            company = metadata.get('company', '')
            if company:
                company_mentions[company] = company_mentions.get(company, 0) + 1
        
        if company_mentions:
            top_companies = sorted(company_mentions.items(), key=lambda x: x[1], reverse=True)[:5]
            company_list = [f"{company}({count}个岗位)" for company, count in top_companies]
            
            findings.append({
                "type": "company_distribution",
                "title": f"目标公司: {len(company_mentions)} 家公司",
                "description": f"你关注的岗位分布在{len(company_mentions)}家公司，其中{', '.join(company_list[:3])}的岗位最多",
                "importance": "medium",
                "companies": dict(top_companies)
            })
        
        # 5. 影响力分析
        if influence_summary:
            top_factor = max(influence_summary.items(), key=lambda x: x[1])
            factor_name, factor_value = top_factor
            
            findings.append({
                "type": "influence_analysis",
                "title": f"关键影响因素: {factor_name}",
                "description": f"在职业决策中，{factor_name}的影响力最大，占比{factor_value*100:.1f}%",
                "importance": "high",
                "factor": factor_name,
                "value": factor_value
            })
        
        # 6. 职业路径分析（基于关系）
        if relationships:
            # 分析岗位之间的关系（如：初级->中级->高级）
            findings.append({
                "type": "career_path",
                "title": f"职业路径: {len(relationships)} 条发展路径",
                "description": f"识别到{len(relationships)}条可能的职业发展路径，建议规划阶梯式成长",
                "importance": "medium",
                "path_count": len(relationships)
            })
        
        # 7. 如果没有数据，给出提示
        if not findings:
            findings.append({
                "type": "no_data",
                "title": "职业规划数据较少",
                "description": "当前系统中记录的职业相关信息较少，建议多与我交流你的职业目标、感兴趣的岗位和技能，以便提供更精准的分析",
                "importance": "medium"
            })
        
        return findings
    
    def _generate_career_recommendations(
        self,
        key_findings: List[Dict],
        target_position: Optional[str],
        target_industry: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        生成职业规划建议 - 基于实际检索数据动态生成
        
        数据来源：
        - key_findings: 从混合检索中提取的关键发现
        - target_position: 用户目标职位
        - target_industry: 用户目标行业
        """
        recommendations = []
        
        # 1. 基于关键发现生成建议
        for finding in key_findings:
            finding_type = finding.get('type', '')
            
            if finding_type == 'job_opportunities':
                # 岗位机会发现 -> 探索或聚焦建议
                count = finding.get('count', 0)
                if count < 5:
                    recommendations.append({
                        "priority": "high",
                        "category": "职业探索",
                        "action": f"当前关注的岗位较少（{count}个），建议拓展职业探索范围，了解更多可能性",
                        "expected_impact": "发现更多职业机会，避免选择局限",
                        "timeline": "1-2个月",
                        "data_source": "job_opportunities"
                    })
                elif count > 20:
                    recommendations.append({
                        "priority": "medium",
                        "category": "目标聚焦",
                        "action": f"当前关注的岗位较多（{count}个），建议聚焦3-5个最感兴趣的方向深入了解",
                        "expected_impact": "提高求职效率，集中精力准备",
                        "timeline": "立即调整",
                        "data_source": "job_opportunities"
                    })
            
            elif finding_type == 'skill_requirements':
                # 技能要求发现 -> 技能提升建议
                skills = finding.get('skills', {})
                if skills:
                    top_3_skills = list(skills.keys())[:3]
                    recommendations.append({
                        "priority": "high",
                        "category": "技能提升",
                        "action": f"目标岗位最常要求的技能是：{', '.join(top_3_skills)}，建议重点学习和实践",
                        "expected_impact": "提高岗位匹配度和竞争力",
                        "timeline": "3-6个月",
                        "data_source": "skill_requirements"
                    })
            
            elif finding_type == 'company_distribution':
                # 公司分布发现 -> 目标公司准备建议
                companies = finding.get('companies', {})
                if companies:
                    top_companies = list(companies.keys())[:3]
                    recommendations.append({
                        "priority": "medium",
                        "category": "目标公司",
                        "action": f"你关注的公司包括：{', '.join(top_companies)}，建议深入了解这些公司的文化、业务和招聘要求",
                        "expected_impact": "提高面试准备针对性",
                        "timeline": "求职前1-2个月",
                        "data_source": "company_distribution"
                    })
            
            elif finding_type == 'career_path':
                # 职业路径发现 -> 阶梯式发展建议
                path_count = finding.get('path_count', 0)
                if path_count > 0:
                    recommendations.append({
                        "priority": "medium",
                        "category": "职业规划",
                        "action": f"识别到{path_count}条职业发展路径，建议规划短期（1-2年）和长期（3-5年）目标",
                        "expected_impact": "明确职业方向，实现阶梯式成长",
                        "timeline": "持续规划",
                        "data_source": "career_path"
                    })
            
            elif finding_type == 'job_category_distribution':
                # 岗位类别分布 -> 多元化探索建议
                distribution = finding.get('distribution', {})
                if distribution:
                    total = sum(distribution.values())
                    max_category_count = max(distribution.values())
                    if max_category_count / total > 0.7:
                        recommendations.append({
                            "priority": "low",
                            "category": "多元探索",
                            "action": "当前关注的岗位类型较为集中，可以考虑了解其他类型的岗位，拓宽视野",
                            "expected_impact": "发现更多职业可能性",
                            "timeline": "探索阶段",
                            "data_source": "job_category_distribution"
                        })
            
            elif finding_type == 'influence_analysis':
                # 影响力分析 -> 决策建议
                factor = finding.get('factor', '')
                if factor:
                    recommendations.append({
                        "priority": "medium",
                        "category": "决策优化",
                        "action": f"在职业决策中，{factor}影响最大，建议在此基础上综合考虑薪资、发展空间、工作环境等因素",
                        "expected_impact": "做出更全面的职业决策",
                        "timeline": "决策时应用",
                        "data_source": "influence_analysis"
                    })
        
        # 2. 基于目标职位生成建议
        if target_position:
            recommendations.append({
                "priority": "high",
                "category": "目标准备",
                "action": f"针对目标职位{target_position}，建议准备相关项目经验、技术面试和行为面试",
                "expected_impact": "提高目标职位求职成功率",
                "timeline": "求职前1-3个月",
                "data_source": "target_position"
            })
        
        # 3. 基于目标行业生成建议
        if target_industry:
            recommendations.append({
                "priority": "medium",
                "category": "行业了解",
                "action": f"针对目标行业{target_industry}，建议关注行业动态、头部公司和核心技术",
                "expected_impact": "提高行业认知和面试表现",
                "timeline": "持续关注",
                "data_source": "target_industry"
            })
        
        # 4. 通用建议
        if len(recommendations) < 2:
            # 经验积累
            recommendations.append({
                "priority": "medium",
                "category": "经验积累",
                "action": "参与实际项目，积累工作经验和可展示的成果",
                "expected_impact": "增强实战能力和简历竞争力",
                "timeline": "持续进行",
                "data_source": "general"
            })
            
            # 人脉拓展
            recommendations.append({
                "priority": "medium",
                "category": "人脉拓展",
                "action": "参加行业活动、技术分享会，建立职业人脉",
                "expected_impact": "获取内推机会和行业信息",
                "timeline": "持续进行",
                "data_source": "general"
            })
        
        # 5. 如果没有足够的数据
        if len(recommendations) < 2:
            recommendations.append({
                "priority": "medium",
                "category": "信息收集",
                "action": "建议多与我交流你的职业目标、感兴趣的岗位和技能，以便提供更精准的建议",
                "expected_impact": "获得个性化职业规划指导",
                "timeline": "随时进行",
                "data_source": "general"
            })
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))
        
        return recommendations[:5]  # 最多返回5条建议
    
    def _analyze_career_decision_logic(
        self,
        rag_data: Dict,
        neo4j_data: Dict
    ) -> Dict[str, Any]:
        """分析职业规划决策逻辑"""
        return {
            "reasoning_path": [
                {"step": 1, "description": "评估当前技能水平和竞争力"},
                {"step": 2, "description": "分析目标职位的要求和匹配度"},
                {"step": 3, "description": "识别技能差距和提升方向"},
                {"step": 4, "description": "制定职业发展路径和行动计划"}
            ],
            "influence_factors": rag_data.get('influence_summary', {}),
            "data_quality": {
                "rag_coverage": len(rag_data.get('nodes', [])) / 15,
                "neo4j_coverage": len(neo4j_data.get('nodes', [])) / 25
            }
        }


# ==================== 工厂函数 ====================

def get_relationship_agent(user_id: str) -> RelationshipInsightAgent:
    """获取人际关系Agent实例"""
    return RelationshipInsightAgent(user_id)


def get_education_agent(user_id: str) -> EducationInsightAgent:
    """获取教育升学Agent实例"""
    return EducationInsightAgent(user_id)


def get_career_agent(user_id: str) -> CareerInsightAgent:
    """获取职业规划Agent实例"""
    return CareerInsightAgent(user_id)


def get_agent_by_type(user_id: str, agent_type: str) -> BaseInsightAgent:
    """
    根据类型获取Agent实例
    
    Args:
        user_id: 用户ID
        agent_type: Agent类型 (relationship/education/career)
    
    Returns:
        对应的Agent实例
    """
    if agent_type == "relationship":
        return get_relationship_agent(user_id)
    elif agent_type == "education":
        return get_education_agent(user_id)
    elif agent_type == "career":
        return get_career_agent(user_id)
    else:
        raise ValueError(f"未知的Agent类型: {agent_type}")
