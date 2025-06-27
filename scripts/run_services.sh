#!/bin/bash

# VITA 项目启动脚本
# 用于同时启动后端服务、视觉分析服务和前端应用

echo "🚀 启动 VITA 虚拟面试助理 (含语音功能)..."

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 检查 Node.js 环境  
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到 npm，请先安装 Node.js"
    exit 1
fi

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

echo "🌟 启动服务..."

# 启动后端服务 (端口 8000)
echo "- 启动后端服务 (http://localhost:8000)"
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动视觉分析服务 (端口 8001)  
echo "- 启动视觉分析服务 (http://localhost:8001)"
cd vision_service
python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload > ../logs/vision.log 2>&1 &
VISION_PID=$!
cd ..

# 等待视觉服务启动
sleep 3

# 启动前端开发服务器 (端口 5173)
echo "- 启动前端服务 (http://localhost:5173)"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 保存 PID 到文件，方便后续停止
echo $BACKEND_PID > logs/backend.pid
echo $VISION_PID > logs/vision.pid  
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "✅ 所有服务已启动！"
echo ""
echo "📍 访问地址:"
echo "   前端应用:     http://localhost:5173"
echo "   后端 API:     http://localhost:8000"
echo "   API 文档:     http://localhost:8000/docs"
echo "   视觉服务:     http://localhost:8001"
echo "   视觉 API 文档: http://localhost:8001/docs"
echo ""
echo "📋 注意事项:"
echo "   1. 确保设置了 QWEN_API_KEY 或 LLAMA_API_KEY 环境变量"
echo "   2. 面试过程中需要授权摄像头和麦克风访问权限"
echo "   3. 建议使用 Chrome 或 Edge 浏览器"
echo "   4. 语音功能需要稳定的网络连接"
echo ""
echo "🛑 停止服务: ./stop_services.sh"
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