# 知识星图点击节点崩溃修复

## 问题描述
Android客户端知识星图功能进入后，点击任意节点时应用崩溃。

## 可能的原因

### 1. 空值访问
- 节点的某些字段为空或空字符串
- metadata为null或空Map
- stories为null或空列表

### 2. 类型转换错误
- metadata中的值类型不匹配
- 尝试将Any类型转换为String时失败

### 3. Compose渲染错误
- 某些UI组件接收到无效数据
- 字符串为空导致UI崩溃

## 修复方案

### 1. 添加空值检查（NodeDetailPanel.kt）

#### 节点名称检查
```kotlin
// 修改前
Text(node.name, ...)

// 修改后
Text(
    node.name.takeIf { it.isNotEmpty() } ?: "未命名节点",
    ...
)
```

#### 节点类型检查
```kotlin
// 修改前
Surface(...) {
    Text(node.type, ...)
}

// 修改后
if (node.type.isNotEmpty()) {
    Surface(...) {
        Text(node.type, ...)
    }
}
```

#### metadata检查
```kotlin
// 修改前
node.metadata?.let { metadata ->
    metadata.forEach { (key, value) ->
        Text(value.toString(), ...)
    }
}

// 修改后
node.metadata?.let { metadata ->
    if (metadata.isNotEmpty()) {
        metadata.forEach { (key, value) ->
            if (key != "description") {
                Text(value?.toString() ?: "", ...)
            }
        }
    }
}
```

#### stories检查
```kotlin
// 修改前
stories?.forEach { story ->
    StoryCard(story)
}

// 修改后
stories?.forEach { story ->
    if (story.isNotEmpty() && story != description) {
        StoryCard(story)
    }
}
```

#### description检查
```kotlin
// 修改前
description?.let {
    StoryCard(it)
}

// 修改后
description?.let {
    if (it.isNotEmpty()) {
        StoryCard(it)
    }
}
```

### 2. 添加try-catch保护

在NodeDetailPanel主函数中添加错误处理：

```kotlin
try {
    when (viewMode) {
        "people" -> PeopleNodeDetail(node, graph, onNavigateToNode)
        "career" -> CareerNodeDetail(node, graph, onNavigateToNode)
        "education" -> EducationNodeDetail(node, graph, onNavigateToNode)
        else -> DefaultNodeDetail(node)
    }
} catch (e: Exception) {
    // 显示错误信息和基本节点信息
    Column {
        Icon(Icons.Default.Warning, ...)
        Text("显示节点详情时出错")
        Text(e.message ?: "未知错误")
        DefaultNodeDetail(node)  // 后备显示
    }
}
```

### 3. 所有视图的修复

#### PeopleNodeDetail
- ✅ 节点名称空值检查
- ✅ 节点类型空值检查
- ✅ metadata空值和空Map检查
- ✅ metadata值的空值检查
- ✅ stories空值和空字符串检查
- ✅ description空值和空字符串检查

#### CareerNodeDetail
- ✅ 节点名称空值检查
- ✅ 节点类型空值检查
- ✅ description从两个来源获取（node.description 或 metadata）
- ✅ description空值和空字符串检查
- ✅ metadata mastery字段的空值检查

#### EducationNodeDetail
- ✅ 节点名称空值检查
- ✅ 节点类型空值检查
- ✅ metadata空值和空Map检查
- ✅ metadata值的空值检查
- ✅ description空值和空字符串检查

#### DefaultNodeDetail
- ✅ 节点名称空值检查
- ✅ 节点ID空值检查
- ✅ 节点类型空值检查

## 修改的文件

1. **android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/NodeDetailPanel.kt**
   - 所有Composable函数添加空值检查
   - 主函数添加try-catch保护
   - 所有字符串访问添加空值处理

## 调试方法

### 1. 查看Logcat日志
```bash
adb logcat | grep -E "KnowledgeGraph|NodeDetailPanel|AndroidRuntime"
```

### 2. 关键日志标签
- `KnowledgeGraph` - 节点点击事件
- `NodeDetailPanel` - 侧边栏渲染
- `AndroidRuntime` - 崩溃堆栈

### 3. 添加调试日志
在NodeDetailPanel中添加：
```kotlin
Log.d("NodeDetailPanel", "显示节点: ${node.name}, 类型: ${node.type}")
Log.d("NodeDetailPanel", "metadata: ${node.metadata}")
Log.d("NodeDetailPanel", "stories: ${node.stories}")
```

## 测试清单

### 基本测试
- [ ] 点击有完整数据的节点
- [ ] 点击只有基本信息的节点
- [ ] 点击没有metadata的节点
- [ ] 点击没有stories的节点
- [ ] 点击没有description的节点

### 边界测试
- [ ] 节点名称为空字符串
- [ ] 节点类型为空字符串
- [ ] metadata为空Map
- [ ] metadata值为null
- [ ] stories为空数组
- [ ] stories包含空字符串
- [ ] description为空字符串

### 视图切换测试
- [ ] 人际关系视图 - 点击节点
- [ ] 职业发展视图 - 点击节点
- [ ] 升学规划视图 - 点击节点
- [ ] 切换视图后点击节点

### 交互测试
- [ ] 点击关联节点导航
- [ ] 关闭侧边栏
- [ ] 点击删除按钮
- [ ] 滚动侧边栏内容

## 预期结果

修复后应该能够：
1. ✅ 点击任何节点不崩溃
2. ✅ 正确显示节点信息
3. ✅ 空字段显示默认值或隐藏
4. ✅ 即使数据不完整也能显示基本信息
5. ✅ 错误时显示友好的错误提示

## 后备方案

如果仍然崩溃，可以：

### 方案1：简化侧边栏
暂时只显示基本信息：
```kotlin
when (viewMode) {
    else -> DefaultNodeDetail(node)  // 所有视图都用默认显示
}
```

### 方案2：禁用侧边栏
注释掉NodeDetailPanel的调用：
```kotlin
// NodeDetailPanel(...)  // 暂时禁用
```

### 方案3：使用旧的底部卡片
恢复之前的简单信息卡片显示。

## 注意事项

1. **Compose不支持try-catch包裹Composable**
   - 只能在Composable函数内部使用try-catch
   - 不能在item {}外部包裹try-catch

2. **空字符串检查**
   - 使用 `isNotEmpty()` 而不是 `!= ""`
   - 使用 `takeIf { it.isNotEmpty() }` 提供默认值

3. **类型安全**
   - metadata的值是Any类型，需要安全转换
   - 使用 `?.toString()` 而不是 `.toString()`

4. **性能考虑**
   - 空值检查不会影响性能
   - try-catch只在异常时有性能开销

## 总结

通过添加全面的空值检查和错误处理，确保即使数据不完整或格式不正确，侧边栏也能正常显示或优雅降级，不会导致应用崩溃。
