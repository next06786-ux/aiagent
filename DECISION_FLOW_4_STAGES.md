# 决策流程 - 4阶段模式

## 概述

决策模拟现在采用完整的4阶段流程，每个persona在每一轮中都会经历：

1. **独立思考** - 可执行技能，流式输出推理
2. **查看他人观点** - 从共享存储读取其他persona的观点
3. **深度反思** - 基于他人观点反思，可执行技能，流式输出
4. **决策** - 做出当前轮次的决策

## 流程图

```
每一轮 (Round N)
│
├─ 阶段1: 独立思考 (Independent Thinking)
│  ├─ 智能选择技能
│  ├─ 执行技能
│  ├─ 基于技能结果分析
│  └─ 流式输出推理过程
│
├─ 阶段2: 查看他人观点 (Observe Others)
│  ├─ 从shared_views读取其他persona的观点
│  └─ 展示其他persona的立场和评分
│
├─ 阶段3: 深度反思 (Deep Reflection)
│  ├─ 基于他人观点进行反思
│  ├─ 智能选择补充技能（如果需要）
│  ├─ 执行补充技能
│  ├─ 调整立场
│  └─ 流式输出反思过程
│
└─ 阶段4: 决策 (Decision)
   ├─ 综合独立思考和深度反思
   ├─ 输出最终立场、评分、信心度
   └─ 写入shared_views供其他persona查看
```

## WebSocket事件流

### 1. Agent生命周期事件

```typescript
// Agent开始
{
  type: 'agent_start',
  persona_id: string,
  persona_name: string,
  rounds: number,
  timestamp: number
}

// Agent完成
{
  type: 'agent_complete',
  persona_id: string,
  persona_name: string,
  total_rounds: number,
  total_duration: number,
  final_score: number,
  final_stance: string,
  final_confidence: number,
  timestamp: number
}
```

### 2. 轮次事件

```typescript
// 轮次开始
{
  type: 'round_start',
  persona_id: string,
  persona_name: string,
  round: number,
  total_rounds: number,
  timestamp: number
}

// 轮次完成
{
  type: 'round_complete',
  persona_id: string,
  persona_name: string,
  round: number,
  duration: number,
  timestamp: number
}
```

### 3. 阶段事件

```typescript
// 阶段开始
{
  type: 'phase_start',
  persona_id: string,
  persona_name: string,
  phase: 'independent_thinking' | 'observe_others' | 'deep_reflection' | 'decision',
  phase_name: string,  // 中文名称
  round: number,
  timestamp: number
}

// 阶段完成
{
  type: 'phase_complete',
  persona_id: string,
  persona_name: string,
  phase: string,
  round: number,
  duration?: number,
  timestamp: number,
  
  // 根据不同阶段，包含不同的结果
  result?: {  // independent_thinking 或 deep_reflection
    stance: string,
    score: number,
    reasoning: string,
    key_points: string[],
    stance_changed?: boolean  // 仅 deep_reflection
  },
  
  observed_count?: number,  // observe_others
  observed_personas?: Array<{
    id: string,
    name: string,
    stance: string,
    score: number
  }>,
  
  decision?: {  // decision
    stance: string,
    score: number,
    confidence: number,
    reasoning: string,
    key_points: string[],
    round: number,
    thinking_summary: string,
    reflection_summary: string
  }
}
```

### 4. 流式推理事件（未来支持）

```typescript
// 推理流式输出
{
  type: 'reasoning_stream',
  persona_id: string,
  persona_name: string,
  phase: 'independent_thinking' | 'deep_reflection',
  chunk: string,  // 文本片段
  accumulated: string,  // 累积文本
  timestamp: number
}
```

## 前端展示建议

### 1. 整体布局

