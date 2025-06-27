"""实时语音交互路由
提供WebSocket端点用于ChatGPT风格的实时语音交互
"""

import asyncio
import json
import logging
import time
import base64
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from core.realtime_speech import (
    RealTimeSpeechService, 
    AudioChunk, 
    VoiceActivityState, 
    TranscriptionResult
)
from models.session import storage, InterviewSession
from core.chat import chat_service

logger = logging.getLogger(__name__)

class RealTimeVoiceHandler:
    """实时语音处理器"""
    
    def __init__(self, websocket: WebSocket, session_id: str):
        logger.debug(f"[RealTimeVoiceHandler:Init] 初始化 handler, session_id={session_id}")
        self.websocket = websocket
        self.session_id = session_id
        self.speech_service = RealTimeSpeechService()
        # 使用现有的存储和聊天服务
        self.session: Optional[InterviewSession] = None
        self.is_connected = False
        self.current_question = ""
        
        # 配置语音服务回调
        self.speech_service.set_callbacks(
            on_speech_start=self._on_speech_start,
            on_speech_end=self._on_speech_end,
            on_transcription=self._on_transcription,
            on_state_change=self._on_state_change
        )
        
        logger.info(f"[RealTimeVoiceHandler:Init] Handler 创建完成, session_id={session_id}")
    
    async def connect(self):
        """建立连接"""
        logger.debug(f"[RealTimeVoiceHandler:WebSocket] 开始建立连接, session_id={self.session_id}")
        try:
            await self.websocket.accept()
            self.is_connected = True
            
            # 获取面试会话
            session_state = await storage.get_session(self.session_id)
            if session_state:
                self.session = InterviewSession(
                    session_id=session_state.session_id,
                    interview_type=session_state.interview_type
                )
            if not self.session:
                await self._send_error("面试会话不存在")
                return False
            
            # 发送连接成功消息
            await self._send_message({
                "type": "connected",
                "session_id": self.session_id,
                "state": self.speech_service.get_current_state().value,
                "message": "实时语音连接已建立"
            })
            
            # 发送第一个问题
            if self.session and self.session.current_question:
                self.current_question = self.session.current_question
                await self._send_question(self.current_question)
                await self._speak_question(self.current_question)
            
            logger.info(f"[RealTimeVoiceHandler:WebSocket] 连接建立成功, session_id={self.session_id}")
            return True
            
        except Exception as e:
            logger.exception(f"[RealTimeVoiceHandler:WebSocket] 连接建立失败: {e}")
            await self._send_error(f"连接失败: {str(e)}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        logger.debug(f"[RealTimeVoiceHandler:WebSocket] 开始断开连接, session_id={self.session_id}")
        self.is_connected = False
        logger.info(f"[RealTimeVoiceHandler:WebSocket] 连接已断开, session_id={self.session_id}")
    
    async def handle_message(self, message: Dict[str, Any]):
        """处理客户端消息"""
        logger.debug(f"[RealTimeVoiceHandler:WebSocket] 收到消息: {message} , session_id={self.session_id}")
        try:
            message_type = message.get("type")
            
            if message_type == "audio_chunk":
                await self._handle_audio_chunk(message)
            elif message_type == "configure":
                await self._handle_configure(message)
            elif message_type == "interrupt":
                await self._handle_interrupt()
            elif message_type == "ping":
                await self._send_message({"type": "pong", "timestamp": time.time()})
            else:
                logger.warning(f"未知消息类型: {message_type}")
                
        except Exception as e:
            logger.exception(f"[RealTimeVoiceHandler:WebSocket] 处理消息失败: {e}")
            await self._send_error(f"处理消息失败: {str(e)}")
    
    async def _handle_audio_chunk(self, message: Dict[str, Any]):
        """处理音频块"""
        try:
            # 解码音频数据
            audio_data_b64 = message.get("data")
            logger.debug(f"[RealTimeVoiceHandler:Audio] 收到音频块, size_base64={len(audio_data_b64 or '')}, session_id={self.session_id}")
            if not audio_data_b64:
                return
            
            audio_data = base64.b64decode(audio_data_b64)
            timestamp = message.get("timestamp", time.time())
            sample_rate = message.get("sample_rate", 16000)
            
            # 创建音频块
            audio_chunk = AudioChunk(
                data=audio_data,
                timestamp=timestamp,
                sample_rate=sample_rate
            )
            
            # 处理音频块
            transcription_result = await self.speech_service.process_audio_chunk(audio_chunk)
            
            if transcription_result:
                logger.debug(f"[RealTimeVoiceHandler:Audio] STT 结果: text='{transcription_result.text}', confidence={transcription_result.confidence}, session_id={self.session_id}")
            
            # 如果有转录结果，处理用户回答
            if transcription_result and transcription_result.text.strip():
                await self._process_user_answer(transcription_result.text)
                
        except Exception as e:
            logger.exception(f"[RealTimeVoiceHandler:Audio] 处理音频块失败: {e}")
            await self._send_error(f"音频处理失败: {str(e)}")
    
    async def _handle_configure(self, message: Dict[str, Any]):
        """处理配置消息"""
        try:
            config = message.get("config", {})
            
            self.speech_service.configure(
                vad_threshold=config.get("vad_threshold"),
                silence_timeout=config.get("silence_timeout"),
                min_speech_duration=config.get("min_speech_duration"),
                max_speech_duration=config.get("max_speech_duration")
            )
            
            await self._send_message({
                "type": "configured",
                "message": "配置已更新"
            })
            
        except Exception as e:
            logger.error(f"处理配置失败: {e}")
            await self._send_error(f"配置失败: {str(e)}")
    
    async def _handle_interrupt(self):
        """处理打断消息"""
        try:
            # 重置语音服务状态
            self.speech_service._reset_speech_state()
            
            await self._send_message({
                "type": "interrupted",
                "message": "语音已被打断"
            })
            
        except Exception as e:
            logger.error(f"处理打断失败: {e}")
    
    async def _process_user_answer(self, answer_text: str):
        """处理用户回答"""
        try:
            logger.info(f"[RealTimeVoiceHandler:Logic] 处理用户回答, text='{answer_text}', session_id={self.session_id}")
            
            # 更新会话历史
            session_state = await storage.get_session(self.session_id)
            if session_state:
                session_state.history.append({
                    "role": "candidate",
                    "content": answer_text,
                    "timestamp": time.time()
                })
                await storage.update_session(session_state)
                
                # 生成下一个问题
                next_question = await chat_service.generate_interview_question(
                    session_state.job_description,
                    session_state.history,
                    interview_type=session_state.interview_type
                )
                
                result = {
                    "success": True,
                    "next_question": next_question,
                    "is_completed": len(session_state.history) >= 10  # 示例完成条件
                }
                
                if result.get("success"):
                    next_question = result.get("next_question")
                    if next_question:
                        self.current_question = next_question
                        await self._send_question(next_question)
                        # 稍等一下再播放问题，给用户一些反应时间
                        await asyncio.sleep(0.5)
                        await self._speak_question(next_question)
                        logger.info(f"[RealTimeVoiceHandler:Logic] 生成下一个问题: '{next_question}', session_id={self.session_id}")
                    else:
                        # 面试结束
                        await self._send_message({
                            "type": "interview_completed",
                            "message": "面试已完成",
                            "session_id": self.session_id
                        })
                        
                        # 播放结束语
                        await self._speak_question("感谢您参加本次面试，面试已经结束。")
                else:
                    error_msg = result.get("error", "提交回答失败")
                    await self._send_error(error_msg)
                
        except Exception as e:
            logger.exception(f"[RealTimeVoiceHandler:Logic] 处理用户回答失败: {e}")
            await self._send_error(f"处理回答失败: {str(e)}")
    
    async def _speak_question(self, question: str):
        """播放问题语音"""
        try:
            logger.debug(f"[RealTimeVoiceHandler:TTS] 开始合成语音, text='{question}', session_id={self.session_id}")
            
            # 合成语音
            audio_data = await self.speech_service.synthesize_speech(
                text=question,
                voice="nova",
                speed=1.0
            )
            
            logger.debug(f"[RealTimeVoiceHandler:TTS] 合成完成, audio_bytes={len(audio_data)}, session_id={self.session_id}")
            
            # 发送音频数据
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            await self._send_message({
                "type": "audio_response",
                "data": audio_b64,
                "text": question,
                "format": "mp3"
            })
            
        except Exception as e:
            logger.exception(f"[RealTimeVoiceHandler:TTS] 播放问题语音失败: {e}")
            # 如果语音合成失败，至少发送文本
            await self._send_question(question)
    
    async def _send_question(self, question: str):
        """发送问题"""
        await self._send_message({
            "type": "question",
            "text": question,
            "timestamp": time.time()
        })
    
    async def _send_message(self, message: Dict[str, Any]):
        """发送消息到客户端"""
        logger.debug(f"[RealTimeVoiceHandler:WebSocket] 发送消息: {message}, session_id={self.session_id}")
        if self.is_connected:
            try:
                await self.websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.exception(f"[RealTimeVoiceHandler:WebSocket] 发送消息失败: {e}")
                self.is_connected = False
    
    async def _send_error(self, error_message: str):
        """发送错误消息"""
        logger.debug(f"[RealTimeVoiceHandler:WebSocket] 发送错误: {error_message}, session_id={self.session_id}")
        await self._send_message({
            "type": "error",
            "message": error_message,
            "timestamp": time.time()
        })
    
    # 语音服务回调函数
    async def _on_speech_start(self):
        """语音开始回调"""
        await self._send_message({
            "type": "speech_start",
            "timestamp": time.time()
        })
    
    async def _on_speech_end(self):
        """语音结束回调"""
        await self._send_message({
            "type": "speech_end",
            "timestamp": time.time()
        })
    
    async def _on_transcription(self, result: TranscriptionResult):
        """转录结果回调"""
        await self._send_message({
            "type": "transcription",
            "text": result.text,
            "confidence": result.confidence,
            "duration": result.duration,
            "word_count": result.word_count,
            "is_final": result.is_final,
            "timestamp": result.timestamp
        })
    
    async def _on_state_change(self, new_state: VoiceActivityState):
        """状态变化回调"""
        await self._send_message({
            "type": "state_change",
            "state": new_state.value,
            "timestamp": time.time()
        })

# WebSocket端点处理函数
async def handle_realtime_voice_websocket(websocket: WebSocket, session_id: str):
    """处理实时语音WebSocket连接"""
    handler = RealTimeVoiceHandler(websocket, session_id)
    
    try:
        # 建立连接
        if not await handler.connect():
            return
        
        # 消息循环
        while handler.is_connected:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理消息
                await handler.handle_message(message)
                
            except WebSocketDisconnect:
                logger.info(f"客户端主动断开连接: {session_id}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                await handler._send_error("消息格式错误")
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
                await handler._send_error(f"服务器错误: {str(e)}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket处理失败: {e}")
    
    finally:
        await handler.disconnect()