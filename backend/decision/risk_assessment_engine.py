"""
风险评估引擎
量化决策的6大风险维度，生成风险缓解建议
"""
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"          # 0-3分: 绿色
    MEDIUM = "medium"    # 4-6分: 黄色
    HIGH = "high"        # 7-8分: 橙色
    CRITICAL = "critical"  # 9-10分: 红色


@dataclass
class RiskDimension:
    """风险维度"""
    name: str  # 维度名称
    score: float  # 风险得分 0-10
    level: RiskLevel  # 风险等级
    factors: List[str]  # 风险因素
    mitigation: List[str]  # 缓解建议


@dataclass
class RiskAssessment:
    """风险评估结果"""
    option_title: str
    overall_risk: float  # 总体风险 0-10
    overall_level: RiskLevel
    dimensions: Dict[str, RiskDimension]  # 6大维度
    high_risk_count: int  # 高风险维度数量
    recommendations: List[str]  # 总体建议


class RiskAssessmentEngine:
    """风险评估引擎"""
    
    def __init__(self):
        # 风险维度权重
        self.dimension_weights = {
            "health": 1.2,      # 健康风险权重最高
            "finance": 1.0,     # 财务风险
            "social": 0.8,      # 社交风险
            "time": 0.9,        # 时间风险
            "emotion": 1.1,     # 情绪风险
            "learning": 0.7     # 学习风险
        }
    
    def assess_option_risk(
        self,
        option_title: str,
        timeline: List[Dict],
        profile: Any = None
    ) -> RiskAssessment:
        """
        评估单个决策选项的风险
        
        Args:
            option_title: 选项标题
            timeline: 时间线事件列表
            profile: 用户性格画像
        
        Returns:
            RiskAssessment
        """
        # 评估6大维度
        dimensions = {
            "health": self._assess_health_risk(timeline, profile),
            "finance": self._assess_finance_risk(timeline, profile),
            "social": self._assess_social_risk(timeline, profile),
            "time": self._assess_time_risk(timeline, profile),
            "emotion": self._assess_emotion_risk(timeline, profile),
            "learning": self._assess_learning_risk(timeline, profile)
        }
        
        # 计算总体风险
        overall_risk = self._calculate_overall_risk(dimensions)
        overall_level = self._get_risk_level(overall_risk)
        
        # 统计高风险维度
        high_risk_count = sum(
            1 for dim in dimensions.values()
            if dim.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        )
        
        # 生成总体建议
        recommendations = self._generate_recommendations(dimensions, profile)
        
        return RiskAssessment(
            option_title=option_title,
            overall_risk=overall_risk,
            overall_level=overall_level,
            dimensions=dimensions,
            high_risk_count=high_risk_count,
            recommendations=recommendations
        )
    
    def _assess_health_risk(self, timeline: List[Dict], profile: Any) -> RiskDimension:
        """评估健康风险"""
        risk_score = 0.0
        factors = []
        
        # 分析时间线中的健康影响
        health_impacts = []
        for event in timeline:
            impact = event.get('impact', {})
            if '健康' in impact:
                health_impacts.append(impact['健康'])
        
        # 计算平均健康影响
        if health_impacts:
            avg_impact = sum(health_impacts) / len(health_impacts)
            
            # 负面影响越大，风险越高
            if avg_impact < -0.3:
                risk_score += 4.0
                factors.append("持续的健康负面影响")
            elif avg_impact < -0.1:
                risk_score += 2.0
                factors.append("轻微的健康压力")
        
        # 检查压力相关事件
        stress_events = [
            e for e in timeline
            if any(keyword in e.get('event', '') for keyword in ['压力', '疲惫', '焦虑', '睡眠'])
        ]
        
        if len(stress_events) >= 3:
            risk_score += 3.0
            factors.append(f"存在{len(stress_events)}个高压力事件")
        
        # 根据性格调整
        if profile and hasattr(profile, 'neuroticism') and profile.neuroticism >= 3:
            risk_score += 1.0
            factors.append("性格敏感，压力承受能力较弱")
        
        # 限制在0-10范围
        risk_score = min(10.0, max(0.0, risk_score))
        
        # 生成缓解建议
        mitigation = self._generate_health_mitigation(risk_score, factors)
        
        return RiskDimension(
            name="健康风险",
            score=risk_score,
            level=self._get_risk_level(risk_score),
            factors=factors if factors else ["健康影响较小"],
            mitigation=mitigation
        )
    
    def _assess_finance_risk(self, timeline: List[Dict], profile: Any) -> RiskDimension:
        """评估财务风险"""
        risk_score = 0.0
        factors = []
        
        # 分析财务影响
        finance_impacts = []
        for event in timeline:
            impact = event.get('impact', {})
            if '财务' in impact:
                finance_impacts.append(impact['财务'])
        
        if finance_impacts:
            avg_impact = sum(finance_impacts) / len(finance_impacts)
            
            # 负面财务影响
            if avg_impact < -0.4:
                risk_score += 5.0
                factors.append("严重的财务负担")
            elif avg_impact < -0.2:
                risk_score += 3.0
                factors.append("中等财务压力")
            elif avg_impact < 0:
                risk_score += 1.0
                factors.append("轻微财务支出")
        
        # 检查收入中断
        income_loss = any('收入' in e.get('event', '') and '中断' in e.get('event', '') for e in timeline)
        if income_loss:
            risk_score += 3.0
            factors.append("可能面临收入中断")
        
        # 根据风险偏好调整
        if profile and hasattr(profile, 'risk_preference'):
            if profile.risk_preference == "risk_averse" and risk_score > 3:
                risk_score += 1.0
                factors.append("与你的风险规避偏好不符")
        
        risk_score = min(10.0, max(0.0, risk_score))
        mitigation = self._generate_finance_mitigation(risk_score, factors)
        
        return RiskDimension(
            name="财务风险",
            score=risk_score,
            level=self._get_risk_level(risk_score),
            factors=factors if factors else ["财务影响可控"],
            mitigation=mitigation
        )
    
    def _assess_social_risk(self, timeline: List[Dict], profile: Any) -> RiskDimension:
        """评估社交风险"""
        risk_score = 0.0
        factors = []
        
        # 分析社交影响
        social_impacts = []
        for event in timeline:
            impact = event.get('impact', {})
            if '社交' in impact:
                social_impacts.append(impact['社交'])
        
        if social_impacts:
            avg_impact = sum(social_impacts) / len(social_impacts)
            
            if avg_impact < -0.3:
                risk_score += 4.0
                factors.append("社交圈可能缩小")
            elif avg_impact < -0.1:
                risk_score += 2.0
                factors.append("社交时间减少")
        
        # 检查孤独相关事件
        isolation_events = [
            e for e in timeline
            if any(keyword in e.get('event', '') for keyword in ['孤独', '隔离', '独自'])
        ]
        
        if isolation_events:
            risk_score += 2.0
            factors.append("可能感到孤独")
        
        # 外向性格的人社交风险更敏感
        if profile and hasattr(profile, 'extraversion') and profile.extraversion >= 3:
            if risk_score > 2:
                risk_score += 1.0
                factors.append("外向性格，需要更多社交")
        
        risk_score = min(10.0, max(0.0, risk_score))
        mitigation = self._generate_social_mitigation(risk_score, factors)
        
        return RiskDimension(
            name="社交风险",
            score=risk_score,
            level=self._get_risk_level(risk_score),
            factors=factors if factors else ["社交影响正常"],
            mitigation=mitigation
        )
    
    def _assess_time_risk(self, timeline: List[Dict], profile: Any) -> RiskDimension:
        """评估时间风险"""
        risk_score = 0.0
        factors = []
        
        # 分析时间影响
        time_impacts = []
        for event in timeline:
            impact = event.get('impact', {})
            if '时间' in impact:
                time_impacts.append(impact['时间'])
        
        if time_impacts:
            avg_impact = sum(time_impacts) / len(time_impacts)
            
            if avg_impact < -0.5:
                risk_score += 4.0
                factors.append("时间严重不足")
            elif avg_impact < -0.3:
                risk_score += 2.0
                factors.append("时间较为紧张")
        
        # 检查机会成本
        opportunity_cost = any('机会' in e.get('event', '') for e in timeline)
        if opportunity_cost:
            risk_score += 2.0
            factors.append("存在机会成本")
        
        # 检查年龄压力
        age_pressure = any('年龄' in e.get('event', '') for e in timeline)
        if age_pressure:
            risk_score += 1.5
            factors.append("可能面临年龄压力")
        
        risk_score = min(10.0, max(0.0, risk_score))
        mitigation = self._generate_time_mitigation(risk_score, factors)
        
        return RiskDimension(
            name="时间风险",
            score=risk_score,
            level=self._get_risk_level(risk_score),
            factors=factors if factors else ["时间安排合理"],
            mitigation=mitigation
        )
    
    def _assess_emotion_risk(self, timeline: List[Dict], profile: Any) -> RiskDimension:
        """评估情绪风险"""
        risk_score = 0.0
        factors = []
        
        # 分析情绪影响
        emotion_impacts = []
        for event in timeline:
            impact = event.get('impact', {})
            if '情绪' in impact:
                emotion_impacts.append(impact['情绪'])
        
        if emotion_impacts:
            avg_impact = sum(emotion_impacts) / len(emotion_impacts)
            
            if avg_impact < -0.4:
                risk_score += 5.0
                factors.append("情绪压力较大")
            elif avg_impact < -0.2:
                risk_score += 3.0
                factors.append("存在情绪波动")
        
        # 检查负面情绪事件
        negative_emotions = [
            e for e in timeline
            if any(keyword in e.get('event', '') for keyword in ['焦虑', '抑郁', '后悔', '挫败', '失落'])
        ]
        
        if len(negative_emotions) >= 2:
            risk_score += 3.0
            factors.append(f"存在{len(negative_emotions)}个负面情绪事件")
        
        # 神经质高的人情绪风险更高
        if profile and hasattr(profile, 'neuroticism') and profile.neuroticism >= 3:
            risk_score += 1.5
            factors.append("情绪敏感，需要关注心理健康")
        
        risk_score = min(10.0, max(0.0, risk_score))
        mitigation = self._generate_emotion_mitigation(risk_score, factors)
        
        return RiskDimension(
            name="情绪风险",
            score=risk_score,
            level=self._get_risk_level(risk_score),
            factors=factors if factors else ["情绪状态稳定"],
            mitigation=mitigation
        )
    
    def _assess_learning_risk(self, timeline: List[Dict], profile: Any) -> RiskDimension:
        """评估学习风险"""
        risk_score = 0.0
        factors = []
        
        # 分析学习影响
        learning_impacts = []
        for event in timeline:
            impact = event.get('impact', {})
            if '学习' in impact:
                learning_impacts.append(impact['学习'])
        
        # 检查失败概率
        failure_events = [
            e for e in timeline
            if any(keyword in e.get('event', '') for keyword in ['失败', '不足', '困难', '挑战'])
        ]
        
        if len(failure_events) >= 2:
            risk_score += 3.0
            factors.append("存在失败风险")
        
        # 检查能力要求
        high_demand = [
            e for e in timeline
            if any(keyword in e.get('event', '') for keyword in ['高强度', '竞争', '压力'])
        ]
        
        if high_demand:
            risk_score += 2.0
            factors.append("能力要求较高")
        
        # 根据开放性调整
        if profile and hasattr(profile, 'openness') and profile.openness < 2:
            if learning_impacts and sum(learning_impacts) / len(learning_impacts) > 0.5:
                risk_score += 1.0
                factors.append("学习强度可能超出舒适区")
        
        risk_score = min(10.0, max(0.0, risk_score))
        mitigation = self._generate_learning_mitigation(risk_score, factors)
        
        return RiskDimension(
            name="学习风险",
            score=risk_score,
            level=self._get_risk_level(risk_score),
            factors=factors if factors else ["学习压力适中"],
            mitigation=mitigation
        )
    
    def _calculate_overall_risk(self, dimensions: Dict[str, RiskDimension]) -> float:
        """计算总体风险（加权平均）"""
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for key, dimension in dimensions.items():
            weight = self.dimension_weights.get(key, 1.0)
            total_weighted_score += dimension.score * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _get_risk_level(self, score: float) -> RiskLevel:
        """根据分数获取风险等级"""
        if score >= 9:
            return RiskLevel.CRITICAL
        elif score >= 7:
            return RiskLevel.HIGH
        elif score >= 4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_health_mitigation(self, score: float, factors: List[str]) -> List[str]:
        """生成健康风险缓解建议"""
        mitigation = []
        
        if score >= 7:
            mitigation.append("建议每天保证7-8小时睡眠")
            mitigation.append("定期进行体检，关注身体状况")
            mitigation.append("学习压力管理技巧，如冥想、运动")
        elif score >= 4:
            mitigation.append("保持规律作息，避免熬夜")
            mitigation.append("每周至少运动3次，每次30分钟")
        else:
            mitigation.append("继续保持健康的生活方式")
        
        return mitigation
    
    def _generate_finance_mitigation(self, score: float, factors: List[str]) -> List[str]:
        """生成财务风险缓解建议"""
        mitigation = []
        
        if score >= 7:
            mitigation.append("建议准备至少6个月的应急资金")
            mitigation.append("考虑兼职或副业增加收入来源")
            mitigation.append("制定详细的财务预算计划")
        elif score >= 4:
            mitigation.append("建立应急储蓄基金")
            mitigation.append("控制非必要开支")
        else:
            mitigation.append("保持良好的储蓄习惯")
        
        return mitigation
    
    def _generate_social_mitigation(self, score: float, factors: List[str]) -> List[str]:
        """生成社交风险缓解建议"""
        mitigation = []
        
        if score >= 7:
            mitigation.append("主动维护重要的社交关系")
            mitigation.append("定期参加社交活动或兴趣小组")
            mitigation.append("利用线上方式保持联系")
        elif score >= 4:
            mitigation.append("每周安排固定的社交时间")
            mitigation.append("保持与朋友的定期联系")
        else:
            mitigation.append("继续保持良好的社交平衡")
        
        return mitigation
    
    def _generate_time_mitigation(self, score: float, factors: List[str]) -> List[str]:
        """生成时间风险缓解建议"""
        mitigation = []
        
        if score >= 7:
            mitigation.append("使用时间管理工具，如番茄工作法")
            mitigation.append("学会说不，避免过度承诺")
            mitigation.append("优先处理重要且紧急的事项")
        elif score >= 4:
            mitigation.append("制定每日/每周计划")
            mitigation.append("合理分配工作和休息时间")
        else:
            mitigation.append("保持当前的时间管理方式")
        
        return mitigation
    
    def _generate_emotion_mitigation(self, score: float, factors: List[str]) -> List[str]:
        """生成情绪风险缓解建议"""
        mitigation = []
        
        if score >= 7:
            mitigation.append("考虑寻求心理咨询支持")
            mitigation.append("培养情绪调节技巧")
            mitigation.append("保持与亲友的情感连接")
        elif score >= 4:
            mitigation.append("定期进行放松活动")
            mitigation.append("记录情绪日记，觉察情绪变化")
        else:
            mitigation.append("继续保持积极的心态")
        
        return mitigation
    
    def _generate_learning_mitigation(self, score: float, factors: List[str]) -> List[str]:
        """生成学习风险缓解建议"""
        mitigation = []
        
        if score >= 7:
            mitigation.append("寻找导师或学习伙伴")
            mitigation.append("分解大目标为小步骤")
            mitigation.append("提前准备，留出充足的学习时间")
        elif score >= 4:
            mitigation.append("制定系统的学习计划")
            mitigation.append("定期复习和总结")
        else:
            mitigation.append("保持当前的学习节奏")
        
        return mitigation
    
    def _generate_recommendations(self, dimensions: Dict[str, RiskDimension], profile: Any) -> List[str]:
        """生成总体建议"""
        recommendations = []
        
        # 找出高风险维度
        high_risks = [
            dim for dim in dimensions.values()
            if dim.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]
        
        if high_risks:
            recommendations.append(f"⚠️ 需要特别关注{len(high_risks)}个高风险维度")
            for risk in high_risks:
                recommendations.append(f"• {risk.name}: {risk.factors[0] if risk.factors else '需要注意'}")
        else:
            recommendations.append("✅ 整体风险可控，可以考虑此选项")
        
        # 根据性格给建议
        if profile:
            if hasattr(profile, 'risk_preference'):
                if profile.risk_preference == "risk_averse" and len(high_risks) > 0:
                    recommendations.append("💡 考虑到你的风险规避偏好，建议谨慎评估")
                elif profile.risk_preference == "risk_seeking" and len(high_risks) == 0:
                    recommendations.append("💡 此选项较为稳妥，符合稳健发展策略")
        
        return recommendations


