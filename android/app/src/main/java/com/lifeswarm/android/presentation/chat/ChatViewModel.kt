package com.lifeswarm.android.presentation.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.lifeswarm.android.LifeSwarmApp
import com.lifeswarm.android.data.model.ChatSocketRequest
import com.lifeswarm.android.data.remote.WebSocketClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * 聊天 ViewModel - 对应 web/src/pages/AIChatPage.tsx 的状态管理
 */
class ChatViewModel(application: Application) : AndroidViewModel(application) {
    
    private val app = application as LifeSwarmApp
    private val chatRepository = app.chatRepository
    private val authStorage = app.authStorage
    
    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()
    
    private var webSocketClient: WebSocketClient? = null
    private var currentUserId: String = ""
    
    init {
        println("[ChatViewModel] ========== 初始化开始 ==========")
        loadUserId()
        loadConversations()
        println("[ChatViewModel] ========== 初始化完成 ==========")
    }
    
    private fun loadUserId() {
        viewModelScope.launch {
            try {
                println("[ChatViewModel] 开始加载用户ID")
                authStorage.userFlow.collect { user ->
                    currentUserId = user?.userId ?: ""
                    println("[ChatViewModel] 用户ID已更新: $currentUserId")
                }
            } catch (e: Exception) {
                println("[ChatViewModel] 加载用户ID失败: ${e.message}")
                e.printStackTrace()
            }
        }
    }
    
    private fun loadConversations() {
        viewModelScope.launch {
            try {
                println("[ChatViewModel] 开始加载会话列表")
                // 获取当前用户
                val user = authStorage.getUser()
                if (user != null) {
                    println("[ChatViewModel] 用户: ${user.userId}, 开始获取会话列表")
                    val conversations = chatRepository.listConversations(user.userId)
                    println("[ChatViewModel] 获取到 ${conversations.size} 个会话")
                    _uiState.update { it.copy(conversations = conversations) }
                } else {
                    println("[ChatViewModel] 用户未登录，跳过加载会话列表")
                }
            } catch (e: Exception) {
                println("[ChatViewModel] 加载会话列表失败: ${e.message}")
                e.printStackTrace()
                _uiState.update { it.copy(error = "加载会话列表失败: ${e.message}") }
            }
        }
    }
    
    fun updateInput(text: String) {
        println("[ChatViewModel] updateInput 被调用: '$text'")
        _uiState.update { 
            val newState = it.copy(input = text)
            println("[ChatViewModel] 状态已更新: input='${newState.input}'")
            newState
        }
    }
    
    fun startNewConversation() {
        webSocketClient?.disconnect()
        webSocketClient = null
        
        _uiState.update {
            it.copy(
                currentSessionId = "",
                messages = listOf(
                    ChatMessage(
                        id = "welcome_new",
                        role = "assistant",
                        content = "新对话已准备好。你可以先自由表达，我会帮你判断什么时候切到图谱或平行人生。",
                        timestamp = System.currentTimeMillis().toString()
                    )
                ),
                error = "",
                streamStatus = "",
                routeSuggestion = null
            )
        }
    }
    
