import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import pickle
import os

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"  # 最近最少使用
    TTL = "ttl"  # 生存时间
    LFU = "lfu"  # 最少使用频率
    FIFO = "fifo"  # 先进先出

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_seconds is None:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def touch(self) -> None:
        """更新访问时间和计数"""
        self.last_accessed = datetime.now()
        self.access_count += 1

class MemoryCache:
    """内存缓存管理器"""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[int] = None,
        strategy: CacheStrategy = CacheStrategy.LRU
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.strategy = strategy
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        
        # 统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def _generate_key(self, key: Union[str, Dict, List]) -> str:
        """生成缓存键"""
        if isinstance(key, str):
            return key
        elif isinstance(key, (dict, list)):
            # 对复杂对象生成哈希键
            key_str = json.dumps(key, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(key_str.encode()).hexdigest()
        else:
            return str(key)
    
    async def get(self, key: Union[str, Dict, List]) -> Optional[Any]:
        """获取缓存值"""
        cache_key = self._generate_key(key)
        
        async with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                self._misses += 1
                return None
            
            # 检查是否过期
            if entry.is_expired:
                del self._cache[cache_key]
                self._misses += 1
                return None
            
            # 更新访问信息
            entry.touch()
            self._hits += 1
            
            logger.debug(f"缓存命中: {cache_key[:20]}...")
            return entry.value
    
    async def set(
        self,
        key: Union[str, Dict, List],
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """设置缓存值"""
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        
        async with self._lock:
            # 如果缓存已满，执行清理策略
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                await self._evict()
            
            entry = CacheEntry(
                key=cache_key,
                value=value,
                ttl_seconds=ttl
            )
            
            self._cache[cache_key] = entry
            logger.debug(f"缓存设置: {cache_key[:20]}... (TTL: {ttl}s)")
    
    async def delete(self, key: Union[str, Dict, List]) -> bool:
        """删除缓存项"""
        cache_key = self._generate_key(key)
        
        async with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug(f"缓存删除: {cache_key[:20]}...")
                return True
            return False
    
    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
            logger.info("缓存已清空")
    
    async def _evict(self) -> None:
        """根据策略清理缓存"""
        if not self._cache:
            return
        
        # 首先清理过期项
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._evictions += 1
        
        # 如果还需要清理，根据策略选择
        if len(self._cache) >= self.max_size:
            if self.strategy == CacheStrategy.LRU:
                # 删除最近最少使用的项
                oldest_key = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].last_accessed
                )
                del self._cache[oldest_key]
                self._evictions += 1
            
            elif self.strategy == CacheStrategy.LFU:
                # 删除使用频率最低的项
                least_used_key = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].access_count
                )
                del self._cache[least_used_key]
                self._evictions += 1
            
            elif self.strategy == CacheStrategy.FIFO:
                # 删除最早创建的项
                oldest_key = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].created_at
                )
                del self._cache[oldest_key]
                self._evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "evictions": self._evictions,
            "strategy": self.strategy.value
        }
    
    async def cleanup_expired(self) -> int:
        """清理过期项"""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
            
            return len(expired_keys)

