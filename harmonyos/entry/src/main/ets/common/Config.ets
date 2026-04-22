/**
 * 应用配置
 */

/**
 * 应用配置接口
 */
export interface AppConfig {
  apiBaseUrl: string;
  wsBaseUrl: string;
  appVersion: string;
  environment: 'development' | 'production';
}

/**
 * 默认配置
 */
export const defaultConfig: AppConfig = {
  apiBaseUrl: 'http://localhost:8000',
  wsBaseUrl: 'ws://localhost:8000',
  appVersion: '1.0.0',
  environment: 'development'
};

/**
 * 获取配置
 */
export function getConfig(): AppConfig {
  return defaultConfig;
}
