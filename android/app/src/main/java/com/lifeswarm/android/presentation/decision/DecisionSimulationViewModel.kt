package com.lifeswarm.android.presentation.decision

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.lifeswarm.android.data.model.OptionInput
import com.lifeswarm.android.data.model.ThinkingRecord
import com.lifeswarm.android.data.remote.DecisionWebSocketClient
import com.lifeswarm.android.data.remote.OptionPayload
import com.lifeswarm.android.data.remote.SimulationEvent
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * 决策推演 ViewModel
 * 对应 Web 端的 DecisionSimulationPage 状态管理
 */
class DecisionSimulationViewModel(application: Application) : AndroidViewModel(application) {
    
    private val wsClient = DecisionWebSocketClient()
    private var closeConnection: (() -> Unit)? = null
    
    private val _uiState = MutableStateFlow(SimulationUiState())
    val uiState: StateFlow<SimulationUiState> = _uiState.asStateFlow()
    
    /**
     * 启动推演
     */
    fun startSimulation(
        sessionId: String,
        userId: String,
        question: String,
        options: List<OptionInput>,
        collectedInfo: Any? = null,
        decisionType: String = "general"
    ) {
        viewModelScope.launch {
            android.util.Log.d("Simulation", "[推演] 启动推演: ${options.size} 个选项")
            
            _uiState.update {
                it.copy(
                    phase = SimulationPhase.CONNECTING,
                    statusMessage = "正在连接推演引擎...",
                    question = question,
                    options = options
                )
            }
            
            // 只连接第一个选项（后续可以扩展为并行）
            if (options.isNotEmpty()) {
                connectOption(
                    sessionId = sessionId,
                    userId = userId,
                    question = question,
                    option = options[0],
                    optionIndex = 0,
                    collectedInfo = collectedInfo,
                    decisionType = decisionType
                )
            }
        }
    }
    
    /**
     * 连接单个选项的推演
     */
    private fun connectOption(
        sessionId: String,
        userId: String,
        question: String,
        option: OptionInput,
        optionIndex: Int,
        collectedInfo: Any?,
        decisionType: String
    ) {
        val optionId = "option_${optionIndex + 1}"
        
        android.util.Log.d("Simulation", "[推演] 连接选项: $optionId - ${option.title}")
        
        closeConnection = wsClient.connect(
            sessionId = sessionId,
            userId = userId,
            question = question,
            option = OptionPayload(
                title = option.title,
                description = option.description ?: ""
            ),
            optionIndex = optionIndex,
            collectedInfo = collectedInfo,
            decisionType = decisionType,
            onOpen = {
                android.util.Log.d("Simulation", "[推演] WebSocket 已连接")
                _uiState.update {
                    it.copy(
                        phase = SimulationPhase.RUNNING,
                        statusMessage = "推演引擎已启动"
                    )
                }
            },
            onEvent = { event ->
                handleEvent(optionId, event)
            },
            onError = { error ->
                android.util.Log.e("Simulation", "[推演] 错误: $error")
                _uiState.update {
                    it.copy(
                        phase = SimulationPhase.ERROR,
                        error = error
                    )
                }
            }
        )
    }
    
