"""
模型管理API
提供Whisper模型的状态查询、下载和管理功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import asyncio
from core.whisper_model_manager import get_model_manager
from core.logger import logger

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("/whisper/status")
async def get_whisper_models_status() -> Dict[str, Any]:
    """获取所有Whisper模型的状态"""
    try:
        model_manager = get_model_manager()
        models = model_manager.list_available_models()
        
        return {
            "status": "ok",
            "models": models,
            "download_in_progress": model_manager.download_in_progress,
            "recommended_model": "medium"  # 推荐使用medium模型
        }
    except Exception as e:
        logger.error(f"获取模型状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whisper/{model_size}")
async def get_whisper_model_info(model_size: str) -> Dict[str, Any]:
    """获取指定Whisper模型的详细信息"""
    try:
        model_manager = get_model_manager()
        info = model_manager.get_model_info(model_size)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"不支持的模型: {model_size}")
        
        return {
            "status": "ok",
            "model_size": model_size,
            "info": info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模型信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whisper/{model_size}/download")
async def download_whisper_model(
    model_size: str,
    background_tasks: BackgroundTasks,
    force: bool = False
) -> Dict[str, Any]:
    """下载指定的Whisper模型"""
    try:
        model_manager = get_model_manager()
        
        # 检查模型是否已存在
        if not force and model_manager.find_local_model(model_size):
            return {
                "status": "exists",
                "message": f"模型 {model_size} 已存在",
                "path": str(model_manager.find_local_model(model_size))
            }
        
        # 检查是否有正在进行的下载
        if model_manager.download_in_progress:
            return {
                "status": "downloading",
                "message": "已有下载任务正在进行",
                "progress": model_manager.download_progress
            }
        
        # 在后台开始下载
        async def download_task():
            try:
                success = await model_manager.download_model_async(model_size)
                if success:
                    logger.info(f"✅ 模型 {model_size} 下载成功")
                else:
                    logger.error(f"❌ 模型 {model_size} 下载失败")
            except Exception as e:
                logger.error(f"下载任务出错: {e}")
        
        background_tasks.add_task(download_task)
        
        return {
            "status": "started",
            "message": f"开始下载模型 {model_size}",
            "model_size": model_size
        }
        
    except Exception as e:
        logger.error(f"启动模型下载失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whisper/download/progress")
async def get_download_progress() -> Dict[str, Any]:
    """获取当前下载进度"""
    try:
        model_manager = get_model_manager()
        
        return {
            "status": "ok",
            "downloading": model_manager.download_in_progress,
            "progress": model_manager.download_progress
        }
    except Exception as e:
        logger.error(f"获取下载进度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whisper/ensure/{model_size}")
async def ensure_model_available(model_size: str) -> Dict[str, Any]:
    """确保模型可用（必要时自动下载）"""
    try:
        model_manager = get_model_manager()
        
        # 同步方式确保模型可用
        model_path = await model_manager.ensure_model_available(model_size, auto_download=True)
        
        if model_path:
            return {
                "status": "ready",
                "message": f"模型 {model_size} 已就绪",
                "path": str(model_path)
            }
        else:
            return {
                "status": "failed",
                "message": f"无法获取模型 {model_size}",
                "suggestion": "请检查网络连接或手动下载模型"
            }
            
    except Exception as e:
        logger.error(f"确保模型可用失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/whisper/cache")
async def cleanup_whisper_cache() -> Dict[str, Any]:
    """清理Whisper模型缓存"""
    try:
        model_manager = get_model_manager()
        freed_bytes = model_manager.cleanup_cache()
        
        freed_mb = freed_bytes / (1024 * 1024)
        
        return {
            "status": "ok",
            "message": f"清理缓存成功",
            "freed_mb": round(freed_mb, 2)
        }
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 