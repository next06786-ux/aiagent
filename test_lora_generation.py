"""
测试LoRA模型生成功能
"""
import torch
from backend.lora.lora_model_manager import LoRAModelManager

def test_lora_generation():
    """测试LoRA生成"""
    user_id = "a113a299-ecff-4363-8d44-aff979dfc547"
    
    print(f"\n{'='*80}")
    print(f"测试用户 {user_id} 的LoRA模型生成")
    print(f"{'='*80}\n")
    
    # 检查GPU内存
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"总内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        print(f"已用内存: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
        print(f"缓存内存: {torch.cuda.memory_reserved(0) / 1024**3:.2f} GB\n")
    
    # 初始化管理器
    manager = LoRAModelManager()
    
    # 简单的测试prompt
    prompt = """<|im_start|>user
你好，请用一句话介绍你自己。
<|im_end|>
<|im_start|>assistant
"""
    
    print("测试1: 简单生成（50 tokens）")
    try:
        response = manager.generate(
            user_id=user_id,
            prompt=prompt,
            max_new_tokens=50,
            temperature=0.7
        )
        print(f"✓ 生成成功")
        print(f"响应: {response}\n")
    except Exception as e:
        print(f"✗ 生成失败: {e}\n")
        return False
    
    # 检查内存
    if torch.cuda.is_available():
        print(f"生成后GPU内存:")
        print(f"已用: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
        print(f"缓存: {torch.cuda.memory_reserved(0) / 1024**3:.2f} GB\n")
    
    # 测试较长的生成
    json_prompt = """<|im_start|>user
请生成一个简单的JSON对象，包含name和age字段。
<|im_end|>
<|im_start|>assistant
"""
    
    print("测试2: JSON生成（100 tokens）")
    try:
        response = manager.generate(
            user_id=user_id,
            prompt=json_prompt,
            max_new_tokens=100,
            temperature=0.7
        )
        print(f"✓ 生成成功")
        print(f"响应: {response}\n")
    except Exception as e:
        print(f"✗ 生成失败: {e}\n")
        return False
    
    print(f"{'='*80}")
    print("✅ 所有测试通过")
    print(f"{'='*80}\n")
    return True

if __name__ == "__main__":
    test_lora_generation()
