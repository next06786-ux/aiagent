/**
 * HTTP拦截器
 * 处理认证、响应拦截等
 */
import http from '@ohos.net.http';
import router from '@ohos.router';
import dataPreferences from '@ohos.data.preferences';
import { AppConstants } from '../constants/AppConstants';
import { common } from '@kit.AbilityKit';

export class HttpInterceptor {
  /**
   * 添加认证头
   */
  static async addAuthHeader(
    request: http.HttpRequestOptions,
    context: common.UIAbilityContext
  ): Promise<http.HttpRequestOptions> {
    try {
      const preferences = await dataPreferences.getPreferences(
        context,
        'auth'
      );
      const token = await preferences.get(AppConstants.CACHE_KEYS.AUTH_TOKEN, '') as string;
      
      if (token) {
        // 创建新的header对象
        const newHeader: Record<string, string> = {};
        if (request.header) {
          // 复制现有header
          Object.keys(request.header).forEach(key => {
            if (request.header) {
              newHeader[key] = request.header[key] as string;
            }
          });
        }
        // 添加Authorization
        newHeader['Authorization'] = `Bearer ${token}`;
        request.header = newHeader;
      }
    } catch (error) {
      console.error('获取Token失败:', error);
    }
    
    return request;
  }
  
  /**
   * 处理响应
   */
  static async handleResponse(
    response: http.HttpResponse,
    context: common.UIAbilityContext
  ): Promise<Object> {
    try {
      const result = JSON.parse(response.result.toString()) as Record<string, Object>;
      
      // 兼容两种响应格式：
      // 1. { code: 200, data: {...}, message: "..." }
      // 2. { success: true, data: {...}, message: "..." }
      
      const code = result.code as number;
      const success = result.success as boolean;
      
      // Token过期处理
      if (code === 401) {
        // 清除Token
        try {
          const preferences = await dataPreferences.getPreferences(
            context,
            'auth'
          );
          await preferences.clear();
          await preferences.flush();
        } catch (error) {
          console.error('清除Token失败:', error);
        }
        
        // 跳转到登录页
        router.pushUrl({ url: 'pages/LoginPage' });
        const error = new Error('Token已过期，请重新登录');
        throw error;
      }
      
      // 检查响应是否成功
      // 支持两种格式：code字段或success字段
      const isSuccess = (code === 200 || code === 0) || (success === true);
      
      if (!isSuccess) {
        const message = result.message as string || '请求失败';
        const error = new Error(message);
        throw error;
      }
      
      return result;
      
    } catch (error) {
      if (error instanceof SyntaxError) {
        const err = new Error('响应数据格式错误');
        throw err;
      }
      if (error instanceof Error) {
        throw error;
      }
      const err = new Error('未知错误');
      throw err;
    }
  }
}
