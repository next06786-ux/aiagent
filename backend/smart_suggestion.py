#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能建议系统
Smart Suggestion System

核心功能：
- 分析跨领域因果关系
- 智能建议用户开启新领域
- 帮助用户理解多智能体的价值
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from user_config import UserConfig, AgentDomain, DOMAIN_DESCRIPTIONS


@dataclass
class Suggestion:
    """建议"""
    id: str  # 建议ID
    domain: AgentDomain  # 建议开启的领域
    reason: str  # 建议原因
    benefit: str  # 开启后的好处
    confidence: float  # 置信度（0-1）
    evidence: List[str]  # 证据列表
    created_at: datetime  # 创建时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'domain': self.domain.value,
            'domain_name': DOMAIN_DESCRIPTIONS[self.domain]['name'],
            'domain_icon': DOMAIN_DESCRIPTIONS[self.domain]['icon'],
            'reason': self.reason,
            'benefit': self.benefit,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'created_at': self.created_at.isoformat()
        }


class SmartSuggestion:
    """
    智能建议系统
    
    核心理念：
    - 后台运行所有6个智能体
    - 分析跨领域的因果关系
    - 当发现某个领域影响用户关心的领域时，建议开启
    """
    
    def __init__(self, prediction_engine):
        """
        初始化
        
        Args:
            prediction_engine: 预测引擎
        """
        self.engine = prediction_engine
        self.suggestion_history: List[Suggestion] = []
    
    def analyze_and_suggest(
        self,
        user_config: UserConfig,
        full_predictions: Dict[str, Any]
    ) -> List[Suggestion]:
        """
        分析并生成建议
        
        Args:
            user_config: 用户配置
            full_predictions: 完整的预测结果（所有6个智能体）
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 如果用户不想要自动建议，直接返回
        if not user_config.auto_suggest:
            return suggestions
        
        # 获取涌现模式
        emergent_patterns = full_predictions.get('emergent_patterns', [])
        
        # 分析每个涌现模式
        for pattern in emergent_patterns:
            # 检查是否涉及跨领域因果关系
            suggestion = self._analyze_pattern(pattern, user_config)
            if suggestion:
                # 检查是否已被拒绝
                if not user_config.is_suggestion_rejected(suggestion.id):
                    suggestions.append(suggestion)
        
        # 保存建议历史
        self.suggestion_history.extend(suggestions)
        
        return suggestions
    
    def _analyze_pattern(
        self,
        pattern: Dict[str, Any],
        user_config: UserConfig
    ) -> Optional[Suggestion]:
        """
        分析单个涌现模式
        
        Args:
            pattern: 涌现模式
            user_config: 用户配置
            
        Returns:
            建议（如果有）
        """
        pattern_type = pattern.get('type', '')
        description = pattern.get('description', '')
        confidence = pattern.get('confidence', 0.5)
        
        # 提取涉及的智能体
        involved_agents = self._extract_agents_from_description(description)
        
        if len(involved_agents) < 2:
            return None
        
        # 检查是否有用户关心的领域
        enabled_domains = set(user_config.enabled_agents)
        involved_domains = set(involved_agents)
        
        # 用户关心的领域
        user_cares = enabled_domains & involved_domains
        # 用户未开启的领域
        not_enabled = involved_domains - enabled_domains
        
        if user_cares and not_enabled:
            # 有跨领域影响，生成建议
            target_domain = list(not_enabled)[0]  # 建议开启的领域
            source_domain = list(user_cares)[0]  # 用户关心的领域
            
            return self._create_suggestion(
                target_domain=target_domain,
                source_domain=source_domain,
                pattern_type=pattern_type,
                description=description,
                confidence=confidence
            )
        
        return None
    
    def _extract_agents_from_description(self, description: str) -> List[AgentDomain]:
        """
        从描述中提取涉及的智能体
        
        Args:
            description: 描述文本
            
        Returns:
            智能体列表
        """
        agents = []
        
        # 关键词映射
        keywords = {
            AgentDomain.HEALTH: ['健康', '睡眠', '运动', '生病', '免疫'],
            AgentDomain.TIME: ['工作', '时间', '效率', '加班', '任务'],
            AgentDomain.EMOTION: ['情绪', '压力', '焦虑', '幸福', '心情'],
            AgentDomain.SOCIAL: ['社交', '朋友', '孤独', '聚会'],
            AgentDomain.FINANCE: ['财务', '消费', '储蓄', '金钱'],
            AgentDomain.LEARNING: ['学习', '知识', '技能', '课程']
        }
        
        for domain, words in keywords.items():
            if any(word in description for word in words):
                agents.append(domain)
        
        return agents
    
    def _create_suggestion(
        self,
        target_domain: AgentDomain,
        source_domain: AgentDomain,
        pattern_type: str,
        description: str,
        confidence: float
    ) -> Suggestion:
        """
        创建建议
        
        Args:
            target_domain: 建议开启的领域
            source_domain: 用户关心的领域
            pattern_type: 模式类型
            description: 模式描述
            confidence: 置信度
            
        Returns:
            建议对象
        """
        # 生成建议ID
        suggestion_id = f"{source_domain.value}_to_{target_domain.value}"
        
        # 获取领域信息
        target_info = DOMAIN_DESCRIPTIONS[target_domain]
        source_info = DOMAIN_DESCRIPTIONS[source_domain]
        
        # 生成建议文本
        reason = self._generate_reason(
            target_domain, source_domain, pattern_type, description
        )
        
        benefit = self._generate_benefit(target_domain, source_domain)
        
        # 提取证据
        evidence = [description]
        
        return Suggestion(
            id=suggestion_id,
            domain=target_domain,
            reason=reason,
            benefit=benefit,
            confidence=confidence,
            evidence=evidence,
            created_at=datetime.now()
        )
    
    def _generate_reason(
        self,
        target_domain: AgentDomain,
        source_domain: AgentDomain,
        pattern_type: str,
        description: str
    ) -> str:
        """
        生成建议原因
        
        Args:
            target_domain: 目标领域
            source_domain: 源领域
            pattern_type: 模式类型
            description: 描述
            
        Returns:
            原因文本
        """
        target_name = DOMAIN_DESCRIPTIONS[target_domain]['name']
        source_name = DOMAIN_DESCRIPTIONS[source_domain]['name']
        
        if pattern_type == 'cascade':
            return f"我们检测到{target_name}问题正在影响你的{source_name}"
        elif pattern_type == 'feedback_loop':
            return f"发现{target_name}和{source_name}之间存在相互影响"
        else:
            return f"你的{source_name}问题可能与{target_name}有关"
    
    def _generate_benefit(
        self,
        target_domain: AgentDomain,
        source_domain: AgentDomain
    ) -> str:
        """
        生成开启后的好处
        
        Args:
            target_domain: 目标领域
            source_domain: 源领域
            
        Returns:
            好处文本
        """
        target_name = DOMAIN_DESCRIPTIONS[target_domain]['name']
        source_name = DOMAIN_DESCRIPTIONS[source_domain]['name']
        
        return f"开启{target_name}预测，可以获得更准确的{source_name}建议"
    
    def get_suggestion_stats(self) -> Dict[str, Any]:
        """
        获取建议统计
        
        Returns:
            统计信息
        """
        total = len(self.suggestion_history)
        
        if total == 0:
            return {
                'total': 0,
                'by_domain': {},
                'avg_confidence': 0
            }
        
        # 按领域统计
        by_domain = {}
        for suggestion in self.suggestion_history:
            domain = suggestion.domain.value
            by_domain[domain] = by_domain.get(domain, 0) + 1
        
        # 平均置信度
        avg_confidence = sum(s.confidence for s in self.suggestion_history) / total
        
        return {
            'total': total,
            'by_domain': by_domain,
            'avg_confidence': avg_confidence
        }


class SuggestionPresenter:
    """
    建议展示器
    
    负责将建议以友好的方式展示给用户
    """
    
    @staticmethod
    def format_suggestion(suggestion: Suggestion) -> str:
        """
        格式化建议为文本
        
        Args:
            suggestion: 建议
            
        Returns:
            格式化的文本
        """
        domain_info = DOMAIN_DESCRIPTIONS[suggestion.domain]
        
        text = f"""
