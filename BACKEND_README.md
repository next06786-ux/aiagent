# Backend 目录结构完整说明文档

本文档详细说明了backend目录中每个文件夹和文件的作用。

**最后更新时间**: 2026-04-18

---

## 📋 目录概览

Backend采用模块化架构，共18个模块目录，分为以下几类：

### 🎯 七大核心功能模块
1. **ai_core** - AI核心（意图识别、功能导航）
2. **knowledge** - 知识星图（知识图谱）
3. **decision + vertical + decision_algorithm** - 决策副本（三维垂直决策）
4. **insights + emergence** - 智慧洞察（涌现检测、对话分析）
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
- `neo4j_knowledge_graph.py` - **Neo4j知识图谱基础类**
  - 提供实体、关系的CRUD操作
  - 提供图谱查询和统计功能
  - 支持路径查找、中心节点分析

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

**功能**: 决策信息收集、决策推演、多智能体评估

**核心工作流程**:
1. 用户点击决策副本球体 → 进入对话
2. `decision_info_collector.py` 收集用户信息（对话式）
3. AI根据收集的信息推荐模拟方向（生成选项）
4. `enhanced_decision_api.py` 协调整个推演流程（WebSocket）
5. 根据决策类型调用对应的多智能体评估器进行推演：
   - 教育升学 → `multi_agent_education_evaluator.py` ✅ 已完整实现
   - 职业规划 → `multi_agent_career_evaluator.py` ✅ 已完整实现
   - 人际关系 → `multi_agent_relationship_evaluator.py` ✅ 已完整实现
6. 返回推演结果和时间线（12个月的演化过程）

**推演架构**（三个领域统一）:
```
用户对话 → 信息收集 → AI推荐选项 → WebSocket推演
                                    ↓
                        垂直决策引擎（vertical/）
                                    ↓
                        多智能体评估器（5个Agent并行）
                                    ↓
                        决策算法支持（decision_algorithm/）
                                    ↓
                        实时流式返回（12个月时间线）
```

**文件列表**:
- `decision_info_collector.py` - **决策信息收集器（对话收集用户信息）**
- `enhanced_decision_api.py` - **增强决策API（主要API，核心入口，包含WebSocket推演）**
- `multi_agent_career_evaluator.py` - **多智能体职业评估器（职业推演，5个Agent）**
- `multi_agent_education_evaluator.py` - **多智能体教育评估器（升学推演，5个Agent）**
- `multi_agent_relationship_evaluator.py` - **多智能体关系评估器（关系推演，5个Agent）**
- `lora_decision_analyzer.py` - **LoRA决策分析器（时间线生成、推荐生成）**
- `personal_knowledge_fusion.py` - **个人知识融合（PKF-DS，提取个人事实）**
- `review_agents.py` - 审查智能体（节点评审）
- `risk_assessment_engine.py` - 风险评估引擎（选项风险评估）
- `future_os_api.py` - Future OS API（统一智能体接口）
- `future_os_service.py` - Future OS服务

**API端点**: 
- `/api/decision/enhanced/*` - 决策信息收集和推演
- `/ws/decision-simulate` - **WebSocket决策推演（主要入口）**
- `/api/v5/future-os/*` - Future OS统一接口

**推演实现状态**:
- ✅ **教育升学推演** - 完整实现（已测试通过）
  - 垂直引擎: `vertical/education/education_decision_engine.py`
  - 多智能体: `multi_agent_education_evaluator.py` (5个Agent)
  - 算法支持: `decision_algorithm/education_decision_algorithm.py`
  
- ✅ **职业规划推演** - 完整实现（代码结构与教育一致）
  - 垂直引擎: `vertical/career/career_decision_engine.py`
  - 多智能体: `multi_agent_career_evaluator.py` (5个Agent)
  - 算法支持: `decision_algorithm/career_decision_algorithm.py`
  
- ✅ **人际关系推演** - 完整实现（代码结构与教育一致）
  - 垂直引擎: `vertical/relationship/relationship_decision_engine.py`
  - 多智能体: `multi_agent_relationship_evaluator.py` (5个Agent)
  - 算法支持: `decision_algorithm/relationship_decision_algorithm.py`

