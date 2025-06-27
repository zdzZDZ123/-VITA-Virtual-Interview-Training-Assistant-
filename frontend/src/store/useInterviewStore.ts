/**
 * VITA 面试状态管理
 * 使用 Zustand 管理全局状态
 */
import { create } from 'zustand';
import type { VisualMetrics, StartSessionResponse } from '../api/client';
import { startSession as apiStartSession, submitAnswer as apiSubmitAnswer } from '../api/client';

// -----------------------------
// 类型定义
// -----------------------------
export interface InterviewSession {
  session_id: string;
  interview_type: 'behavioral' | 'technical' | 'situational' | 'voice';
  job_description: string;
  created_at: string;
  is_active: boolean;
  avatar_model?: string; // 数字人模型选择
}

export interface ConversationItem {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  question_number?: number;
}

export interface FeedbackReport {
  session_id: string;
  feedback: string;
  visual_analysis?: Record<string, unknown>;
}

export interface InterviewState {
  // 会话信息
  session: InterviewSession | null;
  sessionId: string | null;
  conversation: ConversationItem[];
  currentQuestion: string;
  questionNumber: number;
  
  // 用户输入
  currentAnswer: string;
  isSubmitting: boolean;
  isLoading: boolean;
  
  // 视觉分析
  visualMetrics: VisualMetrics[];
  isAnalyzing: boolean;
  
  // UI 状态
  isInterviewActive: boolean;
  showFeedback: boolean;
  error: string | null;
  
  // 反馈报告
  feedbackReport: FeedbackReport | null;
  
  // Actions
  setSession: (session: InterviewSession) => void;
  setCurrentQuestion: (question: string, questionNumber?: number) => void;
  setCurrentAnswer: (answer: string) => void;
  addConversationItem: (item: ConversationItem) => void;
  addVisualMetrics: (metrics: VisualMetrics) => void;
  
  setSubmitting: (submitting: boolean) => void;
  setAnalyzing: (analyzing: boolean) => void;
  setInterviewActive: (active: boolean) => void;
  setShowFeedback: (show: boolean) => void;
  setError: (error: string | null) => void;
  
  // 新增方法
  startSession: (params: { job_description: string, interview_type: 'behavioral' | 'technical' | 'situational' }) => Promise<StartSessionResponse>;
  submitAnswer: (answer: string) => Promise<void>;
  clearSession: () => void;
  
  resetInterview: () => void;
}

