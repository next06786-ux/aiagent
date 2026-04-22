package com.lifeswarm.android.data.remote

import com.lifeswarm.android.BuildConfig

/**
 * API 配置 - 对应 web/src/services/api.ts
 */
object ApiConfig {
    // 对应 web 端的 API_BASE_URL
    val API_BASE_URL: String = BuildConfig.API_BASE_URL.trimEnd('/')
    
    // WebSocket 地址
    val WS_BASE_URL: String = API_BASE_URL
        .replace("http://", "ws://")
        .replace("https://", "wss://")
    
    init {
        println("[API] 配置信息:")
        println("  API_BASE_URL: $API_BASE_URL")
        println("  WS_BASE_URL: $WS_BASE_URL")
        println("  是否使用localhost: ${API_BASE_URL.contains("localhost")}")
    }
}

/**
 * API 错误 - 对应 web 端的 ApiError
 */
class ApiException(
    message: String,
    val status: Int = 500,
    val details: Any? = null
) : Exception(message)
