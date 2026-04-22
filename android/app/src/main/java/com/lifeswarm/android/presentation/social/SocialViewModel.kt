package com.lifeswarm.android.presentation.social

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifeswarm.android.data.model.Friend
import com.lifeswarm.android.data.model.FriendRequest
import com.lifeswarm.android.data.model.SearchResult
import com.lifeswarm.android.data.repository.SocialRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * 标签页类型
 */
enum class SocialTab {
    FRIENDS,    // 好友列表
    REQUESTS,   // 好友请求
    SEARCH      // 添加好友
}

/**
 * UI 状态
 */
data class SocialUiState(
    val activeTab: SocialTab = SocialTab.FRIENDS,
    val friends: List<Friend> = emptyList(),
    val friendRequests: List<FriendRequest> = emptyList(),
    val searchResults: List<SearchResult> = emptyList(),
    val searchQuery: String = "",
    val isLoading: Boolean = false,
    val error: String = "",
    val successMessage: String = ""
)

/**
 * 社交功能 ViewModel
 */
class SocialViewModel(
    private val userId: String,
    private val repository: SocialRepository = SocialRepository()
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(SocialUiState())
    val uiState: StateFlow<SocialUiState> = _uiState.asStateFlow()
    
    companion object {
        private const val TAG = "SocialViewModel"
    }
    
    init {
        // 初始加载好友列表
        loadFriends()
    }
    
    /**
     * 切换标签页
     */
    fun switchTab(tab: SocialTab) {
        _uiState.value = _uiState.value.copy(
            activeTab = tab,
            error = "",
            successMessage = ""
        )
        
        when (tab) {
            SocialTab.FRIENDS -> loadFriends()
            SocialTab.REQUESTS -> loadFriendRequests()
            SocialTab.SEARCH -> {
                // 清空搜索结果
                _uiState.value = _uiState.value.copy(
                    searchResults = emptyList(),
                    searchQuery = ""
                )
            }
        }
    }
    
    /**
     * 加载好友列表
     */
    fun loadFriends() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "")
            
            try {
                val result = repository.getFriends(userId)
                
                result.onSuccess { friends ->
                    _uiState.value = _uiState.value.copy(
                        friends = friends,
                        isLoading = false
                    )
                    Log.d(TAG, "加载好友列表成功: ${friends.size} 位好友")
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "加载失败"
                    )
                    Log.e(TAG, "加载好友列表失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "加载异常"
                )
                Log.e(TAG, "加载好友列表异常", e)
            }
        }
    }
    
    /**
     * 加载好友请求
     */
    fun loadFriendRequests() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "")
            
            try {
                val result = repository.getFriendRequests(userId)
                
                result.onSuccess { requests ->
                    _uiState.value = _uiState.value.copy(
                        friendRequests = requests,
                        isLoading = false
                    )
                    Log.d(TAG, "加载好友请求成功: ${requests.size} 条请求")
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "加载失败"
                    )
                    Log.e(TAG, "加载好友请求失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "加载异常"
                )
                Log.e(TAG, "加载好友请求异常", e)
            }
        }
    }
    
    /**
     * 更新搜索关键词
     */
    fun updateSearchQuery(query: String) {
        _uiState.value = _uiState.value.copy(searchQuery = query)
    }
    
    /**
     * 搜索用户
     */
    fun searchUsers() {
        val query = _uiState.value.searchQuery.trim()
        if (query.isEmpty()) return
        
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "")
            
            try {
                val result = repository.searchUsers(query, userId)
                
                result.onSuccess { results ->
                    _uiState.value = _uiState.value.copy(
                        searchResults = results,
                        isLoading = false
                    )
                    Log.d(TAG, "搜索用户成功: ${results.size} 个结果")
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "搜索失败"
                    )
                    Log.e(TAG, "搜索用户失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "搜索异常"
                )
                Log.e(TAG, "搜索用户异常", e)
            }
        }
    }
    
    /**
     * 发送好友请求
     */
    fun sendFriendRequest(toUserId: String, message: String = "") {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "", successMessage = "")
            
            try {
                val result = repository.sendFriendRequest(userId, toUserId, message)
                
                result.onSuccess {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "好友请求已发送"
                    )
                    Log.d(TAG, "发送好友请求成功")
                    
                    // 重新搜索以更新状态
                    searchUsers()
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "发送失败"
                    )
                    Log.e(TAG, "发送好友请求失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "发送异常"
                )
                Log.e(TAG, "发送好友请求异常", e)
            }
        }
    }
    
    /**
     * 接受好友请求
     */
    fun acceptFriendRequest(requestId: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "", successMessage = "")
            
            try {
                val result = repository.acceptFriendRequest(requestId, userId)
                
                result.onSuccess {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "已成为好友"
                    )
                    Log.d(TAG, "接受好友请求成功")
                    
                    // 重新加载好友请求列表
                    loadFriendRequests()
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "操作失败"
                    )
                    Log.e(TAG, "接受好友请求失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "操作异常"
                )
                Log.e(TAG, "接受好友请求异常", e)
            }
        }
    }
    
    /**
     * 拒绝好友请求
     */
    fun rejectFriendRequest(requestId: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "", successMessage = "")
            
            try {
                val result = repository.rejectFriendRequest(requestId, userId)
                
                result.onSuccess {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "已拒绝"
                    )
                    Log.d(TAG, "拒绝好友请求成功")
                    
                    // 重新加载好友请求列表
                    loadFriendRequests()
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "操作失败"
                    )
                    Log.e(TAG, "拒绝好友请求失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "操作异常"
                )
                Log.e(TAG, "拒绝好友请求异常", e)
            }
        }
    }
    
    /**
     * 删除好友
     */
    fun removeFriend(friendId: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "", successMessage = "")
            
            try {
                val result = repository.removeFriend(userId, friendId)
                
                result.onSuccess {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "已删除好友"
                    )
                    Log.d(TAG, "删除好友成功")
                    
                    // 重新加载好友列表
                    loadFriends()
                }.onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "操作失败"
                    )
                    Log.e(TAG, "删除好友失败", e)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "操作异常"
                )
                Log.e(TAG, "删除好友异常", e)
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
