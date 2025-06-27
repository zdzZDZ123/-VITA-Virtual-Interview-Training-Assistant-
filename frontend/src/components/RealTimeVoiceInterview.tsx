import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useInterviewStore } from '../store/useInterviewStore';
import { toast } from 'react-hot-toast';

interface VoiceMessage {
  id: string;
  role: 'interviewer' | 'candidate';
  content: string;
  timestamp: Date;
  audioUrl?: string;
  isPlaying?: boolean;
  duration?: number;
}

interface VoiceState {
  isListening: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  isConnected: boolean;
  volume: number;
  confidence: number;
}

const RealTimeVoiceInterview: React.FC = () => {
  const { sessionId, currentQuestion, submitAnswer, isLoading } = useInterviewStore();
  
  // 添加调试模式状态
  const [debugMode, setDebugMode] = useState(false);
  
  // 语音状态
  const [voiceState, setVoiceState] = useState<VoiceState>({
    isListening: false,
    isProcessing: false,
    isSpeaking: false,
    isConnected: false,
    volume: 0,
    confidence: 0
  });
  
  // 对话历史
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  
  // 当前用户输入
  const [currentInput, setCurrentInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  
  // 语音设置
  const [voiceSettings, setVoiceSettings] = useState({
    voice: 'nova',
    speed: 1.0,
    autoPlay: true,
    interruptible: true,
    silenceThreshold: 2000, // 2秒静默后停止录音
    volumeThreshold: 0.01
  });
  
  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  
  // 初始化音频上下文
  const initializeAudioContext = useCallback(async () => {
    try {
      console.log('[RealTimeVoiceInterview:Audio] 开始初始化音频上下文...');
      
      // 如果已有AudioContext且状态正常，则直接使用
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        if (audioContextRef.current.state === 'suspended') {
          console.log('[RealTimeVoiceInterview:Audio] 现有音频上下文处于挂起状态，正在恢复...');
          await audioContextRef.current.resume();
          console.log('[RealTimeVoiceInterview:Audio] 现有音频上下文恢复成功');
        }
        console.log('[RealTimeVoiceInterview:Audio] 使用现有音频上下文，状态:', audioContextRef.current.state);
        return true;
      }
      
      // 创建新的AudioContext
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      console.log('[RealTimeVoiceInterview:Audio] 音频上下文创建成功');
      
      if (audioContextRef.current.state === 'suspended') {
        console.log('[RealTimeVoiceInterview:Audio] 音频上下文处于挂起状态，正在恢复...');
        await audioContextRef.current.resume();
        console.log('[RealTimeVoiceInterview:Audio] 音频上下文恢复成功');
      }
      
      console.log('[RealTimeVoiceInterview:Audio] 音频上下文初始化成功，状态:', audioContextRef.current.state);
      return true;
    } catch (error) {
      console.error('[RealTimeVoiceInterview:Audio] 音频上下文初始化失败:', error);
      console.error('[RealTimeVoiceInterview:Audio] 错误详情:', {
        errorName: error instanceof Error ? error.name : 'Unknown',
        errorMessage: error instanceof Error ? error.message : String(error),
        errorStack: error instanceof Error ? error.stack : undefined
      });
      return false;
    }
  }, []);
  
  // 音量检测
  const analyzeAudio = useCallback(() => {
    if (!analyserRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    // 计算音量
    const volume = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length / 255;
    
    setVoiceState(prev => ({ ...prev, volume }));
    
    // 静默检测
    if (volume < voiceSettings.volumeThreshold) {
      if (!silenceTimerRef.current && isRecording) {
        silenceTimerRef.current = setTimeout(() => {
          stopListening();
        }, voiceSettings.silenceThreshold);
      }
    } else {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
    }
    
    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(analyzeAudio);
    }
  }, [isRecording, voiceSettings.volumeThreshold, voiceSettings.silenceThreshold]);
  
  // 开始监听
  const startListening = useCallback(async () => {
    try {
      console.log('[RealTimeVoiceInterview:Audio] 开始监听流程...');
      
      const audioInitialized = await initializeAudioContext();
      if (!audioInitialized) {
        throw new Error('音频系统初始化失败');
      }
      
      console.log('[RealTimeVoiceInterview:Audio] 正在请求麦克风权限...');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });
      
      console.log('[RealTimeVoiceInterview:Audio] 成功获取媒体流:', {
        streamId: stream.id,
        active: stream.active,
        audioTracks: stream.getAudioTracks().length
      });
      
      streamRef.current = stream;
      
      // 设置音频分析
      const audioContext = audioContextRef.current!;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
      
      console.log('[RealTimeVoiceInterview:Audio] 音频分析器已设置');
      
      // 设置录音 - 检测支持的MIME类型
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/webm';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = 'audio/mp4';
          if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = ''; // 使用默认格式
          }
        }
      }
      
      console.log('[RealTimeVoiceInterview:Audio] 使用MIME类型:', mimeType || '默认');
      
      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log('[RealTimeVoiceInterview:Audio] 音频数据可用，大小:', event.data.size);
        } else {
          console.warn('[RealTimeVoiceInterview:Audio] 收到空的音频数据块');
        }
      };
      
      mediaRecorder.onstop = async () => {
        console.log('[RealTimeVoiceInterview:Audio] 录音停止，准备处理音频...');
        console.log('[RealTimeVoiceInterview:Audio] 音频块总数:', audioChunksRef.current.length);
        
        if (audioChunksRef.current.length === 0) {
          console.error('[RealTimeVoiceInterview:Audio] 没有收集到音频数据');
          toast.error('录音失败：没有收集到音频数据，请重试');
          return;
        }
        
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/webm' });
        console.log('[RealTimeVoiceInterview:Audio] 音频Blob创建完成，大小:', audioBlob.size);
        
        if (audioBlob.size === 0) {
          console.error('[RealTimeVoiceInterview:Audio] 音频Blob为空');
          toast.error('录音失败：音频数据为空，请重试');
          return;
        }
        
        await processAudioInput(audioBlob);
      };
      
      mediaRecorder.onstart = () => {
        console.log('[RealTimeVoiceInterview:Audio] MediaRecorder已启动');
      };
      
      mediaRecorder.onerror = (event) => {
        console.error('[RealTimeVoiceInterview:Audio] MediaRecorder错误:', event);
        toast.error('录音器错误，请重试');
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(1000); // 每1秒收集一次数据，避免过于频繁的分片
      
      setIsRecording(true);
      setVoiceState(prev => ({ ...prev, isListening: true, isConnected: true }));
      
      console.log('[RealTimeVoiceInterview:Audio] 开始录音，每100ms收集一次数据');
      
      // 开始音量分析
      analyzeAudio();
      
      toast.success('开始监听，请说话...');
      
    } catch (error) {
      console.error('[RealTimeVoiceInterview:Audio] 开始监听失败:', error);
      console.error('[RealTimeVoiceInterview:Audio] 错误详情:', {
        errorName: error instanceof Error ? error.name : 'Unknown',
        errorMessage: error instanceof Error ? error.message : String(error),
        errorStack: error instanceof Error ? error.stack : undefined
      });
      toast.error('无法访问麦克风，请检查权限设置');
      setVoiceState(prev => ({ ...prev, isListening: false, isConnected: false }));
    }
  }, [initializeAudioContext, analyzeAudio]);
  
  // 停止监听
  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    setVoiceState(prev => ({ ...prev, isListening: false, volume: 0 }));
  }, [isRecording]);
  
  // 处理音频输入
  const processAudioInput = useCallback(async (audioBlob: Blob) => {
    console.log('[RealTimeVoiceInterview:Audio] 开始处理音频输入，Blob大小:', audioBlob.size);
    setVoiceState(prev => ({ ...prev, isProcessing: true }));
    
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('language', 'zh');
      
      console.log('[RealTimeVoiceInterview:Audio] 准备发送音频到后端进行转录...');
      const response = await fetch('http://localhost:8000/speech/transcribe', {
        method: 'POST',
        body: formData
      });
      
      console.log('[RealTimeVoiceInterview:Audio] 转录响应状态:', response.status);
      
      const data = await response.json();
      console.log('[RealTimeVoiceInterview:Audio] 转录响应数据:', data);
      
      if (data.success && data.text.trim()) {
        const userMessage: VoiceMessage = {
          id: Date.now().toString(),
          role: 'candidate',
          content: data.text,
          timestamp: new Date(),
          duration: data.duration,
        };
        
        console.log('[RealTimeVoiceInterview:Audio] 转录成功，文本:', data.text);
        console.log('[RealTimeVoiceInterview:Audio] 置信度:', data.confidence);
        
        setMessages(prev => [...prev, userMessage]);
        setCurrentInput(data.text);
        setVoiceState(prev => ({ ...prev, confidence: data.confidence || 0 }));
        
        // 提交答案并获取下一个问题
        await handleSubmitAnswer(data.text);
      } else {
        console.warn('[RealTimeVoiceInterview:Audio] 转录失败或文本为空:', data);
      }
    } catch (error) {
      console.error('[RealTimeVoiceInterview:Audio] 语音处理失败:', error);
      console.error('[RealTimeVoiceInterview:Audio] 错误详情:', {
        errorName: error instanceof Error ? error.name : 'Unknown',
        errorMessage: error instanceof Error ? error.message : String(error),
        errorStack: error instanceof Error ? error.stack : undefined
      });
      toast.error('语音识别失败，请重试');
    } finally {
      setVoiceState(prev => ({ ...prev, isProcessing: false }));
      console.log('[RealTimeVoiceInterview:Audio] 音频处理完成');
    }
  }, []);
  
  // 提交答案
  const handleSubmitAnswer = useCallback(async (answer: string) => {
    try {
      await submitAnswer(answer);
      
      // 获取最新的问题并播放
      if (voiceSettings.autoPlay) {
        // 等待store更新
        setTimeout(() => {
          const latestQuestion = useInterviewStore.getState().currentQuestion;
          if (latestQuestion) {
            speakText(latestQuestion);
          }
        }, 500);
      }
    } catch (error) {
      console.error('提交答案失败:', error);
      toast.error('提交答案失败，请重试');
    }
  }, [submitAnswer, voiceSettings.autoPlay]);
  
  // 语音合成
  const speakText = useCallback(async (text: string) => {
    console.log('[RealTimeVoiceInterview:TTS] 开始语音合成，文本长度:', text.length);
    console.log('[RealTimeVoiceInterview:TTS] 文本内容:', text);
    
    if (voiceState.isSpeaking) {
      // 如果允许打断，停止当前播放
      if (voiceSettings.interruptible && audioRef.current) {
        console.log('[RealTimeVoiceInterview:TTS] 打断当前播放...');
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      } else {
        console.log('[RealTimeVoiceInterview:TTS] 当前正在播放，且不允许打断，跳过');
        return;
      }
    }
    
    setVoiceState(prev => ({ ...prev, isSpeaking: true }));
    
    try {
      console.log('[RealTimeVoiceInterview:TTS] 发送TTS请求...');
      console.log('[RealTimeVoiceInterview:TTS] 请求参数:', {
        voice: voiceSettings.voice,
        speed: voiceSettings.speed
      });
      
      const response = await fetch('http://localhost:8000/speech/synthesize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          text,
          voice: voiceSettings.voice,
          speed: voiceSettings.speed.toString()
        })
      });
      
      console.log('[RealTimeVoiceInterview:TTS] TTS响应状态:', response.status);
      console.log('[RealTimeVoiceInterview:TTS] TTS响应头:', {
        contentType: response.headers.get('content-type'),
        contentLength: response.headers.get('content-length')
      });
      
      if (response.ok) {
        const audioBlob = await response.blob();
        console.log('[RealTimeVoiceInterview:TTS] 音频Blob接收成功，大小:', audioBlob.size, '类型:', audioBlob.type);
        
        const audioUrl = URL.createObjectURL(audioBlob);
        console.log('[RealTimeVoiceInterview:TTS] 音频URL创建成功:', audioUrl);
        
        const interviewerMessage: VoiceMessage = {
          id: Date.now().toString(),
          role: 'interviewer',
          content: text,
          timestamp: new Date(),
          audioUrl,
          isPlaying: true
        };
        
        setMessages(prev => [...prev, interviewerMessage]);
        
        if (audioRef.current) {
          console.log('[RealTimeVoiceInterview:TTS] 设置音频源...');
          audioRef.current.src = audioUrl;
          
          // 添加错误处理
          audioRef.current.onerror = (e) => {
            console.error('[RealTimeVoiceInterview:TTS] 音频播放错误:', e);
            console.error('[RealTimeVoiceInterview:TTS] 音频元素错误详情:', {
              error: audioRef.current?.error,
              errorCode: audioRef.current?.error?.code,
              errorMessage: audioRef.current?.error?.message
            });
            toast.error('音频播放失败');
            setVoiceState(prev => ({ ...prev, isSpeaking: false }));
          };
          
          // 确保音频可以播放
          try {
            // 设置音量
            audioRef.current.volume = 1.0;
            // 确保不是静音
            audioRef.current.muted = false;
            
            console.log('[RealTimeVoiceInterview:TTS] 准备播放音频...');
            const playPromise = audioRef.current.play();
            
            if (playPromise !== undefined) {
              playPromise
                .then(() => {
                  console.log('[RealTimeVoiceInterview:TTS] 音频开始播放成功');
                })
                .catch((error) => {
                  console.error('[RealTimeVoiceInterview:TTS] 播放失败:', error);
                  console.error('[RealTimeVoiceInterview:TTS] 播放错误详情:', {
                    errorName: error.name,
                    errorMessage: error.message,
                    errorCode: error.code
                  });
                  // 如果是自动播放策略问题，提示用户
                  if (error.name === 'NotAllowedError') {
                    toast.error('请点击页面任意位置以启用音频播放');
                    // 添加点击事件监听器
                    const handleClick = async () => {
                      try {
                        await audioRef.current?.play();
                        console.log('[RealTimeVoiceInterview:TTS] 用户点击后播放成功');
                        document.removeEventListener('click', handleClick);
                      } catch (e) {
                        console.error('[RealTimeVoiceInterview:TTS] 点击后播放仍然失败:', e);
                      }
                    };
                    document.addEventListener('click', handleClick);
                  } else {
                    toast.error('音频播放失败，请检查浏览器设置');
                  }
                  setVoiceState(prev => ({ ...prev, isSpeaking: false }));
                });
            }
          } catch (playError) {
            console.error('[RealTimeVoiceInterview:TTS] 播放异常:', playError);
            toast.error('音频播放失败');
            setVoiceState(prev => ({ ...prev, isSpeaking: false }));
          }
        }
      } else {
        const errorText = await response.text();
        console.error('[RealTimeVoiceInterview:TTS] 语音合成响应错误:', response.status, errorText);
        toast.error(`语音合成失败: ${response.status}`);
        setVoiceState(prev => ({ ...prev, isSpeaking: false }));
      }
    } catch (error) {
      console.error('[RealTimeVoiceInterview:TTS] 语音合成失败:', error);
      console.error('[RealTimeVoiceInterview:TTS] 错误详情:', {
        errorName: error instanceof Error ? error.name : 'Unknown',
        errorMessage: error instanceof Error ? error.message : String(error),
        errorStack: error instanceof Error ? error.stack : undefined
      });
      toast.error('语音合成失败');
      setVoiceState(prev => ({ ...prev, isSpeaking: false }));
    }
  }, [voiceState.isSpeaking, voiceSettings]);
  
  // 切换监听状态
  const toggleListening = useCallback(() => {
    if (voiceState.isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [voiceState.isListening, startListening, stopListening]);
  
  // 初始化面试
  useEffect(() => {
    if (sessionId && currentQuestion && messages.length === 0) {
      const welcomeMessage: VoiceMessage = {
        id: 'welcome',
        role: 'interviewer',
        content: `欢迎参加面试！${currentQuestion}`,
        timestamp: new Date()
      };
      
      setMessages([welcomeMessage]);
      
      // 延迟播放，确保组件已经完全加载
      if (voiceSettings.autoPlay) {
        setTimeout(() => {
          speakText(welcomeMessage.content);
        }, 1000);
      }
    }
  }, [sessionId, currentQuestion, messages.length, voiceSettings.autoPlay]);
  
  // 清理资源
  useEffect(() => {
    return () => {
      stopListening();
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [stopListening]);
  
  // 音频播放结束处理
  const handleAudioEnded = useCallback(() => {
    console.log('音频播放结束');
    setVoiceState(prev => ({ ...prev, isSpeaking: false }));
    setMessages(prev => prev.map(msg => ({ ...msg, isPlaying: false })));
    
    // 自动开始监听
    if (voiceSettings.autoPlay && !voiceState.isListening) {
      setTimeout(() => {
        startListening();
      }, 500);
    }
  }, [voiceSettings.autoPlay, voiceState.isListening, startListening]);
  
  // 添加音频加载成功处理
  const handleAudioCanPlay = useCallback(() => {
    console.log('音频可以播放了');
  }, []);
  
  // 添加音频加载开始处理
  const handleAudioLoadStart = useCallback(() => {
    console.log('音频开始加载');
  }, []);
  
  if (!sessionId) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-gray-500 mb-2">面试会话未初始化</div>
          <div className="text-sm text-gray-400">请返回设置页面重新开始</div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="max-w-4xl mx-auto p-6 h-screen flex flex-col">
      {/* 头部状态栏 */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`w-3 h-3 rounded-full ${
              voiceState.isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className="text-sm font-medium">
              {voiceState.isListening ? '正在监听...' : 
               voiceState.isProcessing ? '处理中...' : 
               voiceState.isSpeaking ? '面试官说话中...' : '待机中'}
            </span>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* 音量指示器 */}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">音量</span>
              <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-500 transition-all duration-100"
                  style={{ width: `${voiceState.volume * 100}%` }}
                ></div>
              </div>
            </div>
            
            {/* 置信度 */}
            {voiceState.confidence > 0 && (
              <div className="text-xs text-gray-500">
                置信度: {(voiceState.confidence * 100).toFixed(1)}%
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* 对话区域 */}
      <div className="flex-1 bg-white rounded-lg shadow-sm p-4 overflow-y-auto mb-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${
              message.role === 'interviewer' ? 'justify-start' : 'justify-end'
            }`}>
              <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.role === 'interviewer' 
                  ? 'bg-blue-100 text-blue-900' 
                  : 'bg-gray-100 text-gray-900'
              }`}>
                <div className="flex items-start space-x-2">
                  <div className="flex-1">
                    <div className="text-sm font-medium mb-1">
                      {message.role === 'interviewer' ? '🤖 面试官' : '👤 您'}
                    </div>
                    <div className="text-sm">{message.content}</div>
                    {message.duration && (
                      <div className="text-xs text-gray-500 mt-1">
                        时长: {message.duration.toFixed(1)}s
                      </div>
                    )}
                  </div>
                  
                  {message.audioUrl && (
                    <button
                      onClick={() => speakText(message.content)}
                      className="text-blue-500 hover:text-blue-700 p-1"
                      disabled={voiceState.isSpeaking}
                    >
                      {message.isPlaying ? '🔊' : '🔇'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {voiceState.isProcessing && (
            <div className="flex justify-center">
              <div className="bg-gray-100 rounded-lg px-4 py-2">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <span className="text-sm text-gray-600 ml-2">处理语音中...</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* 控制面板 */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center justify-center space-x-4">
          {/* 主要控制按钮 */}
          <button
            onClick={toggleListening}
            disabled={voiceState.isProcessing || isLoading}
            className={`w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl transition-all duration-200 ${
              voiceState.isListening
                ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                : 'bg-blue-500 hover:bg-blue-600'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {voiceState.isListening ? '🛑' : '🎤'}
          </button>
          
          {/* 测试语音按钮 */}
          <button
            onClick={() => speakText('测试语音功能，面试官正在说话')}
            disabled={voiceState.isSpeaking}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
          >
            测试语音
          </button>
          
          {/* 调试模式切换 */}
          <button
            onClick={() => setDebugMode(!debugMode)}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            {debugMode ? '关闭调试' : '开启调试'}
          </button>
          
          {/* 设置按钮 */}
          <div className="flex items-center space-x-2">
            <select
              value={voiceSettings.voice}
              onChange={(e) => setVoiceSettings(prev => ({ ...prev, voice: e.target.value }))}
              className="text-sm border rounded px-2 py-1"
              title="选择面试官声音"
            >
              <option value="alloy">Alloy</option>
              <option value="echo">Echo</option>
              <option value="fable">Fable</option>
              <option value="onyx">Onyx</option>
              <option value="nova">Nova</option>
              <option value="shimmer">Shimmer</option>
            </select>
            
            <label className="flex items-center space-x-1 text-sm">
              <input
                type="checkbox"
                checked={voiceSettings.autoPlay}
                onChange={(e) => setVoiceSettings(prev => ({ ...prev, autoPlay: e.target.checked }))}
              />
              <span>自动播放</span>
            </label>
            
            <label className="flex items-center space-x-1 text-sm">
              <input
                type="checkbox"
                checked={voiceSettings.interruptible}
                onChange={(e) => setVoiceSettings(prev => ({ ...prev, interruptible: e.target.checked }))}
              />
              <span>可打断</span>
            </label>
          </div>
        </div>
        
        {/* 当前输入显示 */}
        {currentInput && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">当前识别结果:</div>
            <div className="text-sm">{currentInput}</div>
          </div>
        )}
      </div>
      
      {/* 音频播放器 - 调试模式下可见 */}
      <audio
        ref={audioRef}
        onEnded={handleAudioEnded}
        onCanPlay={handleAudioCanPlay}
        onLoadStart={handleAudioLoadStart}
        onError={(e) => {
          console.error('音频元素错误:', e);
          const audio = e.currentTarget;
          console.error('错误详情:', {
            error: audio.error,
            src: audio.src,
            readyState: audio.readyState,
            networkState: audio.networkState
          });
        }}
        preload="auto"
        controls={debugMode}
        crossOrigin="anonymous"
        style={{ display: debugMode ? 'block' : 'none' }}
        className={debugMode ? 'mt-4 w-full' : ''}
      />
    </div>
  );
};

export default RealTimeVoiceInterview;