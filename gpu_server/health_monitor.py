#!/usr/bin/env python3
"""
GPU服务器健康监控
监控GPU、内存、服务状态
"""
import os
import sys
import time
import json
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
import threading


class GPUMonitor:
    """GPU监控器"""
    
    def __init__(self, log_dir: str = "/root/autodl-tmp/logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._history = []
        self._max_history = 1000
    
    def get_gpu_stats(self) -> Dict[str, Any]:
        """获取GPU状态"""
        try:
            import torch
            if not torch.cuda.is_available():
                return {"available": False}
            
            return {
                "available": True,
                "device_name": torch.cuda.get_device_name(0),
                "memory_total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3,
                "memory_allocated_gb": torch.cuda.memory_allocated() / 1024**3,
                "memory_cached_gb": torch.cuda.memory_reserved() / 1024**3,
                "memory_free_gb": (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1024**3,
                "utilization_percent": self._get_gpu_utilization()
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def _get_gpu_utilization(self) -> float:
        """获取GPU利用率（需要nvidia-smi）"""
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            return float(result.stdout.strip())
        except:
            return 0.0
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统状态"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/root/autodl-tmp")
        
        return {
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": memory.total / 1024**3,
            "memory_used_gb": memory.used / 1024**3,
            "memory_percent": memory.percent,
            "disk_total_gb": disk.total / 1024**3,
            "disk_used_gb": disk.used / 1024**3,
            "disk_percent": disk.percent
        }
    
    def get_service_stats(self, port: int = 8000) -> Dict[str, Any]:
        """获取服务状态"""
        # 检查端口是否在监听
        is_running = False
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == "LISTEN":
                is_running = True
                break
        
        # 获取进程信息
        process_info = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'uvicorn' in ' '.join(cmdline):
                    process_info = {
                        "pid": proc.info['pid'],
                        "memory_mb": proc.info['memory_info'].rss / 1024**2 if proc.info['memory_info'] else 0,
                        "cpu_percent": proc.info['cpu_percent']
                    }
                    break
            except:
                pass
        
        return {
            "is_running": is_running,
            "port": port,
            "process": process_info
        }
    
    def get_full_status(self) -> Dict[str, Any]:
        """获取完整状态"""
        return {
            "timestamp": datetime.now().isoformat(),
            "gpu": self.get_gpu_stats(),
            "system": self.get_system_stats(),
            "service": self.get_service_stats()
        }
    
    def start_monitoring(self, interval: int = 60):
        """启动后台监控"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._thread.start()
        print(f"📊 监控已启动，间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("📊 监控已停止")
    
    def _monitor_loop(self, interval: int):
        """监控循环"""
        while self._running:
            try:
                status = self.get_full_status()
                self._history.append(status)
                
                # 限制历史记录数量
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]
                
                # 保存到文件
                log_file = os.path.join(self.log_dir, "monitor.json")
                with open(log_file, 'w') as f:
                    json.dump({
                        "current": status,
                        "history_count": len(self._history)
                    }, f, indent=2)
                
                # 检查告警
                self._check_alerts(status)
                
            except Exception as e:
                print(f"⚠️ 监控错误: {e}")
            
            time.sleep(interval)
    
    def _check_alerts(self, status: Dict):
        """检查告警条件"""
        alerts = []
        
        # GPU显存告警
        gpu = status.get("gpu", {})
        if gpu.get("available"):
            mem_used = gpu.get("memory_allocated_gb", 0)
            mem_total = gpu.get("memory_total_gb", 1)
            if mem_used / mem_total > 0.9:
                alerts.append(f"⚠️ GPU显存使用率过高: {mem_used:.1f}/{mem_total:.1f} GB")
        
        # 系统内存告警
        system = status.get("system", {})
        if system.get("memory_percent", 0) > 90:
            alerts.append(f"⚠️ 系统内存使用率过高: {system['memory_percent']}%")
        
        # 磁盘告警
        if system.get("disk_percent", 0) > 90:
            alerts.append(f"⚠️ 磁盘使用率过高: {system['disk_percent']}%")
        
        # 服务告警
        service = status.get("service", {})
        if not service.get("is_running"):
            alerts.append("⚠️ 后端服务未运行")
        
        # 输出告警
        for alert in alerts:
            print(alert)
    
    def get_history(self, limit: int = 100) -> list:
        """获取历史记录"""
        return self._history[-limit:]


def print_status(monitor: GPUMonitor):
    """打印状态"""
    status = monitor.get_full_status()
    
    print("\n" + "=" * 60)
    print(f"📊 服务器状态 - {status['timestamp']}")
    print("=" * 60)
    
    # GPU状态
    gpu = status["gpu"]
    if gpu.get("available"):
        print(f"\n🎮 GPU: {gpu['device_name']}")
        print(f"   显存: {gpu['memory_allocated_gb']:.1f} / {gpu['memory_total_gb']:.1f} GB ({gpu['memory_allocated_gb']/gpu['memory_total_gb']*100:.1f}%)")
        print(f"   利用率: {gpu.get('utilization_percent', 0):.1f}%")
    else:
        print("\n🎮 GPU: 不可用")
    
    # 系统状态
    sys_stat = status["system"]
    print(f"\n💻 系统:")
    print(f"   CPU: {sys_stat['cpu_percent']:.1f}% ({sys_stat['cpu_count']} 核)")
    print(f"   内存: {sys_stat['memory_used_gb']:.1f} / {sys_stat['memory_total_gb']:.1f} GB ({sys_stat['memory_percent']:.1f}%)")
    print(f"   磁盘: {sys_stat['disk_used_gb']:.1f} / {sys_stat['disk_total_gb']:.1f} GB ({sys_stat['disk_percent']:.1f}%)")
    
    # 服务状态
    svc = status["service"]
    print(f"\n🌐 服务:")
    print(f"   状态: {'✅ 运行中' if svc['is_running'] else '❌ 未运行'}")
    print(f"   端口: {svc['port']}")
    if svc.get("process"):
        print(f"   PID: {svc['process']['pid']}")
        print(f"   内存: {svc['process']['memory_mb']:.1f} MB")
    
    print("\n" + "=" * 60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="GPU服务器监控")
    parser.add_argument("action", nargs="?", default="status",
                       choices=["status", "watch", "daemon"],
                       help="操作: status(显示状态), watch(持续监控), daemon(后台监控)")
    parser.add_argument("--interval", "-i", type=int, default=5, help="监控间隔(秒)")
    
    args = parser.parse_args()
    
    monitor = GPUMonitor()
    
    if args.action == "status":
        print_status(monitor)
    
    elif args.action == "watch":
        print("📊 持续监控中... (Ctrl+C 退出)")
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                print_status(monitor)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n👋 监控已停止")
    
    elif args.action == "daemon":
        monitor.start_monitoring(interval=args.interval)
        print("📊 后台监控已启动")
        print(f"📝 日志文件: {monitor.log_dir}/monitor.json")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            monitor.stop_monitoring()


if __name__ == "__main__":
    main()
