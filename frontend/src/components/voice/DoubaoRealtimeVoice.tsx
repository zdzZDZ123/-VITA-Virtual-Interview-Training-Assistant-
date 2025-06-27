import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Settings, PhoneOff, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';

// WebSocket消息类型定义
interface WebSocketMessage {
  type: string;
  text?: string;
  emotion?: EmotionMetrics;
  duration?: number;
  message?: string;
}

// 语音状态枚举
enum VoiceState {
  IDLE = 'idle',           // 空闲
  LISTENING = 'listening', // 正在聆听用户
  THINKING = 'thinking',   // AI思考中
  SPEAKING = 'speaking'    // AI说话中
}

// 情绪指标类型
interface EmotionMetrics {
  pleasantness: number;  // 愉悦度 0-100
  energy: number;        // 能量值 0-100
  clarity: number;       // 清晰度 0-100
}

// 对话消息类型
interface VoiceMessage {
  id: string;
  type: 'user' | 'ai';
  text: string;
  timestamp: Date;
  duration?: number;     // 语音时长（秒）
  emotion?: EmotionMetrics;
}

interface DoubaoRealtimeVoiceProps {
  sessionId: string;
  onSessionEnd: () => void;
  className?: string;
}

export const DoubaoRealtimeVoice: React.FC<DoubaoRealtimeVoiceProps> = ({
  sessionId,
  onSessionEnd,
  className = ''
}) => {
  // 状态管理
  const [voiceState, setVoiceState] = useState<VoiceState>(VoiceState.IDLE);
  const [isConnected, setIsConnected] = useState(false);
  const [isAudioInitialized, setIsAudioInitialized] = useState(false);
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [currentEmotion, setCurrentEmotion] = useState<EmotionMetrics>({
    pleasantness: 75,
    energy: 65,
    clarity: 80
  });
  
  // 音频控制状态
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(80);
  const [selectedVoice, setSelectedVoice] = useState('zh-CN-XiaoxiaoNeural');
  
  // 计时器状态
  const [sessionDuration, setSessionDuration] = useState(0);
  const [recordingDuration, setRecordingDuration] = useState(0);
  
  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // 动画数据
  const [waveformData, setWaveformData] = useState<number[]>(new Array(32).fill(0));
  const [isWaveAnimating, setIsWaveAnimating] = useState(false);

  // 初始化音频上下文
  const initializeAudio = useCallback(async () => {
    try {
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 64;
    } catch (error) {
      console.error('音频初始化失败:', error);
    }
  }, []);

  // 初始化音频系统（包含麦克风权限）
  const initializeAudioSystem = useCallback(async () => {
    try {
      console.log('🎤 开始初始化音频系统...');
      
      // 1. 初始化音频上下文
      await initializeAudio();
      
      // 2. 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log('✅ 麦克风权限获取成功');
      
      // 3. 停止临时流（仅用于权限验证）
      stream.getTracks().forEach(track => track.stop());
      
      // 4. 标记音频系统已初始化
      setIsAudioInitialized(true);
      console.log('✅ 音频系统初始化完成');
      
    } catch (error) {
      console.error('❌ 音频系统初始化失败:', error);
      alert('无法访问麦克风，请检查浏览器权限设置');
    }
  }, [initializeAudio]);

  // WebSocket连接
  const connectWebSocket = useCallback(() => {
    const wsUrl = `ws://localhost:8000/api/v1/ws/realtime-voice/${sessionId}`;
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      setIsConnected(true);
      setVoiceState(VoiceState.IDLE);
      console.log('🔗 实时语音连接已建立');
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    wsRef.current.onclose = () => {
      setIsConnected(false);
      setVoiceState(VoiceState.IDLE);
      console.log('🔌 实时语音连接已断开');
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };
  }, [sessionId]);

  // 处理WebSocket消息
  const handleWebSocketMessage = (data: WebSocketMessage) => {
    console.log('📨 收到WebSocket消息:', data);
    
    switch (data.type) {
      case 'ai_response':
        console.log('🤖 收到AI回复:', data.text);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'ai',
          text: data.text || '',
          timestamp: new Date(),
          emotion: data.emotion
        }]);
        setVoiceState(VoiceState.SPEAKING);
        break;
        
      case 'transcription':
        console.log('📝 收到语音转录:', data.text);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'user',
          text: data.text || '',
          timestamp: new Date(),
          duration: data.duration
        }]);
        setVoiceState(VoiceState.THINKING);
        break;
        
      case 'emotion_update':
        console.log('😊 情感数据更新:', data.emotion);
        if (data.emotion) {
          setCurrentEmotion(data.emotion);
        }
        break;
        
      case 'audio_start':
        console.log('🔊 AI开始语音播放');
        setVoiceState(VoiceState.SPEAKING);
        setIsWaveAnimating(true);
        break;
        
      case 'audio_end':
        console.log('🔇 AI语音播放结束');
        setVoiceState(VoiceState.IDLE);
        setIsWaveAnimating(false);
        break;
        
      case 'error':
        console.error('❌ 服务器错误:', data.message);
        setVoiceState(VoiceState.IDLE);
        alert(`服务器错误: ${data.message || '未知错误'}`);
        break;
        
      default:
        console.log('❓ 未知消息类型:', data.type);
        break;
    }
  };

  // 切换录音状态
  const toggleRecording = async () => {
    if (!isConnected) {
      console.log('❌ WebSocket未连接');
      return;
    }
    
    if (!isAudioInitialized) {
      console.log('❌ 音频系统未初始化，请先点击初始化音频');
      alert('请先点击"初始化音频"按钮');
      return;
    }
    
    if (voiceState === VoiceState.LISTENING) {
      // 正在录音，停止录音
      stopRecording();
    } else if (voiceState === VoiceState.IDLE) {
      // 空闲状态，开始录音
      await startRecording();
    }
  };

  // 开始录音
  const startRecording = async () => {
    if (!isConnected) return;
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // 连接音频分析器
      if (audioContextRef.current && analyserRef.current) {
        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyserRef.current);
        startWaveformAnalysis();
      }
      
      mediaRecorderRef.current = new MediaRecorder(stream);
      const audioChunks: Blob[] = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        sendAudioToServer(audioBlob);
      };
      
      mediaRecorderRef.current.start();
      setVoiceState(VoiceState.LISTENING);
      setIsWaveAnimating(true);
      console.log('🎤 开始录音...');
      
    } catch (error) {
      console.error('录音启动失败:', error);
      alert('无法访问麦克风，请检查权限设置');
    }
  };

  // 停止录音
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setVoiceState(VoiceState.THINKING);
      setIsWaveAnimating(false);
      console.log('🛑 停止录音，正在处理...');
    }
  };

  // 发送音频到服务器
  const sendAudioToServer = (audioBlob: Blob) => {
    console.log('📤 准备发送音频数据，大小:', audioBlob.size, 'bytes');
    
    if (!wsRef.current) {
      console.error('❌ WebSocket连接未建立');
      return;
    }
    
    if (wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('❌ WebSocket连接状态异常:', wsRef.current.readyState);
      return;
    }
    
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const base64Audio = reader.result as string;
        const audioData = base64Audio.split(',')[1];
        
        const message = {
          type: 'audio_data',
          audio: audioData,
          voice: selectedVoice,
          session_id: sessionId,
          timestamp: new Date().toISOString()
        };
        
        console.log('📤 发送音频数据到服务器:', {
          type: message.type,
          audioSize: audioData.length,
          voice: message.voice,
          sessionId: message.session_id
        });
        
        wsRef.current?.send(JSON.stringify(message));
        console.log('✅ 音频数据发送成功');
        
      } catch (error) {
        console.error('❌ 发送音频数据失败:', error);
        setVoiceState(VoiceState.IDLE);
      }
    };
    
    reader.onerror = () => {
      console.error('❌ 读取音频文件失败');
      setVoiceState(VoiceState.IDLE);
    };
    
    reader.readAsDataURL(audioBlob);
  };

  // 实时波形分析
  const startWaveformAnalysis = () => {
    if (!analyserRef.current) return;
    
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const updateWaveform = () => {
      if (!analyserRef.current || !isWaveAnimating) return;
      
      analyserRef.current.getByteFrequencyData(dataArray);
      const normalizedData = Array.from(dataArray).map(value => value / 255);
      setWaveformData(normalizedData.slice(0, 32));
      
      requestAnimationFrame(updateWaveform);
    };
    
    updateWaveform();
  };

  // 格式化时间
  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // 获取状态显示文本
  const getStateText = () => {
    switch (voiceState) {
      case VoiceState.IDLE: return '准备就绪';
      case VoiceState.LISTENING: return '正在聆听...';
      case VoiceState.THINKING: return 'AI思考中...';
      case VoiceState.SPEAKING: return 'AI正在回答...';
      default: return '未知状态';
    }
  };

  // 获取状态颜色
  const getStateColor = () => {
    switch (voiceState) {
      case VoiceState.IDLE: return 'text-green-500';
      case VoiceState.LISTENING: return 'text-blue-500';
      case VoiceState.THINKING: return 'text-yellow-500';
      case VoiceState.SPEAKING: return 'text-purple-500';
      default: return 'text-gray-500';
    }
  };

  // 生命周期
  useEffect(() => {
    initializeAudio();
    connectWebSocket();
    
    const sessionTimer = setInterval(() => {
      setSessionDuration(prev => prev + 1);
    }, 1000);
    
    return () => {
      clearInterval(sessionTimer);
      wsRef.current?.close();
      audioContextRef.current?.close();
    };
  }, [initializeAudio, connectWebSocket]);

  // 录音计时器
  useEffect(() => {
    let recordingTimer: NodeJS.Timeout;
    
    if (voiceState === VoiceState.LISTENING) {
      setRecordingDuration(0);
      recordingTimer = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    }
    
    return () => {
      if (recordingTimer) clearInterval(recordingTimer);
    };
  }, [voiceState]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className={`h-screen flex flex-col bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white ${className}`}>
      {/* 头部状态栏 */}
      <div className="flex-none px-6 py-4 bg-black/20 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className={`font-medium ${getStateColor()}`}>
              {getStateText()}
            </span>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-300">
            <span>会话时长: {formatTime(sessionDuration)}</span>
            {voiceState === VoiceState.LISTENING && (
              <span className="text-blue-400">录音: {formatTime(recordingDuration)}</span>
            )}
          </div>
        </div>
      </div>

      {/* 主内容区域 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 波形可视化区域 */}
        <div className="flex-none h-32 flex items-center justify-center bg-black/10 backdrop-blur-sm">
          <div className="flex items-end space-x-1 h-20">
            {waveformData.map((value, index) => (
              <div
                key={index}
                className={`w-2 bg-gradient-to-t transition-all duration-100 ${
                  isWaveAnimating 
                    ? voiceState === VoiceState.LISTENING 
                      ? 'from-blue-500 to-blue-300' 
                      : 'from-purple-500 to-purple-300'
                    : 'from-gray-600 to-gray-400'
                }`}
                style={{ 
                  height: `${Math.max(4, value * 80)}px`,
                  opacity: isWaveAnimating ? 0.8 + value * 0.2 : 0.3
                }}
              />
            ))}
          </div>
        </div>

        {/* 情绪指标条 */}
        <div className="flex-none px-6 py-3 bg-black/10 backdrop-blur-sm">
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div>
              <div className="flex justify-between mb-1">
                <span>愉悦度</span>
                <span>{currentEmotion.pleasantness}%</span>
              </div>
              <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-500"
                  style={{ width: `${currentEmotion.pleasantness}%` }}
                />
              </div>
            </div>
            
            <div>
              <div className="flex justify-between mb-1">
                <span>能量值</span>
                <span>{currentEmotion.energy}%</span>
              </div>
              <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-orange-500 to-orange-400 transition-all duration-500"
                  style={{ width: `${currentEmotion.energy}%` }}
                />
              </div>
            </div>
            
            <div>
              <div className="flex justify-between mb-1">
                <span>清晰度</span>
                <span>{currentEmotion.clarity}%</span>
              </div>
              <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-500"
                  style={{ width: `${currentEmotion.clarity}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* 对话消息区域 */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <Mic className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#ffffff', margin: '1rem 0 0.5rem' }}>
                  实时语音面试
                </p>
                {!isAudioInitialized ? (
                  <div className="space-y-4">
                    <p className="text-sm text-yellow-400">首次使用需要初始化音频系统</p>
                    <Button
                      onClick={initializeAudioSystem}
                      className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg"
                    >
                      🎤 初始化音频系统
                    </Button>
                    <p className="text-xs text-gray-500">点击后将获取麦克风权限，用于语音识别</p>
                  </div>
                ) : (
                  <p className="text-sm text-green-400">✅ 音频系统已就绪，点击麦克风开始对话</p>
                )}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-100'
                  }`}
                >
                  <p className="text-sm leading-relaxed">{message.text}</p>
                  <div className="flex items-center justify-between mt-2 text-xs opacity-70">
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    {message.duration && (
                      <span>{message.duration}s</span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 底部控制栏 */}
      <div className="flex-none px-6 py-4 bg-black/20 backdrop-blur-sm">
        <div className="flex items-center justify-center space-x-4">
          {/* 麦克风主按钮 */}
          <Button
            size="lg"
            disabled={!isConnected}
            className={`w-20 h-20 rounded-full transition-all duration-200 ${
              voiceState === VoiceState.LISTENING
                ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                : 'bg-blue-500 hover:bg-blue-600'
            }`}
            onClick={toggleRecording}
          >
            {voiceState === VoiceState.LISTENING ? (
              <MicOff className="w-8 h-8" />
            ) : voiceState === VoiceState.THINKING ? (
              <Loader2 className="w-8 h-8 animate-spin" />
            ) : (
              <Mic className="w-8 h-8" />
            )}
          </Button>

          {/* 音量控制 */}
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMuted(!isMuted)}
              className="text-gray-300 hover:text-white"
            >
              {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </Button>
            <input
              type="range"
              min="0"
              max="100"
              value={volume}
              onChange={(e) => setVolume(parseInt(e.target.value))}
              className="w-20 h-2 bg-gray-700 rounded-lg appearance-none slider"
              title="音量调节"
              aria-label="音量调节滑块"
            />
            <span className="text-xs text-gray-400 w-8">{volume}%</span>
          </div>

          {/* 设置按钮 */}
          <Button
            variant="ghost"
            size="sm"
            className="text-gray-300 hover:text-white"
          >
            <Settings className="w-5 h-5" />
          </Button>

          {/* 结束通话 */}
          <Button
            variant="destructive"
            size="sm"
            onClick={onSessionEnd}
            className="ml-4"
          >
            <PhoneOff className="w-4 h-4 mr-2" />
            结束面试
          </Button>
        </div>

        {/* 语音选择 */}
        <div className="mt-3 flex justify-center">
          <select
            value={selectedVoice}
            onChange={(e) => setSelectedVoice(e.target.value)}
            className="bg-gray-700 text-white px-3 py-1 rounded text-sm border-none outline-none"
            title="选择语音"
            aria-label="语音选择器"
          >
            <option value="zh-CN-XiaoxiaoNeural">小晓 - 温柔女声</option>
            <option value="zh-CN-YunxiNeural">云希 - 专业男声</option>
            <option value="zh-CN-XiaoyiNeural">小艺 - 活泼女声</option>
            <option value="zh-CN-YunyangNeural">云扬 - 稳重男声</option>
            <option value="en-US-JennyNeural">Jenny - 美式英语女声</option>
            <option value="en-US-GuyNeural">Guy - 美式英语男声</option>
          </select>
        </div>
      </div>
    </div>
  );
}; 