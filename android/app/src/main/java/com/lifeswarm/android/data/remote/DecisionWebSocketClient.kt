package com.lifeswarm.android.data.remote

import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonObject
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

/**
 * 决策推演 WebSocket 客户端
 * 对应 Web 端的 openDecisionSimulationSocket
 */
class DecisionWebSocketClient(
    private val baseUrl: String = "ws://82.157.195.238:8000"
) {
    private val TAG = "DecisionWebSocket"
    private val gson = Gson()
    private var webSocket: WebSocket? = null
    
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)  // 无限超时，因为是长连接
        .build()
    
    /**
     * 连接到推演引擎
     */
    fun connect(
        sessionId: String,
        userId: String,
        question: String,
        option: OptionPayload,
        optionIndex: Int,
        collectedInfo: Any? = null,
        decisionType: String = "general",
        onEvent: (SimulationEvent) -> Unit,
        onError: (String) -> Unit,
        onOpen: () -> Unit = {}
    ): () -> Unit {
        // 正确的 WebSocket 路径
        val url = "$baseUrl/api/decision/persona/ws/simulate-option"
        
        Log.d(TAG, "[WebSocket] 准备连接: $url")
        Log.d(TAG, "[WebSocket] sessionId: $sessionId")
        Log.d(TAG, "[WebSocket] userId: $userId")
        Log.d(TAG, "[WebSocket] option: ${option.title}")
        
        val request = Request.Builder()
            .url(url)
            .build()
        
        val listener = object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.d(TAG, "[WebSocket] 连接已建立")
                onOpen()
                
                // 发送初始化消息
                val initMessage = mapOf(
                    "type" to "start_simulation",
                    "session_id" to sessionId,
                    "user_id" to userId,
                    "question" to question,
                    "option" to mapOf(
                        "title" to option.title,
                        "description" to option.description
                    ),
                    "option_index" to optionIndex,
                    "collected_info" to collectedInfo,
                    "decision_type" to decisionType
                )
                
                val json = gson.toJson(initMessage)
                webSocket.send(json)
                Log.d(TAG, "[WebSocket] 已发送初始化消息")
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    Log.d(TAG, "[WebSocket] 收到消息: ${text.take(200)}")
                    val jsonObject = gson.fromJson(text, JsonObject::class.java)
                    val event = parseEvent(jsonObject)
                    if (event != null) {
                        onEvent(event)
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "[WebSocket] 解析消息失败", e)
                    onError("解析消息失败: ${e.message}")
                }
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "[WebSocket] 连接失败", t)
                onError("连接失败: ${t.message}")
            }
            
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "[WebSocket] 连接已关闭: $code - $reason")
            }
        }
        
        webSocket = client.newWebSocket(request, listener)
        
        // 返回关闭函数
        return {
            Log.d(TAG, "[WebSocket] 主动关闭连接")
            webSocket?.close(1000, "Client closed")
            webSocket = null
        }
    }
    
    /**
     * 发送暂停/继续消息
     */
    fun sendPauseControl(optionId: String, isPaused: Boolean) {
        val message = mapOf(
            "type" to if (isPaused) "pause_simulation" else "resume_simulation",
            "option_id" to optionId
        )
        webSocket?.send(gson.toJson(message))
    }
    
    /**
     * 解析事件
     */
    private fun parseEvent(json: JsonObject): SimulationEvent? {
        val type = json.get("type")?.asString ?: return null
        
        return when (type) {
            "status" -> {
                val content = json.get("content")?.asString ?: ""
                SimulationEvent.Status(content)
            }
            
            "option_start", "start" -> {
                val optionId = json.get("option_id")?.asString ?: ""
                val title = json.get("title")?.asString ?: ""
                SimulationEvent.OptionStart(optionId, title)
            }
            
            "agents_start", "personas_init" -> {
                val agentsArray = json.getAsJsonArray("agents") ?: json.getAsJsonArray("personas")
                val agents = agentsArray?.map { agentJson ->
                    val obj = agentJson.asJsonObject
                    AgentInfo(
                        id = obj.get("id")?.asString ?: "",
                        name = obj.get("name")?.asString ?: ""
                    )
                } ?: emptyList()
                val month = json.get("month")?.asInt ?: 0
                val optionId = json.get("option_id")?.asString ?: ""
                SimulationEvent.AgentsStart(optionId, agents, month)
            }
            
            "agent_thinking" -> {
                val agentId = json.get("agent_id")?.asString ?: ""
                val optionId = json.get("option_id")?.asString ?: ""
                val content = json.get("content")?.asString ?: ""
                val stage = json.get("stage")?.asString ?: "thinking"
                SimulationEvent.AgentThinking(optionId, agentId, content, stage)
            }
            
            "persona_analysis" -> {
                val optionId = json.get("option_id")?.asString ?: ""
                val personaId = json.get("persona_id")?.asString ?: ""
                val personaName = json.get("persona_name")?.asString ?: ""
                val content = json.get("content")?.asString ?: ""
                val personaData = json.getAsJsonObject("persona_data")
                
                if (personaData != null) {
                    val score = personaData.get("score")?.asDouble ?: 0.0
                    val stance = personaData.get("stance")?.asString ?: ""
                    val reasoning = personaData.get("reasoning")?.asString ?: ""
                    val keyPoints = personaData.getAsJsonArray("key_points")?.map { 
                        it.asString 
                    } ?: emptyList()
                    
                    SimulationEvent.PersonaAnalysis(
                        optionId, personaId, personaName, content, 
                        score, stance, reasoning, keyPoints
                    )
                } else {
                    null
                }
            }
            
            "persona_interaction" -> {
                val optionId = json.get("option_id")?.asString ?: ""
                val interactionData = json.getAsJsonObject("interaction_data")
                
                if (interactionData != null) {
                    val fromId = interactionData.get("from_persona_id")?.asString ?: ""
                    val toId = interactionData.get("to_persona_id")?.asString ?: ""
                    val content = interactionData.get("content")?.asString ?: ""
                    val interactionType = interactionData.get("interaction_type")?.asString ?: "讨论"
                    
                    SimulationEvent.PersonaInteraction(optionId, fromId, toId, content, interactionType)
                } else {
                    null
                }
            }
            
            "final_evaluation" -> {
                val optionId = json.get("option_id")?.asString ?: ""
                val evaluationData = json.getAsJsonObject("evaluation_data")
                
                if (evaluationData != null) {
                    val overallScore = evaluationData.get("overall_score")?.asDouble ?: 0.0
                    val riskLevel = evaluationData.get("risk_level")?.asString ?: "中等"
                    val executionConfidence = evaluationData.get("execution_confidence")?.asDouble ?: 0.0
                    val recommendation = evaluationData.get("recommendation")?.asString ?: ""
                    
                    SimulationEvent.FinalEvaluation(optionId, overallScore, riskLevel, executionConfidence, recommendation)
                } else {
                    null
                }
            }
            
            "option_complete", "done", "complete" -> {
                val optionId = json.get("option_id")?.asString ?: ""
                SimulationEvent.Complete(optionId)
            }
            
            "error" -> {
                val content = json.get("content")?.asString ?: "未知错误"
                SimulationEvent.Error(content)
            }
            
            else -> {
                Log.d(TAG, "[WebSocket] 未知事件类型: $type")
                null
            }
        }
    }
}

