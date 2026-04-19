// ============================================
// Neo4j 数据库架构初始化脚本
// 版本: 3.0
// 更新时间: 2026-04-17
// 说明: 纯用户数据架构，只存储从对话/照片/传感器提取的信息
// ============================================

// ============================================
// 1. 清除旧数据（谨慎使用！）
// ============================================
MATCH (n) DETACH DELETE n;

// ============================================
// 2. 创建唯一性约束
// ============================================

// User节点约束
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.user_id IS UNIQUE;

// Entity节点约束
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE;

// Event节点约束
CREATE CONSTRAINT event_id_unique IF NOT EXISTS
FOR (ev:Event) REQUIRE ev.event_id IS UNIQUE;

// Concept节点约束
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
FOR (c:Concept) REQUIRE c.concept_id IS UNIQUE;

// Pattern节点约束
CREATE CONSTRAINT pattern_id_unique IF NOT EXISTS
FOR (p:Pattern) REQUIRE p.pattern_id IS UNIQUE;

// Source节点约束
CREATE CONSTRAINT source_id_unique IF NOT EXISTS
FOR (s:Source) REQUIRE s.source_id IS UNIQUE;

// ============================================
// 3. 创建索引（提升查询性能）
// ============================================

// User索引
CREATE INDEX user_name_index IF NOT EXISTS
FOR (u:User) ON (u.name);

CREATE INDEX user_location_index IF NOT EXISTS
FOR (u:User) ON (u.location);

// Entity索引
CREATE INDEX entity_name_index IF NOT EXISTS
FOR (e:Entity) ON (e.name);

CREATE INDEX entity_type_index IF NOT EXISTS
FOR (e:Entity) ON (e.type);

CREATE INDEX entity_category_index IF NOT EXISTS
FOR (e:Entity) ON (e.category);

CREATE INDEX entity_extracted_at_index IF NOT EXISTS
FOR (e:Entity) ON (e.extracted_at);

// Event索引
CREATE INDEX event_type_index IF NOT EXISTS
FOR (ev:Event) ON (ev.type);

CREATE INDEX event_start_time_index IF NOT EXISTS
FOR (ev:Event) ON (ev.start_time);

// Concept索引
CREATE INDEX concept_type_index IF NOT EXISTS
FOR (c:Concept) ON (c.type);

CREATE INDEX concept_name_index IF NOT EXISTS
FOR (c:Concept) ON (c.name);

// Pattern索引
CREATE INDEX pattern_type_index IF NOT EXISTS
FOR (p:Pattern) ON (p.type);

// Source索引
CREATE INDEX source_type_index IF NOT EXISTS
FOR (s:Source) ON (s.type);

CREATE INDEX source_timestamp_index IF NOT EXISTS
FOR (s:Source) ON (s.timestamp);

// ============================================
// 4. 插入示例数据（可选）
// ============================================

// 创建示例用户
CREATE (u:User {
  user_id: 'user_demo',
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
});

// 创建示例对话来源
CREATE (s1:Source {
  source_id: 'conv_demo_001',
  type: 'Conversation',
  content: '我大学同学李四现在在阿里工作，做算法工程师，薪资很不错。',
  timestamp: datetime('2026-04-15T10:30:00'),
  metadata: {session_id: 'session_demo', turn: 1}
});

CREATE (s2:Source {
  source_id: 'conv_demo_002',
  type: 'Conversation',
  content: '下周三下午2点要去字节跳动面试Python后端工程师岗位。',
  timestamp: datetime('2026-04-16T14:20:00'),
  metadata: {session_id: 'session_demo', turn: 5}
});

CREATE (s3:Source {
  source_id: 'conv_demo_003',
  type: 'Conversation',
  content: '我想申请清华大学计算机系的研究生，专业是人工智能方向。',
  timestamp: datetime('2026-04-17T09:15:00'),
  metadata: {session_id: 'session_demo', turn: 10}
});

// 创建示例实体 - 人物
CREATE (e1:Entity {
  entity_id: 'entity_demo_001',
  name: '李四',
  type: 'Person',
  category: 'friend',
  description: '大学同学，现在在阿里工作',
  attributes: {role: '同学', company: '阿里巴巴', position: '算法工程师', relationship: '朋友'},
  confidence: 0.95,
  extracted_at: datetime('2026-04-15T10:30:00'),
  source_id: 'conv_demo_001'
});

