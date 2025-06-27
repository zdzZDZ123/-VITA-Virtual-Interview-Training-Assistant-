# VITA 双API架构详解

## 🌐 架构概述

VITA采用**Llama API + Qwen API**的双云端API架构，实现高性能、高可用的智能面试系统：

```
┌─────────────────────────┐    ┌─────────────────────────┐
│      Llama API          │    │       Qwen API          │
│  api.llama-api.com      │    │ dashscope.aliyuncs.com  │
│  (第三方API服务)        │    │    (阿里云API)          │
└───────────┬─────────────┘    └───────────┬─────────────┘
            │                              │
            └──────────┬───────────────────┘
                       │
               ┌───────┴────────┐
               │ API切换管理器   │
               └───────┬────────┘
                       │
               ┌───────┴────────┐
               │   VITA 应用    │
               └────────────────┘
```

## 🔧 API配置详情

### 1. Llama API (主力)
- **提供商**: 第三方Llama API服务
- **API地址**: `https://api.llama-api.com/v1`
- **认证格式**: `LLM|数字ID|密钥字符串`
- **示例密钥**: `LLM|727268019715816|R9EX2i7cmHya1_7HAFiIAxxtAUk`

**可用模型**:
```python
LLAMA_MODELS = {
    "chat": "Llama-3.3-70B-Instruct",           # 主要对话模型
    "analysis": "__REMOVED_API_KEY__",  # 深度分析
    "interview": "Llama-3.3-70B-Instruct",      # 面试专用
    "code": "__REMOVED_API_KEY__",  # 代码相关
    "math": "__REMOVED_API_KEY__",  # 数学推理
    "fallback": "Llama-3.3-8B-Instruct"        # 轻量备用
}
```

### 2. Qwen API (备份/特殊任务)
- **提供商**: 阿里云DashScope
- **API地址**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **认证格式**: `sk-` 开头的短密钥
- **示例密钥**: `__REMOVED_API_KEY__`

**可用模型**:
```python
QWEN_MODELS = {
    "chat": "qwen-plus",                        # 通用对话
    "analysis": "qwen-plus",                    # 内容分析
    "turbo": "qwen-turbo",                     # 快速响应
    "long": "qwen-long",                       # 长文本处理
    "audio": "Qwen/Qwen2-Audio-7B-Instruct",  # 音频处理
    "code": "Qwen/Qwen2.5-Coder-32B-Instruct",    # 代码任务
    "math": "Qwen/Qwen2.5-Math-72B-Instruct", # 数学推理
    "vision": "Qwen/Qwen2-VL-72B-Instruct"    # 视觉理解
}
```

## 🔄 智能切换机制

### 切换策略
1. **任务优先**: 音频任务→Qwen-Audio, 视觉任务→Qwen-VL
2. **健康状态**: 主API故障时自动切换到备用API
3. **性能优化**: 根据响应时间动态调整
4. **负载均衡**: 分散请求压力

### 切换触发条件
```python
# 自动切换条件
SWITCH_CONDITIONS = {
    "api_failure": True,        # API服务失败
    "timeout": 30,              # 响应超时(秒)
    "error_rate": 0.1,          # 错误率阈值
    "rate_limit": True,         # 达到速率限制
    "model_unavailable": True   # 模型不可用
}
```

## 📝 环境配置

### 基础配置 (.env)
```env
# === Llama API配置 ===
LLAMA_API_KEY=LLM|727268019715816|R9EX2i7cmHya1_7HAFiIAxxtAUk
LLAMA_API_BASE_URL=https://api.llama-api.com/v1

# === Qwen API配置 ===  
QWEN_API_KEY=__REMOVED_API_KEY__

# === 切换控制 ===
USE_QWEN_FALLBACK=true        # 启用Qwen备份
PREFER_LLAMA=true             # 优先使用Llama
ENABLE_AUTO_SWITCH=true       # 启用自动切换
HEALTH_CHECK_INTERVAL=60      # 健康检查间隔(秒)
MAX_RETRY_COUNT=3             # 最大重试次数

# === 性能配置 ===
REQUEST_TIMEOUT=30            # 请求超时
MAX_CONCURRENT_REQUESTS=10    # 最大并发数
RATE_LIMIT_PER_MINUTE=60     # 每分钟请求限制
```

