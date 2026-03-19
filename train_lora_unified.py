"""
统一的 LoRA 训练脚本
自动从数据库和 RAG 系统获取对话数据进行训练
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 你的真实用户ID
USER_ID = "a113a299-ecff-4363-8d44-aff979dfc547"

print("="*80)
print(f"为用户 {USER_ID} 训练LoRA模型")
print("="*80)

try:
    from backend.lora.auto_lora_trainer import AutoLoRATrainer
    from backend.conversation.conversation_storage import ConversationStorage
    from learning.production_rag_system import ProductionRAGSystem
    
    # 1. 从数据库获取对话历史
    print(f"\n1. 检查数据库对话历史")
    storage = ConversationStorage()
    sessions = storage.get_user_sessions(USER_ID)
    print(f"   数据库会话数量: {len(sessions)}")
    
    db_conversations = []
    for session in sessions:
        messages = storage.get_session_messages(USER_ID, session['id'])
        
        # 将消息配对成对话
        for i in range(0, len(messages) - 1, 2):
            if i + 1 < len(messages):
                user_msg = messages[i]
                ai_msg = messages[i + 1]
                
                if user_msg['role'] == 'user' and ai_msg['role'] == 'assistant':
                    db_conversations.append({
                        "user": user_msg['content'],
                        "assistant": ai_msg['content'],
                        "timestamp": user_msg['timestamp']
                    })
    
    print(f"   数据库对话对数: {len(db_conversations)}")
    
    # 2. 从 RAG 系统获取记忆
    print(f"\n2. 检查 RAG 系统记忆")
    try:
        rag_system = ProductionRAGSystem(USER_ID)
        memories = rag_system.get_all_memories()
        
        rag_conversations = []
        for mem in memories:
            if mem.memory_type.value == "conversation":
                content = mem.content
                if "用户:" in content and "AI:" in content:
                    parts = content.split("AI:")
                    user_msg = parts[0].replace("用户:", "").strip()
                    ai_msg = parts[1].strip() if len(parts) > 1 else ""
                    
                    if user_msg and ai_msg:
                        rag_conversations.append({
                            "user": user_msg,
                            "assistant": ai_msg,
                            "timestamp": mem.timestamp
                        })
        
        print(f"   RAG 对话对数: {len(rag_conversations)}")
    except Exception as e:
        print(f"   ⚠️ RAG 系统暂时不可用: {e}")
        rag_conversations = []
    
    # 3. 合并数据（去重）
    all_conversations = db_conversations + rag_conversations
    
    # 简单去重：基于内容
    unique_conversations = []
    seen = set()
    for conv in all_conversations:
        key = (conv['user'][:50], conv['assistant'][:50])  # 使用前50个字符作为key
        if key not in seen:
            seen.add(key)
            unique_conversations.append(conv)
    
    print(f"\n3. 合并后的训练数据")
    print(f"   总对话对数: {len(unique_conversations)}")
    
    if len(unique_conversations) < 5:
        print(f"\n   ⚠️ 对话历史太少（需要至少5对对话），无法训练LoRA模型")
        print(f"   💡 建议: 先与AI对话至少5轮，积累足够的数据")
        print(f"\n   当前数据来源:")
        print(f"   - 数据库: {len(db_conversations)} 对")
        print(f"   - RAG系统: {len(rag_conversations)} 对")
        sys.exit(1)
    
    # 4. 初始化训练器并训练
    print(f"\n4. 开始训练LoRA模型...")
    print(f"   这可能需要几分钟时间，请耐心等待...")
    
    trainer = AutoLoRATrainer(user_id=USER_ID)
    
    # 直接使用我们准备好的对话数据
    from torch.utils.data import Dataset
    dataset = trainer.prepare_dataset(unique_conversations)
    
    print(f"   训练数据集大小: {len(dataset)}")
    
    # 开始训练
    model_path = trainer.train_lora(dataset)
    
    # 更新状态
    trainer.status['last_training_time'] = __import__('datetime').datetime.now().isoformat()
    trainer.status['model_version'] += 1
    trainer.status['training_samples'] = len(unique_conversations)
    trainer.save_status()
    
    # 5. 显示结果
    print(f"\n" + "="*80)
    print(f"训练完成！")
    print(f"="*80)
    print(f"模型版本: v{trainer.status['model_version']}")
    print(f"训练数据量: {len(unique_conversations)} 对对话")
    print(f"模型保存位置: {model_path}")
    
    print(f"\n✅ 现在可以使用决策模拟功能了！")
    print(f"💡 LoRA 模型会根据你的对话风格和偏好生成个性化的决策分析")
    
except ImportError as e:
    print(f"\n❌ 导入失败: {e}")
    print(f"\n💡 请确保已安装所有依赖:")
    print(f"   pip install torch transformers peft")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"\n❌ 训练失败: {e}")
    import traceback
    traceback.print_exc()
