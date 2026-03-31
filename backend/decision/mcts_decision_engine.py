# -*- coding: utf-8 -*-
"""
MCTS-PD: 基于蒙特卡洛树搜索的个性化决策推演引擎

核心思想：
- 每个月生成多个候选事件（扩展），用个性化价值函数评估（评估），
  选最优作为主链、次优作为分支（选择），逐月推进（回溯）。
- LoRA 个性化模型作为策略网络，知识图谱和 RAG 记忆作为约束条件。
- 用户反馈实时调整节点先验概率（在线学习）。

参考：
- MCTS: Browne et al., "A Survey of Monte Carlo Tree Search Methods", 2012
- LLM-ABMS: Gao et al., "LLM Empowered Agent-based Modeling and Simulation", 2024
- GenSim: Tang et al., "GenSim: A General Social Simulation Platform", NAACL 2025
"""
import math
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MCTSNode:
    """MCTS 树节点"""
    node_id: str
    month: int
    event: str
    impact: Dict[str, float]
    probability: float
    prior: float = 1.0          # 先验概率（受反馈调整）
    visit_count: int = 0
    total_value: float = 0.0
    children: list = field(default_factory=list)
    parent_id: Optional[str] = None
    is_branch: bool = False

    @property
    def avg_value(self) -> float:
        return self.total_value / max(self.visit_count, 1)

    def ucb1(self, parent_visits: int, exploration: float = 1.4) -> float:
        if self.visit_count == 0:
            return float('inf')
        exploit = self.avg_value
        explore = exploration * math.sqrt(math.log(parent_visits) / self.visit_count)
        return (exploit + explore) * self.prior

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "month": self.month,
            "event": self.event,
            "impact": self.impact,
            "probability": self.probability,
            "prior": round(self.prior, 3),
            "visit_count": self.visit_count,
            "avg_value": round(self.avg_value, 3),
            "is_branch": self.is_branch,
            "parent_id": self.parent_id,
            "children_count": len(self.children)
        }
