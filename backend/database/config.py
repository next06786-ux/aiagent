"""
数据库配置
存储层：MySQL（结构化）+ Neo4j（知识图谱）+ ChromaDB（向量/RAG）
"""
import os
from enum import Enum
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if not os.path.exists(_env_path):
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(_env_path)


class CacheType(Enum):
    MEMORY = "memory"
    REDIS  = "redis"


class DatabaseConfig:
    """数据库配置 — MySQL + Neo4j + ChromaDB"""

    # ── MySQL ──────────────────────────────────────────────────────────────
    MYSQL_HOST     = os.getenv('MYSQL_HOST',     'localhost')
    MYSQL_PORT     = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_USER     = os.getenv('MYSQL_USER',     'lifeswarm')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'lifeswarm123')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'lifeswarm')

    # ── Neo4j ──────────────────────────────────────────────────────────────
    NEO4J_URI      = os.getenv('NEO4J_URI',      'bolt://localhost:7687')
    NEO4J_USER     = os.getenv('NEO4J_USER',     'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'lifeswarm123')
    NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')

    # ── ChromaDB ───────────────────────────────────────────────────────────
    # 嵌入式模式，数据持久化到本地目录，无需单独服务
    CHROMA_PATH    = os.getenv('CHROMA_PATH', './data/chroma')

    # ── 缓存 ───────────────────────────────────────────────────────────────
    CACHE_TYPE     = os.getenv('CACHE_TYPE', CacheType.MEMORY.value)
    REDIS_HOST     = os.getenv('REDIS_HOST',     'localhost')
    REDIS_PORT     = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_DB       = int(os.getenv('REDIS_DB',   '0'))
    REDIS_PREFIX   = os.getenv('REDIS_PREFIX',   'lifeswarm:')

    # ── 连接池 ─────────────────────────────────────────────────────────────
    POOL_SIZE      = int(os.getenv('DB_POOL_SIZE',      '5'))
    MAX_OVERFLOW   = int(os.getenv('DB_MAX_OVERFLOW',   '10'))
    POOL_TIMEOUT   = int(os.getenv('DB_POOL_TIMEOUT',   '30'))
    POOL_RECYCLE   = int(os.getenv('DB_POOL_RECYCLE',   '3600'))

    # ── 缓存设置 ───────────────────────────────────────────────────────────
    CACHE_TTL      = int(os.getenv('CACHE_TTL',      '3600'))
    CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', '1000'))

    DEBUG = os.getenv('LIFESWARM_ENV', 'production') == 'development'

    @classmethod
    def get_database_url(cls) -> str:
        return (
            f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}"
            f"@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @classmethod
    def get_engine_options(cls) -> dict:
        return {
            'pool_pre_ping':  True,
            'pool_recycle':   cls.POOL_RECYCLE,
            'pool_size':      cls.POOL_SIZE,
            'max_overflow':   cls.MAX_OVERFLOW,
            'pool_timeout':   cls.POOL_TIMEOUT,
        }

    @classmethod
    def get_redis_url(cls) -> str:
        if cls.REDIS_PASSWORD:
            return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"


# 根据环境选配置（都用同一套，只有 DEBUG 标志不同）
ENV = os.getenv('LIFESWARM_ENV', 'production')
config = DatabaseConfig
