"""
检查数据库中的用户信息
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database.connection import db_connection
from backend.database.models import User

print("="*80)
print("检查数据库中的用户")
print("="*80)

try:
    db = db_connection.get_session()
    
    # 查询所有用户
    users = db.query(User).all()
    
    print(f"\n数据库中共有 {len(users)} 个用户:\n")
    
    for user in users:
        print(f"用户ID: {user.user_id}")
        print(f"用户名: {user.username}")
        print(f"邮箱: {user.email}")
        print(f"昵称: {user.nickname}")
        print(f"创建时间: {user.created_at}")
        print("-" * 80)
    
    # 查找特定用户
    target_username = "@163com"
    target_user = db.query(User).filter(User.username == target_username).first()
    
    if target_user:
        print(f"\n✅ 找到用户 '{target_username}':")
        print(f"   用户ID: {target_user.user_id}")
        print(f"   邮箱: {target_user.email}")
        print(f"   昵称: {target_user.nickname}")
    else:
        print(f"\n❌ 未找到用户 '{target_username}'")
        print(f"\n💡 可用的用户名:")
        for user in users:
            print(f"   - {user.username}")
    
    db.close()
    
except Exception as e:
    print(f"\n❌ 查询失败: {e}")
    import traceback
    traceback.print_exc()
