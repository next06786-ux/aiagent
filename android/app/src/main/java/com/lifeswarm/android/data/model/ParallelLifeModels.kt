package com.lifeswarm.android.data.model

import com.google.gson.annotations.SerializedName

/**
 * 塔罗牌数据模型
 */
data class TarotCard(
    @SerializedName("card") val card: String,
    @SerializedName("card_key") val cardKey: String,
    @SerializedName("dimension") val dimension: String,
    @SerializedName("dimension_key") val dimensionKey: String,
    @SerializedName("scenario") val scenario: String,
    @SerializedName("options") val options: List<TarotOption>,
    @SerializedName("timestamp") val timestamp: String,
    @SerializedName("icon") val icon: String? = null
)

/**
 * 塔罗牌选项
 */
data class TarotOption(
    @SerializedName("id") val id: String,
    @SerializedName("text") val text: String,
    @SerializedName("tendency") val tendency: String // "left" or "right"
)

/**
 * 决策画像
 */
data class DecisionProfile(
    @SerializedName("dimensions") val dimensions: Map<String, DimensionData>,
    @SerializedName("patterns") val patterns: List<String>,
    @SerializedName("confidence") val confidence: Double,
    @SerializedName("total_choices") val totalChoices: Int
)

/**
 * 维度数据
 */
data class DimensionData(
    @SerializedName("value") val value: Double,
    @SerializedName("count") val count: Int,
    @SerializedName("confidence") val confidence: Double
)

/**
 * 游戏统计
 */
data class GameStats(
    @SerializedName("total_cards_drawn") val totalCardsDrawn: Int,
    @SerializedName("choices_made") val choicesMade: Int,
    @SerializedName("profile_confidence") val profileConfidence: Double,
    @SerializedName("dimensions_analyzed") val dimensionsAnalyzed: Int
)

/**
 * 抽牌请求
 */
data class DrawCardRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("drawn_cards") val drawnCards: List<String>? = null
)

/**
 * 提交选择请求
 */
data class SubmitChoiceRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("card") val card: String,
    @SerializedName("card_key") val cardKey: String,
    @SerializedName("dimension") val dimension: String,
    @SerializedName("dimension_key") val dimensionKey: String,
    @SerializedName("scenario") val scenario: String,
    @SerializedName("choice") val choice: String,
    @SerializedName("tendency") val tendency: String
)
