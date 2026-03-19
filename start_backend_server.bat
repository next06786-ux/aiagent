@echo off
echo ========================================
echo 启动 LifeSwarm AI 后端服务器
echo ========================================
echo.

echo 切换到 backend 目录...
cd /d "%~dp0backend"
echo 当前目录: %CD%
echo.

echo 激活 pytorch 环境并启动服务器...
call conda activate pytorch
if errorlevel 1 (
    echo 错误: 无法激活 pytorch 环境
    pause
    exit /b 1
)

echo.
echo 启动 FastAPI 服务器 (端口 8000)...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
