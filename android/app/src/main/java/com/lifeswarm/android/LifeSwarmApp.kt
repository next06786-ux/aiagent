package com.lifeswarm.android

import android.app.Application
import com.lifeswarm.android.data.local.AuthStorage
import com.lifeswarm.android.data.remote.ApiClient
import com.lifeswarm.android.data.repository.AuthRepository
import com.lifeswarm.android.data.repository.ChatRepository
import com.lifeswarm.android.data.repository.DecisionRepository
import com.lifeswarm.android.data.repository.KnowledgeGraphRepository

/**
 * 应用程序类 - 初始化全局依赖
 */
class LifeSwarmApp : Application() {
    
    // 全局单例
    lateinit var authStorage: AuthStorage
        private set
    
    lateinit var authRepository: AuthRepository
        private set
    
    lateinit var chatRepository: ChatRepository
        private set
    
    lateinit var decisionRepository: DecisionRepository
        private set
    
    lateinit var knowledgeGraphRepository: KnowledgeGraphRepository
        private set
    
    override fun onCreate() {
        super.onCreate()
        
        // 初始化存储
        authStorage = AuthStorage(applicationContext)
        
        // 初始化仓库
        authRepository = AuthRepository(
            ApiClient.apiService,
            authStorage
        )
        
        chatRepository = ChatRepository(
            ApiClient.apiService
        )
        
        decisionRepository = DecisionRepository(
            ApiClient.apiService
        )
        
        knowledgeGraphRepository = KnowledgeGraphRepository(
            ApiClient.apiService
        )
    }
}
