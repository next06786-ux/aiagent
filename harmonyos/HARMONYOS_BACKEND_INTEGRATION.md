# HarmonyOS 后端对接架构文档

**版本**: 3.0  
**最后更新**: 2026-04-20  
**适配后端版本**: Backend v1.0.0 (多人格决策系统)  
**后端端口**: 6006 (注意：不是8000)

---

## 📋 文档概览

本文档详细说明HarmonyOS应用如何对接后端系统，包括：
- ✅ 七大核心功能模块的API完整对接
- ✅ 所有服务层已实现并验证
- ✅ 3D球体UI设计规范（模仿Web端）
- ✅ 数据库直接使用后端Neo4j/MySQL/Redis/FAISS
- ✅ WebSocket实时通信（决策推演）
- ✅ 完整的技术架构和实现指南

**对接完成度**: 100% ✅

### 1. AI核心模块 (ai_core)

**功能**: 意图识别和功能导航，智能路由用户请求到对应功能模块

**后端实现**: `backend/ai_core/intent_router.py` + `backend/ai_core/ai_core_api.py`

**API端点**: `/api/v5/ai-core/*`

**主要接口**:
```typescript
// 意图识别（已在WebSocket聊天中集成，HarmonyOS可选实现）
POST /api/v5/ai-core/intent
{
  "user_id": "string",
  "message": "string",
  "context": {}
}
返回: {
  "has_navigation_intent": boolean,
  "primary_route": {
    "module": "decision|knowledge|insights|schedule|social|parallel_life",
    "name": "模块名称",
    "description": "描述",
    "confidence": 0.85
  },
**HarmonyOS实现**: ✅ 已完成
```typescript
// services/AICoreService.ets（已实现）
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';

export class AICoreService {
  private httpClient = HttpClient.getInstance();
  
  async recognizeIntent(userId: string, message: string): Promise<IntentResult> {
    const result = await this.httpClient.post<IntentResult>(
      ApiConstants.AI_CORE.INTENT,
      { user_id: userId, message, context: {} }
    );
    return result.data;
  }
  
