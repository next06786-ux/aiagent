package com.lifeswarm.android.data.model

import com.google.gson.annotations.SerializedName

/**
 * 智慧洞察数据模型
 */

// ==================== 智能洞察（涌现发现）====================

/**
 * 智能洞察
 */
data class SmartInsight(
    @SerializedName("insight_id") val insightId: String,
    @SerializedName("category") val category: String,
    @SerializedName("level") val level: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String,
    @SerializedName("evidence") val evidence: List<String> = emptyList(),
    @SerializedName("recommendations") val recommendations: List<String> = emptyList(),
    @SerializedName("confidence") val confidence: Double,
    @SerializedName("impact_score") val impactScore: Double,
    @SerializedName("created_at") val createdAt: String
)

/**
 * 仪表盘摘要
 */
data class DashboardSummary(
    @SerializedName("total_insights") val totalInsights: Int,
    @SerializedName("critical_count") val criticalCount: Int,
    @SerializedName("warning_count") val warningCount: Int,
    @SerializedName("suggestion_count") val suggestionCount: Int
)

/**
 * 情绪趋势项
 */
data class EmotionTrendItem(
    @SerializedName("date") val date: String,
    @SerializedName("avg_emotion") val avgEmotion: Double,
    @SerializedName("count") val count: Int
)

/**
 * 主题项
 */
data class TopicItem(
    @SerializedName("topic") val topic: String,
    @SerializedName("count") val count: Int
)

/**
 * 涌现统计
 */
data class EmergenceStats(
    @SerializedName("total_events") val totalEvents: Int,
    @SerializedName("pattern_events") val patternEvents: Int,
    @SerializedName("synergy_events") val synergyEvents: Int,
    @SerializedName("feedback_loop_events") val feedbackLoopEvents: Int,
    @SerializedName("threshold_events") val thresholdEvents: Int
)

/**
 * 仪表盘数据
 */
data class DashboardData(
    @SerializedName("summary") val summary: DashboardSummary,
    @SerializedName("emotion_trend") val emotionTrend: List<EmotionTrendItem> = emptyList(),
    @SerializedName("topic_distribution") val topicDistribution: List<TopicItem> = emptyList(),
    @SerializedName("top_insights") val topInsights: List<SmartInsight> = emptyList(),
    @SerializedName("emergence_stats") val emergenceStats: EmergenceStats
)

// ==================== Agent 洞察报告 ====================

/**
 * 关键发现
 */
data class KeyFinding(
    @SerializedName("type") val type: String = "",
    @SerializedName("title") val title: String = "",
    @SerializedName("description") val description: String = "",
    @SerializedName("importance") val importance: String = "low"
)

/**
 * ML 评估
 */
data class MLEvaluation(
    @SerializedName("risk_level") val riskLevel: String = "",
    @SerializedName("trend") val trend: String = "",
    @SerializedName("match_score") val matchScore: Double = 0.0,
    @SerializedName("model_version") val modelVersion: String = ""
)

/**
 * 推荐建议
 */
data class Recommendation(
    @SerializedName("priority") val priority: String = "low",
    @SerializedName("category") val category: String = "",
    @SerializedName("action") val action: String = "",
    @SerializedName("expected_impact") val expectedImpact: String = "",
    @SerializedName("timeline") val timeline: String = "",
    @SerializedName("reasoning") val reasoning: String? = null,
    @SerializedName("involved_domains") val involvedDomains: List<String>? = null
)

/**
 * 推理步骤
 */
data class ReasoningStep(
    @SerializedName("step") val step: Int = 0,
    @SerializedName("description") val description: String = ""
)

/**
 * 决策逻辑
 */
data class DecisionLogic(
    @SerializedName("reasoning_path") val reasoningPath: List<ReasoningStep> = emptyList(),
    @SerializedName("influence_factors") val influenceFactors: Map<String, Double> = emptyMap(),
    @SerializedName("data_quality") val dataQuality: Map<String, Double> = emptyMap()
)

/**
 * Agent 洞察报告
 */
data class AgentInsightReport(
    @SerializedName("insight_id") val insightId: String = "",
    @SerializedName("agent_type") val agentType: String = "",
    @SerializedName("title") val title: String = "",
    @SerializedName("summary") val summary: String = "",
    @SerializedName("key_findings") val keyFindings: List<KeyFinding> = emptyList(),
    @SerializedName("ml_evaluation") val mlEvaluation: MLEvaluation? = null,
    @SerializedName("recommendations") val recommendations: List<Recommendation> = emptyList(),
    @SerializedName("decision_logic") val decisionLogic: DecisionLogic? = null,
    @SerializedName("data_sources") val dataSources: Map<String, Any> = emptyMap(),
    @SerializedName("confidence_score") val confidenceScore: Double = 0.0,
    @SerializedName("generated_at") val generatedAt: String = "",
    @SerializedName("layer_timing") val layerTiming: Map<String, Double>? = null
)

// ==================== 跨领域分析 ====================

/**
 * 跨领域模式
 */
data class CrossDomainPattern(
    @SerializedName("pattern_type") val patternType: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String,
    @SerializedName("domains") val domains: List<String>,
    @SerializedName("strength") val strength: String
)

