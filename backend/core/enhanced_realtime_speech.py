"""
增强实时语音服务模块
整合豆包实时语音交互和本地语音服务，提供智能切换和备用机制
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, AsyncGenerator, List, Callable
from dataclasses import dataclass
from enum import Enum

from .config import config
from .realtime_speech import RealTimeSpeechService, AudioChunk, TranscriptionResult, VoiceActivityState

logger = logging.getLogger(__name__)

class EnhancedVoiceState(Enum):
    """增强语音状态"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"
    SWITCHING_SERVICE = "switching_service"

@dataclass
class EnhancedVoiceResult:
    """增强语音结果"""
    text: str
    confidence: float
    is_final: bool
    timestamp: float
    duration: Optional[float] = None
    emotion: Optional[str] = None
    service_used: str = "doubao"  # 使用的服务类型
    audio_data: Optional[bytes] = None

class EnhancedRealtimeSpeechService:
    """增强实时语音服务
    
    集成豆包实时语音交互（首选）和本地语音服务（备用）
    提供智能切换和故障恢复机制
    """
    
    def __init__(self):
        self.current_state = EnhancedVoiceState.IDLE
        
        # 豆包实时语音服务
        self.doubao_service = None
        self.doubao_available = False
        
        # 本地语音服务
        self.local_service = RealTimeSpeechService()
        self.local_available = True
        
        # 当前使用的服务
        self.current_service = "doubao"  # 默认使用豆包
        self.auto_switch_enabled = config.ENABLE_AUTO_SWITCH
        
        # 回调函数
        self.on_voice_start: Optional[Callable] = None
        self.on_voice_end: Optional[Callable] = None
        self.on_transcription: Optional[Callable[[EnhancedVoiceResult], None]] = None
        self.on_audio_response: Optional[Callable[[bytes], None]] = None
        self.on_state_change: Optional[Callable[[EnhancedVoiceState], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_service_switch: Optional[Callable[[str, str], None]] = None
        
        # 性能统计
        self.stats = {
            "doubao_calls": 0,
            "local_calls": 0,
            "switch_count": 0,
            "error_count": 0
        }
        
        logger.info("增强实时语音服务初始化完成")
    
    async def initialize(self):
        """初始化服务"""
        try:
            # 尝试初始化豆包服务
            await self._init_doubao_service()
            
            # 初始化本地服务
            if hasattr(self.local_service, 'initialize'):
                await self.local_service.initialize()
            
            # 设置回调
            self._setup_callbacks()
            
            logger.info("✅ 增强实时语音服务初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 增强实时语音服务初始化失败: {e}")
            # 如果豆包不可用，直接使用本地服务
            self.current_service = "local"
    
    async def _init_doubao_service(self):
        """初始化豆包服务"""
        try:
            # 尝试创建豆包服务实例
            # 注意：由于豆包实时语音可能还在内测，这里使用模拟实现
            from .doubao_realtime_speech import create_doubao_realtime_service
            
            doubao_key = config.get_doubao_key()
            self.doubao_service = create_doubao_realtime_service(doubao_key)
            
            # 尝试连接
            if await self.doubao_service.connect():
                self.doubao_available = True
                logger.info("✅ 豆包实时语音服务连接成功")
            else:
                self.doubao_available = False
                logger.warning("⚠️ 豆包实时语音服务连接失败，将使用本地服务")
                
        except Exception as e:
            logger.warning(f"⚠️ 豆包服务初始化失败: {e}，将使用本地服务")
            self.doubao_available = False
            self.current_service = "local"
    
    def _setup_callbacks(self):
        """设置服务回调"""
        # 豆包服务回调
        if self.doubao_service:
            self.doubao_service.set_callbacks(
                on_voice_start=self._on_doubao_voice_start,
                on_voice_end=self._on_doubao_voice_end,
                on_transcription=self._on_doubao_transcription,
                on_audio_response=self._on_doubao_audio_response,
                on_error=self._on_doubao_error
            )
        
        # 本地服务回调
        self.local_service.on_speech_start = self._on_local_voice_start
        self.local_service.on_speech_end = self._on_local_voice_end
        self.local_service.on_transcription = self._on_local_transcription
        self.local_service.on_state_change = self._on_local_state_change
    
    async def process_audio_chunk(self, audio_chunk: AudioChunk) -> Optional[EnhancedVoiceResult]:
        """处理音频块"""
        try:
            # 根据当前服务选择处理方式
            if self.current_service == "doubao" and self.doubao_available:
                return await self._process_with_doubao(audio_chunk)
            else:
                return await self._process_with_local(audio_chunk)
                
        except Exception as e:
            logger.error(f"音频处理失败: {e}")
            # 尝试切换服务
            if self.auto_switch_enabled:
                await self._try_switch_service()
            return None
    
    async def _process_with_doubao(self, audio_chunk: AudioChunk) -> Optional[EnhancedVoiceResult]:
        """使用豆包服务处理音频"""
        try:
            self.stats["doubao_calls"] += 1
            
            # 发送音频到豆包服务
            await self.doubao_service.send_audio_chunk(audio_chunk.data)
            
            # 豆包服务是异步的，结果会通过回调返回
            return None
            
        except Exception as e:
            logger.error(f"豆包服务处理失败: {e}")
            # 自动切换到本地服务
            if self.auto_switch_enabled:
                await self._switch_to_local()
                return await self._process_with_local(audio_chunk)
            raise
    
    async def _process_with_local(self, audio_chunk: AudioChunk) -> Optional[EnhancedVoiceResult]:
        """使用本地服务处理音频"""
        try:
            self.stats["local_calls"] += 1
            
            # 使用本地服务处理
            result = await self.local_service.process_audio_chunk(audio_chunk)
            
            if result:
                # 转换为增强结果格式
                enhanced_result = EnhancedVoiceResult(
                    text=result.text,
                    confidence=result.confidence,
                    is_final=result.is_final,
                    timestamp=result.timestamp,
                    duration=result.duration,
                    service_used="local"
                )
                return enhanced_result
            
            return None
            
        except Exception as e:
            logger.error(f"本地服务处理失败: {e}")
            raise
    
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "professional_female",
        speed: float = 1.0,
        interrupt_current: bool = True
    ) -> bytes:
        """合成语音"""
        try:
            # 根据当前服务选择合成方式
            if self.current_service == "doubao" and self.doubao_available:
                return await self._synthesize_with_doubao(text, voice, speed)
            else:
                return await self._synthesize_with_local(text, voice, speed)
                
        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            # 尝试切换服务
            if self.auto_switch_enabled and self.current_service == "doubao":
                await self._switch_to_local()
                return await self._synthesize_with_local(text, voice, speed)
            raise
    
    async def _synthesize_with_doubao(self, text: str, voice: str, speed: float) -> bytes:
        """使用豆包服务合成语音"""
        try:
            # 使用豆包语音合成
            return await self.doubao_service.synthesize_speech(text, voice)
        except Exception as e:
            logger.error(f"豆包语音合成失败: {e}")
            raise
    
    async def _synthesize_with_local(self, text: str, voice: str, speed: float) -> bytes:
        """使用本地服务合成语音"""
        try:
            # 映射豆包声音到本地声音
            local_voice = self._map_voice_to_local(voice)
            return await self.local_service.synthesize_speech(text, local_voice, speed)
        except Exception as e:
            logger.error(f"本地语音合成失败: {e}")
            raise
    
    def _map_voice_to_local(self, doubao_voice: str) -> str:
        """映射豆包语音到本地语音"""
        voice_mapping = {
            "professional_female": "nova",
            "professional_male": "echo",
            "friendly_female": "shimmer",
            "friendly_male": "onyx",
            "casual": "alloy"
        }
        return voice_mapping.get(doubao_voice, "nova")
    
    async def _switch_to_local(self):
        """切换到本地服务"""
        if self.current_service != "local":
            logger.info("🔄 切换到本地语音服务")
            old_service = self.current_service
            self.current_service = "local"
            self.stats["switch_count"] += 1
            
            if self.on_service_switch:
                await self.on_service_switch(old_service, "local")
    
    async def _try_switch_service(self):
        """尝试切换服务"""
        if self.current_service == "doubao":
            await self._switch_to_local()
        # 可以在这里添加重试豆包服务的逻辑
    
    # 豆包服务回调方法
    async def _on_doubao_voice_start(self):
        """豆包语音开始回调"""
        self._change_state(EnhancedVoiceState.LISTENING)
        if self.on_voice_start:
            await self.on_voice_start()
    
    async def _on_doubao_voice_end(self):
        """豆包语音结束回调"""
        self._change_state(EnhancedVoiceState.PROCESSING)
        if self.on_voice_end:
            await self.on_voice_end()
    
    async def _on_doubao_transcription(self, result):
        """豆包转录结果回调"""
        enhanced_result = EnhancedVoiceResult(
            text=result.text,
            confidence=result.confidence,
            is_final=result.is_final,
            timestamp=result.timestamp,
            duration=result.duration,
            emotion=result.emotion,
            service_used="doubao"
        )
        
        if self.on_transcription:
            await self.on_transcription(enhanced_result)
    
    async def _on_doubao_audio_response(self, audio_data: bytes):
        """豆包音频响应回调"""
        if self.on_audio_response:
            await self.on_audio_response(audio_data)
    
    async def _on_doubao_error(self, error_msg: str):
        """豆包错误回调"""
        logger.error(f"豆包服务错误: {error_msg}")
        self.stats["error_count"] += 1
        
        # 自动切换到本地服务
        if self.auto_switch_enabled:
            await self._switch_to_local()
    
    # 本地服务回调方法
    async def _on_local_voice_start(self):
        """本地语音开始回调"""
        self._change_state(EnhancedVoiceState.LISTENING)
        if self.on_voice_start:
            await self.on_voice_start()
    
    async def _on_local_voice_end(self):
        """本地语音结束回调"""
        self._change_state(EnhancedVoiceState.PROCESSING)
        if self.on_voice_end:
            await self.on_voice_end()
    
    async def _on_local_transcription(self, result: TranscriptionResult):
        """本地转录结果回调"""
        enhanced_result = EnhancedVoiceResult(
            text=result.text,
            confidence=result.confidence,
            is_final=result.is_final,
            timestamp=result.timestamp,
            duration=result.duration,
            service_used="local"
        )
        
        if self.on_transcription:
            await self.on_transcription(enhanced_result)
    
    async def _on_local_state_change(self, new_state: VoiceActivityState):
        """本地状态变化回调"""
        # 映射本地状态到增强状态
        state_mapping = {
            VoiceActivityState.SILENCE: EnhancedVoiceState.IDLE,
            VoiceActivityState.SPEECH: EnhancedVoiceState.LISTENING,
            VoiceActivityState.PROCESSING: EnhancedVoiceState.PROCESSING,
            VoiceActivityState.SPEAKING: EnhancedVoiceState.SPEAKING
        }
        
        enhanced_state = state_mapping.get(new_state, EnhancedVoiceState.IDLE)
        self._change_state(enhanced_state)
    
    def _change_state(self, new_state: EnhancedVoiceState):
        """改变状态"""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            logger.debug(f"增强语音状态变化: {old_state.value} -> {new_state.value}")
            
            if self.on_state_change:
                asyncio.create_task(self.on_state_change(new_state))
    
    def set_callbacks(
        self,
        on_voice_start: Optional[Callable] = None,
        on_voice_end: Optional[Callable] = None,
        on_transcription: Optional[Callable[[EnhancedVoiceResult], None]] = None,
        on_audio_response: Optional[Callable[[bytes], None]] = None,
        on_state_change: Optional[Callable[[EnhancedVoiceState], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_service_switch: Optional[Callable[[str, str], None]] = None
    ):
        """设置回调函数"""
        self.on_voice_start = on_voice_start
        self.on_voice_end = on_voice_end
        self.on_transcription = on_transcription
        self.on_audio_response = on_audio_response
        self.on_state_change = on_state_change
        self.on_error = on_error
        self.on_service_switch = on_service_switch
    
    def get_current_service(self) -> str:
        """获取当前使用的服务"""
        return self.current_service
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "current_service": self.current_service,
            "doubao_available": self.doubao_available,
            "local_available": self.local_available
        }
    
    def get_current_state(self) -> EnhancedVoiceState:
        """获取当前状态"""
        return self.current_state
    
    async def disconnect(self):
        """断开连接"""
        try:
            if self.doubao_service:
                await self.doubao_service.disconnect()
        except Exception as e:
            logger.error(f"断开豆包服务连接时出错: {e}")

# 全局实例
_enhanced_service: Optional[EnhancedRealtimeSpeechService] = None

async def get_enhanced_realtime_service() -> EnhancedRealtimeSpeechService:
    """获取增强实时语音服务实例"""
    global _enhanced_service
    
    if _enhanced_service is None:
        _enhanced_service = EnhancedRealtimeSpeechService()
        await _enhanced_service.initialize()
    
    return _enhanced_service 