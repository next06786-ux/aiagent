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
 * 平行人生（塔罗牌游戏）数据仓库
 */
class ParallelLifeRepository {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val gson = Gson()
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()
    
    companion object {
        private const val TAG = "ParallelLifeRepository"
    }
    
    /**
     * 抽取塔罗牌
     */
    suspend fun drawCard(userId: String, drawnCards: List<String>? = null): Result<TarotCard> = withContext(Dispatchers.IO) {
        try {
            val requestBody = DrawCardRequest(
                userId = userId,
                drawnCards = drawnCards
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "抽牌请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/v5/parallel-life/draw-card")
                .post(json.toRequestBody(jsonMediaType))
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "抽牌响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.success != true) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "抽牌失败"))
            }
            
            val card = gson.fromJson(gson.toJson(apiResponse.data), TarotCard::class.java)
            Result.success(card)
            
        } catch (e: Exception) {
            Log.e(TAG, "抽牌失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 提交选择
     */
    suspend fun submitChoice(
        userId: String,
        card: String,
        cardKey: String,
        dimension: String,
        dimensionKey: String,
        scenario: String,
        choice: String,
        tendency: String
    ): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val requestBody = SubmitChoiceRequest(
                userId = userId,
                card = card,
                cardKey = cardKey,
                dimension = dimension,
                dimensionKey = dimensionKey,
                scenario = scenario,
                choice = choice,
                tendency = tendency
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "提交选择请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/v5/parallel-life/submit-choice")
                .post(json.toRequestBody(jsonMediaType))
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "提交选择响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.success != true) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "提交失败"))
            }
            
            Result.success(Unit)
            
        } catch (e: Exception) {
            Log.e(TAG, "提交选择失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 获取决策画像
     */
    suspend fun getDecisionProfile(userId: String): Result<DecisionProfile> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/v5/parallel-life/decision-profile/$userId")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "获取画像响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.success != true) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "获取画像失败"))
            }
            
            val profile = gson.fromJson(gson.toJson(apiResponse.data), DecisionProfile::class.java)
            Result.success(profile)
            
        } catch (e: Exception) {
            Log.e(TAG, "获取画像失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 获取游戏统计
     */
    suspend fun getGameStats(userId: String): Result<GameStats> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/v5/parallel-life/game-stats/$userId")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "获取统计响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
            
            if (apiResponse.success != true) {
                return@withContext Result.failure(Exception(apiResponse.message ?: "获取统计失败"))
            }
            
            val stats = gson.fromJson(gson.toJson(apiResponse.data), GameStats::class.java)
            Result.success(stats)
            
        } catch (e: Exception) {
            Log.e(TAG, "获取统计失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * API 响应包装类
     */
    private data class ApiResponse(
        val success: Boolean?,
        val message: String?,
        val data: Any?
    )
}
