"""
前端传感器数据集成模块
将 HarmonyOS 前端的真实传感器数据接入决策层
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class SensorDataPoint:
    """传感器数据点"""
    timestamp: datetime
    sensor_type: str  # 'heart_rate', 'accelerometer', 'gyroscope', 'light', 'pressure', 'temperature'
    value: float
    unit: str
    accuracy: float  # 0-1, 准确度评分
    device_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'sensor_type': self.sensor_type,
            'value': self.value,
            'unit': self.unit,
            'accuracy': self.accuracy,
            'device_id': self.device_id
        }


@dataclass
class HealthDataPoint:
    """健康数据点"""
    timestamp: datetime
    data_type: str  # 'sleep', 'exercise', 'blood_pressure', 'blood_oxygen', 'stress'
    value: float
    unit: str
    source: str  # 'wearable', 'manual', 'app'
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'data_type': self.data_type,
            'value': self.value,
            'unit': self.unit,
            'source': self.source
        }


class SensorDataCollector:
    """传感器数据收集器"""
    
    def __init__(self, data_service, buffer_size: int = 1000):
        """
        初始化传感器数据收集器
        
        Args:
            data_service: 数据服务
            buffer_size: 缓冲区大小
        """
        self.data_service = data_service
        self.buffer_size = buffer_size
        self.sensor_buffer: Dict[str, List[SensorDataPoint]] = {}
        self.health_buffer: Dict[str, List[HealthDataPoint]] = {}
        self.callbacks: List[Callable] = []
    
    def register_callback(self, callback: Callable):
        """
        注册回调函数
        当收到新数据时调用
        
        Args:
            callback: 回调函数
        """
        self.callbacks.append(callback)
    
    def add_sensor_data(self, user_id: str, data_point: SensorDataPoint):
        """
        添加传感器数据
        
        Args:
            user_id: 用户ID
            data_point: 数据点
        """
        if user_id not in self.sensor_buffer:
            self.sensor_buffer[user_id] = []
        
        self.sensor_buffer[user_id].append(data_point)
        
        # 保持缓冲区大小
        if len(self.sensor_buffer[user_id]) > self.buffer_size:
            self.sensor_buffer[user_id].pop(0)
        
        # 触发回调
        self._trigger_callbacks(user_id, 'sensor', data_point)
        
        logger.debug(f"Added sensor data for user {user_id}: {data_point.sensor_type}")
    
    def add_health_data(self, user_id: str, data_point: HealthDataPoint):
        """
        添加健康数据
        
        Args:
            user_id: 用户ID
            data_point: 数据点
        """
        if user_id not in self.health_buffer:
            self.health_buffer[user_id] = []
        
        self.health_buffer[user_id].append(data_point)
        
        # 保持缓冲区大小
        if len(self.health_buffer[user_id]) > self.buffer_size:
            self.health_buffer[user_id].pop(0)
        
        # 触发回调
        self._trigger_callbacks(user_id, 'health', data_point)
        
        logger.debug(f"Added health data for user {user_id}: {data_point.data_type}")
    
    def _trigger_callbacks(self, user_id: str, data_type: str, data_point):
        """触发回调函数"""
        for callback in self.callbacks:
            try:
                callback(user_id, data_type, data_point)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def get_sensor_data(self, user_id: str, sensor_type: Optional[str] = None,
                       time_range: Optional[tuple] = None) -> List[SensorDataPoint]:
        """
        获取传感器数据
        
        Args:
            user_id: 用户ID
            sensor_type: 传感器类型过滤
            time_range: 时间范围 (start_time, end_time)
        
        Returns:
            数据点列表
        """
        if user_id not in self.sensor_buffer:
            return []
        
        data = self.sensor_buffer[user_id]
        
        # 按传感器类型过滤
        if sensor_type:
            data = [d for d in data if d.sensor_type == sensor_type]
        
        # 按时间范围过滤
        if time_range:
            start_time, end_time = time_range
            data = [d for d in data if start_time <= d.timestamp <= end_time]
        
        return data
    
    def get_health_data(self, user_id: str, data_type: Optional[str] = None,
                       time_range: Optional[tuple] = None) -> List[HealthDataPoint]:
        """
        获取健康数据
        
        Args:
            user_id: 用户ID
            data_type: 数据类型过滤
            time_range: 时间范围 (start_time, end_time)
        
        Returns:
            数据点列表
        """
        if user_id not in self.health_buffer:
            return []
        
        data = self.health_buffer[user_id]
        
        # 按数据类型过滤
        if data_type:
            data = [d for d in data if d.data_type == data_type]
        
        # 按时间范围过滤
        if time_range:
            start_time, end_time = time_range
            data = [d for d in data if start_time <= d.timestamp <= end_time]
        
        return data
    
    def flush_to_database(self, user_id: str):
        """
        将缓冲区数据刷新到数据库
        
        Args:
            user_id: 用户ID
        """
        try:
            # 保存传感器数据
            if user_id in self.sensor_buffer:
                for data_point in self.sensor_buffer[user_id]:
                    self.data_service.save_sensor_data(user_id, data_point)
            
            # 保存健康数据
            if user_id in self.health_buffer:
                for data_point in self.health_buffer[user_id]:
                    self.data_service.save_health_data(user_id, data_point)
            
            logger.info(f"Flushed data to database for user {user_id}")
        except Exception as e:
            logger.error(f"Error flushing data to database: {e}")


class RealTimeDataProcessor:
    """实时数据处理器"""
    
    def __init__(self, decision_engine, sensor_collector):
        """
        初始化实时数据处理器
        
        Args:
            decision_engine: 决策引擎
            sensor_collector: 传感器数据收集器
        """
        self.decision_engine = decision_engine
        self.sensor_collector = sensor_collector
        self.aggregation_window = 60  # 秒
        self.last_aggregation_time: Dict[str, datetime] = {}
    
    def process_sensor_data(self, user_id: str, data_type: str, data_point):
        """
        处理传感器数据
        
        Args:
            user_id: 用户ID
            data_type: 数据类型
            data_point: 数据点
        """
        if data_type == 'sensor':
            self._process_sensor_point(user_id, data_point)
        elif data_type == 'health':
            self._process_health_point(user_id, data_point)
    
    def _process_sensor_point(self, user_id: str, data_point: SensorDataPoint):
        """处理单个传感器数据点"""
        
        # 检查是否需要聚合
        now = datetime.now()
        last_time = self.last_aggregation_time.get(user_id, now - timedelta(seconds=self.aggregation_window))
        
        if (now - last_time).total_seconds() >= self.aggregation_window:
            self._aggregate_and_analyze(user_id)
            self.last_aggregation_time[user_id] = now
    
    def _process_health_point(self, user_id: str, data_point: HealthDataPoint):
        """处理单个健康数据点"""
        
        # 立即分析健康数据
        self._analyze_health_data(user_id, data_point)
    
    def _aggregate_and_analyze(self, user_id: str):
        """聚合数据并分析"""
        
        try:
            # 获取最近的传感器数据
            time_range = (
                datetime.now() - timedelta(seconds=self.aggregation_window),
                datetime.now()
            )
            
            sensor_data = self.sensor_collector.get_sensor_data(user_id, time_range=time_range)
            health_data = self.sensor_collector.get_health_data(user_id, time_range=time_range)
            
            if not sensor_data and not health_data:
                return
            
            # 聚合数据
            aggregated_metrics = self._aggregate_metrics(sensor_data, health_data)
            
            # 生成决策
            if aggregated_metrics:
                from backend.decision_layer.decision_engine import HealthMetrics
                
                metrics = HealthMetrics(
                    heart_rate=aggregated_metrics.get('heart_rate', 0),
                    blood_oxygen=aggregated_metrics.get('blood_oxygen', 0),
                    temperature=aggregated_metrics.get('temperature', 0),
                    blood_pressure_systolic=aggregated_metrics.get('blood_pressure_systolic', 0),
                    blood_pressure_diastolic=aggregated_metrics.get('blood_pressure_diastolic', 0),
                    sleep_hours=aggregated_metrics.get('sleep_hours', 0),
                    exercise_minutes=aggregated_metrics.get('exercise_minutes', 0),
                    stress_level=aggregated_metrics.get('stress_level', 0)
                )
                
                decisions = self.decision_engine.analyze_health_metrics(user_id, metrics)
                
                logger.info(f"Generated {len(decisions)} decisions for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error in aggregation and analysis: {e}")
    
    def _analyze_health_data(self, user_id: str, data_point: HealthDataPoint):
        """分析健康数据"""
        
        try:
            # 根据数据类型进行特定分析
            if data_point.data_type == 'blood_pressure':
                self._analyze_blood_pressure(user_id, data_point)
            elif data_point.data_type == 'blood_oxygen':
                self._analyze_blood_oxygen(user_id, data_point)
            elif data_point.data_type == 'sleep':
                self._analyze_sleep(user_id, data_point)
            elif data_point.data_type == 'stress':
                self._analyze_stress(user_id, data_point)
        
        except Exception as e:
            logger.error(f"Error analyzing health data: {e}")
    
    def _aggregate_metrics(self, sensor_data: List[SensorDataPoint],
                          health_data: List[HealthDataPoint]) -> Dict[str, float]:
        """
        聚合指标
        
        Args:
            sensor_data: 传感器数据列表
            health_data: 健康数据列表
        
        Returns:
            聚合后的指标字典
        """
        metrics = {}
        
        # 聚合传感器数据
        for sensor_type in ['heart_rate', 'temperature', 'blood_oxygen']:
            values = [d.value for d in sensor_data if d.sensor_type == sensor_type]
            if values:
                metrics[sensor_type] = sum(values) / len(values)
        
        # 聚合健康数据
        for data_type in ['blood_pressure_systolic', 'blood_pressure_diastolic', 'sleep_hours', 'exercise_minutes', 'stress_level']:
            values = [d.value for d in health_data if d.data_type == data_type]
            if values:
                metrics[data_type] = sum(values) / len(values)
        
        return metrics
    
    def _analyze_blood_pressure(self, user_id: str, data_point: HealthDataPoint):
        """分析血压"""
        if data_point.value > 140:
            logger.warning(f"High blood pressure detected for user {user_id}: {data_point.value}")
    
    def _analyze_blood_oxygen(self, user_id: str, data_point: HealthDataPoint):
        """分析血氧"""
        if data_point.value < 95:
            logger.warning(f"Low blood oxygen detected for user {user_id}: {data_point.value}")
    
    def _analyze_sleep(self, user_id: str, data_point: HealthDataPoint):
        """分析睡眠"""
        if data_point.value < 6:
            logger.warning(f"Insufficient sleep detected for user {user_id}: {data_point.value} hours")
    
    def _analyze_stress(self, user_id: str, data_point: HealthDataPoint):
        """分析压力"""
        if data_point.value > 70:
            logger.warning(f"High stress level detected for user {user_id}: {data_point.value}")


class FrontendDataBridge:
    """前端数据桥接器"""
    
    def __init__(self, sensor_collector: SensorDataCollector,
                 real_time_processor: RealTimeDataProcessor):
        """
        初始化前端数据桥接器
        
        Args:
            sensor_collector: 传感器数据收集器
            real_time_processor: 实时数据处理器
        """
        self.sensor_collector = sensor_collector
        self.real_time_processor = real_time_processor
    
    def receive_sensor_data_from_frontend(self, user_id: str, sensor_data: Dict[str, Any]):
        """
        从前端接收传感器数据
        
        Args:
            user_id: 用户ID
            sensor_data: 传感器数据字典
                {
                    'sensor_type': 'heart_rate',
                    'value': 72.5,
                    'unit': 'bpm',
                    'accuracy': 0.95,
                    'device_id': 'device_001',
                    'timestamp': '2024-01-01T12:00:00'
                }
        """
        try:
            data_point = SensorDataPoint(
                timestamp=datetime.fromisoformat(sensor_data['timestamp']),
                sensor_type=sensor_data['sensor_type'],
                value=sensor_data['value'],
                unit=sensor_data['unit'],
                accuracy=sensor_data.get('accuracy', 1.0),
                device_id=sensor_data.get('device_id', 'unknown')
            )
            
            self.sensor_collector.add_sensor_data(user_id, data_point)
            logger.info(f"Received sensor data from frontend for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error receiving sensor data from frontend: {e}")
    
    def receive_health_data_from_frontend(self, user_id: str, health_data: Dict[str, Any]):
        """
        从前端接收健康数据
        
        Args:
            user_id: 用户ID
            health_data: 健康数据字典
                {
                    'data_type': 'blood_pressure',
                    'value': 120,
                    'unit': 'mmHg',
                    'source': 'wearable',
                    'timestamp': '2024-01-01T12:00:00'
                }
        """
        try:
            data_point = HealthDataPoint(
                timestamp=datetime.fromisoformat(health_data['timestamp']),
                data_type=health_data['data_type'],
                value=health_data['value'],
                unit=health_data['unit'],
                source=health_data.get('source', 'manual')
            )
            
            self.sensor_collector.add_health_data(user_id, data_point)
            logger.info(f"Received health data from frontend for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error receiving health data from frontend: {e}")
    
    def batch_receive_sensor_data(self, user_id: str, sensor_data_list: List[Dict[str, Any]]):
        """
        批量接收传感器数据
        
        Args:
            user_id: 用户ID
            sensor_data_list: 传感器数据列表
        """
        for sensor_data in sensor_data_list:
            self.receive_sensor_data_from_frontend(user_id, sensor_data)
    
    def batch_receive_health_data(self, user_id: str, health_data_list: List[Dict[str, Any]]):
        """
        批量接收健康数据
        
        Args:
            user_id: 用户ID
            health_data_list: 健康数据列表
        """
        for health_data in health_data_list:
            self.receive_health_data_from_frontend(user_id, health_data)

