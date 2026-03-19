"""
自进化混合智能体系统
Hybrid Intelligence System with Self-Evolution

5层架构：
1. 感知层（Perception Layer）- LLM主导
2. 推理层（Reasoning Layer）- 科学模型主导
3. 洞察层（Insight Layer）- LLM主导
4. 决策层（Decision Layer）- LLM主导
5. 交互层（Interaction Layer）- LLM主导
"""
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from .llm_service import get_llm_service
from .conversation_manager import get_conversation_manager


class LayerType(Enum):
    """层类型"""
    PERCEPTION = "perception"  # 感知层
    REASONING = "reasoning"  # 推理层
    INSIGHT = "insight"  # 洞察层
    DECISION = "decision"  # 决策层
    INTERACTION = "interaction"  # 交互层


class HybridIntelligenceSystem:
    """混合智能体系统"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.llm = get_llm_service()
        self.conversation_manager = get_conversation_manager()
        
        # 知识库
        self.knowledge_base = {
            'user_patterns': {},  # 用户行为模式
            'causal_relations': [],  # 因果关系
            'personal_rules': [],  # 个人规则
            'feedback_history': []  # 反馈历史
        }
        
        # 自进化参数
        self.evolution_config = {
            'learning_rate': 0.01,
            'confidence_threshold': 0.7,
            'feedback_weight': 0.3
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        完整的5层处理流程
        
        Args:
            input_data: 输入数据（可以是文本、数据、图像等）
        
        Returns:
            处理结果
        """
        # 1. 感知层：理解用户意图和上下文
        perception_result = self._perception_layer(input_data)
        
        # 2. 推理层：科学计算和量化分析
        reasoning_result = self._reasoning_layer(perception_result)
        
        # 3. 洞察层：深度因果推理
        insight_result = self._insight_layer(reasoning_result)
        
        # 4. 决策层：生成个性化建议
        decision_result = self._decision_layer(insight_result)
        
        # 5. 交互层：自然语言呈现
        interaction_result = self._interaction_layer(decision_result)
        
        # 记录处理历史（用于自进化）
        self._record_processing(input_data, interaction_result)
        
        return interaction_result
    
    def _perception_layer(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        感知层：LLM主导，理解用户意图和上下文
        
        功能：
        - 意图识别
        - 情感分析
        - 上下文理解
        - 多模态融合
        """
        if not self.llm:
            return {
                'intent': 'unknown',
                'emotion': 'neutral',
                'context': input_data,
                'entities': []
            }
        
        # 构建感知提示词
        prompt = f"""
你是一个感知分析专家。请分析以下用户输入，提取关键信息。

用户输入: {json.dumps(input_data, ensure_ascii=False)}

请提供：
1. 用户意图（如：咨询健康、记录数据、寻求建议等）
2. 情感状态（如：焦虑、平静、积极等）
3. 关键实体（如：睡眠、运动、压力等）
4. 上下文信息（如：时间、地点、相关背景）

以JSON格式返回：
{{
    "intent": "用户意图",
    "emotion": "情感状态",
    "entities": ["实体1", "实体2"],
    "context": {{"key": "value"}},
    "urgency": "紧急程度(low/medium/high)"
}}
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的感知分析专家，擅长理解用户意图和情感。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm.chat(messages, temperature=0.3)
            # 尝试解析JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                perception_result = json.loads(json_match.group())
            else:
                perception_result = {
                    'intent': 'general_query',
                    'emotion': 'neutral',
                    'entities': [],
                    'context': input_data,
                    'urgency': 'medium'
                }
            
            perception_result['raw_input'] = input_data
            perception_result['llm_analysis'] = response
            
            return perception_result
            
        except Exception as e:
            print(f"感知层处理失败: {e}")
            return {
                'intent': 'unknown',
                'emotion': 'neutral',
                'entities': [],
                'context': input_data,
                'urgency': 'medium',
                'raw_input': input_data
            }
    
    def _reasoning_layer(self, perception_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        推理层：科学模型主导，量化计算
        
        功能：
        - 健康指标计算
        - 风险评估
        - 趋势预测
        - 数据关联分析
        """
        reasoning_result = {
            'perception': perception_result,
            'quantitative_analysis': {},
            'risk_assessment': {},
            'predictions': {}
        }
        
        # 提取数据
        raw_input = perception_result.get('raw_input', {})
        entities = perception_result.get('entities', [])
        
        # 健康领域的量化分析
        if 'health' in entities or 'sleep' in str(raw_input).lower():
            reasoning_result['quantitative_analysis']['health'] = self._calculate_health_metrics(raw_input)
        
        # 时间管理的量化分析
        if 'time' in entities or 'work' in str(raw_input).lower():
            reasoning_result['quantitative_analysis']['time'] = self._calculate_time_metrics(raw_input)
        
        # 风险评估
        reasoning_result['risk_assessment'] = self._assess_risks(reasoning_result['quantitative_analysis'])
        
        # 趋势预测
        reasoning_result['predictions'] = self._predict_trends(reasoning_result['quantitative_analysis'])
        
        return reasoning_result
    
    def _calculate_health_metrics(self, data: Dict[str, Any]) -> Dict[str, float]:
        """计算健康指标"""
        metrics = {}
        
        # 睡眠分数
        sleep_hours = data.get('sleep_hours', 7)
        metrics['sleep_score'] = min(100, max(0, (sleep_hours / 8) * 100))
        
        # 运动分数
        exercise_minutes = data.get('exercise_minutes', 0)
        metrics['exercise_score'] = min(100, (exercise_minutes / 30) * 100)
        
        # 压力分数
        stress_level = data.get('stress_level', 5)
        metrics['stress_score'] = max(0, 100 - stress_level * 10)
        
        # 综合健康分数
        metrics['overall_health'] = (
            metrics['sleep_score'] * 0.4 +
            metrics['exercise_score'] * 0.3 +
            metrics['stress_score'] * 0.3
        )
        
        return metrics
    
    def _calculate_time_metrics(self, data: Dict[str, Any]) -> Dict[str, float]:
        """计算时间管理指标"""
        metrics = {}
        
        work_hours = data.get('work_hours', 8)
        task_count = data.get('task_count', 5)
        completion_rate = data.get('completion_rate', 70)
        
        # 效率分数
        metrics['efficiency_score'] = completion_rate
        
        # 工作负荷
        metrics['workload'] = min(100, (work_hours / 8) * 100)
        
        # 时间压力
        metrics['time_pressure'] = min(100, (task_count / 5) * 100)
        
        return metrics
    
    def _assess_risks(self, quantitative_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """风险评估"""
        risks = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': []
        }
        
        # 健康风险
        if 'health' in quantitative_analysis:
            health = quantitative_analysis['health']
            if health.get('overall_health', 100) < 60:
                risks['high_risk'].append({
                    'type': 'health',
                    'description': '整体健康状况较差',
                    'score': health['overall_health']
                })
            elif health.get('overall_health', 100) < 75:
                risks['medium_risk'].append({
                    'type': 'health',
                    'description': '健康状况需要改善',
                    'score': health['overall_health']
                })
        
        return risks
    
    def _predict_trends(self, quantitative_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """趋势预测"""
        predictions = {}
        
        # 基于当前数据的简单预测
        if 'health' in quantitative_analysis:
            health = quantitative_analysis['health']
            current_score = health.get('overall_health', 70)
            
            # 预测未来趋势
            if current_score < 70:
                predictions['health_trend'] = {
                    'direction': 'declining',
                    'predicted_score_7days': max(50, current_score - 5),
                    'confidence': 0.7
                }
            else:
                predictions['health_trend'] = {
                    'direction': 'stable',
                    'predicted_score_7days': current_score,
                    'confidence': 0.8
                }
        
        return predictions
    
    def _insight_layer(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        洞察层：LLM主导，深度因果推理
        
        功能：
        - 因果关系分析
        - 模式识别
        - 根本原因分析
        - 长期影响评估
        """
        if not self.llm:
            return {
                'reasoning': reasoning_result,
                'causal_insights': [],
                'patterns': [],
                'root_causes': []
            }
        
        # 构建洞察提示词（简化版，更快响应）
        quantitative = reasoning_result.get('quantitative_analysis', {})
        risks = reasoning_result.get('risk_assessment', {})
        
        prompt = f"""分析以下数据，给出简洁洞察：

数据: {json.dumps(quantitative, ensure_ascii=False)}
风险: {json.dumps(risks, ensure_ascii=False)}

返回JSON格式：
{{
    "causal_insights": [{{"cause": "原因", "effect": "结果", "confidence": 0.8}}],
    "patterns": [{{"pattern": "模式描述"}}],
    "root_causes": ["根本原因"],
    "long_term_impact": "长期影响"
}}"""
        
        messages = [
            {"role": "system", "content": "你是数据分析专家，给出简洁洞察。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm.chat(messages, temperature=0.5)
            
            # 解析JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                insight_result = json.loads(json_match.group())
            else:
                insight_result = {
                    'causal_insights': [],
                    'patterns': [],
                    'root_causes': [],
                    'long_term_impact': ''
                }
            
            insight_result['reasoning'] = reasoning_result
            insight_result['llm_analysis'] = response
            
            return insight_result
            
        except Exception as e:
            print(f"洞察层处理失败: {e}")
            return {
                'reasoning': reasoning_result,
                'causal_insights': [],
                'patterns': [],
                'root_causes': []
            }
    
    def _decision_layer(self, insight_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        决策层：LLM主导，生成个性化建议
        
        功能：
        - 目标设定
        - 行动计划
        - 优先级排序
        - 个性化定制
        """
        if not self.llm:
            return {
                'insight': insight_result,
                'recommendations': [],
                'action_plan': [],
                'priorities': []
            }
        
        # 构建决策提示词（简化版）
        causal_insights = insight_result.get('causal_insights', [])
        root_causes = insight_result.get('root_causes', [])
        
        prompt = f"""基于分析给出建议：

因果: {json.dumps(causal_insights, ensure_ascii=False)}
原因: {json.dumps(root_causes, ensure_ascii=False)}

返回JSON：
{{
    "recommendations": [
        {{
            "title": "建议标题",
            "description": "详细描述",
            "steps": ["步骤1", "步骤2"],
            "priority": "high",
            "expected_impact": "预期效果"
        }}
    ]
}}"""
        
        messages = [
            {"role": "system", "content": "你是决策专家，给出可行建议。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm.chat(messages, temperature=0.6)
            
            # 解析JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision_result = json.loads(json_match.group())
            else:
                decision_result = {'recommendations': []}
            
            decision_result['insight'] = insight_result
            decision_result['llm_analysis'] = response
            
            return decision_result
            
        except Exception as e:
            print(f"决策层处理失败: {e}")
            return {
                'insight': insight_result,
                'recommendations': []
            }
    
    def _interaction_layer(self, decision_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        交互层：LLM主导，自然语言呈现
        
        功能：
        - 自然语言生成
        - 个性化表达
        - 情感适配
        - 对话式交互
        """
        if not self.llm:
            return {
                'decision': decision_result,
                'response': '系统分析完成，请查看建议。',
                'follow_up_questions': []
            }
        
        # 构建交互提示词
        recommendations = decision_result.get('recommendations', [])
        
        prompt = f"""
你是LifeSwarm的AI助手。请将以下分析结果转化为友好、自然的对话回复。

建议列表: {json.dumps(recommendations, ensure_ascii=False)}

要求：
1. 语气友好、温暖、鼓励
2. 简洁明了，避免冗长
3. 突出重点，分点呈现
4. 提供1-2个后续问题，引导用户深入交流

直接返回对话文本，不要JSON格式。
"""
        
        messages = [
            {"role": "system", "content": "你是LifeSwarm的AI助手，友好、专业、关心用户健康。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm.chat(messages, temperature=0.7)
            
            return {
                'decision': decision_result,
                'response': response,
                'timestamp': datetime.now().isoformat(),
                'layer_results': {
                    'perception': decision_result.get('insight', {}).get('reasoning', {}).get('perception', {}),
                    'reasoning': decision_result.get('insight', {}).get('reasoning', {}),
                    'insight': decision_result.get('insight', {}),
                    'decision': decision_result
                }
            }
            
        except Exception as e:
            print(f"交互层处理失败: {e}")
            return {
                'decision': decision_result,
                'response': '分析完成，建议已生成。',
                'timestamp': datetime.now().isoformat()
            }
    
    def _record_processing(self, input_data: Dict[str, Any], output_result: Dict[str, Any]):
        """记录处理历史，用于自进化"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'input': input_data,
            'output': output_result,
            'user_id': self.user_id
        }
        
        # 保存到知识库（实际应该保存到数据库）
        if 'processing_history' not in self.knowledge_base:
            self.knowledge_base['processing_history'] = []
        
        self.knowledge_base['processing_history'].append(record)
    
    def learn_from_feedback(self, feedback: Dict[str, Any]):
        """
        从用户反馈中学习（自进化）
        
        Args:
            feedback: 用户反馈
                - rating: 评分 (1-5)
                - helpful: 是否有帮助
                - comments: 评论
                - action_taken: 是否采取了建议
        """
        # 记录反馈
        self.knowledge_base['feedback_history'].append({
            'timestamp': datetime.now().isoformat(),
            'feedback': feedback
        })
        
        # 更新个人规则
        if feedback.get('helpful') and feedback.get('action_taken'):
            # 正反馈：强化这种模式
            self._reinforce_pattern(feedback)
        elif not feedback.get('helpful'):
            # 负反馈：调整策略
            self._adjust_strategy(feedback)
    
    def _reinforce_pattern(self, feedback: Dict[str, Any]):
        """强化有效模式"""
        # 提取成功模式
        pattern = {
            'type': 'successful_recommendation',
            'context': feedback.get('context', {}),
            'recommendation': feedback.get('recommendation', {}),
            'confidence': min(1.0, feedback.get('rating', 3) / 5.0)
        }
        
        self.knowledge_base['user_patterns'][f"pattern_{len(self.knowledge_base['user_patterns'])}"] = pattern
    
    def _adjust_strategy(self, feedback: Dict[str, Any]):
        """调整策略"""
        # 记录失败案例，用于改进
        adjustment = {
            'type': 'failed_recommendation',
            'context': feedback.get('context', {}),
            'reason': feedback.get('comments', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        if 'adjustments' not in self.knowledge_base:
            self.knowledge_base['adjustments'] = []
        
        self.knowledge_base['adjustments'].append(adjustment)
    
    def get_evolution_status(self) -> Dict[str, Any]:
        """获取自进化状态"""
        return {
            'user_id': self.user_id,
            'patterns_learned': len(self.knowledge_base.get('user_patterns', {})),
            'feedback_count': len(self.knowledge_base.get('feedback_history', [])),
            'processing_count': len(self.knowledge_base.get('processing_history', [])),
            'evolution_config': self.evolution_config
        }


# 全局实例管理
_hybrid_systems = {}

def get_hybrid_system(user_id: str) -> HybridIntelligenceSystem:
    """获取用户的混合智能体系统"""
    global _hybrid_systems
    
    if user_id not in _hybrid_systems:
        _hybrid_systems[user_id] = HybridIntelligenceSystem(user_id)
    
    return _hybrid_systems[user_id]
