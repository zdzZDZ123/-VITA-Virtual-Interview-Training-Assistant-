# OpenAI依赖已移除，现在使用纯本地语音服务
#!/bin/bash

# VITA 项目启动脚本 (含API密钥配置)
# 自动配置API密钥并启动所有服务
# VITA现在使用纯本地语音服务，不再需要OpenAI Key

echo "🎙️ VITA (Virtual Interview & Training Assistant)"
echo "===================================================="
echo "智能语音面试训练助理启动程序"
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 未提供API密钥，请作为第一个参数传入"
    exit 1
fi

# 设置API密钥 - 支持Qwen或Llama
export QWEN_API_KEY=$1
export LLAMA_API_KEY=$1

# 设置服务端口
export BACKEND_PORT=8000
export VISION_PORT=8001
export FRONTEND_PORT=5173

echo "✅ API密钥已设置"
echo "================================================="
echo "🚀 VITA 服务启动配置"
echo "================================================="
echo "   API Key: ${1:0:10}..."
echo "   日志级别: $LOG_LEVEL"
echo "   启动模式: $START_MODE"
echo "================================================="
echo ""

# 检查环境依赖
echo "📦 检查环境依赖..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查Node.js环境  
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到npm，请先安装Node.js"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 创建日志目录
mkdir -p logs

echo "📦 安装依赖..."

# 安装后端依赖
echo "- 安装后端依赖"
cd backend
pip install -r requirements.txt > ../logs/backend_install.log 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 后端依赖安装失败，请检查 logs/backend_install.log"
    exit 1
fi
cd ..

# 安装视觉服务依赖
echo "- 安装视觉服务依赖"
cd vision_service
pip install -r requirements.txt > ../logs/vision_install.log 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 视觉服务依赖安装失败，请检查 logs/vision_install.log"
    exit 1
fi
cd ..

# 安装前端依赖
echo "- 安装前端依赖"
cd frontend
npm install > ../logs/frontend_install.log 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 前端依赖安装失败，请检查 logs/frontend_install.log"
    exit 1
fi
cd ..

echo ""
echo "🌟 启动服务..."
echo ""

# 启动后端服务
echo "- 启动后端服务 (http://localhost:8000)"
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动视觉分析服务
echo "- 启动视觉分析服务 (http://localhost:8001)"
cd vision_service
python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload > ../logs/vision.log 2>&1 &
VISION_PID=$!
cd ..

# 等待视觉服务启动
sleep 3

# 启动前端开发服务器
echo "- 启动前端服务 (http://localhost:5173)"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 保存PID到文件
echo $BACKEND_PID > logs/backend.pid
echo $VISION_PID > logs/vision.pid  
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "🎉 所有服务已启动！"
echo ""
echo "📍 访问地址:"
echo "   前端应用:      http://localhost:5173"
echo "   后端API:       http://localhost:8000"
echo "   API文档:       http://localhost:8000/docs"
echo "   视觉服务:      http://localhost:8001"
echo "   视觉API文档:   http://localhost:8001/docs"
echo ""
echo "🔑 功能特性:"
echo "   ✓ GPT-4o驱动的智能面试对话"
echo "   ✓ Whisper高精度语音识别"
echo "   ✓ TTS-HD自然语音合成"
echo "   ✓ MediaPipe实时视觉分析"
echo "   ✓ Nova专业女性AI面试官声音"
echo ""
echo "💡 使用提示:"
echo "   1. 确保浏览器允许摄像头和麦克风权限"
echo "   2. 推荐使用Chrome或Edge浏览器"
echo "   3. 使用 ./stop_services.sh 停止所有服务"
echo ""
echo "📊 查看日志: tail -f logs/*.log"
echo ""
echo "⏳ 服务正在运行中... (按 Ctrl+C 退出)"

# 等待用户中断
trap 'echo ""; echo "🛑 正在停止服务..."; kill $BACKEND_PID $VISION_PID $FRONTEND_PID 2>/dev/null; rm -f logs/*.pid; echo "✅ 所有服务已停止"; exit 0' INT

# 持续监控服务状态
while true; do
    sleep 5
    
    # 检查服务是否还在运行
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ 后端服务已停止"
        break
    fi
    
    if ! kill -0 $VISION_PID 2>/dev/null; then
        echo "❌ 视觉服务已停止"
        break  
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ 前端服务已停止"
        break
    fi
done

echo "🛑 某个服务意外停止，正在清理..."
kill $BACKEND_PID $VISION_PID $FRONTEND_PID 2>/dev/null
rm -f logs/*.pid