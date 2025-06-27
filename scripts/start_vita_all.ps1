# PowerShell脚本：一键启动完整VITA系统
param(
    [switch]$SkipPortCheck = $false,
    [switch]$BackendOnly = $false,
    [switch]$FrontendOnly = $false
)

Write-Host "🚀 VITA虚拟面试助手系统启动脚本" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

# 函数：检查端口占用并清理
function Clear-Port {
    param([int]$Port)
    
    if ($SkipPortCheck) {
        return
    }
    
    try {
        $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                     Select-Object -ExpandProperty OwningProcess -Unique
        
        if ($processes) {
            Write-Host "🔪 清理端口$Port占用进程..." -ForegroundColor Yellow
            foreach ($pid in $processes) {
                try {
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    Write-Host "  终止进程 PID: $pid" -ForegroundColor Gray
                } catch {
                    Write-Host "  无法终止进程 PID: $pid" -ForegroundColor Red
                }
            }
            Start-Sleep -Seconds 2
            Write-Host "✅ 端口$Port清理完成" -ForegroundColor Green
        } else {
            Write-Host "📋 端口$Port未被占用" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️ 端口${Port}检查失败: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# 函数：检查Python环境
function Test-PythonEnvironment {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
            return $true
        }
    } catch {}
    
    Write-Host "❌ Python未安装或不在PATH中" -ForegroundColor Red
    return $false
}

# 函数：检查Node.js环境
function Test-NodeEnvironment {
    try {
        $nodeVersion = node --version 2>&1
        $npmVersion = npm --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
            Write-Host "✅ npm: $npmVersion" -ForegroundColor Green
            return $true
        }
    } catch {}
    
    Write-Host "❌ Node.js未安装或不在PATH中" -ForegroundColor Red
    return $false
}

# 函数：启动后端
function Start-Backend {
    Write-Host "`n🔧 启动VITA后端服务..." -ForegroundColor Cyan
    
    # 清理端口
    Clear-Port -Port 8000
    
    # 启动后端
    try {
        $backendProcess = Start-Process -FilePath "python" -ArgumentList "start_vita_backend.py" -PassThru -WindowStyle Normal
        Write-Host "✅ 后端服务已启动 (PID: $($backendProcess.Id))" -ForegroundColor Green
        Write-Host "📍 后端地址: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "📚 API文档: http://localhost:8000/docs" -ForegroundColor Cyan
        return $backendProcess
    } catch {
        Write-Host "❌ 后端启动失败: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 函数：启动前端
function Start-Frontend {
    Write-Host "`n🎨 启动VITA前端服务..." -ForegroundColor Cyan
    
    # 检查前端目录
    if (!(Test-Path "frontend\package.json")) {
        Write-Host "❌ 未找到frontend目录" -ForegroundColor Red
        return $null
    }
    
    # 清理端口
    Clear-Port -Port 5173
    
    # 启动前端
    try {
        $frontendProcess = Start-Process -FilePath "powershell" -ArgumentList "-File", "start_frontend_dev.ps1" -PassThru -WindowStyle Normal
        Write-Host "✅ 前端服务已启动 (PID: $($frontendProcess.Id))" -ForegroundColor Green
        Write-Host "📍 前端地址: http://localhost:5173" -ForegroundColor Cyan
        return $frontendProcess
    } catch {
        Write-Host "❌ 前端启动失败: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 主流程
try {
    # 环境检查
    Write-Host "`n🔍 检查运行环境..." -ForegroundColor Cyan
    $pythonOk = Test-PythonEnvironment
    $nodeOk = Test-NodeEnvironment
    
    if (!$FrontendOnly -and !$pythonOk) {
        Write-Host "❌ Python环境不可用，无法启动后端" -ForegroundColor Red
        exit 1
    }
    
    if (!$BackendOnly -and !$nodeOk) {
        Write-Host "❌ Node.js环境不可用，无法启动前端" -ForegroundColor Red
        exit 1
    }
    
    $processes = @()
    
    # 启动服务
    if (!$FrontendOnly) {
        $backendProc = Start-Backend
        if ($backendProc) {
            $processes += $backendProc
        }
        Start-Sleep -Seconds 3  # 等待后端启动
    }
    
    if (!$BackendOnly) {
        $frontendProc = Start-Frontend
        if ($frontendProc) {
            $processes += $frontendProc
        }
    }
    
    if ($processes.Count -eq 0) {
        Write-Host "❌ 没有服务成功启动" -ForegroundColor Red
        exit 1
    }
    
    # 显示启动摘要
    Write-Host "`n" + "=" * 50 -ForegroundColor Gray
    Write-Host "🎉 VITA系统启动完成!" -ForegroundColor Green
    Write-Host "=" * 50 -ForegroundColor Gray
    
    if (!$FrontendOnly) {
        Write-Host "🔧 后端服务: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "📚 API文档: http://localhost:8000/docs" -ForegroundColor Cyan
    }
    
    if (!$BackendOnly) {
        Write-Host "🎨 前端界面: http://localhost:5173" -ForegroundColor Cyan
    }
    
    Write-Host "`n💡 按任意键停止所有服务..." -ForegroundColor Yellow
    Read-Host
    
} finally {
    # 清理进程
    Write-Host "`n🛑 正在停止所有服务..." -ForegroundColor Yellow
    
    if ($processes) {
        foreach ($proc in $processes) {
            try {
                if (!$proc.HasExited) {
                    $proc.Kill()
                    Write-Host "  已停止服务 PID: $($proc.Id)" -ForegroundColor Gray
                }
            } catch {
                Write-Host "  无法停止服务 PID: $($proc.Id)" -ForegroundColor Red
            }
        }
    }
    
    # 强制清理端口
    if (!$FrontendOnly) {
        Clear-Port -Port 8000
    }
    if (!$BackendOnly) {
        Clear-Port -Port 5173
    }
    
    Write-Host "✅ 所有服务已停止" -ForegroundColor Green
} 