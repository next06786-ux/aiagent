/**
 * 生活分析服务 - 调用后端分析API
 * 集成6大领域分析、涌现检测、报告生成
 */
import http from '@ohos.net.http';
import { ApiConfig } from '../config/ApiConfig';

export interface HealthAnalysis {
  health_score: number;
  sleep_debt: number;
  immunity_score: number;
  fatigue_level: number;
  recovery_status: string;
  risk_factors: string[];
  recommendations: string[];
}

export interface TimeAnalysis {
  efficiency_score: number;
  cognitive_load: number;
  time_pressure: number;
  focus_time: number;
  procrastination_level: number;
  time_allocation: Record<string, number>;
  risk_factors: string[];
  recommendations: string[];
}

export interface FinanceAnalysis {
  savings_rate: number;
  financial_health: number;
  risk_level: string;
  spending_pattern: Record<string, number>;
  financial_stability: number;
  debt_ratio: number;
  risk_factors: string[];
  recommendations: string[];
}

export interface EmotionAnalysis {
  mood_score: number;
  emotional_stability: number;
  regulation_ability: number;
  risk_level: string;
  mood_trend: string;
  emotional_patterns: Record<string, Object>;
  risk_factors: string[];
  recommendations: string[];
}

export interface SocialAnalysis {
  loneliness_score: number;
  satisfaction_score: number;
  relationship_quality: number;
  social_engagement: number;
  support_network_strength: number;
  social_patterns: Record<string, Object>;
  risk_factors: string[];
  recommendations: string[];
}

export interface LearningAnalysis {
  learning_efficiency: number;
  knowledge_retention: number;
  progress_score: number;
  learning_consistency: number;
  skill_development: Record<string, number>;
  learning_patterns: Record<string, Object>;
  risk_factors: string[];
  recommendations: string[];
}

interface DomainsType {
  health: HealthAnalysis;
  time: TimeAnalysis;
  emotion: EmotionAnalysis;
  social: SocialAnalysis;
  finance: FinanceAnalysis;
  learning: LearningAnalysis;
}

export interface LifeAnalysis {
  user_id: string;
  timestamp: string;
  overall_score: number;
  domains: DomainsType;
  key_insights: string[];
  priority_actions: string[];
}

export interface EmergencePattern {
  id: string;
  type: string;
  domains: string[];
  description: string;
  confidence: number;
  impact_score: number;
  recommendations: string[];
}

interface EmergenceSummary {
  total_patterns: number;
  by_type: Record<string, number>;
  high_impact: number;
  patterns: EmergencePattern[];
}

export interface EmergenceReport {
  user_id: string;
  detection_time: string;
  summary: EmergenceSummary;
  patterns: EmergencePattern[];
}

export class LifeAnalysisService {
  private static instance: LifeAnalysisService;
  private baseUrl: string = ApiConfig.getBaseUrl();

  private constructor() {}

  static getInstance(): LifeAnalysisService {
    if (!LifeAnalysisService.instance) {
      LifeAnalysisService.instance = new LifeAnalysisService();
    }
    return LifeAnalysisService.instance;
  }

  /**
   * 获取综合生活分析
   */
  async getLifeAnalysis(userId: string): Promise<LifeAnalysis> {
    try {
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${this.baseUrl}/api/v4/life-analysis/${userId}`,
        {
          method: http.RequestMethod.GET,
          header: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        if ((result['code'] as number) === 200) {
          return result['data'] as LifeAnalysis;
        }
      }
      throw new Error('Failed to fetch life analysis');
    } catch (error) {
      console.error('Error fetching life analysis:', error);
      throw new Error('Error fetching life analysis');
    }
  }

  /**
   * 获取特定领域分析
   */
  async getDomainAnalysis(userId: string, domain: string): Promise<Record<string, Object>> {
    try {
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${this.baseUrl}/api/v4/domain-analysis/${userId}/${domain}`,
        {
          method: http.RequestMethod.GET,
          header: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        if ((result['code'] as number) === 200) {
          return (result['data'] as Record<string, Object>)['analysis'] as Record<string, Object>;
        }
      }
      throw new Error(`Failed to fetch ${domain} analysis`);
    } catch (error) {
      console.error(`Error fetching ${domain} analysis:`, error);
      throw new Error(`Error fetching ${domain} analysis`);
    }
  }

