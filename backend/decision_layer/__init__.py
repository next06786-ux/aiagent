"""
决策层系统初始化和配置
"""

import logging
from typing import Optional
from backend.decision_layer.decision_engine import DecisionEngine, DecisionExecutor
from backend.decision_layer.frontend_integration import (
    SensorDataCollector,
    RealTimeDataProcessor,
    FrontendDataBridge
)

logger = logging.getLogger(__name__)


class DecisionLayerConfig:
    """决策层配置"""
    
    def __init__(self):
        """初始化配置"""
        # 数据采集配置
        self.sensor_buffer_size = 1000
        self.aggregation_window = 60  # 秒
        
        # 决策配置
        self.max_decisions_per_analysis = 10
        self.decision_cache_size = 1000
        
        # 通知配置
        self.enable_notifications = True
        self.notification_priority_threshold = 2  # 只发送优先级 >= 2 的通知
        
        # 数据库配置
        self.auto_flush_interval = 300  # 秒
        self.batch_size = 100


class DecisionLayerSystem:
    """决策层系统"""
    
    def __init__(self, data_service, knowledge_graph, rl_agent, notification_service):
        """
        初始化决策层系统
        
        Args:
            data_service: 数据服务
            knowledge_graph: 知识图谱
            rl_agent: 强化学习代理
            notification_service: 通知服务
        """
        self.config = DecisionLayerConfig()
        self.data_service = data_service
        self.knowledge_graph = knowledge_graph
        self.rl_agent = rl_agent
        self.notification_service = notification_service
        
        # 初始化各个组件
        self.decision_engine: Optional[DecisionEngine] = None
        self.decision_executor: Optional[DecisionExecutor] = None
        self.sensor_collector: Optional[SensorDataCollector] = None
        self.real_time_processor: Optional[RealTimeDataProcessor] = None
        self.frontend_bridge: Optional[FrontendDataBridge] = None
        
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        初始化决策层系统
        
        Returns:
            是否初始化成功
        """
        try:
            logger.info("Initializing Decision Layer System...")
            
            # 1. 初始化决策引擎
            self.decision_engine = DecisionEngine(
                self.data_service,
                self.knowledge_graph,
                self.rl_agent
            )
            logger.info("✓ Decision Engine initialized")
            
            # 2. 初始化决策执行器
            self.decision_executor = DecisionExecutor(
                self.notification_service,
                self.data_service
            )
            logger.info("✓ Decision Executor initialized")
            
            # 3. 初始化传感器数据收集器
            self.sensor_collector = SensorDataCollector(
                self.data_service,
                buffer_size=self.config.sensor_buffer_size
            )
            logger.info("✓ Sensor Data Collector initialized")
            
            # 4. 初始化实时数据处理器
            self.real_time_processor = RealTimeDataProcessor(
                self.decision_engine,
                self.sensor_collector
            )
            self.real_time_processor.aggregation_window = self.config.aggregation_window
            logger.info("✓ Real-time Data Processor initialized")
            
            # 5. 注册数据处理回调
            self.sensor_collector.register_callback(
                self.real_time_processor.process_sensor_data
            )
            logger.info("✓ Data processing callbacks registered")
            
            # 6. 初始化前端数据桥接器
            self.frontend_bridge = FrontendDataBridge(
                self.sensor_collector,
                self.real_time_processor
            )
            logger.info("✓ Frontend Data Bridge initialized")
            
            self._initialized = True
            logger.info("✓ Decision Layer System initialized successfully")
            
            return True
        
        except Exception as e:
            logger.error(f"Error initializing Decision Layer System: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    def get_decision_engine(self) -> Optional[DecisionEngine]:
        """获取决策引擎"""
        if not self._initialized:
            logger.warning("Decision Layer System not initialized")
            return None
        return self.decision_engine
    
    def get_decision_executor(self) -> Optional[DecisionExecutor]:
        """获取决策执行器"""
        if not self._initialized:
            logger.warning("Decision Layer System not initialized")
            return None
        return self.decision_executor
    
    def get_frontend_bridge(self) -> Optional[FrontendDataBridge]:
        """获取前端数据桥接器"""
        if not self._initialized:
            logger.warning("Decision Layer System not initialized")
            return None
        return self.frontend_bridge
    
    def get_sensor_collector(self) -> Optional[SensorDataCollector]:
        """获取传感器数据收集器"""
        if not self._initialized:
            logger.warning("Decision Layer System not initialized")
            return None
        return self.sensor_collector
    
    def shutdown(self):
        """关闭决策层系统"""
        try:
            logger.info("Shutting down Decision Layer System...")
            
            # 刷新所有缓冲区数据
            if self.sensor_collector:
                logger.info("Flushing sensor data buffers...")
                # 这里应该遍历所有用户并刷新数据
            
            self._initialized = False
            logger.info("✓ Decision Layer System shut down successfully")
        
        except Exception as e:
            logger.error(f"Error shutting down Decision Layer System: {e}")


class DecisionLayerFactory:
    """决策层工厂"""
    
    _instance: Optional[DecisionLayerSystem] = None
    
    @classmethod
    def create(cls, data_service, knowledge_graph, rl_agent, notification_service) -> DecisionLayerSystem:
        """
        创建决策层系统实例
        
        Args:
            data_service: 数据服务
            knowledge_graph: 知识图谱
            rl_agent: 强化学习代理
            notification_service: 通知服务
        
        Returns:
            决策层系统实例
        """
        if cls._instance is None:
            cls._instance = DecisionLayerSystem(
                data_service,
                knowledge_graph,
                rl_agent,
                notification_service
            )
        
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> Optional[DecisionLayerSystem]:
        """获取决策层系统实例"""
        return cls._instance
    
    @classmethod
    def reset(cls):
        """重置工厂"""
        if cls._instance:
            cls._instance.shutdown()
        cls._instance = None


# 全局决策层系统实例
_decision_layer_system: Optional[DecisionLayerSystem] = None


def initialize_decision_layer(data_service, knowledge_graph, rl_agent, notification_service) -> bool:
    """
    初始化全局决策层系统
    
    Args:
        data_service: 数据服务
        knowledge_graph: 知识图谱
        rl_agent: 强化学习代理
        notification_service: 通知服务
    
    Returns:
        是否初始化成功
    """
    global _decision_layer_system
    
    _decision_layer_system = DecisionLayerFactory.create(
        data_service,
        knowledge_graph,
        rl_agent,
        notification_service
    )
    
    return _decision_layer_system.initialize()


def get_decision_layer_system() -> Optional[DecisionLayerSystem]:
    """获取全局决策层系统"""
    return _decision_layer_system


def shutdown_decision_layer():
    """关闭全局决策层系统"""
    global _decision_layer_system
    
    if _decision_layer_system:
        _decision_layer_system.shutdown()
        _decision_layer_system = None

