"""
生产级RAG记忆系统
使用sentence-transformers + FAISS向量数据库
需要GPU加速以获得最佳性能
"""
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import os
from enum import Enum
import pickle

# 尝试导入专业库
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    PRODUCTION_MODE = True
except ImportError:
    PRODUCTION_MODE = False
    print("⚠️  警告: 未安装sentence-transformers或faiss-cpu")
    print("   生产环境请安装: pip install sentence-transformers faiss-cpu")
    print("   GPU加速请安装: pip install sentence-transformers faiss-gpu")


class MemoryType(Enum):
    """记忆类型"""
    CONVERSATION = "conversation"
    SENSOR_DATA = "sensor_data"
    PHOTO = "photo"
    KNOWLEDGE = "knowledge"
    DECISION = "decision"
    EXPERIENCE = "experience"
    INSIGHT = "insight"
    SCHEDULE = "schedule"  # 日程安排记忆
    TASK_COMPLETION = "task_completion"  # 任务完成记录
    DECISION_LOGIC = "decision_logic"  # 决策逻辑画像（来自平行人生塔罗牌游戏）


@dataclass
class UnifiedMemory:
    """统一记忆条目"""
    id: str
    user_id: str
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    importance: float
    access_count: int = 0
    last_access: Optional[datetime] = None
    related_memories: List[str] = None


