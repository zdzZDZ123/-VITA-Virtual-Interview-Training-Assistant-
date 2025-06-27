# OpenAI依赖已移除，现在使用纯本地语音服务
@echo off
echo Starting VITA Backend Server...

:: 设置环境变量
# OpenAI配置已移除
set QWEN_API_KEY=__REMOVED_API_KEY__

:: 切换到项目根目录
cd /d %~dp0

:: 设置Python路径
set PYTHONPATH=%cd%

:: 启动后端服务器
echo Starting server from project root...
python -m backend.run_backend

:: 如果失败，尝试从backend目录启动
if errorlevel 1 (
    echo.
    echo First attempt failed, trying from backend directory...
    cd backend
    python run_backend.py
)

pause