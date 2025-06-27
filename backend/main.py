# 修复模块导入路径 - 确保从任何目录都能正确启动
import sys
import pathlib

# 修复模块导入路径 - 确保从任何目录都能正确启动
ROOT_DIR = pathlib.Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, WebSocket, Response
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio
import logging
import base64
import json
from typing import List
from datetime import datetime
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import uuid
import os

# 现在安全导入本地模块
from core.config import config
from core.chat import chat_service
from core.speech import speech_service, voice_interviewer
from core.qwen_llama_client import create_http_client, get_client_manager, initialize_clients
from core.dynamic_switch import get_dynamic_switch_manager
from core.performance_monitor import get_performance_monitor
from ws_router import ws_router
from realtime_voice_router import handle_realtime_voice_websocket
from models.api import (
    StartSessionRequest, StartSessionResponse, 
    SubmitAnswerRequest, QuestionResponse,
    FeedbackReport, ErrorResponse
)
from models.session import SessionState, storage

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VITA Interview Service", 
    version="1.0.0",
    description="虚拟面试与培训助理 - 基于豆包优先三模型架构的智能多模态面试评估系统，支持表情语气分析"
)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173", 
        "http://127.0.0.1:5174",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "file://*",  # 允许本地文件访问
        "*"  # 临时允许所有源，用于调试
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 早期配置静态文件 - 在路由定义之前
from fastapi.responses import FileResponse

# 检查前端构建目录并挂载静态文件
current_dir = Path(os.getcwd())
logger.info(f"📍 当前工作目录: {current_dir}")

# 尝试多个可能的前端路径
frontend_paths = [
    Path("../frontend/dist"),
    Path("frontend/dist"),
    current_dir.parent / "frontend" / "dist"
]

frontend_dist = None
for path in frontend_paths:
    abs_path = path.resolve()
    logger.info(f"🔍 检查前端路径: {abs_path}")
    if abs_path.exists():
        frontend_dist = abs_path
        logger.info(f"✅ 找到前端构建目录: {frontend_dist}")
        break

# 全局变量，用于存储前端目录路径
frontend_dist_global = frontend_dist

def setup_static_files():
    """设置静态文件挂载"""
    global frontend_dist_global
    
    # 重新检查前端目录
    for path in frontend_paths:
        abs_path = path.resolve()
        if abs_path.exists():
            frontend_dist_global = abs_path
            logger.info(f"✅ 重新找到前端构建目录: {frontend_dist_global}")
            break
    
    if frontend_dist_global and frontend_dist_global.exists():
        # 挂载前端静态文件目录
        logger.info(f"🗂️ 开始挂载静态文件从: {frontend_dist_global}")
        
        # 检查并挂载各个静态资源目录
        static_dirs = [
            ("js", "js"),
            ("css", "css"), 
            ("models", "models"),
            ("assets", "assets")
        ]
        
        for mount_path, dir_name in static_dirs:
            static_dir = frontend_dist_global / dir_name
            if static_dir.exists():
                # 检查是否已经挂载过，避免重复挂载
                mount_name = f"static_{mount_path}"
                try:
                    app.mount(f"/{mount_path}", StaticFiles(directory=str(static_dir)), name=mount_name)
                    logger.info(f"✅ 挂载 /{mount_path} -> {static_dir}")
                except Exception as e:
                    logger.warning(f"⚠️ 挂载 /{mount_path} 时出错: {e}")
            else:
                logger.info(f"⚠️ 跳过不存在的目录: {static_dir}")
        
        logger.info("✅ 前端静态资源挂载完成")
        return True
    else:
        logger.warning("⚠️ 未找到前端构建目录")
        return False

# 挂载后端测试静态文件（用于开发和测试）
backend_static = Path("static")
if backend_static.exists():
    app.mount("/static", StaticFiles(directory=str(backend_static)), name="static")
    logger.info(f"✅ 挂载后端静态文件: {backend_static.resolve()} -> /static")
else:
    logger.info("ℹ️ 后端静态文件目录不存在，跳过挂载")

# 导入路由
from api.health import router as health_router
from api.model_manager import router as model_router
from api.modules import router as modules_router
from api.multimodal_interview_api import router as multimodal_router

# 包含WebSocket路由
app.include_router(ws_router, prefix="/api/v1", tags=["websocket"])

# 注册路由
app.include_router(health_router)
app.include_router(model_router)
app.include_router(modules_router)
app.include_router(multimodal_router)

