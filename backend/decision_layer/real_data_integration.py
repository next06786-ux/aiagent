"""
决策层与真实数据集成
将真实的HarmonyOS前端数据、MySQL、Redis、Neo4j集成到决策系统
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class RealDataDecisionBridge:
    """真实数据决策桥接器"""
    
    def __init__(self, mysql_service, redis_service, neo4j_service, decision_engine):
        """
        初始化真实数据决策桥接器
        
        Args:
            mysql_service: MySQL服务
            redis_service: Redis服务
            neo4j_service: Neo4j服务
            decision_engine: 决策引擎
        """
        self.mysql_service = mysql_service
        self.redis_service = redis_service
        self.neo4j_service = neo4j_service
        self.decision_engine = decision_engine
    
    def process_harmonyos_sensor_data(self, user_id: str, sensor_data: Dict[str, Any]) -> List[Any]:
        """
        处理HarmonyOS前端传感器数据并生成决策
        
        Args:
            user_id: 用户ID
            sensor_data: 传感器数据
                {
                    'heart_rate': 72,
                    'steps': 1250,
                    'accelerometer': {'x': 0.1, 'y': 0.2, 'z': 9.8},
                    'gyroscope': {'x': 0.01, 'y': 0.02, 'z': 0.03},
                    'light': 500,
                    'pressure': 1013,
                    'temperature': 36.8,
                    'blood_oxygen': 97,
                    'timestamp': '2026-03-15T10:30:00'
                }
        
        Returns:
            生成的决策列表
        """
        try:
            # 1. 保存到MySQL
            self._save_to_mysql(user_id, sensor_data)
            
            # 2. 缓存到Redis
            self._cache_to_redis(user_id, sensor_data)
            
            # 3. 更新Neo4j知识图谱
            self._update_neo4j(user_id, sensor_data)
            
            # 4. 生成决策
            decisions = self._generate_decisions_from_real_data(user_id, sensor_data)
            
            logger.info(f"Processed HarmonyOS sensor data for user {user_id}: {len(decisions)} decisions generated")
            
            return decisions
        
        except Exception as e:
            logger.error(f"Error processing HarmonyOS sensor data: {e}")
            return []
    
    def _save_to_mysql(self, user_id: str, sensor_data: Dict[str, Any]):
        """保存传感器数据到MySQL"""
        try:
            record = {
                'user_id': user_id,
                'timestamp': sensor_data.get('timestamp', datetime.now().isoformat()),
                'heart_rate': sensor_data.get('heart_rate'),
                'steps': sensor_data.get('steps'),
                'accelerometer_x': sensor_data.get('accelerometer', {}).get('x'),
                'accelerometer_y': sensor_data.get('accelerometer', {}).get('y'),
                'accelerometer_z': sensor_data.get('accelerometer', {}).get('z'),
                'gyroscope_x': sensor_data.get('gyroscope', {}).get('x'),
                'gyroscope_y': sensor_data.get('gyroscope', {}).get('y'),
                'gyroscope_z': sensor_data.get('gyroscope', {}).get('z'),
                'light': sensor_data.get('light'),
                'pressure': sensor_data.get('pressure'),
                'temperature': sensor_data.get('temperature'),
                'blood_oxygen': sensor_data.get('blood_oxygen')
            }
            
            self.mysql_service.insert_sensor_data(record)
            logger.debug(f"Saved sensor data to MySQL for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error saving to MySQL: {e}")
    
    def _cache_to_redis(self, user_id: str, sensor_data: Dict[str, Any]):
        """缓存传感器数据到Redis"""
        try:
            # 缓存最新传感器数据
            cache_key = f"user:{user_id}:latest_sensor_data"
            self.redis_service.set(cache_key, json.dumps(sensor_data), ex=3600)
            
            # 缓存最新心率
            if 'heart_rate' in sensor_data:
                hr_key = f"user:{user_id}:latest_heart_rate"
                self.redis_service.set(hr_key, sensor_data['heart_rate'], ex=300)
            
            # 缓存最新步数
            if 'steps' in sensor_data:
                steps_key = f"user:{user_id}:latest_steps"
                self.redis_service.set(steps_key, sensor_data['steps'], ex=300)
            
            logger.debug(f"Cached sensor data to Redis for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error caching to Redis: {e}")
    
    def _update_neo4j(self, user_id: str, sensor_data: Dict[str, Any]):
        """更新Neo4j知识图谱"""
        try:
            # 创建或更新用户节点
            self.neo4j_service.merge_user_node(user_id)
            
            # 创建传感器读数节点
            reading_id = f"reading_{user_id}_{datetime.now().timestamp()}"
            self.neo4j_service.create_sensor_reading_node(
                reading_id,
                user_id,
                sensor_data
            )
            
            # 创建关系
            self.neo4j_service.create_relationship(
                user_id,
                "HAS_SENSOR_READING",
                reading_id
            )
            
            logger.debug(f"Updated Neo4j knowledge graph for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error updating Neo4j: {e}")
    
    def _generate_decisions_from_real_data(self, user_id: str, sensor_data: Dict[str, Any]) -> List[Any]:
        """基于真实数据生成决策"""
        try:
            from backend.decision_layer.decision_engine import HealthMetrics
            
            # 构建健康指标
            metrics = HealthMetrics(
                heart_rate=sensor_data.get('heart_rate', 0),
                blood_oxygen=sensor_data.get('blood_oxygen', 0),
                temperature=sensor_data.get('temperature', 0),
                blood_pressure_systolic=sensor_data.get('blood_pressure_systolic', 0),
                blood_pressure_diastolic=sensor_data.get('blood_pressure_diastolic', 0),
                sleep_hours=sensor_data.get('sleep_hours', 0),
                exercise_minutes=sensor_data.get('exercise_minutes', 0),
                stress_level=sensor_data.get('stress_level', 0)
            )
            
            # 分析健康指标
            decisions = self.decision_engine.analyze_health_metrics(user_id, metrics)
            
            return decisions
        
        except Exception as e:
            logger.error(f"Error generating decisions: {e}")
            return []
    
    def get_user_health_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        获取用户健康摘要
        
        Args:
            user_id: 用户ID
            days: 天数
        
        Returns:
            健康摘要
        """
        try:
            # 从MySQL查询历史数据
            start_date = datetime.now() - timedelta(days=days)
            sensor_records = self.mysql_service.query_sensor_data(
                user_id,
                start_date=start_date
            )
            
            if not sensor_records:
                return {}
            
            # 计算统计数据
            heart_rates = [r['heart_rate'] for r in sensor_records if r.get('heart_rate')]
            temperatures = [r['temperature'] for r in sensor_records if r.get('temperature')]
            blood_oxygens = [r['blood_oxygen'] for r in sensor_records if r.get('blood_oxygen')]
            
            summary = {
                'user_id': user_id,
                'period_days': days,
                'data_points': len(sensor_records),
                'heart_rate': {
                    'avg': sum(heart_rates) / len(heart_rates) if heart_rates else 0,
                    'min': min(heart_rates) if heart_rates else 0,
                    'max': max(heart_rates) if heart_rates else 0
                },
                'temperature': {
                    'avg': sum(temperatures) / len(temperatures) if temperatures else 0,
                    'min': min(temperatures) if temperatures else 0,
                    'max': max(temperatures) if temperatures else 0
                },
                'blood_oxygen': {
                    'avg': sum(blood_oxygens) / len(blood_oxygens) if blood_oxygens else 0,
                    'min': min(blood_oxygens) if blood_oxygens else 0,
                    'max': max(blood_oxygens) if blood_oxygens else 0
                }
            }
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting health summary: {e}")
            return {}
    
    def get_cached_latest_data(self, user_id: str) -> Dict[str, Any]:
        """
        从Redis获取最新缓存数据
        
        Args:
            user_id: 用户ID
        
        Returns:
            最新数据
        """
        try:
            cache_key = f"user:{user_id}:latest_sensor_data"
            cached_data = self.redis_service.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            return {}
        
        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return {}
    
    def query_knowledge_graph(self, user_id: str, query_type: str = "health_status") -> List[Dict[str, Any]]:
        """
        查询知识图谱
        
        Args:
            user_id: 用户ID
            query_type: 查询类型
        
        Returns:
            查询结果
        """
        try:
            if query_type == "health_status":
                # 查询用户的健康状态
                return self.neo4j_service.query_user_health_status(user_id)
            
            elif query_type == "sensor_readings":
                # 查询用户的传感器读数
                return self.neo4j_service.query_user_sensor_readings(user_id)
            
            elif query_type == "relationships":
                # 查询用户的关系
                return self.neo4j_service.query_user_relationships(user_id)
            
            else:
                logger.warning(f"Unknown query type: {query_type}")
                return []
        
        except Exception as e:
            logger.error(f"Error querying knowledge graph: {e}")
            return []


