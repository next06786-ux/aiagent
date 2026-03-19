"""
LifeSwarm 后端服务器启动脚本
用于启动FastAPI服务器
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

def main():
    # 切换到项目根目录（backend 的父目录）
    # 这样所有相对路径都相对于项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    print(f"📁 工作目录: {os.getcwd()}")
    print()
    
    # 加载环境变量
    load_dotenv()
    
    print("=" * 60)
    print("  LifeSwarm Backend Server")
    print("=" * 60)
    print()
    
    # 检查环境变量
    llm_provider = os.getenv("LLM_PROVIDER")
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    print("📋 环境配置:")
    print(f"   LLM_PROVIDER: {llm_provider or '未设置'}")
    print(f"   DASHSCOPE_API_KEY: {'已设置 ✅' if api_key else '未设置 ❌'}")
    print()
    
    if not api_key:
        print("⚠️  警告: DASHSCOPE_API_KEY 未设置")
        print("   AI对话功能将无法使用")
        print("   请在 .env 文件中配置")
        print()
    
    # 检查是否在正确的目录
    if not os.path.exists("backend/main.py"):
        print("❌ 错误: 未找到 backend/main.py")
        print("   请确保在项目根目录运行")
        sys.exit(1)
    
    print("🚀 启动服务器...")
    print(f"   服务器地址: http://localhost:8000")
    print(f"   API文档: http://localhost:8000/docs")
    print(f"   交互式文档: http://localhost:8000/redoc")
    print()
    print("💡 提示:")
    print("   - 按 Ctrl+C 停止服务器")
    print("   - 访问 /docs 查看API文档")
    print("   - 访问 /health 检查服务器状态")
    print()
    
    try:
        # 使用 uvicorn 启动服务器
        # 注意：现在在项目根目录，所以要指定 backend.main:app
        subprocess.run([
            "uvicorn",
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"  # 自动重载（开发模式）
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
