package com.lifeswarm.android.presentation.treehole

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifeswarm.android.data.model.TreeHole
import com.lifeswarm.android.data.model.TreeHoleMessage
import com.lifeswarm.android.data.model.TrendingDecision
import com.lifeswarm.android.data.repository.TreeHoleRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * UI 状态
 */
data class TreeHoleUiState(
    val treeHoles: List<TreeHole> = emptyList(),
    val trendingDecisions: List<TrendingDecision> = emptyList(),
    val isLoading: Boolean = false,
    val error: String = "",
    val successMessage: String = ""
)

/**
 * 树洞详情 UI 状态
 */
data class TreeHoleDetailUiState(
    val treeHole: TreeHole? = null,
    val messages: List<TreeHoleMessage> = emptyList(),
    val isLoading: Boolean = false,
    val isSending: Boolean = false,
    val error: String = "",
    val successMessage: String = ""
)

/**
 * 树洞 ViewModel
 */
class TreeHoleViewModel(
    private val userId: String,
    private val repository: TreeHoleRepository = TreeHoleRepository()
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(TreeHoleUiState())
    val uiState: StateFlow<TreeHoleUiState> = _uiState.asStateFlow()
    
    companion object {
        private const val TAG = "TreeHoleViewModel"
    }
    
    init {
        loadTreeHoles()
        loadTrendingDecisions()
    }
    
    /**
     * 加载树洞列表
     */
    fun loadTreeHoles() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "")
            
            try {
                val result = repository.getAllTreeHoles()
                
                result.onSuccess { treeHoles ->
                    _uiState.value = _uiState.value.copy(
                        treeHoles = treeHoles,
                        isLoading = false
                    )
                    Log.d(TAG, "加载树洞列表成功: ${treeHoles.size} 个树洞")
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "加载失败"
                    )
                    Log.e(TAG, "加载树洞列表失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "加载异常"
                )
                Log.e(TAG, "加载树洞列表异常", e)
            }
        }
    }
    
    /**
     * 加载热门决策
     */
    fun loadTrendingDecisions() {
        viewModelScope.launch {
            try {
                val result = repository.getTrendingDecisions()
                
                result.onSuccess { decisions ->
                    _uiState.value = _uiState.value.copy(
                        trendingDecisions = decisions
                    )
                    Log.d(TAG, "加载热门决策成功: ${decisions.size} 条")
                }.onFailure { e ->
                    Log.e(TAG, "加载热门决策失败", e)
                }
            } catch (e: Exception) {
                Log.e(TAG, "加载热门决策异常", e)
            }
        }
    }
    
    /**
     * 创建树洞
     */
    fun createTreeHole(title: String, description: String, onSuccess: (String) -> Unit) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "", successMessage = "")
            
            try {
                val result = repository.createTreeHole(userId, title, description)
                
                result.onSuccess { treeHoleId ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "树洞创建成功"
                    )
                    Log.d(TAG, "创建树洞成功: $treeHoleId")
                    
                    // 重新加载列表
                    loadTreeHoles()
                    
                    // 回调成功
                    onSuccess(treeHoleId)
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "创建失败"
                    )
                    Log.e(TAG, "创建树洞失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "创建异常"
                )
                Log.e(TAG, "创建树洞异常", e)
            }
        }
    }
    
    /**
     * 清除消息
     */
    fun clearMessages() {
        _uiState.value = _uiState.value.copy(
            error = "",
            successMessage = ""
        )
    }
}

/**
 * 树洞详情 ViewModel
 */
class TreeHoleDetailViewModel(
    private val userId: String,
    private val treeHoleId: String,
    private val repository: TreeHoleRepository = TreeHoleRepository()
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(TreeHoleDetailUiState())
    val uiState: StateFlow<TreeHoleDetailUiState> = _uiState.asStateFlow()
    
    companion object {
        private const val TAG = "TreeHoleDetailViewModel"
    }
    
    init {
        loadMessages()
    }
    
    /**
     * 设置树洞信息
     */
    fun setTreeHole(treeHole: TreeHole) {
        _uiState.value = _uiState.value.copy(treeHole = treeHole)
    }
    
    /**
     * 加载消息列表
     */
    fun loadMessages() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "")
            
            try {
                val result = repository.getTreeHoleMessages(treeHoleId)
                
                result.onSuccess { messages ->
                    _uiState.value = _uiState.value.copy(
                        messages = messages,
                        isLoading = false
                    )
                    Log.d(TAG, "加载消息成功: ${messages.size} 条消息")
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "加载失败"
                    )
                    Log.e(TAG, "加载消息失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "加载异常"
                )
                Log.e(TAG, "加载消息异常", e)
            }
        }
    }
    
    /**
     * 发送消息
     */
    fun sendMessage(content: String, isAnonymous: Boolean = true) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSending = true, error = "", successMessage = "")
            
            try {
                val result = repository.sendMessage(treeHoleId, userId, content, isAnonymous)
                
                result.onSuccess {
                    _uiState.value = _uiState.value.copy(
                        isSending = false,
                        successMessage = "发送成功"
                    )
                    Log.d(TAG, "发送消息成功")
                    
                    // 重新加载消息列表
                    loadMessages()
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isSending = false,
                        error = e.message ?: "发送失败"
                    )
                    Log.e(TAG, "发送消息失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isSending = false,
                    error = e.message ?: "发送异常"
                )
                Log.e(TAG, "发送消息异常", e)
            }
        }
    }
    
    /**
     * 清除消息
     */
    fun clearMessages() {
        _uiState.value = _uiState.value.copy(
            error = "",
            successMessage = ""
        )
    }
}
