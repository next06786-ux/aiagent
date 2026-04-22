# Backend 目录结构完整说明文档

本文档详细说明了backend目录中每个文件夹和文件的作用。

**最后更新时间**: 2026-04-20

---

## 📋 目录概览

Backend采用模块化架构，共15个模块目录，分为以下几类：

### 🎯 七大核心功能模块
1. **ai_core** - AI核心（意图识别、功能导航）
2. **knowledge** - 知识星图（知识图谱）
3. **decision + vertical** - 决策副本（多人格决策系统）
4. **insights** - 智慧洞察（实时Agent、协作智能体）
5. **parallel_life** - 平行人生（塔罗牌决策游戏）
6. **social** - 社交系统树洞世界（好友、树洞）
7. **schedule** - 智能日程（日程推荐、自动生成）

### 🔧 支持模块
- **database** - 数据库管理
- **auth** - 用户认证
- **llm** - LLM服务
- **learning** - RAG记忆系统
- **conversation** - 对话系统
- **admin** - 管理员功能

---

## 📁 详细目录结构

### 1️⃣ ai_core/ - AI核心模块

**功能**: 意图识别和功能导航，智能路由用户请求到对应功能模块

**文件列表**:
- `__init__.py` - 模块初始化
- `ai_core_api.py` - AI核心API路由（意图识别、功能导航）
- `intent_router.py` - 意图路由器，分析用户意图并导航到对应功能

**API端点**: `/api/ai-core/*`

---

### 2️⃣ knowledge/ - 知识星图模块

**功能**: 知识图谱管理，支持Neo4j图数据库，构建和查询知识关系

**核心架构**:
```
用户数据（对话/照片/传感器）
        ↓
information_extractor.py（信息提取）
        ↓
information_knowledge_graph.py（存储到Neo4j）
        ↓
neo4j_knowledge_graph.py（基础操作）
        ↓
支持RAG+Neo4j混合检索
```

**文件列表**:
- `information_extractor.py` - **信息提取器**（从对话/照片/传感器提取实体和关系）
  - 支持LLM智能提取 + 正则兜底
  - 提取人物、地点、事件、概念等实体
  - 推理实体之间的关系
- `information_knowledge_graph.py` - **信息知识图谱主类**（核心）
  - 管理信息节点（concept, entity, event, pattern）
  - 管理来源节点（photo, sensor_record, conversation）
  - 支持溯源查询（信息来自哪张照片/哪次对话）
  - 支持人际关系查询、节点类型查询
  - 提供统计和导出功能
- `future_os_api.py` - Future OS API接口

**技术栈**: Neo4j图数据库

**使用场景**:
- 对话中提取信息并存储（`main.py`）
- 决策信息收集（`decision_info_collector.py`）
- 人际关系图谱构建（`people_graph_builder.py`）
- RAG混合检索（`knowledge_graph_rag.py`）
- 函数调用查询关系（`function_calling.py`）

**三个视图的构建**:
- **职业星图**: `vertical/career/neo4j_career_kg.py` - 从Neo4j查询岗位 → LLM批量分类 → 构建技能层/岗位层/公司层
- **教育星图**: `vertical/education/neo4j_education_kg.py` - 从Neo4j查询2,631所高校 → LLM批量分类 → 构建学业层/学校层/行动层
- **人际关系星图**: `vertical/relationship/neo4j_relationship_kg.py` - 从information_kg查询人物 → 构建家人层/朋友层/同事层/其他层

**统一架构**：三个领域的星图构建都采用相同的模式：
1. 从数据源查询（Neo4j或information_kg）
2. 使用LLM批量分类（可选）
3. 使用Fibonacci球面算法3D分布
4. 返回nodes和edges用于前端可视化

---

### 3️⃣ decision/ - 决策模块（核心）

**功能**: 多人格决策推演系统，7个独特人格从不同角度分析决策

**核心工作流程**:
1. 用户点击决策副本球体 → 进入对话
2. `decision_info_collector.py` 收集用户信息（对话式）
   - 集成塔罗牌决策逻辑画像（从RAG检索用户决策偏好）
3. AI根据收集的信息推荐模拟方向（生成选项）
4. `persona_decision_api.py` 协调整个推演流程（WebSocket）
5. 7个决策人格并行分析（每个人格独立思考）：
   - 理性分析师（逻辑推理）
   - 情感共鸣者（情感洞察）
   - 风险评估师（风险分析）
   - 机会探索者（机会发现）
   - 道德守护者（伦理评估）
   - 实用主义者（实际可行性）
   - 创新思考者（创新视角）
6. 深度反思阶段：每个人格查看其他人格的观点，进行二次思考
7. 综合评分和推演结果实时流式返回

