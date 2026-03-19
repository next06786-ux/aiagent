"""
启动本地 Qwen3.5-0.8B 模型服务器
"""
import subprocess
import sys
import os

def start_local_model_server():
    """启动本地模型服务器"""
    print("="*70)
    print("🚀 启动本地 Qwen3.5-0.8B 模型服务器")
    print("="*70)
    print()
    print("模型信息:")
    print("  - 模型: Qwen3.5-0.8B")
    print("  - 端口: 8000")
    print("  - API: http://localhost:8000/v1/chat/completions")
    print("  - 格式: OpenAI 兼容")
    print()
    print("优化特性:")
    print("  ✓ Float16 精度")
    print("  ✓ KV Cache 加速")
    print("  ✓ 自动混合精度")
    print()
    print("正在启动服务器...")
    print("="*70)
    print()
    
    # 启动优化版服务器
    try:
        subprocess.run([
            sys.executable,
            "backend/llm/local_qwen_server_optimized.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n请确保:")
        print("  1. 已安装 transformers: pip install transformers")
        print("  2. 已安装 torch: pip install torch")
        print("  3. 模型已下载到本地")

if __name__ == "__main__":
    start_local_model_server()
