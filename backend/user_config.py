#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户配置管理
User Configuration Management

支持渐进式展示策略：
- 用户可以选择关心的生活领域
- 支持简单模式和专家模式
- 后台始终运行所有智能体，但只展示用户关心的内容
"""
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum


class DisplayMode(Enum):
    """展示模式"""
    SIMPLE = "simple"  # 简单模式：只显示选择的领域
    EXPERT = "expert"  # 专家模式：显示所有内容


class AgentDomain(Enum):
    """智能体领域"""
    HEALTH = "health"  # 健康管理
    TIME = "time"  # 时间管理
    EMOTION = "emotion"  # 情绪管理
    SOCIAL = "social"  # 社交管理
    FINANCE = "finance"  # 财务管理
    LEARNING = "learning"  # 学习管理


# 领域描述
DOMAIN_DESCRIPTIONS = {
    AgentDomain.HEALTH: {
        'name': '健康管理',
        'description': '预测健康风险，避免生病',
        'icon': '🏥',
        'benefits': [
            '提前3天预警健康风险',
            '优化睡眠和运动计划',
            '避免突然生病影响工作'
        ]
    },
    AgentDomain.TIME: {
        'name': '工作效率',
        'description': '优化时间安排，提高效率',
        'icon': '⏰',
        'benefits': [
            '预测工作效率变化',
            '发现时间冲突',
            '优化工作节奏'
        ]
    },
    AgentDomain.EMOTION: {
        'name': '情绪管理',
        'description': '预测压力爆发，及时调整',
        'icon': '😊',
        'benefits': [
            '预测情绪崩溃风险',
            '压力管理建议',
            '保持心理健康'
        ]
    },
    AgentDomain.SOCIAL: {
        'name': '社交生活',
        'description': '平衡社交和独处时间',
        'icon': '👥',
        'benefits': [
            '预测社交需求',
            '避免社交孤立',
            '优化社交时间'
        ]
    },
    AgentDomain.FINANCE: {
        'name': '财务规划',
        'description': '预测财务风险，合理消费',
        'icon': '💰',
        'benefits': [
            '预测财务风险',
            '消费建议',
            '储蓄目标管理'
        ]
    },
    AgentDomain.LEARNING: {
        'name': '学习成长',
        'description': '优化学习计划，提高效率',
        'icon': '📚',
        'benefits': [
            '预测学习效果',
            '优化学习时间',
            '知识保持提醒'
        ]
    }
}


class UserConfig:
    """
    用户配置
    
    核心理念：
    - 后台始终运行所有6个智能体
    - 但只向用户展示他们关心的领域
    - 通过智能建议引导用户逐步开启新领域
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # 用户启用的智能体领域（默认只有健康）
        self.enabled_agents: List[AgentDomain] = [AgentDomain.HEALTH]
        
        # 展示模式（默认简单模式）
        self.display_mode: DisplayMode = DisplayMode.SIMPLE
        
        # 是否自动建议开启新领域
        self.auto_suggest: bool = True
        
        # 已拒绝的建议（避免重复建议）
        self.rejected_suggestions: List[str] = []
        
        # 配置创建时间
        self.created_at: datetime = datetime.now()
        
        # 最后更新时间
        self.updated_at: datetime = datetime.now()
    
    def enable_agent(self, domain: AgentDomain) -> bool:
        """
        启用智能体领域
        
        Args:
            domain: 要启用的领域
            
        Returns:
            是否成功启用
        """
        if domain not in self.enabled_agents:
            self.enabled_agents.append(domain)
            self.updated_at = datetime.now()
            return True
        return False
    
    def disable_agent(self, domain: AgentDomain) -> bool:
        """
        禁用智能体领域
        
        Args:
            domain: 要禁用的领域
            
        Returns:
            是否成功禁用
        """
        if domain in self.enabled_agents:
            # 至少保留一个领域
            if len(self.enabled_agents) > 1:
                self.enabled_agents.remove(domain)
                self.updated_at = datetime.now()
                return True
        return False
    
    def is_agent_enabled(self, domain: AgentDomain) -> bool:
        """
        检查智能体是否启用
        
        Args:
            domain: 要检查的领域
            
        Returns:
            是否启用
        """
        return domain in self.enabled_agents
    
    def should_display(self, domain: AgentDomain) -> bool:
        """
        判断是否应该向用户展示这个领域的结果
        
        Args:
            domain: 要检查的领域
            
        Returns:
            是否应该展示
        """
        if self.display_mode == DisplayMode.EXPERT:
            # 专家模式：显示所有内容
            return True
        else:
            # 简单模式：只显示启用的领域
            return domain in self.enabled_agents
    
    def set_display_mode(self, mode: DisplayMode):
        """
        设置展示模式
        
        Args:
            mode: 展示模式
        """
        self.display_mode = mode
        self.updated_at = datetime.now()
    
    def reject_suggestion(self, suggestion_id: str):
        """
        拒绝建议
        
        Args:
            suggestion_id: 建议ID
        """
        if suggestion_id not in self.rejected_suggestions:
            self.rejected_suggestions.append(suggestion_id)
            self.updated_at = datetime.now()
    
    def is_suggestion_rejected(self, suggestion_id: str) -> bool:
        """
        检查建议是否已被拒绝
        
        Args:
            suggestion_id: 建议ID
            
        Returns:
            是否已拒绝
        """
        return suggestion_id in self.rejected_suggestions
    
    def get_enabled_domains(self) -> List[str]:
        """
        获取启用的领域名称列表
        
        Returns:
            领域名称列表
        """
        return [domain.value for domain in self.enabled_agents]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            配置字典
        """
        return {
            'user_id': self.user_id,
            'enabled_agents': [d.value for d in self.enabled_agents],
            'display_mode': self.display_mode.value,
            'auto_suggest': self.auto_suggest,
            'rejected_suggestions': self.rejected_suggestions,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserConfig':
        """
        从字典创建配置
        
        Args:
            data: 配置字典
            
        Returns:
            用户配置对象
        """
        config = cls(data['user_id'])
        config.enabled_agents = [
            AgentDomain(d) for d in data.get('enabled_agents', ['health'])
        ]
        config.display_mode = DisplayMode(data.get('display_mode', 'simple'))
        config.auto_suggest = data.get('auto_suggest', True)
        config.rejected_suggestions = data.get('rejected_suggestions', [])
        
        if 'created_at' in data:
            config.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            config.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return config


class OnboardingFlow:
    """
    用户引导流程
    
    帮助新用户选择关心的领域
    """
    
    @staticmethod
    def get_recommended_domains() -> List[AgentDomain]:
        """
        获取推荐的初始领域
        
        Returns:
            推荐领域列表
        """
        # 推荐从健康开始（最容易理解和验证）
        return [AgentDomain.HEALTH]
    
    @staticmethod
    def get_domain_info(domain: AgentDomain) -> Dict[str, Any]:
        """
        获取领域信息
        
        Args:
            domain: 领域
            
        Returns:
            领域信息
        """
        return DOMAIN_DESCRIPTIONS.get(domain, {})
    
    @staticmethod
    def get_all_domains_info() -> List[Dict[str, Any]]:
        """
        获取所有领域信息
        
        Returns:
            所有领域信息列表
        """
        result = []
        for domain in AgentDomain:
            info = DOMAIN_DESCRIPTIONS.get(domain, {})
            info['domain'] = domain.value
            result.append(info)
        return result


if __name__ == '__main__':
    # 测试
    print("=" * 70)
    print("  用户配置系统测试")
    print("=" * 70)
    
    # 创建用户配置
    config = UserConfig('test_user')
    print(f"\n初始配置:")
    print(f"  启用的领域: {config.get_enabled_domains()}")
    print(f"  展示模式: {config.display_mode.value}")
    
    # 启用新领域
    print(f"\n启用时间管理...")
    config.enable_agent(AgentDomain.TIME)
    print(f"  启用的领域: {config.get_enabled_domains()}")
    
    # 检查是否应该展示
    print(f"\n展示检查（简单模式）:")
    for domain in AgentDomain:
        should_display = config.should_display(domain)
        print(f"  {domain.value}: {'✓' if should_display else '✗'}")
    
    # 切换到专家模式
    print(f"\n切换到专家模式...")
    config.set_display_mode(DisplayMode.EXPERT)
    print(f"  展示模式: {config.display_mode.value}")
    
    print(f"\n展示检查（专家模式）:")
    for domain in AgentDomain:
        should_display = config.should_display(domain)
        print(f"  {domain.value}: {'✓' if should_display else '✗'}")
    
    # 获取所有领域信息
    print(f"\n所有领域信息:")
    for info in OnboardingFlow.get_all_domains_info():
        print(f"\n  {info['icon']} {info['name']}")
        print(f"     {info['description']}")
        print(f"     优势:")
        for benefit in info['benefits']:
            print(f"       • {benefit}")
    
    print("\n" + "=" * 70)
    print("✓ 测试完成")
    print("=" * 70)
