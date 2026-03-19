#!/bin/bash
# vLLM Multi-LoRA 环境配置脚本
# 适用于 AutoDL 32GB vGPU 服务器

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           vLLM Multi-LoRA 环境配置                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# 配置
DATA_DIR="/root/autodl-tmp"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "📁 项目目录: $PROJECT_DIR"
echo "📁 数据目录: $DATA_DIR"

# 1. 创建目录结构
echo ""
echo "📂 创建目录结构..."
mkdir -p $DATA_DIR/models/base
mkdir -p $DATA_DIR/models/lora
mkdir -p $DATA_DIR/data
mkdir -p $DATA_DIR/logs
mkdir -p $DATA_DIR/huggingface

# 设置 HuggingFace 缓存目录
export HF_HOME=$DATA_DIR/huggingface
export TRANSFORMERS_CACHE=$DATA_DIR/huggingface

# 2. 检查 CUDA 版本
echo ""
echo "🔍 检查 CUDA 环境..."
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $5}' | cut -d',' -f1)
    echo "   CUDA 版本: $CUDA_VERSION"
else
    echo "   ⚠️ nvcc 未找到，尝试从 nvidia-smi 获取..."
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
    echo "   CUDA 版本: $CUDA_VERSION"
fi

# 3. 检查 GPU
echo ""
echo "🎮 检查 GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# 4. 升级 pip
echo ""
echo "📦 升级 pip..."
pip install --upgrade pip -q

# 5. 安装 vLLM
echo ""
echo "📦 安装 vLLM..."
echo "   这可能需要几分钟..."

# vLLM 需要特定的 CUDA 版本，自动检测安装
pip install vllm -q

# 6. 安装其他依赖
echo ""
echo "📦 安装其他依赖..."
pip install fastapi uvicorn[standard] -q
pip install pydantic httpx aiofiles -q
pip install transformers accelerate -q
pip install peft -q  # 用于 LoRA 训练

# 7. 验证安装
echo ""
echo "✅ 验证安装..."

python3 << 'EOF'
import sys

def check(name, package=None):
    try:
        mod = __import__(package or name)
        version = getattr(mod, '__version__', 'unknown')
        print(f"  ✓ {name}: {version}")
        return True
    except ImportError as e:
        print(f"  ✗ {name}: {e}")
        return False

print("核心依赖:")
check("vLLM", "vllm")
check("PyTorch", "torch")
check("Transformers", "transformers")
check("PEFT", "peft")

print("\n服务依赖:")
check("FastAPI", "fastapi")
check("Uvicorn", "uvicorn")

print("\nGPU 状态:")
import torch
if torch.cuda.is_available():
    print(f"  ✓ CUDA 可用")
    print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
    mem_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"  ✓ 显存: {mem_gb:.1f} GB")
    
    # 检查 vLLM 是否能正常导入
    try:
        from vllm import LLM
        print(f"  ✓ vLLM 引擎可用")
    except Exception as e:
        print(f"  ✗ vLLM 引擎错误: {e}")
else:
    print("  ✗ CUDA 不可用")
EOF

# 8. 下载模型（可选）
echo ""
echo "=========================================="
echo "📥 是否下载基座模型？"
echo "   推荐: Qwen/Qwen2.5-7B-Instruct (约 15GB)"
echo "=========================================="
read -p "下载模型? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📥 下载 Qwen2.5-7B-Instruct..."
    python3 << 'EOF'
from huggingface_hub import snapshot_download
import os

model_name = "Qwen/Qwen2.5-7B-Instruct"
cache_dir = os.environ.get("HF_HOME", "/root/autodl-tmp/huggingface")

print(f"下载模型: {model_name}")
print(f"缓存目录: {cache_dir}")

snapshot_download(
    repo_id=model_name,
    cache_dir=cache_dir,
    resume_download=True
)

print("✅ 模型下载完成!")
EOF
fi

# 9. 完成
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    ✅ 配置完成!                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 启动命令:"
echo ""
echo "   # 启动 vLLM Multi-LoRA 服务"
echo "   python gpu_server/vllm_multi_lora_server.py"
echo ""
echo "   # 或指定模型"
echo "   python gpu_server/vllm_multi_lora_server.py --model Qwen/Qwen2.5-7B-Instruct"
echo ""
echo "   # 后台运行"
echo "   nohup python gpu_server/vllm_multi_lora_server.py > logs/vllm.log 2>&1 &"
echo ""
echo "📋 API 端点:"
echo "   - 健康检查: GET  /health"
echo "   - 模型列表: GET  /v1/models"
echo "   - LoRA列表: GET  /v1/loras"
echo "   - 聊天补全: POST /v1/chat/completions"
echo "   - 文本补全: POST /v1/completions"
echo ""