// -----------------------------
// Zustand Store
// -----------------------------
export const useInterviewStore = create<InterviewState>((set, get) => ({
  // Initial state
  session: null,
  sessionId: null,
  conversation: [],
  currentQuestion: '',
  questionNumber: 0,
  currentAnswer: '',
  isSubmitting: false,
  isLoading: false,
  
  visualMetrics: [],
  isAnalyzing: false,
  
  isInterviewActive: false,
  showFeedback: false,
  error: null,
  feedbackReport: null,
  
  // Actions
  setSession: (session) => set({ 
    session, 
    sessionId: session.session_id 
  }),
  
  setCurrentQuestion: (question, questionNumber = 0) => {
    set({ 
      currentQuestion: question,
      questionNumber: questionNumber 
    });
    
    // 添加到对话历史
    const conversationItem: ConversationItem = {
      role: 'assistant',
      content: question,
      timestamp: new Date(),
      question_number: questionNumber,
    };
    
    set((state) => ({
      conversation: [...state.conversation, conversationItem]
    }));
  },
  
  setCurrentAnswer: (answer) => set({ currentAnswer: answer }),
  
  addConversationItem: (item) => set((state) => ({
    conversation: [...state.conversation, item]
  })),
  
  addVisualMetrics: (metrics) => set((state) => ({
    visualMetrics: [...state.visualMetrics, metrics]
  })),
  
  setSubmitting: (submitting) => set({ isSubmitting: submitting }),
  setAnalyzing: (analyzing) => set({ isAnalyzing: analyzing }),
  setInterviewActive: (active) => set({ isInterviewActive: active }),
  setShowFeedback: (show) => set({ showFeedback: show }),
  setError: (error) => set({ error }),
  
  // 开始面试会话
  startSession: async (params: { job_description: string, interview_type: 'behavioral' | 'technical' | 'situational' }) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await apiStartSession(params);
      
      // 创建session对象
      const session: InterviewSession = {
        session_id: data.session_id,
        interview_type: params.interview_type,
        job_description: params.job_description,
        created_at: new Date().toISOString(),
        is_active: true
      };
      
      set({
        session,
        sessionId: data.session_id,
        currentQuestion: data.first_question,
        questionNumber: 1,
        isInterviewActive: true,
      });
      
      return data;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '创建会话失败' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // 提交答案的方法
  submitAnswer: async (answer: string) => {
    const state = get();
    if (!state.sessionId) {
      throw new Error('会话未初始化');
    }

    console.log('🔍 [DEBUG] 开始提交答案，当前完整状态:', {
      sessionId: state.sessionId,
      currentQuestion: state.currentQuestion,
      questionNumber: state.questionNumber,
      isInterviewActive: state.isInterviewActive,
      isLoading: state.isLoading,
      conversationLength: state.conversation.length
    });

    set({ isLoading: true, error: null });
    
    try {
      // 调用API提交答案
      const data = await apiSubmitAnswer(state.sessionId, { answer });
      
      console.log('🔍 [DEBUG] API返回数据:', data);
      
      // 添加用户回答到对话历史
      const userItem: ConversationItem = {
        role: 'user',
        content: answer,
        timestamp: new Date(),
      };
      
      // 添加AI问题到对话历史
      const assistantItem: ConversationItem = {
        role: 'assistant',
        content: data.question,
        timestamp: new Date(),
        question_number: data.question_number,
      };
      
      console.log('🔍 [DEBUG] 准备更新状态:', {
        newQuestion: data.question,
        newQuestionNumber: data.question_number,
        userItem,
        assistantItem
      });
      
      set((prevState) => {
        const newFields: Partial<InterviewState> = {
          conversation: [...prevState.conversation, userItem, assistantItem],
        currentQuestion: data.question,
        questionNumber: data.question_number,
          currentAnswer: '', // 清空当前回答
          isLoading: false, // 确保加载状态重置
        };
        const merged: InterviewState = { ...prevState, ...newFields } as InterviewState;
        
        console.log('🔍 [DEBUG] 状态更新后，完整状态检查:', {
          currentQuestion: merged.currentQuestion,
          questionNumber: merged.questionNumber,
          conversationLength: merged.conversation.length,
          isInterviewActive: merged.isInterviewActive,
          isLoading: merged.isLoading,
          sessionId: merged.sessionId
        });
        
        return merged;
      });
      
    } catch (error) {
      console.error('❌ [DEBUG] 提交答案失败:', error);
      set({ error: error instanceof Error ? error.message : '提交失败' });
      throw error;
    }
  },
  
  clearSession: () => set({
    session: null,
    sessionId: null,
    conversation: [],
    currentQuestion: '',
    questionNumber: 0,
    currentAnswer: '',
    isSubmitting: false,
    isLoading: false,
    visualMetrics: [],
    isAnalyzing: false,
    isInterviewActive: false,
    showFeedback: false,
    error: null,
    feedbackReport: null,
  }),
  
  resetInterview: () => set({
    session: null,
    sessionId: null,
    conversation: [],
    currentQuestion: '',
    questionNumber: 0,
    currentAnswer: '',
    isSubmitting: false,
    isLoading: false,
    visualMetrics: [],
    isAnalyzing: false,
    isInterviewActive: false,
    showFeedback: false,
    error: null,
    feedbackReport: null,
  }),
}));

// -----------------------------
// Selector hooks (便利函数)
// -----------------------------
export const useSession = () => useInterviewStore((state) => state.session);
export const useConversation = () => useInterviewStore((state) => state.conversation);
export const useCurrentQuestion = () => useInterviewStore((state) => state.currentQuestion);
export const useCurrentAnswer = () => useInterviewStore((state) => state.currentAnswer);
export const useVisualMetrics = () => useInterviewStore((state) => state.visualMetrics);
export const useInterviewStatus = () => useInterviewStore((state) => ({
  isActive: state.isInterviewActive,
  isSubmitting: state.isSubmitting,
  isAnalyzing: state.isAnalyzing,
  showFeedback: state.showFeedback,
  error: state.error,
}));

// 计算统计数据的选择器
export const useInterviewStats = () => useInterviewStore((state) => {
  const questionCount = state.conversation.filter(item => item.role === 'assistant').length;
  const answerCount = state.conversation.filter(item => item.role === 'user').length;
  
  // 计算平均视觉指标
  const avgGazeScore = state.visualMetrics.length > 0 
    ? state.visualMetrics.reduce((sum, m) => sum + m.gaze_contact_score, 0) / state.visualMetrics.length 
    : 0;
    
  const avgPostureScore = state.visualMetrics.length > 0
    ? state.visualMetrics.reduce((sum, m) => sum + m.posture_stability, 0) / state.visualMetrics.length
    : 0;
  
  return {
    questionCount,
    answerCount,
    metricsCount: state.visualMetrics.length,
    avgGazeScore,
    avgPostureScore,
  };
});