"""
检查用户的 LoRA 训练状态
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def check_user_lora(user_id: str):
    """检查指定用户的 LoRA 状态"""
    print("="*80)
    print(f"检查用户 LoRA 状态: {user_id}")
    print("="*80)
    
    # 1. 检查状态文件
    status_file = f"backend/data/lora_status/{user_id}_status.json"
    print(f"\n1. 检查状态文件: {status_file}")
    
    if os.path.exists(status_file):
        print(f"   ✅ 状态文件存在")
        with open(status_file, 'r', encoding='utf-8') as f:
            status = json.load(f)
        print(f"   模型版本: v{status.get('model_version', 0)}")
        print(f"   训练样本数: {status.get('training_samples', 0)}")
        print(f"   最后训练时间: {status.get('last_training_time', 'N/A')}")
    else:
        print(f"   ❌ 状态文件不存在")
    
    # 2. 检查模型文件
    model_dir = f"./models/lora/{user_id}"
    print(f"\n2. 检查模型目录: {model_dir}")
    
    if os.path.exists(model_dir):
        print(f"   ✅ 模型目录存在")
        
        # 列出所有版本
        versions = []
        for item in os.listdir(model_dir):
            version_path = os.path.join(model_dir, item)
            if os.path.isdir(version_path) and item.startswith('v'):
                versions.append(item)
        
        if versions:
            print(f"   可用版本: {', '.join(sorted(versions))}")
            
            # 检查最新版本
            latest_version = sorted(versions)[-1]
            latest_path = os.path.join(model_dir, latest_version, 'final')
            
            if os.path.exists(latest_path):
                print(f"   ✅ 最新模型: {latest_version}/final")
                
                # 列出模型文件
                model_files = os.listdir(latest_path)
                print(f"   模型文件数: {len(model_files)}")
                
                # 检查关键文件
                key_files = ['adapter_config.json', 'adapter_model.safetensors']
                for key_file in key_files:
                    if key_file in model_files:
                        print(f"      ✅ {key_file}")
                    else:
                        print(f"      ❌ {key_file} 缺失")
            else:
                print(f"   ❌ 最新模型路径不存在: {latest_path}")
        else:
            print(f"   ⚠️ 没有找到任何版本")
    else:
        print(f"   ❌ 模型目录不存在")
    
    # 3. 检查对话数据
    print(f"\n3. 检查对话数据")
    try:
        from backend.conversation.conversation_storage import ConversationStorage
        storage = ConversationStorage()
        sessions = storage.get_user_sessions(user_id)
        
        print(f"   会话数: {len(sessions)}")
        
        total_messages = 0
        for session in sessions:
            messages = storage.get_session_messages(user_id, session['id'])
            total_messages += len(messages)
        
        print(f"   总消息数: {total_messages}")
        print(f"   对话对数: {total_messages // 2}")
        
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
    
    # 4. 总结
    print(f"\n" + "="*80)
    print(f"总结")
    print(f"="*80)
    
    has_status = os.path.exists(status_file)
    has_model = os.path.exists(model_dir)
    
    if has_status and has_model:
        print(f"✅ 用户 {user_id} 的 LoRA 模型已就绪")
        print(f"💡 可以使用决策模拟功能")
    elif has_model:
        print(f"⚠️ 模型存在但状态文件缺失")
        print(f"💡 可以尝试使用，但建议重新训练")
    else:
        print(f"❌ 用户 {user_id} 还没有训练 LoRA 模型")
        print(f"💡 请先运行: python train_lora_unified.py")

if __name__ == "__main__":
    # 检查所有可能的用户
    users = [
        "2c2139f7-bab4-483d-9882-ae83ce8734cd",  # 你的真实用户ID
        "default_user"  # 默认用户ID
    ]
    
    for user_id in users:
        check_user_lora(user_id)
        print("\n")