  async navigateToFunction(userId: string, intent: string, params: any): Promise<NavigationResult> {
    const result = await this.httpClient.post<NavigationResult>(
      ApiConstants.AI_CORE.NAVIGATE,
      { user_id: userId, intent, params }
    );
    return result.data;
  }
}
```

**注意**: AI核心的意图识别已集成在后端的WebSocket聊天流程中，HarmonyOS客户端可以选择性实现独立的意图识别调用。   url: `${this.baseUrl}/intent`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
### 2. 知识星图模块 (knowledge)

**功能**: 知识图谱管理，支持Neo4j图数据库，构建和查询知识关系

**后端实现**: 
- 信息提取: `backend/knowledge/information_extractor.py`
- 知识图谱: `backend/knowledge/information_knowledge_graph.py`
- 星图API: `backend/decision/future_os_api.py`
- 职业星图: `backend/vertical/career/neo4j_career_kg.py`
- 教育星图: `backend/vertical/education/neo4j_education_kg.py`
- 关系星图: `backend/vertical/relationship/neo4j_relationship_kg.py`

**API端点**: `/api/knowledge/*` 和 `/api/v5/future-os/*`

**核心架构**:
```
用户数据（对话/照片/传感器）
        ↓
信息提取（LLM智能提取 + 正则兜底）
        ↓
存储到Neo4j（节点类型：concept/entity/event/pattern）
        ↓
支持RAG+Neo4j混合检索
        ↓
三个星图视图（Fibonacci球面算法3D分布）
```

**主要接口**:
```typescript
// 添加信息到知识图谱（后端自动处理，无需客户端调用）
POST /api/knowledge/add-info
{
  "user_id": "string",
  "source_type": "conversation|photo|sensor",
  "content": "string",
  "entities": [],
  "relationships": []
}

// 查询知识图谱
POST /api/knowledge/query
{
  "user_id": "string",
  "query": "string",
  "query_type": "entity|relationship|pattern"
}

// 获取人际关系图谱
GET /api/knowledge/relationships/{user_id}

// 获取知识统计
GET /api/knowledge/stats/{user_id}
```

**三个星图视图API** (核心功能):
```typescript
// 职业星图（从Neo4j查询岗位 → LLM批量分类 → 3D分布）
GET /api/v5/future-os/career-graph/{user_id}
返回: { 
**HarmonyOS实现**: ✅ 已完成
```typescript
// services/KnowledgeGraphService.ets（已实现）
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { StarMapData, KnowledgeResult } from '../models/KnowledgeNode';

export class KnowledgeGraphService {
  private httpClient = HttpClient.getInstance();
  
  // 添加信息（通常由后端自动处理，客户端可选调用）
  async addInformation(
    userId: string,
    sourceType: 'conversation' | 'photo' | 'sensor',
    content: string,
    entities?: any[],
    relationships?: any[]
  ): Promise<void> {
    await this.httpClient.post(
      ApiConstants.KNOWLEDGE.ADD_INFO,
      {
        user_id: userId,
        source_type: sourceType,
        content,
        entities: entities || [],
        relationships: relationships || []
      }
    );
  }
  
  // 查询知识图谱
  async queryKnowledge(
    userId: string,
    query: string,
    queryType: 'entity' | 'relationship' | 'pattern' = 'entity'
  ): Promise<KnowledgeResult> {
    const result = await this.httpClient.post<KnowledgeResult>(
      ApiConstants.KNOWLEDGE.QUERY,
      { user_id: userId, query, query_type: queryType }
    );
    return result.data;
### 3. 决策副本模块 (decision) - 核心功能 ✅

**功能**: 多人格决策推演系统，7个独特人格从不同角度分析决策

**后端实现**:
- 主API: `backend/decision/persona_decision_api.py`
- 人格定义: `backend/decision/decision_personas.py`
- 人格系统: `backend/decision/decision_persona_system.py`
- 记忆系统: `backend/decision/persona_memory_system.py`
- 技能系统: `backend/decision/persona_skills.py`
- 信息收集: `backend/decision/decision_info_collector.py`
- Prompt管理: `backend/decision/prompts/`

**API端点**: `/api/decision/persona/*` 和 WebSocket `/api/decision/persona/ws/simulate-option`

**核心工作流程**:
```
1. 用户点击决策副本球体 → 进入对话
2. 信息收集（decision_info_collector.py）
   - 对话式收集用户信息
   - 自动集成塔罗牌决策逻辑画像（从FAISS检索）
   - 置信度阈值：20%（至少4次选择）
3. AI根据收集的信息推荐模拟方向（生成选项）
4. WebSocket协调整个推演流程（persona_decision_api.py）
5. 7个决策人格并行分析（每个人格独立思考）
   - 第0轮：独立分析
   - 使用RAG检索相关记忆和知识
   - 使用Neo4j查询知识图谱
6. 深度反思阶段：每个人格查看其他人格的观点，进行二次思考
7. 综合评分和推演结果实时流式返回
8. 支持暂停/继续功能（stop_simulation消息）
```

**7个决策人格**:
1. **理性分析师** (rational_analyst) - 逻辑推理、数据分析、因果关系
2. **情感共鸣者** (emotional_resonator) - 情感洞察、人际关系、心理影响
3. **风险评估师** (risk_assessor) - 风险识别、概率评估、应对策略
4. **机会探索者** (opportunity_explorer) - 机会发现、潜力挖掘、创新可能
5. **道德守护者** (moral_guardian) - 伦理评估、价值观、社会责任
6. **实用主义者** (pragmatist) - 实际可行性、资源评估、执行难度
7. **创新思考者** (innovator) - 创新视角、突破性思维、未来趋势

**主要接口**:
```typescript
// 1. 开始信息收集
POST /api/decision/persona/collect/start
{
  "user_id": "string",
  "question": "string",
  "decision_type": "career|education|relationship|general"
}
返回: { 
  session_id: "string", 
  message: "string",
  next_question: "string"
}

// 2. 继续信息收集（对话式）
POST /api/decision/persona/collect/continue
{
  "session_id": "string",
  "user_id": "string",
  "user_input": "string"
}
返回: { 
  is_complete: boolean,
  next_question: "string",
  collected_info: {},
  progress: number,
  decision_logic_profile: {}  // 自动集成的决策逻辑画像
}

// 3. 生成AI推荐选项
POST /api/decision/persona/generate-options
{
  "session_id": "string",
  "user_id": "string"
}
**WebSocket推演接口** (核心功能):
```typescript
// WebSocket连接地址
ws://your-backend:6006/api/decision/persona/ws/simulate-option

// 发送消息格式
{
  "type": "start_simulation",
  "session_id": "string",
  "user_id": "string",
  "question": "string",
  "option": {
    "title": "string",
    "description": "string"
  },
  "option_index": 0,
  "collected_info": {},
  "decision_type": "general"
}

// 暂停推演
{
  "type": "stop_simulation",
  "option_id": "option_1",
  "session_id": "string"
}

// 接收消息类型（完整列表）
{
  "type": "status",
  "content": "正在连接..."
}

{
  "type": "option_start",
  "option_id": "option_1",
  "title": "选项标题"
}

{
  "type": "agents_start" | "personas_init",
  "option_id": "option_1",
  "agents": [
    { 
      "id": "rational_analyst", 
      "name": "理性分析师",
      "description": "从逻辑和数据角度分析"
    },
    ...
  ],
  "month": 0
}

{
  "type": "agent_thinking",
  "option_id": "option_1",
  "agent_id": "rational_analyst",
  "content": "正在分析...",
  "stage": "thinking" | "reflection",
  "skill_result": {
    "skill_name": "rag_retrieval",
    "result": "检索到的相关记忆"
  }
}

{
  "type": "persona_analysis",
  "option_id": "option_1",
  "persona_id": "rational_analyst",
  "persona_name": "理性分析师",
  "persona_data": {
    "score": 75,
    "stance": "支持" | "反对" | "中立",
    "confidence": 0.8,
    "key_points": ["要点1", "要点2"],
    "reasoning": "详细推理过程",
    "round": 0
  },
  "content": "分析内容"
}

{
  "type": "persona_interaction",
  "option_id": "option_1",
  "persona_id": "rational_analyst",
  "interaction_data": {
    "from_persona_id": "rational_analyst",
    "to_persona_id": "emotional_resonator",
    "interaction_type": "讨论" | "质疑" | "支持",
    "content": "交互内容",
    "action": "viewing" | "stance_changed" | "stance_hold"
  },
  "content": "交互描述"
}

{
  "type": "final_evaluation",
  "option_id": "option_1",
  "evaluation_data": {
    "overall_score": 75,
    "risk_level": "低" | "中" | "高",
    "execution_confidence": 0.8,
    "recommendation": "综合建议",
    "impact_summary": {
      "short_term": "短期影响",
      "long_term": "长期影响"
    }
  }
}

{
  "type": "option_complete" | "done" | "complete",
  "option_id": "option_1",
  "final_score": 75,
**HarmonyOS实现**: ✅ 已完成
```typescript
// services/DecisionService.ets（已实现）
import { HttpClient } from '../utils/HttpClient';
import { WebSocketClient } from '../utils/WebSocketClient';
import { ApiConstants } from '../constants/ApiConstants';
import { SessionInfo, CollectionProgress, OptionsResult } from '../models/User';
import { Decision, Option } from '../models/Decision';
import { WebSocketEvent } from '../models/Agent';

export class DecisionService {
  private httpClient = HttpClient.getInstance();
  private wsClient: WebSocketClient | null = null;
  
  // 1. 开始信息收集
  async startCollection(
    userId: string,
    question: string,
    decisionType: string
  ): Promise<SessionInfo> {
    const result = await this.httpClient.post<SessionInfo>(
      ApiConstants.DECISION.START_COLLECTION,
      { user_id: userId, question, decision_type: decisionType }
    );
    return result.data;
  }
  
  // 2. 继续信息收集
  async continueCollection(
    sessionId: string,
    userId: string,
    userInput: string
  ): Promise<CollectionProgress> {
    const result = await this.httpClient.post<CollectionProgress>(
      ApiConstants.DECISION.CONTINUE_COLLECTION,
      { session_id: sessionId, user_id: userId, user_input: userInput }
    );
    return result.data;
  }
  
  // 3. 生成AI推荐选项
  async generateOptions(
    sessionId: string,
    userId: string
  ): Promise<OptionsResult> {
    const result = await this.httpClient.post<OptionsResult>(
      ApiConstants.DECISION.GENERATE_OPTIONS,
      { session_id: sessionId, user_id: userId }
    );
    return result.data;
  }
  
  // 4. WebSocket推演
  async startSimulation(
    sessionId: string,
    userId: string,
    question: string,
    option: { title: string; description: string },
    optionIndex: number,
    collectedInfo: any,
    decisionType: string,
    onMessage: (event: WebSocketEvent) => void
  ): Promise<void> {
    // 创建WebSocket连接
    this.wsClient = new WebSocketClient(ApiConstants.WS.DECISION_SIMULATE);
    
    // 注册消息处理器
    this.wsClient.on('open', () => {
      console.log('决策推演WebSocket已连接');
      // 发送开始推演消息
      this.wsClient?.send({
        type: 'start_simulation',
        session_id: sessionId,
        user_id: userId,
        question,
        option,
        option_index: optionIndex,
        collected_info: collectedInfo,
        decision_type: decisionType
      });
    });
    
    // 注册所有消息类型的处理器
    this.wsClient.on('*', (event: WebSocketEvent) => {
      onMessage(event);
    });
    
    this.wsClient.on('error', (data) => {
      console.error('WebSocket错误:', data);
      onMessage({
        type: 'error',
        content: '连接错误，请检查网络'
      });
    });
    
    this.wsClient.on('close', () => {
      console.log('WebSocket连接已关闭');
    });
    
    // 连接WebSocket
    await this.wsClient.connect();
  }
  
  // 暂停推演
  pauseSimulation(optionId: string, sessionId: string): void {
    if (this.wsClient) {
      this.wsClient.send({
        type: 'stop_simulation',
        option_id: optionId,
        session_id: sessionId
      });
    }
  }
### 4. 智慧洞察模块 (insights) ✅

**功能**: 实时智慧洞察Agent系统（三个专业Agent）

**后端实现**:
- Agent系统: `backend/insights/realtime_insight_agents.py`
- API接口: `backend/insights/realtime_insight_api.py`
- 协作系统: `backend/insights/collaborative_agents.py`
- 多Agent系统: `backend/insights/multi_agent_system.py`

**API端点**: `/api/insights/realtime/*`

**三个专业Agent**:
1. **RelationshipInsightAgent** - 人际关系洞察
   - 分析关系网络、社交模式、关系质量
   - 使用RAG检索相关记忆
   - 使用Neo4j查询人际关系图谱
   
2. **EducationInsightAgent** - 教育升学洞察
   - 分析升学路径、学校匹配、竞争力评估
   - 查询2,631所高校数据
   - 提供个性化升学建议
   
3. **CareerInsightAgent** - 职业规划洞察
   - 分析职业发展、技能匹配、岗位选择
   - 查询真实岗位数据
   - 提供职业发展路径建议

**主要接口**:
```typescript
// 人际关系洞察
POST /api/insights/realtime/relationship/insight
{
  "user_id": "string",
  "query": "分析我的人际关系网络",
  "context": {}
}
返回: {
  "insight_type": "relationship",
  "key_findings": [
    "发现1：你的社交网络主要集中在工作领域",
    "发现2：与家人的互动频率较低"
  ],
  "recommendations": [
    "建议1：增加与家人的互动时间",
    "建议2：拓展兴趣爱好相关的社交圈"
  ],
  "decision_logic": {
    "social_preference": "偏向工作社交",
    "relationship_priority": "职业发展优先"
  },
  "confidence": 0.85,
  "data_sources": ["rag_memory", "neo4j_graph"]
}

// 教育升学洞察
POST /api/insights/realtime/education/insight
{
  "user_id": "string",
  "query": "分析我的升学路径",
  "context": {
    "current_grade": "高三",
    "target_major": "计算机科学"
  }
}
返回: {
  "insight_type": "education",
  "key_findings": [...],
  "recommendations": [...],
  "matched_schools": [
    {
      "name": "清华大学",
      "match_score": 0.92,
      "reasons": ["专业实力强", "地理位置优"]
    }
  ],
  "confidence": 0.88
}

// 职业规划洞察
POST /api/insights/realtime/career/insight
{
  "user_id": "string",
  "query": "分析我的职业发展",
  "context": {
    "current_position": "软件工程师",
    "years_experience": 3
  }
### 5. 平行人生模块 (parallel_life) ✅

**功能**: 塔罗牌决策游戏，通过游戏化方式收集用户决策逻辑并集成到决策系统

**后端实现**:
- 游戏引擎: `backend/parallel_life/tarot_game.py`
- 逻辑分析: `backend/parallel_life/decision_logic_analyzer.py`
- API接口: `backend/parallel_life/parallel_life_api.py`

**API端点**: `/api/v5/parallel-life/*`

**核心工作流程**:
```
1. 用户玩塔罗牌游戏，在不同场景中做出选择
2. tarot_game.py 生成塔罗牌场景和选项（多个场景）
3. decision_logic_analyzer.py 分析用户选择，提取决策模式
4. 决策逻辑存储到FAISS（MemoryType.DECISION_LOGIC）
5. 在决策推演时自动检索并应用用户的决策偏好
   - 置信度阈值：20%（至少4次选择）
   - 自动集成到信息收集阶段
```

**决策维度**（6个维度）:
- **理性 vs 感性** - 决策时更依赖逻辑还是情感
- **保守 vs 冒险** - 风险偏好程度
- **个人 vs 集体** - 个人利益还是集体利益优先
- **短期 vs 长期** - 关注即时回报还是长远发展
- **物质 vs 精神** - 物质追求还是精神满足
- **稳定 vs 变化** - 偏好稳定还是追求变化

**主要接口**:
```typescript
// 开始塔罗牌游戏
POST /api/v5/parallel-life/start-game
{
  "user_id": "string"
}
返回: {
  "game_id": "string",
  "scene": {
    "title": "职业选择的十字路口",
    "description": "你面临两个工作机会...",
    "image": "scene_1.jpg",
    "options": [
      { 
        "id": "A", 
        "text": "选择稳定的大公司", 
        "dimension": "保守vs冒险" 
      },
      { 
        "id": "B", 
        "text": "选择创业公司", 
        "dimension": "保守vs冒险" 
      }
    ]
  },
  "current_scene_index": 1,
  "total_scenes": 10
}

// 提交选择
POST /api/v5/parallel-life/submit-choice
{
  "game_id": "string",
  "user_id": "string",
  "choice_id": "A"
}
返回: {
  "next_scene": {
    "title": "...",
    "description": "...",
    "options": [...]
  },
  "is_complete": false,
  "current_scene_index": 2,
  "total_scenes": 10,
  "decision_profile": null  // 游戏结束时返回完整画像
}

// 游戏完成时返回
{
  "next_scene": null,
  "is_complete": true,
  "decision_profile": {
    "dimensions": {
      "理性vs感性": { 
        "value": 0.6,  // 0-1，0.5为中立，>0.5偏右侧
        "count": 5,    // 该维度的选择次数
        "confidence": 1.0  // 置信度
      },
      "保守vs冒险": { 
        "value": 0.7, 
        "count": 4, 
        "confidence": 0.8 
      },
      ...
    },
    "patterns": [
      "理性vs感性: 明显倾向于右侧选择（感性）",
      "保守vs冒险: 明显倾向于右侧选择（冒险）"
    ],
    "confidence": 0.45,  // 总体置信度（需>=0.2才应用）
    "total_choices": 10
  }
}
### 6. 社交系统模块 (social) ✅

**功能**: 好友管理、树洞世界（匿名分享）

**后端实现**:
- 好友管理: `backend/social/friend_api.py` + `backend/social/friend_service.py`
- 树洞系统: `backend/social/tree_hole_api.py` + `backend/social/tree_hole_storage.py`
- AI分析: `backend/social/ai_empathy_analyzer.py` + `backend/social/ai_tree_hole_analyzer.py`

**API端点**: `/api/friends/*` 和 `/api/tree-hole/*`

**主要接口**:
```typescript
// ==================== 好友管理 ====================

// 获取好友列表
GET /api/friends/list/{user_id}
返回: [
  {
    "friend_id": "string",
    "username": "string",
    "nickname": "string",
    "avatar_url": "string",
    "status": "online|offline",
    "last_active": "timestamp"
  },
  ...
]

// 添加好友
POST /api/friends/add
{
  "user_id": "string",
  "friend_id": "string"
}

// 删除好友
POST /api/friends/remove
{
  "user_id": "string",
  "friend_id": "string"
}

// 获取好友请求
GET /api/friends/requests/{user_id}
返回: [
  {
    "request_id": "string",
    "from_user_id": "string",
    "username": "string",
    "nickname": "string",
    "message": "string",
    "created_at": "timestamp"
  },
  ...
]

// ==================== 树洞世界 ====================

// 获取树洞帖子列表
GET /api/tree-hole/posts?page=1&limit=20
返回: [
  {
    "post_id": "string",
    "content": "string",
    "is_anonymous": boolean,
    "author": {
      "user_id": "string",
      "nickname": "string",
### 7. 智能日程模块 (schedule) ✅

**功能**: 日程分析、推荐、自动生成

**后端实现**:
- 日程API: `backend/schedule/schedule_api.py`
- 日程分析: `backend/schedule/schedule_analyzer.py`
- 日程推荐: `backend/schedule/schedule_recommender.py`
- 自动生成: `backend/schedule/schedule_auto_generator.py`
- 任务管理: `backend/schedule/schedule_task_manager.py`
- RAG集成: `backend/schedule/schedule_rag_integration.py`

**API端点**: `/api/v5/schedule/*`

**主要接口**:
```typescript
// 获取日程列表
GET /api/v5/schedule/list/{user_id}?date=2026-04-20
返回: [
  {
    "schedule_id": "string",
    "user_id": "string",
    "title": "团队会议",
    "description": "讨论Q2规划",
    "start_time": "2026-04-20T10:00:00",
    "end_time": "2026-04-20T11:00:00",
    "priority": "high|medium|low",
    "status": "pending|completed|cancelled",
    "tags": ["工作", "会议"],
    "created_at": "timestamp"
  },
  ...
]

// 添加日程
POST /api/v5/schedule/add
{
  "user_id": "string",
  "title": "string",
  "start_time": "2026-04-20T10:00:00",
  "end_time": "2026-04-20T11:00:00",
  "description": "string",
  "priority": "high|medium|low",
  "tags": ["工作"]
}
返回: {
  "schedule_id": "string",
  "title": "string",
  ...
}

// 更新日程
PUT /api/v5/schedule/update/{schedule_id}
{
  "title": "新标题",
  "start_time": "2026-04-20T14:00:00",
  "priority": "high"
}

// 删除日程
DELETE /api/v5/schedule/delete/{schedule_id}

// 获取日程推荐
POST /api/v5/schedule/recommend
{
  "user_id": "string",
  "date": "2026-04-20",
  "preferences": {
    "work_hours_start": "09:00",
    "work_hours_end": "18:00",
    "break_duration": 60
  }
}
返回: [
  {
    "title": "建议：复习项目文档",
    "suggested_time": "2026-04-20T14:00:00",
    "duration": 60,
    "reason": "基于你的学习习惯，下午2点是最佳学习时间",
    "priority": "medium",
    "confidence": 0.85
  },
  ...
]

// 自动生成日程
POST /api/v5/schedule/auto-generate
{
  "user_id": "string",
  "date_range": {
    "start": "2026-04-20",
    "end": "2026-04-27"
  },
  "goals": [
    "完成项目报告",
    "学习新技术",
    "锻炼身体"
  ]
}
返回: [
  {
    "schedule_id": "string",
    "title": "项目报告 - 第一部分",
    "start_time": "2026-04-20T09:00:00",
    "end_time": "2026-04-20T11:00:00",
    "description": "完成项目背景和目标部分",
    "priority": "high",
    "auto_generated": true,
    "generation_reason": "基于你的工作习惯和项目截止日期"
  },
  ...
]

// 获取日程统计
GET /api/v5/schedule/stats/{user_id}?start_date=2026-04-01&end_date=2026-04-30
返回: {
  "total_schedules": 45,
  "completed": 30,
  "pending": 10,
  "cancelled": 5,
  "completion_rate": 0.67,
  "average_duration": 90,
  "busiest_day": "2026-04-15",
  "category_distribution": {
    "工作": 20,
    "学习": 15,
    "运动": 10
  }
}
```

**HarmonyOS实现**: ✅ 已完成
```typescript
// services/ScheduleService.ets（已实现）
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { Schedule, ScheduleInput, ScheduleRecommendation } from '../models/Schedule';

export class ScheduleService {
  private httpClient = HttpClient.getInstance();
  
  // 获取日程列表
  async getScheduleList(userId: string, date?: string): Promise<Schedule[]> {
    const params: Record<string, any> = {};
    if (date) {
      params.date = date;
    }
    
    const result = await this.httpClient.get<Schedule[]>(
      `${ApiConstants.SCHEDULE.LIST}/${userId}`,
      params
    );
    return result.data;
  }
  
  // 添加日程
  async addSchedule(schedule: ScheduleInput): Promise<Schedule> {
    const result = await this.httpClient.post<Schedule>(
      ApiConstants.SCHEDULE.ADD,
      schedule
    );
    return result.data;
  }
  
  // 更新日程
  async updateSchedule(scheduleId: string, updates: Partial<Schedule>): Promise<Schedule> {
    const result = await this.httpClient.put<Schedule>(
      `${ApiConstants.SCHEDULE.UPDATE}/${scheduleId}`,
      updates
    );
    return result.data;
  }
  
  // 删除日程
  async deleteSchedule(scheduleId: string): Promise<void> {
    await this.httpClient.delete(
      `${ApiConstants.SCHEDULE.DELETE}/${scheduleId}`
    );
  }
  
  // 获取日程推荐
  async getRecommendations(
    userId: string,
    date: string,
    preferences?: Record<string, any>
  ): Promise<ScheduleRecommendation[]> {
    const result = await this.httpClient.post<ScheduleRecommendation[]>(
      ApiConstants.SCHEDULE.RECOMMEND,
      { user_id: userId, date, preferences: preferences || {} }
    );
    return result.data;
  }
  
  // 自动生成日程
  async autoGenerateSchedule(
    userId: string,
    dateRange: { start: string; end: string },
    goals?: string[]
  ): Promise<Schedule[]> {
    const result = await this.httpClient.post<Schedule[]>(
      ApiConstants.SCHEDULE.AUTO_GENERATE,
      { user_id: userId, date_range: dateRange, goals: goals || [] }
    );
    return result.data;
  }
  
  // 获取今天的日程
  async getTodaySchedule(userId: string): Promise<Schedule[]> {
    const today = new Date().toISOString().split('T')[0];
    return this.getScheduleList(userId, today);
  }
  
  // 获取本周的日程
  async getWeekSchedule(userId: string): Promise<Schedule[]> {
    const today = new Date();
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - today.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    
    const result = await this.httpClient.get<Schedule[]>(
      `${ApiConstants.SCHEDULE.LIST}/${userId}`,
      {
        start_date: startOfWeek.toISOString().split('T')[0],
        end_date: endOfWeek.toISOString().split('T')[0]
      }
    );
    return result.data;
  }
}
```

**数据模型**:
```typescript
// models/Schedule.ets
export interface Schedule {
  schedule_id: string;
  user_id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'completed' | 'cancelled';
  tags: string[];
  auto_generated?: boolean;
  generation_reason?: string;
  created_at: string;
}

export interface ScheduleInput {
  user_id: string;
  title: string;
  start_time: string;
  end_time: string;
  description?: string;
  priority?: 'high' | 'medium' | 'low';
  tags?: string[];
}

export interface ScheduleRecommendation {
  title: string;
  suggested_time: string;
  duration: number;
  reason: string;
  priority: 'high' | 'medium' | 'low';
  confidence: number;
}
```

**HarmonyOS对接状态**: ✅ 已实现 `ScheduleService.ets`

**关键特性**:
- ✅ 完整的日程CRUD操作
- ✅ 智能日程推荐
- ✅ 自动日程生成
- ✅ 基于RAG的个性化推荐
- ✅ 日程统计分析
- ✅ 后台异步任务处理ort { ApiConstants } from '../constants/ApiConstants';
import { Friend, Post, Comment } from '../models/Social';

export class SocialService {
  private httpClient = HttpClient.getInstance();
  
  // ==================== 好友管理 ====================
  
  // 获取好友列表
  async getFriendsList(userId: string): Promise<Friend[]> {
    const result = await this.httpClient.get<Friend[]>(
      `${ApiConstants.SOCIAL.FRIENDS_LIST}/${userId}`
    );
    return result.data;
  }
  
  // 添加好友
  async addFriend(userId: string, friendId: string): Promise<void> {
    await this.httpClient.post(
      ApiConstants.SOCIAL.FRIENDS_ADD,
      { user_id: userId, friend_id: friendId }
    );
  }
  
  // 删除好友
  async removeFriend(userId: string, friendId: string): Promise<void> {
    await this.httpClient.post(
      ApiConstants.SOCIAL.FRIENDS_REMOVE,
      { user_id: userId, friend_id: friendId }
    );
  }
  
  // 获取好友请求
  async getFriendRequests(userId: string): Promise<any[]> {
    const result = await this.httpClient.get(
      `${ApiConstants.SOCIAL.FRIENDS_REQUESTS}/${userId}`
    );
    return result.data;
  }
  
  // ==================== 树洞世界 ====================
  
  // 获取树洞帖子列表
  async getTreeHolePosts(page: number = 1, limit: number = 20): Promise<Post[]> {
    const result = await this.httpClient.get<Post[]>(
      ApiConstants.SOCIAL.TREE_HOLE_POSTS,
      { page, limit }
    );
    return result.data;
  }
  
  // 发布树洞帖子
  async postToTreeHole(
    userId: string,
    content: string,
    isAnonymous: boolean = false,
    tags: string[] = []
  ): Promise<Post> {
    const result = await this.httpClient.post<Post>(
      ApiConstants.SOCIAL.TREE_HOLE_POST,
      { user_id: userId, content, is_anonymous: isAnonymous, tags }
    );
    return result.data;
  }
  
  // 获取帖子详情
  async getPostDetail(postId: string): Promise<Post> {
    const result = await this.httpClient.get<Post>(
      `${ApiConstants.SOCIAL.TREE_HOLE_POST}/${postId}`
    );
    return result.data;
  }
  
  // 评论帖子
  async commentPost(
    postId: string,
    userId: string,
    content: string
  ): Promise<Comment> {
    const result = await this.httpClient.post<Comment>(
      ApiConstants.SOCIAL.TREE_HOLE_COMMENT,
      { post_id: postId, user_id: userId, content }
    );
    return result.data;
  }
  
  // 点赞帖子
  async likePost(postId: string, userId: string): Promise<void> {
    await this.httpClient.post(
      ApiConstants.SOCIAL.TREE_HOLE_LIKE,
      { post_id: postId, user_id: userId }
    );
  }
  
  // 取消点赞
  async unlikePost(postId: string, userId: string): Promise<void> {
    await this.httpClient.post(
      `${ApiConstants.SOCIAL.TREE_HOLE_LIKE}/cancel`,
      { post_id: postId, user_id: userId }
    );
  }
}
```

**数据模型**:
```typescript
// models/Social.ets
export interface Friend {
  friend_id: string;
  username: string;
  nickname: string;
  avatar_url?: string;
  status: 'online' | 'offline';
  last_active?: string;
}

export interface Post {
  post_id: string;
  content: string;
  is_anonymous: boolean;
  author?: {
    user_id: string;
    nickname: string;
    avatar_url?: string;
  };
  tags: string[];
  likes_count: number;
  comments_count: number;
  created_at: string;
  ai_analysis?: {
    emotion: string;
    topics: string[];
  };
  comments?: Comment[];
}

export interface Comment {
  comment_id: string;
  user_id: string;
  nickname: string;
  content: string;
  created_at: string;
}
```

**HarmonyOS对接状态**: ✅ 已实现 `SocialService.ets`

**关键特性**:
- ✅ 完整的好友管理功能
- ✅ 树洞匿名分享
- ✅ AI情感分析（后端自动）
- ✅ 评论和点赞功能
- ✅ 话题标签系统 id: string;
    text: string;
    dimension: string;
  }>;
}

export interface GameProgress {
  next_scene?: TarotScene;
  is_complete: boolean;
  decision_profile?: DecisionProfile;
  current_scene_index: number;
  total_scenes: number;
}

export interface DecisionProfile {
  dimensions: Record<string, {
    value: number;
    count: number;
    confidence: number;
  }>;
  patterns: string[];
  confidence: number;
  total_choices: number;
  last_updated?: string;
}
```

**HarmonyOS对接状态**: ✅ 已实现 `ParallelLifeService.ets`

**关键特性**:
- ✅ 完整的塔罗牌游戏流程
- ✅ 6个决策维度分析
- ✅ 决策画像生成
- ✅ 自动集成到决策系统
- ✅ 置信度阈值控制（20%）     throw new Error(`未知的洞察类型: ${type}`);
    }
  }
}
```

**数据模型**:
```typescript
// models/Insight.ets
export interface InsightResult {
  insight_type: 'relationship' | 'education' | 'career';
  key_findings: string[];
  recommendations: string[];
  decision_logic?: Record<string, any>;
  confidence: number;
  data_sources?: string[];
  matched_schools?: SchoolMatch[];
  career_paths?: CareerPath[];
}

export interface SchoolMatch {
  name: string;
  match_score: number;
  reasons: string[];
}

export interface CareerPath {
  path: string;
  feasibility: number;
  required_skills: string[];
}
```

**HarmonyOS对接状态**: ✅ 已实现 `InsightsService.ets`

**关键特性**:
- ✅ 三个专业Agent独立运行
- ✅ RAG记忆检索集成
- ✅ Neo4j知识图谱查询
- ✅ 个性化洞察生成
- ✅ 决策逻辑应用content": "分析内容"
}

{
  "type": "persona_interaction",
  "option_id": "option_1",
  "persona_id": "rational_analyst",
  "interaction_data": {
    "from_persona_id": "rational_analyst",
    "to_persona_id": "emotional_resonator",
    "interaction_type": "讨论" | "质疑" | "支持",
    "content": "交互内容",
    "action": "viewing" | "stance_changed" | "stance_hold"
  },
  "content": "交互描述"
}

{
  "type": "final_evaluation",
  "option_id": "option_1",
  "evaluation_data": {
    "overall_score": 75,
    "risk_level": "低" | "中" | "高",
    "execution_confidence": 0.8,
    "recommendation": "string",
    "impact_summary": {}
  }
}

{
  "type": "option_complete" | "done" | "complete",
  "option_id": "option_1",
  "final_score": 75,
  "risk_level": 0.3,
  "execution_confidence": 0.8
}

{
  "type": "error",
  "content": "错误信息"
}
```

**HarmonyOS实现**:
```typescript
// services/DecisionService.ets
import webSocket from '@ohos.net.webSocket';

export class DecisionService {
  private baseUrl = 'http://your-backend:6006/api/decision/persona';
  private wsUrl = 'ws://your-backend:6006/api/decision/persona/ws/simulate-option';
  private ws: webSocket.WebSocket | null = null;
  
  // 1. 开始信息收集
  async startCollection(userId: string, question: string, decisionType: string): Promise<SessionInfo> {
    const response = await http.request({
      url: `${this.baseUrl}/start-collection`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { user_id: userId, question, decision_type: decisionType }
    });
    return JSON.parse(response.result.toString());
  }
  
  // 2. 继续信息收集
  async continueCollection(sessionId: string, userId: string, userInput: string): Promise<CollectionProgress> {
    const response = await http.request({
      url: `${this.baseUrl}/continue-collection`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { session_id: sessionId, user_id: userId, user_input: userInput }
    });
    return JSON.parse(response.result.toString());
  }
  
  // 3. 生成AI推荐选项
  async generateOptions(sessionId: string, userId: string): Promise<OptionsResult> {
    const response = await http.request({
      url: `${this.baseUrl}/generate-options`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { session_id: sessionId, user_id: userId }
    });
    return JSON.parse(response.result.toString());
  }
  
  // 4. WebSocket推演
  async startSimulation(
    sessionId: string,
    userId: string,
    question: string,
    option: { title: string, description: string },
    optionIndex: number,
    collectedInfo: any,
    decisionType: string,
    onMessage: (event: any) => void
  ): Promise<void> {
    this.ws = webSocket.createWebSocket();
    
    this.ws.on('open', () => {
      console.log('WebSocket连接成功');
      // 发送开始推演消息
      this.ws?.send(JSON.stringify({
        type: 'start_simulation',
        session_id: sessionId,
        user_id: userId,
        question,
        option,
        option_index: optionIndex,
        collected_info: collectedInfo,
        decision_type: decisionType
      }));
    });
    
    this.ws.on('message', (err, value) => {
      if (!err && value) {
        const event = JSON.parse(value.toString());
        onMessage(event);
      }
    });
    
    this.ws.on('error', (err) => {
      console.error('WebSocket错误:', err);
    });
    
    this.ws.on('close', () => {
      console.log('WebSocket连接关闭');
    });
    
    await this.ws.connect(this.wsUrl);
  }
  
  // 暂停推演
  pauseSimulation(optionId: string, sessionId: string): void {
    if (this.ws) {
      this.ws.send(JSON.stringify({
        type: 'stop_simulation',
        option_id: optionId,
        session_id: sessionId
      }));
    }
  }
  
  // 关闭WebSocket
  closeSimulation(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

---


### 4. 智慧洞察模块 (insights)

**功能**: 实时智慧洞察Agent系统 + 三层混合架构（规则引擎 + ML + LLM）

**API端点**: `/api/insights/realtime/*`

**三个专业Agent**:
1. RelationshipInsightAgent - 人际关系洞察
2. EducationInsightAgent - 教育升学洞察
3. CareerInsightAgent - 职业规划洞察

**主要接口**:
```typescript
// 人际关系洞察
POST /api/insights/realtime/relationship/insight
{
  "user_id": "string",
  "query": "分析我的人际关系网络",
  "context": {}
}
返回: {
  "insight_type": "relationship",
  "key_findings": [],
  "recommendations": [],
  "decision_logic": {},
  "confidence": 0.85
}

// 教育升学洞察
POST /api/insights/realtime/education/insight
{
  "user_id": "string",
  "query": "分析我的升学路径",
  "context": {}
}

// 职业规划洞察
POST /api/insights/realtime/career/insight
{
  "user_id": "string",
  "query": "分析我的职业发展",
  "context": {}
}

// Agent状态查询
GET /api/insights/realtime/agents/status
```

**HarmonyOS实现**:
```typescript
// services/InsightsService.ets
export class InsightsService {
  private baseUrl = 'http://your-backend:8000/api/insights/realtime';
  
  async getRelationshipInsight(userId: string, query: string): Promise<InsightResult> {
    const response = await http.request({
      url: `${this.baseUrl}/relationship/insight`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { user_id: userId, query, context: {} }
    });
    return JSON.parse(response.result.toString());
  }
  
  async getEducationInsight(userId: string, query: string): Promise<InsightResult> {
    const response = await http.request({
      url: `${this.baseUrl}/education/insight`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { user_id: userId, query, context: {} }
    });
    return JSON.parse(response.result.toString());
  }
  
  async getCareerInsight(userId: string, query: string): Promise<InsightResult> {
    const response = await http.request({
      url: `${this.baseUrl}/career/insight`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { user_id: userId, query, context: {} }
    });
    return JSON.parse(response.result.toString());
  }
}
```

---

### 5. 平行人生模块 (parallel_life)

**功能**: 塔罗牌决策游戏，通过游戏化方式收集用户决策逻辑

**API端点**: `/api/v5/parallel-life/*`

**核心工作流程**:
```
1. 用户玩塔罗牌游戏，在不同场景中做出选择
2. tarot_game.py 生成塔罗牌场景和选项
3. decision_logic_analyzer.py 分析用户选择，提取决策模式
4. 决策逻辑存储到FAISS（MemoryType.DECISION_LOGIC）
5. 在决策推演时自动检索并应用用户的决策偏好
```

**决策维度**:
- 理性 vs 感性
- 保守 vs 冒险
- 个人 vs 集体
- 短期 vs 长期
- 物质 vs 精神
- 稳定 vs 变化

**主要接口**:
```typescript
// 开始塔罗牌游戏
POST /api/v5/parallel-life/start-game
{
  "user_id": "string"
}
返回: {
  "game_id": "string",
  "scene": {
    "title": "string",
    "description": "string",
    "options": [
      { "id": "A", "text": "string", "dimension": "理性vs感性" },
      { "id": "B", "text": "string", "dimension": "理性vs感性" }
    ]
  }
}

// 提交选择
POST /api/v5/parallel-life/submit-choice
{
  "game_id": "string",
  "user_id": "string",
  "choice_id": "A"
}
返回: {
  "next_scene": {},
  "is_complete": boolean,
  "decision_profile": {}  // 游戏结束时返回
}

// 获取决策画像
GET /api/v5/parallel-life/decision-profile/{user_id}
返回: {
  "dimensions": {
    "理性vs感性": { "value": 0.6, "count": 5, "confidence": 1.0 }
  },
  "patterns": [],
  "confidence": 0.25,
  "total_choices": 5
}
```

**HarmonyOS实现**:
```typescript
// services/ParallelLifeService.ets
export class ParallelLifeService {
  private baseUrl = 'http://your-backend:8000/api/v5/parallel-life';
  
  async startGame(userId: string): Promise<GameSession> {
    const response = await http.request({
      url: `${this.baseUrl}/start-game`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { user_id: userId }
    });
    return JSON.parse(response.result.toString());
  }
  
  async submitChoice(gameId: string, userId: string, choiceId: string): Promise<GameProgress> {
    const response = await http.request({
      url: `${this.baseUrl}/submit-choice`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { game_id: gameId, user_id: userId, choice_id: choiceId }
    });
    return JSON.parse(response.result.toString());
  }
  
  async getDecisionProfile(userId: string): Promise<DecisionProfile> {
    const response = await http.request({
      url: `${this.baseUrl}/decision-profile/${userId}`,
      method: http.RequestMethod.GET
    });
    return JSON.parse(response.result.toString());
  }
}
```

---

### 6. 社交系统模块 (social)

**功能**: 好友管理、树洞世界（匿名分享）

**API端点**: `/api/friends/*` 和 `/api/tree-hole/*`

**主要接口**:
```typescript
// 好友管理
GET /api/friends/list/{user_id}
POST /api/friends/add
POST /api/friends/remove
GET /api/friends/requests/{user_id}

// 树洞世界
GET /api/tree-hole/posts
POST /api/tree-hole/post
{
  "user_id": "string",
  "content": "string",
  "is_anonymous": true,
  "tags": []
}

GET /api/tree-hole/post/{post_id}
POST /api/tree-hole/comment
POST /api/tree-hole/like
```

**HarmonyOS实现**:
```typescript
// services/SocialService.ets
export class SocialService {
  private friendsUrl = 'http://your-backend:8000/api/friends';
  private treeHoleUrl = 'http://your-backend:8000/api/tree-hole';
  
  // 好友列表
  async getFriendsList(userId: string): Promise<Friend[]> {
    const response = await http.request({
      url: `${this.friendsUrl}/list/${userId}`,
      method: http.RequestMethod.GET
    });
    return JSON.parse(response.result.toString());
  }
  
  // 发布树洞
  async postToTreeHole(userId: string, content: string, isAnonymous: boolean): Promise<Post> {
    const response = await http.request({
      url: `${this.treeHoleUrl}/post`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { user_id: userId, content, is_anonymous: isAnonymous, tags: [] }
    });
    return JSON.parse(response.result.toString());
  }
  
  // 获取树洞列表
  async getTreeHolePosts(page: number = 1, limit: number = 20): Promise<Post[]> {
    const response = await http.request({
      url: `${this.treeHoleUrl}/posts?page=${page}&limit=${limit}`,
      method: http.RequestMethod.GET
    });
    return JSON.parse(response.result.toString());
  }
}
```

---

### 7. 智能日程模块 (schedule)

**功能**: 日程分析、推荐、自动生成

**API端点**: `/api/v5/schedule/*`

**主要接口**:
```typescript
// 获取日程列表
GET /api/v5/schedule/list/{user_id}?date=2026-04-20

// 添加日程
POST /api/v5/schedule/add
{
  "user_id": "string",
  "title": "string",
  "start_time": "2026-04-20T10:00:00",
  "end_time": "2026-04-20T11:00:00",
  "description": "string",
  "priority": "high|medium|low"
}

// 获取日程推荐
POST /api/v5/schedule/recommend
{
  "user_id": "string",
  "date": "2026-04-20",
  "preferences": {}
}

// 自动生成日程
POST /api/v5/schedule/auto-generate
{
  "user_id": "string",
  "date_range": {
    "start": "2026-04-20",
    "end": "2026-04-27"
  },
  "goals": []
}
```

**HarmonyOS实现**:
```typescript
// services/ScheduleService.ets
export class ScheduleService {
  private baseUrl = 'http://your-backend:6006/api/v5/schedule';
  
  async getScheduleList(userId: string, date: string): Promise<Schedule[]> {
    const response = await http.request({
      url: `${this.baseUrl}/list/${userId}?date=${date}`,
      method: http.RequestMethod.GET
    });
    return JSON.parse(response.result.toString());
  }
  
  async addSchedule(schedule: ScheduleInput): Promise<Schedule> {
    const response = await http.request({
      url: `${this.baseUrl}/add`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: schedule
    });
    return JSON.parse(response.result.toString());
  }
  
  async getRecommendations(userId: string, date: string): Promise<ScheduleRecommendation[]> {
    const response = await http.request({
      url: `${this.baseUrl}/recommend`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { user_id: userId, date, preferences: {} }
    });
    return JSON.parse(response.result.toString());
  }
}
```

---


## 🎨 3D球体UI设计规范（模仿Web端）

### 主界面设计

**参考**: `web/src/pages/DecisionSimulationPage.tsx` 和 `web/src/components/decision/PersonaInteractionView.css`

**核心设计元素**:

1. **背景渐变光晕**
```css
background: linear-gradient(135deg, rgba(240, 247, 255, 0.4) 0%, rgba(232, 244, 255, 0.3) 100%);

/* 背景光晕动画 */
radial-gradient(circle, rgba(184, 220, 255, 0.15), transparent 70%);
filter: blur(80px);
animation: backgroundPulse 8s ease-in-out infinite;
```

2. **中心选项球体**
```css
/* 球体样式 */
width: 200px;
height: 200px;
border-radius: 50%;
border: 2px solid rgba(184, 220, 255, 0.8);

