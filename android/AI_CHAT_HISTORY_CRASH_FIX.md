# AI对话历史功能崩溃修复

## 问题描述
在Android客户端的AI对话功能中，点击"历史对话"按钮时系统崩溃。

## 问题原因

### 根本原因
`ChatViewModel`继承自`AndroidViewModel`，需要`Application`参数才能正确实例化。但在以下两个地方使用了不正确的创建方式：

1. **ChatScreen.kt**：使用默认参数`viewModel: ChatViewModel = viewModel()`
2. **AppNavigation.kt (conversation-list路由)**：直接调用`viewModel()`创建实例

这两种方式都无法提供必需的`Application`参数，导致实例化失败并崩溃。

### 第二个问题：NullPointerException
后端返回的某些会话数据中，`updatedAt`或`createdAt`字段为`null`，导致Compose的`Text`组件崩溃。

错误信息：
```
java.lang.NullPointerException: Attempt to invoke virtual method 'int java.lang.String.length()' on a null object reference
at androidx.compose.ui.text.platform.AndroidParagraphHelper_androidKt.createCharSequence
```

### ChatViewModel构造函数
```kotlin
class ChatViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application as LifeSwarmApp
    private val chatRepository = app.chatRepository
    private val authStorage = app.authStorage
    // ...
}
```

## 解决方案

### 1. 创建ChatViewModelFactory

创建了`ChatViewModelFactory.kt`来正确实例化`ChatViewModel`：

```kotlin
class ChatViewModelFactory(
    private val application: Application
) : ViewModelProvider.Factory {
    
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ChatViewModel::class.java)) {
            return ChatViewModel(application) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
    }
}
```

### 2. 修改AppNavigation.kt

#### chat路由
使用Factory创建ViewModel实例：

```kotlin
composable("chat") {
    val chatViewModel: ChatViewModel = viewModel(
        factory = ChatViewModelFactory(application)
    )
    
    ChatScreen(
        viewModel = chatViewModel,
        // ... 其他参数
    )
}
```

#### conversation-list路由
从chat页面共享ViewModel实例：

```kotlin
composable("conversation-list") {
    val chatViewModel: ChatViewModel = viewModel(
        viewModelStoreOwner = navController.getBackStackEntry("chat")
    )
    
    ConversationListScreen(
        conversations = uiState.conversations,
        // ... 其他参数
    )
}
```

### 3. 修改ChatScreen.kt

移除默认参数，改为必需参数：

```kotlin
@Composable
fun ChatScreen(
    viewModel: ChatViewModel,  // 改为必需参数
    onNavigateBack: () -> Unit,
    // ... 其他参数
) {
    // ...
}
```

### 4. 修复NullPointerException

#### 为ConversationItem添加默认值
```kotlin
data class ConversationItem(
    @SerializedName("conversation_id") val conversationId: String = "",
    @SerializedName("title") val title: String? = null,
    @SerializedName("created_at") val createdAt: String = "",
    @SerializedName("updated_at") val updatedAt: String = ""
)
```

#### 在UI层添加空值检查
```kotlin
Text(
    text = conversation.title?.takeIf { it.isNotEmpty() } ?: "未命名会话",
    // ...
)

val formattedTime = remember(conversation.updatedAt) {
    val timeStr = conversation.updatedAt.takeIf { it.isNotEmpty() } ?: return@remember "未知时间"
    try {
        formatTime(timeStr)
    } catch (e: Exception) {
        timeStr
    }
}
```

### 5. 实现加载历史会话功能

#### 在ChatViewModel中添加loadConversation方法
```kotlin
fun loadConversation(sessionId: String) {
    viewModelScope.launch {
        try {
            // 断开当前WebSocket连接
            webSocketClient?.disconnect()
            webSocketClient = null
            
            // 获取会话消息
            val messages = chatRepository.getConversationMessages(currentUserId, sessionId)
            
            // 转换为ChatMessage格式
            val chatMessages = messages.map { msg ->
                ChatMessage(
                    id = msg.messageId,
                    role = msg.role,
                    content = msg.content,
                    timestamp = msg.timestamp
                )
            }
            
            // 更新状态
            _uiState.update {
                it.copy(
                    currentSessionId = sessionId,
                    messages = chatMessages,
                    error = "",
                    streamStatus = "",
                    routeSuggestion = null
                )
            }
        } catch (e: Exception) {
            _uiState.update {
                it.copy(
                    error = "加载会话失败: ${e.message}",
                    currentSessionId = sessionId,
                    messages = emptyList()
                )
            }
        }
    }
}
```

#### 在会话列表点击时调用
```kotlin
onConversationClick = { sessionId ->
    chatViewModel.loadConversation(sessionId)
    navController.popBackStack()
}
```

## 修复效果

1. ✅ **chat页面**：使用Factory正确创建ViewModel实例
2. ✅ **conversation-list页面**：共享chat页面的ViewModel实例
3. ✅ **数据一致性**：两个页面共享同一个ViewModel，会话列表数据保持同步
4. ✅ **避免崩溃**：所有ViewModel实例都通过正确的方式创建
5. ✅ **空值安全**：所有字段都有默认值，UI层有空值检查
6. ✅ **历史会话加载**：点击会话后可以查看历史消息

## 相关文件

- `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatViewModelFactory.kt` (新建)
- `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatScreen.kt` (修改)
- `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ChatViewModel.kt` (修改 - 添加loadConversation)
- `android/app/src/main/java/com/lifeswarm/android/presentation/chat/ConversationListScreen.kt` (修改 - 空值检查)
- `android/app/src/main/java/com/lifeswarm/android/presentation/navigation/AppNavigation.kt` (修改)
- `android/app/src/main/java/com/lifeswarm/android/data/model/ApiModels.kt` (修改 - 添加默认值)

## 测试建议

1. 打开AI对话页面
2. 点击右上角"历史对话"按钮
3. 验证页面正常打开，不崩溃
4. 验证会话列表正确显示
5. 点击任意会话，验证历史消息正确加载
6. 点击"新对话"按钮，验证功能正常
7. 返回聊天页面，验证状态保持一致