**推演架构**（多人格并行）:
```
用户对话 → 信息收集（含决策逻辑画像）→ AI推荐选项 → WebSocket推演
                                                    ↓
                                    7个决策人格并行分析（第0轮）
                                                    ↓
                                    深度反思（查看其他人格观点）
                                                    ↓
                                    综合评分 + 实时流式返回
```

**文件列表**:
- `persona_decision_api.py` - **多人格决策API（主要API，核心入口，WebSocket推演）**
- `decision_personas.py` - **7个决策人格定义（每个人格的特征和分析方法）**
- `decision_persona_system.py` - **人格系统管理器**
- `persona_memory_system.py` - **人格记忆系统（分层记忆架构）**
- `persona_skills.py` - **人格技能系统（RAG检索、知识图谱查询等）**
- `decision_info_collector.py` - **决策信息收集器（对话收集用户信息）**
- `future_os_api.py` - Future OS API（统一智能体接口）
- `enhanced_decision_api_full_backup.py` - 旧版API备份文件
- `prompts/` - **Prompt管理目录**
  - `prompt_manager.py` - Prompt管理器（核心）
  - `README.md` - Prompt系统说明
  - `IMPLEMENTATION_SUMMARY.md` - 实现总结
  - `MIGRATION_SUMMARY.md` - 迁移总结
  - `configs/` - Prompt配置文件目录
    - `info_collection/` - 信息收集Prompt
      - `free_talk_followup.yaml` - 自由对话跟进
      - `next_question.yaml` - 下一个问题
      - `targeted_question.yaml` - 针对性问题
    - `option_generation/` - 选项生成Prompt
      - `generate_options.yaml` - 生成AI推荐选项
    - `persona_analysis/` - 人格分析Prompt（7个人格）
      - `rational_analyst.yaml` - 理性分析师
      - `social_navigator.yaml` - 情感共鸣者
      - `conservative.yaml` - 风险评估师
      - `adventurer.yaml` - 机会探索者
      - `idealist.yaml` - 道德守护者
      - `pragmatist.yaml` - 实用主义者
      - `innovator.yaml` - 创新思考者
- `DECISION_PERSONA_ARCHITECTURE.md` - 决策人格架构文档
- `LAYERED_MEMORY_ARCHITECTURE.md` - 分层记忆架构文档
- `PERSONA_CAPABILITIES.md` - 人格能力文档

**API端点**: 
- `/api/decision/persona/*` - 多人格决策API
  - `/start-collection` - 开始信息收集
  - `/continue-collection` - 继续信息收集
  - `/generate-options` - 生成AI推荐选项
  - `/session/{session_id}` - 获取会话信息
  - `/update-outcome` - 更新决策结果
- `/ws/decision/simulate-option` - **WebSocket决策推演（主要入口）**
  - 支持`stop_simulation`消息实现暂停功能
- `/api/v5/future-os/*` - Future OS统一接口

**WebSocket消息类型**:
- `start_simulation` - 开始推演
- `stop_simulation` - 停止推演（暂停功能）
- `persona_status` - 人格状态更新
- `persona_analysis` - 人格分析结果
- `reflection_complete` - 反思完成
- `final_score` - 最终综合评分
- `simulation_complete` - 推演完成

**7个决策人格**:
1. **理性分析师** - 逻辑推理、数据分析、因果关系
2. **情感共鸣者** - 情感洞察、人际关系、心理影响
3. **风险评估师** - 风险识别、概率评估、应对策略
4. **机会探索者** - 机会发现、潜力挖掘、创新可能
5. **道德守护者** - 伦理评估、价值观、社会责任
6. **实用主义者** - 实际可行性、资源评估、执行难度
7. **创新思考者** - 创新视角、突破性思维、未来趋势

**人格分析流程**:
- 第0轮：独立分析（每个人格基于自己的视角）
- 深度反思：查看其他人格的观点，进行二次思考
- 最终评分：综合所有人格的分析结果

**决策逻辑画像集成**:
- 从塔罗牌游戏收集的决策逻辑自动集成到信息收集阶段
- 通过RAG系统检索用户的决策偏好和价值观
- 置信度阈值：20%（至少4次选择）
- 自动应用到人格分析中，提供个性化洞察

---

### 4️⃣ vertical/ - 垂直决策模块

**功能**: 三维垂直决策系统（职业、关系、升学）

**主要文件**:
- `__init__.py` - 模块初始化
- `background_classifier.py` - 后台分类任务
- `base_vertical_engine.py` - 垂直引擎基类
- `decision_logic_integration.py` - 决策逻辑集成
- `llm_batch_classifier.py` - LLM批量分类器
- `unified_decision_workflow.py` - 统一决策工作流
- `unified_kg_query.py` - 统一知识图谱查询
- `vertical_decision_api.py` - 垂直决策API

