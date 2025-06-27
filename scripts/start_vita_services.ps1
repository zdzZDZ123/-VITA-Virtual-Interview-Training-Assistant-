#!/usr/bin/env pwsh

<#
.SYNOPSIS
Start VITA Virtual Interview Assistant Services

.DESCRIPTION
Starts backend API service and frontend development server with API key configuration

.PARAMETER QwenKey
Qwen API Key

.PARAMETER DoubaoKey
Doubao API Key

.PARAMETER Backend
Start backend service only

.PARAMETER Frontend  
Start frontend service only

.EXAMPLE
.\start_vita_services.ps1 -QwenKey "sk-xxx" -DoubaoKey "826cca61-xxx"

.EXAMPLE
.\start_vita_services.ps1 -Backend

.EXAMPLE
.\start_vita_services.ps1 -Frontend
#>

param(
    [string]$QwenKey = "",
    [string]$DoubaoKey = "",
    [switch]$Backend = $false,
    [switch]$Frontend = $false
)

# Set error handling
$ErrorActionPreference = "Stop"

# Get project root directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Green

# Change to project root directory
Set-Location $ProjectRoot

# Set API key environment variables
if ($QwenKey) {
    $env:QWEN_API_KEY = $QwenKey
    Write-Host "Qwen API Key configured" -ForegroundColor Green
}

if ($DoubaoKey) {
    $env:DOUBAO_API_KEY = $DoubaoKey
    Write-Host "Doubao API Key configured" -ForegroundColor Green
}

# Function to start backend service
function Start-BackendService {
    Write-Host "Starting VITA Backend Service..." -ForegroundColor Yellow
    
    # Change to backend directory
    Set-Location "backend"
    
    # Check if main.py exists
    if (-not (Test-Path "main.py")) {
        Write-Error "main.py not found in backend directory"
        return $false
    }
    
    try {
        # Start backend with uvicorn
        Write-Host "Starting uvicorn server on port 8000..." -ForegroundColor Cyan
        python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
        return $true
    }
    catch {
        Write-Error "Failed to start backend: $($_.Exception.Message)"
        return $false
    }
}

# Function to start frontend service
function Start-FrontendService {
    Write-Host "Starting VITA Frontend Service..." -ForegroundColor Yellow
    
    # Change to frontend directory
    Set-Location "frontend"
    
    # Check if package.json exists
    if (-not (Test-Path "package.json")) {
        Write-Error "package.json not found in frontend directory"
        return $false
    }
    
    try {
        # Install dependencies if node_modules doesn't exist
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
            npm install
        }
        
        # Start frontend development server
        Write-Host "Starting development server..." -ForegroundColor Cyan
        npm run dev
        return $true
    }
    catch {
        Write-Error "Failed to start frontend: $($_.Exception.Message)"
        return $false
    }
}

# Function to start all services
function Start-AllServices {
    Write-Host "Starting All VITA Services..." -ForegroundColor Yellow
    
    # Start backend in background
    Write-Host "Starting backend service in background..." -ForegroundColor Cyan
    $backendJob = Start-Job -ScriptBlock {
        param($ProjectRoot, $QwenKey, $DoubaoKey)
        
        Set-Location "$ProjectRoot\backend"
        
        if ($QwenKey) { $env:QWEN_API_KEY = $QwenKey }
        if ($DoubaoKey) { $env:DOUBAO_API_KEY = $DoubaoKey }
        
        python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
    } -ArgumentList $ProjectRoot, $QwenKey, $DoubaoKey
    
    # Wait a moment for backend to start
    Start-Sleep -Seconds 5
    
    # Check if backend started successfully
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/system/status" -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "Backend service started successfully" -ForegroundColor Green
        }
    }
    catch {
        Write-Warning "Backend may not have started properly"
    }
    
    # Start frontend
    Set-Location "$ProjectRoot\frontend"
    
    # Install dependencies if needed
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
        npm install
    }
    
    Write-Host "Starting frontend development server..." -ForegroundColor Cyan
    npm run dev
}

# Main execution logic
try {
    if ($Backend) {
        Start-BackendService
    }
    elseif ($Frontend) {
        Start-FrontendService
    }
    else {
        Start-AllServices
    }
}
catch {
    Write-Error "Startup failed: $($_.Exception.Message)"
    exit 1
}

Write-Host "VITA services startup completed" -ForegroundColor Green 