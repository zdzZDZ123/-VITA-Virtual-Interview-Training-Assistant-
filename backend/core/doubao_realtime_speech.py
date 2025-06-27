"""
豆包实时语音服务模块
提供基于豆包大模型的端到端实时语音交互功能
"""

import asyncio
import logging
import json
import time
import base64
import uuid
import websockets
from typing import Dict, Any, Optional, AsyncGenerator, List, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class DoubaoVoiceState(Enum):
    """豆包语音状态"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"

@dataclass
class DoubaoAudioConfig:
    """豆包音频配置"""
    sample_rate: int = 16000
    channels: int = 1
    format: str = "pcm"
    encoding: str = "base64"

@dataclass
class DoubaoVoiceResult:
    """豆包语音结果"""
    text: str
    confidence: float
    is_final: bool
    timestamp: float
    duration: Optional[float] = None
    emotion: Optional[str] = None
    audio_data: Optional[bytes] = None

class DoubaoRealtimeSpeechService:
    """豆包实时语音服务
    
    基于豆包大模型的端到端实时语音交互服务
    支持语音理解和生成的一体化处理
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws_url = "wss://doubao-realtime-voice.volcengine.com/v1/realtime"
        self.session_id = None
        self.websocket = None
        self.current_state = DoubaoVoiceState.IDLE
        self.audio_config = DoubaoAudioConfig()
        
        # 回调函数
        self.on_voice_start: Optional[Callable] = None
        self.on_voice_end: Optional[Callable] = None
        self.on_transcription: Optional[Callable[[DoubaoVoiceResult], None]] = None
        self.on_audio_response: Optional[Callable[[bytes], None]] = None
        self.on_state_change: Optional[Callable[[DoubaoVoiceState], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # 系统提示词配置
        self.system_prompt = "你是VITA智能面试助手，具备高情商和高智商。请用专业、友好的语调进行面试对话。"
        self.voice_style = "professional_female"  # 专业女性声音
        
        logger.info("豆包实时语音服务初始化完成")
    
    async def connect(self) -> bool:
        """连接到豆包实时语音服务"""
        try:
            self.session_id = str(uuid.uuid4())
            
            # 构建连接URL
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "X-Session-ID": self.session_id,
                "X-Service-Type": "realtime-voice"
            }
            
            logger.info(f"正在连接豆包实时语音服务... Session ID: {self.session_id}")
            
            # 建立WebSocket连接
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )
            
            # 发送会话初始化消息
            await self._send_session_init()
            
            # 启动消息接收循环
            asyncio.create_task(self._message_receiver())
            
            self._change_state(DoubaoVoiceState.IDLE)
            logger.info("✅ 豆包实时语音服务连接成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 连接豆包实时语音服务失败: {e}")
            await self._handle_error(f"连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        try:
            if self.websocket and not self.websocket.closed:
                await self.websocket.close()
            self._change_state(DoubaoVoiceState.IDLE)
            logger.info("豆包实时语音服务已断开连接")
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")
    
    async def _send_session_init(self):
        """发送会话初始化消息"""
        init_message = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": self.system_prompt,
                "voice": self.voice_style,
                "input_audio_format": self.audio_config.format,
                "output_audio_format": "mp3",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 1000
                },
                "tool_choice": "none",
                "temperature": 0.8
            }
        }
        
        await self._send_message(init_message)
        logger.info("已发送会话初始化消息")
    
    async def _send_message(self, message: Dict[str, Any]):
        """发送消息到WebSocket"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.send(json.dumps(message))
    
    async def _message_receiver(self):
        """接收并处理WebSocket消息"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析错误: {e}")
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket连接已关闭")
        except Exception as e:
            logger.error(f"消息接收循环出错: {e}")
            await self._handle_error(f"消息接收出错: {e}")
    
    async def _handle_message(self, data: Dict[str, Any]):
        """处理接收到的消息"""
        message_type = data.get("type", "")
        
        if message_type == "session.created":
            logger.info("会话创建成功")
            
        elif message_type == "session.updated":
            logger.info("会话配置已更新")
            
        elif message_type == "input_audio_buffer.speech_started":
            logger.debug("检测到语音开始")
            self._change_state(DoubaoVoiceState.LISTENING)
            if self.on_voice_start:
                await self.on_voice_start()
                
        elif message_type == "input_audio_buffer.speech_stopped":
            logger.debug("检测到语音结束")
            self._change_state(DoubaoVoiceState.PROCESSING)
            if self.on_voice_end:
                await self.on_voice_end()
                
        elif message_type == "conversation.item.input_audio_transcription.completed":
            # 语音转录完成
            transcript = data.get("transcript", "")
            confidence = data.get("confidence", 0.95)
            
            result = DoubaoVoiceResult(
                text=transcript,
                confidence=confidence,
                is_final=True,
                timestamp=time.time()
            )
            
            logger.info(f"语音转录: '{transcript}' (置信度: {confidence:.2f})")
            
            if self.on_transcription:
                await self.on_transcription(result)
                
        elif message_type == "response.audio.delta":
            # 接收到音频响应数据
            audio_base64 = data.get("delta", "")
            if audio_base64:
                try:
                    audio_data = base64.b64decode(audio_base64)
                    if self.on_audio_response:
                        await self.on_audio_response(audio_data)
                except Exception as e:
                    logger.error(f"音频数据解码失败: {e}")
                    
        elif message_type == "response.audio.done":
            logger.debug("音频响应完成")
            self._change_state(DoubaoVoiceState.IDLE)
            
        elif message_type == "response.done":
            logger.debug("响应完成")
            self._change_state(DoubaoVoiceState.IDLE)
            
        elif message_type == "error":
            error_msg = data.get("error", {}).get("message", "未知错误")
            logger.error(f"豆包服务错误: {error_msg}")
            await self._handle_error(error_msg)
            
        else:
            logger.debug(f"收到未处理的消息类型: {message_type}")
    
    async def send_audio_chunk(self, audio_data: bytes):
        """发送音频数据块"""
        if self.current_state == DoubaoVoiceState.ERROR:
            logger.warning("服务处于错误状态，跳过音频发送")
            return
            
        try:
            # 将音频数据编码为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            message = {
                "type": "input_audio_buffer.append",
                "audio": audio_base64
            }
            
            await self._send_message(message)
            
        except Exception as e:
            logger.error(f"发送音频数据失败: {e}")
            await self._handle_error(f"音频发送失败: {e}")
    
    async def commit_audio(self):
        """提交音频缓冲区（结束当前语音输入）"""
        try:
            message = {
                "type": "input_audio_buffer.commit"
            }
            await self._send_message(message)
            logger.debug("音频缓冲区已提交")
            
        except Exception as e:
            logger.error(f"提交音频缓冲区失败: {e}")
    
    async def send_text_message(self, text: str):
        """发送文本消息（用于测试或备用）"""
        try:
            message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": text
                        }
                    ]
                }
            }
            
            await self._send_message(message)
            
            # 触发响应生成
            response_message = {
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"],
                    "instructions": "请用专业友好的语调回应用户"
                }
            }
            
            await self._send_message(response_message)
            
        except Exception as e:
            logger.error(f"发送文本消息失败: {e}")
    
    async def interrupt_response(self):
        """中断当前响应"""
        try:
            message = {
                "type": "response.cancel"
            }
            await self._send_message(message)
            logger.debug("已中断当前响应")
            
        except Exception as e:
            logger.error(f"中断响应失败: {e}")
    
    def _change_state(self, new_state: DoubaoVoiceState):
        """改变状态"""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            logger.debug(f"状态变化: {old_state.value} -> {new_state.value}")
            
            if self.on_state_change:
                asyncio.create_task(self.on_state_change(new_state))
    
    async def _handle_error(self, error_msg: str):
        """处理错误"""
        self._change_state(DoubaoVoiceState.ERROR)
        if self.on_error:
            await self.on_error(error_msg)
    
    def set_callbacks(
        self,
        on_voice_start: Optional[Callable] = None,
        on_voice_end: Optional[Callable] = None,
        on_transcription: Optional[Callable[[DoubaoVoiceResult], None]] = None,
        on_audio_response: Optional[Callable[[bytes], None]] = None,
        on_state_change: Optional[Callable[[DoubaoVoiceState], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """设置回调函数"""
        self.on_voice_start = on_voice_start
        self.on_voice_end = on_voice_end
        self.on_transcription = on_transcription
        self.on_audio_response = on_audio_response
        self.on_state_change = on_state_change
        self.on_error = on_error
    
    def configure_voice(
        self,
        voice_style: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """配置语音参数"""
        if voice_style:
            self.voice_style = voice_style
        if system_prompt:
            self.system_prompt = system_prompt
        if temperature:
            self.temperature = temperature
        
        logger.info(f"语音配置已更新: voice={self.voice_style}")
    
    def get_current_state(self) -> DoubaoVoiceState:
        """获取当前状态"""
        return self.current_state
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.websocket and not self.websocket.closed
    
    def is_listening(self) -> bool:
        """是否正在监听"""
        return self.current_state == DoubaoVoiceState.LISTENING
    
    def is_processing(self) -> bool:
        """是否正在处理"""
        return self.current_state == DoubaoVoiceState.PROCESSING
    
    def is_speaking(self) -> bool:
        """是否正在说话"""
        return self.current_state == DoubaoVoiceState.SPEAKING

# 工厂函数
def create_doubao_realtime_service(api_key: str) -> DoubaoRealtimeSpeechService:
    """创建豆包实时语音服务实例"""
    return DoubaoRealtimeSpeechService(api_key)

# 全局实例（延迟初始化）
_doubao_service: Optional[DoubaoRealtimeSpeechService] = None

def get_doubao_realtime_service(api_key: Optional[str] = None) -> Optional[DoubaoRealtimeSpeechService]:
    """获取全局豆包实时语音服务实例"""
    global _doubao_service
    
    if _doubao_service is None and api_key:
        _doubao_service = create_doubao_realtime_service(api_key)
    
    return _doubao_service 