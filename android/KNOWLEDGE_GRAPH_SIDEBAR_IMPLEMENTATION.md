# 知识星图侧边栏功能实现

## 概述
为Android客户端的知识星图功能添加了与Web端一致的侧边栏，用于显示节点详细信息。

## 参考实现
- **Web端**: `web/src/pages/KnowledgeGraphPage.tsx` (行 1300-2200)
- **Android端**: `android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/NodeDetailPanel.kt`

## 新增文件

### NodeDetailPanel.kt
完整的节点详情侧边栏组件，包含：

#### 1. 主组件 - NodeDetailPanel
```kotlin
@Composable
fun NodeDetailPanel(
    selectedNode: KnowledgeGraphNode?,
    graph: KnowledgeGraphView?,
    viewMode: String,
    onClose: () -> Unit,
    onDelete: ((KnowledgeGraphNode) -> Unit)? = null,
    onNavigateToNode: ((KnowledgeGraphNode) -> Unit)? = null,
    modifier: Modifier = Modifier
)
```

**功能**：
- 侧边栏滑入/滑出动画
- 根据视图模式显示不同内容
- 删除和关闭按钮
- 支持节点导航

#### 2. 人际关系视图详情 - PeopleNodeDetail
显示内容：
- ✅ 节点名称和类型
- ✅ 连接数统计
- ✅ 基本信息（metadata）
- ✅ 相关故事
- ✅ 关联人物列表
- ✅ 点击关联人物可导航

#### 3. 职业发展视图详情 - CareerNodeDetail
显示内容：
- ✅ 节点名称和类型（带颜色标识）
- ✅ 技能掌握度进度条
  - 已掌握（绿色）
  - 部分掌握（黄色）
  - 待学习（红色）
- ✅ 节点描述
- ✅ 关联节点（按关系类型分组）
  - 已掌握技能
  - 需要的技能
  - 所属公司
  - 技能依赖

#### 4. 升学规划视图详情 - EducationNodeDetail
显示内容：
- ✅ 节点名称和类型
- ✅ 详细信息（学校、专业等）
- ✅ 描述信息
- ✅ 关联节点（按关系类型分组）
  - 学业成就
  - 符合条件的院校
  - 需要的行动

#### 5. 辅助组件
- **SectionTitle**: 章节标题
- **StoryCard**: 故事卡片
- **RelatedNodeCard**: 关联节点卡片（可点击导航）

#### 6. 工具函数
- `getRelatedNodes()`: 获取节点的所有关联节点
- `getNodeTypeColor()`: 根据节点类型返回颜色
- `getRelationLabel()`: 获取关系类型的中文标签
- `getEducationRelationLabel()`: 获取升学关系的中文标签

## 修改的文件

### KnowledgeGraphScreen.kt
**修改内容**：
1. 集成 `NodeDetailPanel` 组件
2. 点击节点时查找对应的 `KnowledgeGraphNode`
3. 传递完整的图谱数据给侧边栏
4. 实现节点导航功能
5. 移除旧的底部信息卡片，改用侧边栏

**关键代码**：
```kotlin
// 查找对应的KnowledgeGraphNode
val graphNode = selectedNode?.let { node ->
    nodes.find { it.id == node.id }
}

// 显示侧边栏
NodeDetailPanel(
    selectedNode = graphNode,
    graph = (uiState as? KnowledgeGraphUiState.Success)?.data,
    viewMode = selectedView,
    onClose = { /* ... */ },
    onDelete = { /* ... */ },
    onNavigateToNode = { /* ... */ },
    modifier = Modifier.align(Alignment.CenterEnd)
)
```

## 功能特性

### 1. 动画效果
- ✅ 侧边栏滑入/滑出动画
- ✅ 淡入/淡出效果
- ✅ 平滑过渡

### 2. 交互功能
- ✅ 点击节点显示详情
- ✅ 点击关闭按钮隐藏侧边栏
- ✅ 点击删除按钮删除节点（待实现后端）
- ✅ 点击关联节点导航到该节点
- ✅ 点击空白区域重置视角

### 3. 视图适配
- ✅ 人际关系视图
- ✅ 职业发展视图
- ✅ 升学规划视图
- ✅ 默认视图（兜底）

