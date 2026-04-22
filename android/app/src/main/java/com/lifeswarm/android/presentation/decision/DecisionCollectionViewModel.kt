package com.lifeswarm.android.presentation.decision

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.lifeswarm.android.LifeSwarmApp
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * 决策信息采集 ViewModel
 */
class DecisionCollectionViewModel(application: Application) : AndroidViewModel(application) {
    
    private val app = application as LifeSwarmApp
    private val decisionRepository = app.decisionRepository
    private val authStorage = app.authStorage
    
    private val _uiState = MutableStateFlow(DecisionCollectionUiState())
    val uiState: StateFlow<DecisionCollectionUiState> = _uiState.asStateFlow()
    
    fun startCollection(initialQuestion: String, decisionType: String = "general") {
        viewModelScope.launch {
            // 获取当前用户
            val currentUser = authStorage.userFlow.first()
            val currentUserId = currentUser?.userId ?: ""
            
            if (currentUserId.isEmpty()) {
                _uiState.update { it.copy(error = "用户未登录") }
                return@launch
            }
            
            _uiState.update {
                it.copy(
                    isLoading = true,
                    error = "",
                    messages = listOf(
                        CollectionMessage(
                            id = "user_0",
                            role = "user",
                            content = initialQuestion
                        )
                    )
                )
            }
            
            try {
                val session = decisionRepository.startDecisionCollection(
                    userId = currentUserId,
                    initialQuestion = initialQuestion,
                    decisionType = decisionType
                )
                
                _uiState.update {
                    it.copy(
                        sessionId = session.sessionId,
                        isLoading = false,
                        messages = it.messages + CollectionMessage(
                            id = "ai_0",
                            role = "assistant",
                            content = session.message
                        )
                    )
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = "启动采集失败: ${e.message}"
                    )
                }
            }
        }
    }
    
    fun updateInput(text: String) {
        _uiState.update { it.copy(input = text) }
    }
    
    /**
     * 手动结束采集并生成选项
     * 返回生成的选项列表，如果失败返回 null
     */
    suspend fun finishCollection(): List<com.lifeswarm.android.data.model.OptionInput>? {
        return try {
            android.util.Log.d("DecisionCollection", "[采集] 用户手动结束采集，开始生成选项")
            
            // 先标记为加载状态
            _uiState.update {
                it.copy(
                    isLoading = true,
                    loadingMessage = "正在分析收集的信息...",
                    error = ""
                )
            }
            
            // 模拟进度更新（因为 API 可能需要较长时间）
            kotlinx.coroutines.delay(1000)
            _uiState.update {
                it.copy(loadingMessage = "AI 正在生成决策方案...")
            }
            
            // 调用生成选项 API
            val options = decisionRepository.generateDecisionOptions(
                sessionId = _uiState.value.sessionId,
                userOptions = emptyList()
            )
            
            android.util.Log.d("DecisionCollection", "[采集] 生成了 ${options.size} 个选项")
            
            // 标记完成并添加系统消息
            _uiState.update {
                it.copy(
                    isComplete = true,
                    isLoading = false,
                    loadingMessage = "",
                    summary = "已收集足够信息，生成了 ${options.size} 个决策方案",
                    messages = it.messages + CollectionMessage(
                        id = "system_${System.currentTimeMillis()}",
                        role = "system",
                        content = "✓ 信息采集完成！已生成 ${options.size} 个决策方案"
                    ),
                    generatedOptions = options
                )
            }
            
            options
        } catch (e: Exception) {
            android.util.Log.e("DecisionCollection", "[采集] 生成选项失败: ${e.message}", e)
            _uiState.update {
                it.copy(
                    isLoading = false,
                    loadingMessage = "",
                    error = "生成选项失败: ${e.message}"
                )
            }
            null
        }
    }
    
    fun sendResponse() {
        val currentState = _uiState.value
        if (currentState.input.isBlank() || currentState.isLoading) {
            return
        }
        
        // 检查 sessionId 是否存在
        if (currentState.sessionId.isEmpty()) {
            _uiState.update {
                it.copy(
                    error = "会话未初始化，请重新开始"
                )
            }
            return
        }
        
        val userMessage = CollectionMessage(
            id = "user_${System.currentTimeMillis()}",
            role = "user",
            content = currentState.input.trim()
        )
        
        _uiState.update {
            it.copy(
                input = "",
                isLoading = true,
                error = "",
                messages = it.messages + userMessage
            )
        }
        
        viewModelScope.launch {
            try {
                val response = decisionRepository.continueDecisionCollection(
                    sessionId = currentState.sessionId,
                    userResponse = userMessage.content
                )
                
                // 调试日志
                android.util.Log.d("DecisionCollection", "[采集] 收到响应:")
                android.util.Log.d("DecisionCollection", "  round: ${response.round}")
                android.util.Log.d("DecisionCollection", "  phase: ${response.phase}")
                android.util.Log.d("DecisionCollection", "  isComplete: ${response.isComplete}")
                android.util.Log.d("DecisionCollection", "  aiQuestion: ${response.aiQuestion}")
                android.util.Log.d("DecisionCollection", "  summary: ${response.summary}")
                
                val aiMessage = CollectionMessage(
                    id = "ai_${System.currentTimeMillis()}",
                    role = "assistant",
                    content = response.aiQuestion ?: response.summary ?: "继续..."
                )
                
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        round = response.round ?: it.round,
                        phase = response.phase ?: it.phase,
                        isComplete = response.isComplete,
                        summary = response.summary ?: "",
                        collectedInfo = response.collectedInfo,
                        messages = it.messages + aiMessage
                    )
                }
                
                if (response.isComplete) {
                    android.util.Log.d("DecisionCollection", "[采集] 采集已完成！")
                }
            } catch (e: Exception) {
                android.util.Log.e("DecisionCollection", "[采集] 错误: ${e.message}", e)
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = "采集失败: ${e.message}"
                    )
                }
            }
        }
    }
}

data class DecisionCollectionUiState(
    val sessionId: String = "",
    val messages: List<CollectionMessage> = emptyList(),
    val input: String = "",
    val isLoading: Boolean = false,
    val loadingMessage: String = "",  // 加载时显示的详细消息
    val error: String = "",
    val round: Int = 0,
    val phase: String = "",
    val isComplete: Boolean = false,
    val summary: String = "",
    val collectedInfo: com.lifeswarm.android.data.model.CollectedInfo? = null,
    val generatedOptions: List<com.lifeswarm.android.data.model.OptionInput> = emptyList()
)
