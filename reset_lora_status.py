"""
重置 LoRA 训练状态
用于清除卡住的训练标记
"""
import json
import os

def reset_training_status(user_id: str = "test_user_001"):
    """重置训练状态"""
    
    status_file = f"./models/lora/{user_id}/status.json"
    
    if not os.path.exists(status_file):
        print(f"❌ 状态文件不存在: {status_file}")
        return
    
    # 读取当前状态
    with open(status_file, 'r', encoding='utf-8') as f:
        status = json.load(f)
    
    print("当前状态:")
    print(f"  is_training: {status.get('is_training')}")
    print(f"  total_trainings: {status.get('total_trainings')}")
    print(f"  model_version: {status.get('model_version')}")
    print()
    
    # 重置 is_training 标记
    status['is_training'] = False
    
    # 保存
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
    
    print("✅ 已重置训练状态")
    print(f"  is_training: {status['is_training']}")
    print()
    print("现在可以重新运行: python test_lora_training.py")


if __name__ == "__main__":
    reset_training_status()
