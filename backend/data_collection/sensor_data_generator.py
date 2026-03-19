"""
传感器数据生成器 - 用于测试和演示
生成真实的传感器数据模拟
"""
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json


class SensorDataGenerator:
    """传感器数据生成器"""
    
    def __init__(self, user_id: str, seed: int = None):
        self.user_id = user_id
        if seed:
            random.seed(seed)
    
    def generate_daily_data(self, date: datetime) -> Dict[str, Any]:
        """生成一天的完整传感器数据"""
        hour = date.hour
        
        # 根据时间段生成不同的活动模式
        if 6 <= hour < 9:
            activity_type = "morning_routine"
            intensity = 0.3
        elif 9 <= hour < 12:
            activity_type = "work"
            intensity = 0.5
        elif 12 <= hour < 14:
            activity_type = "lunch"
            intensity = 0.2
        elif 14 <= hour < 18:
            activity_type = "work"
            intensity = 0.6
        elif 18 <= hour < 20:
            activity_type = "exercise"
            intensity = 0.8
        elif 20 <= hour < 23:
            activity_type = "leisure"
            intensity = 0.3
        else:
            activity_type = "sleep"
            intensity = 0.0
        
        # 生成传感器数据
        return {
            "timestamp": int(date.timestamp() * 1000),
            "sensor": {
                "heartRate": self._generate_heart_rate(intensity, activity_type),
                "steps": self._generate_steps(intensity, activity_type),
                "accelerometer": self._generate_accelerometer(intensity),
                "gyroscope": self._generate_gyroscope(intensity),
                "lightLevel": self._generate_light_level(hour)
            },
            "health": {
                "sleepHours": self._generate_sleep_hours(hour),
                "sleepQuality": self._generate_sleep_quality(hour),
                "exerciseMinutes": self._generate_exercise_minutes(activity_type),
                "stressLevel": self._generate_stress_level(hour, activity_type),
                "mood": self._generate_mood(hour, activity_type)
            },
            "context": {
                "timeOfDay": self._get_time_of_day(hour),
                "dayOfWeek": date.strftime("%A"),
                "weather": self._generate_weather(),
                "location": self._generate_location(hour, activity_type)
            },
            "metadata": {
                "dataQuality": 0.85,
                "completeness": 1.0,
                "availableModalities": ["sensor", "health", "context"]
            }
        }
    
    def _generate_heart_rate(self, intensity: float, activity_type: str) -> int:
        """生成心率数据"""
        if activity_type == "sleep":
            base = 55
            variance = 5
        elif activity_type == "exercise":
            base = 120
            variance = 20
        elif activity_type == "work":
            base = 75
            variance = 10
        else:
            base = 70
            variance = 8
        
        return int(base + intensity * 30 + random.randint(-variance, variance))
    
    def _generate_steps(self, intensity: float, activity_type: str) -> int:
        """生成步数数据"""
        if activity_type == "sleep":
            return 0
        elif activity_type == "exercise":
            return random.randint(100, 200)
        elif activity_type == "work":
            return random.randint(20, 60)
        else:
            return random.randint(10, 40)
    
    def _generate_accelerometer(self, intensity: float) -> Dict[str, float]:
        """生成加速度计数据"""
        return {
            "x": round(random.uniform(-1, 1) * intensity, 3),
            "y": round(random.uniform(-1, 1) * intensity, 3),
            "z": round(9.8 + random.uniform(-0.5, 0.5) * intensity, 3)
        }
    
    def _generate_gyroscope(self, intensity: float) -> Dict[str, float]:
        """生成陀螺仪数据"""
        return {
            "x": round(random.uniform(-0.1, 0.1) * intensity, 4),
            "y": round(random.uniform(-0.1, 0.1) * intensity, 4),
            "z": round(random.uniform(-0.1, 0.1) * intensity, 4)
        }
    
    def _generate_light_level(self, hour: int) -> int:
        """生成光线水平"""
        if 6 <= hour < 9:
            return random.randint(100, 300)
        elif 9 <= hour < 18:
            return random.randint(500, 1000)
        elif 18 <= hour < 21:
            return random.randint(100, 300)
        else:
            return random.randint(0, 50)
    
    def _generate_sleep_hours(self, hour: int) -> float:
        """生成睡眠时长"""
        if 0 <= hour < 6:
            return round(random.uniform(6, 8), 1)
        else:
            return 0.0
    
    def _generate_sleep_quality(self, hour: int) -> float:
        """生成睡眠质量"""
        if 0 <= hour < 6:
            return round(random.uniform(0.6, 0.95), 2)
        else:
            return 0.0
    
    def _generate_exercise_minutes(self, activity_type: str) -> int:
        """生成运动时长"""
        if activity_type == "exercise":
            return random.randint(30, 60)
        else:
            return 0
    
    def _generate_stress_level(self, hour: int, activity_type: str) -> float:
        """生成压力水平"""
        if activity_type == "work":
            base = 6.0
        elif activity_type == "exercise":
            base = 3.0
        elif activity_type == "sleep":
            base = 1.0
        else:
            base = 4.0
        
        return round(base + random.uniform(-1, 1), 1)
    
    def _generate_mood(self, hour: int, activity_type: str) -> int:
        """生成心情评分"""
        if activity_type == "exercise":
            base = 8
        elif activity_type == "sleep":
            base = 5
        elif activity_type == "work":
            base = 6
        else:
            base = 7
        
        return max(1, min(10, base + random.randint(-2, 2)))
    
    def _get_time_of_day(self, hour: int) -> str:
        """获取时间段"""
        if 6 <= hour < 9:
            return "morning"
        elif 9 <= hour < 12:
            return "forenoon"
        elif 12 <= hour < 14:
            return "noon"
        elif 14 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def _generate_weather(self) -> Dict[str, Any]:
        """生成天气数据"""
        weather_types = ["sunny", "cloudy", "rainy", "snowy"]
        return {
            "type": random.choice(weather_types),
            "temperature": random.randint(5, 35),
            "humidity": random.randint(30, 90),
            "windSpeed": random.randint(0, 20)
        }
    
    def _generate_location(self, hour: int, activity_type: str) -> Dict[str, Any]:
        """生成位置数据"""
        locations = {
            "home": {"latitude": 39.9042, "longitude": 116.4074, "name": "Home"},
            "office": {"latitude": 39.9015, "longitude": 116.4074, "name": "Office"},
            "gym": {"latitude": 39.9100, "longitude": 116.4100, "name": "Gym"},
            "park": {"latitude": 39.9200, "longitude": 116.4200, "name": "Park"}
        }
        
        if activity_type == "sleep":
            loc = locations["home"]
        elif activity_type == "work":
            loc = locations["office"]
        elif activity_type == "exercise":
            loc = locations["gym"]
        else:
            loc = random.choice(list(locations.values()))
        
        return {
            "latitude": loc["latitude"] + random.uniform(-0.01, 0.01),
            "longitude": loc["longitude"] + random.uniform(-0.01, 0.01),
            "name": loc["name"]
        }
    
    def generate_week_data(self, start_date: datetime = None) -> List[Dict[str, Any]]:
        """生成一周的数据"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        
        data = []
        current = start_date
        
        for _ in range(7 * 24):  # 7天，每小时一条数据
            data.append(self.generate_daily_data(current))
            current += timedelta(hours=1)
        
        return data


def generate_test_dataset(user_id: str = "test_user", days: int = 7) -> List[Dict[str, Any]]:
    """生成测试数据集"""
    generator = SensorDataGenerator(user_id, seed=42)
    
    start_date = datetime.now() - timedelta(days=days)
    data = []
    current = start_date
    
    for _ in range(days * 24):
        data.append(generator.generate_daily_data(current))
        current += timedelta(hours=1)
    
    return data


if __name__ == "__main__":
    # 生成测试数据
    data = generate_test_dataset("demo_user", days=7)
    
    # 保存到文件
    with open("/e:/ai/data/test_sensor_data.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ 生成了 {len(data)} 条测试数据")
    print(f"📁 保存到: /e:/ai/data/test_sensor_data.json")

