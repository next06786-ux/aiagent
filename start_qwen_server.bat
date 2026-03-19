@echo off
echo ========================================
echo 启动本地 Qwen 模型服务器
echo ========================================
echo.

cd /d "%~dp0"

echo 激活 pytorch 环境...
call conda activate pytorch

echo.
echo 启动模型服务器（端口 8000）...
echo 首次启动会自动下载模型，请耐心等待...
echo.

python backend/llm/local_qwen_server.py

pause
