/**
 * 服务类
 */
export class AppConfig {
  // 处理逻辑
  // IP
  // 处理逻辑
  public static readonly BASE_URL: string = 'http://192.168.43.6:8000';
  
  // API
  public static readonly API_VERSION: string = 'v4';
  
  // 处理逻辑
  public static readonly CONNECT_TIMEOUT: number = 60000;
  public static readonly READ_TIMEOUT: number = 60000;
  
  // ID
  public static readonly DEFAULT_USER_ID: string = 'default_user';
  
  // 处理逻辑
  public static readonly SENSOR_INTERVAL: number = 5000; // 5
  public static readonly CONTEXT_INTERVAL: number = 60000; // 1
  
  /**
   * API
   */
  public static getApiUrl(path: string): string {
    return `${AppConfig.BASE_URL}${path}`;
  }
  
  /**
   * V4 API
   */
  public static getV4ApiUrl(path: string): string {
    return `${AppConfig.BASE_URL}/api/${AppConfig.API_VERSION}${path}`;
  }
}