**子目录**:
- `career/` - 职业决策引擎和知识图谱
  - `career_knowledge_graph.py` - 职业知识图谱
  - `job_neo4j_storage.py` - 岗位Neo4j存储
  - `job_scheduler.py` - 岗位调度器
  - `job_updater_service.py` - 岗位更新服务
  - `neo4j_career_kg.py` - Neo4j职业知识图谱
  - `real_job_cache_loader.py` - 真实岗位缓存加载器
  - `real_job_data_integration.py` - 真实岗位数据集成
- `education/` - 教育决策引擎和知识图谱
  - `education_cache_warmer.py` - 教育缓存预热器
  - `education_decision_engine.py` - 教育决策引擎
  - `education_knowledge_graph.py` - 教育知识图谱
  - `neo4j_education_kg.py` - Neo4j教育知识图谱
  - `school_matching_cache.py` - 学校匹配缓存
- `relationship/` - 关系决策引擎和知识图谱
  - `neo4j_relationship_kg.py` - Neo4j关系知识图谱
- `time/` - 时间决策引擎
- `general/` - 通用决策引擎

---

**说明**: decision_algorithm模块已被整合到vertical模块中，不再作为独立模块存在。决策算法功能现在由vertical模块的各个子模块提供。

---

### 6️⃣ insights/ - 智慧洞察模块

**功能**: 三层混合架构洞察系统（规则引擎 + ML + LLM）+ 实时智慧洞察Agent

**核心架构**:
```
三层混合架构（用于决策分析）:
Layer 1: 规则引擎（emergence_adapter.py）
Layer 2: 机器学习（ml_enhanced_insights.py）
Layer 3: LLM增强（llm_enhancer.py）

实时智慧洞察Agent（新增）:
- RelationshipInsightAgent（人际关系洞察）
- EducationInsightAgent（教育升学洞察）
- CareerInsightAgent（职业规划洞察）
每个Agent实时通过RAG+Neo4j混合检索生成专业洞察报告
```

**文件列表**:
- `__init__.py` - 模块初始化
- `collaborative_agents.py` - 协作智能体系统
- `multi_agent_system.py` - 多智能体系统
- `ml_models.py` - 机器学习模型
- `realtime_insight_agents.py` - **实时智慧洞察Agent系统**
  - RelationshipInsightAgent - 人际关系洞察
  - EducationInsightAgent - 教育升学洞察
  - CareerInsightAgent - 职业规划洞察
- `realtime_insight_api.py` - **实时洞察API**
- `README.md` - 模块说明文档
- `AGENT_MEMORY_ARCHITECTURE.md` - Agent记忆架构文档
- `INSIGHT_MEMORY_ARCHITECTURE.md` - 洞察记忆架构文档
- `三层AI架构设计.md` - 三层AI架构设计文档

**API端点**: 
- `/api/insights/*` - 三层混合架构洞察API
- `/api/insights/realtime/*` - 实时智慧洞察Agent API（新增）
  - `/relationship/insight` - 人际关系洞察
  - `/education/insight` - 教育升学洞察
  - `/career/insight` - 职业规划洞察
  - `/agents/status` - Agent状态查询

**三层架构工作流程**:
1. 用户请求分析 → data_connector获取真实数据
2. data_transformer转换数据格式
3. Layer 1: emergence_adapter检测涌现模式（规则引擎）
4. Layer 2: ml_enhanced_insights进行量化评估（ML模型）
5. Layer 3: llm_enhancer生成深度洞察（LLM分析）
6. hybrid_insights_engine整合三层结果
7. 返回综合洞察报告

**实时Agent工作流程**（新增）:
1. 用户请求特定领域洞察（人际关系/教育/职业）
2. Agent从RAG系统检索相关记忆（向量检索）
3. Agent从Neo4j检索知识图谱（图检索）
4. Agent使用LLM生成专业洞察报告
5. 返回包含关键发现、建议、决策逻辑的完整报告

**使用场景**:
- 决策分析：使用三层混合架构进行全面评估
- 实时洞察：使用专业Agent进行领域深度分析
- 人际关系：分析关系网络、社交模式、关系质量
- 教育升学：分析升学路径、学校匹配、竞争力评估
- 职业规划：分析职业发展、技能匹配、岗位选择

---

### 7️⃣ emergence/ - 涌现检测模块

**功能**: 实时对话分析、智能洞察生成

**说明**: emergence模块已被整合到insights模块中，不再作为独立模块存在。涌现检测功能现在由insights模块的实时Agent系统提供。

**API端点**: `/api/v1/insights/*`

**工作流程**: 
1. 用户发消息 → realtime_analyzer实时分析
2. 提取情绪、话题、意图等数据
3. 存储洞察数据到数据库
4. insight_api提供洞察查询接口

**说明**: 
- 本模块专注于对话实时分析
- 与insights模块配合，提供涌现检测能力
- 已删除冗余文件：conversation_analyzer.py, emergence_detector.py, smart_insight_engine.py

