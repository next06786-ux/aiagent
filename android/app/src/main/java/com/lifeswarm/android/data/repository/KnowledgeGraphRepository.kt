package com.lifeswarm.android.data.repository

import com.lifeswarm.android.data.model.*
import com.lifeswarm.android.data.remote.ApiException
import com.lifeswarm.android.data.remote.ApiService

/**
 * 知识图谱仓库 - 对应 web/src/services/futureOs.ts
 */
class KnowledgeGraphRepository(
    private val apiService: ApiService
) {
    
    /**
     * 获取人际关系图谱 - 对应 web 端的 getPeopleGraphView
     */
    suspend fun getPeopleGraph(request: PeopleGraphRequest): KnowledgeGraphView {
        val response = apiService.getPeopleGraph(request)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "获取人际关系图谱失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (!result.success || result.data == null) {
            throw ApiException(
                result.message ?: "获取人际关系图谱失败",
                500,
                result
            )
        }
        
        return result.data
    }
    
    /**
     * 获取职业图谱 - 对应 web 端的 getCareerGraphView
     */
    suspend fun getCareerGraph(request: CareerGraphRequest): KnowledgeGraphView {
        val response = apiService.getCareerGraph(request)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "获取职业图谱失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (!result.success || result.data == null) {
            throw ApiException(
                result.message ?: "获取职业图谱失败",
                500,
                result
            )
        }
        
        return result.data
    }
    
    /**
     * 获取升学规划图谱 - 对应 web 端的 getEducationGraphView
     */
    suspend fun getEducationGraph(request: EducationGraphRequest): KnowledgeGraphView {
        val response = apiService.getEducationGraph(request)
        
        if (!response.isSuccessful || response.body() == null) {
            throw ApiException(
                "获取升学规划图谱失败",
                response.code(),
                response.errorBody()?.string()
            )
        }
        
        val result = response.body()!!
        
        if (!result.success || result.data == null) {
            throw ApiException(
                result.message ?: "获取升学规划图谱失败",
                500,
                result
            )
        }
        
        return result.data
    }
}