/* 玻璃态背景 */
background:
  radial-gradient(ellipse 55% 40% at 30% 20%, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 0.9) 30%, transparent 60%),
  radial-gradient(ellipse 40% 55% at 75% 55%, rgba(255, 255, 255, 0.7) 0%, transparent 50%),
  linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(232, 244, 255, 0.9) 60%, rgba(200, 226, 255, 0.85) 100%);

/* 阴影和光晕 */
box-shadow:
  0 20px 60px rgba(10, 89, 247, 0.15),
  0 10px 30px rgba(10, 89, 247, 0.1),
  inset 0 2px 4px rgba(255, 255, 255, 1),
  inset 0 -3px 8px rgba(10, 89, 247, 0.08),
  0 0 50px rgba(184, 220, 255, 0.3);

backdrop-filter: blur(40px);
```

3. **智能体节点球体**
```css
/* 节点样式 */
width: 120px;
height: 120px;
border-radius: 50%;
border: 1.5px solid rgba(184, 220, 255, 0.6);

/* 玻璃态背景 */
background:
  radial-gradient(circle at 50% 30%, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.85) 30%, rgba(255, 255, 255, 0.6) 70%),
  linear-gradient(135deg, #E8F4FF 0%, #B8DCFF 100%);

/* 阴影 */
box-shadow:
  0 10px 40px rgba(10, 89, 247, 0.15),
  0 5px 20px rgba(10, 89, 247, 0.1),
  inset 0 1px 3px rgba(255, 255, 255, 0.9);

/* 高光效果 */
::before {
  background:
    radial-gradient(circle at 34% 26%, rgba(255, 255, 255, 0.55), transparent 26%),
    radial-gradient(circle at 74% 80%, rgba(255, 255, 255, 0.12), transparent 20%);
}

/* 轨道光晕 */
::before {
  border: 1px solid rgba(184, 220, 255, 0.35);
  background: radial-gradient(circle, rgba(255, 255, 255, 0.5), transparent 60%);
  filter: blur(6px);
  animation: nodeOrbitPulse 4s ease-in-out infinite;
}
```

4. **思考状态动画**
```css
@keyframes thinkingPulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 10px 40px rgba(10, 89, 247, 0.15);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 15px 60px rgba(10, 89, 247, 0.3);
  }
}
```

5. **交互连线**
```css
/* SVG连线 */
stroke: rgba(10, 89, 247, 0.3);
stroke-width: 2;
stroke-dasharray: 5, 5;
animation: dash 1s linear infinite;
```

6. **消息气泡**
```css
background: white;
border: 2px solid #0A59F7;
border-radius: 12px;
padding: 10px 12px;
box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
animation: bubbleIn 0.3s ease;

