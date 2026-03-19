"""
大模型增强的智能体
LLM-Enhanced Agents - 为每个智能体添加大模型推理能力
"""
from typing import Dict, Any, Optional
from .llm_service import get_llm_service


class EnhancedAgentMixin:
    """智能体增强混入类"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.llm_enabled = self.llm_service is not None
    
    def get_llm_analysis(self, data: Dict[str, Any], prediction: Dict[str, Any]) -> Optional[str]:
        """
        获取大模型分析
        
        Args:
            data: 输入数据
            prediction: 预测结果
        
        Returns:
            大模型分析结果，如果未启用则返回 None
        """
        if not self.llm_enabled:
            return None
        
        # 子类需要实现具体的分析方法
        return None


class EnhancedHealthAgent(EnhancedAgentMixin):
    """大模型增强的健康智能体"""
    
    def __init__(self, base_agent):
        super().__init__()
        self.base_agent = base_agent
    
    def analyze(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析健康数据
        
        Returns:
            {
                'prediction': 基础预测结果,
                'llm_analysis': 大模型深度分析（如果启用）,
                'recommendations': 建议列表
            }
        """
        # 1. 使用基础智能体进行科学计算
        self.base_agent.update(health_data)
        prediction = self.base_agent.simulate(days=7)
        
        result = {
            'prediction': prediction,
            'llm_analysis': None,
            'recommendations': []
        }
        
        # 2. 如果启用大模型，进行深度分析
        if self.llm_enabled and self.llm_service:
            try:
                llm_analysis = self.llm_service.analyze_health(
                    health_data=health_data,
                    prediction=prediction
                )
                result['llm_analysis'] = llm_analysis
                
                # 从大模型分析中提取建议
                result['recommendations'] = self._extract_recommendations(llm_analysis)
            except Exception as e:
                print(f"LLM 分析失败: {e}")
        
        return result
    
    def _extract_recommendations(self, analysis: str) -> list:
        """从大模型分析中提取建议"""
        # 简单实现：查找数字列表
        recommendations = []
        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                recommendations.append(line)
        return recommendations


