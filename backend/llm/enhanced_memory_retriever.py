"""
增强的历史记忆检索系统
实现语义相似度检索和时间衰减权重
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import json
from enum import Enum
import math


class MemoryType(Enum):
    """记忆类型"""
    CONVERSATION = "conversation"
    SENSOR_DATA = "sensor_data"
    DECISION = "decision"
    FEEDBACK = "feedback"
    INSIGHT = "insight"
    PATTERN = "pattern"


class Memory:
    """记忆对象"""
    
    def __init__(self, memory_id: str, memory_type: MemoryType, content: str,
                 metadata: Dict[str, Any], importance: float = 0.5,
                 timestamp: datetime = None):
        """
        初始化记忆
        
        Args:
            memory_id: 记忆ID
            memory_type: 记忆类型
            content: 记忆内容
            metadata: 元数据
            importance: 重要性（0-1）
            timestamp: 时间戳
        """
        self.memory_id = memory_id
        self.memory_type = memory_type
        self.content = content
        self.metadata = metadata
        self.importance = importance
        self.timestamp = timestamp or datetime.now()
        self.access_count = 0
        self.last_access_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "importance": self.importance,
            "timestamp": self.timestamp.isoformat(),
            "access_count": self.access_count,
            "last_access_time": self.last_access_time.isoformat() if self.last_access_time else None
        }


class EnhancedMemoryRetriever:
    """增强的记忆检索器"""
    
    def __init__(self, user_id: str, max_memories: int = 1000):
        """
        初始化记忆检索器
        
        Args:
            user_id: 用户ID
            max_memories: 最大记忆数
        """
        self.user_id = user_id
        self.max_memories = max_memories
        self.memories: List[Memory] = []
        self.memory_index: Dict[str, Memory] = {}
    
    def add_memory(self, memory_type: MemoryType, content: str, 
                   metadata: Dict[str, Any] = None, importance: float = 0.5) -> str:
        """
        添加记忆
        
        Args:
            memory_type: 记忆类型
            content: 记忆内容
            metadata: 元数据
            importance: 重要性
        
        Returns:
            记忆ID
        """
        memory_id = f"mem_{len(self.memories)}_{datetime.now().timestamp()}"
        memory = Memory(
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
            importance=importance
        )
        
        self.memories.append(memory)
        self.memory_index[memory_id] = memory
        
        # 如果超过最大数量，删除最旧的记忆
        if len(self.memories) > self.max_memories:
            oldest_memory = min(self.memories, key=lambda m: m.timestamp)
            self.memories.remove(oldest_memory)
            del self.memory_index[oldest_memory.memory_id]
        
        return memory_id
    
    def retrieve_by_similarity(self, query: str, top_k: int = 5, 
                              memory_types: List[MemoryType] = None) -> List[Tuple[Memory, float]]:
        """
        按相似度检索记忆
        
        Args:
            query: 查询文本
            top_k: 返回数量
            memory_types: 记忆类型过滤
        
        Returns:
            (记忆, 相似度)列表
        """
        # 过滤记忆
        filtered_memories = self.memories
        if memory_types:
            filtered_memories = [m for m in self.memories if m.memory_type in memory_types]
        
        # 计算相似度
        similarities = []
        for memory in filtered_memories:
            similarity = self._calculate_similarity(query, memory.content)
            # 应用时间衰减
            time_decay = self._calculate_time_decay(memory.timestamp)
            # 应用重要性权重
            final_score = similarity * time_decay * (0.5 + memory.importance)
            similarities.append((memory, final_score))
        
        # 按分数排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 返回top_k
        result = similarities[:top_k]
        
        # 更新访问信息
        for memory, _ in result:
            memory.access_count += 1
            memory.last_access_time = datetime.now()
        
        return result
    
    def retrieve_by_type(self, memory_type: MemoryType, top_k: int = 5) -> List[Memory]:
        """
        按类型检索记忆
        
        Args:
            memory_type: 记忆类型
            top_k: 返回数量
        
        Returns:
            记忆列表
        """
        # 过滤记忆
        filtered_memories = [m for m in self.memories if m.memory_type == memory_type]
        
        # 按时间排序（最新的在前）
        filtered_memories.sort(key=lambda m: m.timestamp, reverse=True)
        
        # 返回top_k
        return filtered_memories[:top_k]
    
    def retrieve_by_metadata(self, metadata_key: str, metadata_value: Any, 
                            top_k: int = 5) -> List[Memory]:
        """
        按元数据检索记忆
        
        Args:
            metadata_key: 元数据键
            metadata_value: 元数据值
            top_k: 返回数量
        
        Returns:
            记忆列表
        """
        # 过滤记忆
        filtered_memories = [
            m for m in self.memories 
            if metadata_key in m.metadata and m.metadata[metadata_key] == metadata_value
        ]
        
        # 按时间排序（最新的在前）
        filtered_memories.sort(key=lambda m: m.timestamp, reverse=True)
        
        # 返回top_k
        return filtered_memories[:top_k]
    
    def retrieve_by_time_range(self, start_time: datetime, end_time: datetime, 
                              top_k: int = 5) -> List[Memory]:
        """
        按时间范围检索记忆
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            top_k: 返回数量
        
        Returns:
            记忆列表
        """
        # 过滤记忆
        filtered_memories = [
            m for m in self.memories 
            if start_time <= m.timestamp <= end_time
        ]
        
        # 按时间排序（最新的在前）
        filtered_memories.sort(key=lambda m: m.timestamp, reverse=True)
        
        # 返回top_k
        return filtered_memories[:top_k]
    
    def retrieve_important_memories(self, top_k: int = 5) -> List[Memory]:
        """
        检索重要记忆
        
        Args:
            top_k: 返回数量
        
        Returns:
            记忆列表
        """
        # 按重要性排序
        sorted_memories = sorted(self.memories, key=lambda m: m.importance, reverse=True)
        
        # 返回top_k
        return sorted_memories[:top_k]
    
    def retrieve_frequently_accessed_memories(self, top_k: int = 5) -> List[Memory]:
        """
        检索频繁访问的记忆
        
        Args:
            top_k: 返回数量
        
        Returns:
            记忆列表
        """
        # 按访问次数排序
        sorted_memories = sorted(self.memories, key=lambda m: m.access_count, reverse=True)
        
        # 返回top_k
        return sorted_memories[:top_k]
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度（改进版本，支持中文）
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            相似度（0-1）
        """
        # 简单的字符级相似度（适用于中文）
        # 将文本转换为字符集合
        chars1 = set(text1.lower())
        chars2 = set(text2.lower())
        
        # 计算Jaccard相似度
        if not chars1 and not chars2:
            return 1.0
        
        intersection = len(chars1 & chars2)
        union = len(chars1 | chars2)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        # 同时考虑子串匹配
        # 检查是否有共同的关键词
        keywords1 = set([w for w in text1 if len(w) > 1])
        keywords2 = set([w for w in text2 if len(w) > 1])
        
        keyword_match = 0
        for kw1 in keywords1:
            for kw2 in keywords2:
                if kw1 in kw2 or kw2 in kw1:
                    keyword_match += 1
        
        keyword_score = min(keyword_match / max(len(keywords1), len(keywords2), 1), 1.0) if keywords1 or keywords2 else 0
        
        # 综合评分
        return jaccard * 0.5 + keyword_score * 0.5
    
    def _calculate_time_decay(self, timestamp: datetime, half_life_days: int = 30) -> float:
        """
        计算时间衰减权重
        
        Args:
            timestamp: 时间戳
            half_life_days: 半衰期（天数）
        
        Returns:
            衰减权重（0-1）
        """
        # 计算时间差
        time_diff = datetime.now() - timestamp
        days_passed = time_diff.total_seconds() / (24 * 3600)
        
        # 计算衰减权重（指数衰减）
        decay = math.exp(-days_passed / half_life_days)
        
        return max(0.1, decay)  # 最小权重为0.1
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Returns:
            统计信息
        """
        type_counts = {}
        for memory_type in MemoryType:
            count = len([m for m in self.memories if m.memory_type == memory_type])
            type_counts[memory_type.value] = count
        
        total_importance = sum(m.importance for m in self.memories)
        avg_importance = total_importance / len(self.memories) if self.memories else 0
        
        total_access = sum(m.access_count for m in self.memories)
        avg_access = total_access / len(self.memories) if self.memories else 0
        
        return {
            "total_memories": len(self.memories),
            "memory_types": type_counts,
            "average_importance": avg_importance,
            "total_access_count": total_access,
            "average_access_count": avg_access,
            "oldest_memory": self.memories[0].timestamp.isoformat() if self.memories else None,
            "newest_memory": self.memories[-1].timestamp.isoformat() if self.memories else None
        }
    
    def export_memories(self) -> List[Dict[str, Any]]:
        """
        导出所有记忆
        
        Returns:
            记忆列表
        """
        return [m.to_dict() for m in self.memories]


def get_enhanced_memory_retriever(user_id: str) -> EnhancedMemoryRetriever:
    """获取增强的记忆检索器实例（单例模式）"""
    # 使用全局字典存储每个用户的实例
    if not hasattr(get_enhanced_memory_retriever, '_instances'):
        get_enhanced_memory_retriever._instances = {}
    
    if user_id not in get_enhanced_memory_retriever._instances:
        get_enhanced_memory_retriever._instances[user_id] = EnhancedMemoryRetriever(user_id)
    
    return get_enhanced_memory_retriever._instances[user_id]

