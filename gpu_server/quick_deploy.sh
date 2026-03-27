#!/bin/bash
# Transformers 推理服务快速部署脚本

set -e

echo "=========================================="
echo "  LifeSwarm Transformers 快速部署"
echo "=========================================="

# 检测 GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  未检测到 nvidia-smi，请确保已安装 NVIDIA 驱动"
fi

echo ""
echo "GPU 信息:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "  无法获取 GPU 信息"
echo ""

# 安装依赖
echo "正在安装依赖..."
pip install torch transformers accelerate bitsandbytes peft -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install fastapi uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "✓ 依赖已安装"

# 启动服务器
echo ""
echo "启动推理服务器..."
echo ""

python gpu_server/start_server.py \
  --port 8000 \
  --quantize
