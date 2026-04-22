package com.lifeswarm.android.data.repository

import com.lifeswarm.android.data.model.*
import com.lifeswarm.android.data.remote.ApiException
import com.lifeswarm.android.data.remote.ApiService
import com.lifeswarm.android.data.remote.WebSocketClient

/**
 * 聊天仓库 - 对应 web/src/services/chat.ts
 */
class ChatRepository(
    private val apiService: ApiService
) {
    
    /**
     * 获取会话列表 - 对应 web 端的 listConversations 函数
     */
    suspend fun listConversations(userId: String): List<ConversationItem> {
        val response = apiService.listConversations(userId)
        
        if (!response.isSuccessful || response.body() == null) {
            return emptyList()
        }
        
        val result = response.body()!!
        
        if (!result.success) {
            return emptyList()
        }
        
        return result.data ?: emptyList()
    }
    
    /**
     * 获取会话消息 - 对应 web 端的 getConversationMessages 函数
     */
    suspend fun getConversationMessages(
        userId: String,
        sessionId: String
    ): List<ConversationMessageData> {
        val response = apiService.getConversationMessages(userId, sessionId)
        
        if (!response.isSuccessful || response.body() == null) {
            return emptyList()
        }
        
        val result = response.body()!!
        
        if (!result.success) {
            return emptyList()
        }
        
        return result.data ?: emptyList()
    }
    
    /**
     * 创建新会话 - 对应 web 端的 createConversation 函数
     */
    suspend fun createConversation(userId: String): String {
        val response = apiService.createConversation(userId)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "创建会话失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (!result.success || result.data == null) {
            throw ApiException(
                result.message ?: "创建会话失败"
            )
        }
        
        return result.data["conversation_id"] ?: throw ApiException("创建会话失败：未返回会话ID")
    }
    
    /**
     * 打开聊天 WebSocket - 对应 web 端的 openChatSocket 函数
     * 导航建议通过 WebSocket 的 navigation 消息类型返回，不再使用单独的 HTTP API
     */
    fun openChatSocket(
        payload: ChatSocketRequest,
        handlers: WebSocketClient.ChatSocketHandlers
    ): WebSocketClient {
        val client = WebSocketClient("/ws/chat", handlers)
        client.connect(payload)
        return client
    }
}
