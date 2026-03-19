import { stream } from '@kit.ArkTS';
import { http } from '@kit.ArkTS';
import { promptAction } from '@kit.ArkUI';

// 流式消息数据结构
interface StreamMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  thinking?: string;  // 思考过程
  isStreaming: boolean;
  timestamp: number;
}

// 自定义可读流用于处理HTTP响应
class ResponseReadableStream extends stream.Readable {
  private buffer: string = '';
  private isEnded: boolean = false;

  constructor() {
    super({ encoding: 'utf-8' });
  }

  // 模拟接收数据
  receiveChunk(chunk: string) {
    this.push(chunk);
  }

  // 标记流结束
  endStream() {
    this.push(null);
    this.isEnded = true;
  }

  doRead(size: number): void {
    // 由push方法驱动，无需额外实现
  }
}

// 自定义可写流用于缓冲处理的数据
class BufferWritableStream extends stream.Writable {
  private buffer: string = '';
  private onDataCallback?: (data: string) => void;

  constructor(onData?: (data: string) => void) {
    super();
    this.onDataCallback = onData;
  }

  doWrite(chunk: string | Uint8Array, encoding: string, callback: Function): void {
    try {
      const str = typeof chunk === 'string' ? chunk : new TextDecoder().decode(chunk);
      this.buffer += str;
      
      // 实时回调处理数据
      if (this.onDataCallback) {
        this.onDataCallback(str);
      }
      
      callback();
    } catch (error) {
      callback(error);
    }
  }

  getBuffer(): string {
    return this.buffer;
  }

  clearBuffer(): void {
    this.buffer = '';
  }
}

@Entry
@Component
struct StreamingAIChatPage {
  @State messages: StreamMessage[] = [];
  @State inputText: string = '';
  @State isLoading: boolean = false;
  @State currentStreamingMessage: StreamMessage | null = null;
  @State scrollOffset: number = 0;
  @State thinkingVisible: boolean = false;
  @State thinkingContent: string = '';

  private scroller: Scroller = new Scroller();
  private messageId: number = 0;

  // 生成唯一消息ID
  private generateMessageId(): string {
    return `msg_${Date.now()}_${++this.messageId}`;
  }

  // 发送消息并处理流式响应
  private async sendMessage() {
    if (!this.inputText.trim()) {
      promptAction.showToast({ message: '请输入消息' });
      return;
    }

    const userMessage: StreamMessage = {
      id: this.generateMessageId(),
      role: 'user',
      content: this.inputText,
      isStreaming: false,
      timestamp: Date.now()
    };

    this.messages.push(userMessage);
    this.inputText = '';
    this.isLoading = true;

    // 创建AI助手消息
    const assistantMessage: StreamMessage = {
      id: this.generateMessageId(),
      role: 'assistant',
      content: '',
      thinking: '',
      isStreaming: true,
      timestamp: Date.now()
    };

    this.messages.push(assistantMessage);
    this.currentStreamingMessage = assistantMessage;

    try {
      await this.streamChatResponse(userMessage.content, assistantMessage);
    } catch (error) {
      promptAction.showToast({ message: `错误: ${error.message}` });
      assistantMessage.isStreaming = false;
    } finally {
      this.isLoading = false;
      this.scrollToBottom();
    }
  }

