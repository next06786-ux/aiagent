"""
知识图谱感知 RAG 系统
将 Neo4j 知识图谱深度融入 RAG 检索 + 生成流程

核心理念:
1. 图谱不仅是存储层，更是推理层
2. 利用图谱的关系结构进行语义检索
3. 将图谱子图转换为结构化上下文
4. 结合向量检索和图检索的双重优势
"""
import os
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# 导入现有的知识图谱系统
from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph


class RetrievalMode(Enum):
    """检索模式"""
    VECTOR_ONLY = "vector_only"           # 仅向量检索
    GRAPH_ONLY = "graph_only"             # 仅图检索
    HYBRID = "hybrid"                     # 混合检索
    GRAPH_FIRST = "graph_first"           # 图优先 + 向量验证


@dataclass
class GraphNode:
    """图谱节点封装"""
    id: str
    name: str
    node_type: str
    category: str
    confidence: float
    metadata: Dict[str, Any]
    influence_score: float = 0.0
    related_nodes: List[str] = None

    def to_text(self) -> str:
        """转换为可读文本"""
        meta_str = ", ".join([f"{k}: {v}" for k, v in list(self.metadata.items())[:5]])
        return f"[{self.node_type}] {self.name} ({self.category}) - 置信度: {self.confidence:.2f}, 影响: {self.influence_score:.2f} | {meta_str}"


@dataclass
class GraphContext:
    """图谱上下文"""
    nodes: List[GraphNode]
    relationships: List[Dict[str, Any]]
    reasoning_path: str  # 推理路径描述
    influence_summary: Dict[str, float]  # 各因素影响力汇总


