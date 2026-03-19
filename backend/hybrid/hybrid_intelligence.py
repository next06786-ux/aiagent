"""
混合智能系统
整合LLM、个人模型、知识图谱、强化学习、决策引擎和涌现检测
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from enum import Enum
import json


class HybridIntelligenceMode(Enum):
    """混合智能模式"""
    LLM_ONLY = "llm_only"  # 仅使用LLM
    PERSONAL_MODEL_ONLY = "personal_model_only"  # 仅使用个人模型
    HYBRID = "hybrid"  # 混合模式
    ADAPTIVE = "adaptive"  # 自适应模式


class HybridIntelligenceSystem:
    """混合智能系统"""
    
    def __init__(self, user_id: str):
        """
        初始化混合智能系统
        
        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        
        # 导入各个组件
        from backend.knowledge.automated_kg_builder import get_automated_kg_builder
        from backend.learning.rl_trainer import get_rl_trainer
        from backend.decision.decision_engine import get_decision_engine
        from backend.emergence.emergence_detector import get_emergence_detector
        
        self.kg_builder = get_automated_kg_builder(user_id)
        self.rl_trainer = get_rl_trainer(user_id)
        self.decision_engine = get_decision_engine(user_id)
        self.emergence_detector = get_emergence_detector(user_id)
        
        # 模式选择
        self.current_mode = HybridIntelligenceMode.ADAPTIVE
        
        # 系统统计
        self.system_stats = {
            "total_interactions": 0,
            "kg_entities": 0,
            "rl_episodes": 0,
            "decisions_made": 0,
            "emergences_detected": 0,
            "system_health": 0.5
        }
        
        # 交互历史
        self.interaction_history: List[Dict[str, Any]] = []
    
    def process_user_input(self, user_message: str, user_data: Dict[str, float],
                          llm_response: str = None) -> Dict[str, Any]:
        """
        处理用户输入 - 混合智能处理流程
        
        Args:
            user_message: 用户消息
            user_data: 用户数据
            llm_response: LLM的响应（可选）
        
        Returns:
            处理结果
        """
        result = {
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # 第1步：知识图谱构建
        kg_result = self.kg_builder.build_from_user_data(user_data, user_message)
        result["components"]["knowledge_graph"] = {
            "extracted_entities": kg_result["extracted_entities"],
            "inferred_relations": kg_result["inferred_relations"],
            "entity_count": len(self.kg_builder.entities),
            "relation_count": len(self.kg_builder.relations)
        }
        self.system_stats["kg_entities"] = len(self.kg_builder.entities)
        
        # 第2步：涌现检测
        self.emergence_detector.add_data_point(user_data)
        emergence_events = self.emergence_detector.detect_all_emergences()
        result["components"]["emergence_detection"] = {
            "detected_events": [e.to_dict() for e in emergence_events],
            "event_count": len(emergence_events),
            "statistics": self.emergence_detector.get_emergence_statistics()
        }
        self.system_stats["emergences_detected"] = self.emergence_detector.detection_stats["total_events"]
        
        # 第3步：强化学习预测
        available_actions = ["exercise", "sleep", "meditation", "social", "work"]
        selected_action, selection_method = self.rl_trainer.select_action(user_data, available_actions)
        
        # 预测行动成功概率
        action_success_probs = {}
        for action in available_actions:
            action_success_probs[action] = self.rl_trainer.predict_action_success(user_data, action)
        
        result["components"]["reinforcement_learning"] = {
            "selected_action": selected_action,
            "selection_method": selection_method,
            "action_success_probabilities": action_success_probs,
            "training_episodes": self.rl_trainer.episode_count,
            "average_reward": self.rl_trainer.total_reward / self.rl_trainer.episode_count if self.rl_trainer.episode_count > 0 else 0.0
        }
        self.system_stats["rl_episodes"] = self.rl_trainer.episode_count
        
        # 第4步：决策制定
        kg_data = {
            "causal_chains": self.kg_builder.get_causal_chains(kg_result["extracted_entities"][0] if kg_result["extracted_entities"] else "health", max_depth=2)
        }
        decision = self.decision_engine.make_decision(user_data, kg_data, action_success_probs)
        
        result["components"]["decision_engine"] = {
            "decision": decision.to_dict(),
            "decision_statistics": self.decision_engine.get_decision_statistics()
        }
        self.system_stats["decisions_made"] = self.decision_engine.decision_stats["total_decisions"]
        
        # 第5步：模式选择和融合
        mode = self._select_mode(user_data, emergence_events)
        result["components"]["mode_selection"] = {
            "selected_mode": mode.value,
            "reasoning": self._get_mode_reasoning(mode, emergence_events)
        }
        
        # 第6步：生成最终建议
        final_recommendation = self._generate_final_recommendation(
            user_message,
            decision,
            llm_response,
            mode,
            emergence_events
        )
        
        result["final_recommendation"] = final_recommendation
        
        # 更新统计
        self.system_stats["total_interactions"] += 1
        self.system_stats["system_health"] = self._calculate_system_health()
        
        # 记录交互
        self.interaction_history.append(result)
        
        return result
    
    def _select_mode(self, user_data: Dict[str, float], 
                    emergence_events: List[Any]) -> HybridIntelligenceMode:
        """
        选择混合智能模式
        
        Args:
            user_data: 用户数据
            emergence_events: 涌现事件
        
        Returns:
            选择的模式
        """
        # 如果检测到复杂的涌现现象，使用混合模式
        if len(emergence_events) > 3:
            return HybridIntelligenceMode.HYBRID
        
        # 如果用户数据完整且有足够的历史数据，使用个人模型
        if len(user_data) > 5 and self.rl_trainer.episode_count > 10:
            return HybridIntelligenceMode.PERSONAL_MODEL_ONLY
        
        # 否则使用自适应模式
        return HybridIntelligenceMode.ADAPTIVE
    
    def _get_mode_reasoning(self, mode: HybridIntelligenceMode, 
                           emergence_events: List[Any]) -> str:
        """
        获取模式选择的推理
        
        Args:
            mode: 选择的模式
            emergence_events: 涌现事件
        
        Returns:
            推理说明
        """
        if mode == HybridIntelligenceMode.HYBRID:
            return f"检测到{len(emergence_events)}个复杂涌现现象，使用混合模式以获得最佳决策"
        elif mode == HybridIntelligenceMode.PERSONAL_MODEL_ONLY:
            return "用户数据充分，个人模型已充分训练，使用个人模型模式"
        else:
            return "使用自适应模式，根据实时情况调整策略"
    
    def _generate_final_recommendation(self, user_message: str, decision: Any,
                                      llm_response: str, mode: HybridIntelligenceMode,
                                      emergence_events: List[Any]) -> Dict[str, Any]:
        """
        生成最终建议
        
        Args:
            user_message: 用户消息
            decision: 决策对象
            llm_response: LLM响应
            mode: 选择的模式
            emergence_events: 涌现事件
        
        Returns:
            最终建议
        """
        recommendation = {
            "primary_action": decision.recommendation,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence,
            "expected_impact": decision.expected_impact,
            "mode": mode.value
        }
        
        # 如果有涌现事件，添加到建议中
        if emergence_events:
            recommendation["emergence_insights"] = [
                {
                    "type": e.emergence_type.value,
                    "description": e.description,
                    "strength": e.strength
                }
                for e in emergence_events[:3]
            ]
        
        # 如果有LLM响应，融合到建议中
        if llm_response:
            recommendation["llm_insights"] = llm_response
        
        return recommendation
    
    def _calculate_system_health(self) -> float:
        """
        计算系统健康度
        
        Returns:
            健康度（0-1）
        """
        # 基于各个组件的性能计算
        kg_health = min(len(self.kg_builder.entities) / 100, 1.0)
        rl_health = min(self.rl_trainer.total_reward / 10, 1.0) if self.rl_trainer.episode_count > 0 else 0.5
        decision_health = self.decision_engine.decision_stats["success_rate"]
        emergence_health = min(self.emergence_detector.detection_stats["total_events"] / 20, 1.0)
        
        # 加权平均
        health = (kg_health * 0.25 + rl_health * 0.25 + decision_health * 0.25 + emergence_health * 0.25)
        
        return health
    
    def get_system_overview(self) -> Dict[str, Any]:
        """
        获取系统概览
        
        Returns:
            系统概览
        """
        return {
            "user_id": self.user_id,
            "current_mode": self.current_mode.value,
            "system_health": self.system_stats["system_health"],
            "statistics": {
                "total_interactions": self.system_stats["total_interactions"],
                "kg_entities": self.system_stats["kg_entities"],
                "rl_episodes": self.system_stats["rl_episodes"],
                "decisions_made": self.system_stats["decisions_made"],
                "emergences_detected": self.system_stats["emergences_detected"]
            },
            "component_status": {
                "knowledge_graph": {
                    "entity_count": len(self.kg_builder.entities),
                    "relation_count": len(self.kg_builder.relations)
                },
                "reinforcement_learning": {
                    "episodes": self.rl_trainer.episode_count,
                    "average_reward": self.rl_trainer.total_reward / self.rl_trainer.episode_count if self.rl_trainer.episode_count > 0 else 0.0
                },
                "decision_engine": {
                    "total_decisions": self.decision_engine.decision_stats["total_decisions"],
                    "success_rate": self.decision_engine.decision_stats["success_rate"]
                },
                "emergence_detection": {
                    "total_events": self.emergence_detector.detection_stats["total_events"]
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def export_system_state(self) -> Dict[str, Any]:
        """
        导出系统状态
        
        Returns:
            系统状态数据
        """
        return {
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "overview": self.get_system_overview(),
            "knowledge_graph": self.kg_builder.export_graph(),
            "reinforcement_learning": self.rl_trainer.export_model(),
            "decisions": self.decision_engine.export_decisions(),
            "emergence": self.emergence_detector.export_emergence_data(),
            "interaction_history": self.interaction_history[-10:]  # 最近10次交互
        }


def get_hybrid_intelligence_system(user_id: str) -> HybridIntelligenceSystem:
    """获取混合智能系统实例"""
    return HybridIntelligenceSystem(user_id)

