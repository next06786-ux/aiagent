"""
将数据库中的对话历史迁移到RAG系统
用于LoRA训练
"""
import sys
from backend.database.connection import db_connection
from backend.database.models import ConversationHistory
from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType
from sqlalchemy import func

def migrate_user_conversations(user_id: str):
    """迁移指定用户的对话到RAG系统"""
    print(f"\n{'='*80}")
    print(f"迁移用户 {user_id} 的对话到RAG系统")
    print(f"{'='*80}\n")
    
    db = None
    try:
        # 连接数据库
        db = db_connection.get_session()
        print("✓ 数据库连接已建立")
        
        # 获取用户的所有会话
        sessions = db.query(ConversationHistory.session_id).filter(
            ConversationHistory.user_id == user_id
        ).distinct().all()
        
        session_ids = [s.session_id for s in sessions]
        print(f"✓ 找到 {len(session_ids)} 个会话")
        
        if not session_ids:
            print("❌ 没有找到对话历史")
            return
        
        # 初始化RAG系统
        rag = ProductionRAGSystem(user_id)
        print("✓ RAG系统已初始化")
        
        # 统计
        total_pairs = 0
        migrated_pairs = 0
        
        # 遍历每个会话
        for session_id in session_ids:
            print(f"\n处理会话: {session_id}")
            
            # 获取会话的所有消息，按时间排序
            messages = db.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.session_id == session_id
            ).order_by(ConversationHistory.timestamp.asc()).all()
            
            # 配对用户消息和AI回复
            i = 0
            while i < len(messages) - 1:
                if messages[i].role == 'user' and messages[i+1].role == 'assistant':
                    user_msg = messages[i].content
                    ai_msg = messages[i+1].content
                    thinking = messages[i+1].thinking
                    timestamp = messages[i].timestamp
                    
                    total_pairs += 1
                    
                    # 保存到RAG系统
                    try:
                        conversation_content = f"用户: {user_msg}\nAI: {ai_msg}"
                        rag.add_memory(
                            memory_type=MemoryType.CONVERSATION,
                            content=conversation_content,
                            metadata={
                                "session_id": session_id,
                                "thinking": thinking,
                                "timestamp": timestamp.isoformat()
                            }
                        )
                        migrated_pairs += 1
                        print(f"  ✓ 迁移对话对 {migrated_pairs}/{total_pairs}")
                    except Exception as e:
                        print(f"  ✗ 迁移失败: {e}")
                    
                    i += 2  # 跳过这一对
                else:
                    i += 1  # 继续查找
        
        print(f"\n{'='*80}")
        print(f"迁移完成！")
        print(f"{'='*80}")
        print(f"总对话对数: {total_pairs}")
        print(f"成功迁移: {migrated_pairs}")
        print(f"失败: {total_pairs - migrated_pairs}")
        
        # 验证RAG系统中的数据
        memories = rag.get_all_memories()
        conversation_count = sum(1 for m in memories if m.memory_type.value == "conversation")
        print(f"\nRAG系统中的对话数: {conversation_count}")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        # 默认使用最新注册的用户
        user_id = "a113a299-ecff-4363-8d44-aff979dfc547"
    
    migrate_user_conversations(user_id)
