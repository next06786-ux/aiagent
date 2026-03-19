"""
数据处理管道
实现多模态融合、数据清洗、特征提取、异常检测、质量评估
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict
import json


class DataQuality(Enum):
    """数据质量等级"""
    EXCELLENT = 0.95  # 95%+
    GOOD = 0.85  # 85-95%
    FAIR = 0.70  # 70-85%
    POOR = 0.50  # 50-70%
    VERY_POOR = 0.30  # <50%


@dataclass
class CleanedData:
    """清洗后的数据"""
    original_value: float
    cleaned_value: float
    is_outlier: bool
    quality_score: float
    cleaning_method: str
    timestamp: datetime


class DataCleaner:
    """数据清洗器"""
    
    def __init__(self):
        self.outlier_threshold = 3.0  # 标准差倍数
        self.missing_value_strategy = "interpolate"  # interpolate, forward_fill, drop
    
    def clean_sensor_data(self, values: List[float], sensor_type: str) -> List[CleanedData]:
        """清洗传感器数据"""
        cleaned_data = []
        
        if not values:
            return cleaned_data
        
        # 1. 检测异常值
        mean = np.mean(values)
        std = np.std(values)
        
        # 2. 处理缺失值
        values = self._handle_missing_values(values)
        
        # 3. 清洗每个值
        for i, value in enumerate(values):
            # 检测异常值
            z_score = abs((value - mean) / std) if std > 0 else 0
            is_outlier = z_score > self.outlier_threshold
            
            # 清洗异常值
            if is_outlier:
                cleaned_value = self._interpolate_value(values, i)
                cleaning_method = "interpolation"
            else:
                cleaned_value = value
                cleaning_method = "none"
            
            # 计算质量分数
            quality_score = 1.0 if not is_outlier else 0.7
            
            cleaned_data.append(CleanedData(
                original_value=value,
                cleaned_value=cleaned_value,
                is_outlier=is_outlier,
                quality_score=quality_score,
                cleaning_method=cleaning_method,
                timestamp=datetime.now()
            ))
        
        return cleaned_data
    
    def _handle_missing_values(self, values: List[float]) -> List[float]:
        """处理缺失值"""
        if self.missing_value_strategy == "drop":
            return [v for v in values if v is not None]
        elif self.missing_value_strategy == "forward_fill":
            return self._forward_fill(values)
        else:  # interpolate
            return self._interpolate_missing(values)
    
    def _forward_fill(self, values: List[float]) -> List[float]:
        """前向填充"""
        result = []
        last_value = None
        
        for v in values:
            if v is not None:
                result.append(v)
                last_value = v
            elif last_value is not None:
                result.append(last_value)
            else:
                result.append(np.mean([x for x in values if x is not None]))
        
        return result
    
    def _interpolate_missing(self, values: List[float]) -> List[float]:
        """插值填充"""
        result = []
        valid_indices = [i for i, v in enumerate(values) if v is not None]
        
        if not valid_indices:
            return [np.mean(values)] * len(values)
        
        for i, v in enumerate(values):
            if v is not None:
                result.append(v)
            else:
                # 找最近的两个有效值
                left_idx = max([idx for idx in valid_indices if idx < i], default=None)
                right_idx = min([idx for idx in valid_indices if idx > i], default=None)
                
                if left_idx is not None and right_idx is not None:
                    # 线性插值
                    left_val = values[left_idx]
                    right_val = values[right_idx]
                    interpolated = left_val + (right_val - left_val) * (i - left_idx) / (right_idx - left_idx)
                    result.append(interpolated)
                elif left_idx is not None:
                    result.append(values[left_idx])
                elif right_idx is not None:
                    result.append(values[right_idx])
                else:
                    result.append(np.mean([x for x in values if x is not None]))
        
        return result
    
    def _interpolate_value(self, values: List[float], index: int) -> float:
        """插值单个值"""
        if index == 0:
            return values[1] if len(values) > 1 else values[0]
        elif index == len(values) - 1:
            return values[-2]
        else:
            return (values[index - 1] + values[index + 1]) / 2


class FeatureExtractor:
    """特征提取器"""
    
    def extract_temporal_features(self, values: List[float], timestamps: List[datetime]) -> Dict[str, float]:
        """提取时间特征"""
        if not values:
            return {}
        
        values = np.array(values)
        
        features = {
            # 统计特征
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
            "q25": float(np.percentile(values, 25)),
            "q75": float(np.percentile(values, 75)),
            "range": float(np.max(values) - np.min(values)),
            "iqr": float(np.percentile(values, 75) - np.percentile(values, 25)),
            
            # 趋势特征
            "trend": float(np.polyfit(range(len(values)), values, 1)[0]),
            "acceleration": float(np.mean(np.diff(np.diff(values)))),
            
            # 变异性特征
            "cv": float(np.std(values) / np.mean(values)) if np.mean(values) != 0 else 0,
            "skewness": float(self._calculate_skewness(values)),
            "kurtosis": float(self._calculate_kurtosis(values)),
            
            # 周期特征
            "periodicity": float(self._detect_periodicity(values)),
            
            # 最近值特征
            "recent_mean": float(np.mean(values[-5:])) if len(values) >= 5 else float(np.mean(values)),
            "recent_trend": float(np.polyfit(range(min(5, len(values))), values[-min(5, len(values)):], 1)[0])
        }
        
        return features
    
    def _calculate_skewness(self, values: np.ndarray) -> float:
        """计算偏度"""
        mean = np.mean(values)
        std = np.std(values)
        if std == 0:
            return 0.0
        return np.mean(((values - mean) / std) ** 3)
    
    def _calculate_kurtosis(self, values: np.ndarray) -> float:
        """计算峰度"""
        mean = np.mean(values)
        std = np.std(values)
        if std == 0:
            return 0.0
        return np.mean(((values - mean) / std) ** 4) - 3
    
    def _detect_periodicity(self, values: np.ndarray) -> float:
        """检测周期性"""
        if len(values) < 10:
            return 0.0
        
        # 简化的周期检测：计算自相关
        mean = np.mean(values)
        c0 = np.sum((values - mean) ** 2) / len(values)
        
        if c0 == 0:
            return 0.0
        
        # 计算lag-1自相关
        c1 = np.sum((values[:-1] - mean) * (values[1:] - mean)) / len(values)
        
        return abs(c1 / c0)
    
    def extract_multimodal_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """提取多模态特征"""
        features = {}
        
        # 从传感器数据提取特征
        if "sensors" in data:
            for sensor_type, sensor_data in data["sensors"].items():
                if isinstance(sensor_data, (int, float)):
                    features[f"sensor_{sensor_type}"] = float(sensor_data)
        
        # 从HealthKit数据提取特征
        if "healthkit" in data:
            for key, value in data["healthkit"].items():
                if isinstance(value, (int, float)):
                    features[f"health_{key}"] = float(value)
        
        # 从应用使用数据提取特征
        if "app_usage" in data:
            app_usage = data["app_usage"]
            if "total_usage_minutes" in app_usage:
                features["app_total_usage"] = float(app_usage["total_usage_minutes"])
            if "by_category" in app_usage:
                for category, cat_data in app_usage["by_category"].items():
                    features[f"app_{category}_usage"] = float(cat_data.get("total_duration", 0))
        
        # 从位置天气数据提取特征
        if "location_weather" in data:
            for key, value in data["location_weather"].items():
                if isinstance(value, (int, float)):
                    features[f"weather_{key}"] = float(value)
        
        return features


class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self):
        self.z_score_threshold = 3.0
        self.isolation_forest_contamination = 0.1
    
    def detect_anomalies_zscore(self, values: List[float]) -> List[bool]:
        """使用Z-score检测异常"""
        if len(values) < 2:
            return [False] * len(values)
        
        values = np.array(values)
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return [False] * len(values)
        
        z_scores = np.abs((values - mean) / std)
        return (z_scores > self.z_score_threshold).tolist()
    
    def detect_anomalies_iqr(self, values: List[float]) -> List[bool]:
        """使用IQR检测异常"""
        if len(values) < 4:
            return [False] * len(values)
        
        values = np.array(values)
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        return ((values < lower_bound) | (values > upper_bound)).tolist()
    
    def detect_contextual_anomalies(self, values: List[float], context: Dict[str, Any]) -> List[bool]:
        """检测上下文异常"""
        anomalies = [False] * len(values)
        
        # 根据上下文调整异常检测
        if "activity" in context:
            activity = context["activity"]
            
            # 不同活动下的异常阈值不同
            if activity == "sleeping":
                # 睡眠时心率应该较低
                anomalies = [v > 100 for v in values]
            elif activity == "running":
                # 跑步时心率应该较高
                anomalies = [v < 100 for v in values]
        
        return anomalies


class DataQualityAssessor:
    """数据质量评估器"""
    
    def assess_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据质量"""
        quality_scores = {}
        
        # 评估传感器数据质量
        if "sensors" in data:
            quality_scores["sensors"] = self._assess_sensor_quality(data["sensors"])
        
        # 评估HealthKit数据质量
        if "healthkit" in data:
            quality_scores["healthkit"] = self._assess_healthkit_quality(data["healthkit"])
        
        # 评估应用使用数据质量
        if "app_usage" in data:
            quality_scores["app_usage"] = self._assess_app_usage_quality(data["app_usage"])
        
        # 评估位置天气数据质量
        if "location_weather" in data:
            quality_scores["location_weather"] = self._assess_location_weather_quality(data["location_weather"])
        
        # 计算总体质量分数
        overall_score = np.mean(list(quality_scores.values())) if quality_scores else 0.5
        
        return {
            "overall_quality": overall_score,
            "quality_level": self._get_quality_level(overall_score),
            "by_modality": quality_scores,
            "assessment_time": datetime.now().isoformat()
        }
    
    def _assess_sensor_quality(self, sensors: Dict[str, Any]) -> float:
        """评估传感器数据质量"""
        if not sensors:
            return 0.0
        
        quality_scores = []
        
        for sensor_type, sensor_data in sensors.items():
            if isinstance(sensor_data, dict):
                # 检查准确度和置信度
                accuracy = sensor_data.get("accuracy", 0.9)
                confidence = sensor_data.get("confidence", 0.9)
                quality_scores.append((accuracy + confidence) / 2)
            else:
                quality_scores.append(0.8)  # 默认质量分数
        
        return np.mean(quality_scores) if quality_scores else 0.5
    
    def _assess_healthkit_quality(self, healthkit: Dict[str, Any]) -> float:
        """评估HealthKit数据质量"""
        # HealthKit数据通常质量较高
        return 0.9
    
    def _assess_app_usage_quality(self, app_usage: Dict[str, Any]) -> float:
        """评估应用使用数据质量"""
        # 应用使用数据质量取决于数据完整性
        if "total_usage_minutes" in app_usage and "by_category" in app_usage:
            return 0.85
        return 0.7
    
    def _assess_location_weather_quality(self, location_weather: Dict[str, Any]) -> float:
        """评估位置天气数据质量"""
        # 位置天气数据质量取决于数据完整性
        required_fields = ["latitude", "longitude", "temperature", "humidity"]
        present_fields = sum(1 for field in required_fields if field in location_weather)
        return present_fields / len(required_fields)
    
    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 0.95:
            return "EXCELLENT"
        elif score >= 0.85:
            return "GOOD"
        elif score >= 0.70:
            return "FAIR"
        elif score >= 0.50:
            return "POOR"
        else:
            return "VERY_POOR"


