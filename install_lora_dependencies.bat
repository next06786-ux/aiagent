@echo off
echo ========================================
echo 安装 LoRA 训练所需依赖
echo ========================================
echo.

cd /d "%~dp0"

echo 激活 pytorch 环境...
call conda activate pytorch

echo.
echo 正在安装依赖包...
echo.

echo [1/6] 安装 transformers...
pip install transformers -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [2/6] 安装 peft (LoRA)...
pip install peft -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [3/6] 安装 accelerate...
pip install accelerate -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [4/6] 安装 bitsandbytes...
pip install bitsandbytes -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [5/6] 安装 datasets...
pip install datasets -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [6/6] 安装 sentencepiece...
pip install sentencepiece protobuf -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 运行环境检查: python check_environment.py
echo.

pause