  /**
   * 获取涌现模式
   */
  async getEmergencePatterns(userId: string): Promise<EmergenceReport> {
    try {
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${this.baseUrl}/api/emergence/patterns/${userId}`,
        {
          method: http.RequestMethod.GET,
          header: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        if ((result['code'] as number) === 200) {
          return result['data'] as EmergenceReport;
        }
      }
      throw new Error('Failed to fetch emergence patterns');
    } catch (error) {
      console.error('Error fetching emergence patterns:', error);
      throw new Error('Error fetching emergence patterns');
    }
  }

  /**
   * 获取综合报告
   */
  async getComprehensiveReport(userId: string): Promise<Record<string, Object>> {
    try {
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${this.baseUrl}/api/emergence/report/${userId}`,
        {
          method: http.RequestMethod.GET,
          header: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        if ((result['code'] as number) === 200) {
          return result['data'] as Record<string, Object>;
        }
      }
      throw new Error('Failed to fetch comprehensive report');
    } catch (error) {
      console.error('Error fetching comprehensive report:', error);
      throw new Error('Error fetching comprehensive report');
    }
  }

  /**
   * 上传多模态数据
   */
  async uploadMultimodalData(userId: string, data: Record<string, Object>): Promise<Record<string, Object>> {
    try {
      const httpRequest = http.createHttp();
      const requestData: Record<string, Object> = {
        'user_id': userId,
        'timestamp': Date.now()
      };
      
      // 合并数据
      const keys = Object.keys(data);
      for (let i = 0; i < keys.length; i++) {
        const key = keys[i];
        requestData[key] = data[key];
      }
      
      const response = await httpRequest.request(
        `${this.baseUrl}/api/v4/multimodal/data`,
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: JSON.stringify(requestData)
        }
      );

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        if ((result['code'] as number) === 200) {
          return result['data'] as Record<string, Object>;
        }
      }
      throw new Error('Failed to upload multimodal data');
    } catch (error) {
      console.error('Error uploading multimodal data:', error);
      throw new Error('Error uploading multimodal data');
    }
  }

  /**
   * 提交反馈
   */
  async submitFeedback(userId: string, feedback: Record<string, Object>): Promise<Record<string, Object>> {
    try {
      const httpRequest = http.createHttp();
      const requestData: Record<string, Object> = {
        'user_id': userId
      };
      
      // 合并反馈数据
      const keys = Object.keys(feedback);
      for (let i = 0; i < keys.length; i++) {
        const key = keys[i];
        requestData[key] = feedback[key];
      }
      
      const response = await httpRequest.request(
        `${this.baseUrl}/api/hybrid/feedback`,
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: JSON.stringify(requestData)
        }
      );

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        if ((result['code'] as number) === 200) {
          return result['data'] as Record<string, Object>;
        }
      }
      throw new Error('Failed to submit feedback');
    } catch (error) {
      console.error('Error submitting feedback:', error);
      throw new Error('Error submitting feedback');
    }
  }

  /**
   * 获取进化指标
   */
  async getEvolutionMetrics(userId: string): Promise<Record<string, Object>> {
    try {
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${this.baseUrl}/api/hybrid/evolution/${userId}`,
        {
          method: http.RequestMethod.GET,
          header: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        if ((result['code'] as number) === 200) {
          return result['data'] as Record<string, Object>;
        }
      }
      throw new Error('Failed to fetch evolution metrics');
    } catch (error) {
      console.error('Error fetching evolution metrics:', error);
      throw new Error('Error fetching evolution metrics');
    }
  }
}

export default LifeAnalysisService.getInstance();

