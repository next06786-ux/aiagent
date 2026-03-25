"""
数据库配置
Database Configuration - 支持 SQLite, MySQL, PostgreSQL, Redis
"""
import os
from enum import Enum
from dotenv import load_dotenv

# 加载 .env 文件
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if not os.path.exists(_env_path):
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(_env_path)


class DatabaseType(Enum):
    """数据库类型"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"


class CacheType(Enum):
    """缓存类型"""
    MEMORY = "memory"
    REDIS = "redis"


class DatabaseConfig:
    """数据库配置"""
    
    # 主数据库配置（默认 MySQL）
    DB_TYPE = os.getenv('DB_TYPE', DatabaseType.MYSQL.value)
    
    # MySQL 配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_USER = os.getenv('MYSQL_USER', 'lifeswarm')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'lifeswarm123')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'lifeswarm')
    
    # PostgreSQL 配置
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'lifeswarm')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'lifeswarm123')
    POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'lifeswarm')
    
    # 缓存配置
    CACHE_TYPE = os.getenv('CACHE_TYPE', CacheType.MEMORY.value)
    
    # Redis 配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_PREFIX = os.getenv('REDIS_PREFIX', 'lifeswarm:')
    
    # 连接池配置
    POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
    MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    
    # 缓存配置
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 默认 1 小时
    CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', '1000'))  # 内存缓存最大条目数
    
    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库连接 URL"""
        if cls.DB_TYPE == DatabaseType.MYSQL.value:
            return (
                f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}"
                f"@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}"
                f"?charset=utf8mb4"
            )
        
        elif cls.DB_TYPE == DatabaseType.POSTGRESQL.value:
            return (
                f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
                f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DATABASE}"
            )
        
        else:
            raise ValueError(f"Unsupported database type: {cls.DB_TYPE}")
    
    @classmethod
    def get_engine_options(cls) -> dict:
        """获取数据库引擎选项"""
        options = {
            'pool_pre_ping': True,  # 连接前检查
            'pool_recycle': cls.POOL_RECYCLE,  # 连接回收时间
            'pool_size': cls.POOL_SIZE,
            'max_overflow': cls.MAX_OVERFLOW,
            'pool_timeout': cls.POOL_TIMEOUT,
        }
        
        return options
    
    @classmethod
    def get_redis_url(cls) -> str:
        """获取 Redis 连接 URL"""
        if cls.REDIS_PASSWORD:
            return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        else:
            return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"


# 开发环境配置
class DevelopmentConfig(DatabaseConfig):
    """开发环境配置"""
    DB_TYPE = DatabaseType.MYSQL.value
    CACHE_TYPE = CacheType.MEMORY.value
    DEBUG = True


# 生产环境配置
class ProductionConfig(DatabaseConfig):
    """生产环境配置"""
    DB_TYPE = DatabaseType.MYSQL.value
    CACHE_TYPE = CacheType.REDIS.value
    DEBUG = False


# 测试环境配置（使用 MySQL 测试数据库）
class TestingConfig(DatabaseConfig):
    """测试环境配置"""
    DB_TYPE = DatabaseType.MYSQL.value
    MYSQL_DATABASE = 'lifeswarm_test'  # 测试数据库
    CACHE_TYPE = CacheType.MEMORY.value
    DEBUG = True


# 根据环境变量选择配置
ENV = os.getenv('LIFESWARM_ENV', 'development')

if ENV == 'production':
    config = ProductionConfig
elif ENV == 'testing':
    config = TestingConfig
else:
    config = DevelopmentConfig
