"""
数据库连接管理
Database Connection Manager - 支持多种数据库
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from .config import config
import logging

# 禁用 SQLAlchemy 的详细日志输出
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

# 创建基类
Base = declarative_base()


class DatabaseConnection:
    """数据库连接管理器"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.Session = None
        self._initialize()
    
    def _initialize(self):
        """初始化数据库连接"""
        # 获取数据库 URL
        database_url = config.get_database_url()
        
        # 获取引擎选项
        engine_options = config.get_engine_options()
        
        # 创建引擎
        self.engine = create_engine(
            database_url,
            **engine_options,
            echo=False  # 关闭 SQLAlchemy SQL 日志输出
        )
        
        # 创建会话工厂
        self.session_factory = sessionmaker(bind=self.engine)
        
        # 创建线程安全的会话
        self.Session = scoped_session(self.session_factory)
        
        print(f"✓ 数据库连接已建立: {config.DB_TYPE}")
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
        print("✓ 数据库表已创建")
    
    def drop_tables(self):
        """删除所有表（谨慎使用）"""
        Base.metadata.drop_all(self.engine)
        print("⚠️ 数据库表已删除")
    
    def get_session(self):
        """获取数据库会话"""
        return self.Session()
    
    def close_session(self):
        """关闭会话"""
        self.Session.remove()
    
    def dispose(self):
        """释放连接池"""
        if self.engine:
            self.engine.dispose()
            print("✓ 数据库连接已释放")


# 全局数据库连接实例
db_connection = DatabaseConnection()
