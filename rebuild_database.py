"""
重建数据库表（删除旧表并创建新表）
"""
import sys
import os
import hashlib

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database.connection import db_connection
from backend.database.models import Base, User
from datetime import datetime

print("="*80)
print("重建数据库表")
print("="*80)

def hash_password(password: str) -> str:
    """密码加密"""
    salt = "lifeswarm_salt_2024"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

try:
    engine = db_connection.engine
    
    # 1. 删除所有旧表
    print("\n1. 删除旧表...")
    print("   ⚠️  警告：这将删除所有数据！")
    
    confirm = input("   确认删除所有表？(yes/no): ")
    if confirm.lower() != 'yes':
        print("   操作已取消")
        sys.exit(0)
    
    Base.metadata.drop_all(engine)
    print("   ✅ 旧表已删除")
    
    # 2. 创建所有新表
    print("\n2. 创建新表...")
    Base.metadata.create_all(engine)
    print("   ✅ 新表创建成功")
    
    # 3. 创建测试用户
    print("\n3. 创建测试用户...")
    
    user_id = "2c2139f7-bab4-483d-9882-ae83ce8734cd"
    username = "@163com"
    email = "test@163.com"
    password = "123456"
    nickname = "测试用户"
    
    db = db_connection.get_session()
    
    try:
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
    print("✅ 数据库重建完成！")
    print("="*80)
    
    print(f"\n登录信息:")
    print(f"   用户名: {username}")
    print(f"   密码: {password}")
    print(f"   用户ID: {user_id}")
    
except Exception as e:
    print(f"\n❌ 重建失败: {e}")
    import traceback
    traceback.print_exc()
