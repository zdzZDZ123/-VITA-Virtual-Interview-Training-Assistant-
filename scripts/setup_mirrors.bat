@echo off
echo 🚀 配置VITA项目镜像源
echo ====================================

echo 📦 配置pip镜像源...
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

echo 🤗 配置HuggingFace镜像源...
set HF_ENDPOINT=https://hf-mirror.com
setx HF_ENDPOINT "https://hf-mirror.com"

echo 🔧 更新pip和基础工具...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

echo 📚 安装/升级语音相关包...
pip install --upgrade faster-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install --upgrade edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple  
pip install --upgrade openai-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install --upgrade huggingface-hub -i https://pypi.tuna.tsinghua.edu.cn/simple

echo ✅ 镜像源配置完成！
echo 🌐 pip镜像源: 清华大学
echo 🤗 HuggingFace镜像源: hf-mirror.com
echo 📋 当前配置:
pip config list

pause 