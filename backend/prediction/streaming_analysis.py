"""
实时流式分析模块 - Phase 2.2
支持SSE流式推送、实时模式检测、增量更新
"""
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import asyncio
import json
from dataclasses import asdict


class StreamingAnalysisEngine:
    """流式分析引擎"""
    
    def __init__(self):
        self.active_streams = {}  # 活跃的流
        self.buffer_size = 100  # 缓冲区大小
        self.update_interval = 5  # 更新间隔（秒）
    
    async def stream_analysis(
        self,
        user_id: str,
        history: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """
        流式分析生成器
        使用SSE推送实时分析结果
        """
        from .emergence_detection import get_emergence_detection_system
        
        system = get_emergence_detection_system()
        
        try:
            # 1. 发送开始信号
            yield self._format_sse_message({
                "type": "start",
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "message": "Analysis started"
            })
            
            # 2. 流式执行分析
            yield self._format_sse_message({
                "type": "progress",
                "stage": "causal_inference",
                "progress": 10,
                "message": "Inferring causal relationships..."
            })
            
            # 执行因果推理
            patterns = system.pattern_detector.detect_patterns(history)
            
            yield self._format_sse_message({
                "type": "progress",
                "stage": "pattern_detection",
                "progress": 40,
                "message": f"Detected {len(patterns)} patterns"
            })
            
            # 3. 流式推送模式
            for i, pattern in enumerate(patterns):
                progress = 40 + (i / len(patterns)) * 30 if patterns else 40
                
                yield self._format_sse_message({
                    "type": "pattern",
                    "pattern": {
                        "id": pattern.pattern_id,
                        "type": pattern.pattern_type,
                        "scale": pattern.scale,
                        "strength": pattern.strength,
                        "confidence": pattern.confidence
                    },
                    "progress": progress
                })
                
                # 模拟处理延迟
                await asyncio.sleep(0.1)
            
            # 4. 生成可视化数据
            yield self._format_sse_message({
                "type": "progress",
                "stage": "visualization",
                "progress": 70,
                "message": "Generating visualizations..."
            })
            
            causal_graph = system.pattern_detector.causal_engine.causal_graph
            dashboard_data = system.viz_generator.generate_dashboard_data(
                history, patterns, dict(causal_graph)
            )
            
            yield self._format_sse_message({
                "type": "visualization",
                "data": dashboard_data
            })
            
            # 5. 生成报告
            yield self._format_sse_message({
                "type": "progress",
                "stage": "report",
                "progress": 90,
                "message": "Generating report..."
            })
            
            report = system._generate_report(
                patterns,
                [{"pattern": p, "explanation": system.explainer.generate_explanation(p)} for p in patterns],
                dashboard_data
            )
            
            yield self._format_sse_message({
                "type": "report",
                "data": report
            })
            
            # 6. 完成
            yield self._format_sse_message({
                "type": "complete",
                "timestamp": datetime.now().isoformat(),
                "total_patterns": len(patterns),
                "message": "Analysis completed successfully"
            })
        
        except Exception as e:
            yield self._format_sse_message({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _format_sse_message(self, data: Dict[str, Any]) -> str:
        """格式化SSE消息"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    async def stream_incremental_update(
        self,
        user_id: str,
        new_data: Dict[str, Any],
        previous_patterns: List
    ) -> AsyncGenerator[str, None]:
        """
        增量更新流
        只推送变化的部分
        """
        from .emergence_detection import get_emergence_detection_system
        
        system = get_emergence_detection_system()
        
        try:
            yield self._format_sse_message({
                "type": "incremental_start",
                "timestamp": datetime.now().isoformat()
            })
            
            # 检测新的模式
            new_patterns = system.pattern_detector.detect_patterns([new_data])
            
            # 比较新旧模式
            new_pattern_ids = {p.pattern_id for p in new_patterns}
            old_pattern_ids = {p.pattern_id for p in previous_patterns}
            
            added = new_pattern_ids - old_pattern_ids
            removed = old_pattern_ids - new_pattern_ids
            
            # 推送变化
            yield self._format_sse_message({
                "type": "incremental_update",
                "added_patterns": len(added),
                "removed_patterns": len(removed),
                "timestamp": datetime.now().isoformat()
            })
            
            # 推送新增模式
            for pattern in new_patterns:
                if pattern.pattern_id in added:
                    yield self._format_sse_message({
                        "type": "pattern_added",
                        "pattern": {
                            "id": pattern.pattern_id,
                            "type": pattern.pattern_type,
                            "scale": pattern.scale
                        }
                    })
            
            yield self._format_sse_message({
                "type": "incremental_complete",
                "timestamp": datetime.now().isoformat()
            })
        
        except Exception as e:
            yield self._format_sse_message({
                "type": "error",
                "error": str(e)
            })


class RealTimePatternMonitor:
    """实时模式监控器"""
    
    def __init__(self):
        self.monitored_patterns = {}  # 监控的模式
        self.alerts = []  # 告警列表
        self.thresholds = {
            "strength": 0.8,  # 强度阈值
            "confidence": 0.7,  # 置信度阈值
            "change_rate": 0.3  # 变化率阈值
        }
    
    def monitor_pattern(
        self,
        pattern_id: str,
        pattern: 'Pattern',
        threshold: Optional[float] = None
    ) -> None:
        """监控模式"""
        self.monitored_patterns[pattern_id] = {
            "pattern": pattern,
            "threshold": threshold or self.thresholds["strength"],
            "created_at": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "alert_count": 0
        }
    
    def check_alerts(self, patterns: List['Pattern']) -> List[Dict[str, Any]]:
        """检查告警"""
        alerts = []
        
        for pattern in patterns:
            if pattern.pattern_id in self.monitored_patterns:
                monitor = self.monitored_patterns[pattern.pattern_id]
                
                # 检查强度是否超过阈值
                if pattern.strength > monitor["threshold"]:
                    alert = {
                        "type": "high_strength",
                        "pattern_id": pattern.pattern_id,
                        "pattern_type": pattern.pattern_type,
                        "strength": pattern.strength,
                        "threshold": monitor["threshold"],
                        "timestamp": datetime.now().isoformat(),
                        "severity": "high" if pattern.strength > 0.9 else "medium"
                    }
                    alerts.append(alert)
                    monitor["alert_count"] += 1
        
        self.alerts.extend(alerts)
        return alerts
    
    def get_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        return self.alerts[-limit:]
    
    def clear_alerts(self) -> None:
        """清除告警"""
        self.alerts = []


class AdaptiveAnalysisScheduler:
    """自适应分析调度器"""
    
    def __init__(self):
        self.analysis_frequency = 3600  # 默认分析频率（秒）
        self.adaptive_enabled = True
        self.pattern_change_history = []
    
    def adjust_frequency(self, pattern_volatility: float) -> int:
        """
        根据模式波动性调整分析频率
        
        波动性高 -> 更频繁的分析
        波动性低 -> 更少的分析
        """
        if not self.adaptive_enabled:
            return self.analysis_frequency
        
        # 波动性范围：0-1
        # 高波动性（>0.7）：每30分钟分析一次
        # 中波动性（0.3-0.7）：每小时分析一次
        # 低波动性（<0.3）：每3小时分析一次
        
        if pattern_volatility > 0.7:
            self.analysis_frequency = 1800  # 30分钟
        elif pattern_volatility > 0.3:
            self.analysis_frequency = 3600  # 1小时
        else:
            self.analysis_frequency = 10800  # 3小时
        
        return self.analysis_frequency
    
    def calculate_volatility(self, pattern_history: List[Dict[str, Any]]) -> float:
        """计算模式波动性"""
        if len(pattern_history) < 2:
            return 0.0
        
        # 计算强度变化的标准差
        strengths = [p.get("strength", 0) for p in pattern_history]
        
        if not strengths:
            return 0.0
        
        mean = sum(strengths) / len(strengths)
        variance = sum((x - mean) ** 2 for x in strengths) / len(strengths)
        volatility = variance ** 0.5
        
        return min(volatility, 1.0)  # 限制在0-1范围内


class BatchAnalysisProcessor:
    """批量分析处理器"""
    
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self.pending_analyses = []
    
    async def process_batch(
        self,
        analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量处理分析请求
        """
        from .emergence_detection import get_emergence_detection_system
        
        system = get_emergence_detection_system()
        results = []
        
        # 分批处理
        for i in range(0, len(analyses), self.batch_size):
            batch = analyses[i:i + self.batch_size]
            
            for analysis in batch:
                try:
                    result = system.analyze(analysis.get("history", []))
                    results.append({
                        "user_id": analysis.get("user_id"),
                        "status": "success",
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "user_id": analysis.get("user_id"),
                        "status": "error",
                        "error": str(e)
                    })
                
                # 批次间延迟
                await asyncio.sleep(0.1)
        
        return results


# 全局实例
_streaming_engine = None
_monitor = None
_scheduler = None
_batch_processor = None

def get_streaming_engine() -> StreamingAnalysisEngine:
    """获取流式分析引擎"""
    global _streaming_engine
    if _streaming_engine is None:
        _streaming_engine = StreamingAnalysisEngine()
    return _streaming_engine

def get_pattern_monitor() -> RealTimePatternMonitor:
    """获取实时模式监控器"""
    global _monitor
    if _monitor is None:
        _monitor = RealTimePatternMonitor()
    return _monitor

def get_analysis_scheduler() -> AdaptiveAnalysisScheduler:
    """获取自适应分析调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AdaptiveAnalysisScheduler()
    return _scheduler

def get_batch_processor() -> BatchAnalysisProcessor:
    """获取批量分析处理器"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchAnalysisProcessor()
    return _batch_processor

