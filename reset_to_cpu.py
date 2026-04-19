"""
重置为CPU模式
"""
import shutil
import os

print("="*60)
print("重置为CPU模式")
print("="*60)

# 清除GPU格式数据
rag_data_dir = "./data/production_rag"
if os.path.exists(rag_data_dir):
    print(f"\n删除GPU格式数据: {rag_data_dir}")
    shutil.rmtree(rag_data_dir)
    print("✅ 已删除")

# 重新创建目录
os.makedirs(rag_data_dir, exist_ok=True)
print(f"✅ 已重新创建目录")

print("\n" + "="*60)
print("✅ 重置完成")
print("="*60)
print("\n现在运行: python init_faiss_data.py")
print("然后重启后端")