class KnowledgeGraphAwareRAG:
    """
    知识图谱感知 RAG 系统

    使用方式:
    kg_rag = KnowledgeGraphAwareRAG(user_id="user123")

    # 检索相关上下文
    context = kg_rag.retrieve(
        query="我应该去北京还是上海工作？",
        max_nodes=10,
        mode=RetrievalMode.HYBRID
    )

    # 传入 LLM 生成答案
    answer = llm.chat([
        {"role": "system", "content": f"基于以下知识图谱分析：\n{context.to_prompt()}"},
        {"role": "user", "content": query}
    ])
    """

    def __init__(
        self,
        user_id: str,
        use_vector_search: bool = True,
        use_graph_reasoning: bool = True,
        cache_dir: str = "./data/kg_rag_cache"
    ):
        self.user_id = user_id
        self.use_vector_search = use_vector_search
        self.use_graph_reasoning = use_graph_reasoning

        # 初始化知识图谱连接
        self.kg = InformationKnowledgeGraph(user_id)

        # 初始化向量检索（复用现有的 RAG 系统）
        self.vector_rag = None
        if use_vector_search:
            self._init_vector_rag()

        # 缓存目录
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        print(f"✅ 知识图谱感知 RAG 初始化完成")
        print(f"   用户: {user_id}")
        print(f"   向量检索: {'启用' if use_vector_search else '禁用'}")
        print(f"   图推理: {'启用' if use_graph_reasoning else '禁用'}")

    def _init_vector_rag(self):
        """初始化向量检索组件"""
        try:
            from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType
            self.vector_rag = ProductionRAGSystem(
                user_id=self.user_id,
                storage_path=os.path.join(self.cache_dir, "vectors")
            )
            print(f"   向量维度: {self.vector_rag.embedding_dim}")
        except Exception as e:
            print(f"⚠️  向量检索初始化失败: {e}")
            print(f"   将使用纯图检索模式")
            self.use_vector_search = False

    def retrieve(
        self,
        query: str,
        max_nodes: int = 10,
        mode: RetrievalMode = RetrievalMode.HYBRID,
        include_reasoning: bool = True
    ) -> GraphContext:
        """
        检索知识图谱并构建上下文

        Args:
            query: 用户查询
            max_nodes: 最大节点数
            mode: 检索模式
            include_reasoning: 是否包含推理路径

        Returns:
            GraphContext: 结构化图谱上下文
        """
        if mode == RetrievalMode.VECTOR_ONLY:
            return self._vector_only_retrieve(query, max_nodes)
        elif mode == RetrievalMode.GRAPH_ONLY:
            return self._graph_only_retrieve(query, max_nodes, include_reasoning)
        elif mode == RetrievalMode.HYBRID:
            return self._hybrid_retrieve(query, max_nodes, include_reasoning)
        elif mode == RetrievalMode.GRAPH_FIRST:
            return self._graph_first_retrieve(query, max_nodes, include_reasoning)
        else:
            return self._hybrid_retrieve(query, max_nodes, include_reasoning)

    def _vector_only_retrieve(self, query: str, max_nodes: int) -> GraphContext:
        """仅使用向量检索"""
        if not self.vector_rag:
            return GraphContext(nodes=[], relationships=[], reasoning_path="无向量索引", influence_summary={})

        try:
            from backend.learning.production_rag_system import MemoryType
            memories = self.vector_rag.search(
                query=query,
                memory_types=[MemoryType.KNOWLEDGE, MemoryType.INSIGHT, MemoryType.EXPERIENCE],
                top_k=max_nodes
            )

            nodes = []
            for mem in memories:
                nodes.append(GraphNode(
                    id=mem.id,
                    name=mem.content[:50],
                    node_type=mem.memory_type.value,
                    category=mem.metadata.get('category', 'unknown'),
                    confidence=mem.importance,
                    metadata=mem.metadata,
                    influence_score=mem.importance
                ))

            return GraphContext(
                nodes=nodes,
                relationships=[],
                reasoning_path="基于语义相似度检索",
                influence_summary={"语义相似度": 1.0}
            )
        except Exception as e:
            print(f"向量检索失败: {e}")
            return GraphContext(nodes=[], relationships=[], reasoning_path="向量检索失败", influence_summary={})

    def _graph_only_retrieve(self, query: str, max_nodes: int, include_reasoning: bool) -> GraphContext:
        """仅使用图检索"""
        try:
            # 从查询中提取关键词
            keywords = self._extract_keywords(query)

            # 收集所有相关节点
            all_nodes = []
            all_relationships = []

            for keyword in keywords:
                # 1. 搜索相关节点
                search_results = self.kg.search_information(
                    keyword=keyword,
                    limit=max_nodes // 2
                )

                # 2. 获取每个节点的详细信息和关联
                for result in search_results:
                    node_data = result.get('information', result)
                    if not node_data:
                        continue

                    # 获取相关节点（深度为2）
                    related = self.kg.get_related_information(
                        info_name=node_data.get('name', ''),
                        max_depth=2
                    )

                    # 构建节点对象
                    node = GraphNode(
                        id=node_data.get('id', ''),
                        name=node_data.get('name', ''),
                        node_type=node_data.get('type', 'unknown'),
                        category=node_data.get('category', 'unknown'),
                        confidence=node_data.get('confidence', 0.5),
                        metadata=node_data,
                        influence_score=self._calculate_influence(node_data)
                    )

                    if node not in all_nodes:
                        all_nodes.append(node)

                    # 构建关系
                    for rel in related:
                        rel_data = rel.get('information', {})
                        if rel_data:
                            all_relationships.append({
                                "source": node_data.get('name', ''),
                                "target": rel_data.get('name', ''),
                                "path": " -> ".join(rel.get('path', []))
                            })

            # 按影响力排序
            all_nodes.sort(key=lambda x: x.influence_score, reverse=True)
            all_nodes = all_nodes[:max_nodes]

            # 计算影响力汇总
            influence_summary = self._calculate_influence_summary(all_nodes)

            # 生成推理路径
            reasoning_path = ""
            if include_reasoning:
                reasoning_path = self._generate_reasoning_path(query, all_nodes, keywords)

            return GraphContext(
                nodes=all_nodes,
                relationships=all_relationships[:max_nodes * 2],
                reasoning_path=reasoning_path,
                influence_summary=influence_summary
            )

        except Exception as e:
            print(f"图检索失败: {e}")
            import traceback
            traceback.print_exc()
            return GraphContext(nodes=[], relationships=[], reasoning_path=f"图检索失败: {str(e)}", influence_summary={})

    def _hybrid_retrieve(self, query: str, max_nodes: int, include_reasoning: bool) -> GraphContext:
        """
        混合检索：结合向量和图检索

        策略:
        1. 从图谱中检索相关节点
        2. 用向量搜索验证/补充
        3. 根据影响力合并排序
        """
        # 1. 图检索
        graph_context = self._graph_only_retrieve(query, max_nodes // 2, False)

        # 2. 向量检索（如果有）
        vector_nodes = []
        if self.vector_rag:
            try:
                from backend.learning.production_rag_system import MemoryType
                memories = self.vector_rag.search(
                    query=query,
                    memory_types=[MemoryType.KNOWLEDGE, MemoryType.INSIGHT],
                    top_k=max_nodes // 2
                )

                for mem in memories:
                    vector_nodes.append(GraphNode(
                        id=mem.id,
                        name=mem.content[:50],
                        node_type=mem.memory_type.value,
                        category=mem.metadata.get('category', 'unknown'),
                        confidence=mem.importance,
                        metadata=mem.metadata,
                        influence_score=mem.importance * 0.8  # 向量结果影响力稍低
                    ))
            except Exception as e:
                print(f"向量检索补充失败: {e}")

        # 3. 合并去重（按名称匹配）
        all_nodes = graph_context.nodes.copy()
        for v_node in vector_nodes:
            # 检查是否已存在
            is_duplicate = False
            for g_node in all_nodes:
                if self._is_similar(v_node.name, g_node.name):
                    # 保留影响力更高的
                    if v_node.influence_score > g_node.influence_score:
                        all_nodes.remove(g_node)
                        all_nodes.append(v_node)
                    is_duplicate = True
                    break
            if not is_duplicate:
                all_nodes.append(v_node)

        # 4. 排序并截取
        all_nodes.sort(key=lambda x: x.influence_score, reverse=True)
        all_nodes = all_nodes[:max_nodes]

        # 5. 计算影响力汇总
        influence_summary = self._calculate_influence_summary(all_nodes)

        # 6. 生成推理路径
        reasoning_path = ""
        if include_reasoning:
            reasoning_path = self._generate_reasoning_path(query, all_nodes, self._extract_keywords(query))

        return GraphContext(
            nodes=all_nodes,
            relationships=graph_context.relationships[:max_nodes * 2],
            reasoning_path=reasoning_path,
            influence_summary=influence_summary
        )

    def _graph_first_retrieve(self, query: str, max_nodes: int, include_reasoning: bool) -> GraphContext:
        """
        图优先检索：以知识图谱为主，向量为辅

        适用场景：需要强因果关系推理的查询
        """
        # 1. 先进行图检索，获取因果链
        graph_context = self._graph_only_retrieve(query, max_nodes, include_reasoning)

        # 2. 如果图结果不足，用向量补充
        if len(graph_context.nodes) < max_nodes // 2 and self.vector_rag:
            try:
                from backend.learning.production_rag_system import MemoryType
                memories = self.vector_rag.search(
                    query=query,
                    top_k=max_nodes // 2
                )

                for mem in memories[:max_nodes - len(graph_context.nodes)]:
                    vector_node = GraphNode(
                        id=mem.id,
                        name=mem.content[:50],
                        node_type=mem.memory_type.value,
                        category=mem.metadata.get('category', 'unknown'),
                        confidence=mem.importance,
                        metadata=mem.metadata,
                        influence_score=mem.importance * 0.6  # 向量结果影响力打折
                    )
                    graph_context.nodes.append(vector_node)

                # 重新排序
                graph_context.nodes.sort(key=lambda x: x.influence_score, reverse=True)
            except Exception as e:
                print(f"向量补充失败: {e}")

        # 3. 重新计算影响力汇总
        graph_context.influence_summary = self._calculate_influence_summary(graph_context.nodes)

        return graph_context

    def add_knowledge_to_rag(
        self,
        content: str,
        category: str,
        metadata: Dict[str, Any],
        importance: float = 0.5
    ) -> str:
        """
        添加知识到 RAG 系统

        这会自动:
        1. 存入向量数据库（用于语义检索）
        2. 存入知识图谱（用于关系推理）

        Args:
            content: 知识内容
            category: 分类
            metadata: 元数据
            importance: 重要性

        Returns:
            str: 知识ID
        """
        memory_id = ""

        # 1. 添加到向量数据库
        if self.vector_rag:
            try:
                from backend.learning.production_rag_system import MemoryType
                memory_id = self.vector_rag.add_memory(
                    memory_type=MemoryType.KNOWLEDGE,
                    content=content,
                    metadata={"category": category, **metadata},
                    importance=importance
                )
            except Exception as e:
                print(f"向量存储失败: {e}")

        # 2. 添加到知识图谱
        try:
            info_type = metadata.get('type', 'concept')
            node_id = self.kg.add_information(
                name=content[:100],  # 截断名称
                info_type=info_type,
                category=category,
                confidence=importance,
                attributes=metadata
            )

            # 如果有来源信息，建立关系
            if 'related_to' in metadata:
                self.kg.add_information_relationship(
                    source_name=content[:100],
                    target_name=metadata['related_to'],
                    relation_type=metadata.get('relation_type', 'RELATED_TO')
                )
        except Exception as e:
            print(f"知识图谱存储失败: {e}")

        return memory_id

    def query_with_context(
        self,
        query: str,
        llm_service=None,
        max_context_nodes: int = 10
    ) -> Dict[str, Any]:
        """
        使用知识图谱上下文查询 LLM

        这是最常用的 API：
        kg_rag.query_with_context(
            query="我应该去北京还是上海？",
            llm_service=llm_service
        )

        Returns:
            {
                "answer": "...",
                "context": GraphContext,
                "reasoning": "..."
            }
        """
        # 1. 检索上下文
        context = self.retrieve(
            query=query,
            max_nodes=max_context_nodes,
            mode=RetrievalMode.HYBRID,
            include_reasoning=True
        )

        # 2. 如果有 LLM，用它生成答案
        answer = ""
        if llm_service:
            try:
                prompt = context.to_prompt()
                answer = llm_service.chat([
                    {"role": "system", "content": f"""你是一个基于用户个人知识图谱的AI助手。

知识图谱上下文：
{prompt}

请基于上述上下文回答用户问题。
要求：
1. 引用图谱中的具体节点和数据
2. 给出有依据的分析
3. 如果信息不足，明确指出"""},
                    {"role": "user", "content": query}
                ], temperature=0.3)
            except Exception as e:
                answer = f"LLM生成失败: {str(e)}"
                print(f"LLM调用失败: {e}")

        return {
            "answer": answer,
            "context": context,
            "reasoning": context.reasoning_path,
            "nodes_count": len(context.nodes),
            "influence_summary": context.influence_summary
        }

    # ==================== 辅助方法 ====================

    def _extract_keywords(self, query: str) -> List[str]:
        """从查询中提取关键词"""
        # 简单实现：中文分词
        import re

        # 移除标点
        query = re.sub(r'[，。！？、]', ' ', query)

        # 常见停用词
        stop_words = {'我', '你', '他', '她', '它', '的', '了', '是', '在', '和', '与', '还是', '应该', '要不要'}

        # 提取2-8个字的词
        words = re.findall(r'[\u4e00-\u9fa5]{2,8}', query)
        keywords = [w for w in words if w not in stop_words]

        # 如果提取不到，返回原始查询词
        if not keywords:
            keywords = [query[:10]]

        return keywords[:5]  # 最多5个关键词

    def _calculate_influence(self, node_data: Dict) -> float:
        """计算节点的影响力分数"""
        # 基于置信度和出现次数
        confidence = node_data.get('confidence', 0.5)
        mention_count = node_data.get('mention_count', 1)

        # 归一化
        influence = confidence * (1 + min(mention_count, 10) * 0.05)
        return min(influence, 1.0)

    def _calculate_influence_summary(self, nodes: List[GraphNode]) -> Dict[str, float]:
        """计算各类别的影响力汇总"""
        summary: Dict[str, float] = {}

        for node in nodes:
            category = node.category or 'unknown'
            if category not in summary:
                summary[category] = 0
            summary[category] += node.influence_score

        # 归一化
        total = sum(summary.values())
        if total > 0:
            summary = {k: v / total for k, v in summary.items()}

        return summary

    def _generate_reasoning_path(
        self,
        query: str,
        nodes: List[GraphNode],
        keywords: List[str]
    ) -> str:
        """生成推理路径描述"""
        if not nodes:
            return "未找到相关知识节点"

        lines = ["## 推理路径\n"]

        # 1. 识别关键因素
        key_factors = []
        for node in nodes[:5]:
            if any(kw in node.name for kw in keywords):
                key_factors.append(node)

        if key_factors:
            lines.append(f"### 关键因素（匹配查询）：")
            for factor in key_factors:
                lines.append(f"- **{factor.name}** ({factor.category})")
                lines.append(f"  - 影响力: {factor.influence_score:.2f}, 置信度: {factor.confidence:.2f}")
            lines.append("")

        # 2. 次要因素
        other_factors = [n for n in nodes if n not in key_factors]
        if other_factors:
            lines.append("### 相关因素：")
            for factor in other_factors[:3]:
                lines.append(f"- {factor.name} ({factor.category})")
            lines.append("")

        # 3. 结论提示
        lines.append("### 分析建议")
        lines.append(f"基于 {len(nodes)} 个相关节点的分析，可以从以下维度考虑：")

        categories = set(n.category for n in nodes)
        for cat in categories:
            lines.append(f"- {cat} 相关因素")

        return "\n".join(lines)

    def _is_similar(self, text1: str, text2: str) -> bool:
        """判断两个文本是否相似（简单实现）"""
        # 简单：检查是否有共同字符
        set1 = set(text1)
        set2 = set(text2)
        overlap = len(set1 & set2)
        return overlap >= min(len(set1), len(set2)) * 0.5

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "user_id": self.user_id,
            "vector_search": {
                "enabled": self.use_vector_search,
                "vector_rag": self.vector_rag is not None
            },
            "graph_reasoning": {
                "enabled": self.use_graph_reasoning
            }
        }

        if self.vector_rag:
            try:
                stats["vector_rag_stats"] = self.vector_rag.get_statistics()
            except:
                pass

        return stats


