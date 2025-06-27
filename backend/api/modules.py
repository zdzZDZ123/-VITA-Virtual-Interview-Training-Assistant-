"""
模块健康检查API
提供语音模块的状态查询、诊断和管理功能
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from core.module_registry import get_module_registry, check_voice_modules_health
from core.logger import logger

router = APIRouter(prefix="/api/modules", tags=["modules"])

@router.get("/health")
async def get_modules_health() -> Dict[str, Any]:
    """获取所有语音模块的健康状态"""
    try:
        health_report = check_voice_modules_health()
        return {
            "status": "ok",
            "data": health_report,
            "summary": {
                "total": health_report["total_modules"],
                "ready": health_report["ready_modules"],
                "errors": health_report["error_modules"],
                "health_score": round(health_report["ready_modules"] / max(health_report["total_modules"], 1) * 100, 1)
            }
        }
    except Exception as e:
        logger.error(f"获取模块健康状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_modules_status() -> Dict[str, Any]:
    """获取详细的模块状态信息"""
    try:
        registry = get_module_registry()
        modules = registry.get_all_modules()
        
        # 按类型分组
        speech_recognition = {}
        text_to_speech = {}
        other = {}
        
        for name, info in modules.items():
            module_data = info.to_dict()
            
            if name in ["faster-whisper", "whisper"]:
                speech_recognition[name] = module_data
            elif name in ["edge-tts", "pyttsx3"]:
                text_to_speech[name] = module_data
            else:
                other[name] = module_data
        
        return {
            "status": "ok",
            "categories": {
                "speech_recognition": speech_recognition,
                "text_to_speech": text_to_speech,
                "other": other
            },
            "dependencies_check": registry.check_dependencies()
        }
    except Exception as e:
        logger.error(f"获取模块状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{module_name}")
async def get_module_status(module_name: str) -> Dict[str, Any]:
    """获取指定模块的详细状态"""
    try:
        registry = get_module_registry()
        module_info = registry.get_module_status(module_name)
        
        if not module_info:
            raise HTTPException(status_code=404, detail=f"模块 {module_name} 不存在")
        
        return {
            "status": "ok",
            "module": module_info.to_dict(),
            "is_available": registry.is_module_available(module_name)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模块 {module_name} 状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reload/{module_name}")
async def reload_module(module_name: str) -> Dict[str, Any]:
    """重新加载指定模块"""
    try:
        registry = get_module_registry()
        success = registry.reload_module(module_name)
        
        if success:
            return {
                "status": "ok",
                "message": f"模块 {module_name} 重新加载成功",
                "module": registry.get_module_status(module_name).to_dict()
            }
        else:
            return {
                "status": "error",
                "message": f"模块 {module_name} 重新加载失败"
            }
    except Exception as e:
        logger.error(f"重新加载模块 {module_name} 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations")
async def get_module_recommendations() -> Dict[str, Any]:
    """获取模块优化建议"""
    try:
        registry = get_module_registry()
        health_report = registry.get_health_report()
        
        recommendations = []
        
        # 检查各个模块的状态并给出建议
        modules = registry.get_all_modules()
        
        # faster-whisper相关建议
        if "faster-whisper" in modules:
            fw_info = modules["faster-whisper"]
            if fw_info.status.value == "not_installed":
                recommendations.append({
                    "type": "installation",
                    "module": "faster-whisper",
                    "priority": "high",
                    "message": "建议安装 faster-whisper 以获得更好的语音识别性能",
                    "action": "pip install faster-whisper"
                })
            elif fw_info.status.value == "installed":
                recommendations.append({
                    "type": "model_download",
                    "module": "faster-whisper",
                    "priority": "medium",
                    "message": "建议下载 medium 模型以获得最佳性能",
                    "action": "python scripts/download_faster_whisper.py medium"
                })
        
        # edge-tts相关建议
        if "edge-tts" in modules:
            et_info = modules["edge-tts"]
            if et_info.status.value == "not_installed":
                recommendations.append({
                    "type": "installation",
                    "module": "edge-tts",
                    "priority": "high",
                    "message": "建议安装 edge-tts 以获得高质量的语音合成",
                    "action": "pip install edge-tts"
                })
        
        # 通用建议
        if health_report["ready_modules"] < health_report["total_modules"]:
            recommendations.append({
                "type": "general",
                "priority": "medium",
                "message": "部分模块未正常工作，建议检查安装和配置",
                "action": "运行: python backend/fix_whisper_models.py --diagnose-only"
            })
        
        return {
            "status": "ok",
            "recommendations": recommendations,
            "health_score": round(health_report["ready_modules"] / max(health_report["total_modules"], 1) * 100, 1)
        }
    except Exception as e:
        logger.error(f"获取模块建议失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 