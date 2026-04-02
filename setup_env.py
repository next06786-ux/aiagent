#!/usr/bin/env python3
"""
LifeSwarm 环境变量快速配置脚本
帮助用户快速配置必要的环境变量
"""
import os
from pathlib import Path

def create_env_file():
    """创建 .env 文件"""
    
    print("\n" + "=" * 70)
    print("  LifeSwarm 环境变量配置")
    print("=" * 70 + "\n")
    
    env_file = Path(".env")
    
    # 检查是否已存在
    if env_file.exists():
        print("⚠️  .env 文件已存在")
        response = input("是否覆盖? (y/n): ").strip().lower()
        if response != 'y':
            print("✅ 保留现有配置")
            return
    
    print("\n请输入以下配置信息:")
    print("(如果不确定，可以先使用默认值)\n")
    
    # 收集配置信息
    config = {}
    
    # LLM 配置
    print("1️⃣  LLM 配置 (阿里云通义千问)")
    api_key = input("   DASHSCOPE_API_KEY (必需): ").strip()
    if not api_key:
        print("   ⚠️  API密钥为空，AI功能将不可用")
        api_key = "your_dashscope_api_key_here"
    config['DASHSCOPE_API_KEY'] = api_key
    
    # Neo4j 配置
    print("\n2️⃣  Neo4j 配置 (知识图谱数据库)")
    neo4j_uri = input("   NEO4J_URI (默认: bolt://localhost:7687): ").strip()
    config['NEO4J_URI'] = neo4j_uri or "bolt://localhost:7687"
    
    neo4j_user = input("   NEO4J_USER (默认: neo4j): ").strip()
    config['NEO4J_USER'] = neo4j_user or "neo4j"
    
    neo4j_password = input("   NEO4J_PASSWORD (默认: password): ").strip()
    config['NEO4J_PASSWORD'] = neo4j_password or "password"
    
    # PostgreSQL 配置
    print("\n3️⃣  PostgreSQL 配置 (主数据库)")
    db_url = input("   DATABASE_URL (默认: postgresql://user:password@localhost:5432/lifeswarm): ").strip()
    config['DATABASE_URL'] = db_url or "postgresql://user:password@localhost:5432/lifeswarm"
    
    # Redis 配置
    print("\n4️⃣  Redis 配置 (缓存)")
    redis_url = input("   REDIS_URL (默认: redis://localhost:6379/0): ").strip()
    config['REDIS_URL'] = redis_url or "redis://localhost:6379/0"
    
    # 服务器配置
    print("\n5️⃣  服务器配置")
    server_port = input("   SERVER_PORT (默认: 8000): ").strip()
    config['SERVER_PORT'] = server_port or "8000"
    
    debug = input("   DEBUG 模式 (y/n, 默认: y): ").strip().lower()
    config['DEBUG'] = "True" if debug != 'n' else "False"
    
    # 生成 .env 文件内容
    env_content = f"""# LifeSwarm 环境配置文件
# 自动生成于 {Path.cwd()}

# ==================== LLM 配置 ====================
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY={config['DASHSCOPE_API_KEY']}

# ==================== 数据库配置 ====================
# Neo4j 知识图谱数据库
NEO4J_URI={config['NEO4J_URI']}
NEO4J_USER={config['NEO4J_USER']}
NEO4J_PASSWORD={config['NEO4J_PASSWORD']}

# PostgreSQL 主数据库
DATABASE_URL={config['DATABASE_URL']}

# ==================== 缓存配置 ====================
# Redis 缓存
REDIS_URL={config['REDIS_URL']}

# ==================== 服务器配置 ====================
SERVER_HOST=0.0.0.0
SERVER_PORT={config['SERVER_PORT']}
DEBUG={config['DEBUG']}

# ==================== 日志配置 ====================
LOG_LEVEL=INFO
LOG_FILE=logs/lifeswarm.log

# ==================== 功能开关 ====================
ENABLE_RAG=True
ENABLE_KNOWLEDGE_GRAPH=True
ENABLE_EMERGENCE_DETECTION=True
ENABLE_REINFORCEMENT_LEARNING=True
ENABLE_MULTIMODAL_FUSION=True
"""
    
    # 写入文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("\n" + "=" * 70)
    print("✅ .env 文件已创建")
    print("=" * 70)
    print(f"\n📁 文件位置: {env_file.absolute()}")
    print("\n📋 配置摘要:")
    print(f"   LLM: {config['DASHSCOPE_API_KEY'][:20]}***")
    print(f"   Neo4j: {config['NEO4J_URI']}")
    print(f"   PostgreSQL: {config['DATABASE_URL'][:40]}***")
    print(f"   Redis: {config['REDIS_URL']}")
    print(f"   Server Port: {config['SERVER_PORT']}")
    print(f"   Debug: {config['DEBUG']}")
    print("\n✨ 现在可以启动后端服务了!")
    print("   运行: python quick_start.py")
    print()

if __name__ == "__main__":
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\n❌ 配置已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")














