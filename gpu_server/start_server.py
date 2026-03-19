#!/usr/bin/env python3
"""
GPU服务器统一启动脚本
启动完整的LifeSwarm后端服务
"""
import os
import sys
import argparse
import signal
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 设置环境变量
os.environ.setdefault("DATA_DIR", "/root/autodl-tmp")


def setup_environment():
    """设置环境"""
    from gpu_server.gpu_config import get_config
    
    config = get_config()
    
    # 设置CUDA
    if config.use_gpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(config.gpu_device)
    
    # 设置HuggingFace缓存目录
    os.environ["HF_HOME"] = os.path.join(config.data_dir, "huggingface")
    os.environ["TRANSFORMERS_CACHE"] = os.path.join(config.data_dir, "huggingface")
    
    # 创建必要目录
    os.makedirs(config.logs_dir, exist_ok=True)
    os.makedirs(config.database_dir, exist_ok=True)
    
    return config


def print_banner(config):
    """打印启动横幅"""
    gpu_info = config.get_gpu_info()
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ██╗     ██╗███████╗███████╗███████╗██╗    ██╗ █████╗ ██████╗ ███╗   ███╗    ║
║     ██║     ██║██╔════╝██╔════╝██╔════╝██║    ██║██╔══██╗██╔══██╗████╗ ████║    ║
║     ██║     ██║█████╗  █████╗  ███████╗██║ █╗ ██║███████║██████╔╝██╔████╔██║    ║
║     ██║     ██║██╔══╝  ██╔══╝  ╚════██║██║███╗██║██╔══██║██╔══██╗██║╚██╔╝██║    ║
║     ███████╗██║██║     ███████╗███████║╚███╔███╔╝██║  ██║██║  ██║██║ ╚═╝ ██║    ║
║     ╚══════╝╚═╝╚═╝     ╚══════╝╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝    ║
║                                                                  ║
║                    GPU Server Edition                            ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"📁 数据目录: {config.data_dir}")
    print(f"🌐 服务地址: http://{config.host}:{config.port}")
    
    if gpu_info.get("available"):
        print(f"🎮 GPU: {gpu_info['device_name']}")
        print(f"💾 显存: {gpu_info['memory_total_gb']:.1f} GB")
    else:
        print("⚠️  GPU不可用，使用CPU模式")
    
    print(f"🤖 默认模型: {config.default_model}")
    print(f"🔧 LoRA训练: {'启用' if config.lora_enabled else '禁用'}")
    print(f"📚 RAG系统: {'启用' if config.rag_enabled else '禁用'}")
    print()


def start_server(config, reload: bool = False):
    """启动服务器"""
    import uvicorn
    
    print("🚀 启动服务...")
    print(f"📝 API文档: http://{config.host}:{config.port}/docs")
    print()
    
    uvicorn.run(
        "backend.main:app",
        host=config.host,
        port=config.port,
        reload=reload,
        workers=config.workers,
        log_level="info",
        access_log=True
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LifeSwarm GPU Server")
    parser.add_argument("--host", default=None, help="服务地址")
    parser.add_argument("--port", type=int, default=None, help="服务端口")
    parser.add_argument("--reload", action="store_true", help="开发模式（自动重载）")
    parser.add_argument("--no-gpu", action="store_true", help="禁用GPU")
    parser.add_argument("--model", default=None, help="指定模型")
    parser.add_argument("--config", action="store_true", help="仅显示配置")
    
    args = parser.parse_args()
    
    # 设置环境
    if args.no_gpu:
        os.environ["USE_GPU"] = "false"
    if args.model:
        os.environ["DEFAULT_MODEL"] = args.model
    
    config = setup_environment()
    
    # 覆盖命令行参数
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    
    # 打印横幅
    print_banner(config)
    
    # 仅显示配置
    if args.config:
        print("📋 完整配置:")
        for key, value in config.to_dict().items():
            print(f"  {key}: {value}")
        return
    
    # 信号处理
    def signal_handler(sig, frame):
        print("\n🛑 收到停止信号，正在关闭...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动服务
    try:
        start_server(config, reload=args.reload)
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
