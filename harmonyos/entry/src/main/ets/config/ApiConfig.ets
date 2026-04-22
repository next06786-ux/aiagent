/**
 * API配置
 */

/**
 * API环境配置
 */
export interface ApiEnvironment {
  name: string;
  baseUrl: string;
  wsUrl: string;
}

/**
 * 开发环境
 */
export const developmentEnv: ApiEnvironment = {
  name: 'development',
  baseUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000'
};

/**
 * 生产环境
 */
export const productionEnv: ApiEnvironment = {
  name: 'production',
  baseUrl: 'https://api.example.com',
  wsUrl: 'wss://api.example.com'
};

/**
 * 当前环境
 */
export const currentEnv: ApiEnvironment = developmentEnv;

/**
 * 获取API基础URL
 */
export function getApiBaseUrl(): string {
  return currentEnv.baseUrl;
}

/**
 * 获取WebSocket URL
 */
export function getWsUrl(): string {
  return currentEnv.wsUrl;
}
