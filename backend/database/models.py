"""
数据库模型
使用SQLAlchemy ORM
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Date, 
    JSON, ForeignKey, Text, Boolean, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(String(50), primary_key=True)
    
    # 认证信息
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # 存储加密后的密码
    
    # 用户信息
    nickname = Column(String(50))
    avatar_url = Column(String(500))
    phone = Column(String(20))
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    memories = relationship("VisualMemory", back_populates="user")
    health_records = relationship("HealthRecord", back_populates="user")
    predictions = relationship("Prediction", back_populates="user")


class VisualMemory(Base):
    """视觉记忆表"""
    __tablename__ = 'visual_memories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.id'))
    
    # 视觉特征（存储为JSON）
    features = Column(JSON)  # 特征向量
    scene = Column(String(50))
    objects = Column(JSON)  # 物体列表
    activities = Column(JSON)  # 活动列表
    
    # 时空信息
    timestamp = Column(Integer)
    location_lat = Column(Float)
    location_lng = Column(Float)
    
    # 元数据
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    user = relationship("User", back_populates="memories")


class HealthRecord(Base):
    """健康记录表"""
    __tablename__ = 'health_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.id'))
    
    # 健康指标
    timestamp = Column(DateTime, default=datetime.now)
    sleep_hours = Column(Float)
    sleep_quality = Column(Float)  # 0-1
    steps = Column(Integer)
    heart_rate = Column(Integer)
    exercise_minutes = Column(Integer)
    stress_level = Column(Float)  # 0-10
    
    # 计算指标
    health_score = Column(Float)  # 0-100
    
    # 关系
    user = relationship("User", back_populates="health_records")


class TimeRecord(Base):
    """时间记录表"""
    __tablename__ = 'time_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.id'))
    
    timestamp = Column(DateTime, default=datetime.now)
    date = Column(String(10))  # YYYY-MM-DD
    
    # 时间分配
    work_hours = Column(Float)
    sleep_hours = Column(Float)
    exercise_hours = Column(Float)
    social_hours = Column(Float)
    leisure_hours = Column(Float)
    
    # 效率指标
    productivity_score = Column(Float)  # 0-1
    focus_time = Column(Float)  # 专注时间（小时）
    
    # 应用使用
    app_usage = Column(JSON)  # {app_name: minutes}


class Prediction(Base):
    """预测记录表"""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.id'))
    
    # 预测信息
    prediction_type = Column(String(50))  # health, time, etc.
    time_horizon = Column(String(20))  # 1_day, 1_week, etc.
    created_at = Column(DateTime, default=datetime.now)
    target_date = Column(DateTime)
    
    # 预测结果
    prediction_data = Column(JSON)  # 预测的详细数据
    confidence = Column(Float)
    
    # 验证
    actual_data = Column(JSON)  # 实际发生的数据
    accuracy = Column(Float)  # 预测准确度
    verified_at = Column(DateTime)
    
    # 关系
    user = relationship("User", back_populates="predictions")


class EmergentPattern(Base):
    """涌现模式表"""
    __tablename__ = 'emergent_patterns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.id'))
    
    # 模式信息
    pattern_type = Column(String(50))  # cascade, feedback_loop, tipping_point
    domain = Column(String(50))
    description = Column(Text)
    
    # 置信度和影响
    confidence = Column(Float)
    impact_score = Column(Float)
    
    # 涉及的智能体
    involved_agents = Column(JSON)
    
    # 详细信息
    details = Column(JSON)
    
    # 时间
    detected_at = Column(DateTime, default=datetime.now)
    valid_until = Column(DateTime)


# 数据库连接
class Database:
    """数据库管理类"""
    
    def __init__(self, db_url: str = None):
        # 从环境变量读取MySQL配置
        if db_url is None:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            mysql_host = os.getenv("MYSQL_HOST", "localhost")
            mysql_port = os.getenv("MYSQL_PORT", "3306")
            mysql_user = os.getenv("MYSQL_USER", "root")
            mysql_password = os.getenv("MYSQL_PASSWORD", "")
            mysql_database = os.getenv("MYSQL_DATABASE", "lifeswarm")
            
            db_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4"
        
        self.db_url = db_url
        self._engine = None
        self._SessionLocal = None
    
    @property
    def engine(self):
        """延迟初始化数据库引擎"""
        if self._engine is None:
            self._engine = create_engine(self.db_url, echo=False, pool_recycle=3600)
        return self._engine
    
    @property
    def SessionLocal(self):
        """延迟初始化Session工厂"""
        if self._SessionLocal is None:
            self._SessionLocal = sessionmaker(bind=self.engine)
        return self._SessionLocal
        
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def drop_tables(self):
        """删除所有表（仅用于测试）"""
        Base.metadata.drop_all(self.engine)


# 全局数据库实例（延迟初始化）
db = Database()



# ==================== 新增模型 ====================

class ImageMemory(Base):
    """图像记忆表"""
    __tablename__ = 'image_memories'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    image_id = Column(String(100), unique=True, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # 场景信息
    scene_type = Column(String(50))
    indoor_outdoor = Column(String(20))
    time_context = Column(String(50))
    scene_description = Column(Text)
    scene_confidence = Column(Float)
    
    # 活动信息
    activity_type = Column(String(50))
    activity_description = Column(Text)
    activity_confidence = Column(Float)
    
    # 位置信息
    latitude = Column(Float)
    longitude = Column(Float)
    location_name = Column(String(200))
    
    # 特征（JSON 存储）
    features = Column(JSON)
    
    # 缩略图（Base64）
    thumbnail = Column(Text)
    
    # 标签
    tags = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Anomaly(Base):
    """异常记录表"""
    __tablename__ = 'anomalies'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 异常信息
    anomaly_type = Column(String(50), nullable=False)
    domain = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # high, medium, low
    message = Column(Text)
    value = Column(Float)
    
    # 状态
    status = Column(String(20), default='active')  # active, resolved, ignored
    resolved_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class SmartSuggestionRecord(Base):
    """智能建议记录表"""
    __tablename__ = 'smart_suggestions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 建议信息
    priority = Column(String(20), nullable=False)  # high, medium, low
    domain = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    action = Column(Text)
    
    # 状态
    status = Column(String(20), default='pending')  # pending, accepted, rejected, expired
    user_response = Column(String(200))
    responded_at = Column(DateTime)
    
    # 关联的异常
    anomaly_id = Column(Integer, ForeignKey('anomalies.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DailySummary(Base):
    """每日总结表"""
    __tablename__ = 'daily_summaries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # 总结内容
    data_points = Column(Integer, default=0)
    domains = Column(JSON)
    highlights = Column(JSON)
    concerns = Column(JSON)
    summary_text = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='unique_user_date'),
    )


class WeeklyReport(Base):
    """周报表"""
    __tablename__ = 'weekly_reports'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    
    # 报告内容
    data_points = Column(Integer, default=0)
    summary = Column(Text)
    trends = Column(JSON)
    achievements = Column(JSON)
    recommendations = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'year', 'week', name='unique_user_week'),
    )


class BackupRecord(Base):
    """备份记录表"""
    __tablename__ = 'backup_records'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    backup_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 备份信息
    backup_type = Column(String(20), nullable=False)  # full, incremental
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    # 备份内容统计
    items_count = Column(JSON)
    
    # 状态
    status = Column(String(20), default='completed')  # completed, failed, in_progress
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ConversationHistory(Base):
    """对话历史表"""
    __tablename__ = 'conversation_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    
    # Agent信息（新增）
    agent_type = Column(String(20), index=True)  # relationship, education, career
    conversation_id = Column(String(100), index=True)  # 对话会话ID
    conversation_title = Column(String(200))  # 对话标题（自动生成）
    
    # 对话信息
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    thinking = Column(Text)  # AI思考过程
    
    # 上下文
    context = Column(JSON)  # 对话时的上下文数据
    retrieval_stats = Column(JSON)  # 检索统计信息
    
    # 反馈
    rating = Column(Integer)  # 1-5星评分
    helpful = Column(Boolean)  # 是否有帮助
    action_taken = Column(Boolean)  # 用户是否采取了行动
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 会话ID（用于分组对话）- 保留兼容性
    session_id = Column(String(100), index=True)


class UserConfig(Base):
    """用户配置表"""
    __tablename__ = 'user_configs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, unique=True, index=True)
    
    # 启用的领域
    enabled_domains = Column(JSON, default=list)  # ['health', 'time', ...]
    
    # 显示模式
    display_mode = Column(String(20), default='simple')  # simple, expert
    
    # 通知设置
    notification_enabled = Column(Boolean, default=True)
    notification_frequency = Column(String(20), default='daily')  # realtime, daily, weekly
    
    # 隐私设置
    data_collection_enabled = Column(Boolean, default=True)
    visual_memory_enabled = Column(Boolean, default=False)
    
    # 个性化设置
    language = Column(String(10), default='zh-CN')
    timezone = Column(String(50), default='Asia/Shanghai')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EvolutionMetrics(Base):
    """进化指标表 - 记录个人模型的进化过程"""
    __tablename__ = 'evolution_metrics'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    
    # 进化指标
    total_samples = Column(Integer, default=0)  # 总样本数
    confidence_score = Column(Float, default=0.0)  # 置信度
    accuracy = Column(Float, default=0.0)  # 准确率
    
    # 各领域指标
    domain_metrics = Column(JSON)  # {'health': {...}, 'time': {...}}
    
    # 推荐策略
    recommended_strategy = Column(String(20))  # llm_only, personal_only, hybrid
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class UserInsight(Base):
    """用户洞察表 - 存储从对话中实时提取的洞察数据"""
    __tablename__ = 'user_insights'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    
    # 洞察标识
    insight_id = Column(String(100), nullable=False)
    
    # 洞察类型和分类
    data_type = Column(String(50), nullable=False)  # emotion, topic, intent, entity, image, voice
    category = Column(String(50), nullable=False, index=True)  # health, work, social, finance, learning, emotion
    
    # 洞察内容
    content = Column(Text)
    value = Column(Float)  # 量化值（如情绪分数0-10）
    confidence = Column(Float, default=0.8)
    
    # 来源
    source_message_id = Column(String(100))  # 关联的消息ID
    
    # 元数据（改名避免与SQLAlchemy冲突）
    extra_data = Column(JSON)  # 额外信息（检测到的关键词等）
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_insights_user_type', 'user_id', 'data_type'),
        Index('idx_user_insights_user_category', 'user_id', 'category'),
        Index('idx_user_insights_user_time', 'user_id', 'timestamp'),
    )


class EmergenceInsight(Base):
    """涌现洞察表 - 存储涌现分析生成的高级洞察"""
    __tablename__ = 'emergence_insights'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    
    # 洞察标识
    insight_id = Column(String(100), nullable=False, unique=True)
    
    # 洞察分类和级别
    category = Column(String(50), nullable=False)  # cascade, synergy, tipping_point, feedback_loop, pattern, trend, anomaly
    level = Column(String(20), nullable=False)  # critical, warning, suggestion, info
    
    # 洞察内容
    title = Column(String(200), nullable=False)
    description = Column(Text)
    evidence = Column(JSON)  # 支撑证据列表
    recommendations = Column(JSON)  # 建议行动列表
    
    # 评分
    confidence = Column(Float, default=0.8)
    impact_score = Column(Float, default=50.0)  # 影响力分数 0-100
    
    # 相关指标
    related_metrics = Column(JSON)  # 相关的指标列表
    
    # 可视化数据
    visualization_data = Column(JSON)
    
    # 状态
    status = Column(String(20), default='active')  # active, resolved, dismissed
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)  # 过期时间
    
    __table_args__ = (
        Index('idx_emergence_user_category', 'user_id', 'category'),
        Index('idx_emergence_user_level', 'user_id', 'level'),
    )
