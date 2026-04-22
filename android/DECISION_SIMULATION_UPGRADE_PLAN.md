# 决策副本功能升级计划

## 目标
将 Web 端的决策副本功能完整移植到 Android 端，实现相同的用户体验和功能。

## Web 端功能分析

### 核心功能
1. **并行推演**：多个选项同时进行推演
2. **人格 Agent 系统**：
   - 多个 AI 人格（Persona）参与决策分析
   - 每个人格有独立的思考过程
   - 显示人格的实时状态（等待/思考/完成）
   - 显示人格的评分和立场
3. **人格交互**：
   - 人格之间的讨论和辩论
   - 实时显示交互消息
   - 交互类型（质疑、支持、补充等）
4. **实时评分**：
   - 每个选项的综合评分
   - 基于所有人格的评分计算
5. **推演控制**：
   - 暂停/继续特定选项的推演
   - 切换查看不同选项的推演过程
6. **可视化**：
   - 人格头像和状态指示器
   - 思考气泡动画
   - 评分进度条
   - 交互连线动画

## Android 端现状

### 已实现
- ✅ 基础 WebSocket 连接
- ✅ 顺序推演（一个接一个）
- ✅ 简单的事件列表显示
- ✅ 进度条显示

### 缺失功能
- ❌ 人格 Agent 可视化
- ❌ 并行推演
- ❌ 人格交互动画
- ❌ 实时评分系统
- ❌ 推演控制（暂停/继续）
- ❌ 高级可视化效果

## 升级任务清单

### 阶段 1：数据模型和 ViewModel 升级 ✅

**任务**：
1. ✅ 创建人格 Agent 数据模型
   - `PersonaAgent` 数据类
   - 状态：waiting, thinking, complete, error
   - 属性：id, name, score, stance, thinkingHistory
2. ✅ 创建人格交互数据模型
   - `PersonaInteraction` 数据类
   - 属性：from, to, type, message, timestamp
3. ✅ 升级 `DecisionSimulationViewModel`
   - 支持并行 WebSocket 连接
   - 管理多个选项的状态
   - 处理人格相关的 WebSocket 消息
   - 实时计算综合评分

**文件**：
- ✅ `android/app/src/main/java/com/lifeswarm/android/data/model/PersonaModels.kt` (已创建)
- ✅ `android/app/src/main/java/com/lifeswarm/android/presentation/decision/EnhancedDecisionSimulationViewModel.kt` (已创建)

### 阶段 2：人格可视化组件 ✅

**任务**：
1. ✅ 创建人格卡片组件
   - 显示人格头像（使用 Material Icons）
   - 状态指示器（颜色编码）
   - 思考气泡动画
   - 评分显示
2. ✅ 创建人格网格布局
   - 响应式网格（2列）
   - 自动适应屏幕大小
3. ✅ 创建思考历史对话框
   - 显示人格的完整思考过程
   - 分轮次显示
   - 支持展开/折叠

**文件**：
- ✅ `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/PersonaCard.kt` (已创建)
- ✅ `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/PersonaGrid.kt` (已创建)
- ✅ `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/ThinkingHistoryDialog.kt` (已创建)

### 阶段 3：交互可视化 ✅

**任务**：
1. ✅ 创建交互消息组件
   - 显示人格之间的对话
   - 消息气泡样式
   - 发送者和接收者标识
2. ✅ 创建交互时间线
   - 按时间顺序显示交互
   - 支持滚动查看历史
3. ✅ 添加交互动画
   - 消息出现动画
   - 连线动画（可选）

**文件**：
- ✅ `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/InteractionMessage.kt` (已创建)
- ✅ `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/InteractionTimeline.kt` (已创建)

### 阶段 4：评分系统 ✅

**任务**：
1. ✅ 创建评分卡片组件
   - 显示综合评分
   - 进度条动画
   - 评分变化动画
2. ✅ 创建评分对比视图
   - 多个选项的评分对比
   - 柱状图或雷达图
3. ✅ 实时更新评分
   - 监听人格评分变化
   - 自动计算平均分

**文件**：
- ✅ `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/ScoreCard.kt` (已创建)
- ✅ `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/ScoreComparison.kt` (已创建)

### 阶段 5：推演控制 ✅

**任务**：
1. ✅ 添加选项切换 Tab
   - 显示所有选项
   - 切换查看不同选项的推演
2. ✅ 添加暂停/继续按钮
   - 控制特定选项的推演
   - 更新 WebSocket 连接状态
3. ✅ 添加推演速度控制（可选）
   - 快速/正常/慢速模式

