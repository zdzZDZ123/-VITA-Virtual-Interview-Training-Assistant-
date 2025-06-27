#!/usr/bin/env python3
"""
Edge-TTS引擎实现
使用微软Edge浏览器的TTS服务
"""

import asyncio
import logging
import tempfile
import os
from typing import Dict, Any, Optional
import edge_tts
from .base import BaseTTSEngine

class EdgeTTSEngine(BaseTTSEngine):
    """Edge-TTS引擎"""
    
    def __init__(self):
        super().__init__()
        self.name = "edge-tts"
        self.priority = 1  # 高优先级
        self.logger = logging.getLogger(f"core.tts_engines.edge_engine.{self.__class__.__name__}")
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1.0  # 重试延迟（秒）
        self.token_retry_delay = 30.0  # Token失效时的重试延迟
        
        # 支持的语音列表（中英文常用）
        self.default_voices = {
            'nova': 'zh-CN-XiaoxiaoNeural',    # 中文女声
            'alloy': 'zh-CN-YunxiNeural',      # 中文男声
            'echo': 'zh-CN-XiaoyiNeural',      # 中文女声
            'fable': 'zh-CN-YunyangNeural',    # 中文男声
            'onyx': 'en-US-AriaNeural',        # 英文女声
            'shimmer': 'en-US-JennyNeural',    # 英文女声
            
            # 英文语音扩展映射
            'nova_en': 'en-US-JennyNeural',    # 美式英语女性
            'echo_en': 'en-US-GuyNeural',      # 美式英语男性
            'alloy_en': 'en-US-AriaNeural',    # 美式英语女性
            'fable_en': 'en-US-DavisNeural',   # 美式英语男性
            'onyx_en': 'en-US-TonyNeural',     # 美式英语男性
            'shimmer_en': 'en-US-SaraNeural'   # 美式英语女性
        }
        
        # 为了兼容性，添加voice_mapping
        self.voice_mapping = self.default_voices
        
        try:
            self._test_availability()
            self.available = True
            self.logger.info(f"🎤 {self.name} 初始化完成 (可用: {self.available})")
        except Exception as e:
            self.available = False
            self.logger.warning(f"⚠️ {self.name} 初始化失败，但将在使用时重试: {e}")
    
    def _test_availability(self):
        """测试Edge-TTS是否可用"""
        try:
            # 尝试导入edge_tts并进行简单检查
            import edge_tts
            self.logger.debug(f"✅ edge-tts版本: {edge_tts.__version__}")
        except ImportError as e:
            raise Exception(f"edge-tts库未安装: {e}")
    
    async def synthesize_async(self, text: str, voice: str = "nova", speed: float = 1.0) -> bytes:
        """异步语音合成"""
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        # 映射语音名称
        actual_voice = self.default_voices.get(voice, voice)
        
        # 处理语音速度
        rate = self._calculate_rate(speed)
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"🎵 开始Edge-TTS合成 (尝试 {attempt + 1}/{self.max_retries})")
                self.logger.debug(f"   文本: {text[:50]}{'...' if len(text) > 50 else ''}")
                self.logger.debug(f"   语音: {actual_voice}, 速度: {rate}")
                
                # 创建临时文件
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    temp_path = temp_file.name
                
                try:
                    # 使用edge-tts进行合成
                    communicate = edge_tts.Communicate(
                        text=text,
                        voice=actual_voice,
                        rate=rate
                    )
                    
                    # 保存到临时文件
                    await communicate.save(temp_path)
                    
                    # 读取音频数据
                    with open(temp_path, 'rb') as f:
                        audio_data = f.read()
                    
                    if not audio_data:
                        raise Exception("生成的音频文件为空")
                    
                    self.logger.info(f"✅ Edge-TTS合成成功，音频大小: {len(audio_data)} bytes")
                    return audio_data
                    
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass
                        
            except Exception as e:
                error_str = str(e).lower()
                
                # 检查是否是Token相关错误
                if "403" in error_str or "trustedclienttoken" in error_str or "invalid response status" in error_str:
                    self.logger.warning(f"🔑 Edge-TTS Token失效 (尝试 {attempt + 1}): {e}")
                    
                    if attempt < self.max_retries - 1:
                        # Token失效时使用更长的延迟
                        delay = self.token_retry_delay if attempt == 0 else self.retry_delay * (attempt + 1)
                        self.logger.info(f"⏱️ Token失效，等待 {delay} 秒后重试...")
                        await asyncio.sleep(delay)
                        continue
                else:
                    self.logger.warning(f"⚠️ Edge-TTS合成尝试 {attempt + 1} 失败: {e}")
                    
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))  # 指数退避
                        continue
                
                # 最后一次尝试失败
                if attempt == self.max_retries - 1:
                    error_msg = f"Edge-TTS合成失败: {e}"
                    self.logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)
    
    def _calculate_rate(self, speed: float) -> str:
        """计算语音速度"""
        if speed <= 0.5:
            return "-50%"
        elif speed <= 0.75:
            return "-25%"
        elif speed <= 1.25:
            return "+0%"
        elif speed <= 1.5:
            return "+25%"
        elif speed <= 2.0:
            return "+50%"
        else:
            return "+100%"
    
    def get_available_voices(self) -> list:
        """获取可用的语音列表"""
        return list(self.default_voices.keys())
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            import edge_tts
            return True
        except Exception:
            return False
    
    def is_healthy(self) -> bool:
        """检查引擎健康状态"""
        return self.is_available()
    
    def get_supported_voices(self) -> Dict[str, str]:
        """获取支持的声音列表"""
        return {
            # 主要中文声音
            "nova": "小晓 - 女性，亲切自然",
            "echo": "云希 - 男性，沉稳专业", 
            "alloy": "晓伊 - 女性，清晰中性",
            "fable": "云健 - 男性，温和友善",
            "onyx": "云夏 - 男性，深沉磁性",
            "shimmer": "晓双 - 女性，活泼开朗",
            
            # 英文声音（扩展）
            "nova_en": "Jenny - 美式英语女性",
            "echo_en": "Guy - 美式英语男性",
            "alloy_en": "Aria - 美式英语女性",
            "fable_en": "Davis - 美式英语男性", 
            "onyx_en": "Tony - 美式英语男性",
            "shimmer_en": "Sara - 美式英语女性"
        }
    
    async def synthesize(
        self, 
        text: str, 
        voice: str = "nova", 
        speed: float = 1.0,
        output_format: str = "mp3",
        **kwargs
    ) -> bytes:
        """
        使用edge-tts合成语音
        
        Args:
            text: 要合成的文本
            voice: 声音类型
            speed: 语速倍率
            output_format: 输出格式 ("mp3" 或 "wav")
            **kwargs: 其他参数
            
        Returns:
            指定格式的音频数据
            
        Raises:
            RuntimeError: 当edge-tts不可用时
            Exception: 合成失败时
        """
        if not self.is_available():
            raise RuntimeError("edge-tts 不可用，请安装: pip install edge-tts")
        
        # 验证和标准化参数
        voice = self.validate_voice(voice)
        speed = self.validate_speed(speed)
        output_format = output_format.lower()
        
        # 获取对应的edge-tts语音名称
        edge_voice = self.voice_mapping.get(voice, "zh-CN-XiaoxiaoNeural")
        
        # 计算语速参数 (edge-tts使用百分比格式)
        rate_percent = int((speed - 1.0) * 100)
        rate = f"{rate_percent:+d}%" if rate_percent != 0 else "+0%"
        
        self.logger.debug(f"🎵 Edge-TTS合成: voice={edge_voice}, rate={rate}, format={output_format}, text_len={len(text)}")
        
        try:
            # 创建Communicate对象
            communicate = edge_tts.Communicate(text, edge_voice, rate=rate)
            
            # 使用临时文件存储音频
            mp3_suffix = '.mp3'
            with tempfile.NamedTemporaryFile(suffix=mp3_suffix, delete=False) as tmp_file:
                mp3_filename = tmp_file.name
            
            try:
                # 保存MP3音频到临时文件
                await communicate.save(mp3_filename)
                
                if output_format == "wav":
                    # 转换为WAV格式
                    wav_filename = mp3_filename.replace('.mp3', '.wav')
                    try:
                        # 尝试使用pydub进行转换
                        import io
                        from pydub import AudioSegment
                        
                        # 读取MP3并转换为WAV
                        audio_segment = AudioSegment.from_mp3(mp3_filename)
                        
                        # 设置WAV参数以提高兼容性
                        audio_segment = audio_segment.set_frame_rate(22050)  # 标准采样率
                        audio_segment = audio_segment.set_channels(1)        # 单声道
                        audio_segment = audio_segment.set_sample_width(2)    # 16位
                        
                        wav_buffer = io.BytesIO()
                        audio_segment.export(wav_buffer, format="wav")
                        audio_data = wav_buffer.getvalue()
                        
                        self.logger.debug(f"✅ Edge-TTS WAV转换成功: {len(audio_data)} bytes")
                        return audio_data
                        
                    except ImportError:
                        self.logger.warning("pydub不可用，尝试使用FFmpeg命令行...")
                        # 尝试使用FFmpeg命令行转换
                        import subprocess
                        try:
                            result = subprocess.run([
                                'ffmpeg', '-i', mp3_filename, 
                                '-ar', '22050',  # 采样率
                                '-ac', '1',      # 单声道
                                '-f', 'wav',     # 输出格式
                                wav_filename
                            ], capture_output=True, check=True)
                            
                            with open(wav_filename, 'rb') as f:
                                audio_data = f.read()
                            
                            os.unlink(wav_filename)  # 清理WAV文件
                            self.logger.debug(f"✅ Edge-TTS FFmpeg WAV转换成功: {len(audio_data)} bytes")
                            return audio_data
                            
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            self.logger.warning("FFmpeg不可用，返回原始MP3数据")
                            # 转换失败，返回原始MP3
                            with open(mp3_filename, 'rb') as f:
                                audio_data = f.read()
                            return audio_data
                    
                    except Exception as e:
                        self.logger.warning(f"WAV转换失败: {e}，返回原始MP3数据")
                        # 转换失败，返回原始MP3
                        with open(mp3_filename, 'rb') as f:
                            audio_data = f.read()
                        return audio_data
                else:
                    # 返回MP3格式
                    with open(mp3_filename, 'rb') as f:
                        audio_data = f.read()
                    
                    self.logger.debug(f"✅ Edge-TTS MP3合成成功: {len(audio_data)} bytes")
                    return audio_data
                
            finally:
                # 清理临时文件
                if os.path.exists(mp3_filename):
                    os.unlink(mp3_filename)
                    
        except Exception as e:
            self.logger.error(f"❌ Edge-TTS合成失败: {e}")
            raise Exception(f"Edge-TTS合成失败: {e}")
    
    async def __REMOVED_API_KEY__(self) -> Dict[str, Any]:
        """
        从edge-tts服务获取所有可用的声音列表
        
        Returns:
            可用声音的详细信息
        """
        if not self.is_available():
            return {}
        
        try:
            voices = await edge_tts.VoicesManager.create()
            
            # 过滤中文和英文声音
            chinese_voices = []
            english_voices = []
            
            for voice in voices.voices:
                voice_info = {
                    "name": voice["Name"],
                    "short_name": voice["ShortName"], 
                    "gender": voice.get("Gender", "Unknown"),
                    "locale": voice.get("Locale", ""),
                    "display_name": voice.get("DisplayName", "")
                }
                
                if voice["Locale"].startswith("zh"):
                    chinese_voices.append(voice_info)
                elif voice["Locale"].startswith("en"):
                    english_voices.append(voice_info)
            
            return {
                "chinese_voices": chinese_voices,
                "english_voices": english_voices,
                "total_count": len(voices.voices)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 获取Edge-TTS声音列表失败: {e}")
            return {}
    
    def __REMOVED_API_KEY__(self, language: str = "zh") -> str:
        """
        根据语言推荐合适的声音
        
        Args:
            language: 语言代码 (zh, en)
            
        Returns:
            推荐的voice标识符
        """
        if language.startswith("zh"):
            # 中文推荐
            return "nova"  # 小晓，自然亲切
        elif language.startswith("en"):
            # 英文推荐
            return "nova_en"  # Jenny，清晰自然
        else:
            # 默认推荐
            return "nova" 