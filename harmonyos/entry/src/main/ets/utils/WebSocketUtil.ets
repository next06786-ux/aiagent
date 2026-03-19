/**
 * WebSocket 工具类
 * 用于实时流式通信
 */
import webSocket from '@ohos.net.webSocket';
import { ApiConfig } from '../config/ApiConfig';

export class WebSocketUtil {
  private ws: webSocket.WebSocket | null = null;
  private url: string = '';
  private isConnected: boolean = false;
  private messageCallback: ((data: string) => void) | null = null;
  private errorCallback: ((error: string) => void) | null = null;
  private closeCallback: (() => void) | null = null;
  
  /**
   * 连接 WebSocket
   */
  async connect(path: string): Promise<void> {
    // 构造 WebSocket URL (ws:// 或 wss://)
    const baseUrl = ApiConfig.getBaseUrl();
    this.url = baseUrl.replace('http://', 'ws://').replace('https://', 'wss://') + path;
    
    console.info('[WebSocket] 开始连接:', this.url);
    
    return new Promise<void>((resolve, reject) => {
      try {
        this.ws = webSocket.createWebSocket();
        
        // 监听打开事件
        this.ws.on('open', (err, value) => {
          if (!err) {
            console.info('[WebSocket] ✅ 连接成功');
            this.isConnected = true;
            resolve();
          } else {
            console.error('[WebSocket] ❌ 连接失败:', JSON.stringify(err));
            reject(new Error('WebSocket连接失败'));
          }
        });
        
        // 监听消息事件
        this.ws.on('message', (err, value) => {
          if (!err) {
            const data = value as string;
            console.info('[WebSocket] 📨 收到消息:', data.substring(0, 100));
            
            if (this.messageCallback) {
              this.messageCallback(data);
            }
          } else {
            console.error('[WebSocket] ❌ 消息接收失败:', JSON.stringify(err));
          }
        });
        
        // 监听关闭事件
        this.ws.on('close', (err, value) => {
          console.info('[WebSocket] 🔌 连接已关闭');
          this.isConnected = false;
          
          if (this.closeCallback) {
            this.closeCallback();
          }
        });
        
        // 监听错误事件
        this.ws.on('error', (err) => {
          console.error('[WebSocket] ❌ 错误:', JSON.stringify(err));
          this.isConnected = false;
          
          if (this.errorCallback) {
            this.errorCallback(JSON.stringify(err));
          }
        });
        
        // 发起连接
        this.ws.connect(this.url, (err, value) => {
          if (err) {
            console.error('[WebSocket] ❌ 连接请求失败:', JSON.stringify(err));
            reject(new Error('WebSocket连接请求失败'));
          }
        });
        
      } catch (error) {
        console.error('[WebSocket] ❌ 创建失败:', error);
        reject(error);
      }
    });
  }
  
  /**
   * 发送消息
   */
  send(data: string | Object): void {
    if (!this.ws || !this.isConnected) {
      console.error('[WebSocket] ❌ 未连接，无法发送消息');
      return;
    }
    
    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      console.info('[WebSocket] 📤 发送消息:', message.substring(0, 100));
      
      this.ws.send(message, (err) => {
        if (err) {
          console.error('[WebSocket] ❌ 发送失败:', JSON.stringify(err));
        } else {
          console.info('[WebSocket] ✅ 发送成功');
        }
      });
    } catch (error) {
      console.error('[WebSocket] ❌ 发送异常:', error);
    }
  }
  
  /**
   * 关闭连接
   */
  close(): void {
    if (this.ws) {
      console.info('[WebSocket] 关闭连接...');
      
      try {
        this.ws.close((err) => {
          if (err) {
            console.error('[WebSocket] ❌ 关闭失败:', JSON.stringify(err));
          } else {
            console.info('[WebSocket] ✅ 已关闭');
          }
        });
      } catch (error) {
        console.error('[WebSocket] ❌ 关闭异常:', error);
      }
      
      // 清理事件监听
      this.ws.off('open');
      this.ws.off('message');
      this.ws.off('close');
      this.ws.off('error');
      
      this.ws = null;
      this.isConnected = false;
    }
  }
  
  /**
   * 设置消息回调
   */
  onMessage(callback: (data: string) => void): void {
    this.messageCallback = callback;
  }
  
  /**
   * 设置错误回调
   */
  onError(callback: (error: string) => void): void {
    this.errorCallback = callback;
  }
  
  /**
   * 设置关闭回调
   */
  onClose(callback: () => void): void {
    this.closeCallback = callback;
  }
  
  /**
   * 检查连接状态
   */
  isConnectedStatus(): boolean {
    return this.isConnected;
  }
}
