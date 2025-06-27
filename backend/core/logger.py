"""
VITA项目的日志管理模块
使用loguru提供结构化、高性能的日志记录
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger as loguru_logger

# 日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class LoggerConfig:
    """日志配置类"""
    
    # 日志格式
    LOG_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message} | "
        "{extra}"
    )
    
    # 简化格式（用于控制台）
    CONSOLE_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # 文件日志配置
    FILE_CONFIG = {
        "rotation": "10 MB",
        "retention": "30 days",
        "compression": "zip",
        "encoding": "utf-8"
    }

class VITALogger:
    """VITA项目日志器包装类"""
    
    def __init__(self, name: str = "vita"):
        self.name = name
        self._logger = loguru_logger.bind(name=name)
        self._setup_done = False
    
    def setup(self):
        """设置日志器（只执行一次）"""
        if self._setup_done:
            return
            
        # 移除默认处理器
        loguru_logger.remove()
        
        # 添加控制台处理器
        loguru_logger.add(
            sys.stderr,
            format=LoggerConfig.CONSOLE_FORMAT,
            level="INFO",
            colorize=True
        )
        
        # 添加文件处理器
        loguru_logger.add(
            LOG_DIR / "vita_debug.log",
            format=LoggerConfig.LOG_FORMAT,
            level="DEBUG",
            **LoggerConfig.FILE_CONFIG
        )
        
        loguru_logger.add(
            LOG_DIR / "vita_error.log",
            format=LoggerConfig.LOG_FORMAT,
            level="ERROR",
            **LoggerConfig.FILE_CONFIG
        )
        
        self._setup_done = True
    
    def bind(self, **kwargs):
        """绑定额外上下文"""
        return VITALogger(self.name).with_context(kwargs)
    
    def with_context(self, context: Dict[str, Any]):
        """添加上下文信息"""
        new_logger = VITALogger(self.name)
        new_logger._logger = self._logger.bind(**context)
        new_logger._setup_done = self._setup_done
        return new_logger
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        self._logger.bind(**kwargs).debug(message)
    
    def info(self, message: str, **kwargs):
        """信息日志"""
        self._logger.bind(**kwargs).info(message)
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        self._logger.bind(**kwargs).warning(message)
    
    def error(self, message: str, **kwargs):
        """错误日志"""
        self._logger.bind(**kwargs).error(message)
    
    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self._logger.bind(**kwargs).critical(message)
    
    def exception(self, message: str, **kwargs):
        """异常日志（包含堆栈跟踪）"""
        self._logger.bind(**kwargs).exception(message)

# 创建全局日志器实例
logger = VITALogger()
logger.setup()

# 兼容标准logging的函数
def get_logger(name: str = "vita") -> VITALogger:
    """获取日志器实例"""
    return VITALogger(name)

# 向后兼容的函数
def setup_logger():
    """设置日志器（向后兼容）"""
    logger.setup()

# 导出主要接口
__all__ = ["logger", "get_logger", "setup_logger", "VITALogger", "LoggerConfig"] 