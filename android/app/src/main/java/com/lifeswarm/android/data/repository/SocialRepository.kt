package com.lifeswarm.android.data.repository

import android.util.Log
import com.google.gson.Gson
import com.lifeswarm.android.data.model.*
import com.lifeswarm.android.data.remote.ApiConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

/**
 * 社交功能数据仓库
 */
class SocialRepository {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val gson = Gson()
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()
    
    companion object {
        private const val TAG = "SocialRepository"
    }
    
    /**
     * 搜索用户
     */
    suspend fun searchUsers(query: String, userId: String, limit: Int = 10): Result<List<SearchResult>> = withContext(Dispatchers.IO) {
        try {
            val requestBody = SearchUsersRequest(
                query = query,
                userId = userId,
                limit = limit
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "搜索用户请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/social/search-users")
                .post(json.toRequestBody(jsonMediaType))
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "搜索用户响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "搜索失败"))
            }
            
            val results = gson.fromJson(
                gson.toJson(apiResponse.data),
                Array<SearchResult>::class.java
            ).toList()
            
            Result.success(results)
            
        } catch (e: Exception) {
            Log.e(TAG, "搜索用户失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 发送好友请求
     */
    suspend fun sendFriendRequest(fromUserId: String, toUserId: String, message: String = ""): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val requestBody = SendFriendRequestPayload(
                fromUserId = fromUserId,
                toUserId = toUserId,
                message = message
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "发送好友请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/social/send-friend-request")
                .post(json.toRequestBody(jsonMediaType))
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "发送好友请求响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "发送失败"))
            }
            
            Result.success(Unit)
            
        } catch (e: Exception) {
            Log.e(TAG, "发送好友请求失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 获取好友请求列表
     */
    suspend fun getFriendRequests(userId: String): Result<List<FriendRequest>> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/social/friend-requests/$userId")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "获取好友请求响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "获取失败"))
            }
            
            val requests = gson.fromJson(
                gson.toJson(apiResponse.data),
                Array<FriendRequest>::class.java
            ).toList()
            
            Result.success(requests)
            
        } catch (e: Exception) {
            Log.e(TAG, "获取好友请求失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 接受好友请求
     */
    suspend fun acceptFriendRequest(requestId: String, userId: String): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val requestBody = HandleFriendRequestPayload(
                requestId = requestId,
                userId = userId
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "接受好友请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/social/accept-friend-request")
                .post(json.toRequestBody(jsonMediaType))
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "接受好友请求响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "操作失败"))
            }
            
            Result.success(Unit)
            
        } catch (e: Exception) {
            Log.e(TAG, "接受好友请求失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 拒绝好友请求
     */
    suspend fun rejectFriendRequest(requestId: String, userId: String): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val requestBody = HandleFriendRequestPayload(
                requestId = requestId,
                userId = userId
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "拒绝好友请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/social/reject-friend-request")
                .post(json.toRequestBody(jsonMediaType))
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "拒绝好友请求响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "操作失败"))
            }
            
            Result.success(Unit)
            
        } catch (e: Exception) {
            Log.e(TAG, "拒绝好友请求失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 获取好友列表
     */
    suspend fun getFriends(userId: String): Result<List<Friend>> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/social/friends/$userId")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "获取好友列表响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "获取失败"))
            }
            
            val friends = gson.fromJson(
                gson.toJson(apiResponse.data),
                Array<Friend>::class.java
            ).toList()
            
            Result.success(friends)
            
        } catch (e: Exception) {
            Log.e(TAG, "获取好友列表失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 删除好友
     */
    suspend fun removeFriend(userId: String, friendId: String): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val requestBody = RemoveFriendPayload(
                userId = userId,
                friendId = friendId
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "删除好友请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/social/remove-friend")
                .post(json.toRequestBody(jsonMediaType))
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "删除好友响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "操作失败"))
            }
            
            Result.success(Unit)
            
        } catch (e: Exception) {
            Log.e(TAG, "删除好友失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * API 响应包装类
     */
    private data class ApiResponse(
        val code: Int,
        val message: String?,
        val data: Any?
    )
}
