# OpenAI依赖已移除，现在使用纯本地语音服务
@echo off
echo ==========================================
echo Starting VITA Services...
echo ==========================================
echo.

REM 设置API密钥
set QWEN_API_KEY=__REMOVED_API_KEY__
echo Setting QWEN_API_KEY...

REM 启动后端服务
echo Starting Backend Service...
start "VITA Backend" cmd /c "cd backend && set QWEN_API_KEY=%QWEN_API_KEY% && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM 等待后端启动
echo Waiting for backend to start...
timeout /t 8

REM 启动前端服务
echo Starting Frontend Service...
start "VITA Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo ==========================================
echo VITA Services Started!
echo ==========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5174
echo.
echo Press any key to stop all services...
pause >nul

REM 关闭所有服务
taskkill /FI "WINDOWTITLE eq VITA Backend*" /F
taskkill /FI "WINDOWTITLE eq VITA Frontend*" /F

echo Services stopped.