# 推演界面修复总结

## 问题诊断

通过日志分析发现了根本原因：

### 问题1: 消息类型不匹配
**现象**: 后端发送 `personas_init` 消息，但前端只处理 `agents_start` 和 `personas_start`

**日志证据**:
```
[WebSocket-option_1] 收到消息: personas_init
[WebSocket-option_1] 未知消息类型: personas_init
```

**后端发送的消息**:
```json
{
  "type": "personas_init",
  "option_id": "option_1",
  "personas": [
    {"id": "rational_analyst", "name": "理性分析师", ...},
    {"id": "adventurer", "name": "冒险家", ...},
    ...
  ]
}
```

### 问题2: 字段名不一致
后端使用 `personas` 字段，前端期望 `agents` 或 `personas`（已兼容）

## 修复方案

### 修复1: 添加 `personas_init` 消息类型支持

在 `handleWebSocketMessage` 方法中添加对 `personas_init` 的处理：

```kotlin
when (eventType) {
    "agents_start", "personas_start", "personas_init" -> {
        handleAgentsStart(optionId, json)
    }
    // ...
}
```

### 修复2: 添加 `start` 和 `thinking` 消息类型支持

后端还发送了 `start` 和 `thinking` 消息类型，也需要处理：

```kotlin
when (eventType) {
    "start", "option_start" -> handleOptionStart(optionId, json)
    "agent_thinking", "thinking" -> handleAgentThinking(optionId, json)
    // ...
}
```

### 修复3: 添加 `shared_facts` 消息类型

后端发送 `shared_facts` 消息，虽然不需要特殊处理，但应该避免警告日志：

```kotlin
"shared_facts" -> {
    Log.d(TAG, "[消息处理-$optionId] 收到 shared_facts 消息")
}
```

### 修复4: 增强字段名兼容性

在 `handleAgentsStart` 中添加更多字段名的兼容：

```kotlin
val agentsArray = json.optJSONArray("agents") 
    ?: json.optJSONArray("personas")
    ?: json.optJSONArray("persona_list")

val agent = PersonaAgent(
    id = agentJson.optString("id", agentJson.optString("persona_id", "")),
    name = agentJson.optString("name", agentJson.optString("persona_name", "")),
    status = PersonaStatus.WAITING
)
```

## 预期效果

修复后，当收到 `personas_init` 消息时：

1. ✅ 消息被正确识别和处理
2. ✅ 7个 personas 被解析并添加到 agents 列表
3. ✅ UI 状态更新，`activeOptionState.agents` 不再为空
4. ✅ 界面显示圆形布局的 Agent 球体，而不是"等待 Agent 启动..."

## 验证步骤

重新运行应用后，查看日志应该看到：

```
[消息处理-option_1] 收到 agents/personas 初始化消息
[handleAgentsStart-option_1] 添加 Agent: 理性分析师 (rational_analyst)
[handleAgentsStart-option_1] 添加 Agent: 冒险家 (adventurer)
...
[handleAgentsStart-option_1] 总共添加了 7 个 Agents
[updateOptionState-option_1] 更新状态: agents=7, score=0.0, complete=false
[handleAgentsStart-option_1] 验证: UI状态中的 agents 数量: 7
```

然后界面应该显示7个 Agent 球体围绕中心选项卡片排列。

## 其他发现

从日志中还发现后端的消息流程：

1. `start` - 推演开始
2. `status` - 状态更新（多次）
3. `personas_init` - 初始化7个人格
4. `shared_facts` - 共享事实
5. `agent_thinking` - Agent 思考过程（多次）
6. 后续还会有 `persona_analysis`、`persona_interaction`、`final_evaluation` 等

所有这些消息类型都已在代码中正确处理。
