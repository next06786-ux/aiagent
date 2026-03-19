/**
 * 用户会话管理器
 * 全局管理当前登录用户的 ID，确保所有页面使用真实用户 ID
 */
import { AuthService } from './AuthService';
import emitter from '@ohos.events.emitter';

export class UserSessionManager {
  private static instance: UserSessionManager;
  private currentUserId: string = '';
  private isInitialized: boolean = false;
  private listeners: Set<(userId: string) => void> = new Set();
  
  // 事件ID定义
  private static readonly EVENT_USER_LOGIN = 1001;
  private static readonly EVENT_USER_LOGOUT = 1002;
  
  private constructor() {
    // 私有构造函数
  }
  
  /**
   * 获取单例实例
   */
  static getInstance(): UserSessionManager {
    if (!UserSessionManager.instance) {
      UserSessionManager.instance = new UserSessionManager();
    }
    return UserSessionManager.instance;
  }
  
  /**
   * 初始化会话管理器
   * 应该在应用启动时调用
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }
    
    try {
      console.info('[UserSessionManager] 开始初始化...');
      
      const authService = AuthService.getInstance();
      await authService.ensureInitialized();
      
      // 获取当前用户ID
      const user = authService.getCurrentUser();
      if (user && user.user_id) {
        this.currentUserId = user.user_id;
        console.info('[UserSessionManager] 加载用户ID:', this.currentUserId);
      } else {
        this.currentUserId = 'default_user';
        console.warn('[UserSessionManager] 未登录，使用默认用户ID');
      }
      
      this.isInitialized = true;
      
      // 通知所有监听器
      this.notifyListeners();
      
    } catch (err) {
      console.error('[UserSessionManager] 初始化失败:', err);
      this.currentUserId = 'default_user';
      this.isInitialized = true;
    }
  }
  
  /**
   * 获取当前用户ID（同步方法）
   * 如果未初始化，返回 default_user
   */
  getCurrentUserId(): string {
    if (!this.isInitialized) {
      console.warn('[UserSessionManager] 未初始化，返回默认用户ID');
      return 'default_user';
    }
    return this.currentUserId || 'default_user';
  }
  
  /**
   * 获取当前用户ID（异步方法，确保已初始化）
   */
  async getUserId(): Promise<string> {
    await this.initialize();
    return this.currentUserId || 'default_user';
  }
  
  /**
   * 用户登录后更新会话
   */
  async onUserLogin(userId: string): Promise<void> {
    console.info('[UserSessionManager] 用户登录:', userId);
    this.currentUserId = userId;
    this.isInitialized = true;
    
    // 通知所有监听器
    this.notifyListeners();
    
    // 发送全局事件
    try {
      const eventData: emitter.EventData = {
        data: {
          userId: userId
        }
      };
      emitter.emit({ eventId: UserSessionManager.EVENT_USER_LOGIN }, eventData);
    } catch (err) {
      console.error('[UserSessionManager] 发送登录事件失败:', err);
    }
  }
  
  /**
   * 用户登出后清除会话
   */
  async onUserLogout(): Promise<void> {
    console.info('[UserSessionManager] 用户登出');
    const oldUserId = this.currentUserId;
    this.currentUserId = 'default_user';
    
    // 通知所有监听器
    this.notifyListeners();
    
    // 发送全局事件
    try {
      const eventData: emitter.EventData = {
        data: {
          oldUserId: oldUserId
        }
      };
      emitter.emit({ eventId: UserSessionManager.EVENT_USER_LOGOUT }, eventData);
    } catch (err) {
      console.error('[UserSessionManager] 发送登出事件失败:', err);
    }
  }
  
  /**
   * 添加用户ID变化监听器
   */
  addListener(callback: (userId: string) => void): void {
    this.listeners.add(callback);
  }
  
  /**
   * 移除用户ID变化监听器
   */
  removeListener(callback: (userId: string) => void): void {
    this.listeners.delete(callback);
  }
  
  /**
   * 通知所有监听器
   */
  private notifyListeners(): void {
    const userId = this.currentUserId;
    this.listeners.forEach(callback => {
      try {
        callback(userId);
      } catch (err) {
        console.error('[UserSessionManager] 监听器回调失败:', err);
      }
    });
  }
  
  /**
   * 检查是否已登录
   */
  isLoggedIn(): boolean {
    return this.currentUserId !== '' && this.currentUserId !== 'default_user';
  }
  
  /**
   * 订阅用户登录事件
   */
  static subscribeLoginEvent(callback: (userId: string) => void): void {
    try {
      emitter.on({ eventId: UserSessionManager.EVENT_USER_LOGIN }, (eventData: emitter.EventData) => {
        const data = eventData.data as Record<string, string>;
        if (data && data.userId) {
          callback(data.userId);
        }
      });
    } catch (err) {
      console.error('[UserSessionManager] 订阅登录事件失败:', err);
    }
  }
  
  /**
   * 订阅用户登出事件
   */
  static subscribeLogoutEvent(callback: () => void): void {
    try {
      emitter.on({ eventId: UserSessionManager.EVENT_USER_LOGOUT }, () => {
        callback();
      });
    } catch (err) {
      console.error('[UserSessionManager] 订阅登出事件失败:', err);
    }
  }
}

/**
 * 获取用户会话管理器实例
 */
export function getUserSessionManager(): UserSessionManager {
  return UserSessionManager.getInstance();
}

/**
 * 快速获取当前用户ID（同步）
 */
export function getCurrentUserId(): string {
  return UserSessionManager.getInstance().getCurrentUserId();
}

/**
 * 快速获取当前用户ID（异步，确保已初始化）
 */
export async function getUserId(): Promise<string> {
  return await UserSessionManager.getInstance().getUserId();
}
