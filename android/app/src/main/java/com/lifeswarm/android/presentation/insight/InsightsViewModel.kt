package com.lifeswarm.android.presentation.insight

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifeswarm.android.data.model.AgentInsightReport
import com.lifeswarm.android.data.model.CrossDomainAnalysisResult
import com.lifeswarm.android.data.repository.InsightRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * 视图模式
 */
enum class ViewMode {
    AGENTS,           // 单Agent分析
    CROSS_DOMAIN      // 跨领域综合分析
}

/**
 * Agent 类型
 */
enum class AgentType(val displayName: String, val icon: String, val description: String) {
    RELATIONSHIP("人际关系Agent", "👥", "分析人际关系网络、社交模式、关系质量"),
    EDUCATION("教育升学Agent", "🎓", "分析升学路径、学校选择、专业匹配"),
    CAREER("职业规划Agent", "💼", "分析职业发展、技能匹配、岗位选择")
}

/**
 * UI 状态
 */
data class InsightsUiState(
    val viewMode: ViewMode = ViewMode.AGENTS,
    val selectedAgent: AgentType? = null,
    val agentReport: AgentInsightReport? = null,
    val isAgentLoading: Boolean = false,
    val agentError: String = "",
    
    // 跨领域分析
    val crossDomainQuery: String = "综合分析我的人际关系、教育背景和职业发展，给出整体战略建议",
    val crossDomainResult: CrossDomainAnalysisResult? = null,
    val isCrossDomainLoading: Boolean = false,
    val crossDomainError: String = ""
)

/**
 * 智慧洞察 ViewModel
 */
class InsightsViewModel(
    private val token: String,
    private val repository: InsightRepository = InsightRepository()
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(InsightsUiState())
    val uiState: StateFlow<InsightsUiState> = _uiState.asStateFlow()
    
    companion object {
        private const val TAG = "InsightsViewModel"
    }
    
    /**
     * 切换视图模式
     */
    fun switchViewMode(mode: ViewMode) {
        _uiState.value = _uiState.value.copy(
            viewMode = mode,
            selectedAgent = null,
            agentReport = null,
            agentError = ""
        )
    }
    
    /**
     * 生成 Agent 洞察报告
     */
    fun generateAgentInsight(agentType: AgentType) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                selectedAgent = agentType,
                isAgentLoading = true,
                agentReport = null,
                agentError = ""
            )
            
            try {
                Log.d(TAG, "开始生成${agentType.displayName}报告")
                
                val result = when (agentType) {
                    AgentType.RELATIONSHIP -> repository.generateRelationshipInsight(token)
                    AgentType.EDUCATION -> repository.generateEducationInsight(token)
                    AgentType.CAREER -> repository.generateCareerInsight(token)
                }
                
                result.onSuccess { report ->
                    Log.d(TAG, "生成${agentType.displayName}报告成功")
                    Log.d(TAG, "报告ID: ${report.insightId}")
                    Log.d(TAG, "报告标题: ${report.title}")
                    Log.d(TAG, "关键发现数量: ${report.keyFindings.size}")
                    Log.d(TAG, "推荐建议数量: ${report.recommendations.size}")
                    
                    _uiState.value = _uiState.value.copy(
                        agentReport = report,
                        isAgentLoading = false
                    )
                }.onFailure { e ->
                    Log.e(TAG, "生成${agentType.displayName}报告失败", e)
                    e.printStackTrace()
                    
                    _uiState.value = _uiState.value.copy(
                        isAgentLoading = false,
                        agentError = e.message ?: "生成报告失败"
                    )
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "生成Agent报告异常", e)
                e.printStackTrace()
                
                _uiState.value = _uiState.value.copy(
                    isAgentLoading = false,
                    agentError = e.message ?: "生成报告异常"
                )
            }
        }
    }
    
    /**
     * 返回 Agent 选择
     */
    fun backToAgentSelection() {
        _uiState.value = _uiState.value.copy(
            selectedAgent = null,
            agentReport = null,
            agentError = ""
        )
    }
    
    /**
     * 更新跨领域查询
     */
    fun updateCrossDomainQuery(query: String) {
        _uiState.value = _uiState.value.copy(crossDomainQuery = query)
    }
    
    /**
     * 生成跨领域分析
     */
    fun generateCrossDomainAnalysis() {
        val query = _uiState.value.crossDomainQuery.trim()
        if (query.isEmpty()) {
            _uiState.value = _uiState.value.copy(crossDomainError = "请输入分析查询")
            return
        }
        
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isCrossDomainLoading = true,
                crossDomainResult = null,
                crossDomainError = ""
            )
            
            try {
                val result = repository.generateCrossDomainAnalysis(token, query)
                
                result.onSuccess { analysisResult ->
                    _uiState.value = _uiState.value.copy(
                        crossDomainResult = analysisResult,
                        isCrossDomainLoading = false
                    )
                    Log.d(TAG, "生成跨领域分析成功")
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isCrossDomainLoading = false,
                        crossDomainError = e.message ?: "分析失败"
                    )
                    Log.e(TAG, "生成跨领域分析失败", e)
                }
                
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isCrossDomainLoading = false,
                    crossDomainError = e.message ?: "分析异常"
                )
                Log.e(TAG, "生成跨领域分析异常", e)
            }
        }
    }
    
    /**
     * 清除错误
     */
    fun clearError() {
        _uiState.value = _uiState.value.copy(
            agentError = "",
            crossDomainError = ""
        )
    }
}