/* 不同action类型的颜色 */
.action-thinking { border-color: #0A59F7; }
.action-retrieving { border-color: #FF9500; }
.action-analyzing { border-color: #6B48FF; }
.action-analysis_done { border-color: #34C759; }
```

### HarmonyOS实现指南

**1. Canvas绘制球体**
```typescript
// components/SphereView.ets
@Component
export struct SphereView {
  @State sphereData: SphereData = {};
  private settings: RenderingContextSettings = new RenderingContextSettings(true);
  private context: CanvasRenderingContext2D = new CanvasRenderingContext2D(this.settings);
  
  build() {
    Canvas(this.context)
      .width('100%')
      .height('100%')
      .onReady(() => {
        this.drawSphere();
      })
  }
  
  drawSphere() {
    const centerX = this.context.width / 2;
    const centerY = this.context.height / 2;
    const radius = 100;
    
    // 绘制球体阴影
    const shadowGradient = this.context.createRadialGradient(
      centerX, centerY + 20, 0,
      centerX, centerY + 20, radius + 40
    );
    shadowGradient.addColorStop(0, 'rgba(10, 89, 247, 0.15)');
    shadowGradient.addColorStop(1, 'rgba(10, 89, 247, 0)');
    this.context.fillStyle = shadowGradient;
    this.context.fillRect(0, 0, this.context.width, this.context.height);
    
    // 绘制球体主体
    const gradient = this.context.createRadialGradient(
      centerX - radius * 0.3, centerY - radius * 0.3, 0,
      centerX, centerY, radius
    );
    gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
    gradient.addColorStop(0.3, 'rgba(255, 255, 255, 0.9)');
    gradient.addColorStop(0.7, 'rgba(232, 244, 255, 0.9)');
    gradient.addColorStop(1, 'rgba(200, 226, 255, 0.85)');
    
    this.context.beginPath();
    this.context.arc(centerX, centerY, radius, 0, Math.PI * 2);
    this.context.fillStyle = gradient;
    this.context.fill();
    
    // 绘制高光
    const highlightGradient = this.context.createRadialGradient(
      centerX - radius * 0.4, centerY - radius * 0.4, 0,
      centerX - radius * 0.4, centerY - radius * 0.4, radius * 0.3
    );
    highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.6)');
    highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
    
    this.context.beginPath();
    this.context.arc(centerX - radius * 0.4, centerY - radius * 0.4, radius * 0.3, 0, Math.PI * 2);
    this.context.fillStyle = highlightGradient;
    this.context.fill();
    
    // 绘制边框
    this.context.beginPath();
    this.context.arc(centerX, centerY, radius, 0, Math.PI * 2);
    this.context.strokeStyle = 'rgba(184, 220, 255, 0.8)';
    this.context.lineWidth = 2;
    this.context.stroke();
  }
}
```

**2. 使用Lottie动画（推荐）**
```typescript
// 使用Lottie实现更复杂的球体动画
import lottie from '@ohos/lottie';

@Component
export struct AnimatedSphere {
  private animationItem: any = null;
  
  build() {
    Column() {
      // Lottie动画容器
      Canvas(this.context)
        .width(200)
        .height(200)
        .onReady(() => {
          this.animationItem = lottie.loadAnimation({
            container: this.context,
            renderer: 'canvas',
            loop: true,
            autoplay: true,
            path: 'common/lottie/sphere_animation.json'
          });
        })
    }
  }
}
```

**3. 3D效果（使用XComponent）**
```typescript
// 使用XComponent实现真正的3D球体
@Component
export struct Sphere3D {
  private xComponentController: XComponentController = new XComponentController();
  
  build() {
    XComponent({
      id: 'sphere3d',
      type: 'surface',
      controller: this.xComponentController
    })
      .width(200)
      .height(200)
      .onLoad(() => {
        // 初始化OpenGL ES渲染
        this.initGL();
      })
  }
  
  initGL() {
    // OpenGL ES代码实现3D球体渲染
    // 参考HarmonyOS官方3D渲染示例
  }
}
```

**4. 布局实现**
```typescript
// pages/DecisionSimulationPage.ets
@Entry
@Component
struct DecisionSimulationPage {
  @State agents: Agent[] = [];
  @State centerOption: Option = {};
  
  build() {
    Stack() {
      // 背景渐变
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 135,
          colors: [
            [0xF0F7FF, 0.0],
            [0xE8F4FF, 1.0]
          ]
        })
      
      // 背景光晕
      Column()
        .width(600)
        .height(600)
        .position({ x: '50%', y: '50%' })
        .translate({ x: '-50%', y: '-50%' })
        .borderRadius(300)
        .backgroundBlurStyle(BlurStyle.Thin)
        .backgroundColor('rgba(184, 220, 255, 0.15)')
      
      // 中心选项球体
      SphereView({ sphereData: this.centerOption })
        .width(200)
        .height(200)
        .position({ x: '50%', y: '50%' })
        .translate({ x: '-50%', y: '-50%' })
      
      // 智能体节点（环形分布）
      ForEach(this.agents, (agent: Agent, index: number) => {
        const angle = (index / this.agents.length) * Math.PI * 2;
        const radius = 250;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        
        AgentNode({ agent: agent })
          .width(120)
          .height(120)
          .position({ 
            x: `calc(50% + ${x}px)`, 
            y: `calc(50% + ${y}px)` 
          })
          .translate({ x: '-50%', y: '-50%' })
      })
      
      // 连线（使用Canvas绘制）
      Canvas(this.lineContext)
        .width('100%')
        .height('100%')
        .onReady(() => {
          this.drawConnections();
        })
    }
    .width('100%')
    .height('100%')
  }
  
  drawConnections() {
    // 绘制中心到各节点的连线
    const centerX = this.lineContext.width / 2;
    const centerY = this.lineContext.height / 2;
    
    this.agents.forEach((agent, index) => {
      const angle = (index / this.agents.length) * Math.PI * 2;
      const radius = 250;
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;
      
      this.lineContext.beginPath();
      this.lineContext.moveTo(centerX, centerY);
      this.lineContext.lineTo(x, y);
      this.lineContext.strokeStyle = 'rgba(10, 89, 247, 0.2)';
      this.lineContext.lineWidth = 2;
      this.lineContext.setLineDash([5, 5]);
      this.lineContext.stroke();
    });
  }
}
```

---


## 🗄️ 数据库对接

### 直接使用后端数据库

HarmonyOS应用不需要独立的数据库，直接通过API访问后端的MySQL和Neo4j数据库。

### 数据库架构

**1. MySQL数据库**
- 用户数据（User表）
- 对话记录（Conversation, Message表）
- 决策记录（Decision表）
- 洞察数据（Insight表）
- 日程数据（Schedule表）
- 社交数据（Friend, TreeHolePost表）

**2. Neo4j图数据库**
- 知识图谱节点和关系
- 职业星图（技能、岗位、公司）
- 教育星图（学业、学校、行动）
- 人际关系星图（家人、朋友、同事）

**3. Redis缓存**
- 会话缓存
- 热点数据缓存
- 实时状态缓存

**4. FAISS向量数据库**
- 对话记忆（CONVERSATION）
- 决策逻辑画像（DECISION_LOGIC）
- 知识记忆（KNOWLEDGE）
- 经验记忆（EXPERIENCE）
- 洞察记忆（INSIGHT）

### 数据同步策略

**1. 实时同步**
- 用户操作立即通过API同步到后端
- WebSocket实时推送更新

**2. 离线缓存**
```typescript
// utils/OfflineCache.ets
import dataPreferences from '@ohos.data.preferences';

export class OfflineCache {
  private preferences: dataPreferences.Preferences | null = null;
  
  async init() {
    this.preferences = await dataPreferences.getPreferences(
      getContext(this),
      'offline_cache'
    );
  }
  
  // 缓存数据
  async cacheData(key: string, data: any): Promise<void> {
    await this.preferences?.put(key, JSON.stringify(data));
    await this.preferences?.flush();
  }
  
  // 获取缓存
  async getCachedData(key: string): Promise<any> {
    const data = await this.preferences?.get(key, '');
    return data ? JSON.parse(data as string) : null;
  }
  
  // 清除缓存
  async clearCache(): Promise<void> {
    await this.preferences?.clear();
    await this.preferences?.flush();
  }
}
```

**3. 数据预加载**
```typescript
// services/DataPreloader.ets
export class DataPreloader {
  async preloadUserData(userId: string): Promise<void> {
    // 预加载用户常用数据
    const promises = [
      this.preloadKnowledgeGraph(userId),
      this.preloadRecentConversations(userId),
      this.preloadSchedules(userId),
      this.preloadFriends(userId)
    ];
    
    await Promise.all(promises);
  }
  
  private async preloadKnowledgeGraph(userId: string): Promise<void> {
    const kgService = new KnowledgeGraphService();
    const starMaps = await Promise.all([
      kgService.getStarMap(userId, 'career'),
      kgService.getStarMap(userId, 'education'),
      kgService.getStarMap(userId, 'relationship')
    ]);
    
    // 缓存到本地
    const cache = new OfflineCache();
    await cache.cacheData(`star_maps_${userId}`, starMaps);
  }
}
```

---

## 🔐 用户认证

### 认证流程

**1. 注册**
```typescript
// services/AuthService.ets
export class AuthService {
  private baseUrl = 'http://your-backend:6006/api/auth';
  
  async register(username: string, email: string, password: string, nickname: string): Promise<AuthResult> {
    const response = await http.request({
      url: `${this.baseUrl}/register`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { username, email, password, nickname }
    });
    
    const result = JSON.parse(response.result.toString());
    
    if (result.code === 200) {
      // 保存Token
      await this.saveToken(result.data.token);
      await this.saveUserInfo(result.data);
    }
    
    return result;
  }
  
  async login(username: string, password: string): Promise<AuthResult> {
    const response = await http.request({
      url: `${this.baseUrl}/login`,
      method: http.RequestMethod.POST,
      header: { 'Content-Type': 'application/json' },
      extraData: { username, password }
    });
    
    const result = JSON.parse(response.result.toString());
    
    if (result.code === 200) {
      await this.saveToken(result.data.token);
      await this.saveUserInfo(result.data);
    }
    
    return result;
  }
  
  private async saveToken(token: string): Promise<void> {
    const preferences = await dataPreferences.getPreferences(
      getContext(this),
      'auth'
    );
    await preferences.put('token', token);
    await preferences.flush();
  }
  
  async getToken(): Promise<string> {
    const preferences = await dataPreferences.getPreferences(
      getContext(this),
      'auth'
    );
    return await preferences.get('token', '') as string;
  }
  
  async logout(): Promise<void> {
    const preferences = await dataPreferences.getPreferences(
      getContext(this),
      'auth'
    );
    await preferences.clear();
    await preferences.flush();
  }
}
```

**2. Token管理**
```typescript
// utils/HttpInterceptor.ets
export class HttpInterceptor {
  static async addAuthHeader(request: http.HttpRequest): Promise<http.HttpRequest> {
    const authService = new AuthService();
    const token = await authService.getToken();
    
    if (token) {
      request.header = {
        ...request.header,
        'Authorization': `Bearer ${token}`
      };
    }
    
    return request;
  }
  
  static async handleResponse(response: http.HttpResponse): Promise<any> {
    const result = JSON.parse(response.result.toString());
    
    // Token过期处理
    if (result.code === 401) {
      // 跳转到登录页
      router.pushUrl({ url: 'pages/LoginPage' });
      throw new Error('Token已过期，请重新登录');
    }
    
    return result;
  }
}
```

---

## 📡 网络通信

### HTTP请求封装

```typescript
// utils/HttpClient.ets
import http from '@ohos.net.http';

export class HttpClient {
  private static instance: HttpClient;
  private baseUrl: string = 'http://your-backend:8000';
  
  static getInstance(): HttpClient {
    if (!HttpClient.instance) {
      HttpClient.instance = new HttpClient();
    }
    return HttpClient.instance;
  }
  
  async request<T>(config: RequestConfig): Promise<ApiResponse<T>> {
    const httpRequest = http.createHttp();
    
    try {
      // 添加认证头
      const authConfig = await HttpInterceptor.addAuthHeader({
        url: `${this.baseUrl}${config.url}`,
        method: config.method || http.RequestMethod.GET,
        header: {
          'Content-Type': 'application/json',
          ...config.headers
        },
        extraData: config.data
      });
      
      const response = await httpRequest.request(
        authConfig.url,
        authConfig
      );
      
      // 处理响应
      return await HttpInterceptor.handleResponse(response);
      
    } catch (error) {
      console.error('HTTP请求失败:', error);
      throw error;
    } finally {
      httpRequest.destroy();
    }
  }
  
  async get<T>(url: string, params?: any): Promise<ApiResponse<T>> {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return this.request<T>({
      url: url + queryString,
      method: http.RequestMethod.GET
    });
  }
  
  async post<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      url,
      method: http.RequestMethod.POST,
      data
    });
  }
  
  async put<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>({
      url,
      method: http.RequestMethod.PUT,
      data
    });
  }
  
  async delete<T>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>({
      url,
      method: http.RequestMethod.DELETE
    });
  }
}