  // 处理流式聊天响应
  private async streamChatResponse(userMessage: string, assistantMessage: StreamMessage): Promise<void> {
    return new Promise((resolve, reject) => {
      const httpRequest = http.createHttpRequest();
      
      httpRequest.on('headersReceive', (header) => {
        console.info('Headers received');
      });

      httpRequest.on('dataReceive', (data) => {
        this.processStreamChunk(data, assistantMessage);
      });

      httpRequest.on('dataEnd', () => {
        assistantMessage.isStreaming = false;
        this.currentStreamingMessage = null;
        resolve();
      });

      httpRequest.on('error', (error) => {
        reject(error);
      });

      // 发送请求到后端流式API
      const requestBody = JSON.stringify({
        message: userMessage,
        stream: true
      });

      httpRequest.request(
        'http://localhost:8000/api/chat/stream',
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
          },
          readTimeout: 300000,  // 5分钟超时
          connectTimeout: 10000,
          extraData: requestBody,
          expectDataType: http.HttpDataType.STRING
        }
      );
    });
  }

  // 处理流式数据块
  private processStreamChunk(data: string, message: StreamMessage): void {
    if (!data) return;

    // 处理Server-Sent Events格式
    const lines = data.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const jsonStr = line.substring(6);
          const chunk = JSON.parse(jsonStr);

          if (chunk.type === 'thinking') {
            // 处理思考过程
            message.thinking = (message.thinking || '') + chunk.content;
            this.thinkingContent = message.thinking;
            this.thinkingVisible = true;
          } else if (chunk.type === 'content') {
            // 处理实际内容
            message.content += chunk.content;
            this.thinkingVisible = false;
          } else if (chunk.type === 'done') {
            // 流结束
            message.isStreaming = false;
          }

          // 触发UI更新
          this.messages = [...this.messages];
        } catch (error) {
          console.error('Failed to parse chunk:', error);
        }
      }
    }
  }

  // 滚动到底部
  private scrollToBottom(): void {
    setTimeout(() => {
      this.scroller.scrollEdge(Edge.Bottom);
    }, 100);
  }

  // 清空对话
  private clearMessages(): void {
    this.messages = [];
    this.currentStreamingMessage = null;
    this.thinkingContent = '';
    this.thinkingVisible = false;
  }

  build() {
    Column() {
      // 顶部标题栏
      Row() {
        Text('AI 流式对话')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor('#1a1a1a')
        
        Spacer()
        
        Button('清空')
          .fontSize(14)
          .onClick(() => this.clearMessages())
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#f5f5f5')

      // 消息列表
      Scroll(this.scroller) {
        Column() {
          ForEach(this.messages, (message: StreamMessage) => {
            this.MessageItem(message)
          }, (message: StreamMessage) => message.id)

          // 思考过程显示
          if (this.thinkingVisible && this.thinkingContent) {
            this.ThinkingBubble(this.thinkingContent)
          }
        }
        .width('100%')
        .padding(12)
      }
      .scrollBar(BarState.On)
      .layoutWeight(1)

      // 输入框
      Row() {
        TextInput({ placeholder: '输入消息...' })
          .value(this.inputText)
          .onChange((value) => {
            this.inputText = value;
          })
          .layoutWeight(1)
          .padding(12)
          .backgroundColor('#ffffff')
          .borderRadius(8)
          .border({ width: 1, color: '#e0e0e0' })

        Button('发送')
          .width(60)
          .height(40)
          .margin({ left: 8 })
          .enabled(!this.isLoading)
          .onClick(() => this.sendMessage())
      }
      .width('100%')
      .padding(12)
      .backgroundColor('#f9f9f9')
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#ffffff')
  }

  @Builder
  MessageItem(message: StreamMessage) {
    Column() {
      if (message.role === 'user') {
        // 用户消息
        Row() {
          Spacer()
          Text(message.content)
            .padding(12)
            .backgroundColor('#007AFF')
            .fontColor('#ffffff')
            .borderRadius(12)
            .maxLines(null)
            .textAlign(TextAlign.End)
        }
        .width('100%')
        .margin({ bottom: 8 })
      } else {
        // AI消息
        Row() {
          Column() {
            // 思考过程（如果有）
            if (message.thinking) {
              Column() {
                Text('💭 思考中...')
                  .fontSize(12)
                  .fontColor('#666666')
                  .margin({ bottom: 4 })
                
                Text(message.thinking)
                  .fontSize(12)
                  .fontColor('#999999')
                  .maxLines(null)
                  .opacity(0.7)
              }
              .width('100%')
              .padding(10)
              .backgroundColor('#f0f0f0')
              .borderRadius(8)
              .margin({ bottom: 8 })
            }

            // 实际内容
            if (message.content) {
              Text(message.content)
                .padding(12)
                .backgroundColor('#e8e8e8')
                .fontColor('#1a1a1a')
                .borderRadius(12)
                .maxLines(null)
            }

            // 流式加载指示器
            if (message.isStreaming) {
              Row() {
                ForEach([0, 1, 2], (index: number) => {
                  Circle()
                    .width(6)
                    .height(6)
                    .margin(2)
                    .fillOpacity(0.3 + index * 0.3)
                    .fill('#007AFF')
                }, (index: number) => index.toString())
              }
              .margin({ top: 8 })
            }
          }
          .alignItems(HorizontalAlign.Start)
          Spacer()
        }
        .width('100%')
        .margin({ bottom: 8 })
      }
    }
    .width('100%')
  }

  @Builder
  ThinkingBubble(content: string) {
    Row() {
      Column() {
        Text('🤔 AI 思考中...')
          .fontSize(12)
          .fontColor('#666666')
          .margin({ bottom: 4 })
        
        Text(content)
          .fontSize(12)
          .fontColor('#999999')
          .maxLines(null)
          .opacity(0.8)
      }
      .width('100%')
      .padding(10)
      .backgroundColor('#fff3cd')
      .borderRadius(8)
      .borderLeft({ width: 3, color: '#ffc107' })
      Spacer()
    }
    .width('100%')
    .margin({ bottom: 8 })
  }
}

