@echo off
REM VITA后端服务启动脚本 - 修复版
REM 解决Windows PowerShell和模块路径问题

echo ========================================
echo   VITA 后端服务启动器 (修复版)
echo ========================================
echo.

REM 切换到项目根目录
cd /d "%~dp0\.."

REM 设置环境变量
set DISABLE_WHISPER_ONLINE=true
set PYTHONPATH=%CD%\backend

echo [信息] 项目目录: %CD%
echo [信息] Python路径: %PYTHONPATH%
echo [信息] Whisper在线下载: 已禁用
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

REM 切换到backend目录
cd backend

REM 检查依赖
echo [信息] 检查依赖...
python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [警告] uvicorn未安装，正在安装...
    pip install uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo [信息] 启动VITA后端服务...
echo [信息] 访问地址: http://localhost:8000
echo [信息] 健康检查: http://localhost:8000/health
echo [信息] API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ========================================

REM 启动服务
python run_backend.py

pause