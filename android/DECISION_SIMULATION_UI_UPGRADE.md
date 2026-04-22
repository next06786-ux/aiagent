# 决策推演界面UI升级 - 对齐Web端

## 概述
成功将Android端的决策推演界面UI对齐Web端设计，实现了7个Agent决策人格功能球体和各种交互UI。

## 主要特性

### 1. 7个Agent球体可视化
- **圆形排列**：7个Agent以圆形方式排列在中心选项周围
- **玻璃质感**：使用径向渐变实现玻璃球体效果，带高光和纹理
- **实时状态**：显示Agent的思考状态（等待/思考中/完成/错误）
- **动态动画**：思考中的Agent有脉冲动画效果

### 2. 中心选项球体
- **大型球体**：200dp直径，位于屏幕中心
- **综合评分**：实时显示所有Agent的平均分数
- **选项标题**：显示当前决策选项的名称
- **玻璃效果**：与Agent球体相同的玻璃质感设计

### 3. 实时消息气泡
- **外侧显示**：消息气泡显示在Agent球体外侧，避免遮挡
- **自动消失**：消息显示一段时间后自动消失
- **点击查看**：点击消息气泡可查看完整历史记录
- **截断显示**：长消息自动截断，显示"详细 →"提示

### 4. 分数影响动画
- **连线动画**：Agent完成评分后，从Agent到中心球体绘制动画连线
- **光点移动**：沿连线移动的光点效果
- **渐变消失**：1.5秒后动画自动消失
- **视觉反馈**：清晰展示分数如何影响总分

### 5. Agent历史记录弹窗
- **完整历程**：显示Agent的所有思考记录
- **当前状态**：顶部显示立场和评分
- **分轮显示**：按轮次组织思考记录
- **滚动查看**：支持滚动查看长历史记录

### 6. 缩放和拖拽
- **双指缩放**：支持0.5x到2x的缩放范围
- **拖拽平移**：支持拖拽移动视图
- **控制按钮**：右上角提供放大/缩小/重置按钮
- **缩放指示**：显示当前缩放百分比

### 7. 完成状态提示
- **完成标记**：推演完成后显示"分析完成"标记
- **绿色图标**：使用绿色勾选图标
- **右上角显示**：固定在右上角位置

## 技术实现

### 文件结构
```
android/app/src/main/java/com/lifeswarm/android/presentation/decision/
├── DecisionSimulationScreen.kt          # 主推演页面
├── PersonaInteractionView.kt            # 7个Agent球体交互视图（新增）
├── DecisionCollectionScreen.kt          # 信息采集界面
└── components/                          # 组件目录
```

### 核心组件

#### PersonaInteractionView
- **功能**：7个Agent球体的主容器
- **特性**：缩放、拖拽、动画管理
- **子组件**：
  - `CenterOptionSphere`：中心选项球体
  - `AgentSphere`：单个Agent球体
  - `ScoreImpactAnimation`：分数影响动画
  - `AgentHistoryDialog`：历史记录弹窗

#### 位置计算
```kotlin
private fun getAgentPosition(index: Int, total: Int): Offset {
    val angle = (index.toFloat() / total) * 2 * PI.toFloat() - PI.toFloat() / 2
    val radius = 35f // 半径百分比
    return Offset(
        x = radius * cos(angle),
        y = radius * sin(angle)
    )
}
```

### 设计规范

#### 颜色方案
- **主文本**：#1A1A1A（深黑色）
- **次要文本**：#666666（中灰色）
- **主色调**：#0A59F7（蓝色）
- **强调色**：#6B48FF（紫色）
- **成功色**：#34C759（绿色）
- **错误色**：#FF3B30（红色）

#### 球体效果
- **径向渐变**：从白色到淡蓝色
- **高光位置**：(34%, 26%)
- **高光强度**：55%透明度
- **阴影**：多层阴影实现立体感

#### 动画参数
- **思考脉冲**：2秒循环，scale 1.0-1.05
- **分数动画**：1.5秒线性，从Agent到中心
- **消息显示**：5秒后自动消失
- **缩放范围**：0.5x - 2.0x

## 对比Web端

### 已实现功能 ✅
- ✅ 7个Agent球体圆形排列
- ✅ 玻璃质感球体设计
- ✅ 中心选项球体和综合评分
- ✅ 实时消息气泡显示
- ✅ 分数影响动画
- ✅ Agent历史记录弹窗
- ✅ 缩放和拖拽功能
- ✅ 完成状态提示
- ✅ 立场和评分显示

### 差异说明
1. **交互方式**：Android使用双指缩放，Web使用鼠标滚轮
2. **消息位置**：Android消息气泡位置经过优化，避免遮挡球体
3. **动画实现**：Android使用Compose动画API，Web使用CSS动画
4. **布局适配**：Android针对移动端屏幕尺寸进行了优化

## 使用方法

### 基本用法
```kotlin
PersonaInteractionView(
    agents = listOf(
        AgentState(
            id = "rational_analyst",
            name = "理性分析师",
            status = AgentStatus.COMPLETE,
            score = 85,
            stance = "支持此方案",
            currentMessage = "经过分析，这个方案可行性较高",
            thinkingHistory = listOf(...)
        ),
        // ... 其他6个Agent
    ),
    totalScore = 82.5,
    optionTitle = "是否接受这份工作offer？",
    isComplete = true
)
```

### 手势操作
- **双指缩放**：放大/缩小视图
- **单指拖拽**：平移视图
- **点击球体**：查看Agent历史记录
- **点击消息**：查看完整消息内容

## 后续优化建议

1. **性能优化**
   - 使用`remember`缓存计算结果
   - 优化Canvas绘制性能
   - 减少不必要的重组

2. **交互增强**
   - 添加Agent之间的交互连线动画
   - 支持Agent球体的拖拽排列
   - 添加更多手势操作

3. **视觉效果**
   - 添加粒子效果
   - 增强光晕动画
   - 优化阴影效果

4. **功能扩展**
   - 支持多选项对比视图
   - 添加时间轴回放功能
   - 导出推演结果

## 相关文件
- `PersonaInteractionView.kt`：7个Agent球体交互视图
- `DecisionSimulationScreen.kt`：决策推演主页面
- `DecisionCollectionScreen.kt`：信息采集界面
- `DecisionSimulationViewModel.kt`：推演逻辑ViewModel

## 参考资料
- Web端实现：`web/src/components/decision/PersonaInteractionView.tsx`
- Web端样式：`web/src/components/decision/PersonaInteractionView.css`
- 设计规范：Material Design 3
