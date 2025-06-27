#!/bin/bash
# VITA项目依赖安装脚本 - 使用国内镜像源
# 支持Linux和macOS

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "========================================"
echo "VITA项目依赖安装脚本 - 使用国内镜像源"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        print_error "未找到Python，请先安装Python 3.8+"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 显示Python版本
print_info "检测到Python版本:"
$PYTHON_CMD --version
echo

# 检查Python版本是否符合要求
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MIN_VERSION="3.8"

if [ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]; then
    print_error "Python版本过低，需要3.8+，当前版本: $PYTHON_VERSION"
    exit 1
fi

# 检查是否在正确目录
if [ ! -f "requirements.txt" ]; then
    print_error "未找到requirements.txt文件"
    print_error "请确保在backend目录下运行此脚本"
    exit 1
fi

# 检查pip是否安装
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    print_error "pip未安装，请先安装pip"
    exit 1
fi

# 给Python脚本执行权限
if [ -f "install_with_mirrors.py" ]; then
    chmod +x install_with_mirrors.py
fi

# 运行Python安装脚本
print_info "启动依赖安装程序..."
echo

if $PYTHON_CMD install_with_mirrors.py; then
    echo
    print_success "安装完成！"
    echo
    print_info "快速测试命令:"
    echo "   $PYTHON_CMD -c \"import torch; print('PyTorch:', torch.__version__)\""
    echo "   $PYTHON_CMD -c \"import whisper; print('Whisper: OK')\""
    echo "   $PYTHON_CMD -c \"import fastapi; print('FastAPI: OK')\""
else
    echo
    print_error "安装过程中出现错误"
    print_error "请查看上方错误信息并手动解决"
    exit 1
fi

echo
print_success "脚本执行完成！"