class ProductionRAGSystem:
    """生产级RAG系统"""
    
    # 类级别的共享模型（所有用户共享）
    _shared_model = None
    _embedding_dim = None
    _model_initialized = False
    
    # 查询embedding缓存（所有用户共享）
    _query_cache: Dict[str, np.ndarray] = {}
    _cache_max_size = 1000
    
    @classmethod
    def _initialize_shared_model(cls, model_name: str, use_gpu: bool):
        """初始化共享的embedding模型（只执行一次）"""
        if cls._model_initialized:
            return
        
        if not PRODUCTION_MODE:
            raise RuntimeError("❌ 生产模式必须启用！请安装: pip install sentence-transformers faiss-cpu")
        
        print(f"🚀 初始化生产级RAG系统...")
        print(f"   模型: {model_name}")
        print(f"   请求GPU: {use_gpu}")
        
        # 自动检测GPU可用性
        try:
            import torch
            gpu_available = torch.cuda.is_available()
            gpu_count = torch.cuda.device_count() if gpu_available else 0
            
            print(f"   🔍 GPU检测: available={gpu_available}, count={gpu_count}")
            
            if use_gpu and gpu_available:
                device = 'cuda'
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                print(f"   ✅ GPU加速: 已启用")
                print(f"   GPU设备: {gpu_name}")
                print(f"   显存容量: {gpu_memory:.1f}GB")
            elif use_gpu and not gpu_available:
                device = 'cpu'
                print(f"   ⚠️ GPU加速: 请求启用但GPU不可用，降级到CPU模式")
                print(f"   原因: torch.cuda.is_available() = False")
            else:
                device = 'cpu'
                print(f"   ℹ️ CPU模式: 已启用（use_gpu={use_gpu}）")
        except Exception as e:
            device = 'cpu'
            print(f"   ⚠️ GPU检测失败: {e}")
            print(f"   降级到CPU模式")
        
        # 优先使用本地模型路径
        local_model_path = f"/root/autodl-tmp/huggingface/sentence-transformers/{model_name}"
        if os.path.exists(local_model_path):
            print(f"   📁 使用本地模型: {local_model_path}")
            cls._shared_model = SentenceTransformer(local_model_path, device=device)
        else:
            print(f"   🌐 从HuggingFace下载模型...")
            cls._shared_model = SentenceTransformer(model_name, device=device)
        
        cls._embedding_dim = cls._shared_model.get_sentence_embedding_dimension()
        cls._model_initialized = True
        
        # 验证模型实际运行设备
        actual_device = str(cls._shared_model.device)
        print(f"   ✅ 共享模型初始化完成")
        print(f"   Embedding维度: {cls._embedding_dim}")
        print(f"   目标设备: {device.upper()}")
        print(f"   实际设备: {actual_device.upper()}")
        
        # GPU预热：首次编码会慢，预热后会快很多
        if device == 'cuda':
            print(f"   🔥 GPU预热中...")
            try:
                warmup_texts = [
                    "这是一个测试句子",
                    "GPU预热测试",
                    "向量编码预热"
                ]
                _ = cls._shared_model.encode(warmup_texts, convert_to_numpy=True)
                print(f"   ✅ GPU预热完成")
            except Exception as e:
                print(f"   ⚠️ GPU预热失败: {e}")
    
    def __init__(
        self,
        user_id: str,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        storage_path: str = "./data/production_rag",
        use_gpu: bool = True
    ):
        self.user_id = user_id
        self.storage_path = storage_path
        self.use_gpu = use_gpu
        
        os.makedirs(storage_path, exist_ok=True)
        
        # 初始化共享模型（如果还没初始化）
        if not self._model_initialized:
            self._initialize_shared_model(model_name, use_gpu)
        
        # 使用共享模型
        self.model = self._shared_model
        self.embedding_dim = self._embedding_dim
        
        # 初始化FAISS索引（每个用户独立）
        if PRODUCTION_MODE:
            # 自动检测GPU可用性
            gpu_available = use_gpu and faiss.get_num_gpus() > 0
            
            if gpu_available:
                try:
                    print(f"   🚀 为用户 {user_id} 创建GPU FAISS索引")
                    res = faiss.StandardGpuResources()
                    
                    # 设置GPU显存限制（为4GB显卡优化）
                    # 预留2GB给其他任务，FAISS使用最多2GB
                    res.setTempMemory(2 * 1024 * 1024 * 1024)  # 2GB
                    
                    self.index = faiss.GpuIndexFlatIP(res, self.embedding_dim)
                    self.gpu_resources = res  # 保存引用避免被回收
                    print(f"   ✅ GPU索引创建成功")
                except Exception as e:
                    print(f"   ⚠️ GPU索引创建失败: {e}")
                    print(f"   降级到CPU索引")
                    self.index = faiss.IndexFlatIP(self.embedding_dim)
                    self.gpu_resources = None
            else:
                # CPU索引 - 使用增量模式
                self.index = faiss.IndexFlatIP(self.embedding_dim)
                self.gpu_resources = None
                print(f"   ✓ 为用户 {user_id} 创建CPU FAISS索引")
        else:
            raise RuntimeError("❌ 生产模式必须启用！请安装: pip install sentence-transformers faiss-cpu")
        
        # 记忆存储
        self.memories: Dict[str, UnifiedMemory] = {}
        self.memory_ids: List[str] = []  # 与FAISS索引对应的ID列表
        
        # 类型索引
        self.type_index: Dict[MemoryType, List[str]] = {
            mem_type: [] for mem_type in MemoryType
        }
        
        # 加载已有数据
        self.load_memories()
    
    def add_memory(
        self,
        memory_type: MemoryType,
        content: str,
        metadata: Dict[str, Any],
        importance: float = 0.5
    ) -> str:
        """添加记忆"""
        memory_id = f"{memory_type.value}_{datetime.now().timestamp()}_{len(self.memories)}"
        
        # 创建记忆对象
        memory = UnifiedMemory(
            id=memory_id,
            user_id=self.user_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            timestamp=datetime.now(),
            importance=importance,
            related_memories=[]
        )
        
        # 生成embedding并添加到FAISS
        if PRODUCTION_MODE and self.model:
            embedding = self.model.encode(
                content,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            self.index.add(embedding.reshape(1, -1))
        else:
            # 简化模式
            embedding = self._simple_embedding(content)
        
        # 存储
        self.memories[memory_id] = memory
        self.memory_ids.append(memory_id)
        self.type_index[memory_type].append(memory_id)
        
        # 保存
        self.save_memories()
        
        return memory_id
    
    def search(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        top_k: int = 10,
        min_importance: float = 0.0
    ) -> List[UnifiedMemory]:
        """向量搜索记忆"""
        if not self.memory_ids:
            return []
        
        # 生成查询embedding（使用缓存）
        if PRODUCTION_MODE and self.model:
            # 检查缓存
            cache_key = f"{query}_{self.user_id}"
            if cache_key in self._query_cache:
                query_embedding = self._query_cache[cache_key]
            else:
                # 编码并缓存
                query_embedding = self.model.encode(
                    query,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
                
                # 缓存管理：如果超过最大大小，清除最旧的一半
                if len(self._query_cache) >= self._cache_max_size:
                    keys_to_remove = list(self._query_cache.keys())[:self._cache_max_size // 2]
                    for k in keys_to_remove:
                        del self._query_cache[k]
                
                self._query_cache[cache_key] = query_embedding
            
            # FAISS搜索
            k = min(top_k * 3, len(self.memory_ids))  # 多取一些候选
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1),
                k
            )
            
            # 获取候选记忆
            candidates = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < 0 or idx >= len(self.memory_ids):
                    continue
                
                memory_id = self.memory_ids[idx]
                memory = self.memories[memory_id]
                
                # 类型过滤
                if memory_types and memory.memory_type not in memory_types:
                    continue
                
                # 重要性过滤
                if memory.importance < min_importance:
                    continue
                
                # 综合评分
                score = (
                    float(distance) * 0.6 +  # 相似度
                    memory.importance * 0.3 +
                    min(memory.access_count / 100, 0.1)
                )
                
                candidates.append((memory, score))
        else:
            # 简化模式
            candidates = self._simple_search(query, memory_types, min_importance)
        
        # 排序并返回
        candidates.sort(key=lambda x: x[1], reverse=True)
        results = [mem for mem, _ in candidates[:top_k]]
        
        # 更新访问记录
        for memory in results:
            memory.access_count += 1
            memory.last_access = datetime.now()
        
        return results
    
    def batch_add_memories(
        self,
        memories_data: List[Dict[str, Any]]
    ) -> List[str]:
        """批量添加记忆（更高效）"""
        if not memories_data:
            return []
        
        memory_ids = []
        contents = []
        
        # 准备数据
        for data in memories_data:
            memory_id = f"{data['type']}_{datetime.now().timestamp()}_{len(self.memories)}"
            
            memory = UnifiedMemory(
                id=memory_id,
                user_id=self.user_id,
                memory_type=MemoryType(data['type']),
                content=data['content'],
                metadata=data.get('metadata', {}),
                timestamp=datetime.now(),
                importance=data.get('importance', 0.5),
                related_memories=[]
            )
            
            self.memories[memory_id] = memory
            self.memory_ids.append(memory_id)
            self.type_index[memory.memory_type].append(memory_id)
            
            memory_ids.append(memory_id)
            contents.append(data['content'])
        
        # 批量生成embeddings
        if PRODUCTION_MODE and self.model:
            embeddings = self.model.encode(
                contents,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=32,
                show_progress_bar=True
            )
            self.index.add(embeddings)
        
        self.save_memories()
        return memory_ids
    
    def get_all_memories(
        self,
        memory_types: Optional[List[MemoryType]] = None
    ) -> List[UnifiedMemory]:
        """获取所有记忆（可按类型过滤）"""
        if memory_types:
            result = []
            for mem_type in memory_types:
                for mem_id in self.type_index[mem_type]:
                    result.append(self.memories[mem_id])
            return result
        else:
            return list(self.memories.values())
    
    def get_context_for_conversation(
        self,
        current_query: str,
        max_memories: int = 5
    ) -> str:
        """为对话获取上下文 - 使用大模型总结"""
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
        
        if not memories:
            return "暂无相关历史记忆"
        
        # 如果有大模型，用它来总结上下文
        try:
            from llm.llm_service import get_llm_service
            llm = get_llm_service()
            
            if llm:
                # 构建记忆文本
                memory_texts = []
                for i, memory in enumerate(memories, 1):
                    memory_texts.append(
                        f"{i}. [{memory.memory_type.value}] {memory.content} "
                        f"(重要性: {memory.importance:.2f})"
                    )
                
                prompt = f"""
用户查询: {current_query}

相关历史记忆:
{chr(10).join(memory_texts)}

请总结这些记忆，提取与当前查询最相关的信息。要求：
1. 简洁明了
2. 突出重点
3. 保留关键细节
"""
                
                summary = llm.chat([
                    {"role": "system", "content": "你是记忆总结专家，擅长提取关键信息。"},
                    {"role": "user", "content": prompt}
                ], temperature=0.3)
                
                return summary
        except Exception as e:
            print(f"大模型总结失败，使用原始记忆: {e}")
        
        # 降级：直接返回记忆列表
        context_parts = []
        for memory in memories:
            context_parts.append(
                f"[{memory.memory_type.value}] {memory.content}"
            )
        
        return "\n".join(context_parts)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "production_mode": PRODUCTION_MODE,
            "total_memories": len(self.memories),
            "embedding_dim": self.embedding_dim,
            "gpu_enabled": self.use_gpu if PRODUCTION_MODE else False,
            "by_type": {},
            "importance_distribution": {
                "high": 0,
                "medium": 0,
                "low": 0
            }
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
        
        return stats
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """简化的embedding（无GPU）"""
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.randn(self.embedding_dim)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def _simple_search(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]],
        min_importance: float
    ) -> List[tuple]:
        """简化的搜索（无GPU）"""
        query_embedding = self._simple_embedding(query)
        
        candidates = []
        for memory in self.memories.values():
            if memory_types and memory.memory_type not in memory_types:
                continue
            if memory.importance < min_importance:
                continue
            
            mem_embedding = self._simple_embedding(memory.content)
            similarity = float(np.dot(query_embedding, mem_embedding))
            
            score = (
                similarity * 0.6 +
                memory.importance * 0.3 +
                min(memory.access_count / 100, 0.1)
            )
            
            candidates.append((memory, score))
        
        return candidates
    
    def save_memories(self):
        """保存记忆"""
        # 保存记忆元数据
        metadata_path = os.path.join(
            self.storage_path,
            f"{self.user_id}_metadata.json"
        )
        
        data = {
            "user_id": self.user_id,
            "memories": [
                {
                    "id": m.id,
                    "memory_type": m.memory_type.value,
                    "content": m.content,
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
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 保存FAISS索引 - 纯GPU模式
        if PRODUCTION_MODE and self.index:
            index_path = os.path.join(
                self.storage_path,
                f"{self.user_id}_faiss.index"
            )
            try:
                if self.use_gpu and hasattr(self, 'gpu_resources') and self.gpu_resources:
                    # GPU模式：保存向量数据，不转换为CPU
                    # 提取所有向量数据
                    if self.index.ntotal > 0:
                        vectors = self.index.reconstruct_n(0, self.index.ntotal)
                        # 保存为numpy数组
                        vectors_path = os.path.join(
                            self.storage_path,
                            f"{self.user_id}_vectors.npy"
                        )
                        np.save(vectors_path, vectors)
                        print(f"   ✓ GPU向量数据已保存 ({self.index.ntotal} 个向量)")
                else:
                    # CPU模式：直接保存索引
                    faiss.write_index(self.index, index_path)
                    print(f"   ✓ CPU索引已保存")
            except Exception as e:
                print(f"⚠️  保存FAISS索引失败: {e}")
    
    def load_memories(self):
        """加载记忆"""
        metadata_path = os.path.join(
            self.storage_path,
            f"{self.user_id}_metadata.json"
        )
        
        if not os.path.exists(metadata_path):
            return
        
        try:
            # 加载元数据
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for mem_data in data["memories"]:
                memory = UnifiedMemory(
                    id=mem_data["id"],
                    user_id=self.user_id,
                    memory_type=MemoryType(mem_data["memory_type"]),
                    content=mem_data["content"],
                    metadata=mem_data["metadata"],
                    timestamp=datetime.fromisoformat(mem_data["timestamp"]),
                    importance=mem_data["importance"],
                    access_count=mem_data.get("access_count", 0),
                    last_access=datetime.fromisoformat(mem_data["last_access"]) if mem_data.get("last_access") else None,
                    related_memories=mem_data.get("related_memories", [])
                )
                
                self.memories[memory.id] = memory
                self.memory_ids.append(memory.id)
                self.type_index[memory.memory_type].append(memory.id)
            
            # 加载FAISS索引 - 纯GPU模式
            if PRODUCTION_MODE:
                vectors_path = os.path.join(
                    self.storage_path,
                    f"{self.user_id}_vectors.npy"
                )
                index_path = os.path.join(
                    self.storage_path,
                    f"{self.user_id}_faiss.index"
                )
                
                # GPU模式：直接从向量数据重建GPU索引
                if self.use_gpu and hasattr(self, 'gpu_resources') and self.gpu_resources:
                    if os.path.exists(vectors_path):
                        try:
                            vectors = np.load(vectors_path)
                            self.index.add(vectors)
                            print(f"✅ 加载了 {self.index.ntotal} 个向量（纯GPU模式）")
                        except Exception as e:
                            print(f"⚠️ GPU向量加载失败: {e}")
                # CPU模式：从索引文件加载
                elif os.path.exists(index_path):
                    try:
                        self.index = faiss.read_index(index_path)
                        print(f"✅ 加载了 {self.index.ntotal} 个向量（CPU模式）")
                    except Exception as e:
                        print(f"⚠️ CPU索引加载失败: {e}")
            
        except Exception as e:
            print(f"Failed to load memories: {e}")


# 安装说明
def print_installation_guide():
    """打印安装指南"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          生产级RAG系统 - 安装指南                              ║
╚══════════════════════════════════════════════════════════════╝

📦 CPU版本（适合开发测试）:
   pip install sentence-transformers faiss-cpu

🚀 GPU版本（生产环境推荐）:
   pip install sentence-transformers faiss-gpu

💡 推荐配置:
   - GPU: NVIDIA GPU with CUDA support
   - 内存: 至少8GB RAM
   - 存储: SSD推荐

🔧 模型下载:
   首次运行会自动下载模型（约400MB）
   可以预先下载: python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

📊 性能对比:
   - CPU模式: ~50 queries/sec
   - GPU模式: ~500 queries/sec (10x faster)
   - 批量处理: GPU可达5000+ embeddings/sec
    """)


if __name__ == "__main__":
    if not PRODUCTION_MODE:
        print_installation_guide()
