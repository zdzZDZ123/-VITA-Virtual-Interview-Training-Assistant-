#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import asyncio
import logging
import tempfile
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# 添加项目根路径到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# FastAPI相关导入
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request
from fastapi.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 导入核心模块
from core.config import config
from core.logger import logger
from models.api import (
    StartSessionRequest, StartSessionResponse, 
    SubmitAnswerRequest, QuestionResponse, FeedbackReport
)

# 初始化FastAPI应用
app = FastAPI(
    title="VITA面试训练助手",
    description="AI驱动的智能面试训练平台",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 初始化服务
try:
    from core.speech import get_speech_service
    from core.chat import ChatService
    # from models.session import SessionStorage  # 不需要了，ChatService内置会话管理
    
    speech_service = None
    chat_service = ChatService()
    # storage = SessionStorage()  # 不需要了，ChatService内置会话管理
    
    logger.info("✅ 基础服务初始化成功")
except Exception as e:
    logger.error(f"❌ 服务初始化失败: {e}")

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    global speech_service
    
    try:
        logger.info("🚀 VITA后端服务启动中...")
        
        # 初始化语音服务
        try:
            speech_service = await get_speech_service()
            logger.info("🎵 语音服务初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 语音服务初始化失败: {e}")
            speech_service = None
        
        # 打印配置摘要
        config.print_config_summary()
        
        logger.info("🎉 VITA服务启动完成")
        
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        raise e

@app.on_event("shutdown") 
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("🛑 VITA服务正在关闭...")
    logger.info("👋 VITA服务已安全关闭")

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "VITA Interview Service"}

# 语音相关API端点
@app.post("/speech/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form("zh")
):
    """语音转文字"""
    if not speech_service:
        raise HTTPException(status_code=503, detail="语音服务不可用")
    
    try:
        # 验证文件类型
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="文件类型必须是音频格式")
        
        # 读取音频数据
        audio_data = await audio.read()
        
        # 进行语音识别
        result = await speech_service.speech_to_text(
            audio_data=audio_data,
            filename=audio.filename or "audio.webm",
            language=language
        )
        
        return {
            "success": True,
            "text": result["text"],
            "language": result.get("language"),
            "duration": result.get("duration"),
            "confidence": result.get("confidence", 0.95)
        }
        
    except Exception as e:
        logger.error(f"语音识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")

@app.post("/speech/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    voice: str = Form("nova"),
    speed: float = Form(1.0)
):
    """文字转语音"""
    if not speech_service:
        raise HTTPException(status_code=503, detail="语音服务不可用")
    
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        if len(text) > 4000:
            raise HTTPException(status_code=400, detail="文本长度不能超过4000字符")
        
        # 生成语音
        audio_data = await speech_service.text_to_speech(
            text=text,
            voice=voice,
            speed=speed
        )
        
        # 返回音频数据
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"TTS合成失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")

@app.options("/speech/synthesize")
async def synthesize_options():
    """处理TTS OPTIONS预检请求"""
    return Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400"
    })

# 面试会话相关API
@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """开始新的面试会话"""
    try:
        logger.info(f"Received request to start session: job_description='{request.job_description}' interview_type='{request.interview_type}'")
        
        # 使用新的聊天服务启动面试会话
        result = await chat_service.start_interview_session(
            job_description=request.job_description,
            interview_type=request.interview_type
        )
        
        return StartSessionResponse(
            session_id=result["session_id"],
            first_question=result["first_question"],
            interview_type=result["interview_type"],
            created_at=result["created_at"]
        )
        
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")

@app.post("/session/{session_id}/answer", response_model=QuestionResponse)
async def submit_answer(session_id: str, request: SubmitAnswerRequest):
    """提交答案并获取下一个问题"""
    # 检查会话是否存在
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        # 使用新的聊天服务处理答案并生成下一个问题
        result = await chat_service.__REMOVED_API_KEY__(
            session_id=session_id,
            answer=request.answer
        )
        
        return QuestionResponse(
            question=result["question"],
            question_number=result["question_number"]
        )
        
    except Exception as e:
        logger.error(f"处理回答失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理回答失败: {str(e)}")

@app.get("/session/{session_id}/feedback")
async def get_feedback(session_id: str):
    """生成面试反馈报告"""
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        # 使用新的聊天服务生成反馈报告
        report = chat_service.end_session(session_id)
        
        return {
            "feedback": "面试已完成，感谢您的参与！",
            "session_id": report["session_id"],
            "total_questions": report["questions_count"],
            "total_answers": report["answers_count"],
            "interview_type": report["interview_type"],
            "duration_seconds": report["duration"],
            "completed": report["completed"]
        }
        
    except Exception as e:
        logger.error(f"生成反馈报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成反馈失败: {str(e)}")

# 静态文件服务（用于前端）
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_fixed:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 