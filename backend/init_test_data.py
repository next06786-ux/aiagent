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

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.db_manager import db_manager
from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
from backend.learning.production_rag_system import ProductionRAGSystem, MemoryType
from backend.conversation.conversation_storage import ConversationStorage
from backend.auth.auth_service import get_auth_service


def hash_password(password: str) -> str:
    """生成密码哈希（使用bcrypt）"""
    auth_service = get_auth_service()
    return auth_service.hash_password(password)


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

# 人物关系数据（大幅扩充）
RELATIONSHIPS = [
    # 家人 (10人)
    {"name": "张父", "type": "Person", "category": "family", "relation": "父亲", "attributes": {"age": 50, "occupation": "软件工程师", "company": "华为"}},
    {"name": "张母", "type": "Person", "category": "family", "relation": "母亲", "attributes": {"age": 48, "occupation": "中学教师", "subject": "数学"}},
    {"name": "张妹", "type": "Person", "category": "family", "relation": "妹妹", "attributes": {"age": 18, "school": "北京四中", "grade": "高三"}},
    {"name": "张爷爷", "type": "Person", "category": "family", "relation": "爷爷", "attributes": {"age": 75, "retired": True, "hobby": "书法"}},
    {"name": "张奶奶", "type": "Person", "category": "family", "relation": "奶奶", "attributes": {"age": 73, "retired": True, "hobby": "园艺"}},
    {"name": "张姑姑", "type": "Person", "category": "family", "relation": "姑姑", "attributes": {"age": 45, "occupation": "医生", "hospital": "协和医院"}},
    {"name": "张叔叔", "type": "Person", "category": "family", "relation": "叔叔", "attributes": {"age": 42, "occupation": "创业者", "industry": "互联网"}},
    {"name": "李舅舅", "type": "Person", "category": "family", "relation": "舅舅", "attributes": {"age": 46, "occupation": "大学教授", "university": "北京大学"}},
    {"name": "王表哥", "type": "Person", "category": "family", "relation": "表哥", "attributes": {"age": 28, "occupation": "算法工程师", "company": "字节跳动"}},
    {"name": "李表妹", "type": "Person", "category": "family", "relation": "表妹", "attributes": {"age": 20, "university": "复旦大学", "major": "金融"}},
    
    # 亲密好友 (15人)
    {"name": "赵六", "type": "Person", "category": "close_friends", "relation": "室友", "attributes": {"university": "清华大学", "major": "电子工程", "hobby": "游戏"}},
    {"name": "孙七", "type": "Person", "category": "close_friends", "relation": "高中同学", "attributes": {"university": "浙江大学", "major": "计算机", "city": "杭州"}},
    {"name": "钱小明", "type": "Person", "category": "close_friends", "relation": "发小", "attributes": {"university": "北京大学", "major": "物理", "hobby": "摄影"}},
    {"name": "周小红", "type": "Person", "category": "close_friends", "relation": "高中同桌", "attributes": {"university": "上海交大", "major": "自动化", "city": "上海"}},
    {"name": "吴大伟", "type": "Person", "category": "close_friends", "relation": "初中同学", "attributes": {"university": "南京大学", "major": "软件工程", "hobby": "篮球"}},
    {"name": "郑小芳", "type": "Person", "category": "close_friends", "relation": "社团好友", "attributes": {"university": "清华大学", "major": "自动化", "club": "机器人社"}},
    {"name": "王建国", "type": "Person", "category": "close_friends", "relation": "竞赛队友", "attributes": {"university": "清华大学", "major": "计算机", "competition": "ACM"}},
    {"name": "刘思思", "type": "Person", "category": "close_friends", "relation": "项目伙伴", "attributes": {"university": "清华大学", "major": "软件工程", "project": "AI助手"}},
    {"name": "陈浩然", "type": "Person", "category": "close_friends", "relation": "健身伙伴", "attributes": {"university": "北京体育大学", "major": "运动科学", "hobby": "健身"}},
    {"name": "林雨欣", "type": "Person", "category": "close_friends", "relation": "学习小组", "attributes": {"university": "清华大学", "major": "数学", "gpa": 3.9}},
    {"name": "黄志强", "type": "Person", "category": "close_friends", "relation": "创业伙伴", "attributes": {"university": "清华大学", "major": "工商管理", "startup": "教育科技"}},
    {"name": "张丽娜", "type": "Person", "category": "close_friends", "relation": "支教队友", "attributes": {"university": "北京师范大学", "major": "教育学", "volunteer": True}},
    {"name": "马云飞", "type": "Person", "category": "close_friends", "relation": "乐队成员", "attributes": {"university": "中央音乐学院", "instrument": "吉他", "band": "校园乐队"}},
    {"name": "徐静蕾", "type": "Person", "category": "close_friends", "relation": "辩论队友", "attributes": {"university": "清华大学", "major": "法学", "debate": True}},
    {"name": "何俊杰", "type": "Person", "category": "close_friends", "relation": "游戏队友", "attributes": {"university": "电子科技大学", "major": "游戏设计", "game": "王者荣耀"}},
    
    # 普通朋友 (20人)
    {"name": "周八", "type": "Person", "category": "friends", "relation": "社团朋友", "attributes": {"hobby": "篮球", "university": "清华大学"}},
    {"name": "冯九", "type": "Person", "category": "friends", "relation": "班级同学", "attributes": {"major": "计算机", "hobby": "动漫"}},
    {"name": "陈十", "type": "Person", "category": "friends", "relation": "图书馆常客", "attributes": {"major": "数学", "hobby": "阅读"}},
    {"name": "杨小军", "type": "Person", "category": "friends", "relation": "食堂饭友", "attributes": {"major": "物理", "hobby": "美食"}},
    {"name": "赵小丽", "type": "Person", "category": "friends", "relation": "选修课同学", "attributes": {"major": "经济", "course": "心理学"}},
    {"name": "孙大鹏", "type": "Person", "category": "friends", "relation": "宿舍楼友", "attributes": {"major": "化学", "floor": 5}},
    {"name": "李小花", "type": "Person", "category": "friends", "relation": "志愿者", "attributes": {"major": "社会学", "volunteer": "敬老院"}},
    {"name": "王大锤", "type": "Person", "category": "friends", "relation": "健身房", "attributes": {"major": "体育", "gym": "校体育馆"}},
    {"name": "张小龙", "type": "Person", "category": "friends", "relation": "网球搭档", "attributes": {"major": "建筑", "sport": "网球"}},
    {"name": "刘小雨", "type": "Person", "category": "friends", "relation": "摄影社", "attributes": {"major": "艺术", "club": "摄影社"}},
    {"name": "陈小春", "type": "Person", "category": "friends", "relation": "音乐节", "attributes": {"major": "音乐", "hobby": "摇滚"}},
    {"name": "黄小明", "type": "Person", "category": "friends", "relation": "电影社", "attributes": {"major": "传媒", "club": "电影社"}},
    {"name": "吴小波", "type": "Person", "category": "friends", "relation": "跑步群", "attributes": {"major": "医学", "hobby": "马拉松"}},
    {"name": "郑小燕", "type": "Person", "category": "friends", "relation": "书法社", "attributes": {"major": "中文", "club": "书法社"}},
    {"name": "周小伟", "type": "Person", "category": "friends", "relation": "围棋社", "attributes": {"major": "哲学", "club": "围棋社"}},
    {"name": "冯小刚", "type": "Person", "category": "friends", "relation": "话剧社", "attributes": {"major": "戏剧", "club": "话剧社"}},
    {"name": "林小东", "type": "Person", "category": "friends", "relation": "创客空间", "attributes": {"major": "机械", "makerspace": True}},
    {"name": "马小云", "type": "Person", "category": "friends", "relation": "创业沙龙", "attributes": {"major": "管理", "startup": "咨询"}},
    {"name": "徐小凤", "type": "Person", "category": "friends", "relation": "英语角", "attributes": {"major": "外语", "language": "英语"}},
    {"name": "何小鹏", "type": "Person", "category": "friends", "relation": "科技论坛", "attributes": {"major": "电子", "tech": "硬件"}},
    
    # 导师和老师 (10人)
    {"name": "李教授", "type": "Person", "category": "mentors", "relation": "导师", "attributes": {"title": "教授", "research": "机器学习", "papers": 50}},
    {"name": "陈老师", "type": "Person", "category": "mentors", "relation": "辅导员", "attributes": {"department": "学生处", "experience": 10}},
    {"name": "王教授", "type": "Person", "category": "mentors", "relation": "课程老师", "attributes": {"title": "副教授", "course": "算法设计", "rating": 4.8}},
    {"name": "赵博士", "type": "Person", "category": "mentors", "relation": "实验室导师", "attributes": {"title": "博士后", "research": "深度学习", "lab": "AI实验室"}},
    {"name": "孙教授", "type": "Person", "category": "mentors", "relation": "毕设导师", "attributes": {"title": "教授", "research": "计算机视觉", "students": 15}},
    {"name": "周老师", "type": "Person", "category": "mentors", "relation": "班主任", "attributes": {"department": "计算机系", "class": "计科1班"}},
    {"name": "吴教授", "type": "Person", "category": "mentors", "relation": "学术顾问", "attributes": {"title": "教授", "research": "自然语言处理", "h_index": 30}},
    {"name": "郑老师", "type": "Person", "category": "mentors", "relation": "职业导师", "attributes": {"company": "腾讯", "position": "技术总监", "mentor": True}},
    {"name": "冯博士", "type": "Person", "category": "mentors", "relation": "科研合作", "attributes": {"title": "研究员", "institute": "中科院", "project": "国家重点"}},
    {"name": "林教授", "type": "Person", "category": "mentors", "relation": "学术交流", "attributes": {"title": "教授", "university": "MIT", "visiting": True}},
    
    # 同事和学长 (15人)
    {"name": "刘学长", "type": "Person", "category": "colleagues", "relation": "实验室学长", "attributes": {"grade": "研三", "research": "强化学习"}},
    {"name": "张学姐", "type": "Person", "category": "colleagues", "relation": "实验室学姐", "attributes": {"grade": "研二", "research": "图神经网络"}},
    {"name": "王学长", "type": "Person", "category": "colleagues", "relation": "项目组长", "attributes": {"grade": "博二", "project": "智能推荐"}},
    {"name": "赵学姐", "type": "Person", "category": "colleagues", "relation": "论文合作", "attributes": {"grade": "博三", "papers": 5}},
    {"name": "孙学长", "type": "Person", "category": "colleagues", "relation": "代码审查", "attributes": {"grade": "研三", "github": "10k stars"}},
    {"name": "周学姐", "type": "Person", "category": "colleagues", "relation": "实习同事", "attributes": {"company": "字节跳动", "team": "推荐系统"}},
    {"name": "吴学长", "type": "Person", "category": "colleagues", "relation": "竞赛教练", "attributes": {"competition": "Kaggle", "rank": "Master"}},
    {"name": "郑学姐", "type": "Person", "category": "colleagues", "relation": "开源贡献", "attributes": {"project": "PyTorch", "commits": 100}},
    {"name": "冯学长", "type": "Person", "category": "colleagues", "relation": "技术分享", "attributes": {"blog": "CSDN", "followers": 5000}},
    {"name": "林学姐", "type": "Person", "category": "colleagues", "relation": "读书会", "attributes": {"books": 50, "club": "技术读书会"}},
    {"name": "马学长", "type": "Person", "category": "colleagues", "relation": "创业前辈", "attributes": {"startup": "AI公司", "funding": "A轮"}},
    {"name": "徐学姐", "type": "Person", "category": "colleagues", "relation": "面试辅导", "attributes": {"company": "阿里巴巴", "offers": 3}},
    {"name": "何学长", "type": "Person", "category": "colleagues", "relation": "职业规划", "attributes": {"company": "Google", "position": "SDE"}},
    {"name": "黄学姐", "type": "Person", "category": "colleagues", "relation": "留学咨询", "attributes": {"university": "Stanford", "phd": True}},
    {"name": "杨学长", "type": "Person", "category": "colleagues", "relation": "技术交流", "attributes": {"company": "微软", "team": "Azure"}},
]

