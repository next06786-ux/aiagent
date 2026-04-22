/**
 * HTTP客户端封装
 * 统一处理HTTP请求、认证、错误处理
 */
import http from '@ohos.net.http';
import { ApiConstants } from '../constants/ApiConstants';
import { HttpInterceptor } from './HttpInterceptor';
import { common } from '@kit.AbilityKit';

export class HttpClient {
  private static instance: HttpClient;
  private baseUrl: string = ApiConstants.BASE_URL;
  private context: common.UIAbilityContext | null = null;
  
  private constructor() {}
  
  static getInstance(): HttpClient {
    if (!HttpClient.instance) {
      HttpClient.instance = new HttpClient();
    }
    return HttpClient.instance;
  }
  
  /**
   * 设置Context
   */
  setContext(context: common.UIAbilityContext): void {
    this.context = context;
  }
  
  /**
   * 通用请求方法
   */
  async request<T>(config: RequestConfig): Promise<ApiResponse<T>> {
    if (!this.context) {
      const error = new Error('Context未设置，请先调用setContext');
      throw error;
    }
    
    const httpRequest = http.createHttp();
    
    try {
      // 添加认证头
      const requestOptions: http.HttpRequestOptions = {
        method: config.method || http.RequestMethod.GET,
        header: {
          'Content-Type': 'application/json'
        },
        extraData: config.data,
        expectDataType: http.HttpDataType.STRING,
        connectTimeout: config.timeout || 60000,
        readTimeout: config.timeout || 60000
      };
      
      // 合并自定义header
      if (config.headers) {
        Object.keys(config.headers).forEach(key => {
          if (requestOptions.header && config.headers) {
            requestOptions.header[key] = config.headers[key];
          }
        });
      }
      
      const authConfig = await HttpInterceptor.addAuthHeader(requestOptions, this.context);
      const fullUrl = `${this.baseUrl}${config.url}`;
      
      const response = await httpRequest.request(fullUrl, authConfig);
      
      // 处理响应
      return await HttpInterceptor.handleResponse(response, this.context) as ApiResponse<T>;
      
    } catch (error) {
      console.error('HTTP请求失败:', JSON.stringify(error));
      const err = error as Error;
      throw err;
    } finally {
      httpRequest.destroy();
    }
  }
  
  /**
   * GET请求
   */
  async get<T>(url: string, params?: Record<string, Object>): Promise<ApiResponse<T>> {
    let queryString = '';
    if (params) {
      const paramPairs: string[] = [];
      Object.keys(params).forEach(key => {
        const value = params[key];
        if (value !== null && value !== undefined) {
          paramPairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(value.toString())}`);
        }
      });
      if (paramPairs.length > 0) {
        queryString = '?' + paramPairs.join('&');
      }
    }
    
    return this.request<T>({
      url: url + queryString,
      method: http.RequestMethod.GET
    });
  }
  
  /**
   * POST请求
   */
  async post<T>(url: string, data?: Object): Promise<ApiResponse<T>> {
    // 将数据转换为JSON字符串
    let postData: string | Object = '';
    if (data) {
      postData = JSON.stringify(data);
    }
    
    return this.request<T>({
      url,
      method: http.RequestMethod.POST,
      data: postData
    });
  }
  
  /**
   * PUT请求
   */
  async put<T>(url: string, data?: Object): Promise<ApiResponse<T>> {
    // 将数据转换为JSON字符串
    let putData: string | Object = '';
    if (data) {
      putData = JSON.stringify(data);
    }
    
    return this.request<T>({
      url,
      method: http.RequestMethod.PUT,
      data: putData
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
  data?: string | Object;
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