    /**
     * 处理推演事件
     */
    private fun handleEvent(optionId: String, event: SimulationEvent) {
        when (event) {
            is SimulationEvent.Status -> {
                android.util.Log.d("Simulation", "[推演] 状态: ${event.message}")
                _uiState.update { it.copy(statusMessage = event.message) }
            }
            
            is SimulationEvent.OptionStart -> {
                android.util.Log.d("Simulation", "[推演] 选项开始: ${event.title}")
            }
            
            is SimulationEvent.AgentsStart -> {
                android.util.Log.d("Simulation", "[推演] Agents 启动: ${event.agents.size} 个")
                _uiState.update { state ->
                    val agents = event.agents.map { agentInfo ->
                        AgentState(
                            id = agentInfo.id,
                            name = agentInfo.name,
                            status = AgentStatus.WAITING
                        )
                    }
                    state.copy(
                        agents = agents,
                        currentMonth = if (event.month == 0) 1 else event.month
                    )
                }
            }
            
            is SimulationEvent.AgentThinking -> {
                android.util.Log.d("Simulation", "[推演] Agent 思考: ${event.agentId} - ${event.message}")
                _uiState.update { state ->
                    val updatedAgents = state.agents.map { agent ->
                        if (agent.id == event.agentId) {
                            agent.copy(
                                status = AgentStatus.THINKING,
                                currentMessage = event.message,
                                messageTimestamp = System.currentTimeMillis()
                            )
                        } else {
                            agent
                        }
                    }
                    state.copy(agents = updatedAgents)
                }
            }
            
            is SimulationEvent.PersonaAnalysis -> {
                android.util.Log.d("Simulation", "[推演] Persona 分析: ${event.personaName} - 分数: ${event.score}")
                _uiState.update { state ->
                    val updatedAgents = state.agents.map { agent ->
                        if (agent.id == event.personaId) {
                            val historyRecord = ThinkingRecord(
                                round = 1,
                                message = event.content,
                                timestamp = System.currentTimeMillis(),
                                score = event.score,
                                stance = event.stance,
                                keyPoints = event.keyPoints,
                                reasoning = event.reasoning
                            )
                            
                            agent.copy(
                                status = AgentStatus.COMPLETE,
                                score = event.score,
                                stance = event.stance,
                                thinkingHistory = agent.thinkingHistory + listOf(historyRecord)
                            )
                        } else {
                            agent
                        }
                    }
                    
                    // 计算总分
                    val completedAgents = updatedAgents.filter { it.score != null }
                    val totalScore = if (completedAgents.isNotEmpty()) {
                        completedAgents.sumOf { it.score ?: 0.0 } / completedAgents.size
                    } else {
                        0.0
                    }
                    
                    android.util.Log.d("Simulation", "[推演] 总分更新: $totalScore (${completedAgents.size}/${updatedAgents.size})")
                    
                    state.copy(
                        agents = updatedAgents,
                        totalScore = totalScore
                    )
                }
            }
            
            is SimulationEvent.PersonaInteraction -> {
                android.util.Log.d("Simulation", "[推演] Persona 交互: ${event.fromId} -> ${event.toId}")
                _uiState.update { state ->
                    val interaction = InteractionRecord(
                        from = event.fromId,
                        to = event.toId,
                        type = event.interactionType,
                        message = event.content,
                        timestamp = System.currentTimeMillis()
                    )
                    
                    // 更新发言 Agent 的消息气泡
                    val updatedAgents = state.agents.map { agent ->
                        if (agent.id == event.fromId) {
                            agent.copy(
                                currentMessage = event.content,
                                messageTimestamp = System.currentTimeMillis()
                            )
                        } else {
                            agent
                        }
                    }
                    
                    state.copy(
                        agents = updatedAgents,
                        interactions = state.interactions + interaction
                    )
                }
            }
            
            is SimulationEvent.FinalEvaluation -> {
                android.util.Log.d("Simulation", "[推演] 最终评估: 分数=${event.overallScore}, 风险=${event.riskLevel}")
                _uiState.update { state ->
                    state.copy(
                        finalScore = event.overallScore,
                        riskLevel = event.riskLevel,
                        executionConfidence = event.executionConfidence,
                        recommendation = event.recommendation
                    )
                }
            }
            
            is SimulationEvent.Complete -> {
                android.util.Log.d("Simulation", "[推演] 推演完成")
                _uiState.update {
                    it.copy(
                        phase = SimulationPhase.DONE,
                        statusMessage = "✓ 推演完成！"
                    )
                }
            }
            
            is SimulationEvent.Error -> {
                android.util.Log.e("Simulation", "[推演] 错误: ${event.message}")
                _uiState.update {
                    it.copy(
                        phase = SimulationPhase.ERROR,
                        error = event.message
                    )
                }
            }
        }
    }
    
    /**
     * 清理资源
     */
    override fun onCleared() {
        super.onCleared()
        android.util.Log.d("Simulation", "[推演] ViewModel 清理")
        closeConnection?.invoke()
    }
}

/**
 * 推演 UI 状态
 */
data class SimulationUiState(
    val phase: SimulationPhase = SimulationPhase.IDLE,
    val statusMessage: String = "",
    val error: String = "",
    val question: String = "",
    val options: List<OptionInput> = emptyList(),
    val selectedOptionIndex: Int = 0,
    val agents: List<AgentState> = emptyList(),
    val interactions: List<InteractionRecord> = emptyList(),
    val currentMonth: Int = 0,
    val totalScore: Double = 0.0,
    val finalScore: Double = 0.0,
    val riskLevel: String = "",
    val executionConfidence: Double = 0.0,
    val recommendation: String = ""
)

/**
 * 推演阶段
 */
enum class SimulationPhase {
    IDLE,           // 空闲
    CONNECTING,     // 连接中
    RUNNING,        // 运行中
    DONE,           // 完成
    ERROR           // 错误
}

/**
 * Agent 状态
 */
data class AgentState(
    val id: String,
    val name: String,
    val status: AgentStatus,
    val score: Double? = null,
    val stance: String? = null,
    val currentMessage: String? = null,
    val messageTimestamp: Long? = null,
    val thinkingHistory: List<ThinkingRecord> = emptyList()
)

/**
 * Agent 状态枚举
 */
enum class AgentStatus {
    WAITING,    // 等待中
    THINKING,   // 思考中
    COMPLETE,   // 完成
    ERROR       // 错误
}

/**
 * 交互记录
 */
data class InteractionRecord(
    val from: String,
    val to: String,
    val type: String,
    val message: String,
    val timestamp: Long
)