# ==================== GraphContext 扩展方法 ====================

def _extend_graph_context():
    """为 GraphContext 添加 to_prompt 方法"""

    def to_prompt(self) -> str:
        """将图谱上下文转换为可用于 LLM 的 prompt"""
        lines = ["## 知识图谱上下文\n"]

        if not self.nodes:
            lines.append("（暂无相关知识）\n")
            return "\n".join(lines)

        # 1. 影响力汇总
        if self.influence_summary:
            lines.append("### 因素影响力分析：")
            sorted_influence = sorted(self.influence_summary.items(), key=lambda x: x[1], reverse=True)
            for category, score in sorted_influence[:5]:
                lines.append(f"- **{category}**: {score:.1%}")
            lines.append("")

        # 2. 节点详情
        lines.append(f"### 关键节点（共 {len(self.nodes)} 个）：")
        for i, node in enumerate(self.nodes, 1):
            lines.append(f"{i}. {node.to_text()}")
        lines.append("")

        # 3. 关系（如果有）
        if self.relationships:
            lines.append("### 关系网络：")
            for rel in self.relationships[:10]:
                lines.append(f"- {rel.get('source', '')} → {rel.get('target', '')}")
                if rel.get('path'):
                    lines.append(f"  路径: {rel['path']}")
            lines.append("")

        # 4. 推理路径
        if self.reasoning_path:
            lines.append(f"\n{self.reasoning_path}")

        return "\n".join(lines)

    # 动态添加方法
    GraphContext.to_prompt = to_prompt


# 立即执行扩展
_extend_graph_context()
