# VITA 项目架构分析报告（修正版）

## 📋 项目概览

VITA（Virtual Interview & Training Assistant）是一个基于AI的虚拟面试与培训助理平台，采用**纯云端API驱动**的架构：

- **双API模型架构**：Llama API + Qwen API（通义千问）
- **实时语音交互**：语音识别和语音合成（均通过API）
- **视觉分析**：面部表情、眼神接触、姿态评估
- **数字人技术**：3D虚拟面试官

## 🏗️ 真实技术架构

### API驱动的双模型架构

```
┌─────────────────────┐    ┌─────────────────────┐
│    Llama API        │    │     Qwen API        │
│ api.llama-api.com   │    │ dashscope.aliyun... │
└─────────┬───────────┘    └─────────┬───────────┘
          │                          │
          └────────┬───────────────────┘
                   │
           ┌───────┴────────┐
           │ 动态切换管理器  │
           └───────┬────────┘
                   │
           ┌───────┴────────┐
           │   VITA 应用    │
           └────────────────┘
```

### 后端架构（FastAPI）

```
backend/
├── core/
│   ├── openai_compat.py    # API客户端管理
│   ├── config.py           # 配置管理
│   ├── chat.py             # 对话逻辑
│   ├── speech.py           # 语音处理
│   ├── dynamic_switch.py   # 动态切换
│   └── performance_monitor.py # 性能监控
├── main.py                 # 主应用入口
└── requirements.txt        # 依赖列表
```

## 🤖 API模型配置

### 1. Llama API模型
- **API密钥格式**: `LLM|数字|字符串`
- **API地址**: `https://api.llama-api.com/v1`
- **可用模型**:
  - `Llama-3.3-70B-Instruct` (主要对话)
  - `__REMOVED_API_KEY__` (深度分析)
  - `__REMOVED_API_KEY__` (快速响应)
  - `Llama-3.3-8B-Instruct` (轻量级备用)

### 2. Qwen API模型
- **API密钥格式**: `sk-xxx` (较短)
- **API地址**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **可用模型**:
  - `qwen-plus` (通用对话)
  - `qwen-turbo` (快速响应)
  - `qwen-long` (长文本处理)
  - `Qwen/Qwen2-Audio-7B-Instruct` (音频处理)
  - `Qwen/Qwen2.5-Coder-32B-Instruct` (代码任务)
  - `Qwen/Qwen2.5-Math-72B-Instruct` (数学推理)
  - `Qwen/Qwen2-VL-72B-Instruct` (视觉理解)

## 🔌 核心API端点

### 1. 会话管理
| 端点 | 方法 | 描述 |
|------|------|------|
| `/session/start` | POST | 开始新的面试会话 |
| `/session/{id}/answer` | POST | 提交答案 |
| `/session/{id}/feedback` | GET | 获取反馈报告 |

### 2. 语音处理
| 端点 | 方法 | 描述 |
|------|------|------|
| `/speech/transcribe` | POST | 语音转文字（API驱动） |
| `/speech/synthesize` | POST | 文字转语音（API驱动） |
| `/speech/analyze` | POST | 语音分析 |

### 3. WebSocket实时交互
| 端点 | 描述 |
|------|------|
| `/api/v1/ws/{session_id}` | 标准WebSocket连接 |
| `/api/v1/ws/realtime-voice/{session_id}` | 实时语音WebSocket |

### 4. 系统监控
| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/system/status` | GET | API服务状态 |
| `/api/v1/system/performance` | GET | 性能指标 |
| `/api/v1/system/switch-primary` | POST | 切换主API |

## 🔄 动态切换机制

### API健康检查
系统会定期检查各API服务的健康状态：
- **响应时间监控**
- **错误率统计**
- **可用性检查**

### 自动切换条件
1. **API服务故障**
2. **响应超时**
3. **达到速率限制**
4. **特定任务需求**

## 🌍 部署配置

### 环境变量配置
```env
# Llama API配置
LLAMA_API_KEY=LLM|727268019715816|R9EX2i7cmHya1_7HAFiIAxxtAUk
LLAMA_API_BASE_URL=https://api.llama-api.com/v1

# Qwen API配置（通义千问）
QWEN_API_KEY=__REMOVED_API_KEY__

# 切换配置
USE_QWEN_FALLBACK=true
PREFER_LLAMA=true
ENABLE_AUTO_SWITCH=true

# 语音配置
USE_LOCAL_WHISPER=false
TTS_PROVIDER=api
```

### Docker部署
```yaml
version: '3.8'
services:
  vita-backend:
    build: ./backend
    environment:
      - LLAMA_API_KEY=${LLAMA_API_KEY}
      - QWEN_API_KEY=${QWEN_API_KEY}
    ports:
      - "8000:8000"
  
  vita-frontend:
    build: ./frontend
    ports:
      - "3000:80"
```

## 📊 性能特点

### API调用特性
| 特性 | Llama API | Qwen API |
|------|-----------|----------|
| 响应速度 | 快速 | 极快 |
| 成本 | API计费 | API计费 |
| 中文支持 | 良好 | 优秀 |
| 专业模型 | 多种规格 | 专业细分 |
| 可用性 | 第三方 | 阿里云 |

### 优势分析
1. **无需本地GPU**：完全基于云端API
2. **快速部署**：无需模型下载和本地配置
3. **高可用性**：双API冗余设计
4. **按需付费**：只为实际使用付费
5. **自动更新**：API提供商负责模型更新

## 🔍 监控与维护

### 关键指标
```json
{
  "api_status": {
    "llama": {
      "status": "healthy",
      "response_time": "0.8s",
      "success_rate": "99.5%"
    },
    "qwen": {
      "status": "healthy", 
      "response_time": "0.6s",
      "success_rate": "99.8%"
    }
  },
  "switch_count": 3,
  "total_requests": 1250
}
```

### 成本监控
- API调用次数统计
- Token使用量跟踪
- 成本预警机制

## 💡 最佳实践

1. **API密钥管理**
   - 定期轮换密钥
   - 监控使用量
   - 设置预算限制

2. **性能优化**
   - 缓存常用响应
   - 批量处理请求
   - 选择合适的模型规格

3. **故障恢复**
   - 实现重试机制
   - 监控API状态
   - 准备降级方案

4. **安全考虑**
   - 加密敏感数据
   - 限制API访问
   - 审计日志记录

---

**VITA采用现代化的云端API架构，确保高性能、高可用性和低维护成本！** ✨ 