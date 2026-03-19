"""
系统健康检查工具
检查各个组件的运行状态
"""
import os
import sys
from typing import Dict, List
from datetime import datetime
import requests

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.checks = []
    
    def check_all(self) -> Dict:
        """执行所有健康检查"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        print("\n" + "="*60)
        print("系统健康检查")
        print("="*60 + "\n")
        
        # 1. 检查API服务器
        api_status = self.check_api_server()
        results["checks"]["api_server"] = api_status
        self._print_check_result("API服务器", api_status)
        
        # 2. 检查数据库
        db_status = self.check_database()
        results["checks"]["database"] = db_status
        self._print_check_result("数据库", db_status)
        
        # 3. 检查RAG系统
        rag_status = self.check_rag_system()
        results["checks"]["rag_system"] = rag_status
        self._print_check_result("RAG系统", rag_status)
        
        # 4. 检查心理测评系统
        personality_status = self.check_personality_system()
        results["checks"]["personality_system"] = personality_status
        self._print_check_result("心理测评系统", personality_status)
        
        # 5. 检查决策系统
        decision_status = self.check_decision_system()
        results["checks"]["decision_system"] = decision_status
        self._print_check_result("决策系统", decision_status)
        
        # 6. 检查LoRA系统
        lora_status = self.check_lora_system()
        results["checks"]["lora_system"] = lora_status
        self._print_check_result("LoRA系统", lora_status)
        
        # 7. 检查调度器
        scheduler_status = self.check_scheduler()
        results["checks"]["scheduler"] = scheduler_status
        self._print_check_result("训练调度器", scheduler_status)
        
        # 8. 检查磁盘空间
        disk_status = self.check_disk_space()
        results["checks"]["disk_space"] = disk_status
        self._print_check_result("磁盘空间", disk_status)
        
        # 计算总体状态
        unhealthy_count = sum(1 for check in results["checks"].values() if check["status"] != "healthy")
        if unhealthy_count > 0:
            results["overall_status"] = "degraded" if unhealthy_count < 3 else "unhealthy"
        
        print("\n" + "="*60)
        print(f"总体状态: {results['overall_status'].upper()}")
        print(f"健康组件: {len(results['checks']) - unhealthy_count}/{len(results['checks'])}")
        print("="*60 + "\n")
        
        return results
    
    def check_api_server(self) -> Dict:
        """检查API服务器"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "message": "API服务器运行正常",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"API返回异常状态码: {response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "unhealthy",
                "message": "无法连接到API服务器"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"检查失败: {str(e)}"
            }
    
    def check_database(self) -> Dict:
        """检查数据库"""
        db_path = "./backend/lifeswarm.db"
        
        if not os.path.exists(db_path):
            return {
                "status": "unhealthy",
                "message": "数据库文件不存在"
            }
        
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            conn.close()
            
            return {
                "status": "healthy",
                "message": f"数据库正常，包含{table_count}个表",
                "table_count": table_count
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"数据库访问失败: {str(e)}"
            }
    
    def check_rag_system(self) -> Dict:
        """检查RAG系统"""
        rag_dir = "./backend/data/production_rag"
        
        if not os.path.exists(rag_dir):
            return {
                "status": "degraded",
                "message": "RAG数据目录不存在"
            }
        
        # 统计用户数据
        user_count = len([f for f in os.listdir(rag_dir) if f.endswith('_metadata.json')])
        
        return {
            "status": "healthy",
            "message": f"RAG系统正常，{user_count}个用户有数据",
            "user_count": user_count
        }
    
    def check_personality_system(self) -> Dict:
        """检查心理测评系统"""
        try:
            response = requests.get(f"{self.base_url}/api/personality/questions", timeout=5)
            if response.status_code == 200:
                data = response.json()
                question_count = len(data.get('data', {}).get('questions', []))
                return {
                    "status": "healthy",
                    "message": f"心理测评系统正常，{question_count}道题目",
                    "question_count": question_count
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "心理测评API异常"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"检查失败: {str(e)}"
            }
    
    def check_decision_system(self) -> Dict:
        """检查决策系统"""
        simulations_dir = "./data/simulations"
        
        if not os.path.exists(simulations_dir):
            os.makedirs(simulations_dir, exist_ok=True)
            return {
                "status": "healthy",
                "message": "决策系统已初始化",
                "simulation_count": 0
            }
        
        simulation_count = len([f for f in os.listdir(simulations_dir) if f.endswith('.json')])
        
        return {
            "status": "healthy",
            "message": f"决策系统正常，{simulation_count}个模拟记录",
            "simulation_count": simulation_count
        }
    
    def check_lora_system(self) -> Dict:
        """检查LoRA系统"""
        lora_dir = "./models/lora"
        
        if not os.path.exists(lora_dir):
            return {
                "status": "degraded",
                "message": "LoRA模型目录不存在（未训练模型）"
            }
        
        # 统计用户模型
        user_dirs = [d for d in os.listdir(lora_dir) if os.path.isdir(os.path.join(lora_dir, d))]
        
        return {
            "status": "healthy",
            "message": f"LoRA系统正常，{len(user_dirs)}个用户有模型",
            "user_count": len(user_dirs)
        }
    
    def check_scheduler(self) -> Dict:
        """检查训练调度器"""
        try:
            response = requests.get(f"{self.base_url}/api/lora/scheduler/status", timeout=5)
            if response.status_code == 200:
                data = response.json().get('data', {})
                if data:
                    is_running = data.get('is_running', False)
                    return {
                        "status": "healthy" if is_running else "degraded",
                        "message": f"调度器{'运行中' if is_running else '未运行'}",
                        "is_running": is_running,
                        "active_users": data.get('active_users', 0)
                    }
            
            return {
                "status": "degraded",
                "message": "调度器状态未知"
            }
        except Exception as e:
            return {
                "status": "degraded",
                "message": f"无法获取调度器状态: {str(e)}"
            }
    
    def check_disk_space(self) -> Dict:
        """检查磁盘空间"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            percent_used = disk.percent
            free_gb = disk.free / (1024**3)
            
            if percent_used > 90:
                status = "unhealthy"
                message = f"磁盘空间严重不足: {percent_used:.1f}% 已用"
            elif percent_used > 80:
                status = "degraded"
                message = f"磁盘空间紧张: {percent_used:.1f}% 已用"
            else:
                status = "healthy"
                message = f"磁盘空间充足: {free_gb:.1f} GB 可用"
            
            return {
                "status": status,
                "message": message,
                "percent_used": percent_used,
                "free_gb": free_gb
            }
        except Exception as e:
            return {
                "status": "unknown",
                "message": f"无法检查磁盘空间: {str(e)}"
            }
    
    def _print_check_result(self, name: str, result: Dict):
        """打印检查结果"""
        status = result["status"]
        message = result["message"]
        
        status_icons = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓"
        }
        
        icon = status_icons.get(status, "❓")
        print(f"{icon} {name}: {message}")


# 测试代码
if __name__ == "__main__":
    checker = HealthChecker()
    results = checker.check_all()
    
    # 保存结果
    import json
    os.makedirs("./data", exist_ok=True)
    with open("./data/health_check.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("健康检查结果已保存到: ./data/health_check.json")