class EnhancedTimeAgent(EnhancedAgentMixin):
    """大模型增强的时间智能体"""
    
    def __init__(self, base_agent):
        super().__init__()
        self.base_agent = base_agent
    
    def analyze(self, time_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析时间使用数据"""
        self.base_agent.update(time_data)
        prediction = self.base_agent.simulate(days=7)
        
        result = {
            'prediction': prediction,
            'llm_analysis': None,
            'recommendations': []
        }
        
        if self.llm_enabled and self.llm_service:
            try:
                llm_analysis = self.llm_service.analyze_time(
                    time_data=time_data,
                    prediction=prediction
                )
                result['llm_analysis'] = llm_analysis
                result['recommendations'] = self._extract_recommendations(llm_analysis)
            except Exception as e:
                print(f"LLM 分析失败: {e}")
        
        return result
    
    def _extract_recommendations(self, analysis: str) -> list:
        recommendations = []
        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                recommendations.append(line)
        return recommendations


class EnhancedEmotionAgent(EnhancedAgentMixin):
    """大模型增强的情绪智能体"""
    
    def __init__(self, base_agent):
        super().__init__()
        self.base_agent = base_agent
    
    def analyze(self, emotion_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析情绪数据"""
        self.base_agent.update(emotion_data)
        prediction = self.base_agent.simulate(days=7)
        
        result = {
            'prediction': prediction,
            'llm_analysis': None,
            'recommendations': []
        }
        
        if self.llm_enabled and self.llm_service:
            try:
                llm_analysis = self.llm_service.analyze_emotion(
                    emotion_data=emotion_data,
                    prediction=prediction
                )
                result['llm_analysis'] = llm_analysis
                result['recommendations'] = self._extract_recommendations(llm_analysis)
            except Exception as e:
                print(f"LLM 分析失败: {e}")
        
        return result
    
    def _extract_recommendations(self, analysis: str) -> list:
        recommendations = []
        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                recommendations.append(line)
        return recommendations


class EnhancedSocialAgent(EnhancedAgentMixin):
    """大模型增强的社交智能体"""
    
    def __init__(self, base_agent):
        super().__init__()
        self.base_agent = base_agent
    
    def analyze(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析社交数据"""
        self.base_agent.update(social_data)
        prediction = self.base_agent.simulate(days=7)
        
        result = {
            'prediction': prediction,
            'llm_analysis': None,
            'recommendations': []
        }
        
        if self.llm_enabled and self.llm_service:
            try:
                llm_analysis = self.llm_service.analyze_social(
                    social_data=social_data,
                    prediction=prediction
                )
                result['llm_analysis'] = llm_analysis
                result['recommendations'] = self._extract_recommendations(llm_analysis)
            except Exception as e:
                print(f"LLM 分析失败: {e}")
        
        return result
    
    def _extract_recommendations(self, analysis: str) -> list:
        recommendations = []
        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                recommendations.append(line)
        return recommendations


class EnhancedFinanceAgent(EnhancedAgentMixin):
    """大模型增强的财务智能体"""
    
    def __init__(self, base_agent):
        super().__init__()
        self.base_agent = base_agent
    
    def analyze(self, finance_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析财务数据"""
        self.base_agent.update(finance_data)
        prediction = self.base_agent.simulate(days=7)
        
        result = {
            'prediction': prediction,
            'llm_analysis': None,
            'recommendations': []
        }
        
        if self.llm_enabled and self.llm_service:
            try:
                llm_analysis = self.llm_service.analyze_finance(
                    finance_data=finance_data,
                    prediction=prediction
                )
                result['llm_analysis'] = llm_analysis
                result['recommendations'] = self._extract_recommendations(llm_analysis)
            except Exception as e:
                print(f"LLM 分析失败: {e}")
        
        return result
    
    def _extract_recommendations(self, analysis: str) -> list:
        recommendations = []
        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                recommendations.append(line)
        return recommendations


class EnhancedLearningAgent(EnhancedAgentMixin):
    """大模型增强的学习智能体"""
    
    def __init__(self, base_agent):
        super().__init__()
        self.base_agent = base_agent
    
    def analyze(self, learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析学习数据"""
        self.base_agent.update(learning_data)
        prediction = self.base_agent.simulate(days=7)
        
        result = {
            'prediction': prediction,
            'llm_analysis': None,
            'recommendations': []
        }
        
        if self.llm_enabled and self.llm_service:
            try:
                llm_analysis = self.llm_service.analyze_learning(
                    learning_data=learning_data,
                    prediction=prediction
                )
                result['llm_analysis'] = llm_analysis
                result['recommendations'] = self._extract_recommendations(llm_analysis)
            except Exception as e:
                print(f"LLM 分析失败: {e}")
        
        return result
    
    def _extract_recommendations(self, analysis: str) -> list:
        recommendations = []
        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                recommendations.append(line)
        return recommendations


def enhance_agents(digital_twin) -> Dict[str, Any]:
    """
    为数字孪生的所有智能体添加大模型增强
    
    Args:
        digital_twin: 数字孪生实例
    
    Returns:
        增强后的智能体字典
    """
    enhanced = {}
    
    if hasattr(digital_twin, 'health_agent'):
        enhanced['health'] = EnhancedHealthAgent(digital_twin.health_agent)
    
    if hasattr(digital_twin, 'time_agent'):
        enhanced['time'] = EnhancedTimeAgent(digital_twin.time_agent)
    
    if hasattr(digital_twin, 'emotion_agent'):
        enhanced['emotion'] = EnhancedEmotionAgent(digital_twin.emotion_agent)
    
    if hasattr(digital_twin, 'social_agent'):
        enhanced['social'] = EnhancedSocialAgent(digital_twin.social_agent)
    
    if hasattr(digital_twin, 'finance_agent'):
        enhanced['finance'] = EnhancedFinanceAgent(digital_twin.finance_agent)
    
    if hasattr(digital_twin, 'learning_agent'):
        enhanced['learning'] = EnhancedLearningAgent(digital_twin.learning_agent)
    
    return enhanced