**文件**：
- ✅ `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/SimulationControls.kt` (已创建)

### 阶段 6：UI 整合和优化 ✅

**任务**：
1. ✅ 重构 `DecisionSimulationScreen.kt`
   - 集成所有新组件
   - 优化布局和交互
   - 添加动画效果
2. ✅ 性能优化
   - 减少不必要的重组
   - 优化 WebSocket 消息处理
   - 添加加载状态
3. ✅ 错误处理
   - 网络错误提示
   - 重连机制
   - 降级方案

**文件**：
- ✅ `android/app/src/main/java/com/lifeswarm/android/presentation/decision/DecisionSimulationScreen.kt` (已重构)

## 技术要点

### WebSocket 消息类型
根据 Web 端实现，需要处理以下消息类型：
- `status`: 状态更新
- `option_start`: 选项开始
- `agents_start` / `personas_init`: 人格初始化
- `agent_thinking`: 人格思考中
- `agents_thinking_batch`: 批量人格思考
- `agent_complete`: 人格完成
- `persona_analysis`: 人格分析结果
- `persona_interaction`: 人格交互
- `final_evaluation`: 最终评估
- `option_complete`: 选项完成
- `done` / `complete`: 全部完成
- `error`: 错误

### 并行 WebSocket 连接
- 为每个选项建立独立的 WebSocket 连接
- 使用 `Map<String, WebSocket>` 管理多个连接
- 支持动态添加/移除连接

### 状态管理
- 使用 `StateFlow` 管理 UI 状态
- 按选项 ID 分组管理数据
- 使用 `Map<String, List<PersonaAgent>>` 存储人格状态

### 动画效果
- 使用 Compose Animation API
- 思考气泡：脉冲动画
- 评分变化：数字滚动动画
- 消息出现：淡入 + 滑动动画

## 开发顺序

1. **第一步**：创建数据模型（阶段 1）
2. **第二步**：升级 ViewModel 支持并行推演（阶段 1）
3. **第三步**：创建人格卡片组件（阶段 2）
4. **第四步**：创建评分组件（阶段 4）
5. **第五步**：创建交互组件（阶段 3）
6. **第六步**：添加推演控制（阶段 5）
7. **第七步**：整合和优化（阶段 6）

## 预期效果

完成后，Android 端将具有：
- 🎭 多个 AI 人格的实时思考可视化
- 💬 人格之间的动态交互展示
- 📊 实时评分和对比
- ⏯️ 灵活的推演控制
- ✨ 流畅的动画效果
- 📱 适配移动端的优化布局

与 Web 端保持功能一致，同时针对移动端进行优化。

## 参考文件

### Web 端
- `web/src/pages/DecisionSimulationPage.tsx` - 主页面
- `web/src/components/decision/PersonaInteractionView.tsx` - 人格交互视图

### Android 端
- `android/app/src/main/java/com/lifeswarm/android/presentation/decision/DecisionSimulationScreen.kt` - 现有实现
- `android/app/src/main/java/com/lifeswarm/android/data/model/DecisionModels.kt` - 数据模型

---

## ✅ 升级完成总结

### 已完成的功能

#### 1. 数据层 (阶段 1)
- ✅ `PersonaModels.kt` - 完整的人格数据模型
  - PersonaAgent（人格代理）
  - PersonaStatus（状态枚举）
  - ThinkingRecord（思考记录）
  - PersonaInteraction（人格交互）
  - OptionSimulationState（选项推演状态）
  - SimulationEvent（推演事件）

- ✅ `EnhancedDecisionSimulationViewModel.kt` - 增强版 ViewModel
  - 并行 WebSocket 连接管理
  - 10+ 种 WebSocket 消息类型处理
  - 实时评分计算
  - 暂停/继续控制
  - 选项切换功能

#### 2. UI 组件层 (阶段 2-5)

**人格可视化组件**：
- ✅ `PersonaCard.kt` - 人格卡片
  - 动态头像和状态指示器
  - 思考气泡动画
  - 评分徽章
  - 立场显示
  
- ✅ `PersonaGrid.kt` - 人格网格布局
  - 响应式 2 列布局
  - 点击查看详情

- ✅ `ThinkingHistoryDialog.kt` - 思考历史对话框
  - 分轮次显示思考过程
  - 展开/折叠功能
  - 评分和立场显示

**交互可视化组件**：
- ✅ `InteractionMessage.kt` - 交互消息卡片
  - 动画消息气泡
  - 发送者/接收者标识
  - 交互类型图标

