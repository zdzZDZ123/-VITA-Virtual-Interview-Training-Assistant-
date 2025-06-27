import React, { useEffect, useState } from 'react';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Wifi, 
  WifiOff,
  Activity,
  MessageSquare,
  Phone,
  PhoneOff
} from 'lucide-react';
import { useVoiceConversation } from '../../hooks/useVoiceConversation';
import { formatTime } from '../../utils/timeFormat';

interface RealTimeVoiceConversationProps {
  sessionId: string;
  onSessionEnd?: () => void;
  autoConnect?: boolean;
}

export const RealTimeVoiceConversation: React.FC<RealTimeVoiceConversationProps> = ({
  sessionId,
  onSessionEnd,
  autoConnect = true
}) => {
  const [conversationStartTime] = useState(new Date());
  const [showTranscript, setShowTranscript] = useState(true);
  
  const voiceConversation = useVoiceConversation({
    sessionId,
    silenceTimeout: 3000 // 3秒静音后自动停止录音
  });

  const {
    isConnected,
    isRecording,
    isPlaying,
    isProcessing,
    partialText,
    finalText,
    assistantText,
    messages,
    error,
    networkStatus,
    connect,
    disconnect,
    startRecording,
    stopRecording,
    toggleRecording,
    clearMessages,
    clearError
  } = voiceConversation;

  // 自动连接
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    // 组件卸载时断开连接
    return () => {
      disconnect();
    };
  }, [connect, disconnect, autoConnect]);

  // 计算对话时长
  const getConversationDuration = () => {
    const now = new Date();
    const diff = now.getTime() - conversationStartTime.getTime();
    return Math.floor(diff / 1000);
  };

  // 获取网络状态显示
  const getNetworkStatusIcon = () => {
    switch (networkStatus) {
      case 'connected':
        return <Wifi className="w-5 h-5 text-green-500" />;
      case 'connecting':
        return <Activity className="w-5 h-5 text-yellow-500 animate-pulse" />;
      case 'disconnected':
      case 'error':
        return <WifiOff className="w-5 h-5 text-red-500" />;
    }
  };

  // 获取麦克风状态显示
  const getMicrophoneButton = () => {
    if (!isConnected) {
      return (
        <button
          disabled
          className="w-16 h-16 rounded-full bg-gray-300 flex items-center justify-center cursor-not-allowed"
        >
          <MicOff className="w-8 h-8 text-gray-500" />
        </button>
      );
    }

    if (isRecording) {
      return (
        <button
          onClick={stopRecording}
          className="w-16 h-16 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center transition-colors animate-pulse"
        >
          <Mic className="w-8 h-8 text-white" />
        </button>
      );
    }

    return (
      <button
        onClick={startRecording}
        className="w-16 h-16 rounded-full bg-blue-500 hover:bg-blue-600 flex items-center justify-center transition-colors"
      >
        <Mic className="w-8 h-8 text-white" />
      </button>
    );
  };

  // 结束对话
  const handleEndConversation = () => {
    disconnect();
    onSessionEnd?.();
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      {/* 头部状态栏 */}
      <div className="flex items-center justify-between mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-4">
          {/* 网络状态 */}
          <div className="flex items-center space-x-2">
            {getNetworkStatusIcon()}
            <span className="text-sm font-medium text-gray-700">
              {networkStatus === 'connected' ? '已连接' :
               networkStatus === 'connecting' ? '连接中...' :
               networkStatus === 'error' ? '连接错误' : '未连接'}
            </span>
          </div>

          {/* 对话时长 */}
          <div className="flex items-center space-x-2">
            <MessageSquare className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">
              {formatTime(getConversationDuration())}
            </span>
          </div>

          {/* 消息数量 */}
          <div className="text-sm text-gray-600">
            {messages.length} 条消息
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* 转录开关 */}
          <button
            onClick={() => setShowTranscript(!showTranscript)}
            className={`px-3 py-1 rounded text-sm ${
              showTranscript 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            转录
          </button>

          {/* 结束对话 */}
          <button
            onClick={handleEndConversation}
            className="flex items-center space-x-1 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200"
          >
            <PhoneOff className="w-4 h-4" />
            <span>结束</span>
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center justify-between">
            <p className="text-red-700">{error}</p>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* 主对话区域 */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* 左侧：录音控制 */}
        <div className="lg:w-1/3">
          <div className="bg-gray-50 rounded-lg p-6 text-center">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              语音控制
            </h3>

            {/* 麦克风按钮 */}
            <div className="mb-6">
              {getMicrophoneButton()}
            </div>

            {/* 状态指示 */}
            <div className="space-y-2 text-sm">
              {isRecording && (
                <div className="flex items-center justify-center text-red-600">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse mr-2"></div>
                  正在录音...
                </div>
              )}
              
              {isProcessing && (
                <div className="flex items-center justify-center text-blue-600">
                  <Activity className="w-4 h-4 animate-spin mr-2" />
                  处理中...
                </div>
              )}
              
              {isPlaying && (
                <div className="flex items-center justify-center text-green-600">
                  <Volume2 className="w-4 h-4 mr-2" />
                  AI 正在说话...
                </div>
              )}
            </div>

            {/* 实时转录 */}
            {showTranscript && (partialText || finalText) && (
              <div className="mt-4 p-3 bg-white rounded border">
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  实时转录
                </h4>
                {partialText && (
                  <p className="text-sm text-gray-500 italic">
                    {partialText}
                  </p>
                )}
                {finalText && (
                  <p className="text-sm text-gray-800 font-medium">
                    {finalText}
                  </p>
                )}
              </div>
            )}

            {/* 操作按钮 */}
            <div className="mt-6 space-y-2">
              <button
                onClick={toggleRecording}
                disabled={!isConnected}
                className={`w-full py-2 px-4 rounded text-sm font-medium ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 text-white'
                    : 'bg-blue-500 hover:bg-blue-600 text-white disabled:bg-gray-300'
                }`}
              >
                {isRecording ? '停止录音' : '开始录音'}
              </button>

              <button
                onClick={clearMessages}
                className="w-full py-2 px-4 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded text-sm"
              >
                清空对话
              </button>
            </div>
          </div>
        </div>

        {/* 右侧：对话历史 */}
        <div className="lg:w-2/3">
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              对话记录
            </h3>

            <div className="space-y-4 max-h-96 overflow-y-auto">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>开始语音对话...</p>
                  <p className="text-sm mt-1">点击麦克风按钮开始录音</p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-100 border-l-4 border-blue-500'
                        : 'bg-green-100 border-l-4 border-green-500'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-sm font-medium ${
                        message.type === 'user' ? 'text-blue-700' : 'text-green-700'
                      }`}>
                        {message.type === 'user' ? '👤 你' : '🤖 AI面试官'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-gray-800">{message.text}</p>
                  </div>
                ))
              )}
            </div>

            {/* 当前AI回复 */}
            {assistantText && (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center mb-2">
                  <Activity className="w-4 h-4 text-yellow-600 animate-spin mr-2" />
                  <span className="text-sm font-medium text-yellow-700">
                    AI 正在回复...
                  </span>
                </div>
                <p className="text-gray-800">{assistantText}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 底部提示 */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-800 mb-2">使用提示</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• 点击麦克风按钮开始录音，停顿1.5秒后自动停止</li>
          <li>• AI会自动分析你的回答并提出下一个问题</li>
          <li>• 保持安静的环境以获得最佳语音识别效果</li>
          <li>• 可以随时点击"结束"按钮结束对话</li>
        </ul>
      </div>
    </div>
  );
}; 