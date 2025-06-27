# VITA项目完整功能分析与测试指南

## 📊 项目架构全景分析

### 🎯 核心特色
- **双模型架构**：Llama (主) + Qwen (备) + OpenAI (语音)
- **多模态交互**：文本 + 语音 + 3D数字人 + 视觉
- **实时性能**：WebSocket + 流式处理 + Redis缓存
- **企业级监控**：Prometheus + 性能分析 + 健康检查

---

## 🏗️ A. 项目功能全景速览

### 1. 🤖 核心AI与对话系统
```
双模型架构：
├── Llama API (主要)
│   ├── Llama-3.3-70B-Instruct (复杂对话)
│   ├── Llama-4-Maverick-17B (深度分析)
│   └── Llama-4-Scout-17B (快速响应)
├── Qwen API (备用)
│   ├── qwen-plus (通用)
│   ├── Qwen2.5-Coder-32B (代码)
│   └── Qwen2-VL-72B (视觉)
└── OpenAI API (语音服务)
    ├── Whisper (STT)
    └── TTS-1 (语音合成)
```

**功能模块：**
- 智能面试问答生成
- 行为面试 + 技术面试 + 情境面试
- 职位描述分析与匹配
- 实时反馈评分系统
- 自动切换与故障转移

### 2. 🎵 语音交互能力
```
语音链路：
前端录音 → WebM/Opus → FastAPI → OpenAI Whisper → 文本
文本 → OpenAI TTS → MP3/WAV → 前端播放 → 用户听到
```

**技术栈：**
- **STT**: OpenAI Whisper (云端) + 本地Whisper (可选)
- **TTS**: OpenAI TTS + 备份静音生成器
- **流式**: WebSocket双向实时传输
- **格式**: WebM(录制) + MP3(播放)
- **优化**: 回声消除 + 噪声抑制

### 3. 👤 3D数字人系统
```
3D渲染管道：
Three.js → React-Three-Fiber → GLB模型 → 表情控制
↓
LipSync + 情感表达 + 动作指令 + FPS优化
```

**数字人特性：**
- 8种角色模型（HR、技术面试官、高管等）
- 实时表情同步 (友好/思考/质疑/高兴)
- 唇形同步 (LipSync)
- 动态FPS优化 (45FPS+)
- 个性化配置

### 4. ⚡ 性能优化系统
```
前端优化：
├── Vite手动代码分割
├── Gzip/Brotli压缩
├── 3D动态降质
└── 按需加载

后端优化：
├── Redis分布式缓存
├── async_timeit装饰器
├── API延迟监控(P50/P95/P99)
└── Prometheus集成
```

### 5. 📊 监控与运维
```
监控体系：
├── /metrics (Prometheus格式)
├── /api/v1/system/status (系统状态)
├── /api/v1/system/health (健康检查)
├── 性能报告自动生成
└── 实时错误追踪
```

### 6. 🔌 完整API接口
```
主要端点：
├── /session/** (会话管理)
├── /speech/** (语音服务)
├── /api/v1/system/** (系统管理)
├── /api/v1/ws/** (WebSocket)
└── /metrics (监控)
```

---

## 🧪 B. 详细测试提示词清单

### ➊ 文本对话系统测试

**🎯 基础面试对话**
```
提示词1: "我是一名5年经验的React前端开发工程师，请给我一个技术面试问题"
期望: 返回React相关的技术问题，难度适中

提示词2: "请基于以下JD生成3个STAR行为面试问题：
职位：高级产品经理
要求：负责B端产品设计，具备数据分析能力，5年以上经验"
期望: 3个结构化的STAR问题

提示词3: "请用英语问一个关于微服务架构设计的问题"  
期望: 英文技术问题，涉及微服务

提示词4: "对这个回答打分(1-5)并点评：
'我认为Vue比React更好用，因为语法简单，上手快'"
期望: 数字评分+详细点评
```

**🎯 高级对话测试**
```
提示词5: "创建一个算法工程师的编程题目，包含完整的测试用例"
提示词6: "模拟一次CTO级别的架构设计面试，话题是大数据平台"
提示词7: "生成一个跨文化团队管理的情境面试问题"
```

### ➋ 语音功能全链路测试

