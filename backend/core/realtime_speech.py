"""实时语音服务模块
专为ChatGPT风格的实时语音交互优化
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, AsyncGenerator, List, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np
from core.speech import SpeechService
from .config import config
from core.whisper_model_manager import get_model_manager

logger = logging.getLogger(__name__)

class VoiceActivityState(Enum):
    """语音活动状态"""
    SILENCE = "silence"
    SPEECH = "speech"
    PROCESSING = "processing"
    SPEAKING = "speaking"

@dataclass
class AudioChunk:
    """音频块数据"""
    data: bytes
    timestamp: float
    sample_rate: int = 16000
    channels: int = 1
    
@dataclass
class VoiceActivityResult:
    """语音活动检测结果"""
    is_speech: bool
    confidence: float
    energy: float
    timestamp: float

@dataclass
class TranscriptionResult:
    """转录结果"""
    text: str
    confidence: float
    is_final: bool
    timestamp: float
    duration: float
    word_count: int

class RealTimeSpeechService:
    """实时语音服务"""
    
    def __init__(self):
        # 检查模型状态
        self._check_model_status()
        
        self.speech_service = SpeechService()
        self.vad_threshold = 0.005  # 语音活动检测阈值（降低以提高灵敏度）
        self.silence_timeout = 2.0  # 静默超时时间（秒）
        self.min_speech_duration = 0.5  # 最小语音持续时间
        self.max_speech_duration = 30.0  # 最大语音持续时间
        
        # 状态管理
        self.current_state = VoiceActivityState.SILENCE
        self.speech_start_time = None
        self.last_speech_time = None
        self.accumulated_audio = bytearray()
        
        # 回调函数
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        self.on_transcription: Optional[Callable[[TranscriptionResult], None]] = None
        self.on_state_change: Optional[Callable[[VoiceActivityState], None]] = None
        
        logger.info("RealTimeSpeechService 初始化完成")
    
    def _check_model_status(self):
        """检查并报告模型状态"""
        try:
            model_manager = get_model_manager()
            local_whisper_config = config.get_local_whisper_config()
            model_size = local_whisper_config.get("model_size", "medium")
            
            model_info = model_manager.get_model_info(model_size)
            if model_info and model_info.get("installed"):
                logger.info(f"✅ Whisper模型 {model_size} 已就绪: {model_info.get('path')}")
            else:
                logger.warning(f"⚠️ Whisper模型 {model_size} 未安装")
                logger.info("💡 提示: 运行以下命令下载模型:")
                logger.info(f"   python scripts/download_faster_whisper.py {model_size}")
        except Exception as e:
            logger.warning(f"检查模型状态时出错: {e}")
    
    def set_callbacks(
        self,
        on_speech_start: Optional[Callable] = None,
        on_speech_end: Optional[Callable] = None,
        on_transcription: Optional[Callable[[TranscriptionResult], None]] = None,
        on_state_change: Optional[Callable[[VoiceActivityState], None]] = None
    ):
        """设置回调函数"""
        self.on_speech_start = on_speech_start
        self.on_speech_end = on_speech_end
        self.on_transcription = on_transcription
        self.on_state_change = on_state_change
    
    def _change_state(self, new_state: VoiceActivityState):
        """改变状态并触发回调"""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            logger.debug(f"状态变化: {old_state.value} -> {new_state.value}")
            
            if self.on_state_change:
                try:
                    self.on_state_change(new_state)
                except Exception as e:
                    logger.error(f"状态变化回调失败: {e}")
    
    def _detect_voice_activity(self, audio_chunk: AudioChunk) -> VoiceActivityResult:
        """简单的语音活动检测"""
        try:
            # 将字节数据转换为numpy数组进行分析
            # 假设是16位PCM数据
            audio_array = np.frombuffer(audio_chunk.data, dtype=np.int16)
            
            # 计算能量
            energy = np.mean(np.abs(audio_array.astype(np.float32))) / 32768.0
            
            # 简单的阈值检测
            is_speech = energy > self.vad_threshold
            confidence = min(energy / self.vad_threshold, 1.0) if is_speech else 0.0
            
            return VoiceActivityResult(
                is_speech=is_speech,
                confidence=confidence,
                energy=energy,
                timestamp=audio_chunk.timestamp
            )
        except Exception as e:
            logger.error(f"语音活动检测失败: {e}")
            return VoiceActivityResult(
                is_speech=False,
                confidence=0.0,
                energy=0.0,
                timestamp=audio_chunk.timestamp
            )
    
    async def process_audio_chunk(self, audio_chunk: AudioChunk) -> Optional[TranscriptionResult]:
        """处理音频块"""
        current_time = time.time()
        vad_result = self._detect_voice_activity(audio_chunk)
        
        # 状态机逻辑
        if self.current_state == VoiceActivityState.SILENCE:
            if vad_result.is_speech:
                # 开始检测到语音
                self.speech_start_time = current_time
                self.last_speech_time = current_time
                self.accumulated_audio = bytearray(audio_chunk.data)
                self._change_state(VoiceActivityState.SPEECH)
                
                if self.on_speech_start:
                    try:
                        await self.on_speech_start()
                    except Exception as e:
                        logger.error(f"语音开始回调失败: {e}")
        
        elif self.current_state == VoiceActivityState.SPEECH:
            if vad_result.is_speech:
                # 继续检测到语音
                self.last_speech_time = current_time
                self.accumulated_audio.extend(audio_chunk.data)
                
                # 检查是否超过最大语音持续时间
                if current_time - self.speech_start_time > self.max_speech_duration:
                    logger.warning("语音持续时间过长，强制结束")
                    return await self._finalize_speech()
            
            else:
                # 检测到静默
                self.accumulated_audio.extend(audio_chunk.data)
                
                # 检查静默持续时间
                if current_time - self.last_speech_time > self.silence_timeout:
                    # 静默超时，结束语音
                    speech_duration = current_time - self.speech_start_time
                    if speech_duration >= self.min_speech_duration:
                        return await self._finalize_speech()
                    else:
                        # 语音太短，忽略
                        logger.debug(f"语音持续时间太短 ({speech_duration:.2f}s)，忽略")
                        self._reset_speech_state()
        
        return None
    
    async def _finalize_speech(self) -> Optional[TranscriptionResult]:
        """完成语音处理"""
        if not self.accumulated_audio:
            self._reset_speech_state()
            return None
        
        self._change_state(VoiceActivityState.PROCESSING)
        
        try:
            # 触发语音结束回调
            if self.on_speech_end:
                try:
                    await self.on_speech_end()
                except Exception as e:
                    logger.error(f"语音结束回调失败: {e}")
            
            # 进行语音识别
            audio_data = bytes(self.accumulated_audio)
            speech_duration = time.time() - self.speech_start_time
            
            logger.info(f"开始转录 {len(audio_data)} 字节音频，持续时间 {speech_duration:.2f}s")
            
            transcription_data = await self.speech_service.speech_to_text(
                audio_data=audio_data,
                language="zh"
            )
            
            # 修复：speech_to_text返回的数据结构不包含success字段
            if transcription_data and transcription_data.get("text"):
                text = transcription_data["text"].strip()
                confidence = transcription_data.get("confidence", 0.95)
                word_count = len(text.split()) if text else 0
                
                result = TranscriptionResult(
                    text=text,
                    confidence=confidence,
                    is_final=True,
                    timestamp=time.time(),
                    duration=speech_duration,
                    word_count=word_count
                )
                
                logger.info(f"转录成功: '{text}' (置信度: {confidence:.2f})")
                
                # 触发转录回调
                if self.on_transcription:
                    try:
                        await self.on_transcription(result)
                    except Exception as e:
                        logger.error(f"转录回调失败: {e}")
                
                self._reset_speech_state()
                return result
            else:
                logger.warning("转录失败或结果为空")
                self._reset_speech_state()
                return None
                
        except Exception as e:
            logger.error(f"语音处理失败: {e}")
            self._reset_speech_state()
            return None
    
    def _reset_speech_state(self):
        """重置语音状态"""
        self.speech_start_time = None
        self.last_speech_time = None
        self.accumulated_audio = bytearray()
        self._change_state(VoiceActivityState.SILENCE)
    
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "nova",
        speed: float = 1.0,
        interrupt_current: bool = True
    ) -> bytes:
        """合成语音"""
        if interrupt_current:
            self._change_state(VoiceActivityState.SPEAKING)
        
        try:
            audio_data = await self.speech_service.text_to_speech(
                text=text,
                voice=voice,
                speed=speed
            )
            
            logger.info(f"语音合成成功: '{text[:50]}...' ({len(audio_data)} 字节)")
            return audio_data
            
        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            raise
        finally:
            if interrupt_current:
                self._change_state(VoiceActivityState.SILENCE)
    
    async def stream_synthesize_speech(
        self,
        text: str,
        voice: str = "nova",
        speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        """流式语音合成"""
        self._change_state(VoiceActivityState.SPEAKING)
        
        try:
            async for chunk in self.speech_service.stream_text_to_speech(
                text=text,
                voice=voice,
                speed=speed
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"流式语音合成失败: {e}")
            raise
        finally:
            self._change_state(VoiceActivityState.SILENCE)
    
    def get_current_state(self) -> VoiceActivityState:
        """获取当前状态"""
        return self.current_state
    
    def is_listening(self) -> bool:
        """是否正在监听"""
        return self.current_state in [VoiceActivityState.SILENCE, VoiceActivityState.SPEECH]
    
    def is_processing(self) -> bool:
        """是否正在处理"""
        return self.current_state == VoiceActivityState.PROCESSING
    
    def is_speaking(self) -> bool:
        """是否正在说话"""
        return self.current_state == VoiceActivityState.SPEAKING
    
    def configure(
        self,
        vad_threshold: Optional[float] = None,
        silence_timeout: Optional[float] = None,
        min_speech_duration: Optional[float] = None,
        max_speech_duration: Optional[float] = None
    ):
        """配置参数"""
        if vad_threshold is not None:
            self.vad_threshold = max(0.001, min(1.0, vad_threshold))
        if silence_timeout is not None:
            self.silence_timeout = max(0.5, min(10.0, silence_timeout))
        if min_speech_duration is not None:
            self.min_speech_duration = max(0.1, min(5.0, min_speech_duration))
        if max_speech_duration is not None:
            self.max_speech_duration = max(5.0, min(60.0, max_speech_duration))
        
        logger.info(f"配置更新: VAD阈值={self.vad_threshold}, 静默超时={self.silence_timeout}s")

# 全局实例
realtime_speech_service = RealTimeSpeechService()