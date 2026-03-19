"""
检查用户的对话数据
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

USER_ID = "a113a299-ecff-4363-8d44-aff979dfc547"

print("="*80)
print(f"检查用户对话数据 - {USER_ID}")
print("="*80)

try:
    from backend.conversation.conversation_storage import ConversationStorage
    
    storage = ConversationStorage()
    
    # 1. 获取会话列表
    print("\n1. 数据库会话:")
    sessions = storage.get_user_sessions(USER_ID)
    print(f"   会话数: {len(sessions)}")
    
    total_messages = 0
    for i, session in enumerate(sessions, 1):
        print(f"\n   会话 {i}:")
        print(f"   - ID: {session['id']}")
        print(f"   - 标题: {session['title']}")
        print(f"   - 消息数: {session['message_count']}")
        
        messages = storage.get_session_messages(USER_ID, session['id'])
        total_messages += len(messages)
        
        print(f"   - 消息:")
        for msg in messages[:5]:  # 只显示前5条
            print(f"     {msg['role']}: {msg['content'][:50]}...")
    
    print(f"\n   总消息数: {total_messages}")
    print(f"   对话对数: {total_messages // 2}")
    
    # 2. 检查 RAG 系统
    print("\n2. RAG 系统记忆:")
    try:
        from learning.production_rag_system import ProductionRAGSystem
        
        rag = ProductionRAGSystem(USER_ID)
        memories = rag.get_all_memories()
        
        conversation_memories = [m for m in memories if m.memory_type.value == "conversation"]
        
        print(f"   总记忆数: {len(memories)}")
        print(f"   对话记忆数: {len(conversation_memories)}")
        
        if conversation_memories:
            print(f"\n   对话记忆示例:")
            for mem in conversation_memories[:3]:
                print(f"   - {mem.content[:100]}...")
    
    except Exception as e:
        print(f"   ⚠️ RAG 系统检查失败: {e}")
    
    print(f"\n" + "="*80)
    print("检查完成")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
