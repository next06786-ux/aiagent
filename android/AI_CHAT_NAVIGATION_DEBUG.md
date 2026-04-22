# AI 对话导航功能调试文档

## 功能概述

AI 对话导航功能允许 AI 根据用户的消息内容，智能推荐跳转到相应的功能模块（如知识星图、决策图谱等）。

## 实现方式

### Web 端实现
- 通过 WebSocket 消息获取导航建议
- 消息类型为 `navigation`
- 不使用单独的 HTTP API

### Android 端实现（已完成 ✅）
- ✅ 通过 WebSocket 的 `navigation` 消息类型接收导航建议
- ✅ 在 `WebSocketClient.kt` 中处理 `navigation` 消息
- ✅ 在 `ChatViewModel.kt` 中接收并解析导航数据
- ✅ 在 `ChatScreen.kt` 中显示导航建议卡片
- ✅ 移除了不存在的 HTTP API `/api/v5/future-os/route`

## 代码实现

### 1. WebSocket 客户端 (WebSocketClient.kt)

```kotlin
interface ChatSocketHandlers {
    fun onStart(sessionId: String) {}
    fun onProgress(progress: String) {}
    fun onThinking(thinking: String) {}
    fun onAnswer(answer: String) {}
    fun onNavigation(navData: Map<String, Any>) {}  // 导航消息处理
    fun onDone() {}
    fun onError(message: String) {}
}

// 在 onMessage 中处理 navigation 消息
"navigation" -> {
    try {
        @Suppress("UNCHECKED_CAST")
        val fullMessage = gson.fromJson(text, Map::class.java) as Map<String, Any>
        Log.d(TAG, "[WebSocket] 导航消息详情: $fullMessage")
        handlers.onNavigation(fullMessage)
    } catch (e: Exception) {
        Log.e(TAG, "[WebSocket] 解析导航消息失败", e)
    }
}
```

### 2. ChatViewModel (ChatViewModel.kt)

```kotlin
override fun onNavigation(navData: Map<String, Any>) {
    println("[ChatViewModel] 收到导航消息: $navData")
    
    try {
        val recommendedModule = navData["recommended_module"] as? String ?: ""
        val recommendedView = navData["recommended_view"] as? String
        val reason = navData["reason"] as? String ?: ""
        
        if (recommendedModule.isNotEmpty()) {
            val suggestion = RouteSuggestion(
                recommendedModule = recommendedModule,
                recommendedView = recommendedView,
                reason = reason
            )
            
            _uiState.update {
                it.copy(routeSuggestion = suggestion)
            }
            
            println("[ChatViewModel] ✅ 导航建议已更新到 UI")
        }
    } catch (e: Exception) {
        println("[ChatViewModel] ❌ 解析导航消息失败: ${e.message}")
        e.printStackTrace()
    }
}
```

### 3. UI 显示 (ChatScreen.kt)

导航建议卡片会在收到 `navigation` 消息后自动显示，包含：
- 推荐的模块名称
- 推荐理由
- "100% 匹配"标签
- 导航按钮（点击跳转）
- "不跳转"按钮（点击后 AI 重新生成回答）

**"不跳转"功能实现**：

当用户点击"不跳转"按钮时：
1. 隐藏导航建议卡片
2. 发送特殊消息：`[用户选择不跳转] 请直接回答以下问题，不要建议跳转：${原问题}`
3. 重新打开 WebSocket 连接
4. AI 重新生成回答（不带导航建议）

```kotlin
fun dismissRouteSuggestion() {
    // 隐藏导航建议
    _uiState.update { it.copy(routeSuggestion = null) }
    
    // 获取原始问题
    val originalQuestion = _uiState.value.lastUserMessage
    
    // 发送特殊消息让 AI 重新回答
    val specialMessage = "[用户选择不跳转] 请直接回答以下问题，不要建议跳转：$originalQuestion"
    
    // 重新打开 WebSocket 连接
    // AI 会重新生成不带导航的回答
}
```

## 触发导航的示例消息

根据 Web 端的实现，以下消息会触发导航：

1. **知识星图 (knowledge_graph)**
   - "我现在掌握了哪些技能"
   - "我认识哪些人"
   - "我的人际关系网络"
   - "我的职业发展路径"
   - "我的教育背景"

2. **决策图谱 (decision)**
   - "帮我做个决策"
   - "我该选择哪个工作"
   - "帮我分析一下选择"

3. **平行人生 (parallel_life)**
   - "如果我选择了另一条路"
   - "模拟一下未来"

## 调试方法

### 1. 查看 WebSocket 日志

```bash
adb logcat | grep -E "WebSocketClient|ChatViewModel|ChatScreen"
```

关键日志：
- `[WebSocket] 收到消息: type=navigation`
- `[ChatViewModel] 收到导航消息`
- `[ChatViewModel] ✅ 导航建议已更新到 UI`
- `[ChatScreen] 路由建议状态: 有建议`

### 2. 预期的日志流程

```
[WebSocket] 连接已打开，发送消息
[WebSocket] 收到消息: type=start
[WebSocket] 收到消息: type=progress
[WebSocket] 收到消息: type=navigation, contentLength=93
[WebSocket] 导航消息详情: {type=navigation, recommended_module=knowledge_graph, ...}
[ChatViewModel] 收到导航消息: {recommended_module=knowledge_graph, ...}
[ChatViewModel] 解析导航数据:
[ChatViewModel] - recommendedModule: knowledge_graph
[ChatViewModel] - recommendedView: people
[ChatViewModel] - reason: 用户询问技能相关问题
[ChatViewModel] ✅ 导航建议已更新到 UI
[ChatScreen] 路由建议状态: 有建议 (knowledge_graph)
[ChatScreen] 显示路由建议卡片
```