// 创建示例实体 - 职位
CREATE (e2:Entity {
  entity_id: 'entity_demo_002',
  name: 'Python后端工程师',
  type: 'Job',
  category: 'position',
  description: '字节跳动招聘的后端岗位',
  attributes: {company: '字节跳动', salary: '30k-50k', location: '北京', requirements: ['Python', 'Django', 'MySQL']},
  confidence: 0.92,
  extracted_at: datetime('2026-04-16T14:20:00'),
  source_id: 'conv_demo_002'
});

// 创建示例实体 - 学校
CREATE (e3:Entity {
  entity_id: 'entity_demo_003',
  name: '清华大学',
  type: 'School',
  category: 'university',
  description: '计算机系研究生项目',
  attributes: {major: '人工智能', level: 'master', location: '北京'},
  confidence: 0.98,
  extracted_at: datetime('2026-04-17T09:15:00'),
  source_id: 'conv_demo_003'
});

// 创建示例事件 - 面试
CREATE (ev1:Event {
  event_id: 'event_demo_001',
  name: '字节跳动面试',
  type: 'Interview',
  description: 'Python后端工程师岗位面试',
  start_time: datetime('2026-04-23T14:00:00'),
  location: '北京字节跳动总部',
  participants: ['面试官', '我'],
  confidence: 0.92,
  extracted_at: datetime('2026-04-16T14:20:00'),
  source_id: 'conv_demo_002'
});

// 创建示例概念 - 技能
CREATE (c1:Concept {
  concept_id: 'concept_demo_001',
  name: 'Python编程',
  type: 'Skill',
  description: '熟练使用Python进行后端开发',
  level: '高级',
  confidence: 0.98,
  extracted_at: datetime('2026-04-15T10:30:00'),
  source_id: 'conv_demo_001'
});

CREATE (c2:Concept {
  concept_id: 'concept_demo_002',
  name: 'Django框架',
  type: 'Skill',
  description: 'Django Web框架开发经验',
  level: '中级',
  confidence: 0.90,
  extracted_at: datetime('2026-04-15T10:30:00'),
  source_id: 'conv_demo_001'
});

// 创建示例模式 - 职业偏好
CREATE (p1:Pattern {
  pattern_id: 'pattern_demo_001',
  name: '偏好大厂工作',
  type: 'Preference',
  description: '用户在职业选择中倾向于选择大型互联网公司',
  frequency: 3,
  confidence: 0.85,
  identified_at: datetime('2026-04-17T10:00:00'),
  evidence: ['conv_demo_001', 'conv_demo_002']
});

// ============================================
// 5. 创建关系
// ============================================

// 用户关系
MATCH (u:User {user_id: 'user_demo'})
MATCH (e1:Entity {entity_id: 'entity_demo_001'})
CREATE (u)-[:KNOWS {relationship_type: 'friend', closeness: 0.8, since: datetime('2020-09-01')}]->(e1);

MATCH (u:User {user_id: 'user_demo'})
MATCH (e2:Entity {entity_id: 'entity_demo_002'})
CREATE (u)-[:INTERESTED_IN {interest_level: 0.9, timestamp: datetime('2026-04-16T14:20:00')}]->(e2);

MATCH (u:User {user_id: 'user_demo'})
MATCH (e3:Entity {entity_id: 'entity_demo_003'})
CREATE (u)-[:INTERESTED_IN {interest_level: 0.95, timestamp: datetime('2026-04-17T09:15:00')}]->(e3);

MATCH (u:User {user_id: 'user_demo'})
MATCH (c1:Concept {concept_id: 'concept_demo_001'})
CREATE (u)-[:HAS_PROFILE {since: datetime('2021-01-01'), confidence: 0.98}]->(c1);

MATCH (u:User {user_id: 'user_demo'})
MATCH (c2:Concept {concept_id: 'concept_demo_002'})
CREATE (u)-[:HAS_PROFILE {since: datetime('2022-03-01'), confidence: 0.90}]->(c2);

MATCH (u:User {user_id: 'user_demo'})
MATCH (ev1:Event {event_id: 'event_demo_001'})
CREATE (u)-[:PARTICIPATED_IN {role: 'candidate', timestamp: datetime('2026-04-16T14:20:00')}]->(ev1);

