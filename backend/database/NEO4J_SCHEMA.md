# Neo4j 数据库架构设计

**版本**: 3.0  
**更新时间**: 2026-04-17  
**状态**: 纯用户数据架构，只存储从对话/照片/传感器提取的信息

---

## 📋 目录

1. [架构概述](#架构概述)
2. [核心节点类型](#核心节点类型)
3. [关系类型](#关系类型)
4. [数据流程](#数据流程)
5. [初始化步骤](#初始化步骤)
6. [查询示例](#查询示例)

---

## 架构概述

### 设计原则

1. **纯用户数据**: 只存储从用户对话、照片、传感器提取的信息
2. **信息溯源**: 所有提取的信息都可以追溯到来源（对话、照片、传感器）
3. **灵活扩展**: 支持新增领域和节点类型
4. **统一架构**: 三个领域（职业、教育、人际关系）使用相同的数据结构

### 数据来源

```
用户输入（对话/照片/传感器）
         ↓
information_extractor.py（信息提取）
├─ LLM智能提取（优先）
└─ 正则表达式提取（兜底）
         ↓
information_knowledge_graph.py（存储到Neo4j）
├─ 创建 Entity/Event/Concept/Pattern 节点
├─ 创建 Source 节点（溯源）
└─ 建立关系
         ↓
Neo4j 数据库（统一存储）
└─ User + Entity + Event + Concept + Pattern + Source
         ↓
三个领域的知识星图构建
├─ neo4j_career_kg.py（职业星图）
├─ neo4j_education_kg.py（教育星图）
└─ neo4j_relationship_kg.py（人际关系星图）
```

---

## 核心节点类型

### 1. User（用户）

用户主节点，所有个人信息的中心。

**属性**:
- `user_id` (string, 必需): 用户唯一标识
- `name` (string): 用户姓名
- `age` (integer): 年龄
- `gender` (string): 性别
- `location` (string): 所在城市
- `education_level` (string): 教育水平
- `major` (string): 专业
- `work_years` (integer): 工作年限
- `current_position` (string): 当前职位
- `skills` (list): 技能列表
- `interests` (list): 兴趣爱好
- `created_at` (datetime): 创建时间
- `updated_at` (datetime): 更新时间

**教育星图扩展属性**（用于EducationUserProfile）:
- `current_school` (string): 当前学校
- `gpa` (float): GPA成绩
- `ranking_percent` (float): 排名百分比（如0.1表示前10%）
- `toefl_score` (integer): 托福成绩
- `gre_score` (integer): GRE成绩
- `research_experience` (string): 科研经历描述
- `target_degree` (string): 目标学位（本科/硕士/博士）
- `target_major` (string): 目标专业

**示例**:
```cypher
CREATE (u:User {
  user_id: 'user_001',
  name: '张三',
  age: 28,
  gender: '男',
  location: '北京',
  education_level: '本科',
  major: '计算机科学',
  work_years: 5,
  current_position: 'Python工程师',
  skills: ['Python', 'Django', 'PostgreSQL'],
  interests: ['编程', '阅读', '旅行'],
  created_at: datetime(),
  updated_at: datetime()
})
```

**注意**: 
- User节点存储基础信息，教育星图构建时会从EducationUserProfile获取更详细的教育背景
- 中心节点的metadata会包含完整的教育信息（当前学校、GPA、标化成绩等）

---

### 2. Entity（实体）

从用户对话中提取的实体信息（人物、组织、地点、职位、学校等）。

**属性**:
- `entity_id` (string, 必需): 实体唯一标识
- `name` (string, 必需): 实体名称
- `type` (string, 必需): 实体类型（Person/Organization/Location/Job/School等）
- `category` (string): 实体分类（更细粒度的分类）
- `description` (string): 实体描述
- `attributes` (map): 实体属性（JSON格式）
- `confidence` (float): 提取置信度（0-1）
- `extracted_at` (datetime): 提取时间
- `source_id` (string): 来源ID（关联到Source节点）

**示例**:
```cypher
// 人物实体
CREATE (e:Entity {
  entity_id: 'entity_001',
  name: '李四',
  type: 'Person',
  category: 'friend',
  description: '大学同学，现在在阿里工作',
  attributes: {role: '同学', company: '阿里巴巴', relationship: '朋友'},
  confidence: 0.95,
  extracted_at: datetime(),
  source_id: 'conv_001'
})

// 职位实体
CREATE (e:Entity {
  entity_id: 'entity_002',
  name: 'Python后端工程师',
  type: 'Job',
  category: 'position',
  description: '字节跳动招聘的后端岗位',
  attributes: {company: '字节跳动', salary: '30k-50k', location: '北京'},
  confidence: 0.92,
  extracted_at: datetime(),
  source_id: 'conv_002'
})

// 学校实体
CREATE (e:Entity {
  entity_id: 'entity_003',
  name: '清华大学',
  type: 'School',
  category: 'university',
  description: '计算机系研究生项目',
  attributes: {
    major: '计算机科学', 
    level: 'master',  // bachelor/master/phd
    location: '北京',
    tier: '985',  // 985/211/双一流/普通本科
    ranking: 1  // 学校排名
  },
  confidence: 0.98,
  extracted_at: datetime(),
  source_id: 'conv_003'
})
```

---

### 3. Event（事件）

从用户对话中提取的事件信息（会议、面试、聚会等）。

**属性**:
- `event_id` (string, 必需): 事件唯一标识
- `name` (string, 必需): 事件名称
- `type` (string, 必需): 事件类型（Meeting/Interview/Party/Travel等）
- `description` (string): 事件描述
- `start_time` (datetime): 开始时间
- `end_time` (datetime): 结束时间
- `location` (string): 地点
- `participants` (list): 参与者列表
- `confidence` (float): 提取置信度（0-1）
- `extracted_at` (datetime): 提取时间
- `source_id` (string): 来源ID

**示例**:
```cypher
CREATE (ev:Event {
  event_id: 'event_001',
  name: '字节跳动面试',
  type: 'Interview',
  description: '后端工程师岗位二面',
  start_time: datetime('2026-04-20T14:00:00'),
  location: '北京字节跳动总部',
  participants: ['面试官王五', '我'],
  confidence: 0.92,
  extracted_at: datetime(),
  source_id: 'conv_002'
})
```

---

### 4. Concept（概念）

从用户对话中提取的抽象概念（技能、兴趣、价值观等）。

**属性**:
- `concept_id` (string, 必需): 概念唯一标识
- `name` (string, 必需): 概念名称
- `type` (string, 必需): 概念类型（Skill/Interest/Value/Goal等）
- `description` (string): 概念描述
- `level` (string): 熟练度/重要性级别
- `confidence` (float): 提取置信度（0-1）
- `extracted_at` (datetime): 提取时间
- `source_id` (string): 来源ID

**示例**:
```cypher
CREATE (c:Concept {
  concept_id: 'concept_001',
  name: 'Python编程',
  type: 'Skill',
  description: '熟练使用Python进行后端开发',
  level: '高级',
  confidence: 0.98,
  extracted_at: datetime(),
  source_id: 'conv_003'
})
```

---

### 5. Pattern（模式）

从用户行为中识别的模式（习惯、偏好、决策模式等）。

**属性**:
- `pattern_id` (string, 必需): 模式唯一标识
- `name` (string, 必需): 模式名称
- `type` (string, 必需): 模式类型（Habit/Preference/DecisionPattern等）
- `description` (string): 模式描述
- `frequency` (integer): 出现频率
- `confidence` (float): 识别置信度（0-1）
- `identified_at` (datetime): 识别时间
- `evidence` (list): 证据列表（关联的对话/事件ID）

**示例**:
```cypher
CREATE (p:Pattern {
  pattern_id: 'pattern_001',
  name: '偏好大厂工作',
  type: 'Preference',
  description: '用户在职业选择中倾向于选择大型互联网公司',
  frequency: 5,
  confidence: 0.88,
  identified_at: datetime(),
  evidence: ['conv_001', 'conv_005', 'conv_008']
})
```

---

### 6. Source（来源）

信息来源节点，用于追溯信息的原始出处。

**属性**:
- `source_id` (string, 必需): 来源唯一标识
- `type` (string, 必需): 来源类型（Conversation/Photo/Sensor/Document等）
- `content` (string): 原始内容（对话文本、照片URL等）
- `timestamp` (datetime): 时间戳
- `metadata` (map): 元数据（JSON格式）

**示例**:
```cypher
CREATE (s:Source {
  source_id: 'conv_001',
  type: 'Conversation',
  content: '我大学同学李四现在在阿里工作，做算法工程师...',
  timestamp: datetime('2026-04-15T10:30:00'),
  metadata: {session_id: 'session_123', turn: 5}
})
```

---

## 关系类型

### 用户相关关系

| 关系类型 | 起始节点 | 目标节点 | 描述 | 属性 |
|---------|---------|---------|------|------|
| `HAS_PROFILE` | User | Entity/Concept | 用户拥有的属性/技能 | `since`, `confidence` |
| `PARTICIPATED_IN` | User | Event | 用户参与的事件 | `role`, `timestamp` |
| `INTERESTED_IN` | User | Entity/Concept | 用户感兴趣的内容 | `interest_level`, `timestamp` |
| `KNOWS` | User | Entity(Person) | 用户认识的人 | `relationship_type`, `closeness`, `since` |
| `APPLIED_TO` | User | Entity(Job/School) | 用户申请的职位/学校 | `status`, `applied_at` |

---

### 信息溯源关系

| 关系类型 | 起始节点 | 目标节点 | 描述 | 属性 |
|---------|---------|---------|------|------|
| `EXTRACTED_FROM` | Entity/Event/Concept | Source | 信息提取自来源 | `extraction_method`, `confidence` |
| `MENTIONED_IN` | Entity/Event | Source | 在来源中被提及 | `mention_count`, `context` |
| `CREATED_BY` | Source | User | 来源由用户创建 | `timestamp` |

---

### 实体间关系

| 关系类型 | 起始节点 | 目标节点 | 描述 | 属性 |
|---------|---------|---------|------|------|
| `RELATED_TO` | Entity | Entity | 实体之间的关联 | `relation_type`, `strength` |
| `PART_OF` | Entity | Entity | 实体的从属关系 | `role` |
| `HAPPENED_AT` | Event | Entity(Location) | 事件发生地点 | `timestamp` |
| `INVOLVES` | Event | Entity(Person) | 事件涉及的人物 | `role` |
| `REQUIRES` | Entity(Job) | Concept(Skill) | 职位要求的技能 | `importance`, `level` |
| `LOCATED_IN` | Entity | Entity(Location) | 位置关系 | - |

---

### 模式关系

| 关系类型 | 起始节点 | 目标节点 | 描述 | 属性 |
|---------|---------|---------|------|------|
| `EXHIBITS` | User | Pattern | 用户展现的模式 | `frequency`, `confidence` |
| `SUPPORTS` | Entity/Event | Pattern | 支持某个模式的证据 | `weight` |
| `INFLUENCES` | Pattern | Pattern | 模式之间的影响关系 | `influence_type`, `strength` |

---

## 数据流程

### 整体数据流

```
用户输入（对话/照片/传感器）
         ↓
information_extractor.py（信息提取）
├─ LLM智能提取（优先）
└─ 正则表达式提取（兜底）
         ↓
information_knowledge_graph.py（存储到Neo4j）
├─ 创建 Entity/Event/Concept/Pattern 节点
├─ 创建 Source 节点（溯源）
└─ 建立关系
         ↓
Neo4j 数据库（统一存储）
└─ User + Entity + Event + Concept + Pattern + Source
         ↓
三个领域的知识星图构建
├─ neo4j_career_kg.py（职业星图）
│   └─ 查询 User + Entity(Job) 数据
├─ neo4j_education_kg.py（教育星图）
│   └─ 查询 User + Entity(School) 数据
└─ neo4j_relationship_kg.py（人际关系星图）
    └─ 查询 User + Entity(Person) 数据
         ↓
3D可视化星图（前端展示）
```

---

### 信息提取流程

```
1. 用户输入
   ├─ 对话文本: "我大学同学李四现在在阿里工作"
   ├─ 照片: 识别人物、地点、物品
   └─ 传感器: 位置、时间、活动数据

2. 信息提取（information_extractor.py）
   ├─ LLM提取（优先）
   │   ├─ 实体识别: 李四（Person）、阿里（Company）
   │   ├─ 关系识别: 李四-WORKS_AT-阿里
   │   └─ 属性提取: {role: '同学', relationship: '朋友'}
   └─ 正则提取（兜底）
       └─ 模式匹配: 人名、公司名、时间等

3. 知识图谱存储（information_knowledge_graph.py）
   ├─ 创建节点
   │   ├─ Entity: 李四（Person）
   │   ├─ Entity: 阿里（Company）
   │   └─ Source: 对话记录
   ├─ 创建关系
   │   ├─ 李四-WORKS_AT-阿里
   │   ├─ User-KNOWS-李四
   │   └─ 李四-EXTRACTED_FROM-Source
   └─ 更新用户画像

4. 星图构建（neo4j_*_kg.py）
   ├─ 查询相关节点和关系
   ├─ 计算3D坐标（Fibonacci球面算法）
   └─ 返回可视化数据
```

---

### 职业星图构建流程

```
neo4j_career_kg.py
         ↓
1. 查询用户数据
   ├─ User节点（技能、经验、兴趣）
   ├─ Concept节点（用户的技能）
   ├─ Entity(Job)节点（用户提取的职位信息）
   └─ Pattern节点（职业偏好）
         ↓
2. 计算匹配度
   ├─ 技能匹配度
   ├─ 用户关注度
   └─ 综合评分
         ↓
3. 生成3D坐标
   ├─ Fibonacci球面分布
   └─ 根据匹配度调整距离
         ↓
4. 返回可视化数据
   ├─ nodes: [{id, label, type, position, ...}]
   ├─ edges: [{source, target, type, ...}]
   └─ metadata: {total_nodes, total_edges, ...}
```

---

### 教育星图构建流程

```
neo4j_education_kg.py
         ↓
1. 查询用户数据
   ├─ User节点（学历、专业、兴趣）
   ├─ Concept节点（学习兴趣）
   ├─ Entity(School)节点（用户提取的学校信息）
   └─ Pattern节点（学习偏好）
         ↓
2. 构建中心节点（"我"）
   ├─ 从EducationUserProfile获取用户详细信息
   ├─ 包含当前学校、专业、GPA、排名
   ├─ 包含标化成绩（托福、GRE）
   ├─ 包含科研经历
   └─ 包含申请目标（目标学位、目标专业）
         ↓
3. 过滤目标院校
   ├─ 只保留INTERESTED_IN/APPLIED_TO/ADMITTED_TO关系的学校
   ├─ 排除当前学校（避免重复显示）
   └─ 确保学校层只显示目标院校
         ↓
4. 计算匹配度
   ├─ 专业匹配度
   ├─ 地理位置匹配度
   └─ 用户关注度
         ↓
5. 生成3D坐标
   ├─ Fibonacci球面分布
   └─ 根据匹配度调整距离
         ↓
6. 返回可视化数据
   ├─ nodes: [{id, label, type, position, metadata, ...}]
   │   └─ 中心节点metadata包含完整用户信息
   ├─ edges: [{source, target, type, ...}]
   └─ metadata: {total_nodes, total_edges, ...}
```

#### 教育星图节点结构

**中心节点（"我"）**:
```python
{
    "id": "__me__",
    "label": "我",
    "type": "center",
    "layer": 0,
    "position": {"x": 0, "y": 0, "z": 0},
    "size": 20,
    "color": "#e8f4ff",
    "is_self": True,
    "metadata": {
        "student_id": "user_id",
        "node_type": "User",
        # 当前教育背景
        "current_school": "清华大学",
        "major": "计算机科学",
        "gpa": 3.8,
        "ranking_percent": 0.1,  # 前10%
        # 标化成绩
        "toefl_score": 110,
        "gre_score": 330,
        # 科研经历
        "research_experience": "2篇论文发表",
        # 申请目标
        "target_degree": "硕士",
        "target_major": "人工智能",
        # 综合描述
        "description": "清华大学 计算机科学专业，GPA 3.8，目标：硕士 人工智能"
    }
}
```

**学校节点（目标院校）**:
```python
{
    "id": "school_0",
    "label": "北京大学",
    "type": "school",
    "layer": 2,
    "position": {"x": 38.2, "y": 15.6, "z": 22.1},
    "size": 14,
    "color": "#1890FF",
    "metadata": {
        "node_type": "Entity",
        "entity_type": "School",
        "location": "北京",
        "major": "软件工程",
        "level": "master",
        "tier": "985",
        "ranking": 2,
        "description": "软件工程研究生项目",
        "confidence": 0.95
    }
}
```

**重要说明**:
- 中心节点显示用户的当前教育背景和申请目标
- 学校层只显示目标院校，不包含当前学校
- 通过关系类型区分：INTERESTED_IN（感兴趣）、APPLIED_TO（已申请）、ADMITTED_TO（已录取）

---

### 人际关系星图构建流程

```
neo4j_relationship_kg.py
         ↓
1. 查询用户数据
   ├─ User节点
   ├─ Entity(Person)节点（从对话提取的人物）
   └─ Event节点（涉及人物的事件）
         ↓
2. 查询关系数据
   ├─ User-KNOWS-Entity关系
   ├─ Entity-RELATED_TO-Entity关系
   └─ Event-INVOLVES-Entity关系
         ↓
3. 计算亲密度
   ├─ 互动频率
   ├─ 关系类型（家人/朋友/同事）
   └─ 共同事件数量
         ↓
4. 生成3D坐标
   ├─ Fibonacci球面分布
   └─ 根据亲密度调整距离
         ↓
5. 返回可视化数据
   ├─ nodes: [{id, label, type, position, ...}]
   ├─ edges: [{source, target, type, ...}]
   └─ metadata: {total_nodes, total_edges, ...}
```

---

## 初始化步骤

### 1. 环境准备

确保Neo4j数据库已安装并运行:
```bash
# 检查Neo4j状态
neo4j status

# 启动Neo4j（如果未运行）
neo4j start
```

配置数据库连接（`backend/database/config.py`）:
```python
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_password"
```

---

### 2. 执行初始化脚本

**方法一：使用Python脚本（推荐）**

```bash
cd backend
python -m database.init_neo4j
```

该脚本会自动执行以下操作:
1. 清除旧数据（删除所有节点和关系）
2. 创建唯一性约束
3. 创建索引
4. 插入示例数据（可选）

**方法二：手动执行Cypher脚本**

```bash
# 在Neo4j浏览器中执行
cat backend/database/neo4j_schema.cypher | cypher-shell -u neo4j -p your_password
```

---

### 3. 验证初始化

检查约束和索引:
```cypher
// 查看所有约束
SHOW CONSTRAINTS;

// 查看所有索引
SHOW INDEXES;
```

检查示例数据:
```cypher
// 查看节点数量
MATCH (n) RETURN labels(n) AS label, count(n) AS count;

// 查看关系数量
MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count;
```

---

## 查询示例

### 用户相关查询

#### 1. 查询用户完整画像

```cypher
// 查询用户及其所有关联信息
MATCH (u:User {user_id: 'user_001'})
OPTIONAL MATCH (u)-[r1]->(e:Entity)
OPTIONAL MATCH (u)-[r2]->(c:Concept)
OPTIONAL MATCH (u)-[r3]->(ev:Event)
OPTIONAL MATCH (u)-[r4]->(p:Pattern)
RETURN u, 
       collect(DISTINCT e) AS entities,
       collect(DISTINCT c) AS concepts,
       collect(DISTINCT ev) AS events,
       collect(DISTINCT p) AS patterns;
```

#### 2. 查询用户的技能树

```cypher
// 查询用户拥有的所有技能
MATCH (u:User {user_id: 'user_001'})-[:HAS_PROFILE]->(c:Concept {type: 'Skill'})
RETURN c.name AS skill, c.level AS level, c.confidence AS confidence
ORDER BY c.confidence DESC;
```

#### 3. 查询用户的社交网络

```cypher
// 查询用户认识的所有人及其关系
MATCH (u:User {user_id: 'user_001'})-[r:KNOWS]->(p:Entity {type: 'Person'})
RETURN p.name AS person, 
       r.relationship_type AS relationship,
       r.closeness AS closeness,
       r.since AS since
ORDER BY r.closeness DESC;
```

---

### 职业星图查询

#### 1. 查询用户提取的职位信息

```cypher
// 查询用户关注的所有职位
MATCH (u:User {user_id: 'user_001'})-[:INTERESTED_IN]->(e:Entity {type: 'Job'})
RETURN e.name AS job_title,
       e.attributes.company AS company,
       e.attributes.location AS location,
       e.attributes.salary AS salary,
       e.description AS description
ORDER BY e.extracted_at DESC;
```

#### 2. 查询用户申请的职位状态

```cypher
// 查询用户的求职进度
MATCH (u:User {user_id: 'user_001'})-[r:APPLIED_TO]->(e:Entity {type: 'Job'})
RETURN e.name AS job_title,
       e.attributes.company AS company,
       r.status AS status,
       r.applied_at AS applied_at
ORDER BY r.applied_at DESC;
```

#### 3. 查询职位相关的面试事件

```cypher
// 查询用户的面试记录
MATCH (u:User {user_id: 'user_001'})-[:PARTICIPATED_IN]->(ev:Event {type: 'Interview'})
MATCH (ev)-[:INVOLVES]->(e:Entity {type: 'Job'})
RETURN ev.name AS interview,
       e.name AS job_title,
       ev.start_time AS time,
       ev.location AS location,
       ev.description AS notes
ORDER BY ev.start_time DESC;
```

---

### 教育星图查询

#### 1. 查询用户提取的学校信息

```cypher
// 查询用户关注的所有学校
MATCH (u:User {user_id: 'user_001'})-[:INTERESTED_IN]->(e:Entity {type: 'School'})
RETURN e.name AS school,
       e.attributes.major AS major,
       e.attributes.location AS location,
       e.attributes.level AS level,
       e.attributes.tier AS tier,
       e.attributes.ranking AS ranking,
       e.description AS description
ORDER BY e.extracted_at DESC;
```

#### 2. 查询用户的教育背景（中心节点信息）

```cypher
// 查询用户的完整教育背景（用于中心节点）
MATCH (u:User {user_id: 'user_001'})
RETURN u.user_id AS student_id,
       u.education_level AS current_school,
       u.major AS major,
       // 注意：GPA、标化成绩等详细信息存储在应用层的EducationUserProfile中
       // 这里只返回User节点的基础信息
       u.location AS location,
       u.interests AS interests;
```

#### 3. 查询目标院校（排除当前学校）

```cypher
// 查询用户的目标院校列表（不包含当前学校）
MATCH (u:User {user_id: 'user_001'})-[r]->(e:Entity {type: 'School'})
WHERE type(r) IN ['INTERESTED_IN', 'APPLIED_TO', 'ADMITTED_TO']
  AND e.name <> u.education_level  // 排除当前学校
RETURN e.name AS school,
       type(r) AS relation_type,
       e.attributes.major AS major,
       e.attributes.level AS level,
       e.attributes.tier AS tier,
       e.attributes.ranking AS ranking,
       r.interest_level AS interest_level
ORDER BY r.interest_level DESC, e.attributes.ranking ASC;
```

#### 4. 查询用户的教育背景

```cypher
// 查询用户的学习经历
MATCH (u:User {user_id: 'user_001'})-[r:APPLIED_TO]->(e:Entity {type: 'School'})
RETURN e.name AS school,
       e.attributes.major AS major,
       r.status AS status,
       r.applied_at AS applied_at
ORDER BY r.applied_at DESC;
```

#### 5. 查询学校相关的事件

```cypher
// 查询用户的校园活动
MATCH (u:User {user_id: 'user_001'})-[:PARTICIPATED_IN]->(ev:Event)
MATCH (ev)-[:HAPPENED_AT]->(e:Entity {type: 'School'})
RETURN ev.name AS event,
       e.name AS school,
       ev.start_time AS time,
       ev.description AS description
ORDER BY ev.start_time DESC;
```

---

### 人际关系星图查询

#### 1. 查询用户的核心社交圈

```cypher
// 查询亲密度最高的前10个人
MATCH (u:User {user_id: 'user_001'})-[r:KNOWS]->(p:Entity {type: 'Person'})
RETURN p.name AS person,
       p.description AS description,
       r.relationship_type AS relationship,
       r.closeness AS closeness
ORDER BY r.closeness DESC
LIMIT 10;
```

#### 2. 查询共同好友

```cypher
// 查询用户和某人的共同好友
MATCH (u:User {user_id: 'user_001'})-[:KNOWS]->(friend:Entity {type: 'Person'})
MATCH (target:Entity {name: '李四'})-[:RELATED_TO]->(friend)
RETURN friend.name AS common_friend,
       friend.description AS description
ORDER BY friend.name;
```

#### 3. 查询社交网络的二度连接

```cypher
// 查询用户的二度人脉
MATCH (u:User {user_id: 'user_001'})-[:KNOWS]->(p1:Entity {type: 'Person'})-[:RELATED_TO]->(p2:Entity {type: 'Person'})
WHERE NOT (u)-[:KNOWS]->(p2)
RETURN p2.name AS person,
       p2.description AS description,
       p1.name AS introduced_by,
       count(*) AS connection_count
ORDER BY connection_count DESC
LIMIT 20;
```

---

### 信息溯源查询

#### 1. 查询某个实体的来源

```cypher
// 追溯实体信息的原始来源
MATCH (e:Entity {name: '李四'})-[:EXTRACTED_FROM]->(s:Source)
RETURN e.name AS entity,
       e.type AS type,
       s.type AS source_type,
       s.content AS source_content,
       s.timestamp AS timestamp
ORDER BY s.timestamp DESC;
```

#### 2. 查询某次对话提取的所有信息

```cypher
// 查看某次对话提取了哪些信息
MATCH (s:Source {source_id: 'conv_001'})<-[:EXTRACTED_FROM]-(n)
RETURN labels(n) AS node_type,
       n.name AS name,
       n.type AS type,
       n.confidence AS confidence
ORDER BY n.confidence DESC;
```

#### 3. 查询低置信度的信息

```cypher
// 查询需要人工确认的低置信度信息
MATCH (n)-[:EXTRACTED_FROM]->(s:Source)
WHERE n.confidence < 0.7
RETURN labels(n) AS node_type,
       n.name AS name,
       n.confidence AS confidence,
       s.content AS source_content
ORDER BY n.confidence ASC
LIMIT 20;
```

---

### 模式识别查询

#### 1. 查询用户的行为模式

```cypher
// 查询用户展现的所有模式
MATCH (u:User {user_id: 'user_001'})-[:EXHIBITS]->(p:Pattern)
RETURN p.name AS pattern,
       p.type AS type,
       p.frequency AS frequency,
       p.confidence AS confidence
ORDER BY p.confidence DESC;
```

#### 2. 查询支持某个模式的证据

```cypher
// 查看某个模式的支持证据
MATCH (p:Pattern {name: '偏好大厂工作'})<-[:SUPPORTS]-(evidence)
MATCH (evidence)-[:EXTRACTED_FROM]->(s:Source)
RETURN labels(evidence) AS evidence_type,
       evidence.name AS evidence_name,
       s.content AS source_content,
       s.timestamp AS timestamp
ORDER BY s.timestamp DESC;
```

#### 3. 查询模式之间的影响关系

```cypher
// 查询模式的影响链
MATCH path = (p1:Pattern)-[:INFLUENCES*1..3]->(p2:Pattern)
WHERE p1.name = '偏好大厂工作'
RETURN [node IN nodes(path) | node.name] AS pattern_chain,
       length(path) AS chain_length
ORDER BY chain_length ASC;
```

---

### 统计分析查询

#### 1. 数据库统计

```cypher
// 查看数据库整体统计
MATCH (n)
WITH labels(n) AS label, count(n) AS node_count
RETURN label, node_count
ORDER BY node_count DESC;

// 查看关系统计
MATCH ()-[r]->()
WITH type(r) AS rel_type, count(r) AS rel_count
RETURN rel_type, rel_count
ORDER BY rel_count DESC;
```

#### 2. 用户活跃度统计

```cypher
// 统计用户的信息提取活跃度
MATCH (u:User {user_id: 'user_001'})-[:CREATED_BY]-(s:Source)
WITH u, s.type AS source_type, count(s) AS count
RETURN source_type, count
ORDER BY count DESC;
```

#### 3. 信息质量统计

```cypher
// 统计不同类型节点的平均置信度
MATCH (n)
WHERE exists(n.confidence)
WITH labels(n) AS node_type, avg(n.confidence) AS avg_confidence, count(n) AS count
RETURN node_type, avg_confidence, count
ORDER BY avg_confidence DESC;
```

---

## 附录

### A. 数据库维护

#### 清理过期数据

```cypher
// 删除6个月前的Source节点及其关联信息
MATCH (s:Source)
WHERE s.timestamp < datetime() - duration({months: 6})
OPTIONAL MATCH (s)<-[:EXTRACTED_FROM]-(n)
DETACH DELETE s, n;
```

#### 重建索引

```cypher
// 删除所有索引
CALL db.indexes() YIELD name
CALL db.index.drop(name) YIELD name AS dropped
RETURN dropped;

// 重新创建索引（参考neo4j_schema.cypher）
```

---

### B. 性能优化建议

1. **使用索引**: 确保所有频繁查询的属性都有索引
2. **限制结果集**: 使用`LIMIT`限制返回结果数量
3. **避免全图扫描**: 使用`MATCH`时指定标签和属性
4. **使用`PROFILE`分析**: 分析查询性能瓶颈
5. **批量操作**: 使用`UNWIND`进行批量插入

---

### C. 备份与恢复

#### 备份数据库

```bash
# 停止Neo4j
neo4j stop

# 备份数据
neo4j-admin dump --database=neo4j --to=/path/to/backup.dump

# 启动Neo4j
neo4j start
```

#### 恢复数据库

```bash
# 停止Neo4j
neo4j stop

# 恢复数据
neo4j-admin load --from=/path/to/backup.dump --database=neo4j --force

# 启动Neo4j
neo4j start
```

---

### D. 相关文件

- `backend/database/neo4j_schema.cypher` - 数据库架构定义（Cypher脚本）
- `backend/database/init_neo4j.py` - 数据库初始化脚本（Python）
- `backend/database/config.py` - 数据库配置
- `backend/database/connection.py` - 数据库连接管理
- `backend/knowledge/information_extractor.py` - 信息提取器
- `backend/knowledge/information_knowledge_graph.py` - 知识图谱主类
- `backend/vertical/career/neo4j_career_kg.py` - 职业星图构建器
- `backend/vertical/education/neo4j_education_kg.py` - 教育星图构建器
- `backend/vertical/relationship/neo4j_relationship_kg.py` - 人际关系星图构建器

---

### E. EducationUserProfile 数据类

教育星图使用`EducationUserProfile`数据类来传递用户的详细教育信息。这个类定义在`backend/vertical/education/neo4j_education_kg.py`中。

**字段说明**:

```python
@dataclass
class EducationUserProfile:
    """学生学业档案"""
    student_id: str  # 用户ID，必需
    
    # 当前教育背景
    current_school: str = "未知大学"
    major: str = "计算机科学"
    gpa: float = 3.5
    gpa_max: float = 4.0
    ranking_percent: float = 0.2  # 排名百分比（前20%）
    
    # 标化成绩
    toefl_score: int = 100
    gre_score: int = 320
    sat_act: int = 1400
    
    # 各科成绩（百分制）
    math_score: float = 85.0
    english_score: float = 80.0
    professional_score: float = 82.0
    
    # 科研背景
    research_experience: float = 0.5  # 科研经历（0-1，0.5表示中等）
    publications: int = 0
    
    # 申请意向
    target_degree: str = "硕士"  # 硕士/博士/本科
    target_major: str = "计算机科学"
    target_level: str = "master"  # master/phd/bachelor
    preferred_locations: List[str] = None  # ["北京", "上海", "深圳"]
```

**使用说明**:

1. **数据来源**: 
   - User节点存储基础信息（姓名、年龄、专业等）
   - EducationUserProfile包含更详细的教育背景（GPA、标化成绩、科研经历等）
   - 应用层在构建教育星图时创建EducationUserProfile实例

2. **中心节点构建**:
   - 教育星图的中心节点（"我"）使用EducationUserProfile的所有字段
   - metadata包含完整的用户教育信息
   - 用于前端展示用户的详细背景

3. **目标院校过滤**:
   - 学校层只显示目标院校（INTERESTED_IN/APPLIED_TO/ADMITTED_TO关系）
   - 自动排除current_school，避免重复显示
   - 确保图谱清晰展示申请目标

**示例代码**:

```python
from backend.vertical.education.neo4j_education_kg import (
    Neo4jEducationKnowledgeGraph, 
    EducationUserProfile
)

# 创建用户档案
user_profile = EducationUserProfile(
    student_id="user_001",
    current_school="清华大学",
    major="计算机科学",
    gpa=3.8,
    ranking_percent=0.1,
    toefl_score=110,
    gre_score=330,
    research_experience=0.8,  # 0-1，0.8表示较强的科研经历
    target_degree="硕士",
    target_major="人工智能",
    preferred_locations=["北京", "上海"]
)

# 构建教育星图
kg = Neo4jEducationKnowledgeGraph()
graph_data = kg.build_education_graph(user_profile)

# graph_data包含：
# - nodes: 中心节点（包含完整用户信息）+ 目标院校节点
# - edges: 用户与目标院校的关系
# - metadata: 图谱统计信息
```

---

**文档版本**: 3.0  
**最后更新**: 2026-04-17  
**维护者**: Backend Team  
**联系方式**: backend@example.com

---
