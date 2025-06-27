@echo off
chcp 65001 > nul
setlocal

:: VITA Frontend Startup Script

echo ========================================
echo VITA Frontend Development Server
echo ========================================
echo.

:: Get script directory and navigate to project root
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%\.."

echo Project Root: %CD%
echo.

:: Check if frontend directory exists
if not exist "frontend" (
    echo Error: frontend directory not found
    pause
    exit /b 1
)

:: Navigate to frontend directory
cd frontend

:: Check if package.json exists
if not exist "package.json" (
    echo Error: package.json not found in frontend directory
    pause
    exit /b 1
)

:: Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Starting frontend development server...
echo.

:: Start frontend development server
npm run dev

:: If we reach here, the server has stopped
echo.
echo Frontend development server stopped
pause 