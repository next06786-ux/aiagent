package com.lifeswarm.android.data.remote

import android.util.Log
import com.google.gson.Gson
import com.lifeswarm.android.data.model.ChatSocketRequest
import com.lifeswarm.android.data.model.WebSocketMessage
import okhttp3.*
import okio.ByteString

/**
 * WebSocket 客户端 - 对应 web/src/services/api.ts 的 createSocket
 */
class WebSocketClient(
    private val path: String,
    private val handlers: ChatSocketHandlers
) {
    
    companion object {
        private const val TAG = "WebSocketClient"
    }
    
    private var webSocket: WebSocket? = null
    private val gson = Gson()
    private var thinking = StringBuilder()
    private var answer = StringBuilder()
    
    interface ChatSocketHandlers {
        fun onStart(sessionId: String) {}
        fun onProgress(progress: String) {}
        fun onThinking(thinking: String) {}
        fun onAnswer(answer: String) {}
        fun onNavigation(navData: Map<String, Any>) {}
        fun onDone() {}
        fun onError(message: String) {}
    }
    
    fun connect(payload: ChatSocketRequest) {
        val wsPath = if (path.startsWith("/")) path else "/$path"
        val wsUrl = "${ApiConfig.WS_BASE_URL}$wsPath"
        
        Log.d(TAG, "[WebSocket] 直接连接: $wsUrl")
        
        val request = Request.Builder()
            .url(wsUrl)
            .build()
        
        val client = OkHttpClient.Builder()
            .build()
        
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.d(TAG, "[WebSocket] 连接已打开，发送消息: $payload")
                val json = gson.toJson(payload)
                webSocket.send(json)
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val message = gson.fromJson(text, WebSocketMessage::class.java)
                    val type = message.type
                    val content = message.content ?: ""
                    
                    Log.d(TAG, "[WebSocket] 收到消息: type=$type, contentLength=${content.length}")
                    
                    when (type) {
                        "start" -> {
                            handlers.onStart(message.sessionId ?: "")
                        }
                        "progress" -> {
                            handlers.onProgress(content)
                        }
                        "thinking_chunk" -> {
                            thinking.append(content)
                            handlers.onThinking(thinking.toString())
                        }
                        "thinking" -> {
                            thinking = StringBuilder(content)
                            handlers.onThinking(thinking.toString())
                        }
                        "answer_chunk" -> {
                            answer.append(content)
                            handlers.onAnswer(answer.toString())
                        }
                        "answer" -> {
                            answer = StringBuilder(content)
                            handlers.onAnswer(answer.toString())
                        }
                        "navigation" -> {
                            try {
                                // 解析完整的导航消息
                                @Suppress("UNCHECKED_CAST")
                                val fullMessage = gson.fromJson(text, Map::class.java) as Map<String, Any>
                                
                                Log.d(TAG, "[WebSocket] 导航消息详情: $fullMessage")
                                
                                handlers.onNavigation(fullMessage)
                            } catch (e: Exception) {
                                Log.e(TAG, "[WebSocket] 解析导航消息失败", e)
                            }
                        }
                        "done" -> {
                            handlers.onDone()
                            webSocket.close(1000, "Done")
                        }
                        "error" -> {
                            handlers.onError(content.ifEmpty { "聊天流式连接出错" })
                            webSocket.close(1000, "Error")
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "[WebSocket] 解析消息失败", e)
                    handlers.onError(e.message ?: "解析聊天事件失败")
                }
            }
            
            override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                Log.d(TAG, "[WebSocket] 收到二进制消息: ${bytes.hex()}")
            }
            
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "[WebSocket] 连接关闭中: code=$code, reason=$reason")
                webSocket.close(1000, null)
            }
            
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "[WebSocket] 连接已关闭: code=$code, reason=$reason")
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "[WebSocket] 连接错误", t)
                handlers.onError("聊天连接异常，请稍后重试")
            }
        })
    }
    
    fun close() {
        webSocket?.close(1000, "Client closed")
        webSocket = null
    }
    
    fun disconnect() {
        close()
    }
}
