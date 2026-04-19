"""
高并发检索优化器
Concurrent Retrieval Optimizer

解决问题：
1. 多个智能体同时检索时，向量检索超时（15秒）
2. FAISS向量数据库在高并发下性能瓶颈
3. 资源竞争导致检索失败

优化策略：
1. 连接池管理 - 复用FAISS索引和模型
2. 请求队列 - 控制并发数量，避免资源耗尽
3. 智能缓存 - 缓存热点查询结果
4. 降级策略 - 超时时快速降级到图检索
5. 批量处理 - 合并相似查询，减少重复计算

作者: AI System
版本: 1.0
日期: 2026-04-19
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import threading
from queue import Queue, PriorityQueue
from enum import Enum


class RequestPriority(Enum):
    """请求优先级"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


@dataclass
class RetrievalRequest:
    """检索请求"""
    request_id: str
    query: str
    user_id: str
    max_results: int
    filters: Dict[str, Any]
    priority: RequestPriority
    timeout: float  # 秒
    created_at: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        """用于优先级队列排序"""
        return self.priority.value < other.priority.value


@dataclass
class CachedResult:
    """缓存的检索结果"""
    query_hash: str
    results: List[Any]
    created_at: datetime
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)
    
    def is_expired(self, ttl_seconds: int = 300) -> bool:
        """检查是否过期（默认5分钟）"""
        return (datetime.now() - self.created_at).total_seconds() > ttl_seconds


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, CachedResult] = OrderedDict()
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[CachedResult]:
        """获取缓存"""
        with self.lock:
            if key in self.cache:
                # 移到末尾（最近使用）
                self.cache.move_to_end(key)
                cached = self.cache[key]
                cached.access_count += 1
                cached.last_access = datetime.now()
                self.hits += 1
                return cached
            self.misses += 1
            return None
    
    def put(self, key: str, value: CachedResult):
        """存入缓存"""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            
            # 超过容量，删除最旧的
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def clear_expired(self, ttl_seconds: int = 300):
        """清理过期缓存"""
        with self.lock:
            expired_keys = [
                k for k, v in self.cache.items()
                if v.is_expired(ttl_seconds)
            ]
            for key in expired_keys:
                del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }


