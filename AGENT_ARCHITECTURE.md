# Agent架构文档 - LangChain ReAct实现

## 概述

智慧洞察的三个Agent（人际关系、教育规划、职业发展）采用**Workflow + Agent 混合架构**。

## 核心理念

- **Workflow处理确定性任务**：结构化、可预测、高效
- **Agent处理不确定性任务**：灵活、自主决策、复杂推理
- **混合使用**：Workflow编排流程，Agent在关键决策点介入
- **四模块是"器官"**：提供基础能力（LLM、记忆、工具）
- **Workflow是"骨架"**：定义任务流程和节点
- **Agent是"大脑"**：在决策点进行推理判断

## 架构设计

### 0. MCP (Model Context Protocol) 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP架构                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    MCP Host (Agent系统)                     │ │
│  │  • 管理MCP Server列表                                       │ │
│  │  • 动态发现工具                                             │ │
│  │  • 授权控制                                                 │ │
│  │  • 审计追踪                                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                            ↓                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    MCP Client                               │ │
│  │  • 发送工具调用请求                                         │ │
│  │  • 处理响应                                                 │ │
│  │  • 错误处理                                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                            ↓                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ MCP Server 1 │  │ MCP Server 2 │  │ MCP Server 3 │          │
│  │  (Github)    │  │  (Database)  │  │  (Custom)    │          │
│  │              │  │              │  │              │          │
│  │ Tools        │  │ Tools        │  │ Tools        │          │
│  │ Resources    │  │ Resources    │  │ Resources    │          │
│  │ Prompts      │  │ Prompts      │  │ Prompts      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  三层安全机制：                                                    │
│  1️⃣ 能力声明：Server明确声明工具，Agent只能调用声明的工具        │
│  2️⃣ 授权控制：敏感操作需要人工确认                                │
│  3️⃣ 审计追踪：所有调用都有日志，可追溯                            │
└─────────────────────────────────────────────────────────────────┘
```

#### MCP工作流程

**1. 工具发现（Agent启动时）**
```
Agent启动
   ↓
MCP Host扫描配置的Server列表
   ↓
向每个Server发送 tools/list 请求
   ↓
接收工具列表和描述
   ↓
将所有工具注入LLM上下文
```

**2. 工具调用（运行时）**
```
用户: "帮我在Github创建一个Issue"
   ↓
LLM发现有 github_create_issue 工具
   ↓
LLM生成结构化JSON调用指令
   ↓
MCP Client发送调用请求到Github Server
   ↓
Server调用Github API
   ↓
返回结果给Agent
   ↓
LLM生成最终回答
```

**3. Function Call四步流程**
```
1. 定义工具：告诉LLM有哪些工具可用
2. LLM判断：生成结构化JSON调用指令（不是文本）
3. 代码执行：解析JSON并调用工具
4. 结果回传：把结果传回LLM，生成最终回答
```

**4. Parallel Function Call（并行调用）**
```
LLM判断需要调用多个工具
   ↓
生成多个调用指令
   ↓
并行执行所有工具
   ↓
收集所有结果
   ↓
