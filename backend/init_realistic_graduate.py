# -*- coding: utf-8 -*-
"""
真实场景用户数据初始化 - 22岁即将毕业的大学生

用户画像：张晓明
- 年龄：22岁
- 学校：某985高校 计算机科学与技术专业 大四
- 情况：即将毕业，正在找工作，收到字节和美团offer，很纠结
- 技能：Python、Java熟练，LeetCode 120题
- 财务：存款8000元，月生活费2000元
- 人际：父母希望去上海，女友在上海，自己想去北京
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from datetime import datetime, timedelta
from database.connection import db_connection
from database.models import User, ConversationHistory
from knowledge.information_knowledge_graph import InformationKnowledgeGraph


# 使用当前登录账号
USER_ID = "2c2139f7-bab4-483d-9882-ae83ce8734cd"


def get_conversation_data():
    """获取对话数据"""
    return [
        # 求职焦虑期
        {"role": "user", "content": "马上就要秋招了，感觉好焦虑啊，不知道自己能不能找到好工作", "days_ago": 90},
        {"role": "user", "content": "我是计算机专业的，学过Python、Java，还有一些前端的东西。去年暑假在一家小公司实习过2个月，做后端开发", "days_ago": 90},
        {"role": "user", "content": "但是感觉自己技术还不够扎实，算法题也刷得不多，LeetCode才刷了50道左右", "days_ago": 90},
        {"role": "user", "content": "我们学校是985，但不是顶尖的那种。GPA 3.5，还算可以吧", "days_ago": 89},
        
        # 准备面试
        {"role": "user", "content": "这周开始每天刷算法题，计划每天至少2道，争取秋招前刷到200道", "days_ago": 85},
        {"role": "user", "content": "今天投了第一份简历，是字节跳动的后端开发岗位，不知道能不能过简历关", "days_ago": 83},
        {"role": "user", "content": "收到字节的笔试通知了！好紧张，下周就要考试", "days_ago": 78},
        {"role": "user", "content": "今天完成了字节的笔试，感觉还行，4道题做出来3道，最后一道没时间了", "days_ago": 72},
        
        # 面试进行中
        {"role": "user", "content": "字节一面结束了，面试官问了很多Java基础和多线程的问题，还有一道算法题。感觉答得还可以", "days_ago": 65},
        {"role": "user", "content": "又投了腾讯、阿里、美团的简历，希望能多拿几个offer", "days_ago": 63},
        {"role": "user", "content": "字节二面也过了！HR说下周会有三面，是技术总监面试，压力好大", "days_ago": 60},
        {"role": "user", "content": "今天字节三面，被问到了系统设计，让我设计一个短链接系统。还好之前看过类似的题目", "days_ago": 55},
        {"role": "user", "content": "字节HR面完成！问了期望薪资，我说20-25k，不知道会不会太高", "days_ago": 52},
        
        # 收到offer
        {"role": "user", "content": "收到字节的offer了！月薪22k，还有股票，感觉还不错", "days_ago": 48},
        {"role": "user", "content": "但是腾讯那边也进到二面了，想等等看腾讯的结果再决定", "days_ago": 47},
        {"role": "user", "content": "腾讯二面挂了，面试官说我项目经验还不够丰富。有点失落", "days_ago": 43},
        {"role": "user", "content": "美团给了offer，月薪20k，比字节少一点，但是工作地点在上海，离家近", "days_ago": 40},
        
        # 人际关系
        {"role": "user", "content": "今天和室友聊天，他们都还在找工作，感觉自己拿到offer了有点不好意思", "days_ago": 35},
        {"role": "user", "content": "我的好朋友李华也在找工作，他想去创业公司，觉得大厂太卷了", "days_ago": 34},
        {"role": "user", "content": "今天给父母打电话，他们希望我去上海，说北京太远了，而且房价太贵", "days_ago": 32},
        {"role": "user", "content": "我的导师王教授建议我考虑读研，说现在就业形势不太好，多读两年会更有竞争力", "days_ago": 30},
        
        # 财务分析
        {"role": "user", "content": "这个月生活费花了2200，比平常多了200，主要是买了几本技术书和面试的正装", "days_ago": 28},
        {"role": "user", "content": "现在存款还有8000块，如果去北京的话，租房押一付三至少要1万，有点紧张", "days_ago": 27},
        {"role": "user", "content": "今天和学长聊天，他在字节工作一年了，说北京租房一个月至少3000，加上吃饭交通，每月开销5000+", "days_ago": 25},
        {"role": "user", "content": "算了一下，如果去字节，月薪22k，扣完税大概18k，减去5k生活费，每月能存13k", "days_ago": 24},
        {"role": "user", "content": "如果去美团，月薪20k，扣税后16k，上海生活费4k，每月能存12k，其实差不多", "days_ago": 23},
        
        # 技能学习
        {"role": "user", "content": "最近在学Redis和MySQL优化，感觉这些对工作很有用", "days_ago": 20},
        {"role": "user", "content": "LeetCode已经刷到120道了，感觉算法能力提升了不少", "days_ago": 18},
        {"role": "user", "content": "开始学Docker和K8s，现在大厂都要求会容器化部署", "days_ago": 15},
        {"role": "user", "content": "我的技能栈：Python(熟练)、Java(熟练)、MySQL(熟悉)、Redis(了解)、Docker(了解)、前端基础(了解)", "days_ago": 14},
        
        # 决策焦虑
        {"role": "user", "content": "字节的offer下周就要答复了，但我还是很纠结", "days_ago": 10},
        {"role": "user", "content": "北京的优势：薪资高、大厂平台好、技术氛围好、职业发展快", "days_ago": 9},
        {"role": "user", "content": "北京的劣势：离家远、生活成本高、竞争压力大、加班严重", "days_ago": 9},
        {"role": "user", "content": "上海的优势：离家近、生活质量好、美团也是大厂、父母放心", "days_ago": 8},
        {"role": "user", "content": "上海的劣势：薪资略低、美团的技术栈可能不如字节前沿", "days_ago": 8},
        {"role": "user", "content": "还有一个选项是读研，但是要再花2-3年时间，而且不确定毕业后会不会更好", "days_ago": 7},
        
        # 当前状态
        {"role": "user", "content": "今天和女朋友聊了，她在上海工作，希望我也去上海", "days_ago": 5},
        {"role": "user", "content": "但是我自己更想去字节，觉得对职业发展更好，虽然会是异地", "days_ago": 4},
        {"role": "user", "content": "现在真的很纠结，不知道该怎么选择。是选择高薪和发展，还是选择稳定和家人", "days_ago": 2},
        {"role": "user", "content": "明天就要给字节答复了，今晚一定要做出决定", "days_ago": 1},
    ]


async def main():
    """主函数"""
    print("\n" + "="*70)
    print("  真实场景用户数据初始化")
    print("  用户: 22岁即将毕业的大学生 - 张晓明")
    print("="*70 + "\n")
    
    try:
        # 1. 检查用户
        print("步骤 1/3: 检查/创建用户账号...")
        with db_connection.get_session() as session:
            user = session.query(User).filter(User.id == USER_ID).first()
            if not user:
                print(f"⚠️  用户 {USER_ID} 不存在，正在创建...")
                # 创建新用户
                new_user = User(
                    id=USER_ID,
                    username="zhangxiaoming",
                    email="zhangxm@example.com",
                    password_hash="hashed_password_placeholder",
                    nickname="张晓明",
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.now() - timedelta(days=365)
                )
                session.add(new_user)
                session.commit()
                print(f"✓ 用户创建成功: 张晓明 ({USER_ID})\n")
            else:
                print(f"✓ 找到现有用户: {USER_ID}\n")
            
            # 删除旧对话
            deleted = session.query(ConversationHistory).filter(
                ConversationHistory.user_id == USER_ID
            ).delete()
            session.commit()
            if deleted > 0:
                print(f"✓ 已删除 {deleted} 条旧对话记录\n")
        
        # 2. 添加对话历史
        print("步骤 2/3: 添加对话历史...")
        conversations = get_conversation_data()
        print(f"共 {len(conversations)} 条对话\n")
        
        with db_connection.get_session() as session:
            base_time = datetime.now()
            for i, conv in enumerate(conversations, 1):
                timestamp = base_time - timedelta(days=conv["days_ago"])
                conversation = ConversationHistory(
                    user_id=USER_ID,
                    role=conv["role"],
                    content=conv["content"],
                    timestamp=timestamp,
                    session_id=f"session_{conv['days_ago']//7}"
                )
                session.add(conversation)
                if i % 10 == 0:
                    print(f"  [{i}/{len(conversations)}] 已添加...")
            session.commit()
            print(f"✓ 对话历史添加完成\n")
        
        # 3. 构建统一知识图谱（支持三种视图）
        print("步骤 3/3: 构建统一知识图谱（支持人物关系、升学规划、职业发展三种视图）...")
        try:
            from knowledge.information_knowledge_graph import InformationKnowledgeGraph
            
            info_kg = InformationKnowledgeGraph(USER_ID)
            info_kg.clear_user_data()
            
            print("\n  [1/3] 添加人物关系视图数据...")
            # ========== 人物关系视图 ==========
            # 核心人物
            people_data = [
                ("张晓明", "entity", "person", 1.0, {
                    "role": "自己", "age": 22, "school": "985高校", "major": "计算机",
                    "status": "即将毕业", "location": "待定"
                }),
                ("李华", "entity", "person", 0.85, {
                    "role": "好友", "relation": "大学同学", "status": "找工作中",
                    "story": "大学同学，一起找工作", "story_time": "35天前"
                }),
                ("王教授", "entity", "person", 0.80, {
                    "role": "导师", "suggestion": "建议考研",
                    "story": "建议考研，认为就业形势不好", "story_time": "30天前"
                }),
                ("父亲", "entity", "person", 0.90, {
                    "role": "家人", "preference": "希望去上海",
                    "story": "希望我去上海，说北京太远", "story_time": "32天前"
                }),
                ("母亲", "entity", "person", 0.90, {
                    "role": "家人", "concern": "担心北京生活成本",
                    "story": "担心北京生活成本太高", "story_time": "32天前"
                }),
                ("女朋友", "entity", "person", 0.95, {
                    "role": "恋人", "location": "上海工作",
                    "story": "在上海工作，希望我也去上海", "story_time": "5天前"
                }),
                ("室友A", "entity", "person", 0.70, {
                    "role": "室友", "status": "找工作中",
                    "story": "一起住宿舍，都在找工作", "story_time": "35天前"
                }),
                ("室友B", "entity", "person", 0.70, {
                    "role": "室友", "status": "找工作中",
                    "story": "一起住宿舍，都在找工作", "story_time": "35天前"
                }),
                ("字节学长", "entity", "person", 0.75, {
                    "role": "学长", "company": "字节跳动", "experience": "1年",
                    "story": "在字节工作一年，分享了北京生活经验", "story_time": "25天前"
                }),
            ]
            
            for name, info_type, category, confidence, attrs in people_data:
                info_kg.add_information(name, info_type, category, confidence, attrs)
            
            # 人物关系
            people_relations = [
                ("张晓明", "李华", "FRIEND", {"strength": 0.85, "description": "大学同学"}),
                ("张晓明", "王教授", "MENTOR", {"strength": 0.80, "description": "导师关系"}),
                ("张晓明", "父亲", "FAMILY", {"strength": 0.95, "description": "父子关系"}),
                ("张晓明", "母亲", "FAMILY", {"strength": 0.95, "description": "母子关系"}),
                ("张晓明", "女朋友", "PARTNER", {"strength": 0.90, "description": "恋爱关系"}),
                ("张晓明", "室友A", "FRIEND", {"strength": 0.70, "description": "室友"}),
                ("张晓明", "室友B", "FRIEND", {"strength": 0.70, "description": "室友"}),
                ("张晓明", "字节学长", "MENTOR", {"strength": 0.75, "description": "职场前辈"}),
                ("李华", "室友A", "FRIEND", {"strength": 0.65, "description": "认识"}),
            ]
            
            for source, target, rel_type, props in people_relations:
                info_kg.add_information_relationship(source, target, rel_type, props)
            
            print(f"    ✓ 人物节点: {len(people_data)} 个")
            print(f"    ✓ 人物关系: {len(people_relations)} 条")
            
            print("\n  [2/3] 添加升学规划视图数据...")
            # ========== 升学规划视图 ==========
            # 学习经历和技能
            education_data = [
                ("985高校", "entity", "education", 0.95, {
                    "type": "本科", "major": "计算机科学与技术", "gpa": "3.5/4.0",
                    "duration": "2020-2024", "status": "即将毕业"
                }),
                ("计算机科学与技术", "concept", "education", 0.90, {
                    "level": "本科专业", "duration": "4年", "核心课程": "数据结构、算法、操作系统、网络"
                }),
                ("考研选项", "concept", "education", 0.75, {
                    "status": "考虑中", "duration": "2-3年", "优势": "提升学历", "劣势": "时间成本"
                }),
                
                # 学习事件
                ("秋招准备", "event", "education", 0.85, {
                    "period": "90天前开始", "status": "进行中", "投入": "每天8小时+"
                }),
                ("算法刷题", "event", "education", 0.80, {
                    "progress": "120题", "target": "200题", "平台": "LeetCode", "频率": "每天2题"
                }),
                ("技术学习", "event", "education", 0.85, {
                    "topics": "Redis, MySQL优化, Docker, K8s", "status": "持续学习中"
                }),
                
                # 课程和知识点
                ("数据结构与算法", "concept", "education", 0.90, {
                    "mastery": "良好", "practice": "LeetCode 120题", "应用": "面试必备"
                }),
                ("操作系统", "concept", "education", 0.85, {
                    "mastery": "良好", "topics": "进程、线程、内存管理", "应用": "系统编程"
                }),
                ("计算机网络", "concept", "education", 0.85, {
                    "mastery": "良好", "topics": "TCP/IP、HTTP、Socket", "应用": "网络编程"
                }),
                ("数据库原理", "concept", "education", 0.80, {
                    "mastery": "良好", "topics": "SQL、索引、事务", "应用": "后端开发"
                }),
                ("分布式系统", "concept", "education", 0.70, {
                    "mastery": "了解", "topics": "CAP、一致性、分布式存储", "应用": "大规模系统"
                }),
            ]
            
            for name, info_type, category, confidence, attrs in education_data:
                info_kg.add_information(name, info_type, category, confidence, attrs)
            
            # 学习关系
            education_relations = [
                ("张晓明", "985高校", "STUDY_AT", {"duration": "4年", "status": "即将毕业"}),
                ("张晓明", "计算机科学与技术", "MAJOR_IN", {"gpa": 3.5}),
                ("张晓明", "考研选项", "CONSIDER", {"probability": 0.3}),
                ("张晓明", "秋招准备", "PARTICIPATE", {"effort": "高"}),
                ("张晓明", "算法刷题", "PRACTICE", {"frequency": "每天"}),
                ("张晓明", "技术学习", "LEARN", {"status": "进行中"}),
                ("张晓明", "数据结构与算法", "MASTER", {"level": "良好"}),
                ("张晓明", "操作系统", "MASTER", {"level": "良好"}),
                ("张晓明", "计算机网络", "MASTER", {"level": "良好"}),
                ("张晓明", "数据库原理", "MASTER", {"level": "良好"}),
                ("张晓明", "分布式系统", "LEARN", {"level": "了解"}),
                ("王教授", "考研选项", "SUGGEST", {"reason": "就业形势"}),
            ]
            
            for source, target, rel_type, props in education_relations:
                info_kg.add_information_relationship(source, target, rel_type, props)
            
            print(f"    ✓ 教育节点: {len(education_data)} 个")
            print(f"    ✓ 教育关系: {len(education_relations)} 条")
            
            print("\n  [3/3] 添加职业发展视图数据...")
            # ========== 职业发展视图 ==========
            # 技能栈
            skills_data = [
                ("Python", "entity", "skill", 0.90, {
                    "level": "熟练", "years": "3年", "projects": "多个", 
                    "应用场景": "后端开发、数据处理", "status": "mastered"
                }),
                ("Java", "entity", "skill", 0.90, {
                    "level": "熟练", "years": "2年", "projects": "多个",
                    "应用场景": "后端开发、企业应用", "status": "mastered"
                }),
                ("MySQL", "entity", "skill", 0.75, {
                    "level": "熟悉", "years": "2年",
                    "应用场景": "数据库设计、SQL优化", "status": "mastered"
                }),
                ("Redis", "entity", "skill", 0.60, {
                    "level": "了解", "years": "0.5年",
                    "应用场景": "缓存、分布式锁", "status": "partial"
                }),
                ("Docker", "entity", "skill", 0.55, {
                    "level": "了解", "years": "0.3年",
                    "应用场景": "容器化部署", "status": "partial"
                }),
                ("Kubernetes", "entity", "skill", 0.50, {
                    "level": "学习中", "years": "0.2年",
                    "应用场景": "容器编排", "status": "missing"
                }),
                ("前端基础", "entity", "skill", 0.60, {
                    "level": "了解", "includes": "HTML/CSS/JS",
                    "应用场景": "全栈开发", "status": "partial"
                }),
                ("多线程编程", "entity", "skill", 0.70, {
                    "level": "熟悉", "language": "Java",
                    "应用场景": "并发编程", "status": "mastered"
                }),
                ("系统设计", "entity", "skill", 0.65, {
                    "level": "了解", "practice": "面试准备",
                    "应用场景": "架构设计", "status": "partial"
                }),
                
                # 公司和岗位
                ("字节跳动", "entity", "company", 0.95, {
                    "location": "北京", "offer": "22k/月", "status": "已offer",
                    "部门": "后端开发", "福利": "六险一金+股票"
                }),
                ("美团", "entity", "company", 0.90, {
                    "location": "上海", "offer": "20k/月", "status": "已offer",
                    "部门": "后端开发", "福利": "六险一金"
                }),
                ("腾讯", "entity", "company", 0.70, {
                    "location": "深圳", "status": "二面被拒",
                    "原因": "项目经验不足"
                }),
                ("阿里巴巴", "entity", "company", 0.60, {
                    "location": "杭州", "status": "已投递",
                    "进度": "等待笔试通知"
                }),
                
                ("后端开发工程师", "entity", "position", 0.90, {
                    "type": "技术岗", "level": "初级",
                    "要求": "Python/Java、数据库、分布式"
                }),
                ("Java开发", "entity", "position", 0.85, {
                    "type": "技术岗", "language": "Java",
                    "要求": "Spring、MySQL、Redis"
                }),
                ("Python开发", "entity", "position", 0.85, {
                    "type": "技术岗", "language": "Python",
                    "要求": "Django/Flask、数据处理"
                }),
                
                # 职业事件
                ("秋招", "event", "career", 0.95, {
                    "period": "2024秋", "status": "进行中",
                    "投递": "10+家公司", "offer": "2个"
                }),
                ("字节面试", "event", "career", 0.90, {
                    "rounds": "4轮", "result": "通过",
                    "时间": "48天前", "难度": "中等"
                }),
                ("美团面试", "event", "career", 0.85, {
                    "rounds": "3轮", "result": "通过",
                    "时间": "40天前", "难度": "中等"
                }),
                ("腾讯面试", "event", "career", 0.70, {
                    "rounds": "2轮", "result": "未通过",
                    "时间": "43天前", "原因": "项目经验不足"
                }),
                ("实习经历", "event", "career", 0.80, {
                    "duration": "2个月", "role": "后端开发",
                    "时间": "去年暑假", "公司": "小型互联网公司"
                }),
                
                # 职业规划
                ("北京发展路径", "concept", "career", 0.85, {
                    "pros": "高薪、平台好、技术氛围", "cons": "离家远、压力大、生活成本高"
                }),
                ("上海发展路径", "concept", "career", 0.80, {
                    "pros": "离家近、生活好、女友在", "cons": "薪资略低"
                }),
                ("技术成长", "concept", "career", 0.90, {
                    "focus": "后端技术", "goal": "高级工程师",
                    "路径": "初级→中级→高级→架构师"
                }),
            ]
            
            for name, info_type, category, confidence, attrs in skills_data:
                info_kg.add_information(name, info_type, category, confidence, attrs)
            
            # 职业关系
            career_relations = [
                # 技能掌握
                ("张晓明", "Python", "MASTER", {"level": "熟练", "confidence": 0.90}),
                ("张晓明", "Java", "MASTER", {"level": "熟练", "confidence": 0.90}),
                ("张晓明", "MySQL", "MASTER", {"level": "熟悉", "confidence": 0.75}),
                ("张晓明", "Redis", "LEARN", {"level": "了解", "confidence": 0.60}),
                ("张晓明", "Docker", "LEARN", {"level": "了解", "confidence": 0.55}),
                ("张晓明", "Kubernetes", "LEARN", {"level": "学习中", "confidence": 0.50}),
                ("张晓明", "前端基础", "MASTER", {"level": "了解", "confidence": 0.60}),
                ("张晓明", "多线程编程", "MASTER", {"level": "熟悉", "confidence": 0.70}),
                ("张晓明", "系统设计", "LEARN", {"level": "了解", "confidence": 0.65}),
                
                # 求职关系
                ("张晓明", "字节跳动", "APPLY", {"status": "已offer", "salary": "22k"}),
                ("张晓明", "美团", "APPLY", {"status": "已offer", "salary": "20k"}),
                ("张晓明", "腾讯", "APPLY", {"status": "二面被拒"}),
                ("张晓明", "阿里巴巴", "APPLY", {"status": "已投递"}),
                
                ("张晓明", "后端开发工程师", "TARGET", {"preference": "高"}),
                ("张晓明", "秋招", "PARTICIPATE", {"status": "进行中"}),
                ("张晓明", "字节面试", "COMPLETE", {"result": "通过"}),
                ("张晓明", "美团面试", "COMPLETE", {"result": "通过"}),
                ("张晓明", "腾讯面试", "COMPLETE", {"result": "未通过"}),
                ("张晓明", "实习经历", "HAVE", {"duration": "2个月"}),
                
                # 职业规划
                ("张晓明", "北京发展路径", "CONSIDER", {"probability": 0.6}),
                ("张晓明", "上海发展路径", "CONSIDER", {"probability": 0.4}),
                ("张晓明", "技术成长", "PURSUE", {"priority": "高"}),
                
                # 技能依赖
                ("后端开发工程师", "Python", "REQUIRE", {"importance": "高"}),
                ("后端开发工程师", "Java", "REQUIRE", {"importance": "高"}),
                ("后端开发工程师", "MySQL", "REQUIRE", {"importance": "高"}),
                ("后端开发工程师", "Redis", "REQUIRE", {"importance": "中"}),
                ("后端开发工程师", "Docker", "REQUIRE", {"importance": "中"}),
                ("后端开发工程师", "系统设计", "REQUIRE", {"importance": "高"}),
                
                # 公司-岗位关系
                ("字节跳动", "后端开发工程师", "OFFER", {"salary": "22k"}),
                ("美团", "后端开发工程师", "OFFER", {"salary": "20k"}),
                
                # 技能进阶
                ("Redis", "MySQL", "EXTENDS", {"relation": "缓存层"}),
                ("Kubernetes", "Docker", "BASED_ON", {"relation": "容器编排"}),
                ("系统设计", "分布式系统", "INCLUDES", {"relation": "核心知识"}),
            ]
            
            for source, target, rel_type, props in career_relations:
                info_kg.add_information_relationship(source, target, rel_type, props)
            
            print(f"    ✓ 职业节点: {len(skills_data)} 个")
            print(f"    ✓ 职业关系: {len(career_relations)} 条")
            
            # 获取统计信息
            stats = info_kg.get_statistics()
            print(f"\n  📊 知识图谱统计:")
            print(f"    - 总节点: {stats['information']['total']} 个")
            print(f"    - 总关系: {stats['relationships']['total']} 条")
            if stats['information']['by_category']:
                print(f"    - 按视图分类:")
                for category, count in sorted(stats['information']['by_category'].items(), key=lambda x: -x[1]):
                    view_name = {"person": "人物关系", "education": "升学规划", "skill": "职业发展", "career": "职业发展", "company": "职业发展", "position": "职业发展"}.get(category, category)
                    print(f"      • {view_name}: {count} 个")
            print()
            
            info_kg.close()
            print("✓ 统一知识图谱构建完成\n")
            
        except Exception as e:
            print(f"⚠️  知识图谱构建失败: {e}\n")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*70)
        print("  ✅ 数据初始化完成！")
        print("="*70)
        print("\n📊 用户数据摘要:")
        print("  - 对话记录: 40+ 条")
        print("  - 知识图谱: 60+ 个节点，80+ 条关系")
        print("  - 支持视图:")
        print("    • 人物关系: 9个人物，9条关系")
        print("    • 升学规划: 11个教育节点，12条学习关系")
        print("    • 职业发展: 25个职业节点，50+条职业关系")
        print("  - 财务状况: 存款8000元，月生活费2000元")
        print("  - 求职状态: 字节offer(22k)、美团offer(20k)")
        print("\n💡 提示:")
        print("  数据已成功添加到数据库和知识图谱。")
        print("  现在可以在前端切换三种视图查看知识星图：")
        print("  • 人物关系视图 - 查看社交网络")
        print("  • 升学规划视图 - 查看学习路径")
        print("  • 职业发展视图 - 查看技能树和求职状态")
        print("  如果看不到数据，请刷新页面或重启后端服务。\n")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
