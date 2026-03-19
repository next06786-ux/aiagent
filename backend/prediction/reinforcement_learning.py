"""
强化学习优化模块 - Phase 2.6
实现Q-learning、策略梯度、奖励函数、模型评估
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
from collections import defaultdict


class ActionType(Enum):
    """行动类型"""
    HEALTH_EXERCISE = "health_exercise"  # 运动
    HEALTH_SLEEP = "health_sleep"  # 睡眠
    HEALTH_NUTRITION = "health_nutrition"  # 营养
    TIME_FOCUS = "time_focus"  # 专注工作
    TIME_BREAK = "time_break"  # 休息
    EMOTION_RELAX = "emotion_relax"  # 放松
    EMOTION_SOCIAL = "emotion_social"  # 社交
    LEARNING_STUDY = "learning_study"  # 学习
    LEARNING_REVIEW = "learning_review"  # 复习


@dataclass
class State:
    """状态"""
    state_id: str
    features: Dict[str, float]  # 状态特征
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Transition:
    """转移"""
    state: State
    action: ActionType
    reward: float
    next_state: State
    done: bool


@dataclass
class QValue:
    """Q值"""
    state_id: str
    action: ActionType
    q_value: float
    visit_count: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class RewardFunction:
    """奖励函数"""
    
    def __init__(self):
        self.weights = {
            "health_score": 0.3,
            "mood": 0.2,
            "efficiency": 0.2,
            "social_satisfaction": 0.15,
            "learning_progress": 0.15
        }
    
    def calculate_reward(
        self,
        current_state: Dict[str, float],
        next_state: Dict[str, float],
        action: ActionType
    ) -> float:
        """
        计算奖励
        基于状态变化和行动类型
        """
        reward = 0.0
        
        # 1. 基础奖励（根据行动类型）
        action_rewards = {
            ActionType.HEALTH_EXERCISE: 0.5,
            ActionType.HEALTH_SLEEP: 0.4,
            ActionType.HEALTH_NUTRITION: 0.3,
            ActionType.TIME_FOCUS: 0.4,
            ActionType.TIME_BREAK: 0.2,
            ActionType.EMOTION_RELAX: 0.3,
            ActionType.EMOTION_SOCIAL: 0.35,
            ActionType.LEARNING_STUDY: 0.4,
            ActionType.LEARNING_REVIEW: 0.35
        }
        
        reward += action_rewards.get(action, 0.0)
        
        # 2. 状态改进奖励
        for key, weight in self.weights.items():
            current_val = current_state.get(key, 0.0)
            next_val = next_state.get(key, 0.0)
            improvement = (next_val - current_val) / (abs(current_val) + 1)
            reward += improvement * weight * 0.5
        
        # 3. 惩罚（如果状态恶化）
        for key in self.weights:
            current_val = current_state.get(key, 0.0)
            next_val = next_state.get(key, 0.0)
            if next_val < current_val * 0.8:  # 下降超过20%
                reward -= 0.1
        
        return max(-1.0, min(1.0, reward))  # 限制在[-1, 1]范围内
    
    def set_weights(self, weights: Dict[str, float]) -> None:
        """设置奖励权重"""
        total = sum(weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in weights.items()}


class QLearningAgent:
    """Q-Learning代理"""
    
    def __init__(self, user_id: str, learning_rate: float = 0.1, discount_factor: float = 0.9):
        self.user_id = user_id
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        
        self.q_table = {}  # (state_id, action) -> q_value
        self.reward_function = RewardFunction()
        self.episode_history = []
        self.training_stats = {
            "total_episodes": 0,
            "total_steps": 0,
            "average_reward": 0.0,
            "max_reward": -float('inf'),
            "min_reward": float('inf')
        }
    
    def get_q_value(self, state_id: str, action: ActionType) -> float:
        """获取Q值"""
        key = (state_id, action.value)
        return self.q_table.get(key, 0.0)
    
    def set_q_value(self, state_id: str, action: ActionType, value: float) -> None:
        """设置Q值"""
        key = (state_id, action.value)
        self.q_table[key] = value
    
    def select_action(
        self,
        state_id: str,
        epsilon: float = 0.1,
        available_actions: Optional[List[ActionType]] = None
    ) -> ActionType:
        """
        选择行动（epsilon-greedy策略）
        """
        if available_actions is None:
            available_actions = list(ActionType)
        
        # epsilon概率随机选择，(1-epsilon)概率选择最优行动
        if np.random.random() < epsilon:
            return np.random.choice(available_actions)
        else:
            # 选择Q值最大的行动
            best_action = available_actions[0]
            best_q_value = self.get_q_value(state_id, best_action)
            
            for action in available_actions[1:]:
                q_value = self.get_q_value(state_id, action)
                if q_value > best_q_value:
                    best_q_value = q_value
                    best_action = action
            
            return best_action
    
    def update_q_value(
        self,
        state_id: str,
        action: ActionType,
        reward: float,
        next_state_id: str,
        next_actions: Optional[List[ActionType]] = None
    ) -> float:
        """
        更新Q值（Q-Learning更新规则）
        Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
        """
        if next_actions is None:
            next_actions = list(ActionType)
        
        # 获取当前Q值
        current_q = self.get_q_value(state_id, action)
        
        # 获取下一状态的最大Q值
        max_next_q = max(
            self.get_q_value(next_state_id, a) for a in next_actions
        ) if next_actions else 0.0
        
        # 计算新Q值
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        # 更新Q值
        self.set_q_value(state_id, action, new_q)
        
        return new_q
    
    def train_episode(
        self,
        initial_state: State,
        max_steps: int = 100,
        epsilon: float = 0.1
    ) -> Dict[str, Any]:
        """
        训练一个episode
        """
        current_state = initial_state
        total_reward = 0.0
        steps = 0
        transitions = []
        
        for step in range(max_steps):
            # 选择行动
            action = self.select_action(current_state.state_id, epsilon)
            
            # 模拟环境反应（这里简化处理）
            next_state = self._simulate_next_state(current_state, action)
            
            # 计算奖励
            reward = self.reward_function.calculate_reward(
                current_state.features, next_state.features, action
            )
            
            # 更新Q值
            self.update_q_value(
                current_state.state_id, action, reward, next_state.state_id
            )
            
            # 记录转移
            transitions.append(Transition(
                state=current_state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=False
            ))
            
            total_reward += reward
            current_state = next_state
            steps += 1
            
            # 检查是否完成
            if self._is_terminal_state(next_state):
                break
        
        # 更新统计信息
        self.training_stats["total_episodes"] += 1
        self.training_stats["total_steps"] += steps
        self.training_stats["average_reward"] = (
            (self.training_stats["average_reward"] * (self.training_stats["total_episodes"] - 1) + total_reward) /
            self.training_stats["total_episodes"]
        )
        self.training_stats["max_reward"] = max(
            self.training_stats["max_reward"], total_reward
        )
        self.training_stats["min_reward"] = min(
            self.training_stats["min_reward"], total_reward
        )
        
        # 记录episode
        episode = {
            "episode": self.training_stats["total_episodes"],
            "steps": steps,
            "total_reward": total_reward,
            "transitions": transitions,
            "timestamp": datetime.now().isoformat()
        }
        self.episode_history.append(episode)
        
        return episode
    
    def _simulate_next_state(self, current_state: State, action: ActionType) -> State:
        """模拟下一状态"""
        next_features = current_state.features.copy()
        
        # 根据行动类型更新特征
        if action == ActionType.HEALTH_EXERCISE:
            next_features["health_score"] = min(100, next_features.get("health_score", 70) + 5)
            next_features["mood"] = min(10, next_features.get("mood", 7) + 1)
        elif action == ActionType.HEALTH_SLEEP:
            next_features["health_score"] = min(100, next_features.get("health_score", 70) + 3)
            next_features["mood"] = min(10, next_features.get("mood", 7) + 0.5)
        elif action == ActionType.TIME_FOCUS:
            next_features["efficiency"] = min(100, next_features.get("efficiency", 70) + 10)
        elif action == ActionType.EMOTION_RELAX:
            next_features["mood"] = min(10, next_features.get("mood", 7) + 2)
        elif action == ActionType.EMOTION_SOCIAL:
            next_features["social_satisfaction"] = min(10, next_features.get("social_satisfaction", 6) + 1.5)
            next_features["mood"] = min(10, next_features.get("mood", 7) + 1)
        elif action == ActionType.LEARNING_STUDY:
            next_features["learning_progress"] = min(100, next_features.get("learning_progress", 50) + 5)
        
        # 自然衰减
        for key in ["mood", "efficiency", "social_satisfaction"]:
            if key in next_features:
                next_features[key] = next_features[key] * 0.95
        
        return State(
            state_id=f"state_{datetime.now().timestamp()}",
            features=next_features
        )
    
    def _is_terminal_state(self, state: State) -> bool:
        """检查是否为终止状态"""
        # 简化实现：如果所有指标都很高，则为终止状态
        features = state.features
        return (
            features.get("health_score", 0) > 90 and
            features.get("mood", 0) > 8 and
            features.get("efficiency", 0) > 80
        )
    
    def get_best_policy(self) -> Dict[str, ActionType]:
        """获取最优策略"""
        policy = {}
        
        # 对每个状态，选择Q值最大的行动
        states = set(state_id for state_id, _ in self.q_table.keys())
        
        for state_id in states:
            best_action = ActionType.HEALTH_EXERCISE
            best_q_value = self.get_q_value(state_id, best_action)
            
            for action in ActionType:
                q_value = self.get_q_value(state_id, action)
                if q_value > best_q_value:
                    best_q_value = q_value
                    best_action = action
            
            policy[state_id] = best_action
        
        return policy
    
    def get_training_stats(self) -> Dict[str, Any]:
        """获取训练统计"""
        return self.training_stats.copy()


class PolicyGradientAgent:
    """策略梯度代理"""
    
    def __init__(self, user_id: str, learning_rate: float = 0.01):
        self.user_id = user_id
        self.learning_rate = learning_rate
        
        # 策略参数（简化为线性策略）
        self.policy_params = {action.value: np.random.randn(10) for action in ActionType}
        
        self.reward_function = RewardFunction()
        self.episode_history = []
        self.training_stats = {
            "total_episodes": 0,
            "average_reward": 0.0,
            "policy_entropy": 0.0
        }
    
    def get_action_probabilities(self, state_features: Dict[str, float]) -> Dict[ActionType, float]:
        """
        获取行动概率（softmax）
        """
        # 将状态特征转换为向量
        state_vector = self._features_to_vector(state_features)
        
        # 计算每个行动的logits
        logits = {}
        for action in ActionType:
            params = self.policy_params[action.value]
            logit = np.dot(params, state_vector)
            logits[action] = logit
        
        # 应用softmax
        max_logit = max(logits.values())
        exp_logits = {a: np.exp(l - max_logit) for a, l in logits.items()}
        sum_exp = sum(exp_logits.values())
        
        probabilities = {a: exp / sum_exp for a, exp in exp_logits.items()}
        
        return probabilities
    
    def select_action(self, state_features: Dict[str, float]) -> ActionType:
        """根据策略选择行动"""
        probabilities = self.get_action_probabilities(state_features)
        actions = list(probabilities.keys())
        probs = [probabilities[a] for a in actions]
        
        selected_action = np.random.choice(actions, p=probs)
        return selected_action
    
    def update_policy(
        self,
        transitions: List[Transition],
        returns: List[float]
    ) -> None:
        """
        更新策略（策略梯度）
        """
        for transition, return_value in zip(transitions, returns):
            state_features = transition.state.features
            action = transition.action
            
            # 获取行动概率
            probabilities = self.get_action_probabilities(state_features)
            action_prob = probabilities[action]
            
            # 计算策略梯度
            state_vector = self._features_to_vector(state_features)
            
            # 更新参数
            gradient = return_value * state_vector
            self.policy_params[action.value] += self.learning_rate * gradient
    
    def train_episode(
        self,
        initial_state: State,
        max_steps: int = 100
    ) -> Dict[str, Any]:
        """训练一个episode"""
        current_state = initial_state
        transitions = []
        rewards = []
        
        for step in range(max_steps):
            # 选择行动
            action = self.select_action(current_state.features)
            
            # 模拟环境反应
            next_state = self._simulate_next_state(current_state, action)
            
            # 计算奖励
            reward = self.reward_function.calculate_reward(
                current_state.features, next_state.features, action
            )
            
            transitions.append(Transition(
                state=current_state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=False
            ))
            rewards.append(reward)
            current_state = next_state
            
            if self._is_terminal_state(next_state):
                break
        
        # 计算回报（从后向前累积）
        returns = []
        cumulative_return = 0
        for reward in reversed(rewards):
            cumulative_return = reward + 0.9 * cumulative_return
            returns.insert(0, cumulative_return)
        
        # 更新策略
        self.update_policy(transitions, returns)
        
        # 更新统计信息
        total_reward = sum(rewards)
        self.training_stats["total_episodes"] += 1
        self.training_stats["average_reward"] = (
            (self.training_stats["average_reward"] * (self.training_stats["total_episodes"] - 1) + total_reward) /
            self.training_stats["total_episodes"]
        )
        
        # 计算策略熵
        all_probs = []
        for action in ActionType:
            probs = self.get_action_probabilities(current_state.features)
            all_probs.append(probs[action])
        
        entropy = -sum(p * np.log(p + 1e-8) for p in all_probs)
        self.training_stats["policy_entropy"] = entropy
        
        episode = {
            "episode": self.training_stats["total_episodes"],
            "steps": len(transitions),
            "total_reward": total_reward,
            "transitions": transitions,
            "timestamp": datetime.now().isoformat()
        }
        self.episode_history.append(episode)
        
        return episode
    
    def _features_to_vector(self, features: Dict[str, float]) -> np.ndarray:
        """将特征转换为向量"""
        feature_keys = [
            "health_score", "mood", "efficiency",
            "social_satisfaction", "learning_progress"
        ]
        vector = np.array([features.get(key, 0.0) for key in feature_keys])
        # 归一化
        vector = vector / (np.linalg.norm(vector) + 1e-8)
        # 填充到10维
        if len(vector) < 10:
            vector = np.concatenate([vector, np.zeros(10 - len(vector))])
        return vector[:10]
    
    def _simulate_next_state(self, current_state: State, action: ActionType) -> State:
        """模拟下一状态"""
        next_features = current_state.features.copy()
        
        # 根据行动类型更新特征
        if action == ActionType.HEALTH_EXERCISE:
            next_features["health_score"] = min(100, next_features.get("health_score", 70) + 5)
            next_features["mood"] = min(10, next_features.get("mood", 7) + 1)
        elif action == ActionType.HEALTH_SLEEP:
            next_features["health_score"] = min(100, next_features.get("health_score", 70) + 3)
        elif action == ActionType.TIME_FOCUS:
            next_features["efficiency"] = min(100, next_features.get("efficiency", 70) + 10)
        elif action == ActionType.EMOTION_RELAX:
            next_features["mood"] = min(10, next_features.get("mood", 7) + 2)
        elif action == ActionType.EMOTION_SOCIAL:
            next_features["social_satisfaction"] = min(10, next_features.get("social_satisfaction", 6) + 1.5)
        elif action == ActionType.LEARNING_STUDY:
            next_features["learning_progress"] = min(100, next_features.get("learning_progress", 50) + 5)
        
        return State(
            state_id=f"state_{datetime.now().timestamp()}",
            features=next_features
        )
    
    def _is_terminal_state(self, state: State) -> bool:
        """检查是否为终止状态"""
        features = state.features
        return (
            features.get("health_score", 0) > 90 and
            features.get("mood", 0) > 8
        )
    
    def get_training_stats(self) -> Dict[str, Any]:
        """获取训练统计"""
        return self.training_stats.copy()


class RLModelEvaluator:
    """强化学习模型评估器"""
    
    def __init__(self):
        self.evaluation_results = []
    
    def evaluate_agent(
        self,
        agent,
        test_states: List[State],
        num_episodes: int = 10
    ) -> Dict[str, Any]:
        """
        评估代理
        """
        total_rewards = []
        
        for _ in range(num_episodes):
            for test_state in test_states:
                if hasattr(agent, 'train_episode'):
                    episode = agent.train_episode(test_state)
                    total_rewards.append(episode["total_reward"])
        
        # 计算评估指标
        evaluation = {
            "average_reward": np.mean(total_rewards),
            "std_reward": np.std(total_rewards),
            "max_reward": np.max(total_rewards),
            "min_reward": np.min(total_rewards),
            "success_rate": len([r for r in total_rewards if r > 0.5]) / len(total_rewards),
            "timestamp": datetime.now().isoformat()
        }
        
        self.evaluation_results.append(evaluation)
        
        return evaluation
    
    def compare_agents(
        self,
        agents: Dict[str, Any],
        test_states: List[State],
        num_episodes: int = 10
    ) -> Dict[str, Any]:
        """
        对比多个代理
        """
        comparison = {}
        
        for agent_name, agent in agents.items():
            evaluation = self.evaluate_agent(agent, test_states, num_episodes)
            comparison[agent_name] = evaluation
        
        return comparison
    
    def get_evaluation_history(self) -> List[Dict[str, Any]]:
        """获取评估历史"""
        return self.evaluation_results.copy()


# 全局实例管理
_q_agents = {}
_pg_agents = {}
_evaluator = None

def get_q_learning_agent(user_id: str) -> QLearningAgent:
    """获取Q-Learning代理"""
    if user_id not in _q_agents:
        _q_agents[user_id] = QLearningAgent(user_id)
    return _q_agents[user_id]

def get_policy_gradient_agent(user_id: str) -> PolicyGradientAgent:
    """获取策略梯度代理"""
    if user_id not in _pg_agents:
        _pg_agents[user_id] = PolicyGradientAgent(user_id)
    return _pg_agents[user_id]

def get_rl_evaluator() -> RLModelEvaluator:
    """获取强化学习评估器"""
    global _evaluator
    if _evaluator is None:
        _evaluator = RLModelEvaluator()
    return _evaluator

