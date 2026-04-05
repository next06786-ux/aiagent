#!/usr/bin/env python3
"""清除Redis缓存并重新测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis

# 清除Redis缓存
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )
    
    # 清除所有kg相关缓存
    keys = redis_client.keys("kg_*")
    if keys:
        redis_client.delete(*keys)
        print(f"✓ 已清除 {len(keys)} 个缓存")
    else:
        print("✓ 没有找到缓存")
except Exception as e:
    print(f"✗ 清除缓存失败: {e}")

# 运行测试
print("\n重新运行测试...\n")
os.system("python test_knowledge_graph_views.py")
