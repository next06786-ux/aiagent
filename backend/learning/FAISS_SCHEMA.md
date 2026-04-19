# FAISS 向量数据库架构设计

**版本**: 2.0  
**更新时间**: 2026-04-18  
**状态**: 独立架构，与 Neo4j 互补

---

## 📋 目录

1. [架构理念](#架构理念)
2. [当前状态分析](#当前状态分析)
3. [数据类型定义](#数据类型定义)
4. [与 Neo4j 的分工](#与-neo4j-的分工)
5. [混合检索策略](#混合检索策略)

---

## 架构理念

### 核心原则：独立互补

**Neo4j 和 FAISS 是两个独立的数据库，各有专长：**

```
┌─────────────────────────────────────────────────────────┐
│                    混合检索系统                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐         ┌──────────────────┐    │
│  │   Neo4j (图)     │         │   FAISS (向量)   │    │
│  ├──────────────────┤         ├──────────────────┤    │
│  │ 结构化数据       │         │ 非结构化数据     │    │
│  │ - Entity (实体)  │         │ - Conversation   │    │
│  │ - Event (事件)   │         │ - Experience     │    │
│  │ - Concept (概念) │         │ - Insight        │    │
│  │ - Pattern (模式) │         │ - Knowledge      │    │
│  │                  │         │                  │    │
│  │ 精确匹配         │         │ 语义相似度       │    │
│  │ 关系遍历         │         │ 模糊检索         │    │
│  └──────────────────┘         └──────────────────┘    │
│           ↓                            ↓               │
│           └────────────┬───────────────┘               │
│                        ↓                               │
│                  融合引擎 (RRF)                        │
│                        ↓                               │
│                   统一结果集                           │
└─────────────────────────────────────────────────────────┘
```

### 为什么不需要同步？

1. **数据性质不同**
   - Neo4j: 结构化实体（张三、Python工程师、清华大学）
   - FAISS: 非结构化文本（"我和张三讨论了职业规划"）

2. **检索方式不同**
   - Neo4j: 精确匹配 + 图遍历（"找到所有 Person 类型的节点"）
   - FAISS: 语义相似度（"找到与'人际关系'语义相似的记忆"）

3. **互补而非重复**
   - Neo4j 提供：谁、什么、在哪（实体和关系）
   - FAISS 提供：为什么、怎么样、感受（上下文和语义）

---

## 当前状态分析

### 现有数据统计

根据 2026-04-18 的检查结果：

```
总向量数: 66
索引维度: 384 (paraphrase-multilingual-MiniLM-L12-v2)

按类型统计:
- conversation: 22 个  ✅ 有数据
- decision: 44 个      ✅ 有数据
- knowledge: 0 个      ❌ 无数据
- experience: 0 个     ❌ 无数据
- insight: 0 个        ❌ 无数据
- sensor_data: 0 个    ❌ 无数据
- photo: 0 个          ❌ 无数据
- schedule: 0 个       ❌ 无数据
- task_completion: 0 个 ❌ 无数据
```

### 问题诊断

**为什么人际关系查询返回 0 个向量结果？**

1. **数据缺失**: FAISS 中只有 `conversation` 和 `decision` 类型的数据
2. **内容不匹配**: 现有的 22 个对话记录主要是简单问候（"你好"、"我和安妮去散步了"）
3. **领域过滤**: RAGRetriever 在检索时会根据领域过滤记忆类型
   - 人际关系查询 → 检索 `CONVERSATION` 和 `EXPERIENCE` 类型
   - 但 `EXPERIENCE` 类型为空，`CONVERSATION` 中没有相关内容
4. **重要性过滤**: 即使检索到对话，也可能因为重要性不足被过滤

---

## 数据类型定义

### Memory 数据结构

每个存储在 FAISS 中的记忆都包含以下字段：

```python
@dataclass
class Memory:
    """FAISS 向量记忆数据结构"""
    
    # 核心字段
    id: str                          # 唯一标识符 (UUID)
    content: str                     # 文本内容（用于生成向量）
    embedding: np.ndarray            # 384维向量 (paraphrase-multilingual-MiniLM-L12-v2)
    
    # 分类字段
    memory_type: MemoryType          # 记忆类型（枚举）
    
    # 元数据字段
    importance: float                # 重要性 (0.0-1.0)
    timestamp: datetime              # 创建时间
    metadata: Dict[str, Any]         # 扩展元数据
    
    # 访问统计
    access_count: int = 0            # 访问次数
    last_accessed: Optional[datetime] = None  # 最后访问时间
```

### MemoryType 枚举

```python
class MemoryType(Enum):
    """记忆类型枚举"""
    
    # 对话相关
    CONVERSATION = "conversation"      # 用户与AI的对话记录
    
    # 传感器数据
    SENSOR_DATA = "sensor_data"        # 位置、活动等传感器数据
    
    # 多媒体
    PHOTO = "photo"                    # 照片描述和分析
    
    # 知识和经验
    KNOWLEDGE = "knowledge"            # 知识点、概念、技能
    EXPERIENCE = "experience"          # 个人经验、故事、回忆
    INSIGHT = "insight"                # AI生成的洞察和分析
    
    # 决策和任务
    DECISION = "decision"              # 决策记录和理由
    SCHEDULE = "schedule"              # 日程安排
    TASK_COMPLETION = "task_completion" # 任务完成记录
    
    # 决策逻辑画像（新增）
    DECISION_LOGIC = "decision_logic"  # 从平行人生塔罗牌游戏提取的决策逻辑和价值观
```

### 各类型的字段规范

#### 1. CONVERSATION (对话记录)

```python
Memory(
    id="conv_uuid_xxx",
    content="用户: 我和张三讨论了职业规划\nAI: 很好，职业规划很重要...",
    memory_type=MemoryType.CONVERSATION,
    importance=0.7,
    timestamp=datetime.now(),
    metadata={
        "user_id": "user_xxx",
        "session_id": "session_xxx",
        "turn": 5,                    # 对话轮次
        "user_message": "我和张三讨论了职业规划",
        "ai_response": "很好，职业规划很重要...",
        "thinking": "用户提到了职业规划...",  # AI的思考过程
        "domain": "career"            # 领域标签
    }
)
```

#### 2. EXPERIENCE (经验总结)

```python
Memory(
    id="exp_uuid_xxx",
    content="在字节跳动实习期间，我学会了如何进行代码审查和团队协作",
    memory_type=MemoryType.EXPERIENCE,
    importance=0.85,
    timestamp=datetime.now(),
    metadata={
        "user_id": "user_xxx",
        "domain": "career",
        "tags": ["实习", "字节跳动", "代码审查", "团队协作"],
        "duration": "3个月",
        "outcome": "positive",        # positive/negative/neutral
        "related_entities": ["字节跳动", "Python"],  # 关联的实体
        "extracted_from": "conversation"  # 来源
    }
)
```

#### 3. INSIGHT (洞察发现)

```python
Memory(
    id="insight_uuid_xxx",
    content="用户的人际关系网络中，同事占比27.1%，是最主要的社交圈",
    memory_type=MemoryType.INSIGHT,
    importance=0.9,
    timestamp=datetime.now(),
    metadata={
        "user_id": "user_xxx",
        "domain": "relationship",
        "insight_type": "influence_analysis",  # 洞察类型
        "confidence": 0.85,           # 置信度
        "data_points": 30,            # 数据点数量
        "generated_by": "RelationshipInsightAgent",
        "query": "分析我的人际关系网络",
        "key_metrics": {
            "colleagues": 0.271,
            "friends": 0.234,
            "family": 0.156
        }
    }
)
```

#### 4. KNOWLEDGE (知识点)

```python
Memory(
    id="know_uuid_xxx",
    content="Python 是一种高级编程语言，适合数据分析、Web开发和机器学习",
    memory_type=MemoryType.KNOWLEDGE,
    importance=0.75,
    timestamp=datetime.now(),
    metadata={
        "user_id": "user_xxx",
        "domain": "career",
        "category": "programming_language",
        "tags": ["Python", "编程", "数据分析"],
        "source": "user_input",       # user_input/web/book/course
        "verified": True,             # 是否已验证
        "related_skills": ["数据分析", "Web开发", "机器学习"]
    }
)
```

#### 5. DECISION (决策记录)

```python
Memory(
    id="dec_uuid_xxx",
    content="决定接受字节跳动的offer，因为薪资待遇好且团队氛围不错",
    memory_type=MemoryType.DECISION,
    importance=0.95,
    timestamp=datetime.now(),
    metadata={
        "user_id": "user_xxx",
        "domain": "career",
        "decision_type": "job_offer",
        "options": ["字节跳动", "阿里巴巴", "腾讯"],
        "chosen": "字节跳动",
        "reasons": ["薪资待遇好", "团队氛围不错", "技术栈匹配"],
        "outcome": "pending",         # pending/success/failure
        "confidence": 0.8
    }
)
```

#### 6. SENSOR_DATA (传感器数据)

```python
Memory(
    id="sensor_uuid_xxx",
    content="2026-04-18 14:30 在北京市朝阳区，步行活动，心率72",
    memory_type=MemoryType.SENSOR_DATA,
    importance=0.5,
    timestamp=datetime.now(),
    metadata={
        "user_id": "user_xxx",
        "sensor_type": "location",    # location/activity/health
        "location": {
            "city": "北京",
            "district": "朝阳区",
            "lat": 39.9042,
            "lng": 116.4074
        },
        "activity": "walking",
        "health_metrics": {
            "heart_rate": 72,
            "steps": 5000
        }
    }
)
```

#### 7. PHOTO (照片记忆)

```python
Memory(
    id="photo_uuid_xxx",
    content="2026-04-18 和张三、李四在三里屯聚餐，大家都很开心",
    memory_type=MemoryType.PHOTO,
    importance=0.8,
    timestamp=datetime.now(),
    metadata={
        "user_id": "user_xxx",
        "photo_id": "photo_xxx",
        "photo_url": "s3://bucket/photo_xxx.jpg",
        "location": "三里屯",
        "people": ["张三", "李四"],
        "objects": ["餐桌", "食物"],
        "scene": "restaurant",
        "emotion": "happy",
        "ocr_text": "",               # 照片中的文字
        "analysis": "朋友聚餐场景"
    }
)
```

#### 8. SCHEDULE (日程安排)

```python
Memory(
    id="schedule_uuid_xxx",
    content="2026-04-20 14:00 字节跳动面试，地点：北京总部，岗位：Python后端工程师",
    memory_type=MemoryType.SCHEDULE,
    importance=0.9,
    timestamp=datetime.now(),
    metadata={
        "user_id": "user_xxx",
        "event_type": "interview",
        "start_time": "2026-04-20T14:00:00",
        "end_time": "2026-04-20T16:00:00",
        "location": "北京字节跳动总部",
        "participants": ["面试官王五"],
        "status": "scheduled",        # scheduled/completed/cancelled
        "reminder": True,
        "related_entities": ["字节跳动", "Python后端工程师"]
    }
)
```

#### 9. TASK_COMPLETION (任务完成)

```python
Memory(
    id="task_uuid_xxx",
    content="完成了Python项目的代码重构，提升了30%的性能",
    memory_type=MemoryType.TASK_COMPLETION,
    importance=0.85,
    timestamp=datetime.now(),
    metadata={
        "user_id": "user_xxx",
        "task_id": "task_xxx",
        "task_name": "代码重构",
        "domain": "career",
        "completion_time": "2026-04-18T18:00:00",
        "duration": "3天",
        "outcome": "success",
        "metrics": {
            "performance_improvement": 0.3,
            "code_quality": "improved"
        },
        "learnings": ["学会了性能优化技巧", "理解了代码重构的重要性"]
    }
)
```

#### 10. DECISION_LOGIC (决策逻辑画像) 🆕

```python
Memory(
    id="logic_uuid_xxx",
    content="在'愚者'塔罗牌场景中，用户选择了冒险路径，展现出高风险偏好（0.8）",
    memory_type=MemoryType.DECISION_LOGIC,
    importance=0.95,  # 决策逻辑画像非常重要
    timestamp=datetime.now(),
    metadata={
        "user_id": "user_xxx",
        "source": "tarot_game",           # 数据来源：塔罗牌游戏
        "game_session_id": "session_xxx", # 游戏会话ID
        
        # 塔罗牌信息
        "card": "愚者",                   # 塔罗牌名称
        "card_english": "THE_FOOL",       # 塔罗牌英文名
        
        # 决策维度
        "dimension": "风险偏好",          # 决策维度（中文）
        "dimension_english": "RISK_TOLERANCE",  # 决策维度（英文）
        
        # 选择信息
        "choice": "选择冒险路径",         # 用户的选择
        "scenario": "你站在人生的十字路口...",  # 场景描述
        "options": [                      # 所有选项
            {"id": "A", "text": "选择冒险路径", "tendency": 0.8},
            {"id": "B", "text": "选择稳妥路径", "tendency": 0.2}
        ],
        
        # 决策倾向值
        "tendency_value": 0.8,            # 倾向值 (-1.0 到 1.0)
        "tendency_label": "高风险偏好",   # 倾向标签
        
        # 累积统计
        "total_choices": 5,               # 该维度的总选择次数
        "average_tendency": 0.75,         # 该维度的平均倾向值
        
        # 置信度
        "confidence": 0.85,               # 该维度画像的置信度
        
        # 关联维度
        "related_dimensions": [           # 相关的其他决策维度
            "主动性", "创新性"
        ],
        
        # 应用场景
        "applicable_domains": [           # 适用的决策领域
            "career", "education", "investment"
        ]
    }
)
```

**DECISION_LOGIC 的特殊性**：

1. **高重要性**: importance 通常在 0.9-1.0，因为决策逻辑画像对个性化决策支持至关重要
2. **长期有效**: 不应该被时间衰减过滤，决策逻辑是相对稳定的人格特征
3. **跨领域应用**: 一个决策维度可以应用到多个决策场景
4. **累积更新**: 随着用户玩更多塔罗牌，同一维度的数据会累积，提高置信度

**决策维度映射表**：

```python
DECISION_DIMENSIONS = {
    "RISK_TOLERANCE": "风险偏好",      # 冒险 vs 稳妥
    "INITIATIVE": "主动性",            # 主动 vs 被动
    "THINKING_STYLE": "思维方式",      # 理性 vs 感性
    "AUTHORITY": "权威态度",           # 服从 vs 质疑
    "INNOVATION": "创新性",            # 创新 vs 传统
    "RELATIONSHIP": "关系导向",        # 独立 vs 依赖
    "AMBITION": "野心程度",            # 进取 vs 知足
    "PERSISTENCE": "坚持性",           # 坚持 vs 灵活
    "SOCIAL": "社交倾向",              # 外向 vs 内向
    "PLANNING": "计划性",              # 计划 vs 随机
    "FAIRNESS": "公平观",              # 公平 vs 效率
    "SACRIFICE": "牺牲意愿",           # 牺牲 vs 自我
    "CHANGE": "变化态度",              # 拥抱 vs 抗拒
    "BALANCE": "平衡性",               # 平衡 vs 极端
    "DESIRE": "欲望控制",              # 克制 vs 放纵
    "DESTRUCTION": "破坏性",           # 保守 vs 激进
    "IDEALISM": "理想主义",            # 理想 vs 现实
    "INTUITION": "直觉依赖",           # 直觉 vs 逻辑
    "OPTIMISM": "乐观程度",            # 乐观 vs 悲观
    "REFLECTION": "反思性",            # 反思 vs 行动
    "COMPLETION": "完成导向",          # 完成 vs 过程
}
```

---

## 元数据字段规范

### 通用元数据字段

所有记忆类型都应包含的基础元数据：

```python
metadata = {
    "user_id": str,              # 必需：用户ID
    "domain": str,               # 可选：领域标签 (career/education/relationship)
    "tags": List[str],           # 可选：标签列表
    "source": str,               # 可选：数据来源
    "version": str,              # 可选：数据版本
}
```

### 领域特定元数据

根据 `domain` 字段，可以添加领域特定的元数据：

```python
# 职业领域 (career)
career_metadata = {
    "company": str,              # 公司名称
    "position": str,             # 职位名称
    "skills": List[str],         # 相关技能
    "industry": str,             # 行业
}

# 教育领域 (education)
education_metadata = {
    "school": str,               # 学校名称
    "major": str,                # 专业
    "degree": str,               # 学位
    "courses": List[str],        # 课程列表
}

# 人际关系领域 (relationship)
relationship_metadata = {
    "people": List[str],         # 涉及的人物
    "relationship_type": str,    # 关系类型 (friend/colleague/family)
    "interaction_type": str,     # 互动类型 (meeting/call/message)
    "sentiment": str,            # 情感倾向 (positive/negative/neutral)
}
```

---

### MemoryType 枚举

```python
class MemoryType(Enum):
    CONVERSATION = "conversation"      # 对话记录
    SENSOR_DATA = "sensor_data"        # 传感器数据
    PHOTO = "photo"                    # 照片记忆
    KNOWLEDGE = "knowledge"            # 知识点
    DECISION = "decision"              # 决策记录
    EXPERIENCE = "experience"          # 经验总结
    INSIGHT = "insight"                # 洞察发现
    SCHEDULE = "schedule"              # 日程安排
    TASK_COMPLETION = "task_completion" # 任务完成
```

### 领域与记忆类型映射

```python
domain_memory_mapping = {
    'relationship': [MemoryType.CONVERSATION, MemoryType.EXPERIENCE],
    'career': [MemoryType.KNOWLEDGE, MemoryType.EXPERIENCE, MemoryType.INSIGHT],
    'education': [MemoryType.KNOWLEDGE, MemoryType.EXPERIENCE]
}
```

---

## 与 Neo4j 的分工

### Neo4j 负责（结构化数据）

**存储内容**:
- Entity 节点：Person（张三、李四）、Job（Python工程师）、School（清华大学）
- Event 节点：面试、聚会、会议
- Concept 节点：技能、兴趣、价值观
- Pattern 节点：行为模式、决策模式

**检索特点**:
- 精确匹配：`type='Person'`
- 关系遍历：`User-KNOWS->Person-WORKS_AT->Company`
- 图算法：最短路径、中心性分析

**使用场景**:
- "找到我认识的所有人"
- "找到在阿里工作的朋友"
- "找到我申请过的所有职位"

### FAISS 负责（非结构化数据）

**存储内容**:
- Conversation：对话记录（"我和张三讨论了职业规划"）
- Experience：经验总结（"在字节跳动实习的经历让我学到了..."）
- Insight：洞察发现（"我的人际关系网络中，同事占比最高"）
- Knowledge：知识点（"Python 适合数据分析和 Web 开发"）

**检索特点**:
- 语义相似度：向量距离计算
- 模糊匹配：不需要精确关键词
- 上下文理解：理解查询意图

**使用场景**:
- "我和朋友讨论过什么话题？"
- "我对职业发展有什么想法？"
- "我之前学习过哪些技能？"

### 混合检索的价值

**示例查询**: "分析我的人际关系网络"

```
Neo4j 检索:
✓ 找到 57 个 Person 实体
✓ 返回：张三（同学）、李四（同事）、王五（朋友）...
✓ 提供：结构化的人物列表和关系类型

FAISS 检索:
✓ 找到 5 个相关对话
✓ 返回："我和张三讨论了职业规划"、"李四帮我介绍了工作机会"...
✓ 提供：互动上下文和情感信息

融合结果:
→ 既有人物列表（来自 Neo4j）
→ 又有互动细节（来自 FAISS）
→ 生成更全面的洞察报告
```

---

## 混合检索策略

### 当前实现

```python
# 人际关系查询
query = "分析我的人际关系网络"

# Neo4j 检索
neo4j_results = [
    {"name": "张三", "type": "Person", "category": "friends"},
    {"name": "李四", "type": "Person", "category": "colleagues"},
    # ... 57 个 Person 实体
]

# FAISS 检索
faiss_results = [
    {"content": "我和张三讨论了职业规划", "type": "conversation"},
    {"content": "李四帮我介绍了工作机会", "type": "conversation"},
    # ... 5 个相关对话
]

# RRF 融合
# 同时出现在两个列表中的结果会获得更高分数
# 例如：张三在 Neo4j 中排名第1，在 FAISS 对话中也被提及，融合后排名更高
```

### 为什么向量检索返回 0？

**原因分析**:

1. **FAISS 中缺少相关数据**
   - 现有 22 个对话主要是简单问候
   - 没有实质性的人际关系讨论内容

2. **这是正常的！**
   - 如果用户没有和 AI 讨论过人际关系，FAISS 就不应该有相关数据
   - Neo4j 有 57 个 Person 实体是因为从其他来源提取的（照片、传感器等）
   - FAISS 只存储对话和经验，不存储实体

3. **混合检索仍然有效**
   - 即使 FAISS 返回 0，Neo4j 返回 30 个结果
   - 系统仍然能生成洞察报告
   - 这就是混合检索的优势：互补而非依赖

### 理想状态

**当用户与 AI 有更多互动后**:

```
查询: "分析我的人际关系网络"

Neo4j 检索: 57 个 Person 实体
FAISS 检索: 20 个相关对话/经验
融合结果: 70+ 个节点

洞察质量提升:
- Neo4j 提供：人物列表和关系类型
- FAISS 提供：互动细节和情感信息
- 融合后：更丰富、更有深度的洞察
```

---

## 数据流向

### 正确的数据流

```
用户输入
    ↓
┌───────────────────────────────────────┐
│  信息提取 (information_extractor.py)  │
├───────────────────────────────────────┤
│  识别：实体、事件、概念               │
└───────────────────────────────────────┘
    ↓
    ├─→ 结构化信息 → Neo4j
    │   (Entity/Event/Concept)
    │
    └─→ 对话记录 → FAISS
        (Conversation)

用户对话
    ↓
┌───────────────────────────────────────┐
│  对话处理 (message_processor.py)      │
├───────────────────────────────────────┤
│  存储完整对话上下文                   │
└───────────────────────────────────────┘
    ↓
    FAISS (Conversation)

智慧洞察生成
    ↓
┌───────────────────────────────────────┐
│  洞察 Agent (realtime_insight_agents)  │
├───────────────────────────────────────┤
│  生成洞察报告                         │
└───────────────────────────────────────┘
    ↓
    FAISS (Insight)  ← 可选：存储洞察供后续检索
```

### 不需要同步

❌ **错误做法**: Neo4j Entity → FAISS Knowledge
- 重复存储
- 破坏各自的数据架构
- 增加维护成本

✅ **正确做法**: 各自独立，混合检索时融合
- Neo4j 保持图结构
- FAISS 保持向量结构
- 检索时动态融合结果

---

## 存储最佳实践

### 1. 内容格式化

**原则**: content 字段应该是自包含的、可读的文本

```python
# ✅ 好的做法
content = "2026-04-18 和张三在三里屯讨论了职业规划，他建议我考虑字节跳动的机会"

# ❌ 不好的做法
content = "讨论职业规划"  # 太简短，缺少上下文
```

### 2. 重要性评分

**原则**: importance 应该反映记忆的长期价值

```python
# 重要性评分指南
importance_guide = {
    0.9-1.0: "关键决策、重大事件、核心洞察",
    0.7-0.9: "重要经验、有价值的知识、重要对话",
    0.5-0.7: "一般对话、日常活动",
    0.3-0.5: "简单问候、琐碎信息",
    0.0-0.3: "噪音数据、无关信息"
}
```

### 3. 元数据完整性

**原则**: 元数据应该丰富但不冗余

```python
# ✅ 好的元数据
metadata = {
    "user_id": "user_xxx",
    "domain": "career",
    "tags": ["面试", "字节跳动", "Python"],
    "people": ["张三"],
    "location": "三里屯",
    "outcome": "positive"
}

# ❌ 不好的元数据
metadata = {
    "user_id": "user_xxx",
    "data": "some data"  # 太模糊
}
```

### 4. 时间戳管理

**原则**: 使用 ISO 8601 格式，包含时区信息

```python
from datetime import datetime, timezone

# ✅ 正确的时间戳
timestamp = datetime.now(timezone.utc)

# 元数据中的时间字段
metadata = {
    "created_at": "2026-04-18T14:30:00+08:00",
    "event_time": "2026-04-20T14:00:00+08:00"
}
```

---

## 检索最佳实践

### 1. 记忆类型选择

根据查询意图选择合适的记忆类型：

```python
query_type_mapping = {
    # 人际关系查询
    "relationship": [
        MemoryType.CONVERSATION,  # 对话中的互动
        MemoryType.EXPERIENCE,    # 与人相处的经验
        MemoryType.PHOTO,         # 照片中的人物
        MemoryType.INSIGHT        # 人际关系洞察
    ],
    
    # 职业查询
    "career": [
        MemoryType.KNOWLEDGE,     # 技能和知识
        MemoryType.EXPERIENCE,    # 工作经验
        MemoryType.DECISION,      # 职业决策
        MemoryType.INSIGHT        # 职业洞察
    ],
    
    # 教育查询
    "education": [
        MemoryType.KNOWLEDGE,     # 学习内容
        MemoryType.EXPERIENCE,    # 学习经验
        MemoryType.SCHEDULE,      # 课程安排
        MemoryType.INSIGHT        # 学习洞察
    ]
}
```

### 2. 重要性过滤

根据查询类型设置合适的重要性阈值：

```python
importance_thresholds = {
    "critical": 0.8,    # 只检索最重要的记忆
    "important": 0.6,   # 检索重要记忆
    "normal": 0.4,      # 检索一般记忆
    "all": 0.0          # 检索所有记忆
}
```

### 3. 时间衰减

考虑记忆的时效性：

```python
def calculate_time_decay(timestamp: datetime, decay_rate: float = 0.01) -> float:
    """计算时间衰减因子"""
    days_old = (datetime.now() - timestamp).days
    return max(0, 1 - days_old * decay_rate)

# 应用时间衰减
final_score = base_score * time_decay_factor
```

### 4. 元数据过滤

使用元数据进行精确过滤：

```python
# 过滤特定领域
filtered = [m for m in memories if m.metadata.get('domain') == 'career']

# 过滤特定标签
filtered = [m for m in memories if 'Python' in m.metadata.get('tags', [])]

# 过滤特定人物
filtered = [m for m in memories if '张三' in m.metadata.get('people', [])]
```

---

## 数据维护

### 1. 定期清理

**策略**: 删除低价值、过时的记忆

```python
def cleanup_memories(user_id: str):
    """清理低价值记忆"""
    
    # 删除6个月前的低重要性对话
    cutoff_date = datetime.now() - timedelta(days=180)
    
    memories_to_delete = []
    for memory in get_all_memories(user_id):
        if (memory.memory_type == MemoryType.CONVERSATION and
            memory.importance < 0.5 and
            memory.timestamp < cutoff_date):
            memories_to_delete.append(memory.id)
    
    delete_memories(memories_to_delete)
```

### 2. 重要性更新

**策略**: 根据访问频率更新重要性

```python
def update_importance_by_access(memory: Memory):
    """根据访问频率更新重要性"""
    
    # 访问次数越多，重要性越高
    access_boost = min(0.2, memory.access_count * 0.01)
    memory.importance = min(1.0, memory.importance + access_boost)
```

### 3. 去重

**策略**: 合并相似的记忆

```python
def deduplicate_memories(user_id: str, similarity_threshold: float = 0.95):
    """去重相似记忆"""
    
    memories = get_all_memories(user_id)
    
    for i, mem1 in enumerate(memories):
        for mem2 in memories[i+1:]:
            similarity = cosine_similarity(mem1.embedding, mem2.embedding)
            
            if similarity > similarity_threshold:
                # 保留重要性更高的
                if mem1.importance >= mem2.importance:
                    delete_memory(mem2.id)
                else:
                    delete_memory(mem1.id)
```

---

## 与 Neo4j 的协同

### 数据流向

```
用户输入
    ↓
信息提取
    ↓
    ├─→ 结构化信息 → Neo4j
    │   - Entity (张三、Python工程师)
    │   - Event (面试、聚会)
    │   - Concept (技能、兴趣)
    │
    └─→ 非结构化信息 → FAISS
        - Conversation (完整对话)
        - Experience (经验总结)
        - Insight (洞察发现)
```

### 引用关系

FAISS 中的记忆可以引用 Neo4j 中的实体：

```python
# FAISS 记忆
Memory(
    content="和张三讨论了Python工程师的职业发展",
    metadata={
        "related_entities": [
            {"type": "Person", "name": "张三", "neo4j_id": "entity_001"},
            {"type": "Job", "name": "Python工程师", "neo4j_id": "entity_002"}
        ]
    }
)
```

### 混合检索流程

```python
def hybrid_search(query: str, domain: str):
    """混合检索"""
    
    # 1. Neo4j 检索（结构化）
    neo4j_results = neo4j_retriever.retrieve(
        query=query,
        domain=domain
    )
    # 返回: [张三(Person), 李四(Person), ...]
    
    # 2. FAISS 检索（非结构化）
    faiss_results = faiss_retriever.retrieve(
        query=query,
        memory_types=[MemoryType.CONVERSATION, MemoryType.EXPERIENCE],
        domain=domain
    )
    # 返回: ["和张三讨论了...", "李四帮我介绍了..."]
    
    # 3. RRF 融合
    fused_results = rrf_fusion(neo4j_results, faiss_results)
    
    return fused_results
```

---

## 总结

### FAISS 数据架构核心原则

1. **字段规范**: 每个记忆都有明确的字段定义
2. **类型系统**: 9种记忆类型，各有专门用途
3. **元数据丰富**: 使用元数据增强检索能力
4. **独立架构**: 不依赖 Neo4j，各自独立
5. **互补检索**: 与 Neo4j 配合，提供全面的检索能力

### 当前实现状态

- ✅ Memory 数据结构已定义（`production_rag_system.py`）
- ✅ MemoryType 枚举已实现
- ✅ 存储和检索接口已完善
- ✅ 混合检索系统已集成

### 未来改进方向

1. 实现自动重要性更新机制
2. 添加记忆去重功能
3. 实现定期清理任务
4. 增强元数据提取能力
5. 优化时间衰减算法

---

**文档版本**: 2.0  
**最后更新**: 2026-04-18  
**维护者**: Backend Team

---


