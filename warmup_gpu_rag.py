"""
预热GPU RAG系统
在后端启动前运行，确保使用GPU模式
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("🔥 预热GPU RAG系统")
print("="*60)

from backend.learning.rag_manager import RAGManager

# 清除所有缓存
print("\n1️⃣ 清除旧缓存...")
RAGManager.clear_cache()
print("   ✅ 缓存已清除")

# 为演示用户预创建GPU模式的RAG系统
print("\n2️⃣ 预创建GPU RAG系统...")
demo_users = [
    "2c2139f7-bab4-483d-9882-ae83ce8734cd",  # 演示用户
    "demo_user",
    "test_user"
]

for user_id in demo_users:
    print(f"\n   创建用户 {user_id} 的RAG系统...")
    try:
        rag = RAGManager.get_system(user_id, use_gpu=True)
        print(f"   ✅ 成功 - GPU模式: {rag.use_gpu}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")

print("\n" + "="*60)
print("✅ GPU RAG系统预热完成")
print("="*60)
print("\n现在可以启动后端服务了")
