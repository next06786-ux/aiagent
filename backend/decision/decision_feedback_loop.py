"""
决策反馈循环系统
追踪决策结果，生成训练数据，优化LoRA模型
"""
import os
import sys
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.lora.auto_lora_trainer import AutoLoRATrainer
from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType


@dataclass
class DecisionFeedback:
    """决策反馈"""
    feedback_id: str
    user_id: str
    simulation_id: str
    question: str
    predicted_option: str  # AI推荐的选项
    actual_option: str  # 用户实际选择
    predicted_score: float  # AI预测得分
    actual_satisfaction: int  # 实际满意度 1-10
    feedback_time: str
    feedback_text: Optional[str] = None  # 用户文字反馈
    used_for_training: bool = False


class DecisionFeedbackLoop:
    """决策验证与LoRA优化循环"""
    
    def __init__(self):
        self.feedback_dir = "./data/decision_feedback"
        os.makedirs(self.feedback_dir, exist_ok=True)
    
    def record_decision(
        self,
        user_id: str,
        simulation_id: str,
        question: str,
        predicted_option: str,
        predicted_score: float,
        actual_option: str
    ) -> str:
        """
        记录用户的决策
        
        Args:
            user_id: 用户ID
            simulation_id: 模拟ID
            question: 决策问题
            predicted_option: AI推荐的选项
            predicted_score: AI预测得分
            actual_option: 用户实际选择
        
        Returns:
            feedback_id
        """
        feedback_id = f"feedback_{user_id}_{int(datetime.now().timestamp())}"
        
        feedback = DecisionFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            simulation_id=simulation_id,
            question=question,
            predicted_option=predicted_option,
            actual_option=actual_option,
            predicted_score=predicted_score,
            actual_satisfaction=0,  # 待填写
            feedback_time=datetime.now().isoformat()
        )
        
        # 保存反馈
        self._save_feedback(feedback)
        
        print(f"✅ 决策已记录: {feedback_id}")
        print(f"   问题: {question}")
        print(f"   AI推荐: {predicted_option}")
        print(f"   用户选择: {actual_option}")
        
        return feedback_id
    
    def submit_feedback(
        self,
        feedback_id: str,
        actual_satisfaction: int,
        feedback_text: Optional[str] = None
    ) -> bool:
        """
        提交决策反馈（3个月后）
        
        Args:
            feedback_id: 反馈ID
            actual_satisfaction: 实际满意度 1-10
            feedback_text: 文字反馈
        
        Returns:
            是否成功
        """
        feedback = self._load_feedback(feedback_id)
        
        if not feedback:
            print(f"❌ 反馈不存在: {feedback_id}")
            return False
        
        # 更新反馈
        feedback.actual_satisfaction = actual_satisfaction
        feedback.feedback_text = feedback_text
        
        # 保存
        self._save_feedback(feedback)
        
        print(f"✅ 反馈已提交: {feedback_id}")
        print(f"   满意度: {actual_satisfaction}/10")
        
        # 生成训练数据
        self._generate_training_data(feedback)
        
        return True
    
    def _generate_training_data(self, feedback: DecisionFeedback):
        """
        从决策反馈生成LoRA训练数据
        
        策略:
        1. 如果AI推荐正确且用户满意 → 正样本（强化）
        2. 如果AI推荐错误但用户满意 → 学习样本（纠正）
        3. 如果用户不满意 → 负样本（避免）
        """
        user_id = feedback.user_id
        
        # 判断预测准确性
        is_correct = feedback.predicted_option == feedback.actual_option
        is_satisfied = feedback.actual_satisfaction >= 7
        
        # 构造训练对话
        training_conversations = []
        
        if is_correct and is_satisfied:
            # 正样本：AI推荐正确且用户满意
            conversation = {
                "user": f"我在考虑：{feedback.question}",
                "assistant": f"我建议你选择「{feedback.predicted_option}」。这个选择很适合你的性格和目标。",
                "feedback": "positive",
                "satisfaction": feedback.actual_satisfaction
            }
            training_conversations.append(conversation)
            
            print(f"✅ 生成正样本（AI推荐正确且用户满意）")
        
        elif not is_correct and is_satisfied:
            # 学习样本：AI推荐错误但用户选择正确
            conversation = {
                "user": f"我在考虑：{feedback.question}",
                "assistant": f"经过深思熟虑，我认为「{feedback.actual_option}」是更好的选择。",
                "feedback": "corrective",
                "satisfaction": feedback.actual_satisfaction
            }
            training_conversations.append(conversation)
            
            print(f"📚 生成学习样本（纠正AI推荐）")
        
        elif not is_satisfied:
            # 负样本：用户不满意
            if feedback.feedback_text:
                conversation = {
                    "user": f"我在考虑：{feedback.question}",
                    "assistant": f"让我重新分析。{feedback.feedback_text}",
                    "feedback": "negative",
                    "satisfaction": feedback.actual_satisfaction
                }
                training_conversations.append(conversation)
                
                print(f"⚠️ 生成负样本（用户不满意）")
        
        # 保存到RAG系统（作为对话记忆）
        if training_conversations:
            self._save_to_rag(user_id, training_conversations)
            
            # 标记为已用于训练
            feedback.used_for_training = True
            self._save_feedback(feedback)
            
            # 检查是否需要触发训练
            self._check_trigger_training(user_id)
    
    def _save_to_rag(self, user_id: str, conversations: List[Dict]):
        """保存训练对话到RAG系统"""
        try:
            rag = ProductionRAGSystem(user_id)
            
            for conv in conversations:
                content = f"用户: {conv['user']}\nAI: {conv['assistant']}"
                
                rag.add_memory(
                    content=content,
                    memory_type=MemoryType.CONVERSATION,
                    metadata={
                        "feedback_type": conv["feedback"],
                        "satisfaction": conv["satisfaction"],
                        "is_training_data": True
                    }
                )
            
            print(f"💾 训练数据已保存到RAG系统")
            
        except Exception as e:
            print(f"⚠️ 保存到RAG失败: {e}")
    
    def _check_trigger_training(self, user_id: str):
        """检查是否需要触发LoRA训练"""
        # 统计未训练的反馈数量
        feedbacks = self.get_user_feedbacks(user_id)
        untrained_count = sum(1 for f in feedbacks if f.used_for_training and f.actual_satisfaction > 0)
        
        # 如果有5个以上的新反馈，触发训练
        if untrained_count >= 5:
            print(f"\n🚀 检测到 {untrained_count} 个新反馈，触发LoRA训练...")
            self._trigger_lora_training(user_id, priority="high")
    
    def _trigger_lora_training(self, user_id: str, priority: str = "normal"):
        """触发LoRA模型训练"""
        try:
            trainer = AutoLoRATrainer(user_id)
            
            # 如果是高优先级，降低训练间隔要求
            if priority == "high":
                original_interval = trainer.training_config["train_interval_days"]
                trainer.training_config["train_interval_days"] = 0  # 立即训练
            
            # 执行训练
            trainer.auto_train_workflow()
            
            # 恢复原始配置
            if priority == "high":
                trainer.training_config["train_interval_days"] = original_interval
            
            print(f"✅ LoRA训练已触发")
            
        except Exception as e:
            print(f"❌ 触发训练失败: {e}")
    
    def get_user_feedbacks(self, user_id: str) -> List[DecisionFeedback]:
        """获取用户的所有反馈"""
        feedbacks = []
        
        if not os.path.exists(self.feedback_dir):
            return feedbacks
        
        for filename in os.listdir(self.feedback_dir):
            if filename.startswith(f"feedback_{user_id}_") and filename.endswith('.json'):
                filepath = os.path.join(self.feedback_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    feedbacks.append(DecisionFeedback(**data))
        
        # 按时间排序
        feedbacks.sort(key=lambda x: x.feedback_time, reverse=True)
        
        return feedbacks
    
    def get_pending_feedbacks(self, user_id: str, days_threshold: int = 90) -> List[DecisionFeedback]:
        """
        获取待反馈的决策（超过指定天数且未反馈）
        
        Args:
            user_id: 用户ID
            days_threshold: 天数阈值（默认90天）
        
        Returns:
            待反馈列表
        """
        feedbacks = self.get_user_feedbacks(user_id)
        pending = []
        
        now = datetime.now()
        
        for feedback in feedbacks:
            # 已经反馈过的跳过
            if feedback.actual_satisfaction > 0:
                continue
            
            # 计算天数
            feedback_time = datetime.fromisoformat(feedback.feedback_time)
            days_passed = (now - feedback_time).days
            
            # 超过阈值的加入待反馈列表
            if days_passed >= days_threshold:
                pending.append(feedback)
        
        return pending
    
    def calculate_accuracy(self, user_id: str) -> Dict[str, Any]:
        """
        计算AI决策的准确率
        
        Returns:
            统计数据
        """
        feedbacks = self.get_user_feedbacks(user_id)
        
        # 只统计已反馈的
        completed = [f for f in feedbacks if f.actual_satisfaction > 0]
        
        if not completed:
            return {
                "total_decisions": 0,
                "accuracy": 0.0,
                "avg_satisfaction": 0.0,
                "correct_predictions": 0,
                "total_feedbacks": 0
            }
        
        # 计算准确率
        correct = sum(1 for f in completed if f.predicted_option == f.actual_option)
        accuracy = correct / len(completed)
        
        # 计算平均满意度
        avg_satisfaction = sum(f.actual_satisfaction for f in completed) / len(completed)
        
        return {
            "total_decisions": len(feedbacks),
            "total_feedbacks": len(completed),
            "correct_predictions": correct,
            "accuracy": accuracy,
            "avg_satisfaction": avg_satisfaction
        }
    
    def _save_feedback(self, feedback: DecisionFeedback):
        """保存反馈到文件"""
        filepath = os.path.join(self.feedback_dir, f"{feedback.feedback_id}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(feedback), f, ensure_ascii=False, indent=2)
    
    def _load_feedback(self, feedback_id: str) -> Optional[DecisionFeedback]:
        """加载反馈"""
        filepath = os.path.join(self.feedback_dir, f"{feedback_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return DecisionFeedback(**data)


# 测试代码
if __name__ == "__main__":
    loop = DecisionFeedbackLoop()
    
    user_id = "test_user_001"
    
    print("="*60)
    print("决策反馈循环系统测试")
    print("="*60)
    print()
    
    # 1. 记录决策
    print("1. 记录决策...")
    feedback_id = loop.record_decision(
        user_id=user_id,
        simulation_id="sim_test_123",
        question="毕业后应该选择什么？",
        predicted_option="直接工作",
        predicted_score=82.3,
        actual_option="直接工作"
    )
    print()
    
    # 2. 提交反馈（模拟3个月后）
    print("2. 提交反馈（模拟3个月后）...")
    loop.submit_feedback(
        feedback_id=feedback_id,
        actual_satisfaction=8,
        feedback_text="工作很顺利，收入稳定，感觉选择是对的。"
    )
    print()
    
    # 3. 查看统计
    print("3. 查看准确率统计...")
    stats = loop.calculate_accuracy(user_id)
    print(f"   总决策数: {stats['total_decisions']}")
    print(f"   已反馈数: {stats['total_feedbacks']}")
    print(f"   预测准确: {stats['correct_predictions']}")
    print(f"   准确率: {stats['accuracy']:.1%}")
    print(f"   平均满意度: {stats['avg_satisfaction']:.1f}/10")
    print()
    
    # 4. 查看待反馈列表
    print("4. 查看待反馈列表...")
    pending = loop.get_pending_feedbacks(user_id, days_threshold=0)  # 测试用，阈值设为0
    print(f"   待反馈数: {len(pending)}")
    print()
    
    print("="*60)
    print("测试完成")
    print("="*60)