所有三个领域都采用相同的架构模式：信息收集 → AI推荐 → 多智能体推演（12个月）→ 实时流式返回

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
- `vertical_decision_api.py` - 垂直决策API

**子目录**:
- `career/` - 职业决策引擎和知识图谱
- `education/` - 教育决策引擎和知识图谱
- `relationship/` - 关系决策引擎和知识图谱
- `time/` - 时间决策引擎
- `general/` - 通用决策引擎

---

### 5️⃣ decision_algorithm/ - 决策算法模块

**功能**: 决策算法实现，提供核心决策引擎基类和知识图谱集成

**架构说明**:
- `core_decision_engine.py` 是所有垂直决策引擎（career/education/relationship）的基类
- 提供统一的决策评估接口和算法框架
- 三个算法文件负责知识图谱数据集成

**文件列表**:
- `__init__.py` - 模块初始化
- `career_decision_algorithm.py` - 职业决策算法（知识图谱集成）
- `core_decision_engine.py` - **核心决策引擎（基类）**
- `education_decision_algorithm.py` - 教育决策算法
- `relationship_decision_algorithm.py` - 关系决策算法

**说明**: 
- `core_decision_engine.py` 是所有垂直决策引擎的基类
- 三个算法文件提供知识图谱集成和数据模型定义

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
- `data_connector.py` - 数据连接器（从MySQL/Neo4j获取数据）
- `data_transformer.py` - 数据转换器（转换为分析格式）
- `emergence_adapter.py` - 涌现检测适配器（Layer 1: 规则引擎）
- `hybrid_insights_engine.py` - 混合洞察引擎（三层架构核心）
- `integrated_insights_api.py` - 集成洞察API（主要API入口）
- `llm_enhancer.py` - LLM增强器（Layer 3: LLM深度分析）
- `ml_enhanced_insights.py` - ML增强洞察（Layer 2: ML量化评估）
- `realtime_insight_agents.py` - **实时智慧洞察Agent系统（新增）**
- `realtime_insight_api.py` - **实时洞察API（新增）**
- `README.md` - 模块说明文档
- `REALTIME_AGENTS_README.md` - 实时Agent说明文档

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

**文件列表**:
- `__init__.py` - 模块初始化
- `insight_api.py` - 洞察API（对话分析、洞察生成）
- `realtime_analyzer.py` - 实时分析器（从对话中提取情绪、话题、意图）

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

**功能**: 塔罗牌决策游戏，通过游戏化方式收集用户决策逻辑

**文件列表**:
- `__init__.py` - 模块初始化
- `decision_logic_analyzer.py` - 决策逻辑分析器
- `parallel_life_api.py` - 平行人生API
- `tarot_game.py` - 塔罗牌游戏引擎

**API端点**: `/api/v5/parallel-life/*`

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
- `cache_manager.py` - Redis缓存管理器
- `config.py` - 数据库配置
- `connection.py` - 数据库连接管理
- `db_manager.py` - 数据库管理器（主要接口）
- `init_db.py` - 数据库初始化
- `models.py` - SQLAlchemy数据模型定义

**技术栈**: MySQL + Redis

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
- `__init__.py` - 模块初始化
- `auto_lora_trainer.py` - 自动LoRA训练器（已废弃）
- `collaborative_agent.py` - 协作智能体
- `conversation_manager.py` - 对话管理器
- `deep_ai_processor.py` - 深度AI处理器
- `enhanced_agents.py` - 增强智能体
- `enhanced_conversation_manager.py` - 增强对话管理器
- `enhanced_memory_retriever.py` - 增强记忆检索器
- `hybrid_intelligence_system.py` - 混合智能系统
- `hybrid_llm_service.py` - 混合LLM服务
- `knowledge_distillation.py` - 知识蒸馏
- `llm_service.py` - **LLM服务主入口**（核心文件）
- `llm_switch_api.py` - LLM切换API
- `local_quantized_model.py` - 本地量化模型
- `meta_agent_router.py` - 元智能体路由
- `model_config.py` - 模型配置
- `proactive_questioner.py` - 主动提问器
- `quarot_loader.py` - QUAROT加载器
- `README.md` - 模块说明文档
- `remote_model_client.py` - 远程模型客户端
- `remote_model_server.py` - 远程模型服务器

