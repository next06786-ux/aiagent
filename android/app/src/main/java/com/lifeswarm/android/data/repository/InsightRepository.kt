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
 * 智慧洞察数据仓库
 */
class InsightRepository {
    private val client = OkHttpClient.Builder()
        .connectTimeout(120, TimeUnit.SECONDS)  // 增加到 120 秒
        .readTimeout(180, TimeUnit.SECONDS)     // 增加到 180 秒（3分钟），给 LLM 足够的分析时间
        .writeTimeout(60, TimeUnit.SECONDS)
        .build()
    
    private val gson = com.google.gson.GsonBuilder()
        .setLenient()
        .serializeNulls()
        .create()
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()
    
    companion object {
        private const val TAG = "InsightRepository"
    }
    
    // ==================== 智能洞察（涌现发现）====================
    
    /**
     * 获取仪表盘数据
     */
    suspend fun getDashboard(userId: String): Result<DashboardData> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/v4/emergence/dashboard/$userId")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "获取仪表盘响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, Map::class.java)
            val success = apiResponse["success"] as? Boolean ?: false
            
            if (!success) {
                return@withContext Result.failure(Exception("获取失败"))
            }
            
            val data = gson.fromJson(
                gson.toJson(apiResponse["data"]),
                DashboardData::class.java
            )
            
            Result.success(data)
            
        } catch (e: Exception) {
            Log.e(TAG, "获取仪表盘失败", e)
            Result.failure(e)
        }
    }
    
    /**
     * 获取洞察列表
     */
    suspend fun getInsights(userId: String, limit: Int = 50): Result<List<SmartInsight>> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/v4/emergence/insights/$userId?limit=$limit")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "获取洞察列表响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, Map::class.java)
            val success = apiResponse["success"] as? Boolean ?: false
            
            if (!success) {
                return@withContext Result.failure(Exception("获取失败"))
            }
            
            val insights = gson.fromJson(
                gson.toJson(apiResponse["insights"]),
                Array<SmartInsight>::class.java
            ).toList()
            
            Result.success(insights)
            
        } catch (e: Exception) {
            Log.e(TAG, "获取洞察列表失败", e)
            Result.failure(e)
        }
    }
    
    // ==================== Agent 洞察报告 ====================
    
    /**
     * 生成人际关系洞察报告
     */
    suspend fun generateRelationshipInsight(
        token: String,
        query: String = "分析我的人际关系网络",
        focusArea: String? = null
    ): Result<AgentInsightReport> = withContext(Dispatchers.IO) {
        try {
            val requestBody = AgentInsightRequest(
                query = query,
                focusArea = focusArea
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "生成人际关系洞察请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/insights/realtime/relationship/insight")
                .post(json.toRequestBody(jsonMediaType))
                .addHeader("Authorization", "Bearer $token")
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "生成人际关系洞察响应码: ${response.code}")
            Log.d(TAG, "生成人际关系洞察响应体长度: ${responseBody.length}")
            Log.d(TAG, "生成人际关系洞察响应体前500字符: ${responseBody.take(500)}")
            
            if (!response.isSuccessful) {
                Log.e(TAG, "HTTP错误: ${response.code}")
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            try {
                val apiResponse = gson.fromJson(responseBody, Map::class.java)
                Log.d(TAG, "API响应解析成功，包含键: ${apiResponse.keys}")
                
                val reportJson = gson.toJson(apiResponse["report"])
                Log.d(TAG, "报告JSON长度: ${reportJson.length}")
                Log.d(TAG, "报告JSON前500字符: ${reportJson.take(500)}")
                
                val report = gson.fromJson(reportJson, AgentInsightReport::class.java)
                Log.d(TAG, "报告对象解析成功: ${report.insightId}")
                
                Result.success(report)
            } catch (e: Exception) {
                Log.e(TAG, "JSON解析失败", e)
                Log.e(TAG, "失败的JSON: $responseBody")
                throw e
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "生成人际关系洞察失败", e)
            e.printStackTrace()
            Result.failure(e)
        }
    }
    
    /**
     * 生成教育升学洞察报告
     */
    suspend fun generateEducationInsight(
        token: String,
        query: String = "分析我的升学路径",
        targetSchool: String? = null,
        targetMajor: String? = null
    ): Result<AgentInsightReport> = withContext(Dispatchers.IO) {
        try {
            val requestBody = AgentInsightRequest(
                query = query,
                targetSchool = targetSchool,
                targetMajor = targetMajor
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "生成教育升学洞察请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/insights/realtime/education/insight")
                .post(json.toRequestBody(jsonMediaType))
                .addHeader("Authorization", "Bearer $token")
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "生成教育升学洞察响应码: ${response.code}")
            Log.d(TAG, "生成教育升学洞察响应体前500字符: ${responseBody.take(500)}")
            
            if (!response.isSuccessful) {
                Log.e(TAG, "HTTP错误: ${response.code}")
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            try {
                val apiResponse = gson.fromJson(responseBody, Map::class.java)
                val report = gson.fromJson(
                    gson.toJson(apiResponse["report"]),
                    AgentInsightReport::class.java
                )
                Log.d(TAG, "教育升学报告解析成功: ${report.insightId}")
                Result.success(report)
            } catch (e: Exception) {
                Log.e(TAG, "JSON解析失败", e)
                e.printStackTrace()
                throw e
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "生成教育升学洞察失败", e)
            e.printStackTrace()
            Result.failure(e)
        }
    }
    
    /**
     * 生成职业规划洞察报告
     */
    suspend fun generateCareerInsight(
        token: String,
        query: String = "分析我的职业发展路径",
        targetPosition: String? = null,
        targetIndustry: String? = null
    ): Result<AgentInsightReport> = withContext(Dispatchers.IO) {
        try {
            val requestBody = AgentInsightRequest(
                query = query,
                targetPosition = targetPosition,
                targetIndustry = targetIndustry
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "生成职业规划洞察请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/insights/realtime/career/insight")
                .post(json.toRequestBody(jsonMediaType))
                .addHeader("Authorization", "Bearer $token")
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "生成职业规划洞察响应码: ${response.code}")
            Log.d(TAG, "生成职业规划洞察响应体前500字符: ${responseBody.take(500)}")
            
            if (!response.isSuccessful) {
                Log.e(TAG, "HTTP错误: ${response.code}")
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            try {
                val apiResponse = gson.fromJson(responseBody, Map::class.java)
                val report = gson.fromJson(
                    gson.toJson(apiResponse["report"]),
                    AgentInsightReport::class.java
                )
                Log.d(TAG, "职业规划报告解析成功: ${report.insightId}")
                Result.success(report)
            } catch (e: Exception) {
                Log.e(TAG, "JSON解析失败", e)
                e.printStackTrace()
                throw e
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "生成职业规划洞察失败", e)
            e.printStackTrace()
            Result.failure(e)
        }
    }
    
    // ==================== 跨领域分析 ====================
    
    /**
     * 生成跨领域综合分析
     */
    suspend fun generateCrossDomainAnalysis(
        token: String,
        query: String,
        agentChain: List<String> = listOf("relationship", "education", "career", "cross_domain"),
        initialContext: Map<String, Any>? = null
    ): Result<CrossDomainAnalysisResult> = withContext(Dispatchers.IO) {
        try {
            val requestBody = CrossDomainAnalysisRequest(
                query = query,
                agentChain = agentChain,
                initialContext = initialContext
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "生成跨领域分析请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/insights/realtime/cross-domain/comprehensive-analysis")
                .post(json.toRequestBody(jsonMediaType))
                .addHeader("Authorization", "Bearer $token")
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "生成跨领域分析响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val result = gson.fromJson(responseBody, CrossDomainAnalysisResult::class.java)
            
            Result.success(result)
            
        } catch (e: Exception) {
            Log.e(TAG, "生成跨领域分析失败", e)
            Result.failure(e)
        }
    }
    
    // ==================== 生活领域洞察 ====================
    
    /**
     * 处理生活领域数据
     */
    suspend fun processLifeDomain(
        userId: String,
        text: String = "",
        sensors: Map<String, Any>? = null
    ): Result<ProcessResult> = withContext(Dispatchers.IO) {
        try {
            val requestBody = ProcessRequest(
                userId = userId,
                text = text,
                sensors = sensors
            )
            
            val json = gson.toJson(requestBody)
            Log.d(TAG, "处理生活领域请求: $json")
            
            val request = Request.Builder()
                .url("${ApiConfig.API_BASE_URL}/api/v4/process")
                .post(json.toRequestBody(jsonMediaType))
                .build()
            
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            
            Log.d(TAG, "处理生活领域响应: $responseBody")
            
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
            
            val apiResponse = gson.fromJson(responseBody, Map::class.java)
            val success = apiResponse["success"] as? Boolean ?: false
            
            if (!success) {
                return@withContext Result.failure(Exception("处理失败"))
            }
            
            val data = gson.fromJson(
                gson.toJson(apiResponse["data"]),
                ProcessResult::class.java
            )
            
            Result.success(data)
            
        } catch (e: Exception) {
            Log.e(TAG, "处理生活领域失败", e)
            Result.failure(e)
        }
    }
}
