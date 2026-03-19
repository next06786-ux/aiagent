"""
LoRA 训练测试 - 轻量版（适合 RTX 3050）
"""
import sys
sys.path.append('backend')

from lora.auto_lora_trainer import AutoLoRATrainer
from learning.production_rag_system import ProductionRAGSystem, MemoryType


def test_lora_training_light():
    """测试 LoRA 训练（轻量配置）"""
    
    user_id = "test_user_001"
    
    print("=" * 70)
    print("LoRA 自动训练系统测试 - 轻量版")
    print("=" * 70)
    print()
    
    # 1. 创建训练器
    print("1. 创建 LoRA 训练器...")
    trainer = AutoLoRATrainer(user_id)
    
    # 修改为更轻量的配置
    trainer.training_config.update({
        "num_epochs": 1,          # 只训练 1 轮
        "batch_size": 1,          # 批次大小改为 1
        "max_length": 256,        # 序列长度减半
    })
    
    # LoRA 配置也改小
    trainer.lora_config.r = 4     # 秩从 8 改为 4
    
    print(f"✅ 训练器创建成功")
    print(f"   用户: {user_id}")
    print(f"   基础模型: {trainer.base_model_name}")
    print(f"   轻量配置: epochs=1, batch=1, max_len=256, r=4")
    print()
    
    # 2. 获取对话数据
    print("2. 获取用户对话数据...")
    conversations = trainer.get_user_conversations()
    print(f"找到 {len(conversations)} 条对话")
    print()
    
    if len(conversations) < 20:
        print(f"❌ 数据不足: {len(conversations)}/20")
        print("请先运行: python create_test_conversations.py")
        return
    
    # 3. 开始训练
    print("3. 开始训练 LoRA 模型（轻量版）...")
    print("⚠️  预计需要 3-5 分钟...")
    print()
    
    trainer.auto_train_workflow()
    
    print()
    print("=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == "__main__":
    test_lora_training_light()
