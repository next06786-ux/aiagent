"""
测试决策历史数据库
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decision.decision_history import DecisionHistoryManager

def test_database():
    """测试数据库连接和数据"""
    
    # 数据库配置
    db_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'lifeswarm')
    }
    
    print("数据库配置:")
    print(f"  Host: {db_config['host']}")
    print(f"  Port: {db_config['port']}")
    print(f"  User: {db_config['user']}")
    print(f"  Database: {db_config['database']}")
    print()
    
    try:
        # 创建管理器
        manager = DecisionHistoryManager(db_config)
        
        if not manager.enabled:
            print("❌ 决策历史功能未启用")
            return
        
        print("✅ 数据库连接成功")
        print()
        
        # 查询 test_user_001 的历史记录
        user_id = 'test_user_001'
        print(f"查询用户 {user_id} 的历史记录...")
        result = manager.get_history_list(user_id, limit=100, offset=0)
        
        print(f"查询结果:")
        print(f"  Success: {result.get('success')}")
        print(f"  Total: {result.get('total')}")
        print(f"  Histories: {len(result.get('histories', []))}")
        print()
        
        if result.get('histories'):
            print("历史记录列表:")
            for i, history in enumerate(result['histories'], 1):
                print(f"\n{i}. ID: {history.get('id')}")
                print(f"   Session: {history.get('session_id')}")
                print(f"   Question: {history.get('question')}")
                print(f"   Type: {history.get('decision_type')}")
                print(f"   Created: {history.get('created_at')}")
                print(f"   Completed: {history.get('completed_at')}")
                print(f"   Options: {history.get('options_count')}")
        else:
            print("⚠️ 没有找到历史记录")
            print()
            print("可能的原因:")
            print("1. 数据库表为空")
            print("2. user_id 不匹配")
            print("3. 数据还没有保存")
        
        # 直接查询数据库表
        print("\n" + "="*60)
        print("直接查询数据库表...")
        conn = manager._get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询所有记录
        cursor.execute("SELECT COUNT(*) as total FROM decision_histories")
        total = cursor.fetchone()['total']
        print(f"表中总记录数: {total}")
        
        if total > 0:
            cursor.execute("""
                SELECT id, user_id, session_id, question, created_at 
                FROM decision_histories 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            records = cursor.fetchall()
            print(f"\n最近的 {len(records)} 条记录:")
            for i, record in enumerate(records, 1):
                print(f"\n{i}. ID: {record['id']}")
                print(f"   User: {record['user_id']}")
                print(f"   Session: {record['session_id']}")
                print(f"   Question: {record['question'][:50]}...")
                print(f"   Created: {record['created_at']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_database()