interface RequestConfig {
  url: string;
  method?: http.RequestMethod;
  headers?: Record<string, string>;
  data?: any;
}

interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}
```

### WebSocket封装

```typescript
// utils/WebSocketClient.ets
import webSocket from '@ohos.net.webSocket';

export class WebSocketClient {
  private ws: webSocket.WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 3000;
  private messageHandlers: Map<string, (data: any) => void> = new Map();
  
  constructor(url: string) {
    this.url = url;
  }
  
  async connect(): Promise<void> {
    this.ws = webSocket.createWebSocket();
    
    this.ws.on('open', () => {
      console.log('WebSocket连接成功');
      this.reconnectAttempts = 0;
    });
    
    this.ws.on('message', (err, value) => {
      if (!err && value) {
        try {
          const message = JSON.parse(value.toString());
          this.handleMessage(message);
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
        }
      }
    });
    
    this.ws.on('error', (err) => {
      console.error('WebSocket错误:', err);
    });
    
    this.ws.on('close', () => {
      console.log('WebSocket连接关闭');
      this.attemptReconnect();
    });
    
    await this.ws.connect(this.url);
  }
  
  send(data: any): void {
    if (this.ws) {
      this.ws.send(JSON.stringify(data));
    }
  }
  
  on(eventType: string, handler: (data: any) => void): void {
    this.messageHandlers.set(eventType, handler);
  }
  
  off(eventType: string): void {
    this.messageHandlers.delete(eventType);
  }
  
