# 增强版推演功能集成指南

## 已完成的新功能

### 1. 多选项并行推演 ✅
**文件**: `EnhancedDecisionSimulationViewModel.kt`

**功能**:
- 每个选项独立的 WebSocket 连接
- 支持暂停/继续控制
- 选项状态独立管理

**关键方法**:
```kotlin
// 切换到指定选项
fun switchToOption(optionId: String)

// 暂停选项
fun pauseOption(optionId: String)

// 继续选项
fun resumeOption(optionId: String)
```

### 2. 选项切换 UI ✅
**文件**: `OptionTabsBar.kt`

**两种样式**:
1. **ScrollableTabRow** - 顶部标签栏样式
2. **NavigationBar** - 底部导航栏样式

**使用方法**:
```kotlin
// 顶部标签栏
OptionTabsBar(
    optionStates = uiState.optionStates,
    activeOptionId = uiState.activeOptionId,
    onSelectOption = { viewModel.switchToOption(it) },
    onPauseOption = { viewModel.pauseOption(it) },
    onResumeOption = { viewModel.resumeOption(it) }
)

// 底部导航栏
OptionBottomBar(
    optionStates = uiState.optionStates,
    activeOptionId = uiState.activeOptionId,
    onSelectOption = { viewModel.switchToOption(it) }
)
```

### 3. 可视化增强动画 ✅
**文件**: `SimulationAnimations.kt`

**包含动画**:
1. **InteractionLines** - Agent 交互连线（虚线动画）
2. **ScoreImpactAnimation** - 评分影响动画（从 Agent 到中心的金色线条）
3. **StanceChangeEffect** - 立场变化特效（黄色警告圆圈）
4. **CompletionCelebration** - 完成庆祝动画（旋转星星）
5. **ThinkingRipple** - 思考波纹动画

**使用方法**:
```kotlin
Box(modifier = Modifier.fillMaxSize()) {
    // 主要内容
    CircularAgentsView(...)
    
    // 交互连线
    InteractionLines(
        interactions = currentState.interactions,
        getAgentPosition = { agentId -> calculatePosition(agentId) }
    )
    
    // 评分动画
    currentState.agents
        .filter { it.score != null && it.status == AgentStatus.COMPLETE }
        .forEach { agent ->
            ScoreImpactAnimation(
                agentPosition = getAgentPosition(agent.id),
                centerPosition = Offset(0.5f, 0.5f)
            )
        }
    
    // 立场变化特效
    currentState.agents
        .filter { it.stanceChanged }
        .forEach { agent ->
            StanceChangeEffect(
                agentPosition = getAgentPosition(agent.id)
            )
        }
    
    // 思考波纹
    currentState.agents
        .filter { it.status == AgentStatus.THINKING }
        .forEach { agent ->
            ThinkingRipple(
                agentPosition = getAgentPosition(agent.id)
            )
        }
    
    // 完成庆祝
    if (currentState.isComplete) {
        CompletionCelebration(
            centerPosition = Offset(0.5f, 0.5f)
        )
    }
}
```

## 集成步骤

### 步骤 1: 更新 EnhancedSimulationScreen

在 `EnhancedSimulationScreen.kt` 中添加选项切换栏：

```kotlin
@Composable
fun EnhancedSimulationScreen(
    sessionId: String,
    userId: String,
    question: String,
    options: List<OptionInput>,
    collectedInfo: CollectedInfo?,
    decisionType: String,
    onNavigateBack: () -> Unit
) {
    // 使用新的 ViewModel
    val viewModel: EnhancedDecisionSimulationViewModel = viewModel(
        factory = EnhancedDecisionSimulationViewModelFactory(
            sessionId, userId, question, options, collectedInfo, decisionType
        )
    )
    
    val uiState by viewModel.uiState.collectAsState()
    val currentState = uiState.optionStates[uiState.activeOptionId]
    
    Scaffold(
        topBar = {
            Column {
                TopAppBar(
                    title = { Text("决策图谱舞台") },
                    navigationIcon = {
                        IconButton(onClick = onNavigateBack) {
                            Icon(Icons.Default.ArrowBack, "返回")
                        }
                    }
                )
                
                // 选项切换栏
                OptionTabsBar(
                    optionStates = uiState.optionStates,
                    activeOptionId = uiState.activeOptionId,
                    onSelectOption = { viewModel.switchToOption(it) },
                    onPauseOption = { viewModel.pauseOption(it) },
                    onResumeOption = { viewModel.resumeOption(it) }
                )
            }
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            if (currentState != null) {
                // 主要内容
                CircularAgentsView(
                    agents = currentState.agents,
                    totalScore = currentState.totalScore,
                    optionTitle = currentState.optionTitle,
                    currentMonth = currentState.currentMonth,
                    isComplete = currentState.isComplete,
                    scale = scale,
                    offset = offset,
                    onScaleChange = { scale = it },
                    onOffsetChange = { offset = it },
                    onAgentClick = { agent -> selectedAgent = agent }
                )
                
                // 添加所有动画效果
                AddAnimationEffects(currentState)
            }
        }
    }
}

@Composable
fun AddAnimationEffects(state: OptionSimulationState) {
    // 交互连线
    if (state.interactions.isNotEmpty()) {
        InteractionLines(
            interactions = state.interactions,
            getAgentPosition = { agentId ->
                // 计算 Agent 位置
                val index = state.agents.indexOfFirst { it.id == agentId }
                if (index != -1) {
                    calculateAgentPosition(index, state.agents.size)
                } else {
                    Offset(0.5f, 0.5f)
                }
            }
        )
    }
    
    // 评分动画
    state.agents
        .filter { it.score != null && it.status == PersonaStatus.COMPLETE }
        .forEach { agent ->
            val index = state.agents.indexOf(agent)
            if (index != -1) {
                ScoreImpactAnimation(
                    agentPosition = calculateAgentPosition(index, state.agents.size),
                    centerPosition = Offset(0.5f, 0.5f)
                )
            }
        }
    
    // 思考波纹
    state.agents
        .filter { it.status == PersonaStatus.THINKING }
        .forEach { agent ->
            val index = state.agents.indexOf(agent)
            if (index != -1) {
                ThinkingRipple(
                    agentPosition = calculateAgentPosition(index, state.agents.size)
                )
            }
        }
    
    // 完成庆祝
    if (state.isComplete) {
        CompletionCelebration(
            centerPosition = Offset(0.5f, 0.5f)
        )
    }
}

fun calculateAgentPosition(index: Int, total: Int): Offset {
    val angle = (index.toFloat() / total) * 2 * kotlin.math.PI.toFloat() - kotlin.math.PI.toFloat() / 2
    val radius = 0.35f
    val x = 0.5f + radius * kotlin.math.cos(angle)
    val y = 0.5f + radius * kotlin.math.sin(angle)
    return Offset(x, y)
}
```