**支持的LLM提供商**:
- Qwen (通义千问)
- DeepSeek
- 本地量化模型

**API端点**: `/api/llm/*`

---

### 1️⃣4️⃣ learning/ - RAG记忆系统模块

**功能**: RAG（检索增强生成）、强化学习、记忆管理

**文件列表**:
- `kg_rag_api.py` - 知识图谱RAG API
- `kg_rag_integration.py` - KG-RAG集成
- `knowledge_graph_rag.py` - 知识图谱RAG
- `optimized_reinforcement_learner.py` - 优化强化学习器
- `production_rag_system.py` - **生产级RAG系统**（核心文件）
- `rag_memory.py` - RAG记忆
- `reinforcement_learner.py` - 强化学习器
- `rl_trainer.py` - RL训练器
- `unified_memory_system.py` - 统一记忆系统
- `unified_rag_system.py` - 统一RAG系统

**技术栈**: 
- 向量数据库（用于语义检索）
- 强化学习（Q-Learning, Actor-Critic）

**API端点**: `/api/kg-rag/*`

---

### 1️⃣5️⃣ conversation/ - 对话系统模块

**功能**: 对话管理、流式聊天、函数调用

**文件列表**:
- `conversation_storage.py` - 对话存储
- `conversational_ai.py` - 对话AI主类
- `function_calling.py` - 函数调用注册表
- `simple_streaming.py` - 简单流式聊天

**API端点**: 
- `/api/chat/stream` - 流式聊天
- `/api/chat/chat` - 完整聊天

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

**功能**: 存储静态数据文件

**子目录**:
- `education/` - 教育数据（学校真实数据）
  - `schools_real_data.json` - 2,631所高校数据
- `job_cache/` - 岗位缓存数据（102个JSON文件）
  - 各城市各岗位的真实招聘数据
- `scheduler_config.json` - 调度器配置

---

### 1️⃣8️⃣ 根目录文件

**文件列表**:
- `main.py` - **FastAPI应用主入口**（最重要的文件）
- `start_server.py` - 服务器启动脚本
- `startup_manager.py` - 系统启动管理器
- `STARTUP_OPTIMIZATION.md` - 启动优化文档
- `.env.example` - 环境变量示例

---

## 🗑️ 已删除的冗余模块

以下模块已被删除，因为它们未被七大功能模块使用或存在冗余：