**🎯 TTS（文字转语音）测试**
```bash
# 基础TTS测试
curl -X POST http://localhost:8000/speech/synthesize \
     -F "text=欢迎参加今天的技术面试，请先简单介绍一下您自己" \
     -F "voice=nova" \
     -F "speed=1.0" \
     --output welcome.mp3

# 多语音测试
for voice in nova alloy echo fable onyx shimmer; do
  curl -X POST http://localhost:8000/speech/synthesize \
       -F "text=您好，我是${voice}语音" \
       -F "voice=${voice}" \
       --output "voice_${voice}.mp3"
done

# 语速测试
for speed in 0.5 1.0 1.5 2.0; do
  curl -X POST http://localhost:8000/speech/synthesize \
       -F "text=这是语速${speed}倍速的测试" \
       -F "speed=${speed}" \
       --output "speed_${speed}.mp3"
done
```

**期望结果：**
- HTTP 200状态码
- Content-Type: audio/mpeg
- 文件大小 > 0
- 音频可正常播放
- 不同语音有明显区别

**🎯 STT（语音转文字）测试**
```bash
# 中文识别测试
curl -X POST http://localhost:8000/speech/transcribe \
     -F "audio=@chinese_recording.webm" \
     -F "language=zh"

# 英文识别测试  
curl -X POST http://localhost:8000/speech/transcribe \
     -F "audio=@english_recording.webm" \
     -F "language=en"

# 技术术语测试
curl -X POST http://localhost:8000/speech/transcribe \
     -F "audio=@tech_terms.webm" \
     -F "language=zh"
```

**期望JSON格式：**
```json
{
  "success": true,
  "text": "识别出的文字内容",
  "language": "zh",
  "duration": 5.2,
  "word_count": 12,
  "confidence": 0.95
}
```

**🎯 实时语音WebSocket测试**
```javascript
// 在浏览器控制台执行
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/realtime-voice/test-session');

ws.onopen = () => {
    console.log('WebSocket连接成功');
    // 发送心跳
    ws.send(JSON.stringify({event: 'ping'}));
};

ws.onmessage = (event) => {
    if (typeof event.data === 'string') {
        const msg = JSON.parse(event.data);
        console.log('收到消息:', msg);
    } else {
        console.log('收到音频数据:', event.data.byteLength);
    }
};

// 测试语音合成
ws.send(JSON.stringify({
    event: 'start_speaking',
    text: '这是实时语音合成测试'
}));
```

### ➌ 3D数字人房间测试

**🎯 访问路径**
```
前端路由: http://localhost:5173/digital-human
```

**🎯 功能测试清单**
```
□ 页面加载时间 < 3秒
□ 3D模型正常渲染
□ FPS保持在45以上
□ 选择不同Avatar生效
□ 表情切换流畅 (neutral→friendly→thinking→questioning)
□ 动作响应及时 (idle→talking→listening→waving)
□ 摄像头开启/关闭正常
□ 录音功能可用
□ LipSync与音频同步
□ 性能优化器自动降质
```

**🎯 测试话术**
```
Demo问题1: "请介绍一下您的项目经验"
Demo问题2: "谈谈您遇到的最大技术挑战"
Demo问题3: "您的职业规划是什么？"

测试回答: 
"我有5年的全栈开发经验，主要使用React和Node.js开发企业级应用。
最近在负责一个微服务架构的电商系统，日处理订单量超过10万笔。
未来希望向技术架构师方向发展。"
```

### ➍ 系统监控测试

**🎯 Prometheus监控**
```bash
# 访问监控端点
curl http://localhost:8000/metrics

# 检查关键指标
curl http://localhost:8000/metrics | grep -E "(api_request|latency|error_rate)"
```

**期望输出样例：**
```
# HELP api_request_latency_seconds API请求延迟
# TYPE api_request_latency_seconds histogram
__REMOVED_API_KEY__{le="0.1"} 150
__REMOVED_API_KEY__{le="0.5"} 280
__REMOVED_API_KEY__{le="1.0"} 340
```

**🎯 系统状态检查**
```bash
# 总体健康状态
curl http://localhost:8000/api/v1/system/status | jq

# 性能指标
curl http://localhost:8000/api/v1/system/performance | jq

# 模型切换测试
curl -X POST http://localhost:8000/api/v1/system/switch-primary \
     -H "Content-Type: application/json" \
     -d '{"provider": "qwen", "reason": "testing"}'

# 查看切换状态
curl http://localhost:8000/api/v1/system/switch-status | jq
```

### ➎ 性能压力测试

