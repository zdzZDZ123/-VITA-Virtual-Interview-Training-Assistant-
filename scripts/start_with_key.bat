@echo off
rem VITA 项目启动脚本 (含API密钥配置)
rem VITA现在使用纯本地语音服务，不再需要OpenAI Key

echo 🎙️ VITA (Virtual Interview & Training Assistant)
echo.

rem 检查参数
if "%1"=="" (
    echo ❌ 未提供API密钥，请作为第一个参数传入
    exit /b 1
)

rem 设置API密钥和模型配置
echo 🔧 配置API密钥...
set QWEN_API_KEY=%1
set LLAMA_API_KEY=%1

rem 移除旧的OpenAI模型配置
rem set OPENAI_CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct
rem set OPENAI_ANALYSIS_MODEL=Qwen/Qwen2.5-14B-Instruct
rem set OPENAI_WHISPER_MODEL=Qwen/Qwen-Audio-Chat
rem set OPENAI_TTS_MODEL=microsoft/speecht5_tts
rem set OPENAI_DEFAULT_VOICE=nova

rem 设置服务端口
set BACKEND_PORT=8000
set VISION_PORT=8001
set FRONTEND_PORT=5173

echo ✅ 配置完成
echo.
echo =================================================
echo 🚀 VITA 服务启动配置
echo =================================================
echo    API Key: %QWEN_API_KEY:~0,10%...
echo    日志级别: %LOG_LEVEL%
echo    启动模式: %START_MODE%
echo =================================================
echo.

rem 启动所有服务
call "%~dp0run_services.bat" all

echo.
echo ✅ VITA 所有服务已启动
pause