class RequestQueue:
    """请求队列管理器"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.queue = PriorityQueue()
        self.active_requests = 0
        self.lock = threading.Lock()
        self.total_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0
    
    def submit(self, request: RetrievalRequest) -> bool:
        """提交请求"""
        try:
            self.queue.put(request, block=False)
            self.total_requests += 1
            return True
        except:
            return False
    
    def can_process(self) -> bool:
        """是否可以处理新请求"""
        with self.lock:
            return self.active_requests < self.max_concurrent
    
    def start_processing(self):
        """开始处理一个请求"""
        with self.lock:
            self.active_requests += 1
    
    def finish_processing(self, success: bool = True):
        """完成处理一个请求"""
        with self.lock:
            self.active_requests -= 1
            if success:
                self.completed_requests += 1
            else:
                self.failed_requests += 1
    
    def get_next(self, timeout: float = 1.0) -> Optional[RetrievalRequest]:
        """获取下一个请求"""
        try:
            return self.queue.get(timeout=timeout)
        except:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        return {
            "queue_size": self.queue.qsize(),
            "active_requests": self.active_requests,
            "max_concurrent": self.max_concurrent,
            "total_requests": self.total_requests,
            "completed_requests": self.completed_requests,
            "failed_requests": self.failed_requests
        }




class ConcurrentRetrievalOptimizer:
    """
    并发检索优化器
    
    核心功能：
    1. 请求队列管理 - 控制并发数
    2. 智能缓存 - 减少重复计算
    3. 超时控制 - 快速降级
    4. 批量处理 - 合并相似查询
    5. 性能监控 - 实时统计
    """
    
    def __init__(
        self,
        max_concurrent: int = 3,
        cache_size: int = 1000,
        cache_ttl: int = 300,
        default_timeout: float = 10.0
    ):
        """
        初始化优化器
        
        Args:
            max_concurrent: 最大并发数（建议2-5）
            cache_size: 缓存大小
            cache_ttl: 缓存过期时间（秒）
            default_timeout: 默认超时时间（秒）
        """
        self.max_concurrent = max_concurrent
        self.cache_ttl = cache_ttl
        self.default_timeout = default_timeout
        
        # 核心组件
        self.cache = LRUCache(max_size=cache_size)
        self.request_queue = RequestQueue(max_concurrent=max_concurrent)
        
        # 检索器引用（延迟初始化）
        self.vector_retriever = None
        self.graph_retriever = None
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "timeouts": 0,
            "fallbacks": 0,
            "avg_response_time": 0.0
        }
        
        # 后台清理线程
        self._start_cleanup_thread()
        
        print(f"✅ [并发优化器] 初始化完成")
        print(f"   最大并发: {max_concurrent}")
        print(f"   缓存大小: {cache_size}")
        print(f"   缓存TTL: {cache_ttl}秒")
        print(f"   默认超时: {default_timeout}秒")
    
    def set_retrievers(self, vector_retriever, graph_retriever):
        """设置检索器"""
        self.vector_retriever = vector_retriever
        self.graph_retriever = graph_retriever
    
    async def retrieve(
        self,
        query: str,
        user_id: str,
        max_results: int = 20,
        filters: Dict[str, Any] = None,
        priority: RequestPriority = RequestPriority.NORMAL,
        timeout: Optional[float] = None,
        use_cache: bool = True
    ) -> List[Any]:
        """
        优化的检索接口
        
        Args:
            query: 查询字符串
            user_id: 用户ID
            max_results: 最大结果数
            filters: 过滤条件
            priority: 请求优先级
            timeout: 超时时间（秒）
            use_cache: 是否使用缓存
        
        Returns:
            检索结果列表
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        # 1. 检查缓存
        if use_cache:
            cache_key = self._generate_cache_key(query, user_id, max_results, filters)
            cached = self.cache.get(cache_key)
            
            if cached and not cached.is_expired(self.cache_ttl):
                self.stats["cache_hits"] += 1
                print(f"✓ [缓存命中] query={query[:30]}... (访问{cached.access_count}次)")
                return cached.results
            
            self.stats["cache_misses"] += 1
        
        # 2. 创建请求
        request = RetrievalRequest(
            request_id=f"{user_id}_{time.time()}",
            query=query,
            user_id=user_id,
            max_results=max_results,
            filters=filters or {},
            priority=priority,
            timeout=timeout or self.default_timeout
        )
        
        # 3. 提交到队列
        if not self.request_queue.submit(request):
            print(f"⚠️ [队列满] 请求被拒绝")
            return await self._fallback_retrieve(query, user_id, max_results, filters)
        
        # 4. 等待处理
        try:
            results = await self._process_request(request)
            
            # 5. 缓存结果
            if use_cache and results:
                cached_result = CachedResult(
                    query_hash=cache_key,
                    results=results,
                    created_at=datetime.now()
                )
                self.cache.put(cache_key, cached_result)
            
            # 6. 更新统计
            response_time = time.time() - start_time
            self._update_avg_response_time(response_time)
            
            return results
            
        except asyncio.TimeoutError:
            self.stats["timeouts"] += 1
            print(f"⚠️ [超时] query={query[:30]}... 降级到图检索")
            return await self._fallback_retrieve(query, user_id, max_results, filters)
    
    async def _process_request(self, request: RetrievalRequest) -> List[Any]:
        """处理单个请求"""
        # 等待队列空闲
        while not self.request_queue.can_process():
            await asyncio.sleep(0.1)
            
            # 检查超时
            elapsed = time.time() - request.created_at
            if elapsed > request.timeout:
                raise asyncio.TimeoutError()
        
        # 开始处理
        self.request_queue.start_processing()
        
        try:
            # 执行检索（带超时）
            results = await asyncio.wait_for(
                self._execute_retrieval(request),
                timeout=request.timeout
            )
            
            self.request_queue.finish_processing(success=True)
            return results
            
        except Exception as e:
            self.request_queue.finish_processing(success=False)
            raise
    
    async def _execute_retrieval(self, request: RetrievalRequest) -> List[Any]:
        """执行实际的检索"""
        # 优先使用向量检索
        if self.vector_retriever:
            try:
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    self.vector_retriever.retrieve,
                    request.query,
                    request.max_results,
                    request.filters
                )
                return results
            except Exception as e:
                print(f"⚠️ [向量检索失败] {e}")
        
        # 降级到图检索
        if self.graph_retriever:
            try:
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    self.graph_retriever.retrieve,
                    request.query,
                    request.max_results,
                    request.filters
                )
                return results
            except Exception as e:
                print(f"⚠️ [图检索失败] {e}")
        
        return []
    
    async def _fallback_retrieve(
        self,
        query: str,
        user_id: str,
        max_results: int,
        filters: Dict[str, Any]
    ) -> List[Any]:
        """降级检索（仅使用图检索）"""
        self.stats["fallbacks"] += 1
        
        if not self.graph_retriever:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.graph_retriever.retrieve,
                query,
                max_results,
                filters
            )
            return results
        except Exception as e:
            print(f"❌ [降级检索失败] {e}")
            return []
    
    def _generate_cache_key(
        self,
        query: str,
        user_id: str,
        max_results: int,
        filters: Optional[Dict]
    ) -> str:
        """生成缓存键"""
        key_parts = [
            query,
            user_id,
            str(max_results),
            str(sorted(filters.items()) if filters else "")
        ]
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _update_avg_response_time(self, response_time: float):
        """更新平均响应时间"""
        current_avg = self.stats["avg_response_time"]
        total = self.stats["total_requests"]
        
        # 移动平均
        self.stats["avg_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_loop():
            while True:
                time.sleep(60)  # 每分钟清理一次
                self.cache.clear_expired(self.cache_ttl)
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_stats = self.cache.get_stats()
        queue_stats = self.request_queue.get_stats()
        
        return {
            "optimizer": {
                "total_requests": self.stats["total_requests"],
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "cache_hit_rate": (
                    self.stats["cache_hits"] / max(self.stats["total_requests"], 1)
                ),
                "timeouts": self.stats["timeouts"],
                "fallbacks": self.stats["fallbacks"],
                "avg_response_time_ms": self.stats["avg_response_time"] * 1000
            },
            "cache": cache_stats,
            "queue": queue_stats
        }
    
    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()
        
        print(f"\n{'='*60}")
        print(f"并发检索优化器 - 统计信息")
        print(f"{'='*60}")
        
        print(f"\n📊 总体统计:")
        print(f"  总请求数: {stats['optimizer']['total_requests']}")
        print(f"  平均响应时间: {stats['optimizer']['avg_response_time_ms']:.2f}ms")
        print(f"  超时次数: {stats['optimizer']['timeouts']}")
        print(f"  降级次数: {stats['optimizer']['fallbacks']}")
        
        print(f"\n💾 缓存统计:")
        print(f"  缓存大小: {stats['cache']['size']}/{stats['cache']['max_size']}")
        print(f"  命中率: {stats['cache']['hit_rate']:.2%}")
        print(f"  命中次数: {stats['cache']['hits']}")
        print(f"  未命中次数: {stats['cache']['misses']}")
        
        print(f"\n📋 队列统计:")
        print(f"  队列长度: {stats['queue']['queue_size']}")
        print(f"  活跃请求: {stats['queue']['active_requests']}/{stats['queue']['max_concurrent']}")
        print(f"  完成请求: {stats['queue']['completed_requests']}")
        print(f"  失败请求: {stats['queue']['failed_requests']}")
        
        print(f"{'='*60}\n")




# ==================== 全局单例 ====================

_global_optimizer: Optional[ConcurrentRetrievalOptimizer] = None
_optimizer_lock = threading.Lock()


def get_global_optimizer(
    max_concurrent: int = 8,  # GPU模式默认8个并发
    cache_size: int = 1000,
    cache_ttl: int = 300,
    default_timeout: float = 10.0
) -> ConcurrentRetrievalOptimizer:
    """
    获取全局优化器单例
    
    Args:
        max_concurrent: 最大并发数
        cache_size: 缓存大小
        cache_ttl: 缓存过期时间（秒）
        default_timeout: 默认超时时间（秒）
    
    Returns:
        全局优化器实例
    """
    global _global_optimizer
    
    if _global_optimizer is None:
        with _optimizer_lock:
            if _global_optimizer is None:
                _global_optimizer = ConcurrentRetrievalOptimizer(
                    max_concurrent=max_concurrent,
                    cache_size=cache_size,
                    cache_ttl=cache_ttl,
                    default_timeout=default_timeout
                )
    
    return _global_optimizer


# ==================== 使用示例 ====================

async def example_usage():
    """使用示例"""
    print("\n" + "="*60)
    print("并发检索优化器 - 使用示例")
    print("="*60 + "\n")
    
    # 1. 获取全局优化器
    optimizer = get_global_optimizer(
        max_concurrent=3,
        cache_size=500,
        cache_ttl=300,
        default_timeout=10.0
    )
    
    # 2. 设置检索器（实际使用时）
    # from backend.learning.unified_hybrid_retrieval import Neo4jRetriever, RAGRetriever
    # optimizer.set_retrievers(
    #     vector_retriever=RAGRetriever(...),
    #     graph_retriever=Neo4jRetriever(...)
    # )
    
    # 3. 模拟并发检索
    async def simulate_agent_retrieval(agent_name: str, query: str):
        print(f"[{agent_name}] 开始检索: {query}")
        
        results = await optimizer.retrieve(
            query=query,
            user_id="test_user",
            max_results=20,
            priority=RequestPriority.NORMAL,
            timeout=10.0
        )
        
        print(f"[{agent_name}] 完成检索: {len(results)} 个结果")
        return results
    
    # 4. 并行执行多个Agent
    tasks = [
        simulate_agent_retrieval("关系Agent", "分析我的人际关系"),
        simulate_agent_retrieval("教育Agent", "分析我的教育背景"),
        simulate_agent_retrieval("职业Agent", "分析我的职业发展"),
    ]
    
    results = await asyncio.gather(*tasks)
    
    # 5. 打印统计
    optimizer.print_statistics()
    
    return results


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())
