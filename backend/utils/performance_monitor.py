"""
系统性能监控工具
监控API响应时间、内存使用、数据库查询等
"""
import time
import psutil
import functools
from typing import Dict, List, Callable
from datetime import datetime
from collections import defaultdict
import json
import os


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.api_calls = defaultdict(int)
        self.slow_queries = []
        self.error_count = defaultdict(int)
        
    def track_api_call(self, endpoint: str, duration: float, status_code: int):
        """记录API调用"""
        self.metrics[endpoint].append({
            "duration": duration,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        })
        self.api_calls[endpoint] += 1
        
        # 记录慢查询（超过2秒）
        if duration > 2.0:
            self.slow_queries.append({
                "endpoint": endpoint,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })
        
        # 记录错误
        if status_code >= 400:
            self.error_count[endpoint] += 1
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = {
            "total_calls": sum(self.api_calls.values()),
            "endpoints": {},
            "slow_queries": len(self.slow_queries),
            "total_errors": sum(self.error_count.values()),
            "system": self.get_system_metrics()
        }
        
        # 计算每个端点的统计
        for endpoint, calls in self.api_calls.items():
            metrics = self.metrics[endpoint]
            if metrics:
                durations = [m["duration"] for m in metrics]
                stats["endpoints"][endpoint] = {
                    "calls": calls,
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "errors": self.error_count.get(endpoint, 0)
                }
        
        return stats
    
    def get_system_metrics(self) -> Dict:
        """获取系统指标"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_mb": psutil.virtual_memory().used / (1024 * 1024),
            "disk_percent": psutil.disk_usage('/').percent
        }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """获取最慢的查询"""
        sorted_queries = sorted(
            self.slow_queries,
            key=lambda x: x["duration"],
            reverse=True
        )
        return sorted_queries[:limit]
    
    def reset(self):
        """重置统计"""
        self.metrics.clear()
        self.api_calls.clear()
        self.slow_queries.clear()
        self.error_count.clear()
    
    def save_report(self, filepath: str = "./data/performance_report.json"):
        """保存性能报告"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "slow_queries": self.get_slow_queries()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 性能报告已保存: {filepath}")


# 全局监控器实例
_monitor = PerformanceMonitor()

def get_monitor() -> PerformanceMonitor:
    """获取全局监控器"""
    return _monitor


def monitor_performance(endpoint: str):
    """性能监控装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                
                # 尝试从结果中获取状态码
                if isinstance(result, dict) and "code" in result:
                    status_code = result["code"]
                
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                get_monitor().track_api_call(endpoint, duration, status_code)
        
        return wrapper
    return decorator


# 测试代码
if __name__ == "__main__":
    monitor = PerformanceMonitor()
    
    # 模拟一些API调用
    monitor.track_api_call("/api/test", 0.5, 200)
    monitor.track_api_call("/api/test", 0.3, 200)
    monitor.track_api_call("/api/slow", 2.5, 200)
    monitor.track_api_call("/api/error", 0.1, 500)
    
    # 获取统计
    stats = monitor.get_statistics()
    
    print("="*60)
    print("性能监控统计")
    print("="*60)
    print(f"\n总调用数: {stats['total_calls']}")
    print(f"慢查询数: {stats['slow_queries']}")
    print(f"错误总数: {stats['total_errors']}")
    
    print(f"\n系统指标:")
    print(f"  CPU: {stats['system']['cpu_percent']:.1f}%")
    print(f"  内存: {stats['system']['memory_percent']:.1f}%")
    print(f"  磁盘: {stats['system']['disk_percent']:.1f}%")
    
    print(f"\n端点统计:")
    for endpoint, data in stats['endpoints'].items():
        print(f"\n  {endpoint}:")
        print(f"    调用次数: {data['calls']}")
        print(f"    平均耗时: {data['avg_duration']:.3f}s")
        print(f"    错误次数: {data['errors']}")
    
    # 保存报告
    monitor.save_report()
    
    print("\n" + "="*60)
