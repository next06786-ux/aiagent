"""
决策层系统集成测试
验证决策引擎、前端数据集成和 API 的功能
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockDataService:
    """模拟数据服务"""
    
    def __init__(self):
        self.decisions = []
        self.sensor_data = []
        self.health_data = []
    
    def save_decision(self, decision):
        """保存决策"""
        self.decisions.append(decision)
    
    def save_sensor_data(self, user_id, data_point):
        """保存传感器数据"""
        self.sensor_data.append((user_id, data_point))
    
    def save_health_data(self, user_id, data_point):
        """保存健康数据"""
        self.health_data.append((user_id, data_point))


class MockKnowledgeGraph:
    """模拟知识图谱"""
    
    def query(self, query_str):
        """查询知识图谱"""
        return []


class MockRLAgent:
    """模拟强化学习代理"""
    
    def get_action(self, state):
        """获取动作"""
        return "default_action"


class TestDecisionEngine(unittest.TestCase):
    """决策引擎测试"""
    
    def setUp(self):
        """测试前准备"""
        from backend.decision_layer.decision_engine import DecisionEngine, HealthMetrics
        
        self.data_service = MockDataService()
        self.kg = MockKnowledgeGraph()
        self.rl_agent = MockRLAgent()
        
        self.decision_engine = DecisionEngine(self.data_service, self.kg, self.rl_agent)
        self.HealthMetrics = HealthMetrics
    
    def test_analyze_health_metrics_normal(self):
        """测试正常健康指标分析"""
        metrics = self.HealthMetrics(
            heart_rate=72,
            blood_oxygen=98,
            temperature=37,
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            sleep_hours=8,
            exercise_minutes=30,
            stress_level=30
        )
        
        decisions = self.decision_engine.analyze_health_metrics("user_001", metrics)
        
        # 正常指标应该生成较少的决策
        self.assertLessEqual(len(decisions), 2)
        logger.info(f"✓ Normal metrics test passed: {len(decisions)} decisions generated")
    
    def test_analyze_health_metrics_abnormal(self):
        """测试异常健康指标分析"""
        metrics = self.HealthMetrics(
            heart_rate=150,  # 异常高
            blood_oxygen=92,  # 异常低
            temperature=38.5,  # 异常高
            blood_pressure_systolic=160,  # 异常高
            blood_pressure_diastolic=100,  # 异常高
            sleep_hours=4,  # 睡眠不足
            exercise_minutes=0,  # 无运动
            stress_level=80  # 压力高
        )
        
        decisions = self.decision_engine.analyze_health_metrics("user_001", metrics)
        
        # 异常指标应该生成多个决策
        self.assertGreater(len(decisions), 0)
        
        # 应该包含健康警报
        has_alert = any(d.decision_type.value == 'health_alert' for d in decisions)
        self.assertTrue(has_alert)
        
        logger.info(f"✓ Abnormal metrics test passed: {len(decisions)} decisions generated")
    
    def test_analyze_context(self):
        """测试上下文分析"""
        context = {
            'work_hours': 12,
            'social_interaction_hours': 0.5,
            'meal_count': 2,
            'location': 'office',
            'activity': 'working'
        }
        
        decisions = self.decision_engine.analyze_context("user_001", context)
        
        # 应该生成工作生活平衡和社交连接决策
        self.assertGreater(len(decisions), 0)
        
        logger.info(f"✓ Context analysis test passed: {len(decisions)} decisions generated")
    
    def test_rank_decisions(self):
        """测试决策排序"""
        metrics = self.HealthMetrics(
            heart_rate=150,
            blood_oxygen=92,
            temperature=38.5,
            blood_pressure_systolic=160,
            blood_pressure_diastolic=100,
            sleep_hours=4,
            exercise_minutes=0,
            stress_level=80
        )
        
        decisions = self.decision_engine.analyze_health_metrics("user_001", metrics)
        ranked = self.decision_engine.rank_decisions(decisions)
        
        # 验证排序
        for i in range(len(ranked) - 1):
            self.assertGreaterEqual(
                ranked[i].priority.value,
                ranked[i + 1].priority.value
            )
        
        logger.info(f"✓ Decision ranking test passed")
    
    def test_filter_decisions(self):
        """测试决策过滤"""
        metrics = self.HealthMetrics(
            heart_rate=150,
            blood_oxygen=92,
            temperature=38.5,
            blood_pressure_systolic=160,
            blood_pressure_diastolic=100,
            sleep_hours=4,
            exercise_minutes=0,
            stress_level=80
        )
        
        decisions = self.decision_engine.analyze_health_metrics("user_001", metrics)
        filtered = self.decision_engine.filter_decisions(decisions, max_count=3)
        
        # 过滤后的决策数不应超过 max_count
        self.assertLessEqual(len(filtered), 3)
        
        logger.info(f"✓ Decision filtering test passed: {len(filtered)} decisions after filtering")


class TestSensorDataCollector(unittest.TestCase):
    """传感器数据收集器测试"""
    
    def setUp(self):
        """测试前准备"""
        from backend.decision_layer.frontend_integration import SensorDataCollector, SensorDataPoint
        
        self.data_service = MockDataService()
        self.collector = SensorDataCollector(self.data_service)
        self.SensorDataPoint = SensorDataPoint
    
    def test_add_sensor_data(self):
        """测试添加传感器数据"""
        data_point = self.SensorDataPoint(
            timestamp=datetime.now(),
            sensor_type='heart_rate',
            value=72.5,
            unit='bpm',
            accuracy=0.95,
            device_id='device_001'
        )
        
        self.collector.add_sensor_data("user_001", data_point)
        
        # 验证数据被添加
        retrieved = self.collector.get_sensor_data("user_001", sensor_type='heart_rate')
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0].value, 72.5)
        
        logger.info(f"✓ Add sensor data test passed")
    
    def test_get_sensor_data_with_filter(self):
        """测试带过滤的传感器数据查询"""
        # 添加多个数据点
        for i in range(5):
            data_point = self.SensorDataPoint(
                timestamp=datetime.now() - timedelta(minutes=i),
                sensor_type='heart_rate' if i % 2 == 0 else 'temperature',
                value=70 + i,
                unit='bpm' if i % 2 == 0 else '°C',
                accuracy=0.95,
                device_id='device_001'
            )
            self.collector.add_sensor_data("user_001", data_point)
        
        # 按类型过滤
        heart_rate_data = self.collector.get_sensor_data("user_001", sensor_type='heart_rate')
        self.assertEqual(len(heart_rate_data), 3)
        
        logger.info(f"✓ Sensor data filtering test passed")
    
    def test_callback_registration(self):
        """测试回调函数注册"""
        callback_called = []
        
        def test_callback(user_id, data_type, data_point):
            callback_called.append((user_id, data_type))
        
        self.collector.register_callback(test_callback)
        
        data_point = self.SensorDataPoint(
            timestamp=datetime.now(),
            sensor_type='heart_rate',
            value=72.5,
            unit='bpm',
            accuracy=0.95,
            device_id='device_001'
        )
        
        self.collector.add_sensor_data("user_001", data_point)
        
        # 验证回调被调用
        self.assertEqual(len(callback_called), 1)
        self.assertEqual(callback_called[0], ("user_001", "sensor"))
        
        logger.info(f"✓ Callback registration test passed")


class TestRealTimeDataProcessor(unittest.TestCase):
    """实时数据处理器测试"""
    
    def setUp(self):
        """测试前准备"""
        from backend.decision_layer.frontend_integration import (
            SensorDataCollector, RealTimeDataProcessor, SensorDataPoint
        )
        from backend.decision_layer.decision_engine import DecisionEngine
        
        self.data_service = MockDataService()
        self.kg = MockKnowledgeGraph()
        self.rl_agent = MockRLAgent()
        
        self.collector = SensorDataCollector(self.data_service)
        self.decision_engine = DecisionEngine(self.data_service, self.kg, self.rl_agent)
        self.processor = RealTimeDataProcessor(self.decision_engine, self.collector)
        
        self.SensorDataPoint = SensorDataPoint
    
    def test_process_sensor_data(self):
        """测试处理传感器数据"""
        data_point = self.SensorDataPoint(
            timestamp=datetime.now(),
            sensor_type='heart_rate',
            value=72.5,
            unit='bpm',
            accuracy=0.95,
            device_id='device_001'
        )
        
        # 应该不抛出异常
        self.processor.process_sensor_data("user_001", "sensor", data_point)
        
        logger.info(f"✓ Process sensor data test passed")


class TestFrontendDataBridge(unittest.TestCase):
    """前端数据桥接器测试"""
    
    def setUp(self):
        """测试前准备"""
        from backend.decision_layer.frontend_integration import (
            SensorDataCollector, RealTimeDataProcessor, FrontendDataBridge
        )
        from backend.decision_layer.decision_engine import DecisionEngine
        
        self.data_service = MockDataService()
        self.kg = MockKnowledgeGraph()
        self.rl_agent = MockRLAgent()
        
        self.collector = SensorDataCollector(self.data_service)
        self.decision_engine = DecisionEngine(self.data_service, self.kg, self.rl_agent)
        self.processor = RealTimeDataProcessor(self.decision_engine, self.collector)
        
        self.bridge = FrontendDataBridge(self.collector, self.processor)
    
    def test_receive_sensor_data_from_frontend(self):
        """测试从前端接收传感器数据"""
        sensor_data = {
            'sensor_type': 'heart_rate',
            'value': 72.5,
            'unit': 'bpm',
            'accuracy': 0.95,
            'device_id': 'device_001',
            'timestamp': datetime.now().isoformat()
        }
        
        # 应该不抛出异常
        self.bridge.receive_sensor_data_from_frontend("user_001", sensor_data)
        
        # 验证数据被收集
        collected = self.collector.get_sensor_data("user_001", sensor_type='heart_rate')
        self.assertEqual(len(collected), 1)
        
        logger.info(f"✓ Receive sensor data from frontend test passed")
    
    def test_receive_health_data_from_frontend(self):
        """测试从前端接收健康数据"""
        health_data = {
            'data_type': 'blood_pressure',
            'value': 120,
            'unit': 'mmHg',
            'source': 'wearable',
            'timestamp': datetime.now().isoformat()
        }
        
        # 应该不抛出异常
        self.bridge.receive_health_data_from_frontend("user_001", health_data)
        
        # 验证数据被收集
        collected = self.collector.get_health_data("user_001", data_type='blood_pressure')
        self.assertEqual(len(collected), 1)
        
        logger.info(f"✓ Receive health data from frontend test passed")
    
    def test_batch_receive_sensor_data(self):
        """测试批量接收传感器数据"""
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
                'value': 37.0,
                'unit': '°C',
                'accuracy': 0.9,
                'device_id': 'device_001',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        self.bridge.batch_receive_sensor_data("user_001", sensor_data_list)
        
        # 验证所有数据被收集
        all_data = self.collector.get_sensor_data("user_001")
        self.assertEqual(len(all_data), 2)
        
        logger.info(f"✓ Batch receive sensor data test passed")


class TestDecisionExecutor(unittest.TestCase):
    """决策执行器测试"""
    
    def setUp(self):
        """测试前准备"""
        from backend.decision_layer.decision_engine import DecisionExecutor, Decision, DecisionType, DecisionPriority
        
        self.data_service = MockDataService()
        self.notification_service = MockNotificationService()
        self.executor = DecisionExecutor(self.notification_service, self.data_service)
        
        self.Decision = Decision
        self.DecisionType = DecisionType
        self.DecisionPriority = DecisionPriority
    
    def test_execute_decision(self):
        """测试执行决策"""
        decision = self.Decision(
            decision_id="test_decision_001",
            user_id="user_001",
            decision_type=self.DecisionType.HEALTH_ALERT,
            priority=self.DecisionPriority.HIGH,
            recommendation="Test recommendation",
            reasoning="Test reasoning",
            confidence=0.8,
            expected_impact={'test': 0.5},
            created_at=datetime.now()
        )
        
        success = self.executor.execute_decision(decision)
        
        self.assertTrue(success)
        self.assertEqual(len(self.data_service.decisions), 1)
        
        logger.info(f"✓ Execute decision test passed")


class MockNotificationService:
    """模拟通知服务"""
    
    def __init__(self):
        self.notifications = []
    
    def send_notification(self, user_id, title, body, priority, data):
        """发送通知"""
        self.notifications.append({
            'user_id': user_id,
            'title': title,
            'body': body,
            'priority': priority,
            'data': data
        })


def run_tests():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("开始运行决策层系统集成测试")
    logger.info("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestSensorDataCollector))
    suite.addTests(loader.loadTestsFromTestCase(TestRealTimeDataProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestFrontendDataBridge))
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionExecutor))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    logger.info("=" * 60)
    logger.info(f"测试完成: {result.testsRun} 个测试")
    logger.info(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"失败: {len(result.failures)}")
    logger.info(f"错误: {len(result.errors)}")
    logger.info("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

