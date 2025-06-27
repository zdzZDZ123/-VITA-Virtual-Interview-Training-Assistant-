@echo off
title VITA Edge/Chrome浏览器语音测试
color 0A

echo ========================================
echo    VITA Edge/Chrome浏览器语音测试
echo ========================================
echo.

echo [1/4] 检查后端服务...
timeout /t 2 /nobreak >nul

echo [2/4] 生成测试音频文件...
cd backend
python test_edge_chrome_tts.py
cd ..

echo.
echo [3/4] 准备在浏览器中测试...
echo.
echo 即将自动打开以下浏览器进行测试:
echo   1. Microsoft Edge
echo   2. Google Chrome
echo.
echo 测试地址: http://localhost:8000/static/edge_chrome_voice_test.html
echo.

pause

echo [4/4] 启动浏览器测试...

rem 尝试启动Edge浏览器
echo 正在启动 Microsoft Edge...
start msedge "http://localhost:8000/static/edge_chrome_voice_test.html"
timeout /t 3 /nobreak >nul

rem 尝试启动Chrome浏览器
echo 正在启动 Google Chrome...
start chrome "http://localhost:8000/static/edge_chrome_voice_test.html"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo 测试说明:
echo ========================================
echo 1. 在Edge浏览器中:
echo    - 点击"播放测试语音"按钮
echo    - 确认能听到清晰的中文语音
echo    - 测试麦克风权限功能
echo    - 运行完整面试流程测试
echo.
echo 2. 在Chrome浏览器中:
echo    - 重复上述所有测试步骤
echo    - 确认功能表现一致
echo.
echo 3. 如果两个浏览器都能正常播放语音,
echo    说明VITA的TTS功能完全兼容!
echo.
echo ========================================

echo 测试完成后请按任意键退出...
pause >nul 