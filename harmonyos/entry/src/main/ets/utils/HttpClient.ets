/**
 * HTTP客户端
 * 对标 web/src/services/api.ts
 * 提供统一的HTTP请求封装
 */
import http from '@ohos.net.http';
import { ApiConstants } from '../constants/ApiConstants';
import { ApiEnvelope } from '../types/ApiTypes';

/**
 * API错误类
 */
export class ApiError extends Error {
  status: number;
  details?: any;

  constructor(message: string, status: number = 500, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * HTTP客户端类
 */
export class HttpClient {
  private static instance: HttpClient;
  private baseUrl: string = ApiConstants.BASE_URL;

  private constructor() {}

  /**
   * 获取单例
   */
  static getInstance(): HttpClient {
    if (!HttpClient.instance) {
      HttpClient.instance = new HttpClient();
    }
    return HttpClient.instance;
  }

  /**
   * 构建完整URL
   */
  private buildUrl(path: string): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${this.baseUrl}${cleanPath}`;
  }

  /**
   * 通用请求方法
   */
  private async request<T>(
    path: string,
    method: http.RequestMethod,
    body?: any,
    headers?: Record<string, string>
  ): Promise<T> {
    const startTime = Date.now();
    const url = this.buildUrl(path);
    
    console.log(`[HTTP] 🚀 ${method} ${url}`);

    const httpRequest = http.createHttp();

    try {
      const response = await httpRequest.request(url, {
        method: method,
        header: {
          'Content-Type': 'application/json',
          'Connection': 'keep-alive',
          ...headers
        },
        extraData: body ? JSON.stringify(body) : undefined,
        expectDataType: http.HttpDataType.STRING,
        connectTimeout: 30000,
        readTimeout: 30000
      });

      const fetchTime = Date.now() - startTime;
      console.log(`[HTTP] 📥 ${url} - ${response.responseCode} (${fetchTime}ms)`);

      // 解析响应
      let payload: any;
      try {
        payload = JSON.parse(response.result as string);
      } catch (e) {
        payload = response.result;
      }

      const totalTime = Date.now() - startTime;
      console.log(`[HTTP] ✅ ${url} - 完成 (${totalTime}ms)`);

      // 检查HTTP状态码
      if (response.responseCode < 200 || response.responseCode >= 300) {
        const message = payload?.message || `请求失败 (${response.responseCode})`;
        throw new ApiError(message, response.responseCode, payload);
      }

      return payload as T;
    } catch (error) {
      const totalTime = Date.now() - startTime;
      console.error(`[HTTP] ❌ ${url} - 失败 (${totalTime}ms)`, error);
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(
        error.message || '网络请求失败',
        0,
        error
      );
    } finally {
      httpRequest.destroy();
    }
  }

  /**
   * GET请求
   */
  async get<T>(path: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(path, http.RequestMethod.GET, undefined, headers);
  }

  /**
   * POST请求
   */
  async post<T>(path: string, body?: any, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(path, http.RequestMethod.POST, body, headers);
  }

  /**
   * PUT请求
   */
  async put<T>(path: string, body?: any, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(path, http.RequestMethod.PUT, body, headers);
  }

  /**
   * DELETE请求
   */
  async delete<T>(path: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(path, http.RequestMethod.DELETE, undefined, headers);
  }

  /**
   * 设置基础URL（用于测试）
   */
  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }
}

/**
 * 便捷方法 - 对标Web端api.ts
 */

/**
 * 通用JSON请求
 */
export async function requestJson<T>(
  path: string,
  method: http.RequestMethod = http.RequestMethod.GET,
  body?: any,
  headers?: Record<string, string>
): Promise<T> {
  const client = HttpClient.getInstance();
  
  switch (method) {
    case http.RequestMethod.GET:
      return client.get<T>(path, headers);
    case http.RequestMethod.POST:
      return client.post<T>(path, body, headers);
    case http.RequestMethod.PUT:
      return client.put<T>(path, body, headers);
    case http.RequestMethod.DELETE:
      return client.delete<T>(path, headers);
    default:
      return client.get<T>(path, headers);
  }
}

/**
 * POST JSON请求
 */
export async function postJson<T>(
  path: string,
  body?: any,
  headers?: Record<string, string>
): Promise<T> {
  return HttpClient.getInstance().post<T>(path, body, headers);
}

/**
 * PUT JSON请求
 */
export async function putJson<T>(
  path: string,
  body?: any,
  headers?: Record<string, string>
): Promise<T> {
  return HttpClient.getInstance().put<T>(path, body, headers);
}

/**
 * GET JSON请求
 */
export async function getJson<T>(
  path: string,
  headers?: Record<string, string>
): Promise<T> {
  return HttpClient.getInstance().get<T>(path, headers);
}

/**
 * DELETE JSON请求
 */
export async function deleteJson<T>(
  path: string,
  headers?: Record<string, string>
): Promise<T> {
  return HttpClient.getInstance().delete<T>(path, headers);
}

/**
 * 带Token的请求头
 */
export function withAuth(token: string): Record<string, string> {
  return {
    'Authorization': `Bearer ${token}`
  };
}

/**
 * 默认导出
 */
export default HttpClient;
