@echo off
echo ========================================
echo 升级 Transformers 以支持 Qwen3.5
echo ========================================
echo.

cd /d "%~dp0"

echo 激活 pytorch 环境...
call conda activate pytorch

echo.
echo 正在升级 transformers 到最新版本...
echo.

pip install --upgrade transformers -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ========================================
echo 升级完成！
echo ========================================
echo.
echo 现在可以运行: start_qwen_server.bat
echo.

pause
