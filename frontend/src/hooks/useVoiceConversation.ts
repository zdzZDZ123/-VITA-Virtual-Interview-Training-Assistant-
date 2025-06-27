import { useState, useRef, useCallback, useEffect } from 'react';

interface VoiceMessage {
  type: 'user' | 'assistant';
  text: string;
  timestamp: Date;
  audioUrl?: string;
}

interface VoiceConversationState {
  isConnected: boolean;
  isRecording: boolean;
  isPlaying: boolean;
  isProcessing: boolean;
  partialText: string;
  finalText: string;
  assistantText: string;
  messages: VoiceMessage[];
  error?: string;
  networkStatus: 'connected' | 'connecting' | 'disconnected' | 'error';
}

interface VoiceConversationConfig {
  sessionId: string;
  sampleRate?: number;
  channels?: number;
  silenceTimeout?: number;
}

export const useVoiceConversation = (config: VoiceConversationConfig) => {
  const {
    sessionId,
    sampleRate = 16000,
    channels = 1,
    silenceTimeout = 1500
  } = config;

  // 状态管理
  const [state, setState] = useState<VoiceConversationState>({
    isConnected: false,
    isRecording: false,
    isPlaying: false,
    isProcessing: false,
    partialText: '',
    finalText: '',
    assistantText: '',
    messages: [],
    networkStatus: 'disconnected'
  });

  // 引用管理
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  // const audioWorkletRef = useRef<AudioWorkletNode | null>(null); // 预留给未来的音频处理
  const playbackContextRef = useRef<AudioContext | null>(null);
  const audioBufferQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const recordingChunksRef = useRef<Blob[]>([]);

  // 更新状态的辅助函数
  const updateState = useCallback((updates: Partial<VoiceConversationState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // 添加消息
  const addMessage = useCallback((message: VoiceMessage) => {
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, message]
    }));
  }, []);

  // 重连相关状态
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 初始化WebSocket连接
  const initializeWebSocket = useCallback(() => {
    const wsUrl = `ws://localhost:8000/api/v1/ws/voice/${sessionId}`;
    
    console.log('[useVoiceConversation:WebSocket] 正在初始化WebSocket连接...');
    console.log('[useVoiceConversation:WebSocket] 连接URL:', wsUrl);
    
    // 清除之前的重连定时器
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    updateState({ networkStatus: 'connecting' });
    
    const ws = new WebSocket(wsUrl);
    // 统一binaryType，确保收到的二进制消息为ArrayBuffer，避免浏览器差异导致的解码错误
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[useVoiceConversation:WebSocket] WebSocket连接已建立');
      console.log('[useVoiceConversation:WebSocket] 连接状态:', ws.readyState);
      reconnectAttemptsRef.current = 0; // 重置重连计数器
      updateState({ 
        isConnected: true, 
        networkStatus: 'connected',
        error: undefined 
      });
    };

    ws.onmessage = async (event) => {
      try {
        if (typeof event.data === 'string') {
          // 处理文本消息
          console.log('[useVoiceConversation:WebSocket] 收到文本消息，长度:', event.data.length);
          const message = JSON.parse(event.data);
          console.log('[useVoiceConversation:WebSocket] 解析后的消息:', message);
          await handleWebSocketMessage(message);
        } else {
          // 处理音频数据
          console.log('[useVoiceConversation:WebSocket] 收到二进制数据，大小:', event.data.byteLength);
          await handleAudioData(event.data);
        }
      } catch (error) {
        console.error('[useVoiceConversation:WebSocket] 处理WebSocket消息失败:', error);
      }
    };

    ws.onclose = (event) => {
      console.log('[useVoiceConversation:WebSocket] WebSocket连接已关闭');
      console.log('[useVoiceConversation:WebSocket] 关闭详情:', {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean
      });
      updateState({ 
        isConnected: false, 
        networkStatus: 'disconnected' 
      });
      
      // 自动重连逻辑（非主动关闭时）
      if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
        const reconnectDelay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        console.log(`[useVoiceConversation:WebSocket] 尝试重连 (${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})，${reconnectDelay}ms后重试`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++;
          initializeWebSocket();
        }, reconnectDelay);
      } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
        console.error('[useVoiceConversation:WebSocket] 已达到最大重连次数，停止重连');
        updateState({ 
          networkStatus: 'error',
          error: '连接失败，已达到最大重连次数' 
        });
      }
    };

    ws.onerror = (error: unknown) => {
      console.error('[useVoiceConversation:WebSocket] WebSocket错误:', error);
      console.error('[useVoiceConversation:WebSocket] 错误类型:', typeof error);
      updateState({ 
        networkStatus: 'error',
        error: 'WebSocket连接错误' 
      });
    };

  }, [sessionId]);

  // 处理WebSocket消息
  const handleWebSocketMessage = useCallback(async (message: { event: string; text?: string; message?: string; timestamp?: string; [key: string]: unknown }) => {
    const { event, text } = message;
    
    console.log('[useVoiceConversation:WebSocket] 处理消息事件:', event);

    switch (event) {
      case 'partial_transcript':
        if (text) {
          console.log('[useVoiceConversation:WebSocket] 部分转录文本:', text);
          updateState({ partialText: text });
        }
        break;

      case 'final_transcript':
        if (text) {
          console.log('[useVoiceConversation:WebSocket] 最终转录文本:', text);
          updateState({ 
            finalText: text, 
            partialText: '' 
          });
          addMessage({
            type: 'user',
            text,
            timestamp: new Date()
          });
        }
        break;

      case 'assistant_text':
        if (text) {
          console.log('[useVoiceConversation:WebSocket] 助手回复文本:', text);
          updateState({ assistantText: text });
          addMessage({
            type: 'assistant',
            text,
            timestamp: new Date()
          });
        }
        break;

      case 'speech_start':
        console.log('[useVoiceConversation:WebSocket] 语音播放开始');
        updateState({ isPlaying: true });
        if (!playbackContextRef.current) {
          playbackContextRef.current = new AudioContext();
          console.log('[useVoiceConversation:WebSocket] 创建播放音频上下文');
        }
        if (playbackContextRef.current.state === 'suspended') {
          console.log('[useVoiceConversation:WebSocket] 恢复音频上下文');
          await playbackContextRef.current.resume();
        }
        break;

      case 'speech_end':
        console.log('[useVoiceConversation:WebSocket] 语音播放结束');
        updateState({ isPlaying: false });
        break;

      case 'listening_started':
        console.log('[useVoiceConversation:WebSocket] 开始监听');
        updateState({ isProcessing: true });
        break;

      case 'listening_stopped':
        console.log('[useVoiceConversation:WebSocket] 停止监听');
        updateState({ isProcessing: false });
        break;

      case 'error':
        console.error('[useVoiceConversation:WebSocket] 服务器错误:', message.message);
        updateState({ error: message.message });
        break;

      case 'pong':
        console.log('[useVoiceConversation:WebSocket] 收到心跳响应');
        // 心跳响应
        break;

      default:
        console.log('[useVoiceConversation:WebSocket] 未知消息类型:', event);
    }
  }, [addMessage, updateState]);

  // 处理音频数据
  const handleAudioData = useCallback(async (audioData: Blob | ArrayBuffer) => {
    if (!playbackContextRef.current) {
      console.warn('[useVoiceConversation:Audio] 播放上下文未初始化，无法处理音频');
      return;
    }

    try {
      // 根据数据类型统一为 ArrayBuffer
      let arrayBuffer: ArrayBuffer;
      if (audioData instanceof Blob) {
        console.log('[useVoiceConversation:Audio] 将Blob转换为ArrayBuffer，大小:', audioData.size);
        arrayBuffer = await audioData.arrayBuffer();
      } else if (audioData instanceof ArrayBuffer) {
        console.log('[useVoiceConversation:Audio] 直接使用ArrayBuffer，大小:', audioData.byteLength);
        arrayBuffer = audioData;
      } else {
        console.warn('[useVoiceConversation:Audio] 收到未知类型的音频数据，已忽略', typeof audioData);
        return;
      }

      console.log('[useVoiceConversation:Audio] 开始解码音频数据...');
      const audioBuffer = await playbackContextRef.current.decodeAudioData(arrayBuffer);
      console.log('[useVoiceConversation:Audio] 音频解码成功，时长:', audioBuffer.duration, '秒');
      
      // 添加到播放队列
      audioBufferQueueRef.current.push(audioBuffer);
      console.log('[useVoiceConversation:Audio] 音频已添加到播放队列，队列长度:', audioBufferQueueRef.current.length);
      
      // 如果当前没有播放，开始播放
      if (!isPlayingRef.current) {
        console.log('[useVoiceConversation:Audio] 开始播放音频队列');
        await playNextAudioBuffer();
      }
    } catch (error: unknown) {
      console.error('[useVoiceConversation:Audio] 音频解码失败:', error);
      updateState({ error: '音频解码失败，可能浏览器不支持该格式' });
    }
  }, []);

  // 播放下一个音频缓冲区
  const playNextAudioBuffer = useCallback(async () => {
    if (!playbackContextRef.current || audioBufferQueueRef.current.length === 0) {
      console.log('[useVoiceConversation:Audio] 播放队列为空或上下文未初始化，停止播放');
      isPlayingRef.current = false;
      return;
    }

    isPlayingRef.current = true;
    const audioBuffer = audioBufferQueueRef.current.shift()!;
    console.log('[useVoiceConversation:Audio] 播放音频缓冲区，时长:', audioBuffer.duration, '秒，剩余队列:', audioBufferQueueRef.current.length);
    
    const source = playbackContextRef.current.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(playbackContextRef.current.destination);
    
    source.onended = () => {
      console.log('[useVoiceConversation:Audio] 音频缓冲区播放完成');
      // 播放完成，继续播放队列中的下一个
      playNextAudioBuffer();
    };
    
    console.log('[useVoiceConversation:Audio] 开始播放音频缓冲区');
    source.start();
  }, []);

  // 初始化音频录制
  const initializeAudioRecording = useCallback(async () => {
    try {
      // 停止现有录制（防止冲突）
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }

      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate,
          channelCount: channels,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      mediaStreamRef.current = stream;

      // 创建AudioContext用于音频处理
      audioContextRef.current = new AudioContext({ sampleRate });
      
      // 创建音频源节点
      audioSourceRef.current = audioContextRef.current.createMediaStreamSource(stream);

      // 检查浏览器兼容性并选择合适的编码格式
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

      // 创建MediaRecorder用于录制
      const options: MediaRecorderOptions | undefined = mimeType ? { mimeType } : undefined;

      try {
        mediaRecorderRef.current = new MediaRecorder(stream, options);
      } catch (err: unknown) {
        console.warn('使用 mimeType 创建 MediaRecorder 失败，尝试使用默认参数', err);
        try {
          mediaRecorderRef.current = new MediaRecorder(stream);
        } catch (err2: unknown) {
          console.error('无法创建 MediaRecorder:', err2);
          updateState({ error: '浏览器不支持音频录制或麦克风被占用' });
          return false;
        }
      }

      // 处理录制数据
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordingChunksRef.current.push(event.data);
          // 发送音频数据到服务器
          sendAudioChunk(event.data);
        }
      };

      return true;
    } catch (error: unknown) {
      console.error('初始化音频录制失败:', error);

      let friendlyMsg = '无法访问麦克风';
      if (error && typeof error === 'object' && 'name' in error) {
        const errName = (error as DOMException).name;
        switch (errName) {
          case 'NotAllowedError':
          case 'PermissionDeniedError':
            friendlyMsg = '麦克风访问被拒绝，请在浏览器地址栏右侧允许权限';
            break;
          case 'NotFoundError':
            friendlyMsg = '未检测到麦克风设备，请检查硬件连接';
            break;
          case 'NotReadableError':
            friendlyMsg = '麦克风被其他程序占用，请关闭冲突应用';
            break;
          case 'OverconstrainedError':
            friendlyMsg = '麦克风设备不支持所需的音频参数';
            break;
          default:
            break;
        }
      }
      updateState({ error: friendlyMsg });
      return false;
    }
  }, [sampleRate, channels]);

  // 发送音频数据块
  const sendAudioChunk = useCallback((audioBlob: Blob) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('[useVoiceConversation:Audio] 发送音频数据块，大小:', audioBlob.size);
      // 转换为ArrayBuffer并发送
      audioBlob.arrayBuffer().then(buffer => {
        console.log('[useVoiceConversation:Audio] ArrayBuffer转换完成，大小:', buffer.byteLength);
        wsRef.current?.send(buffer);
      });
    } else {
      console.warn('[useVoiceConversation:Audio] 无法发送音频数据，WebSocket未连接或未打开');
    }
  }, []);

  // 防抖状态
  const isActionInProgressRef = useRef(false);

  // 开始录音
  const startRecording = useCallback(async () => {
    if (!state.isConnected || state.isRecording || isActionInProgressRef.current) {
      return false;
    }

    isActionInProgressRef.current = true;

    try {
      if (!mediaRecorderRef.current) {
        const initialized = await initializeAudioRecording();
        if (!initialized) {
          isActionInProgressRef.current = false;
          return false;
        }
      }

      // 确保之前的录制已停止
      if (mediaRecorderRef.current?.state === 'recording') {
        mediaRecorderRef.current.stop();
        await new Promise(resolve => setTimeout(resolve, 100)); // 等待停止完成
      }

      // 清空之前的录制数据
      recordingChunksRef.current = [];
      
      // 发送开始监听信号
      wsRef.current?.send(JSON.stringify({
        event: 'start_listening'
      }));

      // 开始录制，每100ms发送一次数据
      mediaRecorderRef.current?.start(100);
      
      updateState({ 
        isRecording: true,
        partialText: '',
        finalText: '',
        error: undefined
      });

      // 设置静音检测定时器
      silenceTimerRef.current = setTimeout(() => {
        stopRecording();
      }, silenceTimeout);

      return true;
    } catch (error: unknown) {
      console.error('开始录音失败:', error);
      updateState({ error: '开始录音失败' });
      return false;
    } finally {
      isActionInProgressRef.current = false;
    }
  }, [state.isConnected, state.isRecording, initializeAudioRecording, silenceTimeout]);

  // 停止录音
  const stopRecording = useCallback(() => {
    if (!state.isRecording || isActionInProgressRef.current) return;

    isActionInProgressRef.current = true;

    try {
      // 停止录制
      mediaRecorderRef.current?.stop();
      
      // 发送停止监听信号
      wsRef.current?.send(JSON.stringify({
        event: 'stop_listening'
      }));

      // 清除静音定时器
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }

      updateState({ isRecording: false });
    } catch (error: unknown) {
      console.error('停止录音失败:', error);
    } finally {
      isActionInProgressRef.current = false;
    }
  }, [state.isRecording]);

  // 发送文本消息进行TTS
  const speakText = useCallback((text: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        event: 'start_speaking',
        text
      }));
    }
  }, []);

  // 清理函数
  const cleanup = useCallback(() => {
    // 停止录音
    if (state.isRecording) {
      stopRecording();
    }

    // 清除重连定时器
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // 清除静音定时器
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    // 关闭媒体流
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
    }

    // 关闭AudioContext
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }

    if (playbackContextRef.current) {
      playbackContextRef.current.close();
    }

    // 关闭WebSocket
    if (wsRef.current) {
      wsRef.current.close();
    }

    // 清除定时器
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
  }, [state.isRecording, stopRecording]);

  // 心跳检测
  useEffect(() => {
    if (!state.isConnected) return;

    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ event: 'ping' }));
      }
    }, 30000); // 30秒心跳

    return () => clearInterval(pingInterval);
  }, [state.isConnected]);

  // 组件卸载时清理
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  return {
    // 状态
    ...state,
    
    // 操作函数
    connect: initializeWebSocket,
    disconnect: cleanup,
    startRecording,
    stopRecording,
    speakText,
    
    // 工具函数
    toggleRecording: state.isRecording ? stopRecording : startRecording,
    clearMessages: () => updateState({ messages: [] }),
    clearError: () => updateState({ error: undefined })
  };
}; 