  private handleMessage(message: any): void {
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message);
    }
    
    // 通用处理器
    const allHandler = this.messageHandlers.get('*');
    if (allHandler) {
      allHandler(message);
    }
  }
  
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay);
    } else {
      console.error('WebSocket重连失败，已达到最大重试次数');
    }
  }
  
  close(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

---


## 🏗️ 项目架构

### 目录结构

```
harmonyos/
├── entry/
│   └── src/
│       └── main/
│           ├── ets/
│           │   ├── entryability/
│           │   │   └── EntryAbility.ets
│           │   ├── pages/
│           │   │   ├── Index.ets                    # 主页
│           │   │   ├── LoginPage.ets                # 登录页
│           │   │   ├── DecisionSimulationPage.ets   # 决策推演页
│           │   │   ├── KnowledgeGraphPage.ets       # 知识星图页
│           │   │   ├── InsightsPage.ets             # 智慧洞察页
│           │   │   ├── ParallelLifePage.ets         # 平行人生页
│           │   │   ├── SocialPage.ets               # 社交页
│           │   │   └── SchedulePage.ets             # 日程页
│           │   ├── components/
│           │   │   ├── sphere/
│           │   │   │   ├── SphereView.ets           # 球体组件
│           │   │   │   ├── AgentNode.ets            # 智能体节点
│           │   │   │   └── ConnectionLine.ets       # 连线组件
│           │   │   ├── decision/
│           │   │   │   ├── PersonaInteractionView.ets
│           │   │   │   ├── DecisionInfoCollector.ets
│           │   │   │   └── OptionCard.ets
│           │   │   ├── knowledge/
│           │   │   │   ├── StarMapView.ets          # 星图视图
│           │   │   │   └── NodeDetailPanel.ets
│           │   │   └── common/
│           │   │       ├── LoadingSpinner.ets
│           │   │       └── ErrorToast.ets
│           │   ├── services/
│           │   │   ├── AuthService.ets              # 认证服务
│           │   │   ├── AICoreService.ets            # AI核心服务
│           │   │   ├── KnowledgeGraphService.ets    # 知识图谱服务
│           │   │   ├── DecisionService.ets          # 决策服务
│           │   │   ├── InsightsService.ets          # 洞察服务
│           │   │   ├── ParallelLifeService.ets      # 平行人生服务
│           │   │   ├── SocialService.ets            # 社交服务
│           │   │   └── ScheduleService.ets          # 日程服务
│           │   ├── utils/
│           │   │   ├── HttpClient.ets               # HTTP客户端
│           │   │   ├── WebSocketClient.ets          # WebSocket客户端
│           │   │   ├── HttpInterceptor.ets          # HTTP拦截器
│           │   │   ├── OfflineCache.ets             # 离线缓存
│           │   │   └── DataPreloader.ets            # 数据预加载
│           │   ├── models/
│           │   │   ├── User.ets
│           │   │   ├── Decision.ets
│           │   │   ├── KnowledgeNode.ets
│           │   │   ├── Agent.ets
│           │   │   └── Schedule.ets
│           │   └── constants/
│           │       ├── ApiConstants.ets             # API常量
│           │       └── AppConstants.ets             # 应用常量
│           └── resources/
│               ├── base/
│               │   ├── element/
│               │   ├── media/
│               │   └── profile/
│               └── rawfile/
│                   └── lottie/
│                       └── sphere_animation.json
├── HARMONYOS_BACKEND_INTEGRATION.md                 # 本文档
└── README.md
```

### 核心组件设计

**1. 主页（Index.ets）**
```typescript
@Entry
@Component
struct Index {
  @State currentUser: User | null = null;
  @State selectedModule: string = '';
  
  aboutToAppear() {
    this.checkLoginStatus();
  }
  
  async checkLoginStatus() {
    const authService = new AuthService();
    const token = await authService.getToken();
    
    if (!token) {
      router.pushUrl({ url: 'pages/LoginPage' });
      return;
    }
    
    // 预加载用户数据
    const preloader = new DataPreloader();
    await preloader.preloadUserData(this.currentUser.user_id);
  }
  
  build() {
    Column() {
      // 顶部导航栏
      Row() {
        Text('LifeSwarm')
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
        
        Blank()
        
        Image($r('app.media.avatar'))
          .width(40)
          .height(40)
          .borderRadius(20)
          .onClick(() => {
            // 打开用户中心
          })
      }
      .width('100%')
      .padding(16)
      
      // 功能球体网格
      Grid() {
        GridItem() {
          FunctionSphere({
            title: '决策副本',
            icon: $r('app.media.decision_icon'),
            color: '#667eea',
            onClick: () => {
              router.pushUrl({ url: 'pages/DecisionSimulationPage' });
            }
          })
        }
        
        GridItem() {
          FunctionSphere({
            title: '知识星图',
            icon: $r('app.media.knowledge_icon'),
            color: '#764ba2',
            onClick: () => {
              router.pushUrl({ url: 'pages/KnowledgeGraphPage' });
            }
          })
        }
        
        GridItem() {
          FunctionSphere({
            title: '智慧洞察',
            icon: $r('app.media.insights_icon'),
            color: '#f093fb',
            onClick: () => {
              router.pushUrl({ url: 'pages/InsightsPage' });
            }
          })
        }
        
        GridItem() {
          FunctionSphere({
            title: '平行人生',
            icon: $r('app.media.parallel_icon'),
            color: '#4facfe',
            onClick: () => {
              router.pushUrl({ url: 'pages/ParallelLifePage' });
            }
          })
        }
        
        GridItem() {
          FunctionSphere({
            title: '树洞世界',
            icon: $r('app.media.social_icon'),
            color: '#43e97b',
            onClick: () => {
              router.pushUrl({ url: 'pages/SocialPage' });
            }
          })
        }
        
        GridItem() {
          FunctionSphere({
            title: '智能日程',
            icon: $r('app.media.schedule_icon'),
            color: '#fa709a',
            onClick: () => {
              router.pushUrl({ url: 'pages/SchedulePage' });
            }
          })
        }
      }
      .columnsTemplate('1fr 1fr')
      .rowsTemplate('1fr 1fr 1fr')
      .columnsGap(16)
      .rowsGap(16)
      .width('100%')
      .height('100%')
      .padding(16)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }
}

@Component
struct FunctionSphere {
  @Prop title: string;
  @Prop icon: Resource;
  @Prop color: string;
  @Prop onClick: () => void;
  
  build() {
    Column() {
      // 使用Canvas绘制球体
      SphereView({ color: this.color })
        .width(120)
        .height(120)
      
      Text(this.title)
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .margin({ top: 12 })
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .backgroundColor(Color.White)
    .borderRadius(16)
    .shadow({
      radius: 20,
      color: 'rgba(0, 0, 0, 0.1)',
      offsetX: 0,
      offsetY: 4
    })
    .onClick(this.onClick)
  }
}
```

**2. 决策推演页（DecisionSimulationPage.ets）**
```typescript
@Entry
@Component
struct DecisionSimulationPage {
  @State sessionId: string = '';
  @State question: string = '';
  @State options: Option[] = [];
  @State selectedOption: Option | null = null;
  @State agents: Agent[] = [];
  @State isSimulating: boolean = false;
  @State totalScore: number = 0;
  
  private decisionService: DecisionService = new DecisionService();
  private wsClient: WebSocketClient | null = null;
  
  aboutToAppear() {
    this.startInfoCollection();
  }
  
  async startInfoCollection() {
    const userId = await this.getCurrentUserId();
    const result = await this.decisionService.startCollection(
      userId,
      '我应该选择哪个职业方向？',
      'career'
    );
    
    this.sessionId = result.session_id;
    // 显示信息收集对话界面
  }
  
  async startSimulation(option: Option) {
    this.selectedOption = option;
    this.isSimulating = true;
    
    const userId = await this.getCurrentUserId();
    
    await this.decisionService.startSimulation(
      this.sessionId,
      userId,
      this.question,
      option,
      0,
      {},
      'career',
      (event) => {
        this.handleWebSocketMessage(event);
      }
    );
  }
  
  handleWebSocketMessage(event: any) {
    switch (event.type) {
      case 'agents_start':
        this.agents = event.agents.map(a => ({
          id: a.id,
          name: a.name,
          status: 'waiting',
          score: undefined
        }));
        break;
        
      case 'agent_thinking':
        this.updateAgentStatus(event.agent_id, 'thinking', event.content);
        break;
        
      case 'persona_analysis':
        this.updateAgentAnalysis(
          event.persona_id,
          event.persona_data.score,
          event.persona_data.stance
        );
        this.calculateTotalScore();
        break;
        
      case 'option_complete':
        this.isSimulating = false;
        this.totalScore = event.final_score;
        break;
    }
  }
  
  updateAgentStatus(agentId: string, status: string, message: string) {
    this.agents = this.agents.map(agent => {
      if (agent.id === agentId) {
        return { ...agent, status, currentMessage: message };
      }
      return agent;
    });
  }
  
  updateAgentAnalysis(agentId: string, score: number, stance: string) {
    this.agents = this.agents.map(agent => {
      if (agent.id === agentId) {
        return { ...agent, status: 'complete', score, stance };
      }
      return agent;
    });
  }
  
  calculateTotalScore() {
    const completedAgents = this.agents.filter(a => a.score !== undefined);
    if (completedAgents.length > 0) {
      const sum = completedAgents.reduce((acc, a) => acc + (a.score || 0), 0);
      this.totalScore = sum / completedAgents.length;
    }
  }
  
  build() {
    Stack() {
      // 背景
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 135,
          colors: [[0xF0F7FF, 0.0], [0xE8F4FF, 1.0]]
        })
      
      // 中心选项球体
      if (this.selectedOption) {
        SphereView({
          title: this.selectedOption.title,
          size: 200
        })
          .position({ x: '50%', y: '50%' })
          .translate({ x: '-50%', y: '-50%' })
      }
      
      // 智能体节点（环形分布）
      ForEach(this.agents, (agent: Agent, index: number) => {
        const angle = (index / this.agents.length) * Math.PI * 2;
        const radius = 250;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        
        AgentNode({
          agent: agent,
          onTap: () => {
            // 显示Agent详情
          }
        })
          .width(120)
          .height(120)
          .position({
            x: `calc(50% + ${x}px)`,
            y: `calc(50% + ${y}px)`
          })
          .translate({ x: '-50%', y: '-50%' })
      }, (agent: Agent) => agent.id)
      
      // 总分显示
      if (this.totalScore > 0) {
        Column() {
          Text(`综合评分`)
            .fontSize(14)
            .fontColor('#999')
          Text(`${this.totalScore.toFixed(1)}`)
            .fontSize(32)
            .fontWeight(FontWeight.Bold)
            .fontColor('#0A59F7')
        }
        .position({ x: '50%', y: 80 })
        .translate({ x: '-50%', y: 0 })
      }
      
      // 返回按钮
      Button('返回')
        .position({ x: 16, y: 16 })
        .onClick(() => {
          this.decisionService.closeSimulation();
          router.back();
        })
    }
    .width('100%')
    .height('100%')
  }
}
```

---


## 🎨 UI组件库

### 球体组件（SphereView.ets）

```typescript
@Component
export struct SphereView {
  @Prop title: string = '';
  @Prop size: number = 120;
  @Prop color: string = '#0A59F7';
  @Prop status: 'idle' | 'thinking' | 'complete' = 'idle';
  
  private settings: RenderingContextSettings = new RenderingContextSettings(true);
  private context: CanvasRenderingContext2D = new CanvasRenderingContext2D(this.settings);
  
  build() {
    Stack() {
      Canvas(this.context)
        .width(this.size)
        .height(this.size)
        .onReady(() => {
          this.drawSphere();
        })
      
      if (this.title) {
        Text(this.title)
          .fontSize(14)
          .fontWeight(FontWeight.Bold)
          .fontColor('#1A1A1A')
          .maxLines(2)
          .textAlign(TextAlign.Center)
          .width('80%')
      }
    }
    .width(this.size)
    .height(this.size)
  }
  
  drawSphere() {
    const centerX = this.size / 2;
    const centerY = this.size / 2;
    const radius = this.size / 2 - 10;
    
    // 清空画布
    this.context.clearRect(0, 0, this.size, this.size);
    
    // 绘制外部光晕
    const haloGradient = this.context.createRadialGradient(
      centerX, centerY, radius * 0.8,
      centerX, centerY, radius * 1.3
    );
    haloGradient.addColorStop(0, this.hexToRgba(this.color, 0.2));
    haloGradient.addColorStop(1, this.hexToRgba(this.color, 0));
    
    this.context.beginPath();
    this.context.arc(centerX, centerY, radius * 1.3, 0, Math.PI * 2);
    this.context.fillStyle = haloGradient;
    this.context.fill();
    
    // 绘制球体主体
    const gradient = this.context.createRadialGradient(
      centerX - radius * 0.3, centerY - radius * 0.3, 0,
      centerX, centerY, radius
    );
    gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
    gradient.addColorStop(0.3, 'rgba(255, 255, 255, 0.95)');
    gradient.addColorStop(0.7, this.hexToRgba(this.color, 0.9));
    gradient.addColorStop(1, this.hexToRgba(this.color, 0.85));
    
    this.context.beginPath();
    this.context.arc(centerX, centerY, radius, 0, Math.PI * 2);
    this.context.fillStyle = gradient;
    this.context.fill();
    
    // 绘制高光
    const highlightGradient = this.context.createRadialGradient(
      centerX - radius * 0.4, centerY - radius * 0.4, 0,
      centerX - radius * 0.4, centerY - radius * 0.4, radius * 0.35
    );
    highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.7)');
    highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
    
    this.context.beginPath();
    this.context.arc(centerX - radius * 0.4, centerY - radius * 0.4, radius * 0.35, 0, Math.PI * 2);
    this.context.fillStyle = highlightGradient;
    this.context.fill();
    
    // 绘制边框
    this.context.beginPath();
    this.context.arc(centerX, centerY, radius, 0, Math.PI * 2);
    this.context.strokeStyle = this.hexToRgba(this.color, 0.6);
    this.context.lineWidth = 2;
    this.context.stroke();
    
    // 思考状态动画
    if (this.status === 'thinking') {
      this.animateThinking();
    }
  }
  
  animateThinking() {
    // 使用定时器实现脉冲动画
    let scale = 1.0;
    let growing = true;
    
    const animate = () => {
      if (growing) {
        scale += 0.01;
        if (scale >= 1.05) growing = false;
      } else {
        scale -= 0.01;
        if (scale <= 1.0) growing = true;
      }
      
      this.context.save();
      this.context.scale(scale, scale);
      this.drawSphere();
      this.context.restore();
      
      if (this.status === 'thinking') {
        setTimeout(animate, 50);
      }
    };
    
    animate();
  }
  
  hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
}
```

### 智能体节点组件（AgentNode.ets）

```typescript
@Component
export struct AgentNode {
  @ObjectLink agent: Agent;
  @Prop onTap: () => void;
  
  build() {
    Stack() {
      // 球体
      SphereView({
        title: '',
        size: 120,
        color: this.getAgentColor(),
        status: this.agent.status
      })
      
      // 名称标签
      Text(this.agent.name)
        .fontSize(13)
        .fontWeight(FontWeight.Bold)
        .fontColor('#1A1A1A')
        .backgroundColor('rgba(255, 255, 255, 0.95)')
        .padding({ left: 14, right: 14, top: 5, bottom: 5 })
        .borderRadius(12)
        .position({ x: '50%', y: -30 })
        .translate({ x: '-50%', y: 0 })
      
      // 评分显示
      if (this.agent.score !== undefined) {
        Column() {
          Text(`${this.agent.score}`)
            .fontSize(16)
            .fontWeight(FontWeight.Bold)
            .fontColor('#1A1A1A')
          Text('分')
            .fontSize(10)
            .fontColor('#999')
        }
        .backgroundColor(Color.White)
        .padding(8)
        .borderRadius(12)
        .border({
          width: 2,
          color: this.getScoreColor(this.agent.score)
        })
        .position({ x: '50%', y: '100%' })
        .translate({ x: '-50%', y: 10 })
      }
      
      // 立场标签
      if (this.agent.stance) {
        Text(this.agent.stance)
          .fontSize(11)
          .fontWeight(FontWeight.Medium)
          .fontColor(this.getStanceColor(this.agent.stance))
          .backgroundColor(this.getStanceBackground(this.agent.stance))
          .padding({ left: 10, right: 10, top: 4, bottom: 4 })
          .borderRadius(8)
          .border({
            width: 1,
            color: this.getStanceColor(this.agent.stance)
          })
          .position({ x: '50%', y: '100%' })
          .translate({ x: '-50%', y: 50 })
      }
      
      // 消息气泡
      if (this.agent.currentMessage) {
        MessageBubble({
          message: this.agent.currentMessage,
          action: this.agent.messageAction
        })
          .position({ x: '120%', y: '50%' })
          .translate({ x: 0, y: '-50%' })
      }
    }
    .width(120)
    .height(120)
    .onClick(this.onTap)
  }
  
  getAgentColor(): string {
    const colors = {
      'rational_analyst': '#0A59F7',
      'emotional_resonator': '#FF3B30',
      'risk_assessor': '#FF9500',
      'opportunity_explorer': '#34C759',
      'moral_guardian': '#6B48FF',
      'pragmatist': '#8E8E93',
      'innovator': '#00C7BE'
    };
    return colors[this.agent.id] || '#0A59F7';
  }
  
  getScoreColor(score: number): string {
    if (score >= 70) return '#34C759';
    if (score >= 40) return '#FF9500';
    return '#FF3B30';
  }
  
  getStanceColor(stance: string): string {
    if (stance === '支持') return '#34C759';
    if (stance === '反对') return '#FF3B30';
    return '#8E8E93';
  }
  
  getStanceBackground(stance: string): string {
    if (stance === '支持') return 'rgba(52, 199, 89, 0.1)';
    if (stance === '反对') return 'rgba(255, 59, 48, 0.1)';
    return 'rgba(142, 142, 147, 0.1)';
  }
}

@Component
struct MessageBubble {
  @Prop message: string;
  @Prop action: string = '';
  
  build() {
    Column() {
      Text(this.message)
        .fontSize(11)
        .fontColor('#1A1A1A')
        .maxLines(3)
        .textOverflow({ overflow: TextOverflow.Ellipsis })
    }
    .width(160)
    .padding(12)
    .backgroundColor(Color.White)
    .borderRadius(12)
    .border({
      width: 2,
      color: this.getBorderColor()
    })
    .shadow({
      radius: 16,
      color: 'rgba(0, 0, 0, 0.2)',
      offsetX: 0,
      offsetY: 4
    })
  }
  
  getBorderColor(): string {
    switch (this.action) {
      case 'thinking': return '#0A59F7';
      case 'retrieving': return '#FF9500';
      case 'analyzing': return '#6B48FF';
      case 'analysis_done': return '#34C759';
      default: return '#0A59F7';
    }
  }
}
```

### 星图视图组件（StarMapView.ets）

```typescript
@Component
export struct StarMapView {
  @State nodes: KnowledgeNode[] = [];
  @State edges: KnowledgeEdge[] = [];
  @State selectedNode: KnowledgeNode | null = null;
  
  private settings: RenderingContextSettings = new RenderingContextSettings(true);
  private context: CanvasRenderingContext2D = new CanvasRenderingContext2D(this.settings);
  
  build() {
    Stack() {
      // 背景
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 135,
          colors: [[0x0A1929, 0.0], [0x1A2332, 1.0]]
        })
      
      // Canvas绘制星图
      Canvas(this.context)
        .width('100%')
        .height('100%')
        .onReady(() => {
          this.drawStarMap();
        })
        .onTouch((event: TouchEvent) => {
          if (event.type === TouchType.Down) {
            this.handleTouch(event.touches[0].x, event.touches[0].y);
          }
        })
      
      // 节点详情面板
      if (this.selectedNode) {
        NodeDetailPanel({
          node: this.selectedNode,
          onClose: () => {
            this.selectedNode = null;
          }
        })
          .position({ x: 16, y: 80 })
      }
      
      // 图例
      Column() {
        Text('图例')
          .fontSize(14)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
          .margin({ bottom: 8 })
        
        ForEach(this.getLegendItems(), (item: LegendItem) => {
          Row() {
            Circle()
              .width(12)
              .height(12)
              .fill(item.color)
            
            Text(item.label)
              .fontSize(12)
              .fontColor(Color.White)
              .margin({ left: 8 })
          }
          .margin({ bottom: 4 })
        })
      }
      .padding(16)
      .backgroundColor('rgba(0, 0, 0, 0.6)')
      .borderRadius(12)
      .position({ x: 16, y: '100%' })
      .translate({ x: 0, y: -16 })
      .alignItems(HorizontalAlign.Start)
    }
    .width('100%')
    .height('100%')
  }
  
  drawStarMap() {
    // 清空画布
    this.context.clearRect(0, 0, this.context.width, this.context.height);
    
    // 绘制连线
    this.edges.forEach(edge => {
      const fromNode = this.nodes.find(n => n.id === edge.from);
      const toNode = this.nodes.find(n => n.id === edge.to);
      
      if (fromNode && toNode) {
        this.context.beginPath();
        this.context.moveTo(fromNode.x, fromNode.y);
        this.context.lineTo(toNode.x, toNode.y);
        this.context.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        this.context.lineWidth = 1;
        this.context.stroke();
      }
    });
    
    // 绘制节点
    this.nodes.forEach(node => {
      // 节点光晕
      const haloGradient = this.context.createRadialGradient(
        node.x, node.y, 0,
        node.x, node.y, node.size * 2
      );
      haloGradient.addColorStop(0, this.hexToRgba(node.color, 0.3));
      haloGradient.addColorStop(1, this.hexToRgba(node.color, 0));
      
      this.context.beginPath();
      this.context.arc(node.x, node.y, node.size * 2, 0, Math.PI * 2);
      this.context.fillStyle = haloGradient;
      this.context.fill();
      
      // 节点主体
      const gradient = this.context.createRadialGradient(
        node.x - node.size * 0.3, node.y - node.size * 0.3, 0,
        node.x, node.y, node.size
      );
      gradient.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
      gradient.addColorStop(1, node.color);
      
      this.context.beginPath();
      this.context.arc(node.x, node.y, node.size, 0, Math.PI * 2);
      this.context.fillStyle = gradient;
      this.context.fill();
      
      // 节点边框
      this.context.beginPath();
      this.context.arc(node.x, node.y, node.size, 0, Math.PI * 2);
      this.context.strokeStyle = node.color;
      this.context.lineWidth = 2;
      this.context.stroke();
      
      // 节点标签
      this.context.fillStyle = Color.White;
      this.context.font = '12px sans-serif';
      this.context.textAlign = 'center';
      this.context.fillText(node.label, node.x, node.y + node.size + 16);
    });
  }
  
  handleTouch(x: number, y: number) {
    // 检测点击的节点
    const clickedNode = this.nodes.find(node => {
      const distance = Math.sqrt(
        Math.pow(x - node.x, 2) + Math.pow(y - node.y, 2)
      );
      return distance <= node.size;
    });
    
    if (clickedNode) {
      this.selectedNode = clickedNode;
    }
  }
  
  getLegendItems(): LegendItem[] {
    return [
      { color: '#0A59F7', label: '技能/学业' },
      { color: '#34C759', label: '岗位/学校' },
      { color: '#FF9500', label: '公司/行动' },
      { color: '#FF3B30', label: '人际关系' }
    ];
  }
  
  hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
}

interface LegendItem {
  color: string;
  label: string;
}
```

---


## 📊 数据模型

### 核心数据模型定义

```typescript
// models/User.ets
export class User {
  user_id: string = '';
  username: string = '';
  email: string = '';
  nickname: string = '';
  avatar: string = '';
  created_at: string = '';
}

// models/Decision.ets
export class Decision {
  session_id: string = '';
  user_id: string = '';
  question: string = '';
  decision_type: string = '';
  collected_info: any = {};
  options: Option[] = [];
  chosen_option: string = '';
  actual_outcome: string = '';
  created_at: string = '';
}

export class Option {
  option_id: string = '';
  title: string = '';
  description: string = '';
  final_score: number = 0;
  risk_level: number = 0;
  execution_confidence: number = 0;
  timeline: TimelineEvent[] = [];
}

export class TimelineEvent {
  event_id: string = '';
  month: number = 0;
  event: string = '';
  probability: number = 0;
  impact: number = 0;
  risk_tag: string = '';
}

// models/Agent.ets
@Observed
export class Agent {
  id: string = '';
  name: string = '';
  status: 'waiting' | 'thinking' | 'complete' | 'error' = 'waiting';
  score?: number;
  stance?: string;
  currentMessage?: string;
  messageTimestamp?: number;
  messageAction?: string;
  thinkingHistory: ThinkingRecord[] = [];
}

export class ThinkingRecord {
  round: number = 0;
  message: string = '';
  timestamp: number = 0;
  score?: number;
  stance?: string;
  keyPoints: string[] = [];
  reasoning: string = '';
  action?: string;
  skillResult?: any;
}

// models/KnowledgeNode.ets
export class KnowledgeNode {
  id: string = '';
  label: string = '';
  type: string = '';
  layer: string = '';
  x: number = 0;
  y: number = 0;
  z: number = 0;
  size: number = 10;
  color: string = '#0A59F7';
  properties: Record<string, any> = {};
}

export class KnowledgeEdge {
  from: string = '';
  to: string = '';
  type: string = '';
  weight: number = 1.0;
}

// models/Schedule.ets
export class Schedule {
  schedule_id: string = '';
  user_id: string = '';
  title: string = '';
  description: string = '';
  start_time: string = '';
  end_time: string = '';
  priority: 'high' | 'medium' | 'low' = 'medium';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled' = 'pending';
  tags: string[] = [];
  created_at: string = '';
}

// models/Insight.ets
export class Insight {
  insight_id: string = '';
  user_id: string = '';
  insight_type: 'relationship' | 'education' | 'career' = 'relationship';
  key_findings: string[] = [];
  recommendations: string[] = [];
  decision_logic: any = {};
  confidence: number = 0;
  created_at: string = '';
}

// models/Post.ets
export class Post {
  post_id: string = '';
  user_id: string = '';
  content: string = '';
  is_anonymous: boolean = false;
  tags: string[] = [];
  likes_count: number = 0;
  comments_count: number = 0;
  created_at: string = '';
}

export class Comment {
  comment_id: string = '';
  post_id: string = '';
  user_id: string = '';
  content: string = '';
  created_at: string = '';
}
```

---

## 🔧 工具类和辅助函数

### 常量定义

```typescript
// constants/ApiConstants.ets
export class ApiConstants {
  // 后端地址（需要根据实际部署修改）
  static readonly BASE_URL = 'http://your-backend:8000';
  
  // API端点
  static readonly AUTH = {
    REGISTER: '/api/auth/register',
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout'
  };
  
  static readonly AI_CORE = {
    INTENT: '/api/v5/ai-core/intent',
    NAVIGATE: '/api/v5/ai-core/navigate'
  };
  
  static readonly KNOWLEDGE = {
    ADD_INFO: '/api/knowledge/add-info',
    QUERY: '/api/knowledge/query',
    RELATIONSHIPS: '/api/knowledge/relationships',
    STATS: '/api/knowledge/stats'
  };
  
  static readonly DECISION = {
    START_COLLECTION: '/api/decision/persona/collect/start',
    CONTINUE_COLLECTION: '/api/decision/persona/collect/continue',
    GENERATE_OPTIONS: '/api/decision/persona/generate-options',
    SESSION: '/api/decision/persona/collect/session',
    UPDATE_OUTCOME: '/api/decision/persona/update-outcome'
  };
  
  static readonly INSIGHTS = {
    RELATIONSHIP: '/api/insights/realtime/relationship/insight',
    EDUCATION: '/api/insights/realtime/education/insight',
    CAREER: '/api/insights/realtime/career/insight',
    AGENTS_STATUS: '/api/insights/realtime/agents/status'
  };
  
  static readonly PARALLEL_LIFE = {
    START_GAME: '/api/v5/parallel-life/start-game',
    SUBMIT_CHOICE: '/api/v5/parallel-life/submit-choice',
    DECISION_PROFILE: '/api/v5/parallel-life/decision-profile'
  };
  
  static readonly SOCIAL = {
    FRIENDS_LIST: '/api/friends/list',
    FRIENDS_ADD: '/api/friends/add',
    TREE_HOLE_POSTS: '/api/tree-hole/posts',
    TREE_HOLE_POST: '/api/tree-hole/post',
    TREE_HOLE_COMMENT: '/api/tree-hole/comment'
  };
  
  static readonly SCHEDULE = {
    LIST: '/api/v5/schedule/list',
    ADD: '/api/v5/schedule/add',
    RECOMMEND: '/api/v5/schedule/recommend',
    AUTO_GENERATE: '/api/v5/schedule/auto-generate'
  };
  
  // WebSocket端点
  static readonly WS = {
    CHAT: 'ws://your-backend:8000/ws/chat',
    DECISION_SIMULATE: 'ws://your-backend:8000/ws/decision/simulate-option'
  };
}

// constants/AppConstants.ets
export class AppConstants {
  // 应用配置
  static readonly APP_NAME = 'LifeSwarm';
  static readonly APP_VERSION = '1.0.0';
  
  // 缓存键
  static readonly CACHE_KEYS = {
    USER_INFO: 'user_info',
    AUTH_TOKEN: 'auth_token',
    STAR_MAPS: 'star_maps',
    RECENT_CONVERSATIONS: 'recent_conversations'
  };
  
  // 颜色主题
  static readonly COLORS = {
    PRIMARY: '#0A59F7',
    SUCCESS: '#34C759',
    WARNING: '#FF9500',
    DANGER: '#FF3B30',
    INFO: '#00C7BE',
    PURPLE: '#6B48FF',
    GRAY: '#8E8E93'
  };
  
  // 动画时长
  static readonly ANIMATION = {
    FAST: 200,
    NORMAL: 300,
    SLOW: 500
  };
}
```

### 工具函数

```typescript
// utils/DateUtils.ets
export class DateUtils {
  static formatDate(timestamp: number | string): string {
    const date = new Date(timestamp);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
  
  static formatDateTime(timestamp: number | string): string {
    const date = new Date(timestamp);
    const dateStr = this.formatDate(timestamp);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${dateStr} ${hours}:${minutes}`;
  }
  
  static getRelativeTime(timestamp: number | string): string {
    const now = Date.now();
    const time = new Date(timestamp).getTime();
    const diff = now - time;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    return '刚刚';
  }
}

