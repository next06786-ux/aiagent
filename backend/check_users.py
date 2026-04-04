# -*- coding: utf-8 -*-
"""查询数据库中的用户"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.connection import db_connection
from database.models import User

print("\n查询数据库中的用户...\n")

with db_connection.get_session() as session:
    users = session.query(User).all()
    
    if not users:
        print("数据库中没有用户")
    else:
        print(f"找到 {len(users)} 个用户:\n")
        for user in users:
            print(f"ID: {user.id}")
            print(f"用户名: {user.username}")
            print(f"邮箱: {user.email}")
            print(f"昵称: {user.nickname}")
            print(f"创建时间: {user.created_at}")
            print("-" * 50)
