# 4阶段决策流程 - 快速开始

## 🚀 快速开始

### 1. 测试后端流程

```bash
# 从项目根目录运行（推荐）
python -m backend.test_decision_flow

# 或者设置PYTHONPATH后运行
export PYTHONPATH=$PYTHONPATH:$(pwd)  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%cd%      # Windows CMD
$env:PYTHONPATH += ";$(Get-Location)" # Windows PowerShell

cd backend
python test_decision_flow.py
```

这将运行一个完整的测试，验证4阶段流程是否正常工作。

**预期输出：**
```
============================================================
测试决策流程 - 4阶段模式
============================================================

创建决策委员会...
初始化记忆系统...
开始分析决策...
问题: 是否应该接受新的工作机会？
选项: 接受新工作
轮数配置: 每个Agent执行2轮

🔄 [理性分析师] 开始第1/2轮
  📍 阶段: 独立思考
  ✅ 独立思考完成: 支持 (得分: 75)
  📍 阶段: 查看他人观点
  ✅ 观察到6个其他Agent的观点
  📍 阶段: 深度反思
  ✅ 深度反思完成: 支持 (得分: 72)
  ⚖️  决策: 支持 (得分: 72, 信心: 0.85)
  ⏱️  第1轮完成 (耗时: 5.23s)

🔄 [理性分析师] 开始第2/2轮
  ...
```

### 2. 查看测试结果

```bash
# 查看生成的事件日志
cat decision_flow_test_*.json
```

你会看到完整的事件流，包括：
- 每个Agent的生命周期事件
- 每一轮的4个阶段
- 每个阶段的详细结果

### 3. 前端集成

#### 步骤1: 导入新的Hook和组件

```typescript
// 在 DecisionSimulationPage.tsx 中
import { useDecisionAgents } from '../hooks/useDecisionAgents';
import { AgentCard } from '../components/decision/AgentCard';
import type { DecisionEvent } from '../types/decision-events';
```

#### 步骤2: 使用Hook管理状态

```typescript
const {
  agents,
  initializeAgents,
  handleEvent,
  getAgentRoundProgress,
  reset,
} = useDecisionAgents();
```

#### 步骤3: 处理WebSocket事件

```typescript
openDecisionSimulationSocket(
  {
    session_id: config.sessionId,
    user_id: config.userId,
    question: config.question,
    option: config.options[0],
    option_index: 0,
    collected_info: config.collectedInfo,
    decision_type: config.decisionType || 'general',
    persona_rounds: {
      rational_analyst: 2,
      adventurer: 2,
      pragmatist: 2,
      idealist: 2,
      conservative: 2,
      social_navigator: 2,
      innovator: 2,
    },
  },
  {
    onEvent(event) {
      // 自动处理所有事件
      handleEvent(event as DecisionEvent);
      
      // 初始化Agent列表
      if (event.type === 'personas_init') {
        const personas = (event.personas || []) as any[];
        initializeAgents(
          personas.map(p => ({
            id: p.id,
            name: p.name,
            rounds: 2,
          }))
        );
      }
    },
    onError(message) {
      console.error('WebSocket错误:', message);
    },
  }
);
```

#### 步骤4: 渲染Agent卡片

```typescript
<div className="agents-grid">
  {agents.map(agent => (
    <AgentCard
      key={agent.id}
      agent={agent}
      roundProgress={getAgentRoundProgress(agent.id)}
    />
  ))}
</div>
```

#### 步骤5: 添加样式

```css
.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  padding: 20px;
}
```

## 📊 查看效果

启动前端后，你会看到：

1. **7个Agent卡片**，每个显示：
   - Agent名称和当前轮次
   - 4个阶段的进度（🧠 → 👀 → 🤔 → ⚖️）
   - 当前状态和消息
   - 流式推理（如果启用）
   - 当前决策结果

2. **实时更新**：
   - 阶段图标会随着进度变化（⏳ → 🔄 → ✅）
   - 卡片会有脉冲动画表示正在思考
   - 流式推理会像打字机一样显示

