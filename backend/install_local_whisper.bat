@echo off
echo ========================================
echo VITA 本地 Whisper 安装脚本
echo ========================================
echo.

echo [1/4] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/4] 安装基础依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 错误: 基础依赖安装失败
    pause
    exit /b 1
)

echo.
echo [3/4] 安装本地Whisper依赖...
echo Installing faster-whisper...
pip install faster-whisper
if %ERRORLEVEL% neq 0 (
    echo Failed to install faster-whisper, trying whisper instead...
    pip install whisper
    if %ERRORLEVEL% neq 0 (
        echo Failed to install whisper, trying from GitHub source...
        pip install git+https://github.com/openai/whisper.git
        if %ERRORLEVEL% neq 0 (
            echo Failed to install whisper from all sources. Please check your internet connection and try again.
            pause
            exit /b 1
        )
    )
)

echo.
echo 正在安装 PyTorch (CPU版本)...
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
if %errorlevel% neq 0 (
    echo 警告: PyTorch CPU版本安装失败，尝试默认版本
    pip install torch torchaudio
)

echo.
echo [4/5] 检查GPU支持...
python -c "import torch; print('CUDA可用:', torch.cuda.is_available()); print('CUDA设备数:', torch.cuda.device_count() if torch.cuda.is_available() else 0)"

echo.
echo [5/5] 下载本地Whisper模型...
set /p DOWNLOAD_MODEL="是否下载medium模型到本地? (y/n): "
if /i "%DOWNLOAD_MODEL%"=="y" (
    echo 正在下载faster-whisper-medium模型...
    python -m pip install huggingface_hub
    python scripts\download_faster_whisper.py medium --install-deps
    if %errorlevel% equ 0 (
        echo ✅ 模型下载成功
    ) else (
        echo ⚠️ 模型下载失败，将使用在线模式
    )
) else (
    echo 跳过模型下载，将使用在线模式或缓存模型
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 模型信息:
echo - tiny(39MB): 最快但精度较低
echo - base(74MB): 快速且精度尚可  
echo - small(244MB): 平衡选择
echo - medium(769MB): 推荐，精度和速度平衡 ✅
echo - large(1550MB): 最高精度但较慢
echo.
echo 下一步:
echo 1. 运行: python start_vita_backend.py
echo 2. 或手动下载其他模型: python scripts\download_faster_whisper.py [模型大小]
echo.
echo 离线部署:
echo - 模型位置: whisper_download\medium\
echo - 复制整个whisper_download目录到目标机器即可离线使用
echo.
pause