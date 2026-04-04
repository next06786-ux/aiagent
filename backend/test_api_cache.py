#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试知识图谱API缓存"""

import requests
import time

API_BASE = "http://localhost:8000"
USER_ID = "2c2139f7-bab4-483d-9882-ae83ce8734cd"

def test_api_cache():
    print("\n" + "="*60)
    print("测试知识图谱API Redis缓存")
    print("="*60)
    
    # 第一次请求（无缓存）
    print("\n[测试1] 第一次请求（无缓存）...")
    url = f"{API_BASE}/api/v5/future-os/knowledge/{USER_ID}?view=people"
    
    start = time.time()
    response1 = requests.get(url)
    time1 = time.time() - start
    
    if response1.status_code == 200:
        data1 = response1.json()
        if data1.get('success'):
            nodes = len(data1['data']['nodes'])
            links = len(data1['data']['links'])
            print(f"✓ 加载完成: {nodes} 个节点, {links} 条关系")
            print(f"⏱️  耗时: {time1:.3f} 秒")
        else:
            print(f"❌ 请求失败: {data1.get('message')}")
            return
    else:
        print(f"❌ HTTP错误: {response1.status_code}")
        return
    
    # 第二次请求（有缓存）
    print("\n[测试2] 第二次请求（有缓存）...")
    start = time.time()
    response2 = requests.get(url)
    time2 = time.time() - start
    
    if response2.status_code == 200:
        data2 = response2.json()
        if data2.get('success'):
            nodes = len(data2['data']['nodes'])
            links = len(data2['data']['links'])
            print(f"✓ 加载完成: {nodes} 个节点, {links} 条关系")
            print(f"⏱️  耗时: {time2:.3f} 秒")
    
    # 性能提升
    if time2 > 0:
        speedup = time1 / time2
        improvement = ((time1 - time2) / time1) * 100
        print(f"\n📊 性能提升:")
        print(f"   第一次: {time1:.3f}秒 (从Neo4j加载)")
        print(f"   第二次: {time2:.3f}秒 (从Redis缓存)")
        print(f"   提升: {speedup:.1f}x 倍 ({improvement:.1f}% 更快)")
    
    # 测试清除缓存
    print("\n[测试3] 清除缓存...")
    clear_url = f"{API_BASE}/api/v5/future-os/knowledge/{USER_ID}/cache"
    response3 = requests.delete(clear_url)
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"✓ {data3.get('message')}")
    
    print("\n" + "="*60)
    print("✅ 缓存测试完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        test_api_cache()
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("请确保后端服务已启动: python main.py\n")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
