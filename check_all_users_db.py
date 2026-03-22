import sqlite3
import os

db_path = 'backend/data/lifeswarm.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("  数据库中的所有用户")
    print("=" * 60)
    
    cursor.execute("SELECT user_id, username, email, nickname FROM users")
    users = cursor.fetchall()
    
    for user in users:
        print(f"\nuser_id: {user[0]}")
        print(f"username: {user[1]}")
        print(f"email: {user[2]}")
        print(f"nickname: {user[3]}")
    
    conn.close()
else:
    print(f"数据库文件不存在: {db_path}")
