"""
统一RAG记忆系统 - 整个系统的核心记忆中枢
融合所有数据源：对话、传感器、照片、知识图谱、决策、学习经验
"""
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import os
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    CONVERSATION = "conversation"  # 对话记忆
    SENSOR_DATA = "sensor_data"    # 传感器数据
    PHOTO = "photo"                # 照片记忆
    KNOWLEDGE = "knowledge"        # 知识图谱
    DECISION = "decision"          # 决策记忆
    EXPERIENCE = "experience"      # 经验记忆
    INSIGHT = "insight"            # 洞察记忆


@dataclass
class UnifiedMemory:
    """统一记忆条目"""
    id: str
    user_id: str
    memory_type: MemoryType
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    timestamp: datetime
    importance: float  # 0-1，重要性评分
    access_count: int = 0
    last_access: Optional[datetime] = None
    related_memories: List[str] = None  # 关联记忆ID


class UnifiedRAGSystem:
    """统一RAG记忆系统 - 系统核心
    
    存储层优先级：
    1. ChromaDB（持久化向量数据库，推荐）
    2. 内存字典 + JSON 文件（ChromaDB 不可用时降级）
    """
    
    def __init__(self, user_id: str, storage_path: str = "./data/unified_memory"):
        self.user_id = user_id
        self.storage_path = storage_path
        self.memories: Dict[str, UnifiedMemory] = {}
        # Qwen text-embedding-v3 输出 1024 维；降级哈希向量也用同一维度
        self.embedding_dim = int(os.environ.get("EMBEDDING_DIM", "1024"))
        
        # 按类型索引
        self.type_index: Dict[MemoryType, List[str]] = {
            mem_type: [] for mem_type in MemoryType
        }
        
        # 时间索引
        self.time_index: List[tuple] = []  # (timestamp, memory_id)
        
        os.makedirs(storage_path, exist_ok=True)
        
        # 初始化 ChromaDB（优先）
        self._chroma_collection = None
        self._init_chroma()
        
        self.load_memories()
    
    def _init_chroma(self):
        """初始化 ChromaDB，失败时静默降级到 JSON 文件"""
        try:
            import chromadb
            chroma_path = os.path.join(self.storage_path, "chroma")
            os.makedirs(chroma_path, exist_ok=True)
            client = chromadb.PersistentClient(path=chroma_path)
            # 每个用户独立 collection
            collection_name = f"memories_{self.user_id}".replace("-", "_")
            self._chroma_collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            print(f"✅ ChromaDB 已连接（{self.user_id}，{self._chroma_collection.count()} 条记忆）")
        except ImportError:
            print("ℹ️  ChromaDB 未安装，使用 JSON 文件存储（pip install chromadb 可升级）")
        except Exception as e:
            print(f"⚠️  ChromaDB 初始化失败，降级到 JSON 文件: {e}")
    
    def add_memory(
        self,
        memory_type: MemoryType,
        content: str,
        metadata: Dict[str, Any],
        importance: float = 0.5
    ) -> str:
        """添加记忆到统一系统"""
        memory_id = f"{memory_type.value}_{datetime.now().timestamp()}_{len(self.memories)}"
        
        # 生成embedding
        embedding = self._generate_embedding(content)
        
        # 创建记忆
        memory = UnifiedMemory(
            id=memory_id,
            user_id=self.user_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding,
            metadata=metadata,
            timestamp=datetime.now(),
            importance=importance,
            related_memories=[]
        )
        
        # 存储到内存字典
        self.memories[memory_id] = memory
        
        # 更新索引
        self.type_index[memory_type].append(memory_id)
        self.time_index.append((memory.timestamp, memory_id))
        self.time_index.sort(key=lambda x: x[0], reverse=True)
        
        # 写入 ChromaDB（如果可用）
        if self._chroma_collection is not None:
            try:
                chroma_meta = {
                    "user_id": self.user_id,
                    "memory_type": memory_type.value,
                    "importance": importance,
                    "timestamp": memory.timestamp.isoformat(),
                }
                # ChromaDB metadata 只支持 str/int/float/bool
                for k, v in metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        chroma_meta[k] = v
                self._chroma_collection.upsert(
                    ids=[memory_id],
                    embeddings=[embedding.tolist()],
                    documents=[content],
                    metadatas=[chroma_meta],
                )
            except Exception as e:
                print(f"⚠️  ChromaDB 写入失败: {e}")
        
        # 自动关联相关记忆
        self._auto_link_memories(memory)
        
        # 保存 JSON 备份
        self.save_memories()
        
        return memory_id
    
    def search(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        top_k: int = 10,
        min_importance: float = 0.0
    ) -> List[UnifiedMemory]:
        """跨类型搜索记忆，优先使用 ChromaDB 向量检索"""
        
        # ── ChromaDB 路径（有真实语义向量）──────────────────────────────
        if self._chroma_collection is not None and self._chroma_collection.count() > 0:
            try:
                query_embedding = self._generate_embedding(query)
                where_filter = None
                if memory_types:
                    type_values = [mt.value for mt in memory_types]
                    where_filter = {"memory_type": {"$in": type_values}}
                
                results = self._chroma_collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=min(top_k * 2, self._chroma_collection.count()),
                    where=where_filter,
                )
                
                found: List[UnifiedMemory] = []
                for mid in (results["ids"][0] if results["ids"] else []):
                    mem = self.memories.get(mid)
                    if mem and mem.importance >= min_importance:
                        mem.access_count += 1
                        mem.last_access = datetime.now()
                        found.append(mem)
                    if len(found) >= top_k:
                        break
                
                if found:
                    return found
            except Exception as e:
                print(f"⚠️  ChromaDB 检索失败，降级到内存检索: {e}")
        
        # ── 降级：内存字典余弦相似度检索 ────────────────────────────────
        query_embedding = self._generate_embedding(query)
        candidates = []
        for memory_id, memory in self.memories.items():
            if memory_types and memory.memory_type not in memory_types:
                continue
            if memory.importance < min_importance:
                continue
            similarity = self._cosine_similarity(query_embedding, memory.embedding)
            score = (
                similarity * 0.6 +
                memory.importance * 0.3 +
                min(memory.access_count / 100, 0.1)
            )
            candidates.append((memory, score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        results_mem = [mem for mem, _ in candidates[:top_k]]
        for memory in results_mem:
            memory.access_count += 1
            memory.last_access = datetime.now()
        return results_mem
    
    def get_context_for_conversation(
        self,
        current_query: str,
        max_memories: int = 5
    ) -> str:
        """为对话获取上下文记忆"""
        # 搜索相关记忆
        memories = self.search(
            query=current_query,
            memory_types=[
                MemoryType.CONVERSATION,
                MemoryType.KNOWLEDGE,
                MemoryType.INSIGHT,
                MemoryType.EXPERIENCE
            ],
            top_k=max_memories,
            min_importance=0.3
        )
        
        # 构建上下文
        context_parts = []
        for memory in memories:
            context_parts.append(
                f"[{memory.memory_type.value}] {memory.content}"
            )
        
        return "\n".join(context_parts)
    
    def get_insights_for_domain(
        self,
        domain: str,
        days: int = 7
    ) -> List[UnifiedMemory]:
        """获取特定领域的洞察"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        # 搜索该领域的记忆
        domain_memories = []
        for memory in self.memories.values():
            if memory.timestamp.timestamp() < cutoff_time:
                continue
            
            if memory.metadata.get('domain') == domain:
                domain_memories.append(memory)
        
        # 按重要性排序
        domain_memories.sort(key=lambda x: x.importance, reverse=True)
        
        return domain_memories[:10]
    
    def consolidate_memories(self):
        """记忆整合 - 将相似记忆合并，提取模式"""
        # 找出高度相似的记忆
        similar_groups = []
        processed = set()
        
        memory_list = list(self.memories.values())
        
        for i, mem1 in enumerate(memory_list):
            if mem1.id in processed:
                continue
            
            group = [mem1]
            for mem2 in memory_list[i+1:]:
                if mem2.id in processed:
                    continue
                
                similarity = self._cosine_similarity(mem1.embedding, mem2.embedding)
                if similarity > 0.85:  # 高度相似
                    group.append(mem2)
                    processed.add(mem2.id)
            
            if len(group) > 1:
                similar_groups.append(group)
                processed.add(mem1.id)
        
        # 为每组创建整合记忆
        for group in similar_groups:
            self._create_consolidated_memory(group)
    
    def _create_consolidated_memory(self, memories: List[UnifiedMemory]):
        """创建整合记忆"""
        # 提取共同模式
        contents = [m.content for m in memories]
        combined_content = f"模式: 在{len(memories)}次经历中发现 - " + "; ".join(contents[:3])
        
        # 计算平均重要性
        avg_importance = sum(m.importance for m in memories) / len(memories)
        
        # 创建新的整合记忆
        self.add_memory(
            memory_type=MemoryType.INSIGHT,
            content=combined_content,
            metadata={
                "source_memories": [m.id for m in memories],
                "pattern_count": len(memories),
                "consolidated": True
            },
            importance=min(avg_importance * 1.2, 1.0)  # 提升重要性
        )
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计"""
        stats = {
            "total_memories": len(self.memories),
            "by_type": {},
            "importance_distribution": {
                "high": 0,  # > 0.7
                "medium": 0,  # 0.3-0.7
                "low": 0  # < 0.3
            },
            "most_accessed": [],
            "recent_memories": []
        }
        
        # 按类型统计
        for mem_type in MemoryType:
            stats["by_type"][mem_type.value] = len(self.type_index[mem_type])
        
        # 重要性分布
        for memory in self.memories.values():
            if memory.importance > 0.7:
                stats["importance_distribution"]["high"] += 1
            elif memory.importance > 0.3:
                stats["importance_distribution"]["medium"] += 1
            else:
                stats["importance_distribution"]["low"] += 1
        
        # 最常访问
        sorted_by_access = sorted(
            self.memories.values(),
            key=lambda x: x.access_count,
            reverse=True
        )
        stats["most_accessed"] = [
            {
                "id": m.id,
                "type": m.memory_type.value,
                "content": m.content[:100],
                "access_count": m.access_count
            }
            for m in sorted_by_access[:5]
        ]
        
        # 最近记忆
        stats["recent_memories"] = [
            {
                "id": m.id,
                "type": m.memory_type.value,
                "content": m.content[:100],
                "timestamp": m.timestamp.isoformat()
            }
            for _, m_id in self.time_index[:5]
            for m in [self.memories[m_id]]
        ]
        
        return stats
    
    def _auto_link_memories(self, new_memory: UnifiedMemory):
        """自动关联相关记忆"""
        # 找到最相关的5个记忆
        similar = []
        for memory in self.memories.values():
            if memory.id == new_memory.id:
                continue
            
            similarity = self._cosine_similarity(new_memory.embedding, memory.embedding)
            if similarity > 0.6:
                similar.append((memory.id, similarity))
        
        similar.sort(key=lambda x: x[1], reverse=True)
        new_memory.related_memories = [m_id for m_id, _ in similar[:5]]
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成文本 embedding
        
        优先使用 Qwen text-embedding API（零内存，真实语义）。
        API 不可用时降级为确定性哈希向量（保证同文本相同向量，但无语义）。
        """
        # 尝试 Qwen embedding API
        api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        if api_key:
            try:
                import dashscope
                from dashscope import TextEmbedding
                dashscope.api_key = api_key
                resp = TextEmbedding.call(
                    model=TextEmbedding.Models.text_embedding_v3,
                    input=text[:2048],  # API 最大长度限制
                )
                if resp.status_code == 200:
                    vec = np.array(resp.output["embeddings"][0]["embedding"], dtype=np.float32)
                    # 统一归一化到 self.embedding_dim
                    if len(vec) != self.embedding_dim:
                        # 截断或补零对齐维度
                        aligned = np.zeros(self.embedding_dim, dtype=np.float32)
                        copy_len = min(len(vec), self.embedding_dim)
                        aligned[:copy_len] = vec[:copy_len]
                        vec = aligned
                    norm = np.linalg.norm(vec)
                    return vec / norm if norm > 0 else vec
            except Exception:
                pass  # 静默降级

        # 降级：确定性哈希向量（同文本 → 同向量，但无语义相似性）
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.randn(self.embedding_dim).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        return float(np.dot(vec1, vec2))
    
    def save_memories(self):
        """保存记忆"""
        filepath = os.path.join(self.storage_path, f"{self.user_id}_unified.json")
        
        data = {
            "user_id": self.user_id,
            "memories": [
                {
                    "id": m.id,
                    "memory_type": m.memory_type.value,
                    "content": m.content,
                    "embedding": m.embedding.tolist(),
                    "metadata": m.metadata,
                    "timestamp": m.timestamp.isoformat(),
                    "importance": m.importance,
                    "access_count": m.access_count,
                    "last_access": m.last_access.isoformat() if m.last_access else None,
                    "related_memories": m.related_memories or []
                }
                for m in self.memories.values()
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_memories(self):
        """加载记忆"""
        filepath = os.path.join(self.storage_path, f"{self.user_id}_unified.json")
        
        if not os.path.exists(filepath):
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for mem_data in data["memories"]:
                memory = UnifiedMemory(
                    id=mem_data["id"],
                    user_id=self.user_id,
                    memory_type=MemoryType(mem_data["memory_type"]),
                    content=mem_data["content"],
                    embedding=np.array(mem_data["embedding"]),
                    metadata=mem_data["metadata"],
                    timestamp=datetime.fromisoformat(mem_data["timestamp"]),
                    importance=mem_data["importance"],
                    access_count=mem_data.get("access_count", 0),
                    last_access=datetime.fromisoformat(mem_data["last_access"]) if mem_data.get("last_access") else None,
                    related_memories=mem_data.get("related_memories", [])
                )
                
                self.memories[memory.id] = memory
                self.type_index[memory.memory_type].append(memory.id)
                self.time_index.append((memory.timestamp, memory.id))
            
            self.time_index.sort(key=lambda x: x[0], reverse=True)
            
        except Exception as e:
            print(f"Failed to load memories: {e}")


# 全局记忆系统管理器
class MemorySystemManager:
    """记忆系统管理器"""
    
    _instances: Dict[str, UnifiedRAGSystem] = {}
    
    @classmethod
    def get_system(cls, user_id: str) -> UnifiedRAGSystem:
        """获取用户的记忆系统"""
        if user_id not in cls._instances:
            cls._instances[user_id] = UnifiedRAGSystem(user_id)
        return cls._instances[user_id]
    
    @classmethod
    def add_conversation_memory(cls, user_id: str, conversation: str, importance: float = 0.6):
        """添加对话记忆"""
        system = cls.get_system(user_id)
        return system.add_memory(
            memory_type=MemoryType.CONVERSATION,
            content=conversation,
            metadata={"source": "ai_chat"},
            importance=importance
        )
    
    @classmethod
    def add_sensor_memory(cls, user_id: str, sensor_data: Dict[str, Any], importance: float = 0.4):
        """添加传感器记忆"""
        system = cls.get_system(user_id)
        content = f"传感器数据: {json.dumps(sensor_data, ensure_ascii=False)}"
        return system.add_memory(
            memory_type=MemoryType.SENSOR_DATA,
            content=content,
            metadata=sensor_data,
            importance=importance
        )
    
    @classmethod
    def add_decision_memory(cls, user_id: str, decision: str, outcome: str, importance: float = 0.8):
        """添加决策记忆"""
        system = cls.get_system(user_id)
        content = f"决策: {decision} -> 结果: {outcome}"
        return system.add_memory(
            memory_type=MemoryType.DECISION,
            content=content,
            metadata={"decision": decision, "outcome": outcome},
            importance=importance
        )
    
    @classmethod
    def add_insight_memory(cls, user_id: str, insight: str, domain: str, importance: float = 0.9):
        """添加洞察记忆"""
        system = cls.get_system(user_id)
        return system.add_memory(
            memory_type=MemoryType.INSIGHT,
            content=insight,
            metadata={"domain": domain},
            importance=importance
        )
