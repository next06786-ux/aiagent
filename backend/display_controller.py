#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
展示控制器
Display Controller

负责根据用户配置过滤和展示预测结果
"""
from typing import Dict, Any, List
from user_config import UserConfig, AgentDomain, DisplayMode


class DisplayController:
    """
    展示控制器
    
    核心功能：
    - 根据用户配置过滤预测结果
    - 简单模式：只显示用户关心的领域
    - 专家模式：显示所有内容
    """
    
    def __init__(self, user_config: UserConfig):
        """
        初始化
        
        Args:
            user_config: 用户配置
        """
        self.config = user_config
    
    def filter_predictions(
        self,
        full_predictions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        过滤预测结果
        
        Args:
            full_predictions: 完整的预测结果（所有6个智能体）
            
        Returns:
            过滤后的预测结果
        """
        if self.config.display_mode == DisplayMode.EXPERT:
            # 专家模式：返回所有内容
            return full_predictions
        
        # 简单模式：只返回用户关心的领域
        filtered = {
            'time_horizon': full_predictions.get('time_horizon'),
            'predictions': {},
            'emergent_patterns': [],
            'simulations_summary': {}
        }
        
        # 过滤预测
        predictions = full_predictions.get('predictions', {})
        for domain in self.config.enabled_agents:
            domain_key = domain.value
            if domain_key in predictions:
                filtered['predictions'][domain_key] = predictions[domain_key]
        
        # 过滤涌现模式（只保留与用户关心的领域相关的）
        patterns = full_predictions.get('emergent_patterns', [])
        for pattern in patterns:
            if self._is_pattern_relevant(pattern):
                filtered['emergent_patterns'].append(pattern)
        
        # 过滤模拟摘要
        simulations = full_predictions.get('simulations_summary', {})
        for domain in self.config.enabled_agents:
            domain_key = domain.value
            if domain_key in simulations:
                filtered['simulations_summary'][domain_key] = simulations[domain_key]
        
        return filtered
    
    def _is_pattern_relevant(self, pattern: Dict[str, Any]) -> bool:
        """
        判断涌现模式是否与用户关心的领域相关
        
        Args:
            pattern: 涌现模式
            
        Returns:
            是否相关
        """
        description = pattern.get('description', '')
        domain_value = pattern.get('domain', '')
        
        # 检查模式领域
        if domain_value:
            try:
                domain = AgentDomain(domain_value)
                if domain in self.config.enabled_agents:
                    return True
            except ValueError:
                pass
        
        # 检查描述中是否包含用户关心的领域关键词
        keywords = {
            AgentDomain.HEALTH: ['健康', '睡眠', '运动', '生病'],
            AgentDomain.TIME: ['工作', '时间', '效率', '加班'],
            AgentDomain.EMOTION: ['情绪', '压力', '焦虑', '幸福'],
            AgentDomain.SOCIAL: ['社交', '朋友', '孤独'],
            AgentDomain.FINANCE: ['财务', '消费', '储蓄'],
            AgentDomain.LEARNING: ['学习', '知识', '技能']
        }
        
        for domain in self.config.enabled_agents:
            domain_keywords = keywords.get(domain, [])
            if any(keyword in description for keyword in domain_keywords):
                return True
        
        return False
    
    def format_for_display(
        self,
        filtered_predictions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        格式化预测结果用于展示
        
        Args:
            filtered_predictions: 过滤后的预测结果
            
        Returns:
            格式化后的结果
        """
        formatted = {
            'time_horizon': filtered_predictions.get('time_horizon'),
            'summary': self._generate_summary(filtered_predictions),
            'predictions_by_domain': self._format_predictions(filtered_predictions),
            'emergent_patterns': self._format_patterns(filtered_predictions),
            'recommendations': self._generate_recommendations(filtered_predictions)
        }
        
        return formatted
    
    def _generate_summary(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成摘要
        
        Args:
            predictions: 预测结果
            
        Returns:
            摘要信息
        """
        summary = {
            'enabled_domains': len(self.config.enabled_agents),
            'total_predictions': 0,
            'high_risk_count': 0,
            'patterns_found': len(predictions.get('emergent_patterns', []))
        }
        
        # 统计预测数量和高风险数量
        for domain_preds in predictions.get('predictions', {}).values():
            summary['total_predictions'] += len(domain_preds)
            for pred in domain_preds:
                if isinstance(pred, dict):
                    confidence = pred.get('confidence', 0)
                    if confidence > 0.7:
                        summary['high_risk_count'] += 1
        
        return summary
    
    def _format_predictions(self, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        格式化预测
        
        Args:
            predictions: 预测结果
            
        Returns:
            格式化的预测列表
        """
        formatted = []
        
        for domain_key, domain_preds in predictions.get('predictions', {}).items():
            try:
                domain = AgentDomain(domain_key)
                domain_info = self._get_domain_display_info(domain)
                
                for pred in domain_preds:
                    if isinstance(pred, dict):
                        formatted.append({
                            'domain': domain_key,
                            'domain_name': domain_info['name'],
                            'domain_icon': domain_info['icon'],
                            'description': pred.get('description', ''),
                            'confidence': pred.get('confidence', 0),
                            'time_horizon': pred.get('time_horizon', ''),
                            'type': pred.get('prediction_type', 'general')
                        })
            except ValueError:
                continue
        
        # 按置信度排序
        formatted.sort(key=lambda x: x['confidence'], reverse=True)
        
        return formatted
    
    def _format_patterns(self, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        格式化涌现模式
        
        Args:
            predictions: 预测结果
            
        Returns:
            格式化的模式列表
        """
        patterns = predictions.get('emergent_patterns', [])
        
        formatted = []
        for pattern in patterns:
            formatted.append({
                'type': pattern.get('type', ''),
                'type_name': self._get_pattern_type_name(pattern.get('type', '')),
                'description': pattern.get('description', ''),
                'confidence': pattern.get('confidence', 0),
                'impact_score': pattern.get('impact_score', 0)
            })
        
        return formatted
    
    def _generate_recommendations(self, predictions: Dict[str, Any]) -> List[str]:
        """
        生成建议
        
        Args:
            predictions: 预测结果
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 从预测中提取建议
        for domain_preds in predictions.get('predictions', {}).values():
            for pred in domain_preds:
                if isinstance(pred, dict):
                    details = pred.get('details', {})
                    if 'suggestions' in details:
                        recommendations.extend(details['suggestions'])
        
        # 从涌现模式中提取建议
        for pattern in predictions.get('emergent_patterns', []):
            pattern_type = pattern.get('type', '')
            if pattern_type == 'tipping_point':
                recommendations.append(f"⚠️ 临界点预警: {pattern.get('description', '')}")
        
        return recommendations[:5]  # 最多返回5条建议
    
    def _get_domain_display_info(self, domain: AgentDomain) -> Dict[str, str]:
        """
        获取领域展示信息
        
        Args:
            domain: 领域
            
        Returns:
            展示信息
        """
        from user_config import DOMAIN_DESCRIPTIONS
        return DOMAIN_DESCRIPTIONS.get(domain, {
            'name': domain.value,
            'icon': '📊'
        })
    
    def _get_pattern_type_name(self, pattern_type: str) -> str:
        """
        获取模式类型名称
        
        Args:
            pattern_type: 模式类型
            
        Returns:
            类型名称
        """
        type_names = {
            'cascade': '级联效应',
            'feedback_loop': '反馈循环',
            'tipping_point': '临界点',
            'synergy': '协同效应'
        }
        return type_names.get(pattern_type, pattern_type)


if __name__ == '__main__':
    # 测试
    print("=" * 70)
    print("  展示控制器测试")
    print("=" * 70)
    
    from user_config import UserConfig, AgentDomain, DisplayMode
    
    # 创建用户配置（只开启健康）
    config = UserConfig('test_user')
    controller = DisplayController(config)
    
    print(f"\n用户配置:")
    print(f"  启用的领域: {config.get_enabled_domains()}")
    print(f"  展示模式: {config.display_mode.value}")
    
    # 模拟完整的预测结果
    full_predictions = {
        'time_horizon': '1_week',
        'predictions': {
            'health': [
                {
                    'description': '预测健康分数将下降到75',
                    'confidence': 0.85,
                    'time_horizon': '3_days',
                    'prediction_type': 'health_risk'
                }
            ],
            'time': [
                {
                    'description': '预测工作效率将下降到60%',
                    'confidence': 0.78,
                    'time_horizon': '3_days',
                    'prediction_type': 'efficiency_decline'
                }
            ],
            'emotion': [
                {
                    'description': '预测压力水平将达到8.0/10',
                    'confidence': 0.82,
                    'time_horizon': '3_days',
                    'prediction_type': 'high_stress'
                }
            ]
        },
        'emergent_patterns': [
            {
                'type': 'cascade',
                'description': '工作时间过长导致健康下降',
                'confidence': 0.85,
                'impact_score': 0.80
            },
            {
                'type': 'feedback_loop',
                'description': '压力增加导致效率下降',
                'confidence': 0.75,
                'impact_score': 0.70
            }
        ],
        'simulations_summary': {
            'health': {'health_score': 75},
            'time': {'efficiency': 0.6},
            'emotion': {'stress': 8.0}
        }
    }
    
    # 测试简单模式
    print(f"\n简单模式过滤:")
    filtered = controller.filter_predictions(full_predictions)
    print(f"  预测领域数: {len(filtered['predictions'])}")
    print(f"  涌现模式数: {len(filtered['emergent_patterns'])}")
    print(f"  预测领域: {list(filtered['predictions'].keys())}")
    
    # 格式化展示
    print(f"\n格式化结果:")
    formatted = controller.format_for_display(filtered)
    print(f"  摘要: {formatted['summary']}")
    print(f"  预测数: {len(formatted['predictions_by_domain'])}")
    print(f"  建议数: {len(formatted['recommendations'])}")
    
    # 切换到专家模式
    print(f"\n切换到专家模式...")
    config.set_display_mode(DisplayMode.EXPERT)
    controller = DisplayController(config)
    
    filtered = controller.filter_predictions(full_predictions)
    print(f"  预测领域数: {len(filtered['predictions'])}")
    print(f"  涌现模式数: {len(filtered['emergent_patterns'])}")
    print(f"  预测领域: {list(filtered['predictions'].keys())}")
    
    print("\n" + "=" * 70)
    print("✓ 测试完成")
    print("=" * 70)
