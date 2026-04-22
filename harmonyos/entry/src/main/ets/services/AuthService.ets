/**
 * 认证服务
 * 处理用户注册、登录、登出
 */
import dataPreferences from '@ohos.data.preferences';
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { AppConstants } from '../constants/AppConstants';
import { User, AuthResult } from '../models/User';
import { common } from '@kit.AbilityKit';

/**
 * 注册请求接口
 */
interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  nickname: string;
}

/**
 * 登录请求接口
 */
interface LoginRequest {
  username: string;
  password: string;
}

/**
 * 空请求接口
 */
interface EmptyRequest {
}

export class AuthService {
  private httpClient = HttpClient.getInstance();
  private context: common.UIAbilityContext | null = null;
  
  /**
   * 设置Context
   */
  setContext(context: common.UIAbilityContext): void {
    this.context = context;
  }
  
  /**
   * 用户注册
   */
  async register(
    username: string,
    email: string,
    password: string,
    nickname: string
  ): Promise<AuthResult> {
    const requestData: RegisterRequest = {
      username: username,
      email: email,
      password: password,
      nickname: nickname
    };
    
    const result = await this.httpClient.post<AuthResult>(
      ApiConstants.AUTH.REGISTER,
      requestData
    );
    
    if (result.code === 200 && result.data) {
      // 保存Token和用户信息
      await this.saveToken(result.data.token);
      await this.saveUserInfo(result.data);
    }
    
    return result.data;
  }
  
  /**
   * 用户登录
   */
  async login(username: string, password: string): Promise<AuthResult> {
    const requestData: LoginRequest = {
      username: username,
      password: password
    };
    
    const result = await this.httpClient.post<AuthResult>(
      ApiConstants.AUTH.LOGIN,
      requestData
    );
    
    if (result.code === 200 && result.data) {
      // 保存Token和用户信息
      await this.saveToken(result.data.token);
      await this.saveUserInfo(result.data);
    }
    
    return result.data;
  }
  
  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    try {
      const emptyData: EmptyRequest = {};
      await this.httpClient.post<Object>(ApiConstants.AUTH.LOGOUT, emptyData);
    } catch (error) {
      console.error('登出请求失败:', error);
    } finally {
      // 清除本地数据
      await this.clearAuthData();
    }
  }
  
  /**
   * 保存Token
   */
  private async saveToken(token: string): Promise<void> {
    if (!this.context) {
      throw new Error('Context未设置');
    }
    const preferences = await dataPreferences.getPreferences(
      this.context,
      'auth'
    );
    await preferences.put(AppConstants.CACHE_KEYS.AUTH_TOKEN, token);
    await preferences.flush();
  }
  
  /**
   * 获取Token
   */
  async getToken(): Promise<string> {
    if (!this.context) {
      return '';
    }
    const preferences = await dataPreferences.getPreferences(
      this.context,
      'auth'
    );
    return await preferences.get(AppConstants.CACHE_KEYS.AUTH_TOKEN, '') as string;
  }
  
  /**
   * 保存用户信息
   */
  private async saveUserInfo(userInfo: AuthResult): Promise<void> {
    if (!this.context) {
      throw new Error('Context未设置');
    }
    const preferences = await dataPreferences.getPreferences(
      this.context,
      'auth'
    );
    await preferences.put(AppConstants.CACHE_KEYS.USER_INFO, JSON.stringify(userInfo));
    await preferences.flush();
  }
  
  /**
   * 获取用户信息
   */
  async getUserInfo(): Promise<User | null> {
    if (!this.context) {
      return null;
    }
    try {
      const preferences = await dataPreferences.getPreferences(
        this.context,
        'auth'
      );
      const userInfoStr = await preferences.get(AppConstants.CACHE_KEYS.USER_INFO, '') as string;
      
      if (userInfoStr) {
        return new User(JSON.parse(userInfoStr));
      }
    } catch (error) {
      console.error('获取用户信息失败:', error);
    }
    
    return null;
  }
  
  /**
   * 检查是否已登录
   */
  async isLoggedIn(): Promise<boolean> {
    const token = await this.getToken();
    return token.length > 0;
  }
  
  /**
   * 清除认证数据
   */
  private async clearAuthData(): Promise<void> {
    if (!this.context) {
      return;
    }
    const preferences = await dataPreferences.getPreferences(
      this.context,
      'auth'
    );
    await preferences.clear();
    await preferences.flush();
  }
}