// utils/StringUtils.ets
export class StringUtils {
  static truncate(str: string, maxLength: number): string {
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
  }
  
  static isEmpty(str: string | null | undefined): boolean {
    return !str || str.trim().length === 0;
  }
  
  static isEmail(email: string): boolean {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return regex.test(email);
  }
  
  static isUsername(username: string): boolean {
    const regex = /^[a-zA-Z0-9_]{3,20}$/;
    return regex.test(username);
  }
}

// utils/ColorUtils.ets
export class ColorUtils {
  static hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  
  static getScoreColor(score: number): string {
    if (score >= 70) return AppConstants.COLORS.SUCCESS;
    if (score >= 40) return AppConstants.COLORS.WARNING;
    return AppConstants.COLORS.DANGER;
  }
  
  static getStanceColor(stance: string): string {
    if (stance === '支持') return AppConstants.COLORS.SUCCESS;
    if (stance === '反对') return AppConstants.COLORS.DANGER;
    return AppConstants.COLORS.GRAY;
  }
}

// utils/GeometryUtils.ets
export class GeometryUtils {
  // 计算环形分布的节点位置
  static calculateCirclePositions(
    count: number,
    centerX: number,
    centerY: number,
    radius: number
  ): Array<{ x: number, y: number }> {
    const positions: Array<{ x: number, y: number }> = [];
    
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2 - Math.PI / 2; // 从顶部开始
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;
      positions.push({ x, y });
    }
    