# 教育经历（扩充）
EDUCATION_HISTORY = [
    {"school": "清华大学", "degree": "本科", "major": "计算机科学与技术", "start_year": 2020, "end_year": 2024, "gpa": 3.8},
    {"school": "北京四中", "degree": "高中", "major": "理科实验班", "start_year": 2017, "end_year": 2020, "score": 680},
    {"school": "海淀实验小学", "degree": "小学", "major": "全科", "start_year": 2011, "end_year": 2017, "score": 95},
    {"school": "斯坦福大学", "degree": "交换生", "major": "人工智能", "start_year": 2023, "end_year": 2023, "gpa": 4.0},
    {"school": "MIT", "degree": "暑期课程", "major": "深度学习", "start_year": 2022, "end_year": 2022, "gpa": 3.9},
]

# 技能数据（大幅扩充）
SKILLS = [
    # 编程语言 (10个)
    {"name": "Python", "level": "精通", "years": 4, "projects": 20},
    {"name": "Java", "level": "熟练", "years": 3, "projects": 15},
    {"name": "C++", "level": "熟练", "years": 2, "projects": 10},
    {"name": "JavaScript", "level": "熟练", "years": 2, "projects": 12},
    {"name": "Go", "level": "了解", "years": 1, "projects": 5},
    {"name": "Rust", "level": "了解", "years": 1, "projects": 3},
    {"name": "TypeScript", "level": "熟练", "years": 2, "projects": 8},
    {"name": "SQL", "level": "精通", "years": 3, "projects": 15},
    {"name": "Shell", "level": "熟练", "years": 2, "projects": 10},
    {"name": "R", "level": "了解", "years": 1, "projects": 4},
    
    # AI/ML技能 (15个)
    {"name": "机器学习", "level": "精通", "years": 3, "projects": 12},
    {"name": "深度学习", "level": "精通", "years": 2, "projects": 10},
    {"name": "计算机视觉", "level": "熟练", "years": 2, "projects": 8},
    {"name": "自然语言处理", "level": "熟练", "years": 2, "projects": 7},
    {"name": "强化学习", "level": "了解", "years": 1, "projects": 3},
    {"name": "PyTorch", "level": "精通", "years": 2, "projects": 15},
    {"name": "TensorFlow", "level": "熟练", "years": 2, "projects": 10},
    {"name": "Scikit-learn", "level": "精通", "years": 3, "projects": 12},
    {"name": "Keras", "level": "熟练", "years": 2, "projects": 8},
    {"name": "OpenCV", "level": "熟练", "years": 2, "projects": 6},
    {"name": "Transformers", "level": "熟练", "years": 1, "projects": 5},
    {"name": "LangChain", "level": "了解", "years": 1, "projects": 3},
    {"name": "大模型应用", "level": "熟练", "years": 1, "projects": 6},
    {"name": "RAG系统", "level": "熟练", "years": 1, "projects": 4},
    {"name": "向量数据库", "level": "了解", "years": 1, "projects": 3},
    
    # 后端开发 (10个)
    {"name": "FastAPI", "level": "精通", "years": 2, "projects": 10},
    {"name": "Django", "level": "熟练", "years": 2, "projects": 8},
    {"name": "Flask", "level": "熟练", "years": 2, "projects": 7},
    {"name": "Spring Boot", "level": "熟练", "years": 2, "projects": 6},
    {"name": "Node.js", "level": "熟练", "years": 2, "projects": 8},
    {"name": "微服务架构", "level": "了解", "years": 1, "projects": 3},
    {"name": "RESTful API", "level": "精通", "years": 3, "projects": 15},
    {"name": "GraphQL", "level": "了解", "years": 1, "projects": 2},
    {"name": "gRPC", "level": "了解", "years": 1, "projects": 2},
    {"name": "WebSocket", "level": "熟练", "years": 2, "projects": 5},
    
    # 前端开发 (8个)
    {"name": "React", "level": "熟练", "years": 2, "projects": 10},
    {"name": "Vue", "level": "了解", "years": 1, "projects": 5},
    {"name": "HTML/CSS", "level": "熟练", "years": 3, "projects": 15},
    {"name": "Tailwind CSS", "level": "熟练", "years": 1, "projects": 6},
    {"name": "Webpack", "level": "了解", "years": 1, "projects": 4},
    {"name": "Vite", "level": "熟练", "years": 1, "projects": 5},
    {"name": "Three.js", "level": "了解", "years": 1, "projects": 2},
    {"name": "D3.js", "level": "了解", "years": 1, "projects": 3},
    
    # 数据库 (8个)
    {"name": "MySQL", "level": "精通", "years": 3, "projects": 15},
    {"name": "PostgreSQL", "level": "熟练", "years": 2, "projects": 8},
    {"name": "MongoDB", "level": "熟练", "years": 2, "projects": 10},
    {"name": "Redis", "level": "精通", "years": 2, "projects": 12},
    {"name": "Neo4j", "level": "熟练", "years": 1, "projects": 5},
    {"name": "Elasticsearch", "level": "了解", "years": 1, "projects": 3},
    {"name": "FAISS", "level": "熟练", "years": 1, "projects": 4},
    {"name": "Pinecone", "level": "了解", "years": 1, "projects": 2},
    
    # DevOps (10个)
    {"name": "Docker", "level": "精通", "years": 2, "projects": 15},
    {"name": "Kubernetes", "level": "了解", "years": 1, "projects": 3},
    {"name": "Git", "level": "精通", "years": 4, "projects": 30},
    {"name": "GitHub Actions", "level": "熟练", "years": 2, "projects": 8},
    {"name": "Jenkins", "level": "了解", "years": 1, "projects": 2},
    {"name": "Nginx", "level": "熟练", "years": 2, "projects": 10},
    {"name": "Linux", "level": "精通", "years": 3, "projects": 20},
    {"name": "AWS", "level": "了解", "years": 1, "projects": 4},
    {"name": "阿里云", "level": "熟练", "years": 2, "projects": 8},
    {"name": "监控告警", "level": "了解", "years": 1, "projects": 3},
    
    # 软技能 (10个)
    {"name": "算法设计", "level": "精通", "years": 4, "projects": 25},
    {"name": "系统设计", "level": "熟练", "years": 2, "projects": 10},
    {"name": "代码审查", "level": "熟练", "years": 2, "projects": 15},
    {"name": "技术写作", "level": "熟练", "years": 3, "projects": 20},
    {"name": "项目管理", "level": "了解", "years": 1, "projects": 5},
    {"name": "团队协作", "level": "精通", "years": 4, "projects": 30},
    {"name": "敏捷开发", "level": "熟练", "years": 2, "projects": 10},
    {"name": "技术演讲", "level": "熟练", "years": 2, "projects": 8},
    {"name": "开源贡献", "level": "熟练", "years": 2, "projects": 12},
    {"name": "技术博客", "level": "熟练", "years": 3, "projects": 50},
]

