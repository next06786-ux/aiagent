"""
系统健康检查工具
单机 GPU 部署模式：FastAPI + 本地 Qwen3.5-9B + 用户专属 LoRA
"""
import os
import sys
import socket
from typing import Dict
from datetime import datetime
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class HealthChecker:
    """单机 GPU 部署健康检查器"""

    def __init__(
        self,
        api_base_url: str = "http://127.0.0.1:8000",
        lora_dir: str = "./models/lora"
    ):
        self.api_base_url = api_base_url
        self.lora_dir = lora_dir

    def check_all(self) -> Dict:
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }

        print("\n" + "=" * 60)
        print("单机 GPU 部署健康检查")
        print("=" * 60 + "\n")

        checks = {
            "api_server": ("FastAPI", self.check_api_server),
            "database": ("数据库", self.check_database),
            "decision_system": ("决策系统", self.check_decision_system),
            "lora_system": ("LoRA系统", self.check_lora_system),
            "scheduler": ("训练调度器", self.check_scheduler),
            "disk_space": ("磁盘空间", self.check_disk_space),
            "ports": ("关键端口", self.check_ports),
        }

        unhealthy_count = 0
        for key, (label, func) in checks.items():
            result = func()
            results["checks"][key] = result
            self._print_check_result(label, result)
            if result["status"] not in ["healthy", "degraded"]:
                unhealthy_count += 1

        if unhealthy_count > 0:
            results["overall_status"] = "degraded" if unhealthy_count < 3 else "unhealthy"

        print("\n" + "=" * 60)
        print(f"总体状态: {results['overall_status'].upper()}")
        print("=" * 60 + "\n")
        return results

    def check_api_server(self) -> Dict:
        try:
            resp = requests.get(f"{self.api_base_url}/health", timeout=5)
            if resp.status_code == 200:
                return {
                    "status": "healthy",
                    "message": "FastAPI 运行正常",
                    "response_time": resp.elapsed.total_seconds()
                }
            return {"status": "unhealthy", "message": f"FastAPI 状态码异常: {resp.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"FastAPI 不可达: {e}"}

    def check_database(self) -> Dict:
        mysql_host = os.environ.get("MYSQL_HOST", "localhost")
        mysql_port = int(os.environ.get("MYSQL_PORT", "3306"))
        try:
            with socket.create_connection((mysql_host, mysql_port), timeout=3):
                return {"status": "healthy", "message": f"MySQL 可连接 ({mysql_host}:{mysql_port})"}
        except Exception as e:
            return {"status": "degraded", "message": f"MySQL 不可达: {e}"}

    def check_decision_system(self) -> Dict:
        simulations_dir = "./data/simulations"
        os.makedirs(simulations_dir, exist_ok=True)
        count = len([f for f in os.listdir(simulations_dir) if f.endswith('.json')])
        return {
            "status": "healthy",
            "message": f"决策系统可用，已有 {count} 条模拟记录",
            "simulation_count": count
        }

    def check_lora_system(self) -> Dict:
        if not os.path.exists(self.lora_dir):
            return {"status": "degraded", "message": f"LoRA 目录不存在: {self.lora_dir}"}
        user_dirs = [d for d in os.listdir(self.lora_dir) if os.path.isdir(os.path.join(self.lora_dir, d))]
        return {
            "status": "healthy",
            "message": f"LoRA 目录正常，{len(user_dirs)} 个用户目录",
            "user_count": len(user_dirs),
            "path": self.lora_dir
        }

    def check_scheduler(self) -> Dict:
        try:
            resp = requests.get(f"{self.api_base_url}/api/lora/scheduler/status", timeout=5)
            if resp.status_code != 200:
                return {"status": "degraded", "message": f"调度器状态接口异常: {resp.status_code}"}
            data = resp.json().get("data", {})
            is_running = data.get("is_running", False)
            return {
                "status": "healthy" if is_running else "degraded",
                "message": f"调度器{'运行中' if is_running else '未运行'}",
                "is_running": is_running
            }
        except Exception as e:
            return {"status": "degraded", "message": f"调度器状态未知: {e}"}

    def check_disk_space(self) -> Dict:
        try:
            import psutil
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024 ** 3)
            used = disk.percent
            if used > 90:
                return {"status": "unhealthy", "message": f"磁盘空间严重不足: {used:.1f}% 已用"}
            if used > 80:
                return {"status": "degraded", "message": f"磁盘空间偏紧: {used:.1f}% 已用"}
            return {"status": "healthy", "message": f"磁盘空间正常: {free_gb:.1f} GB 可用"}
        except Exception as e:
            return {"status": "unknown", "message": f"无法检查磁盘空间: {e}"}

    def check_ports(self) -> Dict:
        port_map = {8000: "FastAPI"}
        unavailable = []
        for port, name in port_map.items():
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=2):
                    pass
            except Exception:
                unavailable.append(f"{name}:{port}")
        if unavailable:
            return {"status": "degraded", "message": f"端口未监听: {', '.join(unavailable)}"}
        return {"status": "healthy", "message": "关键端口监听正常 (8000)"}

    def _print_check_result(self, name: str, result: Dict):
        icons = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓",
        }
        print(f"{icons.get(result['status'], '❓')} {name}: {result['message']}")


if __name__ == "__main__":
    import json

    checker = HealthChecker(
        api_base_url=os.environ.get("API_BASE_URL", "http://127.0.0.1:8000"),
        lora_dir=os.environ.get("LORA_MODELS_DIR", "./models/lora"),
    )
    results = checker.check_all()
    os.makedirs("./data", exist_ok=True)
    with open("./data/health_check.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("健康检查结果已保存到: ./data/health_check.json")
