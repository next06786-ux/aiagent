"""
知识蒸馏模块
Knowledge Distillation - 从大模型到个人小模型

实现渐进式个性化：
1. 初期：完全依赖大模型（Qwen3.5-Plus）
2. 中期：大模型 + 个人模型混合
3. 后期：主要使用个人模型，大模型辅助
"""
import os
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from .llm_service import get_llm_service


class KnowledgeDistillation:
    """知识蒸馏器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.llm = get_llm_service()
        
        # 训练数据收集
        self.training_data = {
            'inputs': [],  # 输入数据
            'outputs': [],  # 大模型输出
            'feedbacks': [],  # 用户反馈
            'contexts': []  # 上下文信息
        }
        
        # 个人模型状态
        self.personal_model = {
            'rules': {},  # 个人规则
            'patterns': {},  # 行为模式
            'preferences': {},  # 偏好设置
            'confidence': 0.0  # 模型置信度
        }
        
        # 蒸馏配置
        self.config = {
            'min_samples': 50,  # 最少训练样本数
            'confidence_threshold': 0.7,  # 置信度阈值
            'distillation_rate': 0.1,  # 蒸馏速率
            'update_frequency': 10  # 更新频率（每N次交互）
        }
        
        # 统计信息
        self.stats = {
            'total_interactions': 0,
            'llm_calls': 0,
            'personal_model_calls': 0,
            'hybrid_calls': 0,
            'last_distillation': None
        }
    
    def collect_training_sample(
        self,
        input_data: Dict[str, Any],
        llm_output: Dict[str, Any],
        user_feedback: Optional[Dict[str, Any]] = None
    ):
        """
        收集训练样本
        
        Args:
            input_data: 输入数据
            llm_output: 大模型输出
            user_feedback: 用户反馈（可选）
        """
        sample = {
            'timestamp': datetime.now().isoformat(),
            'input': input_data,
            'output': llm_output,
            'feedback': user_feedback,
            'context': self._extract_context(input_data)
        }
        
        self.training_data['inputs'].append(input_data)
        self.training_data['outputs'].append(llm_output)
        self.training_data['feedbacks'].append(user_feedback)
        self.training_data['contexts'].append(sample['context'])
        
        self.stats['total_interactions'] += 1
        
        # 定期触发蒸馏
        if self.stats['total_interactions'] % self.config['update_frequency'] == 0:
            self.distill_knowledge()
    
    def _extract_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取上下文特征"""
        context = {
            'time_of_day': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'data_type': list(input_data.keys()),
            'data_size': len(str(input_data))
        }
        
        # 提取领域信息
        if 'sleep_hours' in input_data or 'exercise_minutes' in input_data:
            context['domain'] = 'health'
        elif 'work_hours' in input_data or 'task_count' in input_data:
            context['domain'] = 'time'
        else:
            context['domain'] = 'general'
        
        return context
    
    def distill_knowledge(self):
        """
        执行知识蒸馏
        
        从大模型的输出中提取规则和模式，构建个人模型
        """
        if len(self.training_data['inputs']) < self.config['min_samples']:
            print(f"训练样本不足: {len(self.training_data['inputs'])}/{self.config['min_samples']}")
            return
        
        print(f"开始知识蒸馏，样本数: {len(self.training_data['inputs'])}")
        
        # 1. 提取规则
        self._extract_rules()
        
        # 2. 识别模式
        self._identify_patterns()
        
        # 3. 学习偏好
        self._learn_preferences()
        
        # 4. 更新置信度
        self._update_confidence()
        
        self.stats['last_distillation'] = datetime.now().isoformat()
        
        print(f"知识蒸馏完成，个人模型置信度: {self.personal_model['confidence']:.2f}")
    
    def _extract_rules(self):
        """提取个人规则"""
        # 分析输入-输出对，提取规则
        rules = defaultdict(list)
        
        for i, (input_data, output_data, feedback) in enumerate(zip(
            self.training_data['inputs'],
            self.training_data['outputs'],
            self.training_data['feedbacks']
        )):
            # 只从正反馈中学习
            if feedback and feedback.get('helpful', False):
                # 提取条件-动作规则
                condition = self._extract_condition(input_data)
                action = self._extract_action(output_data)
                
                if condition and action:
                    rule_key = f"{condition['type']}_{condition['value_range']}"
                    rules[rule_key].append({
                        'condition': condition,
                        'action': action,
                        'confidence': feedback.get('rating', 3) / 5.0
                    })
        
        # 合并相似规则
        for rule_key, rule_list in rules.items():
            if len(rule_list) >= 3:  # 至少出现3次才认为是有效规则
                avg_confidence = np.mean([r['confidence'] for r in rule_list])
                self.personal_model['rules'][rule_key] = {
                    'condition': rule_list[0]['condition'],
                    'action': rule_list[0]['action'],
                    'confidence': avg_confidence,
                    'frequency': len(rule_list)
                }
    
    def _extract_condition(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取条件"""
        # 简化的条件提取
        if 'sleep_hours' in input_data:
            sleep_hours = input_data['sleep_hours']
            if sleep_hours < 6:
                return {'type': 'sleep', 'value_range': 'low', 'value': sleep_hours}
            elif sleep_hours < 7:
                return {'type': 'sleep', 'value_range': 'medium', 'value': sleep_hours}
            else:
                return {'type': 'sleep', 'value_range': 'good', 'value': sleep_hours}
        
        return None
    
    def _extract_action(self, output_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取动作"""
        # 从输出中提取建议
        if 'decision' in output_data:
            recommendations = output_data['decision'].get('recommendations', [])
            if recommendations:
                return {
                    'type': 'recommendation',
                    'content': recommendations[0] if isinstance(recommendations, list) else recommendations
                }
        
        return None
    
    def _identify_patterns(self):
        """识别行为模式"""
        # 时间模式
        time_patterns = defaultdict(list)
        
        for context, input_data in zip(self.training_data['contexts'], self.training_data['inputs']):
            hour = context.get('time_of_day', 0)
            domain = context.get('domain', 'general')
            
            time_patterns[f"{domain}_{hour}"].append(input_data)
        
        # 保存频繁模式
        for pattern_key, occurrences in time_patterns.items():
            if len(occurrences) >= 5:  # 至少出现5次
                self.personal_model['patterns'][pattern_key] = {
                    'frequency': len(occurrences),
                    'typical_data': self._aggregate_data(occurrences)
                }
    
    def _aggregate_data(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """聚合数据"""
        aggregated = {}
        
        # 计算数值字段的平均值
        numeric_fields = ['sleep_hours', 'exercise_minutes', 'stress_level', 'work_hours']
        
        for field in numeric_fields:
            values = [d.get(field) for d in data_list if field in d]
            if values:
                aggregated[field] = np.mean(values)
        
        return aggregated
    
    def _learn_preferences(self):
        """学习用户偏好"""
        # 从反馈中学习偏好
        preferences = defaultdict(list)
        
        for feedback in self.training_data['feedbacks']:
            if feedback:
                # 偏好的建议类型
                if 'recommendation_type' in feedback:
                    rec_type = feedback['recommendation_type']
                    rating = feedback.get('rating', 3)
                    preferences[rec_type].append(rating)
        
        # 计算偏好分数
        for pref_type, ratings in preferences.items():
            if ratings:
                self.personal_model['preferences'][pref_type] = {
                    'score': np.mean(ratings),
                    'count': len(ratings)
                }
    
    def _update_confidence(self):
        """更新个人模型置信度"""
        # 基于多个因素计算置信度
        factors = []
        
        # 1. 样本数量
        sample_factor = min(1.0, len(self.training_data['inputs']) / 200)
        factors.append(sample_factor)
        
        # 2. 规则数量
        rule_factor = min(1.0, len(self.personal_model['rules']) / 20)
        factors.append(rule_factor)
        
        # 3. 正反馈比例
        positive_feedbacks = sum(
            1 for f in self.training_data['feedbacks']
            if f and f.get('helpful', False)
        )
        total_feedbacks = sum(1 for f in self.training_data['feedbacks'] if f)
        
        if total_feedbacks > 0:
            feedback_factor = positive_feedbacks / total_feedbacks
            factors.append(feedback_factor)
        
        # 综合置信度
        if factors:
            self.personal_model['confidence'] = np.mean(factors)
    
    def should_use_personal_model(self, input_data: Dict[str, Any]) -> Tuple[bool, float]:
        """
        判断是否应该使用个人模型
        
        Returns:
            (是否使用, 置信度)
        """
        # 检查个人模型置信度
        if self.personal_model['confidence'] < self.config['confidence_threshold']:
            return False, self.personal_model['confidence']
        
        # 检查是否有匹配的规则
        condition = self._extract_condition(input_data)
        if condition:
            rule_key = f"{condition['type']}_{condition['value_range']}"
            if rule_key in self.personal_model['rules']:
                rule = self.personal_model['rules'][rule_key]
                return True, rule['confidence']
        
        return False, 0.0
    
    def predict_with_personal_model(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        使用个人模型进行预测
        
        Returns:
            预测结果，如果无法预测则返回None
        """
        condition = self._extract_condition(input_data)
        if not condition:
            return None
        
        rule_key = f"{condition['type']}_{condition['value_range']}"
        if rule_key not in self.personal_model['rules']:
            return None
        
        rule = self.personal_model['rules'][rule_key]
        
        self.stats['personal_model_calls'] += 1
        
        return {
            'source': 'personal_model',
            'confidence': rule['confidence'],
            'recommendation': rule['action'],
            'rule_used': rule_key
        }
    
    def get_recommendation_strategy(self, input_data: Dict[str, Any]) -> str:
        """
        获取推荐策略
        
        Returns:
            'llm_only': 仅使用大模型
            'personal_only': 仅使用个人模型
            'hybrid': 混合使用
        """
        use_personal, confidence = self.should_use_personal_model(input_data)
        
        if not use_personal:
            return 'llm_only'
        
        if confidence > 0.85:
            return 'personal_only'
        
        return 'hybrid'
    
    def hybrid_predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        混合预测：结合大模型和个人模型
        
        Returns:
            混合预测结果
        """
        strategy = self.get_recommendation_strategy(input_data)
        
        if strategy == 'llm_only':
            self.stats['llm_calls'] += 1
            return {
                'source': 'llm',
                'strategy': strategy,
                'note': '使用大模型（个人模型置信度不足）'
            }
        
        elif strategy == 'personal_only':
            result = self.predict_with_personal_model(input_data)
            if result:
                return {
                    **result,
                    'strategy': strategy,
                    'note': '使用个人模型（高置信度）'
                }
        
        else:  # hybrid
            self.stats['hybrid_calls'] += 1
            personal_result = self.predict_with_personal_model(input_data)
            
            return {
                'source': 'hybrid',
                'strategy': strategy,
                'personal_prediction': personal_result,
                'note': '混合模式：个人模型提供基础建议，大模型提供补充'
            }
    
    def get_distillation_status(self) -> Dict[str, Any]:
        """获取蒸馏状态"""
        return {
            'user_id': self.user_id,
            'training_samples': len(self.training_data['inputs']),
            'personal_rules': len(self.personal_model['rules']),
            'personal_patterns': len(self.personal_model['patterns']),
            'model_confidence': self.personal_model['confidence'],
            'stats': self.stats,
            'config': self.config,
            'ready_for_distillation': len(self.training_data['inputs']) >= self.config['min_samples']
        }
    
    def export_personal_model(self) -> Dict[str, Any]:
        """导出个人模型"""
        return {
            'user_id': self.user_id,
            'model': self.personal_model,
            'stats': self.stats,
            'export_time': datetime.now().isoformat()
        }
    
    def import_personal_model(self, model_data: Dict[str, Any]):
        """导入个人模型"""
        if model_data.get('user_id') != self.user_id:
            raise ValueError("用户ID不匹配")
        
        self.personal_model = model_data.get('model', {})
        self.stats = model_data.get('stats', self.stats)


# 全局实例管理
_distillation_systems = {}

def get_distillation_system(user_id: str) -> KnowledgeDistillation:
    """获取用户的知识蒸馏系统"""
    global _distillation_systems
    
    if user_id not in _distillation_systems:
        _distillation_systems[user_id] = KnowledgeDistillation(user_id)
    
    return _distillation_systems[user_id]
