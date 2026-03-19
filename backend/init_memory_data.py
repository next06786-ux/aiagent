"""
初始化历史记忆测试数据
为第2层历史记忆检索系统添加真实的测试数据
"""

from llm.enhanced_memory_retriever import get_enhanced_memory_retriever, MemoryType
from datetime import datetime, timedelta
import random


def init_memory_data(user_id: str = "test_user"):
    """初始化记忆数据"""
    print(f"🔧 正在为用户 {user_id} 初始化历史记忆数据...")
    
    retriever = get_enhanced_memory_retriever(user_id)
    
    # 1. 对话记忆
    conversation_memories = [
        {
            "content": "用户询问如何提高学习效率，我建议使用番茄工作法和间隔重复",
            "metadata": {"domain": "学习", "topic": "学习方法"},
            "importance": 0.8,
            "days_ago": 3
        },
        {
            "content": "用户反馈最近睡眠质量不好，经常失眠，我建议调整作息时间",
            "metadata": {"domain": "健康", "topic": "睡眠"},
            "importance": 0.9,
            "days_ago": 5
        },
        {
            "content": "用户提到工作压力大，感觉时间不够用，我建议做时间管理和优先级排序",
            "metadata": {"domain": "时间", "topic": "时间管理"},
            "importance": 0.85,
            "days_ago": 7
        },
        {
            "content": "用户询问如何改善人际关系，我建议多倾听、少评判，增加共情能力",
            "metadata": {"domain": "社交", "topic": "人际关系"},
            "importance": 0.75,
            "days_ago": 10
        },
        {
            "content": "用户分享了今天的运动数据，跑步5公里，感觉很好",
            "metadata": {"domain": "健康", "topic": "运动"},
            "importance": 0.6,
            "days_ago": 1
        },
        {
            "content": "用户询问如何控制消费，我建议记账和设定预算",
            "metadata": {"domain": "财务", "topic": "理财"},
            "importance": 0.7,
            "days_ago": 14
        },
        {
            "content": "用户反馈情绪低落，我建议进行户外活动和社交互动",
            "metadata": {"domain": "情绪", "topic": "情绪管理"},
            "importance": 0.85,
            "days_ago": 2
        },
        {
            "content": "用户询问数学数列问题，我详细讲解了等差数列和等比数列的性质",
            "metadata": {"domain": "学习", "topic": "数学"},
            "importance": 0.8,
            "days_ago": 4
        },
        {
            "content": "用户分享了今天的饮食记录，摄入热量偏高，我建议调整饮食结构",
            "metadata": {"domain": "健康", "topic": "饮食"},
            "importance": 0.65,
            "days_ago": 1
        },
        {
            "content": "用户询问如何提高专注力，我建议减少干扰源和使用专注力训练APP",
            "metadata": {"domain": "学习", "topic": "专注力"},
            "importance": 0.75,
            "days_ago": 6
        }
    ]
    
    for mem in conversation_memories:
        # 计算时间戳
        timestamp = datetime.now() - timedelta(days=mem["days_ago"])
        
        # 创建记忆对象并手动设置时间戳
        memory_id = retriever.add_memory(
            memory_type=MemoryType.CONVERSATION,
            content=mem["content"],
            metadata=mem["metadata"],
            importance=mem["importance"]
        )
        
        # 更新时间戳
        memory_obj = retriever.memory_index[memory_id]
        memory_obj.timestamp = timestamp
        
        print(f"  ✓ 添加对话记忆: {mem['content'][:30]}... (重要性: {mem['importance']}, {mem['days_ago']}天前)")
    
    # 2. 决策记忆
    decision_memories = [
        {
            "content": "决策：晚上10点前睡觉 -> 结果：睡眠质量提升，第二天精神状态好",
            "metadata": {"domain": "健康", "decision_type": "作息调整", "outcome": "positive"},
            "importance": 0.9,
            "days_ago": 8
        },
        {
            "content": "决策：每天运动30分钟 -> 结果：体重下降2kg，体能提升",
            "metadata": {"domain": "健康", "decision_type": "运动计划", "outcome": "positive"},
            "importance": 0.85,
            "days_ago": 15
        },
        {
            "content": "决策：使用番茄工作法学习 -> 结果：学习效率提升30%",
            "metadata": {"domain": "学习", "decision_type": "学习方法", "outcome": "positive"},
            "importance": 0.8,
            "days_ago": 12
        },
        {
            "content": "决策：减少社交媒体使用时间 -> 结果：专注力提升，焦虑感降低",
            "metadata": {"domain": "时间", "decision_type": "时间管理", "outcome": "positive"},
            "importance": 0.75,
            "days_ago": 20
        },
        {
            "content": "决策：每周记账一次 -> 结果：消费意识提高，储蓄增加",
            "metadata": {"domain": "财务", "decision_type": "理财习惯", "outcome": "positive"},
            "importance": 0.7,
            "days_ago": 25
        }
    ]
    
    for mem in decision_memories:
        timestamp = datetime.now() - timedelta(days=mem["days_ago"])
        
        memory_id = retriever.add_memory(
            memory_type=MemoryType.DECISION,
            content=mem["content"],
            metadata=mem["metadata"],
            importance=mem["importance"]
        )
        
        memory_obj = retriever.memory_index[memory_id]
        memory_obj.timestamp = timestamp
        
        print(f"  ✓ 添加决策记忆: {mem['content'][:30]}... (重要性: {mem['importance']}, {mem['days_ago']}天前)")
    
    # 3. 洞察记忆
    insight_memories = [
        {
            "content": "洞察：睡眠不足会导致第二天的学习效率下降50%以上",
            "metadata": {"domain": "健康", "insight_type": "因果关系"},
            "importance": 0.95,
            "days_ago": 10
        },
        {
            "content": "洞察：运动后的心情明显比运动前好，可能是内啡肽的作用",
            "metadata": {"domain": "健康", "insight_type": "模式发现"},
            "importance": 0.85,
            "days_ago": 18
        },
        {
            "content": "洞察：工作时间超过8小时后，效率会急剧下降，不如早点休息",
            "metadata": {"domain": "时间", "insight_type": "效率规律"},
            "importance": 0.9,
            "days_ago": 22
        },
        {
            "content": "洞察：与朋友交流后，压力感会明显降低，社交对情绪健康很重要",
            "metadata": {"domain": "社交", "insight_type": "情绪影响"},
            "importance": 0.8,
            "days_ago": 16
        }
    ]
    
    for mem in insight_memories:
        timestamp = datetime.now() - timedelta(days=mem["days_ago"])
        
        memory_id = retriever.add_memory(
            memory_type=MemoryType.INSIGHT,
            content=mem["content"],
            metadata=mem["metadata"],
            importance=mem["importance"]
        )
        
        memory_obj = retriever.memory_index[memory_id]
        memory_obj.timestamp = timestamp
        
        print(f"  ✓ 添加洞察记忆: {mem['content'][:30]}... (重要性: {mem['importance']}, {mem['days_ago']}天前)")
    
    # 4. 模式记忆
    pattern_memories = [
        {
            "content": "模式：每周一的工作效率最低，可能是周末休息后的适应期",
            "metadata": {"domain": "时间", "pattern_type": "周期性"},
            "importance": 0.75,
            "days_ago": 30
        },
        {
            "content": "模式：晚上11点后学习效果很差，容易遗忘，不如早上学习",
            "metadata": {"domain": "学习", "pattern_type": "时间规律"},
            "importance": 0.8,
            "days_ago": 28
        },
        {
            "content": "模式：连续工作2小时后需要休息15分钟，否则注意力会分散",
            "metadata": {"domain": "时间", "pattern_type": "工作节奏"},
            "importance": 0.85,
            "days_ago": 35
        }
    ]
    
    for mem in pattern_memories:
        timestamp = datetime.now() - timedelta(days=mem["days_ago"])
        
        memory_id = retriever.add_memory(
            memory_type=MemoryType.PATTERN,
            content=mem["content"],
            metadata=mem["metadata"],
            importance=mem["importance"]
        )
        
        memory_obj = retriever.memory_index[memory_id]
        memory_obj.timestamp = timestamp
        
        print(f"  ✓ 添加模式记忆: {mem['content'][:30]}... (重要性: {mem['importance']}, {mem['days_ago']}天前)")
    
    # 获取统计信息
    stats = retriever.get_memory_statistics()
    
    print(f"\n✅ 记忆数据初始化完成！")
    print(f"   总记忆数: {stats['total_memories']}")
    print(f"   对话记忆: {stats['memory_types']['conversation']}")
    print(f"   决策记忆: {stats['memory_types']['decision']}")
    print(f"   洞察记忆: {stats['memory_types']['insight']}")
    print(f"   模式记忆: {stats['memory_types']['pattern']}")
    print(f"   平均重要性: {stats['average_importance']:.2f}")
    
    return retriever


