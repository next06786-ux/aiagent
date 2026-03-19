"""
测试 LoRA 训练（带详细错误信息）
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

USER_ID = "a113a299-ecff-4363-8d44-aff979dfc547"

print("="*80)
print(f"测试 LoRA 训练 - 用户: {USER_ID}")
print("="*80)

try:
    print("\n1. 导入模块...")
    from backend.lora.auto_lora_trainer import AutoLoRATrainer
    print("   ✅ 模块导入成功")
    
    print("\n2. 初始化训练器...")
    trainer = AutoLoRATrainer(user_id=USER_ID)
    print("   ✅ 训练器初始化成功")
    
    print("\n3. 获取对话数据...")
    conversations = trainer.get_user_conversations()
    print(f"   ✅ 获取到 {len(conversations)} 对对话")
    
    if len(conversations) < 5:
        print(f"\n   ⚠️ 对话数量不足（需要至少 5 对）")
        sys.exit(1)
    
    print("\n4. 准备训练数据集...")
    dataset = trainer.prepare_dataset(conversations)
    print(f"   ✅ 数据集准备完成，大小: {len(dataset)}")
    
    print("\n5. 开始训练...")
    print("   这可能需要几分钟，请耐心等待...\n")
    
    model_path = trainer.train_lora(dataset)
    
    if model_path:
        print(f"\n✅ 训练成功！")
        print(f"   模型路径: {model_path}")
        
        # 更新状态
        trainer.status['model_version'] += 1
        trainer.status['last_training_time'] = __import__('datetime').datetime.now().isoformat()
        trainer.status['training_samples'] = len(conversations)
        trainer.save_status()
        
        print(f"\n模型版本: v{trainer.status['model_version']}")
    else:
        print(f"\n❌ 训练失败")
        sys.exit(1)
    
except KeyboardInterrupt:
    print(f"\n\n⚠️ 训练被用户中断")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ 发生错误: {e}")
    print(f"\n详细错误信息:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
