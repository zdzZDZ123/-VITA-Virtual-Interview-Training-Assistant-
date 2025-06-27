/**
 * 反馈报告组件
 * 显示面试分析结果和建议
 */
import React, { useState, useEffect } from 'react';
import { useInterviewStore } from '../store/useInterviewStore';

interface FeedbackReportProps {
  onBackToHome: () => void;
}

interface FeedbackData {
  session_id: string;
  overall_score: number;
  content_analysis: {
    star_method_score: number;
    keyword_matching: number;
    answer_clarity: number;
    response_relevance: number;
  };
  communication_analysis: {
    confidence_level: number;
    speech_pace: string;
    filler_words_count: number;
    emotional_tone: string;
  };
  visual_analysis?: {
    eye_contact_percentage: number;
    posture_stability: number;
    gesture_appropriateness: number;
    facial_expressions: Record<string, number>;
  };
  overall_impression: string;
  strengths: string[];
  improvement_areas: string[];
  practice_suggestions: string[];
  interview_duration_minutes: number;
}

const FeedbackReport: React.FC<FeedbackReportProps> = ({ onBackToHome }) => {
  const [feedbackData, setFeedbackData] = useState<FeedbackData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { sessionId } = useInterviewStore();

  useEffect(() => {
    const fetchFeedback = async () => {
      if (!sessionId) {
        setError('会话信息丢失');
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`http://localhost:8000/session/${sessionId}/feedback`);
        
        if (!response.ok) {
          throw new Error('获取反馈报告失败');
        }

        const data = await response.json();
        setFeedbackData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取反馈失败');
      } finally {
        setIsLoading(false);
      }
    };

    fetchFeedback();
  }, [sessionId]);

  const ScoreBar: React.FC<{ score: number; label: string; color?: string }> = ({ 
    score, 
    label, 
    color = 'blue' 
  }) => (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm text-gray-600">{Math.round(score * 100)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`bg-${color}-500 h-2 rounded-full transition-all duration-500`}
          style={{ width: `${score * 100}%` }}
        ></div>
      </div>
    </div>
  );

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 0.8) return '优秀';
    if (score >= 0.6) return '良好';
    if (score >= 0.4) return '一般';
    return '需改进';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-700">正在生成反馈报告...</h2>
          <p className="text-gray-500 mt-2">AI正在分析您的面试表现，请稍候</p>
        </div>
      </div>
    );
  }

  if (error || !feedbackData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">生成报告失败</h2>
          <p className="text-gray-500 mb-6">{error}</p>
          <button
            onClick={onBackToHome}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* 页面标题和操作 */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">面试反馈报告</h1>
          <p className="text-gray-600 mb-6">
            面试时长: {Math.round(feedbackData.interview_duration_minutes)} 分钟 | 
            会话ID: {feedbackData.session_id.slice(-8)}
          </p>
          
          <button
            onClick={onBackToHome}
            className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
          >
            重新开始面试
          </button>
        </div>

        {/* 总体评分卡片 */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8 text-center">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">总体评分</h2>
          <div className={`text-6xl font-bold mb-4 ${getScoreColor(feedbackData.overall_score / 100)}`}>
            {Math.round(feedbackData.overall_score)}
          </div>
          <div className={`text-xl font-medium ${getScoreColor(feedbackData.overall_score / 100)}`}>
            {getScoreLabel(feedbackData.overall_score / 100)}
          </div>
          <p className="text-gray-600 mt-4 max-w-2xl mx-auto">
            {feedbackData.overall_impression}
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* 内容分析 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
              <svg className="w-6 h-6 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              内容分析
            </h3>
            
            <ScoreBar 
              score={feedbackData.content_analysis.star_method_score} 
              label="STAR方法运用" 
              color="blue"
            />
            <ScoreBar 
              score={feedbackData.content_analysis.keyword_matching} 
              label="关键词匹配度" 
              color="green"
            />
            <ScoreBar 
              score={feedbackData.content_analysis.answer_clarity} 
              label="回答清晰度" 
              color="purple"
            />
            <ScoreBar 
              score={feedbackData.content_analysis.response_relevance} 
              label="回答相关性" 
              color="indigo"
            />
          </div>

          {/* 沟通分析 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
              <svg className="w-6 h-6 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              沟通分析
            </h3>
            
            <ScoreBar 
              score={feedbackData.communication_analysis.confidence_level} 
              label="自信程度" 
              color="green"
            />
            
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">语速节奏</span>
                <span className="text-sm text-gray-600 capitalize">
                  {feedbackData.communication_analysis.speech_pace}
                </span>
              </div>
            </div>
            
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">填充词使用</span>
                <span className="text-sm text-gray-600">
                  {feedbackData.communication_analysis.filler_words_count} 次
                </span>
              </div>
            </div>
            
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">情绪基调</span>
                <span className="text-sm text-gray-600 capitalize">
                  {feedbackData.communication_analysis.emotional_tone}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 视觉分析（如果有数据） */}
        {feedbackData.visual_analysis && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h3 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
              <svg className="w-6 h-6 text-purple-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              视觉行为分析
            </h3>
            
            <div className="grid md:grid-cols-3 gap-6">
              <ScoreBar 
                score={feedbackData.visual_analysis.eye_contact_percentage} 
                label="眼神接触" 
                color="purple"
              />
              <ScoreBar 
                score={feedbackData.visual_analysis.posture_stability} 
                label="坐姿稳定性" 
                color="indigo"
              />
              <ScoreBar 
                score={feedbackData.visual_analysis.gesture_appropriateness} 
                label="手势得体度" 
                color="pink"
              />
            </div>
          </div>
        )}

        {/* 详细反馈 */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* 优势亮点 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-green-700 mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              优势亮点
            </h3>
            <ul className="space-y-3">
              {feedbackData.strengths.map((strength, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-green-500 mr-2 mt-1">•</span>
                  <span className="text-gray-700">{strength}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* 改进建议 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-orange-700 mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              改进建议
            </h3>
            <ul className="space-y-3">
              {feedbackData.improvement_areas.map((area, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-orange-500 mr-2 mt-1">•</span>
                  <span className="text-gray-700">{area}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* 练习建议 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-blue-700 mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              练习建议
            </h3>
            <ul className="space-y-3">
              {feedbackData.practice_suggestions.map((suggestion, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-blue-500 mr-2 mt-1">•</span>
                  <span className="text-gray-700">{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* 底部操作按钮 */}
        <div className="text-center mt-8">
          <button
            onClick={onBackToHome}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg transition-colors text-lg font-medium"
          >
            开始新的面试练习
          </button>
        </div>
      </div>
    </div>
  );
};

export default FeedbackReport; 