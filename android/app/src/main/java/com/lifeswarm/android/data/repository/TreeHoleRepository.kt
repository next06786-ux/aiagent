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
 * 树洞数据仓库
 */
class TreeHoleRepository {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val gson = Gson()
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()
    
    companion object {
        private const val TAG = "TreeHoleRepository"
    }
    
    /**
     * 获取所有树洞列表
     */
    suspend fun getAllTreeHoles(hours: Int = 168): Result<List<TreeHole>> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/tree-hole/tree-holes?hours=$hours")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "获取树洞列表响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "获取失败"))
            }
            
            val treeHoles = gson.fromJson(
                gson.toJson(apiResponse.data),
                Array<TreeHole>::class.java
            ).toList()
            
            Result.success(treeHoles)
            
        } catch (e: Exception) {
            Log.e(TAG, "获取树洞列表失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 获取用户创建的树洞
     */
    suspend fun getUserTreeHoles(userId: String, hours: Int = 168): Result<List<TreeHole>> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/tree-hole/user/$userId?hours=$hours")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "获取用户树洞响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "获取失败"))
            }
            
            val treeHoles = gson.fromJson(
                gson.toJson(apiResponse.data),
                Array<TreeHole>::class.java
            ).toList()
            
            Result.success(treeHoles)
            
        } catch (e: Exception) {
            Log.e(TAG, "获取用户树洞失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 创建树洞
     */
    suspend fun createTreeHole(userId: String, title: String, description: String): Result<String> = withContext(Dispatchers.IO) {
        try {
            val requestBody = CreateTreeHoleRequest(
                userId = userId,
                title = title,
                description = description
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "创建树洞请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/tree-hole/create")
                .post(json.toRequestBody(jsonMediaType))
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "创建树洞响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "创建失败"))
            }
            
            // 提取 tree_hole_id
            val dataMap = apiResponse.data as? Map<*, *>
            val treeHoleId = dataMap?.get("tree_hole_id") as? String
                ?: return@withContext Result.failure(Exception("未返回树洞ID"))
            
            Result.success(treeHoleId)
            
        } catch (e: Exception) {
            Log.e(TAG, "创建树洞失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 获取树洞消息列表
     */
    suspend fun getTreeHoleMessages(treeHoleId: String, limit: Int = 100, hours: Int = 168): Result<List<TreeHoleMessage>> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/tree-hole/messages/$treeHoleId?limit=$limit&hours=$hours")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "获取树洞消息响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "获取失败"))
            }
            
            val messages = gson.fromJson(
                gson.toJson(apiResponse.data),
                Array<TreeHoleMessage>::class.java
            ).toList()
            
            Result.success(messages)
            
        } catch (e: Exception) {
            Log.e(TAG, "获取树洞消息失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 发送消息到树洞
     */
    suspend fun sendMessage(treeHoleId: String, userId: String, content: String, isAnonymous: Boolean = true): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val requestBody = SendMessageRequest(
                treeHoleId = treeHoleId,
                userId = userId,
                content = content,
                isAnonymous = isAnonymous
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "发送消息请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/tree-hole/messages")
                .post(json.toRequestBody(jsonMediaType))
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "发送消息响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "发送失败"))
            }
            
            Result.success(Unit)
            
        } catch (e: Exception) {
            Log.e(TAG, "发送消息失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 获取热门决策
     */
    suspend fun getTrendingDecisions(timeWindow: Int = 168): Result<List<TrendingDecision>> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/tree-hole/trending-decisions?time_window=$timeWindow")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "获取热门决策响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.code != 200) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "获取失败"))
            }
            
            // 提取 decisions 数组
            val dataMap = apiResponse.data as? Map<*, *>
            val decisionsData = dataMap?.get("decisions")
            
            val decisions = gson.fromJson(
                gson.toJson(decisionsData),
                Array<TrendingDecision>::class.java
            ).toList()
            
            Result.success(decisions)
            
        } catch (e: Exception) {
            Log.e(TAG, "获取热门决策失败", e)
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