- ✅ `InteractionTimeline.kt` - 交互时间线
  - 自动滚动
  - 统计信息显示
  - 时间戳显示

**评分系统组件**：
- ✅ `ScoreCard.kt` - 评分卡片
  - 圆形进度指示器
  - 动画评分显示
  - 完成状态指示

- ✅ `ScoreComparison.kt` - 评分对比
  - 柱状图对比
  - 雷达图可视化
  - 排名列表

**控制组件**：
- ✅ `SimulationControls.kt` - 推演控制
  - 选项标签页切换
  - 暂停/继续按钮
  - 进度信息显示
  - 速度控制（可选）

#### 3. 主屏幕整合 (阶段 6)
- ✅ `DecisionSimulationScreen.kt` - 完全重构
  - 使用 EnhancedDecisionSimulationViewModel
  - 集成所有新组件
  - 响应式布局
  - 流畅动画效果
  - 错误处理和状态管理

### 功能特性

#### 核心功能
- ✅ 并行推演多个选项
- ✅ 实时人格 Agent 可视化
- ✅ 人格之间的交互讨论
- ✅ 动态评分计算和对比
- ✅ 推演控制（暂停/继续/切换）
- ✅ 完整的 WebSocket 消息处理

#### 用户体验
- ✅ 流畅的动画效果
  - 思考气泡脉冲动画
  - 评分变化动画
  - 消息出现动画
  - 状态转换动画
- ✅ 响应式布局
  - 适配不同屏幕尺寸
  - 2 列人格网格
  - 滚动时间线
- ✅ 交互反馈
  - 点击查看详情
  - 状态颜色编码
  - 进度指示器

#### 技术实现
- ✅ Material 3 设计系统
- ✅ Jetpack Compose 声明式 UI
- ✅ StateFlow 状态管理
- ✅ 协程异步处理
- ✅ OkHttp WebSocket 连接
- ✅ JSON 消息解析

### 与 Web 端功能对比

| 功能 | Web 端 | Android 端 | 状态 |
|------|--------|-----------|------|
| 并行推演 | ✅ | ✅ | 完成 |
| 人格可视化 | ✅ | ✅ | 完成 |
| 人格交互 | ✅ | ✅ | 完成 |
| 实时评分 | ✅ | ✅ | 完成 |
| 推演控制 | ✅ | ✅ | 完成 |
| 评分对比 | ✅ | ✅ | 完成 |
| 思考历史 | ✅ | ✅ | 完成 |
| 动画效果 | ✅ | ✅ | 完成 |

### 文件清单

**数据模型**：
1. `android/app/src/main/java/com/lifeswarm/android/data/model/PersonaModels.kt`

**ViewModel**：
2. `android/app/src/main/java/com/lifeswarm/android/presentation/decision/EnhancedDecisionSimulationViewModel.kt`

**UI 组件**：
3. `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/PersonaCard.kt`
4. `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/PersonaGrid.kt`
5. `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/ThinkingHistoryDialog.kt`
6. `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/InteractionMessage.kt`
7. `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/InteractionTimeline.kt`
8. `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/ScoreCard.kt`
9. `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/ScoreComparison.kt`
10. `android/app/src/main/java/com/lifeswarm/android/presentation/decision/components/SimulationControls.kt`

**主屏幕**：
11. `android/app/src/main/java/com/lifeswarm/android/presentation/decision/DecisionSimulationScreen.kt` (重构)

### 下一步建议

#### 测试和优化
1. **WebSocket 连接测试**
   - 测试与真实后端的连接
   - 验证所有消息类型的处理
   - 测试断线重连机制

2. **性能优化**
   - 监控内存使用
   - 优化大量人格时的渲染性能
   - 减少不必要的重组

3. **用户体验优化**
   - 添加加载骨架屏
   - 优化动画流畅度
   - 添加haptic反馈

#### 功能增强
1. **数据持久化**
   - 保存推演历史
   - 支持离线查看
   - 导出推演报告

2. **高级可视化**
   - 3D 人格关系图
   - 更丰富的图表类型
   - 自定义主题

3. **交互增强**
   - 手动干预推演
   - 自定义人格配置
   - 推演回放功能

### 总结

Android 端决策推演功能已完全实现，达到与 Web 端功能对等的水平。所有 6 个阶段的任务均已完成，包括：

- ✅ 完整的数据模型和状态管理
- ✅ 丰富的 UI 组件库
- ✅ 流畅的动画和交互
- ✅ 并行推演和实时更新
- ✅ 完善的错误处理

现在可以进行真实环境测试，并根据用户反馈进行进一步优化。
