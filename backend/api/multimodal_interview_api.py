"""
多模态面试API
提供基于Doubao-Seed-1.6的面试评估接口
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging
import json
import base64
from io import BytesIO
from PIL import Image
import time

from core.multimodal_interview import (
    get_multimodal_evaluator, 
    evaluate_interview_response,
    start_interview,
    get_interview_summary,
    MultimodalAssessment
)
from core.config import VITAConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/multimodal", tags=["多模态面试"])

@router.post("/start-interview")
async def start_interview_session(
    position_type: str = Form(default="general"),
    expected_skills: Optional[str] = Form(default=None)
):
    """
    开始多模态面试会话
    
    Args:
        position_type: 职位类型 (general, software_engineer, data_scientist, etc.)
        expected_skills: 期望技能列表，JSON字符串格式
    """
    try:
        skills_list = []
        if expected_skills:
            try:
                skills_list = json.loads(expected_skills)
            except json.JSONDecodeError:
                skills_list = [skill.strip() for skill in expected_skills.split(",")]
        
        await start_interview(position_type, skills_list)
        
        return JSONResponse({
            "success": True,
            "message": f"面试会话已开始",
            "session_info": {
                "position_type": position_type,
                "expected_skills": skills_list,
                "evaluator_model": "Doubao-Seed-1.6"
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 开始面试会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"开始面试会话失败: {str(e)}")

@router.post("/evaluate-response")
async def evaluate_multimodal_response(
    question: str = Form(..., description="面试问题"),
    answer: str = Form(..., description="用户回答"),
    image: Optional[UploadFile] = File(None, description="用户面部图像"),
    audio: Optional[UploadFile] = File(None, description="用户语音文件"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    多模态面试回答评估
    
    使用Doubao-Seed-1.6模型分析用户的：
    - 面部表情和肢体语言（如果提供图像）
    - 语音语调和情感（如果提供音频）
    - 回答内容质量
    """
    try:
        # 处理图像数据
        image_data = None
        if image:
            if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
                raise HTTPException(status_code=400, detail="仅支持JPEG/PNG图像格式")
            
            # 读取并处理图像
            image_bytes = await image.read()
            
            # 验证图像并调整大小（避免过大的图像）
            try:
                pil_image = Image.open(BytesIO(image_bytes))
                # 如果图像过大，调整大小
                if pil_image.width > 1024 or pil_image.height > 1024:
                    pil_image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                    
                # 转换为JPEG格式以减少大小
                output_buffer = BytesIO()
                pil_image.convert('RGB').save(output_buffer, format='JPEG', quality=85)
                image_data = output_buffer.getvalue()
            except Exception as e:
                logger.error(f"图像处理失败: {e}")
                raise HTTPException(status_code=400, detail=f"图像处理失败: {str(e)}")
        
        # 处理音频数据
        audio_data = None
        if audio:
            if not audio.content_type.startswith("audio/"):
                raise HTTPException(status_code=400, detail="仅支持音频文件")
            
            audio_data = await audio.read()
            
            # 检查音频文件大小（限制25MB）
            if len(audio_data) > 25 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="音频文件过大，限制25MB")
        
        # 执行多模态评估
        logger.info(f"🎭 开始多模态评估: 问题长度={len(question)}, 回答长度={len(answer)}, "
                   f"有图像={'是' if image_data else '否'}, 有音频={'是' if audio_data else '否'}")
        
        assessment = await evaluate_interview_response(
            question=question,
            answer=answer,
            image_data=image_data,
            audio_data=audio_data
        )
        
        # 构建响应数据
        response_data = {
            "success": True,
            "assessment": {
                "overall_score": round(assessment.overall_score, 3),
                "score_breakdown": {
                    "content_quality": {
                        "relevance": round(assessment.content_analysis.relevance_score, 3),
                        "completeness": round(assessment.content_analysis.completeness, 3),
                        "technical_accuracy": round(assessment.content_analysis.technical_accuracy, 3),
                        "communication_clarity": round(assessment.content_analysis.communication_clarity, 3),
                        "keywords_covered": assessment.content_analysis.keywords_coverage
                    },
                    "facial_expression": {
                        "emotion": assessment.facial_analysis.emotion.value,
                        "confidence": round(assessment.facial_analysis.confidence, 3),
                        "eye_contact": round(assessment.facial_analysis.eye_contact, 3),
                        "attention_level": round(assessment.facial_analysis.attention_level, 3)
                    } if image_data else None,
                    "voice_characteristics": {
                        "tone_confidence": round(assessment.voice_analysis.tone_confidence, 3),
                        "speech_pace": assessment.voice_analysis.speech_pace,
                        "clarity": round(assessment.voice_analysis.clarity, 3),
                        "emotional_tone": assessment.voice_analysis.emotional_tone
                    } if audio_data else None
                },
                "engagement_level": assessment.engagement_level.value,
                "feedback": {
                    "strengths": assessment.strengths,
                    "improvements": assessment.areas_for_improvement,
                    "recommendations": assessment.recommendations
                },
                "analysis_timestamp": assessment.timestamp
            },
            "model_info": {
                "evaluator_model": "Doubao-Seed-1.6",
                "analysis_components": {
                    "facial_analysis": image_data is not None,
                    "voice_analysis": audio_data is not None,
                    "content_analysis": True
                }
            }
        }
        
        logger.info(f"✅ 多模态评估完成，综合得分: {assessment.overall_score:.3f}")
        return JSONResponse(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 多模态评估失败: {e}")
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")

@router.get("/session-summary")
async def get_session_summary():
    """
    获取当前面试会话的总结报告
    """
    try:
        summary = get_interview_summary()
        
        if "message" in summary:
            return JSONResponse({
                "success": False,
                "message": summary["message"]
            })
        
        return JSONResponse({
            "success": True,
            "summary": {
                "session_stats": {
                    "duration_seconds": round(summary.get("session_duration", 0), 1),
                    "total_questions": summary.get("total_questions", 0),
                    "average_score": round(summary.get("average_score", 0), 3)
                },
                "performance_analysis": {
                    "score_trend": summary.get("score_trend", []),
                    "emotion_distribution": summary.get("emotion_distribution", {}),
                    "engagement_distribution": summary.get("engagement_distribution", {})
                },
                "key_recommendations": summary.get("recommendations_summary", []),
                "model_info": {
                    "evaluator_model": "Doubao-Seed-1.6",
                    "capabilities": [
                        "面部表情分析",
                        "语音情感识别", 
                        "内容质量评估",
                        "综合表现评分"
                    ]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 获取会话总结失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取总结失败: {str(e)}")

@router.post("/analyze-expression")
async def analyze_facial_expression(
    image: UploadFile = File(..., description="用户面部图像")
):
    """
    单独分析面部表情
    
    使用Doubao-Seed-1.6模型分析用户的面部表情、眼神交流等
    """
    try:
        if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(status_code=400, detail="仅支持JPEG/PNG图像格式")
        
        # 处理图像
        image_bytes = await image.read()
        
        evaluator = get_multimodal_evaluator()
        facial_analysis = await evaluator.analyze_facial_expression(image_bytes)
        
        return JSONResponse({
            "success": True,
            "facial_analysis": {
                "emotion": facial_analysis.emotion.value,
                "confidence": round(facial_analysis.confidence, 3),
                "eye_contact": round(facial_analysis.eye_contact, 3),
                "smile_intensity": round(facial_analysis.smile_intensity, 3),
                "attention_level": round(facial_analysis.attention_level, 3),
                "timestamp": facial_analysis.timestamp
            },
            "model_info": {
                "analyzer_model": "Doubao-Seed-1.6",
                "analysis_type": "facial_expression"
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 面部表情分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.post("/analyze-voice")
async def analyze_voice_characteristics(
    audio: UploadFile = File(..., description="用户语音文件"),
    transcript: str = Form(..., description="语音转录文本")
):
    """
    单独分析语音特征
    
    使用Doubao-Seed-1.6模型分析用户的语音语调、情感等特征
    """
    try:
        if not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="仅支持音频文件")
        
        audio_data = await audio.read()
        
        evaluator = get_multimodal_evaluator()
        voice_analysis = await evaluator.analyze_voice_characteristics(audio_data, transcript)
        
        return JSONResponse({
            "success": True,
            "voice_analysis": {
                "tone_confidence": round(voice_analysis.tone_confidence, 3),
                "speech_pace": voice_analysis.speech_pace,
                "volume_level": round(voice_analysis.volume_level, 3),
                "clarity": round(voice_analysis.clarity, 3),
                "emotional_tone": voice_analysis.emotional_tone,
                "pause_frequency": round(voice_analysis.pause_frequency, 3),
                "timestamp": voice_analysis.timestamp
            },
            "model_info": {
                "analyzer_model": "Doubao-Seed-1.6",
                "analysis_type": "voice_characteristics"
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 语音特征分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.get("/model-capabilities")
async def get_model_capabilities():
    """
    获取Doubao-Seed-1.6模型的能力信息
    """
    return JSONResponse({
        "model_name": "Doubao-Seed-1.6",
        "model_type": "multimodal",
        "capabilities": {
            "facial_analysis": {
                "emotions": ["confident", "nervous", "calm", "excited", "confused", "focused", "stressed"],
                "metrics": ["eye_contact", "smile_intensity", "attention_level", "confidence"]
            },
            "voice_analysis": {
                "characteristics": ["tone_confidence", "speech_pace", "volume_level", "clarity"],
                "emotional_tones": ["自信且专业", "紧张但努力", "平静稳定", "热情积极"]
            },
            "content_analysis": {
                "dimensions": ["relevance", "completeness", "technical_accuracy", "communication_clarity"],
                "features": ["keyword_extraction", "quality_scoring", "relevance_assessment"]
            }
        },
        "integration_status": {
            "api_configured": True,
            "model_available": True,
            "fallback_enabled": True
        }
    })

@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查配置
        config_valid = VITAConfig.get_config_summary()
        
        return JSONResponse({
            "status": "healthy",
            "model": "Doubao-Seed-1.6",
            "service": "multimodal_interview_api",
            "doubao_configured": config_valid.get("doubao_configured", False),
            "timestamp": time.time()
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }, status_code=503) 