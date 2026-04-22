/**
 * HTTP拦截器
 * 处理认证、响应拦截等
 */
import http from '@ohos.net.http';
import router from '@ohos.router';
import dataPreferences from '@ohos.data.preferences';
import { AppConstants } from '../constants/AppConstants';

export class HttpInterceptor {
  /**
   * 添加认证头
   */
  static async addAuthHeader(request: http.HttpRequestOptions): Promise<http.HttpRequestOptions> {
    try {
      const preferences = await dataPreferences.getPreferences(
        getContext(this),
        'auth'
      );
      const token = await preferences.get(AppConstants.CACHE_KEYS.AUTH_TOKEN, '') as string;
      
      if (token) {
        request.header = {
          ...request.header,
          'Authorization': `Bearer ${token}`
        };
      }
    } catch (error) {
      console.error('获取Token失败:', error);
    }
    
    return request;
  }
  
  /**
   * 处理响应
   */
  static async handleResponse(response: http.HttpResponse): Promise<any> {
    try {
      const result = JSON.parse(response.result.toString());
      
      // Token过期处理
      if (result.code === 401) {
        // 清除Token
        try {
          const preferences = await dataPreferences.getPreferences(
            getContext(this),
            'auth'
          );
          await preferences.clear();
          await preferences.flush();
        } catch (error) {
          console.error('清除Token失败:', error);
        }
        
        // 跳转到登录页
        router.pushUrl({ url: 'pages/LoginPage' });
        throw new Error('Token已过期，请重新登录');
      }
      
      // 其他错误处理
      if (result.code !== 200 && result.code !== 0) {
        throw new Error(result.message || '请求失败');
      }
      
      return result;
      
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error('响应数据格式错误');
      }
      throw error;
    }
  }
}
