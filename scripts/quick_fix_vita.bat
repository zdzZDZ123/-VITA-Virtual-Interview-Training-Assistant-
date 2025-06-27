@echo off
echo === VITA 快速修复工具 ===
echo.
echo 本工具将尝试解决常见的VITA项目问题
echo.

:: 设置变量
set PYTHON_CMD=python
set NPM_CMD=npm
set VENV_PATH=backend\venv

:: 检查Python
echo [1/6] 检查Python环境...
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python 3.11+
    pause
    exit /b 1
)
echo ✅ Python已安装

:: 检查Node.js
echo [2/6] 检查Node.js环境...
%NPM_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装或未添加到PATH
    echo 请先安装Node.js 18+
    pause
    exit /b 1
)
echo ✅ Node.js已安装

:: 创建Python虚拟环境
echo [3/6] 设置Python虚拟环境...
if not exist %VENV_PATH% (
    echo 创建虚拟环境...
    cd backend
    %PYTHON_CMD% -m venv venv
    cd ..
)
echo ✅ 虚拟环境已准备

:: 尝试使用国内镜像源安装Python依赖
echo [4/6] 安装Python依赖（使用国内镜像）...
cd backend
call venv\Scripts\activate.bat

:: 创建pip配置文件使用国内镜像
echo [global] > pip.ini
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple >> pip.ini
echo trusted-host = pypi.tuna.tsinghua.edu.cn >> pip.ini

:: 升级pip
python -m pip install --upgrade pip

:: 安装依赖（分组安装以避免超时）
echo 安装核心依赖...
pip install fastapi uvicorn python-multipart pydantic pydantic-settings

echo 安装AI相关依赖...
pip install httpx aiohttp requests

echo 安装音频处理依赖...
pip install numpy scipy soundfile

:: 尝试安装PyTorch（CPU版本）
echo 安装PyTorch（可能需要较长时间）...
pip install torch -f https://download.pytorch.org/whl/torch_stable.html

echo 安装其他依赖...
pip install python-dotenv loguru pytest pytest-asyncio orjson tqdm anyio aiofiles pyyaml email-validator prometheus-client psutil pytest-cov

:: 尝试安装Whisper（如果失败也继续）
echo 尝试安装Whisper...
pip install openai-whisper || echo 本地Whisper安装失败，但不影响基础功能

cd ..

:: 安装前端依赖（使用国内镜像）
echo [5/6] 安装前端依赖（使用淘宝镜像）...
cd frontend
call npm config set registry https://registry.npmmirror.com
call npm install --legacy-peer-deps
cd ..

:: 创建必要的目录
echo [6/6] 创建必要的目录结构...
if not exist cache mkdir cache
if not exist backend\cache mkdir backend\cache
if not exist backend\logs mkdir backend\logs

:: 创建基础环境配置文件
if not exist .env (
    echo 创建.env配置文件...
    echo # VITA Configuration > .env
    echo LLAMA_API_KEY=your_llama_api_key_here >> .env
    echo LLAMA_API_BASE_URL=https://api.llama-api.com/v1 >> .env
    echo QWEN_API_KEY=your_qwen_api_key_here >> .env
    echo USE_LOCAL_WHISPER=false >> .env
    echo TTS_PROVIDER=api >> .env
    echo USE_QWEN_FALLBACK=true >> .env
    echo PREFER_LLAMA=true >> .env
    echo ENABLE_AUTO_SWITCH=true >> .env
    echo ENVIRONMENT=development >> .env
    echo LOG_LEVEL=INFO >> .env
    echo CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"] >> .env
)

echo.
echo ===================================
echo ✅ VITA项目修复完成！
echo ===================================
echo.
echo 下一步：
echo 1. 编辑 .env 文件，配置API密钥：
echo    - LLAMA_API_KEY（Llama API服务）
echo    - QWEN_API_KEY（通义千问API服务）
echo 2. 运行 start_vita_all.bat 启动所有服务
echo.
echo 如果仍有问题，请尝试：
echo - 运行 configure_proxy.bat 配置代理
echo - 运行 offline_install_helper.bat 准备离线安装包
echo.
pause 