### 4. 数据展示
- ✅ 节点基本信息
- ✅ 节点元数据
- ✅ 关联关系
- ✅ 故事内容
- ✅ 技能掌握度
- ✅ 学校信息

## 与Web端对比

| 功能 | Web端 | Android端 | 状态 |
|------|-------|-----------|------|
| 侧边栏布局 | ✅ | ✅ | 完成 |
| 滑入/滑出动画 | ✅ | ✅ | 完成 |
| 节点名称和类型 | ✅ | ✅ | 完成 |
| 基本信息展示 | ✅ | ✅ | 完成 |
| 相关故事 | ✅ | ✅ | 完成 |
| 关联节点列表 | ✅ | ✅ | 完成 |
| 节点导航 | ✅ | ✅ | 完成 |
| 删除节点 | ✅ | ✅ | UI完成，待后端 |
| 技能掌握度 | ✅ | ✅ | 完成 |
| 关系类型分组 | ✅ | ✅ | 完成 |
| 颜色标识 | ✅ | ✅ | 完成 |

## 使用示例

### 基本使用
```kotlin
NodeDetailPanel(
    selectedNode = selectedNode,
    graph = graphData,
    viewMode = "people",
    onClose = { selectedNode = null },
    onDelete = { node -> 
        // 删除节点逻辑
    },
    onNavigateToNode = { node ->
        // 导航到节点
        renderer.focusOnNode(node.id)
    }
)
```

### 在KnowledgeGraphScreen中集成
```kotlin
Box(modifier = Modifier.fillMaxSize()) {
    // 3D图谱视图
    AndroidView(factory = { /* ... */ })
    
    // 侧边栏（右侧）
    NodeDetailPanel(
        selectedNode = graphNode,
        graph = graphData,
        viewMode = selectedView,
        onClose = { /* ... */ },
        modifier = Modifier.align(Alignment.CenterEnd)
    )
}
```

## 样式设计

### 颜色方案
- **主背景**: Surface (95% 不透明度)
- **卡片背景**: SurfaceVariant (50% 不透明度)
- **主要文本**: OnSurface
- **次要文本**: OnSurfaceVariant
- **强调色**: Primary

### 节点类型颜色
- **技能**: 绿色 (#4CAF50)
- **岗位**: 蓝色 (#2196F3)
- **公司**: 紫色 (#9C27B0)
- **其他**: 灰色 (#607D8B)

### 技能掌握度颜色
- **已掌握**: 绿色 (#4CAF50)
- **部分掌握**: 黄色 (#FFC107)
- **待学习**: 红色 (#F44336)

## 待实现功能

### 1. 删除节点后端集成
```kotlin
onDelete = { node ->
    viewModel.deleteNode(node.id)
    // 刷新图谱
    viewModel.loadGraphData()
}
```

### 2. 节点编辑功能
- 编辑节点名称
- 编辑节点属性
- 添加/删除关系

### 3. 更多交互
- 长按节点显示菜单
- 双击节点快速导航
- 手势缩放侧边栏

## 测试建议

### 1. 功能测试
- [ ] 点击不同类型节点，验证详情显示正确
- [ ] 测试三种视图模式的切换
- [ ] 验证关联节点导航功能
- [ ] 测试侧边栏动画效果

### 2. UI测试
- [ ] 验证不同屏幕尺寸的显示效果
- [ ] 测试横屏模式
- [ ] 验证颜色和字体大小
- [ ] 测试滚动性能

### 3. 边界测试
- [ ] 节点无metadata时的显示
- [ ] 节点无故事时的显示
- [ ] 节点无关联时的显示
- [ ] 超长文本的处理

## 性能优化

### 1. 已实现
- ✅ 使用 `remember` 缓存渲染器
- ✅ 使用 `LaunchedEffect` 避免重复加载
- ✅ 列表使用 `items` 而非循环

### 2. 可优化
- 侧边栏内容懒加载
- 图片缓存（如果添加头像）
- 关联节点分页加载

## 总结

Android端知识星图侧边栏功能已完全实现，与Web端功能对齐。主要特性包括：

1. ✅ 完整的节点详情展示
2. ✅ 三种视图模式支持
3. ✅ 流畅的动画效果
4. ✅ 关联节点导航
5. ✅ 与Web端一致的UI设计

下一步可以添加节点编辑、删除等高级功能。
