"""
缓存管理器
Cache Manager - 支持内存缓存和 Redis
"""
import json
import pickle
from typing import Any, Optional, Dict
from datetime import timedelta
import redis
from .config import config, CacheType


class MemoryCache:
    """内存缓存（简单实现）"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Any] = {}
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        # 简单实现，不处理 TTL
        if len(self._cache) >= self._max_size:
            # 删除最旧的项
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = value
    
    def delete(self, key: str):
        """删除缓存"""
        self._cache.pop(key, None)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._cache


class RedisCache:
    """Redis 缓存"""
    
    def __init__(self):
        self.client = redis.from_url(
            config.get_redis_url(),
            decode_responses=False  # 使用二进制模式
        )
        self.prefix = config.REDIS_PREFIX
    
    def _make_key(self, key: str) -> str:
        """生成带前缀的键"""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            data = self.client.get(self._make_key(key))
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        try:
            data = pickle.dumps(value)
            self.client.setex(
                self._make_key(key),
                timedelta(seconds=ttl),
                data
            )
        except Exception as e:
            print(f"Redis set error: {e}")
    
    def delete(self, key: str):
        """删除缓存"""
        try:
            self.client.delete(self._make_key(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
    
    def clear(self, pattern: str = "*"):
        """清空缓存（按模式）"""
        try:
            keys = self.client.keys(f"{self.prefix}{pattern}")
            if keys:
                self.client.delete(*keys)
        except Exception as e:
            print(f"Redis clear error: {e}")
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.client.exists(self._make_key(key)) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    def incr(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        try:
            return self.client.incr(self._make_key(key), amount)
        except Exception as e:
            print(f"Redis incr error: {e}")
            return 0
    
    def expire(self, key: str, ttl: int):
        """设置过期时间"""
        try:
            self.client.expire(self._make_key(key), ttl)
        except Exception as e:
            print(f"Redis expire error: {e}")


class CacheManager:
    """
    缓存管理器
    根据配置自动选择内存缓存或 Redis
    """
    
    def __init__(self):
        if config.CACHE_TYPE == CacheType.REDIS.value:
            try:
                self.cache = RedisCache()
                print("✓ Redis 缓存已启用")
            except Exception as e:
                print(f"⚠️ Redis 连接失败，使用内存缓存: {e}")
                self.cache = MemoryCache(config.CACHE_MAX_SIZE)
        else:
            self.cache = MemoryCache(config.CACHE_MAX_SIZE)
            print("✓ 内存缓存已启用")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        if ttl is None:
            ttl = config.CACHE_TTL
        self.cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """删除缓存"""
        self.cache.delete(key)
    
    def clear(self, pattern: str = "*"):
        """清空缓存"""
        if hasattr(self.cache, 'clear'):
            if isinstance(self.cache, RedisCache):
                self.cache.clear(pattern)
            else:
                self.cache.clear()
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self.cache.exists(key)
    
    # ========== 高级功能 ==========
    
    def get_or_set(self, key: str, factory, ttl: Optional[int] = None) -> Any:
        """
        获取缓存，如果不存在则调用 factory 函数生成并缓存
        
        Args:
            key: 缓存键
            factory: 生成数据的函数
            ttl: 过期时间（秒）
        
        Returns:
            缓存的数据
        """
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value
    
    def cache_predictions(self, user_id: str, predictions: Dict, ttl: int = 3600):
        """缓存预测结果"""
        key = f"predictions:{user_id}"
        self.set(key, predictions, ttl)
    
    def get_cached_predictions(self, user_id: str) -> Optional[Dict]:
        """获取缓存的预测结果"""
        key = f"predictions:{user_id}"
        return self.get(key)
    
    def cache_user_config(self, user_id: str, config_data: Dict):
        """缓存用户配置"""
        key = f"config:{user_id}"
        self.set(key, config_data, ttl=86400)  # 24 小时
    
    def get_cached_user_config(self, user_id: str) -> Optional[Dict]:
        """获取缓存的用户配置"""
        key = f"config:{user_id}"
        return self.get(key)
    
    def invalidate_user_cache(self, user_id: str):
        """清除用户相关的所有缓存"""
        patterns = [
            f"predictions:{user_id}",
            f"config:{user_id}",
            f"data:{user_id}:*",
            f"suggestions:{user_id}:*"
        ]
        for pattern in patterns:
            if isinstance(self.cache, RedisCache):
                self.cache.clear(pattern)
            else:
                self.delete(pattern)


# 全局缓存管理器实例
cache_manager = CacheManager()
