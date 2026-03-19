#!/bin/bash
# vLLM Multi-LoRA 一键部署脚本
# 在 AutoDL GPU 服务器上运行

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         vLLM Multi-LoRA 一键部署                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# ============== 配置 ==============
DATA_DIR="/root/autodl-tmp"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$DATA_DIR/logs"
PID_FILE="$DATA_DIR/vllm.pid"

# 默认模型
DEFAULT_MODEL="Qwen/Qwen2.5-7B-Instruct"
MODEL=${1:-$DEFAULT_MODEL}

# ============== 函数 ==============

setup_dirs() {
    echo "📂 创建目录..."
    mkdir -p $DATA_DIR/models/base
    mkdir -p $DATA_DIR/models/lora
    mkdir -p $DATA_DIR/data
    mkdir -p $LOG_DIR
    mkdir -p $DATA_DIR/huggingface
    
    export HF_HOME=$DATA_DIR/huggingface
    export TRANSFORMERS_CACHE=$DATA_DIR/huggingface
}

check_gpu() {
    echo "🎮 检查 GPU..."
    if ! command -v nvidia-smi &> /dev/null; then
        echo "❌ nvidia-smi 未找到"
        exit 1
    fi
    
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
    echo ""
}

install_deps() {
    echo "📦 安装依赖..."
    
    pip install --upgrade pip -q
    
    # vLLM
    pip install vllm -q 2>/dev/null || {
        echo "   安装 vLLM（可能需要几分钟）..."
        pip install vllm
    }
    
    # 其他依赖
    pip install fastapi uvicorn httpx pydantic -q
    pip install transformers accelerate peft -q
    
    echo "✅ 依赖安装完成"
}

verify_install() {
    echo "🔍 验证安装..."
    
    python3 << 'EOF'
import sys
try:
    import vllm
    print(f"  ✓ vLLM {vllm.__version__}")
except ImportError as e:
    print(f"  ✗ vLLM: {e}")
    sys.exit(1)

try:
    import torch
    if torch.cuda.is_available():
        print(f"  ✓ CUDA 可用: {torch.cuda.get_device_name(0)}")
    else:
        print("  ✗ CUDA 不可用")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ PyTorch: {e}")
    sys.exit(1)

print("  ✓ 环境验证通过")
EOF
}

stop_service() {
    echo "🛑 停止现有服务..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            sleep 2
        fi
        rm -f $PID_FILE
    fi
    
    # 确保没有残留进程
    pkill -f "vllm_service_api" 2>/dev/null || true
    pkill -f "vllm_multi_lora_server" 2>/dev/null || true
    
    sleep 1
}

start_service() {
    echo "🚀 启动 vLLM 服务..."
    echo "   模型: $MODEL"
    echo "   日志: $LOG_DIR/vllm.log"
    
    cd $PROJECT_DIR
    
    # 设置环境变量
    export DATA_DIR=$DATA_DIR
    export BASE_MODEL=$MODEL
    export HF_HOME=$DATA_DIR/huggingface
    
    # 后台启动
    nohup python gpu_server/vllm_service_api.py \
        --host 0.0.0.0 \
        --port 8000 \
        > $LOG_DIR/vllm.log 2>&1 &
    
    echo $! > $PID_FILE
    
    echo "   PID: $(cat $PID_FILE)"
    
    # 等待启动
    echo "   等待服务启动..."
    sleep 10
    
    # 检查是否启动成功
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ 服务启动成功!"
            echo ""
            echo "📋 API 端点:"
            echo "   - 健康检查: GET  http://localhost:8000/health"
            echo "   - 聊天补全: POST http://localhost:8000/v1/chat/completions"
            echo "   - LoRA列表: GET  http://localhost:8000/v1/loras"
            echo "   - 训练LoRA: POST http://localhost:8000/v1/train"
            echo ""
            return 0
        fi
        sleep 2
    done
    
    echo "❌ 服务启动失败，查看日志:"
    tail -50 $LOG_DIR/vllm.log
    return 1
}

show_status() {
    echo "📊 服务状态:"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            echo "   状态: 运行中 (PID: $PID)"
            
            # 尝试获取健康状态
            HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo '{"status":"unknown"}')
            echo "   健康: $HEALTH"
        else
            echo "   状态: 已停止"
        fi
    else
        echo "   状态: 未启动"
    fi
}

show_logs() {
    echo "📜 最近日志:"
    tail -30 $LOG_DIR/vllm.log 2>/dev/null || echo "   无日志"
}

# ============== 主逻辑 ==============

case "${2:-deploy}" in
    deploy|start)
        setup_dirs
        check_gpu
        install_deps
        verify_install
        stop_service
        start_service
        ;;
    stop)
        stop_service
        echo "✅ 服务已停止"
        ;;
    restart)
        stop_service
        start_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "用法: $0 [模型名] [命令]"
        echo ""
        echo "命令:"
        echo "  deploy  - 完整部署（默认）"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看状态"
        echo "  logs    - 查看日志"
        echo ""
        echo "示例:"
        echo "  $0                                    # 使用默认模型部署"
        echo "  $0 Qwen/Qwen2.5-7B-Instruct deploy   # 指定模型部署"
        echo "  $0 _ stop                            # 停止服务"
        echo "  $0 _ logs                            # 查看日志"
        ;;
esac