/**
 * 协同效应
 */
data class Synergy(
    @SerializedName("synergy_type") val synergyType: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String,
    @SerializedName("involved_domains") val involvedDomains: List<String>,
    @SerializedName("potential_benefit") val potentialBenefit: String
)

/**
 * 冲突
 */
data class Conflict(
    @SerializedName("conflict_type") val conflictType: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String,
    @SerializedName("involved_domains") val involvedDomains: List<String>,
    @SerializedName("severity") val severity: String,
    @SerializedName("resolution_suggestion") val resolutionSuggestion: String
)

/**
 * 综合洞察
 */
data class IntegratedInsight(
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String,
    @SerializedName("domains") val domains: List<String>,
    @SerializedName("importance") val importance: String
)

/**
 * 行动计划
 */
data class ActionPlan(
    @SerializedName("short_term") val shortTerm: List<String> = emptyList(),
    @SerializedName("medium_term") val mediumTerm: List<String> = emptyList(),
    @SerializedName("long_term") val longTerm: List<String> = emptyList()
)

/**
 * 跨领域分析
 */
data class CrossDomainAnalysis(
    @SerializedName("summary") val summary: String,
    @SerializedName("cross_domain_patterns") val crossDomainPatterns: List<CrossDomainPattern> = emptyList(),
    @SerializedName("synergies") val synergies: List<Synergy> = emptyList(),
    @SerializedName("conflicts") val conflicts: List<Conflict> = emptyList(),
    @SerializedName("strategic_recommendations") val strategicRecommendations: List<Recommendation> = emptyList(),
    @SerializedName("integrated_insights") val integratedInsights: List<IntegratedInsight> = emptyList(),
    @SerializedName("action_plan") val actionPlan: ActionPlan
)

/**
 * 执行摘要
 */
data class ExecutionSummary(
    @SerializedName("total_agents") val totalAgents: Int,
    @SerializedName("execution_time") val executionTime: Double,
    @SerializedName("shared_context_size") val sharedContextSize: Int
)

/**
 * 跨领域分析结果
 */
data class CrossDomainAnalysisResult(
    @SerializedName("query") val query: String,
    @SerializedName("analysis_type") val analysisType: String,
    @SerializedName("domain_results") val domainResults: Map<String, Any> = emptyMap(),
    @SerializedName("cross_domain_analysis") val crossDomainAnalysis: CrossDomainAnalysis,
    @SerializedName("execution_summary") val executionSummary: ExecutionSummary,
    @SerializedName("timestamp") val timestamp: String
)

// ==================== 生活领域洞察 ====================

/**
 * 领域洞察
 */
data class DomainInsight(
    @SerializedName("domain") val domain: String,
    @SerializedName("insights") val insights: List<String> = emptyList(),
    @SerializedName("predictions") val predictions: List<String> = emptyList(),
    @SerializedName("recommendations") val recommendations: List<String> = emptyList(),
    @SerializedName("confidence") val confidence: Double
)

/**
 * 感知数据
 */
data class PerceptionData(
    @SerializedName("quality") val quality: Double
)

/**
 * 推理数据
 */
data class ReasoningData(
    @SerializedName("confidence") val confidence: Double,
    @SerializedName("selected_agents") val selectedAgents: List<String> = emptyList()
)

/**
 * 知识数据
 */
data class KnowledgeData(
    @SerializedName("entities") val entities: Int,
    @SerializedName("relations") val relations: Int,
    @SerializedName("patterns") val patterns: Int
)

/**
 * 学习数据
 */
data class LearningData(
    @SerializedName("episodes") val episodes: Int,
    @SerializedName("average_reward") val averageReward: Double
)

/**
 * 处理结果
 */
data class ProcessResult(
    @SerializedName("perception") val perception: PerceptionData,
    @SerializedName("reasoning") val reasoning: ReasoningData,
    @SerializedName("knowledge") val knowledge: KnowledgeData,
    @SerializedName("learning") val learning: LearningData,
    @SerializedName("domain_insights") val domainInsights: List<DomainInsight> = emptyList()
)

// ==================== API 请求/响应 ====================

/**
 * Agent 洞察请求
 */
data class AgentInsightRequest(
    @SerializedName("query") val query: String,
    @SerializedName("focus_area") val focusArea: String? = null,
    @SerializedName("target_school") val targetSchool: String? = null,
    @SerializedName("target_major") val targetMajor: String? = null,
    @SerializedName("target_position") val targetPosition: String? = null,
    @SerializedName("target_industry") val targetIndustry: String? = null
)

/**
 * 跨领域分析请求
 */
data class CrossDomainAnalysisRequest(
    @SerializedName("query") val query: String,
    @SerializedName("agent_chain") val agentChain: List<String> = listOf("relationship", "education", "career", "cross_domain"),
    @SerializedName("initial_context") val initialContext: Map<String, Any>? = null
)

/**
 * 生活领域处理请求
 */
data class ProcessRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("text") val text: String,
    @SerializedName("sensors") val sensors: Map<String, Any>? = null
)