一次性传回LLM
```

### 1. Workflow + Agent 混合架构

```
┌─────────────────────────────────────────────────────────────────┐
│              Workflow + Agent 混合架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Workflow引擎                             │ │
│  │  START → MEMORY_LOAD → INTENT_CLASSIFY → 分支              │ │
│  │    ├─ simple → SIMPLE_RESPONSE (纯Workflow)                │ │
│  │    └─ complex → AGENT_DECISION (调用Agent)                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                            ↓                                      │
│  ┌──────────┐  ┌─────────────────┐  ┌──────────┐  ┌──────────┐ │
│  │ LLM模块  │  │   记忆模块      │  │ 工具模块 │  │  ReAct   │ │
│  │          │  │                 │  │          │  │ Executor │ │
│  │  意图    │  │ ┌─────────────┐ │  │  工具    │  │          │ │
│  │  理解    │  │ │上下文窗口   │ │  │  注册    │  │  循环    │ │
│  │  推理    │  │ │128K tokens  │ │  │  调用    │  │  控制    │ │
│  │  判断    │  │ │摘要压缩     │ │  │  结果    │  │  观察    │ │
│  └──────────┘  │ └─────────────┘ │  └──────────┘  └──────────┘ │
│       │        │ ┌─────────────┐ │       │              │       │
│       │        │ │外部记忆     │ │       │              │       │
│       │        │ │• FAISS      │ │       │              │       │
│       │        │ │• MySQL      │ │       │              │       │
│       │        │ │• Neo4j      │ │       │              │       │
│       │        │ │• Redis      │ │       │              │       │
│       │        │ └─────────────┘ │       │              │       │
│       └────────┴─────────────────┴───────┴──────────────┘       │
│                                                                   │
│  工作模式：                                                        │
│  • 简单任务 → 纯Workflow（快速响应）                              │
│  • 复杂任务 → Workflow + Agent（结构化 + 推理）                   │
└─────────────────────────────────────────────────────────────────┘
```

#### 1.0 Workflow引擎
- **职责**：编排确定性任务流程
- **功能**：
  - 定义节点和执行顺序
  - 条件分支路由
  - 在关键点调用Agent
  - 记录执行路径
- **节点类型**：
  - START：开始节点
  - MEMORY_LOAD：加载记忆
  - INTENT_CLASSIFY：意图分类（决策点）
  - SIMPLE_RESPONSE：简单回复（纯Workflow）
  - AGENT_DECISION：Agent决策（调用ReAct）
  - MEMORY_SAVE：保存记忆
  - END：结束节点

#### 1.1 LLM模块
- **职责**：意图理解和推理判断
- **功能**：
  - 理解用户意图（查询/建议/规划/问题解决）
  - 提取关键实体和上下文
  - 评估任务复杂度
  - 推理和判断分析
- **实现**：DashScopeLLM包装器（适配LangChain接口）

#### 1.2 记忆模块
- **职责**：上下文窗口管理和外部记忆存储
- **两层架构**：
  
  **上下文窗口（Context Window）**
  - **容量**：128K tokens（速度最快的短期记忆）
  - **存储内容**：
    - 当前对话历史
    - 任务状态和执行进度
    - 加载的skills和工具
    - 工具调用历史
    - 检索到的长期记忆片段
  - **压缩策略**：
    - 摘要压缩：用LLM将旧对话总结成简短摘要
    - 滑动窗口：保留最近N条完整对话
    - 关键信息提取：保留重要实体和决策点
  
  **外部记忆（External Memory）**
  - **向量数据库（FAISS）**：
    - 对话历史的语义检索
    - 用户偏好和个人信息
    - 历史任务和解决方案
  - **关系数据库（MySQL）**：
    - 结构化对话记录
    - 用户画像和统计数据
    - 任务执行日志
  - **图数据库（Neo4j）**：
    - 知识图谱（人际关系/教育路径/职业网络）
    - 实体关系和属性
    - 跨领域知识关联
  - **缓存（Redis）**：
    - 热点数据快速访问
    - 会话状态临时存储
    - 检索结果缓存

#### 1.3 工具模块
- **职责**：外部API调用、数据库、代码执行器
- **功能**：
  - 工具注册和管理
  - LangChain Tool集成
  - 工具调用和结果处理
  - 错误处理和重试
- **默认工具**：
  - `retrieve_memory`：从长期记忆检索
  - `get_current_time`：获取当前时间

#### 1.4 ReAct执行器
- **职责**：协调Thought-Action-Observation循环
- **功能**：
  - 管理ReAct循环
  - 工具选择和调用
  - 结果观察和反馈
  - 最终答案生成
- **实现**：LangChain AgentExecutor

### 2. ReAct工作模式

#### 2.1 什么是ReAct？

ReAct = **Reasoning (推理) + Acting (行动)**

工作流程：**Thought → Action → Observation → Thought → ...**

#### 2.2 ReAct循环示例

```
Question: 我和朋友最近关系有点紧张，怎么办？

Thought: 我需要先了解用户的社交关系背景
Action: retrieve_memory
Action Input: 用户的朋友关系和社交网络
Observation: 检索到相关信息：用户有3个亲密朋友...

