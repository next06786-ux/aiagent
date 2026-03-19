"""
RAG知识库 - 用于强化学习的自学习
存储成功案例和最佳实践
"""
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import os


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    success_score: float
    timestamp: datetime
    usage_count: int = 0


class RAGMemory:
    """RAG记忆系统 - 简化版向量存储"""
    
    def __init__(self, user_id: str, storage_path: str = "./data/rag_memory"):
        self.user_id = user_id
        self.storage_path = storage_path
        self.memories: List[MemoryEntry] = []
        self.embedding_dim = 384  # 简化的embedding维度
        
        # 创建存储目录
        os.makedirs(storage_path, exist_ok=True)
        
        # 加载已有记忆
        self.load_memories()
    
    def add_memory(
        self,
        content: str,
        metadata: Dict[str, Any],
        success_score: float
    ) -> str:
        """添加新记忆"""
        memory_id = f"mem_{datetime.now().timestamp()}_{len(self.memories)}"
        
        # 生成简单的embedding（实际应用中应使用真实的embedding模型）
        embedding = self._generate_embedding(content)
        
        memory = MemoryEntry(
            id=memory_id,
            content=content,
            embedding=embedding,
            metadata=metadata,
            success_score=success_score,
            timestamp=datetime.now(),
            usage_count=0
        )
        
        self.memories.append(memory)
        self.save_memories()
        
        return memory_id
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.5
    ) -> List[MemoryEntry]:
        """搜索相关记忆"""
        if not self.memories:
            return []
        
        # 生成查询embedding
        query_embedding = self._generate_embedding(query)
        
        # 计算相似度
        similarities = []
        for memory in self.memories:
            similarity = self._cosine_similarity(query_embedding, memory.embedding)
            if similarity >= min_score:
                similarities.append((memory, similarity))
        
        # 排序并返回top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = [mem for mem, _ in similarities[:top_k]]
        
        # 更新使用计数
        for memory in results:
            memory.usage_count += 1
        
        return results
    
    def get_best_practices(
        self,
        domain: str,
        top_k: int = 3
    ) -> List[MemoryEntry]:
        """获取特定领域的最佳实践"""
        domain_memories = [
            mem for mem in self.memories
            if mem.metadata.get('domain') == domain
        ]
        
        # 按成功分数排序
        domain_memories.sort(key=lambda x: x.success_score, reverse=True)
        
        return domain_memories[:top_k]
    
    def update_success_score(
        self,
        memory_id: str,
        new_score: float
    ):
        """更新记忆的成功分数"""
        for memory in self.memories:
            if memory.id == memory_id:
                # 使用移动平均更新分数
                memory.success_score = (
                    0.7 * memory.success_score + 0.3 * new_score
                )
                self.save_memories()
                break
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.memories:
            return {
                "total_memories": 0,
                "average_success_score": 0,
                "most_used_memory": None,
                "domains": {}
            }
        
        # 统计各领域记忆数量
        domains = {}
        for memory in self.memories:
            domain = memory.metadata.get('domain', 'unknown')
            domains[domain] = domains.get(domain, 0) + 1
        
        # 找到最常用的记忆
        most_used = max(self.memories, key=lambda x: x.usage_count)
        
        return {
            "total_memories": len(self.memories),
            "average_success_score": np.mean([m.success_score for m in self.memories]),
            "most_used_memory": {
                "id": most_used.id,
                "content": most_used.content[:100],
                "usage_count": most_used.usage_count
            },
            "domains": domains
        }
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成文本embedding（简化版）"""
        # 实际应用中应使用真实的embedding模型（如sentence-transformers）
        # 这里使用简单的哈希方法作为演示
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.randn(self.embedding_dim)
        # 归一化
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def _cosine_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray
    ) -> float:
        """计算余弦相似度"""
        return float(np.dot(vec1, vec2))
    
    def save_memories(self):
        """保存记忆到磁盘"""
        filepath = os.path.join(self.storage_path, f"{self.user_id}_memories.json")
        
        data = {
            "user_id": self.user_id,
            "memories": [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "embedding": mem.embedding.tolist(),
                    "metadata": mem.metadata,
                    "success_score": mem.success_score,
                    "timestamp": mem.timestamp.isoformat(),
                    "usage_count": mem.usage_count
                }
                for mem in self.memories
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_memories(self):
        """从磁盘加载记忆"""
        filepath = os.path.join(self.storage_path, f"{self.user_id}_memories.json")
        
        if not os.path.exists(filepath):
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.memories = [
                MemoryEntry(
                    id=mem["id"],
                    content=mem["content"],
                    embedding=np.array(mem["embedding"]),
                    metadata=mem["metadata"],
                    success_score=mem["success_score"],
                    timestamp=datetime.fromisoformat(mem["timestamp"]),
                    usage_count=mem.get("usage_count", 0)
                )
                for mem in data["memories"]
            ]
        except Exception as e:
            print(f"Failed to load memories: {e}")
            self.memories = []
    
    def prune_low_quality_memories(self, min_score: float = 0.3):
        """删除低质量记忆"""
        original_count = len(self.memories)
        self.memories = [
            mem for mem in self.memories
            if mem.success_score >= min_score
        ]
        pruned_count = original_count - len(self.memories)
        
        if pruned_count > 0:
            self.save_memories()
        
        return pruned_count


class RAGEnhancedLearner:
    """结合RAG的强化学习器"""
    
    def __init__(self, user_id: str, base_learner):
        self.user_id = user_id
        self.base_learner = base_learner
        self.rag_memory = RAGMemory(user_id)
    
    def learn_from_feedback(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        feedback: Dict[str, Any]
    ):
        """从反馈中学习"""
        # 基础强化学习
        self.base_learner.update(state, action, feedback)
        
        # 如果反馈是正面的，存入RAG记忆
        if feedback.get('rating', 0) >= 0.7:
            content = f"State: {state}, Action: {action}, Result: Success"
            metadata = {
                "domain": state.get('domain', 'unknown'),
                "action_type": action.get('type', 'unknown'),
                "feedback_type": feedback.get('feedback_type', 'unknown')
            }
            
            self.rag_memory.add_memory(
                content=content,
                metadata=metadata,
                success_score=feedback.get('rating', 0.7)
            )
    
    def get_recommendations(
        self,
        current_state: Dict[str, Any],
        domain: str
    ) -> List[Dict[str, Any]]:
        """基于RAG记忆获取推荐"""
        # 搜索相似的成功案例
        query = f"State: {current_state}, Domain: {domain}"
        similar_memories = self.rag_memory.search(query, top_k=3)
        
        # 获取该领域的最佳实践
        best_practices = self.rag_memory.get_best_practices(domain, top_k=2)
        
        recommendations = []
        
        # 从相似案例中提取建议
        for memory in similar_memories:
            recommendations.append({
                "source": "similar_case",
                "content": memory.content,
                "confidence": memory.success_score,
                "usage_count": memory.usage_count
            })
        
        # 从最佳实践中提取建议
        for practice in best_practices:
            recommendations.append({
                "source": "best_practice",
                "content": practice.content,
                "confidence": practice.success_score,
                "usage_count": practice.usage_count
            })
        
        return recommendations
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "base_learner": self.base_learner.get_statistics(),
            "rag_memory": self.rag_memory.get_statistics()
        }