# 前端路由处理 - 在所有API路由之后
# 添加调试路由
@app.get("/debug/static")
async def debug_static():
    global frontend_dist_global
    return {
        "frontend_dist_exists": frontend_dist_global.exists() if frontend_dist_global else False,
        "frontend_dist_path": str(frontend_dist_global) if frontend_dist_global else None,
        "css_dir_exists": (frontend_dist_global / "css").exists() if frontend_dist_global else False,
        "js_dir_exists": (frontend_dist_global / "js").exists() if frontend_dist_global else False,
        "index_html_exists": (frontend_dist_global / "index.html").exists() if frontend_dist_global else False,
        "working_directory": str(current_dir),
        "css_files": list(str(f.name) for f in (frontend_dist_global / "css").glob("*")) if frontend_dist_global and (frontend_dist_global / "css").exists() else [],
        "js_files": list(str(f.name) for f in (frontend_dist_global / "js").glob("*")) if frontend_dist_global and (frontend_dist_global / "js").exists() else []
    }

# 添加手动重新挂载端点
@app.post("/debug/remount-static")
async def remount_static():
    """手动重新挂载静态文件"""
    try:
        success = setup_static_files()
        return {
            "success": success,
            "message": "静态文件挂载已更新" if success else "未找到前端构建目录",
            "frontend_dist": str(frontend_dist_global) if frontend_dist_global else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "重新挂载失败"
        }

# 添加根路径处理，返回index.html
@app.get("/")
async def read_index():
    global frontend_dist_global
    if frontend_dist_global:
        index_file = frontend_dist_global / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
    
    return {"message": "VITA Backend API", "status": "running", "frontend": "not_built"}

# 处理前端路由，对于HTML请求返回index.html
@app.middleware("http")
async def spa_handler(request: Request, call_next):
    response = await call_next(request)
    
    # 如果是404且请求的是HTML页面，返回index.html让前端路由处理
    if (response.status_code == 404 and 
        frontend_dist_global and
        request.url.path != "/" and 
        not request.url.path.startswith("/api") and
        not request.url.path.startswith("/static") and
        not request.url.path.startswith("/js") and
        not request.url.path.startswith("/css") and
        not request.url.path.startswith("/models") and
        not request.url.path.startswith("/debug") and
        "text/html" in request.headers.get("accept", "")):
        index_file = frontend_dist_global / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
    
    return response

logger.info("✅ 前端SPA路由处理已配置")

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("🚀 VITA Qwen优先架构服务启动中...")
    
    try:
        # 设置静态文件挂载
        setup_static_files()
        
        # 验证配置
        config.validate_config()
        logger.info("✅ 配置验证通过")
        
        # 初始化Qwen优先架构客户端
        await __REMOVED_API_KEY__()
        
        # 启动健康监控
        try:
            from core.health_monitor import start_health_monitoring
            await start_health_monitoring(check_interval=60.0)  # 每分钟检查一次
            logger.info("🔍 健康监控已启动")
        except ImportError:
            logger.info("🔍 健康监控模块未找到，跳过")
        
        # 启动缓存管理器
        try:
            from core.cache_manager import start_cache_manager
            await start_cache_manager()
            logger.info("🗄️ 缓存管理器已启动")
        except ImportError:
            logger.info("🗄️ 缓存管理器模块未找到，跳过")
        
        # 打印配置摘要
        config.print_config_summary()
        
        logger.info("🎉 VITA Qwen优先架构服务启动完成")
        
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        raise e


async def __REMOVED_API_KEY__():
    """初始化Qwen优先架构客户端"""
    try:
        # 使用统一的初始化函数
        initialize_clients()
        
        # 获取客户端状态
        client_manager = get_client_manager()
        status = client_manager.get_client_status()
        
        if not status["clients"]:
            raise ValueError("没有可用的API客户端")
        
        logger.info(f"🤖 双模型架构初始化完成，可用客户端: {list(status['clients'].keys())}")
        
    except Exception as e:
        logger.error(f"❌ 双模型架构初始化失败: {e}")
        raise

