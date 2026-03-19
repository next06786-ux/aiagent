#!/bin/bash
# SGLang 快速部署脚本

set -e

echo "=========================================="
echo "  LifeSwarm SGLang 快速部署"
echo "=========================================="

# 设置环境变量
export HF_HOME=/root/autodl-tmp/huggingface
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0

echo "✓ 环境变量已设置"

# 创建目录
mkdir -p /root/autodl-tmp/huggingface
mkdir -p /root/autodl-tmp/models/lora
mkdir -p /root/autodl-tmp/logs

echo "✓ 目录已创建"

# 安装依赖
echo "正在安装 SGLang..."
pip install sglang[all] -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "✓ SGLang 已安装"

# 启动服务器
echo ""
echo "启动 SGLang 服务器..."
echo ""

python -m sglang.launch_server \
  --model-path Qwen/Qwen3.5-9B \
  --port 8000 \
  --tensor-parallel-size 1 \
  --mem-fraction-static 0.8 \
  --context-length 32768 \
  --reasoning-parser qwen3 \
  --download-dir /root/autodl-tmp/huggingface
