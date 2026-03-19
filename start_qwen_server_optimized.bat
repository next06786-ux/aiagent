@echo off
echo ========================================
echo 启动优化版 Qwen 模型服务器
echo ========================================
echo.

cd /d "%~dp0"

echo 激活 pytorch 环境...
call conda activate pytorch

echo.
echo 启动优化版模型服务器（端口 8000）...
echo 性能优化: float16 + KV cache + 优化采样
echo.

python backend/llm/local_qwen_server_optimized.py

pause
