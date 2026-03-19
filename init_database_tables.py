"""
使用 SQLAlchemy 初始化数据库表
"""
import sys
import os
import hashlib

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database.connection import db_connection
from backend.database.models import Base, User
from datetime import datetime

print("="*80)
print("初始化数据库表")
print("="*80)

def hash_password(password: str) -> str:
    """密码加密"""
    salt = "lifeswarm_salt_2024"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

try:
    # 1. 创建所有表
    print("\n1. 创建数据库表...")
    engine = db_connection.engine
    Base.metadata.create_all(engine)
    print("   ✅ 所有表创建成功")
    
    # 2. 创建测试用户
    print("\n2. 创建测试用户...")
    
    # 用户信息
    user_id = "2c2139f7-bab4-483d-9882-ae83ce8734cd"
    username = "@163com"
    email = "test@163.com"
    password = "123456"
    nickname = "测试用户"
    
    db = db_connection.get_session()
    
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.id == user_id).first()
        
        if existing_user:
            print(f"   ℹ️  用户已存在，跳过创建")
            print(f"      用户ID: {existing_user.id}")
            print(f"      用户名: {existing_user.username}")
        else:
            # 创建新用户
            new_user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash=hash_password(password),
                nickname=nickname,
                is_active=True,
                is_verified=False,
                created_at=datetime.now()
            )
            
            db.add(new_user)
            db.commit()
            
            print(f"   ✅ 用户创建成功")
            print(f"      用户ID: {user_id}")
            print(f"      用户名: {username}")
            print(f"      邮箱: {email}")
            print(f"      昵称: {nickname}")
    
    finally:
        db.close()
    
    print(f"\n" + "="*80)
    print("✅ 数据库初始化完成！")
    print("="*80)
    
    print(f"\n登录信息:")
    print(f"   用户名: {username}")
    print(f"   密码: {password}")
    print(f"   用户ID: {user_id}")
    
except Exception as e:
    print(f"\n❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