class RealDataAnalytics:
    """真实数据分析"""
    
    def __init__(self, mysql_service, redis_service):
        """
        初始化真实数据分析
        
        Args:
            mysql_service: MySQL服务
            redis_service: Redis服务
        """
        self.mysql_service = mysql_service
        self.redis_service = redis_service
    
    def calculate_daily_statistics(self, user_id: str, date: str) -> Dict[str, Any]:
        """
        计算每日统计
        
        Args:
            user_id: 用户ID
            date: 日期 (YYYY-MM-DD)
        
        Returns:
            每日统计
        """
        try:
            # 查询该日期的所有数据
            records = self.mysql_service.query_sensor_data_by_date(user_id, date)
            
            if not records:
                return {}
            
            # 计算统计数据
            heart_rates = [r['heart_rate'] for r in records if r.get('heart_rate')]
            steps_list = [r['steps'] for r in records if r.get('steps')]
            temperatures = [r['temperature'] for r in records if r.get('temperature')]
            blood_oxygens = [r['blood_oxygen'] for r in records if r.get('blood_oxygen')]
            
            stats = {
                'user_id': user_id,
                'date': date,
                'data_points': len(records),
                'heart_rate_avg': sum(heart_rates) / len(heart_rates) if heart_rates else 0,
                'heart_rate_min': min(heart_rates) if heart_rates else 0,
                'heart_rate_max': max(heart_rates) if heart_rates else 0,
                'steps_total': sum(steps_list) if steps_list else 0,
                'temperature_avg': sum(temperatures) / len(temperatures) if temperatures else 0,
                'blood_oxygen_avg': sum(blood_oxygens) / len(blood_oxygens) if blood_oxygens else 0
            }
            
            # 缓存到Redis
            cache_key = f"user:{user_id}:daily_stats:{date}"
            self.redis_service.set(cache_key, json.dumps(stats), ex=86400)
            
            return stats
        
        except Exception as e:
            logger.error(f"Error calculating daily statistics: {e}")
            return {}
    
    def detect_anomalies(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        检测异常数据
        
        Args:
            user_id: 用户ID
            days: 天数
        
        Returns:
            异常列表
        """
        try:
            # 查询历史数据
            start_date = datetime.now() - timedelta(days=days)
            records = self.mysql_service.query_sensor_data(
                user_id,
                start_date=start_date
            )
            
            if not records:
                return []
            
            # 计算平均值和标准差
            heart_rates = [r['heart_rate'] for r in records if r.get('heart_rate')]
            
            if not heart_rates:
                return []
            
            avg_hr = sum(heart_rates) / len(heart_rates)
            variance = sum((x - avg_hr) ** 2 for x in heart_rates) / len(heart_rates)
            std_dev = variance ** 0.5
            
            # 检测异常 (超过2个标准差)
            anomalies = []
            for record in records:
                if record.get('heart_rate'):
                    if abs(record['heart_rate'] - avg_hr) > 2 * std_dev:
                        anomalies.append({
                            'timestamp': record['timestamp'],
                            'heart_rate': record['heart_rate'],
                            'deviation': abs(record['heart_rate'] - avg_hr) / std_dev
                        })
            
            return anomalies
        
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def get_trend_analysis(self, user_id: str, metric: str, days: int = 30) -> Dict[str, Any]:
        """
        获取趋势分析
        
        Args:
            user_id: 用户ID
            metric: 指标 (heart_rate, temperature, blood_oxygen, steps)
            days: 天数
        
        Returns:
            趋势分析
        """
        try:
            # 查询历史数据
            start_date = datetime.now() - timedelta(days=days)
            records = self.mysql_service.query_sensor_data(
                user_id,
                start_date=start_date
            )
            
            if not records:
                return {}
            
            # 提取指标值
            values = [r[metric] for r in records if r.get(metric)]
            
            if not values:
                return {}
            
            # 计算趋势
            trend = {
                'metric': metric,
                'period_days': days,
                'data_points': len(values),
                'current_value': values[-1] if values else 0,
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'trend': 'increasing' if values[-1] > values[0] else 'decreasing'
            }
            
            return trend
        
        except Exception as e:
            logger.error(f"Error getting trend analysis: {e}")
            return {}


class RealDataNotificationService:
    """真实数据通知服务"""
    
    def __init__(self, notification_service):
        """
        初始化真实数据通知服务
        
        Args:
            notification_service: 通知服务
        """
        self.notification_service = notification_service
    
    def send_health_alert(self, user_id: str, alert_type: str, message: str, severity: str = "high"):
        """
        发送健康警报
        
        Args:
            user_id: 用户ID
            alert_type: 警报类型
            message: 消息
            severity: 严重程度
        """
        try:
            title = f"[{severity.upper()}] 健康警报"
            
            self.notification_service.send_notification(
                user_id=user_id,
                title=title,
                body=message,
                priority=5 if severity == "critical" else 4 if severity == "high" else 3,
                data={
                    'alert_type': alert_type,
                    'severity': severity,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Sent health alert to user {user_id}: {alert_type}")
        
        except Exception as e:
            logger.error(f"Error sending health alert: {e}")
    
    def send_daily_summary(self, user_id: str, summary: Dict[str, Any]):
        """
        发送每日摘要
        
        Args:
            user_id: 用户ID
            summary: 摘要数据
        """
        try:
            message = f"""
            每日健康摘要:
            - 平均心率: {summary.get('heart_rate_avg', 0):.0f} bpm
            - 步数: {summary.get('steps_total', 0)} 步
            - 平均体温: {summary.get('temperature_avg', 0):.1f}°C
            - 平均血氧: {summary.get('blood_oxygen_avg', 0):.1f}%
            """
            
            self.notification_service.send_notification(
                user_id=user_id,
                title="📊 每日健康摘要",
                body=message,
                priority=2,
                data={
                    'type': 'daily_summary',
                    'summary': summary
                }
            )
            
            logger.info(f"Sent daily summary to user {user_id}")
        
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")

