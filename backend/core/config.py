"""
VITA配置管理模块
管理所有环境变量和模型配置 - 纯本地语音服务版本
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VITAConfig:
    """VITA项目配置类 - 纯本地语音服务版本"""
    
    # 豆包实时语音大模型常量 - 更新为最新模型
    REALTIME_VOICE_MODEL = "Doubao-Seed-1.6-flash"  # 极速响应，TPOT仅需10ms
    
    # 豆包专业语音大模型常量 - 基于图片中的专业语音模型
    REALTIME_VOICE_MODEL = "Doubao-Seed-1.6-flash"      # 实时对话：极速响应，TPOT仅需10ms
    VOICE_RECOGNITION_MODEL = "Doubao-流式语音识别"       # 专业流式语音识别
    VOICE_SYNTHESIS_MODEL = "Doubao-语音合成"           # 专业语音合成
    VOICE_FILE_MODEL = "Doubao-录音文件识别"            # 录音文件识别
    VOICE_CLONING_MODEL = "Doubao-声音复刻"             # 声音复刻（高级功能）
    
    # 豆包MVP最优架构配置 - 基于图片中所有可用模型的最优选择
    MODEL_CONFIG = {
        "doubao": {
            # 🚀 实时交互：极速响应模型 (TPOT仅需10ms)
            "chat": "Doubao-Seed-1.6-flash",                    # 实时聊天 - 10ms极速响应
            "realtime_voice": "Doubao-Seed-1.6-flash",          # 实时语音交互 - 极速响应核心
            
            # 🧠 深度分析：强思考模型 (Coding/Math能力大幅提升)
            "interview": "Doubao-Seed-1.6-thinking",            # 面试对话 - 深度思考推理
            "analysis": "Doubao-Seed-1.6-thinking",             # 深度分析 - 强化思考能力
            "code": "Doubao-Seed-1.6-thinking",                 # 代码评估 - Coding表现更强
            "math": "Doubao-Seed-1.6-thinking",                 # 数学推理 - Math表现更强
            
            # 🎤 专业语音模型：豆包语音专用模型
            "voice_recognition": "Doubao-流式语音识别",           # 专业流式语音识别
            "voice_synthesis": "Doubao-语音合成",               # 专业语音合成
            "voice_file_recognition": "Doubao-录音文件识别",       # 录音文件识别
            "voice_cloning": "Doubao-声音复刻",                 # 声音复刻（高级功能）
            
            # 🔍 多模态理解：视觉思考模型
            "multimodal_interview": "Doubao-1.5-thinking-vision-pro",  # 多模态面试 - 视觉深度思考
            "vision": "Doubao-1.5-vision-pro",                 # 视觉问答 - 多模态理解
            "multimodal": "Doubao-Seed-1.6",                   # 通用多模态处理
            
            # 📄 长文本处理：超长上下文模型
            "long_context": "Doubao-pro-256k",                 # 超长上下文 - 256k token
            "document_analysis": "Doubao-pro-256k",            # 文档分析 - 长文本理解
            
            # 🔄 备用和轻量级模型
            "fallback": "Doubao-lite-4k",                      # 轻量备用 - 快速响应
            "lite": "Doubao-lite-128k",                        # 中等轻量 - 平衡性能
            
            # 🎵 本地备用（保持原有本地能力）
            "speech_recognition_fallback": "local-whisper",     # 本地语音识别备用
            "speech_synthesis_fallback": "local-tts",          # 本地语音合成备用
        },
        
        # Qwen系列 - 作为二级备用
        "qwen": {
            "chat": "qwen-plus",
            "analysis": "qwen-plus", 
            "interview": "qwen-plus",
            "code": "Qwen/Qwen2.5-Coder-32B-Instruct",
            "math": "Qwen/Qwen2.5-Math-72B-Instruct",
            "fallback": "qwen-turbo",
            "vision": "Qwen/Qwen2-VL-72B-Instruct",
            "long_context": "qwen-long",
            "turbo": "qwen-turbo",
            "audio": "Qwen/Qwen2-Audio-7B-Instruct",
            "speech_recognition": "local-whisper",
            "speech_synthesis": "local-tts"
        },
        
        # Llama系列 - 作为最终备用
        "llama": {
            "chat": "Llama-3.3-70B-Instruct",
            "analysis": "__REMOVED_API_KEY__",
            "interview": "Llama-3.3-70B-Instruct", 
            "code": "__REMOVED_API_KEY__",
            "math": "__REMOVED_API_KEY__",
            "fallback": "Llama-3.3-8B-Instruct",
            "speech_recognition": "local-whisper",
            "speech_synthesis": "local-tts"
        }
    }
    
    # 三模型架构配置开关 - 现在豆包优先
    USE_DOUBAO_PRIMARY = True   # 是否启用豆包作为主要方案（新增）
    USE_QWEN_FALLBACK = True    # 是否启用Qwen作为备用方案
    USE_LLAMA_FALLBACK = True   # 是否启用Llama作为最终备用方案
    ENABLE_AUTO_SWITCH = True   # 是否启用自动切换
    PREFER_DOUBAO = True        # 优先使用豆包（新增）
    PREFER_QWEN = False         # 不再优先使用Qwen
    PREFER_LLAMA = False        # 不再优先使用Llama
    
    # 本地Whisper配置 - 强制启用本地Whisper
    USE_LOCAL_WHISPER = True  # 强制启用本地Whisper
    LOCAL_WHISPER_MODEL = os.getenv("LOCAL_WHISPER_MODEL", "medium")
    LOCAL_WHISPER_DEVICE = os.getenv("LOCAL_WHISPER_DEVICE", "auto")
    LOCAL_WHISPER_COMPUTE_TYPE = os.getenv("LOCAL_WHISPER_COMPUTE_TYPE", "float16")
    LOCAL_WHISPER_MODEL_DIR = os.getenv("LOCAL_WHISPER_MODEL_DIR", "whisper_download")
    DISABLE_WHISPER_ONLINE = os.getenv("DISABLE_WHISPER_ONLINE", "false").lower() == "true"
    
    # 本地TTS配置 - 保留作为最终备用
    USE_LOCAL_TTS = True  # 保留本地TTS作为备用
    LOCAL_TTS_ENGINE = os.getenv("LOCAL_TTS_ENGINE", "edge-tts")  # edge-tts/pyttsx3
    
    # 豆包API配置（主要方案）
    DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "__REMOVED_API_KEY__")  # 用户提供的豆包API密钥（UUID格式）
    DOUBAO_API_BASE_URL = os.getenv("DOUBAO_API_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    DOUBAO_REALTIME_URL = os.getenv("DOUBAO_REALTIME_URL", "wss://openspeech.bytedance.com/api/v3/realtime/dialogue")  # 更新为正确的WebSocket URL
    
    # Qwen API配置（备用方案）
    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "__REMOVED_API_KEY__")
    
    # Llama API配置（最终备用方案）
    LLAMA_API_KEY = os.getenv("LLAMA_API_KEY", "LLM|727268019715816|R9EX2i7cmHya1_7HAFiIAxxtAUk")
    LLAMA_API_BASE_URL = os.getenv("LLAMA_API_BASE_URL", "https://api.llama-api.com/v1")
    
    # 语音配置 - 豆包专业语音MVP方案
    VOICE_CONFIG = {
        "primary_service": "doubao",              # 主要语音服务：豆包专业语音模型
        "fallback_service": "local",              # 备用语音服务：本地服务
        
        # 豆包专业语音模型配置
        "doubao_voice_models": {
            "realtime_recognition": "Doubao-流式语音识别",    # 实时流式语音识别
            "file_recognition": "Doubao-录音文件识别",        # 文件语音识别  
            "synthesis": "Doubao-语音合成",                 # 专业语音合成
            "voice_cloning": "Doubao-声音复刻",             # 声音复刻
            "realtime_conversation": "Doubao-Seed-1.6-flash" # 实时对话（10ms极速）
        },
        
        # 语音质量配置
        "default_voice": "professional_female",   # 豆包专业女性声音，适合面试
        "fallback_voice": "nova",                # 本地备用声音
        "default_speed": 1.0,                    # 正常语速
        "quality_mode": "high",                  # 高质量模式
        
        # 技术参数
        "max_audio_size_mb": 25,                 # 最大音频文件大小
        "supported_formats": ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"],
        "sample_rate": 16000,                    # 采样率
        "chunk_duration_ms": 1000,              # 分块处理时长
        
        # 本地备用配置
        "tts_engine": "edge-tts",                # 本地TTS引擎（备用）
        "whisper_model": "medium",               # 本地Whisper模型（备用）
        "use_realtime_voice": True,              # 启用实时语音交互
        
        # 实时语音功能配置
        "realtime_features": {
            "stream_recognition": True,           # 流式语音识别
            "real_time_synthesis": True,         # 实时语音合成
            "voice_interruption": True,          # 语音打断功能
            "echo_cancellation": True,           # 回声消除
            "noise_reduction": True,             # 噪音降低
            "auto_gain_control": True            # 自动增益控制
        },
        
        # 高级语音功能
        "advanced_features": {
            "voice_cloning": True,               # 声音复刻功能
            "emotion_synthesis": True,           # 情感语音合成
            "multi_speaker": True,               # 多说话人识别
            "background_noise_handling": True   # 背景噪音处理
        }
    }
    
    # 服务器配置
    SERVER_CONFIG = {
        "host": "0.0.0.0",
        "backend_port": 8000,
        "vision_port": 8001,
        "frontend_port": 5173,
        "debug": True
    }
    
    # 性能配置 - 优化内存使用
    PERFORMANCE_CONFIG = {
        "cache_size": 50,              # 减少缓存大小以节省内存
        "request_timeout": 30,         # 请求超时时间(秒)
        "max_concurrent_requests": 5,  # 减少最大并发请求数以节省内存
        "rate_limit_per_minute": 60,   # 每分钟请求限制
        "memory_limit_mb": 500,        # 内存使用限制(MB)
        "gc_threshold": 300,           # 垃圾回收阈值(MB)
        "model_cache_size": 2,         # 最多缓存2个模型实例
        "connection_pool_size": 10,    # 连接池大小
        "max_retries": 3               # 最大重试次数
    }
    
    # Qwen特有功能配置
    QWEN_FEATURES = {
        "enable_vision": True,  # 启用视觉理解
        "enable_long_context": True,  # 启用长文本处理
        "max_context_length": 32000,  # Qwen支持的最大上下文长度
        "enable_function_calling": True,  # 启用函数调用
        "enable_plugins": True,  # 启用插件系统
        "supported_plugins": ["web_search", "calculator", "code_interpreter"]
    }
    
    @classmethod
    def _validate_key(cls, key: str) -> str:
        """验证API密钥格式并返回类型"""
        if not key or not isinstance(key, str):
            raise ValueError("无效的API密钥格式")
        
        key = key.strip()
        
        # Qwen密钥格式：sk-xxx（需要优先检查，避免被豆包逻辑误识别）
        if key.startswith("sk-") and len(key) >= 30 and len(key) <= 60:
            logger.debug(f"✅ 检测到有效的Qwen API密钥")
            return 'qwen'
        
        # Llama API密钥格式：LLM|数字|字符串
        elif key.startswith("LLM|"):
            parts = key.split("|")
            if len(parts) >= 3 and parts[1].isdigit():
                logger.debug(f"✅ 检测到有效的Llama API密钥")
                return 'llama'
            else:
                raise ValueError("Llama API密钥格式不正确")
        
        # 豆包API密钥格式支持多种：
        # 1. UUID格式：__REMOVED_API_KEY__
        # 2. 火山引擎格式：包含字母数字和下划线的字符串
        elif len(key) == 36 and key.count('-') == 4:
            # 验证UUID格式：__REMOVED_API_KEY__
            import re
            uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
            if uuid_pattern.match(key):
                logger.debug(f"✅ 检测到有效的豆包API密钥（UUID格式）")
                return 'doubao'
        elif len(key) >= 20 and len(key) <= 50 and key.replace('_', '').replace('-', '').isalnum() and not key.startswith("sk-"):
            # 火山引擎豆包API密钥：字母数字和下划线组合，长度在20-50之间，但不以sk-开头
            logger.debug(f"✅ 检测到有效的豆包API密钥（火山引擎格式）")
            return 'doubao'
        
        else:
            raise ValueError(f"无法识别的API密钥类型: {key[:10]}...")
    
    @classmethod
    def validate_environment(cls) -> Dict[str, Any]:
        """验证环境配置"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "providers": [],
            "speech_services": []
        }
        
        # 检查豆包配置（首选）
        try:
            doubao_key = cls.get_doubao_key()
            if doubao_key:
                key_type = cls._validate_key(doubao_key)
                if key_type == 'doubao':
                    validation_result["providers"].append("doubao")
                    logger.info("✅ 豆包配置有效")
        except Exception as e:
            validation_result["warnings"].append(f"豆包配置问题: {e}")
            logger.warning(f"⚠️ 豆包配置问题: {e}")
        
        # 检查Qwen配置（备用）
        try:
            qwen_key = cls.get_qwen_key()
            if qwen_key:
                key_type = cls._validate_key(qwen_key)
                if key_type == 'qwen':
                    validation_result["providers"].append("qwen")
                    logger.info("✅ Qwen配置有效")
        except Exception as e:
            validation_result["warnings"].append(f"Qwen配置问题: {e}")
            logger.warning(f"⚠️ Qwen配置问题: {e}")
        
        # 检查Llama配置（最终备用）
        try:
            llama_key = cls.get_llama_key()
            if llama_key:
                key_type = cls._validate_key(llama_key)
                if key_type == 'llama':
                    validation_result["providers"].append("llama")
                    logger.info("✅ Llama配置有效")
        except Exception as e:
            validation_result["warnings"].append(f"Llama配置问题: {e}")
            logger.warning(f"⚠️ Llama配置问题: {e}")
        
        # 检查本地语音服务
        if cls.USE_LOCAL_WHISPER:
            validation_result["speech_services"].append("local-whisper")
            logger.info("✅ 本地Whisper已启用")
        
        if cls.USE_LOCAL_TTS:
            validation_result["speech_services"].append("local-tts")
            logger.info("✅ 本地TTS已启用")
        
        # 检查是否至少有一个可用的提供商
        if not validation_result["providers"]:
            validation_result["valid"] = False
            validation_result["errors"].append("没有可用的API提供商")
            logger.error("❌ 没有可用的API提供商")
        
        return validation_result
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "doubao_configured": bool(cls.DOUBAO_API_KEY),
            "qwen_configured": bool(cls.QWEN_API_KEY),
            "llama_configured": bool(cls.LLAMA_API_KEY),
            "local_whisper_enabled": cls.USE_LOCAL_WHISPER,
            "local_tts_enabled": cls.USE_LOCAL_TTS,
            "doubao_primary_enabled": cls.USE_DOUBAO_PRIMARY,
            "qwen_fallback_enabled": cls.USE_QWEN_FALLBACK,
            "llama_fallback_enabled": cls.USE_LLAMA_FALLBACK,
            "prefer_doubao": cls.PREFER_DOUBAO,
            "auto_switch_enabled": cls.ENABLE_AUTO_SWITCH,
            "realtime_voice_enabled": cls.VOICE_CONFIG.get("use_realtime_voice", False)
        }
    
    @classmethod
    def get_doubao_key(cls) -> str:
        """获取豆包API密钥"""
        # 先从环境变量获取，再从类属性获取
        doubao_key = os.getenv("DOUBAO_API_KEY") or cls.DOUBAO_API_KEY
        
        # 清理API密钥格式
        if doubao_key:
            doubao_key = doubao_key.strip()
            # 移除可能的额外引号
            if doubao_key.startswith('"') and doubao_key.endswith('"'):
                doubao_key = doubao_key[1:-1]
            if doubao_key.startswith("'") and doubao_key.endswith("'"):
                doubao_key = doubao_key[1:-1]
            
            logger.debug(f"🔑 检查豆包API密钥: {doubao_key[:8]}...")
            
            # 简化验证逻辑：UUID格式或长度合理的字符串
            if (len(doubao_key) == 36 and doubao_key.count('-') == 4) or (len(doubao_key) >= 20 and not doubao_key.startswith("sk-")):
                logger.debug(f"✅ 豆包API密钥验证成功")
                return doubao_key
            else:
                logger.warning(f"⚠️ 豆包API密钥格式无效: 长度={len(doubao_key)}, 格式={doubao_key[:10]}")
        else:
            logger.warning("⚠️ 未找到豆包API密钥（环境变量或配置）")
        
        # 不抛出异常，返回空字符串让上层处理
        return ""
    
    @classmethod
    def get_doubao_base_url(cls) -> str:
        """获取豆包API基础URL"""
        return cls.DOUBAO_API_BASE_URL
    
    @classmethod
    def get_doubao_realtime_url(cls) -> str:
        """获取豆包实时语音URL"""
        return cls.DOUBAO_REALTIME_URL
    
    @classmethod
    def get_llama_key(cls) -> str:
        """获取Llama API密钥"""
        return cls.LLAMA_API_KEY
    
    @classmethod
    def get_llama_base_url(cls) -> str:
        """获取Llama API基础URL"""
        return cls.LLAMA_API_BASE_URL
    
    @classmethod
    def get_qwen_key(cls) -> str:
        """获取Qwen API密钥"""
        # 先从环境变量获取，再从类属性获取
        qwen_key = os.getenv("QWEN_API_KEY") or cls.QWEN_API_KEY
        
        # 清理API密钥格式
        if qwen_key:
            qwen_key = qwen_key.strip()
            # 移除可能的额外引号
            if qwen_key.startswith('"') and qwen_key.endswith('"'):
                qwen_key = qwen_key[1:-1]
            if qwen_key.startswith("'") and qwen_key.endswith("'"):
                qwen_key = qwen_key[1:-1]
            
            logger.debug(f"🔑 检查Qwen API密钥: {qwen_key[:10]}...")
            
            # 简化验证逻辑：只要是sk-开头且长度合理就认为有效
            if qwen_key.startswith("sk-") and len(qwen_key) >= 30:
                logger.debug(f"✅ Qwen API密钥验证成功")
                return qwen_key
            else:
                logger.warning(f"⚠️ Qwen API密钥格式无效: 长度={len(qwen_key)}, 前缀={qwen_key[:10]}")
        else:
            logger.warning("⚠️ 未找到Qwen API密钥（环境变量或配置）")
        
        # 不抛出异常，返回空字符串让上层处理
        return ""
    
    @classmethod
    def get_model_for_provider(cls, provider: str, function_type: str) -> str:
        """
        根据提供商和功能类型获取对应的模型
        
        Args:
            provider: 提供商类型 (doubao, qwen, 或 llama)
            function_type: 功能类型 (chat, analysis, speech_recognition, speech_synthesis, code, math, realtime_voice)
            
        Returns:
            对应的模型名称
        """
        if provider not in cls.MODEL_CONFIG:
            raise ValueError(f"不支持的提供商: {provider}")
        
        model_mapping = cls.MODEL_CONFIG[provider]
        
        # 处理功能类型映射 - 豆包优先，本地备用
        if function_type == "speech_to_text" or function_type == "speech_recognition":
            if provider == "doubao":
                return model_mapping.get("voice_recognition", "doubao-stt")
            else:
                return "local-whisper"  # 非豆包服务使用本地Whisper
        elif function_type == "text_to_speech" or function_type == "speech_synthesis":
            if provider == "doubao":
                return model_mapping.get("voice_synthesis", "doubao-tts")
            else:
                return "local-tts"  # 非豆包服务使用本地TTS
        elif function_type == "realtime_voice":
            if provider == "doubao":
                return model_mapping.get("realtime_voice", "Doubao-实时语音大模型")
            else:
                raise ValueError(f"{provider} 不支持实时语音功能")
        elif function_type == "code_generation":
            function_type = "code"
        elif function_type == "math_reasoning":
            function_type = "math"
        
        return model_mapping.get(function_type, model_mapping.get("chat"))
    
    @classmethod
    def get_qwen_chat_model(cls) -> str:
        """获取Qwen聊天模型"""
        return cls.get_model_for_provider("qwen", "chat")
    
    @classmethod
    def get_qwen_analysis_model(cls) -> str:
        """获取Qwen分析模型"""
        return cls.get_model_for_provider("qwen", "analysis")
    
    @classmethod
    def get_qwen_interview_model(cls) -> str:
        """获取Qwen面试模型"""
        return cls.get_model_for_provider("qwen", "interview")
    
    @classmethod
    def get_qwen_fallback_model(cls) -> str:
        """获取Qwen备用模型"""
        return cls.get_model_for_provider("qwen", "fallback")
    
    @classmethod
    def get_llama_chat_model(cls) -> str:
        """获取Llama聊天模型（备用）"""
        return cls.get_model_for_provider("llama", "chat")
    
    @classmethod
    def get_llama_analysis_model(cls) -> str:
        """获取Llama分析模型（备用）"""
        return cls.get_model_for_provider("llama", "analysis")
    
    @classmethod
    def get_llama_interview_model(cls) -> str:
        """获取Llama面试模型（备用）"""
        return cls.get_model_for_provider("llama", "interview")
    
    @classmethod
    def get_llama_fallback_model(cls) -> str:
        """获取Llama备用模型"""
        return cls.get_model_for_provider("llama", "fallback")
    
    @classmethod
    def get_voice_config(cls) -> Dict[str, Any]:
        """获取语音配置 - 完全本地化版本"""
        return {
            "default_voice": os.getenv("TTS_DEFAULT_VOICE", cls.VOICE_CONFIG["default_voice"]),
            "default_speed": float(os.getenv("DEFAULT_SPEECH_SPEED", cls.VOICE_CONFIG["default_speed"])),
            "max_audio_size_mb": int(os.getenv("MAX_AUDIO_SIZE_MB", cls.VOICE_CONFIG["max_audio_size_mb"])),
            "supported_formats": cls.VOICE_CONFIG["supported_formats"],
            "tts_engine": cls.VOICE_CONFIG["tts_engine"],
            "whisper_model": cls.VOICE_CONFIG["whisper_model"],
            "use_local_services": True  # 强制使用本地服务
        }
    
    @classmethod
    def get_local_whisper_config(cls) -> Dict[str, Any]:
        """获取本地Whisper配置"""
        return {
            "use_local_whisper": cls.USE_LOCAL_WHISPER,
            "model_size": cls.LOCAL_WHISPER_MODEL,
            "device": cls.LOCAL_WHISPER_DEVICE,
            "compute_type": cls.LOCAL_WHISPER_COMPUTE_TYPE,
            "model_dir": cls.LOCAL_WHISPER_MODEL_DIR,
            "disable_online": cls.DISABLE_WHISPER_ONLINE
        }
    
    @classmethod
    def get_local_tts_config(cls) -> Dict[str, Any]:
        """获取本地TTS配置"""
        return {
            "use_local_tts": cls.USE_LOCAL_TTS,
            "engine": cls.LOCAL_TTS_ENGINE,
            "voice_mapping": {
                "nova": "zh-CN-XiaoxiaoNeural",
                "echo": "zh-CN-YunxiNeural",
                "alloy": "zh-CN-XiaoyiNeural",
                "fable": "zh-CN-YunjianNeural",
                "onyx": "zh-CN-YunxiaNeural",
                "shimmer": "zh-CN-XiaoshuangNeural"
            }
        }
    
    @classmethod
    def get_server_config(cls) -> Dict[str, Any]:
        """获取服务器配置"""
        return {
            "host": os.getenv("BACKEND_HOST", cls.SERVER_CONFIG["host"]),
            "backend_port": int(os.getenv("BACKEND_PORT", cls.SERVER_CONFIG["backend_port"])),
            "vision_port": int(os.getenv("VISION_PORT", cls.SERVER_CONFIG["vision_port"])),
            "frontend_port": int(os.getenv("FRONTEND_PORT", cls.SERVER_CONFIG["frontend_port"])),
            "debug": os.getenv("DEBUG", "true").lower() == "true"
        }
    
    @classmethod
    def get_service_status(cls) -> Dict[str, Any]:
        """获取服务状态信息"""
        status = {
            "status": "healthy",
            "doubao_configured": False,
            "qwen_configured": False,
            "llama_configured": bool(cls.LLAMA_API_KEY),
            "fallback_enabled": cls.USE_LLAMA_FALLBACK,
            "auto_switch_enabled": cls.ENABLE_AUTO_SWITCH,
            "prefer_doubao": getattr(cls, 'PREFER_DOUBAO', True),
            "prefer_qwen": cls.PREFER_QWEN,
            "local_whisper_enabled": cls.USE_LOCAL_WHISPER,
            "local_tts_enabled": cls.USE_LOCAL_TTS,
            "models_configured": len(cls.MODEL_CONFIG)
        }
        
        # 检查豆包配置
        try:
            doubao_key = cls.get_doubao_key()
            status["doubao_configured"] = bool(doubao_key)
        except Exception:
            status["doubao_configured"] = False
        
        # 检查Qwen配置
        try:
            qwen_key = cls.get_qwen_key()
            status["qwen_configured"] = bool(qwen_key)
        except Exception:
            status["qwen_configured"] = False
        
        # 至少需要一个有效的配置
        if not any([status["doubao_configured"], status["qwen_configured"], status["llama_configured"]]):
            status["status"] = "unhealthy"
        
        return status
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否有效"""
        # 至少需要一个有效的API密钥
        has_llama = bool(cls.LLAMA_API_KEY)
        has_qwen = False
        
        try:
            cls.get_qwen_key()
            has_qwen = True
        except:
            pass
        
        if not has_llama and not has_qwen:
            raise ValueError("至少需要配置一个有效的API密钥（Llama或Qwen）")
        
        return True
    
    @classmethod
    def print_config_summary(cls):
        """打印配置摘要"""
        print("\n" + "="*60)
        print("🚀 VITA 豆包专业语音MVP三模型架构配置摘要")
        print("="*60)
        
        # 三模型架构状态
        status = cls.get_service_status()
        summary = cls.get_config_summary()
        
        print(f"\n🏗️  架构状态: {status['status']}")
        print(f"🎯 豆包配置: {'已配置 ✅' if summary['doubao_configured'] else '未配置 ❌'}")
        print(f"🤖 Qwen配置: {'已配置 ✅' if summary['qwen_configured'] else '未配置 ❌'}")
        print(f"🤖 Llama配置: {'已配置 ✅' if summary['llama_configured'] else '未配置 ❌'}")
        print(f"🔄 备用方案: {'启用' if summary['qwen_fallback_enabled'] else '禁用'}")
        print(f"⚡ 自动切换: {'启用' if summary['auto_switch_enabled'] else '禁用'}")
        print(f"🎯 优先使用: {'豆包专业语音MVP' if summary['prefer_doubao'] else 'Qwen/Llama'}")
        
        # 豆包专业语音服务状态
        print(f"\n🎵 豆包专业语音服务配置:")
        print(f"  - 🚀 实时对话: Doubao-Seed-1.6-flash (10ms极速)")
        print(f"  - 🎤 流式识别: Doubao-流式语音识别")
        print(f"  - 🔊 语音合成: Doubao-语音合成")
        print(f"  - 📁 文件识别: Doubao-录音文件识别")
        print(f"  - 🎭 声音复刻: Doubao-声音复刻")
        print(f"  - 💻 本地Whisper: 启用 ✅ (备用)")
        print(f"  - 🔊 本地TTS: 启用 ✅ (备用)")
        print(f"  - 主要服务: doubao专业语音")
        print(f"  - 备用服务: local")
        
        # 豆包模型详细配置
        print(f"\n📌 豆包模型配置（主要）:")
        doubao_models = cls.MODEL_CONFIG.get("doubao", {})
        for task, model in doubao_models.items():
            print(f"  - {task}: {model}")
        
        # Qwen模型配置
        print(f"\n📌 Qwen模型配置（二级备用）:")
        qwen_models = cls.MODEL_CONFIG.get("qwen", {})
        for task, model in qwen_models.items():
            print(f"  - {task}: {model}")
        
        # Llama模型配置
        print(f"\n📌 Llama模型配置（最终备用）:")
        llama_models = cls.MODEL_CONFIG.get("llama", {})
        for task, model in llama_models.items():
            print(f"  - {task}: {model}")
        
        # 语音功能特性
        print(f"\n🎵 豆包专业语音功能:")
        print(f"  - ⚡ 极速响应: 10ms TPOT")
        print(f"  - 🔄 流式识别: 实时语音转文字")
        print(f"  - 🎭 声音复刻: 高级语音克隆")
        print(f"  - 🎪 情感合成: 情感化语音输出") 
        print(f"  - 🎯 多说话人: 智能说话人识别")
        print(f"  - 🔇 噪音处理: 背景噪音消除")
        
        print(f"\n🎵 默认语音: professional_female")
        print(f"🌐 服务端口: 8000")
        print(f"✅ 豆包专业语音为首选，本地服务作为备用")
        print(f"✅ 豆包专业语音MVP架构，智能三级备用切换")
        print(f"✅ 支持端到端专业语音对话，极速+专业+智能")
        print("="*60)


# 全局配置实例
config = VITAConfig()

# 智能模型选择器 - 豆包专业语音MVP架构版本
class ModelSelector:
    """智能模型选择器 - 豆包专业语音MVP架构版本"""
    
    @staticmethod
    def get_best_model_for_task(task_type: str, complexity: str = "medium") -> str:
        """
        根据任务类型和复杂度选择最佳模型
        豆包专业语音MVP架构：极速响应+深度思考+专业语音+多模态理解
        """
        # 专业语音识别任务：首选Doubao-流式语音识别
        if task_type in ["voice_recognition", "speech_to_text", "streaming_asr"]:
            try:
                return config.get_model_for_provider("doubao", "voice_recognition")  # Doubao-流式语音识别
            except:
                return config.get_model_for_provider("qwen", "speech_recognition")  # 降级到本地Whisper
        
        # 专业语音合成任务：首选Doubao-语音合成
        elif task_type in ["voice_synthesis", "text_to_speech", "tts"]:
            try:
                return config.get_model_for_provider("doubao", "voice_synthesis")  # Doubao-语音合成
            except:
                return config.get_model_for_provider("qwen", "speech_synthesis")  # 降级到本地TTS
        
        # 文件语音识别：首选Doubao-录音文件识别
        elif task_type in ["file_recognition", "audio_file_transcription"]:
            try:
                return config.get_model_for_provider("doubao", "voice_file_recognition")  # Doubao-录音文件识别
            except:
                return config.get_model_for_provider("qwen", "speech_recognition")  # 降级到本地
        
        # 声音复刻任务：使用Doubao-声音复刻
        elif task_type in ["voice_cloning", "voice_mimicking"]:
            try:
                return config.get_model_for_provider("doubao", "voice_cloning")  # Doubao-声音复刻
            except:
                return config.get_model_for_provider("qwen", "fallback")  # 降级到基础模型
        
        # 实时语音交互任务：首选Doubao-Seed-1.6-flash(10ms极速)
        elif task_type in ["realtime_voice", "voice_interview", "interactive_speech", "real_time_chat"]:
            try:
                return config.get_model_for_provider("doubao", "realtime_voice")  # Doubao-Seed-1.6-flash
            except:
                return config.get_model_for_provider("qwen", "chat")  # 降级到Qwen
        
        # 面试对话任务：首选Doubao-Seed-1.6-thinking(思考能力大幅提升)
        elif task_type in ["interview", "interview_chat", "assessment"]:
            try:
                return config.get_model_for_provider("doubao", "interview")  # Doubao-Seed-1.6-thinking
            except:
                return config.get_model_for_provider("qwen", "interview")  # 降级到Qwen
        
        # 代码评估任务：首选Doubao-Seed-1.6-thinking(Coding表现更强)
        elif task_type in ["code", "coding", "programming", "code_review"]:
            try:
                return config.get_model_for_provider("doubao", "code")  # Doubao-Seed-1.6-thinking
            except:
                return config.get_model_for_provider("qwen", "code")  # 降级到Qwen专业代码模型
        
        # 数学推理任务：首选Doubao-Seed-1.6-thinking(Math表现更强)
        elif task_type in ["math", "mathematics", "calculation", "reasoning"]:
            try:
                return config.get_model_for_provider("doubao", "math")  # Doubao-Seed-1.6-thinking
            except:
                return config.get_model_for_provider("qwen", "math")  # 降级到Qwen数学模型
        
        # 多模态面试任务：首选Doubao-1.5-thinking-vision-pro(视觉深度思考)
        elif task_type in ["multimodal_interview", "visual_interview", "image_analysis"]:
            try:
                return config.get_model_for_provider("doubao", "multimodal_interview")  # Doubao-1.5-thinking-vision-pro
            except:
                return config.get_model_for_provider("qwen", "vision")  # 降级到Qwen
        
        # 视觉理解任务：首选Doubao-1.5-vision-pro
        elif task_type in ["vision", "image_understanding", "visual_qa"]:
            try:
                return config.get_model_for_provider("doubao", "vision")  # Doubao-1.5-vision-pro
            except:
                return config.get_model_for_provider("qwen", "vision")  # 降级到Qwen
        
        # 长文本处理：首选Doubao-pro-256k(超长上下文)
        elif task_type in ["long_context", "document_analysis", "long_text"]:
            try:
                return config.get_model_for_provider("doubao", "long_context")  # Doubao-pro-256k
            except:
                return config.get_model_for_provider("qwen", "long_context")  # 降级到Qwen
        
        # 深度分析任务：首选Doubao-Seed-1.6-thinking
        elif task_type in ["analysis", "deep_analysis", "reasoning"]:
            try:
                return config.get_model_for_provider("doubao", "analysis")  # Doubao-Seed-1.6-thinking
            except:
                return config.get_model_for_provider("qwen", "analysis")  # 降级到Qwen
        
        # 通用聊天任务：根据复杂度选择
        elif task_type in ["chat", "conversation", "general"]:
            if complexity == "high":
                try:
                    return config.get_model_for_provider("doubao", "interview")  # 高复杂度用思考模型
                except:
                    return config.get_model_for_provider("qwen", "chat")
            else:
                try:
                    return config.get_model_for_provider("doubao", "chat")  # 普通聊天用极速模型
                except:
                    return config.get_model_for_provider("qwen", "chat")
        
        # 默认选择：豆包极速聊天模型
        try:
            return config.get_model_for_provider("doubao", "chat")  # Doubao-Seed-1.6-flash
        except:
            try:
                return config.get_model_for_provider("qwen", "chat")  # 降级到Qwen
            except:
                return config.get_model_for_provider("llama", "chat")  # 最终降级到Llama
    
    @staticmethod
    def get_voice_model_for_task(voice_task: str) -> str:
        """
        专门为语音任务选择模型
        """
        voice_model_map = {
            "realtime_recognition": "Doubao-流式语音识别",
            "file_recognition": "Doubao-录音文件识别", 
            "synthesis": "Doubao-语音合成",
            "voice_cloning": "Doubao-声音复刻",
            "realtime_conversation": "Doubao-Seed-1.6-flash"
        }
        
        return voice_model_map.get(voice_task, "Doubao-Seed-1.6-flash")
    
    @staticmethod
    def get_provider_priority() -> list:
        """
        获取提供商优先级顺序
        """
        return ["doubao", "qwen", "llama"]
    
    @staticmethod 
    def is_voice_task(task_type: str) -> bool:
        """
        判断是否为语音相关任务
        """
        voice_tasks = [
            "voice_recognition", "speech_to_text", "streaming_asr",
            "voice_synthesis", "text_to_speech", "tts",
            "file_recognition", "audio_file_transcription",
            "voice_cloning", "voice_mimicking",
            "realtime_voice", "voice_interview", "interactive_speech"
        ]
        return task_type in voice_tasks


# 导出配置
__all__ = ["VITAConfig", "config", "ModelSelector"]