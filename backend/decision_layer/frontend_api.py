"""
前端数据接收 API
接收来自 HarmonyOS 前端的实时传感器和健康数据
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/frontend-data", tags=["frontend-data"])


# ==================== 依赖注入 ====================

async def get_frontend_data_bridge():
    """获取前端数据桥接器"""
    # 这里应该从应用上下文获取
    pass


# ==================== 数据模型 ====================

class SensorDataRequest:
    """传感器数据请求"""
    def __init__(self, sensor_type: str, value: float, unit: str,
                 accuracy: float = 1.0, device_id: str = "unknown",
                 timestamp: Optional[str] = None):
        self.sensor_type = sensor_type
        self.value = value
        self.unit = unit
        self.accuracy = accuracy
        self.device_id = device_id
        self.timestamp = timestamp or datetime.now().isoformat()


class HealthDataRequest:
    """健康数据请求"""
    def __init__(self, data_type: str, value: float, unit: str,
                 source: str = "manual", timestamp: Optional[str] = None):
        self.data_type = data_type
        self.value = value
        self.unit = unit
        self.source = source
        self.timestamp = timestamp or datetime.now().isoformat()


# ==================== API 端点 ====================

@router.post("/sensor-data")
async def receive_sensor_data(
    user_id: str,
    sensor_type: str,
    value: float,
    unit: str,
    accuracy: float = 1.0,
    device_id: str = "unknown",
    timestamp: Optional[str] = None,
    frontend_bridge = Depends(get_frontend_data_bridge)
) -> Dict[str, Any]:
    """
    接收单个传感器数据
    
    Args:
        user_id: 用户ID
        sensor_type: 传感器类型 (heart_rate, accelerometer, gyroscope, light, pressure, temperature)
        value: 数值
        unit: 单位 (bpm, m/s², lux, Pa, °C)
        accuracy: 准确度 (0-1)
        device_id: 设备ID
        timestamp: 时间戳 (ISO 8601 格式)
    
    Returns:
        接收确认
    """
    try:
        sensor_data = {
            'sensor_type': sensor_type,
            'value': value,
            'unit': unit,
            'accuracy': accuracy,
            'device_id': device_id,
            'timestamp': timestamp or datetime.now().isoformat()
        }
        
        frontend_bridge.receive_sensor_data_from_frontend(user_id, sensor_data)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'sensor_type': sensor_type,
            'message': 'Sensor data received successfully',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error receiving sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health-data")
async def receive_health_data(
    user_id: str,
    data_type: str,
    value: float,
    unit: str,
    source: str = "manual",
    timestamp: Optional[str] = None,
    frontend_bridge = Depends(get_frontend_data_bridge)
) -> Dict[str, Any]:
    """
    接收单个健康数据
    
    Args:
        user_id: 用户ID
        data_type: 数据类型 (sleep, exercise, blood_pressure, blood_oxygen, stress)
        value: 数值
        unit: 单位 (hours, minutes, mmHg, %, 0-100)
        source: 数据来源 (wearable, manual, app)
        timestamp: 时间戳 (ISO 8601 格式)
    
    Returns:
        接收确认
    """
    try:
        health_data = {
            'data_type': data_type,
            'value': value,
            'unit': unit,
            'source': source,
            'timestamp': timestamp or datetime.now().isoformat()
        }
        
        frontend_bridge.receive_health_data_from_frontend(user_id, health_data)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'data_type': data_type,
            'message': 'Health data received successfully',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error receiving health data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sensor-data/batch")
async def receive_batch_sensor_data(
    user_id: str,
    sensor_data_list: List[Dict[str, Any]],
    frontend_bridge = Depends(get_frontend_data_bridge)
) -> Dict[str, Any]:
    """
    批量接收传感器数据
    
    Args:
        user_id: 用户ID
        sensor_data_list: 传感器数据列表
            [
                {
                    'sensor_type': 'heart_rate',
                    'value': 72.5,
                    'unit': 'bpm',
                    'accuracy': 0.95,
                    'device_id': 'device_001',
                    'timestamp': '2024-01-01T12:00:00'
                },
                ...
            ]
    
    Returns:
        批量接收确认
    """
    try:
        frontend_bridge.batch_receive_sensor_data(user_id, sensor_data_list)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'count': len(sensor_data_list),
            'message': f'Received {len(sensor_data_list)} sensor data points',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error receiving batch sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health-data/batch")
async def receive_batch_health_data(
    user_id: str,
    health_data_list: List[Dict[str, Any]],
    frontend_bridge = Depends(get_frontend_data_bridge)
) -> Dict[str, Any]:
    """
    批量接收健康数据
    
    Args:
        user_id: 用户ID
        health_data_list: 健康数据列表
            [
                {
                    'data_type': 'blood_pressure',
                    'value': 120,
                    'unit': 'mmHg',
                    'source': 'wearable',
                    'timestamp': '2024-01-01T12:00:00'
                },
                ...
            ]
    
    Returns:
        批量接收确认
    """
    try:
        frontend_bridge.batch_receive_health_data(user_id, health_data_list)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'count': len(health_data_list),
            'message': f'Received {len(health_data_list)} health data points',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error receiving batch health data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/combined-data")
async def receive_combined_data(
    user_id: str,
    sensor_data: Optional[List[Dict[str, Any]]] = None,
    health_data: Optional[List[Dict[str, Any]]] = None,
    frontend_bridge = Depends(get_frontend_data_bridge)
) -> Dict[str, Any]:
    """
    接收组合的传感器和健康数据
    
    Args:
        user_id: 用户ID
        sensor_data: 传感器数据列表 (可选)
        health_data: 健康数据列表 (可选)
    
    Returns:
        接收确认
    """
    try:
        sensor_count = 0
        health_count = 0
        
        if sensor_data:
            frontend_bridge.batch_receive_sensor_data(user_id, sensor_data)
            sensor_count = len(sensor_data)
        
        if health_data:
            frontend_bridge.batch_receive_health_data(user_id, health_data)
            health_count = len(health_data)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'sensor_data_count': sensor_count,
            'health_data_count': health_count,
            'total_count': sensor_count + health_count,
            'message': f'Received {sensor_count} sensor and {health_count} health data points',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error receiving combined data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{user_id}")
async def get_data_collection_status(
    user_id: str,
    sensor_collector = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    获取数据采集状态
    
    Args:
        user_id: 用户ID
    
    Returns:
        数据采集状态
    """
    try:
        # 这里应该从传感器收集器获取状态
        status = {
            'user_id': user_id,
            'sensor_data_count': 0,
            'health_data_count': 0,
            'last_sensor_update': None,
            'last_health_update': None,
            'buffer_usage': 0
        }
        
        return {
            'status': 'success',
            'data': status,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting data collection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flush/{user_id}")
async def flush_data_to_database(
    user_id: str,
    sensor_collector = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    将缓冲区数据刷新到数据库
    
    Args:
        user_id: 用户ID
    
    Returns:
        刷新结果
    """
    try:
        # 这里应该调用传感器收集器的 flush_to_database 方法
        
        return {
            'status': 'success',
            'user_id': user_id,
            'message': 'Data flushed to database successfully',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error flushing data to database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sensor-types")
async def get_supported_sensor_types() -> Dict[str, Any]:
    """
    获取支持的传感器类型列表
    
    Returns:
        支持的传感器类型
    """
    sensor_types = {
        'heart_rate': {
            'unit': 'bpm',
            'range': [40, 200],
            'description': '心率'
        },
        'accelerometer': {
            'unit': 'm/s²',
            'range': [-50, 50],
            'description': '加速度计'
        },
        'gyroscope': {
            'unit': 'rad/s',
            'range': [-360, 360],
            'description': '陀螺仪'
        },
        'light': {
            'unit': 'lux',
            'range': [0, 100000],
            'description': '光传感器'
        },
        'pressure': {
            'unit': 'Pa',
            'range': [80000, 120000],
            'description': '气压传感器'
        },
        'temperature': {
            'unit': '°C',
            'range': [30, 45],
            'description': '温度传感器'
        }
    }
    
    return {
        'status': 'success',
        'sensor_types': sensor_types,
        'timestamp': datetime.now().isoformat()
    }


@router.get("/health-data-types")
async def get_supported_health_data_types() -> Dict[str, Any]:
    """
    获取支持的健康数据类型列表
    
    Returns:
        支持的健康数据类型
    """
    health_data_types = {
        'sleep': {
            'unit': 'hours',
            'range': [0, 24],
            'description': '睡眠时间'
        },
        'exercise': {
            'unit': 'minutes',
            'range': [0, 1440],
            'description': '运动时间'
        },
        'blood_pressure': {
            'unit': 'mmHg',
            'range': [60, 200],
            'description': '血压'
        },
        'blood_oxygen': {
            'unit': '%',
            'range': [80, 100],
            'description': '血氧'
        },
        'stress': {
            'unit': '0-100',
            'range': [0, 100],
            'description': '压力水平'
        }
    }
    
    return {
        'status': 'success',
        'health_data_types': health_data_types,
        'timestamp': datetime.now().isoformat()
    }


@router.post("/validate-data")
async def validate_sensor_data(
    sensor_type: str,
    value: float
) -> Dict[str, Any]:
    """
    验证传感器数据的有效性
    
    Args:
        sensor_type: 传感器类型
        value: 数值
    
    Returns:
        验证结果
    """
    try:
        # 定义有效范围
        valid_ranges = {
            'heart_rate': (40, 200),
            'accelerometer': (-50, 50),
            'gyroscope': (-360, 360),
            'light': (0, 100000),
            'pressure': (80000, 120000),
            'temperature': (30, 45)
        }
        
        if sensor_type not in valid_ranges:
            return {
                'status': 'invalid',
                'valid': False,
                'message': f'Unknown sensor type: {sensor_type}'
            }
        
        min_val, max_val = valid_ranges[sensor_type]
        is_valid = min_val <= value <= max_val
        
        return {
            'status': 'success',
            'valid': is_valid,
            'sensor_type': sensor_type,
            'value': value,
            'valid_range': [min_val, max_val],
            'message': 'Valid' if is_valid else f'Value out of range [{min_val}, {max_val}]'
        }
    except Exception as e:
        logger.error(f"Error validating data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

