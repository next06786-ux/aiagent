"""
协同决策智能体架构
Collaborative Agent Architecture - 科学模型 + 大模型深度融合
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from .llm_service import get_llm_service


class ReasoningMode(Enum):
    """推理模式"""
    QUANTITATIVE = "quantitative"  # 纯量化（科学模型）
    QUALITATIVE = "qualitative"    # 纯推理（大模型）
    COLLABORATIVE = "collaborative"  # 协同（融合）


@dataclass
class QuantitativeInsight:
    """量化洞察（来自科学模型）"""
    metrics: Dict[str, float]  # 量化指标
    predictions: Dict[str, Any]  # 预测结果
    anomalies: List[str]  # 检测到的异常
    confidence: float  # 置信度
    
    def to_dict(self) -> Dict:
        return {
            'metrics': self.metrics,
            'predictions': self.predictions,
            'anomalies': self.anomalies,
            'confidence': self.confidence
        }


@dataclass
class QualitativeInsight:
    """定性洞察（来自大模型）"""
    reasoning: str  # 推理过程
    patterns: List[str]  # 识别的模式
    root_causes: List[str]  # 根本原因
    recommendations: List[str]  # 建议
    confidence: float  # 置信度
    
    def to_dict(self) -> Dict:
        return {
            'reasoning': self.reasoning,
            'patterns': self.patterns,
            'root_causes': self.root_causes,
            'recommendations': self.recommendations,
            'confidence': self.confidence
        }


@dataclass
class CollaborativeDecision:
    """协同决策结果"""
    quantitative: QuantitativeInsight  # 量化洞察
    qualitative: Optional[QualitativeInsight]  # 定性洞察
    final_decision: Dict[str, Any]  # 最终决策
    reasoning_mode: ReasoningMode  # 使用的推理模式
    confidence: float  # 综合置信度
    
    def to_dict(self) -> Dict:
        return {
            'quantitative': self.quantitative.to_dict(),
            'qualitative': self.qualitative.to_dict() if self.qualitative else None,
            'final_decision': self.final_decision,
            'reasoning_mode': self.reasoning_mode.value,
            'confidence': self.confidence
        }


class DecisionFusionEngine:
    """决策融合引擎"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def fuse(
        self,
        quantitative: QuantitativeInsight,
        qualitative: Optional[QualitativeInsight]
    ) -> Dict[str, Any]:
        """
        融合量化和定性洞察
        
        Args:
            quantitative: 科学模型的量化结果
            qualitative: 大模型的定性分析
        
        Returns:
            融合后的决策
        """
        if qualitative is None:
            # 只有量化数据，直接返回
            return {
                'type': 'quantitative_only',
                'metrics': quantitative.metrics,
                'predictions': quantitative.predictions,
                'recommendations': self._generate_rule_based_recommendations(quantitative)
            }
        
        # 协同决策：结合量化和定性
        decision = {
            'type': 'collaborative',
            'metrics': quantitative.metrics,
            'predictions': quantitative.predictions,
            'patterns': qualitative.patterns,
            'root_causes': qualitative.root_causes,
            'recommendations': self._merge_recommendations(
                quantitative,
                qualitative
            ),
            'reasoning': qualitative.reasoning
        }
        
        # 如果量化和定性结果冲突，使用大模型调解
        if self._has_conflict(quantitative, qualitative):
            decision['conflict_resolution'] = self._resolve_conflict(
                quantitative,
                qualitative
            )
        
        return decision
    
    def _generate_rule_based_recommendations(
        self,
        quantitative: QuantitativeInsight
    ) -> List[str]:
        """基于规则生成建议（当没有大模型时）"""
        recommendations = []
        
        # 基于异常生成建议
        for anomaly in quantitative.anomalies:
            if 'sleep' in anomaly.lower():
                recommendations.append("建议增加睡眠时间至7-8小时")
            elif 'stress' in anomaly.lower():
                recommendations.append("建议进行压力管理，如冥想或运动")
            elif 'exercise' in anomaly.lower():
                recommendations.append("建议每天至少运动30分钟")
        
        return recommendations
    
    def _merge_recommendations(
        self,
        quantitative: QuantitativeInsight,
        qualitative: QualitativeInsight
    ) -> List[Dict[str, Any]]:
        """合并量化和定性建议"""
        merged = []
        
        # 1. 优先级排序：结合量化严重程度和定性重要性
        for rec in qualitative.recommendations:
            priority = self._calculate_priority(rec, quantitative)
            merged.append({
                'recommendation': rec,
                'priority': priority,
                'source': 'llm',
                'quantitative_support': self._find_quantitative_support(
                    rec,
                    quantitative
                )
            })
        
        # 2. 按优先级排序
        merged.sort(key=lambda x: x['priority'], reverse=True)
        
        return merged
    
    def _calculate_priority(
        self,
        recommendation: str,
        quantitative: QuantitativeInsight
    ) -> float:
        """计算建议的优先级"""
        priority = 0.5  # 基础优先级
        
        # 如果建议与检测到的异常相关，提高优先级
        for anomaly in quantitative.anomalies:
            if any(word in recommendation.lower() for word in anomaly.lower().split()):
                priority += 0.3
        
        # 如果量化指标显示严重问题，提高优先级
        if quantitative.confidence < 0.5:
            priority += 0.2
        
        return min(priority, 1.0)
    
    def _find_quantitative_support(
        self,
        recommendation: str,
        quantitative: QuantitativeInsight
    ) -> Dict[str, Any]:
        """为建议找到量化支持"""
        support = {}
        
        # 查找相关的量化指标
        for key, value in quantitative.metrics.items():
            if key.lower() in recommendation.lower():
                support[key] = value
        
        return support
    
    def _has_conflict(
        self,
        quantitative: QuantitativeInsight,
        qualitative: QualitativeInsight
    ) -> bool:
        """检测量化和定性结果是否冲突"""
        # 简单实现：检查置信度差异
        return abs(quantitative.confidence - qualitative.confidence) > 0.3
    
    def _resolve_conflict(
        self,
        quantitative: QuantitativeInsight,
        qualitative: QualitativeInsight
    ) -> str:
        """解决冲突"""
        if self.llm_service:
            prompt = f"""
量化分析显示置信度为 {quantitative.confidence:.2f}，
定性分析显示置信度为 {qualitative.confidence:.2f}。

量化指标: {json.dumps(quantitative.metrics, ensure_ascii=False)}
定性推理: {qualitative.reasoning}

请分析这两个结果为什么会有差异，并给出你的判断。
"""
            messages = [
                {"role": "system", "content": "你是一个决策分析专家，擅长综合量化和定性信息。"},
                {"role": "user", "content": prompt}
            ]
            return self.llm_service.chat(messages)
        
        return "量化和定性分析存在差异，建议综合考虑两方面信息。"


