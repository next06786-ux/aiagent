/**
 * AI核心服务
 * 处理意图识别和功能导航
 */
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { RecognizeIntentRequest, NavigateRequest, EmptyObject } from '../types/RequestInterfaces';

export class AICoreService {
  private httpClient = HttpClient.getInstance();
  
  /**
   * 识别用户意图
   */
  async recognizeIntent(
    userId: string,
    message: string,
    context?: Record<string, Object>
  ): Promise<IntentResult> {
    const requestData: RecognizeIntentRequest = {
      user_id: userId,
      message: message,
      context: context || new EmptyObject()
    };
    
    const result = await this.httpClient.post<IntentResult>(
      ApiConstants.AI_CORE.INTENT,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 导航到功能模块
   */
  async navigateToFunction(
    userId: string,
    intent: string,
    params?: Record<string, Object>
  ): Promise<NavigationResult> {
    const requestData: NavigateRequest = {
      user_id: userId,
      intent: intent,
      params: params || new EmptyObject()
    };
    
    const result = await this.httpClient.post<NavigationResult>(
      ApiConstants.AI_CORE.NAVIGATE,
      requestData
    );
    
    return result.data;
  }
}

/**
 * 实体信息
 */
export interface EntityInfo {
  type: string;
  value: string;
  confidence: number;
}

/**
 * 意图识别结果
 */
export interface IntentResult {
  intent: string;
  confidence: number;
  entities: EntityInfo[];
  suggested_action: string;
  module: string;
}

/**
 * 导航结果
 */
export interface NavigationResult {
  success: boolean;
  module: string;
  page: string;
  params: Record<string, Object>;
  message: string;
}
