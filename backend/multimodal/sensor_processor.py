"""
传感器数据处理模块
处理来自手机的传感器数据（步数、加速度、光线等）
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import math


class SensorProcessor:
    """
    传感器数据处理器
    分析传感器数据，推断用户活动状态
    """
    
    def __init__(self):
        # 活动阈值
        self.activity_thresholds = {
            'sedentary': 0.5,      # 静止
            'light': 2.0,          # 轻度活动
            'moderate': 5.0,       # 中度活动
            'vigorous': 10.0       # 剧烈活动
        }
        
        # 光线阈值（lux）
        self.light_thresholds = {
            'dark': 10,
            'dim': 100,
            'normal': 500,
            'bright': 1000,
            'very_bright': 10000
        }
    
    def process_sensor_data(
        self,
        sensor_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理传感器数据
        
        Args:
            sensor_data: 传感器数据字典
            context: 上下文信息
        
        Returns:
            处理结果
        """
        try:
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'raw_data': sensor_data
            }
            
            # 处理步数
            if 'steps' in sensor_data:
                result['steps_analysis'] = self._analyze_steps(sensor_data['steps'])
            
            # 处理加速度计
            if 'accelerometer' in sensor_data:
                result['motion_analysis'] = self._analyze_motion(sensor_data['accelerometer'])
            
            # 处理光线传感器
            if 'light_level' in sensor_data or 'lightLevel' in sensor_data:
                light = sensor_data.get('light_level') or sensor_data.get('lightLevel')
                result['light_analysis'] = self._analyze_light(light)
            
            # 综合活动状态
            result['activity_state'] = self._infer_activity_state(sensor_data, context)
            
            # 健康指标
            result['health_indicators'] = self._calculate_health_indicators(sensor_data)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'raw_data': sensor_data
            }
    
    def _analyze_steps(self, steps: int) -> Dict[str, Any]:
        """分析步数"""
        # 步数目标（WHO推荐10000步/天）
        target = 10000
        percentage = (steps / target) * 100
        
        # 活动等级
        if steps < 2000:
            level = 'sedentary'
            description = '活动量很少'
        elif steps < 5000:
            level = 'lightly_active'
            description = '轻度活动'
        elif steps < 10000:
            level = 'moderately_active'
            description = '中度活动'
        else:
            level = 'very_active'
            description = '活动量充足'
        
        # 估算消耗的卡路里（粗略估算：1步约0.04卡）
        calories = steps * 0.04
        
        # 估算距离（粗略估算：1步约0.7米）
        distance_km = (steps * 0.7) / 1000
        
        return {
            'steps': steps,
            'target': target,
            'percentage': round(percentage, 1),
            'level': level,
            'description': description,
            'estimated_calories': round(calories, 1),
            'estimated_distance_km': round(distance_km, 2)
        }
    
    def _analyze_motion(self, accelerometer: Dict[str, float]) -> Dict[str, Any]:
        """分析运动状态（基于加速度计）"""
        x = accelerometer.get('x', 0)
        y = accelerometer.get('y', 0)
        z = accelerometer.get('z', 0)
        
        # 计算加速度幅值
        magnitude = math.sqrt(x**2 + y**2 + z**2)
        
        # 判断活动强度
        if magnitude < self.activity_thresholds['sedentary']:
            intensity = 'sedentary'
            description = '静止或坐着'
        elif magnitude < self.activity_thresholds['light']:
            intensity = 'light'
            description = '轻度活动（如走路）'
        elif magnitude < self.activity_thresholds['moderate']:
            intensity = 'moderate'
            description = '中度活动（如快走）'
        else:
            intensity = 'vigorous'
            description = '剧烈活动（如跑步）'
        
        return {
            'magnitude': round(magnitude, 2),
            'intensity': intensity,
            'description': description,
            'x': round(x, 2),
            'y': round(y, 2),
            'z': round(z, 2)
        }
    
    def _analyze_light(self, light_level: float) -> Dict[str, Any]:
        """分析光线水平"""
        # 判断光线等级
        if light_level < self.light_thresholds['dark']:
            level = 'dark'
            description = '黑暗'
            environment = 'indoor_night'
        elif light_level < self.light_thresholds['dim']:
            level = 'dim'
            description = '昏暗'
            environment = 'indoor_dim'
        elif light_level < self.light_thresholds['normal']:
            level = 'normal'
            description = '正常室内光线'
            environment = 'indoor'
        elif light_level < self.light_thresholds['bright']:
            level = 'bright'
            description = '明亮'
            environment = 'indoor_bright'
        else:
            level = 'very_bright'
            description = '非常明亮（可能是户外）'
            environment = 'outdoor'
        
        return {
            'level': level,
            'value': round(light_level, 1),
            'description': description,
            'environment': environment
        }
    
    def _infer_activity_state(
        self,
        sensor_data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """推断综合活动状态"""
        state = {
            'primary_activity': 'unknown',
            'confidence': 0.5,
            'details': []
        }
        
        # 基于步数推断
        steps = sensor_data.get('steps', 0)
        if steps > 100:  # 最近有步数增加
            state['details'].append('最近在走动')
            state['primary_activity'] = 'walking'
            state['confidence'] = 0.7
        elif steps == 0:
            state['details'].append('静止状态')
            state['primary_activity'] = 'sedentary'
            state['confidence'] = 0.8
        
        # 基于加速度计推断
        if 'accelerometer' in sensor_data:
            acc = sensor_data['accelerometer']
            magnitude = math.sqrt(
                acc.get('x', 0)**2 + 
                acc.get('y', 0)**2 + 
                acc.get('z', 0)**2
            )
            
            if magnitude > 5.0:
                state['primary_activity'] = 'exercising'
                state['confidence'] = 0.8
                state['details'].append('检测到运动')
            elif magnitude > 2.0:
                state['primary_activity'] = 'walking'
                state['confidence'] = 0.7
                state['details'].append('检测到走动')
        
        # 基于光线推断环境
        light = sensor_data.get('light_level') or sensor_data.get('lightLevel', 0)
        if light > 10000:
            state['details'].append('可能在户外')
        elif light < 100:
            state['details'].append('可能在室内或夜晚')
        
        return state
    
    def _calculate_health_indicators(
        self,
        sensor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算健康指标"""
        indicators = {}
        
        # 活动量指标
        steps = sensor_data.get('steps', 0)
        if steps > 0:
            indicators['activity_score'] = min(steps / 10000, 1.0)  # 0-1分
            indicators['activity_level'] = 'good' if steps >= 8000 else 'moderate' if steps >= 5000 else 'low'
        
        # 运动强度指标
        if 'accelerometer' in sensor_data:
            acc = sensor_data['accelerometer']
            magnitude = math.sqrt(
                acc.get('x', 0)**2 + 
                acc.get('y', 0)**2 + 
                acc.get('z', 0)**2
            )
            indicators['exercise_intensity'] = 'high' if magnitude > 5 else 'moderate' if magnitude > 2 else 'low'
        
        return indicators


# 全局实例
_processor = None

def get_sensor_processor() -> SensorProcessor:
    """获取全局传感器处理器实例"""
    global _processor
    if _processor is None:
        _processor = SensorProcessor()
    return _processor
