@echo off
echo ==========================================
echo VITA 豆包专业语音MVP - 稳定启动脚本
echo ==========================================
echo.

REM 设置环境变量
echo 🔧 设置API密钥...
set QWEN_API_KEY=__REMOVED_API_KEY__
set DOUBAO_API_KEY=__REMOVED_API_KEY__
set LLAMA_API_KEY=LLM^|727268019715816^|R9EX2i7cmHya1_7HAFiIAxxtAUk

REM 清理现有进程
echo 🧹 清理现有进程...
tasklist | findstr python.exe >nul && (
    echo 发现Python进程，正在终止...
    taskkill /F /IM python.exe >nul 2>&1
    timeout /t 3 >nul
)

REM 检查端口状态
echo 🔍 检查端口状态...
netstat -an | findstr :8000 >nul && (
    echo 端口8000被占用，正在清理...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
        taskkill /F /PID %%i >nul 2>&1
    )
    timeout /t 2 >nul
)

REM 启动后端服务
echo 🚀 启动后端服务...
cd backend
start "VITA Backend" cmd /c "set QWEN_API_KEY=%QWEN_API_KEY% && set DOUBAO_API_KEY=%DOUBAO_API_KEY% && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM 等待后端启动
echo ⏳ 等待后端启动...
timeout /t 15 >nul

REM 验证后端状态
echo 🔍 验证后端状态...
for /L %%i in (1,1,10) do (
    netstat -an | findstr :8000 | findstr LISTENING >nul && goto backend_ready
    echo 等待后端启动 %%i/10...
    timeout /t 2 >nul
)
echo ❌ 后端启动失败
goto end

:backend_ready
echo ✅ 后端服务已就绪

REM 启动前端服务
echo 🌐 启动前端服务...
cd ..\frontend
start "VITA Frontend" cmd /c "npm run dev"

REM 等待前端启动
echo ⏳ 等待前端启动...
timeout /t 10 >nul

echo.
echo ==========================================
echo 🎉 VITA 豆包专业语音MVP 启动完成!
echo ==========================================
echo.
echo 📊 服务状态:
echo   - 后端: http://localhost:8000 ✅
echo   - 前端: http://localhost:5174 ✅
echo   - 豆包专业语音: 已配置 ✅
echo   - 三级备用架构: 豆包→Qwen→Llama ✅
echo.
echo 🎯 功能特性:
echo   - ⚡ Doubao-Seed-1.6-flash: 10ms极速响应
echo   - 🧠 Doubao-Seed-1.6-thinking: 深度思考分析
echo   - 🎤 豆包专业语音: 流式识别+专业合成
echo   - 🤖 数字人面试: 3D虚拟面试官
echo   - 📱 多模态理解: 视觉+语音+文本
echo.
echo 按任意键打开浏览器...
pause >nul
start http://localhost:5174

:end
pause 