Thought: 现在我需要分析关系紧张的原因
Action: analyze_social_network
Action Input: 用户描述的关系紧张情况
Observation: 分析结果显示可能是沟通模式问题...

Thought: 我现在有足够信息给出建议了
Final Answer: 根据你的情况，建议从以下三个方面改善...
```

#### 2.3 ReAct提示模板

```python
"""你是一个专业的{agent_type} Agent，使用ReAct（Reasoning and Acting）模式工作。

{system_prompt}

你可以使用以下工具：
{tools}

使用以下格式回答：

Question: 用户的问题
Thought: 你应该思考要做什么
Action: 要采取的行动，必须是 [{tool_names}] 中的一个
Action Input: 行动的输入
Observation: 行动的结果
... (这个 Thought/Action/Action Input/Observation 可以重复N次)
Thought: 我现在知道最终答案了
Final Answer: 对原始问题的最终答案

开始！

Question: {input}
Thought: {agent_scratchpad}"""
```

### 3. 技术栈

**核心框架**
- **LangChain**：ReAct Agent框架
  - `langchain>=0.1.0`
  - `langchain-community>=0.0.20`
  - `langchain-core>=0.1.0`
- **DashScope**：LLM服务（通义千问，128K上下文窗口）

**记忆系统**
- **向量数据库**：FAISS（语义检索）
- **关系数据库**：MySQL（结构化数据）
- **图数据库**：Neo4j（知识图谱）
- **缓存系统**：Redis（热点数据）

**其他组件**
- **SQLAlchemy**：ORM框架
- **sentence-transformers**：文本向量化

## 三个专业化Agent

### 3.1 RelationshipAgent（人际关系心理学专家）

**定位**：社会心理学和人际沟通专家

**核心能力**：
- 社交网络分析
- 关系质量诊断
- 沟通模式优化
- 冲突解决策略
- 社交技能培养

**专属工具**：
- `analyze_social_network`：分析社交网络结构
- `assess_relationship_quality`：评估关系质量
- `generate_communication_script`：生成沟通脚本

**分析框架**：
- 关系生态系统模型
- 情感账户理论
- 依恋理论
- 社会支持网络理论

### 3.2 EducationAgent（教育规划战略顾问）

**定位**：中国教育体系下的升学路径设计专家

**核心能力**：
- 升学路径规划（考研/保研/就业/出国/考公）
- 院校专业匹配（985/211/双一流）
- 竞争力分析（GPA/科研/实习/竞赛）
- 学习策略优化
- 考试备考指导

**专属工具**：
- `query_university_data`：查询大学和专业信息
- `calculate_admission_probability`：计算录取概率
- `generate_study_plan`：生成学习计划

**分析框架**：
- SWOT升学分析
- 3-5年教育投资回报率
- 学科发展趋势
- 个人-专业匹配度模型

### 3.3 CareerAgent（职业发展战略规划师）

**定位**：职场生态和行业动态专家

**核心能力**：
- 职业定位诊断（霍兰德/MBTI/技能清单）
- 行业趋势洞察
- 技能图谱构建
- 求职策略优化
- 职业转型规划

**专属工具**：
- `assess_career_competitiveness`：评估职业竞争力
- `query_job_market`：查询职位市场信息
- `generate_skill_roadmap`：生成技能学习路线图

**分析框架**：
- 职业生命周期理论
- T型人才模型
- 职业资本积累（人力/社会/心理资本）
- 5年职业规划蓝图

## 记忆管理策略

### 复杂度判断标准

系统使用LLM自动判断任务复杂度，决定使用纯Workflow还是调用Agent：

**simple（简单任务）→ 纯Workflow处理**
- 简单问候或闲聊（"你好"、"在吗"、"谢谢"）
- 单一事实查询（"什么是..."、"谁是..."、"哪里..."）
- 简单确认或澄清（"是的"、"对"、"不是"）
- 无需推理的直接回答
- 不需要调用工具或检索记忆

**medium（中等任务）→ Workflow + Agent推理**
- 需要一定分析但不复杂（"如何..."、"为什么..."）
- 需要检索用户历史信息
- 需要简单的建议或推荐
- 涉及1-2个维度的问题
- 可能需要调用1个工具

**complex（复杂任务）→ Workflow + Agent推理**
- 需要深度分析和推理（"帮我规划..."、"如何解决..."）
- 涉及多个维度或多步骤（"比较...并给出建议"）
- 需要制定计划或策略
- 需要调用多个工具或多次推理
- 开放性问题需要创造性回答
- 涉及复杂的人际关系/职业规划/教育路径

**判断示例：**
```
"你好" → simple → 纯Workflow（0.5秒响应）
"什么是职业规划" → simple → 纯Workflow（1秒响应）
"我应该考研还是工作" → medium → Workflow + Agent（3-5秒）
"帮我分析职业发展路径" → complex → Workflow + Agent（5-10秒）
```

### 记忆写入时机

1. **任务完成后**
   - 保存任务结果和关键发现
   - 记录成功的解决方案
   - 更新用户能力评估

2. **用户提供个人信息时**
   - 保存用户偏好和特征
   - 更新用户画像
   - 建立实体关系

3. **发现新知识时**
   - 更新知识库
   - 建立知识关联
   - 标记知识来源

4. **出错时**
   - 保存失败原因
   - 记录错误上下文
   - 避免重蹈覆辙

### 记忆读取时机

1. **任务开始时**
   - 加载用户偏好和历史背景
   - 检索相关对话历史
   - 获取用户画像

2. **遇到陌生问题时**
   - 检索相关历史经验
   - 查找类似案例
   - 获取领域知识

3. **需要事实核查时**
   - 检索已知信息
   - 验证数据准确性
   - 查询知识图谱

4. **上下文窗口将满时**
   - 触发摘要压缩
   - 保存重要信息到外部记忆
   - 清理过期临时数据

### 记忆压缩流程

```
上下文窗口监控
   ↓
