@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo VITA项目依赖安装脚本 - 使用国内镜像源
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

:: 显示Python版本
echo 🐍 检测到Python版本:
python --version
echo.

:: 检查是否在正确目录
if not exist "requirements.txt" (
    echo ❌ 未找到requirements.txt文件
    echo 请确保在backend目录下运行此脚本
    pause
    exit /b 1
)

:: 运行Python安装脚本
echo 🚀 启动依赖安装程序...
echo.
python install_with_mirrors.py

:: 检查安装结果
if errorlevel 1 (
    echo.
    echo ❌ 安装过程中出现错误
    echo 请查看上方错误信息并手动解决
) else (
    echo.
    echo ✅ 安装完成！
    echo.
    echo 📋 快速测试命令:
    echo    python -c "import torch; print('PyTorch:', torch.__version__)"
    echo    python -c "import whisper; print('Whisper: OK')"
    echo    python -c "import fastapi; print('FastAPI: OK')"
)

echo.
echo 按任意键退出...
pause >nul