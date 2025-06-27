@echo off
echo 🚀 启动VITA前端开发服务器...
cd frontend
if not exist node_modules (
    echo 📦 安装依赖...
    npm install
)
echo 🎨 启动Vite开发服务器...
npm run dev
pause 