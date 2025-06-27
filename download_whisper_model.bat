@echo off
echo ========================================
echo VITA Whisper Model Download Tool
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 设置默认模型大小
set MODEL_SIZE=medium
if not "%1"=="" set MODEL_SIZE=%1

echo 📥 准备下载 Whisper 模型: %MODEL_SIZE%
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 创建模型目录
if not exist "whisper_download" mkdir "whisper_download"

REM 检查是否已安装faster-whisper
python -c "import faster_whisper" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ faster-whisper未安装，正在安装...
    pip install faster-whisper
)

REM 运行下载脚本
echo.
echo 🚀 开始下载模型...
echo.

if exist "scripts\download_faster_whisper.py" (
    python scripts\download_faster_whisper.py %MODEL_SIZE% --verify
) else (
    echo ❌ 错误：下载脚本不存在
    echo 请确保在VITA项目根目录运行此脚本
    pause
    exit /b 1
)

if %errorlevel% equ 0 (
    echo.
    echo ✅ 模型下载成功！
    echo.
    
    REM 验证模型
    echo 🔍 验证模型...
    python -c "from scripts.download_faster_whisper import verify_model; verify_model('%MODEL_SIZE%')" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ 模型验证通过！
    ) else (
        echo ⚠️ 模型验证失败，但可能仍可使用
    )
) else (
    echo.
    echo ❌ 模型下载失败！
    echo.
    echo 可能的解决方案：
    echo 1. 检查网络连接
    echo 2. 使用VPN或代理
    echo 3. 手动下载模型文件
)

echo.
echo ========================================
echo 完成！按任意键退出...
pause >nul 