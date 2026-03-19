"""
清空用户表
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database.connection import db_connection
from backend.database.models import User

print("="*80)
print("清空用户表")
print("="*80)

try:
    db = db_connection.get_session()
    
    # 查询所有用户
    users = db.query(User).all()
    
    print(f"\n当前用户数: {len(users)}")
    
    if len(users) > 0:
        print("\n用户列表:")
        for user in users:
            print(f"  - {user.username} ({user.email}) - ID: {user.id}")
        
        print(f"\n⚠️  警告：这将删除所有用户数据！")
        confirm = input("确认删除所有用户？(yes/no): ")
        
        if confirm.lower() == 'yes':
            # 删除所有用户
            db.query(User).delete()
            db.commit()
            print(f"\n✅ 已删除 {len(users)} 个用户")
        else:
            print("\n操作已取消")
    else:
        print("\n用户表已经是空的")
    
    db.close()
    
    print(f"\n" + "="*80)
    print("完成！")
    print("="*80)
    print("\n现在你可以:")
    print("  1. 重启后端服务")
    print("  2. 在前端注册新用户")
    print("  3. 登录后系统会自动使用新用户的 ID")
    
except Exception as e:
    print(f"\n❌ 操作失败: {e}")
    import traceback
    traceback.print_exc()
