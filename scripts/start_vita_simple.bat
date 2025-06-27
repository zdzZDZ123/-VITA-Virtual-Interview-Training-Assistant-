@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: VITA Virtual Interview Assistant - Simple Startup Script
:: This script provides a simple way to start VITA services

echo ========================================
echo VITA Virtual Interview Assistant
echo ========================================
echo.

:: Set API keys if provided as arguments
if not "%1"=="" (
    set QWEN_API_KEY=%1
    echo Qwen API Key configured
)

if not "%2"=="" (
    set DOUBAO_API_KEY=%2
    echo Doubao API Key configured
)

:: Get script directory and navigate to project root
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%\.."

echo Project Root: %CD%
echo.

:: Check if backend directory exists
if not exist "backend" (
    echo Error: backend directory not found
    pause
    exit /b 1
)

:: Check if main.py exists
if not exist "backend\main.py" (
    echo Error: backend\main.py not found
    pause
    exit /b 1
)

echo Starting VITA Backend Service...
echo.

:: Navigate to backend directory
cd backend

:: Start backend service
echo Starting uvicorn server on port 8000...
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

:: If we reach here, the server has stopped
echo.
echo Backend service stopped
pause 