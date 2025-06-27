@echo off
REM VITA 项目启动脚本 (Windows版本)
REM 用于同时启动后端服务、视觉分析服务和前端应用

echo.
echo 🚀 启动 VITA 虚拟面试助理...
echo.

REM 检查环境
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 npm，请先安装 Node.js
    pause
    exit /b 1
)

REM 创建日志目录
if not exist logs mkdir logs

echo 📦 安装依赖...

REM 安装后端依赖
echo - 安装后端依赖
cd backend
pip install -r requirements.txt > ..\logs\backend_install.log 2>&1
if %errorlevel% neq 0 (
    echo ❌ 后端依赖安装失败，请检查 logs\backend_install.log
    pause
    exit /b 1
)
cd ..

REM 安装视觉服务依赖
echo - 安装视觉服务依赖
cd vision_service
pip install -r requirements.txt > ..\logs\vision_install.log 2>&1
if %errorlevel% neq 0 (
    echo ❌ 视觉服务依赖安装失败，请检查 logs\vision_install.log
    pause
    exit /b 1
)
cd ..

REM 安装前端依赖
echo - 安装前端依赖
cd frontend
npm install > ..\logs\frontend_install.log 2>&1
if %errorlevel% neq 0 (
    echo ❌ 前端依赖安装失败，请检查 logs\frontend_install.log
    pause
    exit /b 1
)
cd ..

echo.
echo 🌟 启动服务...

REM 启动后端服务
echo - 启动后端服务 (http://localhost:8000)
cd backend
start "VITA Backend" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
cd ..

REM 等待后端启动
echo "--- 等待后端服务启动 (10秒)... ---"
timeout /t 10 /nobreak >nul

REM 启动视觉分析服务
echo - 启动视觉分析服务 (http://localhost:8001)
cd vision_service
start "VITA Vision" cmd /k "python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload"
cd ..

REM 等待视觉服务启动
echo "--- 等待视觉服务启动 (5秒)... ---"
timeout /t 5 /nobreak >nul

REM 启动前端开发服务器
echo - 启动前端服务 (http://localhost:5173)
cd frontend
start "VITA Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ✅ 所有服务已启动！
echo.
echo 📍 访问地址:
echo    前端应用:     http://localhost:5173
echo    后端 API:     http://localhost:8000
echo    API 文档:     http://localhost:8000/docs
echo    视觉服务:     http://localhost:8001
echo    视觉 API 文档: http://localhost:8001/docs
echo.
echo 📋 注意事项:
echo    1. 确保设置了 QWEN_API_KEY 或 LLAMA_API_KEY 环境变量
echo    2. 面试过程中需要授权摄像头访问权限
echo    3. 建议使用 Chrome 或 Edge 浏览器
echo.
echo 🛑 停止服务: 关闭各个服务窗口或运行 stop_services.bat
echo 📊 查看日志: 查看 logs\ 目录中的日志文件
echo.
echo ⏳ 服务正在运行中... 按任意键退出脚本
pause >nul 