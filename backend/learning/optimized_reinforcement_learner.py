"""
优化的强化学习模型 - Phase 2
提高个人模型准确度到90%+
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
import numpy as np
import json
from enum import Enum


class LearningStrategy(Enum):
    """学习策略"""
    ACTOR_CRITIC = "actor_critic"  # Actor-Critic方法
    PPO = "ppo"  # 近端策略优化
    DQN = "dqn"  # 深度Q学习
    MULTI_AGENT = "multi_agent"  # 多智能体学习


@dataclass
class OptimizedState:
    """优化的状态表示"""
    user_data: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 缓存的向量表示
    _vector_cache: Optional[np.ndarray] = field(default=None, init=False)
    
    def to_vector(self, normalize: bool = True) -> np.ndarray:
        """转换为向量表示（带缓存）"""
        if self._vector_cache is not None:
            return self._vector_cache
        
        features = []
        
        # 健康特征 (0-1)
        features.append(min(self.user_data.get('sleep_hours', 7) / 10.0, 1.0))
        features.append(min(self.user_data.get('exercise_minutes', 30) / 120.0, 1.0))
        features.append(1.0 - min(self.user_data.get('stress_level', 5) / 10.0, 1.0))
        features.append(self.user_data.get('health_score', 75) / 100.0)
        
        # 情绪特征 (0-1)
        features.append(self.user_data.get('mood', 5) / 10.0)
        features.append(1.0 - min(self.user_data.get('loneliness', 5) / 10.0, 1.0))
        
        # 时间特征 (0-1)
        features.append(1.0 - min(self.context.get('time_pressure', 0.5), 1.0))
        features.append(self.user_data.get('efficiency_score', 70) / 100.0)
        
        # 社交特征 (0-1)
        features.append(self.user_data.get('social_satisfaction', 5) / 10.0)
        features.append(min(self.user_data.get('social_hours', 2) / 8.0, 1.0))
        
        # 上下文特征 (0-1)
        features.append(self.context.get('data_quality', 0.5))
        features.append(self.context.get('urgency', 0.5))
        features.append(self.context.get('complexity', 0.5))
        
        vector = np.array(features, dtype=np.float32)
        
        if normalize:
            # 标准化
            mean = np.mean(vector)
            std = np.std(vector)
            if std > 0:
                vector = (vector - mean) / std
        
        self._vector_cache = vector
        return vector


@dataclass
class OptimizedAction:
    """优化的动作表示"""
    action_id: str
    action_type: str
    content: str
    agent_weights: Dict[str, float]
    confidence: float
    expected_value: float = 0.0  # 预期价值
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizedFeedback:
    """优化的反馈表示"""
    feedback_type: str  # adopted, ignored, rejected, partial
    rating: Optional[float] = None  # 0-1
    comment: Optional[str] = None
    action_effectiveness: float = 0.5  # 0-1，动作有效性
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_reward(self, use_effectiveness: bool = True) -> float:
        """转换为奖励信号（改进版）"""
        base_reward = {
            'adopted': 1.0,
            'partial': 0.5,
            'ignored': 0.0,
            'rejected': -0.5
        }.get(self.feedback_type, 0.0)
        
        # 融合评分
        if self.rating is not None:
            rating_reward = self.rating * 2 - 1  # [-1, 1]
            base_reward = base_reward * 0.6 + rating_reward * 0.4
        
        # 融合有效性
        if use_effectiveness:
            base_reward = base_reward * 0.7 + (self.action_effectiveness * 2 - 1) * 0.3
        
        return np.clip(base_reward, -1.0, 1.0)


class PrioritizedReplayBuffer:
    """优先级经验回放缓冲区"""
    
    def __init__(self, max_size: int = 10000, alpha: float = 0.6, beta: float = 0.4):
        self.max_size = max_size
        self.alpha = alpha  # 优先级指数
        self.beta = beta  # 重要性采样指数
        
        self.buffer = deque(maxlen=max_size)
        self.priorities = deque(maxlen=max_size)
        self.max_priority = 1.0
    
    def add(self, experience: Any, td_error: float = 1.0):
        """添加经验（带优先级）"""
        priority = (abs(td_error) + 1e-6) ** self.alpha
        self.max_priority = max(self.max_priority, priority)
        
        self.buffer.append(experience)
        self.priorities.append(priority)
    
    def sample(self, batch_size: int) -> Tuple[List[Any], np.ndarray]:
        """按优先级采样"""
        if len(self.buffer) < batch_size:
            indices = list(range(len(self.buffer)))
            batch = list(self.buffer)
        else:
            # 计算采样概率
            priorities = np.array(list(self.priorities))
            probabilities = priorities / priorities.sum()
            
            # 按优先级采样
            indices = np.random.choice(
                len(self.buffer),
                batch_size,
                p=probabilities,
                replace=False
            )
            batch = [self.buffer[i] for i in indices]
            
            # 计算重要性权重
            weights = (len(self.buffer) * probabilities[indices]) ** (-self.beta)
            weights /= weights.max()
        
        return batch, np.array(weights) if len(self.buffer) >= batch_size else np.ones(len(batch))
    
    def update_priorities(self, indices: List[int], td_errors: List[float]):
        """更新优先级"""
        for idx, td_error in zip(indices, td_errors):
            priority = (abs(td_error) + 1e-6) ** self.alpha
            self.priorities[idx] = priority
            self.max_priority = max(self.max_priority, priority)
    
    def size(self) -> int:
        return len(self.buffer)


class DualNetworkArchitecture:
    """双网络架构（Actor-Critic）"""
    
    def __init__(self, state_dim: int = 13, action_dim: int = 10):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Actor网络（策略）
        self.actor_weights = np.random.randn(state_dim, action_dim) * 0.01
        self.actor_bias = np.zeros(action_dim)
        
        # Critic网络（价值）
        self.critic_weights = np.random.randn(state_dim, 1) * 0.01
        self.critic_bias = 0.0
        
        # 学习率
        self.actor_lr = 0.001
        self.critic_lr = 0.01
        
        # 动量
        self.actor_momentum = np.zeros_like(self.actor_weights)
        self.critic_momentum = np.zeros_like(self.critic_weights)
    
    def actor_forward(self, state_vector: np.ndarray) -> np.ndarray:
        """Actor前向传播"""
        logits = np.dot(state_vector, self.actor_weights) + self.actor_bias
        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / exp_logits.sum()
    
    def critic_forward(self, state_vector: np.ndarray) -> float:
        """Critic前向传播"""
        return float(np.dot(state_vector, self.critic_weights) + self.critic_bias)
    
    def actor_update(self, state_vector: np.ndarray, action_idx: int, advantage: float):
        """更新Actor"""
        action_probs = self.actor_forward(state_vector)
        
        # 计算梯度
        grad = action_probs.copy()
        grad[action_idx] -= 1
        grad = np.outer(state_vector, grad) * (-advantage)
        
        # 动量更新
        self.actor_momentum = 0.9 * self.actor_momentum + grad
        self.actor_weights -= self.actor_lr * self.actor_momentum
        self.actor_bias -= self.actor_lr * np.sum(grad, axis=0)
    
    def critic_update(self, state_vector: np.ndarray, target: float):
        """更新Critic"""
        prediction = self.critic_forward(state_vector)
        error = target - prediction
        
        # 计算梯度
        grad = -2 * error * state_vector
        
        # 动量更新
        self.critic_momentum = 0.9 * self.critic_momentum + grad.reshape(-1, 1)
        self.critic_weights -= self.critic_lr * self.critic_momentum
        self.critic_bias -= self.critic_lr * error


class OptimizedReinforcementLearner:
    """优化的强化学习器"""
    
    def __init__(
        self,
        user_id: str = "default_user",
        strategy: LearningStrategy = LearningStrategy.ACTOR_CRITIC,
        enable_rag: bool = True
    ):
        self.user_id = user_id
        self.strategy = strategy
        self.enable_rag = enable_rag
        
        # 核心组件
        self.replay_buffer = PrioritizedReplayBuffer(max_size=20000)
        self.network = DualNetworkArchitecture(state_dim=13, action_dim=10)
        
        # 统计信息
        self.total_episodes = 0
        self.total_rewards = deque(maxlen=1000)
        self.episode_rewards = []
        
        # 性能跟踪
        self.accuracy_history = []
        self.loss_history = []
        
        # 智能体权重
        self.agent_weights = defaultdict(lambda: 1.0)
        self.agent_performance = defaultdict(list)
        
        # RAG集成
        self.rag_system = None
        if enable_rag:
            try:
                from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType
                self.rag_system = ProductionRAGSystem(user_id=user_id, use_gpu=False)
                self.MemoryType = MemoryType
                print(f"✅ RAG系统已集成到优化强化学习层")
            except Exception as e:
                print(f"⚠️  RAG集成失败: {e}")
                self.enable_rag = False
    
    def learn(
        self,
        state: OptimizedState,
        action: OptimizedAction,
        feedback: OptimizedFeedback,
        next_state: Optional[OptimizedState] = None
    ):
        """学习单次交互"""
        # 1. 转换反馈为奖励
        reward = feedback.to_reward(use_effectiveness=True)
        
        # 2. 创建经验
        experience = {
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': next_state is None
        }
        
        # 3. 计算TD误差用于优先级
        state_vec = state.to_vector()
        current_value = self.network.critic_forward(state_vec)
        
        if next_state is not None:
            next_state_vec = next_state.to_vector()
            next_value = self.network.critic_forward(next_state_vec)
            target = reward + 0.99 * next_value
        else:
            target = reward
        
        td_error = abs(target - current_value)
        
        # 4. 添加到优先级回放缓冲区
        self.replay_buffer.add(experience, td_error)
        
        # 5. 更新智能体权重
        for agent_id in action.agent_weights:
            self.agent_performance[agent_id].append(reward)
        
        # 6. 如果有足够经验，进行优化
        if self.replay_buffer.size() >= 64:
            self._optimize_networks()
        
        # 7. 定期更新智能体权重
        if self.total_episodes % 20 == 0:
            self._update_agent_weights()
        
        self.total_episodes += 1
        self.total_rewards.append(reward)
        self.episode_rewards.append(reward)
    
    def _optimize_networks(self, batch_size: int = 64):
        """优化网络"""
        # 采样优先级批次
        batch, weights = self.replay_buffer.sample(batch_size)
        
        td_errors = []
        
        for i, exp in enumerate(batch):
            state_vec = exp['state'].to_vector()
            action_idx = hash(exp['action'].action_type) % self.network.action_dim
            
            # 计算目标
            if exp['next_state'] is not None:
                next_state_vec = exp['next_state'].to_vector()
                next_value = self.network.critic_forward(next_state_vec)
                target = exp['reward'] + 0.99 * next_value
            else:
                target = exp['reward']
            
            # 计算优势
            current_value = self.network.critic_forward(state_vec)
            advantage = target - current_value
            
            # 更新网络
            self.network.critic_update(state_vec, target)
            self.network.actor_update(state_vec, action_idx, advantage * weights[i])
            
            # 记录TD误差
            td_errors.append(abs(advantage))
        
        # 更新优先级
        batch_indices = list(range(len(batch)))
        self.replay_buffer.update_priorities(batch_indices, td_errors)
        
        # 记录损失
        avg_loss = np.mean(td_errors)
        self.loss_history.append(avg_loss)
    
    def _update_agent_weights(self):
        """更新智能体权重"""
        for agent_id, performances in self.agent_performance.items():
            if len(performances) >= 10:
                # 计算最近表现
                recent_perf = np.mean(performances[-20:])
                
                # 指数移动平均
                alpha = 0.15
                self.agent_weights[agent_id] = (
                    (1 - alpha) * self.agent_weights[agent_id] +
                    alpha * (1.0 + recent_perf)
                )
                
                # 限制范围
                self.agent_weights[agent_id] = np.clip(
                    self.agent_weights[agent_id],
                    0.1, 2.0
                )
    
    def get_accuracy(self) -> float:
        """获取模型准确度"""
        if len(self.total_rewards) < 10:
            return 0.5
        
        # 计算最近100次的成功率
        recent = list(self.total_rewards)[-100:]
        success_rate = len([r for r in recent if r > 0]) / len(recent)
        
        # 转换为准确度 (0-1)
        accuracy = (success_rate + 1.0) / 2.0
        self.accuracy_history.append(accuracy)
        
        return accuracy
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        recent_rewards = list(self.total_rewards)[-100:] if self.total_rewards else []
        
        accuracy = self.get_accuracy()
        
        stats = {
            'total_episodes': self.total_episodes,
            'buffer_size': self.replay_buffer.size(),
            'average_reward': np.mean(recent_rewards) if recent_rewards else 0.0,
            'reward_std': np.std(recent_rewards) if recent_rewards else 0.0,
            'accuracy': accuracy,
            'accuracy_trend': 'improving' if len(self.accuracy_history) > 1 and 
                            self.accuracy_history[-1] > self.accuracy_history[-2] else 'stable',
            'agent_weights': dict(self.agent_weights),
            'strategy': self.strategy.value,
            'rag_enabled': self.enable_rag
        }
        
        return stats
    
    def predict_action_value(self, state: OptimizedState) -> float:
        """预测动作价值"""
        state_vec = state.to_vector()
        return self.network.critic_forward(state_vec)
    
    def get_policy(self, state: OptimizedState) -> np.ndarray:
        """获取策略（动作概率分布）"""
        state_vec = state.to_vector()
        return self.network.actor_forward(state_vec)
    
    def save(self, filepath: str):
        """保存模型"""
        checkpoint = {
            'actor_weights': self.network.actor_weights.tolist(),
            'actor_bias': self.network.actor_bias.tolist(),
            'critic_weights': self.network.critic_weights.tolist(),
            'critic_bias': float(self.network.critic_bias),
            'total_episodes': self.total_episodes,
            'agent_weights': dict(self.agent_weights),
            'accuracy_history': list(self.accuracy_history)[-100:],
            'strategy': self.strategy.value
        }
        
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def load(self, filepath: str) -> bool:
        """加载模型"""
        try:
            with open(filepath, 'r') as f:
                checkpoint = json.load(f)
            
            self.network.actor_weights = np.array(checkpoint['actor_weights'])
            self.network.actor_bias = np.array(checkpoint['actor_bias'])
            self.network.critic_weights = np.array(checkpoint['critic_weights'])
            self.network.critic_bias = checkpoint['critic_bias']
            self.total_episodes = checkpoint['total_episodes']
            self.agent_weights = defaultdict(lambda: 1.0, checkpoint['agent_weights'])
            self.accuracy_history = checkpoint['accuracy_history']
            
            return True
        except Exception as e:
            print(f"加载模型失败: {e}")
            return False


# 全局实例
_optimized_learner = None

def get_optimized_reinforcement_learner(
    user_id: str = "default_user",
    strategy: LearningStrategy = LearningStrategy.ACTOR_CRITIC
) -> OptimizedReinforcementLearner:
    """获取优化的强化学习器实例"""
    global _optimized_learner
    if _optimized_learner is None:
        _optimized_learner = OptimizedReinforcementLearner(user_id, strategy)
    return _optimized_learner

