/**
 * 用户认证服务
 * User Authentication Service
 */
import preferences from '@ohos.data.preferences';
import common from '@ohos.app.ability.common';
import { HttpUtil } from '../utils/HttpUtil';

// 用户信息接口
export interface UserInfo {
  user_id: string;
  username: string;
  email: string;
  nickname: string;
  avatar_url?: string;
  phone?: string;
  is_verified: boolean;
  created_at?: string;
  last_login?: string;
}

// 登录响应
export interface LoginResponse {
  user_id: string;
  username: string;
  email: string;
  nickname: string;
  avatar_url?: string;
  token: string;
}

// 注册请求
export class RegisterRequest {
  username: string = '';
  email: string = '';
  password: string = '';
  nickname: string = '';
}

// 登录请求
export class LoginRequest {
  username: string = '';
  password: string = '';
}

export class AuthService {
  private static instance: AuthService;
  private currentUser: UserInfo | null = null;
  private token: string = '';
  private isInitialized: boolean = false;
  
  private constructor() {
    // 不在构造函数中加载，延迟到第一次使用时
  }
  
  /**
   * 获取单例实例
   */
  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }
  
  /**
   * 初始化（延迟加载）- 公开方法供外部调用
   */
  async ensureInitialized(): Promise<void> {
    if (this.isInitialized) {
      return;
    }
    
    try {
      await this.loadUserFromStorage();
      this.isInitialized = true;
    } catch (err) {
      console.error('[AuthService] 初始化失败:', err);
      this.isInitialized = true; // 即使失败也标记为已初始化，避免重复尝试
    }
  }
  
  /**
   * 从本地存储加载用户信息
   */
  private async loadUserFromStorage(): Promise<void> {
    try {
      const context = getContext(this) as common.UIAbilityContext;
      const prefs = await preferences.getPreferences(context, 'lifeswarm_auth');
      
      const token = await prefs.get('token', '') as string;
      const userJson = await prefs.get('user_info', '') as string;
      
      if (token && userJson) {
        this.token = token;
        this.currentUser = JSON.parse(userJson) as UserInfo;
        console.info('[AuthService] 从本地加载用户信息:', this.currentUser?.username);
      }
    } catch (err) {
      console.error('[AuthService] 加载用户信息失败:', err);
    }
  }
  
  /**
   * 保存用户信息到本地存储
   */
  private async saveUserToStorage(token: string, userInfo: UserInfo): Promise<void> {
    try {
      const context = getContext(this) as common.UIAbilityContext;
      const prefs = await preferences.getPreferences(context, 'lifeswarm_auth');
      
      await prefs.put('token', token);
      await prefs.put('user_info', JSON.stringify(userInfo));
      await prefs.flush();
      
      this.token = token;
      this.currentUser = userInfo;
      
      console.info('[AuthService] 用户信息已保存');
    } catch (err) {
      console.error('[AuthService] 保存用户信息失败:', err);
    }
  }
  
  /**
   * 清除本地存储的用户信息
   */
  private async clearUserFromStorage(): Promise<void> {
    try {
      const context = getContext(this) as common.UIAbilityContext;
      const prefs = await preferences.getPreferences(context, 'lifeswarm_auth');
      
      await prefs.delete('token');
      await prefs.delete('user_info');
      await prefs.flush();
      
      this.token = '';
      this.currentUser = null;
      
      console.info('[AuthService] 用户信息已清除');
    } catch (err) {
      console.error('[AuthService] 清除用户信息失败:', err);
    }
  }
  
  /**
   * 用户注册
   */
  async register(username: string, email: string, password: string, nickname?: string): Promise<LoginResponse> {
    await this.ensureInitialized();
    
    try {
      const request = new RegisterRequest();
      request.username = username;
      request.email = email;
      request.password = password;
      request.nickname = nickname || username;
      
      console.info('[AuthService] 注册请求:', username, email);
      
      const response = await HttpUtil.post('/api/auth/register', request);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        
        if (result.code === 200) {
          const data = result.data as LoginResponse;
          
          // 保存用户信息
          const userInfo: UserInfo = {
            user_id: data.user_id,
            username: data.username,
            email: data.email,
            nickname: data.nickname,
            avatar_url: data.avatar_url,
            is_verified: false
          };
          
          await this.saveUserToStorage(data.token, userInfo);
          
          console.info('[AuthService] 注册成功:', data.username);
          return data;
        } else {
          throw new Error(result.message as string || '注册失败');
        }
      } else {
        throw new Error(`HTTP ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error('[AuthService] 注册失败:', error.message);
      throw new Error(`注册失败: ${error.message}`);
    }
  }
  
  /**
   * 用户登录
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    await this.ensureInitialized();
    
    try {
      const request = new LoginRequest();
      request.username = username;
      request.password = password;
      
      console.info('[AuthService] 登录请求:', username);
      
      const response = await HttpUtil.post('/api/auth/login', request);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        
        if (result.code === 200) {
          const data = result.data as LoginResponse;
          
          // 保存用户信息
          const userInfo: UserInfo = {
            user_id: data.user_id,
            username: data.username,
            email: data.email,
            nickname: data.nickname,
            avatar_url: data.avatar_url,
            is_verified: false
          };
          
          await this.saveUserToStorage(data.token, userInfo);
          
          console.info('[AuthService] 登录成功:', data.username);
          return data;
        } else {
          throw new Error(result.message as string || '登录失败');
        }
      } else {
        throw new Error(`HTTP ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error('[AuthService] 登录失败:', error.message);
      throw new Error(`登录失败: ${error.message}`);
    }
  }
  
  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    await this.ensureInitialized();
    
    try {
      if (this.token) {
        const logoutData = { 'token': this.token } as Record<string, string>;
        await HttpUtil.post('/api/auth/logout', logoutData);
      }
      
      await this.clearUserFromStorage();
      console.info('[AuthService] 登出成功');
    } catch (err) {
      console.error('[AuthService] 登出失败:', err);
      // 即使请求失败也清除本地数据
      await this.clearUserFromStorage();
    }
  }
  
  /**
   * 验证Token是否有效
   */
  async verifyToken(): Promise<boolean> {
    await this.ensureInitialized();
    
    try {
      if (!this.token) {
        return false;
      }
      
      const tokenData = { 'token': this.token } as Record<string, string>;
      const response = await HttpUtil.post('/api/auth/verify-token', tokenData);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, boolean>;
        return data.valid || false;
      }
      
      return false;
    } catch (err) {
      console.error('[AuthService] Token验证失败:', err);
      return false;
    }
  }
  
  /**
   * 获取当前用户信息
   */
  getCurrentUser(): UserInfo | null {
    // 同步方法，返回已加载的用户信息（可能为null）
    return this.currentUser;
  }
  
  /**
   * 获取当前Token
   */
  getToken(): string {
    // 同步方法，返回已加载的token
    return this.token;
  }
  
  /**
   * 是否已登录
   */
  isLoggedIn(): boolean {
    // 同步方法，检查是否有token和用户信息
    return this.token !== '' && this.currentUser !== null;
  }
  
  /**
   * 获取当前用户ID
   */
  getCurrentUserId(): string {
    // 同步方法，返回用户ID或默认值
    return this.currentUser?.user_id || 'default_user';
  }
  
  /**
   * 异步获取当前用户信息（确保已初始化）
   */
  async getCurrentUserAsync(): Promise<UserInfo | null> {
    await this.ensureInitialized();
    return this.currentUser;
  }
  
  /**
   * 异步检查是否已登录（确保已初始化）
   */
  async isLoggedInAsync(): Promise<boolean> {
    await this.ensureInitialized();
    return this.token !== '' && this.currentUser !== null;
  }
  
  /**
   * 更新用户信息
   */
  async updateUserInfo(nickname?: string, avatarUrl?: string, phone?: string): Promise<UserInfo> {
    await this.ensureInitialized();
    
    try {
      if (!this.currentUser) {
        throw new Error('未登录');
      }
      
      const updateData = {} as Record<string, string>;
      if (nickname) updateData['nickname'] = nickname;
      if (avatarUrl) updateData['avatar_url'] = avatarUrl;
      if (phone) updateData['phone'] = phone;
      
      const response = await HttpUtil.put(`/api/auth/user/${this.currentUser.user_id}`, updateData);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        
        if (result.code === 200) {
          const data = result.data as UserInfo;
          
          // 更新本地用户信息
          await this.saveUserToStorage(this.token, data);
          
          console.info('[AuthService] 用户信息更新成功');
          return data;
        } else {
          throw new Error(result.message as string || '更新失败');
        }
      } else {
        throw new Error(`HTTP ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error('[AuthService] 更新用户信息失败:', error.message);
      throw new Error(`更新失败: ${error.message}`);
    }
  }
  
  /**
   * 修改密码
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await this.ensureInitialized();
    
    try {
      if (!this.currentUser) {
        throw new Error('未登录');
      }
      
      const passwordData = {
        'user_id': this.currentUser.user_id,
        'old_password': oldPassword,
        'new_password': newPassword
      } as Record<string, string>;
      const response = await HttpUtil.post('/api/auth/change-password', passwordData);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        
        if (result.code === 200) {
          console.info('[AuthService] 密码修改成功');
          return;
        } else {
          throw new Error(result.message as string || '修改失败');
        }
      } else {
        throw new Error(`HTTP ${response.responseCode}`);
      }
    } catch (err) {
      const error = err as Error;
      console.error('[AuthService] 修改密码失败:', error.message);
      throw new Error(`修改密码失败: ${error.message}`);
    }
  }
}

/**
 * 获取认证服务实例
 */
export function getAuthService(): AuthService {
  return AuthService.getInstance();
}
