/**
 * 面试房间组件
 * 显示虚拟面试官、问题和答案输入区域
 */
import React, { useState, useEffect } from 'react';
import { useInterviewStore } from '../store/useInterviewStore';
import VirtualInterviewer from './VirtualInterviewer';

interface InterviewRoomProps {
  onEndInterview: () => void;
}

const InterviewRoom: React.FC<InterviewRoomProps> = ({ onEndInterview }) => {
  const {
    sessionId,
    currentQuestion,
    questionNumber,
    submitAnswer,
    isLoading,
    error,
    setError,
    isInterviewActive
  } = useInterviewStore();

  const [userAnswer, setUserAnswer] = useState('');
  const [isAnswering, setIsAnswering] = useState(false);

  // 调试：监控状态变化
  useEffect(() => {
    console.log('🔍 [InterviewRoom] 状态更新:', {
      sessionId,
      currentQuestion: currentQuestion?.substring(0, 50) + '...',
      questionNumber,
      isLoading,
      isInterviewActive,
      hasError: !!error
    });
  }, [sessionId, currentQuestion, questionNumber, isLoading, isInterviewActive, error]);

  // 提交答案
  const handleSubmitAnswer = async () => {
    if (!userAnswer.trim()) {
      setError('请输入您的回答');
      return;
    }

    console.log('🔍 [InterviewRoom] 开始提交答案:', {
      userAnswer: userAnswer.substring(0, 50) + '...',
      currentQuestionNumber: questionNumber
    });

    setIsAnswering(true);
    try {
      await submitAnswer(userAnswer);
      setUserAnswer('');
      console.log('🔍 [InterviewRoom] 答案提交成功');
    } catch (err) {
      console.error('提交答案失败:', err);
    } finally {
      setIsAnswering(false);
    }
  };

  // 结束面试
  const handleEndInterview = () => {
    onEndInterview();
  };

  if (!sessionId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-4">会话未初始化</h2>
          <p className="text-gray-600">请返回首页重新开始面试</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* 顶部状态栏 */}
      <div className="bg-gray-800 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-sm">面试进行中</span>
          </div>
          <div className="text-sm text-gray-300">
            问题 {questionNumber} | 会话ID: {sessionId.slice(-8)}
          </div>
        </div>
        
        <button
          onClick={handleEndInterview}
          className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition-colors"
        >
          结束面试
        </button>
      </div>

      <div className="flex flex-col md:flex-row h-[calc(100vh-80px)]">
        {/* 左侧：虚拟面试官和问题显示 */}
        <div className="w-full md:w-1/2 bg-gray-800 p-6 flex flex-col justify-center">
          <div className="mb-8">
            <VirtualInterviewer 
              currentQuestion={currentQuestion}
              isAsking={!isAnswering}
            />
          </div>
          <div className="bg-gray-700 rounded-lg p-6 shadow-xl">
            <h3 className="text-xl font-semibold mb-4 text-blue-300">
              面试官提问 #{questionNumber}
            </h3>
            <p className="text-gray-100 leading-relaxed text-lg">
              {currentQuestion || '正在加载问题，请稍候...'}
            </p>
          </div>
        </div>

        {/* 右侧：用户回答区域 */}
        <div className="w-full md:w-1/2 bg-gray-850 p-6 flex flex-col justify-center">
          <div className="bg-gray-750 rounded-xl p-8 shadow-2xl">
            <h4 className="text-xl font-semibold mb-6 text-green-300">
              您的回答
            </h4>
            
            <textarea
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              placeholder="请在此处输入您的回答。力求清晰、简洁、切中要点。"
              className="w-full h-48 bg-gray-700 border-2 border-gray-600 rounded-lg p-4 text-white placeholder-gray-400 resize-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 focus:outline-none transition-colors duration-200 text-base"
              disabled={isAnswering || isLoading}
            />

            <div className="flex justify-between items-center mt-6">
              <div className="text-sm text-gray-400">
                字数: {userAnswer.length}
              </div>
              
              <div className="flex space-x-4">
                <button
                  onClick={() => setUserAnswer('')}
                  className="px-6 py-3 bg-gray-600 hover:bg-gray-500 text-white font-medium rounded-lg transition-colors duration-200 disabled:opacity-50"
                  disabled={isAnswering || isLoading || userAnswer.length === 0}
                >
                  清空
                </button>
                
                <button
                  onClick={handleSubmitAnswer}
                  disabled={isAnswering || isLoading || !userAnswer.trim()}
                  className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105 shadow-md focus:outline-none focus:ring-4 focus:ring-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAnswering ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      提交中...
                    </span>
                  ) : '提交回答'}
                </button>
              </div>
            </div>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mt-6 bg-red-900/80 border border-red-700 text-red-100 px-4 py-3 rounded-lg shadow-md">
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InterviewRoom;