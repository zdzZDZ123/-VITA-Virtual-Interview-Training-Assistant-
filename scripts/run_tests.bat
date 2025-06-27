@echo off
echo ====================================
echo VITA 面试功能修复测试
echo ====================================
echo.
echo 请确保后端服务已经启动在 http://localhost:8000
echo.
echo 按任意键开始测试...
pause >nul
echo.

python test_fixes.py

echo.
echo ====================================
echo 测试完成！
echo ====================================
echo.
echo 按任意键退出...
pause >nul 