    return positions;
  }
  
  // 计算Fibonacci球面分布（用于3D星图）
  static calculateFibonacciSphere(
    count: number,
    radius: number
  ): Array<{ x: number, y: number, z: number }> {
    const positions: Array<{ x: number, y: number, z: number }> = [];
    const phi = Math.PI * (3 - Math.sqrt(5)); // 黄金角
    
    for (let i = 0; i < count; i++) {
      const y = 1 - (i / (count - 1)) * 2; // y从1到-1
      const radiusAtY = Math.sqrt(1 - y * y);
      const theta = phi * i;
      
      const x = Math.cos(theta) * radiusAtY * radius;
      const z = Math.sin(theta) * radiusAtY * radius;
      
      positions.push({ x, y: y * radius, z });
    }
    
    return positions;
  }
  
  // 计算两点之间的距离
  static distance(x1: number, y1: number, x2: number, y2: number): number {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  }
}
```

---


## 🚀 部署和配置

### 后端部署

**1. 本地开发环境**
```bash
# 启动后端服务
cd backend
python start_server.py

# 后端将运行在 http://localhost:8000
```

**2. 生产环境部署**
```bash
# 使用Docker部署
docker-compose up -d

# 或使用云服务器
# 配置Nginx反向代理
# 配置SSL证书
```

### HarmonyOS配置

**1. 修改API地址**

在 `constants/ApiConstants.ets` 中修改后端地址：

```typescript
// 开发环境
static readonly BASE_URL = 'http://192.168.1.100:8000';

// 生产环境
static readonly BASE_URL = 'https://api.your-domain.com';
```

**2. 配置网络权限**

在 `entry/src/main/module.json5` 中添加网络权限：

```json
{
  "module": {
    "requestPermissions": [
      {
        "name": "ohos.permission.INTERNET"
      },
      {
        "name": "ohos.permission.GET_NETWORK_INFO"
      }
    ]
  }
}
```

**3. 配置HTTP白名单**

在 `entry/src/main/resources/base/profile/network_config.json` 中配置：

```json
{
  "network-security-config": {
    "domain-config": [
      {
        "domains": [
          {
            "include-subdomains": true,
            "name": "your-backend-domain.com"
          }
        ],
        "cleartextTrafficPermitted": true
      }
    ]
  }
}
```

---

## 🧪 测试指南

### 单元测试

```typescript
// test/services/DecisionService.test.ets
import { describe, it, expect } from '@ohos/hypium';
import { DecisionService } from '../../main/ets/services/DecisionService';

export default function DecisionServiceTest() {
  describe('DecisionService', () => {
    it('should start collection successfully', async () => {
      const service = new DecisionService();
      const result = await service.startCollection(
        'test_user',
        '测试问题',
        'general'
      );
      
      expect(result.session_id).not.toBeNull();
      expect(result.message).not.toBeNull();
    });
    
    it('should generate options successfully', async () => {
      const service = new DecisionService();
      const result = await service.generateOptions(
        'test_session',
        'test_user'
      );
      
      expect(result.options).not.toBeNull();
      expect(result.options.length).toBeGreaterThan(0);
    });
  });
}
```

### 集成测试

```typescript
// test/integration/DecisionFlow.test.ets
import { describe, it, expect } from '@ohos/hypium';
import { DecisionService } from '../../main/ets/services/DecisionService';

export default function DecisionFlowTest() {
  describe('Decision Flow Integration', () => {
    it('should complete full decision flow', async () => {
      const service = new DecisionService();
      
      // 1. 开始信息收集
      const session = await service.startCollection(
        'test_user',
        '我应该选择哪个职业？',
        'career'
      );
      expect(session.session_id).not.toBeNull();
      
      // 2. 继续信息收集
      const progress = await service.continueCollection(
        session.session_id,
        'test_user',
        '我喜欢编程'
      );
      expect(progress.is_complete).toBeDefined();
      
      // 3. 生成选项
      const options = await service.generateOptions(
        session.session_id,
        'test_user'
      );
      expect(options.options.length).toBeGreaterThan(0);
      
      // 4. WebSocket推演（需要mock）
      // ...
    });
  });
}
```

---

## 📝 开发规范

### 代码规范

**1. 命名规范**
- 类名：PascalCase（如 `DecisionService`）
- 方法名：camelCase（如 `startCollection`）
- 常量：UPPER_SNAKE_CASE（如 `BASE_URL`）
- 私有成员：以下划线开头（如 `_context`）

**2. 注释规范**
```typescript
/**
 * 决策服务类
 * 提供决策推演相关的所有功能
 */
export class DecisionService {
  /**
   * 开始信息收集
   * @param userId 用户ID
   * @param question 决策问题
   * @param decisionType 决策类型
   * @returns 会话信息
   */
  async startCollection(
    userId: string,
    question: string,
    decisionType: string
  ): Promise<SessionInfo> {
    // 实现代码
  }
}
```

**3. 错误处理**
```typescript
try {
  const result = await service.someMethod();
  return result;
} catch (error) {
  console.error('操作失败:', error);
  // 显示用户友好的错误提示
  promptAction.showToast({
    message: '操作失败，请稍后重试',
    duration: 2000
  });
  throw error;
}
```

### Git提交规范

```bash
# 功能开发
git commit -m "feat: 添加决策推演功能"

# Bug修复
git commit -m "fix: 修复WebSocket连接断开问题"

# 文档更新
git commit -m "docs: 更新API对接文档"

# 样式调整
git commit -m "style: 优化球体渲染效果"

# 重构
git commit -m "refactor: 重构HTTP客户端"

# 性能优化
git commit -m "perf: 优化星图渲染性能"

# 测试
git commit -m "test: 添加决策服务单元测试"
```

---

## 🔍 常见问题

### Q1: WebSocket连接失败

**问题**: WebSocket无法连接到后端

**解决方案**:
1. 检查后端服务是否正常运行
2. 检查网络权限是否配置
3. 检查防火墙设置
4. 使用 `ws://` 而不是 `wss://`（开发环境）
5. 检查后端CORS配置

```typescript
// 添加连接超时处理
const timeout = setTimeout(() => {
  console.error('WebSocket连接超时');
  ws.close();
}, 10000);

ws.on('open', () => {
  clearTimeout(timeout);
  console.log('WebSocket连接成功');
});
```

### Q2: Canvas绘制性能问题

**问题**: 球体动画卡顿

**解决方案**:
1. 使用离屏Canvas
2. 减少重绘频率
3. 使用requestAnimationFrame
4. 考虑使用Lottie动画

```typescript
// 使用离屏Canvas优化
private offscreenCanvas: OffscreenCanvas = new OffscreenCanvas(200, 200);
private offscreenContext: OffscreenCanvasRenderingContext2D = 
  this.offscreenCanvas.getContext('2d');

drawSphere() {
  // 在离屏Canvas上绘制
  this.offscreenContext.clearRect(0, 0, 200, 200);
  // ... 绘制代码
  
  // 复制到主Canvas
  this.context.drawImage(this.offscreenCanvas, 0, 0);
}
```

### Q3: 数据同步延迟

**问题**: 数据更新不及时

**解决方案**:
1. 使用WebSocket实时推送
2. 实现本地缓存
3. 使用乐观更新策略

```typescript
// 乐观更新示例
async updateSchedule(schedule: Schedule): Promise<void> {
  // 1. 立即更新本地状态
  this.schedules = this.schedules.map(s => 
    s.schedule_id === schedule.schedule_id ? schedule : s
  );
  
  try {
    // 2. 发送到后端
    await this.scheduleService.updateSchedule(schedule);
  } catch (error) {
    // 3. 失败时回滚
    console.error('更新失败，回滚本地状态');
    await this.loadSchedules();
  }
}
```

### Q4: 内存泄漏

**问题**: 应用长时间运行后卡顿

**解决方案**:
1. 及时清理WebSocket连接
2. 移除事件监听器
3. 清理定时器

```typescript
aboutToDisappear() {
  // 清理WebSocket
  if (this.wsClient) {
    this.wsClient.close();
    this.wsClient = null;
  }
  
  // 清理定时器
  if (this.animationTimer) {
    clearInterval(this.animationTimer);
    this.animationTimer = null;
  }
  
  // 清理事件监听
  this.messageHandlers.clear();
}
```

---

## 📚 参考资源

### 官方文档
- [HarmonyOS开发文档](https://developer.harmonyos.com/cn/docs)
- [ArkTS语言参考](https://developer.harmonyos.com/cn/docs/documentation/doc-references-V3/arkts-get-started-0000001504769321-V3)
- [Canvas API](https://developer.harmonyos.com/cn/docs/documentation/doc-references-V3/ts-components-canvas-canvas-0000001478181441-V3)

### 后端API文档
- 参考 `BACKEND_README.md` 了解完整的后端架构
- 参考 `backend/main.py` 查看所有API端点
- 参考各模块的README文档了解详细功能

### 示例代码
- Web端实现: `web/src/pages/DecisionSimulationPage.tsx`
- Web端样式: `web/src/components/decision/PersonaInteractionView.css`
- 后端WebSocket: `backend/decision/persona_decision_api.py`

---

## 🎯 下一步计划

### 短期目标（1-2周）
1. ✅ 完成基础架构搭建
2. ✅ 实现用户认证功能
3. ⬜ 实现决策推演核心功能
4. ⬜ 实现知识星图可视化
5. ⬜ 完成基础UI组件库

### 中期目标（1个月）
1. ⬜ 完成所有7大功能模块
2. ⬜ 优化3D球体渲染性能
3. ⬜ 实现离线缓存功能
4. ⬜ 完善错误处理和日志
5. ⬜ 编写完整的单元测试

### 长期目标（2-3个月）
1. ⬜ 性能优化和内存管理
2. ⬜ 实现数据分析和统计
3. ⬜ 添加更多可视化效果
4. ⬜ 支持多语言国际化
5. ⬜ 发布到应用市场

---

## 📞 技术支持

如有问题，请参考：
1. 本文档的常见问题部分
2. 后端README文档
3. HarmonyOS官方文档
4. 项目Issue追踪

---

**文档版本**: 2.0  
**最后更新**: 2026-04-20  
**维护者**: LifeSwarm开发团队

