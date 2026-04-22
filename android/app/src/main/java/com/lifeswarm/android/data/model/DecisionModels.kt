package com.lifeswarm.android.data.model

import com.google.gson.annotations.SerializedName

/**
 * 决策相关数据模型 - 对应 web/src/types/api.ts 中的决策类型
 */

// 决策历史记录
data class DecisionHistoryRecord(
    @SerializedName("simulation_id") val simulationId: String,
    @SerializedName("question") val question: String,
    @SerializedName("options_count") val optionsCount: Int,
    @SerializedName("recommendation") val recommendation: String?,
    @SerializedName("created_at") val createdAt: String
)

// 决策选项输入
data class OptionInput(
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String?
)

// 生成选项响应
data class GenerateOptionsResponse(
    @SerializedName("ai_options") val aiOptions: List<OptionInput>
)

// 收集的信息
data class CollectedInfo(
    @SerializedName("decision_scenario") val decisionScenario: Map<String, String>,
    @SerializedName("constraints") val constraints: Map<String, String>,
    @SerializedName("priorities") val priorities: Map<String, String>,
    @SerializedName("concerns") val concerns: List<String>,
    @SerializedName("mentioned_options") val mentionedOptions: List<String>
)

// 时间线事件
data class TimelineEvent(
    @SerializedName("event_id") val eventId: String,
    @SerializedName("parent_event_id") val parentEventId: String?,
    @SerializedName("month") val month: Int,
    @SerializedName("event") val event: String,
    @SerializedName("event_type") val eventType: String?,
    @SerializedName("branch_group") val branchGroup: String?,
    @SerializedName("node_level") val nodeLevel: Int?,
    @SerializedName("risk_tag") val riskTag: String?,
    @SerializedName("opportunity_tag") val opportunityTag: String?,
    @SerializedName("visual_weight") val visualWeight: Int?,
    @SerializedName("impact") val impact: Map<String, Double>?,
    @SerializedName("probability") val probability: Double
)

// 风险维度
data class RiskDimension(
    @SerializedName("name") val name: String,
    @SerializedName("score") val score: Double,
    @SerializedName("level") val level: String,
    @SerializedName("factors") val factors: List<String>,
    @SerializedName("mitigation") val mitigation: List<String>
)

// 风险评估
data class RiskAssessment(
    @SerializedName("option_title") val optionTitle: String?,
    @SerializedName("overall_risk") val overallRisk: Double,
    @SerializedName("overall_level") val overallLevel: String,
    @SerializedName("high_risk_count") val highRiskCount: Int?,
    @SerializedName("top_dimensions") val topDimensions: List<String>,
    @SerializedName("dimensions") val dimensions: Map<String, RiskDimension>?,
    @SerializedName("recommendations") val recommendations: List<String>
)

// 决策图谱边
data class DecisionGraphEdge(
    @SerializedName("edge_id") val edgeId: String,
    @SerializedName("source") val source: String,
    @SerializedName("target") val target: String,
    @SerializedName("relation") val relation: String,
    @SerializedName("strength") val strength: Double,
    @SerializedName("label") val label: String?
)

// 决策图谱摘要
data class DecisionGraphSummary(
    @SerializedName("title") val title: String,
    @SerializedName("node_count") val nodeCount: Int,
    @SerializedName("edge_count") val edgeCount: Int,
    @SerializedName("high_risk_nodes") val highRiskNodes: Int,
    @SerializedName("dominant_axes") val dominantAxes: List<String>,
    @SerializedName("agent_stance_mix") val agentStanceMix: Map<String, Double>,
    @SerializedName("review_mode") val reviewMode: String?
)

// 决策图谱
data class DecisionGraph(
    @SerializedName("graph_id") val graphId: String,
    @SerializedName("schema_version") val schemaVersion: Int,
    @SerializedName("layout_hint") val layoutHint: String?,
    @SerializedName("graph_summary") val graphSummary: DecisionGraphSummary,
    @SerializedName("nodes") val nodes: List<TimelineEvent>,
    @SerializedName("edges") val edges: List<DecisionGraphEdge>
)

// 决策选项
data class DecisionOption(
    @SerializedName("option_id") val optionId: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String?,
    @SerializedName("timeline") val timeline: List<TimelineEvent>,
    @SerializedName("decision_graph") val decisionGraph: DecisionGraph,
    @SerializedName("final_score") val finalScore: Double,
    @SerializedName("risk_level") val riskLevel: Double,
    @SerializedName("risk_assessment") val riskAssessment: RiskAssessment?,
    @SerializedName("execution_confidence") val executionConfidence: Double?,
    @SerializedName("dropout_risk_month") val dropoutRiskMonth: Int?,
    @SerializedName("personal_note") val personalNote: String?
)

// 决策记录
data class DecisionRecord(
    @SerializedName("simulation_id") val simulationId: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("question") val question: String,
    @SerializedName("options_count") val optionsCount: Int?,
    @SerializedName("recommendation") val recommendation: String?,
    @SerializedName("schema_version") val schemaVersion: Int?,
    @SerializedName("collected_info_summary") val collectedInfoSummary: CollectedInfo?,
    @SerializedName("options") val options: List<DecisionOption>,
    @SerializedName("created_at") val createdAt: String
)

// 信息采集会话
data class CollectionSession(
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("message") val message: String
)

// 信息采集继续响应
data class CollectionContinueResponse(
    @SerializedName("round") val round: Int?,
    @SerializedName("phase") val phase: String?,
    @SerializedName("ai_question") val aiQuestion: String?,
    @SerializedName("is_complete") val isComplete: Boolean,
    @SerializedName("summary") val summary: String?,
    @SerializedName("collected_info") val collectedInfo: CollectedInfo?
)
