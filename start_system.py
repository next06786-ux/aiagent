"""
LifeSim AI 系统启动脚本
单机部署模式：启动 FastAPI 后端和 LoRA 训练调度器
决策模拟推理直接使用本地 Qwen3.5-9B + 用户专属 LoRA
"""
import os
import sys
import time
import subprocess
import signal
from multiprocessing import Process
from dotenv import load_dotenv
import requests

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 加载环境变量
load_dotenv()
load_dotenv('backend/.env')


def wait_for_http_ready(url: str, name: str, timeout: int = 120, interval: int = 2):
    """等待 HTTP 服务就绪，超时则抛错"""
    print(f"⏳ 等待 {name} 就绪: {url}")
    start = time.time()
    last_error = None
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                print(f"✅ {name} 已就绪")
                return
            last_error = f"status={resp.status_code}"
        except Exception as e:
            last_error = str(e)
        time.sleep(interval)
    raise RuntimeError(f"{name} 在 {timeout} 秒内未就绪: {last_error}")


def start_backend_server():
    """启动后端FastAPI服务器"""
    print("\n" + "="*70)
    print("🚀 启动后端服务器...")
    print("="*70 + "\n")
    
    # 确保在项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 设置PYTHONPATH环境变量，包含项目根目录
    sys.path.insert(0, project_root)
    
    # 使用 uvicorn 启动
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=6006,
        reload=False,
        log_level="info"
    )


def start_lora_scheduler():
    """启动LoRA训练调度器"""
    print("\n" + "="*70)
    print("🤖 启动LoRA训练调度器...")
    print("="*70 + "\n")
    
    time.sleep(3)  # 等待后端服务器启动
    
    from backend.lora.lora_scheduler import get_scheduler
    
    scheduler = get_scheduler()
    scheduler.start()
    
    # 保持运行
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n收到停止信号")
        scheduler.stop()


def main():
    """主函数"""
    print("\n" + "="*70)
    print("  LifeSim AI - 智能生活决策系统")
    print("="*70)
    print("\n系统组件:")
    print("  ✓ GPU 主后端部署")
    print("  ✓ 本地 Qwen3.5-9B 基座")
    print("  ✓ 用户专属 LoRA 推理")
    print("  ✓ FastAPI 后端")
    print("  ✓ 心理测评系统")
    print("  ✓ LoRA个性化模型")
    print("  ✓ 平行宇宙模拟器")
    print("  ✓ 风险评估引擎")
    print("  ✓ 决策反馈循环")
    print("  ✓ 动态画像更新")
    
    print("\n" + "="*70 + "\n")
    
    # 创建进程列表
    processes = []
    
    try:
        # 1. 启动后端服务器
        backend_process = Process(target=start_backend_server, name="Backend")
        backend_process.start()
        processes.append(('后端服务器', backend_process))
        wait_for_http_ready(os.environ.get("API_BASE_URL", "http://127.0.0.1:6006") + "/health", "FastAPI", timeout=60)
        
        # 2. 启动调度器
        scheduler_process = Process(target=start_lora_scheduler, name="Scheduler")
        scheduler_process.start()
        processes.append(('调度器', scheduler_process))
        
        print("\n✅ 系统启动成功!")
        print("\n访问地址:")
        print("  - FastAPI:      http://0.0.0.0:6006/docs")
        print("  - 健康检查文件: ./data/health_check.json")
        print("  - FastAPI健康:  http://127.0.0.1:6006/health")

        # 4. 启动后自动跑一次健康检查
        print("\n🔍 执行启动后健康检查...")
        from backend.utils.health_checker import HealthChecker
        checker = HealthChecker(
            api_base_url=os.environ.get("API_BASE_URL", "http://127.0.0.1:6006"),
            lora_dir=os.environ.get("LORA_MODELS_DIR", "./models/lora"),
        )
        checker.check_all()

        print("\n按 Ctrl+C 停止系统\n")
        
        # 等待进程
        for _, process in processes:
            process.join()
        
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("🛑 正在停止系统...")
        print("="*70 + "\n")
        
        # 终止所有进程
        for name, process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                print(f"✅ {name}已停止")
        
        print("\n" + "="*70)
        print("  系统已安全关闭")
        print("="*70 + "\n")
    
    except Exception as e:
        print(f"\n❌ 系统启动失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 清理所有进程
        for _, process in processes:
            if process.is_alive():
                process.terminate()


if __name__ == "__main__":
    main()
