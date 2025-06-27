import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from core.client_manager import get_active_clients_count
from .qwen_llama_client import _client_registry

logger = logging.getLogger(__name__)

@dataclass
class HealthMetrics:
    """健康检查指标"""
    timestamp: datetime = field(default_factory=datetime.now)
    active_clients: int = 0
    healthy_clients: int = 0
    unhealthy_clients: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 1.0
        return (self.total_requests - self.failed_requests) / self.total_requests
    
    @property
    def health_score(self) -> float:
        """健康评分 (0-1)"""
        if self.active_clients == 0:
            return 0.0
        
        client_health = self.healthy_clients / self.active_clients
        success_rate = self.success_rate
        response_time_score = max(0, 1 - (self.avg_response_time / 10.0))  # 10秒为基准
        
        return (client_health * 0.4 + success_rate * 0.4 + response_time_score * 0.2)

class HealthMonitor:
    """系统健康监控器"""
    
    def __init__(self, check_interval: float = 60.0):
        self.check_interval = check_interval
        self._metrics_history: List[HealthMetrics] = []
        self._max_history = 100  # 保留最近100次检查记录
        self._is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._request_times: List[float] = []
        self._total_requests = 0
        self._failed_requests = 0
        
    async def start_monitoring(self) -> None:
        """开始健康监控"""
        if self._is_monitoring:
            return
            
        self._is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"🔍 健康监控已启动，检查间隔: {self.check_interval}秒")
    
    async def stop_monitoring(self) -> None:
        """停止健康监控"""
        if not self._is_monitoring:
            return
            
        self._is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("🔍 健康监控已停止")
    
    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self._is_monitoring:
            try:
                metrics = await self._collect_metrics()
                self._add_metrics(metrics)
                
                # 检查健康状态并记录警告
                await self._check_health_alerts(metrics)
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 健康监控出错: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _collect_metrics(self) -> HealthMetrics:
        """收集系统指标"""
        metrics = HealthMetrics()
        
        # 客户端指标
        metrics.active_clients = get_active_clients_count()
        
        # 检查每个客户端的健康状态
        healthy_count = 0
        unhealthy_count = 0
        
        for client in _client_registry:
            try:
                if hasattr(client, '_is_healthy') and client._is_healthy:
                    healthy_count += 1
                else:
                    unhealthy_count += 1
            except Exception:
                unhealthy_count += 1
        
        metrics.healthy_clients = healthy_count
        metrics.unhealthy_clients = unhealthy_count
        
        # 请求指标
        metrics.total_requests = self._total_requests
        metrics.failed_requests = self._failed_requests
        
        # 响应时间指标
        if self._request_times:
            metrics.avg_response_time = sum(self._request_times) / len(self._request_times)
            # 清理旧的响应时间记录
            if len(self._request_times) > 1000:
                self._request_times = self._request_times[-500:]
        
        # 系统资源指标（简化版）
        try:
            import psutil
            process = psutil.Process()
            metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            metrics.cpu_usage_percent = process.cpu_percent()
        except ImportError:
            # psutil未安装时的备用方案
            import tracemalloc
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                metrics.memory_usage_mb = current / 1024 / 1024
        except Exception as e:
            logger.debug(f"收集系统资源指标失败: {e}")
        
        return metrics
    
    def _add_metrics(self, metrics: HealthMetrics) -> None:
        """添加指标到历史记录"""
        self._metrics_history.append(metrics)
        if len(self._metrics_history) > self._max_history:
            self._metrics_history.pop(0)
    
    async def _check_health_alerts(self, metrics: HealthMetrics) -> None:
        """检查健康警报"""
        health_score = metrics.health_score
        
        if health_score < 0.3:
            logger.error(f"🚨 系统健康状况严重: 健康评分 {health_score:.2f}")
        elif health_score < 0.6:
            logger.warning(f"⚠️ 系统健康状况不佳: 健康评分 {health_score:.2f}")
        elif health_score > 0.9:
            logger.debug(f"✅ 系统健康状况良好: 健康评分 {health_score:.2f}")
        
        # 检查客户端健康状态
        if metrics.active_clients > 0 and metrics.healthy_clients == 0:
            logger.error("🚨 所有客户端都不健康！")
        elif metrics.unhealthy_clients > metrics.healthy_clients:
            logger.warning(f"⚠️ 不健康客户端数量 ({metrics.unhealthy_clients}) 超过健康客户端 ({metrics.healthy_clients})")
        
        # 检查响应时间
        if metrics.avg_response_time > 10.0:
            logger.warning(f"⚠️ 平均响应时间过长: {metrics.avg_response_time:.2f}秒")
        
        # 检查成功率
        if metrics.success_rate < 0.8:
            logger.warning(f"⚠️ 请求成功率过低: {metrics.success_rate:.2%}")
    
    def record_request(self, response_time: float, success: bool = True) -> None:
        """记录请求指标"""
        self._request_times.append(response_time)
        self._total_requests += 1
        if not success:
            self._failed_requests += 1
    
    def get_current_metrics(self) -> Optional[HealthMetrics]:
        """获取当前指标"""
        return self._metrics_history[-1] if self._metrics_history else None
    
    def get_metrics_history(self, hours: int = 1) -> List[HealthMetrics]:
        """获取指定时间内的指标历史"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self._metrics_history if m.timestamp >= cutoff_time]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状况摘要"""
        current = self.get_current_metrics()
        if not current:
            return {"status": "unknown", "message": "暂无监控数据"}
        
        health_score = current.health_score
        
        if health_score >= 0.9:
            status = "excellent"
            message = "系统运行状况优秀"
        elif health_score >= 0.7:
            status = "good"
            message = "系统运行状况良好"
        elif health_score >= 0.5:
            status = "fair"
            message = "系统运行状况一般"
        elif health_score >= 0.3:
            status = "poor"
            message = "系统运行状况不佳"
        else:
            status = "critical"
            message = "系统运行状况严重"
        
        return {
            "status": status,
            "message": message,
            "health_score": health_score,
            "metrics": {
                "active_clients": current.active_clients,
                "healthy_clients": current.healthy_clients,
                "success_rate": current.success_rate,
                "avg_response_time": current.avg_response_time,
                "memory_usage_mb": current.memory_usage_mb,
                "cpu_usage_percent": current.cpu_usage_percent
            },
            "timestamp": current.timestamp.isoformat()
        }

# 全局健康监控器实例
_health_monitor = HealthMonitor()

async def start_health_monitoring(check_interval: float = 60.0) -> None:
    """启动健康监控"""
    global _health_monitor
    _health_monitor.check_interval = check_interval
    await _health_monitor.start_monitoring()

async def stop_health_monitoring() -> None:
    """停止健康监控"""
    await _health_monitor.stop_monitoring()

def get_health_monitor() -> HealthMonitor:
    """获取健康监控器实例"""
    return _health_monitor

def record_request_metrics(response_time: float, success: bool = True) -> None:
    """记录请求指标的便捷函数"""
    _health_monitor.record_request(response_time, success)

def get_health_summary() -> Dict[str, Any]:
    """获取健康状况摘要的便捷函数"""
    return _health_monitor.get_health_summary()