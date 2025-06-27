"""
WebSocket 实时语音对话路由管理器
增强版本 - 修复资源泄漏和连接管理问题
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Any, Set
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import uuid
from datetime import datetime
import weakref
import threading
import gc

from core.config import config
from core.chat import chat_service
from core.speech import speech_service, voice_interviewer
from models.session import storage

logger = logging.getLogger(__name__)

# WebSocket 路由器
ws_router = APIRouter()

# 全局连接注册表，用于强制清理
_active_connections: Set[weakref.ref] = set()
_connections_lock = threading.RLock()

def _register_connection(connection_ref):
    """注册连接到全局清理列表"""
    with _connections_lock:
        _active_connections.add(connection_ref)

def _unregister_connection(connection_ref):
    """从全局清理列表移除连接"""
    with _connections_lock:
        _active_connections.discard(connection_ref)

async def cleanup_all_connections():
    """清理所有活跃连接"""
    try:
        with _connections_lock:
            connection_refs = list(_active_connections)
        
        cleanup_tasks = []
        for conn_ref in connection_refs:
            conn = conn_ref()
            if conn:
                cleanup_tasks.append(asyncio.create_task(conn.force_cleanup()))
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            logger.info(f"✅ 强制清理了 {len(cleanup_tasks)} 个WebSocket连接")
        
        # 清理失效的引用
        with _connections_lock:
            _active_connections.clear()
            
    except Exception as e:
        logger.error(f"❌ 清理WebSocket连接失败: {e}")

# 活跃连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversation_actors: Dict[str, 'ConversationActor'] = {}
        self._lock = threading.RLock()
        self._stats = {
            "total_connections": 0,
            "active_connections": 0,
            "disconnected_connections": 0,
            "failed_connections": 0
        }
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """建立WebSocket连接"""
        try:
            await websocket.accept()
            
            with self._lock:
                self.active_connections[session_id] = websocket
                self._stats["total_connections"] += 1
                self._stats["active_connections"] += 1
                
                # 创建对话管理器
                if session_id not in self.conversation_actors:
                    self.conversation_actors[session_id] = ConversationActor(session_id, websocket)
            
            logger.info(f"WebSocket连接已建立: {session_id}")
            
        except Exception as e:
            with self._lock:
                self._stats["failed_connections"] += 1
            logger.error(f"WebSocket连接建立失败 {session_id}: {e}")
            raise
    
    def disconnect(self, session_id: str):
        """断开WebSocket连接"""
        try:
            with self._lock:
                if session_id in self.active_connections:
                    del self.active_connections[session_id]
                    self._stats["active_connections"] -= 1
                    self._stats["disconnected_connections"] += 1
                
                if session_id in self.conversation_actors:
                    actor = self.conversation_actors[session_id]
                    # 异步清理，不阻塞断开流程
                    asyncio.create_task(actor.cleanup())
                    del self.conversation_actors[session_id]
            
            logger.info(f"WebSocket连接已断开: {session_id}")
            
        except Exception as e:
            logger.error(f"WebSocket断开处理失败 {session_id}: {e}")
    
    async def send_message(self, session_id: str, message: dict):
        """发送消息"""
        try:
            with self._lock:
                websocket = self.active_connections.get(session_id)
            
            if websocket:
                await websocket.send_text(json.dumps(message))
            else:
                logger.warning(f"尝试向不存在的连接发送消息: {session_id}")
                
        except Exception as e:
            logger.error(f"发送消息失败 {session_id}: {e}")
            self.disconnect(session_id)
    
    async def send_binary(self, session_id: str, data: bytes):
        """发送二进制数据"""
        try:
            with self._lock:
                websocket = self.active_connections.get(session_id)
            
            if websocket:
                await websocket.send_bytes(data)
            else:
                logger.warning(f"尝试向不存在的连接发送二进制数据: {session_id}")
                
        except Exception as e:
            logger.error(f"发送二进制数据失败 {session_id}: {e}")
            self.disconnect(session_id)
    
    def get_actor(self, session_id: str) -> Optional['ConversationActor']:
        """获取对话管理器"""
        with self._lock:
            return self.conversation_actors.get(session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        with self._lock:
            return {
                **self._stats,
                "current_active": len(self.active_connections),
                "current_actors": len(self.conversation_actors)
            }
    
    async def cleanup_all(self):
        """清理所有连接和资源"""
        try:
            with self._lock:
                session_ids = list(self.conversation_actors.keys())
            
            # 并行清理所有actor
            cleanup_tasks = []
            for session_id in session_ids:
                actor = self.conversation_actors.get(session_id)
                if actor:
                    cleanup_tasks.append(asyncio.create_task(actor.cleanup()))
            
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            with self._lock:
                self.active_connections.clear()
                self.conversation_actors.clear()
                
            logger.info("✅ ConnectionManager清理完成")
            
        except Exception as e:
            logger.error(f"❌ ConnectionManager清理失败: {e}")

manager = ConnectionManager()


class ConversationActor:
    """对话管理器 - 处理单个会话的语音对话，增强资源管理"""
    
    def __init__(self, session_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.is_active = True
        self._cleanup_started = False
        self._cleanup_completed = False
        
        # 音频处理队列
        self.audio_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()
        
        # 状态管理
        self.current_transcript = ""
        self.conversation_history = []
        self.is_speaking = False
        self.is_listening = False
        
        # 音频缓冲
        self.audio_buffer = bytearray()
        self.chunk_index = 0
        
        # 错误恢复计数器
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
        # 任务管理 - 使用集合跟踪所有任务
        self.tasks: Set[asyncio.Task] = set()
        
        # 启动处理任务
        self._start_tasks()
        
        # 注册到全局清理列表
        self._connection_ref = weakref.ref(self)
        _register_connection(self._connection_ref)
        
        logger.info(f"对话管理器已创建: {session_id}")
    
    def _start_tasks(self):
        """启动处理任务"""
        try:
            audio_task = asyncio.create_task(self._audio_processor())
            output_task = asyncio.create_task(self._output_processor())
            
            self.tasks.add(audio_task)
            self.tasks.add(output_task)
            
            # 添加任务完成回调
            audio_task.add_done_callback(self._task_done_callback)
            output_task.add_done_callback(self._task_done_callback)
            
        except Exception as e:
            logger.error(f"启动处理任务失败 {self.session_id}: {e}")
    
    def _task_done_callback(self, task):
        """任务完成回调"""
        try:
            self.tasks.discard(task)
            
            if task.exception():
                logger.error(f"任务异常完成 {self.session_id}: {task.exception()}")
            else:
                logger.debug(f"任务正常完成 {self.session_id}")
                
        except Exception as e:
            logger.error(f"任务回调处理失败 {self.session_id}: {e}")
    
    async def process_audio_chunk(self, audio_data: bytes, is_last: bool = False):
        """处理音频数据块"""
        if not self.is_active:
            return
            
        try:
            await asyncio.wait_for(
                self.audio_queue.put({
                    "type": "audio_chunk",
                    "data": audio_data,
                    "is_last": is_last,
                    "timestamp": datetime.now().isoformat()
                }),
                timeout=5.0  # 防止队列阻塞
            )
        except asyncio.TimeoutError:
            logger.warning(f"音频队列阻塞，丢弃音频块 {self.session_id}")
        except Exception as e:
            logger.error(f"处理音频块失败 {self.session_id}: {e}")
    
    async def process_message(self, message: dict):
        """处理WebSocket消息"""
        if not self.is_active:
            return
            
        try:
            event_type = message.get("event")
            
            if event_type == "start_listening":
                await self._start_listening()
            elif event_type == "stop_listening":
                await self._stop_listening()
            elif event_type == "start_speaking":
                await self._start_speaking(message.get("text", ""))
            elif event_type == "ping":
                await self._send_message({"event": "pong", "timestamp": datetime.now().isoformat()})
            else:
                logger.warning(f"未知事件类型: {event_type}")
                
        except Exception as e:
            logger.error(f"处理消息失败 {self.session_id}: {e}")
    
    async def _audio_processor(self):
        """音频处理协程"""
        try:
            while self.is_active:
                try:
                    # 等待音频数据
                    audio_item = await asyncio.wait_for(self.audio_queue.get(), timeout=30.0)
                    
                    if audio_item["type"] == "audio_chunk":
                        await self._process_audio_chunk(audio_item)
                    
                except asyncio.TimeoutError:
                    # 超时检查连接状态
                    if self.is_active:
                        await self._send_message({"event": "ping"})
                except Exception as e:
                    logger.error(f"音频处理错误 {self.session_id}: {e}")
                    self.consecutive_errors += 1
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        logger.error(f"音频处理错误过多，停止处理 {self.session_id}")
                        break
                        
        except Exception as e:
            logger.error(f"音频处理协程异常 {self.session_id}: {e}")
        finally:
            logger.debug(f"音频处理协程结束 {self.session_id}")
    
    async def _output_processor(self):
        """输出处理协程"""
        try:
            while self.is_active:
                try:
                    # 等待输出数据
                    output_item = await asyncio.wait_for(self.output_queue.get(), timeout=30.0)
                    
                    if output_item["type"] == "text_message":
                        await self._send_message(output_item["data"])
                    elif output_item["type"] == "audio_data":
                        await self._send_binary(output_item["data"])
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"输出处理错误 {self.session_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"输出处理协程异常 {self.session_id}: {e}")
        finally:
            logger.debug(f"输出处理协程结束 {self.session_id}")
    
    async def _process_audio_chunk(self, audio_item: dict):
        """处理单个音频块"""
        audio_data = audio_item["data"]
        is_last = audio_item["is_last"]
        
        # 验证音频数据格式
        if not isinstance(audio_data, bytes) or len(audio_data) == 0:
            logger.warning(f"无效音频数据格式: {type(audio_data)}, 大小: {len(audio_data) if hasattr(audio_data, '__len__') else 'unknown'}")
            return
        
        # 添加到缓冲区
        self.audio_buffer.extend(audio_data)
        
        # 仅当正在监听时才处理音频
        if not self.is_listening:
            logger.debug(f"忽略音频块，当前未在监听状态")
            return
            
        # 检查是否有足够音频进行处理
        audio_duration = len(self.audio_buffer) / (16000 * 2)  # 假设16kHz, 16-bit
        logger.debug(f"音频缓冲: {len(self.audio_buffer)} 字节, 时长: {audio_duration:.2f}秒")
        
        # 降低处理延迟，每400ms处理一次
        if audio_duration >= 0.4 or is_last:
            try:
                # 进行语音识别
                result = await speech_service.speech_to_text(
                    bytes(self.audio_buffer),
                    prompt=self.current_transcript
                )
                
                # 重置错误计数器
                self.consecutive_errors = 0
                
                # 发送部分转录结果
                await self._send_message({
                    "event": "partial_transcript",
                    "text": result["text"],
                    "confidence": result["confidence"],
                    "is_final": is_last
                })
                
                if is_last:
                    # 完整转录完成，生成AI回复
                    await self._generate_ai_response(result["text"])
                    
                    # 清空缓冲区
                    self.audio_buffer.clear()
                    self.current_transcript = ""
                else:
                    # 保留部分重叠
                    overlap_size = len(self.audio_buffer) // 5  # 20%重叠
                    self.audio_buffer = self.audio_buffer[-overlap_size:]
                    self.current_transcript = result["text"]
                
            except Exception as e:
                self.consecutive_errors += 1
                logger.error(f"语音识别失败 {self.session_id} (第{self.consecutive_errors}次): {e}")
                
                # 熔断机制：连续5次失败后暂停处理
                if self.consecutive_errors >= self.max_consecutive_errors:
                    await self._send_message({
                        "event": "error",
                        "message": "语音识别连续失败，请检查网络连接或音频质量"
                    })
                    # 清空缓冲区并重置
                    self.audio_buffer.clear()
                    self.consecutive_errors = 0
                else:
                    await self._send_message({
                        "event": "error",
                        "message": f"语音识别失败: {str(e)}"
                    })
    
    async def _generate_ai_response(self, user_text: str):
        """生成AI回复"""
        try:
            # 添加到对话历史
            self.conversation_history.append({
                "role": "user",
                "content": user_text
            })
            
            # 发送最终转录
            await self._send_message({
                "event": "final_transcript",
                "text": user_text
            })
            
            # 获取会话信息
            session = await storage.get_session(self.session_id)
            if not session:
                raise Exception("会话不存在")
            
            # 构建消息历史
            messages = [
                {"role": "system", "content": "你是一个专业的AI面试官。请根据用户的回答提出下一个面试问题，或给出建设性的反馈。保持问题简洁明了。"}
            ]
            messages.extend(self.conversation_history[-10:])  # 保留最近10轮对话
            
            # 生成AI回复
            ai_response = await chat_service.ask_llm(
                messages=messages,
                task_type="interview",
                max_tokens=200
            )
            
            # 发送AI文字回复
            await self._send_message({
                "event": "assistant_text",
                "text": ai_response
            })
            
            # 添加到对话历史
            self.conversation_history.append({
                "role": "assistant", 
                "content": ai_response
            })
            
            # 生成并发送语音
            await self._generate_speech(ai_response)
            
        except Exception as e:
            logger.error(f"AI回复生成失败 {self.session_id}: {e}")
            await self._send_message({
                "event": "error",
                "message": f"AI回复生成失败: {str(e)}"
            })
    
    async def _generate_speech(self, text: str):
        """生成并发送语音"""
        try:
            # 获取语音配置
            voice_config = config.get_voice_config()
            
            # 流式生成语音
            await self._send_message({
                "event": "speech_start",
                "text": text
            })
            
            async for audio_chunk in voice_interviewer.stream_speak_question(text):
                if not self.is_active:
                    break
                await self._send_binary(audio_chunk)
            
            await self._send_message({
                "event": "speech_end"
            })
            
        except Exception as e:
            logger.error(f"语音生成失败 {self.session_id}: {e}")
            await self._send_message({
                "event": "error",
                "message": f"语音生成失败: {str(e)}"
            })
    
    async def _start_listening(self):
        """开始监听"""
        if not self.is_active:
            return
            
        self.is_listening = True
        self.audio_buffer.clear()
        await self._send_message({
            "event": "listening_started"
        })
    
    async def _stop_listening(self):
        """停止监听"""
        if not self.is_active:
            return
            
        self.is_listening = False
        if self.audio_buffer:
            # 处理剩余音频
            await self._process_audio_chunk({
                "data": bytes(),
                "is_last": True,
                "timestamp": datetime.now().isoformat()
            })
        
        await self._send_message({
            "event": "listening_stopped"
        })
    
    async def _start_speaking(self, text: str):
        """开始说话"""
        if not self.is_active:
            return
            
        self.is_speaking = True
        await self._generate_speech(text)
        self.is_speaking = False
    
    async def _send_message(self, message: dict):
        """发送文本消息"""
        if not self.is_active:
            return
            
        try:
            await asyncio.wait_for(
                self.output_queue.put({
                    "type": "text_message",
                    "data": message
                }),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"输出队列阻塞，丢弃消息 {self.session_id}")
        except Exception as e:
            logger.error(f"发送消息失败 {self.session_id}: {e}")
    
    async def _send_binary(self, data: bytes):
        """发送二进制数据"""
        if not self.is_active:
            return
            
        try:
            await asyncio.wait_for(
                self.output_queue.put({
                    "type": "audio_data",
                    "data": data
                }),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"输出队列阻塞，丢弃音频数据 {self.session_id}")
        except Exception as e:
            logger.error(f"发送二进制数据失败 {self.session_id}: {e}")
    
    def stop(self):
        """停止对话管理器 - 同步版本"""
        if self._cleanup_started:
            return
            
        self._cleanup_started = True
        self.is_active = False
        
        # 创建清理任务
        asyncio.create_task(self.cleanup())
    
    async def cleanup(self):
        """异步清理资源"""
        if self._cleanup_completed:
            return
            
        try:
            self.is_active = False
            
            # 取消所有任务
            if self.tasks:
                logger.debug(f"取消 {len(self.tasks)} 个任务 {self.session_id}")
                
                for task in list(self.tasks):
                    if not task.done():
                        task.cancel()
                
                # 等待任务完成或取消
                if self.tasks:
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(*self.tasks, return_exceptions=True),
                            timeout=5.0
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"任务取消超时 {self.session_id}")
                    except Exception as e:
                        logger.warning(f"任务取消异常 {self.session_id}: {e}")
                
                self.tasks.clear()
            
            # 清空队列
            await self._clear_queues()
            
            # 清理音频缓冲区
            self.audio_buffer.clear()
            self.conversation_history.clear()
            
            # 从全局注册表移除
            _unregister_connection(self._connection_ref)
            
            self._cleanup_completed = True
            logger.info(f"对话管理器已完全清理: {self.session_id}")
            
        except Exception as e:
            logger.error(f"清理资源失败 {self.session_id}: {e}")
        finally:
            # 强制垃圾回收
            gc.collect()
    
    async def _clear_queues(self):
        """清空队列"""
        try:
            # 清空音频队列
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            # 清空输出队列
            while not self.output_queue.empty():
                try:
                    self.output_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                    
        except Exception as e:
            logger.warning(f"清空队列失败 {self.session_id}: {e}")
    
    async def force_cleanup(self):
        """强制清理 - 用于全局清理"""
        await self.cleanup()


@ws_router.websocket("/ws/voice/{session_id}")
async def voice_conversation_endpoint(websocket: WebSocket, session_id: str):
    """
    实时语音对话WebSocket端点
    """
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            try:
                data = await websocket.receive()
            except WebSocketDisconnect:
                logger.info(f"WebSocketDisconnect: {session_id}")
                break
            except RuntimeError as e:
                # starlette 会在断开后 raise RuntimeError("Cannot call receive once a disconnect message has been received.")
                logger.info(f"WebSocket runtime closed {session_id}: {e}")
                break
            except Exception as e:
                logger.error(f"接收数据异常 {session_id}: {e}")
                break

            if data.get("type") != "websocket.receive":
                continue

            if "text" in data and data["text"]:
                try:
                    message = json.loads(data["text"])
                    actor = manager.get_actor(session_id)
                    if actor:
                        await actor.process_message(message)
                except json.JSONDecodeError as e:
                    await manager.send_message(session_id, {
                        "event": "error",
                        "message": f"JSON解析错误: {str(e)}"
                    })
            
            elif "bytes" in data and data["bytes"]:
                audio_data = data["bytes"]
                actor = manager.get_actor(session_id)
                if actor:
                    await actor.process_audio_chunk(audio_data)
    finally:
        manager.disconnect(session_id)


@ws_router.websocket("/ws/realtime-voice/{session_id}")
async def realtime_voice_compat_endpoint(websocket: WebSocket, session_id: str):
    """
    实时语音对话WebSocket端点 - 兼容性别名
    与voice_conversation_endpoint功能相同
    """
    await voice_conversation_endpoint(websocket, session_id)


@ws_router.get("/ws/status")
async def websocket_status():
    """获取WebSocket连接状态"""
    try:
        stats = manager.get_stats()
        
        # 添加全局连接统计
        with _connections_lock:
            global_connections = len(_active_connections)
        
        return {
            **stats,
            "global_registered_connections": global_connections,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取WebSocket状态失败: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@ws_router.post("/ws/cleanup")
async def force_cleanup_connections():
    """强制清理所有WebSocket连接"""
    try:
        await cleanup_all_connections()
        await manager.cleanup_all()
        
        return {
            "status": "success",
            "message": "所有WebSocket连接已强制清理",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"强制清理失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }