"""
Pyttsx3 TTS引擎实现 
使用本地pyttsx3库，完全离线，作为edge-tts的备用方案
"""

import asyncio
import tempfile
import os
from typing import Dict, Any
from .base import BaseTTSEngine

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class Pyttsx3Engine(BaseTTSEngine):
    """
    Pyttsx3 TTS引擎实现
    使用系统内置TTS引擎，完全离线
    """
    
    name = "pyttsx3"
    priority = 2  # 备用引擎，优先级较低
    
    def __init__(self):
        super().__init__()
        self._engine = None
        self._init_engine()
        
        self.logger.info(f"🔊 Pyttsx3Engine 初始化 (可用: {PYTTSX3_AVAILABLE})")
    
    def _init_engine(self):
        """初始化pyttsx3引擎"""
        if not PYTTSX3_AVAILABLE:
            return
        
        try:
            self._engine = pyttsx3.init()
            
            # 设置默认属性
            if self._engine:
                # 设置语速 (一般范围 50-300)
                self._engine.setProperty('rate', 180)
                
                # 设置音量 (0.0-1.0)
                self._engine.setProperty('volume', 0.9)
                
                # 尝试设置中文语音
                voices = self._engine.getProperty('voices')
                if voices:
                    # 寻找中文语音
                    for voice in voices:
                        voice_id = voice.id
                        if any(lang in voice_id.lower() for lang in ['zh', 'chinese', 'mandarin']):
                            self._engine.setProperty('voice', voice_id)
                            break
                    else:
                        # 如果没有中文语音，使用第一个可用语音
                        self._engine.setProperty('voice', voices[0].id)
                
                self.logger.info("✅ Pyttsx3引擎初始化成功")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Pyttsx3引擎初始化失败: {e}")
            self._engine = None
    
    def is_available(self) -> bool:
        """检查pyttsx3是否可用"""
        return PYTTSX3_AVAILABLE and self._engine is not None
    
    def get_supported_voices(self) -> Dict[str, str]:
        """获取支持的声音列表"""
        return {
            "nova": "系统默认女声",
            "echo": "系统默认男声", 
            "alloy": "系统中性声音",
            "system": "系统当前语音"
        }
    
    async def synthesize(
        self, 
        text: str, 
        voice: str = "nova", 
        speed: float = 1.0,
        **kwargs
    ) -> bytes:
        """
        使用pyttsx3合成语音
        
        Args:
            text: 要合成的文本
            voice: 声音类型 (pyttsx3使用系统语音)
            speed: 语速倍率
            **kwargs: 其他参数
            
        Returns:
            WAV格式的音频数据
            
        Raises:
            RuntimeError: 当pyttsx3不可用时
            Exception: 合成失败时
        """
        if not self.is_available():
            raise RuntimeError("pyttsx3 不可用，请安装: pip install pyttsx3")
        
        # 验证和标准化参数
        voice = self.validate_voice(voice)
        speed = self.validate_speed(speed)
        
        self.logger.debug(f"🔊 Pyttsx3合成: voice={voice}, speed={speed}, text_len={len(text)}")
        
        try:
            # 设置语速 (pyttsx3的rate通常在50-300之间)
            base_rate = 180
            new_rate = int(base_rate * speed)
            new_rate = max(50, min(400, new_rate))  # 限制范围
            self._engine.setProperty('rate', new_rate)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_filename = tmp_file.name
            
            try:
                # 使用asyncio在线程池中运行同步操作
                await asyncio.get_running_loop().run_in_executor(
                    None, 
                    self._synthesize_sync, 
                    text, 
                    tmp_filename
                )
                
                # 读取生成的音频文件
                with open(tmp_filename, 'rb') as f:
                    audio_data = f.read()
                
                if not audio_data:
                    raise Exception("生成的音频文件为空")
                
                self.logger.debug(f"✅ Pyttsx3合成成功: {len(audio_data)} bytes")
                return audio_data
                
            finally:
                # 清理临时文件
                if os.path.exists(tmp_filename):
                    os.unlink(tmp_filename)
                    
        except Exception as e:
            self.logger.error(f"❌ Pyttsx3合成失败: {e}")
            raise Exception(f"Pyttsx3合成失败: {e}")
    
    def _synthesize_sync(self, text: str, output_file: str):
        """同步的语音合成方法"""
        try:
            # 保存到文件
            self._engine.save_to_file(text, output_file)
            
            # 运行事件循环等待完成
            self._engine.runAndWait()
            
        except Exception as e:
            raise Exception(f"Pyttsx3同步合成失败: {e}")
    
    def __REMOVED_API_KEY__(self) -> Dict[str, Any]:
        """
        获取系统可用的语音列表
        
        Returns:
            系统语音的详细信息
        """
        if not self.is_available():
            return {}
        
        try:
            voices = self._engine.getProperty('voices')
            
            voice_list = []
            for i, voice in enumerate(voices):
                voice_info = {
                    "id": voice.id,
                    "name": voice.name,
                    "age": getattr(voice, 'age', 'Unknown'),
                    "gender": getattr(voice, 'gender', 'Unknown'),
                    "languages": getattr(voice, 'languages', [])
                }
                voice_list.append(voice_info)
            
            return {
                "voices": voice_list,
                "total_count": len(voice_list),
                "current_voice": self._engine.getProperty('voice')
            }
            
        except Exception as e:
            self.logger.error(f"❌ 获取系统语音列表失败: {e}")
            return {}
    
    def set_voice_by_language(self, language: str = "zh") -> bool:
        """
        根据语言设置合适的语音
        
        Args:
            language: 语言代码 (zh, en)
            
        Returns:
            是否设置成功
        """
        if not self.is_available():
            return False
        
        try:
            voices = self._engine.getProperty('voices')
            
            if language.startswith("zh"):
                # 寻找中文语音
                keywords = ['zh', 'chinese', 'mandarin', '中文']
            elif language.startswith("en"):
                # 寻找英文语音
                keywords = ['en', 'english', 'us', 'uk']
            else:
                return False
            
            for voice in voices:
                voice_id = voice.id.lower()
                voice_name = voice.name.lower()
                
                if any(keyword in voice_id or keyword in voice_name for keyword in keywords):
                    self._engine.setProperty('voice', voice.id)
                    self.logger.info(f"✅ 已设置语音: {voice.name}")
                    return True
            
            self.logger.warning(f"⚠️ 未找到{language}语音，使用默认语音")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 设置语音失败: {e}")
            return False 