@app.on_event("shutdown") 
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("🛑 VITA服务正在关闭...")
    
    # 使用新的客户端管理器清理所有客户端连接
    try:
        # 停止健康监控
        try:
            from core.health_monitor import stop_health_monitoring
            await stop_health_monitoring()
            logger.info("🔍 健康监控已停止")
        except (ImportError, AttributeError):
            logger.info("🔍 健康监控模块未找到或已停止")
        
        # 停止缓存管理器
        try:
            from core.cache_manager import stop_cache_manager
            await stop_cache_manager()
            logger.info("🗄️ 缓存管理器已停止")
        except (ImportError, AttributeError):
            logger.info("🗄️ 缓存管理器模块未找到或已停止")
        
        try:
            from core.client_manager import cleanup_all_clients, get_active_clients_count
        except ImportError:
            logger.info("🔧 客户端管理器模块未找到，跳过清理")
            return  # 如果没有客户端管理器，直接返回
        
        active_count = get_active_clients_count()
        if active_count > 0:
            logger.info(f"🧹 开始清理 {active_count} 个活跃客户端...")
            await cleanup_all_clients()
            logger.info("✅ 所有客户端已清理完成")
        else:
            logger.info("✅ 没有需要清理的客户端")
            
        # 清理旧的客户端管理器（兼容性）
        client_manager = get_client_manager()
        if hasattr(client_manager, '_clients'):
            for name, client in client_manager._clients.items():
                if hasattr(client, 'aclose'):
                    await client.aclose()
                    logger.info(f"✅ {name} 客户端已关闭")
    except Exception as e:
        logger.warning(f"⚠️ 客户端清理时出现警告: {e}")
        
    # 优雅地处理异步任务
    try:
        # 获取当前所有任务，排除当前任务
        current_task = asyncio.current_task()
        all_tasks = [task for task in asyncio.all_tasks() if task != current_task and not task.done()]
        
        if all_tasks:
            logger.info(f"⏳ 正在取消 {len(all_tasks)} 个未完成的异步任务...")
            
            # 取消所有任务
            for task in all_tasks:
                if not task.cancelled():
                    task.cancel()
            
            # 等待任务完成或被取消
            try:
                await asyncio.wait_for(
                    asyncio.gather(*all_tasks, return_exceptions=True), 
                    timeout=3.0
                )
                logger.info("✅ 所有异步任务已处理完成")
            except asyncio.TimeoutError:
                logger.warning("⚠️ 部分异步任务未能在超时时间内完成")
            except asyncio.CancelledError:
                logger.info("✅ 异步任务已被正确取消")
        else:
            logger.info("✅ 没有需要处理的异步任务")
            
    except Exception as e:
        logger.warning(f"⚠️ 异步任务清理时出现警告: {e}")
            
    logger.info("👋 VITA服务已安全关闭")


