"""
初始化智能洞察相关的数据库表
"""
import sys
sys.path.insert(0, '.')

from backend.database.models import Base, UserInsight, EmergenceInsight
from backend.database.connection import db_connection

def init_tables():
    """创建智能洞察相关的表"""
    print("🔧 初始化智能洞察数据库表...")
    
    try:
        engine = db_connection.engine
        
        # 只创建新表（不影响现有表）
        UserInsight.__table__.create(engine, checkfirst=True)
        EmergenceInsight.__table__.create(engine, checkfirst=True)
        
        print("✅ UserInsight 表已创建")
        print("✅ EmergenceInsight 表已创建")
        print("\n🎉 智能洞察数据库表初始化完成!")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_tables()
