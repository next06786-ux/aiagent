"""
强化学习自进化模块
让系统从用户反馈中持续学习和优化
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
import numpy as np
import json


@dataclass
class State:
    """状态"""
    user_data: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_vector(self) -> np.ndarray:
        """转换为向量表示"""
        features = []
        
        # 提取数值特征
        features.append(self.user_data.get('sleep_hours', 7) / 10.0)
        features.append(self.user_data.get('exercise_minutes', 30) / 100.0)
        features.append(self.user_data.get('stress_level', 5) / 10.0)
        features.append(self.context.get('data_quality', 0.5))
        features.append(self.context.get('urgency', 0.5))
        features.append(self.context.get('complexity', 0.5))
        
        return np.array(features)


@dataclass
class Action:
    """动作（系统给出的建议）"""
    action_id: str
    action_type: str  # recommendation, alert, query
    content: str
    agent_weights: Dict[str, float]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Feedback:
    """用户反馈"""
    feedback_type: str  # adopted, ignored, rejected
    rating: Optional[float] = None  # 0-1
    comment: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_reward(self) -> float:
        """转换为奖励信号"""
        if self.feedback_type == 'adopted':
            return 1.0
        elif self.feedback_type == 'ignored':
            return 0.0
        elif self.feedback_type == 'rejected':
            return -1.0
        
        # 如果有评分，使用评分
        if self.rating is not None:
            return self.rating * 2 - 1  # 转换到 [-1, 1]
        
        return 0.0


@dataclass
class Experience:
    """经验（状态-动作-奖励-下一状态）"""
    state: State
    action: Action
    reward: float
    next_state: Optional[State] = None
    done: bool = False


class ReplayBuffer:
    """经验回放缓冲区"""
    
    def __init__(self, max_size: int = 10000):
        self.buffer = deque(maxlen=max_size)
    
    def add(self, experience: Experience):
        """添加经验"""
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[Experience]:
        """随机采样"""
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]
    
    def size(self) -> int:
        return len(self.buffer)


class PolicyNetwork:
    """策略网络（简化版）"""
    
    def __init__(self, state_dim: int = 6, action_dim: int = 10):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # 简化的线性策略
        self.weights = np.random.randn(state_dim, action_dim) * 0.1
        self.bias = np.zeros(action_dim)
        
        # 学习率
        self.learning_rate = 0.01
    
    def predict(self, state_vector: np.ndarray) -> np.ndarray:
        """预测动作概率"""
        logits = np.dot(state_vector, self.weights) + self.bias
        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / exp_logits.sum()
    
    def update(self, state_vector: np.ndarray, action_idx: int, advantage: float):
        """更新策略"""
        # 计算梯度
        action_probs = self.predict(state_vector)
        
        # 策略梯度
        grad_weights = np.outer(state_vector, action_probs)
        grad_weights[:, action_idx] -= state_vector
        grad_weights *= -advantage
        
        grad_bias = action_probs.copy()
        grad_bias[action_idx] -= 1
        grad_bias *= -advantage
        
        # 更新参数
        self.weights -= self.learning_rate * grad_weights
        self.bias -= self.learning_rate * grad_bias


class ValueNetwork:
    """价值网络（简化版）"""
    
    def __init__(self, state_dim: int = 6):
        self.state_dim = state_dim
        self.weights = np.random.randn(state_dim) * 0.1
        self.bias = 0.0
        self.learning_rate = 0.01
    
    def predict(self, state_vector: np.ndarray) -> float:
        """预测状态价值"""
        return np.dot(state_vector, self.weights) + self.bias
    
    def update(self, state_vector: np.ndarray, target: float):
        """更新价值函数"""
        prediction = self.predict(state_vector)
        error = target - prediction
        
        # 梯度下降
        self.weights += self.learning_rate * error * state_vector
        self.bias += self.learning_rate * error


class AgentWeightOptimizer:
    """智能体权重优化器"""
    
    def __init__(self):
        self.agent_performance = defaultdict(list)
        self.agent_weights = defaultdict(lambda: 1.0)
    
    def record_performance(self, agent_id: str, reward: float):
        """记录智能体表现"""
        self.agent_performance[agent_id].append(reward)
        
        # 只保留最近100次
        if len(self.agent_performance[agent_id]) > 100:
            self.agent_performance[agent_id] = self.agent_performance[agent_id][-100:]
    
    def update_weights(self):
        """更新智能体权重"""
        for agent_id, performances in self.agent_performance.items():
            if len(performances) >= 10:
                # 计算平均表现
                avg_performance = np.mean(performances[-20:])
                
                # 更新权重（指数移动平均）
                alpha = 0.1
                self.agent_weights[agent_id] = (
                    (1 - alpha) * self.agent_weights[agent_id] +
                    alpha * (1.0 + avg_performance)
                )
                
                # 限制范围
                self.agent_weights[agent_id] = np.clip(
                    self.agent_weights[agent_id],
                    0.1, 2.0
                )
    
    def get_weights(self) -> Dict[str, float]:
        """获取当前权重"""
        return dict(self.agent_weights)


class RecommendationOptimizer:
    """建议模板优化器"""
    
    def __init__(self):
        self.template_performance = defaultdict(list)
        self.template_usage = defaultdict(int)
    
    def record_feedback(self, template_id: str, reward: float):
        """记录模板反馈"""
        self.template_performance[template_id].append(reward)
        self.template_usage[template_id] += 1
    
    def get_best_templates(self, top_k: int = 5) -> List[Tuple[str, float]]:
        """获取最佳模板"""
        template_scores = []
        
        for template_id, performances in self.template_performance.items():
            if len(performances) >= 3:
                avg_score = np.mean(performances)
                usage = self.template_usage[template_id]
                
                # 综合得分：表现 + 使用频率
                score = avg_score * 0.7 + min(usage / 100, 1.0) * 0.3
                template_scores.append((template_id, score))
        
        template_scores.sort(key=lambda x: x[1], reverse=True)
        return template_scores[:top_k]


class ReinforcementLearner:
    """强化学习模块"""
    
    def __init__(self, user_id: str = "default_user", enable_rag: bool = True):
        self.user_id = user_id
        self.replay_buffer = ReplayBuffer(max_size=10000)
        self.policy_network = PolicyNetwork()
        self.value_network = ValueNetwork()
        self.agent_optimizer = AgentWeightOptimizer()
        self.recommendation_optimizer = RecommendationOptimizer()
        
        # RAG集成 - 实现自学习
        self.enable_rag = enable_rag
        self.rag_system = None
        if enable_rag:
            try:
                from learning.production_rag_system import ProductionRAGSystem, MemoryType
                self.rag_system = ProductionRAGSystem(
                    user_id=user_id,
                    use_gpu=True
                )
                self.MemoryType = MemoryType
                print(f"✅ RAG系统已集成到强化学习层")
            except Exception as e:
                print(f"⚠️  RAG集成失败，使用纯强化学习模式: {e}")
                self.enable_rag = False
        
        # 统计信息
        self.total_episodes = 0
        self.total_rewards = []
        self.learning_history = []
    
    def learn(
        self,
        state: State,
        action: Action,
        feedback: Feedback,
        next_state: Optional[State] = None
    ):
        """从单次交互中学习 - 集成RAG实现自学习"""
        # 1. 转换反馈为奖励
        reward = feedback.to_reward()
        
        # 2. 创建经验
        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=(next_state is None)
        )
        
        # 3. 存储经验到内存缓冲区
        self.replay_buffer.add(experience)
        
        # 4. 【RAG集成】存储经验到RAG知识库
        if self.enable_rag and self.rag_system:
            self._store_experience_to_rag(experience)
        
        # 5. 更新智能体权重
        for agent_id, weight in action.agent_weights.items():
            self.agent_optimizer.record_performance(agent_id, reward)
        
        # 6. 更新建议模板
        self.recommendation_optimizer.record_feedback(
            action.action_type,
            reward
        )
        
        # 7. 如果有足够经验，进行策略优化
        if self.replay_buffer.size() >= 32:
            self._optimize_policy()
        
        # 8. 定期更新智能体权重
        if self.total_episodes % 10 == 0:
            self.agent_optimizer.update_weights()
        
        self.total_episodes += 1
        self.total_rewards.append(reward)
    
    def _optimize_policy(self, batch_size: int = 32):
        """优化策略 - 结合RAG历史经验"""
        # 采样经验
        batch = self.replay_buffer.sample(batch_size)
        
        for exp in batch:
            state_vec = exp.state.to_vector()
            
            # 【RAG增强】检索相似历史经验
            historical_advantage = 0.0
            if self.enable_rag and self.rag_system:
                historical_advantage = self._retrieve_historical_advantage(exp.state)
            
            # 计算优势函数（结合历史经验）
            value = self.value_network.predict(state_vec)
            current_advantage = exp.reward - value
            
            # 融合当前优势和历史优势
            advantage = current_advantage * 0.7 + historical_advantage * 0.3
            
            # 更新价值网络
            self.value_network.update(state_vec, exp.reward)
            
            # 更新策略网络（简化：使用动作类型的哈希作为索引）
            action_idx = hash(exp.action.action_type) % self.policy_network.action_dim
            self.policy_network.update(state_vec, action_idx, advantage)
    
    def get_optimized_weights(self) -> Dict[str, float]:
        """获取优化后的智能体权重"""
        return self.agent_optimizer.get_weights()
    
    def get_best_recommendations(self, top_k: int = 5) -> List[Tuple[str, float]]:
        """获取最佳建议模板"""
        return self.recommendation_optimizer.get_best_templates(top_k)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        recent_rewards = self.total_rewards[-100:] if self.total_rewards else []
        
        stats = {
            'total_episodes': self.total_episodes,
            'buffer_size': self.replay_buffer.size(),
            'average_reward': np.mean(recent_rewards) if recent_rewards else 0.0,
            'reward_std': np.std(recent_rewards) if recent_rewards else 0.0,
            'agent_weights': self.get_optimized_weights(),
            'best_templates': self.get_best_recommendations(3),
            'rag_enabled': self.enable_rag
        }
        
        # 添加RAG统计
        if self.enable_rag and self.rag_system:
            rag_stats = self.rag_system.get_statistics()
            stats['rag_memories'] = rag_stats.get('total_memories', 0)
            stats['rag_experience_count'] = rag_stats.get('by_type', {}).get('experience', 0)
        
        return stats
    
    def _store_experience_to_rag(self, experience: Experience):
        """存储经验到RAG知识库"""
        try:
            # 构建经验描述
            state_desc = f"睡眠{experience.state.user_data.get('sleep_hours', 7)}小时, " \
                        f"运动{experience.state.user_data.get('exercise_minutes', 30)}分钟, " \
                        f"压力{experience.state.user_data.get('stress_level', 5)}/10"
            
            action_desc = f"{experience.action.action_type}: {experience.action.content}"
            
            content = f"状态: {state_desc}\n动作: {action_desc}\n结果: 奖励={experience.reward:.2f}"
            
            # 计算重要性（奖励绝对值越大越重要）
            importance = min(abs(experience.reward), 1.0)
            
            # 存储到RAG
            self.rag_system.add_memory(
                memory_type=self.MemoryType.EXPERIENCE,
                content=content,
                metadata={
                    'reward': experience.reward,
                    'action_type': experience.action.action_type,
                    'confidence': experience.action.confidence,
                    'timestamp': experience.state.timestamp.isoformat()
                },
                importance=importance
            )
        except Exception as e:
            print(f"存储经验到RAG失败: {e}")
    
    def _retrieve_historical_advantage(self, state: State) -> float:
        """从RAG检索相似历史经验，计算历史优势"""
        try:
            # 构建查询
            query = f"睡眠{state.user_data.get('sleep_hours', 7)}小时, " \
                   f"运动{state.user_data.get('exercise_minutes', 30)}分钟, " \
                   f"压力{state.user_data.get('stress_level', 5)}/10"
            
            # 检索相似经验
            similar_experiences = self.rag_system.search(
                query=query,
                memory_types=[self.MemoryType.EXPERIENCE],
                top_k=5,
                min_importance=0.3
            )
            
            if not similar_experiences:
                return 0.0
            
            # 计算历史平均奖励
            historical_rewards = []
            for exp_memory in similar_experiences:
                reward = exp_memory.metadata.get('reward', 0.0)
                historical_rewards.append(reward)
            
            # 返回历史优势（平均奖励）
            return np.mean(historical_rewards) if historical_rewards else 0.0
            
        except Exception as e:
            print(f"检索历史经验失败: {e}")
            return 0.0
    
    def save(self, filepath: str):
        """保存学习状态"""
        state = {
            'policy_weights': self.policy_network.weights.tolist(),
            'policy_bias': self.policy_network.bias.tolist(),
            'value_weights': self.value_network.weights.tolist(),
            'value_bias': float(self.value_network.bias),
            'agent_weights': dict(self.agent_optimizer.agent_weights),
            'total_episodes': self.total_episodes,
            'total_rewards': self.total_rewards[-1000:]  # 只保存最近1000个
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load(self, filepath: str):
        """加载学习状态"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.policy_network.weights = np.array(state['policy_weights'])
            self.policy_network.bias = np.array(state['policy_bias'])
            self.value_network.weights = np.array(state['value_weights'])
            self.value_network.bias = state['value_bias']
            self.agent_optimizer.agent_weights = defaultdict(
                lambda: 1.0,
                state['agent_weights']
            )
            self.total_episodes = state['total_episodes']
            self.total_rewards = state['total_rewards']
            
            return True
        except Exception as e:
            print(f"加载失败: {e}")
            return False


