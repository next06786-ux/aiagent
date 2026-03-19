"""
知识图谱推理模块 - Phase 2.4
实现关系推理、路径查询、相似度计算、推荐生成
"""
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
import math


@dataclass
class GraphNode:
    """图节点"""
    node_id: str
    node_type: str  # entity, concept, event, pattern
    properties: Dict[str, Any] = field(default_factory=dict)
    labels: List[str] = field(default_factory=list)


@dataclass
class GraphRelation:
    """图关系"""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: str  # causes, correlates, influences, similar_to
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    confidence: float = 1.0


@dataclass
class InferenceResult:
    """推理结果"""
    query: str
    result_type: str  # path, relation, similarity, recommendation
    results: List[Any]
    confidence: float
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class KnowledgeGraphReasoner:
    """知识图谱推理器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.nodes = {}  # node_id -> GraphNode
        self.relations = {}  # relation_id -> GraphRelation
        self.adjacency_list = defaultdict(list)  # source_id -> [(target_id, relation)]
        self.reverse_adjacency = defaultdict(list)  # target_id -> [(source_id, relation)]
        self.inference_history = []
    
    def add_node(self, node: GraphNode) -> None:
        """添加节点"""
        self.nodes[node.node_id] = node
    
    def add_relation(self, relation: GraphRelation) -> None:
        """添加关系"""
        self.relations[relation.relation_id] = relation
        self.adjacency_list[relation.source_id].append(
            (relation.target_id, relation)
        )
        self.reverse_adjacency[relation.target_id].append(
            (relation.source_id, relation)
        )
    
    def infer_transitive_relations(
        self,
        start_node_id: str,
        relation_type: str,
        max_depth: int = 3
    ) -> List[Tuple[str, List[GraphRelation], float]]:
        """
        推理传递关系
        例如：A causes B, B causes C => A indirectly causes C
        """
        results = []
        visited = set()
        
        def dfs(current_id: str, path: List[GraphRelation], depth: int, confidence: float):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            # 如果路径长度>1，记录推理结果
            if len(path) > 1:
                results.append((current_id, path.copy(), confidence))
            
            # 继续搜索
            for next_id, relation in self.adjacency_list.get(current_id, []):
                if relation.relation_type == relation_type:
                    new_confidence = confidence * relation.confidence
                    dfs(next_id, path + [relation], depth + 1, new_confidence)
            
            visited.remove(current_id)
        
        dfs(start_node_id, [], 0, 1.0)
        
        return results
    
    def find_shortest_path(
        self,
        start_node_id: str,
        end_node_id: str,
        relation_types: Optional[List[str]] = None
    ) -> Optional[Tuple[List[str], List[GraphRelation], float]]:
        """
        查找最短路径（BFS）
        """
        if start_node_id not in self.nodes or end_node_id not in self.nodes:
            return None
        
        queue = deque([(start_node_id, [], [], 1.0)])  # (node_id, path, relations, confidence)
        visited = {start_node_id}
        
        while queue:
            current_id, path, relations, confidence = queue.popleft()
            
            if current_id == end_node_id:
                return (path + [current_id], relations, confidence)
            
            for next_id, relation in self.adjacency_list.get(current_id, []):
                if next_id not in visited:
                    # 检查关系类型
                    if relation_types and relation.relation_type not in relation_types:
                        continue
                    
                    visited.add(next_id)
                    new_confidence = confidence * relation.confidence
                    queue.append((
                        next_id,
                        path + [current_id],
                        relations + [relation],
                        new_confidence
                    ))
        
        return None
    
    def find_all_paths(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 5
    ) -> List[Tuple[List[str], List[GraphRelation], float]]:
        """
        查找所有路径（DFS）
        """
        if start_node_id not in self.nodes or end_node_id not in self.nodes:
            return []
        
        all_paths = []
        
        def dfs(current_id: str, path: List[str], relations: List[GraphRelation], 
                confidence: float, visited: Set[str]):
            if len(path) > max_depth:
                return
            
            if current_id == end_node_id:
                all_paths.append((path + [current_id], relations, confidence))
                return
            
            for next_id, relation in self.adjacency_list.get(current_id, []):
                if next_id not in visited:
                    new_visited = visited.copy()
                    new_visited.add(next_id)
                    new_confidence = confidence * relation.confidence
                    
                    dfs(
                        next_id,
                        path + [current_id],
                        relations + [relation],
                        new_confidence,
                        new_visited
                    )
        
        dfs(start_node_id, [], [], 1.0, {start_node_id})
        
        return all_paths
    
    def calculate_node_similarity(
        self,
        node1_id: str,
        node2_id: str
    ) -> float:
        """
        计算节点相似度
        基于共同邻居、属性相似度等
        """
        if node1_id not in self.nodes or node2_id not in self.nodes:
            return 0.0
        
        node1 = self.nodes[node1_id]
        node2 = self.nodes[node2_id]
        
        # 1. 类型相似度
        type_similarity = 1.0 if node1.node_type == node2.node_type else 0.5
        
        # 2. 标签相似度（Jaccard）
        labels1 = set(node1.labels)
        labels2 = set(node2.labels)
        if labels1 or labels2:
            label_similarity = len(labels1 & labels2) / len(labels1 | labels2)
        else:
            label_similarity = 0.0
        
        # 3. 共同邻居相似度
        neighbors1 = set(n for n, _ in self.adjacency_list.get(node1_id, []))
        neighbors2 = set(n for n, _ in self.adjacency_list.get(node2_id, []))
        if neighbors1 or neighbors2:
            neighbor_similarity = len(neighbors1 & neighbors2) / len(neighbors1 | neighbors2)
        else:
            neighbor_similarity = 0.0
        
        # 4. 属性相似度
        props1 = set(node1.properties.keys())
        props2 = set(node2.properties.keys())
        if props1 or props2:
            prop_similarity = len(props1 & props2) / len(props1 | props2)
        else:
            prop_similarity = 0.0
        
        # 综合相似度
        similarity = (
            type_similarity * 0.2 +
            label_similarity * 0.3 +
            neighbor_similarity * 0.3 +
            prop_similarity * 0.2
        )
        
        return similarity
    
    def find_similar_nodes(
        self,
        node_id: str,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Tuple[str, float]]:
        """查找相似节点"""
        if node_id not in self.nodes:
            return []
        
        similarities = []
        for other_id in self.nodes:
            if other_id != node_id:
                similarity = self.calculate_node_similarity(node_id, other_id)
                if similarity >= min_similarity:
                    similarities.append((other_id, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def infer_missing_relations(
        self,
        confidence_threshold: float = 0.6
    ) -> List[GraphRelation]:
        """
        推理缺失的关系
        基于传递性、相似性等
        """
        inferred_relations = []
        
        # 1. 基于传递性推理
        for node_id in self.nodes:
            # 查找因果传递
            transitive = self.infer_transitive_relations(node_id, "causes", max_depth=2)
            
            for target_id, path, confidence in transitive:
                if confidence >= confidence_threshold:
                    # 创建推理的关系
                    relation = GraphRelation(
                        relation_id=f"inferred_{node_id}_{target_id}_{datetime.now().timestamp()}",
                        source_id=node_id,
                        target_id=target_id,
                        relation_type="indirectly_causes",
                        properties={"inferred": True, "path_length": len(path)},
                        confidence=confidence
                    )
                    inferred_relations.append(relation)
        
        # 2. 基于相似性推理
        for node_id in self.nodes:
            similar_nodes = self.find_similar_nodes(node_id, top_k=3, min_similarity=0.7)
            
            for similar_id, similarity in similar_nodes:
                # 如果两个节点相似，且没有直接关系，创建相似关系
                has_relation = any(
                    target_id == similar_id
                    for target_id, _ in self.adjacency_list.get(node_id, [])
                )
                
                if not has_relation:
                    relation = GraphRelation(
                        relation_id=f"inferred_sim_{node_id}_{similar_id}_{datetime.now().timestamp()}",
                        source_id=node_id,
                        target_id=similar_id,
                        relation_type="similar_to",
                        properties={"inferred": True},
                        confidence=similarity
                    )
                    inferred_relations.append(relation)
        
        return inferred_relations
    
    def query_by_pattern(
        self,
        pattern: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        模式查询
        例如：查找所有 A causes B causes C 的模式
        """
        results = []
        
        # 简化实现：查找特定类型的路径
        if pattern.get("type") == "causal_chain":
            min_length = pattern.get("min_length", 2)
            
            for start_id in self.nodes:
                transitive = self.infer_transitive_relations(
                    start_id, "causes", max_depth=min_length
                )
                
                for target_id, path, confidence in transitive:
                    if len(path) >= min_length:
                        results.append({
                            "start": start_id,
                            "end": target_id,
                            "path": path,
                            "confidence": confidence
                        })
        
        return results


