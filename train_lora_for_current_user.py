"""
为当前登录用户训练LoRA模型
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 你的真实用户ID
USER_ID = "2c2139f7-bab4-483d-9882-ae83ce8734cd"

print("="*80)
print(f"为用户 {USER_ID} 训练LoRA模型")
print("="*80)

try:
    from backend.lora.auto_lora_trainer import AutoLoRATrainer
    from backend.conversation.conversation_storage import ConversationStorage
    
    # 1. 检查用户是否有对话历史
    storage = ConversationStorage()
    sessions = storage.get_user_sessions(USER_ID)
    
    print(f"\n1. 检查对话历史")
    print(f"   用户会话数量: {len(sessions)}")
    
    # 统计总消息数
    total_messages = 0
    for session in sessions:
        messages = storage.get_session_messages(USER_ID, session['id'])  # 使用 'id' 而不是 'session_id'
        total_messages += len(messages)
    
    print(f"   总消息数量: {total_messages}")
    
    if total_messages < 10:
        print(f"   ⚠️ 对话历史太少（需要至少10条消息），无法训练LoRA模型")
        print(f"   💡 建议: 先与AI对话至少5轮，积累足够的数据")
        sys.exit(1)
    
    # 2. 初始化训练器
    print(f"\n2. 初始化LoRA训练器")
    trainer = AutoLoRATrainer(user_id=USER_ID)
    
    # 3. 开始训练
    print(f"\n3. 开始训练LoRA模型...")
    print(f"   这可能需要几分钟时间，请耐心等待...")
    
    result = trainer.train_user_model(
        user_id=USER_ID,
        force_retrain=True  # 强制重新训练
    )
    
    # 4. 显示结果
    print(f"\n" + "="*80)
    print(f"训练完成！")
    print(f"="*80)
    print(f"训练状态: {result.get('status', 'unknown')}")
    print(f"模型版本: v{result.get('model_version', 0)}")
    print(f"训练数据量: {result.get('training_samples', 0)}")
    
    if 'model_path' in result:
        print(f"模型保存位置: {result['model_path']}")
    
    print(f"\n✅ 现在可以使用决策模拟功能了！")
    
except ImportError as e:
    print(f"\n❌ 导入失败: {e}")
    print(f"\n💡 请确保已安装所有依赖:")
    print(f"   pip install torch transformers peft")
    
except Exception as e:
    print(f"\n❌ 训练失败: {e}")
    import traceback
    traceback.print_exc()
