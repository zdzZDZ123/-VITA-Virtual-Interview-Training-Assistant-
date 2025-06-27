@echo off
echo ========================================
echo VITA Whisper 离线安装脚本
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
echo [2/4] 检查依赖包目录...
if not exist "whisper_pkgs" (
    echo 错误: 未找到 whisper_pkgs 目录
    echo 请先按照 WHISPER_OFFLINE_INSTALLATION.md 文档准备离线依赖包
    pause
    exit /b 1
)

echo 找到依赖包目录，开始安装...
echo.
echo [3/4] 离线安装依赖包...
echo 安装 PyTorch 和相关依赖...
pip install --no-index --find-links=".\whisper_pkgs" torch numpy tqdm more-itertools tiktoken setuptools wheel
if %errorlevel% neq 0 (
    echo 错误: 依赖包安装失败
    echo 请检查 whisper_pkgs 目录中是否包含所有必要的 wheel 文件
    pause
    exit /b 1
)

echo.
echo [4/4] 安装Whisper源码...
if exist "backend\whisper-main\whisper-main" (
    echo 找到Whisper源码目录，开始安装...
    cd "backend\whisper-main\whisper-main"
    pip install -e .
    if %errorlevel% neq 0 (
        echo 错误: Whisper源码安装失败
        cd ..\..\..
        pause
        exit /b 1
    )
    cd ..\..\..
    echo Whisper源码安装成功！
) else (
    echo 警告: 未找到Whisper源码目录 backend\whisper-main\whisper-main
    echo 请手动下载Whisper源码并放置到正确位置
    echo 或使用在线安装: pip install whisper
    pip install whisper
    if %errorlevel% neq 0 (
        echo 错误: 在线安装Whisper也失败了
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo 验证安装...
echo ========================================
python -c "import torch; import whisper; print('✓ 所有依赖安装成功!'); print(f'✓ PyTorch 版本: {torch.__version__}'); print(f'✓ CUDA 可用: {torch.cuda.is_available()}')"
if %errorlevel% neq 0 (
    echo 警告: 验证过程中出现问题，但安装可能已完成
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo 现在可以在 .env 文件中设置 USE_LOCAL_WHISPER=true 来启用本地Whisper
echo 运行 python test_local_whisper.py 来测试本地Whisper功能
echo.
pause