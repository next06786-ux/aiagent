#!/bin/bash
# ============================================================
# GPU服务器一键部署脚本
# 适用于AutoDL等GPU云服务器
# 
# 使用方法:
#   curl -sSL https://your-repo/quick_deploy.sh | bash
#   或
#   bash gpu_server/quick_deploy.sh
# ============================================================

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║        LifeSwarm GPU服务器 - 一键部署                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 配置
DATA_DIR="/root/autodl-tmp"
PROJECT_DIR="$DATA_DIR/lifeswarm"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 检测是否在项目目录中运行
if [ -f "$SCRIPT_DIR/../backend/main.py" ]; then
    echo "📁 检测到项目目录: $SCRIPT_DIR/.."
    PROJECT_SOURCE="$SCRIPT_DIR/.."
else
    PROJECT_SOURCE=""
fi

# ==================== Step 1: 环境检查 ====================
echo "🔍 [1/6] 环境检查..."

# 检查GPU
python3 << 'EOF'
import sys
try:
    import torch
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"  ✓ GPU: {gpu_name} ({gpu_mem:.1f} GB)")
    else:
        print("  ⚠️ GPU不可用，将使用CPU模式")
except ImportError:
    print("  ⚠️ PyTorch未安装")
EOF

# 检查磁盘空间
DISK_FREE=$(df -BG /root/autodl-tmp 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
echo "  ✓ 可用磁盘空间: ${DISK_FREE}GB"

if [ "$DISK_FREE" -lt 50 ]; then
    echo "  ⚠️ 警告: 磁盘空间不足50GB，可能影响模型下载"
fi

# ==================== Step 2: 创建目录 ====================
echo ""
echo "📂 [2/6] 创建目录结构..."

mkdir -p $DATA_DIR/models/base
mkdir -p $DATA_DIR/models/lora
mkdir -p $DATA_DIR/data/database
mkdir -p $DATA_DIR/data/rag
mkdir -p $DATA_DIR/data/knowledge_graph
mkdir -p $DATA_DIR/logs
mkdir -p $DATA_DIR/backups

echo "  ✓ 目录创建完成"

# ==================== Step 3: 复制/更新项目代码 ====================
echo ""
echo "📦 [3/6] 部署项目代码..."

if [ -n "$PROJECT_SOURCE" ]; then
    # 从本地复制
    if [ -d "$PROJECT_DIR" ]; then
        echo "  更新现有项目..."
        rsync -av --exclude='__pycache__' --exclude='.git' --exclude='*.pyc' \
            "$PROJECT_SOURCE/" "$PROJECT_DIR/"
    else
        echo "  复制项目代码..."
        cp -r "$PROJECT_SOURCE" "$PROJECT_DIR"
    fi
    echo "  ✓ 项目代码已部署到 $PROJECT_DIR"
else
    if [ -d "$PROJECT_DIR" ]; then
        echo "  ✓ 项目目录已存在: $PROJECT_DIR"
    else
        echo "  ⚠️ 请手动上传项目代码到 $PROJECT_DIR"
        echo "     scp -r ./backend ./gpu_server root@server:$PROJECT_DIR/"
    fi
fi

# ==================== Step 4: 安装依赖 ====================
echo ""
echo "📦 [4/6] 安装Python依赖..."

pip install --upgrade pip -q

# 安装GPU依赖
if [ -f "$PROJECT_DIR/gpu_server/requirements_gpu.txt" ]; then
    pip install -r "$PROJECT_DIR/gpu_server/requirements_gpu.txt" -q
    echo "  ✓ 依赖安装完成"
else
    echo "  ⚠️ 未找到requirements_gpu.txt，安装基础依赖..."
    pip install torch transformers peft accelerate fastapi uvicorn -q
fi

# ==================== Step 5: 创建配置文件 ====================
echo ""
echo "⚙️ [5/6] 创建配置文件..."

# 生成随机密钥
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 检测推荐模型
RECOMMENDED_MODEL=$(python3 << 'EOF'
import torch
if torch.cuda.is_available():
    mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
    if mem >= 24: print("qwen2.5-14b")
    elif mem >= 16: print("qwen2.5-7b")
    else: print("qwen2.5-3b")
else:
    print("qwen2.5-3b")
EOF
)

# 创建环境配置
cat > $DATA_DIR/.env.gpu << EOF
# ============================================================
# GPU服务器环境配置 - 自动生成于 $(date)
# ============================================================

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# 数据目录
DATA_DIR=$DATA_DIR
MODELS_DIR=$DATA_DIR/models
LORA_DIR=$DATA_DIR/models/lora
DATABASE_DIR=$DATA_DIR/data/database

# LLM配置
LLM_PROVIDER=local
DEFAULT_MODEL=$RECOMMENDED_MODEL
LOCAL_MODEL_PATH=$DATA_DIR/models/base/$RECOMMENDED_MODEL

# GPU配置
CUDA_VISIBLE_DEVICES=0
USE_GPU=true
USE_4BIT=false

# LoRA配置
LORA_ENABLED=true
LORA_AUTO_TRAIN=true
LORA_MIN_CONVERSATIONS=50

# RAG配置
RAG_ENABLED=true
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5

# 安全配置（已自动生成，请妥善保管）
API_KEY=$API_KEY
JWT_SECRET=$JWT_SECRET

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=$DATA_DIR/logs/backend.log
EOF

echo "  ✓ 配置文件已创建: $DATA_DIR/.env.gpu"
echo "  ✓ 推荐模型: $RECOMMENDED_MODEL"

# 创建启动脚本
cat > $DATA_DIR/start.sh << 'EOF'
#!/bin/bash
cd /root/autodl-tmp/lifeswarm
export $(cat /root/autodl-tmp/.env.gpu | grep -v '^#' | xargs)
python gpu_server/start_server.py
EOF
chmod +x $DATA_DIR/start.sh

cat > $DATA_DIR/start_daemon.sh << 'EOF'
#!/bin/bash
cd /root/autodl-tmp/lifeswarm
export $(cat /root/autodl-tmp/.env.gpu | grep -v '^#' | xargs)
nohup python gpu_server/start_server.py > /root/autodl-tmp/logs/backend.log 2>&1 &
echo $! > /root/autodl-tmp/backend.pid
echo "✅ 服务已启动 (PID: $!)"
EOF
chmod +x $DATA_DIR/start_daemon.sh

cat > $DATA_DIR/stop.sh << 'EOF'
#!/bin/bash
if [ -f /root/autodl-tmp/backend.pid ]; then
    kill $(cat /root/autodl-tmp/backend.pid) 2>/dev/null
    rm /root/autodl-tmp/backend.pid
    echo "✅ 服务已停止"
else
    pkill -f "start_server.py" && echo "✅ 服务已停止" || echo "⚠️ 服务未运行"
fi
EOF
chmod +x $DATA_DIR/stop.sh

echo "  ✓ 启动脚本已创建"

# ==================== Step 6: 完成 ====================
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    ✅ 部署完成                           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 下一步操作:"
echo ""
echo "1. 下载模型（首次部署需要）:"
echo "   cd $PROJECT_DIR"
echo "   python gpu_server/download_models.py recommended"
echo ""
echo "2. 启动服务:"
echo "   bash $DATA_DIR/start.sh        # 前台运行"
echo "   bash $DATA_DIR/start_daemon.sh # 后台运行"
echo ""
echo "3. 停止服务:"
echo "   bash $DATA_DIR/stop.sh"
echo ""
echo "4. 查看日志:"
echo "   tail -f $DATA_DIR/logs/backend.log"
echo ""
echo "5. 访问服务:"
echo "   API文档: http://your-server:8000/docs"
echo "   健康检查: curl http://localhost:8000/health"
echo ""
echo "═══════════════════════════════════════════════════════════"
