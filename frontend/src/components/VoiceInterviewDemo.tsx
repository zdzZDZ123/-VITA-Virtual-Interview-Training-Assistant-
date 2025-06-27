import React, { useState, useRef } from 'react';

interface VoiceTestResult {
  text: string;
  duration: number;
  wordCount: number;
  confidence: number;
}

const VoiceInterviewDemo: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [transcriptionResult, setTranscriptionResult] = useState<VoiceTestResult | null>(null);
  const [testText, setTestText] = useState('你好，欢迎参加VITA虚拟面试系统。请简单介绍一下自己。');
  const [selectedVoice, setSelectedVoice] = useState('nova');
  const [recordingTime, setRecordingTime] = useState(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const timerRef = useRef<NodeJS.Timeout>();

  const voiceOptions = [
    { value: 'alloy', label: 'Alloy - 中性平衡' },
    { value: 'echo', label: 'Echo - 男性声音' },
    { value: 'fable', label: 'Fable - 英式口音' },
    { value: 'onyx', label: 'Onyx - 深沉男声' },
    { value: 'nova', label: 'Nova - 女性声音' },
    { value: 'shimmer', label: 'Shimmer - 柔和女声' }
  ];

  const sampleTexts = [
    '你好，欢迎参加VITA虚拟面试系统。请简单介绍一下自己。',
    '请描述一次你克服困难的经历，以及你从中学到了什么。',
    '你认为自己最大的优势是什么？请举例说明。',
    '为什么你想要这个职位？你能为我们公司带来什么价值？'
  ];

  const synthesizeSpeech = async () => {
    if (isPlaying) return;
    
    setIsPlaying(true);
    
    try {
      const response = await fetch('http://localhost:8000/speech/synthesize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          text: testText,
          voice: selectedVoice,
          speed: '1.0'
        })
      });
      
      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          await audioRef.current.play();
        }
      } else {
        throw new Error('语音合成失败');
      }
    } catch (error) {
      console.error('语音合成错误:', error);
      alert('语音合成失败，请检查后端服务');
    } finally {
      setIsPlaying(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      const chunks: Blob[] = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
        
        // 停止所有音轨
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      
      setIsRecording(true);
      setRecordingTime(0);
      
      // 开始计时
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('录音失败:', error);
      alert('无法访问麦克风，请检查权限设置');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('language', 'zh');
      
      const response = await fetch('http://localhost:8000/speech/transcribe', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.success) {
        setTranscriptionResult({
          text: data.text,
          duration: data.duration || 0,
          wordCount: data.word_count || 0,
          confidence: data.confidence || 0
        });
      } else {
        throw new Error('转录失败');
      }
    } catch (error) {
      console.error('语音转录错误:', error);
      alert('语音转录失败，请检查后端服务');
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">🎙️ VITA 语音功能演示</h1>
        <p className="text-gray-600">测试语音合成和语音识别功能</p>
      </div>

      {/* 语音合成测试 */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">🔊 语音合成测试</h2>
        
        <div className="space-y-4">
          {/* 文本输入 */}
          <div>
            <label htmlFor="test-text" className="block text-sm font-medium text-gray-700 mb-2">
              测试文本
            </label>
            <textarea
              id="test-text"
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              placeholder="输入要合成为语音的文本..."
            />
          </div>

          {/* 快速选择文本 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">快速选择</label>
            <div className="grid md:grid-cols-2 gap-2">
              {sampleTexts.map((text, index) => (
                <button
                  key={index}
                  onClick={() => setTestText(text)}
                  className="text-left p-2 text-sm bg-gray-50 hover:bg-gray-100 rounded border"
                >
                  {text.substring(0, 50)}...
                </button>
              ))}
            </div>
          </div>

          {/* 语音选择 */}
          <div>
            <label htmlFor="voice-select" className="block text-sm font-medium text-gray-700 mb-2">
              选择语音
            </label>
            <select
              id="voice-select"
              value={selectedVoice}
              onChange={(e) => setSelectedVoice(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {voiceOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* 合成按钮 */}
          <button
            onClick={synthesizeSpeech}
            disabled={isPlaying || !testText.trim()}
            className="w-full flex items-center justify-center px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
          >
            {isPlaying ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                正在播放...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728" />
                </svg>
                🔊 播放语音
              </>
            )}
          </button>
        </div>
      </div>

      {/* 语音识别测试 */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">🎤 语音识别测试</h2>
        
        <div className="space-y-4">
          <p className="text-gray-600">点击下方按钮开始录音，再次点击停止录音并查看识别结果</p>
          
          {/* 录音按钮 */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`w-full flex items-center justify-center px-4 py-3 rounded-lg transition-colors ${
              isRecording
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {isRecording ? (
              <>
                <div className="w-4 h-4 bg-white rounded-full animate-pulse mr-2"></div>
                🛑 停止录音 ({formatTime(recordingTime)})
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                🎤 开始录音
              </>
            )}
          </button>

          {/* 识别结果 */}
          {transcriptionResult && (
            <div className="bg-gray-50 border rounded-lg p-4">
              <h3 className="font-medium text-gray-800 mb-2">识别结果</h3>
              <div className="space-y-2">
                <p className="text-gray-900 border-l-4 border-blue-400 pl-3">
                  "{transcriptionResult.text}"
                </p>
                <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
                  <div>
                    <span className="font-medium">时长:</span> {transcriptionResult.duration.toFixed(1)}秒
                  </div>
                  <div>
                    <span className="font-medium">词数:</span> {transcriptionResult.wordCount}个
                  </div>
                  <div>
                    <span className="font-medium">置信度:</span> {(transcriptionResult.confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 功能说明 */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">✨ 功能特点</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-gray-800 mb-2">🎯 语音合成 (TTS)</h3>
            <ul className="text-sm text-gray-600 space-y-1">
                              <li>• 基于本地TTS引擎</li>
              <li>• 支持6种不同声音风格</li>
              <li>• 高质量自然语音输出</li>
              <li>• 支持语速调节</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-gray-800 mb-2">🎤 语音识别 (STT)</h3>
            <ul className="text-sm text-gray-600 space-y-1">
                              <li>• 基于本地Whisper模型</li>
              <li>• 支持中文和英文识别</li>
              <li>• 高准确度转录</li>
              <li>• 实时语音特征分析</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 隐藏的音频播放器 */}
      <audio
        ref={audioRef}
        onEnded={() => setIsPlaying(false)}
        style={{ display: 'none' }}
      />
    </div>
  );
};

export default VoiceInterviewDemo; 