"""
多模态面试评估模块
使用Doubao-Seed-1.6模型分析用户的表情、语气、肢体语言和回答内容
提供全方位的面试表现评估
"""

import asyncio
import logging
import json
import time
import base64
import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import io
from PIL import Image

from .config import VITAConfig
from .qwen_llama_client import get_client_manager

logger = logging.getLogger(__name__)

class EmotionState(Enum):
    """情绪状态"""
    CONFIDENT = "confident"      # 自信
    NERVOUS = "nervous"          # 紧张
    CALM = "calm"               # 冷静
    EXCITED = "excited"         # 兴奋
    CONFUSED = "confused"       # 困惑
    FOCUSED = "focused"         # 专注
    STRESSED = "stressed"       # 压力大

class EngagementLevel(Enum):
    """参与度级别"""
    HIGH = "high"               # 高度参与
    MEDIUM = "medium"           # 中等参与
    LOW = "low"                 # 低参与
    DISTRACTED = "distracted"   # 分心

@dataclass
class FacialAnalysis:
    """面部表情分析结果"""
    emotion: EmotionState
    confidence: float           # 置信度 0-1
    eye_contact: float         # 眼神交流程度 0-1
    smile_intensity: float     # 微笑强度 0-1
    attention_level: float     # 注意力水平 0-1
    timestamp: float

@dataclass
class VoiceAnalysis:
    """语音分析结果"""
    tone_confidence: float     # 语调自信度 0-1
    speech_pace: float         # 语速 (words per minute)
    volume_level: float        # 音量水平 0-1
    clarity: float            # 清晰度 0-1
    emotional_tone: str       # 情感语调
    pause_frequency: float    # 停顿频率
    timestamp: float

@dataclass
class ContentAnalysis:
    """内容分析结果"""
    relevance_score: float    # 相关性得分 0-1
    completeness: float       # 完整性 0-1
    technical_accuracy: float # 技术准确性 0-1
    communication_clarity: float # 表达清晰度 0-1
    keywords_coverage: List[str] # 关键词覆盖
    timestamp: float

@dataclass
class MultimodalAssessment:
    """综合多模态评估结果"""
    overall_score: float      # 总体得分 0-1
    facial_analysis: FacialAnalysis
    voice_analysis: VoiceAnalysis
    content_analysis: ContentAnalysis
    engagement_level: EngagementLevel
    recommendations: List[str] # 改进建议
    strengths: List[str]      # 优势点
    areas_for_improvement: List[str] # 需要改进的地方
    timestamp: float

