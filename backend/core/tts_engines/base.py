"""
TTS引擎抽象基类
定义统一的TTS接口，支持多种引擎实现
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging


logger = logging.getLogger(__name__)


class BaseTTSEngine(ABC):
    """TTS引擎抽象基类"""
    
    # 子类必须设置的属性
    name: str = "base"
    priority: int = 10  # 数字越小优先级越高
    
    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def synthesize(
        self, 
        text: str, 
        voice: str = "nova", 
        speed: float = 1.0,
        **kwargs
    ) -> bytes:
        """
        合成语音的抽象方法
        
        Args:
            text: 要合成的文本
            voice: 声音类型
            speed: 语速倍率 (0.25-4.0)
            **kwargs: 其他引擎特定参数
            
        Returns:
            音频数据 (MP3/WAV格式)
            
        Raises:
            Exception: 合成失败时抛出异常
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查引擎是否可用
        
        Returns:
            True if available, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_supported_voices(self) -> Dict[str, str]:
        """
        获取支持的声音列表
        
        Returns:
            字典，key为voice标识符，value为描述
        """
        raise NotImplementedError
    
    def validate_voice(self, voice: str) -> str:
        """
        验证并标准化voice参数
        
        Args:
            voice: 声音标识符
            
        Returns:
            标准化的voice标识符
        """
        supported = self.get_supported_voices()
        if voice in supported:
            return voice
        
        # 尝试找到默认voice
        defaults = ["nova", "alloy", "echo"]
        for default in defaults:
            if default in supported:
                self.logger.warning(f"Voice '{voice}' 不支持，使用默认voice: {default}")
                return default
        
        # 如果连默认都没有，返回第一个可用的
        if supported:
            fallback = next(iter(supported.keys()))
            self.logger.warning(f"Voice '{voice}' 不支持，使用fallback: {fallback}")
            return fallback
        
        raise ValueError(f"引擎 {self.name} 不支持任何voice")
    
    def validate_speed(self, speed: float) -> float:
        """
        验证并限制语速参数
        
        Args:
            speed: 语速倍率
            
        Returns:
            限制后的语速倍率
        """
        return max(0.25, min(4.0, speed))
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        获取引擎信息
        
        Returns:
            引擎信息字典
        """
        return {
            "name": self.name,
            "priority": self.priority,
            "available": self.is_available(),
            "supported_voices": self.get_supported_voices()
        }
    
    def __str__(self) -> str:
        return f"{self.name}(priority={self.priority})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>" 