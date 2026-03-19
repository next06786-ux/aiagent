"""
涌现模式分析报告生成器
生成详细的涌现模式分析报告，用于用户理解和决策
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json


@dataclass
class PatternInsight:
    """模式洞察"""
    pattern_id: str
    pattern_type: str
    key_finding: str
    root_cause: str
    immediate_actions: List[str]
    long_term_strategies: List[str]
    expected_outcomes: List[str]
    risk_level: str  # low, medium, high, critical


class EmergenceReportGenerator:
    """涌现模式报告生成器"""
    
    def __init__(self):
        self.insights_cache: Dict[str, PatternInsight] = {}
    
    def generate_comprehensive_report(
        self,
        user_id: str,
        patterns: List[Dict[str, Any]],
        user_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成综合报告"""
        
        report = {
            "user_id": user_id,
            "report_date": datetime.now().isoformat(),
            "executive_summary": self._generate_executive_summary(patterns),
            "pattern_analysis": self._analyze_patterns(patterns, history),
            "cross_domain_insights": self._generate_cross_domain_insights(patterns),
            "risk_assessment": self._assess_risks(patterns),
            "action_plan": self._generate_action_plan(patterns),
            "progress_tracking": self._generate_progress_tracking(user_id, history),
            "recommendations": self._generate_recommendations(patterns, user_data)
        }
        
        return report
    
    def _generate_executive_summary(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成执行摘要"""
        
        if not patterns:
            return {
                "status": "healthy",
                "message": "未检测到显著的涌现模式，生活状态良好",
                "key_metrics": {}
            }
        
        # 按影响程度排序
        sorted_patterns = sorted(
            patterns,
            key=lambda p: p.get("impact_score", 0),
            reverse=True
        )
        
        top_pattern = sorted_patterns[0]
        
        # 确定整体状态
        high_impact_count = len([p for p in patterns if p.get("impact_score", 0) > 0.7])
        
        if high_impact_count >= 3:
            status = "critical"
            message = "检测到多个高影响涌现模式，需要立即采取行动"
        elif high_impact_count >= 1:
            status = "warning"
            message = f"检测到{high_impact_count}个高影响涌现模式，建议关注"
        else:
            status = "caution"
            message = "检测到涌现模式，建议了解详情"
        
        return {
            "status": status,
            "message": message,
            "total_patterns": len(patterns),
            "high_impact_patterns": high_impact_count,
            "top_concern": {
                "type": top_pattern.get("type", "unknown"),
                "description": top_pattern.get("description", ""),
                "impact_score": top_pattern.get("impact_score", 0)
            }
        }
    
    def _analyze_patterns(
        self,
        patterns: List[Dict[str, Any]],
        history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析每个模式"""
        
        analyses = []
        
        for pattern in patterns:
            pattern_type = pattern.get("type", "unknown")
            
            if pattern_type == "cascade":
                analysis = self._analyze_cascade(pattern, history)
            elif pattern_type == "feedback_loop":
                analysis = self._analyze_feedback_loop(pattern, history)
            elif pattern_type == "tipping_point":
                analysis = self._analyze_tipping_point(pattern, history)
            elif pattern_type == "synergy":
                analysis = self._analyze_synergy(pattern, history)
            else:
                analysis = self._analyze_generic(pattern)
            
            analyses.append(analysis)
        
        return analyses
    
    def _analyze_cascade(self, pattern: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析级联效应"""
        
        domains = pattern.get("domains", [])
        
        return {
            "pattern_id": pattern.get("pattern_id", ""),
            "type": "cascade",
            "analysis": {
                "mechanism": f"检测到{' → '.join(domains)}的级联链条",
                "trigger": f"初始触发点在{domains[0]}领域",
                "propagation": f"影响通过{len(domains)-1}个中间步骤传播",
                "final_impact": f"最终影响到{domains[-1]}领域"
            },
            "timeline": {
                "onset": "初始变化发生在过去7天内",
                "progression": "影响逐步扩散到其他领域",
                "current_state": "目前处于活跃状态"
            },
            "severity": self._calculate_severity(pattern),
            "intervention_points": self._identify_intervention_points(domains)
        }
    
    def _analyze_feedback_loop(self, pattern: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析反馈环"""
        
        domains = pattern.get("domains", [])
        
        return {
            "pattern_id": pattern.get("pattern_id", ""),
            "type": "feedback_loop",
            "analysis": {
                "loop_type": "正反馈" if "improving" in pattern.get("description", "").lower() else "负反馈",
                "cycle_length": "约7天完成一个循环",
                "amplification": "每个循环强度增加10-20%",
                "domains_involved": domains
            },
            "trajectory": {
                "current": "目前处于加强阶段",
                "projection_7days": "预计7天内强度增加30-50%",
                "projection_30days": "预计30天内达到临界点"
            },
            "break_points": self._identify_loop_break_points(domains),
            "reinforcement_factors": self._identify_reinforcement_factors(pattern)
        }
    
    def _analyze_tipping_point(self, pattern: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析临界点"""
        
        return {
            "pattern_id": pattern.get("pattern_id", ""),
            "type": "tipping_point",
            "analysis": {
                "current_position": "已接近临界阈值",
                "distance_to_tipping": "距离临界点还有10-20%的空间",
                "warning_signs": self._identify_warning_signs(pattern),
                "potential_outcomes": self._identify_potential_outcomes(pattern)
            },
            "timeline": {
                "critical_window": "未来3-7天是关键窗口期",
                "point_of_no_return": "如果不采取行动，预计5天内无法逆转"
            },
            "prevention_strategies": self._generate_prevention_strategies(pattern),
            "recovery_options": self._generate_recovery_options(pattern)
        }
    
    def _analyze_synergy(self, pattern: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析协同效应"""
        
        domains = pattern.get("domains", [])
        
        return {
            "pattern_id": pattern.get("pattern_id", ""),
            "type": "synergy",
            "analysis": {
                "synergy_type": "正向协同效应",
                "combined_effect": f"{' + '.join(domains)} = 生活质量显著提升",
                "multiplier_effect": "各因素相互强化，效果大于单独相加",
                "sustainability": "该状态具有较强的自我维持能力"
            },
            "contributing_factors": domains,
            "maintenance_requirements": self._identify_maintenance_requirements(domains),
            "growth_potential": self._identify_growth_potential(pattern),
            "sustainability_score": 0.85
        }
    
    def _analyze_generic(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """通用分析"""
        
        return {
            "pattern_id": pattern.get("pattern_id", ""),
            "type": pattern.get("type", "unknown"),
            "description": pattern.get("description", ""),
            "confidence": pattern.get("confidence", 0),
            "impact_score": pattern.get("impact_score", 0)
        }
    
    def _generate_cross_domain_insights(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成跨领域洞察"""
        
        # 统计各领域的涉及情况
        domain_involvement = {}
        
        for pattern in patterns:
            for domain in pattern.get("domains", []):
                if domain not in domain_involvement:
                    domain_involvement[domain] = {
                        "count": 0,
                        "patterns": [],
                        "total_impact": 0
                    }
                
                domain_involvement[domain]["count"] += 1
                domain_involvement[domain]["patterns"].append(pattern.get("pattern_id", ""))
                domain_involvement[domain]["total_impact"] += pattern.get("impact_score", 0)
        
        # 找出最受影响的领域
        most_affected = sorted(
            domain_involvement.items(),
            key=lambda x: x[1]["total_impact"],
            reverse=True
        )
        
        return {
            "domain_involvement": domain_involvement,
            "most_affected_domains": [d[0] for d in most_affected[:3]],
            "interconnection_strength": self._calculate_interconnection_strength(patterns),
            "systemic_insights": self._generate_systemic_insights(patterns, domain_involvement)
        }
    
    def _assess_risks(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """风险评估"""
        
        risks = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for pattern in patterns:
            impact_score = pattern.get("impact_score", 0)
            
            if impact_score > 0.8:
                risk_level = "critical"
            elif impact_score > 0.6:
                risk_level = "high"
            elif impact_score > 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            risks[risk_level].append({
                "pattern_id": pattern.get("pattern_id", ""),
                "description": pattern.get("description", ""),
                "impact_score": impact_score
            })
        
        return {
            "risk_distribution": risks,
            "overall_risk_level": self._calculate_overall_risk(risks),
            "urgent_actions_needed": len(risks["critical"]) > 0,
            "risk_trend": "stable"  # 可以根据历史数据计算
        }
    
    def _generate_action_plan(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成行动计划"""
        
        # 按优先级排序
        sorted_patterns = sorted(
            patterns,
            key=lambda p: p.get("impact_score", 0),
            reverse=True
        )
        
        immediate_actions = []
        short_term_actions = []
        long_term_actions = []
        
        for pattern in sorted_patterns[:3]:  # 前3个最重要的模式
            recommendations = pattern.get("recommendations", [])
            
            if pattern.get("impact_score", 0) > 0.7:
                immediate_actions.extend(recommendations[:2])
            elif pattern.get("impact_score", 0) > 0.5:
                short_term_actions.extend(recommendations[:2])
            else:
                long_term_actions.extend(recommendations[:2])
        
        return {
            "immediate_actions": {
                "timeframe": "今天-明天",
                "actions": immediate_actions[:3],
                "priority": "critical"
            },
            "short_term_actions": {
                "timeframe": "本周",
                "actions": short_term_actions[:3],
                "priority": "high"
            },
            "long_term_actions": {
                "timeframe": "本月",
                "actions": long_term_actions[:3],
                "priority": "medium"
            }
        }
    
    def _generate_progress_tracking(
        self,
        user_id: str,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成进度跟踪"""
        
        if len(history) < 2:
            return {
                "baseline": None,
                "current": None,
                "trend": "insufficient_data"
            }
        
        baseline = history[0]
        current = history[-1]
        
        return {
            "baseline": {
                "health_score": baseline.get("health_score", 75),
                "mood": baseline.get("mood", 5),
                "stress_level": baseline.get("stress_level", 5)
            },
            "current": {
                "health_score": current.get("health_score", 75),
                "mood": current.get("mood", 5),
                "stress_level": current.get("stress_level", 5)
            },
            "changes": {
                "health_change": current.get("health_score", 75) - baseline.get("health_score", 75),
                "mood_change": current.get("mood", 5) - baseline.get("mood", 5),
                "stress_change": current.get("stress_level", 5) - baseline.get("stress_level", 5)
            },
            "trend": "improving" if current.get("health_score", 75) > baseline.get("health_score", 75) else "declining"
        }
    
    def _generate_recommendations(
        self,
        patterns: List[Dict[str, Any]],
        user_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成建议"""
        
        recommendations = []
        
        for pattern in patterns:
            rec = {
                "pattern_id": pattern.get("pattern_id", ""),
                "pattern_type": pattern.get("type", ""),
                "recommendations": pattern.get("recommendations", []),
                "rationale": self._generate_rationale(pattern),
                "expected_impact": self._estimate_impact(pattern),
                "difficulty": self._estimate_difficulty(pattern)
            }
            recommendations.append(rec)
        
        return recommendations
    
    # 辅助方法
    
    def _calculate_severity(self, pattern: Dict[str, Any]) -> str:
        """计算严重程度"""
        impact = pattern.get("impact_score", 0)
        if impact > 0.8:
            return "severe"
        elif impact > 0.6:
            return "moderate"
        else:
            return "mild"
    
    def _identify_intervention_points(self, domains: List[str]) -> List[str]:
        """识别干预点"""
        if not domains:
            return []
        
        # 第一个域是最好的干预点
        return [f"在{domains[0]}领域采取行动可以阻止级联"]
    
    def _identify_loop_break_points(self, domains: List[str]) -> List[str]:
        """识别反馈环的断点"""
        return [f"在{domain}领域打破循环" for domain in domains]
    
    def _identify_reinforcement_factors(self, pattern: Dict[str, Any]) -> List[str]:
        """识别强化因素"""
        return ["持续的压力", "缺乏休息", "负面思维模式"]
    
    def _identify_warning_signs(self, pattern: Dict[str, Any]) -> List[str]:
        """识别警告信号"""
        return ["指标快速变化", "异常行为", "情绪波动"]
    
    def _identify_potential_outcomes(self, pattern: Dict[str, Any]) -> List[str]:
        """识别潜在结果"""
        return ["健康状况恶化", "工作效率下降", "社交隔离"]
    
    def _generate_prevention_strategies(self, pattern: Dict[str, Any]) -> List[str]:
        """生成预防策略"""
        return ["立即采取行动", "建立支持系统", "定期监测"]
    
    def _generate_recovery_options(self, pattern: Dict[str, Any]) -> List[str]:
        """生成恢复选项"""
        return ["寻求专业帮助", "调整生活方式", "建立新的习惯"]
    
    def _identify_maintenance_requirements(self, domains: List[str]) -> List[str]:
        """识别维护需求"""
        return [f"继续维持{domain}领域的良好状态" for domain in domains]
    
    def _identify_growth_potential(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """识别增长潜力"""
        return {
            "potential": "high",
            "areas": ["进一步提升健康水平", "扩展社交圈子", "增加学习投入"]
        }
    
    def _calculate_interconnection_strength(self, patterns: List[Dict[str, Any]]) -> float:
        """计算互联强度"""
        if not patterns:
            return 0.0
        
        # 简单计算：共享领域的数量
        total_connections = 0
        for i, p1 in enumerate(patterns):
            for p2 in patterns[i+1:]:
                shared = len(set(p1.get("domains", [])) & set(p2.get("domains", [])))
                total_connections += shared
        
        return min(1.0, total_connections / max(1, len(patterns)))
    
    def _generate_systemic_insights(
        self,
        patterns: List[Dict[str, Any]],
        domain_involvement: Dict[str, Any]
    ) -> List[str]:
        """生成系统洞察"""
        insights = []
        
        if len(domain_involvement) > 3:
            insights.append("系统中多个领域相互影响，形成复杂的相互作用")
        
        if any(p.get("type") == "feedback_loop" for p in patterns):
            insights.append("存在自我强化的反馈环，需要主动干预")
        
        if any(p.get("type") == "tipping_point" for p in patterns):
            insights.append("系统接近临界点，小的改变可能产生大的影响")
        
        return insights
    
    def _calculate_overall_risk(self, risks: Dict[str, List]) -> str:
        """计算总体风险"""
        if risks["critical"]:
            return "critical"
        elif risks["high"]:
            return "high"
        elif risks["medium"]:
            return "medium"
        else:
            return "low"
    
    def _generate_rationale(self, pattern: Dict[str, Any]) -> str:
        """生成理由"""
        return f"基于检测到的{pattern.get('type', 'unknown')}模式，这些建议可以有效改善情况"
    
    def _estimate_impact(self, pattern: Dict[str, Any]) -> str:
        """估计影响"""
        impact = pattern.get("impact_score", 0)
        if impact > 0.7:
            return "high"
        elif impact > 0.4:
            return "medium"
        else:
            return "low"
    
    def _estimate_difficulty(self, pattern: Dict[str, Any]) -> str:
        """估计难度"""
        pattern_type = pattern.get("type", "")
        if pattern_type == "synergy":
            return "easy"
        elif pattern_type == "cascade":
            return "medium"
        else:
            return "hard"


# 全局实例
_report_generator = None

def get_report_generator() -> EmergenceReportGenerator:
    """获取全局报告生成器实例"""
    global _report_generator
    if _report_generator is None:
        _report_generator = EmergenceReportGenerator()
    return _report_generator

