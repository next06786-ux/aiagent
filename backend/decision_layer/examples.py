"""
决策层系统使用示例
演示如何集成和使用决策层系统
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExampleDataService:
    """示例数据服务"""
    
    def __init__(self):
        self.decisions = []
        self.sensor_data = []
        self.health_data = []
    
    def save_decision(self, decision):
        """保存决策"""
        self.decisions.append(decision)
        logger.info(f"Saved decision: {decision.decision_id}")
    
    def save_sensor_data(self, user_id, data_point):
        """保存传感器数据"""
        self.sensor_data.append((user_id, data_point))
    
    def save_health_data(self, user_id, data_point):
        """保存健康数据"""
        self.health_data.append((user_id, data_point))


class ExampleKnowledgeGraph:
    """示例知识图谱"""
    
    def query(self, query_str):
        """查询知识图谱"""
        return []


class ExampleRLAgent:
    """示例强化学习代理"""
    
    def get_action(self, state):
        """获取动作"""
        return "default_action"


class ExampleNotificationService:
    """示例通知服务"""
    
    def __init__(self):
        self.notifications = []
    
    def send_notification(self, user_id, title, body, priority, data):
        """发送通知"""
        self.notifications.append({
            'user_id': user_id,
            'title': title,
            'body': body,
            'priority': priority,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        logger.info(f"Sent notification to {user_id}: {title}")


def example_1_basic_health_analysis():
    """示例 1: 基本健康指标分析"""
    logger.info("\n" + "=" * 60)
    logger.info("示例 1: 基本健康指标分析")
    logger.info("=" * 60)
    
    from backend.decision_layer import initialize_decision_layer, get_decision_layer_system
    from backend.decision_layer.decision_engine import HealthMetrics
    
    # 初始化系统
    data_service = ExampleDataService()
    kg = ExampleKnowledgeGraph()
    rl_agent = ExampleRLAgent()
    notification_service = ExampleNotificationService()
    
    initialize_decision_layer(data_service, kg, rl_agent, notification_service)
    system = get_decision_layer_system()
    
    # 获取决策引擎
    decision_engine = system.get_decision_engine()
    
    # 创建健康指标
    metrics = HealthMetrics(
        heart_rate=85,
        blood_oxygen=96,
        temperature=37.2,
        blood_pressure_systolic=130,
        blood_pressure_diastolic=85,
        sleep_hours=6.5,
        exercise_minutes=20,
        stress_level=45
    )
    
    # 分析健康指标
    decisions = decision_engine.analyze_health_metrics("user_001", metrics)
    
    logger.info(f"Generated {len(decisions)} decisions:")
    for decision in decisions:
        logger.info(f"  - [{decision.priority.name}] {decision.decision_type.value}")
        logger.info(f"    Recommendation: {decision.recommendation}")
        logger.info(f"    Confidence: {decision.confidence}")


def example_2_context_analysis():
    """示例 2: 上下文分析"""
    logger.info("\n" + "=" * 60)
    logger.info("示例 2: 上下文分析")
    logger.info("=" * 60)
    
    from backend.decision_layer import initialize_decision_layer, get_decision_layer_system
    
    # 初始化系统
    data_service = ExampleDataService()
    kg = ExampleKnowledgeGraph()
    rl_agent = ExampleRLAgent()
    notification_service = ExampleNotificationService()
    
    initialize_decision_layer(data_service, kg, rl_agent, notification_service)
    system = get_decision_layer_system()
    
    # 获取决策引擎
    decision_engine = system.get_decision_engine()
    
    # 创建上下文
    context = {
        'work_hours': 11,
        'social_interaction_hours': 0.5,
        'meal_count': 2,
        'location': 'office',
        'activity': 'working'
    }
    
    # 分析上下文
    decisions = decision_engine.analyze_context("user_001", context)
    
    logger.info(f"Generated {len(decisions)} context-based decisions:")
    for decision in decisions:
        logger.info(f"  - [{decision.priority.name}] {decision.decision_type.value}")
        logger.info(f"    Recommendation: {decision.recommendation}")


def example_3_frontend_data_integration():
    """示例 3: 前端数据集成"""
    logger.info("\n" + "=" * 60)
    logger.info("示例 3: 前端数据集成")
    logger.info("=" * 60)
    
    from backend.decision_layer import initialize_decision_layer, get_decision_layer_system
    
    # 初始化系统
    data_service = ExampleDataService()
    kg = ExampleKnowledgeGraph()
    rl_agent = ExampleRLAgent()
    notification_service = ExampleNotificationService()
    
    initialize_decision_layer(data_service, kg, rl_agent, notification_service)
    system = get_decision_layer_system()
    
    # 获取前端数据桥接器
    frontend_bridge = system.get_frontend_bridge()
    
    # 模拟从前端接收传感器数据
    sensor_data_list = [
        {
            'sensor_type': 'heart_rate',
            'value': 72.5,
            'unit': 'bpm',
            'accuracy': 0.95,
            'device_id': 'device_001',
            'timestamp': datetime.now().isoformat()
        },
        {
            'sensor_type': 'temperature',
            'value': 37.1,
            'unit': '°C',
            'accuracy': 0.9,
            'device_id': 'device_001',
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    logger.info("Receiving sensor data from frontend...")
    frontend_bridge.batch_receive_sensor_data("user_001", sensor_data_list)
    
    # 模拟从前端接收健康数据
    health_data_list = [
        {
            'data_type': 'blood_pressure',
            'value': 120,
            'unit': 'mmHg',
            'source': 'wearable',
            'timestamp': datetime.now().isoformat()
        },
        {
            'data_type': 'sleep',
            'value': 7.5,
            'unit': 'hours',
            'source': 'wearable',
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
        }
    ]
    
    logger.info("Receiving health data from frontend...")
    frontend_bridge.batch_receive_health_data("user_001", health_data_list)
    
    # 获取收集的数据
    sensor_collector = system.get_sensor_collector()
    collected_sensor = sensor_collector.get_sensor_data("user_001")
    collected_health = sensor_collector.get_health_data("user_001")
    
    logger.info(f"Collected {len(collected_sensor)} sensor data points")
    logger.info(f"Collected {len(collected_health)} health data points")


def example_4_decision_execution():
    """示例 4: 决策执行"""
    logger.info("\n" + "=" * 60)
    logger.info("示例 4: 决策执行")
    logger.info("=" * 60)
    
    from backend.decision_layer import initialize_decision_layer, get_decision_layer_system
    from backend.decision_layer.decision_engine import Decision, DecisionType, DecisionPriority
    
    # 初始化系统
    data_service = ExampleDataService()
    kg = ExampleKnowledgeGraph()
    rl_agent = ExampleRLAgent()
    notification_service = ExampleNotificationService()
    
    initialize_decision_layer(data_service, kg, rl_agent, notification_service)
    system = get_decision_layer_system()
    
    # 获取决策执行器
    decision_executor = system.get_decision_executor()
    
    # 创建决策
    decision = Decision(
        decision_id="decision_001",
        user_id="user_001",
        decision_type=DecisionType.EXERCISE_PLAN,
        priority=DecisionPriority.MEDIUM,
        recommendation="建议每天进行30分钟的中等强度运动",
        reasoning="运动量不足，建议增加体育活动",
        confidence=0.75,
        expected_impact={
            'cardiovascular_health_improvement': 0.5,
            'weight_management': 0.4,
            'mental_health_improvement': 0.6
        },
        created_at=datetime.now()
    )
    
    # 执行决策
    logger.info("Executing decision...")
    success = decision_executor.execute_decision(decision)
    
    if success:
        logger.info("✓ Decision executed successfully")
        logger.info(f"  Saved decisions: {len(data_service.decisions)}")
        logger.info(f"  Sent notifications: {len(notification_service.notifications)}")
    else:
        logger.error("✗ Failed to execute decision")


def example_5_batch_analysis():
    """示例 5: 批量分析"""
    logger.info("\n" + "=" * 60)
    logger.info("示例 5: 批量分析")
    logger.info("=" * 60)
    
    from backend.decision_layer import initialize_decision_layer, get_decision_layer_system
    from backend.decision_layer.decision_engine import HealthMetrics
    
    # 初始化系统
    data_service = ExampleDataService()
    kg = ExampleKnowledgeGraph()
    rl_agent = ExampleRLAgent()
    notification_service = ExampleNotificationService()
    
    initialize_decision_layer(data_service, kg, rl_agent, notification_service)
    system = get_decision_layer_system()
    
    # 获取决策引擎
    decision_engine = system.get_decision_engine()
    
    # 创建健康指标
    metrics = HealthMetrics(
        heart_rate=95,
        blood_oxygen=94,
        temperature=37.5,
        blood_pressure_systolic=135,
        blood_pressure_diastolic=88,
        sleep_hours=5.5,
        exercise_minutes=15,
        stress_level=65
    )
    
    # 创建上下文
    context = {
        'work_hours': 10,
        'social_interaction_hours': 0.5,
        'meal_count': 2,
        'location': 'office',
        'activity': 'working'
    }
    
    # 分析健康指标
    health_decisions = decision_engine.analyze_health_metrics("user_001", metrics)
    
    # 分析上下文
    context_decisions = decision_engine.analyze_context("user_001", context)
    
    # 合并决策
    all_decisions = health_decisions + context_decisions
    
    # 排序和过滤
    ranked = decision_engine.rank_decisions(all_decisions)
    filtered = decision_engine.filter_decisions(ranked, max_count=5)
    
    logger.info(f"Health decisions: {len(health_decisions)}")
    logger.info(f"Context decisions: {len(context_decisions)}")
    logger.info(f"Total decisions: {len(all_decisions)}")
    logger.info(f"Filtered decisions (top 5): {len(filtered)}")
    
    logger.info("\nTop decisions:")
    for i, decision in enumerate(filtered, 1):
        logger.info(f"  {i}. [{decision.priority.name}] {decision.decision_type.value}")
        logger.info(f"     Confidence: {decision.confidence}")


def example_6_real_time_processing():
    """示例 6: 实时数据处理"""
    logger.info("\n" + "=" * 60)
    logger.info("示例 6: 实时数据处理")
    logger.info("=" * 60)
    
    from backend.decision_layer import initialize_decision_layer, get_decision_layer_system
    from backend.decision_layer.frontend_integration import SensorDataPoint
    
    # 初始化系统
    data_service = ExampleDataService()
    kg = ExampleKnowledgeGraph()
    rl_agent = ExampleRLAgent()
    notification_service = ExampleNotificationService()
    
    initialize_decision_layer(data_service, kg, rl_agent, notification_service)
    system = get_decision_layer_system()
    
    # 获取传感器收集器和实时处理器
    sensor_collector = system.get_sensor_collector()
    real_time_processor = system.get_real_time_processor()
    
    # 注册回调
    def on_data_received(user_id, data_type, data_point):
        logger.info(f"Data received: {data_type} - {data_point}")
    
    sensor_collector.register_callback(on_data_received)
    
    # 模拟实时数据流
    logger.info("Simulating real-time data stream...")
    for i in range(5):
        data_point = SensorDataPoint(
            timestamp=datetime.now(),
            sensor_type='heart_rate',
            value=70 + i * 2,
            unit='bpm',
            accuracy=0.95,
            device_id='device_001'
        )
        
        sensor_collector.add_sensor_data("user_001", data_point)
        logger.info(f"  Added data point {i+1}: heart_rate = {data_point.value} bpm")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("决策层系统使用示例")
    logger.info("=" * 60)
    
    try:
        # 运行所有示例
        example_1_basic_health_analysis()
        example_2_context_analysis()
        example_3_frontend_data_integration()
        example_4_decision_execution()
        example_5_batch_analysis()
        example_6_real_time_processing()
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ 所有示例执行完成")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == "__main__":
    main()

