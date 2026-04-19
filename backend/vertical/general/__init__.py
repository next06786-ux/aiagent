"""
通用决策推演垂直领域

提供通用的决策推演引擎，适用于不特定于职业、教育、人际关系的决策场景
"""

from backend.vertical.general.general_decision_engine import (
    GeneralDecisionEngine,
    GeneralDecisionContext,
)

__all__ = [
    "GeneralDecisionEngine",
    "GeneralDecisionContext",
]