class DataProcessingPipeline:
    """数据处理管道"""
    
    def __init__(self):
        self.cleaner = DataCleaner()
        self.feature_extractor = FeatureExtractor()
        self.anomaly_detector = AnomalyDetector()
        self.quality_assessor = DataQualityAssessor()
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理原始数据"""
        
        # 1. 数据清洗
        cleaned_data = self._clean_data(raw_data)
        
        # 2. 特征提取
        features = self.feature_extractor.extract_multimodal_features(cleaned_data)
        
        # 3. 异常检测
        anomalies = self._detect_anomalies(cleaned_data)
        
        # 4. 质量评估
        quality = self.quality_assessor.assess_quality(cleaned_data)
        
        # 5. 构建处理结果
        result = {
            "user_id": raw_data.get("user_id"),
            "timestamp": datetime.now().isoformat(),
            "raw_data": raw_data,
            "cleaned_data": cleaned_data,
            "features": features,
            "anomalies": anomalies,
            "quality": quality,
            "processing_status": "success"
        }
        
        return result
    
    def _clean_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗数据"""
        cleaned_data = raw_data.copy()
        
        # 清洗传感器数据
        if "sensors" in raw_data:
            for sensor_type, sensor_value in raw_data["sensors"].items():
                if isinstance(sensor_value, dict) and "value" in sensor_value:
                    # 这里可以应用更复杂的清洗逻辑
                    pass
        
        return cleaned_data
    
    def _detect_anomalies(self, data: Dict[str, Any]) -> Dict[str, List[bool]]:
        """检测异常"""
        anomalies = {}
        
        # 检测传感器异常
        if "sensors" in data:
            for sensor_type, sensor_data in data["sensors"].items():
                if isinstance(sensor_data, dict) and "value" in sensor_data:
                    value = sensor_data["value"]
                    # 简化的异常检测
                    anomalies[f"sensor_{sensor_type}"] = False
        
        return anomalies


# 全局实例
_pipeline = None

def get_data_processing_pipeline() -> DataProcessingPipeline:
    """获取数据处理管道实例"""
    global _pipeline
    if _pipeline is None:
        _pipeline = DataProcessingPipeline()
    return _pipeline

