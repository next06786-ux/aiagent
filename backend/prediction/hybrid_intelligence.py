"""
混合智能系统 - Phase 2.3
实现个人模型训练、策略选择、知识蒸馏、进化指标
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class IntelligenceStrategy(Enum):
    """智能策略枚举"""
    LLM_ONLY = "llm_only"  # 仅使用LLM
    PERSONAL_ONLY = "personal_only"  # 仅使用个人模型
    HYBRID = "hybrid"  # 混合策略


@dataclass
class PersonalModel:
    """个人模型"""
    user_id: str
    model_id: str
    domain: str  # 领域（health, time, emotion等）
    version: int = 1
    
    # 模型参数
    parameters: Dict[str, float] = field(default_factory=dict)
    
    # 训练数据
    training_samples: int = 0
    training_accuracy: float = 0.0
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 进化指标
    total_samples: int = 0
    confidence: float = 0.0
    accuracy: float = 0.0
    domain_accuracy: float = 0.0


@dataclass
class StrategyDecision:
    """策略决策"""
    task_id: str
    domain: str
    selected_strategy: IntelligenceStrategy
    reasoning: str
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class PersonalModelTrainer:
    """个人模型训练器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.models = {}  # domain -> PersonalModel
        self.training_history = []
        self.feedback_buffer = []
    
    def create_model(self, domain: str) -> PersonalModel:
        """创建个人模型"""
        model = PersonalModel(
            user_id=self.user_id,
            model_id=f"model_{domain}_{datetime.now().timestamp()}",
            domain=domain
        )
        self.models[domain] = model
        return model
    
    def add_training_sample(
        self,
        domain: str,
        features: Dict[str, float],
        label: Any,
        feedback: Optional[str] = None
    ) -> None:
        """添加训练样本"""
        if domain not in self.models:
            self.create_model(domain)
        
        model = self.models[domain]
        
        # 更新训练样本计数
        model.training_samples += 1
        model.total_samples += 1
        
        # 存储反馈
        if feedback:
            self.feedback_buffer.append({
                "domain": domain,
                "features": features,
                "label": label,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            })
    
    def train_model(self, domain: str, learning_rate: float = 0.01) -> Dict[str, Any]:
        """训练个人模型"""
        if domain not in self.models:
            return {"status": "error", "message": f"Model for {domain} not found"}
        
        model = self.models[domain]
        
        if model.training_samples < 5:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 5 samples, got {model.training_samples}"
            }
        
        # 简化的训练过程
        # 在实际应用中，这里应该使用真实的ML算法
        
        # 计算准确率（基于反馈）
        if self.feedback_buffer:
            correct = sum(1 for f in self.feedback_buffer if f.get("feedback") == "correct")
            accuracy = correct / len(self.feedback_buffer)
        else:
            accuracy = 0.5 + (model.training_samples / 100) * 0.3  # 模拟准确率
        
        # 更新模型
        model.training_accuracy = accuracy
        model.accuracy = accuracy
        model.confidence = min(model.training_samples / 50, 1.0)  # 置信度随样本增加
        model.updated_at = datetime.now().isoformat()
        model.version += 1
        
        self.training_history.append({
            "domain": domain,
            "version": model.version,
            "accuracy": accuracy,
            "samples": model.training_samples,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "model_id": model.model_id,
            "version": model.version,
            "accuracy": accuracy,
            "confidence": model.confidence,
            "samples": model.training_samples
        }
    
    def get_model(self, domain: str) -> Optional[PersonalModel]:
        """获取个人模型"""
        return self.models.get(domain)
    
    def get_all_models(self) -> Dict[str, PersonalModel]:
        """获取所有模型"""
        return self.models.copy()
    
    def get_training_history(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取训练历史"""
        if domain:
            return [h for h in self.training_history if h["domain"] == domain]
        return self.training_history


class StrategySelector:
    """策略选择器"""
    
    def __init__(self):
        self.decision_history = []
        self.strategy_performance = {
            IntelligenceStrategy.LLM_ONLY: {"success": 0, "total": 0},
            IntelligenceStrategy.PERSONAL_ONLY: {"success": 0, "total": 0},
            IntelligenceStrategy.HYBRID: {"success": 0, "total": 0}
        }
    
    def select_strategy(
        self,
        domain: str,
        task_type: str,
        personal_model: Optional[PersonalModel],
        user_context: Dict[str, Any]
    ) -> StrategyDecision:
        """
        选择最优策略
        
        决策规则：
        1. 如果个人模型置信度>0.8且准确率>0.75 -> PERSONAL_ONLY
        2. 如果个人模型置信度>0.5 -> HYBRID
        3. 否则 -> LLM_ONLY
        """
        
        if personal_model and personal_model.confidence > 0.8 and personal_model.accuracy > 0.75:
            strategy = IntelligenceStrategy.PERSONAL_ONLY
            reasoning = f"Personal model is highly confident ({personal_model.confidence:.2f}) and accurate ({personal_model.accuracy:.2f})"
            confidence = personal_model.confidence
        
        elif personal_model and personal_model.confidence > 0.5:
            strategy = IntelligenceStrategy.HYBRID
            reasoning = f"Personal model is moderately confident ({personal_model.confidence:.2f}), using hybrid approach"
            confidence = 0.7
        
        else:
            strategy = IntelligenceStrategy.LLM_ONLY
            reasoning = "Personal model not available or not confident enough, using LLM"
            confidence = 0.6
        
        decision = StrategyDecision(
            task_id=f"task_{datetime.now().timestamp()}",
            domain=domain,
            selected_strategy=strategy,
            reasoning=reasoning,
            confidence=confidence
        )
        
        self.decision_history.append(decision)
        return decision
    
    def record_outcome(
        self,
        task_id: str,
        strategy: IntelligenceStrategy,
        success: bool
    ) -> None:
        """记录策略执行结果"""
        self.strategy_performance[strategy]["total"] += 1
        if success:
            self.strategy_performance[strategy]["success"] += 1
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, Any]]:
        """获取策略性能"""
        performance = {}
        for strategy, stats in self.strategy_performance.items():
            total = stats["total"]
            success = stats["success"]
            success_rate = success / total if total > 0 else 0
            
            performance[strategy.value] = {
                "total": total,
                "success": success,
                "success_rate": success_rate
            }
        
        return performance
    
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取决策历史"""
        return [
            {
                "task_id": d.task_id,
                "domain": d.domain,
                "strategy": d.selected_strategy.value,
                "reasoning": d.reasoning,
                "confidence": d.confidence,
                "timestamp": d.timestamp
            }
            for d in self.decision_history[-limit:]
        ]


class KnowledgeDistiller:
    """知识蒸馏器"""
    
    def __init__(self):
        self.distilled_knowledge = {}  # domain -> knowledge
        self.distillation_history = []
    
    def distill_from_llm(
        self,
        domain: str,
        llm_response: str,
        confidence: float
    ) -> Dict[str, Any]:
        """
        从LLM响应中蒸馏知识
        提取关键信息、规则、模式
        """
        
        # 简化的蒸馏过程
        # 在实际应用中，这里应该使用NLP技术提取关键信息
        
        distilled = {
            "domain": domain,
            "source": "llm",
            "content": llm_response,
            "confidence": confidence,
            "extracted_rules": self._extract_rules(llm_response),
            "extracted_patterns": self._extract_patterns(llm_response),
            "timestamp": datetime.now().isoformat()
        }
        
        if domain not in self.distilled_knowledge:
            self.distilled_knowledge[domain] = []
        
        self.distilled_knowledge[domain].append(distilled)
        self.distillation_history.append(distilled)
        
        return distilled
    
    def _extract_rules(self, text: str) -> List[str]:
        """提取规则"""
        # 简化实现：查找包含"if"、"then"、"should"等关键词的句子
        rules = []
        sentences = text.split("。")
        
        for sentence in sentences:
            if any(keyword in sentence for keyword in ["如果", "那么", "应该", "需要", "必须"]):
                rules.append(sentence.strip())
        
        return rules[:5]  # 返回前5条规则
    
    def _extract_patterns(self, text: str) -> List[str]:
        """提取模式"""
        # 简化实现：查找包含"模式"、"趋势"、"规律"等关键词的句子
        patterns = []
        sentences = text.split("。")
        
        for sentence in sentences:
            if any(keyword in sentence for keyword in ["模式", "趋势", "规律", "现象", "特点"]):
                patterns.append(sentence.strip())
        
        return patterns[:5]  # 返回前5个模式
    
    def get_distilled_knowledge(self, domain: str) -> List[Dict[str, Any]]:
        """获取蒸馏的知识"""
        return self.distilled_knowledge.get(domain, [])
    
    def get_distillation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取蒸馏历史"""
        return self.distillation_history[-limit:]


class EvolutionMetricsTracker:
    """进化指标追踪器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.metrics = {
            "total_samples": 0,
            "total_interactions": 0,
            "average_confidence": 0.0,
            "average_accuracy": 0.0,
            "model_count": 0,
            "strategy_diversity": 0.0,
            "knowledge_base_size": 0,
            "evolution_stage": "initial"
        }
        self.metrics_history = []
    
    def update_metrics(
        self,
        trainer: PersonalModelTrainer,
        selector: StrategySelector,
        distiller: KnowledgeDistiller
    ) -> Dict[str, Any]:
        """更新进化指标"""
        
        # 计算总样本数
        total_samples = sum(m.total_samples for m in trainer.get_all_models().values())
        
        # 计算平均置信度和准确率
        models = trainer.get_all_models().values()
        if models:
            avg_confidence = sum(m.confidence for m in models) / len(models)
            avg_accuracy = sum(m.accuracy for m in models) / len(models)
        else:
            avg_confidence = 0.0
            avg_accuracy = 0.0
        
        # 计算策略多样性
        performance = selector.get_strategy_performance()
        strategy_diversity = len([s for s in performance.values() if s["total"] > 0]) / 3
        
        # 计算知识库大小
        knowledge_base_size = sum(
            len(distiller.get_distilled_knowledge(domain))
            for domain in trainer.get_all_models().keys()
        )
        
        # 确定进化阶段
        if total_samples < 50:
            stage = "initial"
        elif total_samples < 200:
            stage = "developing"
        elif total_samples < 500:
            stage = "mature"
        else:
            stage = "advanced"
        
        # 更新指标
        self.metrics = {
            "total_samples": total_samples,
            "total_interactions": selector.decision_history.__len__(),
            "average_confidence": avg_confidence,
            "average_accuracy": avg_accuracy,
            "model_count": len(trainer.get_all_models()),
            "strategy_diversity": strategy_diversity,
            "knowledge_base_size": knowledge_base_size,
            "evolution_stage": stage
        }
        
        # 记录历史
        self.metrics_history.append({
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics.copy()
        })
        
        return self.metrics
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        return self.metrics.copy()
    
    def get_metrics_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取指标历史"""
        return self.metrics_history[-limit:]
    
    def get_evolution_report(self) -> Dict[str, Any]:
        """生成进化报告"""
        return {
            "user_id": self.user_id,
            "current_metrics": self.metrics,
            "evolution_stage": self.metrics["evolution_stage"],
            "progress": {
                "samples_progress": min(self.metrics["total_samples"] / 500, 1.0),
                "confidence_progress": self.metrics["average_confidence"],
                "accuracy_progress": self.metrics["average_accuracy"],
                "model_progress": min(self.metrics["model_count"] / 6, 1.0)
            },
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if self.metrics["total_samples"] < 100:
            recommendations.append("收集更多训练数据以提高模型准确率")
        
        if self.metrics["average_confidence"] < 0.6:
            recommendations.append("个人模型置信度较低，建议增加用户反馈")
        
        if self.metrics["average_accuracy"] < 0.7:
            recommendations.append("模型准确率需要改进，考虑调整特征或算法")
        
        if self.metrics["model_count"] < 3:
            recommendations.append("建议为更多领域训练个人模型")
        
        if self.metrics["strategy_diversity"] < 0.5:
            recommendations.append("策略选择不够多样化，建议优化决策规则")
        
        return recommendations


class HybridIntelligenceSystem:
    """混合智能系统"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.trainer = PersonalModelTrainer(user_id)
        self.selector = StrategySelector()
        self.distiller = KnowledgeDistiller()
        self.metrics_tracker = EvolutionMetricsTracker(user_id)
    
    def process_task(
        self,
        domain: str,
        task_type: str,
        user_context: Dict[str, Any],
        llm_response: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理任务
        1. 选择策略
        2. 执行任务
        3. 收集反馈
        4. 更新模型
        """
        
        # 获取个人模型
        personal_model = self.trainer.get_model(domain)
        
        # 选择策略
        decision = self.selector.select_strategy(
            domain, task_type, personal_model, user_context
        )
        
        # 执行任务（这里简化处理）
        result = {
            "task_id": decision.task_id,
            "domain": domain,
            "strategy": decision.selected_strategy.value,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence
        }
        
        # 如果使用LLM，蒸馏知识
        if llm_response and decision.selected_strategy in [
            IntelligenceStrategy.LLM_ONLY,
            IntelligenceStrategy.HYBRID
        ]:
            distilled = self.distiller.distill_from_llm(
                domain, llm_response, decision.confidence
            )
            result["distilled_knowledge"] = distilled
        
        return result
    
    def add_feedback(
        self,
        domain: str,
        features: Dict[str, float],
        label: Any,
        feedback: str
    ) -> None:
        """添加用户反馈"""
        self.trainer.add_training_sample(domain, features, label, feedback)
    
    def train_models(self) -> Dict[str, Any]:
        """训练所有模型"""
        results = {}
        for domain in self.trainer.get_all_models().keys():
            results[domain] = self.trainer.train_model(domain)
        return results
    
    def update_metrics(self) -> Dict[str, Any]:
        """更新进化指标"""
        return self.metrics_tracker.update_metrics(
            self.trainer, self.selector, self.distiller
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "user_id": self.user_id,
            "models": {
                domain: {
                    "version": model.version,
                    "accuracy": model.accuracy,
                    "confidence": model.confidence,
                    "samples": model.training_samples
                }
                for domain, model in self.trainer.get_all_models().items()
            },
            "strategy_performance": self.selector.get_strategy_performance(),
            "metrics": self.metrics_tracker.get_metrics(),
            "evolution_report": self.metrics_tracker.get_evolution_report()
        }


# 全局实例管理
_systems = {}

def get_hybrid_intelligence_system(user_id: str) -> HybridIntelligenceSystem:
    """获取混合智能系统实例"""
    if user_id not in _systems:
        _systems[user_id] = HybridIntelligenceSystem(user_id)
    return _systems[user_id]

