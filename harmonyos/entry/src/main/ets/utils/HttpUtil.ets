/**
 * HTTP 工具类
 * 封装 HTTP 请求
 */
import http from '@ohos.net.http';
import util from '@ohos.util';
import { ApiConfig } from '../config/ApiConfig';

export class HttpUtil {
  /**
   * GET 请求
   */
  static async get(path: string, params?: Record<string, string>): Promise<http.HttpResponse> {
    let url = ApiConfig.getApiUrl(path);
    
    // 添加查询参数
    if (params) {
      const queryString = Object.keys(params)
        .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
        .join('&');
      url = `${url}?${queryString}`;
    }
    
    return HttpUtil.request(url, 'GET');
  }
  
  /**
   * POST 请求
   */
  static async post(path: string, data?: Object): Promise<http.HttpResponse> {
    const url = ApiConfig.getApiUrl(path);
    console.info('[HttpUtil] POST:', url);
    console.info('[HttpUtil] 请求数据:', JSON.stringify(data));
    const response = await HttpUtil.request(url, 'POST', data);
    console.info('[HttpUtil] 响应码:', response.responseCode);
    console.info('[HttpUtil] 响应数据:', response.result);
    return response;
  }
  
  /**
   * DELETE 请求
   */
  static async delete(path: string): Promise<http.HttpResponse> {
    const url = ApiConfig.getApiUrl(path);
    console.info('[HttpUtil] DELETE:', url);
    const response = await HttpUtil.request(url, 'DELETE');
    console.info('[HttpUtil] 响应码:', response.responseCode);
    return response;
  }
  
  /**
   * PUT 请求
   */
  static async put(path: string, data?: Object): Promise<http.HttpResponse> {
    const url = ApiConfig.getApiUrl(path);
    console.info('[HttpUtil] PUT:', url);
    console.info('[HttpUtil] 请求数据:', JSON.stringify(data));
    const response = await HttpUtil.request(url, 'PUT', data);
    console.info('[HttpUtil] 响应码:', response.responseCode);
    return response;
  }
  
  /**
   * POST 流式请求（SSE）- HarmonyOS 兼容方案
   * 
   * 由于 HarmonyOS HTTP 模块的 dataReceive 事件在 SSE 场景下不触发，
   * 我们采用"伪流式"方案：等待完整响应后，手动模拟流式解析
   */
  static async postStream(
    path: string, 
    data: Object,
    onChunk: (chunk: string) => void
  ): Promise<http.HttpResponse> {
    const url = ApiConfig.getApiUrl(path);
    console.info('[HttpUtil] ========== 开始流式请求（兼容模式）==========');
    console.info('[HttpUtil] URL:', url);
    console.info('[HttpUtil] 请求数据:', JSON.stringify(data));
    
    return new Promise<http.HttpResponse>((resolve, reject) => {
      const httpRequest = http.createHttp();
      
      console.info('[HttpUtil] 发送 HTTP 请求...');
      
      // 发送请求
      httpRequest.request(
        url,
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
          },
          extraData: JSON.stringify(data),
          expectDataType: http.HttpDataType.STRING,
          usingProtocol: http.HttpProtocol.HTTP1_1,  // 强制使用 HTTP/1.1
          connectTimeout: 30000,
          readTimeout: 300000
        },
        (err, response) => {
          console.info('[HttpUtil] ========== 请求回调触发 ==========');
          
          if (!err) {
            console.info('[HttpUtil] ✅ 请求完成');
            console.info('[HttpUtil] 响应码:', response.responseCode);
            
            // 获取完整响应数据
            const fullData = response.result as string;
            console.info('[HttpUtil] 响应数据长度:', fullData.length, '字符');
            
            if (fullData && fullData.length > 0) {
              // 手动解析 SSE 格式并模拟流式回调
              const lines = fullData.split('\n');
              let chunkCount = 0;
              
              console.info('[HttpUtil] 开始模拟流式解析，总行数:', lines.length);
              
              for (const line of lines) {
                const trimmedLine = line.trim();
                if (trimmedLine && trimmedLine.startsWith('data: ')) {
                  chunkCount++;
                  console.info(`[HttpUtil] 📨 解析SSE行 #${chunkCount}: ${trimmedLine.substring(0, 80)}...`);
                  
                  // 立即回调（模拟流式效果）
                  onChunk(trimmedLine);
                  
                  // 可选：添加小延迟模拟真实流式效果
                  // 注意：这里是同步代码，无法真正异步延迟
                }
              }
              
              console.info(`[HttpUtil] ✅ 模拟流式解析完成，共处理 ${chunkCount} 个SSE事件`);
            } else {
              console.warn('[HttpUtil] ⚠️ 响应数据为空');
            }
            
            resolve(response);
          } else {
            console.error('[HttpUtil] ❌ 请求失败:', JSON.stringify(err));
            reject(err);
          }
          
          // 清理
          httpRequest.destroy();
          console.info('[HttpUtil] ========== 流式请求结束 ==========');
        }
      );
    });
  }
  
  /**
   * 基础请求方法
   */
  private static async request(
    url: string,
    method: string,
    data?: Object
  ): Promise<http.HttpResponse> {
    return new Promise((resolve, reject) => {
      const httpRequest = http.createHttp();
      
      let httpMethod: http.RequestMethod;
      if (method === 'POST') {
        httpMethod = http.RequestMethod.POST;
      } else if (method === 'DELETE') {
        httpMethod = http.RequestMethod.DELETE;
      } else if (method === 'PUT') {
        httpMethod = http.RequestMethod.PUT;
      } else {
        httpMethod = http.RequestMethod.GET;
      }
      
      httpRequest.request(
        url,
        {
          method: httpMethod,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: data ? JSON.stringify(data) : undefined,
          expectDataType: http.HttpDataType.STRING,
          connectTimeout: 60000,
          readTimeout: 60000
        },
        (err, response) => {
          if (!err) {
            resolve(response);
          } else {
            reject(err);
          }
          httpRequest.destroy();
        }
      );
    });
  }
  
  /**
   * 解析响应数据
   */
  static parseResponse<T>(response: http.HttpResponse): T {
    if (response.responseCode === 200) {
      const result = JSON.parse(response.result as string) as Object;
      return result as T;
    } else {
      throw new Error(`HTTP ${response.responseCode}: ${response.result}`);
    }
  }
}