```
┌─────────────────────────────────────────────────────────┐
│  决策问题: 是否应该接受新的工作机会？                      │
│  选项: 接受新工作                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  [理性分析师] 第2/3轮                                     │
│  ├─ ✅ 独立思考: 支持 (75分)                              │
│  ├─ ✅ 查看他人: 观察到6个观点                             │
│  ├─ 🔄 深度反思中...                                      │
│  └─ ⏳ 决策                                               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  [冒险家] 第2/3轮                                         │
│  ├─ ✅ 独立思考: 强烈支持 (90分)                          │
│  ├─ ✅ 查看他人: 观察到6个观点                             │
│  ├─ ✅ 深度反思: 强烈支持 (88分) ⚠️ 立场微调               │
│  └─ ✅ 决策: 强烈支持 (88分, 信心0.85)                    │
└─────────────────────────────────────────────────────────┘
```

### 2. 阶段指示器

每个persona卡片显示4个阶段的进度：

```
🧠 独立思考  →  👀 查看他人  →  🤔 深度反思  →  ⚖️ 决策
✅            ✅            🔄            ⏳
```

### 3. 推理内容展示

点击阶段可以展开查看详细推理：

```
┌─────────────────────────────────────────────────────────┐
│  🧠 独立思考 (第2轮)                                      │
│  ─────────────────────────────────────────────────────  │
│  立场: 支持                                               │
│  评分: 75/100                                            │
│  信心: 0.80                                              │
│                                                          │
│  推理过程:                                                │
│  从职业发展角度来看，这个机会提供了30%的薪资提升...       │
│  [展开完整推理]                                           │
│                                                          │
│  关键要点:                                                │
│  • 薪资提升显著                                           │
│  • 职业发展机会                                           │
│  • 需要权衡家庭因素                                       │
└─────────────────────────────────────────────────────────┘
```

### 4. 观察他人阶段

```
┌─────────────────────────────────────────────────────────┐
│  👀 查看他人观点 (第2轮)                                  │
│  ─────────────────────────────────────────────────────  │
│  观察到6个其他Agent的观点:                                │
│                                                          │
│  [冒险家] 强烈支持 (90分)                                 │
│  [实用主义者] 支持 (70分)                                 │
│  [理想主义者] 中立 (55分)                                 │
│  [保守派] 反对 (40分)                                     │
│  [社交导航者] 支持 (65分)                                 │
│  [创新者] 强烈支持 (85分)                                 │
└─────────────────────────────────────────────────────────┘
```

## 后端实现要点

### 1. 完整的4阶段流程

```python
for round_num in range(1, rounds + 1):
    # 阶段1: 独立思考
    thinking_result = await persona._phase_independent_thinking(option, context)
    
    # 阶段2: 查看他人观点
    other_views = await get_other_views(shared_views, persona_id)
    
    # 阶段3: 深度反思
    reflection_result = await persona._phase_deep_reflection(
        option, context, other_views, thinking_result
    )
    
    # 阶段4: 决策
    decision_result = make_decision(thinking_result, reflection_result)
    
    # 写入共享存储
    shared_views[persona_id] = decision_result
```

### 2. 技能执行时机

- **独立思考阶段**: 可以执行技能获取信息
- **深度反思阶段**: 可以执行补充技能验证观点

### 3. 流式输出（未来）

```python
async def _analyze_with_streaming(self, ...):
    async for chunk in llm.chat_stream_async(...):
        # 实时推送到前端
        await status_callback('reasoning_stream', {
            'persona_id': self.persona_id,
            'chunk': chunk
        })
```

## 测试

运行测试脚本验证流程：

```bash
cd backend
python test_decision_flow.py
```

测试会验证：
- 每个Agent执行完整的4阶段流程
- 事件推送的完整性
- 轮次和阶段的正确顺序
- 最终决策结果

## 迁移指南

### 前端需要修改的地方

1. **事件处理器**: 添加新的phase_start和phase_complete事件处理
2. **UI组件**: 显示4个阶段的进度
3. **推理展示**: 区分独立思考和深度反思的内容
4. **观察阶段**: 显示其他persona的观点列表

### 后端已完成的修改

- ✅ `_run_persona_with_sharing` 方法重构为4阶段流程
- ✅ 新增phase_start和phase_complete事件
- ✅ 每个阶段独立推送结果
- ✅ 决策阶段综合两次分析结果

## 下一步

1. 前端适配新的事件流
2. 实现流式推理输出
3. 优化阶段切换动画
4. 添加阶段详情展开/折叠