### Python客户端配置
```python
# 客户端初始化示例
from core.openai_compat import create_openai_client

# Llama客户端
llama_client = create_openai_client(
    api_key="LLM|727268019715816|R9EX2i7cmHya1_7HAFiIAxxtAUk",
    base_url="https://api.llama-api.com/v1"
)

# Qwen客户端  
qwen_client = create_openai_client(
    api_key="__REMOVED_API_KEY__"
)
```

## 🚀 API调用示例

### 1. 聊天对话
```python
# 使用Llama进行面试对话
response = await llama_client.chat.completions.create(
    model="Llama-3.3-70B-Instruct",
    messages=[
        {"role": "user", "content": "请介绍一下你的工作经验"}
    ],
    max_tokens=500
)

# 自动切换到Qwen（如果Llama不可用）
response = await qwen_client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "user", "content": "请介绍一下你的工作经验"}
    ],
    max_tokens=500
)
```

### 2. 音频处理
```python
# 使用Qwen进行语音识别
response = await qwen_client.audio.transcriptions.create(
    model="Qwen/Qwen2-Audio-7B-Instruct",
    file=audio_file,
    response_format="json"
)
```

### 3. 健康检查
```python
# API健康状态检查
async def check_api_health(client, model):
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1,
            timeout=10
        )
        return True
    except:
        return False
```

## 📊 监控指标

### 实时监控端点
- `GET /api/v1/system/status` - 系统状态
- `GET /api/v1/system/performance` - 性能指标  
- `GET /api/v1/system/switch-status` - 切换状态
- `POST /api/v1/system/switch-primary` - 手动切换

### 关键指标
```json
{
  "api_status": {
    "llama": {
      "status": "healthy",
      "response_time_ms": 800,
      "success_rate": 99.5,
      "requests_today": 1250,
      "last_error": null
    },
    "qwen": {
      "status": "healthy", 
      "response_time_ms": 600,
      "success_rate": 99.8,
      "requests_today": 340,
      "last_error": null
    }
  },
  "switch_count_today": 3,
  "current_primary": "llama",
  "auto_switch_enabled": true
}
```

## 💰 成本管理

### 成本监控
```python
# 成本跟踪
COST_TRACKING = {
    "llama": {
        "input_tokens": 0.001,    # 每1K tokens成本
        "output_tokens": 0.002,   # 每1K tokens成本
        "requests_today": 1250,
        "cost_today": 15.60
    },
    "qwen": {
        "input_tokens": 0.0008,   # 每1K tokens成本
        "output_tokens": 0.002,   # 每1K tokens成本  
        "requests_today": 340,
        "cost_today": 4.20
    }
}
```

### 成本优化策略
1. **缓存机制**: 重复请求使用缓存结果
2. **模型选择**: 根据任务复杂度选择合适模型
3. **请求优化**: 减少不必要的token使用
4. **预算控制**: 设置每日消费限额

## 🛡️ 错误处理

### 自动重试机制
```python
# 重试配置
RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay": 1.0,
    "exponential_backoff": True,
    "retry_on": [
        "connection_error",
        "timeout",
        "rate_limit",
        "server_error"
    ]
}
```

### 故障转移流程
1. **检测故障**: API健康检查失败
2. **尝试重试**: 指数退避重试
3. **切换API**: 自动切换到备用API
4. **记录日志**: 详细记录切换原因
5. **恢复检测**: 定期检查原API恢复状态

## 🔗 API文档链接

- [Llama API文档](https://docs.llama-api.com/) (假设链接)
- [阿里云DashScope文档](https://help.aliyun.com/zh/dashscope/)
- [OpenAI兼容格式](https://platform.openai.com/docs/api-reference)

---

**VITA的双API架构确保了高可用性、高性能和成本效益的完美平衡！** 🚀 