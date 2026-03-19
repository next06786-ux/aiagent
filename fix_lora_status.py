"""
修复 LoRA 状态文件
为已训练的模型创建状态文件
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

USER_ID = "2c2139f7-bab4-483d-9882-ae83ce8734cd"

print("="*80)
print(f"修复用户 LoRA 状态文件")
print("="*80)

# 1. 创建状态目录
status_dir = "backend/data/lora_status"
os.makedirs(status_dir, exist_ok=True)
print(f"\n✅ 状态目录: {status_dir}")

# 2. 创建状态文件
status_file = f"{status_dir}/{USER_ID}_status.json"

status_data = {
    "user_id": USER_ID,
    "model_version": 1,
    "last_training_time": datetime.now().isoformat(),
    "training_samples": 6,
    "training_config": {
        "min_conversations": 20,
        "train_interval_days": 7,
        "max_samples": 1000,
        "learning_rate": 0.0001,
        "num_epochs": 3,
        "batch_size": 4
    },
    "model_path": f"./models/lora/{USER_ID}/v1/final",
    "status": "ready"
}

with open(status_file, 'w', encoding='utf-8') as f:
    json.dump(status_data, f, indent=2, ensure_ascii=False)

print(f"✅ 状态文件已创建: {status_file}")
print(f"\n状态信息:")
print(f"   用户ID: {status_data['user_id']}")
print(f"   模型版本: v{status_data['model_version']}")
print(f"   训练样本数: {status_data['training_samples']}")
print(f"   模型路径: {status_data['model_path']}")

print(f"\n" + "="*80)
print(f"✅ 修复完成！")
print(f"="*80)
print(f"\n💡 现在你可以:")
print(f"   1. 重启后端服务")
print(f"   2. 在前端使用决策模拟功能")
print(f"   3. 系统会自动使用你的个性化 LoRA 模型")
