#!/usr/bin/env python3
"""
GPU服务器统一启动脚本
启动 SGLang 推理服务
"""
import os
import sys
import argparse
import subprocess
import signal
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def setup_environment():
    """设置环境变量"""
    from gpu_server.gpu_config import ENV_CONFIG, PATHS, ensure_dirs
    
    # 设置环境变量
    for key, value in ENV_CONFIG.items():
        os.environ[key] = value
    
    # 创建必要目录
    ensure_dirs()
    
    print("✓ 环境变量已设置:")
    for key, value in ENV_CONFIG.items():
        print(f"  {key}={value}")


def print_banner():
    """打印启动横幅"""
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
║                    SGLang GPU Server                             ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def start_sglang(model: str = None, port: int = 8000, enable_lora: bool = False):
    """启动 SGLang 服务器"""
    from gpu_server.gpu_config import get_model_config, SGLANG_CONFIG, PATHS, DATA_DIR
    
    config = get_model_config(model)
    
    print(f"🚀 启动 SGLang 服务器...")
    print(f"  模型: {config['hf_name']}")
    print(f"  端口: {port}")
    print(f"  显存需求: {config['vram_gb']} GB")
    print()
    
    cmd = [
        "python", "-m", "sglang.launch_server",
        "--model-path", config['hf_name'],
        "--port", str(port),
        "--tensor-parallel-size", str(SGLANG_CONFIG['tensor_parallel_size']),
        "--mem-fraction-static", str(SGLANG_CONFIG['mem_fraction_static']),
        "--context-length", str(SGLANG_CONFIG['context_length']),
        "--reasoning-parser", SGLANG_CONFIG['reasoning_parser'],
        "--download-dir", PATHS['huggingface'],
    ]
    
    # 添加 LoRA 支持
    if enable_lora:
        lora_dir = PATHS.get('models_lora', f"{DATA_DIR}/models/lora")
        cmd.extend([
            "--enable-lora", "true",
            "--max-lora-rank", str(config['lora_r']),
            "--lora-paths", lora_dir,
        ])
        print(f"  LoRA: 已启用 (模型目录: {lora_dir})")
    
    print(f"\n执行命令:\n{' '.join(cmd)}\n")
    
    # 启动进程
    process = subprocess.Popen(cmd)
    
    return process


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LifeSwarm SGLang Server")
    parser.add_argument("--model", default=None, help="模型名称 (qwen3.5-9b, qwen3.5-0.8b)")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    parser.add_argument("--enable-lora", action="store_true", default=True, help="启用 LoRA 支持（默认开启）")
    parser.add_argument("--no-lora", action="store_true", help="禁用 LoRA 支持")
    parser.add_argument("--show-config", action="store_true", help="仅显示配置")
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    # 设置环境
    setup_environment()
    
    # 仅显示配置
    if args.show_config:
        from gpu_server.gpu_config import get_model_config, get_sglang_launch_cmd
        config = get_model_config(args.model)
        print("\n📋 模型配置:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        print("\n📋 启动命令:")
        print(get_sglang_launch_cmd(args.model))
        return
    
    # 信号处理
    process = None
    
    def signal_handler(sig, frame):
        print("\n🛑 收到停止信号，正在关闭...")
        if process:
            process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动服务
    try:
        enable_lora = not args.no_lora
        process = start_sglang(
            model=args.model,
            port=args.port,
            enable_lora=enable_lora
        )
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
        if process:
            process.terminate()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
