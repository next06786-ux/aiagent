"""
决策逻辑集成模块
为所有垂直领域决策引擎提供决策逻辑画像的获取和融合功能
"""
from typing import Dict, Any, Optional


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """限制值在指定范围内"""
    return max(min_val, min(max_val, value))


def get_decision_logic_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    从平行人生塔罗牌游戏获取决策逻辑画像
    
    Args:
        user_id: 用户ID
    
    Returns:
        决策逻辑画像，如果置信度不足则返回None
    """
    try:
        from backend.parallel_life.decision_logic_analyzer import DecisionLogicAnalyzer
        
        analyzer = DecisionLogicAnalyzer(user_id)
        decision_profile = analyzer.get_decision_profile()
        
        if decision_profile.get('confidence', 0) < 0.3:
            print(f"[决策逻辑] 用户 {user_id} 的决策逻辑置信度不足: {decision_profile.get('confidence')}")
            return None
        
        print(f"[决策逻辑] 成功获取用户 {user_id} 的决策逻辑画像，置信度: {decision_profile.get('confidence')}")
        return decision_profile
        
    except Exception as e:
        print(f"[决策逻辑] 获取决策逻辑画像失败: {e}")
        return None


def merge_decision_logic_to_profile(
    profile: Dict[str, float], 
    decision_profile: Dict[str, Any]
) -> Dict[str, float]:
    """
    将决策逻辑画像融合到用户画像中
    
    Args:
        profile: 原始用户画像
        decision_profile: 决策逻辑画像
    
    Returns:
        融合后的用户画像
    """
    dimensions = decision_profile.get('dimensions', {})
    confidence = decision_profile.get('confidence', 0)
    
    # 映射决策维度到画像参数
    dimension_mapping = {
        '风险偏好': 'risk_tolerance',
        '主动性': 'execution_stability',
        '思维方式': 'growth_bias',
        '权威态度': 'social_dependency',
        '创新倾向': 'ambiguity_tolerance',
        '损失厌恶': 'loss_aversion',
    }
    
    for dimension_name, profile_key in dimension_mapping.items():
        if dimension_name in dimensions and profile_key in profile:
            dim_data = dimensions[dimension_name]
            dim_value = dim_data.get('value', 0)  # -1 到 1
            dim_confidence = dim_data.get('confidence', 0)
            
            # 将 -1~1 映射到 0~1
            normalized_value = (dim_value + 1) / 2
            
            # 根据置信度加权融合
            weight = confidence * dim_confidence
            profile[profile_key] = clamp(
                profile[profile_key] * (1 - weight) + normalized_value * weight
            )
    
    print(f"[决策逻辑] 决策逻辑已融合到画像，权重: {confidence}")
    return profile


def enhance_profile_with_decision_logic(
    user_id: str,
    profile: Dict[str, float]
) -> Dict[str, float]:
    """
    使用决策逻辑增强用户画像（便捷方法）
    
    Args:
        user_id: 用户ID
        profile: 原始用户画像
    
    Returns:
        增强后的用户画像
    """
    decision_profile = get_decision_logic_profile(user_id)
    if decision_profile:
        profile = merge_decision_logic_to_profile(profile, decision_profile)
    return profile
