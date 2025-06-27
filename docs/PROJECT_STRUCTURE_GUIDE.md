# VITA 项目结构指南

## 📁 推荐的项目目录结构

```
VITA (Virtual Interview & Training Assistant)/
├── 📂 backend/                          # 后端服务 (Python FastAPI)
│   ├── 📂 api/                          # API路由层
│   │   ├── __init__.py
│   │   ├── health.py                    # 健康检查API
│   │   ├── model_manager.py             # 模型管理API
│   │   └── modules.py                   # 模块状态API
│   │
│   ├── 📂 core/                         # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── speech.py                    # 主语音服务
│   │   ├── realtime_speech.py           # 实时语音处理
│   │   ├── whisper_model_manager.py     # Whisper模型管理
│   │   ├── module_registry.py           # 模块注册表
│   │   ├── chat.py                      # AI对话服务
│   │   ├── tts_service.py               # TTS服务
│   │   ├── config.py                    # 配置管理
│   │   ├── logger.py                    # 日志系统
│   │   └── 📂 tts_engines/              # TTS引擎实现
│   │       ├── __init__.py
│   │       ├── base.py                  # 基础引擎类
│   │       ├── edge_engine.py           # Edge-TTS引擎
│   │       └── pyttsx3_engine.py        # Pyttsx3引擎
│   │
│   ├── 📂 models/                       # 数据模型层
│   │   ├── __init__.py
│   │   ├── session.py                   # 会话数据模型
│   │   └── api.py                       # API数据模型
│   │
│   ├── 📂 whisper/                      # 本地Whisper模块
│   │   ├── __init__.py
│   │   ├── model.py
│   │   ├── audio.py
│   │   └── ... (其他whisper文件)
│   │
│   ├── 📂 static/                       # 静态文件
│   ├── 📂 tests/                        # 单元测试
│   ├── main.py                          # FastAPI应用入口
│   ├── requirements.txt                 # Python依赖
│   └── fix_whisper_models.py            # 模型修复工具
│
├── 📂 frontend/                         # 前端应用 (React + TypeScript)
│   ├── 📂 src/
│   │   ├── 📂 api/                      # API客户端
│   │   ├── 📂 components/               # React组件
│   │   ├── 📂 store/                    # 状态管理
│   │   ├── 📂 utils/                    # 工具函数
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── 📂 scripts/                          # 工具脚本
│   ├── download_faster_whisper.py       # 模型下载脚本
│   └── __init__.py
│
├── 📂 whisper_download/                 # Whisper模型存储
│   ├── tiny/
│   ├── base/
│   ├── small/
│   ├── medium/                          # 推荐使用的模型
│   └── large/
│
├── 📂 cache/                            # 缓存目录
│   ├── tts/                             # TTS缓存
│   └── models/                          # 模型缓存
│
├── 📂 logs/                             # 日志文件
├── 📂 docs/                             # 项目文档
├── download_whisper_model.bat           # Windows模型下载工具
├── start_backend.bat                    # Windows后端启动脚本
├── README.md                            # 项目说明
└── requirements.txt                     # 项目依赖
```

## 🔧 模块集成架构

### 语音识别模块架构
```
SpeechService (speech.py)
    ├── WhisperModelManager (whisper_model_manager.py)
    │   ├── faster-whisper (优先)
    │   └── whisper (备用)
    │
    └── RealTimeSpeechService (realtime_speech.py)
        ├── 语音活动检测 (VAD)
        ├── 音频累积
        └── 实时转录
```

### 语音合成模块架构
```
TTSService (tts_service.py)
    ├── EdgeTTSEngine (edge_engine.py)      # 主要引擎
    │   └── edge-tts                        # 高质量语音合成
    │
    └── Pyttsx3Engine (pyttsx3_engine.py)   # 备用引擎
        └── pyttsx3                         # 系统TTS
```

### 模块注册架构
```
ModuleRegistry (module_registry.py)
    ├── 模块导入检测
    ├── 版本信息收集
    ├── 状态监控
    └── 健康检查
```

## 📋 模块集成清单

### ✅ 已正确集成的模块

#### 1. faster-whisper
- **位置**: `backend/core/speech.py:66`
- **导入**: `from faster_whisper import WhisperModel`
- **功能**: 高性能语音识别
- **状态**: ✅ 已集成，模型文件需要下载

