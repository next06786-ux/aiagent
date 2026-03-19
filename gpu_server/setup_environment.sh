#!/bin/bash
# AutoDL GPU服务器环境配置脚本
# 适用于 PyTorch 2.1 + CUDA 12.1 镜像

echo "=========================================="
echo "🚀 LoRA训练环境配置"
echo "=========================================="

# 1. 升级pip
pip install --upgrade pip

# 2. 安装核心依赖
echo "📦 安装核心依赖..."
pip install transformers>=4.40.0
pip install peft>=0.10.0
pip install accelerate>=0.28.0
pip install bitsandbytes>=0.43.0
pip install datasets>=2.18.0
pip install sentencepiece
pip install tiktoken

# 3. 安装API服务依赖
echo "📦 安装API服务依赖..."
pip install fastapi>=0.110.0
pip install uvicorn>=0.29.0
pip install python-multipart
pip install aiofiles

# 4. 安装数据库依赖（用于同步用户数据）
pip install aiosqlite
pip install httpx

# 5. 验证安装
echo ""
echo "=========================================="
echo "✅ 验证安装"
echo "=========================================="

python3 << 'EOF'
import torch
print(f"PyTorch版本: {torch.__version__}")
print(f"CUDA可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU设备: {torch.cuda.get_device_name(0)}")
    print(f"显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

import transformers
print(f"Transformers版本: {transformers.__version__}")

import peft
print(f"PEFT版本: {peft.__version__}")

print("\n✅ 环境配置完成!")
EOF

echo ""
echo "=========================================="
echo "📋 下一步操作"
echo "=========================================="
echo "1. 上传项目代码到 /root/autodl-tmp/"
echo "2. 运行: python gpu_server/lora_training_server.py"
echo "3. 服务将在 http://0.0.0.0:8000 启动"
echo "=========================================="
