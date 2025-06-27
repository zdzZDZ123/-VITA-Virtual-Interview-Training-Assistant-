# VITA 语音功能实现文档

## 🎙️ 功能概述

VITA的语音功能模块实现了完整的语音交互体验，包括：

1. **语音合成 (Text-to-Speech)**：将文字转换为自然语音
2. **语音识别 (Speech-to-Text)**：将语音转录为文字
3. **语音分析**：分析语音特征和表现质量
4. **实时语音交互**：支持真实的面试对话体验

## 🏗️ 技术架构

### 后端服务层
```
backend/core/speech.py
├── SpeechService        # 核心语音服务类
├── VoiceInterviewer     # 语音面试官类
└── 辅助函数             # 语音分析和格式化
```

### API端点
```
/speech/transcribe           # 语音转文字
/speech/synthesize          # 文字转语音
/speech/analyze            # 语音特征分析
/speech/voices             # 获取可用语音选项
/session/{id}/question/audio    # 获取问题语音
/session/{id}/answer/voice     # 提交语音回答
```

### 前端组件
```
frontend/src/components/
├── VoiceInterviewer.tsx      # 语音交互组件
├── VoiceInterviewDemo.tsx    # 语音功能演示
└── InterviewRoom.tsx         # 集成语音的面试界面
```

## 🎯 核心功能详解

### 1. 语音合成 (TTS)

**技术栈**：OpenAI TTS API
**支持格式**：MP3
**语音选项**：6种不同风格的声音

```python
# 使用示例
audio_data = await speech_service.text_to_speech(
    text="你好，欢迎参加面试",
    voice="nova",      # 女性声音
    speed=1.0          # 正常语速
)
```

**可用语音类型**：
- `alloy` - 中性、平衡的声音
- `echo` - 男性声音
- `fable` - 英式口音
- `onyx` - 深沉男性声音
- `nova` - 女性声音 (推荐)
- `shimmer` - 柔和女性声音

### 2. 语音识别 (STT)

**技术栈**：OpenAI Whisper API
**支持格式**：webm, mp3, wav, m4a等
**支持语言**：中文、英文等多语言

```python
# 使用示例
result = await speech_service.speech_to_text(
    audio_data=audio_bytes,
    language="zh"
)
# 返回: { "text": "识别的文字", "duration": 3.5, "words": [...] }
```

**功能特性**：
- 高精度转录（通常>95%准确率）
- 支持时间戳标记
- 词级别的置信度评分
- 支持长音频（最长25MB）

### 3. 语音特征分析

分析维度包括：
- **语速**：每分钟词数 (WPM)
- **停顿分析**：停顿次数、平均停顿时长
- **流畅度评分**：基于停顿和语速的综合评分
- **语音时长**：总说话时间

```python
# 分析示例
features = await speech_service.analyze_speech_features(audio_data)
# 返回完整的语音特征数据
```

### 4. 虚拟面试官语音

**智能化特性**：
- 自动格式化问题文本，增加适当停顿
- 为不同类型内容调整语调和语速
- 支持自定义语音配置

```python
# 面试官提问
audio = await voice_interviewer.speak_question(
    "请简单介绍一下您的工作经验"
)

# 反馈朗读
audio = await voice_interviewer.speak_feedback(
    "您的回答结构清晰，表达流畅"
)
```

## 🔧 API使用指南

### 语音合成API

```bash
curl -X POST "http://localhost:8000/speech/synthesize" \
  -F "text=你好，欢迎参加面试" \
  -F "voice=nova" \
  -F "speed=1.0"
```

**响应**：返回MP3音频文件

### 语音转录API

```bash
curl -X POST "http://localhost:8000/speech/transcribe" \
  -F "audio=@recording.webm" \
  -F "language=zh"
```

**响应**：
```json
{
  "success": true,
  "text": "你好，我是张三",
  "duration": 2.5,
  "word_count": 6,
  "confidence": 0.95
}
```

### 语音分析API

```bash
curl -X POST "http://localhost:8000/speech/analyze" \
  -F "audio=@recording.webm"
```

