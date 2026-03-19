#!/bin/bash
# ============================================================
# GPU服务器完整后端部署脚本
# 将整个LifeSwarm后端部署到AutoDL GPU服务器
# ============================================================

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     LifeSwarm GPU服务器 - 完整后端部署                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ==================== 配置 ====================
# AutoDL数据盘（关机后保留）
DATA_DIR="/root/autodl-tmp"
PROJECT_NAME="lifeswarm"
PROJECT_DIR="$DATA_DIR/$PROJECT_NAME"

# 服务配置
BACKEND_PORT=8000
GRADIO_PORT=7860  # AutoDL默认开放的端口

echo "📁 数据目录: $DATA_DIR"
echo "📁 项目目录: $PROJECT_DIR"
echo ""

# ==================== 1. 创建目录结构 ====================
echo "📂 [1/7] 创建目录结构..."

mkdir -p $DATA_DIR/models/base
mkdir -p $DATA_DIR/models/lora
mkdir -p $DATA_DIR/data/database
mkdir -p $DATA_DIR/data/rag
mkdir -p $DATA_DIR/data/knowledge_graph
mkdir -p $DATA_DIR/data/decisions
mkdir -p $DATA_DIR/data/decision_sessions
mkdir -p $DATA_DIR/data/simulations
mkdir -p $DATA_DIR/logs
mkdir -p $DATA_DIR/backups

echo "✅ 目录结构创建完成"

# ==================== 2. 创建软链接 ====================
echo ""
echo "🔗 [2/7] 创建软链接..."

# 如果项目目录存在，创建软链接
if [ -d "$PROJECT_DIR" ]; then
    # 链接数据目录到项目
    ln -sf $DATA_DIR/models $PROJECT_DIR/models 2>/dev/null || true
    ln -sf $DATA_DIR/data $PROJECT_DIR/backend/data 2>/dev/null || true
    ln -sf $DATA_DIR/logs $PROJECT_DIR/logs 2>/dev/null || true
    echo "✅ 软链接创建完成"
else
    echo "⚠️ 项目目录不存在，请先上传项目代码到 $PROJECT_DIR"
fi

# ==================== 3. 安装Python依赖 ====================
echo ""
echo "📦 [3/7] 安装Python依赖..."

# 升级pip
pip install --upgrade pip -q

# 核心ML依赖
echo "  - 安装ML依赖..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -q 2>/dev/null || true
pip install transformers>=4.40.0 -q
pip install peft>=0.10.0 -q
pip install accelerate>=0.28.0 -q
pip install bitsandbytes>=0.43.0 -q
pip install datasets>=2.18.0 -q
pip install sentencepiece tiktoken -q

# 后端依赖
echo "  - 安装后端依赖..."
pip install fastapi>=0.110.0 -q
pip install "uvicorn[standard]>=0.29.0" -q
pip install python-multipart aiofiles httpx -q
pip install sqlalchemy aiosqlite -q
pip install python-dotenv -q

# 数据处理
echo "  - 安装数据处理依赖..."
pip install numpy pandas scikit-learn -q
pip install faiss-cpu sentence-transformers -q

# 其他依赖
echo "  - 安装其他依赖..."
pip install networkx matplotlib pillow -q
pip install websockets python-jose passlib bcrypt -q

echo "✅ Python依赖安装完成"

# ==================== 4. 创建环境配置文件 ====================
echo ""
echo "⚙️ [4/7] 创建环境配置..."

cat > $DATA_DIR/.env.gpu << 'EOF'
# ============================================================
# GPU服务器环境配置
# ============================================================

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# 数据目录
DATA_DIR=/root/autodl-tmp
MODELS_DIR=/root/autodl-tmp/models
LORA_DIR=/root/autodl-tmp/models/lora
DATABASE_DIR=/root/autodl-tmp/data/database

# LLM配置 - 使用本地模型
LLM_PROVIDER=local
LOCAL_MODEL_PATH=/root/autodl-tmp/models/base/Qwen2.5-7B-Instruct
# 或使用API
# LLM_PROVIDER=dashscope
# DASHSCOPE_API_KEY=your-api-key

# GPU配置
CUDA_VISIBLE_DEVICES=0
USE_GPU=true
USE_4BIT=false  # 32GB显存可以不用量化

# LoRA配置
LORA_ENABLED=true
LORA_AUTO_TRAIN=true
LORA_MIN_CONVERSATIONS=50

# RAG配置
RAG_ENABLED=true
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5

# 安全配置
API_KEY=your-secure-api-key-change-me
JWT_SECRET=your-jwt-secret-change-me

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/root/autodl-tmp/logs/backend.log
EOF

echo "✅ 环境配置创建完成: $DATA_DIR/.env.gpu"

