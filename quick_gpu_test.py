"""
快速GPU测试 - 验证RAG系统是否使用GPU
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("快速GPU测试")
print("="*60)

# 1. 检测PyTorch GPU
print("\n1️⃣ 检测PyTorch GPU支持...")
try:
    import torch
    print(f"   ✅ PyTorch已安装")
    print(f"   CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   GPU数量: {torch.cuda.device_count()}")
        print(f"   GPU名称: {torch.cuda.get_device_name(0)}")
        print(f"   显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
except Exception as e:
    print(f"   ❌ PyTorch检测失败: {e}")

# 2. 检测FAISS GPU
print("\n2️⃣ 检测FAISS GPU支持...")
try:
    import faiss
    print(f"   ✅ FAISS已安装")
    print(f"   GPU数量: {faiss.get_num_gpus()}")
except Exception as e:
    print(f"   ❌ FAISS检测失败: {e}")

# 3. 测试RAG系统GPU初始化
print("\n3️⃣ 测试RAG系统GPU初始化...")
try:
    from backend.learning.rag_manager import RAGManager
    
    # 清除旧实例
    RAGManager.clear_cache()
    
    # 创建新实例（启用GPU）
    print("\n   创建RAG系统（use_gpu=True）...")
    rag = RAGManager.get_system("test_gpu_user", use_gpu=True)
    
    print(f"\n   ✅ RAG系统创建成功")
    print(f"   用户ID: {rag.user_id}")
    print(f"   GPU模式: {rag.use_gpu}")
    print(f"   Embedding维度: {rag.embedding_dim}")
    
    # 检查模型设备
    if hasattr(rag, 'model') and rag.model:
        print(f"   模型设备: {rag.model.device}")
    
    # 检查FAISS索引类型
    if hasattr(rag, 'index') and rag.index:
        index_type = type(rag.index).__name__
        print(f"   FAISS索引类型: {index_type}")
        if 'Gpu' in index_type:
            print(f"   ✅ 使用GPU索引")
        else:
            print(f"   ⚠️ 使用CPU索引")
    
except Exception as e:
    print(f"   ❌ RAG系统初始化失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("测试完成")
print("="*60)
