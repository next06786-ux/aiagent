package com.lifeswarm.android.data.repository

import com.lifeswarm.android.data.local.AuthStorage
import com.lifeswarm.android.data.model.*
import com.lifeswarm.android.data.remote.ApiException
import com.lifeswarm.android.data.remote.ApiService
import kotlinx.coroutines.flow.Flow

/**
 * 认证仓库 - 对应 web/src/services/auth.ts
 */
class AuthRepository(
    private val apiService: ApiService,
    private val authStorage: AuthStorage
) {
    
    val tokenFlow: Flow<String> = authStorage.tokenFlow
    val userFlow: Flow<UserInfo?> = authStorage.userFlow
    
    /**
     * 获取当前 Token
     */
    fun getToken(): Flow<String> = tokenFlow
    
    /**
     * 登录 - 对应 web 端的 login 函数
     */
    suspend fun login(payload: LoginPayload): LoginResponse {
        val response = apiService.login(payload)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "登录失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (result.code != 200 || result.data == null) {
            throw ApiException(
                result.message ?: "登录失败",
                result.code,
                result
            )
        }
        
        val loginData = result.data
        
        // 保存到本地存储
        val user = UserInfo(
            userId = loginData.userId,
            username = loginData.username,
            email = loginData.email,
            nickname = loginData.nickname,
            phone = null,
            avatarUrl = loginData.avatarUrl,
            isVerified = false
        )
        authStorage.saveAuth(loginData.token, user)
        
        return loginData
    }
    
    /**
     * 注册 - 对应 web 端的 register 函数
     */
    suspend fun register(payload: RegisterPayload): LoginResponse {
        val response = apiService.register(payload)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "注册失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (result.code != 200 || result.data == null) {
            throw ApiException(
                result.message ?: "注册失败",
                result.code,
                result
            )
        }
        
        val loginData = result.data
        
        // 保存到本地存储
        val user = UserInfo(
            userId = loginData.userId,
            username = loginData.username,
            email = loginData.email,
            nickname = loginData.nickname,
            phone = null,
            avatarUrl = loginData.avatarUrl,
            isVerified = false
        )
        authStorage.saveAuth(loginData.token, user)
        
        return loginData
    }
    
    /**
     * 登出 - 对应 web 端的 logout 函数
     */
    suspend fun logout(token: String) {
        try {
            val response = apiService.logout(mapOf("token" to token))
            
            if (!response.isSuccessful || response.body() == null) {
                throw ApiException(
                    "退出失败",
                    response.code(),
                    response.errorBody()?.string()
                )
            }
            
            val result = response.body()!!
            
            if (result.code != 200) {
                throw ApiException(
                    result.message ?: "退出失败",
                    result.code,
                    result
                )
            }
        } finally {
            // 无论如何都清除本地存储
            authStorage.clearAuth()
        }
    }
    
    /**
     * 验证 token - 对应 web 端的 verifyToken 函数
     */
    suspend fun verifyToken(token: String): Pair<Boolean, String> {
        val response = apiService.verifyToken(mapOf("token" to token))
        
        if (!response.isSuccessful || response.body() == null) {
            return Pair(false, "")
        }
        
        val result = response.body()!!
        
        if (result.code != 200 || result.data?.valid != true) {
            return Pair(false, "")
        }
        
        return Pair(true, result.data.userId ?: "")
    }
    
    /**
     * 获取用户信息 - 对应 web 端的 fetchUser 函数
     */
    suspend fun fetchUser(userId: String): UserInfo {
        val response = apiService.getUser(userId)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "获取用户信息失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (result.code != 200 || result.data == null) {
            throw ApiException(
                result.message ?: "获取用户信息失败",
                result.code,
                result
            )
        }
        
        return result.data
    }
    
    /**
     * 更新用户信息 - 对应 web 端的 updateUser 函数
     */
    suspend fun updateUser(userId: String, payload: UpdateProfilePayload): UserInfo {
        val response = apiService.updateUser(userId, payload)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "更新资料失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (result.code != 200 || result.data == null) {
            throw ApiException(
                result.message ?: "更新资料失败",
                result.code,
                result
            )
        }
        
        return result.data
    }
    
    /**
     * 修改密码 - 对应 web 端的 changePassword 函数
     */
    suspend fun changePassword(userId: String, payload: ChangePasswordPayload) {
        val request = mapOf(
            "user_id" to userId,
            "old_password" to payload.oldPassword,
            "new_password" to payload.newPassword
        )
        
        val response = apiService.changePassword(request)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "修改密码失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (result.code != 200) {
            throw ApiException(
                result.message ?: "修改密码失败",
                result.code,
                result
            )
        }
    }
    
    /**
     * 清除本地认证信息
     */
    suspend fun clearLocalAuth() {
        authStorage.clearAuth()
    }
}