class CollaborativeHealthAgent:
    """协同健康智能体"""
    
    def __init__(self, base_agent):
        self.base_agent = base_agent
        self.llm_service = get_llm_service()
        self.fusion_engine = DecisionFusionEngine()
    
    def analyze(
        self,
        health_data: Dict[str, Any],
        mode: ReasoningMode = ReasoningMode.COLLABORATIVE
    ) -> CollaborativeDecision:
        """
        协同分析健康数据
        
        Args:
            health_data: 健康数据
            mode: 推理模式
        
        Returns:
            协同决策结果
        """
        # 1. 量化层：科学模型计算
        quantitative = self._quantitative_analysis(health_data)
        
        # 2. 定性层：大模型推理（如果启用）
        qualitative = None
        if mode in [ReasoningMode.QUALITATIVE, ReasoningMode.COLLABORATIVE]:
            if self.llm_service:
                qualitative = self._qualitative_analysis(health_data, quantitative)
        
        # 3. 融合层：决策融合
        final_decision = self.fusion_engine.fuse(quantitative, qualitative)
        
        # 4. 计算综合置信度
        confidence = self._calculate_confidence(quantitative, qualitative)
        
        return CollaborativeDecision(
            quantitative=quantitative,
            qualitative=qualitative,
            final_decision=final_decision,
            reasoning_mode=mode,
            confidence=confidence
        )
    
    def _quantitative_analysis(self, health_data: Dict[str, Any]) -> QuantitativeInsight:
        """量化分析（科学模型）"""
        # 更新智能体状态
        self.base_agent.update(health_data)
        
        # 模拟未来状态
        prediction = self.base_agent.simulate(days=7)
        
        # 提取关键指标
        metrics = {
            'health_score': self.base_agent.state.get('health_score', 0),
            'sleep_debt': self.base_agent.state.get('sleep_debt', 0),
            'stress_level': self.base_agent.state.get('stress_level', 0),
            'energy_level': self.base_agent.state.get('energy_level', 0),
            'immune_strength': self.base_agent.state.get('immune_strength', 0)
        }
        
        # 检测异常
        anomalies = []
        if metrics['health_score'] < 60:
            anomalies.append("健康分数低于正常水平")
        if metrics['sleep_debt'] > 5:
            anomalies.append("睡眠债务累积严重")
        if metrics['stress_level'] > 7:
            anomalies.append("压力水平过高")
        if metrics['energy_level'] < 0.4:
            anomalies.append("能量水平不足")
        
        # 计算置信度（基于数据完整性）
        confidence = self._calculate_quantitative_confidence(health_data)
        
        return QuantitativeInsight(
            metrics=metrics,
            predictions=prediction if isinstance(prediction, dict) else {},
            anomalies=anomalies,
            confidence=confidence
        )
    
    def _qualitative_analysis(
        self,
        health_data: Dict[str, Any],
        quantitative: QuantitativeInsight
    ) -> QualitativeInsight:
        """定性分析（大模型推理）"""
        prompt = f"""
你是一个健康分析专家。请深度分析以下健康数据和量化指标。

用户健康数据：
{json.dumps(health_data, ensure_ascii=False, indent=2)}

量化分析结果：
- 健康分数: {quantitative.metrics.get('health_score', 0):.1f}
- 睡眠债务: {quantitative.metrics.get('sleep_debt', 0):.1f} 小时
- 压力水平: {quantitative.metrics.get('stress_level', 0):.1f}/10
- 能量水平: {quantitative.metrics.get('energy_level', 0):.2f}
- 免疫力: {quantitative.metrics.get('immune_strength', 0):.2f}

检测到的异常：
{chr(10).join(f'- {a}' for a in quantitative.anomalies) if quantitative.anomalies else '无'}

请提供：
1. 深度推理：分析这些数据背后的模式和因果关系
2. 识别模式：找出可能被量化分析忽略的隐藏模式
3. 根本原因：分析问题的根本原因（不只是表面症状）
4. 具体建议：给出3-5条可操作的建议

请以 JSON 格式返回：
{{
    "reasoning": "你的推理过程",
    "patterns": ["模式1", "模式2"],
    "root_causes": ["原因1", "原因2"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}
"""
        
        messages = [
            {"role": "system", "content": "你是一个健康分析专家，擅长深度推理和模式识别。请以 JSON 格式返回分析结果。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm_service.chat(messages, temperature=0.7)
            
            # 尝试解析 JSON
            try:
                # 提取 JSON 部分（可能包含在 markdown 代码块中）
                if '```json' in response:
                    json_str = response.split('```json')[1].split('```')[0].strip()
                elif '```' in response:
                    json_str = response.split('```')[1].split('```')[0].strip()
                else:
                    json_str = response
                
                result = json.loads(json_str)
                
                return QualitativeInsight(
                    reasoning=result.get('reasoning', ''),
                    patterns=result.get('patterns', []),
                    root_causes=result.get('root_causes', []),
                    recommendations=result.get('recommendations', []),
                    confidence=0.8  # 大模型的置信度
                )
            except json.JSONDecodeError:
                # JSON 解析失败，使用文本解析
                return self._parse_text_response(response)
        
        except Exception as e:
            print(f"定性分析失败: {e}")
            return QualitativeInsight(
                reasoning="大模型分析失败",
                patterns=[],
                root_causes=[],
                recommendations=[],
                confidence=0.0
            )
    
    def _parse_text_response(self, response: str) -> QualitativeInsight:
        """解析文本响应（当 JSON 解析失败时）"""
        lines = response.split('\n')
        
        reasoning = ""
        patterns = []
        root_causes = []
        recommendations = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '推理' in line or 'reasoning' in line.lower():
                current_section = 'reasoning'
            elif '模式' in line or 'pattern' in line.lower():
                current_section = 'patterns'
            elif '原因' in line or 'cause' in line.lower():
                current_section = 'root_causes'
            elif '建议' in line or 'recommendation' in line.lower():
                current_section = 'recommendations'
            elif current_section:
                if line.startswith(('-', '•', '*')) or line[0].isdigit():
                    content = line.lstrip('-•*0123456789. ')
                    if current_section == 'patterns':
                        patterns.append(content)
                    elif current_section == 'root_causes':
                        root_causes.append(content)
                    elif current_section == 'recommendations':
                        recommendations.append(content)
                elif current_section == 'reasoning':
                    reasoning += line + " "
        
        return QualitativeInsight(
            reasoning=reasoning.strip(),
            patterns=patterns,
            root_causes=root_causes,
            recommendations=recommendations,
            confidence=0.7
        )
    
    def _calculate_quantitative_confidence(self, health_data: Dict[str, Any]) -> float:
        """计算量化分析的置信度"""
        # 基于数据完整性
        required_fields = ['sleep_hours', 'exercise_minutes', 'stress_level']
        present_fields = sum(1 for field in required_fields if field in health_data)
        
        return present_fields / len(required_fields)
    
    def _calculate_confidence(
        self,
        quantitative: QuantitativeInsight,
        qualitative: Optional[QualitativeInsight]
    ) -> float:
        """计算综合置信度"""
        if qualitative is None:
            return quantitative.confidence
        
        # 加权平均：量化 60%，定性 40%
        return 0.6 * quantitative.confidence + 0.4 * qualitative.confidence


def create_collaborative_agents(digital_twin) -> Dict[str, CollaborativeHealthAgent]:
    """
    为数字孪生创建协同智能体
    
    Args:
        digital_twin: 数字孪生实例
    
    Returns:
        协同智能体字典
    """
    agents = {}
    
    if hasattr(digital_twin, 'health_agent'):
        agents['health'] = CollaborativeHealthAgent(digital_twin.health_agent)
    
    # TODO: 为其他智能体创建协同版本
    # agents['time'] = CollaborativeTimeAgent(digital_twin.time_agent)
    # agents['emotion'] = CollaborativeEmotionAgent(digital_twin.emotion_agent)
    # ...
    
    return agents
