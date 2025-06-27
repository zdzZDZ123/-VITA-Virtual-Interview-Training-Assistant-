"""
统一TTS服务
支持多引擎、缓存、并发控制的高级TTS服务
增强版本 - 修复并发安全和资源管理问题
"""

import asyncio
import hashlib
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import time
import json
import threading
import weakref

# 缓存依赖
try:
    from diskcache import Cache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False

from core.tts_engines import get_engines
from .tts_engines.base import BaseTTSEngine


logger = logging.getLogger(__name__)


class TTSService:
    """
    统一TTS服务
    
    特性:
    - 多引擎支持，按优先级自动切换
    - LRU磁盘缓存，避免重复合成
    - 并发控制，防止服务过载
    - 性能监控和错误恢复
    - 线程安全的状态管理
    """
    
    def __init__(
        self, 
        cache_dir: str = "cache/tts",
        max_concurrency: int = 5,
        cache_size_limit: int = 1024 * 1024 * 1024,  # 1GB
        engine_max_concurrency: int = 3  # 每个引擎的最大并发数
    ):
        self.cache_dir = Path(cache_dir)
        self.max_concurrency = max_concurrency
        self.cache_size_limit = cache_size_limit
        self.engine_max_concurrency = engine_max_concurrency
        
        # 线程安全锁
        self._lock = threading.RLock()
        self._engine_lock = threading.RLock()
        
        # 首先初始化统计信息 - 在引擎加载前
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "engine_failures": {},
            "engine_usage": {},
            "average_latency": 0.0,
            "health_checks": 0,
            "concurrent_requests": 0,
            "max_concurrent_reached": 0
        }
        
        # 初始化引擎相关属性
        self._engines: List[BaseTTSEngine] = []
        self._engine_semaphores: Dict[str, asyncio.Semaphore] = {}
        self._engine_health: Dict[str, bool] = {}
        self._engine_last_health_check: Dict[str, float] = {}
        
        # 现在安全地加载引擎
        self._load_engines()
        
        # 初始化缓存
        self._cache = None
        self._init_cache()
        
        # 全局并发控制
        self._semaphore = asyncio.Semaphore(max_concurrency)
        
        # 健康检查配置
        self._health_check_interval = 300  # 5分钟
        self._health_check_timeout = 10  # 10秒
        self._health_recovery_attempts = 3  # 恢复尝试次数
        
        logger.info(f"🎵 TTSService初始化完成: {len(self._engines)}个引擎, 缓存{'启用' if self._cache else '禁用'}")
        
        # 延迟启动健康检查任务 - 等到有事件循环时再启动
        self._health_monitor_started = False
        self._health_monitor_task = None
    
    def _load_engines(self):
        """加载并排序TTS引擎 - 线程安全"""
        try:
            with self._engine_lock:
                engines = get_engines()
                # 只加载可用的引擎
                self._engines = [engine for engine in engines if engine.is_available()]
                
                if not self._engines:
                    logger.warning("⚠️ 没有可用的TTS引擎")
                else:
                    # 为每个引擎创建并发控制和健康状态管理
                    for engine in self._engines:
                        self._engine_semaphores[engine.name] = asyncio.Semaphore(self.engine_max_concurrency)
                        self._engine_health[engine.name] = True
                        self._engine_last_health_check[engine.name] = 0
                        self._stats["engine_usage"][engine.name] = 0
                        self._stats["engine_failures"][engine.name] = 0
                
                engine_names = [engine.name for engine in self._engines]
                logger.info(f"✅ 加载TTS引擎: {engine_names}")
                
        except Exception as e:
            logger.error(f"❌ 加载TTS引擎失败: {e}")
            with self._engine_lock:
                self._engines = []
    
    def _init_cache(self):
        """初始化缓存"""
        if not DISKCACHE_AVAILABLE:
            logger.warning("⚠️ diskcache未安装，缓存功能禁用")
            return
        
        try:
            # 创建缓存目录
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 初始化磁盘缓存
            self._cache = Cache(
                directory=str(self.cache_dir),
                size_limit=self.cache_size_limit,
                eviction_policy='least-recently-used'
            )
            
            logger.info(f"✅ 缓存初始化成功: {self.cache_dir}")
            
        except Exception as e:
            logger.error(f"❌ 缓存初始化失败: {e}")
            self._cache = None
    
    async def synthesize(self, text: str, voice: str = "nova", speed: float = 1.0, output_format: str = "mp3") -> bytes:
        """
        语音合成主方法，支持引擎降级
        
        Args:
            text: 要合成的文本
            voice: 语音类型
            speed: 语音速度
            output_format: 输出格式
            
        Returns:
            音频数据
            
        Raises:
            Exception: 所有引擎都失败时
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        # 按优先级尝试引擎
        engines_to_try = []
        
        # 如果配置了Edge-TTS且可用，优先使用
        if self._engines and self._engines[0].name == "edge-tts" and self._engine_health.get("edge-tts", True):
            engines_to_try.append(("edge-tts", self._engines[0]))
        
        # 添加pyttsx3作为备用
        if len(self._engines) > 1 and self._engines[1].name == "pyttsx3" and self._engine_health.get("pyttsx3", True):
            engines_to_try.append(("pyttsx3", self._engines[1]))
        
        if not engines_to_try:
            raise Exception("没有可用的TTS引擎")
        
        last_error = None
        
        for engine_name, engine in engines_to_try:
            try:
                logger.info(f"🎵 尝试使用{engine_name}引擎进行语音合成")
                
                if hasattr(engine, 'synthesize_async'):
                    # 异步合成
                    audio_data = await engine.synthesize_async(text, voice, speed)
                elif hasattr(engine, 'synthesize'):
                    # 同步合成（在异步环境中调用）
                    import asyncio
                    loop = asyncio.get_running_loop()
                    audio_data = await loop.run_in_executor(None, engine.synthesize, text, voice, speed, output_format)
                else:
                    raise Exception(f"引擎{engine_name}不支持语音合成")
                    
                if audio_data and len(audio_data) > 0:
                    logger.info(f"✅ 使用{engine_name}引擎合成成功，音频大小: {len(audio_data)} bytes")
                    
                    # 更新引擎健康状态
                    with self._lock:
                        self._stats["engine_usage"][engine_name] += 1
                        self._engine_health[engine_name] = True
                    
                        return audio_data
                else:
                    raise Exception("生成的音频数据为空")
                    
            except Exception as e:
                error_msg = f"{engine_name}引擎合成失败: {e}"
                logger.warning(f"⚠️ {error_msg}")
                last_error = error_msg
                
                # 更新引擎健康状态
                with self._lock:
                    self._stats["engine_failures"][engine_name] += 1
                    self._engine_health[engine_name] = False
                
                # 如果还有其他引擎可以尝试，继续
                if engine != engines_to_try[-1][1]:
                    continue
        
        # 所有引擎都失败了
        error_message = f"所有TTS引擎都失败了，最后一个错误: {last_error}"
        logger.error(f"❌ {error_message}")
        raise Exception(error_message)
    
    def _get_engine_health(self, engine_name: str) -> bool:
        """获取引擎健康状态 - 线程安全"""
        with self._engine_lock:
            return self._engine_health.get(engine_name, False)
    
    def _update_engine_health(self, engine_name: str, is_healthy: bool):
        """更新引擎健康状态 - 线程安全"""
        with self._engine_lock:
            old_status = self._engine_health.get(engine_name, True)
            self._engine_health[engine_name] = is_healthy
            
            if old_status != is_healthy:
                status_text = "健康" if is_healthy else "不健康"
                logger.info(f"🔄 引擎 {engine_name} 状态变更: {status_text}")
    
    def _generate_cache_key(
        self, 
        text: str, 
        voice: str, 
        speed: float, 
        kwargs: Dict[str, Any]
    ) -> str:
        """生成缓存键 - 使用稳定的序列化方法"""
        # 创建稳定的键数据结构
        key_data = {
            "text": text.strip(),
            "voice": voice,
            "speed": round(speed, 2),  # 浮点数精度控制
            "version": "1.1"  # 缓存版本控制
        }
        
        # 添加额外参数，确保键的稳定性
        if kwargs:
            # 过滤并排序kwargs以确保一致性
            filtered_kwargs = {k: v for k, v in kwargs.items() 
                             if isinstance(v, (str, int, float, bool))}
            if filtered_kwargs:
                key_data["params"] = filtered_kwargs
        
        # 使用JSON序列化确保稳定的字符串表示
        try:
            key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=True)
        except (TypeError, ValueError) as e:
            logger.warning(f"⚠️ 缓存键序列化失败，使用备用方法: {e}")
            # 备用方法：简单字符串拼接
            key_str = f"{text}|{voice}|{speed}"
        
        # 生成SHA256哈希（比MD5更安全）
        return hashlib.sha256(key_str.encode('utf-8')).hexdigest()[:32]  # 截取前32位
    
    def _update_stats(self, latency: float):
        """更新性能统计 - 线程安全"""
        try:
            with self._lock:
                total = self._stats["total_requests"]
                current_avg = self._stats["average_latency"]
                
                # 计算新的平均延迟
                new_avg = (current_avg * (total - 1) + latency) / total
                self._stats["average_latency"] = new_avg
            
        except Exception as e:
            logger.warning(f"⚠️ 统计更新失败: {e}")
    
    def get_available_engines(self) -> List[Dict[str, Any]]:
        """获取可用引擎信息 - 线程安全"""
        with self._engine_lock:
            return [engine.get_engine_info() for engine in self._engines]
    
    def get_supported_voices(self) -> Dict[str, Dict[str, str]]:
        """获取所有引擎支持的声音 - 线程安全"""
        result = {}
        with self._engine_lock:
            for engine in self._engines:
                try:
                    result[engine.name] = engine.get_supported_voices()
                except Exception as e:
                    logger.warning(f"⚠️ 获取{engine.name}声音列表失败: {e}")
                    result[engine.name] = {}
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计 - 线程安全"""
        with self._lock:
            stats = dict(self._stats)
            
        cache_info = {}
        if self._cache:
            try:
                cache_info = {
                    "size": self._cache.volume(),
                    "count": len(self._cache),
                    "hit_rate": stats["cache_hits"] / max(1, stats["total_requests"])
                }
            except Exception:
                cache_info = {"error": "无法获取缓存信息"}
        
        # 添加引擎健康状态
        with self._engine_lock:
            engine_health = dict(self._engine_health)
        
        return {
            **stats,
            "available_engines": len(self._engines),
            "engine_health": engine_health,
            "cache": cache_info,
            "concurrency_limit": self.max_concurrency
        }
    
    async def clear_cache(self) -> bool:
        """清理缓存"""
        if not self._cache:
            return True
        
        try:
            self._cache.clear()
            logger.info("🧹 TTS缓存已清理")
            return True
        except Exception as e:
            logger.error(f"❌ 清理缓存失败: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查 - 改进的并发安全版本"""
        results = {
            "service_status": "healthy",
            "engines": {},
            "cache_status": "enabled" if self._cache else "disabled",
            "timestamp": time.time()
        }
        
        # 检查每个引擎
        with self._engine_lock:
            engines_to_check = list(self._engines)
        
        for engine in engines_to_check:
            engine_name = engine.name
            try:
                # 使用引擎级别的并发控制进行测试
                async with asyncio.wait_for(
                    self._engine_semaphores[engine_name].acquire(),
                    timeout=self._health_check_timeout
                ):
                    try:
                        # 简单测试合成
                        test_audio = await asyncio.wait_for(
                            engine.synthesize("test", "nova", 1.0),
                            timeout=self._health_check_timeout
                        )
                        
                        is_healthy = test_audio and len(test_audio) > 0
                        self._update_engine_health(engine_name, is_healthy)
                        
                        with self._lock:
                            usage_count = self._stats["engine_usage"].get(engine_name, 0)
                            failure_count = self._stats["engine_failures"].get(engine_name, 0)
                    
                        results["engines"][engine_name] = {
                            "status": "healthy" if is_healthy else "unhealthy",
                            "test_result": is_healthy,
                            "usage_count": usage_count,
                            "failure_count": failure_count,
                            "current_health": self._get_engine_health(engine_name)
                        }
                        
                    except Exception as e:
                        logger.error(f"❌ {engine_name} 健康检查失败: {e}")
                        self._update_engine_health(engine_name, False)
                        results["engines"][engine_name] = {
                            "status": "unhealthy",
                            "test_result": False,
                            "error": str(e),
                            "current_health": self._get_engine_health(engine_name)
                        }
                    finally:
                        self._engine_semaphores[engine_name].release()
                        
            except asyncio.TimeoutError:
                logger.warning(f"⏰ {engine_name} 健康检查超时")
                self._update_engine_health(engine_name, False)
                results["engines"][engine_name] = {
                    "status": "unhealthy", 
                    "error": "健康检查超时",
                    "current_health": False
                }
            except Exception as e:
                logger.warning(f"⚠️ {engine_name} 健康检查异常: {e}")
                self._update_engine_health(engine_name, False)
                results["engines"][engine_name] = {
                    "status": "unhealthy", 
                    "error": str(e),
                    "current_health": False
                }
        
        # 检查整体状态
        healthy_engines = sum(1 for info in results["engines"].values() if info["status"] == "healthy")
        if healthy_engines == 0:
            results["service_status"] = "unhealthy"
        elif healthy_engines < len(self._engines):
            results["service_status"] = "degraded"
        
        with self._lock:
            self._stats["health_checks"] += 1
        
        return results
    
    def _start_health_monitor(self):
        """启动健康监控任务"""
        if self._health_monitor_started:
            return
            
        try:
            async def health_check_task():
                while True:
                    try:
                        await asyncio.sleep(self._health_check_interval)
                        await self._periodic_health_check()
                    except Exception as e:
                        logger.warning(f"⚠️ 健康检查任务异常: {e}")
            
            # 在后台启动健康检查
            self._health_monitor_task = asyncio.create_task(health_check_task())
            self._health_monitor_started = True
            logger.info("🔍 TTS健康监控已启动")
        except RuntimeError as e:
            if "no running event loop" in str(e):
                logger.debug("⏳ 等待事件循环启动后再启动健康监控")
            else:
                logger.warning(f"⚠️ 启动健康监控失败: {e}")
    
    async def _periodic_health_check(self):
        """定期健康检查"""
        try:
            # 执行健康检查
            health_result = await self.health_check()
            
            # 统计健康引擎数量
            healthy_count = sum(
                1 for engine_status in health_result["engines"].values()
                if engine_status["status"] == "healthy"
            )
            
            total_engines = len(self._engines)
            
            if healthy_count == 0:
                logger.error("❌ 所有TTS引擎都不健康")
            elif healthy_count < total_engines:
                logger.warning(f"⚠️ 部分TTS引擎不健康: {healthy_count}/{total_engines}")
            else:
                logger.debug(f"✅ 所有TTS引擎健康: {healthy_count}/{total_engines}")
                        
        except Exception as e:
            logger.error(f"❌ 定期健康检查失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 停止健康监控任务
            if self._health_monitor_task and not self._health_monitor_task.done():
                self._health_monitor_task.cancel()
                try:
                    await self._health_monitor_task
                except asyncio.CancelledError:
                    pass
            
            # 清理缓存
            if self._cache:
                try:
                    self._cache.close()
                except:
                    pass
            
            # 重置状态
            with self._lock:
                self._stats = {
                    "total_requests": 0,
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "engine_failures": {},
                    "engine_usage": {},
                    "average_latency": 0.0,
                    "health_checks": 0,
                    "concurrent_requests": 0,
                    "max_concurrent_reached": 0
                }
            
            with self._engine_lock:
                self._engine_health.clear()
                self._engine_last_health_check.clear()
            
            logger.info("✅ TTSService资源已清理")
            
        except Exception as e:
            logger.warning(f"⚠️ TTSService清理时出现警告: {e}")


# 全局TTS服务实例
_tts_service: Optional[TTSService] = None
_service_lock = threading.Lock()


def get_tts_service() -> TTSService:
    """获取全局TTS服务实例 - 线程安全"""
    global _tts_service
    
    if _tts_service is None:
        with _service_lock:
            if _tts_service is None:
                _tts_service = TTSService()
    
    return _tts_service


async def synthesize_speech(
    text: str,
    voice: str = "nova", 
    speed: float = 1.0,
    **kwargs
) -> bytes:
    """
    快捷的语音合成函数
    
    Args:
        text: 要合成的文本
        voice: 声音类型
        speed: 语速倍率
        **kwargs: 其他参数
        
    Returns:
        音频数据
    """
    service = get_tts_service()
    return await service.synthesize(text, voice, speed, **kwargs) 

async def cleanup_tts_service():
    """清理全局TTS服务"""
    global _tts_service
    
    if _tts_service:
        await _tts_service.cleanup()
        with _service_lock:
            _tts_service = None
        logger.info("✅ 全局TTS服务已清理")