"""
决策层系统
基于真实数据和知识图谱的决策支持
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import math


class DecisionType(Enum):
    """决策类型"""
    IMMEDIATE = "immediate"  # 立即行动
    PLANNED = "planned"  # 计划行动
    PREVENTIVE = "preventive"  # 预防性行动
    CORRECTIVE = "corrective"  # 纠正性行动
    OPTIMIZATION = "optimization"  # 优化性行动


class DecisionConfidence(Enum):
    """决策置信度"""
    VERY_HIGH = 0.9
    HIGH = 0.7
    MEDIUM = 0.5
    LOW = 0.3
    VERY_LOW = 0.1


class Decision:
    """决策"""
    
    def __init__(self, decision_id: str, decision_type: DecisionType,
                 recommendation: str, reasoning: str, confidence: float,
                 target_metrics: Dict[str, float], expected_impact: Dict[str, float]):
        """
        初始化决策
        
        Args:
            decision_id: 决策ID
            decision_type: 决策类型
            recommendation: 推荐内容
            reasoning: 推理过程
            confidence: 置信度
            target_metrics: 目标指标
            expected_impact: 预期影响
        """
        self.decision_id = decision_id
        self.decision_type = decision_type
        self.recommendation = recommendation
        self.reasoning = reasoning
        self.confidence = confidence
        self.target_metrics = target_metrics
        self.expected_impact = expected_impact
        self.created_at = datetime.now()
        self.user_feedback = None
        self.actual_impact = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "recommendation": self.recommendation,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "target_metrics": self.target_metrics,
            "expected_impact": self.expected_impact,
            "created_at": self.created_at.isoformat(),
            "user_feedback": self.user_feedback,
            "actual_impact": self.actual_impact
        }


class DecisionEngine:
    """决策引擎"""
    
    def __init__(self, user_id: str):
        """
        初始化决策引擎
        
        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        self.decisions: Dict[str, Decision] = {}
        self.decision_history: List[Decision] = []
        
        # 决策规则库
        self.decision_rules = self._initialize_decision_rules()
        
        # 决策统计
        self.decision_stats = {
            "total_decisions": 0,
            "accepted_decisions": 0,
            "rejected_decisions": 0,
            "pending_decisions": 0,
            "average_confidence": 0.0,
            "success_rate": 0.0
        }
    
    def _initialize_decision_rules(self) -> Dict[str, Any]:
        """初始化决策规则"""
        return {
            "health": {
                "sleep_hours": {
                    "low": {
                        "threshold": 6,
                        "decision_type": DecisionType.IMMEDIATE,
                        "recommendation": "增加睡眠时间",
                        "actions": ["早睡", "减少夜间活动", "改善睡眠环境"],
                        "expected_impact": {"health_score": 0.15, "mood": 0.1, "stress_level": -0.2}
                    },
                    "high": {
                        "threshold": 9,
                        "decision_type": DecisionType.OPTIMIZATION,
                        "recommendation": "优化睡眠质量",
                        "actions": ["调整睡眠时间", "改善睡眠环境"],
                        "expected_impact": {"health_score": 0.05, "mood": 0.05}
                    }
                },
                "stress_level": {
                    "high": {
                        "threshold": 7,
                        "decision_type": DecisionType.PREVENTIVE,
                        "recommendation": "进行压力管理",
                        "actions": ["冥想", "运动", "社交活动"],
                        "expected_impact": {"stress_level": -0.3, "mood": 0.2, "health_score": 0.1}
                    }
                },
                "exercise_minutes": {
                    "low": {
                        "threshold": 30,
                        "decision_type": DecisionType.PLANNED,
                        "recommendation": "增加运动量",
                        "actions": ["散步", "跑步", "健身房"],
                        "expected_impact": {"health_score": 0.2, "stress_level": -0.15, "mood": 0.15}
                    }
                }
            },
            "time": {
                "work_hours": {
                    "high": {
                        "threshold": 10,
                        "decision_type": DecisionType.CORRECTIVE,
                        "recommendation": "减少工作时间",
                        "actions": ["优化工作流程", "委派任务", "休息"],
                        "expected_impact": {"stress_level": -0.2, "efficiency_score": 0.1}
                    }
                },
                "focus_time": {
                    "low": {
                        "threshold": 4,
                        "decision_type": DecisionType.OPTIMIZATION,
                        "recommendation": "改善专注力",
                        "actions": ["番茄工作法", "减少干扰", "冥想"],
                        "expected_impact": {"efficiency_score": 0.25, "task_completion_rate": 0.2}
                    }
                }
            },
            "emotion": {
                "mood": {
                    "low": {
                        "threshold": 4,
                        "decision_type": DecisionType.IMMEDIATE,
                        "recommendation": "改善心情",
                        "actions": ["社交活动", "户外活动", "爱好活动"],
                        "expected_impact": {"mood": 0.3, "health_score": 0.1}
                    }
                },
                "anxiety_level": {
                    "high": {
                        "threshold": 7,
                        "decision_type": DecisionType.PREVENTIVE,
                        "recommendation": "缓解焦虑",
                        "actions": ["深呼吸", "冥想", "寻求支持"],
                        "expected_impact": {"anxiety_level": -0.3, "mood": 0.2}
                    }
                }
            }
        }
    
    def make_decision(self, user_data: Dict[str, float], 
                     knowledge_graph_data: Dict[str, Any] = None,
                     rl_predictions: Dict[str, float] = None) -> Decision:
        """
        做出决策
        
        Args:
            user_data: 用户数据
            knowledge_graph_data: 知识图谱数据
            rl_predictions: 强化学习预测
        
        Returns:
            决策对象
        """
        # 分析用户数据
        analysis = self._analyze_user_data(user_data)
        
        # 应用决策规则
        applicable_rules = self._apply_decision_rules(analysis)
        
        # 综合知识图谱信息
        if knowledge_graph_data:
            applicable_rules = self._enhance_with_kg(applicable_rules, knowledge_graph_data)
        
        # 综合强化学习预测
        if rl_predictions:
            applicable_rules = self._enhance_with_rl(applicable_rules, rl_predictions)
        
        # 选择最优决策
        best_decision = self._select_best_decision(applicable_rules, user_data)
        
        # 记录决策
        self.decisions[best_decision.decision_id] = best_decision
        self.decision_history.append(best_decision)
        
        # 更新统计
        self.decision_stats["total_decisions"] += 1
        self.decision_stats["pending_decisions"] += 1
        
        return best_decision
    
    def _analyze_user_data(self, user_data: Dict[str, float]) -> Dict[str, Any]:
        """
        分析用户数据
        
        Args:
            user_data: 用户数据
        
        Returns:
            分析结果
        """
        analysis = {
            "critical_issues": [],
            "warnings": [],
            "opportunities": []
        }
        
        # 检查关键问题
        if user_data.get("sleep_hours", 0) < 6:
            analysis["critical_issues"].append({
                "metric": "sleep_hours",
                "value": user_data.get("sleep_hours"),
                "severity": "high"
            })
        
        if user_data.get("stress_level", 0) > 7:
            analysis["critical_issues"].append({
                "metric": "stress_level",
                "value": user_data.get("stress_level"),
                "severity": "high"
            })
        
        # 检查警告
        if user_data.get("exercise_minutes", 0) < 30:
            analysis["warnings"].append({
                "metric": "exercise_minutes",
                "value": user_data.get("exercise_minutes"),
                "severity": "medium"
            })
        
        if user_data.get("mood", 0) < 5:
            analysis["warnings"].append({
                "metric": "mood",
                "value": user_data.get("mood"),
                "severity": "medium"
            })
        
        # 检查机会
        if user_data.get("health_score", 0) > 70:
            analysis["opportunities"].append({
                "metric": "health_score",
                "value": user_data.get("health_score"),
                "opportunity": "进一步优化健康"
            })
        
        return analysis
    
    def _apply_decision_rules(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        应用决策规则
        
        Args:
            analysis: 分析结果
        
        Returns:
            适用的规则列表
        """
        applicable_rules = []
        
        # 处理关键问题
        for issue in analysis["critical_issues"]:
            metric = issue["metric"]
            
            # 查找对应的规则
            for domain, metrics in self.decision_rules.items():
                if metric in metrics:
                    for condition, rule in metrics[metric].items():
                        applicable_rules.append({
                            "metric": metric,
                            "condition": condition,
                            "rule": rule,
                            "priority": "high",
                            "confidence": 0.8
                        })
        
        # 处理警告
        for warning in analysis["warnings"]:
            metric = warning["metric"]
            
            for domain, metrics in self.decision_rules.items():
                if metric in metrics:
                    for condition, rule in metrics[metric].items():
                        applicable_rules.append({
                            "metric": metric,
                            "condition": condition,
                            "rule": rule,
                            "priority": "medium",
                            "confidence": 0.6
                        })
        
        return applicable_rules
    
    def _enhance_with_kg(self, rules: List[Dict[str, Any]], 
                        kg_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        用知识图谱增强规则
        
        Args:
            rules: 规则列表
            kg_data: 知识图谱数据
        
        Returns:
            增强后的规则列表
        """
        # 根据知识图谱中的关系调整置信度
        for rule in rules:
            # 如果知识图谱中有相关的因果关系，增加置信度
            if kg_data.get("causal_chains"):
                rule["confidence"] = min(rule["confidence"] + 0.1, 1.0)
        
        return rules
    
    def _enhance_with_rl(self, rules: List[Dict[str, Any]], 
                        rl_predictions: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        用强化学习预测增强规则
        
        Args:
            rules: 规则列表
            rl_predictions: 强化学习预测
        
        Returns:
            增强后的规则列表
        """
        # 根据强化学习预测调整置信度
        for rule in rules:
            action = rule["rule"].get("actions", [None])[0]
            if action and action in rl_predictions:
                success_prob = rl_predictions[action]
                rule["confidence"] = rule["confidence"] * success_prob
        
        return rules
    
    def _select_best_decision(self, rules: List[Dict[str, Any]], 
                             user_data: Dict[str, float]) -> Decision:
        """
        选择最优决策
        
        Args:
            rules: 规则列表
            user_data: 用户数据
        
        Returns:
            最优决策
        """
        if not rules:
            # 如果没有适用的规则，返回一个通用的优化建议
            decision_id = f"dec_{datetime.now().timestamp()}"
            return Decision(
                decision_id=decision_id,
                decision_type=DecisionType.OPTIMIZATION,
                recommendation="保持当前生活方式，继续监测各项指标",
                reasoning="用户各项指标均在正常范围内",
                confidence=0.5,
                target_metrics={},
                expected_impact={}
            )
        
        # 选择置信度最高的规则
        best_rule = max(rules, key=lambda r: r["confidence"])
        
        decision_id = f"dec_{datetime.now().timestamp()}"
        rule_data = best_rule["rule"]
        
        return Decision(
            decision_id=decision_id,
            decision_type=rule_data["decision_type"],
            recommendation=rule_data["recommendation"],
            reasoning=f"基于{best_rule['metric']}的分析：{best_rule['condition']}",
            confidence=best_rule["confidence"],
            target_metrics={best_rule["metric"]: user_data.get(best_rule["metric"], 0)},
            expected_impact=rule_data["expected_impact"]
        )
    
    def record_decision_feedback(self, decision_id: str, feedback: Dict[str, Any]):
        """
        记录决策反馈
        
        Args:
            decision_id: 决策ID
            feedback: 反馈信息
        """
        if decision_id in self.decisions:
            decision = self.decisions[decision_id]
            decision.user_feedback = feedback.get("feedback", "")
            decision.actual_impact = feedback.get("actual_impact", {})
            
            # 更新统计
            if feedback.get("accepted", False):
                self.decision_stats["accepted_decisions"] += 1
            else:
                self.decision_stats["rejected_decisions"] += 1
            
            self.decision_stats["pending_decisions"] -= 1
            
            # 计算成功率
            if self.decision_stats["accepted_decisions"] + self.decision_stats["rejected_decisions"] > 0:
                self.decision_stats["success_rate"] = (
                    self.decision_stats["accepted_decisions"] / 
                    (self.decision_stats["accepted_decisions"] + self.decision_stats["rejected_decisions"])
                )
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """
        获取决策统计
        
        Returns:
            统计信息
        """
        return {
            "total_decisions": self.decision_stats["total_decisions"],
            "accepted_decisions": self.decision_stats["accepted_decisions"],
            "rejected_decisions": self.decision_stats["rejected_decisions"],
            "pending_decisions": self.decision_stats["pending_decisions"],
            "success_rate": self.decision_stats["success_rate"],
            "average_confidence": sum(d.confidence for d in self.decision_history) / len(self.decision_history) if self.decision_history else 0.0
        }
    
    def get_recent_decisions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近的决策
        
        Args:
            limit: 限制数量
        
        Returns:
            决策列表
        """
        return [d.to_dict() for d in self.decision_history[-limit:]]
    
    def export_decisions(self) -> Dict[str, Any]:
        """
        导出决策
        
        Returns:
            决策数据
        """
        return {
            "user_id": self.user_id,
            "decisions": [d.to_dict() for d in self.decision_history],
            "statistics": self.get_decision_statistics(),
            "exported_at": datetime.now().isoformat()
        }


def get_decision_engine(user_id: str) -> DecisionEngine:
    """获取决策引擎实例"""
    return DecisionEngine(user_id)

