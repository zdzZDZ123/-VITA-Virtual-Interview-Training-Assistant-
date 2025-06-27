@echo off
echo === VITA 离线依赖包准备工具 ===
echo.
echo 本工具将帮助您准备离线环境所需的Python和Node依赖包
echo 注意：VITA使用云端API，无需下载模型文件
echo.

:: 创建离线包目录
if not exist offline_packages mkdir offline_packages
if not exist offline_packages\python mkdir offline_packages\python
if not exist offline_packages\node mkdir offline_packages\node

echo [步骤 1/4] 下载Python依赖包...
echo.

:: 如果有网络，下载Python包
if exist backend\requirements.txt (
    echo 正在下载后端依赖包...
    pip download -r backend\requirements.txt -d offline_packages\python --extra-index-url https://download.pytorch.org/whl/cpu
    
    :: 下载音频处理相关包
    echo 正在下载音频处理依赖包...
    pip download soundfile librosa -d offline_packages\python 2>nul
) else (
    echo ⚠️ 找不到 backend\requirements.txt
)

echo.
echo [步骤 2/4] 下载Node.js依赖包...
echo.

:: 检查前端依赖
cd frontend
if exist package.json (
    echo 正在准备前端离线包...
    :: 使用npm pack创建离线包
    call npm install --package-lock-only
    call npm ci --production --cache .npm-cache
    xcopy /E /I /Y node_modules ..\offline_packages\node\node_modules
    copy package.json ..\offline_packages\node\
    copy package-lock.json ..\offline_packages\node\
) else (
    echo ⚠️ 找不到 frontend\package.json
)
cd ..

echo.
echo [步骤 3/4] 创建离线安装脚本...

:: 创建Python离线安装脚本
echo @echo off > offline_install_python.bat
echo echo 正在安装Python依赖包... >> offline_install_python.bat
echo cd backend >> offline_install_python.bat
echo python -m venv venv >> offline_install_python.bat
echo call venv\Scripts\activate.bat >> offline_install_python.bat
echo pip install --no-index --find-links ..\offline_packages\python -r requirements.txt >> offline_install_python.bat
echo cd .. >> offline_install_python.bat
echo echo Python依赖安装完成！ >> offline_install_python.bat
echo pause >> offline_install_python.bat

:: 创建Node离线安装脚本
echo @echo off > offline_install_node.bat
echo echo 正在安装Node依赖包... >> offline_install_node.bat
echo cd frontend >> offline_install_node.bat
echo if exist node_modules rmdir /s /q node_modules >> offline_install_node.bat
echo xcopy /E /I /Y ..\offline_packages\node\node_modules node_modules >> offline_install_node.bat
echo echo Node依赖安装完成！ >> offline_install_node.bat
echo cd .. >> offline_install_node.bat
echo pause >> offline_install_node.bat

echo.
echo [步骤 4/4] 创建使用说明...

:: 创建说明文件
echo VITA 离线安装包使用说明 > offline_packages\README.txt
echo ====================== >> offline_packages\README.txt
echo. >> offline_packages\README.txt
echo 1. 将整个 offline_packages 文件夹复制到目标机器 >> offline_packages\README.txt
echo 2. 运行 offline_install_python.bat 安装Python依赖 >> offline_packages\README.txt
echo 3. 运行 offline_install_node.bat 安装Node依赖 >> offline_packages\README.txt
echo 4. 使用 start_vita_all.bat 启动所有服务 >> offline_packages\README.txt
echo. >> offline_packages\README.txt
echo 注意：确保目标机器已安装以下软件： >> offline_packages\README.txt
echo - Python 3.11+ >> offline_packages\README.txt
echo - Node.js 18+ >> offline_packages\README.txt
echo - 网络连接（访问Llama API和Qwen API） >> offline_packages\README.txt
echo - 有效的API密钥 >> offline_packages\README.txt

echo.
echo ✅ 离线安装包准备完成！
echo.
echo 离线包保存在: %cd%\offline_packages
echo.
pause 