3. **交互功能**：
   - 点击阶段可以查看详细内容
   - 展开后可以看到推理过程、关键要点等

## 🎯 核心概念

### 4个阶段

1. **独立思考** 🧠
   - Agent独立分析选项
   - 可以执行技能（RAG检索、知识图谱查询等）
   - 输出初步立场和评分

2. **查看他人观点** 👀
   - 从共享存储读取其他Agent的观点
   - 了解其他Agent的立场和理由

3. **深度反思** 🤔
   - 基于他人观点进行反思
   - 可以执行补充技能验证观点
   - 调整自己的立场和评分

4. **决策** ⚖️
   - 综合独立思考和深度反思
   - 做出最终决策
   - 输出立场、评分、信心度

### 多轮执行

每个Agent可以执行N轮（默认2轮），每轮都包含完整的4个阶段：

```
轮次1: 🧠 → 👀 → 🤔 → ⚖️
轮次2: 🧠 → 👀 → 🤔 → ⚖️
...
轮次N: 🧠 → 👀 → 🤔 → ⚖️
```

### 技能执行

Agent可以在以下阶段执行技能：
- **独立思考阶段**：获取信息（RAG检索、知识图谱查询等）
- **深度反思阶段**：验证观点（补充检索、计算等）

## 🔧 配置选项

### 调整Agent轮数

```typescript
persona_rounds: {
  rational_analyst: 3,    // 理性分析师执行3轮
  adventurer: 1,          // 冒险家执行1轮
  pragmatist: 2,
  idealist: 2,
  conservative: 2,
  social_navigator: 2,
  innovator: 2,
}
```

### 决策类型

```typescript
decision_type: 'career'        // 职业决策
decision_type: 'relationship'  // 人际关系决策
decision_type: 'education'     // 教育升学决策
decision_type: 'general'       // 通用决策
```

## 📝 事件监听

如果你想自定义事件处理：

```typescript
onEvent(event) {
  // 先让Hook处理
  handleEvent(event as DecisionEvent);
  
  // 然后添加自定义逻辑
  if (event.type === 'phase_complete') {
    if (event.phase === 'decision') {
      console.log('Agent做出决策:', event.decision);
      // 可以在这里添加自定义逻辑
    }
  }
  
  if (event.type === 'reasoning_stream') {
    console.log('流式推理:', event.chunk);
    // 可以在这里添加自定义显示逻辑
  }
}
```

## 🐛 调试技巧

### 1. 查看WebSocket消息

```typescript
onEvent(event) {
  console.log('[WebSocket]', event.type, event);
  handleEvent(event as DecisionEvent);
}
```

### 2. 查看Agent状态

```typescript
useEffect(() => {
  console.log('当前Agent状态:', agents);
}, [agents]);
```

### 3. 查看轮次进度

```typescript
agents.forEach(agent => {
  const progress = getAgentRoundProgress(agent.id);
  console.log(`${agent.name} 进度:`, progress);
});
```

## 📚 完整文档

- **后端实现**: `DECISION_FLOW_4_STAGES.md`
- **前端集成**: `web/DECISION_FRONTEND_INTEGRATION.md`
- **流式推理**: `backend/decision/STREAMING_REASONING_EXAMPLE.md`
- **完整总结**: `FRONTEND_BACKEND_INTEGRATION_COMPLETE.md`

## ✅ 检查清单

- [ ] 后端测试通过 (`python test_decision_flow.py`)
- [ ] 前端导入新的Hook和组件
- [ ] WebSocket事件处理正确
- [ ] Agent卡片正常显示
- [ ] 4阶段进度正确更新
- [ ] 点击阶段可以查看详情
- [ ] 流式推理显示正常（如果启用）

## 🎉 完成！

现在你已经成功集成了4阶段决策流程！每个Agent都会经历完整的推演过程，前端会实时显示所有进度和结果。
