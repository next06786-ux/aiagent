"""
检查数据库表结构
"""
import pymysql
from backend.database.config import DatabaseConfig

print("="*80)
print("检查数据库表结构")
print("="*80)

try:
    # 连接数据库
    connection = pymysql.connect(
        host=DatabaseConfig.MYSQL_HOST,
        port=DatabaseConfig.MYSQL_PORT,
        user=DatabaseConfig.MYSQL_USER,
        password=DatabaseConfig.MYSQL_PASSWORD,
        database=DatabaseConfig.MYSQL_DATABASE,
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    
    # 查看 users 表结构
    cursor.execute("DESCRIBE users")
    columns = cursor.fetchall()
    
    print(f"\nusers 表结构:")
    print("-" * 80)
    for col in columns:
        print(f"字段: {col[0]:<20} 类型: {col[1]:<20} 允许NULL: {col[2]}")
    
    # 查看表中的数据
    cursor.execute("SELECT * FROM users LIMIT 5")
    users = cursor.fetchall()
    
    print(f"\n\nusers 表数据 (前5条):")
    print("-" * 80)
    
    # 获取列名
    cursor.execute("DESCRIBE users")
    column_names = [col[0] for col in cursor.fetchall()]
    print(f"列名: {column_names}")
    
    for user in users:
        print(f"\n记录: {user}")
    
    cursor.close()
    connection.close()
    
    print(f"\n" + "="*80)
    print("检查完成")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
