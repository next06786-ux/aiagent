"""
强化学习真实训练系统
基于用户反馈的真实强化学习训练
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from enum import Enum
import json
import random
import math


class FeedbackType(Enum):
    """反馈类型"""
    ADOPTED = "adopted"  # 用户采纳了建议
    HELPFUL = "helpful"  # 用户反馈有帮助
    NEUTRAL = "neutral"  # 用户反馈中立
    UNHELPFUL = "unhelpful"  # 用户反馈无帮助
    HARMFUL = "harmful"  # 用户反馈有害


class ReinforcementLearningTrainer:
    """强化学习训练器"""
    
    def __init__(self, user_id: str):
        """
        初始化训练器
        
        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        
        # Q-Learning参数
        self.q_table: Dict[str, Dict[str, float]] = {}  # 状态-行动-价值表
        self.learning_rate = 0.1  # 学习率
        self.discount_factor = 0.95  # 折扣因子
        self.epsilon = 0.1  # 探索率
        
        # 奖励函数定义
        self.reward_mapping = {
            FeedbackType.ADOPTED: 1.0,
            FeedbackType.HELPFUL: 0.8,
            FeedbackType.NEUTRAL: 0.3,
            FeedbackType.UNHELPFUL: -0.3,
            FeedbackType.HARMFUL: -1.0
        }
        
        # 训练历史
        self.training_history: List[Dict[str, Any]] = []
        self.episode_count = 0
        self.total_reward = 0.0
        
        # 策略统计
        self.strategy_stats = {
            "llm_only": {"count": 0, "total_reward": 0.0, "avg_reward": 0.0},
            "personal_model_only": {"count": 0, "total_reward": 0.0, "avg_reward": 0.0},
            "hybrid": {"count": 0, "total_reward": 0.0, "avg_reward": 0.0}
        }
        
        # 推荐统计
        self.recommendation_stats = {
            "exercise": {"count": 0, "adopted": 0, "success_rate": 0.0},
            "sleep": {"count": 0, "adopted": 0, "success_rate": 0.0},
            "meditation": {"count": 0, "adopted": 0, "success_rate": 0.0},
            "social": {"count": 0, "adopted": 0, "success_rate": 0.0},
            "work": {"count": 0, "adopted": 0, "success_rate": 0.0}
        }
    
    def record_interaction(self, state: Dict[str, float], action: str, 
                          feedback_type: FeedbackType, strategy: str = "hybrid") -> Dict[str, Any]:
        """
        记录一次交互
        
        Args:
            state: 状态（用户的各项指标）
            action: 行动（推荐的行动）
            feedback_type: 反馈类型
            strategy: 使用的策略
        
        Returns:
            训练结果
        """
        # 获取奖励
        reward = self.reward_mapping.get(feedback_type, 0.0)
        
        # 转换状态为字符串（用于Q表）
        state_key = self._state_to_key(state)
        
        # 初始化Q表中的状态
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        
        # 初始化Q表中的行动
        if action not in self.q_table[state_key]:
            self.q_table[state_key][action] = 0.0
        
        # 更新Q值
        old_q_value = self.q_table[state_key][action]
        
        # 获取下一个状态的最大Q值（简化：假设下一个状态的最大Q值为0）
        max_next_q = 0.0
        
        # Q-Learning更新公式
        new_q_value = old_q_value + self.learning_rate * (reward + self.discount_factor * max_next_q - old_q_value)
        self.q_table[state_key][action] = new_q_value
        
        # 更新统计信息
        self.episode_count += 1
        self.total_reward += reward
        
        # 更新策略统计
        if strategy in self.strategy_stats:
            self.strategy_stats[strategy]["count"] += 1
            self.strategy_stats[strategy]["total_reward"] += reward
            self.strategy_stats[strategy]["avg_reward"] = (
                self.strategy_stats[strategy]["total_reward"] / self.strategy_stats[strategy]["count"]
            )
        
        # 更新推荐统计
        if action in self.recommendation_stats:
            self.recommendation_stats[action]["count"] += 1
            if feedback_type == FeedbackType.ADOPTED:
                self.recommendation_stats[action]["adopted"] += 1
            self.recommendation_stats[action]["success_rate"] = (
                self.recommendation_stats[action]["adopted"] / self.recommendation_stats[action]["count"]
            )
        
        # 记录训练历史
        history_entry = {
            "episode": self.episode_count,
            "state": state,
            "action": action,
            "feedback_type": feedback_type.value,
            "reward": reward,
            "strategy": strategy,
            "old_q_value": old_q_value,
            "new_q_value": new_q_value,
            "timestamp": datetime.now().isoformat()
        }
        self.training_history.append(history_entry)
        
        return {
            "episode": self.episode_count,
            "reward": reward,
            "q_value_change": new_q_value - old_q_value,
            "total_reward": self.total_reward,
            "average_reward": self.total_reward / self.episode_count
        }
    
    def select_action(self, state: Dict[str, float], available_actions: List[str]) -> Tuple[str, str]:
        """
        选择行动（使用epsilon-greedy策略）
        
        Args:
            state: 状态
            available_actions: 可用的行动列表
        
        Returns:
            (选择的行动, 选择方式)
        """
        state_key = self._state_to_key(state)
        
        # 初始化状态
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        
        # 初始化所有行动的Q值
        for action in available_actions:
            if action not in self.q_table[state_key]:
                self.q_table[state_key][action] = 0.0
        
        # Epsilon-greedy策略
        if random.random() < self.epsilon:
            # 探索：随机选择
            action = random.choice(available_actions)
            selection_method = "exploration"
        else:
            # 利用：选择Q值最高的行动
            action = max(available_actions, key=lambda a: self.q_table[state_key].get(a, 0.0))
            selection_method = "exploitation"
        
        return action, selection_method
    
    def get_best_policy(self) -> Dict[str, str]:
        """
        获取最优策略
        
        Returns:
            状态到最优行动的映射
        """
        policy = {}
        
        for state_key, actions in self.q_table.items():
            if actions:
                best_action = max(actions.items(), key=lambda x: x[1])[0]
                policy[state_key] = best_action
        
        return policy
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """
        获取训练统计信息
        
        Returns:
            统计信息
        """
        return {
            "total_episodes": self.episode_count,
            "total_reward": self.total_reward,
            "average_reward": self.total_reward / self.episode_count if self.episode_count > 0 else 0.0,
            "q_table_size": len(self.q_table),
            "strategy_stats": self.strategy_stats,
            "recommendation_stats": self.recommendation_stats,
            "best_strategy": max(
                self.strategy_stats.items(),
                key=lambda x: x[1]["avg_reward"]
            )[0] if self.strategy_stats else None,
            "best_recommendation": max(
                self.recommendation_stats.items(),
                key=lambda x: x[1]["success_rate"]
            )[0] if self.recommendation_stats else None
        }
    
    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的训练历史
        
        Args:
            limit: 限制数量
        
        Returns:
            训练历史列表
        """
        return self.training_history[-limit:]
    
    def evaluate_strategy_performance(self) -> Dict[str, Any]:
        """
        评估策略性能
        
        Returns:
            性能评估
        """
        evaluation = {}
        
        for strategy, stats in self.strategy_stats.items():
            if stats["count"] > 0:
                evaluation[strategy] = {
                    "usage_count": stats["count"],
                    "average_reward": stats["avg_reward"],
                    "total_reward": stats["total_reward"],
                    "usage_percentage": stats["count"] / self.episode_count * 100 if self.episode_count > 0 else 0
                }
        
        return evaluation
    
    def evaluate_recommendation_performance(self) -> Dict[str, Any]:
        """
        评估推荐性能
        
        Returns:
            性能评估
        """
        evaluation = {}
        
        for action, stats in self.recommendation_stats.items():
            if stats["count"] > 0:
                evaluation[action] = {
                    "recommendation_count": stats["count"],
                    "adoption_count": stats["adopted"],
                    "success_rate": stats["success_rate"],
                    "adoption_rate": stats["adopted"] / stats["count"]
                }
        
        return evaluation
    
    def predict_action_success(self, state: Dict[str, float], action: str) -> float:
        """
        预测行动的成功概率
        
        Args:
            state: 状态
            action: 行动
        
        Returns:
            成功概率（0-1）
        """
        state_key = self._state_to_key(state)
        
        # 获取Q值
        q_value = self.q_table.get(state_key, {}).get(action, 0.0)
        
        # 使用sigmoid函数将Q值转换为概率
        probability = 1 / (1 + math.exp(-q_value))
        
        return probability
    
    def export_model(self) -> Dict[str, Any]:
        """
        导出模型
        
        Returns:
            模型数据
        """
        return {
            "user_id": self.user_id,
            "q_table": self.q_table,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "epsilon": self.epsilon,
            "episode_count": self.episode_count,
            "total_reward": self.total_reward,
            "strategy_stats": self.strategy_stats,
            "recommendation_stats": self.recommendation_stats,
            "exported_at": datetime.now().isoformat()
        }
    
    def _state_to_key(self, state: Dict[str, float]) -> str:
        """
        将状态转换为字符串键
        
        Args:
            state: 状态字典
        
        Returns:
            状态键
        """
        # 将状态值离散化为区间
        discretized = {}
        for key, value in state.items():
            # 将值分为5个区间
            interval = int(value / 20) if value >= 0 else 0
            discretized[key] = min(interval, 4)  # 最多5个区间
        
        # 转换为字符串
        return json.dumps(discretized, sort_keys=True)


class AdaptiveRewardFunction:
    """自适应奖励函数"""
    
    def __init__(self):
        """初始化自适应奖励函数"""
        self.base_rewards = {
            FeedbackType.ADOPTED: 1.0,
            FeedbackType.HELPFUL: 0.8,
            FeedbackType.NEUTRAL: 0.3,
            FeedbackType.UNHELPFUL: -0.3,
            FeedbackType.HARMFUL: -1.0
        }
        self.adjustment_factors = {}
    
    def calculate_reward(self, feedback_type: FeedbackType, context: Dict[str, Any] = None) -> float:
        """
        计算奖励
        
        Args:
            feedback_type: 反馈类型
            context: 上下文信息
        
        Returns:
            奖励值
        """
        base_reward = self.base_rewards.get(feedback_type, 0.0)
        
        # 根据上下文调整奖励
        if context:
            adjustment = self._calculate_adjustment(context)
            return base_reward * (1 + adjustment)
        
        return base_reward
    
    def _calculate_adjustment(self, context: Dict[str, Any]) -> float:
        """
        计算奖励调整因子
        
        Args:
            context: 上下文信息
        
        Returns:
            调整因子
        """
        adjustment = 0.0
        
        # 如果用户长期采纳某个推荐，增加奖励
        if context.get("adoption_streak", 0) > 3:
            adjustment += 0.1
        
        # 如果推荐与用户的目标一致，增加奖励
        if context.get("goal_aligned", False):
            adjustment += 0.15
        
        # 如果推荐的效果显著，增加奖励
        if context.get("impact_score", 0) > 0.7:
            adjustment += 0.2
        
        return adjustment


def get_rl_trainer(user_id: str) -> ReinforcementLearningTrainer:
    """获取强化学习训练器实例"""
    return ReinforcementLearningTrainer(user_id)

