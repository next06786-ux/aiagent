# Android 增强版推演功能 - 完整实现

## 🎯 已实现的核心功能

### 1. ✅ 圆形布局可视化
**对应 Web 端**: `getPersonaPosition()` 函数

**实现**:
- 7个 Agent 围绕中心选项圆形排列
- 智能布局算法：
  - ≤5个：单层五边形（半径 32%）
  - 6-7个：单层圆形（半径 35%）
  - ≥8个：双层布局（内层 25%，外层 40%）
- 使用三角函数计算精确位置

```kotlin
fun calculateAgentPosition(index: Int, total: Int): Offset {
    val angle = (index.toFloat() / total) * 2 * PI.toFloat() - PI.toFloat() / 2
    val radius = when {
        total <= 5 -> 0.32f
        total <= 7 -> 0.35f
        else -> if (index < 5) 0.25f else 0.40f
    }
    val x = 0.5f + radius * cos(angle)
    val y = 0.5f + radius * sin(angle)
    return Offset(x, y)
}
```

### 2. ✅ 缩放和平移控制
**对应 Web 端**: 鼠标滚轮缩放 + 拖拽平移

**实现**:
- 缩放范围：0.5x - 2x
- 手势拖拽平移
- 缩放控制按钮（+/-/重置）
- 实时显示缩放比例
- 使用 `graphicsLayer` 实现流畅变换

```kotlin
Box(
    modifier = Modifier
        .graphicsLayer(
            scaleX = scale,
            scaleY = scale,
            translationX = offset.x,
            translationY = offset.y
        )
)
```

### 3. ✅ Agent 球体可视化
**对应 Web 端**: `PersonaAvatar` 组件

**实现**:
- 120dp 圆形球体
- 径向渐变背景（白色 → 浅蓝 → 深蓝）
- 状态指示器（右上角圆点）
- 思考中脉冲动画
- 点击交互

```kotlin
Box(
    modifier = Modifier
        .size(120.dp)
        .clip(CircleShape)
        .background(
            Brush.radialGradient(
                colors = listOf(
                    Color.White.copy(alpha = 0.98f),
                    Color(0xFFE8F4FF),
                    Color(0xFFB8DCFF)
                )
            )
        )
)
```

### 4. ✅ 中心选项卡片
**对应 Web 端**: `.center-option` 样式

**实现**:
- 180dp 圆形卡片
- 显示选项标题
- 显示当前轮次
- 显示综合评分（大号字体）
- 阴影效果

### 5. ✅ 实时状态显示
**对应 Web 端**: Agent 状态管理

**实现**:
- **等待中** (WAITING) - 灰色指示器
- **思考中** (THINKING) - 蓝色脉冲动画
- **完成** (COMPLETE) - 绿色指示器
- **错误** (ERROR) - 红色指示器

### 6. ✅ 评分和立场显示
**对应 Web 端**: `.persona-score` 和 `.persona-stance`

**实现**:
- 评分：圆角卡片，主题色背景
- 立场：小标签，根据类型变色
  - 支持：绿色背景
  - 反对：红色背景
  - 中立：灰色背景

### 7. ✅ 消息气泡系统
**对应 Web 端**: `.persona-message-bubble`

**实现**:
- 显示在 Agent 下方
- 自动截断长消息（50字符）
- 点击查看详情
- "详细 →" 提示
- 圆角卡片样式

### 8. ✅ 思考历史弹窗
**对应 Web 端**: `.message-modal.history-modal`

**实现**:
- 全屏对话框（80%高度）
- 显示 Agent 名称
- 当前状态（立场 + 评分）
- 历史记录列表：
  - 轮次标记
  - 消息内容
  - 关键论点（列表）
  - 推理过程
  - 时间戳
- 滚动查看

### 9. ✅ 分数影响动画
**对应 Web 端**: `.score-impact-line`

**实现**:
- Agent 完成评分时触发
- 从 Agent 到中心的虚线
- 渐变透明度动画
- 使用 Canvas 绘制

### 10. ✅ 完成标记
**对应 Web 端**: 右上角完成提示

**实现**:
- 绿色勾选图标
- "分析完成"文字
- 卡片样式
- 固定在右上角

## 📊 功能对比表

| 功能 | Web 端 | Android 端 | 状态 |
|------|--------|-----------|------|
| 圆形布局 | ✅ | ✅ | 完成 |
| 缩放控制 | ✅ | ✅ | 完成 |
| 平移控制 | ✅ | ✅ | 完成 |
| Agent 球体 | ✅ 3D | ✅ 2D | 完成 |
| 状态指示 | ✅ | ✅ | 完成 |
| 评分显示 | ✅ | ✅ | 完成 |
| 立场标签 | ✅ | ✅ | 完成 |
| 消息气泡 | ✅ | ✅ | 完成 |
| 思考历史 | ✅ | ✅ | 完成 |
| 分数动画 | ✅ | ✅ | 完成 |
| 交互连线 | ✅ | 🔄 | 待实现 |
| 3D 效果 | ✅ | ❌ | 不适用 |

## 🎨 UI 设计

