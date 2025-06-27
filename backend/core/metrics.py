"""
Performance metrics and monitoring for VITA backend
"""
import time
import psutil
import asyncio
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextvars import ContextVar
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response
from core.logger import logger

# Context variable for request metrics
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})

# Prometheus metrics
request_count = Counter(
    'vita_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    '__REMOVED_API_KEY__',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'vita_http_requests_active',
    'Number of active HTTP requests'
)

model_inference_duration = Histogram(
    '__REMOVED_API_KEY__',
    'Model inference duration in seconds',
    ['model_name', 'operation']
)

websocket_connections = Gauge(
    '__REMOVED_API_KEY__',
    'Number of active WebSocket connections'
)

cache_hits = Counter(
    'vita_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'vita_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

system_cpu_usage = Gauge(
    'vita_system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    '__REMOVED_API_KEY__',
    'System memory usage percentage'
)

system_disk_usage = Gauge(
    'vita_system_disk_usage_percent',
    'System disk usage percentage'
)


class MetricsCollector:
    """Collects and manages system metrics"""
    
    def __init__(self):
        self.collection_interval = 60  # seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start collecting system metrics"""
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._collect_metrics())
            logger.info("Metrics collector started")
    
    async def stop(self):
        """Stop collecting system metrics"""
        if self.is_running and self._task:
            self.is_running = False
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("Metrics collector stopped")
    
    async def _collect_metrics(self):
        """Periodically collect system metrics"""
        while self.is_running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                system_cpu_usage.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                system_memory_usage.set(memory.percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                system_disk_usage.set(disk.percent)
                
                logger.debug(
                    "System metrics collected",
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_percent=disk.percent
                )
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(self.collection_interval)


def track_request_metrics(method: str, endpoint: str):
    """Decorator to track HTTP request metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Increment active requests
            active_requests.inc()
            
            # Start timing
            start_time = time.time()
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Record metrics
                duration = time.time() - start_time
                status = getattr(result, 'status_code', 200)
                
                request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                
                request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                return result
                
            except Exception as e:
                # Record error metrics
                duration = time.time() - start_time
                
                request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status=500
                ).inc()
                
                request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                raise
                
            finally:
                # Decrement active requests
                active_requests.dec()
        
        return wrapper
    return decorator


def track_model_inference(model_name: str, operation: str):
    """Decorator to track model inference metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                model_inference_duration.labels(
                    model_name=model_name,
                    operation=operation
                ).observe(duration)
                
                logger.debug(
                    f"Model inference completed",
                    model_name=model_name,
                    operation=operation,
                    duration_ms=duration * 1000
                )
                
                return result
            except Exception as e:
                logger.bind(
                    model_name=model_name,
                    operation=operation,
                    error=str(e)
                ).error(f"Model inference failed")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                model_inference_duration.labels(
                    model_name=model_name,
                    operation=operation
                ).observe(duration)
                
                logger.debug(
                    f"Model inference completed",
                    model_name=model_name,
                    operation=operation,
                    duration_ms=duration * 1000
                )
                
                return result
            except Exception as e:
                logger.bind(
                    model_name=model_name,
                    operation=operation,
                    error=str(e)
                ).error(f"Model inference failed")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_cache_access(cache_type: str):
    """Track cache hit/miss metrics"""
    def track_hit():
        cache_hits.labels(cache_type=cache_type).inc()
        logger.debug(f"Cache hit", cache_type=cache_type)
    
    def track_miss():
        cache_misses.labels(cache_type=cache_type).inc()
        logger.debug(f"Cache miss", cache_type=cache_type)
    
    return track_hit, track_miss


async def get_metrics_response() -> Response:
    """Generate Prometheus metrics response"""
    metrics_data = generate_latest()
    return Response(
        content=metrics_data,
        media_type="text/plain; version=0.0.4"
    )


# Create global metrics collector instance
metrics_collector = MetricsCollector()


def setup_metrics(app):
    """Setup metrics collection for the application"""
    @app.on_event("startup")
    async def start_metrics():
        await metrics_collector.start()
    
    @app.on_event("shutdown")
    async def stop_metrics():
        await metrics_collector.stop()
    
    # Add metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return await get_metrics_response() 