# ==================== 5. 创建启动脚本 ====================
echo ""
echo "🚀 [5/7] 创建启动脚本..."

cat > $DATA_DIR/start_backend.sh << 'EOF'
#!/bin/bash
# GPU服务器后端启动脚本

PROJECT_DIR="/root/autodl-tmp/lifeswarm"
LOG_FILE="/root/autodl-tmp/logs/backend.log"

# 加载环境变量
export $(cat /root/autodl-tmp/.env.gpu | grep -v '^#' | xargs)

cd $PROJECT_DIR

echo "🚀 启动LifeSwarm后端服务..."
echo "📝 日志文件: $LOG_FILE"

# 启动服务
python -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info \
    2>&1 | tee -a $LOG_FILE
EOF

chmod +x $DATA_DIR/start_backend.sh

# 后台启动脚本
cat > $DATA_DIR/start_backend_daemon.sh << 'EOF'
#!/bin/bash
# GPU服务器后端后台启动脚本

PROJECT_DIR="/root/autodl-tmp/lifeswarm"
LOG_FILE="/root/autodl-tmp/logs/backend.log"
PID_FILE="/root/autodl-tmp/backend.pid"

# 加载环境变量
export $(cat /root/autodl-tmp/.env.gpu | grep -v '^#' | xargs)

cd $PROJECT_DIR

# 检查是否已运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat $PID_FILE)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️ 服务已在运行 (PID: $OLD_PID)"
        exit 1
    fi
fi

echo "🚀 后台启动LifeSwarm后端服务..."

nohup python -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info \
    > $LOG_FILE 2>&1 &

echo $! > $PID_FILE
echo "✅ 服务已启动 (PID: $!)"
echo "📝 日志文件: $LOG_FILE"
echo "🔗 访问地址: http://localhost:8000"
EOF

chmod +x $DATA_DIR/start_backend_daemon.sh

# 停止脚本
cat > $DATA_DIR/stop_backend.sh << 'EOF'
#!/bin/bash
# 停止后端服务

PID_FILE="/root/autodl-tmp/backend.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 停止服务 (PID: $PID)..."
        kill $PID
        rm $PID_FILE
        echo "✅ 服务已停止"
    else
        echo "⚠️ 服务未运行"
        rm $PID_FILE
    fi
else
    echo "⚠️ PID文件不存在"
    # 尝试通过进程名停止
    pkill -f "uvicorn backend.main:app" && echo "✅ 服务已停止" || echo "⚠️ 未找到运行中的服务"
fi
EOF

chmod +x $DATA_DIR/stop_backend.sh

echo "✅ 启动脚本创建完成"

# ==================== 6. 验证安装 ====================
echo ""
echo "🔍 [6/7] 验证安装..."

python3 << 'PYEOF'
import sys

def check(name, package=None):
    try:
        __import__(package or name)
        print(f"  ✓ {name}")
        return True
    except ImportError:
        print(f"  ✗ {name}")
        return False

print("核心依赖:")
check("PyTorch", "torch")
check("Transformers", "transformers")
check("PEFT", "peft")
check("BitsAndBytes", "bitsandbytes")

print("\n后端依赖:")
check("FastAPI", "fastapi")
check("Uvicorn", "uvicorn")
check("SQLAlchemy", "sqlalchemy")

print("\n数据处理:")
check("FAISS", "faiss")
check("Sentence-Transformers", "sentence_transformers")
check("NumPy", "numpy")
check("Pandas", "pandas")

print("\nGPU状态:")
import torch
if torch.cuda.is_available():
    print(f"  ✓ CUDA可用")
    print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
    mem_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"  ✓ 显存: {mem_gb:.1f} GB")
else:
    print("  ✗ CUDA不可用")
PYEOF

# ==================== 7. 显示使用说明 ====================
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    ✅ 部署完成                           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 使用说明:"
echo ""
echo "1. 上传项目代码:"
echo "   scp -r ./backend ./gpu_server root@your-server:$PROJECT_DIR/"
echo ""
echo "2. 修改环境配置:"
echo "   vim $DATA_DIR/.env.gpu"
echo ""
echo "3. 启动服务:"
echo "   前台运行: bash $DATA_DIR/start_backend.sh"
echo "   后台运行: bash $DATA_DIR/start_backend_daemon.sh"
echo ""
echo "4. 停止服务:"
echo "   bash $DATA_DIR/stop_backend.sh"
echo ""
echo "5. 查看日志:"
echo "   tail -f $DATA_DIR/logs/backend.log"
echo ""
echo "6. 访问服务:"
echo "   API文档: http://your-server:8000/docs"
echo "   健康检查: http://your-server:8000/health"
echo ""
echo "═══════════════════════════════════════════════════════════"
