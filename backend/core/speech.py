"""
语音服务模块
提供本地Whisper语音识别和TTS语音合成功能
完全独立于OpenAI API
"""

import os
import tempfile
import asyncio
import socket
import subprocess
from typing import Optional, Dict, Any, AsyncGenerator, List
from pathlib import Path
import aiofiles
import httpx
import logging
import io
from fastapi import HTTPException
from core.config import config, ModelSelector
from .tts_service import get_tts_service
from core.whisper_model_manager import get_model_manager

# 设置logger
logger = logging.getLogger(__name__)

def check_network_connection(timeout: float = 5.0) -> bool:
    """检查网络连接是否可用"""
    try:
        # 尝试连接Google DNS
        socket.create_connection(("8.8.8.8", 53), timeout)
        return True
    except (socket.timeout, socket.error):
        try:
            # 备用：尝试连接Cloudflare DNS
            socket.create_connection(("1.1.1.1", 53), timeout)
            return True
        except (socket.timeout, socket.error):
            return False

def find_local_whisper_model(model_size: str, model_dir: str) -> Optional[Path]:
    """查找本地Whisper模型目录"""
    # 相对于项目根目录查找
    project_root = Path(__file__).parent.parent.parent
    potential_paths = [
        # 项目根目录下的whisper_download
        project_root / model_dir / model_size,
        # 当前工作目录下的whisper_download
        Path.cwd() / model_dir / model_size,
        # 直接在当前目录
        Path(model_dir) / model_size,
        # 绝对路径
        Path(model_dir) if Path(model_dir).is_absolute() else None
    ]
    
    for path in potential_paths:
        if path and path.exists() and path.is_dir():
            # 检查是否包含必要的模型文件
            required_files = ['config.json']  # faster-whisper基本要求
            if all((path / f).exists() for f in required_files):
                logger.info(f"✅ 发现本地模型: {path}")
                return path
    
    return None

# 本地Whisper相关导入
try:
    from faster_whisper import WhisperModel
    import torch
    FASTER_WHISPER_AVAILABLE = True
    logger.info("✅ faster-whisper 可用")
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("⚠️ faster-whisper 未安装，尝试使用标准whisper")

# 备用：尝试使用标准whisper
if not FASTER_WHISPER_AVAILABLE:
    try:
        import whisper
        WHISPER_AVAILABLE = True
        logger.info("✅ 标准whisper 可用")
    except ImportError:
        WHISPER_AVAILABLE = False
        logger.error("❌ 没有可用的Whisper实现")
else:
    # 即使有faster-whisper，也尝试导入标准whisper作为备用
    try:
        import whisper
        WHISPER_AVAILABLE = True
        logger.debug("📦 标准whisper也可用作备用")
    except ImportError:
        WHISPER_AVAILABLE = False
        logger.debug("⚠️ 标准whisper不可用，仅有faster-whisper")

