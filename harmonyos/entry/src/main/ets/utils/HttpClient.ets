/**
 * HTTP客户端封装
 * 统一处理HTTP请求、认证、错误处理
 */
import http from '@ohos.net.http';
import { ApiConstants } from '../constants/ApiConstants';
import { HttpInterceptor } from './HttpInterceptor';

export class HttpClient {
  private static instance: HttpClient;
  private baseUrl: string = ApiConstants.BASE_URL;
  
  private constructor() {}
  
  static getInstance(): HttpClient {
    if (!HttpClient.instance) {
      HttpClient.instance = new HttpClient();
    }
    return HttpClient.instance;
  }
  
  /**
   * 通用请求方法
   */
  async request<T>(config: RequestConfig): Promise<ApiResponse<T>> {
    const httpRequest = http.createHttp();
    
    try {
      // 添加认证头
      const requestOptions: http.HttpRequestOptions = {
        method: config.method || http.RequestMethod.GET,
        header: {
          'Content-Type': 'application/json',
          ...config.headers
        },
        extraData: config.data,
        expectDataType: http.HttpDataType.STRING,
        connectTimeout: config.timeout || 60000,
        readTimeout: config.timeout || 60000
      };
      
      const authConfig = await HttpInterceptor.addAuthHeader(requestOptions);
      const fullUrl = `${this.baseUrl}${config.url}`;
      
      const response = await httpRequest.request(fullUrl, authConfig);
      
      // 处理响应
      return await HttpInterceptor.handleResponse(response);
      
    } catch (error) {
      console.error('HTTP请求失败:', JSON.stringify(error));
      throw error;
    } finally {
      httpRequest.destroy();
    }
  }
  
  /**
   * GET请求
   */
  async get<T>(url: string, params?: Record<string, string>): Promise<ApiResponse<T>> {
    let queryString = '';
    if (params) {
      const paramPairs: string[] = [];
      Object.keys(params).forEach(key => {
        paramPairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`);
      });
      queryString = '?' + paramPairs.join('&');
    }
    
    return this.request<T>({
      url: url + queryString,
      method: http.RequestMethod.GET
    });
  }
  
  /**
   * POST请求
   */
  async post<T>(url: string, data?: Record<string, Object>): Promise<ApiResponse<T>> {
    return this.request<T>({
      url,
      method: http.RequestMethod.POST,
      data
    });
  }
  
  /**
   * PUT请求
   */
  async put<T>(url: string, data?: Record<string, Object>): Promise<ApiResponse<T>> {
    return this.request<T>({
      url,
      method: http.RequestMethod.PUT,
      data
    });
  }
  
  /**
   * DELETE请求
   */
  async delete<T>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>({
      url,
      method: http.RequestMethod.DELETE
    });
  }
  
  /**
   * 设置基础URL
   */
  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }
}

/**
 * 请求配置接口
 */
export interface RequestConfig {
  url: string;
  method?: http.RequestMethod;
  headers?: Record<string, string>;
  data?: Record<string, Object>;
  timeout?: number;
}

/**
 * API响应接口
 */
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}
