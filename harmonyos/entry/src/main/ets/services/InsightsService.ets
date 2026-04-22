/**
 * 智慧洞察服务
 * 处理三个专业Agent的洞察功能
 */
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { InsightResult, Insight, InsightType } from '../models/Insight';
import { GetInsightRequest, EmptyObject } from '../types/RequestInterfaces';

export class InsightsService {
  private httpClient = HttpClient.getInstance();
  
  /**
   * 获取人际关系洞察
   */
  async getRelationshipInsight(
    userId: string,
    query: string,
    context?: Record<string, Object>
  ): Promise<InsightResult> {
    const requestData: GetInsightRequest = {
      user_id: userId,
      query: query,
      context: context || new EmptyObject()
    };
    
    const result = await this.httpClient.post<InsightResult>(
      ApiConstants.INSIGHTS.RELATIONSHIP,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 获取教育升学洞察
   */
  async getEducationInsight(
    userId: string,
    query: string,
    context?: Record<string, Object>
  ): Promise<InsightResult> {
    const requestData: GetInsightRequest = {
      user_id: userId,
      query: query,
      context: context || new EmptyObject()
    };
    
    const result = await this.httpClient.post<InsightResult>(
      ApiConstants.INSIGHTS.EDUCATION,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 获取职业规划洞察
   */
  async getCareerInsight(
    userId: string,
    query: string,
    context?: Record<string, Object>
  ): Promise<InsightResult> {
    const requestData: GetInsightRequest = {
      user_id: userId,
      query: query,
      context: context || new EmptyObject()
    };
    
    const result = await this.httpClient.post<InsightResult>(
      ApiConstants.INSIGHTS.CAREER,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 获取Agent状态
   */
  async getAgentsStatus(): Promise<Record<string, Object>> {
    const result = await this.httpClient.get<Record<string, Object>>(
      ApiConstants.INSIGHTS.AGENTS_STATUS,
      {}
    );
    
    return result.data;
  }
  
  /**
   * 获取洞察（通用方法）
   */
  async getInsight(
    userId: string,
    type: 'relationship' | 'education' | 'career',
    query: string,
    context?: Record<string, Object>
  ): Promise<InsightResult> {
    switch (type) {
      case 'relationship':
        return this.getRelationshipInsight(userId, query, context);
      case 'education':
        return this.getEducationInsight(userId, query, context);
      case 'career':
        return this.getCareerInsight(userId, query, context);
      default:
        throw new Error(`未知的洞察类型: ${type}`);
    }
  }
  
  /**
   * 获取洞察列表
   */
  async getInsights(type: InsightType): Promise<Insight[]> {
    const result = await this.httpClient.get<Insight[]>(
      `${ApiConstants.INSIGHTS.RELATIONSHIP}?type=${type}`,
      {}
    );
    
    return result.data || [];
  }
}
