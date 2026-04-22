package com.lifeswarm.android.data.repository

import com.lifeswarm.android.data.model.*
import com.lifeswarm.android.data.remote.ApiService
import com.lifeswarm.android.data.remote.ApiException
import com.lifeswarm.android.data.remote.StartCollectionRequest
import com.lifeswarm.android.data.remote.GenerateOptionsRequest

/**
 * 决策仓库 - 对应 web/src/services/decision.ts
 */
class DecisionRepository(
    private val apiService: ApiService
) {
    
    /**
     * 获取决策历史
     */
    suspend fun getDecisionHistory(userId: String): List<DecisionHistoryRecord> {
        val response = apiService.getDecisionHistory(userId)
        
        if (!response.isSuccessful || response.body() == null) {
            return emptyList()
        }
        
        val result = response.body()!!
        
        if (result.code != 200) {
            return emptyList()
        }
        
        return result.data ?: emptyList()
    }
    
    /**
     * 获取决策记录详情
     */
    suspend fun getDecisionRecord(simulationId: String): DecisionRecord {
        val response = apiService.getDecisionRecord(simulationId)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "获取推演详情失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (result.code != 200 || result.data == null) {
            throw ApiException(
                result.message ?: "获取推演详情失败",
                result.code,
                result
            )
        }
        
        return result.data
    }
    
    /**
     * 开始决策信息采集
     */
    suspend fun startDecisionCollection(
        userId: String,
        initialQuestion: String,
        decisionType: String = "general"
    ): CollectionSession {
        val payload = StartCollectionRequest(
            user_id = userId,
            initial_question = initialQuestion,
            decision_type = decisionType
        )
        
        val response = apiService.startDecisionCollection(payload)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "启动信息采集失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (result.code != 200 || result.data == null) {
            throw ApiException(
                result.message ?: "启动信息采集失败",
                result.code,
                result
            )
        }
        
        return result.data
    }
    
    /**
     * 继续决策信息采集
     */
    suspend fun continueDecisionCollection(
        sessionId: String,
        userResponse: String
    ): CollectionContinueResponse {
        val payload = mapOf(
            "session_id" to sessionId,
            "user_response" to userResponse
        )
        
        val response = apiService.continueDecisionCollection(payload)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "继续采集失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (result.code != 200 || result.data == null) {
            throw ApiException(
                result.message ?: "继续采集失败",
                result.code,
                result
            )
        }
        
        return result.data
    }
    
    /**
     * 生成决策选项
     */
    suspend fun generateDecisionOptions(
        sessionId: String,
        userOptions: List<String>
    ): List<OptionInput> {
        val payload = GenerateOptionsRequest(
            session_id = sessionId,
            user_options = userOptions
        )
        
        val response = apiService.generateDecisionOptions(payload)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "生成选项失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (result.code != 200 || result.data == null) {
            throw ApiException(
                result.message ?: "生成选项失败",
                result.code,
                result
            )
        }
        
        return result.data.aiOptions
    }
}
