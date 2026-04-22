package com.lifeswarm.android.data.model

import android.os.Parcelable
import com.google.gson.annotations.SerializedName
import kotlinx.parcelize.Parcelize

/**
 * 树洞数据模型
 */
@Parcelize
data class TreeHole(
    @SerializedName("id") val id: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String,
    @SerializedName("message_count") val messageCount: Int = 0,
    @SerializedName("created_at") val createdAt: String? = null,
    @SerializedName("user_id") val userId: String? = null,
    @SerializedName("recommendation_score") val recommendationScore: Double? = null
) : Parcelable

/**
 * 树洞消息
 */
data class TreeHoleMessage(
    @SerializedName("id") val id: String,
    @SerializedName("content") val content: String,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("likes") val likes: Int = 0,
    @SerializedName("is_anonymous") val isAnonymous: Boolean = true,
    @SerializedName("user_id") val userId: String? = null
)

/**
 * 热门决策
 */
data class TrendingDecision(
    @SerializedName("rank") val rank: Int,
    @SerializedName("decision") val decision: String,
    @SerializedName("domain") val domain: String,
    @SerializedName("type") val type: String,
    @SerializedName("keywords") val keywords: List<String> = emptyList(),
    @SerializedName("sentiment") val sentiment: String,
    @SerializedName("description") val description: String,
    @SerializedName("pain_point") val painPoint: String? = null,
    @SerializedName("score") val score: Double,
    @SerializedName("message_count") val messageCount: Int,
    @SerializedName("tree_holes") val treeHoles: List<TreeHoleRef> = emptyList(),
    @SerializedName("trend") val trend: String
)

/**
 * 树洞引用
 */
data class TreeHoleRef(
    @SerializedName("id") val id: String,
    @SerializedName("title") val title: String
)

/**
 * 创建树洞请求
 */
data class CreateTreeHoleRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String
)

/**
 * 发送消息请求
 */
data class SendMessageRequest(
    @SerializedName("tree_hole_id") val treeHoleId: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("content") val content: String,
    @SerializedName("is_anonymous") val isAnonymous: Boolean = true
)
