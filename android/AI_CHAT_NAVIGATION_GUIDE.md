# Android AI 对话导航功能实现指南

## 概述

本文档说明 Android 端 AI 对话导航功能的完整实现，该功能与 Web 端保持一致，通过 WebSocket 接收导航建议。

## 功能说明

当用户在 AI 对话中发送消息时，后端会分析消息内容，并通过 WebSocket 返回导航建议，推荐用户跳转到相应的功能模块：

- **知识星图 (knowledge_graph)**: 查看人际关系、职业发展、教育背景
- **决策图谱 (decision)**: 进行决策模拟和分析
- **平行人生 (parallel_life)**: 模拟不同选择的未来
- **继续对话 (chat)**: 信息不足时建议继续对话

## 实现架构

```
用户发送消息
    ↓
WebSocket 连接
    ↓
后端分析消息
    ↓
返回 navigation 消息
    ↓
WebSocketClient 接收
    ↓
ChatViewModel 解析
    ↓
UI 显示导航卡片
    ↓
用户点击导航
    ↓
跳转到目标模块
```

## 核心代码

### 1. WebSocket 消息处理

**文件**: `android/app/src/main/java/com/lifeswarm/android/data/remote/WebSocketClient.kt`

```kotlin
interface ChatSocketHandlers {
    fun onNavigation(navData: Map<String, Any>) {}
    // ... 其他回调
}

// 在 WebSocketListener.onMessage 中
"navigation" -> {
    try {
        val fullMessage = gson.fromJson(text, Map::class.java) as Map<String, Any>
        handlers.onNavigation(fullMessage)
    } catch (e: Exception) {
        Log.e(TAG, "[WebSocket] 解析导航消息失败", e)
    }
}
```

### 2. ViewModel 状态管理

**文件**: `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatViewModel.kt`

```kotlin
// 在 openChatSocket 的 handlers 中
override fun onNavigation(navData: Map<String, Any>) {
    println("[ChatViewModel] 收到导航消息: $navData")
    
    try {
        // 后端返回的导航数据在 primary_route 对象中
        @Suppress("UNCHECKED_CAST")
        val primaryRoute = navData["primary_route"] as? Map<String, Any>
        
        if (primaryRoute != null) {
            val module = primaryRoute["module"] as? String ?: ""
            val viewMode = primaryRoute["view_mode"] as? String
            val reason = primaryRoute["reason"] as? String ?: ""
            val name = primaryRoute["name"] as? String ?: ""
            
            println("[ChatViewModel] 解析导航数据:")
            println("[ChatViewModel] - module: $module")
            println("[ChatViewModel] - viewMode: $viewMode")
            println("[ChatViewModel] - reason: $reason")
            
            if (module.isNotEmpty()) {
                val suggestion = RouteSuggestion(
                    recommendedModule = module,
                    recommendedView = viewMode,
                    reason = reason
                )
                
                _uiState.update {
                    it.copy(routeSuggestion = suggestion)
                }
                
                println("[ChatViewModel] ✅ 导航建议已更新到 UI")
            }
        }
    } catch (e: Exception) {
        println("[ChatViewModel] ❌ 解析导航消息失败: ${e.message}")
        e.printStackTrace()
    }
}
```

### 3. UI 显示和交互

**文件**: `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatScreen.kt`

```kotlin
// 在 ChatScreen 中
if (routeSuggestion != null) {
    RouteSuggestionCard(
        suggestion = routeSuggestion,
        onNavigate = {
            // 点击卡片跳转到推荐模块
            when (routeSuggestion.recommendedModule) {
                "knowledge_graph" -> onNavigateToKnowledgeGraph(...)
                "decision" -> onNavigateToDecision()
                "parallel_life" -> onNavigateToParallelLife()
            }
        },
        onDismiss = {
            // 点击"不跳转"按钮
            viewModel.dismissRouteSuggestion()
        }
    )
}
```

### 4. "不跳转"功能实现

**文件**: `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatViewModel.kt`

当用户点击"不跳转"按钮时，执行以下步骤：

```kotlin
fun dismissRouteSuggestion() {
    // 1. 隐藏导航建议
    _uiState.update { it.copy(routeSuggestion = null) }
    
    // 2. 获取原始问题
    val originalQuestion = _uiState.value.lastUserMessage
    
    // 3. 关闭之前的 WebSocket 连接
    webSocketClient?.disconnect()
    
    // 4. 发送特殊消息让 AI 重新回答
    val specialMessage = "[用户选择不跳转] 请直接回答以下问题，不要建议跳转：$originalQuestion"
    
    // 5. 重新打开 WebSocket 连接
    // 6. AI 会重新生成不带导航的回答
    // 7. 在新的 onNavigation 中忽略导航建议
}
```

**关键点**：
- 发送的消息格式：`[用户选择不跳转] 请直接回答以下问题，不要建议跳转：${原问题}`
- 后端识别这个特殊格式，不再返回导航建议
- 在新的 WebSocket handlers 中忽略 `navigation` 消息

### 5. UI 显示（旧版本，已废弃）

**文件**: `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatScreen.kt`

