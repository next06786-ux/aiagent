"""
初始化管理员账号
Initialize Admin User
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.db_manager import DatabaseManager
from backend.database.models import User
from datetime import datetime
import bcrypt

def init_admin_user():
    """初始化管理员账号"""
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # 管理员信息
        admin_id = 'admin-00000000-0000-0000-0000-000000000001'
        admin_username = 'admin'
        admin_password = 'admin123'  # 请在生产环境中修改
        admin_email = 'admin@choicerealm.com'
        admin_nickname = '系统管理员'
        
        # 检查管理员是否已存在
        existing_admin = session.query(User).filter(User.id == admin_id).first()
        
        if existing_admin:
            print(f"✓ 管理员账号已存在: {admin_username}")
            print(f"  用户ID: {admin_id}")
            print(f"  邮箱: {admin_email}")
            return
        
        # 创建管理员账号
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        
        admin_user = User(
            id=admin_id,
            username=admin_username,
            email=admin_email,
            password_hash=hashed_password.decode('utf-8'),
            nickname=admin_nickname,
            is_active=True,
            is_verified=True,
            created_at=datetime.now(),
            last_login=datetime.now()
        )
        
        session.add(admin_user)
        session.commit()
        
        print("="*60)
        print("✅ 管理员账号创建成功！")
        print("="*60)
        print(f"\n📋 登录信息:")
        print(f"  用户名: {admin_username}")
        print(f"  密码: {admin_password}")
        print(f"  邮箱: {admin_email}")
        print(f"  用户ID: {admin_id}")
        print(f"\n⚠️  请在生产环境中修改默认密码！")
        print("="*60)
        
    except Exception as e:
        session.rollback()
        print(f"❌ 创建管理员账号失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def check_demo_user():
    """检查演示用户"""
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        demo_id = '2c2139f7-bab4-483d-9882-ae83ce8734cd'
        demo_user = session.query(User).filter(User.id == demo_id).first()
        
        if demo_user:
            print(f"\n✓ 演示用户信息:")
            print(f"  用户名: {demo_user.username}")
            print(f"  昵称: {demo_user.nickname}")
            print(f"  邮箱: {demo_user.email}")
            print(f"  用户ID: {demo_user.id}")
            print(f"  状态: {'活跃' if demo_user.is_active else '禁用'}")
        else:
            print(f"\n⚠️  演示用户不存在，ID: {demo_id}")
            print("  请运行 init_demo_student_data.py 创建演示学生账号")
            
    finally:
        session.close()


if __name__ == "__main__":
    print("\n🚀 初始化管理员账号...\n")
    init_admin_user()
    check_demo_user()
    print("\n✅ 完成！\n")
