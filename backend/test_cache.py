#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试知识图谱Redis缓存"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
from decision.future_os_service import FutureOsService

USER_ID = "2c2139f7-bab4-483d-9882-ae83ce8734cd"

def test_cache():
    service = FutureOsService()
    
    print("\n" + "="*60)
    print("测试知识图谱Redis缓存")
    print("="*60)
    
    # 第一次加载（无缓存）
    print("\n[测试1] 第一次加载（无缓存）...")
    start = time.time()
    result1 = service.get_graph_view(USER_ID, 'people')
    time1 = time.time() - start
    print(f"✓ 加载完成: {len(result1['nodes'])} 个节点, {len(result1['links'])} 条关系")
    print(f"⏱️  耗时: {time1:.3f} 秒")
    
    # 第二次加载（有缓存）
    print("\n[测试2] 第二次加载（有缓存）...")
    start = time.time()
    result2 = service.get_graph_view(USER_ID, 'people')
    time2 = time.time() - start
    print(f"✓ 加载完成: {len(result2['nodes'])} 个节点, {len(result2['links'])} 条关系")
    print(f"⏱️  耗时: {time2:.3f} 秒")
    
    # 性能提升
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\n📊 性能提升: {speedup:.1f}x 倍")
    print(f"   第一次: {time1:.3f}秒")
    print(f"   第二次: {time2:.3f}秒 (缓存)")
    
    # 测试不同视图
    print("\n[测试3] 测试升学规划视图...")
    start = time.time()
    result3 = service.get_graph_view(USER_ID, 'signals')
    time3 = time.time() - start
    print(f"✓ 加载完成: {len(result3['nodes'])} 个节点")
    print(f"⏱️  耗时: {time3:.3f} 秒")
    
    print("\n" + "="*60)
    print("✅ 缓存测试完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_cache()
