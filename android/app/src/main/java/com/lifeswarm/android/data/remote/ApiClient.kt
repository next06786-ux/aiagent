package com.lifeswarm.android.data.remote

import android.util.Log
import com.google.gson.GsonBuilder
import com.lifeswarm.android.data.model.*
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

/**
 * 统一的 API 客户端 - 包含接口定义和实例创建
 */

// ============ API 接口定义 ============
interface ApiService {
    
    // 认证相关 API
    @POST("/api/auth/login")
    suspend fun login(@Body payload: LoginPayload): Response<ApiEnvelope<LoginResponse>>
    
    @POST("/api/auth/register")
    suspend fun register(@Body payload: RegisterPayload): Response<ApiEnvelope<LoginResponse>>
    
    @POST("/api/auth/logout")
    suspend fun logout(@Body request: Map<String, String>): Response<ApiEnvelope<Any>>
    
    @POST("/api/auth/verify-token")
    suspend fun verifyToken(@Body request: Map<String, String>): Response<ApiEnvelope<TokenVerifyResponse>>
    
    @GET("/api/auth/user/{userId}")
    suspend fun getUser(@Path("userId") userId: String): Response<ApiEnvelope<UserInfo>>
    
    @PUT("/api/auth/user/{userId}")
    suspend fun updateUser(
        @Path("userId") userId: String,
        @Body payload: UpdateProfilePayload
    ): Response<ApiEnvelope<UserInfo>>
    
    @POST("/api/auth/change-password")
    suspend fun changePassword(@Body request: Map<String, Any>): Response<ApiEnvelope<Any>>
    
    // 聊天相关 API
    @GET("/api/v4/conversations/{userId}/list")
    suspend fun listConversations(@Path("userId") userId: String): Response<SuccessEnvelope<List<ConversationItem>>>
    
    @GET("/api/v4/conversations/{userId}/{sessionId}/messages")
    suspend fun getConversationMessages(
        @Path("userId") userId: String,
        @Path("sessionId") sessionId: String
    ): Response<SuccessEnvelope<List<ConversationMessageData>>>
    
    @POST("/api/v4/conversations/{userId}/create")
    suspend fun createConversation(@Path("userId") userId: String): Response<SuccessEnvelope<Map<String, String>>>
    
    // 决策相关 API - 对应 web/src/services/decision.ts
    
    @GET("/api/decision/enhanced/history/{userId}")
    suspend fun getDecisionHistory(@Path("userId") userId: String): Response<ApiEnvelope<List<DecisionHistoryRecord>>>
    
    @GET("/api/decision/enhanced/record/{simulationId}")
    suspend fun getDecisionRecord(@Path("simulationId") simulationId: String): Response<ApiEnvelope<DecisionRecord>>
    
    @POST("/api/decision/enhanced/collect/start")
    suspend fun startDecisionCollection(@Body payload: StartCollectionRequest): Response<ApiEnvelope<CollectionSession>>
    
    @POST("/api/decision/enhanced/collect/continue")
    suspend fun continueDecisionCollection(@Body payload: Map<String, String>): Response<ApiEnvelope<CollectionContinueResponse>>
    
    @POST("/api/decision/enhanced/generate-options")
    suspend fun generateDecisionOptions(@Body payload: GenerateOptionsRequest): Response<ApiEnvelope<GenerateOptionsResponse>>
    
    // 知识图谱相关 API - 对应 web/src/services/futureOs.ts
    
    @POST("/api/v5/future-os/people-graph")
    suspend fun getPeopleGraph(@Body payload: PeopleGraphRequest): Response<SuccessEnvelope<KnowledgeGraphView>>
    
    @POST("/api/v5/future-os/career-graph")
    suspend fun getCareerGraph(@Body payload: CareerGraphRequest): Response<SuccessEnvelope<KnowledgeGraphView>>
    
    @POST("/api/v5/future-os/education-graph")
    suspend fun getEducationGraph(@Body payload: EducationGraphRequest): Response<SuccessEnvelope<KnowledgeGraphView>>
    
    // 路由分析 API 已移除 - 导航建议现在通过 WebSocket 的 navigation 消息返回
    // 参考 web/src/services/chat.ts 的实现
    // @POST("/api/v5/future-os/route")
    // suspend fun analyzeRoute(@Body payload: RouteAnalysisRequest): Response<SuccessEnvelope<RouteAnalysisResponse>>
}

// ============ API 客户端单例 ============
object ApiClient {
    
    private const val TAG = "ApiClient"
    
    private val gson = GsonBuilder().setLenient().create()
    
    private val loggingInterceptor = HttpLoggingInterceptor { message ->
        Log.d(TAG, message)
    }.apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val timingInterceptor = okhttp3.Interceptor { chain ->
        val request = chain.request()
        val startTime = System.currentTimeMillis()
        Log.d(TAG, "[API] 发起请求: ${request.url}")
        val response = chain.proceed(request)
        val fetchTime = System.currentTimeMillis() - startTime
        Log.d(TAG, "[API] 收到响应: ${request.url} 耗时: ${fetchTime}ms")
        response
    }
    
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(timingInterceptor)
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)  // 增加到120秒，因为 AI 生成选项需要较长时间
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(ApiConfig.API_BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create(gson))
        .build()
    
    val apiService: ApiService = retrofit.create(ApiService::class.java)
}

// ============ 请求数据类 ============

/**
 * 开始决策采集请求
 */
data class StartCollectionRequest(
    val user_id: String,
    val initial_question: String,
    val decision_type: String = "general"
)

/**
 * 生成决策选项请求
 */
data class GenerateOptionsRequest(
    val session_id: String,
    val user_options: List<String>
)

/**
 * 路由分析请求 - 已废弃，保留数据类定义以防其他地方引用
 * 导航建议现在通过 WebSocket 的 navigation 消息返回
 */
data class RouteAnalysisRequest(
    val user_id: String,
    val message: String
)

/**
 * 路由分析响应 - 已废弃，保留数据类定义以防其他地方引用
 * 导航建议现在通过 WebSocket 的 navigation 消息返回
 */
data class RouteAnalysisResponse(
    val recommended_module: String,
    val recommended_view: String?,
    val reason: String
)