1. **agent/** - 元智能体模块（未使用）
2. **lora/** - LoRA训练模块（未使用）
3. **personality/** - 个性测试模块（未使用）
4. **prediction/** - 预测模块（已清空，功能已迁移到emergence）
5. **utils/** - 工具类模块（未使用）

### 已删除的冗余文件（2026-04-18更新）

**insights/ 目录（智慧洞察模块清理）：**
- `decision_insight_types.py` - 决策洞察类型定义（未使用）
- `impact_chain_analyzer.py` - 影响链分析器（未使用）
- `ml_models.py` - ML模型（未使用）
- `openclaw_agents.py` - OpenClaw智能体（未使用）
- `risk_loop_detector.py` - 风险循环检测器（未使用）
- `smart_insights_engine.py` - 智能洞察引擎（未使用）

**emergence/ 目录（涌现检测模块清理）：**
- `conversation_analyzer.py` - 对话分析器（未使用）
- `emergence_detector.py` - 涌现检测器（未使用）
- `smart_insight_engine.py` - 智能洞察引擎（未使用）

**新增文件（2026-04-18）：**
- `insights/realtime_insight_agents.py` - 实时智慧洞察Agent系统
  - RelationshipInsightAgent - 人际关系洞察Agent
  - EducationInsightAgent - 教育升学洞察Agent
  - CareerInsightAgent - 职业规划洞察Agent
- `insights/realtime_insight_api.py` - 实时洞察API接口
- `insights/REALTIME_AGENTS_README.md` - 实时Agent说明文档

**清理说明**:
- insights和emergence模块存在大量冗余文件，已清理未使用的文件
- 保留实际被前端调用的核心文件
- 新增三个专业领域的实时洞察Agent，通过RAG+Neo4j混合检索生成智慧洞察报告

**decision/ 目录：**
- `decision_engine.py` - 旧版决策引擎（已废弃）
- `decision_type_selector.py` - 决策类型选择器（功能已集成）
- `enhanced_info_collector.py` - 增强信息收集器（未使用）
- `counterfactual_analyzer.py` - 反事实分析器（未实现）
- `career_simulation_agents.py` - 职业模拟智能体（未使用）
- `career_simulation_api.py` - 职业模拟API（未注册）
- `career_simulation_integration.py` - 职业模拟集成（仅在废弃API中使用）
- `multi_agent_career_simulator.py` - 多智能体职业模拟器（未使用）
- `education_api.py` - 教育升学辅助API（未使用）
- `relationship_api.py` - 人际关系辅助API（未使用）
- `integrated_decision_engine.py` - 集成决策引擎（仅在废弃API中使用）
- `real_data_sources.py` - 真实数据源（未使用）
- `websocket_keepalive.py` - WebSocket保活管理（未使用）

**decision_algorithm/ 目录：**
- `ml_enhanced_career_model.py` - ML增强职业模型（未使用）

**knowledge/ 目录：**
- `automated_kg_builder.py` - 自动知识图谱构建器（未集成）
- `enhanced_neo4j_knowledge_graph.py` - 增强版Neo4j知识图谱（未集成）
- `personal_knowledge_graph.py` - 个人知识图谱（未集成）

**vertical/relationship/ 目录：**
- `people_graph_builder.py` - 旧版人物关系图谱构建器（已统一使用neo4j_relationship_kg.py）
- `relationship_knowledge_graph.py` - 空文件（已删除）

**说明**: 
- WebSocket推演是真正的用户流程，decision核心文件只有11个
- knowledge模块保留3个实际使用的核心文件
- 三个领域的星图构建已完全统一架构，都使用neo4j_*_kg.py文件，采用相同的代码结构

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
├─ decision/ (决策副本)
│  ├─ vertical/ (垂直决策)
│  └─ decision_algorithm/ (决策算法)
│
├─ insights/ (智慧洞察)
│  └─ emergence/ (涌现检测)
│
├─ parallel_life/ (平行人生)
├─ social/ (社交系统)
├─ schedule/ (智能日程)
│
├─ learning/ (RAG系统)
└─ conversation/ (对话系统)
```

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
- `/api/v5/future-os/*` - Future OS统一接口
- `/api/v5/decision/*` - 决策推演
- `/api/v5/relationship/*` - 人际关系决策
- `/api/v5/education/*` - 教育升学决策
- `/api/insights/*` - 智慧洞察
- `/api/v1/insights/*` - 涌现检测洞察
- `/api/v5/parallel-life/*` - 平行人生
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
- `/ws/decision-simulate` - 决策推演WebSocket

---

## 🔧 技术栈

- **Web框架**: FastAPI
- **数据库**: MySQL + Redis
- **图数据库**: Neo4j
- **LLM**: Qwen, DeepSeek
- **向量数据库**: 用于RAG
- **ORM**: SQLAlchemy
- **异步**: asyncio

---

## 📌 重要说明

1. **模块化设计**: 每个功能模块独立，便于维护和扩展
2. **按需加载**: 知识图谱和RAG系统在用户登录后按需加载，减少启动时间
3. **真实数据**: 使用真实的学校数据（2,631所）和岗位数据
4. **三层架构**: insights模块采用规则引擎+ML+LLM的三层混合架构
5. **多智能体**: decision模块使用多智能体协作进行决策评估

---

**文档维护**: 如有模块变更，请及时更新本文档

