"""
真实数据采集与集成层
将HarmonyOS前端传感器、MySQL、Neo4j、Redis真实集成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging
from dataclasses import dataclass, asdict

# 数据库和缓存导入
from backend.database.db_manager import DatabaseManager
from backend.database.cache_manager import CacheManager
from backend.knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph
from backend.data_collection.enhanced_sensor_collector import EnhancedSensorCollector

logger = logging.getLogger(__name__)


@dataclass
class RealSensorData:
    """真实传感器数据"""
    user_id: str
    timestamp: datetime
    heart_rate: Optional[float] = None
    steps: Optional[int] = None
    accelerometer_x: Optional[float] = None
    accelerometer_y: Optional[float] = None
    accelerometer_z: Optional[float] = None
    gyroscope_x: Optional[float] = None
    gyroscope_y: Optional[float] = None
    gyroscope_z: Optional[float] = None
    light: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    blood_oxygen: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class RealDataIntegrationLayer:
    """真实数据集成层 - 连接前端、数据库、缓存、知识图谱"""
    
    def __init__(self, user_id: str):
        """
        初始化集成层
        
        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        
        # 初始化各个组件
        self.db_manager = DatabaseManager()
        self.cache_manager = CacheManager()
        self.kg = Neo4jKnowledgeGraph()
        self.sensor_collector = EnhancedSensorCollector(user_id)
        
        # 缓存键前缀
        self.cache_prefix = f"user:{user_id}:"
        
        logger.info(f"Real Data Integration Layer initialized for user {user_id}")
    
    # ==================== 前端传感器数据接收 ====================
    
    def receive_harmonyos_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        接收来自HarmonyOS前端的真实传感器数据
        
        Args:
            sensor_data: 前端发送的传感器数据
            {
                "heart_rate": 72,
                "steps": 1250,
                "accelerometer": {"x": 0.1, "y": 0.2, "z": 9.8},
                "gyroscope": {"x": 0.01, "y": 0.02, "z": 0.03},
                "light": 500,
                "pressure": 1013,
                "temperature": 36.8,
                "blood_oxygen": 97,
                "timestamp": "2026-03-15T10:30:00"
            }
        
        Returns:
            处理结果
        """
        try:
            timestamp = datetime.fromisoformat(sensor_data.get("timestamp", datetime.now().isoformat()))
            
            # 创建真实传感器数据对象
            real_data = RealSensorData(
                user_id=self.user_id,
                timestamp=timestamp,
                heart_rate=sensor_data.get("heart_rate"),
                steps=sensor_data.get("steps"),
                accelerometer_x=sensor_data.get("accelerometer", {}).get("x"),
                accelerometer_y=sensor_data.get("accelerometer", {}).get("y"),
                accelerometer_z=sensor_data.get("accelerometer", {}).get("z"),
                gyroscope_x=sensor_data.get("gyroscope", {}).get("x"),
                gyroscope_y=sensor_data.get("gyroscope", {}).get("y"),
                gyroscope_z=sensor_data.get("gyroscope", {}).get("z"),
                light=sensor_data.get("light"),
                pressure=sensor_data.get("pressure"),
                temperature=sensor_data.get("temperature"),
                blood_oxygen=sensor_data.get("blood_oxygen")
            )
            
            # 1. 存储到MySQL
            self._store_to_mysql(real_data)
            
            # 2. 缓存到Redis
            self._cache_to_redis(real_data)
            
            # 3. 更新知识图谱
            self._update_knowledge_graph(real_data)
            
            logger.info(f"Successfully received and processed sensor data for user {self.user_id}")
            
            return {
                "status": "success",
                "message": "Sensor data received and processed",
                "data": real_data.to_dict(),
                "stored_in": ["mysql", "redis", "neo4j"]
            }
        
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
    
    # ==================== MySQL存储 ====================
    
    def _store_to_mysql(self, real_data: RealSensorData) -> bool:
        """
        存储真实传感器数据到MySQL
        
        Args:
            real_data: 真实传感器数据
        
        Returns:
            是否成功
        """
        try:
            # 使用SQLAlchemy ORM存储
            from backend.database.models import SensorData as SensorDataModel
            
            sensor_record = SensorDataModel(
                user_id=real_data.user_id,
                timestamp=real_data.timestamp,
                heart_rate=real_data.heart_rate,
                steps=real_data.steps,
                accelerometer_x=real_data.accelerometer_x,
                accelerometer_y=real_data.accelerometer_y,
                accelerometer_z=real_data.accelerometer_z,
                gyroscope_x=real_data.gyroscope_x,
                gyroscope_y=real_data.gyroscope_y,
                gyroscope_z=real_data.gyroscope_z,
                light=real_data.light,
                pressure=real_data.pressure,
                temperature=real_data.temperature,
                blood_oxygen=real_data.blood_oxygen
            )
            
            self.db_manager.add(sensor_record)
            self.db_manager.commit()
            
            logger.info(f"Sensor data stored to MySQL for user {self.user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing to MySQL: {e}")
            self.db_manager.rollback()
            return False
    
    # ==================== Redis缓存 ====================
    
    def _cache_to_redis(self, real_data: RealSensorData) -> bool:
        """
        缓存真实传感器数据到Redis
        
        Args:
            real_data: 真实传感器数据
        
        Returns:
            是否成功
        """
        try:
            # 缓存最新的传感器数据
            cache_key = f"{self.cache_prefix}latest_sensor_data"
            cache_value = json.dumps(real_data.to_dict(), default=str)
            
            # 设置缓存，TTL为1小时
            self.cache_manager.set(cache_key, cache_value, ttl=3600)
            
            # 缓存按类型的最新数据
            if real_data.heart_rate is not None:
                self.cache_manager.set(
                    f"{self.cache_prefix}latest_heart_rate",
                    str(real_data.heart_rate),
                    ttl=300  # 5分钟
                )
            
            if real_data.steps is not None:
                self.cache_manager.set(
                    f"{self.cache_prefix}latest_steps",
                    str(real_data.steps),
                    ttl=300
                )
            
            logger.info(f"Sensor data cached to Redis for user {self.user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error caching to Redis: {e}")
            return False
    
    # ==================== Neo4j知识图谱更新 ====================
    
    def _update_knowledge_graph(self, real_data: RealSensorData) -> bool:
        """
        更新Neo4j知识图谱
        
        Args:
            real_data: 真实传感器数据
        
        Returns:
            是否成功
        """
        try:
            # 创建或更新用户节点
            user_node = {
                "id": self.user_id,
                "type": "User",
                "properties": {
                    "last_updated": real_data.timestamp.isoformat()
                }
            }
            
            self.kg.create_or_update_node(user_node)
            
            # 创建传感器数据节点
            sensor_node = {
                "id": f"sensor_{real_data.timestamp.timestamp()}",
                "type": "SensorReading",
                "properties": real_data.to_dict()
            }
            
            self.kg.create_or_update_node(sensor_node)
            
            # 创建关系：User -> SensorReading
            self.kg.create_relationship(
                source_id=self.user_id,
                target_id=sensor_node["id"],
                relationship_type="HAS_SENSOR_READING",
                properties={"timestamp": real_data.timestamp.isoformat()}
            )
            
            # 如果有心率数据，创建心率节点和关系
            if real_data.heart_rate is not None:
                heart_rate_node = {
                    "id": f"heart_rate_{real_data.timestamp.timestamp()}",
                    "type": "HeartRate",
                    "properties": {
                        "value": real_data.heart_rate,
                        "timestamp": real_data.timestamp.isoformat()
                    }
                }
                
                self.kg.create_or_update_node(heart_rate_node)
                self.kg.create_relationship(
                    source_id=sensor_node["id"],
                    target_id=heart_rate_node["id"],
                    relationship_type="HAS_HEART_RATE"
                )
            
            # 如果有步数数据，创建步数节点和关系
            if real_data.steps is not None:
                steps_node = {
                    "id": f"steps_{real_data.timestamp.timestamp()}",
                    "type": "Steps",
                    "properties": {
                        "value": real_data.steps,
                        "timestamp": real_data.timestamp.isoformat()
                    }
                }
                
                self.kg.create_or_update_node(steps_node)
                self.kg.create_relationship(
                    source_id=sensor_node["id"],
                    target_id=steps_node["id"],
                    relationship_type="HAS_STEPS"
                )
            
            logger.info(f"Knowledge graph updated for user {self.user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {e}")
            return False
    
    # ==================== 数据查询 ====================
    
    def get_latest_sensor_data(self) -> Optional[Dict[str, Any]]:
        """
        获取最新的传感器数据（从Redis缓存）
        
        Returns:
            最新的传感器数据
        """
        try:
            cache_key = f"{self.cache_prefix}latest_sensor_data"
            cached_data = self.cache_manager.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            # 如果缓存中没有，从MySQL查询
            return self._get_latest_from_mysql()
        
        except Exception as e:
            logger.error(f"Error getting latest sensor data: {e}")
            return None
    
    def _get_latest_from_mysql(self) -> Optional[Dict[str, Any]]:
        """
        从MySQL获取最新的传感器数据
        
        Returns:
            最新的传感器数据
        """
        try:
            from backend.database.models import SensorData as SensorDataModel
            
            latest = self.db_manager.query(SensorDataModel)\
                .filter(SensorDataModel.user_id == self.user_id)\
                .order_by(SensorDataModel.timestamp.desc())\
                .first()
            
            if latest:
                return {
                    "user_id": latest.user_id,
                    "timestamp": latest.timestamp.isoformat(),
                    "heart_rate": latest.heart_rate,
                    "steps": latest.steps,
                    "temperature": latest.temperature,
                    "blood_oxygen": latest.blood_oxygen
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error querying MySQL: {e}")
            return None
    
    def get_sensor_data_range(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        获取时间范围内的传感器数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            传感器数据列表
        """
        try:
            from backend.database.models import SensorData as SensorDataModel
            
            records = self.db_manager.query(SensorDataModel)\
                .filter(SensorDataModel.user_id == self.user_id)\
                .filter(SensorDataModel.timestamp >= start_time)\
                .filter(SensorDataModel.timestamp <= end_time)\
                .order_by(SensorDataModel.timestamp.desc())\
                .all()
            
            return [
                {
                    "user_id": r.user_id,
                    "timestamp": r.timestamp.isoformat(),
                    "heart_rate": r.heart_rate,
                    "steps": r.steps,
                    "temperature": r.temperature,
                    "blood_oxygen": r.blood_oxygen
                }
                for r in records
            ]
        
        except Exception as e:
            logger.error(f"Error querying sensor data range: {e}")
            return []
    
    def get_daily_statistics(self, date: datetime) -> Dict[str, Any]:
        """
        获取每日统计
        
        Args:
            date: 日期
        
        Returns:
            每日统计
        """
        try:
            start_time = datetime(date.year, date.month, date.day, 0, 0, 0)
            end_time = datetime(date.year, date.month, date.day, 23, 59, 59)
            
            records = self.get_sensor_data_range(start_time, end_time)
            
            if not records:
                return {
                    "date": date.isoformat(),
                    "user_id": self.user_id,
                    "data_points": 0,
                    "statistics": {}
                }
            
            # 计算统计
            heart_rates = [r["heart_rate"] for r in records if r["heart_rate"] is not None]
            steps_list = [r["steps"] for r in records if r["steps"] is not None]
            temperatures = [r["temperature"] for r in records if r["temperature"] is not None]
            blood_oxygens = [r["blood_oxygen"] for r in records if r["blood_oxygen"] is not None]
            
            statistics = {}
            
            if heart_rates:
                statistics["heart_rate"] = {
                    "avg": sum(heart_rates) / len(heart_rates),
                    "min": min(heart_rates),
                    "max": max(heart_rates),
                    "count": len(heart_rates)
                }
            
            if steps_list:
                statistics["steps"] = {
                    "total": sum(steps_list),
                    "avg": sum(steps_list) / len(steps_list),
                    "count": len(steps_list)
                }
            
            if temperatures:
                statistics["temperature"] = {
                    "avg": sum(temperatures) / len(temperatures),
                    "min": min(temperatures),
                    "max": max(temperatures)
                }
            
            if blood_oxygens:
                statistics["blood_oxygen"] = {
                    "avg": sum(blood_oxygens) / len(blood_oxygens),
                    "min": min(blood_oxygens),
                    "max": max(blood_oxygens)
                }
            
            return {
                "date": date.isoformat(),
                "user_id": self.user_id,
                "data_points": len(records),
                "statistics": statistics
            }
        
        except Exception as e:
            logger.error(f"Error calculating daily statistics: {e}")
            return {}
    
    # ==================== 性能优化 ====================
    
    def clear_cache(self) -> bool:
        """
        清除用户的缓存
        
        Returns:
            是否成功
        """
        try:
            # 清除所有该用户的缓存
            pattern = f"{self.cache_prefix}*"
            self.cache_manager.delete_pattern(pattern)
            
            logger.info(f"Cache cleared for user {self.user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计
        
        Returns:
            缓存统计
        """
        try:
            return self.cache_manager.get_stats()
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}


def get_real_data_integration_layer(user_id: str) -> RealDataIntegrationLayer:
    """获取真实数据集成层实例"""
    return RealDataIntegrationLayer(user_id)

