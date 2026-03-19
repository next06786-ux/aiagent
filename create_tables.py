"""
创建数据库表
使用 SQLAlchemy 创建所有模型定义的表
"""
from backend.database.connection import db_connection
from backend.database.models import Base

def create_all_tables():
    """创建所有表"""
    try:
        print("🚀 开始创建数据库表...")
        
        # 创建所有表
        Base.metadata.create_all(db_connection.engine)
        
        print("✅ 数据库表创建成功！")
        
        # 显示创建的表
        from sqlalchemy import inspect
        inspector = inspect(db_connection.engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 已创建 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table}")
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_all_tables()
