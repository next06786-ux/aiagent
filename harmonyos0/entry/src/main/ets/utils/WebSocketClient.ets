/**
 * WebSocket客户端封装
 * 支持自动重连、消息处理
 */
import webSocket from '@ohos.net.webSocket';

export class WebSocketClient {
  private ws: webSocket.WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 3000;
  private messageHandlers: Map<string, (data: any) => void> = new Map();
  private isManualClose: boolean = false;
  
  constructor(url: string) {
    this.url = url;
  }
  
  /**
   * 连接WebSocket
   */
  async connect(): Promise<void> {
    this.isManualClose = false;
    this.ws = webSocket.createWebSocket();
    
    this.ws.on('open', () => {
      console.log('WebSocket连接成功');
      this.reconnectAttempts = 0;
      
      // 触发连接成功回调
      const handler = this.messageHandlers.get('open');
      if (handler) {
        handler({});
      }
    });
    
    this.ws.on('message', (err, value) => {
      if (!err && value) {
        try {
          const message = JSON.parse(value.toString());
          this.handleMessage(message);
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
        }
      }
    });
    
    this.ws.on('error', (err) => {
      console.error('WebSocket错误:', JSON.stringify(err));
      
      // 触发错误回调
      const handler = this.messageHandlers.get('error');
      if (handler) {
        handler({ error: err });
      }
    });
    
    this.ws.on('close', () => {
      console.log('WebSocket连接关闭');
      
      // 触发关闭回调
      const handler = this.messageHandlers.get('close');
      if (handler) {
        handler({});
      }
      
      // 自动重连
      if (!this.isManualClose) {
        this.attemptReconnect();
      }
    });
    
    await this.ws.connect(this.url);
  }
  
  /**
   * 发送消息
   */
  send(data: any): void {
    if (this.ws) {
      try {
        this.ws.send(JSON.stringify(data));
      } catch (error) {
        console.error('发送WebSocket消息失败:', error);
      }
    } else {
      console.error('WebSocket未连接');
    }
  }
  
  /**
   * 注册消息处理器
   */
  on(eventType: string, handler: (data: any) => void): void {
    this.messageHandlers.set(eventType, handler);
  }
  
  /**
   * 移除消息处理器
   */
  off(eventType: string): void {
    this.messageHandlers.delete(eventType);
  }
  
  /**
   * 处理消息
   */
  private handleMessage(message: any): void {
    // 特定类型处理器
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message);
    }
    
    // 通用处理器
    const allHandler = this.messageHandlers.get('*');
    if (allHandler) {
      allHandler(message);
    }
  }
  
  /**
   * 尝试重连
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay);
    } else {
      console.error('WebSocket重连失败，已达到最大重试次数');
      
      // 触发重连失败回调
      const handler = this.messageHandlers.get('reconnect_failed');
      if (handler) {
        handler({});
      }
    }
  }
  
  /**
   * 关闭连接
   */
  close(): void {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.ws !== null;
  }
}