# 双模型架构监控API
@app.get("/api/v1/system/status")
async def get_system_status():
    """获取系统状态"""
    try:
        # 获取配置状态
        config_status = config.get_service_status()
        
        # 获取客户端状态
        client_manager = get_client_manager()
        client_status = client_manager.get_client_status()
        
        return {
            "status": "healthy" if config_status["status"] == "healthy" else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "config": config_status,
            "clients": client_status,
            "version": "1.0.0",
            "architecture": "dual-model"
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@app.get("/api/v1/system/health")
async def health_check():
    """健康检查端点"""
    try:
        client_manager = get_client_manager()
        healthy_client = await client_manager.get_healthy_client()
        
        if healthy_client:
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        else:
            return {"status": "unhealthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}


@app.get("/api/v1/system/performance")
async def get_performance_metrics():
    """获取性能指标"""
    try:
        monitor = get_performance_monitor()
        return monitor.get_performance_summary()
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        return {"error": str(e)}


@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus指标端点"""
    try:
        # 获取性能监控器
        monitor = get_performance_monitor()
        
        # 导出Prometheus格式的指标
        metrics_data = monitor.export_prometheus_metrics()
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST,
            headers={"Content-Type": CONTENT_TYPE_LATEST}
        )
    except Exception as e:
        logger.error(f"导出Prometheus指标失败: {e}")
        return Response(
            content=f"# Error exporting metrics: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )


@app.post("/api/v1/system/switch-primary")
async def switch_primary_provider(request: dict):
    """切换主提供商"""
    try:
        new_primary = request.get("provider")
        reason = request.get("reason", "manual_api_call")
        
        if not new_primary:
            raise HTTPException(status_code=400, detail="缺少provider参数")
        
        switch_manager = get_dynamic_switch_manager()
        success = switch_manager.switch_primary(new_primary, reason)
        
        if success:
            return {
                "success": True,
                "message": f"主提供商已切换到{new_primary}",
                "status": switch_manager.get_switch_status()
            }
        else:
            raise HTTPException(status_code=400, detail="切换失败")
            
    except Exception as e:
        logger.error(f"切换主提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/system/switch-status")
async def get_switch_status():
    """获取切换状态"""
    try:
        switch_manager = get_dynamic_switch_manager()
        return switch_manager.get_switch_status()
    except Exception as e:
        logger.error(f"获取切换状态失败: {e}")
        return {"error": str(e)}


@app.post("/api/v1/system/auto-switch")
async def toggle_auto_switch(request: dict):
    """启用/禁用自动切换"""
    try:
        enabled = request.get("enabled", True)
        switch_manager = get_dynamic_switch_manager()
        switch_manager.enable_auto_switch(enabled)
        
        return {
            "success": True,
            "message": f"自动切换已{'启用' if enabled else '禁用'}",
            "status": switch_manager.get_switch_status()
        }
    except Exception as e:
        logger.error(f"设置自动切换失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# API Endpoints
# -----------------------------
@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """开始面试会话"""
    logger.info(f"Received request to start session: job_description='{request.job_description}' interview_type='{request.interview_type}'")
    
    session_id = str(uuid.uuid4())

    # 创建会话
    session = await storage.create_session(
        job_description=request.job_description,
        interview_type=request.interview_type,
        session_id=session_id
    )

    # 使用新接口生成第一个问题
    first_question = await chat_service.generate_interview_question(
        job_description=request.job_description,
        interview_type=request.interview_type,
        previous_qa=None,
        question_number=1
    )

    # 添加问题到历史
    session.history.append({
        "role": "assistant",
        "content": first_question
    })

    await storage.update_session(session)

    return StartSessionResponse(
        session_id=session_id,
        first_question=first_question,
        interview_type=session.interview_type,
        created_at=session.created_at
    )


@app.post("/session/{session_id}/answer", response_model=QuestionResponse)
async def submit_answer(session_id: str, request: SubmitAnswerRequest):
    """提交答案并获取下一个问题"""
    session = await storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        # 添加用户回答到历史
        session.history.append({
            "role": "user", 
            "content": request.answer
        })
        
        # 构建previous_qa用于新接口
        assistant_messages = [h for h in session.history if h['role'] == 'assistant']
        user_messages = [h for h in session.history if h['role'] == 'user']
        previous_qa = list(zip(assistant_messages, user_messages))
        previous_qa = [(q['content'], a['content']) for q, a in previous_qa]
        
        # 计算下一个问题序号
        next_question_number = len(assistant_messages) + 1
        
        # 使用新接口生成下一个问题
        next_question = await chat_service.generate_interview_question(
            job_description=session.job_description,
            interview_type=session.interview_type,
            previous_qa=previous_qa,
            question_number=next_question_number
        )
        
        # 保存问题到历史
        session.history.append({
            "role": "assistant", 
            "content": next_question
        })
        
        await storage.update_session(session)
        
        # 返回问题序号
        question_number = next_question_number
        
        return QuestionResponse(
            question=next_question,
            question_number=question_number
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理回答失败: {str(e)}")


@app.get("/session/{session_id}/feedback")
async def get_feedback(session_id: str):
    """生成面试反馈报告"""
    session = await storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        # 标记会话完成
        session.is_completed = True
        await storage.update_session(session)
        
        # 生成完整的反馈报告
        try:
            from core.report import report_generator
            report = report_generator.generate_full_report(session)
        except ImportError:
            # 如果报告生成器不存在，返回简单反馈
            report = {"feedback": "面试完成", "session_id": session_id}
        
        return report
        
    except Exception as e:
        logger.error(f"生成反馈报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成反馈失败: {str(e)}")


@app.post("/session/{session_id}/visual-feedback", response_model=FeedbackReport)
async def get_feedback_with_visual(session_id: str):
    """生成包含视觉分析的面试反馈报告"""
    session = await storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        # 标记会话完成
        session.is_completed = True
        await storage.update_session(session)
        
        # TODO: 调用视觉服务获取分析结果 
        # 这里可以从session中获取存储的视觉分析结果
        # 或者调用vision service API获取实时分析
        visual_analysis = None  # 暂时为空，后续集成视觉服务
        
        # 生成完整的反馈报告
        try:
            from core.report import report_generator
            report = report_generator.generate_full_report(session, visual_analysis)
        except ImportError:
            # 如果报告生成器不存在，返回简单反馈
            report = {"feedback": "面试完成", "session_id": session_id, "visual_analysis": visual_analysis}
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成反馈失败: {str(e)}")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "VITA Interview Service"}


# -----------------------------
# 语音相关API端点
# -----------------------------

from fastapi import File, UploadFile, Form
from fastapi.responses import Response
import json

@app.post("/speech/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form("zh")
):
    """
    语音转文字
    """
    try:
        # 验证文件类型
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="文件类型必须是音频格式")
        
        # 读取音频数据
        audio_data = await audio.read()
        
        # 验证音频数据
        await speech_service.validate_audio(audio_data)
        
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
            "word_count": len(result["text"].split()),
            "confidence": 0.95  # 模拟置信度
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")


@app.post("/speech/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    voice: str = Form("nova"),
    speed: float = Form(1.0)
):
    """
    文字转语音 - 传统端点（向后兼容）
    支持Edge-TTS + Pyttsx3 fallback机制
    """
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
        
        # 返回音频数据 - 修复音频格式和响应头
        return Response(
            content=audio_data,
            media_type="audio/mpeg",  # 标准MIME类型
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache", 
                "Expires": "0",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Content-Length": str(len(audio_data)),
                "Accept-Ranges": "bytes",
                "Content-Transfer-Encoding": "binary"
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


@app.get("/speech/formats")
async def get_audio_formats():
    """
    获取支持的音频格式信息
    """
    try:
        from core.audio_processor import audio_processor
        
        return {
            "success": True,
            "ffmpeg_available": audio_processor.ffmpeg_available,
            "supported_formats": {
                "mp3": {
                    "mime_type": "audio/mpeg",
                    "description": "标准MP3格式，广泛支持",
                    "browser_support": ["Chrome", "Firefox", "Safari", "Edge"]
                },
                "wav": {
                    "mime_type": "audio/wav",
                    "description": "WAV格式，最佳兼容性",
                    "browser_support": ["Chrome", "Firefox", "Safari", "Edge"]
                },
                "ogg": {
                    "mime_type": "audio/ogg",
                    "description": "OGG格式，开源替代方案",
                    "browser_support": ["Chrome", "Firefox"]
                }
            },
            "browser_preferences": {
                "Chrome": "wav",
                "Firefox": "ogg", 
                "Safari": "mp3",
                "Edge": "mp3",
                "default": "wav"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取格式信息失败: {str(e)}")


@app.post("/speech/synthesize-multi")
async def synthesize_speech_multi(
    text: str = Form(...),
    voice: str = Form("nova"),
    speed: float = Form(1.0)
):
    """
    多格式语音合成 - 一次生成所有支持的格式
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        if len(text) > 4000:
            raise HTTPException(status_code=400, detail="文本长度不能超过4000字符")
        
        # 导入音频处理器
        try:
            from core.audio_processor import audio_processor
        except ImportError:
            logger.warning("音频处理器模块未找到，使用基础模式")
            # 创建简单的备用处理器
            class SimpleAudioProcessor:
                async def create_multi_format_response(self, audio_data):
                    return {"mp3": {"data": audio_data, "mime_type": "audio/mpeg", "size": len(audio_data)}}
            audio_processor = SimpleAudioProcessor()
        
        # 生成原始音频
        audio_data = await speech_service.text_to_speech(
            text=text,
            voice=voice,
            speed=speed
        )
        
        # 生成多种格式
        formats = await audio_processor.create_multi_format_response(audio_data)
        
        # 转换为base64以便传输
        import base64
        result = {
            "success": True,
            "original_size": len(audio_data),
            "formats": {}
        }
        
        for fmt, data in formats.items():
            result["formats"][fmt] = {
                "data_url": f"data:{data['mime_type']};base64,{base64.b64encode(data['data']).decode()}",
                "mime_type": data['mime_type'],
                "size": data['size'],
                "filename": f"speech.{fmt}"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"多格式TTS合成失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@app.options("/speech/synthesize-multi")
async def synthesize_multi_options():
    """处理多格式TTS OPTIONS预检请求"""
    return Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400"
    })


@app.post("/speech/analyze")
async def analyze_speech(
    audio: UploadFile = File(...)
):
    """
    分析语音特征
    """
    try:
        # 验证文件类型
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="文件类型必须是音频格式")
        
        # 读取音频数据
        audio_data = await audio.read()
        
        # 分析语音特征
        features = await speech_service.analyze_speech_features(audio_data)
        
        return {
            "success": True,
            "features": features,
            "analysis": {
                "speech_rate_level": _get_speech_rate_level(features.get("speech_rate", 0)),
                "fluency_score": _calculate_fluency_score(features),
                "recommendations": _get_speech_recommendations(features)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音分析失败: {str(e)}")


@app.get("/speech/voices")
async def get_voice_options():
    """
    获取可用的语音选项
    """
    try:
        voices = await speech_service.get_supported_voices()
        return {
            "success": True,
            "voices": voices["voices"],
            "default_voice": voices["default"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取语音选项失败: {str(e)}")


@app.post("/session/{session_id}/question/audio")
async def get_question_audio(session_id: str):
    """
    获取当前问题的语音版本
    """
    session = await storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        # 获取最新的问题
        latest_question = None
        for item in reversed(session.history):
            if item['role'] == 'assistant':
                latest_question = item['content']
                break
        
        if not latest_question:
            raise HTTPException(status_code=404, detail="没有找到问题")
        
        # 生成问题的语音
        audio_data = await voice_interviewer.speak_question(latest_question)
        
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=question.mp3"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成问题语音失败: {str(e)}")


@app.post("/session/{session_id}/answer/voice")
async def submit_voice_answer(
    session_id: str,
    audio: UploadFile = File(...)
):
    """
    提交语音回答
    """
    session = await storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        # 读取音频数据
        audio_data = await audio.read()
        
        # 语音转文字
        transcription = await speech_service.speech_to_text(
            audio_data=audio_data,
            filename=audio.filename or "answer.webm"
        )
        
        # 分析语音特征
        speech_features = await speech_service.analyze_speech_features(audio_data)
        
        # 保存语音分析结果到会话
        if not hasattr(session, 'speech_analysis'):
            session.speech_analysis = []
        
        session.speech_analysis.append({
            "timestamp": asyncio.get_running_loop().time(),
            "transcription": transcription,
            "features": speech_features
        })
        
        # 提交文字回答
        answer_text = transcription["text"]
        
        # 添加用户回答到历史
        session.history.append({
            "role": "user", 
            "content": answer_text
        })
        
        # 构建previous_qa用于新接口
        assistant_messages = [h for h in session.history if h['role'] == 'assistant']
        user_messages = [h for h in session.history if h['role'] == 'user']
        previous_qa = list(zip(assistant_messages, user_messages))
        previous_qa = [(q['content'], a['content']) for q, a in previous_qa]
        
        # 计算下一个问题序号
        next_question_number = len(assistant_messages) + 1
        
        # 使用新接口生成下一个问题
        next_question = await chat_service.generate_interview_question(
            job_description=session.job_description,
            interview_type=session.interview_type,
            previous_qa=previous_qa,
            question_number=next_question_number
        )
        
        # 保存问题到历史
        session.history.append({
            "role": "assistant", 
            "content": next_question
        })
        
        await storage.update_session(session)
        
        # 计算当前问题序号
        question_number = len([h for h in session.history if h['role'] == 'assistant'])
        
        return {
            "success": True,
            "transcription": answer_text,
            "speech_analysis": {
                "duration": speech_features.get("duration", 0),
                "speech_rate": speech_features.get("speech_rate", 0),
                "fluency_score": _calculate_fluency_score(speech_features)
            },
            "next_question": next_question,
            "question_number": question_number
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理语音回答失败: {str(e)}")


# -----------------------------
# 数字人相关API端点
# -----------------------------

# 注释掉重复的路由定义，避免与 /session/start 冲突
# @app.post("/session/{session_id}/start")
# async def __REMOVED_API_KEY__(
#     session_id: str,
#     request: dict
# ):
#     """
#     开始数字人面试会话
#     """
#     try:
#         job_description = request.get("job_description", "")
#         interview_type = request.get("interview_type", "behavioral")
#         
#         # 获取或创建会话
#         session = await storage.get_session(session_id)
#         if not session:
#             session = await storage.create_session(
#                 job_description=job_description,
#                 interview_type=interview_type,
#                 session_id=session_id
#             )
#         
#         # 生成第一个问题
#         first_question = await chat_service.generate_interview_question(
#             conversation_history=[],
#             job_description=job_description,
#             interview_type=interview_type
#         )
#         
#         # 生成问题的语音
#         audio_data = await voice_interviewer.speak_question(first_question)
#         
#         # 保存音频到临时文件或返回base64
#         import base64
#         audio_base64 = base64.b64encode(audio_data).decode('utf-8')
#         audio_url = f"data:audio/mpeg;base64,{audio_base64}"
#         
#         # 保存到会话历史
#         session.history.append({
#             "role": "assistant",
#             "content": first_question
#         })
#         await storage.update_session(session)
#         
#         return {
#             "success": True,
#             "question": first_question,
#             "audio_url": audio_url,
#             "expression": "friendly",  # 数字人表情提示
#             "action": "greeting"       # 数字人动作提示
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"启动数字人面试失败: {str(e)}")


@app.post("/session/{session_id}/answer/with_voice")
async def submit_answer_to_digital_human(
    session_id: str,
    request: dict
):
    """
    提交答案给数字人面试官
    """
    session = await storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        answer = request.get("answer", "")
        with_voice = request.get("with_voice", False)
        
        # 添加用户回答到历史
        session.history.append({
            "role": "user",
            "content": answer
        })
        
        # 检查是否应该结束面试
        question_count = len([h for h in session.history if h['role'] == 'assistant'])
        is_complete = question_count >= 5  # 5个问题后结束
        
        if not is_complete:
            # 构建previous_qa用于新接口
            assistant_messages = [h for h in session.history if h['role'] == 'assistant']
            user_messages = [h for h in session.history if h['role'] == 'user']
            previous_qa = list(zip(assistant_messages, user_messages))
            previous_qa = [(q['content'], a['content']) for q, a in previous_qa]
            
            # 计算下一个问题序号
            next_question_number = len(assistant_messages) + 1
            
            # 使用新接口生成下一个问题
            next_question = await chat_service.generate_interview_question(
                job_description=session.job_description,
                interview_type=session.interview_type,
                previous_qa=previous_qa,
                question_number=next_question_number
            )
            
            # 保存问题到历史
            session.history.append({
                "role": "assistant",
                "content": next_question
            })
            
            response_data = {
                "success": True,
                "question": next_question,
                "is_complete": False,
                "question_number": question_count + 1
            }
            
            # 如果需要语音，生成语音
            if with_voice:
                audio_data = await voice_interviewer.speak_question(next_question)
                import base64
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                response_data["audio_url"] = f"data:audio/mpeg;base64,{audio_base64}"
                
                # 根据问题内容决定表情和动作
                if "tell me about" in next_question.lower():
                    response_data["expression"] = "curious"
                    response_data["action"] = "listening"
                elif "challenge" in next_question.lower() or "difficult" in next_question.lower():
                    response_data["expression"] = "serious"
                    response_data["action"] = "thinking"
                else:
                    response_data["expression"] = "neutral"
                    response_data["action"] = "talking"
            
        else:
            # 面试结束
            response_data = {
                "success": True,
                "is_complete": True,
                "message": "面试已完成，正在生成反馈报告...",
                "expression": "smile",
                "action": "nodding"
            }
        
        await storage.update_session(session)
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理回答失败: {str(e)}")


@app.post("/api/speech/transcribe")
async def transcribe_audio_base64(request: Request):
    """转录base64编码的音频数据"""
    try:
        # 获取请求数据
        data = await request.json()
        audio_data = data.get('audio_data')
        
        if not audio_data:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "缺少音频数据"}
            )
        
        # 检查音频数据大小（base64编码后的大小）
        if len(audio_data) > 33554432:  # 约25MB的base64数据
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "音频文件过大，请缩短录音时间"}
            )
        
        # 解码base64音频数据
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            logger.error(f"Base64解码失败: {e}")
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "音频数据格式错误"}
            )
        
        # 检查解码后的音频大小
        if len(audio_bytes) == 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "音频数据为空"}
            )
        
        if len(audio_bytes) > 25 * 1024 * 1024:  # 25MB限制
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "音频文件过大"}
            )
        
        logger.info(f"开始处理音频转录，数据大小: {len(audio_bytes)} bytes")
        
        # 使用语音服务进行转录，设置超时
        try:
            # 添加超时处理
            import asyncio
            result = await asyncio.wait_for(
                speech_service.speech_to_text(audio_bytes),
                timeout=30.0  # 30秒超时
            )
            
            if result and result.get('text'):
                text = result['text'].strip()
                if text:
                    logger.info(f"语音转录成功: {text[:50]}...")
                    return JSONResponse(
                        status_code=200,
                        content={
                            "success": True,
                            "text": text,
                            "language": result.get('language', 'unknown'),
                            "duration": result.get('duration', 0),
                            "confidence": result.get('confidence', 0)
                        }
                    )
                else:
                    logger.warning("语音转录结果为空")
                    return JSONResponse(
                        status_code=200,
                        content={"success": False, "error": "未检测到有效语音内容"}
                    )
            else:
                logger.warning("语音转录失败，无结果")
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": "语音识别服务暂时不可用"}
                )
                
        except asyncio.TimeoutError:
            logger.error("语音转录超时")
            return JSONResponse(
                status_code=408,
                content={"success": False, "error": "语音识别超时，请重试"}
            )
        except Exception as e:
            logger.error(f"语音转录过程中发生错误: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"语音识别失败: {str(e)}"}
            )
            
    except json.JSONDecodeError:
        logger.error("请求JSON格式错误")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "请求格式错误"}
        )
    except Exception as e:
        logger.error(f"转录API发生未知错误: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "服务器内部错误"}
        )


