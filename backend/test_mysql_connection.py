# -*- coding: utf-8 -*-
"""测试MySQL连接"""
import pymysql

# 测试配置
configs = [
    {"user": "root", "password": "", "desc": "root无密码"},
    {"user": "root", "password": "root", "desc": "root密码root"},
    {"user": "root", "password": "123456", "desc": "root密码123456"},
    {"user": "lifeswarm", "password": "lifeswarm123", "desc": "lifeswarm用户"},
]

print("="*70)
print("  MySQL连接测试")
print("="*70 + "\n")

for config in configs:
    try:
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user=config["user"],
            password=config["password"],
            charset='utf8mb4'
        )
        print(f"✓ 连接成功: {config['desc']}")
        
        # 检查数据库
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        print(f"  可用数据库: {', '.join(databases)}")
        
        # 检查lifeswarm数据库是否存在
        if 'lifeswarm' in databases:
            print(f"  ✓ lifeswarm数据库存在")
        else:
            print(f"  ⚠️  lifeswarm数据库不存在")
        
        conn.close()
        print()
        break  # 找到可用连接就停止
        
    except Exception as e:
        print(f"✗ 连接失败: {config['desc']}")
        print(f"  错误: {e}")
        print()

print("="*70)
print("  建议:")
print("  1. 如果root连接成功，可以创建lifeswarm用户和数据库")
print("  2. 或者修改backend/.env文件，使用root用户")
print("="*70)
