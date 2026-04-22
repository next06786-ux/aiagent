package com.lifeswarm.android.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.google.gson.Gson
import com.lifeswarm.android.data.model.UserInfo
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

/**
 * 认证数据存储 - 对应 web 端的 localStorage
 * 使用 DataStore 替代 SharedPreferences
 */
class AuthStorage(private val context: Context) {
    
    companion object {
        private const val STORAGE_NAME = "choicerealm_android_auth"
        private val TOKEN_KEY = stringPreferencesKey("token")
        private val USER_KEY = stringPreferencesKey("user")
        
        private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(
            name = STORAGE_NAME
        )
    }
    
    private val gson = Gson()
    
    // 读取 token
    val tokenFlow: Flow<String> = context.dataStore.data.map { preferences ->
        preferences[TOKEN_KEY] ?: ""
    }
    
    // 读取用户信息
    val userFlow: Flow<UserInfo?> = context.dataStore.data.map { preferences ->
        val userJson = preferences[USER_KEY]
        if (userJson != null) {
            try {
                gson.fromJson(userJson, UserInfo::class.java)
            } catch (e: Exception) {
                null
            }
        } else {
            null
        }
    }
    
    // 保存认证信息
    suspend fun saveAuth(token: String, user: UserInfo) {
        context.dataStore.edit { preferences ->
            preferences[TOKEN_KEY] = token
            preferences[USER_KEY] = gson.toJson(user)
        }
    }
    
    // 清除认证信息
    suspend fun clearAuth() {
        context.dataStore.edit { preferences ->
            preferences.remove(TOKEN_KEY)
            preferences.remove(USER_KEY)
        }
    }
    
    // 同步读取 token（用于初始化）
    suspend fun getToken(): String {
        return tokenFlow.first()
    }
    
    // 同步读取用户信息（用于初始化）
    suspend fun getUser(): UserInfo? {
        return userFlow.first()
    }
}
