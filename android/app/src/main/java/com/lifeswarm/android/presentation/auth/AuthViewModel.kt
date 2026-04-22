package com.lifeswarm.android.presentation.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifeswarm.android.data.model.*
import com.lifeswarm.android.data.repository.AuthRepository
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

/**
 * 认证 ViewModel - 对应 web/src/context/AuthContext.tsx
 */
class AuthViewModel(
    private val authRepository: AuthRepository
) : ViewModel() {
    
    // 认证状态
    private val _authState = MutableStateFlow<AuthState>(AuthState.Loading)
    val authState: StateFlow<AuthState> = _authState.asStateFlow()
    
    // 用户信息
    private val _user = MutableStateFlow<UserInfo?>(null)
    val user: StateFlow<UserInfo?> = _user.asStateFlow()
    
    // Token
    private val _token = MutableStateFlow("")
    val token: StateFlow<String> = _token.asStateFlow()
    
    // 是否已认证
    val isAuthenticated: StateFlow<Boolean> = combine(
        _user,
        _token
    ) { user, token ->
        user != null && token.isNotEmpty()
    }.stateIn(viewModelScope, SharingStarted.Eagerly, false)
    
    // 错误消息
    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage.asStateFlow()
    
    init {
        // 初始化时验证本地存储的认证信息
        bootstrap()
    }
    
    /**
     * 初始化认证状态 - 对应 web 端的 bootstrap 函数
     */
    private fun bootstrap() {
        viewModelScope.launch {
            try {
                // 从本地存储读取
                authRepository.tokenFlow.collect { token ->
                    _token.value = token
                }
            } catch (e: Exception) {
                _authState.value = AuthState.Unauthenticated
            }
        }
        
        viewModelScope.launch {
            try {
                authRepository.userFlow.collect { user ->
                    _user.value = user
                    
                    // 如果有 token 和 user，验证 token 是否有效
                    if (user != null && _token.value.isNotEmpty()) {
                        val (valid, userId) = authRepository.verifyToken(_token.value)
                        if (valid && userId.isNotEmpty()) {
                            // Token 有效，刷新用户信息
                            val freshUser = authRepository.fetchUser(userId)
                            _user.value = freshUser
                            _authState.value = AuthState.Authenticated
                        } else {
                            // Token 无效，清除本地存储
                            authRepository.clearLocalAuth()
                            _token.value = ""
                            _user.value = null
                            _authState.value = AuthState.Unauthenticated
                        }
                    } else {
                        _authState.value = AuthState.Unauthenticated
                    }
                }
            } catch (e: Exception) {
                authRepository.clearLocalAuth()
                _token.value = ""
                _user.value = null
                _authState.value = AuthState.Unauthenticated
            }
        }
    }
    
    /**
     * 登录 - 对应 web 端的 login 函数
     */
    fun login(username: String, password: String) {
        viewModelScope.launch {
            try {
                _authState.value = AuthState.Loading
                _errorMessage.value = null
                
                val payload = LoginPayload(username, password)
                val result = authRepository.login(payload)
                
                _token.value = result.token
                _user.value = UserInfo(
                    userId = result.userId,
                    username = result.username,
                    email = result.email,
                    nickname = result.nickname,
                    phone = null,
                    avatarUrl = result.avatarUrl,
                    isVerified = false
                )
                
                _authState.value = AuthState.Authenticated
            } catch (e: Exception) {
                _errorMessage.value = e.message ?: "登录失败"
                _authState.value = AuthState.Error(e.message ?: "登录失败")
            }
        }
    }
    
    /**
     * 注册 - 对应 web 端的 register 函数
     */
    fun register(username: String, password: String, email: String, nickname: String?) {
        viewModelScope.launch {
            try {
                _authState.value = AuthState.Loading
                _errorMessage.value = null
                
                val payload = RegisterPayload(username, password, email, nickname)
                val result = authRepository.register(payload)
                
                _token.value = result.token
                _user.value = UserInfo(
                    userId = result.userId,
                    username = result.username,
                    email = result.email,
                    nickname = result.nickname,
                    phone = null,
                    avatarUrl = result.avatarUrl,
                    isVerified = false
                )
                
                _authState.value = AuthState.Authenticated
            } catch (e: Exception) {
                _errorMessage.value = e.message ?: "注册失败"
                _authState.value = AuthState.Error(e.message ?: "注册失败")
            }
        }
    }
    
    /**
     * 登出 - 对应 web 端的 logout 函数
     */
    fun logout() {
        viewModelScope.launch {
            try {
                authRepository.logout(_token.value)
            } catch (e: Exception) {
                // 忽略错误，继续清除本地状态
            } finally {
                _token.value = ""
                _user.value = null
                _authState.value = AuthState.Unauthenticated
            }
        }
    }
    
    /**
     * 刷新用户信息 - 对应 web 端的 refreshUser 函数
     */
    fun refreshUser() {
        viewModelScope.launch {
            try {
                val userId = _user.value?.userId ?: return@launch
                val freshUser = authRepository.fetchUser(userId)
                _user.value = freshUser
            } catch (e: Exception) {
                _errorMessage.value = e.message ?: "刷新用户信息失败"
            }
        }
    }
    
    /**
     * 更新资料 - 对应 web 端的 updateProfile 函数
     */
    fun updateProfile(nickname: String?, phone: String?, avatarUrl: String?) {
        viewModelScope.launch {
            try {
                val userId = _user.value?.userId ?: return@launch
                val payload = UpdateProfilePayload(nickname, phone, avatarUrl)
                val updated = authRepository.updateUser(userId, payload)
                _user.value = updated
            } catch (e: Exception) {
                _errorMessage.value = e.message ?: "更新资料失败"
            }
        }
    }
    
    /**
     * 修改密码 - 对应 web 端的 changePassword 函数
     */
    fun changePassword(oldPassword: String, newPassword: String) {
        viewModelScope.launch {
            try {
                val userId = _user.value?.userId ?: return@launch
                val payload = ChangePasswordPayload(oldPassword, newPassword)
                authRepository.changePassword(userId, payload)
            } catch (e: Exception) {
                _errorMessage.value = e.message ?: "修改密码失败"
            }
        }
    }
    
    /**
     * 清除错误消息
     */
    fun clearError() {
        _errorMessage.value = null
    }
}

/**
 * 认证状态
 */
sealed class AuthState {
    object Loading : AuthState()
    object Authenticated : AuthState()
    object Unauthenticated : AuthState()
    data class Error(val message: String) : AuthState()
}