/**
 * 选项负载
 */
data class OptionPayload(
    val title: String,
    val description: String
)

/**
 * Agent 信息
 */
data class AgentInfo(
    val id: String,
    val name: String
)

/**
 * 推演事件
 */
sealed class SimulationEvent {
    data class Status(val message: String) : SimulationEvent()
    data class OptionStart(val optionId: String, val title: String) : SimulationEvent()
    data class AgentsStart(val optionId: String, val agents: List<AgentInfo>, val month: Int) : SimulationEvent()
    data class AgentThinking(val optionId: String, val agentId: String, val message: String, val stage: String) : SimulationEvent()
    data class PersonaAnalysis(
        val optionId: String,
        val personaId: String,
        val personaName: String,
        val content: String,
        val score: Double,
        val stance: String,
        val reasoning: String,
        val keyPoints: List<String>
    ) : SimulationEvent()
    data class PersonaInteraction(
        val optionId: String,
        val fromId: String,
        val toId: String,
        val content: String,
        val interactionType: String
    ) : SimulationEvent()
    data class FinalEvaluation(
        val optionId: String,
        val overallScore: Double,
        val riskLevel: String,
        val executionConfidence: Double,
        val recommendation: String
    ) : SimulationEvent()
    data class Complete(val optionId: String) : SimulationEvent()
    data class Error(val message: String) : SimulationEvent()
}