# 重复的API端点已删除，使用上面改进的版本


# -----------------------------
# 辅助函数
# -----------------------------

def _get_speech_rate_level(speech_rate: float) -> str:
    """根据语速返回等级"""
    if speech_rate < 120:
        return "较慢"
    elif speech_rate < 160:
        return "正常"
    elif speech_rate < 200:
        return "较快"
    else:
        return "过快"


def _calculate_fluency_score(features: dict) -> float:
    """计算流畅度评分"""
    pause_analysis = features.get("pause_analysis", {})
    speech_rate = features.get("speech_rate", 0)
    
    # 基础分数
    score = 0.8
    
    # 根据停顿分析调整
    pause_count = pause_analysis.get("pause_count", 0)
    avg_pause = pause_analysis.get("avg_pause_duration", 0)
    
    if pause_count > 10:  # 停顿过多
        score -= 0.2
    elif avg_pause > 2.0:  # 停顿时间过长
        score -= 0.15
    
    # 根据语速调整
    if speech_rate < 100 or speech_rate > 220:  # 语速异常
        score -= 0.1
    
    return max(0.0, min(1.0, score))


def _get_speech_recommendations(features: dict) -> List[str]:
    """获取语音改进建议"""
    recommendations = []
    
    speech_rate = features.get("speech_rate", 0)
    pause_analysis = features.get("pause_analysis", {})
    
    if speech_rate < 120:
        recommendations.append("建议适当提高语速，让表达更加自然流畅")
    elif speech_rate > 200:
        recommendations.append("建议适当放慢语速，让面试官更容易理解")
    
    pause_count = pause_analysis.get("pause_count", 0)
    if pause_count > 15:
        recommendations.append("减少不必要的停顿，保持回答的连贯性")
    
    avg_pause = pause_analysis.get("avg_pause_duration", 0)
    if avg_pause > 2.0:
        recommendations.append("缩短思考时间，提前准备常见问题的回答")
    
    if not recommendations:
        recommendations.append("语音表达很好，继续保持")
    
    return recommendations