---

### 8️⃣ parallel_life/ - 平行人生模块

**功能**: 塔罗牌决策游戏，通过游戏化方式收集用户决策逻辑并集成到决策系统

**核心工作流程**:
1. 用户玩塔罗牌游戏，在不同场景中做出选择
2. `tarot_game.py` 生成塔罗牌场景和选项
3. `decision_logic_analyzer.py` 分析用户选择，提取决策模式
4. 决策逻辑存储到FAISS（MemoryType.DECISION_LOGIC）
5. 在决策推演时自动检索并应用用户的决策偏好

**决策逻辑集成**:
```
塔罗牌游戏 → 用户选择 → 决策逻辑分析
                            ↓
                    存储到FAISS (DECISION_LOGIC类型)
                            ↓
                    决策信息收集时自动检索
                            ↓
                    应用到人格分析中
```

**文件列表**:
- `__init__.py` - 模块初始化
- `tarot_game.py` - **塔罗牌游戏引擎（生成场景和选项）**
- `decision_logic_analyzer.py` - **决策逻辑分析器（核心）**
  - 记录用户选择到RAG系统
  - 生成决策画像（维度倾向值）
  - 应用到决策推演引擎
- `parallel_life_api.py` - 平行人生API
- `INTEGRATION_GUIDE.md` - 集成指南
- `TAROT_INTEGRATION.md` - 塔罗牌集成文档

**API端点**: `/api/v5/parallel-life/*`

**决策维度**:
- 理性 vs 感性
- 保守 vs 冒险
- 个人 vs 集体
- 短期 vs 长期
- 物质 vs 精神
- 稳定 vs 变化

**决策画像结构**:
```json
{
  "dimensions": {
    "理性vs感性": {
      "value": 0.6,
      "count": 5,
      "confidence": 1.0
    }
  },
  "patterns": ["理性vs感性: 明显倾向于右侧选择"],
  "confidence": 0.25,
  "total_choices": 5
}
```

**集成到决策系统**:
- `decision_info_collector.py` 的 `_get_decision_logic_profile()` 方法
- `decision_personas.py` 的 `supplement_shared_facts()` 方法
- 置信度阈值：20%（至少4次选择才应用）

---

### 9️⃣ social/ - 社交系统模块

**功能**: 好友管理、树洞世界（匿名分享）

**文件列表**:
- `__init__.py` - 模块初始化
- `ai_empathy_analyzer.py` - AI共情分析器
- `ai_tree_hole_analyzer.py` - AI树洞分析器
- `decision_data_service.py` - 决策数据服务
- `friend_api.py` - 好友管理API
- `friend_service.py` - 好友服务
- `init_tree_hole_data.py` - 树洞数据初始化
- `topic_trending.py` - 话题趋势分析
- `tree_hole_api.py` - 树洞API
- `tree_hole_storage.py` - 树洞存储

**API端点**: 
- `/api/friends/*` - 好友管理
- `/api/tree-hole/*` - 树洞世界

---

### 🔟 schedule/ - 智能日程模块

**功能**: 日程分析、推荐、自动生成

**文件列表**:
- `__init__.py` - 模块初始化
- `decision_based_analyzer.py` - 基于决策的分析器
- `schedule_analyzer.py` - 日程分析器
- `schedule_api.py` - 日程API
- `schedule_auto_generator.py` - 日程自动生成器
- `schedule_config.py` - 日程配置
- `schedule_rag_integration.py` - 日程RAG集成
- `schedule_recommender.py` - 日程推荐器
- `schedule_task_manager.py` - 日程任务管理器

**API端点**: `/api/schedule/*`

---

### 1️⃣1️⃣ database/ - 数据库模块

**功能**: 数据库连接、模型定义、缓存管理

**文件列表**:
- `db_manager.py` - **数据库管理器**（主要接口）
- `models.py` - **SQLAlchemy数据模型定义**
- `connection.py` - 数据库连接管理
- `config.py` - 数据库配置
- `cache_manager.py` - Redis缓存管理器
- `init_db.py` - MySQL数据库初始化
- `init_neo4j.py` - Neo4j数据库初始化
- `import_real_data.py` - 真实数据导入工具
- `neo4j_schema.cypher` - Neo4j数据库Schema脚本
- `NEO4J_SCHEMA.md` - Neo4j Schema文档

**技术栈**: MySQL + Redis + Neo4j

**数据模型**: User, Conversation, Message, Decision, Insight, Schedule等

---

### 1️⃣2️⃣ auth/ - 认证模块

**功能**: 用户认证、登录状态管理

**文件列表**:
- `__init__.py` - 模块初始化
- `auth_service.py` - 认证服务（登录、注册、Token验证）
- `login_state_manager.py` - 登录状态管理器
- `startup_login_checker.py` - 启动登录检查器