#### 2. whisper (标准版)
- **位置**: `backend/core/speech.py:77`
- **导入**: `import whisper`
- **功能**: 备用语音识别
- **状态**: ✅ 已集成，正常工作

#### 3. edge-tts
- **位置**: `backend/core/tts_engines/edge_engine.py:13`
- **导入**: `import edge_tts`
- **功能**: 高质量语音合成
- **状态**: ✅ 已集成，正常工作

#### 4. pyttsx3
- **位置**: `backend/core/tts_engines/pyttsx3_engine.py`
- **导入**: `import pyttsx3`
- **功能**: 系统TTS备用
- **状态**: ✅ 已集成，正常工作

## 🚀 API接口文档

### 模块状态API

#### 获取所有模块健康状态
```http
GET /api/modules/health
```

**响应示例**:
```json
{
  "status": "ok",
  "data": {
    "total_modules": 4,
    "ready_modules": 3,
    "error_modules": 1,
    "ready_list": ["whisper", "edge-tts", "pyttsx3"],
    "error_list": ["faster-whisper"],
    "modules": {
      "faster-whisper": {
        "name": "faster-whisper",
        "status": "not_installed",
        "version": null,
        "error_message": "模型文件缺失"
      }
    }
  },
  "summary": {
    "total": 4,
    "ready": 3,
    "errors": 1,
    "health_score": 75.0
  }
}
```

#### 获取详细模块状态
```http
GET /api/modules/status
```

#### 获取特定模块状态
```http
GET /api/modules/status/{module_name}
```

#### 重新加载模块
```http
POST /api/modules/reload/{module_name}
```

#### 获取优化建议
```http
GET /api/modules/recommendations
```

### Whisper模型管理API

#### 获取模型状态
```http
GET /api/models/whisper/status
```

#### 下载模型
```http
POST /api/models/whisper/{model_size}/download
```

#### 确保模型可用
```http
POST /api/models/whisper/ensure/{model_size}
```

## 🛠️ 使用指南

### 1. 检查模块状态
```bash
curl http://localhost:8000/api/modules/health
```

### 2. 下载Whisper模型
```bash
# Windows
download_whisper_model.bat medium

# Linux/Mac
python scripts/download_faster_whisper.py medium
```

### 3. 诊断和修复
```bash
cd backend
python fix_whisper_models.py --diagnose-only  # 仅诊断
python fix_whisper_models.py                  # 自动修复
```

### 4. 在代码中使用模块
```python
# 检查模块是否可用
from backend.core.module_registry import is_voice_module_available

if is_voice_module_available("faster-whisper"):
    # 使用faster-whisper
    pass
else:
    # 使用备用方案
    pass

# 获取模块健康报告
from backend.core.module_registry import check_voice_modules_health
health = check_voice_modules_health()
```

## ⚡ 性能优化建议

### 1. 模型选择
- **tiny**: 最快，精度最低 (39MB)
- **base**: 平衡选择 (74MB)
- **small**: 较好精度 (244MB)
- **medium**: 推荐使用 (769MB) ⭐
- **large**: 最高精度，最慢 (1550MB)

### 2. 部署环境
- **开发环境**: 使用medium模型 + CPU
- **生产环境**: 使用large模型 + GPU (如可用)
- **边缘设备**: 使用small模型 + 量化

### 3. 缓存策略
- TTS结果缓存: 启用
- 模型预加载: 推荐
- 音频压缩: 启用

## 🐛 常见问题解决

### 1. faster-whisper模型缺失
```bash
python scripts/download_faster_whisper.py medium
```

### 2. 模块导入失败
```bash
pip install -r requirements.txt
```

### 3. 权限问题 (Windows)
```bash
# 以管理员身份运行PowerShell
Set-ExecutionPolicy RemoteSigned
```

### 4. 网络连接问题
- 使用VPN或代理
- 手动下载模型文件
- 使用离线安装包

## 📝 维护建议

1. **定期检查**: 使用health API监控模块状态
2. **版本更新**: 关注依赖包的更新
3. **性能监控**: 监控语音处理延迟
4. **日志分析**: 定期查看错误日志
5. **备份策略**: 备份训练好的模型文件 