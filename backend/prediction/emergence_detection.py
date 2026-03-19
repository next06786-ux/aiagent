"""
涌现检测深化 - 主集成模块
整合因果推理、多尺度模式检测、可视化、解释生成
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from .causal_inference_engine import (
    MultiScalePatternDetector,
    PatternExplainer,
    get_pattern_detector
)
from .pattern_visualization import (
    PatternVisualizer,
    InteractiveVisualizationGenerator,
    ExportFormatter,
    get_visualizer,
    get_visualization_generator
)


class EmergenceDetectionSystem:
    """涌现检测系统"""
    
    def __init__(self):
        self.pattern_detector = get_pattern_detector()
        self.explainer = PatternExplainer()
        self.visualizer = get_visualizer()
        self.viz_generator = get_visualization_generator()
        self.export_formatter = ExportFormatter()
        
        self.last_patterns = []
        self.last_causal_graph = {}
        self.analysis_history = []
    
    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行完整的涌现检测分析
        """
        if not history:
            return {
                "status": "error",
                "message": "No history data provided"
            }
        
        try:
            # 1. 检测多尺度模式
            patterns = self.pattern_detector.detect_patterns(history)
            self.last_patterns = patterns
            
            # 2. 获取因果图
            causal_graph = self.pattern_detector.causal_engine.causal_graph
            self.last_causal_graph = dict(causal_graph)
            
            # 3. 为每个模式生成解释
            explained_patterns = []
            for pattern in patterns:
                explanation = self.explainer.generate_explanation(pattern)
                explained_patterns.append({
                    "pattern": pattern,
                    "explanation": explanation
                })
            
            # 4. 生成可视化数据
            dashboard_data = self.viz_generator.generate_dashboard_data(
                history, patterns, self.last_causal_graph
            )
            
            # 5. 生成分析报告
            report = self._generate_report(
                patterns, explained_patterns, dashboard_data
            )
            
            # 6. 保存分析历史
            self.analysis_history.append({
                "timestamp": datetime.now().isoformat(),
                "pattern_count": len(patterns),
                "report": report
            })
            
            return {
                "status": "success",
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
                        "explanation": explained_patterns[i]["explanation"]
                    }
                    for i, p in enumerate(patterns)
                ],
                "causal_graph": self.last_causal_graph,
                "dashboard": dashboard_data,
                "report": report
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_report(
        self,
        patterns: List,
        explained_patterns: List[Dict],
        dashboard_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成分析报告"""
        summary = dashboard_data.get("summary", {})
        
        # 按尺度分类模式
        micro_patterns = [p for p in patterns if p.scale == "micro"]
        meso_patterns = [p for p in patterns if p.scale == "meso"]
        macro_patterns = [p for p in patterns if p.scale == "macro"]
        
        # 生成关键发现
        key_findings = []
        
        if macro_patterns:
            key_findings.append({
                "level": "macro",
                "finding": f"检测到{len(macro_patterns)}个系统级别的协同效应",
                "significance": "high"
            })
        
        if meso_patterns:
            key_findings.append({
                "level": "meso",
                "finding": f"识别出{len(meso_patterns)}条因果链",
                "significance": "high"
            })
        
        if micro_patterns:
            key_findings.append({
                "level": "micro",
                "finding": f"发现{len(micro_patterns)}个指标的显著变化",
                "significance": "medium"
            })
        
        # 生成建议
        recommendations = self._generate_recommendations(patterns)
        
        return {
            "summary": summary,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "detailed_patterns": [
                {
                    "pattern": {
                        "id": ep["pattern"].pattern_id,
                        "type": ep["pattern"].pattern_type,
                        "scale": ep["pattern"].scale
                    },
                    "explanation": ep["explanation"]
                }
                for ep in explained_patterns
            ]
        }
    
    def _generate_recommendations(self, patterns: List) -> List[Dict[str, Any]]:
        """生成建议"""
        recommendations = []
        
        # 分析模式中的关键指标
        all_metrics = set()
        for pattern in patterns:
            all_metrics.update(pattern.metrics)
        
        # 基于模式生成建议
        if len(patterns) > 5:
            recommendations.append({
                "type": "complexity",
                "priority": "high",
                "suggestion": "生活系统中存在多个相互作用的模式，建议关注关键指标的变化"
            })
        
        # 检查是否有高强度的模式
        high_strength_patterns = [p for p in patterns if p.strength > 0.8]
        if high_strength_patterns:
            recommendations.append({
                "type": "focus",
                "priority": "high",
                "suggestion": f"发现{len(high_strength_patterns)}个高强度模式，建议优先关注"
            })
        
        # 检查因果链
        causal_chains = []
        for pattern in patterns:
            causal_chains.extend(pattern.causal_chains)
        
        if causal_chains:
            recommendations.append({
                "type": "causality",
                "priority": "medium",
                "suggestion": f"识别出{len(causal_chains)}条因果链，改变一个指标可能影响其他指标"
            })
        
        return recommendations
    
    def get_pattern_details(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """获取单个模式的详细信息"""
        for pattern in self.last_patterns:
            if pattern.pattern_id == pattern_id:
                explanation = self.explainer.generate_explanation(pattern)
                
                return {
                    "pattern": {
                        "id": pattern.pattern_id,
                        "type": pattern.pattern_type,
                        "scale": pattern.scale,
                        "domains": pattern.domains,
                        "metrics": pattern.metrics,
                        "strength": pattern.strength,
                        "confidence": pattern.confidence
                    },
                    "explanation": explanation,
                    "causal_chains": [
                        {
                            "id": chain.chain_id,
                            "description": chain.description,
                            "strength": chain.total_strength,
                            "length": chain.length,
                            "domains": chain.domains
                        }
                        for chain in pattern.causal_chains
                    ],
                    "visualization": self.viz_generator.generate_interactive_chart_config(pattern)
                }
        
        return None
    
    def export_analysis(self, format: str = "json") -> str:
        """导出分析结果"""
        if format == "json":
            return self.export_formatter.export_to_json(
                self.last_patterns,
                self.last_causal_graph
            )
        elif format == "html":
            dashboard_data = self.viz_generator.generate_dashboard_data(
                [], self.last_patterns, self.last_causal_graph
            )
            return self.export_formatter.export_to_html(dashboard_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """获取分析历史"""
        return self.analysis_history
    
    def compare_analyses(
        self,
        analysis1: Dict[str, Any],
        analysis2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """比较两次分析结果"""
        patterns1 = analysis1.get("patterns", [])
        patterns2 = analysis2.get("patterns", [])
        
        # 计算模式变化
        new_patterns = [p for p in patterns2 if p["id"] not in [p1["id"] for p1 in patterns1]]
        removed_patterns = [p for p in patterns1 if p["id"] not in [p2["id"] for p2 in patterns2]]
        
        # 计算强度变化
        strength_changes = []
        for p2 in patterns2:
            for p1 in patterns1:
                if p2["type"] == p1["type"] and p2["scale"] == p1["scale"]:
                    strength_change = p2["strength"] - p1["strength"]
                    if abs(strength_change) > 0.1:
                        strength_changes.append({
                            "pattern": p2["type"],
                            "change": strength_change
                        })
        
        return {
            "new_patterns": new_patterns,
            "removed_patterns": removed_patterns,
            "strength_changes": strength_changes,
            "pattern_count_change": len(patterns2) - len(patterns1)
        }


# 全局实例
_system = None

def get_emergence_detection_system() -> EmergenceDetectionSystem:
    """获取全局涌现检测系统实例"""
    global _system
    if _system is None:
        _system = EmergenceDetectionSystem()
    return _system

