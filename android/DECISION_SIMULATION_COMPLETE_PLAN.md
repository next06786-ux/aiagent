# 安卓端决策推演完整实现计划

## 目标
实现与 Web 端完全一致的决策推演功能，包括信息采集、选项确认、7人格Agent异步推演。

## 当前状态分析

### 已完成 ✅
1. **信息采集流程** (`DecisionCollectionScreen.kt` + `DecisionCollectionViewModel.kt`)
   - WebSocket 实时对话
   - 多轮信息采集
   - 手动结束采集功能
   - 生成决策选项

2. **选项确认页面** (`DecisionOptionsScreen.kt`)
   - 显示 AI 生成的选项
   - 可展开/收起选项详情
   - 添加/删除自定义选项
   - 显示采集信息摘要

3. **推演页面基础** (`EnhancedSimulationScreen.kt` + `EnhancedDecisionSimulationViewModel.kt`)
   - WebSocket 连接管理
   - 7个Agent圆形布局
   - 实时状态更新
   - 缩放和拖拽控制
   - 思考历史对话框

4. **数据模型** (`PersonaModels.kt`, `DecisionModels.kt`)
   - PersonaAgent
   - ThinkingRecord
   - PersonaInteraction
   - OptionSimulationState

### 需要完善 🔧

1. **推演流程控制**
   - ✅ 单选项推演（已实现）
   - ❌ 多选项并行推演（Web端支持）
   - ❌ 选项切换功能
   - ❌ 暂停/继续推演

2. **可视化效果**
   - ✅ Agent圆形布局
   - ✅ 状态指示器
   - ✅ 消息气泡
   - ❌ Agent交互连线（虚线动画）
   - ❌ 评分影响动画（从Agent到中心的线条）
   - ❌ 立场变化特效（黄色警告）

3. **推演结果**
   - ❌ 推演完成后的结果页面
   - ❌ 综合评估展示
   - ❌ 风险等级显示
   - ❌ 执行信心度
   - ❌ 推荐建议

4. **历史记录**
   - ❌ 决策历史列表
   - ❌ 历史详情查看
   - ❌ 重新查看推演过程

## 实现步骤

### 第一阶段：完善推演流程（优先级：高）

#### 1.1 多选项并行推演
- 修改 `EnhancedDecisionSimulationViewModel` 支持多个选项
- 为每个选项建立独立的 WebSocket 连接
- 实现选项切换 UI（Tab 或底部导航）
- 实现暂停/继续控制

#### 1.2 推演状态管理
- 完善 WebSocket 事件处理
- 添加推演进度跟踪
- 实现错误恢复机制

### 第二阶段：增强可视化效果（优先级：中）

#### 2.1 Agent交互可视化
- 绘制Agent之间的交互连线
- 实现虚线动画效果
- 显示交互类型（质疑、支持、补充）

#### 2.2 评分动画
- 实现评分更新时的动画效果
- 从Agent到中心选项卡的连线
- 分数变化的数字动画

#### 2.3 立场变化特效
- 检测立场变化
- 显示黄色警告动画
- 记录立场变化历史

### 第三阶段：推演结果页面（优先级：高）

#### 3.1 创建结果页面
- `DecisionResultScreen.kt`
- 显示最终评分
- 显示风险等级
- 显示执行信心度
- 显示推荐建议

#### 3.2 结果可视化
- 雷达图（各维度评分）
- 对比图表（多选项对比）
- 关键论点总结

### 第四阶段：历史记录功能（优先级：中）

#### 4.1 历史列表
- `DecisionHistoryScreen.kt`
- 显示历史决策列表
- 按时间排序
- 搜索和筛选

#### 4.2 历史详情
- 查看历史推演结果
- 重新播放推演过程
- 导出决策报告

## Web 端功能对照表

| 功能 | Web 端 | Android 端 | 状态 |
|------|--------|-----------|------|
| 信息采集 | ✅ | ✅ | 完成 |
| 流式响应 | ✅ | ✅ | 完成 |
| 选项确认 | ✅ | ✅ | 完成 |
| 单选项推演 | ✅ | ✅ | 完成 |
| 多选项并行 | ✅ | ❌ | 待实现 |
| 选项切换 | ✅ | ❌ | 待实现 |
| 暂停/继续 | ✅ | ❌ | 待实现 |
| Agent圆形布局 | ✅ | ✅ | 完成 |
| 交互连线 | ✅ | ❌ | 待实现 |
| 评分动画 | ✅ | ❌ | 待实现 |
| 立场变化特效 | ✅ | ❌ | 待实现 |
| 思考历史 | ✅ | ✅ | 完成 |
| 推演结果页 | ✅ | ❌ | 待实现 |
| 历史记录 | ✅ | ❌ | 待实现 |

## 技术要点

### WebSocket 管理
```kotlin
// 为每个选项建立独立连接
private val webSocketInstances = mutableMapOf<String, WebSocket>()

// 连接管理
fun connectOption(optionId: String) {
    val ws = createWebSocket(optionId)
    webSocketInstances[optionId] = ws
}

// 暂停/继续
fun pauseOption(optionId: String) {
    webSocketInstances[optionId]?.send("""{"action":"pause"}""")
}
```

### 状态同步
```kotlin
// 每个选项独立的状态
data class OptionSimulationState(
    val optionId: String,
    val agents: List<PersonaAgent>,
    val interactions: List<PersonaInteraction>,
    val totalScore: Double,
    val isComplete: Boolean,
    val isPaused: Boolean
)

// 全局状态
data class SimulationUiState(
    val activeOptionId: String,
    val optionStates: Map<String, OptionSimulationState>,
    val completedOptions: Set<String>
)
```

### Canvas 绘制
```kotlin
// 绘制交互连线
Canvas(modifier = Modifier.fillMaxSize()) {
    interactions.forEach { interaction ->
        val fromPos = getAgentPosition(interaction.from)
        val toPos = getAgentPosition(interaction.to)
        
        drawLine(
            color = Color.White.copy(alpha = 0.3f),
            start = fromPos,
            end = toPos,
            strokeWidth = 2.dp.toPx(),
            pathEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 10f))
        )
    }
}
```

## 下一步行动

1. **立即开始**：完善推演流程控制
2. **本周完成**：推演结果页面
3. **下周完成**：历史记录功能
4. **持续优化**：可视化效果和动画

## 注意事项

1. 保持与 Web 端 API 的一致性
2. 确保 WebSocket 连接的稳定性
3. 优化内存使用（多个 WebSocket 连接）
4. 处理网络异常和重连
5. 保存推演状态以支持恢复
