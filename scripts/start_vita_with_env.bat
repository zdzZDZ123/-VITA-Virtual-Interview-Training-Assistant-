@echo off
echo ==========================================
echo VITA Enhanced Startup Script
echo ==========================================
echo.

REM 设置关键环境变量
echo Setting up environment variables...
set QWEN_API_KEY=__REMOVED_API_KEY__
set DOUBAO_API_KEY=__REMOVED_API_KEY__
set LLAMA_API_KEY=LLM^|727268019715816^|R9EX2i7cmHya1_7HAFiIAxxtAUk
set USE_LOCAL_WHISPER=true
set LOCAL_WHISPER_MODEL=medium
set LOCAL_TTS_ENGINE=edge-tts

echo QWEN_API_KEY=%QWEN_API_KEY%
echo DOUBAO_API_KEY=%DOUBAO_API_KEY%
echo Environment variables set successfully.
echo.

REM 检查并停止现有进程
echo Checking for existing Python processes...
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE | findstr python.exe >nul
if %ERRORLEVEL%==0 (
    echo Found existing Python processes. Stopping them...
    taskkill /F /IM python.exe >nul 2>&1
    timeout /t 2 >nul
)

REM 检查并停止现有Node.js进程
echo Checking for existing Node.js processes...
tasklist /FI "IMAGENAME eq node.exe" /FO TABLE | findstr node.exe >nul
if %ERRORLEVEL%==0 (
    echo Found existing Node.js processes. Stopping them...
    taskkill /F /IM node.exe >nul 2>&1
    timeout /t 2 >nul
)

echo.
echo ==========================================
echo Starting Backend Service...
echo ==========================================

REM 启动后端服务，在新窗口中
start "VITA Backend" cmd /c "set QWEN_API_KEY=%QWEN_API_KEY% && set DOUBAO_API_KEY=%DOUBAO_API_KEY% && set LLAMA_API_KEY=%LLAMA_API_KEY% && cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info"

echo Waiting for backend to initialize...
timeout /t 10 >nul

REM 测试后端健康状况
echo Testing backend health...
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ Backend is healthy
) else (
    echo ⚠️ Backend health check failed, but continuing...
)

echo.
echo ==========================================
echo Starting Frontend Service...
echo ==========================================

REM 启动前端服务，在新窗口中
start "VITA Frontend" cmd /c "cd frontend && npm run dev"

echo Waiting for frontend to initialize...
timeout /t 8 >nul

echo.
echo ==========================================
echo VITA Services Started!
echo ==========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5174
echo Health:   http://localhost:8000/health
echo.
echo Both services are running in separate windows.
echo Close those windows or press Ctrl+C in them to stop services.
echo.
echo Press any key to open the application in browser...
pause >nul

REM 打开浏览器
start http://localhost:5174

echo.
echo Services are running. Check the separate windows for logs.
echo To stop services, close the Backend and Frontend windows.
pause 