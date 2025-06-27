# OpenAI依赖已移除，现在使用纯本地语音服务
@echo off
echo ================================================
echo VITA 实时语音对话功能启动器
echo ================================================
echo.

:: 设置环境变量
# OpenAI配置已移除
set QWEN_API_KEY=__REMOVED_API_KEY__

echo 🔧 配置环境变量...
# OpenAI配置已移除
echo.

:: 启动后端服务
echo 🚀 启动 VITA 后端服务...
echo 端口: 8000
echo WebSocket: ws://localhost:8000/api/v1/ws/voice/{session_id}
echo.

cd backend
start cmd /k "title VITA Backend && echo 启动后端服务... && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: 等待后端启动
echo ⏳ 等待后端启动完成...
timeout /t 5 /nobreak >nul

:: 在浏览器中打开测试页面
echo 🌐 打开语音对话测试页面...
start http://localhost:8000/docs
start "VITA Voice Test" "%cd%\..\test_voice_conversation.html"

echo.
echo ================================================
echo ✅ VITA 实时语音对话功能已启动！
echo ================================================
echo.
echo 📖 使用说明:
echo 1. 后端API文档: http://localhost:8000/docs
echo 2. 语音测试页面: test_voice_conversation.html
echo 3. WebSocket状态: http://localhost:8000/api/v1/ws/status
echo.
echo 🎤 语音对话测试步骤:
echo 1. 在测试页面点击"连接"按钮
echo 2. 允许浏览器访问麦克风
echo 3. 点击麦克风按钮开始录音
echo 4. 说话后等待AI回复
echo.
echo 💡 提示:
echo - 确保麦克风权限已开启
echo - 使用Chrome/Edge浏览器以获得最佳兼容性
echo - 保持网络连接稳定
echo.
echo ⚠️  关闭时请先按Ctrl+C停止后端服务
echo.
pause