Token使用 > 80% 阈值？
   ↓ 是
LLM摘要压缩
   ├─ 提取关键信息
   ├─ 总结对话要点
   └─ 保留最近3轮完整对话
   ↓
压缩后内容 + 摘要 → 上下文窗口
   ↓
原始对话 → 外部记忆（向量DB + MySQL）
```

## 执行流程

### 完整处理流程

```
1. 用户发送消息
   ↓
2. 记忆加载（任务开始）
   ├─ 从上下文窗口加载当前会话
   ├─ 从外部记忆检索用户偏好
   └─ 从知识图谱获取相关背景
   ↓
3. LLM模块：理解意图
   - 识别意图类型
   - 提取关键实体
   - 评估复杂度
   ↓
4. LangChain ReAct循环开始
   ↓
5. Thought：LLM决定下一步行动
   - 需要检索记忆？（陌生问题）
   - 需要使用工具？
   - 需要事实核查？
   - 可以直接回答？
   ↓
6. Action：执行行动
   - retrieve_memory：从外部记忆检索
   - use_tool：调用专属工具
   - verify_facts：事实核查
   - Final Answer：生成最终答案
   ↓
7. Observation：观察结果
   - 记录执行结果到上下文窗口
   - 反馈给LLM
   ↓
8. 重复步骤5-7（最多5次迭代）
   ↓
9. Final Answer：生成最终回复
   ↓
10. 记忆写入（任务完成）
    ├─ 保存对话到上下文窗口
    ├─ 提取关键信息到外部记忆
    ├─ 更新用户画像（如有新信息）
    ├─ 保存任务结果和发现
    └─ 记录错误（如有失败）
    ↓
11. 上下文窗口检查
    ├─ Token使用 > 80%？
    └─ 是 → 触发摘要压缩
```

### ReAct决策示例

```
迭代1:
  Thought: 我需要了解用户的背景信息
  Action: retrieve_memory
  Observation: 检索到用户的历史对话...

迭代2:
  Thought: 我需要分析用户的社交网络
  Action: analyze_social_network
  Observation: 分析结果显示...

迭代3:
  Thought: 我现在有足够信息了
  Final Answer: 根据分析，我建议...
