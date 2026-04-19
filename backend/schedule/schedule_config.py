"""
智能日程自动生成配置
"""
from typing import Dict, Any


class ScheduleAutoConfig:
    """日程自动生成配置"""
    
    # 每日日程生成时间（24小时制）
    DAILY_GENERATION_HOUR = 2  # 凌晨2点
    DAILY_GENERATION_MINUTE = 0
    
    # 每周计划生成时间
    WEEKLY_GENERATION_DAY = 'sun'  # 周日
    WEEKLY_GENERATION_HOUR = 20  # 晚上8点
    WEEKLY_GENERATION_MINUTE = 0
    
    # 数据变化检查频率（分钟）
    CHECK_INTERVAL_MINUTES = 30  # 每30分钟检查一次（避免使用60导致cron表达式错误）
    
    # 活跃用户定义（最近N天有活动）
    ACTIVE_USER_DAYS = 7
    
    # 数据更新检测窗口（小时）
    UPDATE_DETECTION_HOURS = 1
    
    # 自动生成的日程提前天数
    GENERATION_DAYS_AHEAD = 1  # 生成明天的日程
    
    # 周计划生成天数
    WEEKLY_PLAN_DAYS = 7  # 生成未来7天
    
    # 是否启用自动生成
    ENABLE_AUTO_GENERATION = True
    
    # 是否启用周计划生成
    ENABLE_WEEKLY_GENERATION = True
    
    # 是否启用数据变化触发
    ENABLE_UPDATE_TRIGGER = True
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "daily_generation": {
                "hour": cls.DAILY_GENERATION_HOUR,
                "minute": cls.DAILY_GENERATION_MINUTE,
                "enabled": cls.ENABLE_AUTO_GENERATION
            },
            "weekly_generation": {
                "day": cls.WEEKLY_GENERATION_DAY,
                "hour": cls.WEEKLY_GENERATION_HOUR,
                "minute": cls.WEEKLY_GENERATION_MINUTE,
                "days_ahead": cls.WEEKLY_PLAN_DAYS,
                "enabled": cls.ENABLE_WEEKLY_GENERATION
            },
            "update_trigger": {
                "check_interval_minutes": cls.CHECK_INTERVAL_MINUTES,
                "detection_hours": cls.UPDATE_DETECTION_HOURS,
                "enabled": cls.ENABLE_UPDATE_TRIGGER
            },
            "user_settings": {
                "active_user_days": cls.ACTIVE_USER_DAYS,
                "generation_days_ahead": cls.GENERATION_DAYS_AHEAD
            }
        }
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        import os
        
        cls.DAILY_GENERATION_HOUR = int(os.getenv(
            "SCHEDULE_DAILY_HOUR", 
            cls.DAILY_GENERATION_HOUR
        ))
        cls.DAILY_GENERATION_MINUTE = int(os.getenv(
            "SCHEDULE_DAILY_MINUTE", 
            cls.DAILY_GENERATION_MINUTE
        ))
        
        cls.WEEKLY_GENERATION_HOUR = int(os.getenv(
            "SCHEDULE_WEEKLY_HOUR", 
            cls.WEEKLY_GENERATION_HOUR
        ))
        cls.WEEKLY_GENERATION_MINUTE = int(os.getenv(
            "SCHEDULE_WEEKLY_MINUTE", 
            cls.WEEKLY_GENERATION_MINUTE
        ))
        
        cls.CHECK_INTERVAL_MINUTES = int(os.getenv(
            "SCHEDULE_CHECK_INTERVAL", 
            cls.CHECK_INTERVAL_MINUTES
        ))
        
        cls.ENABLE_AUTO_GENERATION = os.getenv(
            "SCHEDULE_ENABLE_AUTO", 
            "true"
        ).lower() == "true"
        
        cls.ENABLE_WEEKLY_GENERATION = os.getenv(
            "SCHEDULE_ENABLE_WEEKLY", 
            "true"
        ).lower() == "true"
        
        cls.ENABLE_UPDATE_TRIGGER = os.getenv(
            "SCHEDULE_ENABLE_UPDATE_TRIGGER", 
            "true"
        ).lower() == "true"


# 启动时从环境变量加载配置
ScheduleAutoConfig.from_env()