## 已移除的代码

以下代码已被移除或注释，因为后端不提供对应的 HTTP API：

1. `ChatRepository.analyzeRoute()` - HTTP API 调用（已移除）
2. `ChatViewModel.analyzeRoute()` - 路由分析函数（已移除）
3. `ApiService.analyzeRoute()` - API 接口定义（已注释）

## 数据结构

### Navigation 消息格式（实际后端返回）

后端通过 WebSocket 返回的完整消息结构：

```json
{
  "type": "navigation",
  "content": "我注意到你可能想要查看【知识星图】查看你的知识图谱...",
  "routes": [
    {
      "module": "knowledge_graph",
      "confidence": 1.0,
      "reason": "用户明确指令'导航到知识星图'，完全匹配knowledge_graph模块功能",
      "view_mode": null,
      "name": "知识星图",
      "path": "/knowledge-graph",
      "description": "查看你的知识图谱，包括人际关系网络、教育升学规划、职业发展路径"
    }
  ],
  "primary_route": {
    "module": "knowledge_graph",
    "confidence": 1.0,
    "reason": "用户明确指令'导航到知识星图'，完全匹配knowledge_graph模块功能",
    "view_mode": null,
    "name": "知识星图",
    "path": "/knowledge-graph",
    "description": "查看你的知识图谱，包括人际关系网络、教育升学规划、职业发展路径"
  },
  "allow_continue": true
}
```

**重要字段说明**：
- `primary_route`: 主要推荐的路由（Android 端使用这个对象）
- `primary_route.module`: 推荐的模块名称（knowledge_graph, decision, parallel_life）
- `primary_route.view_mode`: 推荐的视图模式（people, career, education，可选）
- `primary_route.reason`: 推荐理由
- `primary_route.name`: 模块显示名称
- `routes`: 所有可能的路由列表
- `allow_continue`: 是否允许继续对话

### RouteSuggestion 数据类

```kotlin
data class RouteSuggestion(
    val recommendedModule: String,      // 推荐的模块: knowledge_graph, decision, parallel_life, chat
    val recommendedView: String?,       // 推荐的视图: people, career, education (仅知识星图)
    val reason: String                  // 推荐理由
)
```

**解析逻辑**：
```kotlin
val primaryRoute = navData["primary_route"] as? Map<String, Any>
val module = primaryRoute["module"] as? String ?: ""
val viewMode = primaryRoute["view_mode"] as? String
val reason = primaryRoute["reason"] as? String ?: ""
```

## 测试步骤

1. 启动 Android 应用
2. 进入 AI 对话界面
3. 发送消息："我现在掌握了哪些技能"
4. 观察日志，确认收到 `navigation` 消息并正确解析 `primary_route`
5. 确认 UI 显示导航建议卡片
6. **测试跳转功能**：点击导航卡片，确认跳转到知识星图页面
7. **测试不跳转功能**：
   - 再次发送相同消息触发导航
   - 点击"不跳转"按钮
   - 观察 AI 重新生成回答（不带导航建议）
   - 确认日志显示：`[用户选择不跳转] 请直接回答以下问题...`

5. 确认 UI 显示导航建议卡片
6. 点击"前往知识星图"按钮
7. 确认成功跳转到知识星图页面

## 故障排查

### 问题：没有收到导航消息

**检查项：**
1. WebSocket 连接是否成功建立
2. 后端是否返回 `navigation` 消息（查看 Web 端日志对比）
3. 消息内容是否触发导航逻辑

**解决方案：**
- 检查 WebSocket 连接日志
- 对比 Web 端相同消息的返回结果
- 确认后端服务正常运行

### 问题：收到导航消息但 UI 不显示

**检查项：**
1. `ChatViewModel.onNavigation()` 是否被调用
2. `routeSuggestion` 状态是否更新
3. `ChatScreen` 是否正确观察状态变化
4. 导航卡片的显示条件是否满足

**解决方案：**
- 查看 `[ChatViewModel] ✅ 导航建议已更新到 UI` 日志
- 检查 `_uiState.update` 是否执行
- 确认 Compose 状态订阅正常

### 问题：点击导航按钮无反应

**检查项：**
1. `onNavigate` 回调是否正确传递
2. 导航逻辑中的模块名称匹配是否正确
3. 导航目标页面是否正确配置

**解决方案：**
- 查看 `[ChatScreen] 用户点击导航按钮` 日志
- 检查 `when (routeSuggestion.recommendedModule)` 分支
- 确认导航路由配置正确

## 与 Web 端的对比

| 特性 | Web 端 | Android 端 |
|------|--------|-----------|
| 导航数据来源 | WebSocket `navigation` 消息 | WebSocket `navigation` 消息 |
| HTTP API | 不使用 | 不使用（已移除） |
| 消息处理 | `chat.ts` 的 `onNavigation` | `ChatViewModel` 的 `onNavigation` |
| UI 显示 | React 组件 | Compose `RouteSuggestionCard` |
| 导航触发 | 路由跳转 | Navigation Compose |

## 参考文件

- `android/app/src/main/java/com/lifeswarm/android/data/remote/WebSocketClient.kt`
- `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatViewModel.kt`
- `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatScreen.kt`
- `android/app/src/main/java/com/lifeswarm/android/data/repository/ChatRepository.kt`
- `web/src/services/chat.ts` (Web 端参考实现)

## 总结

Android 端的 AI 对话导航功能现已完全对齐 Web 端实现：
- ✅ 使用 WebSocket 接收导航建议
- ✅ 移除了不存在的 HTTP API
- ✅ 正确解析和显示导航消息
- ✅ 支持跳转到知识星图、决策图谱等模块

测试时发送类似"我现在掌握了哪些技能"的消息，应该能看到导航建议卡片并成功跳转。