```

## 文件结构

```
backend/agents/
├── __init__.py                          # 模块导出
├── langchain_agent_framework.py         # 核心框架（Workflow + Agent + MCP）
├── langchain_specialized_agents.py      # 三个专业化Agent
├── mcp_integration.py                   # MCP架构实现
├── mcp_example.py                       # MCP基础示例
└── agent_with_mcp_example.py            # Agent + MCP完整集成示例
```

### 核心文件说明

**langchain_agent_framework.py**（1000+ 行）：
- `Workflow`：工作流引擎
- `WorkflowNode`：工作流节点
- `LLMModule`：意图理解和推理
- `MemoryModule`：上下文窗口 + 外部记忆
- `ToolModule`：工具管理（集成MCP）
- `LangChainReActAgent`：Agent基类

**langchain_specialized_agents.py**：
- `RelationshipAgent`：人际关系专家
- `EducationAgent`：教育规划顾问
- `CareerAgent`：职业发展规划师
- `create_langchain_agent()`：Agent工厂函数

**mcp_integration.py**：
- `MCPHost`：MCP管理器
- `MCPClient`：工具调用客户端
- `MCPServer`：Server抽象基类
- `GithubMCPServer`：Github工具示例
- `DatabaseMCPServer`：数据库工具示例
- `ParallelFunctionCaller`：并行调用器
- `MCPTool`、`MCPResource`、`MCPPrompt`：资源定义
- `MCPCallLog`：审计日志

**agent_with_mcp_example.py**：
- Agent + MCP完整集成示例
- Workflow智能路由示例
- 并行调用示例

## 使用示例

### 基础使用（无MCP）

```python
from backend.agents.langchain_specialized_agents import create_langchain_agent

# 创建Agent
agent = create_langchain_agent(
    agent_type='relationship',
    user_id='user_123',
    llm_service=llm_service,
    rag_system=rag_system,
    retrieval_system=retrieval_system,
    use_workflow=True  # 启用Workflow混合模式
)

# 处理消息
result = agent.process("我和朋友最近关系有点紧张，怎么办？")

# 返回结果
{
    'response': '...',
    'mode': 'workflow_agent_hybrid',
    'agent_used': True,
    'execution_path': ['start', 'memory_load', 'intent_classify', 'agent_decision', 'memory_save', 'end'],
    'retrieval_stats': {...}
}
```

### 高级使用（集成MCP）

```python
from backend.agents.langchain_specialized_agents import create_langchain_agent
from backend.agents.mcp_integration import MCPHost, GithubMCPServer, DatabaseMCPServer
import asyncio

async def main():
    # 1. 创建MCP Host
    mcp_host = MCPHost(user_id='user_123')
    
    # 2. 注册MCP Servers
    mcp_host.register_server(GithubMCPServer(api_token='your_token'))
    mcp_host.register_server(DatabaseMCPServer())
    
    # 3. 创建Agent（传入MCP Host）
    agent = create_langchain_agent(
        agent_type='career',
        user_id='user_123',
        llm_service=llm_service,
        rag_system=rag_system,
        retrieval_system=retrieval_system,
        use_workflow=True,
        mcp_host=mcp_host  # 启用MCP
    )
    
    # 4. 初始化Agent（发现MCP工具）
    await agent.initialize()
    
    # 5. 处理消息（自动使用MCP工具）
    result = agent.process("帮我在Github搜索Python相关的仓库")
    
    # 6. 查看审计日志
    logs = mcp_host.get_audit_logs()
    for log in logs:
        print(f"{log.tool_name}: {log.success}")

asyncio.run(main())
```

### 并行调用MCP工具

```python
from backend.agents.mcp_integration import ParallelFunctionCaller

# 创建并行调用器
parallel_caller = ParallelFunctionCaller(mcp_host)

# 并行调用多个工具
tool_calls = [
    {"tool_name": "github_search_repos", "parameters": {"query": "react"}},
    {"tool_name": "github_search_repos", "parameters": {"query": "vue"}},
    {"tool_name": "db_query_users", "parameters": {"user_id": "user_123"}}
]

