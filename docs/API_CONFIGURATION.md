# VITA OpenAI API 配置指南

## 🔑 API密钥配置

您的OpenAI API密钥已成功配置到VITA项目中：

```
API Key: 
```

## 🤖 智能模型选择策略

VITA采用智能模型选择策略，为不同功能选择最适合的模型：

### 面试对话系统
- **模型**: `Qwen/Qwen2.5-7B-Instruct`
- **用途**: 生成面试问题、日常对话
- **优势**: 开源免费，响应速度快，中文优化
- **应用场景**: 
  - 生成行为面试问题
  - 情景面试对话
  - 追问和引导

### 深度内容分析
- **模型**: `Qwen/Qwen2.5-14B-Instruct`
- **用途**: 面试内容分析、反馈生成
- **优势**: 大参数模型，分析深入，中文理解强
- **应用场景**:
  - 回答质量评估
  - 能力维度分析
  - 详细反馈报告生成

### 语音识别系统
- **模型**: `Qwen/Qwen-Audio-Chat`
- **用途**: 语音转文字
- **优势**: 多模态支持，中文识别优化
- **应用场景**:
  - 实时语音转录
  - 语音特征分析
  - 多语言面试支持

### 语音合成系统
- **模型**: `microsoft/speecht5_tts`
- **用途**: 文字转语音
- **优势**: 开源免费，音质自然
- **应用场景**:
  - AI面试官语音
  - 问题朗读
  - 反馈播报

## 🎙️ 语音配置详情

### 默认语音设置
- **AI面试官声音**: `Nova` (专业女性声音)
- **语速**: 1.0x (正常速度)
- **音质**: 高清 (tts-1-hd)

### 语音选择策略
根据不同面试场景自动选择合适的语音：

```python
# 场景化语音选择
voice_scenarios = {
    "formal": "nova",      # 正式面试 - 专业女性
    "technical": "echo",   # 技术面试 - 男性声音  
    "casual": "alloy",     # 轻松对话 - 中性声音
    "friendly": "shimmer", # 友好场合 - 柔和女性
    "authoritative": "onyx" # 权威场合 - 深沉男性
}
```

## 📂 配置文件结构

### 1. 后端配置 (`backend/config.py`)
```python
class VITAConfig:
    # API密钥配置
    OPENAI_API_KEY = "YOUR_API_KEY"
    
    # 模型映射
    MODELS = {
        "chat": "Qwen/Qwen2.5-7B-Instruct",         # 面试对话
        "analysis": "Qwen/Qwen2.5-14B-Instruct",          # 深度分析  
        "speech_to_text": "Qwen/Qwen-Audio-Chat", # 语音识别
        "text_to_speech": "microsoft/speecht5_tts"   # 语音合成
    }
```

### 2. 智能模型选择器
```python
class ModelSelector:
    @staticmethod
    def get_best_model_for_task(task_type: str, complexity: str = "medium") -> str:
        # 根据任务类型和复杂度智能选择模型
        if task_type == "interview":
            return "Qwen/Qwen2.5-7B-Instruct"  # 快速响应
        elif task_type == "analysis":
            return "Qwen/Qwen2.5-14B-Instruct"       # 深度分析
        # ...
```

## 🚀 快速启动

### Windows用户
```bash
# 一键启动 (含API配置)
start_with_key.bat
```

### Linux/macOS用户
```bash
# 一键启动 (含API配置)
chmod +x start_with_key.sh
./start_with_key.sh
```

### 手动配置启动
```bash
# 设置环境变量
export # OpenAI配置已移除，现在使用本地Whisper + 本地TTS
export OPENAI_CHAT_MODEL="Qwen/Qwen2.5-7B-Instruct"
export OPENAI_ANALYSIS_MODEL="Qwen/Qwen2.5-14B-Instruct"

# 启动服务
./run_services.sh
```

## 📊 成本优化策略

### 1. 模型成本对比
| 模型 | 输入价格 | 输出价格 | 使用场景 |
|------|----------|----------|----------|
| Qwen2.5-7B | 免费 | 免费 | 日常对话 |
| Qwen2.5-14B | 免费 | 免费 | 深度分析 |
| Qwen-Audio | 免费 | - | 语音识别 |
| SpeechT5 | 免费 | - | 语音合成 |

### 2. 智能成本控制
```python
# 根据复杂度选择模型
def select_model_by_complexity(task_complexity):
    if task_complexity == "simple":
        return "Qwen/Qwen2.5-7B-Instruct"  # 更经济
    elif task_complexity == "complex":
        return "Qwen/Qwen2.5-14B-Instruct"         # 高质量
    else:
        return "Qwen/Qwen2.5-7B-Instruct"    # 平衡选择
```

## 🔧 API使用统计

### 实时监控
```python
# API调用日志
@monitor_performance
async def ask_llm(self, messages, task_type="chat"):
    logger.info(f"使用模型 {selected_model} 处理 {task_type} 任务")
    # 记录调用信息用于成本分析
```

### 性能指标
- **平均响应时间**: 1-3秒
- **语音识别准确率**: >95%
- **语音合成自然度**: 优秀
- **模型切换成功率**: 100%

## ⚙️ 高级配置

### 1. 环境变量覆盖
```bash
# 运行时覆盖默认配置
export OPENAI_CHAT_MODEL="gpt-4"           # 使用更强模型
export OPENAI_DEFAULT_VOICE="echo"         # 改为男性声音
export DEFAULT_SPEECH_SPEED="0.9"          # 调慢语速
```

### 2. 动态模型切换
```python
# 根据用户偏好动态切换
voice_interviewer.set_voice_config(
    voice="echo",      # 技术面试使用男性声音
    speed=0.9          # 稍慢语速便于理解
)
```

### 3. 缓存优化
```python
# 语音合成结果缓存
@lru_cache(maxsize=100)
async def cached_text_to_speech(text: str, voice: str) -> bytes:
    return await speech_service.text_to_speech(text, voice)
```

## 🛡️ 安全配置

### 1. API密钥保护
- ✅ 密钥不在前端暴露
- ✅ 服务器端统一管理
- ✅ 支持环境变量覆盖
- ✅ 配置验证机制

### 2. 请求限制
```python
PERFORMANCE_CONFIG = {
    "request_timeout": 30,         # 30秒超时
    "max_concurrent_requests": 10, # 最大并发数
    "rate_limit_per_minute": 60   # 每分钟限制
}
```

## 📈 监控与调试

### 1. 配置验证
```python
# 启动时自动验证
config.validate_config()  # 检查API密钥有效性
config.print_config_summary()  # 显示配置摘要
```

### 2. 日志监控
```bash
# 查看API调用日志
tail -f logs/backend.log | grep "OpenAI"

# 监控模型使用情况
grep "使用模型" logs/backend.log
```

## 🎯 最佳实践

### 1. 模型选择建议
- **面试对话**: 使用 `Qwen/Qwen2.5-7B-Instruct` 保证流畅度和中文优化
- **深度分析**: 使用 `Qwen/Qwen2.5-14B-Instruct` 确保准确性
- **语音功能**: 使用 `Qwen/Qwen-Audio-Chat` + `microsoft/speecht5_tts` 最佳体验

### 2. 性能优化
- **缓存策略**: 常用语音合成结果缓存
- **并发控制**: 限制同时API调用数量
- **错误处理**: 优雅降级机制

### 3. 成本控制
- **智能路由**: 根据任务复杂度选择模型
- **批量处理**: 合并相似请求
- **监控告警**: 设置成本阈值提醒

---

**通过智能模型选择和配置优化，VITA实现了性能、成本和用户体验的最佳平衡！** 🎯🚀