    /**
     * 加载历史会话消息
     */
    fun loadConversation(sessionId: String) {
        viewModelScope.launch {
            try {
                println("[ChatViewModel] ========== 开始加载会话 ==========")
                println("[ChatViewModel] sessionId: '$sessionId'")
                println("[ChatViewModel] sessionId.length: ${sessionId.length}")
                println("[ChatViewModel] sessionId.isEmpty: ${sessionId.isEmpty()}")
                println("[ChatViewModel] currentUserId: '$currentUserId'")
                
                // 如果currentUserId为空，先获取用户信息
                if (currentUserId.isEmpty()) {
                    println("[ChatViewModel] currentUserId为空，先获取用户信息")
                    val user = authStorage.getUser()
                    currentUserId = user?.userId ?: ""
                    println("[ChatViewModel] 获取到userId: '$currentUserId'")
                }
                
                if (currentUserId.isEmpty()) {
                    println("[ChatViewModel] ❌ 用户未登录")
                    _uiState.update {
                        it.copy(error = "用户未登录")
                    }
                    return@launch
                }
                
                if (sessionId.isEmpty()) {
                    println("[ChatViewModel] ❌ sessionId为空")
                    _uiState.update {
                        it.copy(error = "会话ID为空")
                    }
                    return@launch
                }
                
                // 断开当前WebSocket连接
                println("[ChatViewModel] 断开WebSocket连接")
                webSocketClient?.disconnect()
                webSocketClient = null
                
                // 获取会话消息
                println("[ChatViewModel] 开始获取会话消息")
                println("[ChatViewModel]   userId: '$currentUserId'")
                println("[ChatViewModel]   sessionId: '$sessionId'")
                
                val messages = chatRepository.getConversationMessages(currentUserId, sessionId)
                println("[ChatViewModel] 获取到 ${messages.size} 条消息")
                
                // 打印前3条消息
                messages.take(3).forEachIndexed { index, msg ->
                    println("[ChatViewModel]   消息${index + 1}: role=${msg.role}, content=${msg.content.take(50)}")
                }
                
                // 转换为ChatMessage格式
                val chatMessages = messages.map { msg ->
                    ChatMessage(
                        id = msg.messageId.takeIf { it.isNotEmpty() } ?: "msg_${System.currentTimeMillis()}",
                        role = msg.role.takeIf { it.isNotEmpty() } ?: "assistant",
                        content = msg.content.takeIf { it.isNotEmpty() } ?: "",
                        timestamp = msg.timestamp.takeIf { it.isNotEmpty() } ?: System.currentTimeMillis().toString()
                    )
                }
                
                println("[ChatViewModel] 转换完成，准备更新状态")
                
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
                
                println("[ChatViewModel] ========== 会话加载完成 ==========")
            } catch (e: Exception) {
                println("[ChatViewModel] ❌ 加载会话失败: ${e.message}")
                e.printStackTrace()
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
    
    fun sendMessage() {
        val currentState = _uiState.value
        
        println("[ChatViewModel] sendMessage 被调用")
        println("[ChatViewModel] - input: '${currentState.input}'")
        println("[ChatViewModel] - isSending: ${currentState.isSending}")
        println("[ChatViewModel] - currentUserId: '$currentUserId'")
        
        if (currentState.input.isBlank()) {
            println("[ChatViewModel] ❌ 输入为空，取消发送")
            _uiState.update { it.copy(error = "请输入消息内容") }
            return
        }
        
        if (currentState.isSending) {
            println("[ChatViewModel] ❌ 正在发送中，取消重复发送")
            return
        }
        
        if (currentUserId.isEmpty()) {
            println("[ChatViewModel] ❌ 用户ID为空，取消发送")
            _uiState.update { it.copy(error = "用户未登录，请重新登录") }
            return
        }
        
        println("[ChatViewModel] ✅ 开始发送消息")
        
        val prompt = currentState.input.trim()
        val userMessage = ChatMessage(
            id = "user_${System.currentTimeMillis()}",
            role = "user",
            content = prompt,
            timestamp = System.currentTimeMillis().toString()
        )
        
        val assistantId = "assistant_${System.currentTimeMillis()}"
        val assistantMessage = ChatMessage(
            id = assistantId,
            role = "assistant",
            content = "",
            timestamp = System.currentTimeMillis().toString()
        )
        
        _uiState.update {
            it.copy(
                input = "",
                isSending = true,
                streamStatus = "正在连接 AI 核心...",
                messages = it.messages + listOf(userMessage, assistantMessage),
                lastUserMessage = prompt,
                error = "",
                routeSuggestion = null  // 清空之前的路由建议
            )
        }
        
        // 打开 WebSocket (导航建议会通过 WebSocket 的 navigation 消息返回)
        viewModelScope.launch {
            try {
                val request = ChatSocketRequest(
                    userId = currentUserId,
                    sessionId = currentState.currentSessionId.ifEmpty { "" },
                    message = prompt,
                    useRag = false
                )
                
                webSocketClient = chatRepository.openChatSocket(
                    request,
                    object : WebSocketClient.ChatSocketHandlers {
                        override fun onStart(sessionId: String) {
                            if (sessionId.isNotEmpty()) {
                                _uiState.update { state -> state.copy(currentSessionId = sessionId) }
                            }
                        }
                        
                        override fun onProgress(progress: String) {
                            _uiState.update { it.copy(streamStatus = progress) }
                        }
                        
                        override fun onThinking(thinking: String) {
                            _uiState.update { state ->
                                state.copy(
                                    messages = state.messages.map { msg ->
                                        if (msg.id == assistantId) {
                                            msg.copy(thinking = thinking)
                                        } else {
                                            msg
                                        }
                                    }
                                )
                            }
                        }
                        
                        override fun onAnswer(answer: String) {
                            _uiState.update { state ->
                                state.copy(
                                    messages = state.messages.map { msg ->
                                        if (msg.id == assistantId) {
                                            msg.copy(content = answer)
                                        } else {
                                            msg
                                        }
                                    }
                                )
                            }
                        }
                        
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
                                    println("[ChatViewModel] - name: $name")
                                    
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
                                    } else {
                                        println("[ChatViewModel] ⚠️ module 为空，跳过导航建议")
                                    }
                                } else {
                                    println("[ChatViewModel] ⚠️ primary_route 为空，跳过导航建议")
                                }
                            } catch (e: Exception) {
                                println("[ChatViewModel] ❌ 解析导航消息失败: ${e.message}")
                                e.printStackTrace()
                            }
                        }
                        
                        override fun onDone() {
                            _uiState.update {
                                it.copy(
                                    isSending = false,
                                    streamStatus = ""
                                )
                            }
                            webSocketClient = null
                            loadConversations()
                        }
                        
                        override fun onError(message: String) {
                            _uiState.update {
                                it.copy(
                                    isSending = false,
                                    streamStatus = "",
                                    error = message
                                )
                            }
                            webSocketClient = null
                        }
                    }
                )
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isSending = false,
                        streamStatus = "",
                        error = "发送失败: ${e.message}"
                    )
                }
            }
        }
    }
    
    // 路由分析功能已移除 - 导航建议现在通过 WebSocket 的 navigation 消息返回
    // 参考 web/src/services/chat.ts 的实现
    
    fun dismissRouteSuggestion() {
        println("[ChatViewModel] dismissRouteSuggestion 被调用")
        
        // 隐藏导航建议
        _uiState.update { it.copy(routeSuggestion = null) }
        
        // 获取原始问题
        val originalQuestion = _uiState.value.lastUserMessage
        if (originalQuestion.isNotEmpty()) {
            println("[ChatViewModel] 用户选择不跳转，原问题: $originalQuestion")
            println("[ChatViewModel] 发送特殊消息让 AI 重新回答")
            
            // 关闭之前的 WebSocket 连接
            webSocketClient?.disconnect()
            webSocketClient = null
            
            // 发送特殊消息，让 AI 重新生成不带导航的回答
            val specialMessage = "[用户选择不跳转] 请直接回答以下问题，不要建议跳转：$originalQuestion"
            
            // 添加一条新的 AI 消息占位
            val assistantId = "assistant_${System.currentTimeMillis()}"
            val assistantMessage = ChatMessage(
                id = assistantId,
                role = "assistant",
                content = "",
                timestamp = System.currentTimeMillis().toString()
            )
            
            _uiState.update {
                it.copy(
                    isSending = true,
                    streamStatus = "正在重新生成回答...",
                    messages = it.messages + assistantMessage
                )
            }
            
            // 重新打开 WebSocket
            viewModelScope.launch {
                try {
                    val request = ChatSocketRequest(
                        userId = currentUserId,
                        sessionId = _uiState.value.currentSessionId,
                        message = specialMessage,
                        useRag = false
                    )
                    
                    webSocketClient = chatRepository.openChatSocket(
                        request,
                        object : WebSocketClient.ChatSocketHandlers {
                            override fun onStart(sessionId: String) {
                                if (sessionId.isNotEmpty()) {
                                    _uiState.update { state -> state.copy(currentSessionId = sessionId) }
                                }
                            }
                            
                            override fun onProgress(progress: String) {
                                _uiState.update { it.copy(streamStatus = progress) }
                            }
                            
                            override fun onThinking(thinking: String) {
                                _uiState.update { state ->
                                    state.copy(
                                        messages = state.messages.map { msg ->
                                            if (msg.id == assistantId) {
                                                msg.copy(thinking = thinking)
                                            } else {
                                                msg
                                            }
                                        }
                                    )
                                }
                            }
                            
                            override fun onAnswer(answer: String) {
                                _uiState.update { state ->
                                    state.copy(
                                        messages = state.messages.map { msg ->
                                            if (msg.id == assistantId) {
                                                msg.copy(content = answer)
                                            } else {
                                                msg
                                            }
                                        }
                                    )
                                }
                            }
                            
                            override fun onNavigation(navData: Map<String, Any>) {
                                // 忽略新的导航建议
                                println("[ChatViewModel] 收到导航消息但已忽略（用户选择不跳转）")
                            }
                            
                            override fun onDone() {
                                _uiState.update {
                                    it.copy(
                                        isSending = false,
                                        streamStatus = ""
                                    )
                                }
                                webSocketClient = null
                                loadConversations()
                            }
                            
                            override fun onError(message: String) {
                                _uiState.update {
                                    it.copy(
                                        isSending = false,
                                        streamStatus = "",
                                        error = message
                                    )
                                }
                                webSocketClient = null
                            }
                        }
                    )
                } catch (e: Exception) {
                    _uiState.update {
                        it.copy(
                            isSending = false,
                            streamStatus = "",
                            error = "重新生成回答失败: ${e.message}"
                        )
                    }
                }
            }
        }
    }
    
    override fun onCleared() {
        super.onCleared()
        webSocketClient?.disconnect()
    }
}

data class ChatUiState(
    val conversations: List<com.lifeswarm.android.data.model.ConversationItem> = emptyList(),
    val messages: List<ChatMessage> = listOf(
        ChatMessage(
            id = "welcome",
            role = "assistant",
            content = "我是 AI 核心入口。你可以先自由聊天，我会在合适的时候把问题导向知识星图、决策图谱舞台或平行人生。",
            timestamp = System.currentTimeMillis().toString()
        )
    ),
    val currentSessionId: String = "",
    val input: String = "",
    val isSending: Boolean = false,
    val streamStatus: String = "",
    val error: String = "",
    val routeSuggestion: RouteSuggestion? = null,
    val lastUserMessage: String = ""
)
