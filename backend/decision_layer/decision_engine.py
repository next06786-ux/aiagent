"""
决策层系统 - 核心决策引擎
基于真实数据的决策支持系统
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """决策类型"""
    HEALTH_ALERT = "health_alert"  # 健康警报
    ACTIVITY_RECOMMENDATION = "activity_recommendation"  # 活动建议
    SLEEP_OPTIMIZATION = "sleep_optimization"  # 睡眠优化
    STRESS_MANAGEMENT = "stress_management"  # 压力管理
    NUTRITION_GUIDANCE = "nutrition_guidance"  # 营养指导
    EXERCISE_PLAN = "exercise_plan"  # 运动计划
    SOCIAL_CONNECTION = "social_connection"  # 社交连接
    WORK_LIFE_BALANCE = "work_life_balance"  # 工作生活平衡
    EMERGENCY = "emergency"  # 紧急情况


class DecisionPriority(Enum):
    """决策优先级"""
    CRITICAL = 5  # 紧急
    HIGH = 4  # 高
    MEDIUM = 3  # 中
    LOW = 2  # 低
    INFO = 1  # 信息


class DecisionConfidence(Enum):
    """决策置信度"""
    VERY_HIGH = 0.9  # 非常高
    HIGH = 0.7  # 高
    MEDIUM = 0.5  # 中
    LOW = 0.3  # 低


@dataclass
class HealthMetrics:
    """健康指标"""
    heart_rate: float
    blood_oxygen: float
    temperature: float
    blood_pressure_systolic: float
    blood_pressure_diastolic: float
    sleep_hours: float
    exercise_minutes: int
    stress_level: float  # 0-100
    
    def is_abnormal(self) -> bool:
        """检查是否异常"""
        return (
            self.heart_rate < 40 or self.heart_rate > 120 or
            self.blood_oxygen < 95 or
            self.temperature < 36 or self.temperature > 38.5 or
            self.blood_pressure_systolic > 140 or self.blood_pressure_diastolic > 90
        )


@dataclass
class Decision:
    """决策对象"""
    decision_id: str
    user_id: str
    decision_type: DecisionType
    priority: DecisionPriority
    recommendation: str
    reasoning: str
    confidence: float
    expected_impact: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    user_feedback: Optional[str] = None
    actual_impact: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'decision_id': self.decision_id,
            'user_id': self.user_id,
            'decision_type': self.decision_type.value,
            'priority': self.priority.name,
            'recommendation': self.recommendation,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'expected_impact': self.expected_impact,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'user_feedback': self.user_feedback,
            'actual_impact': self.actual_impact
        }


class DecisionEngine:
    """决策引擎"""
    
    def __init__(self, data_service, knowledge_graph, rl_agent):
        """
        初始化决策引擎
        
        Args:
            data_service: 数据服务
            knowledge_graph: 知识图谱
            rl_agent: 强化学习代理
        """
        self.data_service = data_service
        self.knowledge_graph = knowledge_graph
        self.rl_agent = rl_agent
        self.decisions_cache: Dict[str, Decision] = {}
    
    def analyze_health_metrics(self, user_id: str, metrics: HealthMetrics) -> List[Decision]:
        """
        分析健康指标并生成决策
        
        Args:
            user_id: 用户ID
            metrics: 健康指标
            
        Returns:
            决策列表
        """
        decisions = []
        
        # 1. 检查异常指标
        if metrics.is_abnormal():
            decision = self._create_health_alert(user_id, metrics)
            decisions.append(decision)
        
        # 2. 分析心率趋势
        if metrics.heart_rate > 100:
            decision = self._create_stress_management_decision(user_id, metrics)
            decisions.append(decision)
        
        # 3. 分析睡眠质量
        if metrics.sleep_hours < 6:
            decision = self._create_sleep_optimization_decision(user_id, metrics)
            decisions.append(decision)
        
        # 4. 分析运动量
        if metrics.exercise_minutes < 30:
            decision = self._create_exercise_recommendation(user_id, metrics)
            decisions.append(decision)
        
        return decisions
    
    def _create_health_alert(self, user_id: str, metrics: HealthMetrics) -> Decision:
        """创建健康警报决策"""
        
        abnormal_metrics = []
        if metrics.heart_rate < 40 or metrics.heart_rate > 120:
            abnormal_metrics.append(f"心率异常: {metrics.heart_rate} bpm")
        if metrics.blood_oxygen < 95:
            abnormal_metrics.append(f"血氧偏低: {metrics.blood_oxygen}%")
        if metrics.temperature < 36 or metrics.temperature > 38.5:
            abnormal_metrics.append(f"体温异常: {metrics.temperature}°C")
        
        reasoning = f"检测到以下异常指标: {', '.join(abnormal_metrics)}"
        
        return Decision(
            decision_id=self._generate_decision_id(),
            user_id=user_id,
            decision_type=DecisionType.HEALTH_ALERT,
            priority=DecisionPriority.CRITICAL,
            recommendation="请立即就医或联系医疗专业人士",
            reasoning=reasoning,
            confidence=0.95,
            expected_impact={
                'health_risk_reduction': 0.8,
                'medical_intervention_needed': True
            },
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)
        )
    
    def _create_stress_management_decision(self, user_id: str, metrics: HealthMetrics) -> Decision:
        """创建压力管理决策"""
        
        return Decision(
            decision_id=self._generate_decision_id(),
            user_id=user_id,
            decision_type=DecisionType.STRESS_MANAGEMENT,
            priority=DecisionPriority.HIGH,
            recommendation="建议进行放松活动: 深呼吸、冥想或瑜伽",
            reasoning=f"心率较高 ({metrics.heart_rate} bpm)，可能表示压力或焦虑",
            confidence=0.75,
            expected_impact={
                'heart_rate_reduction': 0.3,
                'stress_level_reduction': 0.4,
                'well_being_improvement': 0.5
            },
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=4)
        )
    
    def _create_sleep_optimization_decision(self, user_id: str, metrics: HealthMetrics) -> Decision:
        """创建睡眠优化决策"""
        
        return Decision(
            decision_id=self._generate_decision_id(),
            user_id=user_id,
            decision_type=DecisionType.SLEEP_OPTIMIZATION,
            priority=DecisionPriority.MEDIUM,
            recommendation="建议增加睡眠时间至7-9小时，建立规律的睡眠时间表",
            reasoning=f"睡眠时间不足 ({metrics.sleep_hours} 小时)，可能影响健康和认知功能",
            confidence=0.8,
            expected_impact={
                'sleep_quality_improvement': 0.6,
                'energy_level_increase': 0.5,
                'cognitive_performance_improvement': 0.4
            },
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7)
        )
    
    def _create_exercise_recommendation(self, user_id: str, metrics: HealthMetrics) -> Decision:
        """创建运动建议决策"""
        
        return Decision(
            decision_id=self._generate_decision_id(),
            user_id=user_id,
            decision_type=DecisionType.EXERCISE_PLAN,
            priority=DecisionPriority.MEDIUM,
            recommendation="建议每天进行30分钟的中等强度运动，如快走、骑自行车或游泳",
            reasoning=f"运动量不足 ({metrics.exercise_minutes} 分钟)，建议增加体育活动",
            confidence=0.7,
            expected_impact={
                'cardiovascular_health_improvement': 0.5,
                'weight_management': 0.4,
                'mental_health_improvement': 0.6
            },
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7)
        )
    
    def analyze_context(self, user_id: str, context: Dict[str, Any]) -> List[Decision]:
        """
        基于上下文分析生成决策
        
        Args:
            user_id: 用户ID
            context: 上下文信息 (时间、位置、活动等)
            
        Returns:
            决策列表
        """
        decisions = []
        
        # 1. 分析工作生活平衡
        if context.get('work_hours', 0) > 10:
            decision = self._create_work_life_balance_decision(user_id, context)
            decisions.append(decision)
        
        # 2. 分析社交连接
        if context.get('social_interaction_hours', 0) < 1:
            decision = self._create_social_connection_decision(user_id, context)
            decisions.append(decision)
        
        # 3. 分析营养
        if context.get('meal_count', 0) < 3:
            decision = self._create_nutrition_guidance_decision(user_id, context)
            decisions.append(decision)
        
        return decisions
    
    def _create_work_life_balance_decision(self, user_id: str, context: Dict[str, Any]) -> Decision:
        """创建工作生活平衡决策"""
        
        return Decision(
            decision_id=self._generate_decision_id(),
            user_id=user_id,
            decision_type=DecisionType.WORK_LIFE_BALANCE,
            priority=DecisionPriority.MEDIUM,
            recommendation="建议安排休息时间，进行放松活动或与家人朋友互动",
            reasoning=f"工作时间过长 ({context.get('work_hours', 0)} 小时)，需要平衡工作和生活",
            confidence=0.7,
            expected_impact={
                'burnout_prevention': 0.6,
                'productivity_improvement': 0.4,
                'well_being_improvement': 0.7
            },
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=1)
        )
    
    def _create_social_connection_decision(self, user_id: str, context: Dict[str, Any]) -> Decision:
        """创建社交连接决策"""
        
        return Decision(
            decision_id=self._generate_decision_id(),
            user_id=user_id,
            decision_type=DecisionType.SOCIAL_CONNECTION,
            priority=DecisionPriority.LOW,
            recommendation="建议与朋友或家人进行社交互动，可以改善心理健康",
            reasoning="社交互动时间较少，可能影响心理健康和幸福感",
            confidence=0.6,
            expected_impact={
                'mental_health_improvement': 0.5,
                'loneliness_reduction': 0.7,
                'well_being_improvement': 0.6
            },
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=3)
        )
    
    def _create_nutrition_guidance_decision(self, user_id: str, context: Dict[str, Any]) -> Decision:
        """创建营养指导决策"""
        
        return Decision(
            decision_id=self._generate_decision_id(),
            user_id=user_id,
            decision_type=DecisionType.NUTRITION_GUIDANCE,
            priority=DecisionPriority.MEDIUM,
            recommendation="建议规律进食，每天3餐，包含蛋白质、蔬菜和全谷物",
            reasoning="进食次数不足，可能导致营养不均衡和能量不足",
            confidence=0.65,
            expected_impact={
                'energy_level_improvement': 0.5,
                'nutrition_balance': 0.6,
                'metabolic_health_improvement': 0.4
            },
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=1)
        )
    
    def rank_decisions(self, decisions: List[Decision]) -> List[Decision]:
        """
        对决策进行排序
        
        Args:
            decisions: 决策列表
            
        Returns:
            排序后的决策列表
        """
        return sorted(
            decisions,
            key=lambda d: (d.priority.value, d.confidence),
            reverse=True
        )
    
    def filter_decisions(self, decisions: List[Decision], max_count: int = 5) -> List[Decision]:
        """
        过滤决策，返回最重要的N个
        
        Args:
            decisions: 决策列表
            max_count: 最大决策数
            
        Returns:
            过滤后的决策列表
        """
        ranked = self.rank_decisions(decisions)
        return ranked[:max_count]
    
    def _generate_decision_id(self) -> str:
        """生成决策ID"""
        import uuid
        return f"decision_{uuid.uuid4().hex[:12]}"
    
    def cache_decision(self, decision: Decision):
        """缓存决策"""
        self.decisions_cache[decision.decision_id] = decision
    
    def get_cached_decision(self, decision_id: str) -> Optional[Decision]:
        """获取缓存的决策"""
        return self.decisions_cache.get(decision_id)
    
    def update_decision_with_feedback(self, decision_id: str, feedback: str, actual_impact: Dict[str, Any]):
        """
        使用用户反馈更新决策
        
        Args:
            decision_id: 决策ID
            feedback: 用户反馈
            actual_impact: 实际影响
        """
        decision = self.get_cached_decision(decision_id)
        if decision:
            decision.user_feedback = feedback
            decision.actual_impact = actual_impact
            logger.info(f"Decision {decision_id} updated with feedback")


class DecisionExecutor:
    """决策执行器"""
    
    def __init__(self, notification_service, data_service):
        """
        初始化决策执行器
        
        Args:
            notification_service: 通知服务
            data_service: 数据服务
        """
        self.notification_service = notification_service
        self.data_service = data_service
    
    def execute_decision(self, decision: Decision) -> bool:
        """
        执行决策
        
        Args:
            decision: 决策对象
            
        Returns:
            是否执行成功
        """
        try:
            # 1. 保存决策到数据库
            self.data_service.save_decision(decision)
            
            # 2. 发送通知
            self._send_notification(decision)
            
            # 3. 记录执行日志
            logger.info(f"Decision {decision.decision_id} executed successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error executing decision: {e}")
            return False
    
    def _send_notification(self, decision: Decision):
        """发送通知"""
        
        notification_title = f"[{decision.priority.name}] {decision.decision_type.value}"
        notification_body = decision.recommendation
        
        self.notification_service.send_notification(
            user_id=decision.user_id,
            title=notification_title,
            body=notification_body,
            priority=decision.priority.value,
            data={
                'decision_id': decision.decision_id,
                'decision_type': decision.decision_type.value
            }
        )

