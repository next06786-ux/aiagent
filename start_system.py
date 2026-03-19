"""
LifeSim AI 系统启动脚本
启动后端服务器和LoRA训练调度器
"""
import os
import sys
import time
import subprocess
import signal
from multiprocessing import Process
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 加载环境变量
load_dotenv()
load_dotenv('backend/.env.local_model')  # 加载本地模型配置


def start_local_model_server():
    """启动本地Qwen3.5-0.8B模型服务器"""
    print("\n" + "="*70)
    print("🤖 启动本地模型服务器 (Qwen3.5-0.8B)...")
    print("="*70 + "\n")
    
    # 确保在项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # 使用uvicorn启动本地模型服务器
    import uvicorn
    uvicorn.run(
        "backend.llm.local_qwen_server_optimized:app",
        host="0.0.0.0",
        port=8001,  # 使用8001端口，避免与主服务器冲突
        log_level="info"
    )


def start_backend_server():
    """启动后端FastAPI服务器"""
    print("\n" + "="*70)
    print("🚀 启动后端服务器...")
    print("="*70 + "\n")
    
    # 确保在项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 设置PYTHONPATH环境变量，包含项目根目录
    sys.path.insert(0, project_root)
    
    # 使用uvicorn启动（开发模式使用--reload）
    import uvicorn
    uvicorn.run(
        "backend.main:app",  # 使用完整的模块路径
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        reload_dirs=[os.path.join(project_root, "backend")]  # 只监控backend目录
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
    print("  ✓ 心理测评系统")
    print("  ✓ LoRA个性化模型")
    print("  ✓ 平行宇宙模拟器")
    print("  ✓ 风险评估引擎")
    print("  ✓ 决策反馈循环")
    print("  ✓ 动态画像更新")
    
    # 检查是否启用本地模型
    enable_local_model = os.getenv('ENABLE_LOCAL_MODEL', 'false').lower() == 'true'
    if enable_local_model:
        print("  ✓ 本地Qwen3.5-0.8B模型")
    
    print("\n" + "="*70 + "\n")
    
    # 创建进程列表
    processes = []
    
    try:
        # 先启动后端服务器（避免内存冲突）
        backend_process = Process(target=start_backend_server, name="Backend")
        backend_process.start()
        processes.append(('后端服务器', backend_process))
        time.sleep(3)  # 等待后端初始化
        
        # 如果启用本地模型，再启动本地模型服务器
        if enable_local_model:
            print("正在启动本地模型服务器...")
            local_model_process = Process(target=start_local_model_server, name="LocalModel")
            local_model_process.start()
            processes.append(('本地模型服务器', local_model_process))
            time.sleep(5)  # 等待模型加载
        
        # 启动调度器
        scheduler_process = Process(target=start_lora_scheduler, name="Scheduler")
        scheduler_process.start()
        processes.append(('调度器', scheduler_process))
        
        print("\n✅ 系统启动成功!")
        print("\n访问地址:")
        print("  - 主服务API: http://localhost:8000/docs")
        if enable_local_model:
            print("  - 本地模型API: http://localhost:8001/health")
        print("  - 健康检查: http://localhost:8000/health")
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
