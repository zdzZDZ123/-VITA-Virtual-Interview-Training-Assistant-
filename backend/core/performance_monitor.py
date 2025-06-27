"""
性能监控模块
跟踪双模型架构的性能指标和切换情况
增强版本 - 修复内存泄漏和资源管理问题
"""

import time
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict, deque
from contextlib import contextmanager
import logging
import json
import gc
from functools import lru_cache, wraps
from dataclasses import dataclass, field
import psutil
import aiofiles
import weakref

logger = logging.getLogger(__name__)

@dataclass
class MetricData:
    """性能指标数据类"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    avg_duration: float = 0.0
    last_call: Optional[datetime] = None
    error_types: Dict[str, int] = field(default_factory=dict)
    recent_durations: deque = field(default_factory=lambda: deque(maxlen=100))
    created_at: datetime = field(default_factory=datetime.now)  # 添加创建时间

    def is_expired(self, max_age_hours: int = 24) -> bool:
        """检查指标是否过期"""
        if not self.last_call:
            return (datetime.now() - self.created_at).total_seconds() > max_age_hours * 3600
        return (datetime.now() - self.last_call).total_seconds() > max_age_hours * 3600

# 添加async_timeit装饰器
def async_timeit(metric_name: str = None, log_slow_threshold: float = 1.0):
    """
    异步函数性能计时装饰器
    
    Args:
        metric_name: 指标名称，默认使用函数名
        log_slow_threshold: 慢请求阈值（秒），超过则记录警告
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            metric = metric_name or f"{func.__module__}.{func.__name__}"
            
            try:
                # 执行原函数
                result = await func(*args, **kwargs)
                
                # 计算耗时
                duration = time.perf_counter() - start_time
                
                # 记录到性能监控
                monitor = get_performance_monitor()
                monitor.record_api_latency(metric, duration * 1000)  # 转换为毫秒
                
                # 慢请求警告
                if duration > log_slow_threshold:
                    logger.warning(
                        f"Slow API call detected: {metric}",
                        duration_ms=duration * 1000,
                        threshold_ms=log_slow_threshold * 1000,
                        extra={"metric": metric, "duration_ms": duration * 1000}
                    )
                
                return result
                
            except Exception as e:
                # 记录错误
                duration = time.perf_counter() - start_time
                monitor = get_performance_monitor()
                monitor.record_error(f"error.{metric}", str(e))
                monitor.record_api_latency(metric, duration * 1000)
                
                logger.error(f"API call failed: {metric}", error=str(e))
                raise
                
        return wrapper
    return decorator