def test_memory_retrieval(user_id: str = "test_user"):
    """测试记忆检索"""
    print(f"\n🧪 测试记忆检索功能...")
    
    retriever = get_enhanced_memory_retriever(user_id)
    
    print(f"   当前记忆总数: {len(retriever.memories)}")
    
    if len(retriever.memories) == 0:
        print(f"   ⚠️  记忆库为空，请先运行 init_memory_data()")
        return
    
    # 测试1：相似度检索
    print(f"\n1️⃣ 测试相似度检索 - 查询: '如何提高学习效率'")
    results = retriever.retrieve_by_similarity("如何提高学习效率", top_k=3)
    if results:
        for i, (memory, score) in enumerate(results, 1):
            print(f"   {i}. [{memory.memory_type.value}] {memory.content[:50]}... (分数: {score:.3f})")
    else:
        print(f"   未找到相关记忆")
    
    # 测试2：按类型检索
    print(f"\n2️⃣ 测试按类型检索 - 类型: DECISION")
    results = retriever.retrieve_by_type(MemoryType.DECISION, top_k=3)
    if results:
        for i, memory in enumerate(results, 1):
            print(f"   {i}. {memory.content[:50]}... (重要性: {memory.importance})")
    else:
        print(f"   未找到决策记忆")
    
    # 测试3：重要记忆检索
    print(f"\n3️⃣ 测试重要记忆检索")
    results = retriever.retrieve_important_memories(top_k=5)
    if results:
        for i, memory in enumerate(results, 1):
            print(f"   {i}. [{memory.memory_type.value}] {memory.content[:50]}... (重要性: {memory.importance})")
    else:
        print(f"   未找到重要记忆")
    
    # 测试4：按领域检索
    print(f"\n4️⃣ 测试按领域检索 - 领域: 健康")
    results = retriever.retrieve_by_metadata("domain", "健康", top_k=3)
    if results:
        for i, memory in enumerate(results, 1):
            print(f"   {i}. {memory.content[:50]}... (重要性: {memory.importance})")
    else:
        print(f"   未找到健康领域记忆")
    
    print(f"\n✅ 测试完成！")


if __name__ == "__main__":
    # 初始化数据
    retriever = init_memory_data("test_user")
    
    # 测试检索
    test_memory_retrieval("test_user")
