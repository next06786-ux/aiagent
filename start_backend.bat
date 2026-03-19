@echo off
REM LifeSwarm 后端服务启动脚本 (Windows)
REM 快速启动后端服务

setlocal enabledelayedexpansion

echo.
echo ================================================================
echo   LifeSwarm Backend Service - Quick Start
echo ================================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM 检查依赖
echo Checking dependencies...
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] Missing dependencies. Installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [OK] Dependencies installed
echo.

REM 检查 .env 文件
if not exist ".env" (
    echo [WARNING] .env file not found
    echo Creating .env from template...
    if exist ".env.example" (
        copy .env.example .env
        echo [OK] .env created. Please edit it with your configuration.
    )
)

echo.
echo Starting backend service...
echo   URL: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Interactive Docs: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

REM Change to backend directory
if not exist "backend" (
    echo Error: backend directory not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

pause

