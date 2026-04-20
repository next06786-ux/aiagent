/**
 * 知识图谱服务
 * 处理知识星图相关功能
 */
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { StarMapData, KnowledgeResult } from '../models/KnowledgeNode';

export class KnowledgeGraphService {
  private httpClient = HttpClient.getInstance();
  
  /**
   * 添加信息到知识图谱
   */
  async addInformation(
    userId: string,
    sourceType: 'conversation' | 'photo' | 'sensor',
    content: string,
    entities?: any[],
    relationships?: any[]
  ): Promise<void> {
    await this.httpClient.post(
      ApiConstants.KNOWLEDGE.ADD_INFO,
      {
        user_id: userId,
        source_type: sourceType,
        content,
        entities: entities || [],
        relationships: relationships || []
      }
    );
  }
  
  /**
   * 查询知识图谱
   */
  async queryKnowledge(
    userId: string,
    query: string,
    queryType: 'entity' | 'relationship' | 'pattern' = 'entity'
  ): Promise<KnowledgeResult> {
    const result = await this.httpClient.post<KnowledgeResult>(
      ApiConstants.KNOWLEDGE.QUERY,
      {
        user_id: userId,
        query,
        query_type: queryType
      }
    );
    
    return result.data;
  }
  
  /**
   * 获取人际关系图谱
   */
  async getRelationships(userId: string): Promise<any> {
    const result = await this.httpClient.get(
      `${ApiConstants.KNOWLEDGE.RELATIONSHIPS}/${userId}`
    );
    
    return result.data;
  }
  
  /**
   * 获取知识统计
   */
  async getStats(userId: string): Promise<any> {
    const result = await this.httpClient.get(
      `${ApiConstants.KNOWLEDGE.STATS}/${userId}`
    );
    
    return result.data;
  }
  
  /**
   * 获取职业星图
   */
  async getCareerStarMap(userId: string): Promise<StarMapData> {
    const result = await this.httpClient.get<StarMapData>(
      `${ApiConstants.VERTICAL.CAREER_STAR_MAP}/${userId}`
    );
    
    return result.data;
  }
  
  /**
   * 获取教育星图
   */
  async getEducationStarMap(userId: string): Promise<StarMapData> {
    const result = await this.httpClient.get<StarMapData>(
      `${ApiConstants.VERTICAL.EDUCATION_STAR_MAP}/${userId}`
    );
    
    return result.data;
  }
  
  /**
   * 获取人际关系星图
   */
  async getRelationshipStarMap(userId: string): Promise<StarMapData> {
    const result = await this.httpClient.get<StarMapData>(
      `${ApiConstants.VERTICAL.RELATIONSHIP_STAR_MAP}/${userId}`
    );
    
    return result.data;
  }
  
  /**
   * 获取星图数据（通用方法）
   */
  async getStarMap(
    userId: string,
    type: 'career' | 'education' | 'relationship'
  ): Promise<StarMapData> {
    switch (type) {
      case 'career':
        return this.getCareerStarMap(userId);
      case 'education':
        return this.getEducationStarMap(userId);
      case 'relationship':
        return this.getRelationshipStarMap(userId);
      default:
        throw new Error(`未知的星图类型: ${type}`);
    }
  }
}
