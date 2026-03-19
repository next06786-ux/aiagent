@echo off
echo ========================================
echo 安装 Transformers 开发版（支持最新模型）
echo ========================================
echo.

cd /d "%~dp0"

echo 激活 pytorch 环境...
call conda activate pytorch

echo.
echo 正在从 GitHub 安装最新开发版...
echo 这可能需要几分钟...
echo.

pip install git+https://github.com/huggingface/transformers.git -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 现在可以运行: start_qwen_server.bat
echo.

pause
