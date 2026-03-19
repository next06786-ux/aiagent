"""
为测试用户创建对话数据
用于测试 LoRA 训练
"""
import sys
sys.path.append('backend')

from learning.production_rag_system import ProductionRAGSystem, MemoryType
from datetime import datetime

def create_test_conversations():
    """创建测试对话数据"""
    
    user_id = "test_user_001"
    
    print("=" * 60)
    print(f"为用户 {user_id} 创建测试对话数据")
    print("=" * 60)
    print()
    
    # 创建 RAG 系统
    print("初始化 RAG 系统...")
    rag = ProductionRAGSystem(user_id, use_gpu=True)
    
    # 测试对话数据（至少 20 条）
    conversations = [
        ("你好", "你好！很高兴见到你。我是你的个人 AI 助手，有什么可以帮你的吗？"),
        ("我今天心情不太好", "我理解你的感受。能告诉我发生了什么吗？我会认真倾听的。"),
        ("工作压力太大了", "工作压力确实会让人感到疲惫。你可以试着休息一下，或者和我聊聊具体是什么让你感到压力？"),
        ("我想学习 Python", "很好的选择！Python 是一门非常实用的编程语言。你想从哪里开始学习呢？"),
        ("推荐一些学习资源", "我推荐你从 Python 官方教程开始，然后可以看看《Python 编程：从入门到实践》这本书。"),
        ("如何提高工作效率", "提高工作效率可以从时间管理开始，比如使用番茄工作法，每25分钟专注工作，然后休息5分钟。"),
        ("我想锻炼身体", "很好的决定！规律运动对身心健康都有好处。你想尝试什么类型的运动呢？"),
        ("推荐一些运动方式", "可以从简单的开始，比如每天快走30分钟，或者尝试瑜伽、游泳等。关键是找到你喜欢的方式。"),
        ("如何保持健康饮食", "健康饮食的关键是均衡营养，多吃蔬菜水果，适量摄入蛋白质，少吃油腻和高糖食物。"),
        ("我想提升沟通能力", "沟通能力很重要。可以从倾听开始，理解对方的观点，然后清晰表达自己的想法。"),
        ("如何管理时间", "时间管理可以用四象限法则：重要紧急的优先做，重要不紧急的计划做，不重要的尽量少做。"),
        ("推荐一些好书", "根据你的兴趣，我推荐《人类简史》、《思考，快与慢》、《原则》等经典书籍。"),
        ("如何缓解焦虑", "焦虑时可以尝试深呼吸、冥想，或者做一些让你放松的事情，比如听音乐、散步。"),
        ("我想学习新技能", "很好！学习新技能能让人保持活力。你对什么领域感兴趣呢？"),
        ("如何提高专注力", "提高专注力可以尝试：1) 减少干扰 2) 设定明确目标 3) 使用番茄工作法 4) 保证充足睡眠。"),
        ("推荐一些音乐", "根据不同场景，工作时可以听轻音乐或白噪音，放松时可以听古典音乐或爵士乐。"),
        ("如何建立好习惯", "建立习惯需要：1) 从小习惯开始 2) 每天坚持 3) 设置提醒 4) 奖励自己。"),
        ("我想旅行", "旅行是很好的放松方式！你想去哪里呢？我可以帮你规划行程。"),
        ("如何学习英语", "学习英语可以：1) 每天背单词 2) 看英文电影 3) 练习口语 4) 阅读英文文章。"),
        ("推荐一些电影", "根据你的喜好，我推荐《肖申克的救赎》、《阿甘正传》、《盗梦空间》等经典电影。"),
        ("如何提高记忆力", "提高记忆力可以：1) 充足睡眠 2) 规律运动 3) 使用记忆技巧 4) 保持大脑活跃。"),
        ("我想创业", "创业是个勇敢的决定！你有什么想法吗？我可以帮你分析一下。"),
        ("如何理财", "理财的基本原则是：1) 记账 2) 储蓄 3) 分散投资 4) 学习理财知识。"),
        ("推荐一些课程", "根据你的需求，可以看看 Coursera、edX 等平台上的课程，内容丰富且质量高。"),
        ("如何保持动力", "保持动力需要：1) 设定清晰目标 2) 庆祝小成就 3) 找到意义 4) 与他人分享进展。"),
    ]
    
    print(f"准备添加 {len(conversations)} 条对话...")
    print()
    
    # 添加对话到 RAG 系统
    for i, (user_msg, ai_msg) in enumerate(conversations, 1):
        content = f"用户: {user_msg}\nAI: {ai_msg}"
        
        # 使用 ProductionRAGSystem 的 add_memory 方法
        rag.add_memory(
            memory_type=MemoryType.CONVERSATION,
            content=content,
            metadata={"conversation_id": f"test_{i}"},
            importance=0.8
        )
        print(f"  [{i}/{len(conversations)}] 已添加: {user_msg[:30]}...")
    
    print()
    print("=" * 60)
    print(f"✅ 成功为用户 {user_id} 创建 {len(conversations)} 条对话")
    print("=" * 60)
    print()
    
    # 显示统计信息
    stats = rag.get_statistics()
    print(f"📊 统计信息:")
    print(f"   总记忆数: {stats['total_memories']}")
    print(f"   对话记忆: {stats['by_type']['conversation']}")
    print()
    print("现在可以运行: python test_lora_training.py")
    print()


if __name__ == "__main__":
    create_test_conversations()
