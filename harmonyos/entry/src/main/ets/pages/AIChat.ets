/**
 * AI - 
 * HarmonyOS 6
 */




















import { router } from '@kit.ArkUI';
// import promptAction from '@ohos.promptAction'; // Deprecated, use UIContext instead
import { Theme } from '../common/Theme';
import { getAIConversationService, ChatMessage } from '../service/AIConversationService';
import { PhotoAlbumService } from '../service/PhotoAlbumService';
import { MarkdownParser, MarkdownBlock, InlinePart } from '../utils/MarkdownParser';
import { SimpleIcon } from '../components/IconRenderer';
import http from '@ohos.net.http';
import { ApiConfig } from '../config/ApiConfig';
import { getAuthService } from '../service/AuthService';

// 对话会话接口
interface ConversationItem {
  id: string
  title: string
  preview: string
  message_count: number
  last_message_time: string
}

// API响应接口
interface ConversationsResponse {
  success: boolean
  data: ConversationItem[]
}

interface MessagesResponse {
  success: boolean
  data: MessageData[]
}

interface MessageData {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string  // ISO 时间字符串
  thinking?: string
}

interface CreateConversationData {
  conversation_id: string
}

interface CreateConversationResponse {
  success: boolean
  data: CreateConversationData
}

@Entry
@Component
struct AIChat {
  @State messages: ChatMessage[] = [];
  @State inputText: string = '';
  @State isLoading: boolean = false;
  @State showFeedback: boolean = false;
  @State currentStrategy: string = 'llm_only';
  @State inputFocused: boolean = false;
  @State showContent: boolean = false;
  @State expandedThinking: string = ''; // ID
  @State photoScanStatus: string = ''; // 处理逻辑
  @State processingProgress: string = ''; // 处理逻辑
  @State dotAnimation1: number = 1; // 处理逻辑
  @State dotAnimation2: number = 1; // 处理逻辑
  @State dotAnimation3: number = 1; // 处理逻辑
  private animationTimer: number = -1;
  
  // 历史对话相关
  @State showHistoryPanel: boolean = false;
  @State conversations: ConversationItem[] = [];
  @State currentSessionId: string = '';
  @State isLoadingHistory: boolean = false;
  
  private aiService = getAIConversationService();
  private photoService = PhotoAlbumService.getInstance(this.getUIContext());
  private scroller: Scroller = new Scroller();
  
  aboutToAppear() {
    // 只加载本地数据，不发起网络请求
    this.messages = this.aiService.getConversationHistory();
    
    if (this.messages.length === 0) {
      this.addWelcomeMessage();
    }
    
    // 异步加载策略和状态，不阻塞页面显示
    this.loadStrategyAsync().catch((err: Error) => {
      console.error('[AIChat] 加载策略失败:', err.message);
    });
    
    // 异步加载历史对话列表（不阻塞页面）
    this.loadConversations().catch((err: Error) => {
      console.error('[AIChat] 加载历史对话失败:', err.message);
    });
  }
  
