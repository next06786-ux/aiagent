"""
测试自动记忆存储功能
验证对话和图片数据是否自动存入RAG
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_chat_memory_storage():
    """测试对话记忆自动存储"""
    print("=" * 80)
    print("测试1: 对话记忆自动存储")
    print("=" * 80)
    
    # 发送几条对话
    messages = [
        "我最近睡眠不好，怎么办？",
        "如何提高学习效率？",
        "我想改善人际关系"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n{i}. 发送消息: {message}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat/chat",
            json={
                "user_id": "test_user_auto",
                "message": message,
                "stream": False,
                "enable_thinking": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ AI回复: {result['content'][:100]}...")
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
        
        time.sleep(1)
    
    # 通过API查询后端进程中的记忆
    print(f"\n{'=' * 80}")
    print("检查后端进程中的记忆存储情况...")
    print(f"{'=' * 80}")
    
    response = requests.get(f"{BASE_URL}/api/memory/stats/test_user_auto")
    if response.status_code == 200:
        stats = response.json()['data']
        
        print(f"\n📊 记忆统计:")
        print(f"   总记忆数: {stats['total_memories']}")
        print(f"   对话记忆: {stats['memory_types']['conversation']}")
        print(f"   平均重要性: {stats['average_importance']:.2f}")
        
        # 获取最近的对话记忆
        response = requests.get(f"{BASE_URL}/api/memory/list/test_user_auto?memory_type=conversation&limit=6")
        if response.status_code == 200:
            memories = response.json()['data']['memories']
            
            print(f"\n📝 最近的对话记忆:")
            for i, memory in enumerate(memories, 1):
                print(f"   {i}. {memory['content'][:80]}...")
                print(f"      时间: {memory['timestamp'][:19]}, 重要性: {memory['importance']}")
    else:
        print(f"   ❌ 查询失败: {response.status_code}")


def test_multimodal_memory_storage():
    """测试多模态数据记忆自动存储"""
    print(f"\n{'=' * 80}")
    print("测试2: 多模态数据记忆自动存储")
    print(f"{'=' * 80}")
    
    # 发送多模态数据
    data = {
        "user_id": "test_user_auto",
        "timestamp": int(time.time() * 1000),
        "text": "今天跑步了5公里，感觉很好",
        "sensor": {
            "steps": 8000,
            "heartRate": 75,
            "distance": 5.2
        },
        "health": {
            "sleepHours": 7.5,
            "sleepQuality": 8,
            "exerciseMinutes": 45,
            "stressLevel": 3
        },
        "context": {
            "location": "公园",
            "weather": "晴天",
            "temperature": 22
        }
    }
    
    print(f"\n发送多模态数据...")
    response = requests.post(
        f"{BASE_URL}/api/v4/multimodal/data",
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 数据上传成功")
        print(f"   处理的模态: {result['data']['modalities_processed']}")
    else:
        print(f"   ❌ 请求失败: {response.status_code}")
    
    time.sleep(1)
    
    # 通过API查询记忆
    response = requests.get(f"{BASE_URL}/api/memory/stats/test_user_auto")
    if response.status_code == 200:
        stats = response.json()['data']
        
        print(f"\n📊 更新后的记忆统计:")
        print(f"   总记忆数: {stats['total_memories']}")
        print(f"   对话记忆: {stats['memory_types']['conversation']}")
        print(f"   传感器记忆: {stats['memory_types']['sensor_data']}")
        
        # 获取传感器记忆
        response = requests.get(f"{BASE_URL}/api/memory/list/test_user_auto?memory_type=sensor_data&limit=3")
        if response.status_code == 200:
            memories = response.json()['data']['memories']
            
            print(f"\n📡 传感器记忆:")
            for i, memory in enumerate(memories, 1):
                print(f"   {i}. {memory['content'][:80]}...")
    else:
        print(f"   ❌ 查询失败: {response.status_code}")


def test_memory_retrieval():
    """测试记忆检索 - 通过API"""
    print(f"\n{'=' * 80}")
    print("测试3: 记忆检索功能")
    print(f"{'=' * 80}")
    
    # 获取所有记忆
    response = requests.get(f"{BASE_URL}/api/memory/list/test_user_auto?limit=20")
    
    if response.status_code == 200:
        memories = response.json()['data']['memories']
        
        print(f"\n📚 所有记忆 (最近20条):")
        for i, memory in enumerate(memories, 1):
            print(f"\n{i}. [{memory['type']}] {memory['content'][:80]}...")
            print(f"   时间: {memory['timestamp'][:19]}")
            print(f"   重要性: {memory['importance']}, 访问次数: {memory['access_count']}")
        
        if not memories:
            print("   暂无记忆")
    else:
        print(f"   ❌ 查询失败: {response.status_code}")
    
    print(f"\n💡 提示:")
    print(f"   - 记忆已存储在后端进程中")
    print(f"   - 下次对话时，第2层历史记忆检索会自动检索这些记忆")
    print(f"   - 可以通过 GET /api/memory/stats/{{user_id}} 查看统计")
    print(f"   - 可以通过 GET /api/memory/list/{{user_id}} 查看记忆列表")


if __name__ == "__main__":
    print("\n🧪 开始测试自动记忆存储功能...\n")
    
    # 确保后端服务正在运行
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ 后端服务未运行，请先启动: python backend/start_server.py")
            exit(1)
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {e}")
        print("   请先启动: python backend/start_server.py")
        exit(1)
    
    # 运行测试
    test_chat_memory_storage()
    test_multimodal_memory_storage()
    test_memory_retrieval()
    
    print(f"\n{'=' * 80}")
    print("✅ 所有测试完成！")
    print(f"{'=' * 80}\n")