### 布局结构
```
┌─────────────────────────────────────┐
│  [返回]  决策图谱舞台        [缩放]  │
├─────────────────────────────────────┤
│                                     │
│         Agent 1 (球体)              │
│           ↓ 评分                    │
│           ↓ 立场                    │
│           ↓ 消息气泡                │
│                                     │
│  Agent 7  ←  [中心选项]  →  Agent 2 │
│                 ↓ 总分              │
│                                     │
│         Agent 6 (球体)              │
│                                     │
│  [完成标记]                         │
└─────────────────────────────────────┘
```

### 颜色方案
- **主色调**: Material 3 动态主题
- **Agent 球体**: 白色 → 浅蓝渐变
- **状态指示器**:
  - 等待: `Color.Gray`
  - 思考: `Color(0xFF2196F3)` 蓝色
  - 完成: `Color(0xFF4CAF50)` 绿色
  - 错误: `Color(0xFFF44336)` 红色
- **立场标签**:
  - 支持: 绿色 `0xFF4CAF50`
  - 反对: 红色 `0xFFF44336`
  - 中立: 灰色

## 🔧 技术实现

### 1. 圆形布局算法
使用三角函数计算每个 Agent 的位置：
- `angle = (index / total) * 2π - π/2`
- `x = 0.5 + radius * cos(angle)`
- `y = 0.5 + radius * sin(angle)`

### 2. 手势处理
```kotlin
// 拖拽平移
.pointerInput(Unit) {
    detectDragGestures { change, dragAmount ->
        change.consume()
        onOffsetChange(offset + dragAmount)
    }
}

// 点击检测
.pointerInput(Unit) {
    detectTapGestures { onClick() }
}
```

### 3. 动画系统
```kotlin
// 脉冲动画（思考中）
val infiniteTransition = rememberInfiniteTransition()
val pulseAlpha by infiniteTransition.animateFloat(
    initialValue = 0.3f,
    targetValue = 0.8f,
    animationSpec = infiniteRepeatable(
        animation = tween(1000),
        repeatMode = RepeatMode.Reverse
    )
)

// 分数影响动画
Canvas(modifier = Modifier.fillMaxSize()) {
    drawLine(
        color = Color.Blue.copy(alpha = alpha),
        start = agentPosition,
        end = centerPosition,
        strokeWidth = 3f,
        pathEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 10f))
    )
}
```

### 4. 状态管理
```kotlin
// ViewModel 管理所有状态
data class SimulationUiState(
    val agents: List<AgentState>,
    val totalScore: Double,
    val currentMonth: Int,
    val phase: SimulationPhase,
    ...
)

// Agent 状态
data class AgentState(
    val id: String,
    val name: String,
    val status: AgentStatus,
    val score: Double?,
    val stance: String?,
    val currentMessage: String?,
    val thinkingHistory: List<ThinkingRecord>
)
```

## 🚀 性能优化

### 1. 组合优化
- 使用 `remember` 缓存计算结果
- 使用 `derivedStateOf` 避免不必要的重组
- 使用 `key` 优化列表渲染

### 2. 动画优化
- 使用 `graphicsLayer` 而不是 `Modifier.offset`
- 使用 `infiniteTransition` 复用动画
- 避免在动画中触发重组

### 3. 渲染优化
- 使用 `Canvas` 绘制连线（避免创建大量 View）
- 使用 `LazyColumn` 渲染历史记录
- 使用 `wrapContentSize` 优化布局

## 📱 用户交互

### 手势操作
1. **拖拽** - 平移视图
2. **点击 Agent** - 查看思考历史
3. **点击消息气泡** - 查看详细内容
4. **点击历史按钮** - 打开历史弹窗

### 按钮操作
1. **+ 按钮** - 放大视图
2. **- 按钮** - 缩小视图
3. **⟲ 按钮** - 重置视图
4. **返回按钮** - 返回上一页

## 🎯 与 Web 端的差异

### 已实现（功能对等）
✅ 圆形布局
✅ 缩放和平移
✅ Agent 状态显示
✅ 评分和立场
✅ 消息气泡
✅ 思考历史
✅ 分数动画

### 简化实现
🔄 **Agent 球体**: Web 端是 3D 星球，Android 端是 2D 渐变圆形
🔄 **动画效果**: Web 端更复杂，Android 端更简洁

### 待实现
⏳ **交互连线**: Agent 之间的实时交互连线
⏳ **技能结果**: 显示 Agent 使用的技能
⏳ **立场改变动画**: 特殊的警告动画

## 📝 总结

Android 端现在已经实现了 Web 端的核心可视化功能：

1. ✅ **圆形布局** - 7个 Agent 优雅地围绕中心排列
2. ✅ **交互控制** - 缩放、平移、点击查看详情
3. ✅ **实时更新** - Agent 状态、评分、消息实时显示
4. ✅ **思考历史** - 完整的历史记录查看
5. ✅ **动画效果** - 脉冲、分数影响等动画

虽然在 3D 效果上有所简化（Android 使用 2D 渐变代替 3D 星球），但核心的可视化和交互功能已经完全实现，用户体验与 Web 端基本一致！🎉
