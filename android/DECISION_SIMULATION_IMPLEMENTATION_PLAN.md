# Android 决策推演功能实现计划

## 概述
参考 Web 端 `DecisionSimulationPage.tsx` 实现 Android 端的7人格 Agent 异步推演功能。

## 核心功能

### 1. WebSocket 实时通信
- 建立 WebSocket 连接到推演引擎
- 接收实时推演事件（Agent 思考、交互、评分等）
- 支持暂停/继续推演
- 支持多选项并行推演

### 2. Agent 可视化
- 7个人格 Agent 的实时状态显示
- Agent 思考过程动画
- Agent 之间的交互可视化
- 实时评分更新

### 3. 推演阶段
- **连接阶段**：建立 WebSocket 连接
- **运行阶段**：Agent 分析、交互、评分
- **完成阶段**：显示最终结果

## 实现步骤

### 阶段 1：WebSocket 客户端 ✓
- [ ] 创建 `DecisionWebSocketClient.kt`
- [ ] 实现事件解析和分发
- [ ] 处理连接状态管理

### 阶段 2：数据模型
- [ ] 扩展 `PersonaModels.kt` 添加推演相关模型
- [ ] 创建 Agent 状态模型
- [ ] 创建交互事件模型

### 阶段 3：ViewModel
- [ ] 创建 `DecisionSimulationViewModel.kt`
- [ ] 管理 WebSocket 连接
- [ ] 处理实时事件更新
- [ ] 管理 Agent 状态

### 阶段 4：UI 组件
- [ ] 创建 `DecisionSimulationScreen.kt`
- [ ] 实现 Agent 卡片组件
- [ ] 实现交互时间线组件
- [ ] 实现评分显示组件

### 阶段 5：导航集成
- [ ] 更新 `AppNavigation.kt`
- [ ] 从选项确认页面导航到推演页面
- [ ] 传递必要的参数（sessionId, options等）

## 技术要点

### WebSocket 事件类型
```kotlin
sealed class SimulationEvent {
    data class Status(val message: String) : SimulationEvent()
    data class OptionStart(val optionId: String, val title: String) : SimulationEvent()
    data class AgentsStart(val agents: List<Agent>, val month: Int) : SimulationEvent()
    data class AgentThinking(val agentId: String, val message: String) : SimulationEvent()
    data class PersonaAnalysis(val personaId: String, val score: Double, val stance: String) : SimulationEvent()
    data class PersonaInteraction(val from: String, val to: String, val message: String) : SimulationEvent()
    data class FinalEvaluation(val score: Double, val riskLevel: String) : SimulationEvent()
    data class Complete(val optionId: String) : SimulationEvent()
    data class Error(val message: String) : SimulationEvent()
}
```

### Agent 状态
```kotlin
data class AgentState(
    val id: String,
    val name: String,
    val status: AgentStatus,  // waiting, thinking, complete
    val score: Double? = null,
    val stance: String? = null,
    val currentMessage: String? = null,
    val thinkingHistory: List<ThinkingRecord> = emptyList()
)

enum class AgentStatus {
    WAITING, THINKING, COMPLETE, ERROR
}
```

## 参考文件
- Web: `web/src/pages/DecisionSimulationPage.tsx`
- Web: `web/src/components/decision/PersonaInteractionView.tsx`
- Web: `web/src/services/decision.ts`
- Android: `android/app/src/main/java/com/lifeswarm/android/presentation/decision/EnhancedDecisionSimulationViewModel.kt`