  /**
   * 加载历史对话列表
   */
  async loadConversations() {
    try {
      console.info('[AIChat] 开始加载历史对话列表...');
      const userId = getAuthService().getCurrentUserId();
      console.info('[AIChat] 用户ID:', userId);
      
      const httpRequest = http.createHttp();
      const url = `${ApiConfig.getBaseUrl()}/api/v4/conversations/${userId}/list`;
      console.info('[AIChat] 请求URL:', url);
      
      const response = await httpRequest.request(url, {
        method: http.RequestMethod.GET
      });
      
      httpRequest.destroy();
      
      console.info('[AIChat] 响应状态码:', response.responseCode);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as ConversationsResponse;
        if (result.success && result.data) {
          this.conversations = result.data;
          console.info(`[AIChat] ✅ 加载了 ${this.conversations.length} 个历史对话`);
        } else {
          console.warn('[AIChat] ⚠️ 响应成功但没有数据');
        }
      } else {
        console.error('[AIChat] ❌ HTTP错误:', response.responseCode);
      }
    } catch (err) {
      console.error('[AIChat] ❌ 加载历史对话失败:', JSON.stringify(err));
    }
  }
  
  /**
   * 加载指定对话的消息
   */
  async loadConversationMessages(sessionId: string) {
    this.isLoadingHistory = true;
    try {
      const userId = getAuthService().getCurrentUserId();
      const httpRequest = http.createHttp();
      const url = `${ApiConfig.getBaseUrl()}/api/v4/conversations/${userId}/${sessionId}/messages`;
      
      const response = await httpRequest.request(url, {
        method: http.RequestMethod.GET
      });
      
      httpRequest.destroy();
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as MessagesResponse;
        if (result.success && result.data) {
          // 转换为ChatMessage格式
          const messages = result.data.map((msg: MessageData) => {
            // 将 ISO 时间字符串转换为时间戳
            const timestamp = msg.timestamp ? new Date(msg.timestamp).getTime() : Date.now();
            return new ChatMessage(
              msg.id || Date.now().toString(),
              msg.role,
              msg.content,
              timestamp,
              msg.thinking
            );
          });
          this.messages = messages;
          this.currentSessionId = sessionId;
          this.showHistoryPanel = false;
          
          // 滚动到底部
          setTimeout(() => {
            this.scroller.scrollEdge(Edge.Bottom);
          }, 100);
        }
      }
    } catch (err) {
      console.error('[AIChat] 加载对话消息失败:', err);
    } finally {
      this.isLoadingHistory = false;
    }
  }
  
  /**
   * 创建新对话
   */
  async createNewConversation() {
    try {
      const userId = getAuthService().getCurrentUserId();
      const httpRequest = http.createHttp();
      const url = `${ApiConfig.getBaseUrl()}/api/v4/conversations/${userId}/create`;
      
      const response = await httpRequest.request(url, {
        method: http.RequestMethod.POST
      });
      
      httpRequest.destroy();
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as CreateConversationResponse;
        if (result.success && result.data) {
          this.currentSessionId = result.data.conversation_id;
          this.messages = [];
          this.addWelcomeMessage();
          this.showHistoryPanel = false;
          
          // 重新加载对话列表
          this.loadConversations();
        }
      }
    } catch (err) {
      console.error('[AIChat] 创建新对话失败:', err);
    }
  }
  
  onPageShow() {
    // 触发页面动画
    this.triggerPageAnimation();
    // 仅更新照片扫描状态（本地操作，不耗时）
    this.updatePhotoScanStatus();
  }
  
  /**
   * 异步加载策略，不阻塞页面显示
   */
  private async loadStrategyAsync() {
    try {
      this.currentStrategy = await this.aiService.getRecommendationStrategy();
    } catch (err) {
      console.error('加载策略失败:', err);
      // 使用默认策略，不影响用户体验
      this.currentStrategy = 'llm_only';
    }
  }
  
  /**
 * 页面组件
 */
  private updatePhotoScanStatus() {
    const status = this.photoService.getScanStatus()
    
    if (status.isScanning) {
      this.photoScanStatus = ' ...'
    } else if (status.lastScanTime === 0) {
      this.photoScanStatus = ' '
    } else {
      const timeAgo = this.formatTimeAgo(status.lastScanTime)
      const statusIcon = status.lastSyncSuccess ? '' : ''
      this.photoScanStatus = `${statusIcon} ${timeAgo}  ${status.lastScanCount} `
    }
  }
  
  /**
 * 页面组件
 */
  private formatTimeAgo(timestamp: number): string {
    const now = Date.now()
    const diff = now - timestamp
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)
    
    if (minutes < 1) return ''
    if (minutes < 60) return `${minutes}`
    if (hours < 24) return `${hours}`
    return `${days}`
  }
  
  /**
 * 页面组件
 */
  private triggerPageAnimation(): void {
    // 处理逻辑
    this.showContent = false;
    // 处理逻辑
    setTimeout(() => {
      this.showContent = true;
    }, 50);
  }
  

  
  addWelcomeMessage() {
    const welcomeMsg = new ChatMessage(
      Date.now().toString(),
      'assistant',
      ' LifeSwarm AI \n\n Qwen3.5-Plus \n\n\n\n',
      Date.now()
    );
    this.messages.push(welcomeMsg);
  }
  
  async sendMessage() {
    if (!this.inputText.trim() || this.isLoading) {
      return;
    }
    
    const userMessage = this.inputText;
    this.inputText = '';
    this.isLoading = true;
    
    // 处理逻辑
    this.startLoadingAnimation();
    
    // 处理逻辑
    const userMsg = new ChatMessage(
      Date.now().toString(),
      'user',
      userMessage,
      Date.now()
    );
    this.messages.push(userMsg);
    
    // AI
    const aiMsgId = (Date.now() + 1).toString();
    const aiMsg = new ChatMessage(
      aiMsgId,
      'assistant',
      '',
      Date.now(),
      ''
    );
    this.messages.push(aiMsg);
    
    // 处理逻辑
    setTimeout(() => {
      this.scroller.scrollEdge(Edge.Bottom);
    }, 100);
    
    try {
      console.info('[AIChat] 使用 WebSocket 流式发送消息...');
      
      // 使用 WebSocket 流式通信（HarmonyOS 最佳方案）
      await this.aiService.chatStreamWebSocket(
        userMessage,
        // onProgress - 进度更新
        (progress: string) => {
          console.info('[AIChat] 进度更新:', progress);
          this.processingProgress = progress;
        },
        // onThinking - 思考过程
        (thinking: string) => {
          console.info('[AIChat] 收到思考过程, 长度:', thinking.length);
          this.processingProgress = ''; // 清空进度
          this.updateMessage(aiMsgId, 'thinking', thinking);
        },
        // onAnswer - 回复内容
        (answer: string) => {
          console.info('[AIChat] 收到回复内容, 长度:', answer.length);
          this.updateMessage(aiMsgId, 'content', answer);
        },
        // onComplete - 完成
        () => {
          console.info('[AIChat] 对话完成');
          this.processingProgress = '';
          this.stopLoadingAnimation();
          this.showFeedback = true;
          this.isLoading = false;
          
          // 刷新历史对话列表
          this.loadConversations();
        },
        // onError - 错误
        (error: string) => {
          console.error('[AIChat] WebSocket 错误:', error);
          this.processingProgress = '';
          this.stopLoadingAnimation();
          this.isLoading = false;
          
          // AI
          const index = this.messages.findIndex(m => m.id === aiMsgId);
          if (index >= 0) {
            this.messages.splice(index, 1);
          }
          
          try {
            this.getUIContext().getPromptAction().showToast({
              message: `发送失败: ${error}`,
              duration: 3000
            });
          } catch (e) {
            console.error('显示错误提示失败:', e);
          }
        },
        null,  // context
        this.currentSessionId || null,  // 传递当前会话ID
        // onSessionId - 接收服务器返回的 session_id
        (sessionId: string) => {
          console.info('[AIChat] 收到 session_id:', sessionId);
          this.currentSessionId = sessionId;
        }
      );
      
    } catch (err) {
      const error = err as Error;
      console.error('发送消息失败:', error.message);
      
      // AI
      const index = this.messages.findIndex(m => m.id === aiMsgId);
      if (index >= 0) {
        this.messages.splice(index, 1);
      }
      
      try {
        this.getUIContext().getPromptAction().showToast({
          message: `发送失败: ${error.message}`,
          duration: 3000
        });
      } catch (e) {
        console.error('显示错误提示失败:', e);
      }
      
      this.isLoading = false;
      this.stopLoadingAnimation();
    }
  }
  
  /**
 * 页面组件
 */
  private startLoadingAnimation(): void {
    let step = 0;
    this.animationTimer = setInterval(() => {
      step = (step + 1) % 3;
      
      animateTo({ duration: 300, curve: Curve.EaseInOut }, () => {
        this.dotAnimation1 = step === 0 ? 1.5 : 1;
        this.dotAnimation2 = step === 1 ? 1.5 : 1;
        this.dotAnimation3 = step === 2 ? 1.5 : 1;
      });
    }, 300);
  }
  
  /**
 * 页面组件
 */
  private stopLoadingAnimation(): void {
    if (this.animationTimer !== -1) {
      clearInterval(this.animationTimer);
      this.animationTimer = -1;
    }
    this.dotAnimation1 = 1;
    this.dotAnimation2 = 1;
    this.dotAnimation3 = 1;
  }
  
  /**
   * UI更新测试
   */
  private updateMessage(messageId: string, field: 'thinking' | 'content', value: string): void {
    console.info(`[AIChat] updateMessage 被调用 - messageId: ${messageId}, field: ${field}, value长度: ${value.length}`);
    
    const index = this.messages.findIndex(m => m.id === messageId);
    console.info(`[AIChat] 找到消息索引: ${index}`);
    
    if (index >= 0) {
      console.info(`[AIChat] 当前消息: role=${this.messages[index].role}, content长度=${this.messages[index].content.length}, thinking长度=${this.messages[index].thinking?.length || 0}`);
      
      // 创建更新后的消息
      const updatedMessage = new ChatMessage(
        this.messages[index].id,
        this.messages[index].role,
        field === 'content' ? value : this.messages[index].content,
        this.messages[index].timestamp,
        field === 'thinking' ? value : this.messages[index].thinking
      );
      
      console.info(`[AIChat] 更新后消息: content长度=${updatedMessage.content.length}, thinking长度=${updatedMessage.thinking?.length || 0}`);
      
      // 更新UI
      const newMessages: ChatMessage[] = [];
      for (let i = 0; i < this.messages.length; i++) {
        if (i === index) {
          newMessages.push(updatedMessage);
        } else {
          newMessages.push(this.messages[i]);
        }
      }
      this.messages = newMessages;
      
      console.info(`[AIChat] 消息数组已更新，总数: ${this.messages.length}`);
      
      // 滚动到底部
      this.scroller.scrollEdge(Edge.Bottom);
    } else {
      console.error(`[AIChat] 未找到消息ID: ${messageId}`);
    }
  }
  
  /**
   * 文本动画效果
   */
  private animateText(
    messageId: string, 
    fullText: string, 
    field: 'thinking' | 'content',
    delayMs: number = 30
  ): Promise<void> {
    return new Promise<void>((resolve) => {
      if (!fullText || fullText.length === 0) {
        resolve();
        return;
      }
      
      let currentIndex = 0;
      
      const updateText = () => {
        if (currentIndex >= fullText.length) {
          resolve();
          return;
        }
        
        // 1-3
        const chunkSize = Math.floor(Math.random() * 3) + 1;
        currentIndex = Math.min(currentIndex + chunkSize, fullText.length);
        
        const partialText = fullText.substring(0, currentIndex);
        
        //  - UI
        const index = this.messages.findIndex(m => m.id === messageId);
        if (index >= 0) {
          // 处理逻辑
          const updatedMessage = new ChatMessage(
            this.messages[index].id,
            this.messages[index].role,
            field === 'content' ? partialText : this.messages[index].content,
            this.messages[index].timestamp,
            field === 'thinking' ? partialText : this.messages[index].thinking
          );
          
          // UI
          const newMessages: ChatMessage[] = [];
          for (let i = 0; i < this.messages.length; i++) {
            if (i === index) {
              newMessages.push(updatedMessage);
            } else {
              newMessages.push(this.messages[i]);
            }
          }
          this.messages = newMessages;
        }
        
        // 处理逻辑
        this.scroller.scrollEdge(Edge.Bottom);
        
        // 处理逻辑
        setTimeout(updateText, delayMs);
      };
      
      // 处理逻辑
      updateText();
    });
  }
  
  async submitFeedback(helpful: boolean) {
    try {
      await this.aiService.submitFeedback(
        helpful ? 5 : 3,
        helpful,
        false
      );
      this.showFeedback = false;
      
      this.getUIContext().getPromptAction().showToast({
        message: ''
      });
    } catch (err) {
      console.error(':', err);
    }
  }
  
  getStrategyBadge(): string {
    switch (this.currentStrategy) {
      case 'llm_only':
        return 'LLM';
      case 'personal_only':
        return 'Personal';
      case 'hybrid':
        return 'Hybrid';
      default:
        return 'AI';
    }
  }
  
  build() {
    Stack() {
      // 1. 背景层 - 动态渐变
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor(Theme.Color.BackgroundPrimary)
        
      // 装饰性光晕 - 左上
      Circle({ width: 320, height: 320 })
        .fill('rgba(10, 89, 247, 0.12)')
        .blur(70)
        .position({ x: -60, y: -60 })
        
      // 装饰性光晕 - 右下
      Circle({ width: 420, height: 420 })
        .fill('rgba(107, 72, 255, 0.08)')
        .blur(90)
        .position({ x: '65%', y: '75%' })

      Column() {
        // 顶部导航栏 - 毛玻璃效果
        Row() {
          Row({ space: 16 }) {
            Button({ type: ButtonType.Circle, stateEffect: true }) {
              SimpleIcon({
                iconName: 'back',
                iconSize: 20,
                color: Theme.Color.TextPrimary
              })
            }
            .width(44)
            .height(44)
            .backgroundColor(Theme.Color.GlassLight)
            .backdropBlur(Theme.Blur.Medium)
            .onClick(() => {
              this.getUIContext().getRouter().back();
            })
            
            Column({ space: 4 }) {
              Text('AI 对话')
                .fontSize(Theme.Typography.HeadingSmall.size)
                .fontWeight(Theme.Typography.HeadingSmall.weight)
                .fontColor(Theme.Color.TextPrimary)
              
              Text('智能助手 · 随时待命')
                .fontSize(Theme.Typography.Caption.size)
                .fontColor(Theme.Color.TextSecondary)
            }
            .alignItems(HorizontalAlign.Start)
          }
          
          Blank()
          
          // 历史对话按钮
          Button({ type: ButtonType.Circle, stateEffect: true }) {
            SimpleIcon({
              iconName: 'chat',
              iconSize: 20,
              color: Theme.Color.Primary
            })
          }
          .width(44)
          .height(44)
          .backgroundColor(Theme.Color.GlassLight)
          .backdropBlur(Theme.Blur.Medium)
          .onClick(() => {
            this.showHistoryPanel = !this.showHistoryPanel;
          })
          
          // 策略标签
          Text(this.getStrategyBadge())
            .fontSize(Theme.Typography.Overline.size)
            .fontColor(Theme.Color.Primary)
            .fontWeight(Theme.Typography.Overline.weight)
            .letterSpacing(Theme.Typography.Overline.letterSpacing)
            .padding({ left: 12, right: 12, top: 6, bottom: 6 })
            .backgroundColor('rgba(10, 89, 247, 0.1)')
            .borderRadius(Theme.Radius.m)
        }
        .width('100%')
        .height(64)
        .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m })
        .backgroundColor(Theme.Color.GlassHeavy)
        .backdropBlur(Theme.Blur.Heavy)
        .shadow(Theme.Shadow.Soft)
        .zIndex(100)
        .opacity(this.showContent ? 1 : 0)
        .translate({ y: this.showContent ? 0 : -20 })
        .animation({
          duration: 600,
          curve: Curve.Friction
        })
        
        // 相册扫描状态提示
        if (this.photoScanStatus) {
          Row({ space: 8 }) {
            LoadingProgress()
              .width(14)
              .height(14)
              .color(Theme.Color.Primary)
              .visibility(this.photoScanStatus.includes('扫描中') ? Visibility.Visible : Visibility.None)
            
            Text(this.photoScanStatus)
              .fontSize(Theme.Typography.Caption.size)
              .fontColor(Theme.Color.TextSecondary)
          }
          .width('100%')
          .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m, top: 8, bottom: 8 })
          .backgroundColor(Theme.Color.GlassLight)
          .backdropBlur(Theme.Blur.Light)
          .opacity(this.showContent ? 0.9 : 0)
          .animation({
            duration: 400,
            delay: 200
          })
        }
          
        // 消息列表区域
        Scroll(this.scroller) {
          Column({ space: Theme.Spacing.l }) {
            ForEach(this.messages, (msg: ChatMessage, index: number) => {
              Column() {
                this.EnhancedMessageBubble(msg)
              }
              .opacity(this.showContent ? 1 : 0)
              .translate({ y: this.showContent ? 0 : 20 })
              .animation({
                duration: 500,
                curve: Curve.Friction,
                delay: 100 + index * 40
              })
            })
            
            // 加载动画 - 优化版
            if (this.isLoading) {
              Column({ space: 16 }) {
                // 进度提示
                if (this.processingProgress) {
                  Row({ space: 8 }) {
                    LoadingProgress()
                      .width(16)
                      .height(16)
                      .color(Theme.Color.Primary)
                    
                    Text(this.processingProgress)
                      .fontSize(Theme.Typography.BodySmall.size)
                      .fontColor(Theme.Color.Primary)
                      .fontWeight(500)
                  }
                  .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m, top: 8, bottom: 8 })
                  .backgroundColor('rgba(10, 89, 247, 0.08)')
                  .borderRadius(Theme.Radius.m)
                }
                
                // 跳动的点动画
                Row({ space: 8 }) {
                  Circle({ width: 10, height: 10 })
                    .fill(Theme.Color.Primary)
                    .scale({ x: this.dotAnimation1, y: this.dotAnimation1 })
                    .opacity(0.9)
                  
                  Circle({ width: 10, height: 10 })
                    .fill(Theme.Color.Primary)
                    .scale({ x: this.dotAnimation2, y: this.dotAnimation2 })
                    .opacity(0.9)
                  
                  Circle({ width: 10, height: 10 })
                    .fill(Theme.Color.Primary)
                    .scale({ x: this.dotAnimation3, y: this.dotAnimation3 })
                    .opacity(0.9)
                }
              }
              .padding(Theme.Spacing.l)
              .alignItems(HorizontalAlign.Center)
              .width('100%')
            }
          }
          .width('100%')
          .padding({ top: Theme.Spacing.l, bottom: Theme.Spacing.l, left: Theme.Spacing.m, right: Theme.Spacing.m })
        }
        .layoutWeight(1)
        .scrollBar(BarState.Off)
        .edgeEffect(EdgeEffect.Spring)
          
        // 反馈区域
        if (this.showFeedback) {
          Row({ space: 12 }) {
            Text('这个回答有帮助吗？')
              .fontSize(Theme.Typography.BodySmall.size)
              .fontColor(Theme.Color.TextSecondary)
              .layoutWeight(1)
            
            Button('有帮助')
              .fontSize(Theme.Typography.BodySmall.size)
              .fontColor(Theme.Color.Primary)
              .height(36)
              .backgroundColor('rgba(10, 89, 247, 0.1)')
              .borderRadius(Theme.Radius.round)
              .onClick(() => {
                this.submitFeedback(true);
              })
            
            Button('没帮助')
              .fontSize(Theme.Typography.BodySmall.size)
              .fontColor(Theme.Color.TextTertiary)
              .height(36)
              .backgroundColor(Theme.Color.BackgroundTertiary)
              .borderRadius(Theme.Radius.round)
              .onClick(() => {
                this.submitFeedback(false);
              })
          }
          .width('92%')
          .padding(Theme.Spacing.m)
          .backgroundColor(Theme.Color.GlassHeavy)
          .backdropBlur(Theme.Blur.Heavy)
          .borderRadius(Theme.Radius.l)
          .shadow(Theme.Shadow.Medium)
          .margin({ bottom: 12 })
        }
          
        // 输入区域 - 增强版
        Row({ space: 12 }) {
          TextInput({ 
            placeholder: '输入消息...', 
            text: this.inputText 
          })
            .layoutWeight(1)
            .height(52)
            .fontSize(Theme.Typography.BodyLarge.size)
            .fontColor(Theme.Color.TextPrimary)
            .placeholderColor(Theme.Color.TextTertiary)
            .backgroundColor(Theme.Color.BackgroundSecondary)
            .borderRadius(Theme.Radius.round)
            .padding({ left: Theme.Spacing.l, right: Theme.Spacing.l })
            .border({ width: 1, color: this.inputFocused ? Theme.Color.Primary : Theme.Color.BorderLight })
            .shadow(this.inputFocused ? Theme.Shadow.GlowPrimary : Theme.Shadow.Soft)
            .onChange((value: string) => {
              this.inputText = value;
            })
            .onFocus(() => {
              this.inputFocused = true;
            })
            .onBlur(() => {
              this.inputFocused = false;
            })
            .onSubmit(() => {
              this.sendMessage();
            })
          
          // 发送按钮
          Button({ type: ButtonType.Circle, stateEffect: true }) {
            SimpleIcon({
              iconName: 'chat',
              iconSize: 20,
              color: Theme.Color.TextWhite
            })
          }
          .width(52)
          .height(52)
          .backgroundColor(this.inputText.trim() && !this.isLoading
            ? Theme.Color.Primary
            : Theme.Color.TextTertiary)
          .shadow(this.inputText.trim() && !this.isLoading 
            ? Theme.Shadow.GlowPrimary 
            : undefined)
          .enabled(this.inputText.trim().length > 0 && !this.isLoading)
          .onClick(() => {
            this.sendMessage();
          })
          .scale({ 
            x: this.inputText.trim() && !this.isLoading ? 1 : 0.95, 
            y: this.inputText.trim() && !this.isLoading ? 1 : 0.95 
          })
          .animation({
            duration: 200,
            curve: Curve.EaseOut
          })
        }
        .width('100%')
        .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m, bottom: Theme.Spacing.m, top: 12 })
        .backgroundColor(Theme.Color.GlassHeavy)
        .backdropBlur(Theme.Blur.Heavy)
      }
      .width('100%')
      .height('100%')
      
      // 历史对话面板
      if (this.showHistoryPanel) {
        this.HistoryPanel()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }
  
  /**
   * 历史对话面板
   */
  @Builder
  HistoryPanel(): void {
    Column() {
      // 面板头部
      Row() {
        Text('历史对话')
          .fontSize(18)
          .fontWeight(700)
          .fontColor(Theme.Color.TextPrimary)
        
        Blank()
        
        Button('新对话')
          .fontSize(14)
          .fontColor(Theme.Color.Primary)
          .backgroundColor('rgba(10, 89, 247, 0.1)')
          .height(32)
          .borderRadius(16)
          .onClick(() => {
            this.createNewConversation();
          })
        
        Button({ type: ButtonType.Circle }) {
          Text('×')
            .fontSize(24)
            .fontColor(Theme.Color.TextSecondary)
        }
        .width(32)
        .height(32)
        .backgroundColor('transparent')
        .onClick(() => {
          this.showHistoryPanel = false;
        })
      }
      .width('100%')
      .padding(16)
      
      // 对话列表
      if (this.isLoadingHistory) {
        Column() {
          LoadingProgress()
            .width(40)
            .height(40)
            .color(Theme.Color.Primary)
        }
        .width('100%')
        .height(200)
        .justifyContent(FlexAlign.Center)
      } else if (this.conversations.length === 0) {
        Column() {
          Text('暂无历史对话')
            .fontSize(14)
            .fontColor(Theme.Color.TextTertiary)
        }
        .width('100%')
        .height(200)
        .justifyContent(FlexAlign.Center)
      } else {
        List({ space: 8 }) {
          ForEach(this.conversations, (conv: ConversationItem) => {
            ListItem() {
              Column({ space: 8 }) {
                Row() {
                  Text(conv.title)
                    .fontSize(15)
                    .fontWeight(600)
                    .fontColor(Theme.Color.TextPrimary)
                    .maxLines(1)
                    .textOverflow({ overflow: TextOverflow.Ellipsis })
                  
                  Blank()
                  
                  Text(`${conv.message_count}条`)
                    .fontSize(12)
                    .fontColor(Theme.Color.TextTertiary)
                }
                .width('100%')
                
                Text(conv.preview)
                  .fontSize(13)
                  .fontColor(Theme.Color.TextSecondary)
                  .maxLines(2)
                  .textOverflow({ overflow: TextOverflow.Ellipsis })
                
                Text(conv.last_message_time)
                  .fontSize(11)
                  .fontColor(Theme.Color.TextTertiary)
              }
              .width('100%')
              .padding(12)
              .backgroundColor(this.currentSessionId === conv.id 
                ? 'rgba(10, 89, 247, 0.1)' 
                : Theme.Color.BackgroundSecondary)
              .borderRadius(12)
              .onClick(() => {
                this.loadConversationMessages(conv.id);
              })
            }
          })
        }
        .width('100%')
        .layoutWeight(1)
        .scrollBar(BarState.Auto)
      }
    }
    .width('85%')
    .height('80%')
    .backgroundColor(Theme.Color.GlassHeavy)
    .backdropBlur(30)
    .borderRadius(20)
    .shadow(Theme.Shadow.Elevated)
    .padding(8)
    .position({ x: '7.5%', y: '10%' })
    .zIndex(200)
    .transition({ type: TransitionType.Insert, opacity: 0, translate: { x: -100 } })
    .transition({ type: TransitionType.Delete, opacity: 0, translate: { x: -100 } })
  }
  
  /**
   * 增强版消息气泡 - HarmonyOS 6 流体设计
   */
  @Builder
  EnhancedMessageBubble(msg: ChatMessage): void {
    Row() {
      if (msg.role === 'user') {
        Blank()
      }
      
      Column({ space: 12 }) {
        // AI思考过程
        if (msg.role === 'assistant' && msg.thinking) {
          Column({ space: 8 }) {
            Row({ space: 8 }) {
              SimpleIcon({
                iconName: 'insight',
                iconSize: 16,
                color: Theme.Color.Warning
              })
              Text('思考过程')
                .fontSize(Theme.Typography.BodySmall.size)
                .fontColor(Theme.Color.Warning)
                .fontWeight(600)
            }
            .padding({ left: 12, right: 12, top: 8, bottom: 8 })
            .backgroundColor('rgba(255, 149, 0, 0.1)')
            .backdropBlur(Theme.Blur.Light)
            .borderRadius(Theme.Radius.m)
            
            Text(msg.thinking)
              .fontSize(Theme.Typography.BodySmall.size)
              .fontColor(Theme.Color.TextSecondary)
              .lineHeight(22)
              .padding(Theme.Spacing.m)
              .backgroundColor('rgba(255, 251, 240, 0.7)')
              .borderRadius(Theme.Radius.m)
              .width('100%')
              .maxLines(100)
          }
          .width('100%')
          .alignItems(HorizontalAlign.Start)
          .margin({ bottom: 8 })
        }
        
        // 消息内容
        if (msg.content && msg.content !== '...') {
          Column({ space: 8 }) {
            if (msg.role === 'assistant') {
              // AI消息 - Markdown渲染
              this.MarkdownContent(msg.content)
            } else {
              // 用户消息
              Text(msg.content)
                .fontSize(Theme.Typography.BodyLarge.size)
                .fontColor(Theme.Color.TextWhite)
                .lineHeight(28)
                .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m, top: 14, bottom: 14 })
                .backgroundColor(Theme.Color.Primary)
                .borderRadius({
                  topLeft: Theme.Radius.l,
                  topRight: Theme.Radius.s,
                  bottomLeft: Theme.Radius.l,
                  bottomRight: Theme.Radius.l
                })
                .shadow(Theme.Shadow.GlowPrimary)
            }
          }
          .padding(msg.role === 'assistant' ? Theme.Spacing.l : 0)
          .backgroundColor(msg.role === 'user' ? 'transparent' : Theme.Color.GlassHeavy)
          .backdropBlur(msg.role === 'assistant' ? Theme.Blur.Heavy : 0)
          .borderRadius(msg.role === 'assistant' ? Theme.Radius.xl : 0)
          .border(msg.role === 'assistant' ? { width: 1, color: Theme.Color.BorderLight } : undefined)
          .shadow(msg.role === 'assistant' ? Theme.Shadow.Medium : undefined)
          .width(msg.role === 'assistant' ? '100%' : undefined)
        }
        
        // 时间戳
        Text(this.formatTime(msg.timestamp))
          .fontSize(Theme.Typography.Caption.size)
          .fontColor(Theme.Color.TextTertiary)
          .margin({ top: 4 })
          .opacity(0.6)
      }
      .alignItems(msg.role === 'user' 
        ? HorizontalAlign.End 
        : HorizontalAlign.Start)
      .constraintSize({ maxWidth: '85%' })
      
      if (msg.role === 'assistant') {
        Blank()
      }
    }
    .width('100%')
    .justifyContent(msg.role === 'user' 
      ? FlexAlign.End 
      : FlexAlign.Start)
    .padding({ bottom: 8 })
  }
  
  /**
   * Markdown
   */
  @Builder
  MarkdownContent(content: string): void {
    Column({ space: 12 }) {
      ForEach(this.parseMarkdownBlocks(content), (block: MarkdownBlock, index: number) => {
        if (block.type === 'heading') {
          // 处理逻辑
          Text(block.content)
            .fontSize(block.level === 1 ? 20 : block.level === 2 ? 18 : 16)
            .fontWeight(600)
            .fontColor(Theme.Color.TextPrimary)
            .width('100%')
        } else if (block.type === 'list' && block.items) {
          // 处理逻辑
          Column({ space: 6 }) {
            ForEach(block.items, (item: string, itemIndex: number) => {
              Row({ space: 8 }) {
                Text('•')
                  .fontSize(14)
                  .fontColor(Theme.Color.Primary)
                  .width(16)
                
                Text(item)
                  .fontSize(15)
                  .fontColor(Theme.Color.TextPrimary)
                  .lineHeight(22)
                  .layoutWeight(1)
              }
              .width('100%')
              .alignItems(VerticalAlign.Top)
            })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Start)
        } else if (block.type === 'code') {
          // 处理逻辑
          Text(block.content)
            .fontSize(13)
            .fontColor('#E83E8C')
            .fontFamily('monospace')
            .lineHeight(20)
            .padding(12)
            .backgroundColor('#F5F5F5')
            .borderRadius(8)
            .width('100%')
        } else if (block.type === 'paragraph') {
          //  - 
          this.InlineText(block.content)
        }
      })
    }
    .width('100%')
    .alignItems(HorizontalAlign.Start)
  }
  
  /**
   * Markdown
   */
  private parseMarkdownBlocks(content: string): MarkdownBlock[] {
    return MarkdownParser.parse(content);
  }
  
  /**
 * 页面组件
 */
  @Builder
  InlineText(text: string): void {
    Text() {
      ForEach(this.parseInlineParts(text), (part: InlinePart, index: number) => {
        Span(part.text)
          .fontSize(15)
          .fontColor(Theme.Color.TextPrimary)
          .fontWeight(part.bold ? 600 : 400)
      })
    }
    .lineHeight(24)
    .width('100%')
  }
  
  /**
 * 页面组件
 */
  private parseInlineParts(text: string): InlinePart[] {
    return MarkdownParser.parseInline(text);
  }
  
  formatTime(timestamp: number): string {
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  }
}
