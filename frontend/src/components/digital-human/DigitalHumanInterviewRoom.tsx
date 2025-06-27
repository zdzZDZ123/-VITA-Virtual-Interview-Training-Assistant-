import React, { useState, useEffect, useRef } from 'react';
import { DigitalHumanView } from './DigitalHumanView';
import { useInterviewStore } from '../../store/useInterviewStore';
import { getAvatarModel } from '../../config/avatarConfig';
import api from '../../utils/api';

interface Message {
  role: 'interviewer' | 'candidate';
  content: string;
  timestamp: Date;
  audioUrl?: string;
}

export const DigitalHumanInterviewRoom: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentAudioUrl, setCurrentAudioUrl] = useState<string>('');
  const [digitalHumanExpression, setDigitalHumanExpression] = useState('neutral');
  const [digitalHumanAction, setDigitalHumanAction] = useState('idle');
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [apiError, setApiError] = useState<string>('');
  const [interviewProgress, setInterviewProgress] = useState({ current: 0, total: 5 });
  const [showWebcam, setShowWebcam] = useState(false);
  const [webcamStream, setWebcamStream] = useState<MediaStream | null>(null);
  const [recordingTimeout, setRecordingTimeout] = useState<NodeJS.Timeout | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const webcamVideoRef = useRef<HTMLVideoElement>(null);
  const session = useInterviewStore((state) => state.session);
  const sessionId = useInterviewStore((state) => state.sessionId);
  const jobDescription = session?.job_description || '';
  const interviewType = session?.interview_type || 'behavioral';
  const avatarModel = session?.avatar_id || 'simple';
  
  const getInitialQuestion = () => {
    const questions = {
      'technical': '请解释一下 JavaScript 中的事件循环 (event loop) 。',
      'behavioral': '请简单介绍一下您自己，包括您的教育背景和工作经验。',
      'situational': '如果您在项目中遇到了技术难题，您会如何解决？'
    };
    return questions[interviewType as keyof typeof questions] || questions.technical;
  };


  
  // Initialize interview
  useEffect(() => {
    const initializeInterview = async () => {
      setConnectionStatus('connecting');
      
      try {
        // 初始化摄像头
        await initializeWebcam();
        
        // 模拟连接成功
        setTimeout(() => {
          setConnectionStatus('connected');
          setInterviewProgress({ current: 1, total: 5 });
          
          // 添加初始问题
          const initialQuestion = getInitialQuestion();
          setMessages([{
            role: 'interviewer',
            content: initialQuestion,
            timestamp: new Date()
          }]);
          
          setDigitalHumanExpression('friendly');
          setDigitalHumanAction('talking');
        }, 1000);
        
      } catch (error) {
        console.error('Interview initialization failed:', error);
        setConnectionStatus('error');
        setApiError('面试初始化失败，请刷新页面重试');
      }
    };

    initializeInterview();
    
    // 清理函数
    return () => {
      if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        setWebcamStream(null);
      }
      setShowWebcam(false);
      if (recordingTimeout) {
        clearTimeout(recordingTimeout);
      }
    };
  }, []);



  const getAvatarExpression = (baseExpression: string) => {
    // 根据数字人的性格特点调整表情
    if (avatarConfig.personality?.traits?.includes('friendly')) {
      return baseExpression === 'neutral' ? 'friendly' : baseExpression;
    }
    if (avatarConfig.personality?.traits?.includes('professional')) {
      return baseExpression === 'friendly' ? 'confident' : baseExpression;
    }
    return baseExpression;
  };
  
  const getAvatarAction = (baseAction: string) => {
    // 根据数字人的专业领域调整动作
    if (avatarConfig.expertise?.includes('technical') && baseAction === 'greeting') {
      return 'professional_greeting';
    }
    if (avatarConfig.expertise?.includes('creative') && baseAction === 'thinking') {
      return 'creative_thinking';
    }
    return baseAction;
  };



  // 提交答案函数
  const handleSubmitAnswer = async () => {
    if (!currentAnswer.trim() || isProcessing) return;

    setIsProcessing(true);
    setDigitalHumanExpression('thinking');
    setDigitalHumanAction('listening');

    // 添加用户回答到消息列表
    const userMessage: Message = {
      role: 'candidate',
      content: currentAnswer,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setCurrentAnswer('');

    try {
      // 检查是否为离线模式
      if (connectionStatus !== 'connected') {
        handleOfflineAnswer();
        return;
      }

      // 调用API获取下一个问题
      const response = await api.post(`/session/${sessionId}/answer`, {
        answer: currentAnswer,
        question_index: messages.length
      });

      const { next_question, is_complete, feedback } = response.data;

      if (is_complete) {
        // 面试结束
        const completionMessage: Message = {
          role: 'interviewer',
          content: '感谢您参加本次面试！我们会尽快与您联系。',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, completionMessage]);
        setDigitalHumanExpression('happy');
        setDigitalHumanAction('waving');
        setInterviewProgress({ current: 5, total: 5 });
      } else {
        // 添加下一个问题
        const nextMessage: Message = {
          role: 'interviewer',
          content: next_question,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, nextMessage]);
        setDigitalHumanExpression('questioning');
        setDigitalHumanAction('talking');
        setInterviewProgress(prev => ({ ...prev, current: prev.current + 1 }));
      }

    } catch (error) {
      console.error('Error submitting answer:', error);
      setApiError('提交答案失败，请重试');
      handleOfflineAnswer();
    } finally {
      setIsProcessing(false);
    }
  };



  // 开始录音函数
  const startRecording = async () => {
    try {
      // 清除之前的错误
      setApiError('');
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processAudioRecording(audioBlob);
        
        // 停止所有音频轨道
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setApiError('录音过程中发生错误，请重试');
        setIsRecording(false);
        setIsProcessing(false);
        setDigitalHumanExpression('neutral');
      };

      mediaRecorder.start(1000); // 每秒收集一次数据
      setIsRecording(true);
      setDigitalHumanExpression('listening');
      setDigitalHumanAction('listening');
      
      // 设置最大录音时间（30秒）
      const timeout = setTimeout(() => {
        if (isRecording && mediaRecorderRef.current?.state === 'recording') {
          stopRecording();
          setApiError('录音时间过长，已自动停止');
        }
      }, 30000);
      setRecordingTimeout(timeout);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      setApiError('无法访问麦克风，请检查权限设置');
      setIsRecording(false);
    }
  };

  // 停止录音函数
  const stopRecording = () => {
    if (recordingTimeout) {
      clearTimeout(recordingTimeout);
      setRecordingTimeout(null);
    }
    
    if (mediaRecorderRef.current && isRecording) {
      try {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
        setIsProcessing(true);
        setDigitalHumanExpression('thinking');
        setDigitalHumanAction('thinking');
      } catch (error) {
        console.error('Error stopping recording:', error);
        setApiError('停止录音时发生错误');
        setIsRecording(false);
        setIsProcessing(false);
      }
    }
  };

  // 获取情感上下文
  const getEmotionalContext = () => {
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) return 'neutral';
    
    // 简单的情感分析逻辑
    const content = lastMessage.content.toLowerCase();
    if (content.includes('困难') || content.includes('挑战') || content.includes('问题')) {
      return 'challenging';
    }
    if (content.includes('成功') || content.includes('优秀') || content.includes('满意')) {
      return 'positive';
    }
    return 'neutral';
  };

  // 初始化摄像头函数
  const initializeWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        } 
      });
      setWebcamStream(stream);
      if (webcamVideoRef.current) {
        webcamVideoRef.current.srcObject = stream;
      }
      setShowWebcam(true);
    } catch (error) {
      console.error('Error accessing webcam:', error);
      setApiError('无法访问摄像头，请检查权限设置');
    }
  };

  // 数字人准备就绪处理函数
  const handleDigitalHumanReady = () => {
    console.log('Digital human loaded and ready');
  };

  // 停止摄像头
  const stopWebcam = () => {
    if (webcamStream) {
      webcamStream.getTracks().forEach(track => track.stop());
      setWebcamStream(null);
    }
    setShowWebcam(false);
  };

  // 获取模型URL函数
  const getModelUrl = () => {
    switch (avatarModel) {
      case 'demo': return '/models/demo_avatar.glb';
      case 'female': return '/models/simple_female.glb';
      case 'male': return '/models/simple_male.glb';
      case 'professional_female': return '/models/professional_female.glb';
      case 'tech_interviewer': return '/models/tech_interviewer.glb';
      case 'creative_interviewer': return '/models/creative_interviewer.glb';
      case 'senior_executive': return '/models/senior_executive.glb';
      case 'friendly_hr': return '/models/friendly_hr.glb';
      default: return undefined;
    }
  };

  // 获取当前面试阶段
  const getInterviewStage = () => {
    if (messages.length === 0) return 'greeting';
    if (messages.length <= 2) return 'introduction';
    if (messages.length <= 6) return 'technical';
    if (messages.length <= 8) return 'behavioral';
    return 'closing';
  };

  const avatarConfig = getAvatarModel(avatarModel);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6 h-screen">
        
        {/* Digital Human Panel */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-800">数字人面试</h1>
            
            {/* 摄像头控制按钮 */}
            <div className="flex items-center space-x-2">
              <button
                onClick={showWebcam ? stopWebcam : initializeWebcam}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  showWebcam
                    ? 'bg-red-500 hover:bg-red-600 text-white'
                    : 'bg-green-500 hover:bg-green-600 text-white'
                }`}
              >
                {showWebcam ? '关闭摄像头' : '开启摄像头'}
              </button>
            </div>
          </div>
          
          <div className="flex-1 relative">
            {/* Digital Human View */}
            <div className="h-full">
              <DigitalHumanView
                audioUrl={currentAudioUrl}
                expression={digitalHumanExpression}
                action={digitalHumanAction}
                onReady={handleDigitalHumanReady}
                className="w-full h-full"
                modelUrl={getModelUrl()}
                avatarId={avatarModel}
                interviewStage={getInterviewStage() as any}
                isAISpeaking={isProcessing}
                isUserSpeaking={isRecording}
              />
            </div>
            
            {/* 用户摄像头画面 */}
            {showWebcam && (
              <div className="absolute top-4 right-4 w-48 h-36 bg-black rounded-lg overflow-hidden shadow-lg border-2 border-white">
                <video
                  ref={webcamVideoRef}
                  autoPlay
                  muted
                  playsInline
                  className="w-full h-full object-cover"
                  style={{ transform: 'scaleX(-1)' }} // 镜像显示
                />
                <div className="absolute bottom-2 left-2 text-white text-xs bg-black bg-opacity-50 px-2 py-1 rounded">
                  您的画面
                </div>
              </div>
            )}
          </div>
          
          {/* Debug Info */}
          <div className="mt-4 p-3 bg-gray-100 rounded-lg text-sm text-gray-600">
            <div>SessionID: {sessionId}</div>
            <div>连接状态: {connectionStatus}</div>
            <div>面试类型: {interviewType}</div>
            <div>数字人模型: {avatarModel}</div>
            <div>进度: {interviewProgress.current}/{interviewProgress.total}</div>
            <div>消息数: {messages.length}</div>
            {showWebcam && <div>摄像头: 已启用</div>}
          </div>
        </div>
        
        <div className="flex-1 bg-white rounded-lg shadow-lg p-6 mb-4 overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Interview Conversation</h2>
            <div className="flex items-center space-x-2">
              {/* 连接状态指示器 */}
              <div className={`w-3 h-3 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-500' :
                connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
              }`}></div>
              <span className="text-sm text-gray-600">
                {connectionStatus === 'connected' ? '已连接' :
                 connectionStatus === 'connecting' ? '连接中...' :
                 connectionStatus === 'error' ? '连接错误' : '未连接'}
              </span>
              
              {/* 进度指示器 */}
              <div className="text-sm text-gray-500">
                {interviewProgress.current}/{interviewProgress.total}
              </div>
            </div>
          </div>
          
          {/* API错误提示 */}
          {apiError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-4 h-4 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-red-700 text-sm">{apiError}</span>
                <button
                  onClick={() => setApiError('')}
                  className="ml-auto text-red-500 hover:text-red-700"
                >
                  ✕
                </button>
              </div>
            </div>
          )}
          
          {/* Messages */}
          <div className="h-[calc(100%-4rem)] overflow-y-auto space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'candidate' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-lg ${
                    message.role === 'candidate'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-800'
                  }`}
                >
                  <p className="text-sm font-semibold mb-1">
                    {message.role === 'candidate' ? 'You' : 'Interviewer'}
                  </p>
                  <p>{message.content}</p>
                  <p className="text-xs mt-2 opacity-70">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            
            {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-gray-200 text-gray-800 p-4 rounded-lg">
                  <p className="text-sm font-semibold mb-1">Interviewer</p>
                  <p className="flex items-center">
                    <span>Thinking</span>
                    <span className="ml-2 flex space-x-1">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </span>
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input Panel */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center space-x-4">
            <textarea
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              placeholder="Type your answer here or use voice recording..."
              className="flex-1 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              disabled={isRecording || isProcessing}
            />
            
            <div className="flex flex-col space-y-2">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center min-w-[80px] ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 text-white'
                    : 'bg-green-500 hover:bg-green-600 text-white'
                }`}
                disabled={isProcessing}
              >
                {isRecording ? (
                  <>
                    <div className="w-3 h-3 bg-white rounded-full animate-pulse mr-2"></div>
                    Stop
                  </>
                ) : (
                  'Record'
                )}
              </button>
              
              <button
                onClick={handleSubmitAnswer}
                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!currentAnswer.trim() || isProcessing || isRecording}
              >
                {isProcessing ? 'Processing...' : 'Submit'}
              </button>
            </div>
          </div>
          
          {/* 录音状态提示 */}
          {isRecording && (
            <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center text-green-700 text-sm">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                正在录音... 点击 "Stop" 结束录音
              </div>
            </div>
          )}
          
          {/* 处理状态提示 */}
          {isProcessing && !isRecording && (
            <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center text-blue-700 text-sm">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse mr-2"></div>
                正在处理语音识别...
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );





  // 组件挂载时初始化
  useEffect(() => {
    const initializeInterview = async () => {
      setConnectionStatus('connecting');
      
      try {
        // 初始化摄像头
        await initializeWebcam();
        
        // 模拟连接成功
        setTimeout(() => {
          setConnectionStatus('connected');
          setInterviewProgress({ current: 1, total: 5 });
          
          // 添加初始问题
          const initialQuestion = getInitialQuestion();
          setMessages([{
            role: 'interviewer',
            content: initialQuestion,
            timestamp: new Date()
          }]);
          
          setDigitalHumanExpression('friendly');
          setDigitalHumanAction('talking');
        }, 1000);
        
      } catch (error) {
        console.error('Interview initialization failed:', error);
        setConnectionStatus('error');
        setApiError('面试初始化失败，请刷新页面重试');
      }
    };

    initializeInterview();
    
    // 清理函数
    return () => {
      stopWebcam();
      if (recordingTimeout) {
        clearTimeout(recordingTimeout);
      }
    };
  }, []);

  const getQuestionsForExpertise = () => {
      if (avatarConfig.expertise?.includes('technical')) {
        return [
          '请简单介绍一下您的技术背景和编程经验。',
          '您最熟悉的编程语言是什么？请描述一个您用它解决的复杂问题。',
          '请解释一下您对软件架构设计的理解。',
          '您如何进行代码审查和质量保证？',
          '您对我们的技术栈有什么了解？您期望在技术方面有什么发展？'
        ];
      } else if (avatarConfig.expertise?.includes('creative')) {
        return [
          '请介绍一下您的创意背景和设计经验。',
          '您如何保持创意灵感和跟上设计趋势？',
          '请描述一个您最满意的创意项目。',
          '您如何平衡创意表达和商业需求？',
          '您对我们公司的品牌和设计理念有什么看法？'
        ];
      } else {
        return [
          '请简单介绍一下您自己。',
          '您为什么对这个职位感兴趣？',
          '您认为自己最大的优势是什么？',
          '您如何处理工作中的挑战？',
          '您对未来的职业规划是什么？'
        ];
      }
    };





  const handleOfflineAnswer = () => {
    console.log('🔌 离线模式处理答案');
    
    const mockQuestions = [
      '请简单介绍一下您自己，包括您的教育背景和工作经验。',
      '您为什么对这个职位感兴趣？您认为自己最适合这个岗位的地方是什么？',
      '请描述一个您在工作中遇到的挑战，以及您是如何解决的。',
      '您如何看待团队合作？请举例说明您在团队中的角色。',
      '您对未来3-5年的职业规划是什么？'
    ];
    
    const currentQuestionIndex = Math.floor(messages.length / 2);
    
    if (currentQuestionIndex < mockQuestions.length) {
      setTimeout(() => {
        const nextQuestion = mockQuestions[currentQuestionIndex];
        const nextMessage: Message = {
          role: 'interviewer',
          content: nextQuestion,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, nextMessage]);
        setDigitalHumanExpression('questioning');
        setDigitalHumanAction('talking');
        setInterviewProgress({ current: currentQuestionIndex + 2, total: 5 });
        setIsProcessing(false);
      }, 2000);
    } else {
      // 面试结束
      setTimeout(() => {
        const completionMessage: Message = {
          role: 'interviewer',
          content: '感谢您参加本次面试！我们会尽快与您联系。',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, completionMessage]);
        setDigitalHumanExpression('happy');
        setDigitalHumanAction('waving');
        setInterviewProgress({ current: 5, total: 5 });
        setIsProcessing(false);
      }, 2000);
    }
  };

  const processAudioRecording = async (audioBlob: Blob) => {
    try {
      // 检查音频大小
      if (audioBlob.size === 0) {
        throw new Error('录音数据为空，请重新录音');
      }
      
      if (audioBlob.size > 25 * 1024 * 1024) { // 25MB限制
        throw new Error('录音文件过大，请缩短录音时间');
      }
      
      // Convert to base64 for API
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      
      reader.onloadend = async () => {
        try {
          const base64Audio = reader.result?.toString().split(',')[1];
          
          if (!base64Audio) {
            throw new Error('音频数据转换失败');
          }
          
          console.log('发送音频数据到服务器，大小:', audioBlob.size, 'bytes');
          
          // Send to speech-to-text API with timeout
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时
          
          const response = await api.post(
            `/api/speech/transcribe`,
            {
              audio_data: base64Audio
            },
            {
              signal: controller.signal,
              timeout: 30000
            }
          );
          
          clearTimeout(timeoutId);
          
          if (response.data.success) {
            const { text } = response.data;
            if (text && text.trim()) {
              setCurrentAnswer(text.trim());
              
              // 自动提交转录结果
              setTimeout(() => {
                if (text.trim()) {
                  setCurrentAnswer(text.trim());
                  // 不自动提交，让用户确认
                }
              }, 500);
            } else {
              setApiError('未检测到有效语音，请重新录音');
            }
          } else {
            throw new Error(response.data.error || '语音识别失败');
          }
          
        } catch (error: any) {
          console.error('语音识别API调用失败:', error);
          if (error.name === 'AbortError') {
            setApiError('语音识别超时，请重试');
          } else if (error.response?.status === 400) {
            setApiError('音频格式不支持，请重新录音');
          } else if (error.response?.status === 500) {
            setApiError('服务器语音识别服务暂时不可用');
          } else {
            setApiError(`语音识别失败: ${error.message || '未知错误'}`);
          }
        }
      };
      
      reader.onerror = () => {
        setApiError('音频文件读取失败，请重试');
      };
      
    } catch (error: any) {
      console.error('Error processing audio:', error);
      setApiError(error.message || '音频处理失败，请重试');
    } finally {
      setIsProcessing(false);
      setDigitalHumanExpression('neutral');
      setDigitalHumanAction('idle');
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Digital Human Panel */}
      <div className="w-1/2 p-4">
        <div className="h-full bg-white rounded-lg shadow-lg overflow-hidden">
          <DigitalHumanView
            audioUrl={currentAudioUrl}
            expression={digitalHumanExpression}
            action={digitalHumanAction}
            onReady={handleDigitalHumanReady}
            modelUrl={getModelUrl()}
            className="h-full"
            avatarId={avatarModel}
            avatarConfig={avatarConfig}
            interviewStage={getInterviewStage()}
            isAISpeaking={isProcessing}
            isUserSpeaking={isRecording}
            currentMessage={messages[messages.length - 1]?.content}
            emotionalContext={getEmotionalContext()}
            lightingPreset={avatarConfig.appearance?.lighting || "professional"}
            enableSmartExpressions={avatarConfig.features?.facialExpressions || true}
            onAudioEnd={() => setCurrentAudioUrl('')}
            onError={(error) => {
              console.error('DigitalHumanView 错误:', error);
              setApiError(error);
            }}
          />
        </div>
      </div>

      {/* Chat Panel */}
      <div className="w-1/2 p-4 flex flex-col">
        {/* 调试面板 */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4 text-xs">
          <div className="font-semibold text-yellow-800 mb-2">🔧 调试信息</div>
          <div className="grid grid-cols-2 gap-2 text-yellow-700">
            <div>SessionID: {sessionId || '未设置'}</div>
            <div>连接状态: {connectionStatus}</div>
            <div>面试类型: {interviewType}</div>
            <div>数字人模型: {avatarModel}</div>
            <div>进度: {interviewProgress.current}/{interviewProgress.total}</div>
            <div>消息数: {messages.length}</div>
          </div>
        </div>
        
        <div className="flex-1 bg-white rounded-lg shadow-lg p-6 mb-4 overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Interview Conversation</h2>
            <div className="flex items-center space-x-2">
              {/* 连接状态指示器 */}
              <div className={`w-3 h-3 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-500' :
                connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
              }`}></div>
              <span className="text-sm text-gray-600">
                {connectionStatus === 'connected' ? '已连接' :
                 connectionStatus === 'connecting' ? '连接中...' :
                 connectionStatus === 'error' ? '连接错误' : '未连接'}
              </span>
              
              {/* 进度指示器 */}
              <div className="text-sm text-gray-500">
                {interviewProgress.current}/{interviewProgress.total}
              </div>
            </div>
          </div>
          
          {/* API错误提示 */}
          {apiError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-4 h-4 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-red-700 text-sm">{apiError}</span>
                <button
                  onClick={() => setApiError('')}
                  className="ml-auto text-red-500 hover:text-red-700"
                >
                  ✕
                </button>
              </div>
            </div>
          )}
          
          {/* Messages */}
          <div className="h-[calc(100%-4rem)] overflow-y-auto space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'candidate' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-lg ${
                    message.role === 'candidate'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-800'
                  }`}
                >
                  <p className="text-sm font-semibold mb-1">
                    {message.role === 'candidate' ? 'You' : 'Interviewer'}
                  </p>
                  <p>{message.content}</p>
                  <p className="text-xs mt-2 opacity-70">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            
            {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-gray-200 text-gray-800 p-4 rounded-lg">
                  <p className="text-sm font-semibold mb-1">Interviewer</p>
                  <p className="flex items-center">
                    <span>Thinking</span>
                    <span className="ml-2 flex space-x-1">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </span>
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input Panel */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center space-x-4">
            <textarea
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              placeholder="Type your answer here or use voice recording..."
              className="flex-1 p-3 border border-gray-300 rounded-lg resize-none"
              rows={3}
              disabled={isRecording || isProcessing}
            />
            
            <div className="flex flex-col space-y-2">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 text-white'
                    : 'bg-green-500 hover:bg-green-600 text-white'
                }`}
                disabled={isProcessing}
              >
                {isRecording ? 'Stop' : 'Record'}
              </button>
              
              <button
                onClick={handleSubmitAnswer}
                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                disabled={!currentAnswer.trim() || isProcessing}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};