MATCH (u:User {user_id: 'user_demo'})
MATCH (p1:Pattern {pattern_id: 'pattern_demo_001'})
CREATE (u)-[:EXHIBITS {frequency: 3, confidence: 0.85}]->(p1);

// 信息溯源关系
MATCH (e1:Entity {entity_id: 'entity_demo_001'})
MATCH (s1:Source {source_id: 'conv_demo_001'})
CREATE (e1)-[:EXTRACTED_FROM {extraction_method: 'LLM', confidence: 0.95}]->(s1);

MATCH (e2:Entity {entity_id: 'entity_demo_002'})
MATCH (s2:Source {source_id: 'conv_demo_002'})
CREATE (e2)-[:EXTRACTED_FROM {extraction_method: 'LLM', confidence: 0.92}]->(s2);

MATCH (e3:Entity {entity_id: 'entity_demo_003'})
MATCH (s3:Source {source_id: 'conv_demo_003'})
CREATE (e3)-[:EXTRACTED_FROM {extraction_method: 'LLM', confidence: 0.98}]->(s3);

MATCH (ev1:Event {event_id: 'event_demo_001'})
MATCH (s2:Source {source_id: 'conv_demo_002'})
CREATE (ev1)-[:EXTRACTED_FROM {extraction_method: 'LLM', confidence: 0.92}]->(s2);

MATCH (c1:Concept {concept_id: 'concept_demo_001'})
MATCH (s1:Source {source_id: 'conv_demo_001'})
CREATE (c1)-[:EXTRACTED_FROM {extraction_method: 'LLM', confidence: 0.98}]->(s1);

MATCH (c2:Concept {concept_id: 'concept_demo_002'})
MATCH (s1:Source {source_id: 'conv_demo_001'})
CREATE (c2)-[:EXTRACTED_FROM {extraction_method: 'LLM', confidence: 0.90}]->(s1);

MATCH (s1:Source {source_id: 'conv_demo_001'})
MATCH (u:User {user_id: 'user_demo'})
CREATE (s1)-[:CREATED_BY {timestamp: datetime('2026-04-15T10:30:00')}]->(u);

MATCH (s2:Source {source_id: 'conv_demo_002'})
MATCH (u:User {user_id: 'user_demo'})
CREATE (s2)-[:CREATED_BY {timestamp: datetime('2026-04-16T14:20:00')}]->(u);

MATCH (s3:Source {source_id: 'conv_demo_003'})
MATCH (u:User {user_id: 'user_demo'})
CREATE (s3)-[:CREATED_BY {timestamp: datetime('2026-04-17T09:15:00')}]->(u);

// 实体间关系
MATCH (ev1:Event {event_id: 'event_demo_001'})
MATCH (e2:Entity {entity_id: 'entity_demo_002'})
CREATE (ev1)-[:INVOLVES {role: 'target_position'}]->(e2);

MATCH (e2:Entity {entity_id: 'entity_demo_002'})
MATCH (c1:Concept {concept_id: 'concept_demo_001'})
CREATE (e2)-[:REQUIRES {importance: 'high', level: 'advanced'}]->(c1);

MATCH (e2:Entity {entity_id: 'entity_demo_002'})
MATCH (c2:Concept {concept_id: 'concept_demo_002'})
CREATE (e2)-[:REQUIRES {importance: 'medium', level: 'intermediate'}]->(c2);

// 模式关系
MATCH (e1:Entity {entity_id: 'entity_demo_001'})
MATCH (p1:Pattern {pattern_id: 'pattern_demo_001'})
CREATE (e1)-[:SUPPORTS {weight: 0.7}]->(p1);

MATCH (e2:Entity {entity_id: 'entity_demo_002'})
MATCH (p1:Pattern {pattern_id: 'pattern_demo_001'})
CREATE (e2)-[:SUPPORTS {weight: 0.9}]->(p1);

// ============================================
// 6. 验证数据
// ============================================

// 查看节点统计
MATCH (n)
WITH labels(n) AS label, count(n) AS node_count
RETURN label, node_count
ORDER BY node_count DESC;

// 查看关系统计
MATCH ()-[r]->()
WITH type(r) AS rel_type, count(r) AS rel_count
RETURN rel_type, rel_count
ORDER BY rel_count DESC;

// ============================================
// 初始化完成！
// ============================================
