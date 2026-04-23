# 决策推演前端集成指南

## 概述

本文档说明如何在前端集成新的4阶段决策推演流程，包括：
1. WebSocket事件处理
2. Agent状态管理
3. UI组件使用
4. 流式推理显示

## 文件结构

```
web/src/
├── types/
│   └── decision-events.ts          # 事件类型定义
├── hooks/
│   └── useDecisionAgents.ts        # Agent状态管理Hook
├── components/decision/
│   ├── AgentCard.tsx               # Agent卡片组件
│   └── AgentCard.css               # Agent卡片样式
└── pages/
    └── DecisionSimulationPage.tsx  # 决策推演页面（需要更新）
```

## 使用步骤

### 1. 更新DecisionSimulationPage.tsx

在决策推演页面中使用新的Hook和组件：

```typescript
import { useDecisionAgents } from '../hooks/useDecisionAgents';
import { AgentCard } from '../components/decision/AgentCard';
import type { DecisionEvent } from '../types/decision-events';

export function DecisionSimulationPage() {
  const {
    agents,
    initializeAgents,
    handleEvent,
    getAgent,
    getAgentRoundProgress,
    reset,
  } = useDecisionAgents();

  // WebSocket连接
  useEffect(() => {
    if (!config.sessionId || !config.options?.length) return;

    const wsInstance = openDecisionSimulationSocket(
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
          // 处理事件
          handleEvent(event as DecisionEvent);
          
          // 初始化Agent列表
          if (event.type === 'personas_init') {
            const personas = (event.personas || []) as any[];
            initializeAgents(
              personas.map(p => ({
                id: p.id,
                name: p.name,
                rounds: 2, // 从persona_rounds配置获取
              }))
            );
          }
        },
        onError(message) {
          console.error('WebSocket错误:', message);
        },
      }
    );

    return () => {
      wsInstance();
      reset();
    };
  }, [config]);

  return (
    <div className="decision-simulation-page">
      <h1>{config.question}</h1>
      
      {/* Agent卡片网格 */}
      <div className="agents-grid">
        {agents.map(agent => (
          <AgentCard
            key={agent.id}
            agent={agent}
            roundProgress={getAgentRoundProgress(agent.id)}
            onExpand={(agentId, phase, round) => {
              console.log('展开阶段详情:', agentId, phase, round);
            }}
          />
        ))}
      </div>
    </div>
  );
}
```

### 2. 添加样式

在页面CSS中添加Agent网格布局：

```css
.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  padding: 20px;
}

@media (max-width: 768px) {
  .agents-grid {
    grid-template-columns: 1fr;
  }
}
```

### 3. 处理WebSocket事件

新的事件类型和处理方式：

```typescript
// 事件类型
type DecisionEvent = 
  | { type: 'agent_start'; persona_id: string; persona_name: string; rounds: number }
  | { type: 'round_start'; persona_id: string; round: number; total_rounds: number }
  | { type: 'phase_start'; persona_id: string; phase: PhaseType; phase_name: string; round: number }
  | { type: 'phase_complete'; persona_id: string; phase: PhaseType; round: number; result?: any; ... }
  | { type: 'reasoning_stream'; persona_id: string; chunk: string; accumulated: string }
  | { type: 'agent_complete'; persona_id: string; final_score: number; final_stance: string }
  | ...

// 事件处理
function handleWebSocketEvent(event: DecisionEvent) {
  switch (event.type) {
    case 'agent_start':
      console.log(`${event.persona_name} 开始推演，共${event.rounds}轮`);
      break;
      
    case 'round_start':
      console.log(`第${event.round}/${event.total_rounds}轮开始`);
      break;
      
    case 'phase_start':
      console.log(`进入${event.phase_name}阶段`);
      break;
      
    case 'phase_complete':
      if (event.phase === 'independent_thinking') {
        console.log('独立思考完成:', event.result);
      } else if (event.phase === 'observe_others') {
        console.log('观察到', event.observed_count, '个其他Agent');
      } else if (event.phase === 'deep_reflection') {
        console.log('深度反思完成:', event.result);
        if (event.result.stance_changed) {
          console.log('⚠️ 立场已改变');
        }
      } else if (event.phase === 'decision') {
        console.log('决策完成:', event.decision);
      }
      break;
      
    case 'reasoning_stream':
      // 流式推理，实时更新UI
      console.log('推理片段:', event.chunk);
      break;
      
    case 'agent_complete':
      console.log(`${event.persona_name} 完成推演`);
      console.log('最终结果:', event.final_stance, event.final_score);
      break;
  }
}
```

## 4阶段流程说明

### 阶段1: 独立思考 (Independent Thinking)

