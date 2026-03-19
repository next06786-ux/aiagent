#!/usr/bin/env python3
"""
LifeSwarm 快速启动脚本（简化版）
仅启动后端服务，不检查外部依赖
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def main():
    print("\n" + "=" * 70)
    print("  LifeSwarm 后端服务 - 快速启动")
    print("=" * 70 + "\n")
    
    # 检查API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if api_key:
        print(f"✅ DASHSCOPE_API_KEY: {api_key[:10]}***")
    else:
        print("⚠️  DASHSCOPE_API_KEY 未设置")
        print("   AI对话功能将无法使用")
    
    print("\n🚀 启动后端服务...")
    print("   地址: http://localhost:8000")
    print("   API文档: http://localhost:8000/docs")
    print("   健康检查: http://localhost:8000/health")
    print("\n💡 按 Ctrl+C 停止服务器\n")
    
    backend_dir = Path(__file__).parent / 'backend'
    
    try:
        os.chdir(backend_dir)
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload',
            '--log-level', 'info'
        ])
    except KeyboardInterrupt:
        print("\n\n✅ 服务器已停止")
    except FileNotFoundError:
        print("\n❌ 错误: 未找到 uvicorn")
        print("   请安装: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

