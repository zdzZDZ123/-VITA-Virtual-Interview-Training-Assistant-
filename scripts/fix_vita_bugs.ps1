Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   VITA项目Bug修复脚本 v2.0" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootPath = Split-Path -Parent $scriptPath
Set-Location $rootPath

Write-Host "[1/5] 检查Edge-TTS版本..." -ForegroundColor Yellow
Set-Location "backend"
$edgeTtsVersion = python -c "import edge_tts; print(edge_tts.__version__)" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 当前Edge-TTS版本: $edgeTtsVersion" -ForegroundColor Green
    if ($edgeTtsVersion -ne "7.0.2") {
        Write-Host "🔄 升级Edge-TTS到7.0.2..." -ForegroundColor Yellow
        pip install edge-tts==7.0.2 --upgrade
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Edge-TTS升级失败，尝试使用国内镜像源..." -ForegroundColor Red
            pip install edge-tts==7.0.2 --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple/
        }
    }
} else {
    Write-Host "⚠️ Edge-TTS导入失败，重新安装..." -ForegroundColor Yellow
    pip install edge-tts==7.0.2 --upgrade
}

Write-Host ""
Write-Host "[2/5] 检查OpenAI库兼容性..." -ForegroundColor Yellow
$openaiVersion = python -c "import openai; print(openai.__version__)" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 当前OpenAI版本: $openaiVersion" -ForegroundColor Green
} else {
    Write-Host "⚠️ OpenAI库导入失败，重新安装..." -ForegroundColor Yellow
    pip install openai --upgrade --force-reinstall
}

Write-Host ""
Write-Host "[3/5] 检查前端构建..." -ForegroundColor Yellow
Set-Location "..\frontend"
if (Test-Path "dist") {
    Write-Host "✅ 前端已构建" -ForegroundColor Green
} else {
    Write-Host "🔨 构建前端项目..." -ForegroundColor Yellow
    if (Test-Path "node_modules") {
        Write-Host "📦 检测到node_modules存在，继续构建..." -ForegroundColor Cyan
    } else {
        Write-Host "📦 安装前端依赖..." -ForegroundColor Cyan
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ npm install失败" -ForegroundColor Red
            exit 1
        }
    }
    
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 前端构建失败，请检查源代码错误" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 前端构建完成" -ForegroundColor Green
}

Write-Host ""
Write-Host "[4/5] 验证修复结果..." -ForegroundColor Yellow
Set-Location "..\backend"

Write-Host "🔍 检查依赖版本..." -ForegroundColor Cyan
try {
    $edgeVersion = python -c "import edge_tts; print(f'Edge-TTS: {edge_tts.__version__}')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $edgeVersion" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Edge-TTS导入测试失败" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Edge-TTS检查失败" -ForegroundColor Yellow
}

try {
    $openaiVersion = python -c "import openai; print(f'OpenAI: {openai.__version__}')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $openaiVersion" -ForegroundColor Green
    } else {
        Write-Host "⚠️ OpenAI库导入测试失败" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ OpenAI检查失败" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[5/5] 启动测试..." -ForegroundColor Yellow
Write-Host "🚀 准备启动VITA服务器进行验证..." -ForegroundColor Cyan
Write-Host "提示: 服务器启动后，请访问 http://localhost:8000 测试前端" -ForegroundColor Gray
Write-Host "      按 Ctrl+C 停止服务器" -ForegroundColor Gray
Write-Host ""

Start-Sleep -Seconds 3
python main.py

Write-Host ""
Write-Host "✅ VITA Bug修复完成！" -ForegroundColor Green
Write-Host "📊 修复内容:" -ForegroundColor Cyan
Write-Host "   - Edge-TTS升级到7.0.2版本" -ForegroundColor White
Write-Host "   - OpenAI客户端兼容性修复" -ForegroundColor White
Write-Host "   - 前端构建和静态文件服务修复" -ForegroundColor White
Write-Host "   - TTS引擎重试机制增强" -ForegroundColor White 