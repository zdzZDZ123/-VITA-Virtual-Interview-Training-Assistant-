"""
面试报告生成模块
生成结构化的面试反馈报告
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from models.api import FeedbackReport
from models.session import SessionState

logger = logging.getLogger(__name__)

class ReportGenerator:
    """面试报告生成器"""
    
    def __init__(self):
        logger.info("ReportGenerator 初始化成功")
    
    def generate_full_report(
        self, 
        session: SessionState, 
        visual_analysis: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        生成完整的面试反馈报告
        
        Args:
            session: 面试会话对象
            visual_analysis: 可选的视觉分析结果
            
        Returns:
            结构化的反馈报告字典
        """
        try:
            # 分析对话内容
            analysis = self._analyze_conversation(session.history)
            
            # 计算面试时长（分钟）
            if hasattr(session, 'created_at') and hasattr(session, 'updated_at'):
                duration_minutes = (session.updated_at - session.created_at).total_seconds() / 60
            else:
                duration_minutes = len(session.history) * 2  # 估算每个对话2分钟
            
            # 构建前端期望的数据结构
            report = {
                "session_id": session.session_id,
                "overall_score": self._calculate_overall_score(session.history),
                "content_analysis": {
                    "star_method_score": analysis["technical"].get("vocabulary_diversity", 70) / 100,
                    "keyword_matching": 0.75,  # 模拟值
                    "answer_clarity": analysis["technical"].get("avg_response_length", 10) / 20,
                    "response_relevance": 0.85  # 模拟值
                },
                "communication_analysis": {
                    "confidence_level": analysis["communication_score"] / 100,
                    "speech_pace": "moderate",
                    "filler_words_count": 3,
                    "emotional_tone": "professional"
                },
                "overall_impression": analysis["detailed"],
                "strengths": analysis["strengths"],
                "improvement_areas": analysis["improvements"],
                "practice_suggestions": [
                    "练习使用STAR方法结构化回答",
                    "准备更多具体的项目案例",
                    "注意控制回答时间在2-3分钟内",
                    "多使用数据和成果来支撑观点"
                ],
                "interview_duration_minutes": round(duration_minutes, 1)
            }
            
            # 如果有视觉分析数据，添加到报告中
            if visual_analysis:
                report["visual_analysis"] = {
                    "eye_contact_percentage": visual_analysis.get("gaze_contact_score", 0.7),
                    "posture_stability": visual_analysis.get("posture_stability", 0.8),
                    "gesture_appropriateness": visual_analysis.get("gesture_appropriateness", 0.75),
                    "facial_expressions": visual_analysis.get("emotion_confidence", {})
                }
            
            return report
            
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            # 返回默认报告以避免前端错误
            return {
                "session_id": session.session_id if session else "unknown",
                "overall_score": 70,
                "content_analysis": {
                    "star_method_score": 0.7,
                    "keyword_matching": 0.7,
                    "answer_clarity": 0.7,
                    "response_relevance": 0.7
                },
                "communication_analysis": {
                    "confidence_level": 0.7,
                    "speech_pace": "moderate",
                    "filler_words_count": 5,
                    "emotional_tone": "neutral"
                },
                "overall_impression": "面试完成，表现良好。",
                "strengths": ["完成了面试流程", "态度积极"],
                "improvement_areas": ["增加回答的深度", "提供更多具体例子"],
                "practice_suggestions": ["多练习常见面试问题", "准备个人经历的案例"],
                "interview_duration_minutes": 10
            }
    
    def _analyze_conversation(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        分析对话内容
        
        Args:
            history: 对话历史
            
        Returns:
            分析结果字典
        """
        try:
            # 提取用户回答
            user_responses = [h['content'] for h in history if h['role'] == 'user']
            
            if not user_responses:
                return self._empty_analysis()
            
            # 简单的文本分析 (在实际项目中会使用LLM进行深度分析)
            total_words = sum(len(response.split()) for response in user_responses)
            avg_response_length = total_words / len(user_responses) if user_responses else 0
            
            # 模拟分析结果
            analysis = {
                "strengths": self._identify_strengths(user_responses, avg_response_length),
                "improvements": self._identify_improvements(user_responses, avg_response_length),
                "detailed": self._generate_detailed_feedback(user_responses),
                "technical": {
                    "avg_response_length": round(avg_response_length, 1),
                    "total_responses": len(user_responses),
                    "vocabulary_diversity": self._calculate_vocabulary_diversity(user_responses)
                },
                "communication_score": self._calculate_communication_score(user_responses, avg_response_length)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"对话分析失败: {e}")
            return self._empty_analysis()
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """返回空的分析结果"""
        return {
            "strengths": ["参与了面试过程"],
            "improvements": ["增加回答的详细程度"],
            "detailed": "分析数据不足，建议进行更长时间的面试。",
            "technical": {
                "avg_response_length": 0,
                "total_responses": 0,
                "vocabulary_diversity": 0
            },
            "communication_score": 50
        }
    
    def _identify_strengths(self, responses: List[str], avg_length: float) -> List[str]:
        """识别优势"""
        strengths = []
        
        if avg_length > 20:
            strengths.append("回答详细充分")
        
        if len(responses) >= 5:
            strengths.append("积极参与面试互动")
        
        # 检查关键词
        combined_text = " ".join(responses).lower()
        if any(keyword in combined_text for keyword in ["经验", "项目", "团队", "学习"]):
            strengths.append("具有相关工作经验")
        
        if any(keyword in combined_text for keyword in ["挑战", "问题", "解决", "创新"]):
            strengths.append("具备问题解决能力")
        
        return strengths if strengths else ["参与了完整的面试流程"]
    
    def _identify_improvements(self, responses: List[str], avg_length: float) -> List[str]:
        """识别改进点"""
        improvements = []
        
        if avg_length < 10:
            improvements.append("可以提供更详细的回答")
        
        if len(responses) < 3:
            improvements.append("增加与面试官的互动")
        
        # 检查结构化回答
        combined_text = " ".join(responses).lower()
        if not any(keyword in combined_text for keyword in ["首先", "然后", "最后", "另外"]):
            improvements.append("使用更结构化的回答方式")
        
        if not any(keyword in combined_text for keyword in ["例如", "比如", "具体来说"]):
            improvements.append("增加具体例子和案例")
        
        return improvements if improvements else ["继续保持良好的表现"]
    
    def _generate_detailed_feedback(self, responses: List[str]) -> str:
        """生成详细反馈"""
        if not responses:
            return "未收集到足够的回答数据进行详细分析。"
        
        feedback_parts = [
            f"本次面试共收集到 {len(responses)} 个回答。",
            f"平均回答长度为 {sum(len(r.split()) for r in responses) / len(responses):.1f} 个词。"
        ]
        
        # 分析回答质量
        long_responses = [r for r in responses if len(r.split()) > 15]
        if long_responses:
            feedback_parts.append(f"其中 {len(long_responses)} 个回答较为详细，显示了良好的表达能力。")
        
        feedback_parts.append("建议在未来的面试中继续保持自信，并尝试用具体例子支持你的观点。")
        
        return " ".join(feedback_parts)
    
    def _calculate_vocabulary_diversity(self, responses: List[str]) -> float:
        """计算词汇多样性"""
        if not responses:
            return 0.0
        
        all_words = []
        for response in responses:
            words = response.lower().split()
            all_words.extend(words)
        
        if not all_words:
            return 0.0
        
        unique_words = set(all_words)
        diversity = len(unique_words) / len(all_words)
        return round(diversity * 100, 1)
    
    def _calculate_communication_score(self, responses: List[str], avg_length: float) -> int:
        """计算沟通评分"""
        base_score = 60
        
        # 基于回答长度调整
        if avg_length > 20:
            base_score += 15
        elif avg_length > 10:
            base_score += 10
        elif avg_length < 5:
            base_score -= 10
        
        # 基于回答数量调整
        if len(responses) > 5:
            base_score += 10
        elif len(responses) < 3:
            base_score -= 5
        
        # 基于词汇多样性调整
        diversity = self._calculate_vocabulary_diversity(responses)
        if diversity > 80:
            base_score += 10
        elif diversity < 50:
            base_score -= 5
        
        return max(0, min(100, base_score))
    
    def _calculate_overall_score(self, history: List[Dict[str, str]]) -> int:
        """计算总体评分"""
        user_responses = [h['content'] for h in history if h['role'] == 'user']
        
        if not user_responses:
            return 0
        
        # 基于多个维度计算分数
        communication_score = self._calculate_communication_score(
            user_responses, 
            sum(len(r.split()) for r in user_responses) / len(user_responses)
        )
        
        # 参与度评分
        participation_score = min(100, len(user_responses) * 20)
        
        # 综合评分
        overall_score = int((communication_score * 0.7 + participation_score * 0.3))
        
        return max(0, min(100, overall_score))
    
    def _integrate_visual_analysis(
        self, 
        report: FeedbackReport, 
        visual_analysis: Dict[str, Any]
    ) -> FeedbackReport:
        """
        整合视觉分析结果到报告中
        
        Args:
            report: 原始报告
            visual_analysis: 视觉分析结果
            
        Returns:
            整合后的报告
        """
        try:
            # 添加视觉分析的优势
            if "confident_moments" in visual_analysis:
                report.strengths.append("表现出良好的自信状态")
            
            if "good_eye_contact" in visual_analysis:
                report.strengths.append("保持了良好的眼神交流")
            
            # 添加视觉分析的改进建议
            if "posture_issues" in visual_analysis:
                report.improvement_areas.append("注意保持良好的坐姿")
            
            if "distraction_detected" in visual_analysis:
                report.improvement_areas.append("减少面试过程中的分心行为")
            
            # 更新技术评估
            if hasattr(report, 'technical_assessment') and isinstance(report.technical_assessment, dict):
                report.technical_assessment.update({
                    "visual_confidence": visual_analysis.get("confidence_score", 0),
                    "attention_score": visual_analysis.get("attention_score", 0),
                    "professional_appearance": visual_analysis.get("appearance_score", 0)
                })
            
            logger.info("视觉分析结果已整合到报告中")
            
        except Exception as e:
            logger.error(f"整合视觉分析失败: {e}")
        
        return report

# 全局实例
report_generator = ReportGenerator()