# 职业目标（大幅扩充）
CAREER_GOALS = [
    # 国内大厂 (15个)
    {"position": "算法工程师", "company": "字节跳动", "priority": "高", "timeline": "2024年", "salary": "40-60k", "location": "北京"},
    {"position": "后端工程师", "company": "腾讯", "priority": "高", "timeline": "2024年", "salary": "35-55k", "location": "深圳"},
    {"position": "AI研究员", "company": "阿里巴巴", "priority": "中", "timeline": "2024年", "salary": "45-65k", "location": "杭州"},
    {"position": "机器学习工程师", "company": "百度", "priority": "中", "timeline": "2024年", "salary": "35-50k", "location": "北京"},
    {"position": "全栈工程师", "company": "美团", "priority": "中", "timeline": "2024年", "salary": "30-45k", "location": "北京"},
    {"position": "数据科学家", "company": "京东", "priority": "低", "timeline": "2024年", "salary": "30-45k", "location": "北京"},
    {"position": "推荐算法工程师", "company": "快手", "priority": "中", "timeline": "2024年", "salary": "35-50k", "location": "北京"},
    {"position": "NLP工程师", "company": "小米", "priority": "低", "timeline": "2024年", "salary": "28-42k", "location": "北京"},
    {"position": "计算机视觉工程师", "company": "华为", "priority": "中", "timeline": "2024年", "salary": "30-45k", "location": "深圳"},
    {"position": "大数据工程师", "company": "滴滴", "priority": "低", "timeline": "2024年", "salary": "28-40k", "location": "北京"},
    {"position": "搜索算法工程师", "company": "搜狗", "priority": "低", "timeline": "2024年", "salary": "25-38k", "location": "北京"},
    {"position": "广告算法工程师", "company": "拼多多", "priority": "中", "timeline": "2024年", "salary": "35-50k", "location": "上海"},
    {"position": "风控算法工程师", "company": "蚂蚁金服", "priority": "中", "timeline": "2024年", "salary": "40-60k", "location": "杭州"},
    {"position": "语音识别工程师", "company": "科大讯飞", "priority": "低", "timeline": "2024年", "salary": "25-35k", "location": "合肥"},
    {"position": "自动驾驶算法工程师", "company": "小鹏汽车", "priority": "中", "timeline": "2025年", "salary": "35-55k", "location": "广州"},
    
    # 外企 (10个)
    {"position": "Software Engineer", "company": "Google", "priority": "高", "timeline": "2025年", "salary": "60-100k", "location": "美国"},
    {"position": "ML Engineer", "company": "Meta", "priority": "高", "timeline": "2025年", "salary": "55-95k", "location": "美国"},
    {"position": "Research Scientist", "company": "Microsoft", "priority": "中", "timeline": "2025年", "salary": "50-85k", "location": "美国"},
    {"position": "AI Engineer", "company": "Amazon", "priority": "中", "timeline": "2025年", "salary": "50-80k", "location": "美国"},
    {"position": "Data Scientist", "company": "Apple", "priority": "中", "timeline": "2025年", "salary": "55-90k", "location": "美国"},
    {"position": "Backend Engineer", "company": "Netflix", "priority": "低", "timeline": "2025年", "salary": "50-85k", "location": "美国"},
    {"position": "Full Stack Engineer", "company": "Uber", "priority": "低", "timeline": "2025年", "salary": "45-75k", "location": "美国"},
    {"position": "ML Researcher", "company": "OpenAI", "priority": "高", "timeline": "2026年", "salary": "80-150k", "location": "美国"},
    {"position": "Research Engineer", "company": "DeepMind", "priority": "高", "timeline": "2026年", "salary": "70-130k", "location": "英国"},
    {"position": "AI Scientist", "company": "Anthropic", "priority": "中", "timeline": "2026年", "salary": "75-140k", "location": "美国"},
    
    # 创业和其他 (5个)
    {"position": "技术合伙人", "company": "AI创业公司", "priority": "中", "timeline": "2025年", "salary": "股权", "location": "北京"},
    {"position": "独立开发者", "company": "自由职业", "priority": "低", "timeline": "2025年", "salary": "不定", "location": "远程"},
    {"position": "技术顾问", "company": "咨询公司", "priority": "低", "timeline": "2026年", "salary": "项目制", "location": "北京"},
    {"position": "开源维护者", "company": "开源基金会", "priority": "低", "timeline": "2026年", "salary": "捐赠", "location": "远程"},
    {"position": "技术讲师", "company": "在线教育", "priority": "低", "timeline": "2026年", "salary": "课时费", "location": "远程"},
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
            
            # 确保User节点存在
            kg.ensure_user_exists()
            
            # 创建人物关系
            print(f"  创建人物关系...")
            for person in RELATIONSHIPS:
                kg.add_information(
                    name=person["name"],
                    info_type="entity",
                    category=person["category"],
                    confidence=0.9,
                    attributes={
                        "type": person["type"],  # 实体类型（Person）
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
                        "type": "School",  # 实体类型（School）
                        "degree": edu["degree"],
                        "major": edu["major"],
                        "start_year": edu["start_year"],
                        "end_year": edu["end_year"],
                        "gpa": edu.get("gpa", 0)
                    }
                )
                
                # 添加User到School的INTERESTED_IN关系
                kg.add_user_relationship(
                    target_name=edu["school"],
                    relation_type="INTERESTED_IN",
                    properties={
                        "interest_level": 0.8,
                        "degree": edu["degree"],
                        "major": edu["major"]
                    }
                )
                total_nodes += 1
                total_relations += 1
            
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
            
            # 创建职业目标（Job实体）
            print(f"  创建职业目标...")
            for goal in CAREER_GOALS:
                # 创建Job实体（而不是career_goal概念）
                kg.add_information(
                    name=goal["position"],
                    info_type="entity",
                    category="tech",
                    confidence=0.9,
                    attributes={
                        "type": "Job",  # 实体类型（Job）
                        "position": goal["position"],
                        "company": goal["company"],
                        "priority": goal["priority"],
                        "timeline": goal["timeline"]
                    }
                )
                
                # 添加User到Job的INTERESTED_IN关系
                kg.add_user_relationship(
                    target_name=goal["position"],
                    relation_type="INTERESTED_IN",
                    properties={
                        "interest_level": 0.9 if goal["priority"] == "高" else 0.85 if goal["priority"] == "中" else 0.8,
                        "priority": goal["priority"],
                        "company": goal["company"]
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
