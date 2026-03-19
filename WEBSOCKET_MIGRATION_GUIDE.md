# WebSocket 迁移指南

## 当前问题
前端使用 HTTP 轮询机制，每 500ms 发送一次请求，在 AI 处理期间会产生大量 HTTP 请求。

## 解决方案
使用 WebSocket 实现实时双向通信，后端主动推送进度更新。

## 后端 WebSocket 端点
已实现：`ws://localhost:8000/ws/chat/{session_id}`

## 前端改造步骤

### 1. 在 AIConversationService.ets 中添加 WebSocket 支持

```typescript
import webSocket from '@ohos.net.webSocket';

export class AIConversationService {
  private ws: webSocket.WebSocket | null = null;
  
  /**
   * 使用 WebSocket 进行聊天（实时推送）
   */
  async chatWithWebSocket(
    message: string,
    onProgress: (progress: string) => void,
    onThinking: (thinking: string) => void,
    onAnswer: (answer: string) => void,
    onComplete: () => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      // 1. 先调用 /api/chat/start 获取 session_id
      const startResponse = await this.chatStart(message);
      const sessionId = startResponse.session_id;
      
      // 2. 建立 WebSocket 连接
      this.ws = webSocket.createWebSocket();
      const wsUrl = `ws://${ApiConfig.getBaseUrl().replace('http://', '')}/ws/chat/${sessionId}`;
      
      // 3. 设置事件监听
      this.ws.on('open', () => {
        console.info('[WebSocket] 连接已建立');
      });
      
      this.ws.on('message', (err, value) => {
        if (err) {
          console.error('[WebSocket] 接收消息错误:', err);
          return;
        }
        
        try {
          const data = JSON.parse(value as string);
          
          switch (data.type) {
            case 'progress':
              onProgress(data.content);
              break;
            case 'thinking':
              onThinking(data.content);
              break;
            case 'answer':
              onAnswer(data.content);
              break;
            case 'complete':
              onComplete();
              this.closeWebSocket();
              break;
            case 'error':
              onError(data.content);
              this.closeWebSocket();
              break;
          }
        } catch (parseErr) {
          console.error('[WebSocket] 解析消息失败:', parseErr);
        }
      });
      
      this.ws.on('close', () => {
        console.info('[WebSocket] 连接已关闭');
      });
      
      this.ws.on('error', (err) => {
        console.error('[WebSocket] 连接错误:', err);
        onError('WebSocket 连接失败');
      });
      
      // 4. 连接到服务器
      await this.ws.connect(wsUrl);
      
    } catch (err) {
      console.error('[WebSocket] 初始化失败:', err);
      onError(err.message);
    }
  }
  
  /**
   * 关闭 WebSocket 连接
   */
  private closeWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

### 2. 在 AIChat.ets 中使用 WebSocket

```typescript
async sendMessage() {
  if (!this.inputText.trim() || this.isLoading) {
    return;
  }
  
  const userMessage = this.inputText;
  this.inputText = '';
  this.isLoading = true;
  this.startLoadingAnimation();
  
  // 添加用户消息
  const userMsg: ChatMessage = {
    id: Date.now().toString(),
    role: 'user',
    content: userMessage,
    timestamp: Date.now()
  };
  this.messages.push(userMsg);
  
  // 添加 AI 消息占位符
  const aiMsgId = (Date.now() + 1).toString();
  const aiMsg: ChatMessage = {
    id: aiMsgId,
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
    thinking: ''
  };
  this.messages.push(aiMsg);
  
  try {
    // 使用 WebSocket
    await this.aiService.chatWithWebSocket(
      userMessage,
      // onProgress
      (progress: string) => {
        this.processingProgress = progress;
      },
      // onThinking
      (thinking: string) => {
        this.processingProgress = '';
        this.updateMessage(aiMsgId, 'thinking', thinking);
      },
      // onAnswer
      (answer: string) => {
        this.updateMessage(aiMsgId, 'content', answer);
      },
      // onComplete
      () => {
        this.processingProgress = '';
        this.stopLoadingAnimation();
        this.showFeedback = true;
        this.isLoading = false;
      },
      // onError
      (error: string) => {
        console.error('[AIChat] WebSocket 错误:', error);
        this.processingProgress = '';
        this.stopLoadingAnimation();
        this.isLoading = false;
        
        this.getUIContext().getPromptAction().showToast({
          message: `发送失败: ${error}`,
          duration: 3000
        });
      }
    );
    
  } catch (err) {
    console.error('[AIChat] 发送消息失败:', err);
    this.isLoading = false;
  }
}
```

### 3. 后端需要修改 WebSocket 推送逻辑

在 `backend/main.py` 的 `process_chat()` 函数中，需要通过 WebSocket 推送进度：

```python
from websocket_manager import get_connection_manager

async def process_chat():
    manager = get_connection_manager()
    
    try:
        # 推送进度
        await manager.send_progress(session_id, "正在初始化...")
        
        # 推送思考过程
        await manager.send_thinking(session_id, thinking_process)
        
        # 推送回复内容
        await manager.send_answer(session_id, final_response)
        
        # 推送完成信号
        await manager.send_complete(session_id)
        
    except Exception as e:
        await manager.send_error(session_id, str(e))
```

## 优势对比

### HTTP 轮询（当前）
- ❌ 每 500ms 发送一次请求
- ❌ 在长时间处理时产生大量无效请求
- ❌ 增加服务器负载
- ✅ 实现简单

### WebSocket（推荐）
- ✅ 实时双向通信
- ✅ 服务器主动推送，无需轮询
- ✅ 减少网络开销
- ✅ 更好的用户体验
- ❌ 实现稍复杂

## 当前临时方案
已将轮询间隔从 100ms 改为 500ms，减少 80% 的请求量。