class PersistentCache(MemoryCache):
    """持久化缓存管理器"""
    
    def __init__(
        self,
        cache_dir: str = "cache",
        max_size: int = 1000,
        default_ttl: Optional[int] = None,
        strategy: CacheStrategy = CacheStrategy.LRU,
        auto_save_interval: int = 300  # 5分钟自动保存
    ):
        super().__init__(max_size, default_ttl, strategy)
        self.cache_dir = cache_dir
        self.auto_save_interval = auto_save_interval
        self._save_task: Optional[asyncio.Task] = None
        self._loaded = False
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
    
    async def _load_cache(self) -> None:
        """从磁盘加载缓存"""
        if self._loaded:
            return
            
        cache_file = os.path.join(self.cache_dir, "cache.pkl")
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    self._cache = pickle.load(f)
                
                # 清理过期项
                await self.cleanup_expired()
                
                logger.info(f"从磁盘加载了 {len(self._cache)} 个缓存项")
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            self._cache = {}
        
        self._loaded = True
    
    async def _save_cache(self) -> None:
        """保存缓存到磁盘"""
        cache_file = os.path.join(self.cache_dir, "cache.pkl")
        
        try:
            async with self._lock:
                with open(cache_file, 'wb') as f:
                    pickle.dump(self._cache, f)
                
                logger.debug(f"缓存已保存到磁盘: {len(self._cache)} 项")
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    async def start_auto_save(self) -> None:
        """启动自动保存"""
        if self._save_task is not None:
            return
        
        self._save_task = asyncio.create_task(self._auto_save_loop())
        logger.info(f"缓存自动保存已启动，间隔: {self.auto_save_interval}秒")
    
    async def stop_auto_save(self) -> None:
        """停止自动保存"""
        if self._save_task:
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass
            self._save_task = None
        
        # 最后保存一次
        await self._save_cache()
        logger.info("缓存自动保存已停止")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项（同步版本）"""
        self._ensure_loaded()
        return super().get(key)
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> None:
        """设置缓存项（同步版本）"""
        self._ensure_loaded()
        super().set(key, value, ttl)
    
    def _ensure_loaded(self) -> None:
        """确保缓存已加载（同步版本）"""
        if self._loaded:
            return
            
        cache_file = os.path.join(self.cache_dir, "cache.pkl")
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    self._cache = pickle.load(f)
                
                logger.info(f"从磁盘加载了 {len(self._cache)} 个缓存项")
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            self._cache = {}
        
        self._loaded = True
    
    async def _auto_save_loop(self) -> None:
        """自动保存循环"""
        while True:
            try:
                await asyncio.sleep(self.auto_save_interval)
                await self._save_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"自动保存失败: {e}")

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        # 不同类型的缓存
        self.chat_cache = MemoryCache(
            max_size=500,
            default_ttl=3600,  # 1小时
            strategy=CacheStrategy.LRU
        )
        
        self.model_cache = MemoryCache(
            max_size=100,
            default_ttl=7200,  # 2小时
            strategy=CacheStrategy.LFU
        )
        
        self.config_cache = MemoryCache(
            max_size=50,
            default_ttl=1800,  # 30分钟
            strategy=CacheStrategy.TTL
        )
        
        # 持久化缓存用于长期数据
        self.persistent_cache = PersistentCache(
            cache_dir="cache/persistent",
            max_size=1000,
            default_ttl=86400,  # 24小时
            strategy=CacheStrategy.LRU
        )
        
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """启动缓存管理器"""
        await self.persistent_cache.start_auto_save()
        
        # 启动定期清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("🗄️ 缓存管理器已启动")
    
    async def stop(self) -> None:
        """停止缓存管理器"""
        await self.persistent_cache.stop_auto_save()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🗄️ 缓存管理器已停止")
    
    async def _cleanup_loop(self) -> None:
        """定期清理循环"""
        while True:
            try:
                await asyncio.sleep(600)  # 每10分钟清理一次
                
                # 清理所有缓存的过期项
                await self.chat_cache.cleanup_expired()
                await self.model_cache.cleanup_expired()
                await self.config_cache.cleanup_expired()
                await self.persistent_cache.cleanup_expired()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"缓存清理出错: {e}")
    
    def get_cache_by_type(self, cache_type: str) -> MemoryCache:
        """根据类型获取缓存"""
        cache_map = {
            "chat": self.chat_cache,
            "model": self.model_cache,
            "config": self.config_cache,
            "persistent": self.persistent_cache
        }
        
        return cache_map.get(cache_type, self.chat_cache)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有缓存的统计信息"""
        return {
            "chat_cache": self.chat_cache.get_stats(),
            "model_cache": self.model_cache.get_stats(),
            "config_cache": self.config_cache.get_stats(),
            "persistent_cache": self.persistent_cache.get_stats()
        }
    
    async def clear_all(self) -> None:
        """清空所有缓存"""
        await self.chat_cache.clear()
        await self.model_cache.clear()
        await self.config_cache.clear()
        await self.persistent_cache.clear()
        
        logger.info("所有缓存已清空")

# 全局缓存管理器实例
_cache_manager = CacheManager()

async def start_cache_manager() -> None:
    """启动缓存管理器"""
    await _cache_manager.start()

async def stop_cache_manager() -> None:
    """停止缓存管理器"""
    await _cache_manager.stop()

def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    return _cache_manager

def get_cache(cache_type: str = "chat") -> MemoryCache:
    """获取指定类型的缓存"""
    return _cache_manager.get_cache_by_type(cache_type)

def cache_key_for_chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    """为聊天请求生成缓存键"""
    key_data = {
        "messages": messages,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    return hashlib.md5(
        json.dumps(key_data, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()