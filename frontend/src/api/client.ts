/**
 * VITA API 客户端
 * 封装后端和视觉服务的API调用
 */
import axios from 'axios';

// API 基础配置
// 开发环境直接连接后端，生产环境使用环境变量或默认值
const API_BASE_URL = import.meta.env.DEV 
  ? 'http://localhost:8000' // 开发环境直接连接后端
  : (import.meta.env.VITE_API_URL || 'http://localhost:8000');
  
const VISION_API_URL = import.meta.env.VITE_VISION_API_URL || 'http://localhost:8000';

// 创建 Axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const visionClient = axios.create({
  baseURL: VISION_API_URL,
  timeout: 30000,
});

// -----------------------------
// 类型定义
// -----------------------------
export interface StartSessionRequest {
  job_description: string;
  interview_type?: 'behavioral' | 'technical' | 'situational';
}

export interface StartSessionResponse {
  session_id: string;
  first_question: string;
  interview_type: string;
  created_at: string;
}

export interface SubmitAnswerRequest {
  answer: string;
}

export interface QuestionResponse {
  question: string;
  question_number: number;
  total_questions?: number;
}

export interface FeedbackResponse {
  report: string;
  session_id: string;
}

export interface VisualMetrics {
  gaze_contact_score: number;
  posture_stability: number;
  emotion_confidence: Record<string, number>;
  gesture_appropriateness: number;
  analysis_timestamp: string;
}

// -----------------------------
// API 函数
// -----------------------------

/**
 * 开始新的面试会话
 */
export const startSession = async (request: StartSessionRequest): Promise<StartSessionResponse> => {
  const response = await apiClient.post('/session/start', request);
  return response.data;
};

/**
 * 提交答案并获取下一个问题
 */
export const submitAnswer = async (sessionId: string, request: SubmitAnswerRequest): Promise<QuestionResponse> => {
  const response = await apiClient.post(`/session/${sessionId}/answer`, request);
  return response.data;
};

/**
 * 获取面试反馈报告
 */
export const getFeedback = async (sessionId: string): Promise<FeedbackResponse> => {
  const response = await apiClient.get(`/session/${sessionId}/feedback`);
  return response.data;
};

/**
 * 健康检查
 */
export const healthCheck = async (): Promise<{ status: string }> => {
  const response = await apiClient.get('/health');
  return response.data;
};

/**
 * 分析视频帧
 */
export const analyzeFrame = async (imageBlob: Blob): Promise<VisualMetrics> => {
  const formData = new FormData();
  formData.append('file', imageBlob, 'frame.jpg');
  
  const response = await visionClient.post('/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * 视觉服务健康检查
 */
export const visionHealthCheck = async (): Promise<{ status: string }> => {
  const response = await visionClient.get('/health');
  return response.data;
};

// 错误处理拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

visionClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Vision API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);