class SelfEvolvingSystem:
    """自进化系统"""
    
    def __init__(self, meta_agent, knowledge_graph, user_id: str = "default_user"):
        self.meta_agent = meta_agent
        self.knowledge_graph = knowledge_graph
        self.user_id = user_id
        self.learner = ReinforcementLearner(user_id=user_id, enable_rag=True)
        
        # 当前状态
        self.current_state: Optional[State] = None
        self.current_action: Optional[Action] = None
    
    async def process_user_input(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户输入"""
        # 1. 使用元智能体协调
        result = await self.meta_agent.orchestrate(user_data)
        
        # 2. 创建状态和动作
        self.current_state = State(
            user_data=user_data,
            context=result['context']
        )
        
        self.current_action = Action(
            action_id=f"action_{datetime.now().timestamp()}",
            action_type=result['advice'][0]['type'] if result['advice'] else 'general',
            content=result['advice'][0]['message'] if result['advice'] else '',
            agent_weights=result['weights'],
            confidence=result['decision']['confidence']
        )
        
        return result
    
    def receive_feedback(
        self,
        feedback_type: str,
        rating: Optional[float] = None,
        comment: Optional[str] = None
    ):
        """接收用户反馈"""
        if self.current_state is None or self.current_action is None:
            print("警告：没有当前状态或动作")
            return
        
        # 创建反馈
        feedback = Feedback(
            feedback_type=feedback_type,
            rating=rating,
            comment=comment
        )
        
        # 学习
        self.learner.learn(
            state=self.current_state,
            action=self.current_action,
            feedback=feedback
        )
        
        # 更新元智能体的权重
        optimized_weights = self.learner.get_optimized_weights()
        self._update_meta_agent_weights(optimized_weights)
    
    def _update_meta_agent_weights(self, optimized_weights: Dict[str, float]):
        """更新元智能体的基础权重"""
        for capability in self.meta_agent.agent_capabilities:
            if capability.agent_id in optimized_weights:
                capability.base_weight = optimized_weights[capability.agent_id]
    
    def get_learning_progress(self) -> Dict[str, Any]:
        """获取学习进度"""
        stats = self.learner.get_statistics()
        
        return {
            'episodes': stats['total_episodes'],
            'average_reward': stats['average_reward'],
            'improvement': self._calculate_improvement(),
            'agent_weights': stats['agent_weights'],
            'best_strategies': stats['best_templates']
        }
    
    def _calculate_improvement(self) -> float:
        """计算改进程度"""
        if len(self.learner.total_rewards) < 20:
            return 0.0
        
        # 比较最近10次和之前10次的平均奖励
        recent = np.mean(self.learner.total_rewards[-10:])
        previous = np.mean(self.learner.total_rewards[-20:-10])
        
        if previous == 0:
            return 0.0
        
        return (recent - previous) / abs(previous) * 100
