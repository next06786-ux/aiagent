package com.lifeswarm.android.data.model

import com.google.gson.annotations.SerializedName

/**
 * 好友数据模型
 */
data class Friend(
    @SerializedName("user_id") val userId: String,
    @SerializedName("username") val username: String,
    @SerializedName("nickname") val nickname: String,
    @SerializedName("avatar_url") val avatarUrl: String? = null,
    @SerializedName("email") val email: String? = null,
    @SerializedName("status") val status: String = "offline", // "online" or "offline"
    @SerializedName("last_seen") val lastSeen: String? = null,
    @SerializedName("friend_since") val friendSince: String? = null
)

/**
 * 好友请求数据模型
 */
data class FriendRequest(
    @SerializedName("request_id") val requestId: String,
    @SerializedName("from_user_id") val fromUserId: String,
    @SerializedName("from_username") val fromUsername: String,
    @SerializedName("from_nickname") val fromNickname: String,
    @SerializedName("from_avatar_url") val fromAvatarUrl: String? = null,
    @SerializedName("message") val message: String = "",
    @SerializedName("created_at") val createdAt: String
)

/**
 * 用户搜索结果
 */
data class SearchResult(
    @SerializedName("user_id") val userId: String,
    @SerializedName("username") val username: String,
    @SerializedName("nickname") val nickname: String,
    @SerializedName("avatar_url") val avatarUrl: String? = null,
    @SerializedName("email") val email: String? = null,
    @SerializedName("is_friend") val isFriend: Boolean = false
)

/**
 * 搜索用户请求
 */
data class SearchUsersRequest(
    @SerializedName("query") val query: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("limit") val limit: Int = 10
)

/**
 * 发送好友请求
 */
data class SendFriendRequestPayload(
    @SerializedName("from_user_id") val fromUserId: String,
    @SerializedName("to_user_id") val toUserId: String,
    @SerializedName("message") val message: String = ""
)

/**
 * 接受/拒绝好友请求
 */
data class HandleFriendRequestPayload(
    @SerializedName("request_id") val requestId: String,
    @SerializedName("user_id") val userId: String
)

/**
 * 删除好友请求
 */
data class RemoveFriendPayload(
    @SerializedName("user_id") val userId: String,
    @SerializedName("friend_id") val friendId: String
)