🌀 AI发现了新的模式

{suggestion.reason}

建议开启"{domain_info['icon']} {domain_info['name']}"模块

{suggestion.benefit}

证据：
"""
        for evidence in suggestion.evidence:
            text += f"  • {evidence}\n"
        
        text += f"\n置信度: {suggestion.confidence:.0%}"
        
        return text
    
    @staticmethod
    def format_suggestions_list(suggestions: List[Suggestion]) -> str:
        """
        格式化建议列表
        
        Args:
            suggestions: 建议列表
            
        Returns:
            格式化的文本
        """
        if not suggestions:
            return "暂无新建议"
        
        text = f"发现 {len(suggestions)} 个建议:\n\n"
        
        for i, suggestion in enumerate(suggestions, 1):
            domain_info = DOMAIN_DESCRIPTIONS[suggestion.domain]
            text += f"{i}. {domain_info['icon']} {domain_info['name']}\n"
            text += f"   {suggestion.reason}\n"
            text += f"   置信度: {suggestion.confidence:.0%}\n\n"
        
        return text


if __name__ == '__main__':
    # 测试
    print("=" * 70)
    print("  智能建议系统测试")
    print("=" * 70)
    
    # 创建用户配置（只开启健康）
    from user_config import UserConfig, AgentDomain
    config = UserConfig('test_user')
    
    print(f"\n用户配置:")
    print(f"  启用的领域: {config.get_enabled_domains()}")
    
    # 模拟预测结果（包含跨领域因果关系）
    mock_predictions = {
        'emergent_patterns': [
            {
                'type': 'cascade',
                'description': '工作时间过长(11.0h)导致健康下降(75.0)',
                'confidence': 0.85,
                'involved_agents': ['time', 'health']
            },
            {
                'type': 'feedback_loop',
                'description': '压力过大(7.8/10)导致健康下降(75.0)',
                'confidence': 0.80,
                'involved_agents': ['emotion', 'health']
            }
        ]
    }
    
    # 创建智能建议系统（不需要真实的预测引擎）
    suggester = SmartSuggestion(None)
    
    # 生成建议
    print(f"\n分析跨领域模式...")
    suggestions = suggester.analyze_and_suggest(config, mock_predictions)
    
    print(f"\n生成了 {len(suggestions)} 个建议:")
    for suggestion in suggestions:
        print(f"\n{SuggestionPresenter.format_suggestion(suggestion)}")
    
    # 统计
    stats = suggester.get_suggestion_stats()
    print(f"\n建议统计:")
    print(f"  总数: {stats['total']}")
    print(f"  平均置信度: {stats['avg_confidence']:.1%}")
    print(f"  按领域:")
    for domain, count in stats['by_domain'].items():
        print(f"    {domain}: {count}")
    
    print("\n" + "=" * 70)
    print("✓ 测试完成")
    print("=" * 70)
