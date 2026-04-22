package com.lifeswarm.android.data.model

import com.google.gson.annotations.SerializedName

/**
 * API 数据模型 - 对应 web/src/types/api.ts
 */

// 通用响应封装
data class ApiEnvelope<T>(
    @SerializedName("code") val code: Int,
    @SerializedName("message") val message: String?,
    @SerializedName("data") val data: T?
)

data class SuccessEnvelope<T>(
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String?,
    @SerializedName("data") val data: T?
)

// 用户相关模型
data class UserInfo(
    @SerializedName("user_id") val userId: String,
    @SerializedName("username") val username: String,
    @SerializedName("email") val email: String,
    @SerializedName("nickname") val nickname: String?,
    @SerializedName("phone") val phone: String?,
    @SerializedName("avatar_url") val avatarUrl: String?,
    @SerializedName("is_verified") val isVerified: Boolean = false,
    @SerializedName("created_at") val createdAt: String? = null,
    @SerializedName("last_login") val lastLogin: String? = null
)

// 登录请求
data class LoginPayload(
    @SerializedName("username") val username: String,
    @SerializedName("password") val password: String
)

// 登录响应
data class LoginResponse(
    @SerializedName("token") val token: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("username") val username: String,
    @SerializedName("email") val email: String,
    @SerializedName("nickname") val nickname: String?,
    @SerializedName("avatar_url") val avatarUrl: String?,
    @SerializedName("is_admin") val isAdmin: Boolean? = false
)

// 注册请求
data class RegisterPayload(
    @SerializedName("username") val username: String,
    @SerializedName("password") val password: String,
    @SerializedName("email") val email: String,
    @SerializedName("nickname") val nickname: String?
)

// Token 验证响应
data class TokenVerifyResponse(
    @SerializedName("valid") val valid: Boolean,
    @SerializedName("user_id") val userId: String?
)

// 更新资料请求
data class UpdateProfilePayload(
    @SerializedName("nickname") val nickname: String?,
    @SerializedName("phone") val phone: String?,
    @SerializedName("avatar_url") val avatarUrl: String?
)

// 修改密码请求
data class ChangePasswordPayload(
    @SerializedName("old_password") val oldPassword: String,
    @SerializedName("new_password") val newPassword: String
)

// 聊天相关模型
data class ConversationItem(
    @SerializedName("id") val id: String = "",  // 后端使用 "id"
    @SerializedName("conversation_id") val conversationId: String = "",  // 兼容旧字段
    @SerializedName("title") val title: String? = null,
    @SerializedName("preview") val preview: String? = null,  // 添加预览字段
    @SerializedName("message_count") val messageCount: Int = 0,  // 添加消息数量
    @SerializedName("last_message_time") val lastMessageTime: String = "",  // 后端使用这个字段
    @SerializedName("created_at") val createdAt: String = "",
    @SerializedName("updated_at") val updatedAt: String = ""
) {
    // 获取实际的会话ID（优先使用id，其次conversationId）
    val sessionId: String
        get() = id.takeIf { it.isNotEmpty() } ?: conversationId
    
    // 获取实际的更新时间（优先使用lastMessageTime，其次updatedAt）
    val displayTime: String
        get() = lastMessageTime.takeIf { it.isNotEmpty() } ?: updatedAt
}

data class ConversationMessageData(
    @SerializedName("message_id") val messageId: String = "",
    @SerializedName("role") val role: String = "", // "user" or "assistant"
    @SerializedName("content") val content: String = "",
    @SerializedName("timestamp") val timestamp: String = ""
)

// WebSocket 聊天请求
data class ChatSocketRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("message") val message: String,
    @SerializedName("use_rag") val useRag: Boolean = false
)

// WebSocket 消息类型
data class WebSocketMessage(
    @SerializedName("type") val type: String,
    @SerializedName("content") val content: String?,
    @SerializedName("session_id") val sessionId: String?
)
