"""
清除RAG缓存，强制重新初始化GPU模式
"""
import shutil
import os

print("="*60)
print("清除RAG缓存")
print("="*60)

# 清除FAISS数据
rag_data_dir = "./data/production_rag"
if os.path.exists(rag_data_dir):
    print(f"\n删除目录: {rag_data_dir}")
    shutil.rmtree(rag_data_dir)
    print("✅ 已删除")
else:
    print(f"\n目录不存在: {rag_data_dir}")

# 重新创建目录
os.makedirs(rag_data_dir, exist_ok=True)
print(f"✅ 已重新创建目录")

print("\n" + "="*60)
print("✅ 缓存清除完成")
print("="*60)
print("\n现在重启后端，将使用GPU模式初始化")