**🎯 使用项目自带的性能测试脚本**
```bash
# TTS并发测试
python performance_test.py \
  --endpoint http://localhost:8000/speech/synthesize \
  --concurrency 20 \
  --requests 100

# API延迟测试
python performance_test.py \
  --endpoint http://localhost:8000/session/start \
  --concurrency 10 \
  --requests 50

# 查看报告
cat optimization_report.json | jq '.api_performance'
```

**🎯 使用wrk压力测试**
```bash
# 安装wrk (Windows需要WSL)
# Ubuntu: sudo apt install wrk

# TTS压力测试
wrk -t4 -c20 -d30s --script=tts_test.lua http://localhost:8000/speech/synthesize

# 创建tts_test.lua脚本
cat > tts_test.lua << 'EOF'
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/x-www-form-urlencoded"
wrk.body = "text=测试文本&voice=nova&speed=1.0"
EOF
```

### ➏ 视觉分析测试 (可选)

**🎯 如果启用了视觉服务**
```bash
# 启动视觉服务
cd vision_service
python app.py

# 测试图像分析
curl -X POST http://localhost:8001/analyze \
     -F "image=@test_face.jpg"

# 期望输出
{
  "confidence": 0.85,
  "eye_contact": 0.9,
  "expression": "professional",
  "posture": "upright"
}
```

---

## 🚀 C. 快速测试执行方案

### 方案1：一键启动测试
```bash
# 1. 启动服务 (已包含API密钥)
start_with_openai_key.bat

# 2. 等待服务启动 (约30秒)

# 3. 打开测试页面
浏览器访问: test_voice_interview_fixed.html

# 4. 执行自动化测试
```

### 方案2：分模块测试
```bash
# 后端API测试
cd backend && python -m pytest tests/ -v

# 前端组件测试  
cd frontend && npm test

# E2E测试
cd frontend && npx playwright test
```

### 方案3：生产环境验证
```bash
# 构建并启动生产版本
cd frontend && npm run build
cd ../backend && python main.py

# 访问生产路径
http://localhost:8000/app/
```

---

## 📋 D. 测试检查清单

### 基础功能 (必测)
```
□ 服务启动无错误
□ 健康检查通过 (/health)
□ API密钥配置正确
□ 数据库连接正常
□ Redis缓存可用
□ 基础对话功能
□ TTS语音合成
□ STT语音识别
□ WebSocket连接
```

### 高级功能 (推荐)
```
□ 3D数字人渲染
□ 实时语音对话
□ 性能监控正常
□ 多模型切换
□ 摄像头集成
□ 表情动作同步
□ 错误处理机制
□ 缓存命中率 >80%
```

### 性能基准 (优化)
```
□ API P95延迟 <500ms
□ TTS响应时间 <2s
□ STT识别准确率 >90%
□ 3D渲染FPS ≥45
□ 前端加载时间 <3s
□ 并发支持 >20用户
□ 内存使用 <2GB
□ CPU使用率 <70%
```

---

## 🎯 E. 常见问题诊断

### Q1: 语音无声音
```bash
# 检查API密钥
echo $OPENAI_API_KEY

# 检查TTS端点
curl -X POST http://localhost:8000/speech/synthesize \
     -F "text=测试" -F "voice=nova" --output test.mp3

# 检查浏览器控制台错误
```

### Q2: 数字人不渲染
```bash
# 检查模型文件
ls frontend/public/models/

# 检查WebGL支持
# 在浏览器控制台执行：
console.log(!!window.WebGLRenderingContext);
```

### Q3: WebSocket连接失败
```bash
# 检查WebSocket端点
curl --include \
     --no-buffer \
     --header "Connection: Upgrade" \
     --header "Upgrade: websocket" \
     --header "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
     --header "Sec-WebSocket-Version: 13" \
     http://localhost:8000/api/v1/ws/realtime-voice/test
```

### Q4: 性能问题
```bash
# 检查系统资源
curl http://localhost:8000/api/v1/system/performance | jq '.memory_usage'

# 查看详细日志
tail -f backend/logs/vita.log
```

---

## 🎉 总结

通过这个完整的测试指南，您可以：

1. **全面验证** - 覆盖所有核心功能模块
2. **性能评估** - 获得详细的性能基准数据  
3. **问题诊断** - 快速定位和解决常见问题
4. **持续监控** - 建立长期的性能监控体系

**建议测试顺序：**
1. 基础功能验证 (30分钟)
2. 语音功能测试 (45分钟)  
3. 3D数字人体验 (30分钟)
4. 性能压力测试 (60分钟)
5. 问题修复优化 (根据发现的问题)

祝您测试顺利！🚀 