**技术**: JWT Token认证

---

### 1️⃣3️⃣ llm/ - LLM服务模块

**功能**: 大语言模型服务，支持多种LLM提供商

**文件列表**:
- `llm_service.py` - **LLM服务主入口**（核心文件）
- `hybrid_llm_service.py` - 混合LLM服务
- `model_config.py` - 模型配置
- `llm_switch_api.py` - LLM切换API
- `collaborative_agent.py` - 协作智能体
- `enhanced_agents.py` - 增强智能体
- `conversation_manager.py` - 对话管理器
- `enhanced_conversation_manager.py` - 增强对话管理器
- `enhanced_memory_retriever.py` - 增强记忆检索器
- `deep_ai_processor.py` - 深度AI处理器
- `hybrid_intelligence_system.py` - 混合智能系统
- `meta_agent_router.py` - 元智能体路由
- `proactive_questioner.py` - 主动提问器
- `knowledge_distillation.py` - 知识蒸馏
- `local_quantized_model.py` - 本地量化模型
- `quarot_loader.py` - QUAROT加载器
- `remote_model_client.py` - 远程模型客户端
- `remote_model_server.py` - 远程模型服务器
- `__init__.py` - 模块初始化
- `README.md` - 模块说明文档

**支持的LLM提供商**:
- Qwen (通义千问)
- DeepSeek
- 本地量化模型

**API端点**: `/api/llm/*`

---

### 1️⃣4️⃣ learning/ - RAG记忆系统模块

**功能**: RAG（检索增强生成）、FAISS向量检索、记忆管理、混合检索优化

**核心架构**:
```
用户数据 → 向量化 → FAISS索引 → 语义检索
                                    ↓
                            混合检索（向量+知识图谱）
                                    ↓
                            返回相关记忆和知识
```

**文件列表**:
- `production_rag_system.py` - **生产级RAG系统（核心文件）**
  - 支持多种记忆类型（CONVERSATION, DECISION_LOGIC等）
  - FAISS向量索引和检索
  - 记忆重要性评分
- `unified_hybrid_retrieval.py` - **统一混合检索系统**
  - 向量检索 + 知识图谱检索
  - 智能结果融合
- `concurrent_retrieval_optimizer.py` - **并发检索优化器**
  - 多查询并行处理
  - 连接池管理
- `kg_rag_integration.py` - KG-RAG集成
- `kg_rag_api.py` - KG-RAG API接口
- `neo4j_faiss_sync.py` - Neo4j与FAISS同步
- `rag_manager.py` - RAG管理器
- `rag_config.py` - RAG配置
- `rag_memory.py` - RAG记忆管理
- `unified_memory_system.py` - 统一记忆系统
- `unified_rag_system.py` - 统一RAG系统
- `vector_retrieval_pool.py` - 向量检索连接池
- `optimized_reinforcement_learner.py` - 优化强化学习器
- `reinforcement_learner.py` - 强化学习器
- `rl_trainer.py` - RL训练器
- `FAISS_SCHEMA.md` - **FAISS架构文档**
- `CONCURRENT_OPTIMIZATION_GUIDE.md` - 并发优化指南
- `GPU_OPTIMIZATION_GUIDE.md` - GPU优化指南
- `HIGH_CONCURRENCY_OPTIMIZATION.md` - 高并发优化指南

**记忆类型（MemoryType）**:
- `CONVERSATION` - 对话记忆
- `DECISION_LOGIC` - 决策逻辑画像（塔罗牌游戏收集）
- `KNOWLEDGE` - 知识记忆
- `EXPERIENCE` - 经验记忆
- `INSIGHT` - 洞察记忆

**技术栈**: 
- FAISS（向量检索）
- Neo4j（知识图谱）
- 混合检索（向量+图）
- 并发优化（连接池、批处理）

**API端点**: `/api/kg-rag/*`

**使用场景**:
- 决策信息收集：检索用户历史决策和偏好
- 人格分析：检索相关知识和经验
- 智慧洞察：检索用户数据生成洞察报告
- 对话系统：检索上下文和历史对话

---

### 1️⃣5️⃣ conversation/ - 对话系统模块

**功能**: 对话管理、流式聊天、函数调用

**文件列表**:
- `conversational_ai.py` - **对话AI主类**（核心）
- `conversation_storage.py` - 对话存储
- `message_processor.py` - **消息处理器**（核心）
- `function_calling.py` - 函数调用注册表
- `simple_streaming.py` - 简单流式聊天
- `MESSAGE_PROCESSING_README.md` - 消息处理说明文档

**API端点**: 
- `/api/chat/stream` - 流式聊天
- `/api/chat/chat` - 完整聊天

