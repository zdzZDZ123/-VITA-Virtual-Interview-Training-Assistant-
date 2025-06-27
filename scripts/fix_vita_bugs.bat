@echo off
echo ====================================
echo   VITA项目Bug修复脚本 v2.0
echo ====================================
echo.

cd /d "%~dp0\.."

echo [1/5] 升级Edge-TTS到最新版本...
cd backend
pip install edge-tts==7.0.2 --upgrade
if %ERRORLEVEL% neq 0 (
    echo ❌ Edge-TTS升级失败，尝试使用国内镜像源...
    pip install edge-tts==7.0.2 --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple/
)
echo ✅ Edge-TTS升级完成

echo.
echo [2/5] 重新安装OpenAI依赖...
pip install openai --upgrade --force-reinstall
if %ERRORLEVEL% neq 0 (
    echo ❌ OpenAI库安装失败，尝试使用国内镜像源...
    pip install openai --upgrade --force-reinstall -i https://pypi.tuna.tsinghua.edu.cn/simple/
)
echo ✅ OpenAI依赖修复完成

echo.
echo [3/5] 构建前端项目...
cd ..\frontend
if exist "node_modules" (
    echo 📦 检测到node_modules存在，继续构建...
) else (
    echo 📦 安装前端依赖...
    npm install
    if %ERRORLEVEL% neq 0 (
        echo ❌ npm install失败，尝试使用yarn...
        yarn install
        if %ERRORLEVEL% neq 0 (
            echo ❌ 前端依赖安装失败，请手动执行: npm install
            goto :error
        )
    )
)

echo 🔨 构建前端项目...
npm run build
if %ERRORLEVEL% neq 0 (
    echo ❌ 前端构建失败，请检查源代码错误
    goto :error
)
echo ✅ 前端构建完成

echo.
echo [4/5] 验证修复结果...
cd ..\backend

echo 🔍 检查依赖版本...
python -c "import edge_tts; print(f'Edge-TTS版本: {edge_tts.__version__}')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ⚠️ Edge-TTS导入测试失败
) else (
    echo ✅ Edge-TTS导入正常
)

python -c "import openai; print(f'OpenAI版本: {openai.__version__}')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ⚠️ OpenAI库导入测试失败
) else (
    echo ✅ OpenAI库导入正常
)

echo.
echo [5/5] 启动测试...
echo 🚀 准备启动VITA服务器进行验证...
echo 提示: 服务器启动后，请访问 http://localhost:8000 测试前端
echo       按 Ctrl+C 停止服务器
echo.

timeout /t 3 /nobreak >nul
python main.py

goto :end

:error
echo.
echo ❌ 修复过程中出现错误，请检查上述错误信息
echo 💡 建议手动执行以下步骤:
echo    1. cd backend && pip install edge-tts==7.0.2 --upgrade
echo    2. cd frontend && npm install && npm run build
echo    3. cd backend && python main.py
pause
exit /b 1

:end
echo.
echo ✅ VITA Bug修复完成！
echo 📊 修复内容:
echo    - Edge-TTS升级到7.0.2版本
echo    - OpenAI客户端兼容性修复
echo    - 前端构建和静态文件服务修复
echo    - TTS引擎重试机制增强
pause 