class MultimodalInterviewEvaluator:
    """多模态面试评估器
    
    使用Doubao-Seed-1.6模型进行全方位面试评估
    """
    
    def __init__(self):
        self.model_name = "Doubao-Seed-1.6"
        self.client_manager = get_client_manager()
        
        # 评估历史
        self.assessment_history: List[MultimodalAssessment] = []
        
        # 当前面试会话配置
        self.current_session = {
            "start_time": 0,
            "question_count": 0,
            "current_question": "",
            "expected_keywords": [],
            "position_type": "general"  # 职位类型
        }
        
        logger.info("🎭 多模态面试评估器初始化完成")
    
    def start_interview_session(self, position_type: str = "general", expected_skills: List[str] = None):
        """开始面试会话"""
        self.current_session = {
            "start_time": time.time(),
            "question_count": 0,
            "current_question": "",
            "expected_keywords": expected_skills or [],
            "position_type": position_type
        }
        self.assessment_history.clear()
        logger.info(f"🎬 开始面试会话: {position_type}")
    
    async def analyze_facial_expression(self, image_data: bytes) -> FacialAnalysis:
        """分析面部表情"""
        try:
            # 将图像编码为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 构建多模态分析prompt
            prompt = """
作为专业的面试官，请分析这张面试者的照片，评估以下方面：

1. 情绪状态 (confident/nervous/calm/excited/confused/focused/stressed)
2. 眼神交流程度 (0-1, 1表示完全直视)
3. 微笑强度 (0-1, 1表示自然微笑)
4. 注意力水平 (0-1, 1表示高度专注)
5. 整体置信度 (0-1)

请以JSON格式返回结果：
{
  "emotion": "情绪状态",
  "confidence": 0.8,
  "eye_contact": 0.7,
  "smile_intensity": 0.6,
  "attention_level": 0.9
}
"""

            # 获取客户端并发送请求
            client = await self.client_manager.get_healthy_client(provider_type="doubao")
            if not client:
                raise Exception("豆包客户端不可用")
            
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # 解析响应
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            
            return FacialAnalysis(
                emotion=EmotionState(result_json.get("emotion", "calm")),
                confidence=result_json.get("confidence", 0.5),
                eye_contact=result_json.get("eye_contact", 0.5),
                smile_intensity=result_json.get("smile_intensity", 0.5),
                attention_level=result_json.get("attention_level", 0.5),
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"❌ 面部表情分析失败: {e}")
            # 返回默认分析结果
            return FacialAnalysis(
                emotion=EmotionState.CALM,
                confidence=0.5,
                eye_contact=0.5,
                smile_intensity=0.5,
                attention_level=0.5,
                timestamp=time.time()
            )
    
    async def analyze_voice_characteristics(self, audio_data: bytes, transcript: str) -> VoiceAnalysis:
        """分析语音特征"""
        try:
            # 构建语音分析prompt
            prompt = f"""
作为语音分析专家，请分析以下面试回答的语音特征：

转录文本: "{transcript}"

请评估以下语音特征：
1. 语调自信度 (0-1, 1表示非常自信)
2. 语速适中程度 (以words per minute估算)
3. 音量适中程度 (0-1, 0.5为适中)
4. 表达清晰度 (0-1, 1表示非常清晰)
5. 情感语调描述
6. 停顿频率 (0-1, 0.3为适中)

基于文本内容推断这些特征，以JSON格式返回：
{{
  "tone_confidence": 0.8,
  "speech_pace": 150,
  "volume_level": 0.6,
  "clarity": 0.9,
  "emotional_tone": "自信且专业",
  "pause_frequency": 0.3
}}
"""

            client = await self.client_manager.get_healthy_client(provider_type="doubao")
            if not client:
                raise Exception("豆包客户端不可用")
            
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            
            return VoiceAnalysis(
                tone_confidence=result_json.get("tone_confidence", 0.5),
                speech_pace=result_json.get("speech_pace", 150),
                volume_level=result_json.get("volume_level", 0.5),
                clarity=result_json.get("clarity", 0.5),
                emotional_tone=result_json.get("emotional_tone", "平静"),
                pause_frequency=result_json.get("pause_frequency", 0.3),
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"❌ 语音特征分析失败: {e}")
            return VoiceAnalysis(
                tone_confidence=0.5,
                speech_pace=150,
                volume_level=0.5,
                clarity=0.5,
                emotional_tone="平静",
                pause_frequency=0.3,
                timestamp=time.time()
            )
    
    async def analyze_content_quality(self, question: str, answer: str) -> ContentAnalysis:
        """分析回答内容质量"""
        try:
            prompt = f"""
作为面试专家，请评估以下面试问答的质量：

问题: "{question}"
回答: "{answer}"

请从以下维度评估（0-1分）：
1. 相关性得分 - 回答是否直接相关
2. 完整性 - 回答是否完整全面
3. 技术准确性 - 技术内容是否准确
4. 表达清晰度 - 逻辑是否清晰
5. 关键词覆盖 - 提到了哪些重要关键词

以JSON格式返回：
{{
  "relevance_score": 0.8,
  "completeness": 0.7,
  "technical_accuracy": 0.9,
  "communication_clarity": 0.8,
  "keywords_coverage": ["关键词1", "关键词2"]
}}
"""

            client = await self.client_manager.get_healthy_client(provider_type="doubao")
            if not client:
                raise Exception("豆包客户端不可用")
            
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            
            return ContentAnalysis(
                relevance_score=result_json.get("relevance_score", 0.5),
                completeness=result_json.get("completeness", 0.5),
                technical_accuracy=result_json.get("technical_accuracy", 0.5),
                communication_clarity=result_json.get("communication_clarity", 0.5),
                keywords_coverage=result_json.get("keywords_coverage", []),
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"❌ 内容质量分析失败: {e}")
            return ContentAnalysis(
                relevance_score=0.5,
                completeness=0.5,
                technical_accuracy=0.5,
                communication_clarity=0.5,
                keywords_coverage=[],
                timestamp=time.time()
            )
    
    async def comprehensive_assessment(
        self,
        question: str,
        answer: str,
        image_data: Optional[bytes] = None,
        audio_data: Optional[bytes] = None
    ) -> MultimodalAssessment:
        """综合多模态评估"""
        try:
            # 并行执行各项分析
            tasks = []
            
            # 内容分析（必须）
            content_task = self.analyze_content_quality(question, answer)
            tasks.append(content_task)
            
            # 面部表情分析（如果有图像）
            if image_data:
                facial_task = self.analyze_facial_expression(image_data)
                tasks.append(facial_task)
            else:
                facial_task = None
            
            # 语音分析（如果有音频）
            if audio_data:
                voice_task = self.analyze_voice_characteristics(audio_data, answer)
                tasks.append(voice_task)
            else:
                voice_task = None
            
            # 等待所有分析完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            content_analysis = results[0] if isinstance(results[0], ContentAnalysis) else ContentAnalysis(
                relevance_score=0.5, completeness=0.5, technical_accuracy=0.5,
                communication_clarity=0.5, keywords_coverage=[], timestamp=time.time()
            )
            
            facial_analysis = None
            voice_analysis = None
            
            result_idx = 1
            if facial_task:
                facial_analysis = results[result_idx] if isinstance(results[result_idx], FacialAnalysis) else FacialAnalysis(
                    emotion=EmotionState.CALM, confidence=0.5, eye_contact=0.5,
                    smile_intensity=0.5, attention_level=0.5, timestamp=time.time()
                )
                result_idx += 1
            
            if voice_task:
                voice_analysis = results[result_idx] if isinstance(results[result_idx], VoiceAnalysis) else VoiceAnalysis(
                    tone_confidence=0.5, speech_pace=150, volume_level=0.5,
                    clarity=0.5, emotional_tone="平静", pause_frequency=0.3, timestamp=time.time()
                )
            
            # 如果没有面部或语音分析，使用默认值
            if not facial_analysis:
                facial_analysis = FacialAnalysis(
                    emotion=EmotionState.CALM, confidence=0.5, eye_contact=0.5,
                    smile_intensity=0.5, attention_level=0.5, timestamp=time.time()
                )
            
            if not voice_analysis:
                voice_analysis = VoiceAnalysis(
                    tone_confidence=0.5, speech_pace=150, volume_level=0.5,
                    clarity=0.5, emotional_tone="平静", pause_frequency=0.3, timestamp=time.time()
                )
            
            # 计算综合得分
            overall_score = self._calculate_overall_score(
                content_analysis, facial_analysis, voice_analysis
            )
            
            # 确定参与度
            engagement_level = self._determine_engagement_level(
                facial_analysis, voice_analysis, content_analysis
            )
            
            # 生成建议和评价
            recommendations, strengths, improvements = await self._generate_feedback(
                content_analysis, facial_analysis, voice_analysis, overall_score
            )
            
            assessment = MultimodalAssessment(
                overall_score=overall_score,
                facial_analysis=facial_analysis,
                voice_analysis=voice_analysis,
                content_analysis=content_analysis,
                engagement_level=engagement_level,
                recommendations=recommendations,
                strengths=strengths,
                areas_for_improvement=improvements,
                timestamp=time.time()
            )
            
            # 添加到历史记录
            self.assessment_history.append(assessment)
            self.current_session["question_count"] += 1
            
            logger.info(f"✅ 多模态评估完成，综合得分: {overall_score:.2f}")
            return assessment
            
        except Exception as e:
            logger.error(f"❌ 综合评估失败: {e}")
            # 返回默认评估
            return self._create_default_assessment()
    
    def _calculate_overall_score(
        self,
        content: ContentAnalysis,
        facial: FacialAnalysis,
        voice: VoiceAnalysis
    ) -> float:
        """计算综合得分"""
        # 权重分配：内容50%，面部表情25%，语音25%
        content_score = (
            content.relevance_score * 0.3 +
            content.completeness * 0.3 +
            content.technical_accuracy * 0.2 +
            content.communication_clarity * 0.2
        )
        
        facial_score = (
            facial.confidence * 0.4 +
            facial.eye_contact * 0.3 +
            facial.attention_level * 0.3
        )
        
        voice_score = (
            voice.tone_confidence * 0.4 +
            voice.clarity * 0.3 +
            (1 - abs(voice.volume_level - 0.5) * 2) * 0.3  # 音量适中性
        )
        
        overall = content_score * 0.5 + facial_score * 0.25 + voice_score * 0.25
        return min(max(overall, 0.0), 1.0)
    
    def _determine_engagement_level(
        self,
        facial: FacialAnalysis,
        voice: VoiceAnalysis,
        content: ContentAnalysis
    ) -> EngagementLevel:
        """确定参与度级别"""
        engagement_score = (
            facial.attention_level * 0.4 +
            facial.eye_contact * 0.3 +
            voice.tone_confidence * 0.2 +
            content.relevance_score * 0.1
        )
        
        if engagement_score >= 0.8:
            return EngagementLevel.HIGH
        elif engagement_score >= 0.6:
            return EngagementLevel.MEDIUM
        elif engagement_score >= 0.4:
            return EngagementLevel.LOW
        else:
            return EngagementLevel.DISTRACTED
    
    async def _generate_feedback(
        self,
        content: ContentAnalysis,
        facial: FacialAnalysis,
        voice: VoiceAnalysis,
        overall_score: float
    ) -> Tuple[List[str], List[str], List[str]]:
        """生成反馈建议"""
        try:
            prompt = f"""
作为面试专家，基于以下评估数据生成反馈：

综合得分: {overall_score:.2f}
内容质量: 相关性{content.relevance_score:.2f}, 完整性{content.completeness:.2f}
面部表情: 自信度{facial.confidence:.2f}, 眼神交流{facial.eye_contact:.2f}
语音表现: 语调自信{voice.tone_confidence:.2f}, 清晰度{voice.clarity:.2f}

请生成：
1. 3-5条具体的改进建议
2. 2-3个表现优势
3. 2-3个需要改进的地方

以JSON格式返回：
{{
  "recommendations": ["建议1", "建议2"],
  "strengths": ["优势1", "优势2"],
  "improvements": ["改进点1", "改进点2"]
}}
"""

            client = await self.client_manager.get_healthy_client(provider_type="doubao")
            if client:
                response = await client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=600,
                    temperature=0.2
                )
                
                result_json = json.loads(response.choices[0].message.content)
                return (
                    result_json.get("recommendations", []),
                    result_json.get("strengths", []),
                    result_json.get("improvements", [])
                )
        except Exception as e:
            logger.error(f"❌ 反馈生成失败: {e}")
        
        # 默认反馈
        return (
            ["保持自信的表达", "注意眼神交流", "回答要更加具体"],
            ["回答相关性好", "表达较为清晰"],
            ["可以更加自信", "注意语速控制"]
        )
    
    def _create_default_assessment(self) -> MultimodalAssessment:
        """创建默认评估结果"""
        return MultimodalAssessment(
            overall_score=0.5,
            facial_analysis=FacialAnalysis(
                emotion=EmotionState.CALM, confidence=0.5, eye_contact=0.5,
                smile_intensity=0.5, attention_level=0.5, timestamp=time.time()
            ),
            voice_analysis=VoiceAnalysis(
                tone_confidence=0.5, speech_pace=150, volume_level=0.5,
                clarity=0.5, emotional_tone="平静", pause_frequency=0.3, timestamp=time.time()
            ),
            content_analysis=ContentAnalysis(
                relevance_score=0.5, completeness=0.5, technical_accuracy=0.5,
                communication_clarity=0.5, keywords_coverage=[], timestamp=time.time()
            ),
            engagement_level=EngagementLevel.MEDIUM,
            recommendations=["保持自然的表达"],
            strengths=["基本表现正常"],
            areas_for_improvement=["可以更加自信"],
            timestamp=time.time()
        )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话总结"""
        if not self.assessment_history:
            return {"message": "暂无评估数据"}
        
        # 计算平均分数
        avg_score = sum(a.overall_score for a in self.assessment_history) / len(self.assessment_history)
        
        # 统计情绪分布
        emotions = [a.facial_analysis.emotion.value for a in self.assessment_history]
        emotion_counts = {emotion: emotions.count(emotion) for emotion in set(emotions)}
        
        # 统计参与度
        engagements = [a.engagement_level.value for a in self.assessment_history]
        engagement_counts = {level: engagements.count(level) for level in set(engagements)}
        
        return {
            "session_duration": time.time() - self.current_session["start_time"],
            "total_questions": len(self.assessment_history),
            "average_score": avg_score,
            "emotion_distribution": emotion_counts,
            "engagement_distribution": engagement_counts,
            "score_trend": [a.overall_score for a in self.assessment_history],
            "recommendations_summary": self._summarize_recommendations()
        }
    
    def _summarize_recommendations(self) -> List[str]:
        """总结推荐建议"""
        all_recommendations = []
        for assessment in self.assessment_history:
            all_recommendations.extend(assessment.recommendations)
        
        # 统计频率最高的建议
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        # 返回前5个最常见的建议
        return sorted(recommendation_counts.keys(), 
                     key=lambda x: recommendation_counts[x], reverse=True)[:5]

# 全局实例
_multimodal_evaluator: Optional[MultimodalInterviewEvaluator] = None

def get_multimodal_evaluator() -> MultimodalInterviewEvaluator:
    """获取多模态评估器实例"""
    global _multimodal_evaluator
    
    if _multimodal_evaluator is None:
        _multimodal_evaluator = MultimodalInterviewEvaluator()
    
    return _multimodal_evaluator

# 便捷函数
async def evaluate_interview_response(
    question: str,
    answer: str,
    image_data: Optional[bytes] = None,
    audio_data: Optional[bytes] = None
) -> MultimodalAssessment:
    """便捷的面试回答评估函数"""
    evaluator = get_multimodal_evaluator()
    return await evaluator.comprehensive_assessment(question, answer, image_data, audio_data)

async def start_interview(position_type: str = "general", expected_skills: List[str] = None):
    """开始面试会话"""
    evaluator = get_multimodal_evaluator()
    evaluator.start_interview_session(position_type, expected_skills)

def get_interview_summary() -> Dict[str, Any]:
    """获取面试总结"""
    evaluator = get_multimodal_evaluator()
    return evaluator.get_session_summary() 