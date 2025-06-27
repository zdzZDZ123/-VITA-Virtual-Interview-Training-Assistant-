"""
API 请求和响应数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

# -----------------------------
# 请求模型
# -----------------------------
class StartSessionRequest(BaseModel):
    """开始面试会话请求"""
    job_description: str = Field(..., min_length=10, description="职位描述，至少10个字符")
    interview_type: str = Field(default="behavioral", description="面试类型：behavioral/technical/situational")
    
    class Config:
        schema_extra = {
            "example": {
                "job_description": "我们在寻找一位高级前端工程师，负责React应用开发...",
                "interview_type": "behavioral"
            }
        }

class SubmitAnswerRequest(BaseModel):
    """提交答案请求"""
    answer: str = Field(..., min_length=1, description="候选人的回答")
    
    class Config:
        schema_extra = {
            "example": {
                "answer": "我在上一家公司负责开发了一个电商平台的前端..."
            }
        }

# -----------------------------
# 响应模型
# -----------------------------
class StartSessionResponse(BaseModel):
    """开始面试会话响应"""
    session_id: str
    first_question: str
    interview_type: str
    created_at: datetime

class QuestionResponse(BaseModel):
    """面试问题响应"""
    question: str
    question_number: int = Field(description="当前问题序号")
    total_questions: Optional[int] = Field(default=None, description="预计总问题数")

class SessionStatusResponse(BaseModel):
    """会话状态响应"""
    session_id: str
    is_active: bool
    question_count: int
    duration_minutes: float
    last_activity: datetime

# -----------------------------
# 反馈报告相关模型
# -----------------------------
class ContentAnalysis(BaseModel):
    """内容分析结果"""
    star_method_score: float = Field(ge=0, le=1, description="STAR法则运用评分(0-1)")
    keyword_matching: float = Field(ge=0, le=1, description="关键词匹配度(0-1)")
    answer_clarity: float = Field(ge=0, le=1, description="回答清晰度(0-1)")
    response_relevance: float = Field(ge=0, le=1, description="回答相关性(0-1)")

class CommunicationAnalysis(BaseModel):
    """沟通分析结果"""
    confidence_level: float = Field(ge=0, le=1, description="自信程度(0-1)")
    speech_pace: str = Field(description="语速评估：slow/normal/fast")
    filler_words_count: int = Field(ge=0, description="口头禅/填充词次数")
    emotional_tone: str = Field(description="情绪基调：positive/neutral/negative")

class VisualAnalysis(BaseModel):
    """视觉分析结果"""
    eye_contact_percentage: float = Field(ge=0, le=1, description="眼神接触百分比(0-1)")
    posture_stability: float = Field(ge=0, le=1, description="坐姿稳定性(0-1)")
    facial_expressions: Dict[str, float] = Field(description="面部表情分析")
    gesture_appropriateness: float = Field(ge=0, le=1, description="手势得体度(0-1)")

class FeedbackReport(BaseModel):
    """完整反馈报告"""
    session_id: str
    overall_score: float = Field(ge=0, le=100, description="总体评分(0-100)")
    
    # 三大分析模块
    content_analysis: ContentAnalysis
    communication_analysis: CommunicationAnalysis
    visual_analysis: Optional[VisualAnalysis] = None
    
    # 文字报告
    overall_impression: str
    strengths: List[str]
    improvement_areas: List[str]
    practice_suggestions: List[str]
    
    # 元数据
    generated_at: datetime = Field(default_factory=datetime.now)
    interview_duration_minutes: float

class ErrorResponse(BaseModel):
    """错误响应"""
    error_code: str
    message: str
    details: Optional[str] = None