```kotlin
// 在 ChatScreen 中
val routeSuggestion = uiState.routeSuggestion

if (routeSuggestion != null) {
    RouteSuggestionCard(
        suggestion = routeSuggestion,
        isRouting = uiState.isRouting,
        onNavigate = {
            when (routeSuggestion.recommendedModule) {
                "knowledge_graph" -> {
                    onNavigateToKnowledgeGraph(
                        uiState.lastUserMessage,
                        routeSuggestion.recommendedView
                    )
                }
                "decision" -> {
                    onNavigateToDecision(uiState.lastUserMessage)
                }
                "parallel_life" -> {
                    onNavigateToParallelLife(uiState.lastUserMessage)
                }
            }
        }
    )
}
```

## 数据模型

### Navigation 消息格式（实际后端返回）

后端通过 WebSocket 返回的消息：

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

**Android 端解析逻辑**：
```kotlin
val primaryRoute = navData["primary_route"] as? Map<String, Any>
val module = primaryRoute["module"] as? String ?: ""
val viewMode = primaryRoute["view_mode"] as? String
val reason = primaryRoute["reason"] as? String ?: ""
```

### RouteSuggestion 数据类

```kotlin
data class RouteSuggestion(
    val recommendedModule: String,      // 推荐的模块
    val recommendedView: String?,       // 推荐的视图（可选）
    val reason: String                  // 推荐理由
)
```

## 触发导航的消息示例

### 知识星图

| 消息 | 推荐视图 |
|------|---------|
| "我现在掌握了哪些技能" | career (职业发展) |
| "我认识哪些人" | people (人际关系) |
| "我的教育背景" | education (升学规划) |

### 决策图谱

- "帮我做个决策"
- "我该选择哪个工作"
- "帮我分析一下选择"

### 平行人生

- "如果我选择了另一条路"
- "模拟一下未来"

## 与 Web 端的对比

| 方面 | Web 端 | Android 端 |
|------|--------|-----------|
| 数据来源 | WebSocket `navigation` 消息 | WebSocket `navigation` 消息 ✅ |
| HTTP API | 不使用 | 不使用 ✅ |
| 消息解析 | `chat.ts` | `WebSocketClient.kt` ✅ |
| 状态管理 | React State | Kotlin StateFlow ✅ |
| UI 组件 | React Component | Jetpack Compose ✅ |
| 导航方式 | React Router | Navigation Compose ✅ |

## 测试方法

### 1. 启动应用并登录

确保使用测试账号 `test_user_001` 登录。

### 2. 进入 AI 对话

点击"AI 核心"进入对话界面。

### 3. 发送测试消息

发送："我现在掌握了哪些技能"

### 4. 观察日志

```bash
adb logcat | grep -E "WebSocket|ChatViewModel|ChatScreen"
```

预期看到：
```
[WebSocket] 收到消息: type=navigation
[ChatViewModel] 收到导航消息
[ChatViewModel] ✅ 导航建议已更新到 UI
[ChatScreen] 路由建议状态: 有建议 (knowledge_graph)
```

### 5. 验证 UI

- 应该看到导航建议卡片
- 卡片显示推荐模块和理由
- 有"前往知识星图"按钮

### 6. 测试导航

点击导航按钮，应该跳转到知识星图页面。

## 常见问题

### Q: 为什么不使用 HTTP API？

A: 参考 Web 端实现，导航建议是通过 WebSocket 的 `navigation` 消息返回的，不是单独的 HTTP API。这样可以在对话流程中实时返回导航建议，无需额外的 API 调用。

### Q: 如果没有收到导航消息怎么办？

A: 检查以下几点：
1. WebSocket 连接是否正常
2. 后端服务是否正常运行
3. 消息内容是否足够触发导航逻辑
4. 查看后端日志确认是否返回了 navigation 消息

### Q: 导航建议何时显示？

A: 当后端分析用户消息后，如果判断需要导航，会通过 WebSocket 发送 `navigation` 消息。Android 端接收到消息后立即显示导航卡片。

### Q: 可以自定义导航逻辑吗？

A: 导航逻辑由后端 AI 决定，前端只负责接收和显示。如需修改导航逻辑，需要在后端调整。

## 代码变更总结

### 新增功能

1. ✅ WebSocket `navigation` 消息处理
2. ✅ ChatViewModel 导航状态管理
3. ✅ UI 导航卡片显示和交互

### 移除代码

1. ❌ `ChatRepository.analyzeRoute()` - HTTP API 调用
2. ❌ `ChatViewModel.analyzeRoute()` - 路由分析函数
3. ❌ `ApiService.analyzeRoute()` - API 接口定义（已注释）

### 保留代码

- `RouteAnalysisRequest` 和 `RouteAnalysisResponse` 数据类（已标记为废弃）
- `RouteSuggestion` 数据类（继续使用）

## 相关文件

- `android/app/src/main/java/com/lifeswarm/android/data/remote/WebSocketClient.kt`
- `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatViewModel.kt`
- `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatScreen.kt`
- `android/app/src/main/java/com/lifeswarm/android/data/repository/ChatRepository.kt`
- `android/app/src/main/java/com/lifeswarm/android/data/remote/ApiClient.kt`
- `web/src/services/chat.ts` (Web 端参考)

## 下一步

功能已完成，可以进行以下测试：

1. ✅ 单元测试：验证消息解析逻辑
2. ✅ 集成测试：验证 WebSocket 消息处理
3. ✅ UI 测试：验证导航卡片显示和交互
4. ✅ 端到端测试：验证完整的导航流程

## 维护建议

1. 保持与 Web 端的实现一致
2. 定期检查后端 API 变更
3. 添加更多日志以便调试
4. 考虑添加导航分析统计
