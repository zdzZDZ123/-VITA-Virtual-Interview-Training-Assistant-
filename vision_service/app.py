"""
VITA 视觉分析微服务
分析眼神接触、面部表情、姿态等非语言行为
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional
import cv2
import numpy as np
import mediapipe as mp
import io
from datetime import datetime

app = FastAPI(title="VITA Vision Service", version="0.1.0")

# 初始化 MediaPipe
mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# -----------------------------
# 数据模型
# -----------------------------
class VisualMetrics(BaseModel):
    """视觉分析结果"""
    gaze_contact_score: float = Field(ge=0, le=1, description="眼神接触评分 (0-1)")
    posture_stability: float = Field(ge=0, le=1, description="坐姿稳定性 (0-1)")
    emotion_confidence: Dict[str, float] = Field(description="情绪置信度")
    gesture_appropriateness: float = Field(ge=0, le=1, description="手势得体度 (0-1)")
    analysis_timestamp: datetime = Field(default_factory=datetime.now)

class AnalysisRequest(BaseModel):
    """分析请求参数"""
    frame_interval: int = Field(default=5, description="分析帧间隔")
    sensitivity: float = Field(default=0.5, ge=0, le=1, description="检测敏感度")

# -----------------------------
# 视觉分析核心函数
# -----------------------------
class VisionAnalyzer:
    def __init__(self):
        self.face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.pose = mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def analyze_gaze(self, face_landmarks, image_shape) -> float:
        """
        分析眼神接触 - 基于眼球位置相对于屏幕中心的偏移
        """
        if not face_landmarks:
            return 0.0
        
        # 获取眼部关键点 (简化版本)
        left_eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        right_eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        
        h, w = image_shape[:2]
        screen_center = np.array([w/2, h/2])
        
        # 计算双眼中心点
        left_eye_center = np.mean([
            [face_landmarks.landmark[i].x * w, face_landmarks.landmark[i].y * h] 
            for i in left_eye_indices[:4]  # 取前4个点简化计算
        ], axis=0)
        
        right_eye_center = np.mean([
            [face_landmarks.landmark[i].x * w, face_landmarks.landmark[i].y * h] 
            for i in right_eye_indices[:4]
        ], axis=0)
        
        eyes_center = (left_eye_center + right_eye_center) / 2
        
        # 计算与屏幕中心的距离
        distance = np.linalg.norm(eyes_center - screen_center)
        max_distance = min(w, h) * 0.3  # 30% 屏幕尺寸作为最大距离
        
        # 转换为评分 (距离越近评分越高)
        gaze_score = max(0, 1 - (distance / max_distance))
        return min(1.0, gaze_score)
    
    def analyze_emotion(self, face_landmarks) -> Dict[str, float]:
        """
        简化的情绪分析 - 基于面部关键点几何关系
        """
        if not face_landmarks:
            return {"neutral": 1.0, "confident": 0.0, "nervous": 0.0}
        
        # 嘴角点
        mouth_left = face_landmarks.landmark[61]  # 左嘴角
        mouth_right = face_landmarks.landmark[291]  # 右嘴角
        mouth_center = face_landmarks.landmark[13]  # 嘴部中心
        
        # 眉毛点
        left_eyebrow = face_landmarks.landmark[70]
        right_eyebrow = face_landmarks.landmark[300]
        
        # 计算嘴角弧度 (微笑检测)
        mouth_curve = (mouth_left.y + mouth_right.y) / 2 - mouth_center.y
        smile_confidence = max(0, -mouth_curve * 10)  # 负值表示上扬
        
        # 计算眉毛高度 (自信度检测)
        eyebrow_height = -(left_eyebrow.y + right_eyebrow.y) / 2
        confidence_score = max(0, min(1, eyebrow_height * 5))
        
        # 归一化情绪评分
        total = smile_confidence + confidence_score + 0.3  # 基础 neutral 分
        return {
            "confident": confidence_score / total,
            "positive": smile_confidence / total, 
            "neutral": 0.3 / total,
            "nervous": max(0, 1 - (confidence_score + smile_confidence))
        }
    
    def analyze_posture(self, pose_landmarks) -> float:
        """
        分析坐姿稳定性 - 基于肩膀、头部位置
        """
        if not pose_landmarks:
            return 0.5  # 默认中等稳定性
        
        # 肩膀关键点
        left_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # 头部关键点
        nose = pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
        
        # 计算肩膀水平度
        shoulder_slope = abs(left_shoulder.y - right_shoulder.y)
        stability_score = max(0, 1 - shoulder_slope * 20)  # 水平度越好评分越高
        
        # 头部位置检查 (相对于肩膀中心)
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        head_offset = abs(nose.x - shoulder_center_x)
        head_stability = max(0, 1 - head_offset * 10)
        
        return (stability_score + head_stability) / 2

    def analyze_frame(self, image: np.ndarray) -> VisualMetrics:
        """分析单帧图像"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 面部分析
        face_results = self.face_mesh.process(rgb_image)
        gaze_score = 0.0
        emotions = {"neutral": 1.0, "confident": 0.0, "nervous": 0.0}
        
        if face_results.multi_face_landmarks:
            face_landmarks = face_results.multi_face_landmarks[0]
            gaze_score = self.analyze_gaze(face_landmarks, image.shape)
            emotions = self.analyze_emotion(face_landmarks)
        
        # 姿态分析
        pose_results = self.pose.process(rgb_image)
        posture_score = 0.5
        
        if pose_results.pose_landmarks:
            posture_score = self.analyze_posture(pose_results.pose_landmarks)
        
        return VisualMetrics(
            gaze_contact_score=gaze_score,
            posture_stability=posture_score,
            emotion_confidence=emotions,
            gesture_appropriateness=0.8  # 暂时固定值，后续可扩展手势分析
        )

# 全局分析器实例
analyzer = VisionAnalyzer()

# -----------------------------
# API 端点
# -----------------------------
@app.post("/analyze", response_model=VisualMetrics)
async def analyze_video_frame(file: UploadFile = File(...)):
    """
    分析上传的图像帧
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="仅支持图像文件")
    
    try:
        # 读取图像
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="无法解析图像")
        
        # 分析图像
        metrics = analyzer.analyze_frame(image)
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "VITA Vision Service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 