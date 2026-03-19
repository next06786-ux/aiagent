"""
验证用户的LoRA模型是否准备就绪
"""
import sys
import os
from backend.learning.production_rag_system import ProductionRAGSystem

def verify_user_lora(user_id: str):
    """验证用户的LoRA模型状态"""
    print(f"\n{'='*80}")
    print(f"验证用户 {user_id} 的LoRA模型状态")
    print(f"{'='*80}\n")
    
    # 1. 检查RAG系统中的对话数据
    print("1. 检查RAG系统中的对话数据")
    try:
        rag = ProductionRAGSystem(user_id)
        memories = rag.get_all_memories()
        conversation_count = sum(1 for m in memories if m.memory_type.value == "conversation")
        print(f"   ✓ RAG系统中有 {conversation_count} 条对话")
        
        if conversation_count == 0:
            print("   ❌ 没有对话数据，无法训练LoRA模型")
            return False
    except Exception as e:
        print(f"   ❌ 检查RAG系统失败: {e}")
        return False
    
    # 2. 检查LoRA模型文件
    print("\n2. 检查LoRA模型文件")
    model_path = f"./models/lora/{user_id}/v1/final"
    if os.path.exists(model_path):
        print(f"   ✓ LoRA模型存在: {model_path}")
        
        # 检查必要的文件
        required_files = ["adapter_config.json", "adapter_model.safetensors"]
        all_exist = True
        for file in required_files:
            file_path = os.path.join(model_path, file)
            if os.path.exists(file_path):
                print(f"   ✓ {file}")
            else:
                print(f"   ✗ {file} 缺失")
                all_exist = False
        
        if not all_exist:
            print("   ❌ LoRA模型文件不完整")
            return False
    else:
        print(f"   ❌ LoRA模型不存在: {model_path}")
        return False
    
    print(f"\n{'='*80}")
    print("✅ 用户LoRA模型准备就绪，可以进行决策模拟！")
    print(f"{'='*80}\n")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = "a113a299-ecff-4363-8d44-aff979dfc547"
    
    verify_user_lora(user_id)