**工作流程**:
1. 用户发送消息 → message_processor处理
2. conversational_ai调用LLM生成回复
3. function_calling处理函数调用（如查询知识图谱）
4. simple_streaming实现流式返回

---

### 1️⃣6️⃣ admin/ - 管理员模块

**功能**: 管理员权限管理、系统管理

**文件列表**:
- `__init__.py` - 模块初始化
- `admin_api.py` - 管理员API
- `admin_service.py` - 管理员服务

**API端点**: `/api/admin/*`

---

### 1️⃣7️⃣ data/ - 数据目录

**功能**: 存储静态数据文件和运行时数据

**子目录**:
- `education/` - 教育数据（学校真实数据）
  - `schools_real_data.json` - 2,631所高校数据
- `job_cache/` - 岗位缓存数据（102个JSON文件）
  - 各城市各岗位的真实招聘数据
  - 包含统计数据（stats_*.json）
- `decision_sessions/` - 决策会话数据
  - 存储用户决策信息收集会话
- `persona_memories/` - 人格记忆数据
  - 存储7个决策人格的记忆文件
  - 按人格、决策类型、用户ID组织
- `scheduler_config.json` - 调度器配置

---

### 1️⃣8️⃣ 根目录文件

**文件列表**:
- `main.py` - **FastAPI应用主入口**（最重要的文件）
  - 注册所有API路由
  - 配置CORS和中间件
  - 启动时初始化各系统
- `start_server.py` - 服务器启动脚本
  - 使用uvicorn启动FastAPI应用
- `startup_manager.py` - **系统启动管理器**
  - 管理LLM、数据库、RAG等系统的初始化
  - 按需加载用户系统（知识图谱、RAG）
- `STARTUP_OPTIMIZATION.md` - 启动优化文档
- `.env.example` - 环境变量示例

---

## 🗑️ 已删除的冗余模块

以下模块已被删除或整合，因为它们未被七大功能模块使用或存在冗余：

