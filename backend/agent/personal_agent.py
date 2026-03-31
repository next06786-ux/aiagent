# -*- coding: utf-8 -*-
"""
个性化决策 Agent

参考 LLM-empowered ABMS 框架（Gao et al., 2024），
将用户建模为一个具有感知、记忆、推理、行动四层能力的 LLM Agent。

架构：
  感知层（Perception）：多模态输入（文字/语音/图片）+ 对话分析
  记忆层（Memory）：RAG 向量记忆 + Neo4j 知识图谱 + 对话历史
  推理层（Reasoning）：LoRA 个性化微调模型 + 决策推演引擎
  行动层（Action）：时间线生成 + 建议输出 + 反馈纠错
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class AgentState:
    """Agent 当前状态快照"""
    user_id: str
    # 感知层状态
    last_input_type: str = "none"  # text / voice / image
    last_input_time: Optional[str] = None
    # 记忆层状态
    memory_count: int = 0
    kg_node_count: int = 0
    kg_relation_count: int = 0
    # 推理层状态
    has_lora: bool = False
    lora_version: int = 0
    decision_style: str = "unknown"
    risk_preference: str = "unknown"
    # 行动层状态
    total_simulations: int = 0
    total_feedbacks: int = 0
    # 游戏数据
    game_chapters_played: int = 0
    game_choices_made: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "perception": {
                "last_input_type": self.last_input_type,
                "last_input_time": self.last_input_time,
            },
            "memory": {
                "memory_count": self.memory_count,
                "kg_nodes": self.kg_node_count,
                "kg_relations": self.kg_relation_count,
            },
            "reasoning": {
                "has_lora": self.has_lora,
                "lora_version": self.lora_version,
                "decision_style": self.decision_style,
                "risk_preference": self.risk_preference,
            },
            "action": {
                "total_simulations": self.total_simulations,
                "total_feedbacks": self.total_feedbacks,
            },
            "game": {
                "chapters_played": self.game_chapters_played,
                "choices_made": self.game_choices_made,
            }
        }


class PersonalDecisionAgent:
    """
    个性化决策 Agent
    整合感知、记忆、推理、行动四层能力
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.state = AgentState(user_id=user_id)

    def refresh_state(self) -> AgentState:
        """刷新 Agent 状态（从各子系统收集最新信息）"""
        # 记忆层
        try:
            from backend.learning.unified_rag_system import MemorySystemManager
            rag = MemorySystemManager.get_system(self.user_id)
            stats = rag.get_memory_statistics()
            self.state.memory_count = stats.get("total_memories", 0)
        except Exception:
            pass

        # 知识图谱
        try:
            from backend.knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph
            with Neo4jKnowledgeGraph(self.user_id) as kg:
                kg_stats = kg.get_statistics()
                self.state.kg_node_count = kg_stats.get("total_nodes", 0)
                self.state.kg_relation_count = kg_stats.get("total_relations", 0)
        except Exception:
            pass

        # LoRA 状态
        try:
            from backend.lora.lora_model_manager import lora_manager
            self.state.has_lora = lora_manager.has_lora_model(self.user_id)
            info = lora_manager.get_model_info(self.user_id)
            self.state.lora_version = info.get("version", 0)
        except Exception:
            pass

        # 决策风格（从 profile）
        try:
            from backend.personality.personality_test import PersonalityTest
            pt = PersonalityTest()
            profile = pt.load_profile(self.user_id)
            if profile:
                self.state.decision_style = getattr(profile, 'decision_style', 'unknown')
                self.state.risk_preference = getattr(profile, 'risk_preference', 'unknown')
        except Exception:
            pass

        return self.state


# 全局 Agent 实例缓存
_agents: Dict[str, PersonalDecisionAgent] = {}


def get_personal_agent(user_id: str) -> PersonalDecisionAgent:
    if user_id not in _agents:
        _agents[user_id] = PersonalDecisionAgent(user_id)
    return _agents[user_id]
