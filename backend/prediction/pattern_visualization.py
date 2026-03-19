"""
模式可视化模块 - 涌现检测深化
生成因果图、模式流程图、交互式可视化数据
"""
from typing import Dict, List, Any, Optional
from dataclasses import asdict
import json
from datetime import datetime


class PatternVisualizer:
    """模式可视化器"""
    
    def visualize_causal_graph(self, causal_graph: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        可视化因果图
        返回节点和边的数据结构
        """
        nodes = []
        edges = []
        node_set = set()
        
        # 创建节点
        for cause, effects in causal_graph.items():
            if cause not in node_set:
                nodes.append({
                    "id": cause,
                    "label": cause,
                    "type": "metric",
                    "color": self._get_metric_color(cause)
                })
                node_set.add(cause)
            
            for effect in effects:
                if effect not in node_set:
                    nodes.append({
                        "id": effect,
                        "label": effect,
                        "type": "metric",
                        "color": self._get_metric_color(effect)
                    })
                    node_set.add(effect)
                
                # 创建边
                edges.append({
                    "source": cause,
                    "target": effect,
                    "type": "causal",
                    "strength": 0.7  # 默认强度
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "force-directed"
        }
    
    def visualize_causal_chain(self, chain: 'CausalChain') -> Dict[str, Any]:
        """可视化单条因果链"""
        nodes = []
        edges = []
        
        # 创建节点
        for i, relation in enumerate(chain.relations):
            if i == 0:
                nodes.append({
                    "id": relation.cause,
                    "label": relation.cause,
                    "type": "start",
                    "color": "#4CAF50"
                })
            
            nodes.append({
                "id": relation.effect,
                "label": relation.effect,
                "type": "end" if i == len(chain.relations) - 1 else "middle",
                "color": "#2196F3" if i < len(chain.relations) - 1 else "#FF9800"
            })
            
            # 创建边
            edges.append({
                "source": relation.cause,
                "target": relation.effect,
                "strength": relation.strength,
                "delay": relation.delay,
                "confidence": relation.confidence,
                "label": f"{relation.strength:.2f} ({relation.delay}d)"
            })
        
        return {
            "chain_id": chain.chain_id,
            "nodes": nodes,
            "edges": edges,
            "total_strength": chain.total_strength,
            "domains": chain.domains,
            "description": chain.description
        }
    
    def visualize_pattern_network(self, patterns: List['Pattern']) -> Dict[str, Any]:
        """可视化模式网络"""
        nodes = []
        edges = []
        node_map = {}
        
        # 创建模式节点
        for pattern in patterns:
            node_id = pattern.pattern_id
            node_map[node_id] = pattern
            
            nodes.append({
                "id": node_id,
                "label": pattern.pattern_type,
                "type": pattern.scale,
                "strength": pattern.strength,
                "confidence": pattern.confidence,
                "color": self._get_pattern_color(pattern.scale),
                "size": 20 + pattern.strength * 30
            })
        
        # 创建模式之间的连接（基于共享指标）
        for i, pattern1 in enumerate(patterns):
            for pattern2 in patterns[i+1:]:
                shared_metrics = set(pattern1.metrics) & set(pattern2.metrics)
                
                if shared_metrics:
                    edges.append({
                        "source": pattern1.pattern_id,
                        "target": pattern2.pattern_id,
                        "type": "shared_metrics",
                        "shared_count": len(shared_metrics),
                        "shared_metrics": list(shared_metrics)
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "hierarchical"
        }
    
    def generate_timeline_visualization(
        self,
        history: List[Dict[str, Any]],
        patterns: List['Pattern']
    ) -> Dict[str, Any]:
        """生成时间线可视化"""
        timeline_events = []
        
        # 为每个模式创建时间线事件
        for pattern in patterns:
            event = {
                "id": pattern.pattern_id,
                "type": pattern.pattern_type,
                "scale": pattern.scale,
                "timestamp": datetime.now().isoformat(),
                "strength": pattern.strength,
                "confidence": pattern.confidence,
                "description": pattern.explanation,
                "metrics": pattern.metrics
            }
            timeline_events.append(event)
        
        return {
            "events": timeline_events,
            "total_events": len(timeline_events),
            "time_range": {
                "start": history[0].get("timestamp", "unknown") if history else None,
                "end": history[-1].get("timestamp", "unknown") if history else None
            }
        }
    
    def generate_heatmap_data(
        self,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成热力图数据（指标相关性矩阵）"""
        if not history:
            return {"matrix": [], "metrics": []}
        
        # 提取所有数值指标
        metrics = []
        for key in history[0].keys():
            if isinstance(history[0][key], (int, float)):
                metrics.append(key)
        
        # 构建相关性矩阵
        matrix = []
        for metric1 in metrics:
            row = []
            for metric2 in metrics:
                values1 = [h.get(metric1, 0) for h in history]
                values2 = [h.get(metric2, 0) for h in history]
                
                # 计算相关系数
                try:
                    import numpy as np
                    correlation = np.corrcoef(values1, values2)[0, 1]
                    if np.isnan(correlation):
                        correlation = 0
                except:
                    correlation = 0
                
                row.append(correlation)
            
            matrix.append(row)
        
        return {
            "matrix": matrix,
            "metrics": metrics,
            "type": "correlation_heatmap"
        }
    
    def _get_metric_color(self, metric: str) -> str:
        """根据指标类型获取颜色"""
        metric_lower = metric.lower()
        
        if any(kw in metric_lower for kw in ['sleep', 'exercise', 'health']):
            return "#4CAF50"  # 绿色 - 健康
        elif any(kw in metric_lower for kw in ['work', 'focus', 'efficiency']):
            return "#2196F3"  # 蓝色 - 工作
        elif any(kw in metric_lower for kw in ['mood', 'stress', 'emotion']):
            return "#FF9800"  # 橙色 - 情绪
        elif any(kw in metric_lower for kw in ['social', 'loneliness']):
            return "#9C27B0"  # 紫色 - 社交
        elif any(kw in metric_lower for kw in ['savings', 'spending', 'finance']):
            return "#F44336"  # 红色 - 财务
        else:
            return "#757575"  # 灰色 - 其他
    
    def _get_pattern_color(self, scale: str) -> str:
        """根据模式尺度获取颜色"""
        if scale == "micro":
            return "#4CAF50"  # 绿色
        elif scale == "meso":
            return "#2196F3"  # 蓝色
        elif scale == "macro":
            return "#FF9800"  # 橙色
        else:
            return "#757575"  # 灰色


class InteractiveVisualizationGenerator:
    """交互式可视化生成器"""
    
    def generate_dashboard_data(
        self,
        history: List[Dict[str, Any]],
        patterns: List['Pattern'],
        causal_graph: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """生成仪表板数据"""
        visualizer = PatternVisualizer()
        
        return {
            "summary": {
                "total_patterns": len(patterns),
                "micro_patterns": len([p for p in patterns if p.scale == "micro"]),
                "meso_patterns": len([p for p in patterns if p.scale == "meso"]),
                "macro_patterns": len([p for p in patterns if p.scale == "macro"]),
                "average_strength": sum(p.strength for p in patterns) / len(patterns) if patterns else 0,
                "average_confidence": sum(p.confidence for p in patterns) / len(patterns) if patterns else 0
            },
            "causal_graph": visualizer.visualize_causal_graph(causal_graph),
            "pattern_network": visualizer.visualize_pattern_network(patterns),
            "timeline": visualizer.generate_timeline_visualization(history, patterns),
            "heatmap": visualizer.generate_heatmap_data(history),
            "top_patterns": self._get_top_patterns(patterns, top_n=5)
        }
    
    def _get_top_patterns(self, patterns: List['Pattern'], top_n: int = 5) -> List[Dict[str, Any]]:
        """获取排名前N的模式"""
        # 按强度和置信度排序
        sorted_patterns = sorted(
            patterns,
            key=lambda p: p.strength * p.confidence,
            reverse=True
        )
        
        top_patterns = []
        for pattern in sorted_patterns[:top_n]:
            top_patterns.append({
                "id": pattern.pattern_id,
                "type": pattern.pattern_type,
                "scale": pattern.scale,
                "strength": pattern.strength,
                "confidence": pattern.confidence,
                "domains": pattern.domains,
                "metrics": pattern.metrics,
                "explanation": pattern.explanation,
                "score": pattern.strength * pattern.confidence
            })
        
        return top_patterns
    
    def generate_interactive_chart_config(
        self,
        pattern: 'Pattern'
    ) -> Dict[str, Any]:
        """生成交互式图表配置"""
        return {
            "type": "pattern_detail",
            "pattern_id": pattern.pattern_id,
            "title": f"{pattern.pattern_type} - {pattern.scale}",
            "metrics": pattern.metrics,
            "domains": pattern.domains,
            "strength": pattern.strength,
            "confidence": pattern.confidence,
            "explanation": pattern.explanation,
            "causal_chains": [
                {
                    "id": chain.chain_id,
                    "description": chain.description,
                    "strength": chain.total_strength,
                    "length": chain.length
                }
                for chain in pattern.causal_chains
            ]
        }


class ExportFormatter:
    """导出格式化器"""
    
    def export_to_json(
        self,
        patterns: List['Pattern'],
        causal_graph: Dict[str, List[str]]
    ) -> str:
        """导出为JSON格式"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "patterns": [
                {
                    "id": p.pattern_id,
                    "type": p.pattern_type,
                    "scale": p.scale,
                    "domains": p.domains,
                    "metrics": p.metrics,
                    "strength": p.strength,
                    "confidence": p.confidence,
                    "explanation": p.explanation
                }
                for p in patterns
            ],
            "causal_graph": causal_graph
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def export_to_html(
        self,
        dashboard_data: Dict[str, Any]
    ) -> str:
        """导出为HTML格式"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>涌现检测分析报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; }
                .metric { display: inline-block; margin: 10px 20px 10px 0; }
                .metric-value { font-size: 24px; font-weight: bold; color: #2196F3; }
                .metric-label { font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <h1>涌现检测分析报告</h1>
            <div class="summary">
                <h2>统计摘要</h2>
        """
        
        summary = dashboard_data.get("summary", {})
        for key, value in summary.items():
            html += f"""
                <div class="metric">
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{key}</div>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html


# 全局实例
_visualizer = None
_generator = None

def get_visualizer() -> PatternVisualizer:
    """获取全局可视化器实例"""
    global _visualizer
    if _visualizer is None:
        _visualizer = PatternVisualizer()
    return _visualizer

def get_visualization_generator() -> InteractiveVisualizationGenerator:
    """获取全局交互式可视化生成器实例"""
    global _generator
    if _generator is None:
        _generator = InteractiveVisualizationGenerator()
    return _generator

