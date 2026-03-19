#!/bin/bash
# AutoDL GPU服务器环境配置脚本
# 运行方式: bash gpu_server/setup_gpu_env.sh

set -e

echo "=========================================="
echo "🚀 LoRA决策系统 - GPU环境配置"
echo "=========================================="

# 获取项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="/root/autodl-tmp"

echo "📁 项目目录: $PROJECT_DIR"
echo "📁 数据目录: $DATA_DIR"

# 1. 创建必要的目录
echo ""
echo "📂 创建目录结构..."
mkdir -p $DATA_DIR/models/base
mkdir -p $DATA_DIR/models/lora
mkdir -p $DATA_DIR/data/database
mkdir -p $DATA_DIR/data/rag
mkdir -p $DATA_DIR/logs

# 2. 创建软链接（让项目代码能访问数据目录）
echo "🔗 创建软链接..."
ln -sf $DATA_DIR/models $PROJECT_DIR/models 2>/dev/null || true
ln -sf $DATA_DIR/data $PROJECT_DIR/data 2>/dev/null || true
ln -sf $DATA_DIR/logs $PROJECT_DIR/logs 2>/dev/null || true

# 3. 升级pip
echo ""
echo "📦 升级pip..."
pip install --upgrade pip -q

# 4. 安装PyTorch依赖（如果需要）
echo "📦 检查PyTorch..."
python3 -c "import torch; print(f'PyTorch {torch.__version__} 已安装')" 2>/dev/null || {
    echo "安装PyTorch..."
    pip install torch torchvision torchaudio -q
}

# 5. 安装核心ML依赖
echo "📦 安装ML依赖..."
pip install transformers>=4.40.0 -q
pip install peft>=0.10.0 -q
pip install accelerate>=0.28.0 -q
pip install bitsandbytes>=0.43.0 -q
pip install datasets>=2.18.0 -q
pip install sentencepiece tiktoken -q

# 6. 安装后端依赖
echo "📦 安装后端依赖..."
pip install fastapi>=0.110.0 -q
pip install uvicorn[standard]>=0.29.0 -q
pip install python-multipart aiofiles httpx -q
pip install sqlalchemy aiosqlite -q
pip install numpy pandas scikit-learn -q
pip install faiss-cpu sentence-transformers -q

# 7. 安装项目依赖（如果有requirements.txt）
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "📦 安装项目依赖..."
    pip install -r $PROJECT_DIR/requirements.txt -q
fi

# 8. 验证安装
echo ""
echo "=========================================="
echo "✅ 验证安装"
echo "=========================================="

python3 << 'EOF'
import sys

def check_import(name, package=None):
    try:
        __import__(package or name)
        print(f"  ✓ {name}")
        return True
    except ImportError:
        print(f"  ✗ {name} - 未安装")
        return False

print("核心依赖:")
check_import("PyTorch", "torch")
check_import("Transformers", "transformers")
check_import("PEFT", "peft")
check_import("BitsAndBytes", "bitsandbytes")

print("\n后端依赖:")
check_import("FastAPI", "fastapi")
check_import("Uvicorn", "uvicorn")
check_import("SQLAlchemy", "sqlalchemy")

print("\nGPU状态:")
import torch
if torch.cuda.is_available():
    print(f"  ✓ CUDA可用")
    print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
    print(f"  ✓ 显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    print("  ✗ CUDA不可用")

print("\n✅ 环境配置完成!")
EOF

echo ""
echo "=========================================="
echo "📋 下一步"
echo "=========================================="
echo "1. 启动服务: python gpu_server/start_server.py"
echo "2. 或后台运行: nohup python gpu_server/start_server.py > logs/server.log 2>&1 &"
echo "=========================================="
