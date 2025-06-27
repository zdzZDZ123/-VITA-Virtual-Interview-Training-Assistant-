import React, { useState, useEffect, useRef } from 'react';

interface VoiceInterviewerProps {
  question: string;
  onTranscription?: (text: string) => void;
  isVoiceMode?: boolean;
  onVoiceModeChange?: (enabled: boolean) => void;
}

interface VoiceSettings {
  voice: string;
  speed: number;
  autoPlay: boolean;
}

interface VoiceOption {
  name: string;
  description: string;
  gender: string;
  language: string;
}

const VoiceInterviewer: React.FC<VoiceInterviewerProps> = ({
  question,
  onTranscription,
  isVoiceMode = false,
  onVoiceModeChange
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings>({
    voice: 'nova',
    speed: 1.0,
    autoPlay: true
  });
  const [availableVoices, setAvailableVoices] = useState<Record<string, VoiceOption>>({});
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioInitialized, setAudioInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const audioRef = useRef<HTMLAudioElement>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout>();
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    const initializeVoice = async () => {
      await fetchVoiceOptions();
    };
    
    initializeVoice();
    
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      // 清理音频资源
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
      }
    };
  }, []);

  useEffect(() => {
    if (question && isVoiceMode && voiceSettings.autoPlay && audioInitialized) {
      playQuestionAudio();
    }
  }, [question, isVoiceMode, voiceSettings.autoPlay, audioInitialized]);

  // 初始化音频上下文（需要用户交互）
  const initializeAudio = async () => {
    if (audioInitialized) return;
    
    try {
      // 创建一个临时的音频上下文来触发用户授权
      const tempContext = new AudioContext();
      await tempContext.resume();
      tempContext.close();
      
      setAudioInitialized(true);
      setError(null);
      console.log('[VoiceInterviewer] 音频系统已初始化');
    } catch (error) {
      console.error('[VoiceInterviewer] 音频初始化失败:', error);
      setError('音频初始化失败，请刷新页面重试');
    }
  };

  const fetchVoiceOptions = async () => {
    try {
      const response = await fetch('http://localhost:8000/speech/voices');
      const data = await response.json();
      if (data.success) {
        setAvailableVoices(data.voices);
      }
    } catch (error) {
      console.error('[VoiceInterviewer] 获取语音选项失败:', error);
      // 设置默认语音选项
      setAvailableVoices({
        'nova': { name: 'Nova', description: '自然女声', gender: 'female', language: 'zh-CN' },
        'alloy': { name: 'Alloy', description: '中性声音', gender: 'neutral', language: 'zh-CN' },
        'echo': { name: 'Echo', description: '男声', gender: 'male', language: 'zh-CN' }
      });
    }
  };

  const playQuestionAudio = async () => {
    if (!question || isPlaying) return;
    
    // 确保音频已初始化
    if (!audioInitialized) {
      await initializeAudio();
      if (!audioInitialized) return;
    }
    
    setIsPlaying(true);
    setError(null);
    
    try {
      console.log('[VoiceInterviewer] 开始播放问题音频:', { 
        question: question.substring(0, 50), 
        voice: voiceSettings.voice,
        speed: voiceSettings.speed 
      });
      
      const response = await fetch('http://localhost:8000/speech/synthesize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          text: question,
          voice: voiceSettings.voice,
          speed: voiceSettings.speed.toString()
        })
      });
      
      console.log('[VoiceInterviewer] TTS响应状态:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('[VoiceInterviewer] TTS响应错误:', errorText);
        throw new Error(`TTS请求失败: ${response.status} ${response.statusText}`);
      }
      
      const audioBlob = await response.blob();
      console.log('[VoiceInterviewer] 收到音频数据:', { 
        size: audioBlob.size, 
        type: audioBlob.type 
      });
      
      if (audioBlob.size === 0) {
        throw new Error('收到空的音频数据');
      }
      
      const audioUrl = URL.createObjectURL(audioBlob);
      
      if (audioRef.current) {
        // 清理旧的音频源
        if (audioRef.current.src && audioRef.current.src.startsWith('blob:')) {
          URL.revokeObjectURL(audioRef.current.src);
        }
        
        audioRef.current.src = audioUrl;
        audioRef.current.volume = 1.0;
        audioRef.current.muted = false;
        
        // 添加加载成功事件
        audioRef.current.onloadeddata = () => {
          console.log('[VoiceInterviewer] 音频数据加载完成');
        };
        
        // 添加播放结束事件
        audioRef.current.onended = () => {
          console.log('[VoiceInterviewer] 音频播放结束');
          setIsPlaying(false);
          URL.revokeObjectURL(audioUrl);
        };
        
        // 添加错误处理
        audioRef.current.onerror = (e) => {
          console.error('[VoiceInterviewer] 音频播放错误:', e);
          const audio = audioRef.current as HTMLAudioElement;
          let errorMsg = '音频播放失败';
          
          if (audio.error) {
            console.error('[VoiceInterviewer] 错误代码:', audio.error.code);
            switch (audio.error.code) {
              case audio.error.MEDIA_ERR_ABORTED:
                errorMsg = '音频播放被中断';
                break;
              case audio.error.MEDIA_ERR_NETWORK:
                errorMsg = '网络错误，无法加载音频';
                break;
              case audio.error.MEDIA_ERR_DECODE:
                errorMsg = '音频格式不支持或解码失败';
                break;
              case audio.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                errorMsg = '音频源不支持';
                break;
            }
          }
          
          setError(errorMsg);
          setIsPlaying(false);
          URL.revokeObjectURL(audioUrl);
        };
        
        // 尝试播放
        try {
          console.log('[VoiceInterviewer] 尝试播放音频...');
          const playPromise = audioRef.current.play();
          
          if (playPromise !== undefined) {
            await playPromise;
            console.log('[VoiceInterviewer] 音频播放成功开始');
          }
        } catch (playError) {
          console.error('[VoiceInterviewer] 播放失败:', playError);
          
          if (playError instanceof Error && playError.name === 'NotAllowedError') {
            setError('需要用户交互才能播放音频，请点击页面任意位置后重试');
            // 添加全局点击监听器
            const handleGlobalClick = async () => {
              document.removeEventListener('click', handleGlobalClick);
              await initializeAudio();
              // 重新尝试播放
              if (audioRef.current) {
                try {
                  await audioRef.current.play();
                  setError(null);
                  console.log('[VoiceInterviewer] 用户交互后播放成功');
                } catch (retryError) {
                  console.error('[VoiceInterviewer] 重试播放失败:', retryError);
                }
              }
            };
            document.addEventListener('click', handleGlobalClick);
          } else {
            setError(`播放失败: ${playError instanceof Error ? playError.message : String(playError)}`);
          }
          
          setIsPlaying(false);
          URL.revokeObjectURL(audioUrl);
        }
      }
    } catch (error) {
      console.error('[VoiceInterviewer] 播放问题语音失败:', error);
      setError(error instanceof Error ? error.message : '播放语音失败');
      setIsPlaying(false);
    }
  };

  const startVoiceRecording = async () => {
    if (isRecording) return;
    
    setError(null);
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      });
      
      // 检测支持的MIME类型
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/webm';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = 'audio/mp4';
          if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = 'audio/ogg';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
              console.warn('[VoiceInterviewer] 使用默认MIME类型');
              mimeType = '';
            }
          }
        }
      }
      
      console.log('[VoiceInterviewer] 使用MIME类型:', mimeType || '默认');
      
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      audioChunksRef.current = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log('[VoiceInterviewer] 录音数据块:', event.data.size);
        }
      };
      
      recorder.onstop = async () => {
        console.log('[VoiceInterviewer] 录音停止，总块数:', audioChunksRef.current.length);
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/webm' });
        console.log('[VoiceInterviewer] 合并后音频大小:', audioBlob.size);
        
        if (audioBlob.size > 0) {
          await submitVoiceAnswer(audioBlob);
        } else {
          setError('录音数据为空');
        }
        
        stream.getTracks().forEach(track => track.stop());
      };
      
      recorder.onerror = (event: any) => {
        console.error('[VoiceInterviewer] 录音器错误:', event.error);
        setError('录音失败: ' + event.error);
      };
      
      setMediaRecorder(recorder);
      
      recorder.start(100); // 每100ms收集一次数据
      setIsRecording(true);
      setRecordingTime(0);
      
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      console.log('[VoiceInterviewer] 录音开始');
      
    } catch (error: any) {
      console.error('[VoiceInterviewer] 开始录音失败:', error);
      let errorMsg = '无法访问麦克风';
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        errorMsg = '麦克风权限被拒绝，请在浏览器设置中允许访问麦克风';
      } else if (error.name === 'NotFoundError') {
        errorMsg = '未找到麦克风设备';
      } else if (error.name === 'NotReadableError') {
        errorMsg = '麦克风被其他程序占用';
      }
      
      setError(errorMsg);
    }
  };

  const stopVoiceRecording = () => {
    if (!isRecording || !mediaRecorder) return;
    
    console.log('[VoiceInterviewer] 停止录音，录音器状态:', mediaRecorder.state);
    
    if (mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
    
    setIsRecording(false);
    
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }
  };

  const submitVoiceAnswer = async (audioBlob: Blob) => {
    try {
      console.log('[VoiceInterviewer] 提交语音答案，大小:', audioBlob.size, '类型:', audioBlob.type);
      
      const formData = new FormData();
      formData.append('audio', audioBlob, 'answer.webm');
      formData.append('language', 'zh'); // 添加语言参数
      
      const response = await fetch('http://localhost:8000/speech/transcribe', {
        method: 'POST',
        body: formData
      });
      
      console.log('[VoiceInterviewer] 转录响应状态:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('[VoiceInterviewer] 转录响应错误:', errorText);
        throw new Error(`转录请求失败: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('[VoiceInterviewer] 转录结果:', data);
      
      if (data.success && data.text && onTranscription) {
        onTranscription(data.text);
        setError(null);
      } else {
        setError(data.error || '语音识别失败');
      }
    } catch (error: any) {
      console.error('[VoiceInterviewer] 提交语音回答失败:', error);
      setError(error.message || '语音识别失败');
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 处理语音模式切换
  const handleVoiceModeToggle = async () => {
    const newMode = !isVoiceMode;
    
    // 如果开启语音模式，先初始化音频
    if (newMode && !audioInitialized) {
      await initializeAudio();
    }
    
    onVoiceModeChange?.(newMode);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      {/* 错误提示 */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}
      
      {/* 虚拟面试官头像区域 */}
      <div className="text-center mb-6">
        <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mx-auto mb-4 flex items-center justify-center">
          <div className={`w-4 h-4 bg-white rounded-full ${isPlaying ? 'animate-pulse' : ''}`}></div>
        </div>
        <h3 className="text-lg font-semibold text-gray-800">AI面试官</h3>
        <p className="text-sm text-gray-500">
          {isPlaying ? '正在朗读问题...' : isRecording ? '正在聆听您的回答...' : '准备就绪'}
        </p>
      </div>

      {/* 语音模式开关 */}
      <div className="mb-6">
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <h4 className="font-medium text-gray-800">语音交互模式</h4>
            <p className="text-sm text-gray-500">启用语音问答，让面试更真实</p>
          </div>
          <button
            onClick={handleVoiceModeToggle}
            title={isVoiceMode ? '关闭语音模式' : '开启语音模式'}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              isVoiceMode ? 'bg-blue-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                isVoiceMode ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* 语音设置 */}
      {isVoiceMode && (
        <div className="mb-6 space-y-4">
          <h4 className="font-medium text-gray-800">语音设置</h4>
          
          {/* 音频初始化提示 */}
          {!audioInitialized && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                首次使用需要初始化音频系统，请点击下方按钮
              </p>
              <button
                onClick={initializeAudio}
                className="mt-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-md text-sm"
              >
                初始化音频
              </button>
            </div>
          )}
          
          {/* 语音选择 */}
          <div>
            <label htmlFor="voice-select" className="block text-sm font-medium text-gray-700 mb-2">
              面试官声音
            </label>
            <select
              id="voice-select"
              value={voiceSettings.voice}
              onChange={(e) => setVoiceSettings(prev => ({...prev, voice: e.target.value}))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {Object.entries(availableVoices).map(([key, voice]) => (
                <option key={key} value={key}>
                  {voice.name} - {voice.description}
                </option>
              ))}
            </select>
          </div>
          
          {/* 语速控制 */}
          <div>
            <label htmlFor="speed-slider" className="block text-sm font-medium text-gray-700 mb-2">
              语速: {voiceSettings.speed.toFixed(1)}x
            </label>
            <input
              id="speed-slider"
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={voiceSettings.speed}
              onChange={(e) => setVoiceSettings(prev => ({...prev, speed: parseFloat(e.target.value)}))}
              className="w-full"
              title={`语速: ${voiceSettings.speed.toFixed(1)}x`}
            />
          </div>
          
          {/* 自动播放 */}
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={voiceSettings.autoPlay}
              onChange={(e) => setVoiceSettings(prev => ({...prev, autoPlay: e.target.checked}))}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">自动播放新问题</span>
          </label>
        </div>
      )}

      {/* 问题显示区域 */}
      <div className="mb-6">
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-lg">
          <p className="text-gray-800 leading-relaxed">{question}</p>
        </div>
      </div>

      {/* 语音控制按钮 */}
      {isVoiceMode && (
        <div className="space-y-4">
          {/* 播放问题按钮 */}
          <button
            onClick={playQuestionAudio}
            disabled={isPlaying || !question || !audioInitialized}
            className="w-full flex items-center justify-center px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
            {isPlaying ? '正在播放...' : '🔊 播放问题'}
          </button>
          
          {/* 录音按钮 */}
          <button
            onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
            disabled={isPlaying}
            className={`w-full flex items-center justify-center px-4 py-3 rounded-lg transition-colors ${
              isRecording
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white'
            } disabled:bg-gray-400`}
          >
            {isRecording ? (
              <>
                <div className="w-3 h-3 bg-white rounded-full animate-pulse mr-2"></div>
                停止录音 ({formatTime(recordingTime)})
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                🎤 开始语音回答
              </>
            )}
          </button>
        </div>
      )}
      
      {/* 隐藏的音频播放器 */}
      <audio
        ref={audioRef}
        crossOrigin="anonymous"
        preload="auto"
        style={{ display: 'none' }}
      />
      
      {/* 技术提示 */}
      {isVoiceMode && (
        <div className="mt-4 text-xs text-gray-500">
          <p>💡 技术说明：</p>
          <ul className="list-disc list-inside space-y-1 mt-1">
                            <li>使用本地Whisper进行语音识别</li>
                <li>基于本地TTS引擎的智能语音合成</li>
            <li>支持实时语音特征分析</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default VoiceInterviewer; 