# 双模型架构实现总结

## 概述

本次修改实现了严格的OpenAI优先、Qwen备份的双模型架构，确保：
1. 默认优先使用OpenAI API
2. OpenAI不可用时自动切换到Qwen API
3. 严格的模型一致性（OpenAI调用只使用OpenAI模型，Qwen调用只使用Qwen模型）

## 主要修改

### 1. 配置文件 (backend/core/config.py)

#### 模型配置分离
```python
MODEL_CONFIG = {
    "openai": {
        "chat": "gpt-4",
        "analysis": "gpt-4",
        "speech_recognition": "whisper-1",
        "speech_synthesis": "tts-1",
        "code": "gpt-4",
        "math": "gpt-4"
    },
    "qwen": {
        "chat": "qwen-plus",
        "analysis": "qwen-plus",
        "speech_recognition": "Qwen/Qwen2-Audio-7B-Instruct",
        "speech_synthesis": "qwen-plus",  # Qwen暂不支持TTS
        "code": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "math": "Qwen/Qwen2.5-Math-72B-Instruct"
    }
}
```

#### 新增方法
- `get_openai_key()`: 获取OpenAI API密钥
- `get_qwen_key()`: 获取Qwen API密钥
- `get_model_for_provider(provider, function_type)`: 根据提供商获取对应模型

### 2. OpenAI兼容层 (backend/core/openai_compat.py)

#### ClientManager增强
- 新增 `set_preferences()` 方法设置客户端偏好
- `get_healthy_client()` 支持指定提供商类型参数
- 实现了严格的OpenAI优先逻辑

#### 新增初始化函数
```python
def initialize_clients():
    """初始化所有配置的客户端"""
    # 自动注册OpenAI和Qwen客户端
    # 设置客户端管理器偏好
```

### 3. 聊天服务 (backend/core/chat.py)

#### 修改ask_llm方法
1. 首先尝试使用OpenAI客户端
2. 使用OpenAI对应的模型
3. 如果失败且启用备份，切换到Qwen
4. 使用Qwen对应的模型

```python
# 首先尝试使用OpenAI
client = await self.client_manager.get_healthy_client(provider_type='openai')
if client:
    selected_model = config.get_model_for_provider('openai', task_type)
    # 调用OpenAI...

# 如果失败，尝试Qwen
if config.USE_QWEN_FALLBACK and config.ENABLE_AUTO_SWITCH:
    fallback_client = await self.client_manager.get_healthy_client(provider_type='qwen')
    if fallback_client:
        selected_model = config.get_model_for_provider('qwen', task_type)
        # 调用Qwen...
```

### 4. 语音服务 (backend/core/speech.py)

#### 语音识别
- 优先使用本地Whisper（如果配置）
- 其次使用OpenAI的whisper-1
- 最后使用Qwen的语音识别模型

#### 语音合成
- 只支持OpenAI的tts-1模型
- Qwen暂不支持语音合成

### 5. 主文件 (backend/main.py)

- 使用统一的 `initialize_clients()` 函数
- 简化了客户端初始化逻辑

## 配置说明

### 环境变量
```bash
# OpenAI配置
# OpenAI配置已移除，现在使用本地Whisper + 本地TTS

# Qwen配置（备份）
QWEN_API_KEY=sk-xxx...

# 架构配置
PREFER_OPENAI=true          # 优先使用OpenAI
USE_QWEN_FALLBACK=true      # 启用Qwen备份
ENABLE_AUTO_SWITCH=true     # 启用自动切换
```

### 测试方法

运行测试脚本验证实现：
```bash
cd backend
python test_dual_model.py
```

## 注意事项

1. **API密钥格式**
   - OpenAI: `sk-proj-xxx` 或长度>50的 `sk-xxx`
   - Qwen: 长度<=50的 `sk-xxx`

2. **模型兼容性**
   - Qwen不支持OpenAI的TTS功能
   - 语音识别优先使用本地Whisper以提高性能

3. **错误处理**
   - 每个服务都实现了完整的错误处理和自动重试
   - 支持优雅降级到备份方案

## 已实现的改进

### 1. 支持更多的Qwen特有功能
- 添加了Qwen视觉理解模型 (Qwen2-VL-72B-Instruct)
- 添加了长文本处理模型 (qwen-long)
- 添加了快速响应模型 (qwen-turbo)
- 配置了Qwen特有功能开关（视觉理解、长文本、函数调用、插件系统）

### 2. 实现Qwen的语音合成支持
- 创建了TTS备份服务模块 (tts_fallback.py)
- 支持Edge TTS和pyttsx3两种备份方案
- 当使用Qwen时自动切换到备份TTS服务
- 提供了丰富的中文语音选择

### 3. 添加详细的性能监控
- 创建了性能监控模块 (performance_monitor.py)
- 跟踪每个API调用的耗时、成功率、错误类型
- 记录提供商切换历史
- 支持性能指标导出
- 提供性能上下文管理器便于集成

### 4. 支持动态切换主备角色
- 创建了动态切换管理器 (dynamic_switch.py)
- 支持手动切换主提供商
- 支持基于性能自动切换
- 提供了完整的REST API接口：
  - GET /api/v1/system/performance - 获取性能指标
  - POST /api/v1/system/switch-primary - 切换主提供商
  - GET /api/v1/system/switch-status - 获取切换状态
  - POST /api/v1/system/auto-switch - 启用/禁用自动切换

## 新增依赖

如果要使用TTS备份功能，需要安装：
```bash
pip install edge-tts pyttsx3
```

## API使用示例

### 切换主提供商
```bash
curl -X POST http://localhost:8000/api/v1/system/switch-primary \
  -H "Content-Type: application/json" \
  -d '{"provider": "qwen", "reason": "testing"}'
```

### 查看性能指标
```bash
curl http://localhost:8000/api/v1/system/performance
```

### 启用自动切换
```bash
curl -X POST http://localhost:8000/api/v1/system/auto-switch \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
``` 