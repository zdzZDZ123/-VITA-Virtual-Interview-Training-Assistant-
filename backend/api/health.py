from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from datetime import datetime
from core.health_monitor import get_health_summary, get_health_monitor
from core.client_manager import get_active_clients_count
from core.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["健康检查"])

@router.get("/", summary="基础健康检查")
async def health_check() -> Dict[str, Any]:
    """基础健康检查端点"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "VITA",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="健康检查失败")

@router.get("/detailed", summary="详细健康状态")
async def detailed_health() -> Dict[str, Any]:
    """详细健康状态检查"""
    try:
        health_summary = get_health_summary()
        
        return {
            "service": "VITA",
            "timestamp": datetime.now().isoformat(),
            "health": health_summary,
            "clients": {
                "active_count": get_active_clients_count()
            },
            "config": {
                "llama_enabled": bool(config.LLAMA_API_KEY),
                "qwen_enabled": bool(config.QWEN_API_KEY),
                "local_whisper_enabled": config.USE_LOCAL_WHISPER,
                "local_tts_enabled": config.USE_LOCAL_TTS
            }
        }
    except Exception as e:
        logger.error(f"详细健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="详细健康检查失败")

@router.get("/metrics", summary="系统指标")
async def get_metrics() -> Dict[str, Any]:
    """获取系统监控指标"""
    try:
        monitor = get_health_monitor()
        current_metrics = monitor.get_current_metrics()
        
        if not current_metrics:
            return {
                "status": "no_data",
                "message": "暂无监控数据",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "timestamp": current_metrics.timestamp.isoformat(),
            "clients": {
                "active": current_metrics.active_clients,
                "healthy": current_metrics.healthy_clients,
                "unhealthy": current_metrics.unhealthy_clients
            },
            "requests": {
                "total": current_metrics.total_requests,
                "failed": current_metrics.failed_requests,
                "success_rate": current_metrics.success_rate,
                "avg_response_time": current_metrics.avg_response_time
            },
            "system": {
                "memory_usage_mb": current_metrics.memory_usage_mb,
                "cpu_usage_percent": current_metrics.cpu_usage_percent
            },
            "health_score": current_metrics.health_score
        }
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取系统指标失败")

@router.get("/metrics/history", summary="历史指标")
async def get_metrics_history(hours: int = 1) -> Dict[str, Any]:
    """获取历史监控指标"""
    try:
        if hours < 1 or hours > 24:
            raise HTTPException(status_code=400, detail="时间范围必须在1-24小时之间")
        
        monitor = get_health_monitor()
        history = monitor.get_metrics_history(hours=hours)
        
        if not history:
            return {
                "status": "no_data",
                "message": f"过去{hours}小时内暂无监控数据",
                "hours": hours,
                "timestamp": datetime.now().isoformat()
            }
        
        # 转换为API友好的格式
        metrics_data = []
        for metrics in history:
            metrics_data.append({
                "timestamp": metrics.timestamp.isoformat(),
                "health_score": metrics.health_score,
                "active_clients": metrics.active_clients,
                "healthy_clients": metrics.healthy_clients,
                "success_rate": metrics.success_rate,
                "avg_response_time": metrics.avg_response_time,
                "memory_usage_mb": metrics.memory_usage_mb,
                "cpu_usage_percent": metrics.cpu_usage_percent
            })
        
        return {
            "hours": hours,
            "count": len(metrics_data),
            "data": metrics_data,
            "summary": {
                "avg_health_score": sum(m["health_score"] for m in metrics_data) / len(metrics_data),
                "avg_response_time": sum(m["avg_response_time"] for m in metrics_data) / len(metrics_data),
                "avg_success_rate": sum(m["success_rate"] for m in metrics_data) / len(metrics_data)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取历史指标失败")

@router.get("/clients", summary="客户端状态")
async def get_clients_status() -> Dict[str, Any]:
    """获取所有客户端的状态信息"""
    try:
        from core.qwen_llama_client import _client_registry
        
        clients_info = []
        for client in _client_registry:
            try:
                client_info = {
                    "type": getattr(client, '_client_type', 'unknown'),
                    "base_url": getattr(client, '_base_url', 'unknown'),
                    "is_healthy": getattr(client, '_is_healthy', False),
                    "retry_count": getattr(client, '_retry_count', 0),
                    "max_retries": getattr(client, '_max_retries', 0),
                    "is_closing": getattr(client, '_is_closing', False)
                }
                clients_info.append(client_info)
            except Exception as e:
                logger.warning(f"获取客户端信息失败: {e}")
                clients_info.append({
                    "type": "error",
                    "error": str(e)
                })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_clients": len(clients_info),
            "active_clients": get_active_clients_count(),
            "clients": clients_info
        }
    except Exception as e:
        logger.error(f"获取客户端状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取客户端状态失败")

@router.post("/test", summary="健康检查测试")
async def test_health_endpoints() -> Dict[str, Any]:
    """测试所有健康检查端点"""
    try:
        results = {}
        
        # 测试基础健康检查
        try:
            basic_health = await health_check()
            results["basic_health"] = {"status": "success", "data": basic_health}
        except Exception as e:
            results["basic_health"] = {"status": "error", "error": str(e)}
        
        # 测试详细健康检查
        try:
            detailed = await detailed_health()
            results["detailed_health"] = {"status": "success", "data": detailed}
        except Exception as e:
            results["detailed_health"] = {"status": "error", "error": str(e)}
        
        # 测试指标获取
        try:
            metrics = await get_metrics()
            results["metrics"] = {"status": "success", "data": metrics}
        except Exception as e:
            results["metrics"] = {"status": "error", "error": str(e)}
        
        # 测试客户端状态
        try:
            clients = await get_clients_status()
            results["clients_status"] = {"status": "success", "data": clients}
        except Exception as e:
            results["clients_status"] = {"status": "error", "error": str(e)}
        
        # 计算总体测试结果
        success_count = sum(1 for r in results.values() if r["status"] == "success")
        total_count = len(results)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_tests": total_count,
                "successful_tests": success_count,
                "failed_tests": total_count - success_count,
                "success_rate": success_count / total_count if total_count > 0 else 0
            },
            "results": results
        }
    except Exception as e:
        logger.error(f"健康检查测试失败: {e}")
        raise HTTPException(status_code=500, detail="健康检查测试失败")