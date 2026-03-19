"""
元智能体（Meta-Agent）
系统的"指挥家" - 协调所有智能体，动态权重分配，涌现模式检测
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import numpy as np
from collections import defaultdict


class AgentType(Enum):
    """智能体类型"""
    SCIENTIFIC = "scientific"
    LLM = "llm"
    HYBRID = "hybrid"


@dataclass
class AgentCapability:
    """智能体能力描述"""
    agent_id: str
    agent_type: AgentType
    domain: str
    capabilities: List[str]
    strengths: List[str]
    weaknesses: List[str]
    base_weight: float = 1.0
    performance_history: List[float] = field(default_factory=list)


@dataclass
class ContextSignal:
    """上下文信号"""
    user_state: Dict[str, Any]
    data_quality: float
    urgency: float
    complexity: float
    domain: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResult:
    """智能体结果"""
    agent_id: str
    predictions: Dict[str, Any]
    confidence: float
    reasoning: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class EmergentPattern:
    """涌现模式"""
    pattern_type: str
    description: str
    involved_agents: List[str]
    confidence: float
    evidence: Dict[str, Any]


class DynamicWeightCalculator:
    """动态权重计算器"""
    
    def __init__(self):
        self.weight_history = defaultdict(list)
    
    def calculate_weights(
        self,
        agents: List[AgentCapability],
        context: ContextSignal
    ) -> Dict[str, float]:
        """动态计算智能体权重"""
        weights = {}
        
        for agent in agents:
            weight = self._calculate_single_weight(agent, context)
            weights[agent.agent_id] = weight
            self.weight_history[agent.agent_id].append(weight)
        
        # 归一化
        total = sum(weights.values())
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}
        
        return weights
    
    def _calculate_single_weight(
        self,
        agent: AgentCapability,
        context: ContextSignal
    ) -> float:
        """计算单个智能体的权重"""
        weight = agent.base_weight
        
        # 1. 领域匹配度
        if agent.domain == context.domain:
            weight *= 1.5
        
        # 2. 数据质量适配
        if agent.agent_type == AgentType.SCIENTIFIC:
            weight *= context.data_quality
        elif agent.agent_type == AgentType.LLM:
            weight *= (1.0 + (1.0 - context.data_quality) * 0.5)
        
        # 3. 复杂度适配
        if context.complexity > 0.7:
            if agent.agent_type == AgentType.LLM:
                weight *= 1.3
        else:
            if agent.agent_type == AgentType.SCIENTIFIC:
                weight *= 1.2
        
        # 4. 历史表现
        if agent.performance_history:
            avg_performance = np.mean(agent.performance_history[-10:])
            weight *= (0.5 + avg_performance)
        
        # 5. 紧急度调整
        if context.urgency > 0.8:
            if agent.agent_type == AgentType.SCIENTIFIC:
                weight *= 1.2
        
        return max(weight, 0.1)


class EmergenceDetector:
    """涌现模式检测器"""
    
    def detect(
        self,
        results: List[AgentResult],
        context: ContextSignal
    ) -> List[EmergentPattern]:
        """检测智能体之间的涌现模式"""
        patterns = []
        
        # 1. 一致性涌现
        consensus = self._detect_consensus(results)
        if consensus:
            patterns.append(consensus)
        
        # 2. 互补性涌现
        complementary = self._detect_complementary(results)
        if complementary:
            patterns.append(complementary)
        
        # 3. 矛盾性涌现
        conflicts = self._detect_conflicts(results)
        patterns.extend(conflicts)
        
        return patterns
    
    def _detect_consensus(self, results: List[AgentResult]) -> Optional[EmergentPattern]:
        """检测一致性模式"""
        if len(results) < 2:
            return None
        
        confidences = [r.confidence for r in results]
        avg_confidence = np.mean(confidences)
        
        if avg_confidence > 0.8 and np.std(confidences) < 0.1:
            return EmergentPattern(
                pattern_type="consensus",
                description="所有智能体高度一致，预测可信度极高",
                involved_agents=[r.agent_id for r in results],
                confidence=avg_confidence,
                evidence={"confidences": confidences}
            )
        
        return None
    
    def _detect_complementary(self, results: List[AgentResult]) -> Optional[EmergentPattern]:
        """检测互补性模式"""
        scientific_results = [r for r in results if 'scientific' in r.agent_id]
        llm_results = [r for r in results if 'llm' in r.agent_id]
        
        if scientific_results and llm_results:
            return EmergentPattern(
                pattern_type="complementary",
                description="科学模型提供量化基础，大模型提供深度洞察",
                involved_agents=[r.agent_id for r in results],
                confidence=0.8,
                evidence={
                    "scientific_count": len(scientific_results),
                    "llm_count": len(llm_results)
                }
            )
        
        return None
    
    def _detect_conflicts(self, results: List[AgentResult]) -> List[EmergentPattern]:
        """检测矛盾模式"""
        conflicts = []
        
        for i, r1 in enumerate(results):
            for r2 in results[i+1:]:
                if abs(r1.confidence - r2.confidence) > 0.4:
                    conflicts.append(EmergentPattern(
                        pattern_type="conflict",
                        description=f"{r1.agent_id} 和 {r2.agent_id} 的预测存在显著差异",
                        involved_agents=[r1.agent_id, r2.agent_id],
                        confidence=0.7,
                        evidence={
                            "confidence_diff": abs(r1.confidence - r2.confidence)
                        }
                    ))
        
        return conflicts


class AgentSelector:
    """智能体选择器"""
    
    def select(
        self,
        available_agents: List[AgentCapability],
        context: ContextSignal,
        max_agents: int = 6
    ) -> List[AgentCapability]:
        """智能选择要调用的智能体"""
        scored_agents = []
        
        for agent in available_agents:
            score = self._calculate_relevance_score(agent, context)
            scored_agents.append((score, agent))
        
        scored_agents.sort(key=lambda x: x[0], reverse=True)
        
        selected = [agent for _, agent in scored_agents[:max_agents]]
        
        return selected
    
    def _calculate_relevance_score(
        self,
        agent: AgentCapability,
        context: ContextSignal
    ) -> float:
        """计算智能体的相关性分数"""
        score = 0.0
        
        # 领域匹配
        if agent.domain == context.domain:
            score += 10.0
        
        # 能力匹配
        for capability in agent.capabilities:
            if capability.lower() in str(context.user_state).lower():
                score += 2.0
        
        # 优势场景匹配
        if context.complexity > 0.7 and "complex_reasoning" in agent.strengths:
            score += 5.0
        
        if context.data_quality < 0.5 and "low_data" in agent.strengths:
            score += 5.0
        
        return score


class MetaAgent:
    """元智能体 - 系统的大脑"""
    
    def __init__(self):
        self.weight_calculator = DynamicWeightCalculator()
        self.emergence_detector = EmergenceDetector()
        self.agent_selector = AgentSelector()
        self.registered_agents: Dict[str, Any] = {}
        self.agent_capabilities: List[AgentCapability] = []
    
    def register_agent(
        self,
        agent_id: str,
        agent_instance: Any,
        capability: AgentCapability
    ):
        """注册智能体"""
        self.registered_agents[agent_id] = agent_instance
        self.agent_capabilities.append(capability)
    
    async def orchestrate(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """协调所有智能体"""
        # 1. 理解用户情况
        context = self._understand_context(user_data)
        
        # 2. 选择要调用的智能体
        selected_agents = self.agent_selector.select(
            self.agent_capabilities,
            context
        )
        
        # 3. 动态分配权重
        weights = self.weight_calculator.calculate_weights(
            selected_agents,
            context
        )
        
        # 4. 并行调用智能体
        results = await self._parallel_call(selected_agents, user_data)
        
        # 5. 加权融合
        decision = self._weighted_fusion(results, weights)
        
        # 6. 检测涌现模式
        emergent_patterns = self.emergence_detector.detect(results, context)
        
        # 7. 生成最终建议
        final_advice = self._generate_advice(decision, emergent_patterns, context)
        
        return {
            "context": {
                "domain": context.domain,
                "data_quality": context.data_quality,
                "urgency": context.urgency,
                "complexity": context.complexity
            },
            "selected_agents": [a.agent_id for a in selected_agents],
            "weights": weights,
            "agent_results": [
                {
                    "agent_id": r.agent_id,
                    "confidence": r.confidence,
                    "execution_time": r.execution_time
                }
                for r in results
            ],
            "emergent_patterns": [
                {
                    "type": p.pattern_type,
                    "description": p.description,
                    "confidence": p.confidence
                }
                for p in emergent_patterns
            ],
            "decision": decision,
            "advice": final_advice
        }
    
    def _understand_context(self, user_data: Dict[str, Any]) -> ContextSignal:
        """理解用户情况"""
        required_fields = ['sleep_hours', 'exercise_minutes', 'stress_level']
        present = sum(1 for f in required_fields if f in user_data)
        data_quality = present / len(required_fields)
        
        urgency = 0.5
        if user_data.get('stress_level', 0) > 8:
            urgency = 0.9
        elif user_data.get('health_score', 100) < 50:
            urgency = 0.8
        
        complexity = 0.5
        if len(user_data) > 10:
            complexity = 0.7
        if 'symptoms' in user_data and len(user_data.get('symptoms', [])) > 3:
            complexity = 0.8
        
        domain = "health"
        if 'work_hours' in user_data or 'meetings' in user_data:
            domain = "time"
        if 'mood' in user_data or 'emotion' in user_data:
            domain = "emotion"
        
        return ContextSignal(
            user_state=user_data,
            data_quality=data_quality,
            urgency=urgency,
            complexity=complexity,
            domain=domain
        )
    
    async def _parallel_call(
        self,
        agents: List[AgentCapability],
        user_data: Dict[str, Any]
    ) -> List[AgentResult]:
        """并行调用智能体"""
        tasks = []
        
        for agent_cap in agents:
            agent = self.registered_agents.get(agent_cap.agent_id)
            if agent:
                task = self._call_agent(agent, agent_cap.agent_id, user_data)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for result in results:
            if isinstance(result, AgentResult):
                valid_results.append(result)
        
        return valid_results
    
    async def _call_agent(
        self,
        agent: Any,
        agent_id: str,
        user_data: Dict[str, Any]
    ) -> AgentResult:
        """调用单个智能体"""
        start_time = datetime.now()
        
        try:
            if hasattr(agent, 'analyze'):
                result = agent.analyze(user_data)
            elif hasattr(agent, 'predict'):
                result = agent.predict(user_data)
            else:
                result = {"predictions": {}, "confidence": 0.5}
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResult(
                agent_id=agent_id,
                predictions=result.get('predictions', {}),
                confidence=result.get('confidence', 0.5),
                reasoning=result.get('reasoning'),
                execution_time=execution_time
            )
        
        except Exception as e:
            print(f"Agent {agent_id} failed: {e}")
            return AgentResult(
                agent_id=agent_id,
                predictions={},
                confidence=0.0,
                execution_time=0.0
            )
    
    def _weighted_fusion(
        self,
        results: List[AgentResult],
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """加权融合智能体结果"""
        if not results:
            return {}
        
        fused_predictions = {}
        fused_confidence = 0.0
        
        for result in results:
            weight = weights.get(result.agent_id, 0.0)
            fused_confidence += result.confidence * weight
            
            for key, value in result.predictions.items():
                if key not in fused_predictions:
                    fused_predictions[key] = []
                fused_predictions[key].append({
                    "value": value,
                    "weight": weight,
                    "agent": result.agent_id
                })
        
        final_predictions = {}
        for key, values in fused_predictions.items():
            if isinstance(values[0]["value"], (int, float)):
                weighted_sum = sum(v["value"] * v["weight"] for v in values)
                final_predictions[key] = weighted_sum
            else:
                final_predictions[key] = max(values, key=lambda x: x["weight"])["value"]
        
        return {
            "predictions": final_predictions,
            "confidence": fused_confidence,
            "contributing_agents": len(results)
        }
    
    def _generate_advice(
        self,
        decision: Dict[str, Any],
        emergent_patterns: List[EmergentPattern],
        context: ContextSignal
    ) -> List[Dict[str, Any]]:
        """生成最终建议"""
        advice = []
        
        predictions = decision.get("predictions", {})
        confidence = decision.get("confidence", 0.0)
        
        if confidence > 0.7:
            advice.append({
                "type": "high_confidence",
                "message": "多个智能体高度一致，建议立即采取行动",
                "priority": "high",
                "predictions": predictions
            })
        elif confidence < 0.4:
            advice.append({
                "type": "low_confidence",
                "message": "预测不确定性较高，建议收集更多数据",
                "priority": "medium",
                "suggestions": ["增加数据采集频率", "补充关键信息"]
            })
        
        for pattern in emergent_patterns:
            if pattern.pattern_type == "consensus":
                advice.append({
                    "type": "consensus_detected",
                    "message": pattern.description,
                    "priority": "high",
                    "confidence": pattern.confidence
                })
            elif pattern.pattern_type == "conflict":
                advice.append({
                    "type": "conflict_detected",
                    "message": pattern.description,
                    "priority": "medium",
                    "suggestion": "需要人工判断或收集更多信息"
                })
        
        if context.urgency > 0.8:
            advice.insert(0, {
                "type": "urgent",
                "message": "检测到紧急情况，请立即关注",
                "priority": "critical"
            })
        
        return advice


def create_meta_agent_system(digital_twin) -> MetaAgent:
    """创建元智能体系统"""
    meta_agent = MetaAgent()
    
    if hasattr(digital_twin, 'health_agent'):
        meta_agent.register_agent(
            "health_scientific",
            digital_twin.health_agent,
            AgentCapability(
                agent_id="health_scientific",
                agent_type=AgentType.SCIENTIFIC,
                domain="health",
                capabilities=["health_prediction", "anomaly_detection"],
                strengths=["quantitative_analysis", "high_data_quality"],
                weaknesses=["complex_reasoning", "low_data"]
            )
        )
    
    return meta_agent