results = await parallel_caller.call_parallel(tool_calls)
```

### 自定义MCP Server

```python
from backend.agents.mcp_integration import MCPServer, MCPTool

class MyCustomServer(MCPServer):
    def __init__(self):
        super().__init__(
            server_id="my_server",
            name="My Custom Server",
            description="自定义工具服务器"
        )
    
    async def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="my_custom_tool",
                description="我的自定义工具",
                parameters={
                    "type": "object",
                    "properties": {
                        "input": {"type": "string"}
                    }
                },
                server_id=self.server_id,
                requires_approval=False
            )
        ]
    
    async def call_tool(self, tool_name: str, parameters: Dict) -> Any:
        if tool_name == "my_custom_tool":
            return {"result": f"处理了: {parameters['input']}"}
        raise ValueError(f"未知工具: {tool_name}")
    
    async def list_resources(self):
        return []
    
    async def list_prompts(self):
        return []
    
    async def read_resource(self, uri: str):
        return None

# 使用自定义Server
mcp_host.register_server(MyCustomServer())
```

### API接口

```bash
POST /api/agent-chat
Content-Type: application/json

{
  "token": "xxx",
  "agent_type": "relationship",
  "message": "我和朋友最近关系有点紧张，怎么办？",
  "conversation_id": "uuid" (可选),
  "conversation_title": "关系问题咨询" (可选)
}
```

响应：
```json
{
  "success": true,
  "response": "根据你的情况...",
  "retrieval_stats": {
    "intent": "寻求建议",
    "complexity": "medium"
  },
  "conversation_id": "uuid",
  "tasks_executed": 3,
  "tools_used": ["retrieve_memory", "analyze_social_network"]
}
```

## 优势

### 架构优势

1. **结构清晰**：Workflow + Agent + MCP三层架构，职责明确
2. **推理透明**：ReAct模式记录完整的思考和行动过程
3. **工具灵活**：MCP动态发现，运行时扩展能力
4. **记忆持久**：上下文窗口 + 外部记忆双层架构
5. **专业深度**：每个Agent有独特的分析框架和工具集
6. **框架成熟**：基于LangChain，社区支持好

### 性能优势

1. **智能路由**：简单任务走Workflow（快），复杂任务走Agent（准）
2. **并行调用**：多个工具同时执行，提高响应速度
3. **记忆压缩**：自动压缩上下文窗口，节省Token
4. **缓存优化**：Redis + 上下文窗口多层缓存

### 安全优势

1. **能力声明**：Server明确声明工具，防止越权
2. **授权控制**：敏感操作需要人工确认
3. **审计追踪**：所有调用都有日志，可追溯
4. **记忆隔离**：每个用户独立的记忆空间

### 扩展优势

1. **动态发现**：无需重新部署，运行时添加工具
2. **标准协议**：MCP是标准协议，可接入任何Server
3. **易于集成**：MCP Tool可转换为LangChain Tool
4. **模块化**：各模块独立，易于替换和升级

## 未来扩展

### 短期计划

1. **更多MCP Servers**：
   - 邮件服务（发送邮件、读取邮件）
   - 日历服务（创建事件、查询日程）
   - 文件服务（读写文件、搜索文档）
   - 天气服务（查询天气、预报）

2. **增强Workflow**：
   - 条件分支更复杂
   - 循环节点支持
   - 子工作流嵌套
   - 可视化编辑器

3. **优化记忆系统**：
   - 更智能的压缩策略
   - 记忆重要性自动评估
   - 知识图谱自动构建
   - 跨会话记忆共享

### 中期计划

1. **多Agent协作**：
   - Agent之间的通信协议
   - 任务分配和协调
   - 结果聚合和冲突解决
   - 协作工作流

2. **自主学习**：
   - 从用户反馈中学习
   - 工具使用模式优化
   - 个性化推荐
   - A/B测试框架

3. **可视化监控**：
   - ReAct步骤可视化
   - Workflow执行图
   - MCP调用链路追踪
   - 性能监控面板

### 长期计划

1. **Agent市场**：
   - 用户自定义Agent
   - Agent模板商店
   - 工具插件市场
   - 社区贡献

2. **多模态支持**：
   - 图像理解和生成
   - 语音输入输出
   - 视频分析
   - 文档解析

3. **企业级功能**：
   - 多租户隔离
   - 权限管理系统
   - SLA保证
   - 私有化部署

## 调试和监控

### 启用详细日志

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # 启用详细日志
    max_iterations=5,
    handle_parsing_errors=True
)
```

