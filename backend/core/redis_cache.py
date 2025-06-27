"""
Redis缓存管理器 - 使用aiocache + Redis替代内存缓存
高性能、分布式、支持TTL的缓存解决方案
"""

import os
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import logging

from aiocache import Cache
from aiocache.serializers import JsonSerializer, PickleSerializer
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis缓存包装器，提供高性能的分布式缓存"""
    
    def __init__(
        self,
        namespace: str = "vita",
        redis_url: str = None,
        ttl: int = 3600,
        serializer: str = "json"
    ):
        """
        初始化Redis缓存
        
        Args:
            namespace: 缓存命名空间，避免键冲突
            redis_url: Redis连接URL，默认从环境变量获取
            ttl: 默认过期时间（秒）
            serializer: 序列化器类型 (json/pickle)
        """
        self.namespace = namespace
        self.ttl = ttl
        
        # Redis连接配置
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # 选择序列化器
        if serializer == "pickle":
            serializer_class = PickleSerializer
        else:
            serializer_class = JsonSerializer
        
        # 创建aiocache实例
        self.cache = Cache(
            Cache.REDIS,
            endpoint=redis_url.split("://")[1].split("/")[0].split(":")[0],
            port=int(redis_url.split(":")[-1].split("/")[0]) if ":" in redis_url else 6379,
            db=int(redis_url.split("/")[-1]) if "/" in redis_url else 0,
            namespace=namespace,
            ttl=ttl,
            serializer=serializer_class()
        )
        
        # 直接的Redis客户端（用于高级操作）
        self._redis_client = None
        self._redis_url = redis_url
        
        logger.info(f"Redis缓存初始化完成: namespace={namespace}, ttl={ttl}s")
    
    async def _get_redis_client(self):
        """延迟初始化Redis客户端"""
        if self._redis_client is None:
            self._redis_client = await aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=False  # 返回bytes，方便处理二进制数据
            )
        return self._redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的值，如果不存在返回None
        """
        try:
            value = await self.cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit: {self.namespace}:{key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 要缓存的值
            ttl: 过期时间（秒），None使用默认值
            
        Returns:
            是否设置成功
        """
        try:
            ttl = ttl or self.ttl
            await self.cache.set(key, value, ttl=ttl)
            logger.debug(f"Cache set: {self.namespace}:{key}, ttl={ttl}s")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存键"""
        try:
            await self.cache.delete(key)
            logger.debug(f"Cache delete: {self.namespace}:{key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        """清空命名空间下的所有缓存"""
        try:
            await self.cache.clear()
            logger.info(f"Cache cleared: namespace={self.namespace}")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return await self.cache.exists(key)
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    async def increment(self, key: str, delta: int = 1) -> Optional[int]:
        """原子递增操作"""
        try:
            client = await self._get_redis_client()
            full_key = f"{self.namespace}:{key}"
            value = await client.incrby(full_key, delta)
            return value
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None
    
    async def get_many(self, keys: list) -> dict:
        """批量获取缓存"""
        try:
            return await self.cache.multi_get(keys)
        except Exception as e:
            logger.error(f"Cache multi_get error: {e}")
            return {}
    
    async def set_many(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """批量设置缓存"""
        try:
            ttl = ttl or self.ttl
            await self.cache.multi_set(list(mapping.items()), ttl=ttl)
            return True
        except Exception as e:
            logger.error(f"Cache multi_set error: {e}")
            return False
    
    async def close(self):
        """关闭连接"""
        try:
            await self.cache.close()
            if self._redis_client:
                await self._redis_client.close()
            logger.info(f"Redis缓存连接已关闭: namespace={self.namespace}")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e}")


class CacheManager:
    """统一的缓存管理器，管理多个命名空间的缓存"""
    
    def __init__(self):
        self._caches = {}
        self._default_ttls = {
            "chat": 3600,         # 聊天缓存1小时
            "analysis": 7200,     # 分析缓存2小时
            "speech": 1800,       # 语音缓存30分钟
            "session": 86400,     # 会话缓存24小时
            "metrics": 300,       # 指标缓存5分钟
        }
    
    def get_cache(self, namespace: str = "default") -> RedisCache:
        """
        获取指定命名空间的缓存实例
        
        Args:
            namespace: 缓存命名空间
            
        Returns:
            RedisCache实例
        """
        if namespace not in self._caches:
            ttl = self._default_ttls.get(namespace, 3600)
            self._caches[namespace] = RedisCache(
                namespace=f"vita:{namespace}",
                ttl=ttl
            )
        return self._caches[namespace]
    
    async def close_all(self):
        """关闭所有缓存连接"""
        for cache in self._caches.values():
            await cache.close()
        self._caches.clear()


# 全局缓存管理器实例
_cache_manager = CacheManager()


def get_cache(namespace: str = "default") -> RedisCache:
    """获取缓存实例的便捷函数"""
    return _cache_manager.get_cache(namespace)


async def close_all_caches():
    """关闭所有缓存连接"""
    await _cache_manager.close_all()


# 导出
__all__ = [
    "RedisCache",
    "CacheManager",
    "get_cache",
    "close_all_caches"
] 