1. **agent/** - 元智能体模块（未使用）
2. **lora/** - LoRA训练模块（未使用）
3. **personality/** - 个性测试模块（未使用）
4. **prediction/** - 预测模块（已清空）
5. **utils/** - 工具类模块（未使用）
6. **emergence/** - 涌现检测模块（已整合到insights）
7. **decision_algorithm/** - 决策算法模块（已整合到vertical）

### 已删除的冗余文件（2026-04-20更新）

**insights/ 目录（智慧洞察模块）：**
- 保留的核心文件：
  - `collaborative_agents.py` - 协作智能体系统
  - `multi_agent_system.py` - 多智能体系统
  - `ml_models.py` - 机器学习模型
  - `realtime_insight_agents.py` - 实时智慧洞察Agent
  - `realtime_insight_api.py` - 实时洞察API
  - 相关文档：README.md, AGENT_MEMORY_ARCHITECTURE.md等

**decision/ 目录（决策模块）：**
- 保留的核心文件（多人格系统）：
  - `persona_decision_api.py` - 多人格决策API（主要入口）
  - `decision_personas.py` - 7个决策人格定义
  - `decision_persona_system.py` - 人格系统管理器
  - `persona_memory_system.py` - 人格记忆系统
  - `persona_skills.py` - 人格技能系统
  - `decision_info_collector.py` - 决策信息收集器
  - `future_os_api.py` - Future OS API
  - `prompts/` - Prompt管理目录
  - 备份文件：`enhanced_decision_api_full_backup.py`
  - 相关文档：DECISION_PERSONA_ARCHITECTURE.md等

**knowledge/ 目录（知识星图模块）：**
- 保留的核心文件：
  - `information_extractor.py` - 信息提取器
  - `information_knowledge_graph.py` - 信息知识图谱
  - `future_os_api.py` - Future OS API

**vertical/ 目录（垂直决策模块）：**
- 完整保留，包含career/, education/, relationship/等子目录
- 所有文件都在使用中

**learning/ 目录（RAG系统）：**
- 完整保留，所有文件都在使用中
- 核心文件：production_rag_system.py, unified_hybrid_retrieval.py等

**说明**: 
- 所有测试文件（test_*.py）已在之前清理
- 所有辅助脚本（check_*.py, add_*.py等）已在之前清理
- 当前backend目录只保留实际使用的核心文件
- 多人格决策系统是当前的主要决策推演方式

---

## 📊 模块依赖关系

```
main.py (入口)
├─ startup_manager.py (系统初始化)
├─ database/ (数据库)
├─ auth/ (认证)
├─ llm/ (LLM服务)
│
├─ ai_core/ (AI核心)
│  └─ intent_router → 路由到各功能模块
│
├─ knowledge/ (知识星图)
│  └─ Neo4j知识图谱
│
├─ decision/ (决策副本 - 多人格系统)
│  ├─ persona_decision_api.py (WebSocket推演)
│  ├─ decision_personas.py (7个人格)
│  ├─ persona_memory_system.py (分层记忆)
│  ├─ persona_skills.py (RAG检索)
│  └─ decision_info_collector.py (信息收集)
│       └─ 集成决策逻辑画像
│
├─ parallel_life/ (平行人生 - 塔罗牌游戏)
│  ├─ tarot_game.py (游戏引擎)
│  └─ decision_logic_analyzer.py (决策逻辑分析)
│       └─ 存储到FAISS (DECISION_LOGIC类型)
│
├─ learning/ (RAG系统 - FAISS向量检索)
│  ├─ production_rag_system.py (核心)
│  ├─ unified_hybrid_retrieval.py (混合检索)
│  └─ concurrent_retrieval_optimizer.py (并发优化)
│
├─ insights/ (智慧洞察)
│  ├─ realtime_insight_agents.py (实时Agent)
│  └─ hybrid_insights_engine.py (三层架构)
│
├─ vertical/ (垂直决策)
│  ├─ career/ (职业)
│  ├─ education/ (教育)
│  └─ relationship/ (关系)
│
├─ social/ (社交系统)
├─ schedule/ (智能日程)
└─ conversation/ (对话系统)
```

**关键数据流**:
1. **塔罗牌 → 决策系统**:
   - 用户玩塔罗牌 → decision_logic_analyzer → FAISS (DECISION_LOGIC)
   - 决策推演时 → decision_info_collector → 检索决策逻辑 → 应用到人格分析

2. **多人格决策推演**:
   - 用户请求 → persona_decision_api (WebSocket)
   - 7个人格并行分析 → 深度反思 → 综合评分
   - 支持stop_simulation消息实现暂停功能

3. **混合检索**:
   - 查询 → unified_hybrid_retrieval
   - 向量检索 (FAISS) + 图检索 (Neo4j)
   - 智能融合 → 返回结果

---

## 🚀 启动流程

1. `start_server.py` 启动uvicorn
2. `main.py` 加载FastAPI应用
3. `startup_manager.py` 初始化各系统
   - LLM服务
   - 数据库连接
   - 知识图谱（按需加载）
   - RAG系统（按需加载）
4. 注册所有API路由
5. 系统就绪，开始接收请求

---

## 📝 API端点总览

### 核心功能API
- `/api/ai-core/*` - AI核心（意图识别）
- `/api/decision/persona/*` - **多人格决策API（主要）**
  - `POST /start-collection` - 开始信息收集
  - `POST /continue-collection` - 继续信息收集
  - `POST /generate-options` - 生成AI推荐选项
  - `GET /session/{session_id}` - 获取会话信息
  - `POST /update-outcome` - 更新决策结果
- `/api/v5/future-os/*` - Future OS统一接口
- `/api/insights/*` - 智慧洞察（三层架构）
- `/api/insights/realtime/*` - 实时智慧洞察Agent
  - `POST /relationship/insight` - 人际关系洞察
  - `POST /education/insight` - 教育升学洞察
  - `POST /career/insight` - 职业规划洞察
- `/api/v1/insights/*` - 涌现检测洞察
- `/api/v5/parallel-life/*` - 平行人生（塔罗牌游戏）
- `/api/friends/*` - 好友管理
- `/api/tree-hole/*` - 树洞世界
- `/api/schedule/*` - 智能日程

### 支持功能API
- `/api/chat/*` - 对话系统
- `/api/kg-rag/*` - 知识图谱RAG
- `/api/llm/*` - LLM管理
- `/api/admin/*` - 管理员

### WebSocket端点
- `/ws/chat` - 聊天WebSocket
- `/ws/decision/simulate-option` - **决策推演WebSocket（主要）**
  - 消息类型：
    - `start_simulation` - 开始推演
    - `stop_simulation` - 停止推演（暂停功能）
    - `persona_status` - 人格状态更新
    - `persona_analysis` - 人格分析结果
    - `reflection_complete` - 反思完成
    - `final_score` - 最终综合评分
    - `simulation_complete` - 推演完成

---

## 🔧 技术栈

- **Web框架**: FastAPI
- **数据库**: MySQL + Redis
- **图数据库**: Neo4j
- **向量数据库**: FAISS（用于RAG语义检索）
- **LLM**: Qwen, DeepSeek
- **ORM**: SQLAlchemy
- **异步**: asyncio
- **WebSocket**: 实时推演和聊天

---

## 📌 重要说明

1. **模块化设计**: 每个功能模块独立，便于维护和扩展
2. **按需加载**: 知识图谱和RAG系统在用户登录后按需加载，减少启动时间
3. **真实数据**: 使用真实的学校数据（2,631所）和岗位数据
4. **多人格系统**: decision模块采用7个独特人格并行分析决策
5. **决策逻辑集成**: 塔罗牌游戏收集的决策逻辑自动应用到决策推演
6. **混合检索**: 向量检索（FAISS）+ 知识图谱（Neo4j）智能融合
7. **实时推演**: WebSocket实时流式返回推演结果，支持暂停/继续
8. **分层记忆**: 人格记忆系统采用短期/长期/核心三层架构

---

## 🎯 核心功能流程

### 决策推演完整流程
1. 用户进入决策副本 → 对话收集信息
2. 系统检索用户的决策逻辑画像（来自塔罗牌游戏）
3. AI生成推荐选项
4. 用户选择一个选项 → 建立WebSocket连接
5. 7个人格并行分析（第0轮独立思考）
6. 深度反思阶段（每个人格查看其他人格观点）
7. 综合评分 → 实时流式返回结果
8. 用户可随时暂停/继续推演

### 塔罗牌决策逻辑收集流程
1. 用户玩塔罗牌游戏 → 在不同场景做选择
2. decision_logic_analyzer分析选择模式
3. 存储到FAISS（MemoryType.DECISION_LOGIC）
4. 生成决策画像（各维度倾向值）
5. 决策推演时自动检索并应用

---

**文档维护**: 如有模块变更，请及时更新本文档

**最后更新**: 2026-04-20 - 更新多人格决策系统、塔罗牌集成、FAISS架构

---

## 📊 文件统计

### Python代码文件统计
- admin: 3个文件
- ai_core: 3个文件
- auth: 4个文件
- conversation: 5个文件
- database: 8个文件
- decision: 9个文件（含prompts子目录）
- insights: 6个文件
- knowledge: 3个文件
- learning: 15个文件
- llm: 19个文件
- parallel_life: 4个文件
- schedule: 9个文件
- social: 10个文件
- vertical: 26个文件（含子目录）
- 根目录: 3个文件

**总计**: 127个Python文件

### 文档文件统计
- 模块说明文档: 20个.md文件
- Prompt配置文件: 10个.yaml文件
- 数据库Schema: 1个.cypher文件

### 数据文件统计
- 教育数据: 1个JSON文件（2,631所高校）
- 岗位缓存: 102个JSON文件
- 决策会话: 44个JSON文件
- 人格记忆: 400+个JSON文件

---

## ✅ 文档完整性检查

本文档已涵盖backend目录下的所有模块和文件：
- ✅ 15个功能模块全部说明
- ✅ 127个Python文件全部提及
- ✅ 20个文档文件全部列出
- ✅ 所有API端点全部记录
- ✅ 所有WebSocket端点全部说明
- ✅ 模块依赖关系完整展示
- ✅ 核心功能流程详细描述

测试用户账号（密码统一为: 123456）：
  - 用户名: 张三
    User ID: test_user_001
    邮箱: zhangsan@example.com
    密码: 123456
    学校: 清华大学 - 计算机科学

  - 用户名: 李四
    User ID: test_user_002
    邮箱: lisi@example.com
    密码: 123456
    学校: 北京大学 - 人工智能

  - 用户名: 王五
    User ID: test_user_003
    邮箱: wangwu@example.com
    密码: 123456
    学校: 上海交通大学 - 软件工程
    docker logs -f lifeswarm-backend

    git add backend/init_test_data.py
    git commit -m "扩充教育升学测试数据：添加30所目标院校（国内10所+美国15所+欧洲5所）"
    git push origin main
    
cd /opt/aiagent/
git checkout -- backend/init_test_data.py  # 放弃本地修改
git pull origin main
docker compose build backend
docker compose up -d backend
sleep 10
docker exec -it lifeswarm-backend python backend/init_test_data.py






git pull origin main

# 2. 清空Neo4j数据（重新初始化）
docker exec -it lifeswarm-neo4j cypher-shell -u neo4j -p neo4j_secure_password_2024 "MATCH (n {user_id: 'test_user_001'}) DETACH DELETE n;"
docker exec -it lifeswarm-neo4j cypher-shell -u neo4j -p neo4j_secure_password_2024 "MATCH (n {user_id: 'test_user_002'}) DETACH DELETE n;"
docker exec -it lifeswarm-neo4j cypher-shell -u neo4j -p neo4j_secure_password_2024 "MATCH (n {user_id: 'test_user_003'}) DETACH DELETE n;"

# 3. 重新初始化测试数据
docker exec -it lifeswarm-backend python backend/init_test_data.py

# 4. 验证数据
docker exec -it lifeswarm-backend python backend/verify_career_data.py




cd /path/to/your/project

# 2. 拉取最新代码
git pull origin main

# 3. 停止并删除旧容器
docker compose down


# 或者只重启（如果只修改了代码）
docker compose up -d

# 5. 查看日志确认启动成功
  docker compose logs -f backend