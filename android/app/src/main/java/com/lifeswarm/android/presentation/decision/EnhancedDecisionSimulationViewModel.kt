package com.lifeswarm.android.presentation.decision

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifeswarm.android.data.model.*
import com.lifeswarm.android.data.remote.ApiConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import okhttp3.*
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * 增强版决策推演 ViewModel
 * 支持多选项并行推演、暂停/继续控制、可视化增强
 * 对应 Web 端的 DecisionSimulationPage.tsx
 */
class EnhancedDecisionSimulationViewModel(
    private val sessionId: String,
    private val userId: String,
    private val question: String,
    private val options: List<OptionInput>,
    private val collectedInfo: CollectedInfo?,
    private val decisionType: String
) : ViewModel() {
    
    companion object {
        private const val TAG = "EnhancedSimulation"
    }
    
    private val _uiState = MutableStateFlow(EnhancedSimulationUiState())
    val uiState: StateFlow<EnhancedSimulationUiState> = _uiState.asStateFlow()
    
    // WebSocket 连接管理 - 每个选项一个连接
    private val webSocketInstances = mutableMapOf<String, WebSocket>()
    private val okHttpClient = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()
    
    // 选项状态管理
    private val optionStates = mutableMapOf<String, OptionSimulationState>()
    
    init {
        initializeOptions()
    }
    
    /**
     * 初始化所有选项
     */
    private fun initializeOptions() {
        if (options.isEmpty()) {
            _uiState.update { it.copy(error = "没有可推演的方案") }
            return
        }
        
        Log.d(TAG, "[初始化] 创建 ${options.size} 个选项")
        
        // 初始化所有选项状态
        options.forEachIndexed { index, option ->
            val optionId = "option_${index + 1}"
            optionStates[optionId] = OptionSimulationState(
                optionId = optionId,
                optionTitle = option.title,
                optionDescription = option.description ?: "",
                isPaused = index > 0  // 第一个选项自动开始，其他暂停
            )
        }
        
        // 更新 UI 状态
        _uiState.update {
            it.copy(
                activeOptionId = "option_1",
                optionStates = optionStates.toMap(),
                currentStatus = "准备推演..."
            )
        }
        
        // 自动连接第一个选项
        connectOption("option_1", 0)
    }
    
    /**
     * 切换到指定选项
     */
    fun switchToOption(optionId: String) {
        Log.d(TAG, "[切换选项] 切换到: $optionId")
        
        _uiState.update { it.copy(activeOptionId = optionId) }
        
        // 如果该选项还未连接且未暂停，则建立连接
        val state = optionStates[optionId]
        if (state != null && !state.isPaused && !webSocketInstances.containsKey(optionId)) {
            val index = optionId.removePrefix("option_").toIntOrNull()?.minus(1) ?: 0
            if (index in options.indices) {
                connectOption(optionId, index)
            }
        }
    }
    
    /**
     * 暂停指定选项的推演
     */
    fun pauseOption(optionId: String) {
        Log.d(TAG, "[暂停] 暂停选项: $optionId")
        
        val currentState = optionStates[optionId]
        if (currentState == null) {
            Log.w(TAG, "[暂停] 选项 $optionId 不存在")
            return
        }
        
        // 更新状态为暂停
        optionStates[optionId] = currentState.copy(isPaused = true)
        
        _uiState.update {
            it.copy(optionStates = optionStates.toMap())
        }
        
        Log.d(TAG, "[暂停] 状态已更新为暂停")
        
        // 发送暂停消息到后端
        val ws = webSocketInstances[optionId]
        if (ws != null) {
            val pauseMessage = """{"action":"pause"}"""
            val sendResult = ws.send(pauseMessage)
            Log.d(TAG, "[暂停] 发送暂停消息: $pauseMessage, 结果: $sendResult")
        } else {
            Log.w(TAG, "[暂停] WebSocket 连接不存在，无法发送暂停消息")
        }
    }
    
    /**
     * 继续指定选项的推演
     */
    fun resumeOption(optionId: String) {
        Log.d(TAG, "[继续] 继续选项: $optionId")
        
        val currentState = optionStates[optionId]
        if (currentState == null) {
            Log.w(TAG, "[继续] 选项 $optionId 不存在")
            return
        }
        
        // 更新状态为继续
        optionStates[optionId] = currentState.copy(isPaused = false)
        
        _uiState.update {
            it.copy(optionStates = optionStates.toMap())
        }
        
        Log.d(TAG, "[继续] 状态已更新为继续")
        
        // 如果已有连接，发送继续消息
        if (webSocketInstances.containsKey(optionId)) {
            val ws = webSocketInstances[optionId]
            val resumeMessage = """{"action":"resume"}"""
            val sendResult = ws?.send(resumeMessage)
            Log.d(TAG, "[继续] 发送继续消息: $resumeMessage, 结果: $sendResult")
        } else {
            Log.d(TAG, "[继续] WebSocket 连接不存在，重新建立连接")
            // 如果没有连接，建立新连接
            val index = optionId.removePrefix("option_").toIntOrNull()?.minus(1) ?: 0
            if (index in options.indices) {
                connectOption(optionId, index)
            }
        }
    }
    
    /**
     * 为指定选项建立 WebSocket 连接
     */
    private fun connectOption(optionId: String, index: Int) {
        // 检查是否已有连接
        if (webSocketInstances.containsKey(optionId)) {
            Log.d(TAG, "[连接] 选项 $optionId 已有连接")
            return
        }
        
        // 检查是否已暂停
        if (optionStates[optionId]?.isPaused == true) {
            Log.d(TAG, "[连接] 选项 $optionId 已暂停，跳过连接")
            return
        }
        
        val option = options.getOrNull(index) ?: return
        
        viewModelScope.launch {
            try {
                val wsUrl = "${ApiConfig.WS_BASE_URL}/api/decision/persona/ws/simulate-option"
                
                Log.d(TAG, "[连接] 连接选项 $optionId: ${option.title}")
                Log.d(TAG, "[连接] WebSocket URL: $wsUrl")
                
                val request = Request.Builder()
                    .url(wsUrl)
                    .build()
                
                val listener = object : WebSocketListener() {
                    override fun onOpen(webSocket: WebSocket, response: Response) {
                        Log.d(TAG, "[WebSocket-$optionId] 连接已建立")
                        
                        // 发送初始化消息
                        val initMessage = JSONObject().apply {
                            put("type", "start_simulation")
                            put("session_id", sessionId)
                            put("user_id", userId)
                            put("question", question)
                            put("option", JSONObject().apply {
                                put("title", option.title)
                                put("description", option.description ?: "")
                            })
                            put("option_index", index)
                            put("collected_info", collectedInfo?.let { 
                                JSONObject().apply {
                                    put("decision_scenario", JSONObject(it.decisionScenario))
                                    put("constraints", JSONObject(it.constraints))
                                    put("priorities", JSONObject(it.priorities))
                                    put("concerns", JSONArray(it.concerns))
                                    put("mentioned_options", JSONArray(it.mentionedOptions))
                                }
                            } ?: JSONObject())
                            put("decision_type", decisionType)
                        }
                        
                        val messageStr = initMessage.toString()
                        Log.d(TAG, "[WebSocket-$optionId] 发送初始化消息: $messageStr")
                        
                        val sendResult = webSocket.send(messageStr)
                        Log.d(TAG, "[WebSocket-$optionId] 消息发送结果: $sendResult")
                        
                        updateOptionState(optionId) { state ->
                            state.copy(
                                events = state.events + SimulationEvent(
                                    type = "connected",
                                    content = "连接已建立"
                                )
                            )
                        }
                    }
                    
                    override fun onMessage(webSocket: WebSocket, text: String) {
                        try {
                            val json = JSONObject(text)
                            val eventType = json.optString("type")
                            
                            Log.d(TAG, "[WebSocket-$optionId] 收到消息: $eventType")
                            
                            // 检查是否已暂停
                            val currentState = optionStates[optionId]
                            if (currentState?.isPaused == true) {
                                Log.d(TAG, "[WebSocket-$optionId] 选项已暂停，忽略消息: $eventType")
                                return
                            }
                            
                            handleWebSocketMessage(optionId, eventType, json)
                        } catch (e: Exception) {
                            Log.e(TAG, "[WebSocket-$optionId] 解析消息失败", e)
                        }
                    }
                    
                    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                        Log.e(TAG, "[WebSocket-$optionId] 连接失败", t)
                        
                        updateOptionState(optionId) { state ->
                            state.copy(
                                events = state.events + SimulationEvent(
                                    type = "error",
                                    content = "连接失败: ${t.message}"
                                )
                            )
                        }
                        
                        _uiState.update {
                            it.copy(error = "选项 ${index + 1} 连接失败: ${t.message}")
                        }
                    }
                    
                    override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                        Log.d(TAG, "[WebSocket-$optionId] 连接已关闭: $code - $reason")
                        webSocketInstances.remove(optionId)
                    }
                }
                
                val webSocket = okHttpClient.newWebSocket(request, listener)
                webSocketInstances[optionId] = webSocket
                
            } catch (e: Exception) {
                Log.e(TAG, "[连接] 连接失败", e)
                _uiState.update {
                    it.copy(error = "连接失败: ${e.message}")
                }
            }
        }
    }
    
    /**
     * 处理 WebSocket 消息
     */
    private fun handleWebSocketMessage(optionId: String, eventType: String, json: JSONObject) {
        Log.d(TAG, "[消息处理-$optionId] 类型: $eventType, 完整消息: $json")
        
        when (eventType) {
            "status" -> handleStatus(optionId, json)
            "start", "option_start" -> handleOptionStart(optionId, json)
            "agents_start", "personas_start", "personas_init" -> {
                Log.d(TAG, "[消息处理-$optionId] 收到 agents/personas 初始化消息")
                handleAgentsStart(optionId, json)
            }
            "agent_thinking", "thinking" -> handleAgentThinking(optionId, json)
            "agents_thinking_batch" -> handleAgentsThinkingBatch(optionId, json)
            "agent_complete" -> handleAgentComplete(optionId, json)
            "persona_analysis" -> handlePersonaAnalysis(optionId, json)
            "persona_interaction" -> handlePersonaInteraction(optionId, json)
            "final_evaluation" -> handleFinalEvaluation(optionId, json)
            "option_complete" -> handleOptionComplete(optionId, json)
            "done", "complete" -> handleDone(optionId, json)
            "error" -> handleError(optionId, json)
            "shared_facts" -> {
                // 忽略 shared_facts 消息，仅记录日志
                Log.d(TAG, "[消息处理-$optionId] 收到 shared_facts 消息")
            }
            else -> Log.w(TAG, "[WebSocket-$optionId] 未知消息类型: $eventType, 消息内容: $json")
        }
    }
    
    // ========== 消息处理函数 ==========
    
    private fun handleStatus(optionId: String, json: JSONObject) {
        val content = json.optString("content", "")
        updateOptionState(optionId) { state ->
            state.copy(
                events = state.events + SimulationEvent(
                    type = "status",
                    content = content
                )
            )
        }
        
        // 如果是当前活动选项，更新全局状态
        if (_uiState.value.activeOptionId == optionId) {
            _uiState.update { it.copy(currentStatus = content) }
        }
    }
    
    private fun handleOptionStart(optionId: String, json: JSONObject) {
        val title = json.optString("title", "")
        updateOptionState(optionId) { state ->
            state.copy(
                events = state.events + SimulationEvent(
                    type = "start",
                    content = "开始分析: $title"
                )
            )
        }
    }
    
    private fun handleAgentsStart(optionId: String, json: JSONObject) {
        // 尝试多种可能的字段名
        val agentsArray = json.optJSONArray("agents") 
            ?: json.optJSONArray("personas")
            ?: json.optJSONArray("persona_list")
        val month = json.optInt("month", 0)
        
        Log.d(TAG, "[handleAgentsStart-$optionId] agentsArray: $agentsArray, month: $month")
        
        if (agentsArray != null) {
            val agents = mutableListOf<PersonaAgent>()
            for (i in 0 until agentsArray.length()) {
                val agentJson = agentsArray.getJSONObject(i)
                val agent = PersonaAgent(
                    id = agentJson.optString("id", agentJson.optString("persona_id", "")),
                    name = agentJson.optString("name", agentJson.optString("persona_name", "")),
                    status = PersonaStatus.WAITING
                )
                agents.add(agent)
                Log.d(TAG, "[handleAgentsStart-$optionId] 添加 Agent: ${agent.name} (${agent.id})")
            }
            
            Log.d(TAG, "[handleAgentsStart-$optionId] 总共添加了 ${agents.size} 个 Agents")
            
            updateOptionState(optionId) { state ->
                val newState = state.copy(
                    agents = agents,
                    currentMonth = if (month == 0) 1 else month
                )
                Log.d(TAG, "[handleAgentsStart-$optionId] 更新后的 agents 数量: ${newState.agents.size}")
                newState
            }
            
            // 验证更新后的状态
            val currentState = optionStates[optionId]
            Log.d(TAG, "[handleAgentsStart-$optionId] 验证: optionStates 中的 agents 数量: ${currentState?.agents?.size}")
            
            // 验证 UI 状态
            val uiState = _uiState.value
            val uiOptionState = uiState.optionStates[optionId]
            Log.d(TAG, "[handleAgentsStart-$optionId] 验证: UI状态中的 agents 数量: ${uiOptionState?.agents?.size}")
        } else {
            Log.w(TAG, "[handleAgentsStart-$optionId] agentsArray 为 null! 完整消息: $json")
        }
    }
    
    private fun handleAgentThinking(optionId: String, json: JSONObject) {
        val agentId = json.optString("agent_id")
        val content = json.optString("content", "正在思考...")
        val stage = json.optString("stage", "thinking")
        
        updateOptionState(optionId) { state ->
            state.copy(
                agents = state.agents.map { agent ->
                    if (agent.id == agentId) {
                        val record = ThinkingRecord(
                            round = if (stage == "reflection") 1 else 0,
                            message = content,
                            timestamp = System.currentTimeMillis()
                        )
                        agent.copy(
                            status = PersonaStatus.THINKING,
                            currentMessage = content,
                            messageTimestamp = System.currentTimeMillis(),
                            thinkingHistory = agent.thinkingHistory + record
                        )
                    } else {
                        agent
                    }
                }
            )
        }
    }
    
    private fun handleAgentsThinkingBatch(optionId: String, json: JSONObject) {
        val agentsArray = json.optJSONArray("agents")
        
        if (agentsArray != null) {
            val thinkingAgents = mutableMapOf<String, String>()
            for (i in 0 until agentsArray.length()) {
                val agentJson = agentsArray.getJSONObject(i)
                val agentId = agentJson.optString("agent_id")
                val content = agentJson.optString("content")
                thinkingAgents[agentId] = content
            }
            
            updateOptionState(optionId) { state ->
                state.copy(
                    agents = state.agents.map { agent ->
                        thinkingAgents[agent.id]?.let { content ->
                            agent.copy(
                                status = PersonaStatus.THINKING,
                                currentMessage = content,
                                messageTimestamp = System.currentTimeMillis()
                            )
                        } ?: agent
                    }
                )
            }
        }
    }
    
    private fun handleAgentComplete(optionId: String, json: JSONObject) {
        val agentId = json.optString("agent_id")
        val score = json.optDouble("score", Double.NaN)
        
        updateOptionState(optionId) { state ->
            state.copy(
                agents = state.agents.map { agent ->
                    if (agent.id == agentId) {
                        agent.copy(
                            status = PersonaStatus.COMPLETE,
                            score = if (score.isNaN()) null else score
                        )
                    } else {
                        agent
                    }
                }
            )
        }
    }
    
    private fun handlePersonaAnalysis(optionId: String, json: JSONObject) {
        val personaId = json.optString("persona_id")
        val content = json.optString("content", "")
        val personaDataJson = json.optJSONObject("persona_data")
        
        if (personaDataJson != null) {
            val score = personaDataJson.optDouble("score", Double.NaN)
            val stance = personaDataJson.optString("stance", "")
            val keyPointsArray = personaDataJson.optJSONArray("key_points")
            val keyPoints = mutableListOf<String>()
            if (keyPointsArray != null) {
                for (i in 0 until keyPointsArray.length()) {
                    keyPoints.add(keyPointsArray.getString(i))
                }
            }
            val reasoning = personaDataJson.optString("reasoning", "")
            val round = personaDataJson.optInt("round", 0)
            
            updateOptionState(optionId) { state ->
                val updatedAgents = state.agents.map { agent ->
                    if (agent.id == personaId) {
                        val record = ThinkingRecord(
                            round = round,
                            message = content,
                            timestamp = System.currentTimeMillis(),
                            score = if (score.isNaN()) null else score,
                            stance = stance,
                            keyPoints = keyPoints,
                            reasoning = reasoning
                        )
                        agent.copy(
                            status = PersonaStatus.COMPLETE,
                            score = if (score.isNaN()) null else score,
                            stance = stance,
                            thinkingHistory = agent.thinkingHistory + record
                        )
                    } else {
                        agent
                    }
                }
                
                // 计算总分
                val completedAgents = updatedAgents.filter { it.score != null }
                val totalScore = if (completedAgents.isNotEmpty()) {
                    completedAgents.mapNotNull { it.score }.average()
                } else {
                    0.0
                }
                
                state.copy(
                    agents = updatedAgents,
                    totalScore = totalScore
                )
            }
        }
    }
    
    private fun handlePersonaInteraction(optionId: String, json: JSONObject) {
        val personaId = json.optString("persona_id")
        val content = json.optString("content", "")
        val interactionDataJson = json.optJSONObject("interaction_data")
        
        if (interactionDataJson != null) {
            val interaction = PersonaInteraction(
                from = interactionDataJson.optString("from_persona_id", ""),
                to = interactionDataJson.optString("to_persona_id", ""),
                type = interactionDataJson.optString("interaction_type", "讨论"),
                message = interactionDataJson.optString("content", ""),
                timestamp = System.currentTimeMillis(),
                action = interactionDataJson.optString("action")
            )
            
            updateOptionState(optionId) { state ->
                // 更新发言 Agent 的消息
                val updatedAgents = state.agents.map { agent ->
                    if (agent.id == interaction.from) {
                        val record = ThinkingRecord(
                            round = 1,
                            message = content,
                            timestamp = System.currentTimeMillis(),
                            action = interaction.action
                        )
                        agent.copy(
                            currentMessage = content,
                            messageTimestamp = System.currentTimeMillis(),
                            messageAction = interaction.action,
                            thinkingHistory = agent.thinkingHistory + record
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
    }
    
    private fun handleFinalEvaluation(optionId: String, json: JSONObject) {
        val evaluationDataJson = json.optJSONObject("evaluation_data")
        
        if (evaluationDataJson != null) {
            val overallScore = evaluationDataJson.optDouble("overall_score", 0.0)
            val riskLevel = evaluationDataJson.optString("risk_level", "中等")
            val executionConfidence = evaluationDataJson.optDouble("execution_confidence", 0.0)
            val recommendation = evaluationDataJson.optString("recommendation", "")
            
            updateOptionState(optionId) { state ->
                state.copy(
                    totalScore = overallScore,
                    events = state.events + SimulationEvent(
                        type = "evaluation",
                        content = "综合评估: $recommendation",
                        month = 3
                    )
                )
            }
        }
    }
    
    private fun handleOptionComplete(optionId: String, json: JSONObject) {
        val finalScore = json.optDouble("final_score", 0.0)
        
        updateOptionState(optionId) { state ->
            state.copy(
                isComplete = true,
                totalScore = finalScore
            )
        }
    }
    
    private fun handleDone(optionId: String, json: JSONObject) {
        updateOptionState(optionId) { state ->
            state.copy(isComplete = true)
        }
        
        // 检查是否所有选项都完成
        val allComplete = optionStates.values.all { it.isComplete }
        if (allComplete) {
            _uiState.update {
                it.copy(
                    isComplete = true,
                    currentStatus = "所有方案推演完成"
                )
            }
        }
    }
    
    private fun handleError(optionId: String, json: JSONObject) {
        val content = json.optString("content", "推演出错")
        updateOptionState(optionId) { state ->
            state.copy(
                events = state.events + SimulationEvent(
                    type = "error",
                    content = content
                )
            )
        }
    }
    
    // ========== 状态更新辅助函数 ==========
    
    private fun updateOptionState(optionId: String, update: (OptionSimulationState) -> OptionSimulationState) {
        val currentState = optionStates[optionId]
        if (currentState == null) {
            Log.w(TAG, "[updateOptionState] optionId $optionId 不存在于 optionStates 中")
            return
        }
        
        val newState = update(currentState)
        optionStates[optionId] = newState
        
        Log.d(TAG, "[updateOptionState-$optionId] 更新状态: agents=${newState.agents.size}, score=${newState.totalScore}, complete=${newState.isComplete}")
        
        _uiState.update {
            val updatedUiState = it.copy(optionStates = optionStates.toMap())
            Log.d(TAG, "[updateOptionState-$optionId] UI状态已更新, 当前活动选项: ${updatedUiState.activeOptionId}")
            updatedUiState
        }
    }
    
    override fun onCleared() {
        super.onCleared()
        // 关闭所有 WebSocket 连接
        webSocketInstances.values.forEach { it.close(1000, "ViewModel cleared") }
        webSocketInstances.clear()
    }
}

/**
 * 增强版 UI 状态
 */
data class EnhancedSimulationUiState(
    val activeOptionId: String = "",
    val optionStates: Map<String, OptionSimulationState> = emptyMap(),
    val currentStatus: String = "准备推演...",
    val isComplete: Boolean = false,
    val error: String = ""
)