```typescript
// 阶段开始
{
  type: 'phase_start',
  phase: 'independent_thinking',
  phase_name: '独立思考',
  round: 1
}

// 可能的技能执行
{
  type: 'skill_selection',
  selected_skills: ['rag_retrieval', 'kg_query'],
  reason: '需要检索相关知识'
}

{
  type: 'skill_start',
  skill_name: 'rag_retrieval'
}

{
  type: 'skill_complete',
  skill_name: 'rag_retrieval',
  summary: '检索到5条相关记忆'
}

// 流式推理（可选）
{
  type: 'reasoning_stream',
  chunk: '从职业发展角度来看...',
  accumulated: '从职业发展角度来看...'
}

// 阶段完成
{
  type: 'phase_complete',
  phase: 'independent_thinking',
  result: {
    stance: '支持',
    score: 75,
    reasoning: '详细的推理过程...',
    key_points: ['薪资提升显著', '职业发展机会']
  }
}
```

### 阶段2: 查看他人观点 (Observe Others)

```typescript
// 阶段开始
{
  type: 'phase_start',
  phase: 'observe_others',
  phase_name: '查看他人观点',
  round: 1
}

// 阶段完成
{
  type: 'phase_complete',
  phase: 'observe_others',
  observed_count: 6,
  observed_personas: [
    { id: 'adventurer', name: '冒险家', stance: '强烈支持', score: 90 },
    { id: 'conservative', name: '保守派', stance: '反对', score: 40 },
    ...
  ]
}
```

### 阶段3: 深度反思 (Deep Reflection)

```typescript
// 阶段开始
{
  type: 'phase_start',
  phase: 'deep_reflection',
  phase_name: '深度反思',
  round: 1
}

// 可能的补充技能执行
{
  type: 'skill_selection',
  selected_skills: ['verify_claim'],
  reason: '需要验证其他Agent提出的观点'
}

// 流式推理（可选）
{
  type: 'reasoning_stream',
  chunk: '考虑到其他Agent的观点...',
  accumulated: '考虑到其他Agent的观点...'
}

// 阶段完成
{
  type: 'phase_complete',
  phase: 'deep_reflection',
  result: {
    stance: '支持',
    score: 72,
    reasoning: '深度反思的过程...',
    key_points: ['综合考虑各方观点', '调整了评分'],
    stance_changed: false
  }
}
```

### 阶段4: 决策 (Decision)

```typescript
// 阶段开始
{
  type: 'phase_start',
  phase: 'decision',
  phase_name: '决策',
  round: 1
}

// 阶段完成
{
  type: 'phase_complete',
  phase: 'decision',
  decision: {
    stance: '支持',
    score: 72,
    confidence: 0.85,
    reasoning: '综合独立思考和深度反思...',
    key_points: ['薪资提升', '职业发展', '需要权衡家庭'],
    round: 1,
    thinking_summary: '从职业发展角度来看...',
    reflection_summary: '考虑到其他Agent的观点...'
  }
}
```

## 流式推理实现

### 后端实现（未来）

在 `backend/decision/decision_personas.py` 中添加流式分析方法（参考 `STREAMING_REASONING_EXAMPLE.md`）。

### 前端处理

```typescript
// 在useDecisionAgents Hook中已经处理了reasoning_stream事件
// Agent状态会自动更新streamingReasoning字段

// 在AgentCard组件中显示
{agent.streamingReasoning && (
  <div className="agent-card__streaming">
    <div className="agent-card__streaming-text">
      {agent.streamingReasoning}
      <span className="agent-card__cursor">|</span>
    </div>
  </div>
)}
```

## 配置Agent轮数

```typescript
// 在WebSocket连接时配置每个Agent的轮数
openDecisionSimulationSocket(
  {
    ...
    persona_rounds: {
      rational_analyst: 3,    // 理性分析师执行3轮
      adventurer: 2,          // 冒险家执行2轮
      pragmatist: 2,
      idealist: 2,
      conservative: 2,
      social_navigator: 2,
      innovator: 2,
    },
  },
  ...
);
```

## 完整示例

查看 `web/src/pages/DecisionSimulationPage.tsx` 中的完整实现示例。

## 测试

1. 启动后端服务
2. 启动前端开发服务器
3. 进入决策推演页面
4. 观察Agent卡片的4阶段进度
5. 点击阶段查看详细内容

## 注意事项

1. 确保WebSocket连接正常
2. 处理所有事件类型，避免遗漏
3. 流式推理需要后端支持（当前为预留接口）
4. Agent卡片会自动更新，无需手动刷新
5. 支持多轮推演，每轮都包含完整的4个阶段

## 下一步

1. 实现流式推理后端支持
2. 添加更多交互功能（暂停/继续、查看历史等）
3. 优化UI动画和过渡效果
4. 添加数据导出功能
