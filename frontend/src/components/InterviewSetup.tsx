/**
 * 面试设置组件 - 现代化设计
 * 用户输入职位描述和选择面试类型
 */
import React, { useState } from 'react';
import { AvatarSelector } from './digital-human/AvatarSelector';
import { getAvatarModel } from '../config/avatarConfig';

interface InterviewSetupProps {
  onStart: (settings: {
    jobDescription: string,
    interviewType: 'behavioral' | 'technical' | 'situational',
    avatarModel?: string,
    mode: 'text' | 'voice' | 'digital-human'
  }) => void;
  onError?: () => void;
}

const InterviewSetup: React.FC<InterviewSetupProps> = ({ onStart, onError }) => {
  const [jobDescription, setJobDescription] = useState('');
  const [interviewType, setInterviewType] = useState<'behavioral' | 'technical' | 'situational'>('technical');
  const [selectedAvatarId, setSelectedAvatarId] = useState('simple');
  const [isStarting, setIsStarting] = useState(false);
  const [showError, setShowError] = useState(false);
  const [showAvatarSelector, setShowAvatarSelector] = useState(false);
  
  React.useEffect(() => {
    if (onError) {
      setIsStarting(false);
    }
  }, [onError]);

  const handleStart = (mode: 'text' | 'voice' | 'digital-human') => {
    if (!jobDescription.trim()) {
      setShowError(true);
      setTimeout(() => setShowError(false), 3000);
      return;
    }
    
    setIsStarting(true);
    setShowError(false);
    
    onStart({
      jobDescription,
      interviewType,
      mode,
      avatarModel: mode === 'digital-human' ? selectedAvatarId : 'demo'
    });
  };

  const interviewTypeOptions = [
    { 
      value: 'behavioral', 
      label: '行为面试', 
      description: '基于过往经历和行为模式的深度评估',
      icon: '🧠'
    },
    { 
      value: 'technical', 
      label: '技术面试', 
      description: '专业技能与解决问题能力的全面考察',
      icon: '⚡'
    },
    { 
      value: 'situational', 
      label: '情景面试', 
      description: '模拟真实工作场景的应变能力测试',
      icon: '🎯'
    },
  ] as const;

  const selectedAvatar = getAvatarModel(selectedAvatarId);

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden">
      {/* 背景动画效果 */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-green-600/20 to-blue-600/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-purple-600/10 to-pink-600/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      <div className="relative z-10 max-w-4xl mx-auto px-6 py-16">
        {/* 头部标题区域 */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl mb-8">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          
          <h1 className="text-6xl font-bold bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent mb-6 tracking-tight">
            VITA
          </h1>
          
          <p className="text-2xl text-gray-300 mb-4 font-light">
            Virtual Interview & Training Assistant
          </p>
          
          <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
            基于先进AI技术的智能面试训练平台，为您提供个性化的面试体验与专业反馈
          </p>
        </div>

        {/* 主要内容区域 */}
        <div className="bg-gray-900/50 backdrop-blur-xl border border-gray-800 rounded-3xl p-8 shadow-2xl">
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-2">开始您的AI面试体验</h2>
            <p className="text-gray-400">选择面试类型并描述目标职位，AI面试官将为您量身定制面试问题</p>
          </div>
          
          {/* 面试类型选择 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">选择面试类型</label>
            <div className="grid md:grid-cols-3 gap-4">
              {interviewTypeOptions.map((option) => (
                <label
                  key={option.value}
                  className={`relative border rounded-lg p-4 cursor-pointer transition-colors ${
                    interviewType === option.value
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-gray-600 hover:border-gray-500 bg-gray-800/50'
                  }`}
                >
                  <input
                    type="radio"
                    name="interviewType"
                    value={option.value}
                    checked={interviewType === option.value}
                    onChange={(e) => setInterviewType(e.target.value as typeof interviewType)}
                    className="sr-only"
                  />
                  <div className="flex items-center">
                    <div className={`w-4 h-4 rounded-full border-2 mr-3 ${
                      interviewType === option.value ? 'border-blue-500 bg-blue-500' : 'border-gray-400'
                    }`}>
                      {interviewType === option.value && (
                        <div className="w-2 h-2 rounded-full bg-white mx-auto mt-0.5"></div>
                      )}
                    </div>
                    <div>
                      <div className="font-medium text-white">{option.label}</div>
                      <div className="text-sm text-gray-400">{option.description}</div>
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 数字人面试官选择 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">选择数字人面试官</label>
            
            {/* 当前选择的数字人预览 */}
            <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-white">
                      {selectedAvatar.name}
                    </h4>
                    <p className="text-sm text-gray-400">
                      {selectedAvatar.description}
                    </p>
                    <div className="flex items-center space-x-2 mt-2">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
                        {selectedAvatar.appearance?.style || '专业'}
                      </span>
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        {selectedAvatar.quality}
                      </span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setShowAvatarSelector(!showAvatarSelector)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  {showAvatarSelector ? '收起选择' : '更换面试官'}
                </button>
              </div>
            </div>
            
            {/* 数字人选择器 */}
            {showAvatarSelector && (
              <div className="bg-gray-800/30 border border-gray-700 rounded-lg p-4 max-h-96 overflow-y-auto">
                <AvatarSelector
                  currentAvatarId={selectedAvatarId}
                  onAvatarChange={(avatarId) => {
                    setSelectedAvatarId(avatarId);
                    setShowAvatarSelector(false);
                  }}
                  interviewType={interviewType}
                  deviceType="desktop"
                  className=""
                />
              </div>
            )}
          </div>

          {/* 职位描述输入 */}
          <div className="mb-6">
            <label htmlFor="jobDescription" className="block text-sm font-medium text-gray-300 mb-2">
              职位描述 *
            </label>
            <textarea
              id="jobDescription"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="请粘贴您要应聘的职位描述，AI面试官将根据此信息进行针对性提问..."
              className="w-full h-32 px-3 py-2 bg-gray-800/50 border border-gray-600 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-white placeholder-gray-400"
              disabled={isStarting}
            />
            <div className="mt-2 text-sm text-gray-400">
              字符数: {jobDescription.length} (建议至少100字符)
            </div>
          </div>

          {/* 错误提示 */}
          {showError && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
              <p className="text-red-300 text-sm">请输入职位描述后再开始面试</p>
            </div>
          )}

          {/* 开始按钮 */}
          <div className="flex flex-col items-center space-y-4">
            <button
              onClick={() => handleStart('text')}
              disabled={isStarting || jobDescription.length < 10}
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors text-lg w-full max-w-xs"
            >
              {isStarting ? '正在创建面试...' : '开始文本面试'}
            </button>

            <button
              type="button"
              onClick={() => handleStart('voice')}
              disabled={isStarting || jobDescription.length < 10}
              className="px-8 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors text-lg w-full max-w-xs"
            >
              开始语音面试
            </button>

            <button
              type="button"
              onClick={() => handleStart('digital-human')}
              disabled={isStarting || jobDescription.length < 10}
              className="px-8 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors text-lg w-full max-w-xs"
            >
              开始数字人面试
            </button>
          </div>

          {/* 温馨提示 */}
          <div className="mt-8 bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
            <div className="flex">
              <svg className="w-5 h-5 text-amber-400 mt-0.5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h4 className="text-sm font-medium text-amber-300 mb-1">面试前准备</h4>
                <ul className="text-sm text-amber-200 space-y-1">
                  <li>• 确保网络连接稳定，摄像头和麦克风工作正常</li>
                  <li>• 选择安静、光线充足的环境进行面试</li>
                  <li>• 建议使用STAR法则回答问题（情境、任务、行动、结果）</li>
                  <li>• 数字人面试支持实时表情识别和互动反馈</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewSetup;