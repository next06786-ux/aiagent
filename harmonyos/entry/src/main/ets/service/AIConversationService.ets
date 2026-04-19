/**
 * AI
 * Qwen3.5-Plus
 */
import preferences from '@ohos.data.preferences';
import common from '@ohos.app.ability.common';
import http from '@ohos.net.http';
import { HttpUtil } from '../utils/HttpUtil';
import { ApiConfig } from '../config/ApiConfig';
import { ConversationHistoryService } from './ConversationHistoryService';
import { getAuthService } from './AuthService';

// 处理逻辑
@Observed
export class ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  thinking?: string;
  
  constructor(id: string, role: 'user' | 'assistant', content: string, timestamp: number, thinking?: string) {
    this.id = id;
    this.role = role;
    this.content = content;
    this.timestamp = timestamp;
    this.thinking = thinking;
  }
}

// 会话信息
export interface ConversationSession {
  session_id: string;
  title: string;
  start_time: string;
  last_time: string;
  message_count: number;
  is_current: boolean;
}

// 聊天请求接口
interface ChatRequest {
  user_id: string;
  message: string;
  context: Record<string, string> | null;
  session_id?: string;  // 添加可选的 session_id
}

// 混合处理请求接口
interface HybridProcessRequest {
  user_id: string;
  input_data: Record<string, string>;
  enable_distillation: boolean;
}

// 反馈请求接口
interface FeedbackRequest {
  user_id: string;
  rating: number;
  helpful: boolean;
  action_taken: boolean;
  comments: string;
}

export class AIConversationService {
  private userId: string = '';
  private conversationHistory: ChatMessage[] = [];
  private historyService: ConversationHistoryService;
  private currentSessionId: string = '';
  private authService = getAuthService();
  private userIdLoaded: boolean = false;
  
  constructor() {
    this.userId = 'default_user'; // 默认值
    this.historyService = ConversationHistoryService.getInstance();
    // 延迟加载用户ID，不阻塞构造函数
    this.loadUserIdAsync();
  }
  
  /**
   * 异步加载用户ID（不阻塞）
   */
  private async loadUserIdAsync(): Promise<void> {
    if (this.userIdLoaded) return;
    
    try {
      // 从AuthService获取用户ID
      const user = await this.authService.getCurrentUserAsync();
      if (user) {
        this.userId = user.user_id;
        console.info('[AIConversationService] 从AuthService加载用户ID:', this.userId);
      } else {
        // 如果没有登录用户，尝试从旧的preferences加载
        const context = getContext(this) as common.UIAbilityContext;
        const prefs = await preferences.getPreferences(context, 'lifeswarm_prefs');
        this.userId = await prefs.get('user_id', 'default_user') as string;
        console.info('[AIConversationService] 从preferences加载用户ID:', this.userId);
      }
      this.userIdLoaded = true;
    } catch (err) {
      console.error('[AIConversationService] 加载用户ID失败:', err);
      this.userId = 'default_user';
      this.userIdLoaded = true;
    }
  }
  
  /**
   * 确保用户ID已加载
   */
  private async ensureUserIdLoaded(): Promise<void> {
    if (!this.userIdLoaded) {
      await this.loadUserIdAsync();
    }
  }
  
  /**
 * 服务类
 */
  async chatStream(
    message: string, 
    onThinking: (text: string) => void,
    onAnswer: (text: string) => void,
    onComplete: () => void,
    context: Record<string, string> | null = null
  ): Promise<void> {
    // 确保用户ID已加载
    await this.ensureUserIdLoaded();
    
    // 处理逻辑
    if (!this.historyService.getCurrentConversation()) {
      this.historyService.startConversation(this.userId);
    }
    
    // 构造后端期望的请求格式（必须包含user_id）
    const request: ChatRequest = {
      user_id: this.userId,
      message: message,
      context: context
    };
    
    try {
      console.info(`发送请求到: ${ApiConfig.getBaseUrl()}/api/chat/stream`);
      console.info(`请求数据: ${JSON.stringify(request)}`);
      
      // HttpUtil
      const response = await HttpUtil.postStream('/api/chat/stream', request, 
        (chunk: string) => {
          console.info(`[AIConversationService] chunk: ${chunk}`);
          try {
            const data = JSON.parse(chunk) as Record<string, string>;
            console.info(`[AIConversationService] chunk: type=${data.type}, content=${data.content?.length || 0}`);
            
            if (data.type === 'thinking') {
              onThinking(data.content || '');
            } else if (data.type === 'answer') {
              onAnswer(data.content || '');
            } else if (data.type === 'error') {
              throw new Error(data.content || '');
            }
          } catch (parseErr) {
            const error = parseErr as Error;
            console.warn(':', error.message, ':', chunk);
          }
        }
      );
      
      if (response.responseCode === 200) {
        console.info('[AIConversationService] ');
        onComplete();
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
      
    } catch (err) {
      const error = err as Error;
      console.error(':', error.message);
      throw new Error(`: ${error.message}`);
    }
  }
  
  /**
 * 服务类
 */
  async chatStart(message: string, context: Record<string, string> | null = null): Promise<Record<string, string>> {
    // 确保用户ID已加载
    await this.ensureUserIdLoaded();
    
    console.info('[AIConversationService] chatStart 开始');
    console.info('[AIConversationService] userId:', this.userId);
    console.info('[AIConversationService] message:', message);
    
    const request: ChatRequest = {
      user_id: this.userId,
      message: message,
      context: context
    };
    
    console.info('[AIConversationService] 请求数据:', JSON.stringify(request));
    
    try {
      console.info('[AIConversationService]  HttpUtil.post /api/chat/start');
      const response = await HttpUtil.post('/api/chat/start', request);
      
      console.info('[AIConversationService] :', response.responseCode);
      console.info('[AIConversationService] :', response.result);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        console.info('[AIConversationService] :', JSON.stringify(result));
        // 如果返回格式是 {code, message, data}，提取data部分
        if (result.data) {
          return result.data as Record<string, string>;
        }
        return result as Record<string, string>;
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error('[AIConversationService] :', error.message);
      throw new Error(error.message);
    }
  }
  
  /**
 * 服务类
 */
  async chatPoll(sessionId: string): Promise<Record<string, string>> {
    console.info('[AIConversationService] chatPoll session:', sessionId);
    
    try {
      const response = await HttpUtil.get(`/api/chat/poll/${sessionId}`);
      
      console.info('[AIConversationService] chatPoll :', response.responseCode);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        console.info('[AIConversationService] chatPoll :', JSON.stringify(result));
        // 如果返回格式是 {code, message, data}，提取data部分
        if (result.data) {
          return result.data as Record<string, string>;
        }
        return result as Record<string, string>;
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error('[AIConversationService] :', error.message);
      throw new Error(error.message);
    }
  }
  
  /**
   * 使用 WebSocket 流式聊天（真正的实时流式）
   * 
   * 这是 HarmonyOS 的最佳方案：WebSocket 支持真正的实时双向通信
   */
  async chatStreamWebSocket(
    message: string,
    onProgress: (progress: string) => void,
    onThinking: (thinking: string) => void,
    onAnswer: (answer: string) => void,
    onComplete: () => void,
    onError: (error: string) => void,
    context: Record<string, string> | null = null,
    sessionId: string | null = null,  // 添加 sessionId 参数
    onSessionId: ((sessionId: string) => void) | null = null  // 添加 session_id 回调
  ): Promise<void> {
    // 确保用户ID已加载
    await this.ensureUserIdLoaded();
    
    console.info('[WebSocket] ========================================');
    console.info('[WebSocket] 🚀 开始 WebSocket 流式聊天');
    console.info('[WebSocket] 用户ID:', this.userId);
    console.info('[WebSocket] 消息:', message);
    console.info('[WebSocket] ========================================');
    
    try {
      // 动态导入 WebSocketUtil
      const WebSocketUtilModule = await import('../utils/WebSocketUtil');
      const ws = new WebSocketUtilModule.WebSocketUtil();
      
      // 累积数据
      let fullThinking = '';
      let fullAnswer = '';
      
      // 设置消息回调（在连接之前设置）
      ws.onMessage((data: string) => {
        console.info('[WebSocket] 📨 收到原始消息:', data.substring(0, 150));
        
        // 🔥 关键修改：使用 setTimeout 将 UI 更新放到下一个事件循环
        // 这样可以避免阻塞 UI 线程，保证滚动流畅
        setTimeout(() => {
          try {
            const event = JSON.parse(data) as Record<string, string>;
            const eventType = event.type || '';
            const content = event.content || '';
            
            console.info(`[WebSocket] 📦 解析事件: type=${eventType}, content长度=${content.length}`);
            
            switch (eventType) {
              case 'start':
                console.info('[WebSocket] 🎬 会话开始:', event.session_id);
                // 保存 session_id 供后续使用
                if (event.session_id && onSessionId) {
                  onSessionId(event.session_id);
                }
                break;
                
              case 'progress':
                console.info('[WebSocket] 📊 进度:', content);
                onProgress(content);
                break;
                
              case 'thinking_chunk':
                fullThinking += content;
                console.info(`[WebSocket] 💭 思考块 (累积: ${fullThinking.length})`);
                onThinking(fullThinking);
                break;
                
              case 'thinking':
                fullThinking = content;
                console.info(`[WebSocket] 💭 完整思考 (长度: ${fullThinking.length})`);
                onThinking(fullThinking);
                break;
                
              case 'answer_chunk':
                fullAnswer += content;
                console.info(`[WebSocket] ✍️ 回答块 (累积: ${fullAnswer.length})`);
                onAnswer(fullAnswer);
                break;
                
              case 'answer':
                fullAnswer = content;
                console.info(`[WebSocket] ✍️ 完整回答 (长度: ${fullAnswer.length})`);
                onAnswer(fullAnswer);
                break;
                
              case 'done':
                console.info('[WebSocket] 🎉 对话完成');
                onComplete();
                ws.close();
                break;
                
              case 'error':
                console.error('[WebSocket] ❌ 错误:', content);
                onError(content);
                ws.close();
                break;
                
              default:
                console.warn(`[WebSocket] ⚠️ 未知事件类型: ${eventType}`);
            }
          } catch (parseErr) {
            const error = parseErr as Error;
            console.error('[WebSocket] ❌ JSON解析失败:', error.message);
            console.error('[WebSocket] 原始数据:', data);
          }
        }, 0);
      });
      
      // 设置错误回调
      ws.onError((error: string) => {
        console.error('[WebSocket] ❌ 连接错误:', error);
        onError(error);
      });
      
      // 设置关闭回调
      ws.onClose(() => {
        console.info('[WebSocket] 🔌 连接已关闭');
      });
      
      // 连接 WebSocket
      await ws.connect('/ws/chat');
      
      // 发送消息
      const request: ChatRequest = {
        user_id: this.userId,
        message: message,
        context: context
      };
      
      // 如果有 sessionId，添加到请求中
      if (sessionId) {
        request.session_id = sessionId;
      }
      
      console.info('[WebSocket] 📤 发送请求:', JSON.stringify(request));
      ws.send(request);
      
    } catch (err) {
      const error = err as Error;
      console.error('[WebSocket] ========================================');
      console.error('[WebSocket] ❌ 流式聊天失败:', error.message);
      console.error('[WebSocket] ========================================');
      onError(error.message);
    }
  }
  
  /**
   * 延迟函数（保留用于其他用途）
   */
  private delay(ms: number): Promise<void> {
    return new Promise<void>((resolve) => {
      setTimeout(() => resolve(), ms);
    });
  }
  
  /**
 * 服务类
 */
  async chat(message: string, context: Record<string, string> | null = null): Promise<ChatMessage> {
    // 确保用户ID已加载
    await this.ensureUserIdLoaded();
    
    // 处理逻辑
    if (!this.historyService.getCurrentConversation()) {
      this.historyService.startConversation(this.userId);
    }
    
    const request: ChatRequest = {
      user_id: this.userId,
      message: message,
      context: context
    };
    
    try {
      console.info(`AI请求: ${ApiConfig.getBaseUrl()}/api/chat`);
      console.info(`消息: ${message}`);
      
      const response = await HttpUtil.post('/api/chat', request);
      
      console.info(`: ${response.responseCode}`);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, string>;
        console.info('AI');
        
        // 处理逻辑
        const userMessage = new ChatMessage(
          Date.now().toString(),
          'user',
          message,
          Date.now()
        );
        this.conversationHistory.push(userMessage);
        
        // RAG
        this.historyService.addMessage('user', message);
        
        // AI
        const aiMessage = new ChatMessage(
          (Date.now() + 1).toString(),
          'assistant',
          (result as Record<string, string>).ai_response || '',
          Date.now(),
          (result as Record<string, string>).thinking_process || undefined
        );
        this.conversationHistory.push(aiMessage);
        
        // AI
        this.historyService.addMessage('assistant', aiMessage.content);
        
        return aiMessage;
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error(':', error.message);
      throw new Error(`: ${error.message}`);
    }
  }
  

  
  /**
 * 服务类
 */
  async hybridProcess(inputData: Record<string, string>): Promise<Record<string, string>> {
    // 确保用户ID已加载
    await this.ensureUserIdLoaded();
    
    const request: HybridProcessRequest = {
      user_id: this.userId,
      input_data: inputData,
      enable_distillation: true
    };
    
    try {
      const response = await HttpUtil.post('/api/hybrid/process', request);
      
      if (response.responseCode === 200) {
        return HttpUtil.parseResponse<Record<string, string>>(response);
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error(':', error.message);
      throw new Error(error.message);
    }
  }
  
  /**
 * 服务类
 */
  async submitFeedback(rating: number, helpful: boolean, actionTaken: boolean, comments: string = ''): Promise<void> {
    // 确保用户ID已加载
    await this.ensureUserIdLoaded();
    
    const request: FeedbackRequest = {
      user_id: this.userId,
      rating: rating,
      helpful: helpful,
      action_taken: actionTaken,
      comments: comments
    };
    
    try {
      await HttpUtil.post('/api/hybrid/feedback', request);
    } catch (err) {
      const error = err as Error;
      console.error(':', error.message);
      throw new Error(error.message);
    }
  }
  
  /**
 * 服务类
 */
  async getEvolutionStatus(): Promise<Object> {
    try {
      const response = await HttpUtil.get(`/api/hybrid/evolution/${this.userId}`);
      
      if (response.responseCode === 200) {
        return JSON.parse(response.result as string) as Object;
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error(':', error.message);
      throw new Error(error.message);
    }
  }
  
  /**
 * 服务类
 */
  async getRecommendationStrategy(): Promise<string> {
    try {
      const response = await HttpUtil.get(`/api/hybrid/strategy/${this.userId}`);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, string>;
        return (result as Record<string, string>).strategy || 'llm_only';
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error(':', error.message);
      return 'llm_only';
    }
  }
  
  /**
 * 服务类
 */
  getConversationHistory(): ChatMessage[] {
    return this.conversationHistory;
  }
  
  /**
 * 服务类
 */
  async clearHistory(): Promise<void> {
    // RAG
    await this.historyService.endConversation();
    
    // 处理逻辑
    this.conversationHistory = [];
    
    // 创建新会话
    await this.createNewSession();
  }
  
  /**
   * 获取所有会话列表
   */
  async getAllSessions(): Promise<ConversationSession[]> {
    try {
      const response = await HttpUtil.get(`/api/chat/sessions/${this.userId}`);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, Object>;
        return (data.sessions as ConversationSession[]) || [];
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error(':', error.message);
      return [];
    }
  }
  
  /**
   * 加载指定会话的历史记录
   */
  async loadSession(sessionId: string): Promise<void> {
    try {
      const response = await HttpUtil.get(`/api/chat/session/${this.userId}/${sessionId}`);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, Object>;
        const history = data.history as Array<Record<string, string>>;
        
        // 清空当前历史
        this.conversationHistory = [];
        
        // 加载历史记录
        if (history && history.length > 0) {
          history.forEach((msg: Record<string, string>) => {
            this.conversationHistory.push(new ChatMessage(
              Date.now().toString() + Math.random(),
              msg.role as 'user' | 'assistant',
              msg.content,
              new Date(msg.timestamp).getTime(),
              msg.thinking
            ));
          });
        }
        
        this.currentSessionId = sessionId;
        console.info(`[AIConversationService] : ${sessionId}, : ${this.conversationHistory.length}`);
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error(':', error.message);
      throw new Error(error.message);
    }
  }
  
  /**
   * 删除指定会话
   */
  async deleteSession(sessionId: string): Promise<void> {
    try {
      const response = await HttpUtil.delete(`/api/chat/session/${this.userId}/${sessionId}`);
      
      if (response.responseCode === 200) {
        console.info(`[AIConversationService] : ${sessionId}`);
        
        // 如果删除的是当前会话，清空历史
        if (sessionId === this.currentSessionId) {
          this.conversationHistory = [];
          this.currentSessionId = '';
        }
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error(':', error.message);
      throw new Error(error.message);
    }
  }
  
  /**
   * 创建新会话
   */
  async createNewSession(): Promise<string> {
    try {
      const emptyData: Record<string, string> = {};
      const response = await HttpUtil.post(`/api/chat/session/new/${this.userId}`, emptyData);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, string>;
        const sessionId = data.session_id;
        
        this.currentSessionId = sessionId;
        this.conversationHistory = [];
        
        console.info(`[AIConversationService] : ${sessionId}`);
        return sessionId;
      } else {
        throw new Error(`: ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error(':', error.message);
      throw new Error(error.message);
    }
  }
  
  /**
   * 获取当前会话ID
   */
  getCurrentSessionId(): string {
    return this.currentSessionId;
  }
}

// 处理逻辑
let aiConversationService: AIConversationService | null = null;

export function getAIConversationService(): AIConversationService {
  if (!aiConversationService) {
    aiConversationService = new AIConversationService();
  }
  return aiConversationService;
}