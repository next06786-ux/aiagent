"""
测试数据初始化脚本
创建100+个测试用例，包括：
- 用户数据
- 对话历史
- 知识图谱（人物关系、教育、职业）
- RAG记忆
"""
import sys
import os
from datetime import datetime, timedelta
import random
import hashlib

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.db_manager import db_manager
from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType
from backend.conversation.conversation_storage import ConversationStorage


def hash_password(password: str) -> str:
    """生成密码哈希（简单的SHA256，实际应用应使用bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()


# ==================== 测试数据模板 ====================

# 测试用户
TEST_USERS = [
    {
        "user_id": "test_user_001",
        "username": "张三",
        "email": "zhangsan@example.com",
        "password": "123456",  # 测试密码
        "age": 22,
        "gender": "male",
        "university": "清华大学",
        "major": "计算机科学"
    },
    {
        "user_id": "test_user_002", 
        "username": "李四",
        "email": "lisi@example.com",
        "password": "123456",  # 测试密码
        "age": 21,
        "gender": "female",
        "university": "北京大学",
        "major": "人工智能"
    },
    {
        "user_id": "test_user_003",
        "username": "王五",
        "email": "wangwu@example.com",
        "password": "123456",  # 测试密码
        "age": 23,
        "gender": "male",
        "university": "上海交通大学",
        "major": "软件工程"
    }
]

# 人物关系数据
RELATIONSHIPS = [
    # 家人
    {"name": "张父", "type": "Person", "category": "family", "relation": "父亲", "attributes": {"age": 50, "occupation": "工程师"}},
    {"name": "张母", "type": "Person", "category": "family", "relation": "母亲", "attributes": {"age": 48, "occupation": "教师"}},
    {"name": "张妹", "type": "Person", "category": "family", "relation": "妹妹", "attributes": {"age": 18, "school": "高中"}},
    
    # 好友
    {"name": "赵六", "type": "Person", "category": "close_friends", "relation": "室友", "attributes": {"university": "清华大学", "major": "电子工程"}},
    {"name": "孙七", "type": "Person", "category": "close_friends", "relation": "高中同学", "attributes": {"university": "浙江大学"}},
    {"name": "周八", "type": "Person", "category": "friends", "relation": "社团朋友", "attributes": {"hobby": "篮球"}},
    
    # 导师和同事
    {"name": "李教授", "type": "Person", "category": "mentors", "relation": "导师", "attributes": {"title": "教授", "research": "机器学习"}},
    {"name": "陈老师", "type": "Person", "category": "mentors", "relation": "辅导员", "attributes": {"department": "学生处"}},
    {"name": "刘学长", "type": "Person", "category": "colleagues", "relation": "实验室学长", "attributes": {"grade": "研三"}},
]

# 教育经历
EDUCATION_HISTORY = [
    {"school": "清华大学", "degree": "本科", "major": "计算机科学", "start_year": 2020, "end_year": 2024, "gpa": 3.8},
    {"school": "北京四中", "degree": "高中", "major": "理科", "start_year": 2017, "end_year": 2020, "score": 650},
]

# 技能数据
SKILLS = [
    {"name": "Python", "level": "精通", "years": 3, "projects": 10},
    {"name": "机器学习", "level": "熟练", "years": 2, "projects": 5},
    {"name": "深度学习", "level": "了解", "years": 1, "projects": 2},
    {"name": "Java", "level": "熟练", "years": 2, "projects": 8},
    {"name": "前端开发", "level": "了解", "years": 1, "projects": 3},
    {"name": "数据库", "level": "熟练", "years": 2, "projects": 6},
]

# 职业目标
CAREER_GOALS = [
    {"position": "算法工程师", "company": "字节跳动", "priority": "高", "timeline": "2024年"},
    {"position": "后端工程师", "company": "腾讯", "priority": "中", "timeline": "2024年"},
    {"position": "AI研究员", "company": "阿里巴巴", "priority": "中", "timeline": "2025年"},
]

# 对话历史模板
CONVERSATION_TEMPLATES = [
    # 学习相关
    "我最近在学习深度学习，有什么好的资源推荐吗？",
    "今天完成了机器学习作业，感觉收获很大",
    "准备考研，需要制定一个学习计划",
    "导师让我读一篇关于Transformer的论文",
    
    # 职业规划
    "我想了解算法工程师的职业发展路径",
    "字节跳动的面试流程是怎样的？",
    "需要准备哪些技能才能进入大厂？",
    "实习经历对找工作有多重要？",
    
    # 人际关系
    "今天和室友一起打篮球，很开心",
    "导师给了我很多建设性的建议",
    "周末和高中同学聚会",
    "参加了学校的技术分享会，认识了很多朋友",
    
    # 生活日常
    "今天天气不错，去图书馆学习了一天",
    "晚上和朋友一起吃火锅",
    "周末计划去爬山",
    "最近压力有点大，需要放松一下",
]


# ==================== 初始化函数 ====================

def init_users():
    """初始化测试用户"""
    print("\n" + "="*60)
    print("1. 初始化测试用户")
    print("="*60)
    
    from backend.database.models import User
    
    session = db_manager.get_session()
    
    try:
        for user in TEST_USERS:
            try:
                # 检查用户是否已存在
                existing_user = session.query(User).filter(
                    (User.username == user["username"]) | (User.email == user["email"])
                ).first()
                
                if existing_user:
                    print(f"⚠ 用户已存在: {user['username']} (ID: {existing_user.id})")
                    # 更新user_id映射，以便后续使用
                    user["user_id"] = existing_user.id
                    continue
                
                # 生成密码哈希
                password_hash = hash_password(user["password"])
                
                # 创建新用户
                new_user = User(
                    id=user["user_id"],
                    username=user["username"],
                    email=user["email"],
                    password_hash=password_hash,
                    nickname=user["username"],
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                session.add(new_user)
                session.commit()
                
                print(f"✓ 创建用户: {user['username']} (ID: {user['user_id']}) - 密码: {user['password']}")
                
            except Exception as e:
                session.rollback()
                print(f"✗ 创建用户失败 {user['username']}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ 完成：处理了 {len(TEST_USERS)} 个测试用户")
        
    finally:
        session.close()


def init_knowledge_graph():
    """初始化知识图谱数据"""
    print("\n" + "="*60)
    print("2. 初始化知识图谱数据")
    print("="*60)
    
    total_nodes = 0
    total_relations = 0
    
    for user in TEST_USERS:
        user_id = user["user_id"]
        print(f"\n为用户 {user['username']} 创建知识图谱...")
        
        try:
            kg = InformationKnowledgeGraph(user_id)
            
            # 创建人物关系
            print(f"  创建人物关系...")
            for person in RELATIONSHIPS:
                kg.add_information(
                    name=person["name"],
                    info_type="entity",
                    category=person["category"],
                    confidence=0.9,
                    attributes={
                        "entity_type": person["type"],
                        **person["attributes"]
                    }
                )
                
                # 创建关系
                kg.add_user_relationship(
                    target_name=person["name"],
                    relation_type="KNOWS",
                    properties={
                        "relationship_type": person["category"],
                        "relation": person["relation"],
                        "closeness": 0.8 if person["category"] in ["family", "close_friends"] else 0.5
                    }
                )
                total_nodes += 1
                total_relations += 1
            
            # 创建教育经历
            print(f"  创建教育经历...")
            for edu in EDUCATION_HISTORY:
                kg.add_information(
                    name=edu["school"],
                    info_type="entity",
                    category="education",
                    confidence=1.0,
                    attributes={
                        "entity_type": "School",
                        "degree": edu["degree"],
                        "major": edu["major"],
                        "start_year": edu["start_year"],
                        "end_year": edu["end_year"],
                        "gpa": edu.get("gpa", 0)
                    }
                )
                total_nodes += 1
            
            # 创建技能
            print(f"  创建技能...")
            for skill in SKILLS:
                kg.add_information(
                    name=skill["name"],
                    info_type="concept",
                    category="skill",
                    confidence=0.9,
                    attributes={
                        "concept_type": "Skill",
                        "level": skill["level"],
                        "years": skill["years"],
                        "projects": skill["projects"]
                    }
                )
                
                kg.add_user_relationship(
                    target_name=skill["name"],
                    relation_type="HAS_PROFILE",
                    properties={
                        "level": skill["level"],
                        "confidence": 0.9
                    }
                )
                total_nodes += 1
                total_relations += 1
            
            # 创建职业目标
            print(f"  创建职业目标...")
            for goal in CAREER_GOALS:
                kg.add_information(
                    name=f"{goal['company']}-{goal['position']}",
                    info_type="concept",
                    category="career_goal",
                    confidence=0.8,
                    attributes={
                        "concept_type": "Goal",
                        "position": goal["position"],
                        "company": goal["company"],
                        "priority": goal["priority"],
                        "timeline": goal["timeline"]
                    }
                )
                
                kg.add_user_relationship(
                    target_name=f"{goal['company']}-{goal['position']}",
                    relation_type="INTERESTED_IN",
                    properties={
                        "interest_level": 0.8,
                        "priority": goal["priority"]
                    }
                )
                total_nodes += 1
                total_relations += 1
            
            kg.close()
            print(f"  ✓ 完成用户 {user['username']} 的知识图谱")
            
        except Exception as e:
            print(f"  ✗ 创建知识图谱失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ 完成：创建了 {total_nodes} 个节点，{total_relations} 个关系")


def init_conversations():
    """初始化对话历史"""
    print("\n" + "="*60)
    print("3. 初始化对话历史")
    print("="*60)
    
    total_conversations = 0
    
    for user in TEST_USERS:
        user_id = user["user_id"]
        session_id = f"session_{user_id}_init"
        
        print(f"\n为用户 {user['username']} 创建对话历史...")
        
        # 创建20条对话
        for i in range(20):
            try:
                # 用户消息
                user_message = random.choice(CONVERSATION_TEMPLATES)
                ConversationStorage.save_message(
                    user_id=user_id,
                    session_id=session_id,
                    role="user",
                    content=user_message
                )
                
                # AI回复（简单模拟）
                ai_response = f"我理解你的问题。{random.choice(['这是一个很好的想法', '我建议你可以', '根据你的情况'])}"
                ConversationStorage.save_message(
                    user_id=user_id,
                    session_id=session_id,
                    role="assistant",
                    content=ai_response
                )
                
                total_conversations += 2
                
            except Exception as e:
                print(f"  ✗ 创建对话失败: {e}")
        
        print(f"  ✓ 创建了 20 轮对话")
    
    print(f"\n✅ 完成：创建了 {total_conversations} 条对话记录")


def init_rag_memories():
    """初始化RAG记忆"""
    print("\n" + "="*60)
    print("4. 初始化RAG记忆系统")
    print("="*60)
    
    total_memories = 0
    
    for user in TEST_USERS:
        user_id = user["user_id"]
        
        print(f"\n为用户 {user['username']} 创建RAG记忆...")
        
        try:
            rag = ProductionRAGSystem(user_id=user_id, use_gpu=False)
            
            # 对话记忆
            for template in CONVERSATION_TEMPLATES[:10]:
                rag.add_memory(
                    memory_type=MemoryType.CONVERSATION,
                    content=template,
                    metadata={"user_id": user_id, "source": "init_script"},
                    importance=0.7
                )
                total_memories += 1
            
            # 知识记忆
            for skill in SKILLS:
                rag.add_memory(
                    memory_type=MemoryType.KNOWLEDGE,
                    content=f"掌握{skill['name']}技能，水平：{skill['level']}",
                    metadata={"user_id": user_id, "category": "skill", "level": skill['level']},
                    importance=0.8
                )
                total_memories += 1
            
            # 经验记忆
            experiences = [
                "参加了学校的算法竞赛，获得了二等奖",
                "完成了一个机器学习项目，效果不错",
                "在实验室做了一个月的研究助理",
            ]
            for exp in experiences:
                rag.add_memory(
                    memory_type=MemoryType.EXPERIENCE,
                    content=exp,
                    metadata={"user_id": user_id, "domain": "education"},
                    importance=0.75
                )
                total_memories += 1
            
            print(f"  ✓ 创建了 {len(CONVERSATION_TEMPLATES[:10]) + len(SKILLS) + len(experiences)} 条记忆")
            
        except Exception as e:
            print(f"  ✗ 创建RAG记忆失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ 完成：创建了 {total_memories} 条RAG记忆")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("测试数据初始化脚本")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 初始化用户
        init_users()
        
        # 2. 初始化知识图谱
        init_knowledge_graph()
        
        # 3. 初始化对话历史
        init_conversations()
        
        # 4. 初始化RAG记忆
        init_rag_memories()
        
        print("\n" + "="*60)
        print("✅ 所有测试数据初始化完成！")
        print("="*60)
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n测试用户账号（密码统一为: 123456）：")
        for user in TEST_USERS:
            print(f"  - 用户名: {user['username']}")
            print(f"    User ID: {user['user_id']}")
            print(f"    邮箱: {user['email']}")
            print(f"    密码: {user['password']}")
            print(f"    学校: {user['university']} - {user['major']}")
            print()
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
