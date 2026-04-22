# 知识星图JSON解析错误修复

## 问题描述
知识星图功能无法显示，出现错误：
```
java.lang.IllegalStateException: Expected BEGIN_OBJECT but was STRING 
at line 1 column 380 path $.data.nodes[1].stories[0]
```

## 根本原因
后端返回的 `stories` 字段是字符串数组（`List<String>`），但Android端的数据模型定义为对象数组（`List<NodeStory>`），导致JSON解析失败。

## 修复方案

### 1. 修改KnowledgeGraphNode数据模型
**文件**: `android/app/src/main/java/com/lifeswarm/android/data/model/KnowledgeGraphModels.kt`

#### 修改前
```kotlin
data class KnowledgeGraphNode(
    @SerializedName("id") val id: String,
    @SerializedName("name") val name: String,
    @SerializedName("type") val type: String,
    @SerializedName("stories") val stories: List<NodeStory>? = null,
    // ...
)
```

#### 修改后
```kotlin
data class KnowledgeGraphNode(
    @SerializedName("id") val id: String = "",
    @SerializedName("name") val name: String = "",
    @SerializedName("type") val type: String = "",
    @SerializedName("stories") val stories: List<String>? = null,  // 改为字符串列表
    @SerializedName("description") val description: String? = null,  // 添加description字段
    // ...
)
```

**关键变化**：
1. ✅ `stories` 从 `List<NodeStory>` 改为 `List<String>`
2. ✅ 添加 `description` 字段
3. ✅ 所有必需字段添加默认值

### 2. 修改KnowledgeGraphLink数据模型
```kotlin
// 修改前
data class KnowledgeGraphLink(
    @SerializedName("source") val source: String,
    @SerializedName("target") val target: String,
    @SerializedName("type") val type: String,
    // ...
)

// 修改后
data class KnowledgeGraphLink(
    @SerializedName("source") val source: String = "",
    @SerializedName("target") val target: String = "",
    @SerializedName("type") val type: String = "",
    // ...
)
```

### 3. 修改KnowledgeGraphView数据模型
```kotlin
// 修改前
data class KnowledgeGraphView(
    @SerializedName("nodes") val nodes: List<KnowledgeGraphNode>,
    @SerializedName("links") val links: List<KnowledgeGraphLink>,
    // ...
)

// 修改后
data class KnowledgeGraphView(
    @SerializedName("nodes") val nodes: List<KnowledgeGraphNode> = emptyList(),
    @SerializedName("links") val links: List<KnowledgeGraphLink> = emptyList(),
    // ...
)
```

### 4. 更新NodeDetailPanel使用stories的方式
**文件**: `android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/NodeDetailPanel.kt`

#### 修改前
```kotlin
stories?.forEach { story ->
    if (story.content != description) {
        StoryCard(story.content)
    }
}
```

#### 修改后
```kotlin
stories?.forEach { story ->
    if (story != description) {
        StoryCard(story)  // 直接使用字符串
    }
}
```

## 后端数据格式

### 实际返回格式
```json
{
  "nodes": [
    {
      "id": "node_1",
      "name": "张三",
      "type": "person",
      "stories": [
        "大学同学，一起找工作",
        "经常一起讨论技术问题"
      ],
      "description": "我的好朋友",
      "metadata": {
        "age": 25,
        "occupation": "工程师"
      }
    }
  ],
  "links": [
    {
      "source": "node_1",
      "target": "node_2",
      "type": "friend"
    }
  ]
}
```

### 关键字段说明
- **stories**: 字符串数组，每个元素是一个故事文本
- **description**: 节点的主要描述
- **metadata**: 节点的元数据，可以包含任意键值对

## 数据模型对比

| 字段 | Web端 | Android端（修复前） | Android端（修复后） |
|------|-------|-------------------|-------------------|
| stories | `string[]` | `NodeStory[]` | `string[]` ✅ |
| description | `string?` | 无 | `string?` ✅ |
| id | `string` | `string` | `string` (默认值) ✅ |
| name | `string` | `string` | `string` (默认值) ✅ |
| type | `string` | `string` | `string` (默认值) ✅ |

## 测试验证

### 1. 编译测试
```bash
cd android
./gradlew clean
./gradlew assembleDebug
```

### 2. 功能测试
- [ ] 打开知识星图页面
- [ ] 切换到人际关系视图
- [ ] 验证节点正常显示
- [ ] 点击节点查看详情
- [ ] 验证故事列表正常显示
- [ ] 切换到职业发展视图
- [ ] 切换到升学规划视图

### 3. 边界测试
- [ ] 节点无stories字段
- [ ] stories为空数组
- [ ] 节点无description字段
- [ ] metadata为空

## 预期结果

修复后应该能够：
1. ✅ 正常加载知识图谱数据
2. ✅ 显示3D节点和连线
3. ✅ 点击节点显示侧边栏
4. ✅ 侧边栏正确显示故事列表
5. ✅ 侧边栏正确显示描述信息
6. ✅ 关联节点导航正常工作

## 注意事项

### 1. NodeStory类保留
虽然当前不使用 `NodeStory` 类，但保留它以备将来后端可能返回对象格式：
```kotlin
// 保留但当前未使用
data class NodeStory(
    @SerializedName("story_id") val storyId: String,
    @SerializedName("title") val title: String,
    @SerializedName("content") val content: String,
    @SerializedName("timestamp") val timestamp: String,
    @SerializedName("emotion") val emotion: String? = null
)
```

### 2. 向后兼容
如果将来后端改为返回对象格式，可以：
1. 创建自定义的Gson TypeAdapter
2. 同时支持字符串和对象格式
3. 或者创建两个不同的字段

### 3. 默认值策略
所有必需字段都添加了默认值，确保：
- JSON缺少字段时不会崩溃
- 可以创建空对象用于测试
- 提高代码的健壮性

## 相关文件

- `android/app/src/main/java/com/lifeswarm/android/data/model/KnowledgeGraphModels.kt`
- `android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/NodeDetailPanel.kt`
- `android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/KnowledgeGraphScreen.kt`

## 总结

通过将 `stories` 字段从对象数组改为字符串数组，并为所有必需字段添加默认值，解决了JSON解析错误。现在Android端的数据模型与后端返回的实际格式完全匹配。
