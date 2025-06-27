#!/bin/bash

echo "========================================"
echo "VITA 本地 Whisper 安装脚本"
echo "========================================"
echo

echo "[1/5] 检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到Python，请先安装Python 3.8+"
    exit 1
fi

echo
echo "[2/5] 安装基础依赖..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "错误: 基础依赖安装失败"
    exit 1
fi

echo
echo "[3/5] 安装本地Whisper依赖..."
echo "正在安装 faster-whisper..."
pip3 install faster-whisper>=1.0.0
if [ $? -ne 0 ]; then
    echo "警告: faster-whisper 安装失败，尝试安装原版whisper"
    pip3 install whisper
    if [ $? -ne 0 ]; then
        echo "警告: whisper 安装失败，尝试从GitHub源安装..."
        pip3 install git+https://github.com/openai/whisper.git
        if [ $? -ne 0 ]; then
            echo "错误: 所有whisper安装方式都失败，请检查网络连接后重试"
            exit 1
        fi
    fi
fi

echo
echo "正在安装 PyTorch..."
# 检测系统架构
if [[ "$(uname -m)" == "arm64" ]] || [[ "$(uname -m)" == "aarch64" ]]; then
    echo "检测到ARM架构，安装ARM版本PyTorch"
    pip3 install torch torchaudio
else
    echo "检测到x86架构，安装CPU版本PyTorch"
    pip3 install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

if [ $? -ne 0 ]; then
    echo "警告: PyTorch 安装失败，尝试默认版本"
    pip3 install torch torchaudio
fi

echo
echo "[4/5] 检查GPU支持..."
python3 -c "import torch; print('CUDA可用:', torch.cuda.is_available()); print('CUDA设备数:', torch.cuda.device_count() if torch.cuda.is_available() else 0)"

echo
echo "[5/5] 下载本地Whisper模型..."
read -p "是否下载medium模型到本地? (y/n): " download_model
if [[ $download_model == "y" || $download_model == "Y" ]]; then
    echo "正在下载faster-whisper-medium模型..."
    pip3 install huggingface_hub
    python3 scripts/download_faster_whisper.py medium --install-deps
    if [ $? -eq 0 ]; then
        echo "✅ 模型下载成功"
    else
        echo "⚠️ 模型下载失败，将使用在线模式"
    fi
else
    echo "跳过模型下载，将使用在线模式或缓存模型"
fi

echo
echo "========================================"
echo "安装完成！"
echo "========================================"
echo
echo "模型信息:"
echo "- tiny(39MB): 最快但精度较低"
echo "- base(74MB): 快速且精度尚可"  
echo "- small(244MB): 平衡选择"
echo "- medium(769MB): 推荐，精度和速度平衡 ✅"
echo "- large(1550MB): 最高精度但较慢"
echo
echo "下一步:"
echo "1. 运行: python3 start_vita_backend.py"
echo "2. 或手动下载其他模型: python3 scripts/download_faster_whisper.py [模型大小]"
echo
echo "离线部署:"
echo "- 模型位置: whisper_download/medium/"
echo "- 复制整个whisper_download目录到目标机器即可离线使用"
echo