class SpeechService:
    """语音服务类，使用本地Whisper进行语音识别
    
    完全独立于云端API，提供本地化的语音处理能力
    """
    
    def __init__(self):
        try:
            voice_config = config.get_voice_config()
            self.supported_formats = voice_config["supported_formats"]
            self.max_audio_size_mb = voice_config["max_audio_size_mb"]
            
            # 初始化本地Whisper模型
            self.local_whisper = None
            self.local_whisper_config = config.get_local_whisper_config()
            
            # 强制使用本地Whisper
            if FASTER_WHISPER_AVAILABLE or WHISPER_AVAILABLE:
                self._init_local_whisper()
            else:
                raise Exception("没有可用的Whisper实现，请安装 faster-whisper 或 whisper")
            
            # 初始化新的TTS服务
            self.tts_service = get_tts_service()
            
            logger.info("✅ SpeechService 初始化成功 (纯本地Whisper)")
        except Exception as e:
            logger.error(f"❌ SpeechService 初始化失败: {e}")
            raise
    
    def _init_local_whisper(self):
        """初始化本地Whisper模型 - 使用新的模型管理器"""
        try:
            model_size = self.local_whisper_config["model_size"]
            device = self.local_whisper_config["device"]
            compute_type = self.local_whisper_config["compute_type"]
            disable_online = self.local_whisper_config.get("disable_online", False)
            
            # 自动检测设备
            if device == "auto":
                if FASTER_WHISPER_AVAILABLE and torch.cuda.is_available():
                    device = "cuda"
                    logger.info("🚀 检测到CUDA，使用GPU加速")
                else:
                    device = "cpu"
                    compute_type = "int8"  # CPU使用int8更快
                    logger.info("💻 使用CPU进行推理")
            
            logger.info(f"⏳ 正在加载本地Whisper模型: {model_size}, 设备: {device}, 精度: {compute_type}")
            
            # 使用模型管理器查找或下载模型
            model_manager = get_model_manager()
            
            # 先检查本地是否有模型
            local_model_path = model_manager.find_local_model(model_size)
            
            if local_model_path:
                # 尝试加载本地模型
                if FASTER_WHISPER_AVAILABLE:
                    if self._try_local_model_path(local_model_path, device, compute_type):
                        logger.info(f"✅ 使用本地faster-whisper模型: {local_model_path}")
                        return
            else:
                # 本地没有模型，提示用户
                logger.warning(f"⚠️ 未找到本地模型 {model_size}")
                logger.info("💡 您可以通过以下方式获取模型：")
                logger.info(f"   1. 运行: python scripts/download_faster_whisper.py {model_size}")
                logger.info(f"   2. 或者在启动时等待自动下载（需要网络连接）")
            
            # 策略2: 尝试从系统缓存加载
            if FASTER_WHISPER_AVAILABLE:
                if self._try_faster_whisper_cached(model_size, device, compute_type):
                    logger.info(f"✅ 使用缓存的faster-whisper模型: {model_size}")
                    return
            
            # 策略3: 在线下载 (仅在网络可用且未禁用时)
            if not disable_online and check_network_connection():
                logger.info("🌐 网络可用，尝试在线下载模型...")
                if FASTER_WHISPER_AVAILABLE:
                    if self._try_faster_whisper_online(model_size, device, compute_type):
                        logger.info(f"✅ 在线下载faster-whisper模型成功: {model_size}")
                        # 保存路径信息供下次使用
                        logger.info("💡 模型已下载到系统缓存，下次启动将直接使用")
                        return
            else:
                if disable_online:
                    logger.info("🚫 在线下载已禁用 (DISABLE_WHISPER_ONLINE=true)")
                else:
                    logger.info("🌐 网络不可用，无法下载模型")
            
            # 策略4: 使用标准whisper作为最终备用
            if WHISPER_AVAILABLE:
                logger.info("📦 使用标准whisper作为备用方案")
                if self._try_standard_whisper(model_size):
                    logger.info(f"✅ 使用标准whisper模型: {model_size}")
                    logger.info("💡 建议下载faster-whisper模型以获得更好的性能")
                    return
            
            # 所有策略都失败 - 不中断启动，只记录警告
            logger.warning("⚠️ 无法加载任何Whisper模型，语音识别功能将被禁用")
            logger.info("💡 您可以稍后通过以下方式启用语音功能：")
            logger.info("   1. 确保网络连接正常")
            logger.info(f"   2. 运行: python -c \"from faster_whisper import WhisperModel; WhisperModel('{model_size}')\"")
            logger.info("   3. 重启服务")
            self.local_whisper = None
            
        except Exception as e:
            logger.warning(f"⚠️ 本地Whisper模型加载失败: {e}")
            logger.info("🚀 服务将在禁用语音识别的情况下继续启动")
            self.local_whisper = None
        
    def _try_local_model_path(self, model_path: Path, device: str, compute_type: str) -> bool:
        """尝试使用本地模型路径加载faster-whisper"""
        try:
            logger.info(f"📂 使用本地模型路径: {model_path}")
            self.local_whisper = WhisperModel(
                str(model_path), 
                device=device, 
                compute_type=compute_type,
                local_files_only=True
            )
            self.whisper_type = "faster_whisper_local"
            return True
        except Exception as e:
            logger.warning(f"⚠️ 本地模型路径加载失败: {e}")
            return False
    
    def _try_faster_whisper_cached(self, model_size: str, device: str, compute_type: str) -> bool:
        """尝试使用系统缓存的faster-whisper模型"""
        try:
            # 静默模式尝试，避免警告日志
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.local_whisper = WhisperModel(
                    model_size, 
                    device=device, 
                    compute_type=compute_type,
                    local_files_only=True
                )
            self.whisper_type = "faster_whisper_cached"
            return True
        except Exception:
            # 静默失败，不输出警告
            return False
    
    def _try_faster_whisper_online(self, model_size: str, device: str, compute_type: str) -> bool:
        """尝试使用faster-whisper在线模式"""
        try:
            # 在线下载可能需要一些时间，给用户提示
            logger.info(f"📥 正在下载faster-whisper模型: {model_size} (首次使用需要时间)...")
            self.local_whisper = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type,
                local_files_only=False  # 允许在线下载
            )
            self.whisper_type = "faster_whisper_online"
            return True
        except Exception as e:
            logger.warning(f"⚠️ 在线下载faster-whisper模型失败: {e}")
            return False
    
    def _try_standard_whisper(self, model_size: str) -> bool:
        """尝试使用标准whisper"""
        try:
            # 标准whisper首次下载也可能需要时间
            logger.info(f"📦 加载标准whisper模型: {model_size}...")
            self.local_whisper = whisper.load_model(model_size)
            self.whisper_type = "standard_whisper"
            logger.info(f"🎉 本地Whisper模型加载成功！(标准whisper - {model_size})")
            return True
        except Exception as e:
            logger.warning(f"⚠️ 标准whisper加载失败: {e}")
            return False
    
    async def speech_to_text(
        self, 
        audio_data: bytes, 
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        语音转文字 - 纯本地Whisper实现
        
        Args:
            audio_data: 音频数据
            language: 语言代码 (可选)
            prompt: 提示文本，有助于提高识别准确率
            filename: 原始文件名，用于确定音频格式
            
        Returns:
            包含转录文本和置信度的字典
        """
        try:
            # 验证音频数据
            await self.validate_audio(audio_data)
            
            # 创建临时文件，根据原文件名决定后缀
            suffix = ".wav"
            if filename and "." in filename:
                suffix = filename[filename.rfind(".") :]
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # 使用本地Whisper模型
                if self.local_whisper is None:
                    return {
                        "text": "[语音识别功能暂时不可用]",
                        "language": "zh",
                        "duration": 0,
                        "words": [],
                        "confidence": 0.0,
                        "error": "Whisper模型未加载，请检查网络连接或手动安装模型"
                    }
                
                return await self._transcribe_with_local_whisper(
                    temp_file_path, language, prompt
                )
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"❌ 语音转文字失败: {e}")
            raise HTTPException(status_code=500, detail=f"语音转文字失败: {str(e)}")
    
    async def _transcribe_with_local_whisper(
        self, 
        audio_file_path: str, 
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用本地Whisper模型进行转录"""
        try:
            logger.info(f"🎯 使用本地Whisper模型进行语音识别 ({self.whisper_type})")
            
            # 在线程池中运行同步的转录操作
            loop = asyncio.get_running_loop()
            
            # 兼容不同的 faster-whisper 加载策略 (local / cached / online)
            if self.whisper_type and self.whisper_type.startswith("faster_whisper"):
                # faster-whisper实现
                segments, info = await loop.run_in_executor(
                    None,
                    lambda: self.local_whisper.transcribe(
                        audio_file_path,
                        language=language,
                        initial_prompt=prompt,
                        beam_size=5,
                        word_timestamps=True
                    )
                )
                
                # 提取文本和词级时间戳
                text_parts = []
                words = []
                
                for segment in segments:
                    text_parts.append(segment.text)
                    if hasattr(segment, 'words') and segment.words:
                        for word in segment.words:
                            words.append({
                                "word": word.word,
                                "start": word.start,
                                "end": word.end,
                                "probability": getattr(word, 'probability', 0.95)
                            })
                
                full_text = "".join(text_parts).strip()
                
                result = {
                    "text": full_text,
                    "language": info.language,
                    "duration": info.duration,
                    "words": words,
                    "confidence": 0.95  # faster-whisper默认置信度
                }
            else:
                # 标准whisper实现
                result_data = await loop.run_in_executor(
                    None,
                    lambda: self.local_whisper.transcribe(
                        audio_file_path,
                        language=language,
                        initial_prompt=prompt,
                        word_timestamps=True
                    )
                )
                
                result = {
                    "text": result_data["text"].strip(),
                    "language": result_data.get("language", language or "zh"),
                    "duration": len(result_data.get("segments", [])) * 30,  # 估算时长
                    "words": [],  # 标准whisper的词级时间戳格式不同
                    "confidence": 0.90  # 标准whisper默认置信度
                }
                
                # 提取分段信息
                if "segments" in result_data:
                    for segment in result_data["segments"]:
                        if "words" in segment:
                            for word in segment["words"]:
                                result["words"].append({
                                    "word": word.get("word", ""),
                                    "start": word.get("start", 0),
                                    "end": word.get("end", 0),
                                    "probability": word.get("probability", 0.90)
                                })
            
            logger.info(f"✅ 本地Whisper识别完成，文本长度: {len(result['text'])}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 本地Whisper转录失败: {e}")
            raise Exception(f"本地Whisper转录失败: {e}")
    
    async def text_to_speech(
        self,
        text: str,
        voice: str = "nova",
        response_format: str = "mp3",
        speed: float = 1.0,
        output_format: str = None
    ) -> bytes:
        """
        文字转语音 - 使用本地TTS服务
        
        Args:
            text: 要转换的文本
            voice: 声音类型
            response_format: 音频格式 (已弃用，使用output_format)
            speed: 语音速度
            output_format: 输出格式 ("mp3" 或 "wav")
            
        Returns:
            音频数据（字节）
        """
        try:
            logger.info(f"🎵 使用本地TTS服务进行语音合成，文本长度: {len(text)}")
            
            # 确定输出格式
            format_to_use = output_format or response_format or "mp3"
            
            # 使用新的统一TTS服务，传递格式参数
            if hasattr(self.tts_service, 'synthesize_with_format'):
                audio_data = await self.tts_service.synthesize_with_format(
                    text=text,
                    voice=voice,
                    speed=speed,
                    output_format=format_to_use
                )
            else:
                # 备用：尝试直接调用引擎
                from core.tts_engines.edge_engine import EdgeTTSEngine
                engine = EdgeTTSEngine()
                if engine.is_available():
                    audio_data = await engine.synthesize(
                        text=text,
                        voice=voice,
                        speed=speed,
                        output_format=format_to_use
                    )
                else:
                    # 最终备用：使用原有方法
                    audio_data = await self.tts_service.synthesize(
                        text=text,
                        voice=voice,
                        speed=speed
                    )
            
            logger.info(f"✅ 本地TTS合成完成，音频大小: {len(audio_data)} 字节, 格式: {format_to_use}")
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ 本地TTS合成失败: {e}")
            raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")
    
    async def validate_audio(self, audio_data: bytes) -> None:
        """验证音频数据"""
        if not audio_data:
            logger.warning("❌ 音频数据为空")
            raise HTTPException(status_code=400, detail="音频数据为空")
        
        if len(audio_data) < 100:  # 小于100字节认为无效
            logger.warning(f"❌ 音频数据过小: {len(audio_data)} bytes")
            raise HTTPException(status_code=400, detail="音频数据过小，可能是无效录音")
        
        # 检查文件大小
        size_mb = len(audio_data) / (1024 * 1024)
        if size_mb > self.max_audio_size_mb:
            logger.warning(f"❌ 音频文件过大: {size_mb:.1f}MB")
            raise HTTPException(
                status_code=413, 
                detail=f"音频文件过大: {size_mb:.1f}MB > {self.max_audio_size_mb}MB"
            )
        
        logger.debug(f"✅ 音频验证通过，大小: {size_mb:.2f}MB")

    async def get_supported_voices(self) -> Dict[str, Any]:
        """
        获取支持的语音选项
        
        Returns:
            包含voices和default键的字典
        """
        try:
            logger.info("🎵 获取支持的语音选项")
            
            # 获取TTS服务支持的语音
            tts_voices = {}
            if hasattr(self.tts_service, 'get_supported_voices'):
                tts_voices = self.tts_service.get_supported_voices()
            
            # 合并所有引擎的语音选项
            all_voices = {}
            default_voice = "nova"  # 默认语音
            
            # 从配置获取默认语音
            voice_config = config.get_voice_config()
            default_voice = voice_config.get("default_voice", "nova")
            
            # 整合Edge-TTS引擎的语音
            if "edge-tts" in tts_voices:
                edge_voices = tts_voices["edge-tts"]
                for voice_id, description in edge_voices.items():
                    all_voices[voice_id] = {
                        "name": voice_id,
                        "description": description,
                        "engine": "edge-tts",
                        "language": "zh-CN" if not voice_id.endswith("_en") else "en-US",
                        "gender": self._detect_voice_gender(description),
                        "available": True
                    }
            
            # 整合Pyttsx3引擎的语音
            if "pyttsx3" in tts_voices:
                pyttsx3_voices = tts_voices["pyttsx3"]
                for voice_id, description in pyttsx3_voices.items():
                    if voice_id not in all_voices:  # 避免重复
                        all_voices[voice_id] = {
                            "name": voice_id,
                            "description": description,
                            "engine": "pyttsx3",
                            "language": "zh-CN",
                            "gender": self._detect_voice_gender(description),
                            "available": True
                        }
            
            # 如果没有从引擎获取到语音，提供默认语音选项
            if not all_voices:
                all_voices = {
                    "nova": {
                        "name": "nova",
                        "description": "默认女声 - 自然亲切",
                        "engine": "system",
                        "language": "zh-CN",
                        "gender": "female",
                        "available": True
                    },
                    "echo": {
                        "name": "echo",
                        "description": "默认男声 - 沉稳专业",
                        "engine": "system",
                        "language": "zh-CN",
                        "gender": "male",
                        "available": True
                    },
                    "alloy": {
                        "name": "alloy",
                        "description": "中性声音 - 清晰中性",
                        "engine": "system",
                        "language": "zh-CN",
                        "gender": "neutral",
                        "available": True
                    }
                }
            
            # 确保默认语音存在
            if default_voice not in all_voices:
                default_voice = next(iter(all_voices.keys())) if all_voices else "nova"
            
            result = {
                "voices": all_voices,
                "default": default_voice,
                "total_count": len(all_voices),
                "engines": list(set(voice["engine"] for voice in all_voices.values())),
                "languages": list(set(voice["language"] for voice in all_voices.values()))
            }
            
            logger.info(f"✅ 获取语音选项成功: {len(all_voices)} 个语音, 默认: {default_voice}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取语音选项失败: {e}")
            # 返回最基本的默认语音选项
            return {
                "voices": {
                    "nova": {
                        "name": "nova",
                        "description": "默认语音",
                        "engine": "fallback",
                        "language": "zh-CN",
                        "gender": "female",
                        "available": True
                    }
                },
                "default": "nova",
                "total_count": 1,
                "engines": ["fallback"],
                "languages": ["zh-CN"],
                "error": str(e)
            }
    
    def _detect_voice_gender(self, description: str) -> str:
        """
        根据描述检测语音性别
        
        Args:
            description: 语音描述
            
        Returns:
            性别: "male", "female", "neutral"
        """
        desc_lower = description.lower()
        
        # 检测女性关键词
        if any(keyword in desc_lower for keyword in ['female', '女', '女性', '女声', 'aria', 'jenny', 'sara']):
            return "female"
        
        # 检测男性关键词
        if any(keyword in desc_lower for keyword in ['male', '男', '男性', '男声', 'guy', 'davis', 'tony']):
            return "male"
        
        # 检测中性关键词
        if any(keyword in desc_lower for keyword in ['neutral', '中性', 'alloy']):
            return "neutral"
        
        # 默认根据名称判断
        if any(name in desc_lower for name in ['nova', 'aria', 'jenny', 'sara', '晓', '小']):
            return "female"
        elif any(name in desc_lower for name in ['echo', 'onyx', 'guy', 'davis', 'tony', '云', '男']):
            return "male"
        
        return "neutral"


class VoiceInterviewer:
    """语音面试官类"""
    
    def __init__(self, speech_service: SpeechService):
        self.speech_service = speech_service
        voice_config = config.get_voice_config()
        self.interviewer_voice = voice_config["default_voice"]  # 使用配置的默认声音
        self.speech_speed = voice_config["default_speed"]
        
    async def speak_question(self, question: str) -> bytes:
        """
        朗读面试问题
        
        Args:
            question: 问题文本
            
        Returns:
            音频数据
        """
        # 为问题添加适当的语调提示
        formatted_question = self._format_question_for_speech(question)
        
        return await self.speech_service.text_to_speech(
            text=formatted_question,
            voice=self.interviewer_voice,
            speed=self.speech_speed
        )

    async def stream_speak_question(self, question: str) -> AsyncGenerator[bytes, None]:
        """
        流式朗读面试问题
        
        Args:
            question: 问题文本
            
        Yields:
            音频数据块
        """
        formatted_question = self._format_question_for_speech(question)
        
        async for chunk in self.speech_service.stream_text_to_speech(
            text=formatted_question,
            voice=self.interviewer_voice,
            speed=self.speech_speed
        ):
            yield chunk

    async def process_voice_answer(
        self, 
        audio_data: bytes,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理语音回答
        
        Args:
            audio_data: 音频数据
            context: 上下文信息
            
        Returns:
            处理结果
        """
        try:
            # 转录语音
            transcript_result = await self.speech_service.speech_to_text(
                audio_data, 
                prompt=context
            )
            
            # 分析语音特征
            speech_analysis = await self.speech_service.analyze_speech_features(audio_data)
            
            return {
                "transcript": transcript_result,
                "speech_analysis": speech_analysis,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"语音答案处理失败: {e}")
            return {
                "error": str(e),
                "status": "error"
            }

    def _format_question_for_speech(self, question: str) -> str:
        """
        为语音合成格式化问题文本
        
        Args:
            question: 原始问题
            
        Returns:
            格式化后的问题
        """
        # 添加适当的停顿和语调
        formatted = question.strip()
        
        # 确保以问号结尾
        if not formatted.endswith(('?', '？')):
            formatted += "?"
        
        # 为较长的问题添加停顿
        if len(formatted) > 50:
            # 在逗号后添加短停顿
            formatted = formatted.replace(',', ', ')
            formatted = formatted.replace('，', '， ')
        
        return formatted

    def set_voice_config(self, voice: Optional[str] = None, speed: Optional[float] = None):
        """
        设置语音配置
        
        Args:
            voice: 声音类型
            speed: 语速
        """
        if voice:
            self.interviewer_voice = voice
        if speed:
            self.speech_speed = max(0.25, min(4.0, speed))


# 全局实例
speech_service = SpeechService()
voice_interviewer = VoiceInterviewer(speech_service)

# 导出函数（用于测试兼容）
def get_client_manager():
    """获取客户端管理器（用于测试兼容）"""
    from core.qwen_llama_client import get_client_manager
    return get_client_manager()

async def get_speech_service() -> SpeechService:
    """获取语音服务实例"""
    return speech_service

# Export
__all__ = ["SpeechService", "VoiceInterviewer", "speech_service", "voice_interviewer", "get_speech_service", "get_client_manager"]