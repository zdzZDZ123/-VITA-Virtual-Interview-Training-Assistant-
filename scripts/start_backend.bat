# OpenAI依赖已移除，现在使用纯本地语音服务
@echo off
echo Starting VITA Backend Service...

cd /d "%~dp0backend"

# OpenAI配置已移除
set QWEN_API_KEY=__REMOVED_API_KEY__

# OpenAI配置已移除
echo Starting FastAPI server on port 8000...

uvicorn main:app --reload --port 8000 --host 0.0.0.0

pause