#!/usr/bin/env python3
"""
VITA 简化版后端服务器 - 专门用于测试前端
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import uuid
import uvicorn
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="VITA Simplified Server", version="1.0.0")

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple models for the session endpoints
class StartSessionRequest(BaseModel):
    job_description: str
    interview_type: str = "text"

class StartSessionResponse(BaseModel):
    session_id: str
    first_question: str
    interview_type: str
    created_at: datetime

class SubmitAnswerRequest(BaseModel):
    answer: str

class QuestionResponse(BaseModel):
    question: str
    question_number: int
    total_questions: Optional[int] = None

# Simple in-memory storage for sessions
sessions = {}

# 简单的健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "VITA simplified server is running"}

# Session start endpoint
@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """开始面试会话"""
    session_id = str(uuid.uuid4())
    
    # Generate a simple first question based on job description
    first_question = f"请简单介绍一下您自己，以及您对{request.job_description}这个职位的理解。"
    
    # Store session
    sessions[session_id] = {
        "session_id": session_id,
        "job_description": request.job_description,
        "interview_type": request.interview_type,
        "created_at": datetime.now(),
        "history": [{"role": "assistant", "content": first_question}]
    }
    
    return StartSessionResponse(
        session_id=session_id,
        first_question=first_question,
        interview_type=request.interview_type,
        created_at=datetime.now()
    )

# Submit answer endpoint
@app.post("/session/{session_id}/answer", response_model=QuestionResponse)
async def submit_answer(session_id: str, request: SubmitAnswerRequest):
    """提交答案并获取下一个问题"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Add user's answer to history
    session["history"].append({"role": "user", "content": request.answer})
    
    # Generate next question (simplified logic)
    question_number = len([msg for msg in session["history"] if msg["role"] == "assistant"]) + 1
    
    if question_number <= 3:  # Limit to 3 questions for simplicity
        if question_number == 2:
            next_question = "请描述一个您在前端开发中遇到的技术挑战，以及您是如何解决的？"
        elif question_number == 3:
            next_question = "您如何看待前端技术的发展趋势？您认为哪些技术值得重点关注？"
        else:
            next_question = "感谢您的回答，面试即将结束。"
        
        # Add assistant's question to history
        session["history"].append({"role": "assistant", "content": next_question})
        
        return QuestionResponse(
            question=next_question,
            question_number=question_number,
            total_questions=3
        )
    else:
        # Interview completed
        return QuestionResponse(
            question="面试已完成，感谢您的参与！",
            question_number=question_number,
            total_questions=3
        )

# 挂载前端静态文件
dist_dir = Path(__file__).parent.parent / "frontend" / "dist"
if dist_dir.exists():
    print(f"✅ 找到前端构建目录: {dist_dir}")
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")
    print(f"✅ 已挂载前端静态文件到根路径")
else:
    print(f"❌ 未找到前端构建目录: {dist_dir}")

if __name__ == "__main__":
    print("🚀 启动VITA简化版服务器...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8002,  # 使用8002端口避免冲突
        reload=False,
        access_log=True,
        log_level="info"
    )