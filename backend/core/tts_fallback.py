#!/usr/bin/env python3
"""
TTS备份服务
当主要的TTS服务不可用时，提供备用的语音合成功能
"""

import asyncio
import logging
from typing import Optional, Union
import struct
import wave
import io
import base64

logger = logging.getLogger(__name__)

# 尝试导入edge-tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts未安装，TTS备份服务将生成静音音频")

# 尝试导入pyttsx3
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# 导入TTS引擎
from .tts_engines.edge_engine import EdgeTTSEngine
from .tts_engines.pyttsx3_engine import Pyttsx3Engine


class TTSFallbackService:
    """TTS备份服务，优先使用edge-tts，其次pyttsx3，最后生成静音"""
    
    def __init__(self):
        self.sample_rate = 16000
        self.channels = 1
        self.bits_per_sample = 16
        self.voice_mapping = {
            "nova": "zh-CN-XiaoxiaoNeural",  # 女性声音
            "echo": "zh-CN-YunxiNeural",     # 男性声音
            "alloy": "zh-CN-XiaoyiNeural",   # 中性声音
            "fable": "zh-CN-YunjianNeural",  # 男性声音
            "onyx": "zh-CN-YunxiaNeural",    # 男性声音
            "shimmer": "zh-CN-XiaoshuangNeural"  # 女性声音
        }
        logger.info("✅ TTS备份服务初始化成功")
        
        # 初始化引擎
        self.edge_engine = EdgeTTSEngine()
        self.pyttsx3_engine = Pyttsx3Engine()
        
        logger.info(f"🎵 TTS备份服务初始化完成")
        logger.info(f"   Edge-TTS 可用: {self.edge_engine.is_healthy()}")
        logger.info(f"   Pyttsx3 可用: {self.pyttsx3_engine.is_available()}")
        
    async def synthesize_speech(
        self, 
        text: str, 
        voice: str = "nova", 
        speed: float = 1.0,
        format: str = "mp3"
    ) -> bytes:
        """
        统一的语音合成接口，与原speech服务兼容
        
        Args:
            text: 输入文本
            voice: 语音类型
            speed: 语速
            format: 音频格式（暂不使用，保持兼容性）
            
        Returns:
            音频数据
        """
        return await self.synthesize_with_fallback(text, voice, speed)
        
    async def synthesize_with_fallback(
        self, 
        text: str, 
        voice: str = "nova", 
        speed: float = 1.0
    ) -> bytes:
        """
        使用fallback机制进行语音合成
        
        Args:
            text: 要合成的文本
            voice: 语音类型
            speed: 语音速度
            
        Returns:
            音频数据
            
        Raises:
            Exception: 所有引擎都失败时
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        logger.info(f"🎵 开始语音合成，文本长度: {len(text)}")
        
        # 第一次尝试：Edge-TTS
        try:
            logger.info("🔄 尝试使用 Edge-TTS 引擎...")
            audio_data = await self._try_edge_tts(text, voice, speed)
            if audio_data and len(audio_data) > 0:
                logger.info(f"✅ Edge-TTS 合成成功，音频大小: {len(audio_data)} bytes")
                return audio_data
        except Exception as e:
            logger.warning(f"⚠️ Edge-TTS 失败: {e}")
        
        # 第二次尝试：Pyttsx3 备用引擎
        try:
            logger.info("🔄 切换到 Pyttsx3 备用引擎...")
            audio_data = await self._try_pyttsx3(text, voice, speed)
            if audio_data and len(audio_data) > 0:
                logger.info(f"✅ Pyttsx3 合成成功，音频大小: {len(audio_data)} bytes")
                return audio_data
        except Exception as e:
            logger.error(f"❌ Pyttsx3 也失败了: {e}")
        
        # 所有引擎都失败
        error_msg = "所有TTS引擎都失败了"
        logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)
    
    async def _try_edge_tts(self, text: str, voice: str, speed: float) -> Optional[bytes]:
        """尝试使用Edge-TTS"""
        try:
            if hasattr(self.edge_engine, 'synthesize_async'):
                return await self.edge_engine.synthesize_async(text, voice, speed)
            elif hasattr(self.edge_engine, 'synthesize'):
                # 在异步环境中调用同步方法
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, self.edge_engine.synthesize, text, voice, speed, "mp3")
            else:
                raise Exception("Edge-TTS引擎不支持语音合成")
        except Exception as e:
            raise Exception(f"Edge-TTS合成失败: {e}")
    
    async def _try_pyttsx3(self, text: str, voice: str, speed: float) -> Optional[bytes]:
        """尝试使用Pyttsx3"""
        try:
            if not self.pyttsx3_engine.is_available():
                raise Exception("Pyttsx3引擎不可用")
            
            # Pyttsx3是同步的，需要在executor中运行
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, 
                self.pyttsx3_engine.synthesize, 
                text, voice, speed, "wav"
            )
        except Exception as e:
            raise Exception(f"Pyttsx3合成失败: {e}")
    
    def get_available_engines(self) -> dict:
        """获取可用引擎状态"""
        return {
            "edge-tts": {
                "available": self.edge_engine.is_healthy(),
                "name": "Edge-TTS",
                "description": "微软Edge浏览器在线TTS服务"
            },
            "pyttsx3": {
                "available": self.pyttsx3_engine.is_available(),
                "name": "Pyttsx3",
                "description": "本地离线TTS引擎"
            }
        }


# 全局TTS备份服务实例
tts_fallback = TTSFallbackService() 


def get_fallback_handler() -> TTSFallbackService:
    """获取全局TTS fallback处理器"""
    return tts_fallback


async def synthesize_with_fallback(
    text: str, 
    voice: str = "nova", 
    speed: float = 1.0
) -> Union[bytes, str]:
    """
    便捷函数：使用fallback机制进行语音合成
    
    Returns:
        bytes: 音频数据，如果成功
        str: base64编码的音频数据，作为备用格式
    """
    handler = get_fallback_handler()
    try:
        audio_data = await handler.synthesize_with_fallback(text, voice, speed)
        return audio_data
    except Exception as e:
        logger.error(f"❌ Fallback合成失败: {e}")
        # 返回一个静音音频作为最后的备用方案
        return await _generate_silence_audio()


async def _generate_silence_audio() -> bytes:
    """生成静音音频作为最后的备用方案"""
    try:
        # 生成1秒的静音WAV音频
        import wave
        import io
        
        # WAV文件参数
        sample_rate = 22050
        duration = 1.0  # 1秒
        frames = int(sample_rate * duration)
        
        # 创建静音数据
        silence_data = b'\x00\x00' * frames  # 16位静音
        
        # 创建WAV文件
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silence_data)
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    except Exception as e:
        logger.error(f"❌ 生成静音音频失败: {e}")
        # 返回最小的WAV文件头
        return b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00' 