**响应**：
```json
{
  "success": true,
  "features": {
    "duration": 15.3,
    "word_count": 45,
    "speech_rate": 176,
    "pause_analysis": {
      "pause_count": 3,
      "avg_pause_duration": 0.8,
      "total_pause_time": 2.4
    }
  },
  "analysis": {
    "speech_rate_level": "正常",
    "fluency_score": 0.85,
    "recommendations": ["语速适中，表达流畅"]
  }
}
```

## 💻 前端集成示例

### 基础语音录制

```typescript
const startRecording = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mediaRecorder = new MediaRecorder(stream);
  
  mediaRecorder.ondataavailable = (event) => {
    audioChunks.push(event.data);
  };
  
  mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    await submitVoiceAnswer(audioBlob);
  };
  
  mediaRecorder.start();
};
```

### 语音播放

```typescript
const playQuestionAudio = async (text: string) => {
  const response = await fetch('/speech/synthesize', {
    method: 'POST',
    body: new URLSearchParams({ text, voice: 'nova' })
  });
  
  const audioBlob = await response.blob();
  const audioUrl = URL.createObjectURL(audioBlob);
  
  const audio = new Audio(audioUrl);
  await audio.play();
};
```

## 🚀 集成到面试流程

### 1. 面试设置阶段
- 用户可选择是否启用语音模式
- 设置面试官语音偏好
- 麦克风权限检查

### 2. 面试进行阶段
- 自动播放问题语音（可选）
- 语音回答录制
- 实时转录显示
- 语音特征分析

### 3. 反馈阶段
- 语音表现分析
- 语速、流畅度评分
- 具体改进建议

## 📊 性能指标

### 延迟性能
- **语音合成**：2-5秒（取决于文本长度）
- **语音识别**：1-3秒（取决于音频长度）
- **特征分析**：1-2秒

### 准确性
- **中文识别准确率**：>95%
- **英文识别准确率**：>98%
- **语音合成自然度**：优秀

### 资源消耗
- **带宽需求**：中等（音频传输）
- **存储需求**：低（临时文件）
- **计算需求**：低（主要依赖API）

## 🔒 安全与隐私

### 数据保护
- 音频数据仅临时存储，处理后立即删除
- 不在服务器端永久保存用户语音
- 所有传输使用HTTPS加密

### 权限管理
- 明确的麦克风权限请求
- 用户可随时禁用语音功能
- 透明的数据使用说明

## 🛠️ 开发工具

### 测试组件
使用 `VoiceInterviewDemo` 组件进行功能测试：

```bash
# 启动开发服务器
npm run dev

# 访问演示页面
http://localhost:5173/voice-demo
```

### 调试工具
- 浏览器开发者工具查看网络请求
- 音频播放器调试
- MediaRecorder API状态监控

## 📈 未来扩展

### Phase 2 计划
1. **实时语音分析**
   - 实时情绪检测
   - 语音质量实时反馈
   - 实时语速提醒

2. **高级语音特征**
   - 声音特征分析（音调、音量）
   - 说话风格识别
   - 紧张度检测

3. **多语言支持**
   - 更多语言的语音合成
   - 口音适应
   - 方言识别

### Phase 3 愿景
1. **3D虚拟面试官**
   - 口型同步
   - 面部表情
   - 肢体语言

2. **AI对话优化**
   - 基于语音的智能追问
   - 情绪感知对话
   - 个性化语音风格

## 🐛 常见问题

### Q: 为什么语音识别不准确？
A: 确保：
- 麦克风质量良好
- 环境安静
- 说话清晰
- 网络连接稳定

### Q: 语音合成失败怎么办？
A: 检查：
- OpenAI API密钥配置
- 网络连接
- 文本长度（不超过4000字符）

### Q: 浏览器不支持语音功能？
A: 推荐使用：
- Chrome 70+
- Firefox 65+
- Safari 14+
- Edge 80+

## 📞 技术支持

如遇到语音功能相关问题，请：
1. 查看浏览器控制台错误信息
2. 检查网络连接和API配置
3. 参考本文档的故障排除部分
4. 提交Issue到项目仓库

---

**语音功能让VITA面试体验更加真实和自然！** 🎙️✨ 