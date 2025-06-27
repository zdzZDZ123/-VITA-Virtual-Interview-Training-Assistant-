# PowerShell脚本：启动VITA前端开发服务器
Write-Host "🎨 启动VITA前端开发服务器..." -ForegroundColor Green

# 检查是否在正确目录
if (!(Test-Path "frontend\package.json")) {
    Write-Host "❌ 未找到frontend目录，请在项目根目录运行此脚本" -ForegroundColor Red
    exit 1
}

# 进入frontend目录
Set-Location frontend

# 检查Node.js和npm
try {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "✅ Node.js版本: $nodeVersion" -ForegroundColor Green
    Write-Host "✅ npm版本: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js或npm未安装，请先安装Node.js" -ForegroundColor Red
    exit 1
}

# 检查依赖是否已安装
if (!(Test-Path "node_modules")) {
    Write-Host "📦 安装依赖..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
}

Write-Host "🚀 启动开发服务器..." -ForegroundColor Green
Write-Host "📍 前端地址: http://localhost:5173" -ForegroundColor Cyan
Write-Host "📍 后端地址: http://localhost:8000" -ForegroundColor Cyan
Write-Host "💡 按Ctrl+C停止服务" -ForegroundColor Yellow

# 启动开发服务器
npm run dev 