### 步骤 2: 创建 ViewModel Factory

```kotlin
class EnhancedDecisionSimulationViewModelFactory(
    private val sessionId: String,
    private val userId: String,
    private val question: String,
    private val options: List<OptionInput>,
    private val collectedInfo: CollectedInfo?,
    private val decisionType: String
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(EnhancedDecisionSimulationViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return EnhancedDecisionSimulationViewModel(
                sessionId, userId, question, options, collectedInfo, decisionType
            ) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
```

### 步骤 3: 更新 UI 状态数据类

确保 `EnhancedSimulationUiState` 包含所有必要的字段：

```kotlin
data class EnhancedSimulationUiState(
    val activeOptionId: String = "",
    val optionStates: Map<String, OptionSimulationState> = emptyMap(),
    val currentStatus: String = "",
    val error: String = ""
)
```

## 功能特性

### 多选项并行推演

1. **独立 WebSocket 连接**
   - 每个选项有自己的 WebSocket 连接
   - 连接状态独立管理
   - 支持断线重连

2. **暂停/继续控制**
   - 点击暂停按钮：发送 `{"action":"pause"}` 消息
   - 点击继续按钮：发送 `{"action":"resume"}` 消息或重新建立连接
   - 状态实时同步

3. **选项切换**
   - 点击标签切换到对应选项
   - 自动加载该选项的推演状态
   - 如果选项未开始，自动建立连接

### 可视化增强

1. **交互连线动画**
   - 虚线从发送者指向接收者
   - 虚线持续流动（dashPathEffect 动画）
   - 箭头指示方向

2. **评分影响动画**
   - Agent 完成评分时触发
   - 金色线条从 Agent 延伸到中心
   - 带有发光效果
   - 1秒后自动消失

3. **立场变化特效**
   - 检测到立场变化时触发
   - 黄色警告圆圈脉冲动画
   - 3秒后自动消失

4. **思考波纹动画**
   - Agent 思考时持续显示
   - 蓝色波纹向外扩散
   - 循环播放

5. **完成庆祝动画**
   - 所有 Agent 完成时触发
   - 旋转的金色星星
   - 5秒后自动消失

## 性能优化建议

1. **WebSocket 连接管理**
   - 限制同时活跃的连接数（建议最多 3 个）
   - 暂停的选项不建立连接
   - 及时关闭不用的连接

2. **动画性能**
   - 使用 `remember` 缓存动画状态
   - 限制同时显示的动画数量
   - 使用 `LaunchedEffect` 控制动画生命周期

3. **内存优化**
   - 限制思考历史记录数量（最多 50 条）
   - 及时清理已完成选项的详细数据
   - 使用 `derivedStateOf` 优化状态派生

## 测试清单

- [ ] 多选项切换流畅
- [ ] 暂停/继续功能正常
- [ ] WebSocket 连接稳定
- [ ] 交互连线正确显示
- [ ] 评分动画触发正确
- [ ] 立场变化特效显示
- [ ] 思考波纹持续显示
- [ ] 完成庆祝动画播放
- [ ] 内存占用合理
- [ ] 无卡顿和崩溃

## 下一步优化

1. 添加选项对比视图（并排显示多个选项）
2. 实现推演回放功能
3. 添加更多动画效果（粒子效果、光晕等）
4. 优化大量 Agent 时的性能
5. 添加推演进度保存和恢复
