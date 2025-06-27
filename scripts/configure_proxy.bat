@echo off
echo === VITA 代理配置工具 ===
echo.

:: 检查是否需要配置代理
set /p USE_PROXY="是否需要配置代理？(y/n): "

if /i "%USE_PROXY%"=="y" (
    echo.
    echo 请输入代理信息：
    set /p PROXY_HOST="代理服务器地址（例如：proxy.company.com）: "
    set /p PROXY_PORT="代理端口（例如：8080）: "
    set /p PROXY_USER="代理用户名（如果不需要认证请直接回车）: "
    
    if not "%PROXY_USER%"=="" (
        set /p PROXY_PASS="代理密码: "
        set PROXY_URL=http://%PROXY_USER%:%PROXY_PASS%@%PROXY_HOST%:%PROXY_PORT%
    ) else (
        set PROXY_URL=http://%PROXY_HOST%:%PROXY_PORT%
    )
    
    echo.
    echo 正在配置 npm 代理...
    call npm config set proxy %PROXY_URL%
    call npm config set https-proxy %PROXY_URL%
    
    echo 正在配置 pip 代理...
    echo [global] > pip.ini
    echo proxy = %PROXY_URL% >> pip.ini
    
    echo 正在设置环境变量...
    setx HTTP_PROXY %PROXY_URL%
    setx HTTPS_PROXY %PROXY_URL%
    set HTTP_PROXY=%PROXY_URL%
    set HTTPS_PROXY=%PROXY_URL%
    
    echo.
    echo ✅ 代理配置完成！
) else (
    echo.
    echo 正在清除代理配置...
    call npm config delete proxy
    call npm config delete https-proxy
    if exist pip.ini del pip.ini
    
    echo ✅ 代理配置已清除！
)

echo.
pause 