### 查看ReAct步骤

```python
result = agent.process("用户消息")
for step in result['react_steps']:
    print(f"{step['step_type']}: {step['content']}")
```

## 常见问题

### Q: 如何添加新的MCP Server？
A: 继承`MCPServer`基类并实现四个方法：
```python
class MyMCPServer(MCPServer):
    async def list_tools(self) -> List[MCPTool]:
        # 返回工具列表
    
    async def call_tool(self, tool_name, parameters):
        # 执行工具调用
    
    async def list_resources(self):
        # 返回资源列表
    
    async def list_prompts(self):
        # 返回提示词列表
```

### Q: MCP和LangChain Tool有什么区别？
A: 
- **MCP**：动态发现、跨系统、标准协议
- **LangChain Tool**：静态注册、单系统、框架特定
- **关系**：MCP Tool可以转换为LangChain Tool使用

### Q: 如何实现人工授权？
A: 设置授权回调函数：
```python
async def approval_callback(tool, parameters):
    # 发送通知给用户
    # 等待用户确认
    return user_approved

mcp_host.set_approval_callback(approval_callback)
```

### Q: 审计日志存在哪里？
A: 当前存在内存中，生产环境应该：
1. 存入数据库（MySQL）
2. 导出到文件
3. 发送到日志系统（ELK）
4. 定期归档

### Q: 并行调用有什么限制？
A: 
- 工具之间不能有依赖关系
- 需要考虑API限流
- 某个工具失败不影响其他工具
- 结果顺序与输入对应

### Q: 系统如何判断任务是简单还是复杂？
A: 使用LLM自动判断，基于以下标准：
- **simple**：问候、单一查询、无需推理
- **medium**：需要分析、检索历史、简单建议
- **complex**：深度推理、多维度、制定计划

判断结果会打印在日志中，可以观察和调整。

### Q: 判断错误怎么办？
A: 可以通过以下方式优化：
1. 调整`understand_intent`的提示词
2. 增加更多判断示例
3. 根据Agent类型定制判断标准
4. 手动指定`use_workflow=False`强制使用Agent

### Q: ReAct和四模块冲突吗？
A: 不冲突。四模块提供基础能力（LLM、记忆、工具），ReAct定义工作流程。

### Q: 为什么要用LangChain？
A: LangChain提供成熟的ReAct实现、工具系统、记忆管理，减少重复造轮子。

### Q: 如何添加新工具？
A: 在Agent的`_register_agent_tools()`方法中调用`tool_module.register_custom_tool()`。

### Q: 如何控制ReAct迭代次数？
A: 在创建AgentExecutor时设置`max_iterations`参数（Workflow模式默认3次，纯Agent模式5次）。

### Q: 工具调用失败怎么办？
A: AgentExecutor会自动处理错误（`handle_parsing_errors=True`），并尝试重新思考。

### Q: 上下文窗口满了怎么办？
A: 自动触发摘要压缩：
1. 监控Token使用率（阈值80%）
2. LLM总结旧对话为摘要
3. 保留最近3轮完整对话
4. 原始对话存入外部记忆

### Q: 如何避免重复犯错？
A: 失败时自动记录：
1. 保存失败原因到外部记忆
2. 标记错误上下文和参数
3. 下次遇到类似情况时检索
4. 提示Agent避免相同错误

### Q: 记忆检索速度慢怎么办？
A: 多层缓存策略：
1. Redis缓存热点数据（毫秒级）
2. 上下文窗口缓存当前会话（最快）
3. 向量检索使用FAISS（秒级）
4. 异步预加载用户偏好

### Q: 如何保护用户隐私？
A: 记忆隔离机制：
1. 每个用户独立的记忆空间
2. 向量索引按用户ID分区
3. 数据库行级权限控制
4. 敏感信息加密存储
