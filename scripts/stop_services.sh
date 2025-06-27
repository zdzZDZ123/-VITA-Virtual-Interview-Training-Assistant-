#!/bin/bash

# VITA 项目停止脚本
# 用于停止所有运行中的服务

echo "🛑 正在停止 VITA 服务..."

# 从 PID 文件中读取进程ID并停止
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "- 停止后端服务 (PID: $BACKEND_PID)"
        kill $BACKEND_PID
    fi
    rm -f logs/backend.pid
fi

if [ -f "logs/vision.pid" ]; then
    VISION_PID=$(cat logs/vision.pid)
    if kill -0 $VISION_PID 2>/dev/null; then
        echo "- 停止视觉服务 (PID: $VISION_PID)"
        kill $VISION_PID
    fi
    rm -f logs/vision.pid
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "- 停止前端服务 (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID
    fi
    rm -f logs/frontend.pid
fi

# 备用方案：通过端口查找并停止进程
echo "- 检查并清理剩余进程..."

# 停止占用8000端口的进程 (后端)
BACKEND_PORT_PID=$(lsof -ti:8000)
if [ ! -z "$BACKEND_PORT_PID" ]; then
    echo "  发现后端服务占用端口8000 (PID: $BACKEND_PORT_PID)"
    kill $BACKEND_PORT_PID 2>/dev/null
fi

# 停止占用8001端口的进程 (视觉服务)
VISION_PORT_PID=$(lsof -ti:8001)
if [ ! -z "$VISION_PORT_PID" ]; then
    echo "  发现视觉服务占用端口8001 (PID: $VISION_PORT_PID)"
    kill $VISION_PORT_PID 2>/dev/null
fi

# 停止占用5173端口的进程 (前端)
FRONTEND_PORT_PID=$(lsof -ti:5173)
if [ ! -z "$FRONTEND_PORT_PID" ]; then
    echo "  发现前端服务占用端口5173 (PID: $FRONTEND_PORT_PID)"
    kill $FRONTEND_PORT_PID 2>/dev/null
fi

# 等待进程完全停止
sleep 2

echo "✅ 所有 VITA 服务已停止"

# 清理日志文件 (可选)
read -p "🗑️  是否清理日志文件? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f logs/*.log
    echo "✅ 日志文件已清理"
fi 