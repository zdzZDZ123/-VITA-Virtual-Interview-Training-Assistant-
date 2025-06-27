import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import traceback
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """错误分类"""
    NETWORK = "network"
    API = "api"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    SYSTEM = "system"
    UNKNOWN = "unknown"

@dataclass
class ErrorInfo:
    """错误信息"""
    timestamp: datetime
    error_type: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    traceback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    resolved: bool = False

class RetryConfig:
    """重试配置"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """计算重试延迟时间"""
        if attempt <= 0:
            return 0
        
        # 指数退避
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        # 添加抖动
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay

class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self):
        self._error_history: List[ErrorInfo] = []
        self._max_history = 1000
        self._error_patterns: Dict[str, ErrorCategory] = {
            "connection": ErrorCategory.NETWORK,
            "timeout": ErrorCategory.NETWORK,
            "network": ErrorCategory.NETWORK,
            "api_key": ErrorCategory.AUTHENTICATION,
            "unauthorized": ErrorCategory.AUTHENTICATION,
            "forbidden": ErrorCategory.AUTHENTICATION,
            "rate_limit": ErrorCategory.RATE_LIMIT,
            "quota": ErrorCategory.RATE_LIMIT,
            "validation": ErrorCategory.VALIDATION,
            "invalid": ErrorCategory.VALIDATION,
        }
    
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """根据错误信息自动分类"""
        error_msg = str(error).lower()
        
        for pattern, category in self._error_patterns.items():
            if pattern in error_msg:
                return category
        
        # 根据异常类型分类
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorCategory.VALIDATION
        elif "api" in error_msg or "client" in error_msg:
            return ErrorCategory.API
        
        return ErrorCategory.UNKNOWN
    
    def determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """确定错误严重程度"""
        error_msg = str(error).lower()
        
        # 关键词映射
        critical_keywords = ["critical", "fatal", "crash", "system"]
        high_keywords = ["failed", "error", "exception", "unauthorized"]
        medium_keywords = ["warning", "timeout", "retry"]
        
        if any(keyword in error_msg for keyword in critical_keywords):
            return ErrorSeverity.CRITICAL
        elif category == ErrorCategory.AUTHENTICATION:
            return ErrorSeverity.HIGH
        elif any(keyword in error_msg for keyword in high_keywords):
            return ErrorSeverity.HIGH
        elif any(keyword in error_msg for keyword in medium_keywords):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None
    ) -> ErrorInfo:
        """记录错误信息"""
        
        # 自动分类和评级
        if category is None:
            category = self.categorize_error(error)
        if severity is None:
            severity = self.determine_severity(error, category)
        
        error_info = ErrorInfo(
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            message=str(error),
            category=category,
            severity=severity,
            traceback=traceback.format_exc(),
            context=context or {}
        )
        
        # 添加到历史记录
        self._error_history.append(error_info)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)
        
        # 根据严重程度记录日志
        log_msg = f"[{category.value.upper()}] {error_info.message}"
        if context:
            log_msg += f" | Context: {context}"
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_msg)
        elif severity == ErrorSeverity.HIGH:
            logger.error(log_msg)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
        
        return error_info
    
    def get_error_stats(self, hours: int = 1) -> Dict[str, Any]:
        """获取错误统计信息"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self._error_history if e.timestamp >= cutoff_time]
        
        if not recent_errors:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "most_common": []
            }
        
        # 按分类统计
        by_category = {}
        for error in recent_errors:
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        # 按严重程度统计
        by_severity = {}
        for error in recent_errors:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # 最常见的错误
        error_counts = {}
        for error in recent_errors:
            key = f"{error.error_type}: {error.message[:50]}"
            error_counts[key] = error_counts.get(key, 0) + 1
        
        most_common = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_errors": len(recent_errors),
            "by_category": by_category,
            "by_severity": by_severity,
            "most_common": most_common,
            "time_range_hours": hours
        }
    
    def should_retry(self, error: Exception, attempt: int, max_retries: int) -> bool:
        """判断是否应该重试"""
        if attempt >= max_retries:
            return False
        
        category = self.categorize_error(error)
        
        # 不应重试的错误类型
        no_retry_categories = {
            ErrorCategory.AUTHENTICATION,  # 认证错误
            ErrorCategory.VALIDATION      # 验证错误
        }
        
        if category in no_retry_categories:
            return False
        
        # 特定错误消息不重试
        no_retry_messages = [
            "invalid api key",
            "unauthorized",
            "forbidden",
            "not found",
            "bad request"
        ]
        
        error_msg = str(error).lower()
        if any(msg in error_msg for msg in no_retry_messages):
            return False
        
        return True

def with_retry(
    retry_config: Optional[RetryConfig] = None,
    exceptions: Union[Type[Exception], tuple] = Exception,
    on_retry: Optional[Callable] = None
):
    """重试装饰器"""
    if retry_config is None:
        retry_config = RetryConfig()
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            last_exception = None
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    error_info = error_handler.log_error(e, {
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "max_retries": retry_config.max_retries
                    })
                    
                    if not error_handler.should_retry(e, attempt, retry_config.max_retries):
                        logger.error(f"❌ {func.__name__} 不可重试的错误: {e}")
                        raise e
                    
                    if attempt < retry_config.max_retries:
                        delay = retry_config.get_delay(attempt + 1)
                        logger.warning(f"⚠️ {func.__name__} 第{attempt + 1}次尝试失败，{delay:.2f}秒后重试: {e}")
                        
                        if on_retry:
                            try:
                                await on_retry(e, attempt + 1)
                            except Exception as retry_error:
                                logger.error(f"重试回调函数出错: {retry_error}")
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"❌ {func.__name__} 达到最大重试次数，最终失败: {e}")
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            last_exception = None
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    error_info = error_handler.log_error(e, {
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "max_retries": retry_config.max_retries
                    })
                    
                    if not error_handler.should_retry(e, attempt, retry_config.max_retries):
                        logger.error(f"❌ {func.__name__} 不可重试的错误: {e}")
                        raise e
                    
                    if attempt < retry_config.max_retries:
                        delay = retry_config.get_delay(attempt + 1)
                        logger.warning(f"⚠️ {func.__name__} 第{attempt + 1}次尝试失败，{delay:.2f}秒后重试: {e}")
                        
                        if on_retry:
                            try:
                                on_retry(e, attempt + 1)
                            except Exception as retry_error:
                                logger.error(f"重试回调函数出错: {retry_error}")
                        
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ {func.__name__} 达到最大重试次数，最终失败: {e}")
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def handle_errors(
    category: Optional[ErrorCategory] = None,
    severity: Optional[ErrorSeverity] = None,
    reraise: bool = True
):
    """错误处理装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(e, {
                    "function": func.__name__,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                }, category, severity)
                
                if reraise:
                    raise e
                return None
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(e, {
                    "function": func.__name__,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                }, category, severity)
                
                if reraise:
                    raise e
                return None
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

# 全局错误处理器实例
_global_error_handler = ErrorHandler()

def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    return _global_error_handler

def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    category: Optional[ErrorCategory] = None,
    severity: Optional[ErrorSeverity] = None
) -> ErrorInfo:
    """记录错误的便捷函数"""
    return _global_error_handler.log_error(error, context, category, severity)

def get_error_stats(hours: int = 1) -> Dict[str, Any]:
    """获取错误统计的便捷函数"""
    return _global_error_handler.get_error_stats(hours)