# 测试代码
if __name__ == "__main__":
    engine = RiskAssessmentEngine()
    
    # 模拟时间线
    timeline = [
        {
            "month": 1,
            "event": "开始备考，压力增大",
            "impact": {"学习": 0.8, "时间": -0.5, "情绪": -0.3, "健康": -0.2, "社交": -0.3, "财务": -0.1},
            "probability": 0.9
        },
        {
            "month": 3,
            "event": "进入强化阶段，感到疲惫",
            "impact": {"学习": 0.9, "时间": -0.7, "情绪": -0.5, "健康": -0.4, "社交": -0.4, "财务": -0.1},
            "probability": 0.85
        },
        {
            "month": 6,
            "event": "冲刺阶段，焦虑感上升",
            "impact": {"学习": 0.7, "时间": -0.8, "情绪": -0.6, "健康": -0.5, "社交": -0.5, "财务": -0.2},
            "probability": 0.8
        }
    ]
    
    # 模拟性格画像
    class MockProfile:
        neuroticism = 3
        extraversion = 4
        openness = 3
        risk_preference = "risk_neutral"
    
    # 评估风险
    assessment = engine.assess_option_risk(
        option_title="考研",
        timeline=timeline,
        profile=MockProfile()
    )
    
    print("="*60)
    print("风险评估结果")
    print("="*60)
    print(f"\n选项: {assessment.option_title}")
    print(f"总体风险: {assessment.overall_risk:.1f}/10 ({assessment.overall_level.value})")
    print(f"高风险维度数: {assessment.high_risk_count}")
    
    print(f"\n6大风险维度:")
    for key, dim in assessment.dimensions.items():
        print(f"\n{dim.name}: {dim.score:.1f}/10 ({dim.level.value})")
        print(f"  风险因素:")
        for factor in dim.factors:
            print(f"    - {factor}")
        print(f"  缓解建议:")
        for mit in dim.mitigation:
            print(f"    • {mit}")
    
    print(f"\n总体建议:")
    for rec in assessment.recommendations:
        print(f"  {rec}")
    
    print("\n" + "="*60)