class RecommendationEngine:
    """推荐引擎"""
    
    def __init__(self, reasoner: KnowledgeGraphReasoner):
        self.reasoner = reasoner
    
    def recommend_actions(
        self,
        current_state: Dict[str, Any],
        goal: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        推荐行动
        基于知识图谱中的因果关系
        """
        recommendations = []
        
        # 查找与目标相关的节点
        goal_nodes = [
            node_id for node_id, node in self.reasoner.nodes.items()
            if goal.lower() in node.properties.get("name", "").lower()
        ]
        
        if not goal_nodes:
            return []
        
        goal_node_id = goal_nodes[0]
        
        # 查找所有指向目标的路径
        for node_id in self.reasoner.nodes:
            if node_id == goal_node_id:
                continue
            
            paths = self.reasoner.find_all_paths(node_id, goal_node_id, max_depth=3)
            
            for path, relations, confidence in paths:
                if confidence > 0.5:
                    recommendations.append({
                        "action": self.reasoner.nodes[node_id].properties.get("name", node_id),
                        "path": [self.reasoner.nodes[n].properties.get("name", n) for n in path],
                        "confidence": confidence,
                        "steps": len(path) - 1
                    })
        
        # 按置信度和步数排序
        recommendations.sort(key=lambda x: (x["confidence"], -x["steps"]), reverse=True)
        
        return recommendations[:top_k]
    
    def recommend_similar_items(
        self,
        item_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """推荐相似项"""
        similar_nodes = self.reasoner.find_similar_nodes(item_id, top_k=top_k)
        
        recommendations = []
        for node_id, similarity in similar_nodes:
            node = self.reasoner.nodes[node_id]
            recommendations.append({
                "item_id": node_id,
                "name": node.properties.get("name", node_id),
                "type": node.node_type,
                "similarity": similarity,
                "properties": node.properties
            })
        
        return recommendations
    
    def recommend_by_collaborative_filtering(
        self,
        user_preferences: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        协同过滤推荐
        基于用户偏好和图结构
        """
        # 收集所有偏好节点的邻居
        neighbor_scores = defaultdict(float)
        
        for pref_id in user_preferences:
            if pref_id not in self.reasoner.nodes:
                continue
            
            # 获取邻居节点
            for neighbor_id, relation in self.reasoner.adjacency_list.get(pref_id, []):
                if neighbor_id not in user_preferences:
                    # 累加分数（基于关系权重和置信度）
                    score = relation.weight * relation.confidence
                    neighbor_scores[neighbor_id] += score
        
        # 排序
        sorted_neighbors = sorted(
            neighbor_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 生成推荐
        recommendations = []
        for node_id, score in sorted_neighbors[:top_k]:
            node = self.reasoner.nodes[node_id]
            recommendations.append({
                "item_id": node_id,
                "name": node.properties.get("name", node_id),
                "type": node.node_type,
                "score": score,
                "properties": node.properties
            })
        
        return recommendations


class SemanticQueryEngine:
    """语义查询引擎"""
    
    def __init__(self, reasoner: KnowledgeGraphReasoner):
        self.reasoner = reasoner
    
    def query(self, query_text: str) -> InferenceResult:
        """
        语义查询
        解析自然语言查询并执行
        """
        query_lower = query_text.lower()
        
        # 简化的查询解析
        if "路径" in query_lower or "path" in query_lower:
            return self._handle_path_query(query_text)
        elif "相似" in query_lower or "similar" in query_lower:
            return self._handle_similarity_query(query_text)
        elif "推荐" in query_lower or "recommend" in query_lower:
            return self._handle_recommendation_query(query_text)
        elif "因果" in query_lower or "cause" in query_lower:
            return self._handle_causal_query(query_text)
        else:
            return InferenceResult(
                query=query_text,
                result_type="unknown",
                results=[],
                confidence=0.0,
                reasoning="无法理解查询"
            )
    
    def _handle_path_query(self, query_text: str) -> InferenceResult:
        """处理路径查询"""
        # 简化实现：假设查询格式为 "从A到B的路径"
        results = []
        
        # 查找所有节点对的最短路径
        node_ids = list(self.reasoner.nodes.keys())
        if len(node_ids) >= 2:
            path_result = self.reasoner.find_shortest_path(node_ids[0], node_ids[1])
            if path_result:
                path, relations, confidence = path_result
                results.append({
                    "path": path,
                    "relations": [r.relation_type for r in relations],
                    "confidence": confidence
                })
        
        return InferenceResult(
            query=query_text,
            result_type="path",
            results=results,
            confidence=0.8,
            reasoning="查找最短路径"
        )
    
    def _handle_similarity_query(self, query_text: str) -> InferenceResult:
        """处理相似度查询"""
        results = []
        
        # 查找第一个节点的相似节点
        node_ids = list(self.reasoner.nodes.keys())
        if node_ids:
            similar = self.reasoner.find_similar_nodes(node_ids[0], top_k=5)
            results = [
                {"node_id": node_id, "similarity": sim}
                for node_id, sim in similar
            ]
        
        return InferenceResult(
            query=query_text,
            result_type="similarity",
            results=results,
            confidence=0.85,
            reasoning="计算节点相似度"
        )
    
    def _handle_recommendation_query(self, query_text: str) -> InferenceResult:
        """处理推荐查询"""
        engine = RecommendationEngine(self.reasoner)
        
        # 简化实现：推荐相似项
        node_ids = list(self.reasoner.nodes.keys())
        if node_ids:
            recommendations = engine.recommend_similar_items(node_ids[0], top_k=5)
        else:
            recommendations = []
        
        return InferenceResult(
            query=query_text,
            result_type="recommendation",
            results=recommendations,
            confidence=0.75,
            reasoning="基于相似度推荐"
        )
    
    def _handle_causal_query(self, query_text: str) -> InferenceResult:
        """处理因果查询"""
        results = []
        
        # 查找因果链
        node_ids = list(self.reasoner.nodes.keys())
        if node_ids:
            transitive = self.reasoner.infer_transitive_relations(
                node_ids[0], "causes", max_depth=3
            )
            results = [
                {
                    "target": target_id,
                    "path_length": len(path),
                    "confidence": confidence
                }
                for target_id, path, confidence in transitive[:5]
            ]
        
        return InferenceResult(
            query=query_text,
            result_type="causal",
            results=results,
            confidence=0.8,
            reasoning="推理因果关系"
        )


# 全局实例管理
_reasoners = {}
_recommendation_engines = {}
_query_engines = {}

def get_knowledge_graph_reasoner(user_id: str) -> KnowledgeGraphReasoner:
    """获取知识图谱推理器"""
    if user_id not in _reasoners:
        _reasoners[user_id] = KnowledgeGraphReasoner(user_id)
    return _reasoners[user_id]

def get_recommendation_engine(user_id: str) -> RecommendationEngine:
    """获取推荐引擎"""
    if user_id not in _recommendation_engines:
        reasoner = get_knowledge_graph_reasoner(user_id)
        _recommendation_engines[user_id] = RecommendationEngine(reasoner)
    return _recommendation_engines[user_id]

def get_semantic_query_engine(user_id: str) -> SemanticQueryEngine:
    """获取语义查询引擎"""
    if user_id not in _query_engines:
        reasoner = get_knowledge_graph_reasoner(user_id)
        _query_engines[user_id] = SemanticQueryEngine(reasoner)
    return _query_engines[user_id]