@app.post("/speech/synthesize-smart")
async def synthesize_speech_smart(
    request: Request,
    text: str = Form(...),
    voice: str = Form("nova"),
    speed: float = Form(1.0)
):
    """
    智能语音合成 - 根据浏览器自动选择最佳音频格式
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        if len(text) > 4000:
            raise HTTPException(status_code=400, detail="文本长度不能超过4000字符")
        
        # 导入音频处理器
        try:
            from core.audio_processor import audio_processor
        except ImportError:
            logger.warning("音频处理器模块未找到，使用基础模式")
            # 创建简单的备用处理器
            class SimpleAudioProcessor:
                def get_browser_preferred_format(self, user_agent=""):
                    return "wav"
                async def standardize_for_web(self, audio_data, format="wav"):
                    return audio_data, "audio/wav" if format == "wav" else "audio/mpeg"
            audio_processor = SimpleAudioProcessor()
        
        # 生成原始音频
        audio_data = await speech_service.text_to_speech(
            text=text,
            voice=voice,
            speed=speed
        )
        
        # 获取浏览器信息
        user_agent = request.headers.get("User-Agent", "")
        preferred_format = audio_processor.get_browser_preferred_format(user_agent)
        
        logger.info(f"🎯 检测到浏览器偏好格式: {preferred_format} (UA: {user_agent[:50]}...)")
        
        # 标准化音频格式
        converted_data, mime_type = await audio_processor.standardize_for_web(
            audio_data, preferred_format
        )
        
        # 返回优化后的音频
        return Response(
            content=converted_data,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename=speech.{preferred_format}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache", 
                "Expires": "0",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, User-Agent",
                "Content-Length": str(len(converted_data)),
                "Accept-Ranges": "bytes",
                "X-Audio-Format": preferred_format,
                "X-Original-Size": str(len(audio_data)),
                "X-Converted-Size": str(len(converted_data))
            }
        )
        
    except Exception as e:
        logger.error(f"智能TTS合成失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@app.options("/speech/synthesize-smart")
async def synthesize_smart_options():
    """处理智能TTS OPTIONS预检请求"""
    return Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, User-Agent",
        "Access-Control-Max-Age": "86400"
    })


# 启动服务器
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 启动VITA服务器...")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=False,
        log_level="info"
    )
