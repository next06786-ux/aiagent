package com.lifeswarm.android.data.model

/**
 * 人格 Agent 数据模型
 * 对应 Web 端的 PersonaAgent 接口
 */
data class PersonaAgent(
    val id: String,
    val name: String,
    val status: PersonaStatus = PersonaStatus.WAITING,
    val score: Double? = null,
    val stance: String? = null,
    val currentMessage: String? = null,
    val messageTimestamp: Long? = null,
    val messageAction: String? = null,
    val thinkingHistory: List<ThinkingRecord> = emptyList()
)

/**
 * 人格状态
 */
enum class PersonaStatus {
    WAITING,    // 等待中
    THINKING,   // 思考中
    COMPLETE,   // 已完成
    ERROR       // 错误
}

/**
 * 思考记录
 */
data class ThinkingRecord(
    val round: Int,                    // 轮次（0=初始分析，1=深度反思）
    val message: String,               // 思考内容
    val timestamp: Long,               // 时间戳
    val score: Double? = null,         // 评分
    val stance: String? = null,        // 立场
    val keyPoints: List<String> = emptyList(),  // 关键点
    val reasoning: String? = null,     // 推理过程
    val action: String? = null,        // 动作类型（用于交互）
    val skillResult: SkillResult? = null  // 技能执行结果
)

/**
 * 技能执行结果
 */
data class SkillResult(
    val skillName: String,
    val success: Boolean,
    val result: String,
    val metadata: Map<String, Any> = emptyMap()
)

/**
 * 人格交互
 */
data class PersonaInteraction(
    val from: String,           // 发送者 ID
    val to: String,             // 接收者 ID
    val type: String,           // 交互类型（质疑、支持、补充等）
    val message: String,        // 消息内容
    val timestamp: Long,        // 时间戳
    val action: String? = null  // 动作类型
)

/**
 * 选项推演状态
 */
data class OptionSimulationState(
    val optionId: String,
    val optionTitle: String,
    val optionDescription: String,
    val agents: List<PersonaAgent> = emptyList(),
    val interactions: List<PersonaInteraction> = emptyList(),
    val currentMonth: Int = 0,
    val totalScore: Double = 0.0,
    val isComplete: Boolean = false,
    val isPaused: Boolean = false,
    val events: List<SimulationEvent> = emptyList()
)

/**
 * 推演事件
 */
data class SimulationEvent(
    val type: String,
    val content: String,
    val month: Int = 0,
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * 人格分析数据
 */
data class PersonaAnalysisData(
    val id: String,
    val score: Double,
    val stance: String,
    val confidence: Double = 0.5,
    val keyPoints: List<String> = emptyList(),
    val reasoning: String = "",
    val round: Int = 0
)

/**
 * 人格交互数据
 */
data class PersonaInteractionData(
    val fromPersonaId: String,
    val toPersonaId: String,
    val fromPersona: String,
    val toPersona: String,
    val interactionType: String,
    val content: String,
    val action: String? = null
)

/**
 * 最终评估数据
 */
data class FinalEvaluationData(
    val overallScore: Double,
    val riskLevel: String,
    val executionConfidence: Double,
    val recommendation: String,
    val impactSummary: Map<String, Any> = emptyMap()
)