# 同步函数性能计时装饰器
def timeit(metric_name: str = None, log_slow_threshold: float = 1.0):
    """
    同步函数性能计时装饰器
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            metric = metric_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                
                monitor = get_performance_monitor()
                monitor.record_api_latency(metric, duration * 1000)
                
                if duration > log_slow_threshold:
                    logger.warning(f"Slow call: {metric}", duration_ms=duration * 1000)
                
                return result
                
            except Exception as e:
                duration = time.perf_counter() - start_time
                monitor = get_performance_monitor()
                monitor.record_error(f"error.{metric}", str(e))
                
                logger.error(f"API call failed: {metric}", error=str(e))
                raise
                
        return wrapper
    return decorator

class PerformanceMonitor:
    """性能监控器 - 线程安全版本，增强内存管理"""
    
    def __init__(self, max_history: int = 1000, enable_gc_optimization: bool = True):
        self.max_history = max_history
        self._lock = threading.RLock()  # 使用可重入锁
        self._metrics_lock = threading.RLock()
        
        # 使用更高效的数据结构
        self.metrics: Dict[str, MetricData] = {}
        
        # 切换记录
        self.switch_history = deque(maxlen=max_history)
        
        # 实时指标
        self.current_provider = None
        self.last_switch_time = None
        self.switch_count = 0
        
        # 性能阈值 - 针对豆包实时语音优化
        self.thresholds = {
            "slow_response_ms": 3000,  # 慢响应阈值（毫秒）
            "realtime_voice_ms": 500,  # 实时语音响应阈值（更严格）
            "error_rate_threshold": 0.1,  # 错误率阈值
            "switch_cooldown_seconds": 30,  # 切换冷却时间（缩短）
            "memory_threshold_mb": 300,  # 内存使用阈值（降低）
            "max_metrics": 500,  # 最大指标数量（减少）
            "metric_retention_hours": 12  # 指标保留时间（缩短）
        }
        
        # 内存优化
        self.enable_gc_optimization = enable_gc_optimization
        self._last_gc_time = time.time()
        self._gc_interval = 300  # 5分钟
        self._last_cleanup = time.time()
        self._cleanup_interval = 3600  # 1小时清理一次
        
        # 缓存
        self._summary_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 5  # 缓存5秒
        
        # 统计信息
        self._stats = {
            "total_metrics_created": 0,
            "total_metrics_cleaned": 0,
            "memory_cleanups": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # 启动清理任务
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动定期清理任务"""
        try:
            async def cleanup_loop():
                while True:
                    try:
                        await asyncio.sleep(self._cleanup_interval)
                        await self._cleanup_expired_metrics()
                        self._check_memory_pressure()
                    except Exception as e:
                        logger.warning(f"性能监控清理任务异常: {e}")
            
            # 检查是否有事件循环
            try:
                loop = asyncio.get_running_loop()
                self._cleanup_task = asyncio.create_task(cleanup_loop())
                logger.info("✅ 性能监控清理任务已启动")
            except RuntimeError:
                # 没有运行的事件循环，稍后启动
                logger.debug("⏳ 等待事件循环启动后再启动性能监控清理任务")
        except Exception as e:
            logger.warning(f"启动性能监控清理任务失败: {e}")
    
    async def _cleanup_expired_metrics(self):
        """清理过期的性能指标"""
        try:
            expired_keys = []
            retention_hours = self.thresholds["metric_retention_hours"]
            
            with self._metrics_lock:
                for key, metric in list(self.metrics.items()):
                    if metric.is_expired(retention_hours):
                        expired_keys.append(key)
                
                # 删除过期指标
                for key in expired_keys:
                    del self.metrics[key]
                
                self._stats["total_metrics_cleaned"] += len(expired_keys)
            
            if expired_keys:
                logger.info(f"🧹 清理了 {len(expired_keys)} 个过期性能指标")
            
            # 检查是否超过最大指标数量
            await self._enforce_max_metrics()
            
        except Exception as e:
            logger.error(f"清理过期指标失败: {e}")
    
    async def _enforce_max_metrics(self):
        """强制执行最大指标数量限制"""
        try:
            max_metrics = self.thresholds["max_metrics"]
            
            with self._metrics_lock:
                if len(self.metrics) > max_metrics:
                    # 按最后调用时间排序，删除最旧的指标
                    metrics_by_time = sorted(
                        self.metrics.items(),
                        key=lambda x: x[1].last_call or x[1].created_at
                    )
                    
                    excess_count = len(self.metrics) - max_metrics
                    for i in range(excess_count):
                        key = metrics_by_time[i][0]
                        del self.metrics[key]
                    
                    self._stats["total_metrics_cleaned"] += excess_count
                    logger.info(f"🧹 强制清理了 {excess_count} 个最旧的性能指标")
                    
        except Exception as e:
            logger.error(f"强制清理指标失败: {e}")
    
    def _check_memory_pressure(self):
        """检查内存压力并执行清理"""
        try:
            current_memory = self._get_memory_usage()
            memory_threshold = self.thresholds["memory_threshold_mb"]
            
            if current_memory > memory_threshold:
                logger.warning(f"内存使用过高: {current_memory:.1f}MB > {memory_threshold}MB")
                
                # 清理缓存
                self._clear_cache()
                
                # 强制垃圾回收
                if self.enable_gc_optimization:
                    gc.collect()
                    self._stats["memory_cleanups"] += 1
                
                # 如果内存仍然过高，清理更多指标
                with self._metrics_lock:
                    if len(self.metrics) > 100:
                        # 保留最近的100个指标
                        metrics_by_time = sorted(
                            self.metrics.items(),
                            key=lambda x: x[1].last_call or x[1].created_at,
                            reverse=True
                        )
                        
                        new_metrics = dict(metrics_by_time[:100])
                        cleaned_count = len(self.metrics) - len(new_metrics)
                        self.metrics = new_metrics
                        self._stats["total_metrics_cleaned"] += cleaned_count
                        
                        logger.warning(f"⚠️ 内存压力清理了 {cleaned_count} 个性能指标")
                        
        except Exception as e:
            logger.error(f"检查内存压力失败: {e}")
    
    def _clear_cache(self):
        """清理缓存"""
        with self._lock:
            self._summary_cache = None
            self._cache_timestamp = None
    
    def _get_or_create_metrics(self, key: str) -> MetricData:
        """获取或创建指标数据"""
        with self._metrics_lock:
            if key not in self.metrics:
                self.metrics[key] = MetricData()
                self._stats["total_metrics_created"] += 1
                
                # 检查是否需要清理
                if len(self.metrics) > self.thresholds["max_metrics"] * 1.1:
                    asyncio.create_task(self._enforce_max_metrics())
                    
            return self.metrics[key]
    
    def record_api_call(
        self,
        provider: str,
        function_type: str,
        duration: float,
        success: bool,
        error: Optional[Exception] = None,
        metadata: Optional[Dict] = None
    ):
        """记录API调用 - 线程安全"""
        try:
            key = f"{provider}:{function_type}"
            
            with self._lock:
                metrics = self._get_or_create_metrics(key)
                
                # 更新计数
                metrics.total_calls += 1
                if success:
                    metrics.successful_calls += 1
                else:
                    metrics.failed_calls += 1
                    if error:
                        error_type = type(error).__name__
                        if error_type not in metrics.error_types:
                            metrics.error_types[error_type] = 0
                        metrics.error_types[error_type] += 1
                
                # 更新时长统计
                metrics.total_duration += duration
                metrics.min_duration = min(metrics.min_duration, duration)
                metrics.max_duration = max(metrics.max_duration, duration)
                metrics.avg_duration = metrics.total_duration / metrics.total_calls
                metrics.recent_durations.append(duration)
                
                # 更新最后调用时间
                metrics.last_call = datetime.now()
                
                # 清除缓存
                self._clear_cache()
            
            # 记录慢响应（在锁外执行）
            if duration > self.thresholds["slow_response_ms"] / 1000:
                logger.warning(
                    f"慢响应检测: {provider} {function_type} 耗时 {duration:.2f}秒"
                )
            
            # 定期垃圾回收和清理
            self._check_gc()
            
        except Exception as e:
            logger.error(f"记录API调用失败: {e}", exc_info=True)
    
    def record_provider_switch(
        self,
        from_provider: str,
        to_provider: str,
        reason: str,
        function_type: str
    ):
        """记录提供商切换 - 线程安全"""
        try:
            with self._lock:
                switch_event = {
                    "timestamp": datetime.now(),
                    "from": from_provider,
                    "to": to_provider,
                    "reason": reason,
                    "function_type": function_type
                }
                
                self.switch_history.append(switch_event)
                self.current_provider = to_provider
                self.last_switch_time = datetime.now()
                self.switch_count += 1
                
                # 清除缓存
                self._clear_cache()
            
            logger.info(
                f"提供商切换: {from_provider} -> {to_provider} "
                f"(原因: {reason}, 功能: {function_type})"
            )
            
        except Exception as e:
            logger.error(f"记录提供商切换失败: {e}", exc_info=True)
    
    @lru_cache(maxsize=32)
    def _calculate_success_rate(self, successful: int, total: int) -> float:
        """计算成功率 - 带缓存"""
        return successful / total if total > 0 else 0.0
    
    def get_provider_stats(self, provider: str) -> Dict[str, Any]:
        """获取特定提供商的统计信息 - 优化版本"""
        stats = {
            "provider": provider,
            "functions": {}
        }
        
        with self._lock:
            # 使用列表推导式提高效率
            provider_metrics = [
                (key, metrics) 
                for key, metrics in self.metrics.items() 
                if key.startswith(f"{provider}:")
            ]
        
        for key, metrics in provider_metrics:
            function_type = key.split(":", 1)[1]
            
            # 计算成功率
            success_rate = self._calculate_success_rate(
                metrics.successful_calls, 
                metrics.total_calls
            )
            
            # 计算最近的平均响应时间
            recent_durations = list(metrics.recent_durations)
            recent_avg = (
                sum(recent_durations) / len(recent_durations)
                if recent_durations else 0
            )
            
            stats["functions"][function_type] = {
                "total_calls": metrics.total_calls,
                "success_rate": success_rate,
                "avg_duration": metrics.avg_duration,
                "recent_avg_duration": recent_avg,
                "min_duration": metrics.min_duration if metrics.min_duration != float('inf') else 0,
                "max_duration": metrics.max_duration,
                "error_types": dict(metrics.error_types),
                "last_call": metrics.last_call.isoformat() if metrics.last_call else None
            }
        
        return stats
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要 - 带缓存"""
        # 检查缓存
        if self._summary_cache and self._cache_timestamp:
            if time.time() - self._cache_timestamp < self._cache_ttl:
                self._stats["cache_hits"] += 1
                return self._summary_cache
        
        self._stats["cache_misses"] += 1
        
        with self._lock:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "current_provider": self.current_provider,
                "switch_count": self.switch_count,
                "last_switch": self.last_switch_time.isoformat() if self.last_switch_time else None,
                "providers": {},
                "memory_usage_mb": self._get_memory_usage(),
                "metrics_count": len(self.metrics),
                "stats": dict(self._stats)
            }
            
            # 获取所有提供商
            providers = {key.split(":", 1)[0] for key in self.metrics.keys()}
            
            # 获取每个提供商的统计
            for provider in providers:
                summary["providers"][provider] = self.get_provider_stats(provider)
            
            # 添加切换历史摘要
            if self.switch_history:
                recent_switches = list(self.switch_history)[-10:]  # 最近10次切换
                summary["recent_switches"] = [
                    {
                        "timestamp": switch["timestamp"].isoformat(),
                        "from": switch["from"],
                        "to": switch["to"],
                        "reason": switch["reason"],
                        "function_type": switch["function_type"]
                    }
                    for switch in recent_switches
                ]
            
            # 更新缓存
            self._summary_cache = summary
            self._cache_timestamp = time.time()
        
        return summary
    
    def should_switch_provider(
        self,
        current_provider: str,
        function_type: str
    ) -> Optional[str]:
        """判断是否应该切换提供商 - 优化版本"""
        # 检查冷却时间
        if self.last_switch_time:
            cooldown = timedelta(seconds=self.thresholds["switch_cooldown_seconds"])
            if datetime.now() - self.last_switch_time < cooldown:
                return None
        
        key = f"{current_provider}:{function_type}"
        
        with self._lock:
            metrics = self.metrics.get(key)
        
        if not metrics or metrics.total_calls < 10:
            return None  # 数据不足
        
        # 检查错误率
        error_rate = self._calculate_success_rate(
            metrics.failed_calls, 
            metrics.total_calls
        )
        if error_rate > self.thresholds["error_rate_threshold"]:
            logger.warning(
                f"{current_provider} {function_type} 错误率过高: {error_rate:.2%}"
            )
            return "high_error_rate"
        
        # 检查响应时间
        recent_durations = list(metrics.recent_durations)
        if recent_durations:
            recent_avg = sum(recent_durations) / len(recent_durations)
            if recent_avg > self.thresholds["slow_response_ms"] / 1000:
                logger.warning(
                    f"{current_provider} {function_type} 响应过慢: {recent_avg:.2f}s"
                )
                return "slow_response"
        
        return None
    
    def export_metrics(self, filepath: str):
        """导出性能指标到文件 - 异步版本"""
        try:
            summary = self.get_performance_summary()
            
            # 使用异步写入
            async def _async_write():
                async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(summary, indent=2, ensure_ascii=False))
            
            # 如果在异步上下文中，直接执行
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(_async_write())
            except RuntimeError:
                # 同步环境，使用普通写入
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"性能指标已导出到: {filepath}")
            
        except Exception as e:
            logger.error(f"导出性能指标失败: {e}", exc_info=True)
    
    def reset_metrics(self):
        """重置所有指标 - 线程安全"""
        with self._lock:
            self.metrics.clear()
            self.switch_history.clear()
            self.switch_count = 0
            self.last_switch_time = None
            self._clear_cache()
            
            # 重置统计信息
            self._stats = {
                "total_metrics_created": 0,
                "total_metrics_cleaned": 0,
                "memory_cleanups": 0,
                "cache_hits": 0,
                "cache_misses": 0
            }
            
            # 强制垃圾回收
            if self.enable_gc_optimization:
                gc.collect()
            
        logger.info("性能指标已重置")
    
    def _check_gc(self):
        """检查并执行垃圾回收"""
        if not self.enable_gc_optimization:
            return
        
        current_time = time.time()
        if current_time - self._last_gc_time > self._gc_interval:
            self._last_gc_time = current_time
            gc.collect(0)  # 只收集第0代
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # 如果没有psutil，返回估算值
            import sys
            return sys.getsizeof(self.metrics) / 1024 / 1024
    
    @contextmanager
    def batch_record(self):
        """批量记录上下文管理器"""
        batch_records = []
        
        def batch_record_api_call(**kwargs):
            batch_records.append(kwargs)
        
        # 临时替换记录方法
        original_record = self.record_api_call
        self.record_api_call = batch_record_api_call
        
        try:
            yield
        finally:
            # 恢复原方法
            self.record_api_call = original_record
            
            # 批量处理记录
            with self._lock:
                for record in batch_records:
                    self.record_api_call(**record)
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 取消清理任务
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # 清理所有指标
            self.reset_metrics()
            
            logger.info("✅ PerformanceMonitor资源已清理")
            
        except Exception as e:
            logger.warning(f"⚠️ PerformanceMonitor清理时出现警告: {e}")

    def record_realtime_voice_call(
        self,
        provider: str,
        duration: float,
        success: bool,
        latency: Optional[float] = None,
        audio_quality: Optional[str] = None,
        error: Optional[Exception] = None
    ):
        """记录实时语音调用的专用方法"""
        try:
            # 使用特殊的key标识实时语音调用
            key = f"{provider}:realtime_voice"
            
            with self._lock:
                metrics = self._get_or_create_metrics(key)
                
                # 更新基础统计
                metrics.total_calls += 1
                if success:
                    metrics.successful_calls += 1
                else:
                    metrics.failed_calls += 1
                    if error:
                        error_type = type(error).__name__
                        if error_type not in metrics.error_types:
                            metrics.error_types[error_type] = 0
                        metrics.error_types[error_type] += 1
                
                # 更新时长统计
                metrics.total_duration += duration
                metrics.min_duration = min(metrics.min_duration, duration)
                metrics.max_duration = max(metrics.max_duration, duration)
                metrics.avg_duration = metrics.total_duration / metrics.total_calls
                metrics.recent_durations.append(duration)
                metrics.last_call = datetime.now()
                
                # 清除缓存
                self._clear_cache()
            
            # 实时语音特殊检查
            realtime_threshold = self.thresholds["realtime_voice_ms"] / 1000
            if duration > realtime_threshold:
                logger.warning(
                    f"实时语音响应过慢: {provider} 耗时 {duration:.2f}秒 > {realtime_threshold}秒",
                    extra={
                        "provider": provider,
                        "duration": duration,
                        "threshold": realtime_threshold,
                        "latency": latency,
                        "audio_quality": audio_quality
                    }
                )
            
            # 记录到普通API调用
            self.record_api_call(provider, "realtime_voice", duration, success, error, {
                "latency": latency,
                "audio_quality": audio_quality,
                "is_realtime": True
            })
            
        except Exception as e:
            logger.error(f"记录实时语音调用失败: {e}", exc_info=True)
    
    def get_realtime_voice_performance(self) -> Dict[str, Any]:
        """获取实时语音性能统计"""
        try:
            performance = {
                "providers": {},
                "overall": {
                    "total_calls": 0,
                    "avg_latency": 0,
                    "success_rate": 0,
                    "slow_calls": 0
                }
            }
            
            realtime_threshold = self.thresholds["realtime_voice_ms"] / 1000
            total_calls = 0
            total_duration = 0
            total_success = 0
            slow_calls = 0
            
            with self._lock:
                for key, metrics in self.metrics.items():
                    if ":realtime_voice" in key:
                        provider = key.split(":")[0]
                        
                        # 计算慢调用数量
                        recent_slow = sum(
                            1 for d in metrics.recent_durations 
                            if d > realtime_threshold
                        )
                        
                        performance["providers"][provider] = {
                            "total_calls": metrics.total_calls,
                            "success_rate": metrics.successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0,
                            "avg_duration": metrics.avg_duration,
                            "min_duration": metrics.min_duration if metrics.min_duration != float('inf') else 0,
                            "max_duration": metrics.max_duration,
                            "slow_calls": recent_slow,
                            "error_types": dict(metrics.error_types),
                            "last_call": metrics.last_call.isoformat() if metrics.last_call else None
                        }
                        
                        # 累计总体统计
                        total_calls += metrics.total_calls
                        total_duration += metrics.total_duration
                        total_success += metrics.successful_calls
                        slow_calls += recent_slow
            
            # 计算总体统计
            if total_calls > 0:
                performance["overall"] = {
                    "total_calls": total_calls,
                    "avg_latency": total_duration / total_calls,
                    "success_rate": total_success / total_calls,
                    "slow_calls": slow_calls,
                    "slow_rate": slow_calls / total_calls
                }
            
            return performance
            
        except Exception as e:
            logger.error(f"获取实时语音性能失败: {e}")
            return {"error": str(e)}


class PerformanceContext:
    """性能监控上下文管理器 - 优化版本"""
    
    def __init__(
        self,
        monitor: PerformanceMonitor,
        provider: str,
        function_type: str,
        metadata: Optional[Dict] = None
    ):
        self.monitor = monitor
        self.provider = provider
        self.function_type = function_type
        self.metadata = metadata or {}
        self.start_time = None
        self.success = True
        self.error = None
    
    async def __aenter__(self):
        self.start_time = time.perf_counter()  # 使用更精确的计时器
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        
        if exc_type is not None:
            self.success = False
            self.error = exc_val
            
        # 记录API调用
        self.monitor.record_api_call(
            provider=self.provider,
            function_type=self.function_type,
            duration=duration,
            success=self.success,
            error=self.error,
            metadata=self.metadata
        )
        
# 全局性能监控器实例
_performance_monitor: Optional[PerformanceMonitor] = None
_monitor_lock = threading.Lock()

def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例 - 线程安全"""
    global _performance_monitor
    
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor


