@echo off
echo ========================================
echo VITA Whisper 依赖包下载脚本
echo ========================================
echo 此脚本需要在有网络连接的环境中运行
echo 用于下载Whisper离线安装所需的所有依赖包
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/3] 创建依赖包下载目录...
if not exist "whisper_pkgs" (
    mkdir whisper_pkgs
    echo 创建目录: whisper_pkgs
) else (
    echo 目录已存在: whisper_pkgs
)

echo.
echo [3/3] 下载Whisper依赖包...
echo 正在下载核心依赖包...
echo 注意: PyTorch可能较大，请耐心等待...
echo.

echo 下载 torch, numpy, tqdm, more-itertools, tiktoken, setuptools, wheel...
pip download torch numpy tqdm more-itertools tiktoken setuptools wheel -d whisper_pkgs
if %errorlevel% neq 0 (
    echo 错误: 依赖包下载失败
    echo 请检查网络连接或尝试使用国内镜像源
    echo 例如: pip download -i https://pypi.tuna.tsinghua.edu.cn/simple torch numpy tqdm more-itertools tiktoken setuptools wheel -d whisper_pkgs
    pause
    exit /b 1
)

echo.
echo ========================================
echo 下载完成！
echo ========================================
echo 依赖包已下载到 whisper_pkgs 目录
echo.
echo 目录内容:
dir whisper_pkgs
echo.
echo ========================================
echo 重要提示:
echo ========================================
echo 1. PyTorch建议手动下载匹配的版本:
echo    访问: https://pytorch.org/get-started/locally/
echo    选择适合你的CUDA版本和Python版本的wheel文件
echo    下载后放入 whisper_pkgs 目录
echo.
echo 2. 如果需要GPU加速，确保下载CUDA版本的PyTorch
echo.
echo 3. 将整个 whisper_pkgs 目录拷贝到目标机器
echo    然后运行 install_whisper_offline.bat 进行离线安装
echo.
echo 4. 如果下载的torch不是你需要的版本，请删除并手动下载正确版本
echo.
pause