# 为了Prometheus指标导出，添加额外的指标跟踪
class PrometheusMetrics:
    """Prometheus指标收集器"""
    
    def __init__(self):
        self._api_latencies = defaultdict(deque)  # API延迟
        self._error_counts = defaultdict(int)     # 错误计数
        self._request_counts = defaultdict(int)   # 请求计数
        self._response_times = defaultdict(deque) # 响应时间
        self._provider_switches = 0               # 切换次数
        self.active_requests = 0                  # 活跃请求数
        self._lock = threading.Lock()
        
        # 最大历史记录
        self.max_history = 1000
    
    def record_api_latency(self, endpoint: str, latency_ms: float):
        """记录API延迟"""
        with self._lock:
            if len(self._api_latencies[endpoint]) >= self.max_history:
                self._api_latencies[endpoint].popleft()
            self._api_latencies[endpoint].append(latency_ms)
    
    def record_error(self, endpoint: str, error: str):
        """记录错误"""
        with self._lock:
            self._error_counts[endpoint] += 1
    
    def increment_switch_count(self):
        """增加切换计数"""
        with self._lock:
            self._provider_switches += 1


# 扩展PerformanceMonitor以支持Prometheus
def _extend_performance_monitor():
    """扩展性能监控器以支持Prometheus指标"""
    monitor = get_performance_monitor()
    
    # 添加Prometheus指标属性
    if not hasattr(monitor, '_prometheus_metrics'):
        monitor._prometheus_metrics = PrometheusMetrics()
        
        # 添加原始的record_api_latency方法
        original_record = monitor.record_api_call
        
        def enhanced_record_api_call(provider, function_type, duration, success, error=None, metadata=None):
            # 调用原方法
            original_record(provider, function_type, duration, success, error, metadata)
            
            # 记录到Prometheus指标
            endpoint = f"{provider}.{function_type}"
            monitor._prometheus_metrics.record_api_latency(endpoint, duration * 1000)
            monitor._prometheus_metrics._request_counts[endpoint] += 1
            
            if not success:
                monitor._prometheus_metrics.record_error(endpoint, str(error) if error else "unknown")
        
        monitor.record_api_call = enhanced_record_api_call
        
        # 添加record_api_latency方法（向后兼容）
        def record_api_latency(endpoint: str, latency_ms: float):
            monitor._prometheus_metrics.record_api_latency(endpoint, latency_ms)
        
        monitor.record_api_latency = record_api_latency
        
        # 添加record_error方法
        def record_error(endpoint: str, error: str):
            monitor._prometheus_metrics.record_error(endpoint, error)
        
        monitor.record_error = record_error
        
        # 修改切换记录以增加计数
        original_switch = monitor.record_provider_switch
        
        def enhanced_switch(from_provider, to_provider, reason, function_type):
            original_switch(from_provider, to_provider, reason, function_type)
            monitor._prometheus_metrics.increment_switch_count()
        
        monitor.record_provider_switch = enhanced_switch
        
        # 添加Prometheus导出方法
        def export_prometheus_metrics() -> str:
            """导出Prometheus格式的指标"""
            import psutil
            
            lines = []
            metrics = monitor._prometheus_metrics
            
            # 导出API延迟指标
            lines.append("# HELP vita_api_latency_milliseconds API调用延迟（毫秒）")
            lines.append("# TYPE vita_api_latency_milliseconds summary")
            
            with metrics._lock:
                for endpoint, latencies in metrics._api_latencies.items():
                    if latencies:
                        recent = list(latencies)
                        avg_latency = sum(recent) / len(recent)
                        lines.append(f'vita_api_latency_milliseconds{{endpoint="{endpoint}",quantile="0.5"}} {avg_latency:.2f}')
                        if recent:
                            sorted_latencies = sorted(recent)
                            p95_idx = int(len(sorted_latencies) * 0.95)
                            p95 = sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else sorted_latencies[-1]
                            lines.append(f'vita_api_latency_milliseconds{{endpoint="{endpoint}",quantile="0.95"}} {p95:.2f}')
            
            # 导出错误率指标
            lines.append("\n# HELP vita_error_rate 错误率")
            lines.append("# TYPE vita_error_rate gauge")
            error_count = sum(metrics._error_counts.values())
            total_requests = sum(metrics._request_counts.values())
            error_rate = error_count / total_requests if total_requests > 0 else 0
            lines.append(f"vita_error_rate {error_rate:.4f}")
            
            # 导出切换次数指标
            lines.append("\n# HELP vita_provider_switch_count 提供商切换次数")
            lines.append("# TYPE vita_provider_switch_count counter")
            with metrics._lock:
                lines.append(f"vita_provider_switch_count {metrics._provider_switches}")
            
            # 导出响应时间指标
            lines.append("\n# HELP vita_response_time_seconds 响应时间（秒）")
            lines.append("# TYPE vita_response_time_seconds histogram")
            
            with monitor._lock:
                for key, metric_data in monitor.metrics.items():
                    provider, function = key.split(":", 1)
                    if metric_data.recent_durations:
                        for duration in list(metric_data.recent_durations):
                            lines.append(f'__REMOVED_API_KEY__{{provider="{provider}",function="{function}",le="{duration:.2f}"}} 1')
            
            # 导出活跃请求数
            lines.append("\n# HELP vita_active_requests 活跃请求数")
            lines.append("# TYPE vita_active_requests gauge")
            lines.append(f"vita_active_requests {metrics.active_requests}")
            
            # 导出内存使用
            lines.append("\n# HELP vita_memory_usage_mb 内存使用（MB）")
            lines.append("# TYPE vita_memory_usage_mb gauge")
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            lines.append(f"vita_memory_usage_mb {memory_mb:.2f}")
            
            # 导出CPU使用率
            lines.append("\n# HELP vita_cpu_usage_percent CPU使用率")
            lines.append("# TYPE vita_cpu_usage_percent gauge")
            cpu_percent = psutil.Process().cpu_percent(interval=0.1)
            lines.append(f"vita_cpu_usage_percent {cpu_percent:.2f}")
            
            return "\n".join(lines) + "\n"
        
        monitor.export_prometheus_metrics = export_prometheus_metrics
    
    return monitor


# 初始化扩展
_extend_performance_monitor() 