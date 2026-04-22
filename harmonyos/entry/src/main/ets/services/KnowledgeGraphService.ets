/**
 * 知识图谱服务
 * 处理知识星图相关功能
 */
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { StarMapData, KnowledgeResult, KnowledgeNode, KnowledgeEdge } from '../models/KnowledgeNode';
import { AddInformationRequest, QueryKnowledgeRequest, EmptyObject } from '../types/RequestInterfaces';

// 定义请求数据接口
class CareerGraphRequest {
  user_id: string = '';
  mastered_skills: string[] = [];
  partial_skills: string[] = [];
  missing_skills: string[] = [];
  target_direction: string = '';
}

class EducationGraphRequest {
  user_id: string = '';
  gpa: number = 0;
  gpa_max: number = 0;
  ranking_percent: number = 0;
  sat_act: number = 0;
  research_experience: number = 0;
  publications: number = 0;
  target_major: string = '';
  target_level: string = '';
  search_keyword: string = '';
  location: string = '';
}

class RelationshipGraphRequest {
  user_id: string = '';
  question: string = '';
  session_id: string | null = null;
}

// 定义后端响应的数据结构（用于类型转换）
class GraphDataWrapper {
  data: Object | null = null;
}

export class KnowledgeGraphService {
  private httpClient = HttpClient.getInstance();
  
  /**
   * 添加信息到知识图谱
   */
  async addInformation(
    userId: string,
    sourceType: 'conversation' | 'photo' | 'sensor',
    content: string,
    entities?: Object[],
    relationships?: Object[]
  ): Promise<void> {
    const entitiesData: Object[] = entities || [];
    const relationshipsData: Object[] = relationships || [];
    const requestData: AddInformationRequest = {
      user_id: userId,
      source_type: sourceType,
      content: content,
      entities: entitiesData,
      relationships: relationshipsData
    };
    
    await this.httpClient.post<Object>(
      ApiConstants.KNOWLEDGE.ADD_INFO,
      requestData
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
    const requestData: QueryKnowledgeRequest = {
      user_id: userId,
      query: query,
      query_type: queryType
    };
    
    const result = await this.httpClient.post<KnowledgeResult>(
      ApiConstants.KNOWLEDGE.QUERY,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 获取人际关系图谱
   */
  async getRelationships(userId: string): Promise<Object> {
    const result = await this.httpClient.get<Object>(
      `${ApiConstants.KNOWLEDGE.RELATIONSHIPS}/${userId}`,
      {}
    );
    
    return result.data;
  }
  
  /**
   * 获取知识统计
   */
  async getStats(userId: string): Promise<Object> {
    const result = await this.httpClient.get<Object>(
      `${ApiConstants.KNOWLEDGE.STATS}/${userId}`,
      {}
    );
    
    return result.data;
  }
  
  /**
   * 获取职业星图 - 使用POST请求，与Web端对齐
   * 完全按照Web端逻辑实现，对接同一套后端API
   */
  async getCareerStarMap(userId: string): Promise<StarMapData> {
    const requestData = new CareerGraphRequest();
    requestData.user_id = userId;
    requestData.mastered_skills = [];  // 空数组，让后端从知识图谱查询
    requestData.partial_skills = [];
    requestData.missing_skills = [];
    requestData.target_direction = 'Python工程师';
    
    console.info('[KnowledgeGraphService] 发起职业图谱请求:', JSON.stringify(requestData));
    
    const result = await this.httpClient.post<Object>(
      ApiConstants.VERTICAL.CAREER_STAR_MAP,
      requestData
    );
    
    console.info('[KnowledgeGraphService] 职业图谱响应:', JSON.stringify(result));
    
    // result本身就是完整的响应对象 {code, message, data}
    // 我们需要访问result.data来获取图谱数据
    const wrapper = new GraphDataWrapper();
    wrapper.data = result.data;
    return this.convertCareerGraphToStarMap(wrapper);
  }
  
  /**
   * 获取教育星图 - 使用POST请求，与Web端对齐
   */
  async getEducationStarMap(userId: string): Promise<StarMapData> {
    const requestData = new EducationGraphRequest();
    requestData.user_id = userId;
    requestData.gpa = 3.5;
    requestData.gpa_max = 4.0;
    requestData.ranking_percent = 0.2;
    requestData.sat_act = 1450;
    requestData.research_experience = 0.6;
    requestData.publications = 2;
    requestData.target_major = '计算机科学';
    requestData.target_level = 'master';
    requestData.search_keyword = '';
    requestData.location = '';
    
    console.info('[KnowledgeGraphService] 发起教育图谱请求:', JSON.stringify(requestData));
    
    const result = await this.httpClient.post<Object>(
      ApiConstants.VERTICAL.EDUCATION_STAR_MAP,
      requestData
    );
    
    console.info('[KnowledgeGraphService] 教育图谱响应:', JSON.stringify(result));
    
    const wrapper = new GraphDataWrapper();
    wrapper.data = result.data;
    return this.convertBackendDataToStarMap(wrapper, 'education');
  }
  
  /**
   * 获取人际关系星图 - 使用POST请求，与Web端对齐
   */
  async getRelationshipStarMap(userId: string): Promise<StarMapData> {
    const requestData = new RelationshipGraphRequest();
    requestData.user_id = userId;
    requestData.question = '';
    requestData.session_id = null;
    
    console.info('[KnowledgeGraphService] 发起人际关系图谱请求:', JSON.stringify(requestData));
    
    const result = await this.httpClient.post<Object>(
      ApiConstants.VERTICAL.RELATIONSHIP_STAR_MAP,
      requestData
    );
    
    console.info('[KnowledgeGraphService] 人际关系图谱响应:', JSON.stringify(result));
    
    const wrapper = new GraphDataWrapper();
    wrapper.data = result.data;
    return this.convertBackendDataToStarMap(wrapper, 'relationship');
  }
  
  /**
   * 转换职业图谱数据 - 专门处理career-graph API返回的数据
   * 完全按照Web端逻辑实现
   */
  private convertCareerGraphToStarMap(backendResponse: GraphDataWrapper): StarMapData {
    console.info('[KnowledgeGraphService] 开始转换职业图谱数据');
    
    const dataField = backendResponse.data as Record<string, Object> | null;
    if (!dataField) {
      console.error('[KnowledgeGraphService] 后端返回数据为空');
      return { nodes: [], edges: [], layers: [] };
    }
    
    const nodesArray = dataField.nodes as Object[] | null;
    const edgesArray = dataField.edges as Object[] | null;
    
    console.info(`[KnowledgeGraphService] 职业图谱原始数据: nodes=${nodesArray?.length || 0}, edges=${edgesArray?.length || 0}`);
    
    // 打印前5个节点的详细信息用于调试
    if (nodesArray && nodesArray.length > 0) {
      console.info('[KnowledgeGraphService] 前5个节点详情:');
      for (let i = 0; i < Math.min(5, nodesArray.length); i++) {
        const node = nodesArray[i] as Record<string, Object>;
        const position = node.position as Record<string, number> | null;
        console.info(`  节点${i}: id=${node.id}, label=${node.label}, type=${node.type}, pos=(${position?.x || 0}, ${position?.y || 0}, ${position?.z || 0})`);
      }
    }
    
    // 转换节点 - 使用后端返回的position（同心圆布局）
    const nodes: KnowledgeNode[] = (nodesArray || []).map((nodeObj: Object, index: number): KnowledgeNode => {
      const node = nodeObj as Record<string, Object>;
      const position = node.position as Record<string, number> | null;
      const metadata = node.metadata as Record<string, Object> | null;
      const nodeType = node.type as string || 'default';
      const isSelf = node.is_self as boolean || false;
      
      // 获取节点颜色 - 按照Web端逻辑
      let color = '#A0C4FF';
      if (nodeType === 'center' || isSelf) {
        color = '#E8F4FF';  // 中心节点"我"
      } else if (nodeType === 'skill') {
        const status = (metadata?.status as string) || 'mastered';
        if (status === 'mastered') color = '#4CAF50';      // 已掌握-绿色
        else if (status === 'partial') color = '#FFC107';  // 部分掌握-黄色
        else if (status === 'missing') color = '#F44336';  // 缺失-红色
      } else if (nodeType === 'job') {
        color = '#2196F3';  // 岗位-蓝色
      } else if (nodeType === 'company') {
        color = '#9C27B0';  // 公司-紫色
      }
      
      // 获取节点大小
      let size = 10;
      if (nodeType === 'center' || isSelf) {
        size = 20;
      } else if (nodeType === 'job') {
        size = 14;
      } else if (nodeType === 'company') {
        size = 16;
      } else if (nodeType === 'skill') {
        size = 12;
      }
      
      const createdNode = KnowledgeNode.create(
        node.id as string || '',
        (node.name as string) || (node.label as string) || '',
        nodeType,
        nodeType,  // category与type相同
        position?.x || 0,
        position?.y || 0,
        position?.z || 0,
        size,
        color
      );
      
      // 打印前10个节点的位置信息
      if (index < 10) {
        console.info(`[KnowledgeGraphService] 节点${index} 转换后: name=${createdNode.label}, type=${nodeType}, pos=(${createdNode.x}, ${createdNode.y}, ${createdNode.z}), color=${color}`);
      }
      
      return createdNode;
    });
    
    // 转换连线 - 后端返回的是edges字段
    const edges: KnowledgeEdge[] = (edgesArray || []).map((edgeObj: Object): KnowledgeEdge => {
      const edge = edgeObj as Record<string, Object>;
      const edgeType = edge.type as string || 'RELATED';
      const weight = (edge.weight as number) || (edge.strength as number) || 1.0;
      
      return KnowledgeEdge.create(
        edge.source as string || '',
        edge.target as string || '',
        edgeType,
        weight
      );
    });
    
    console.info(`[KnowledgeGraphService] 职业图谱转换完成: nodes=${nodes.length}, edges=${edges.length}`);
    if (edges.length > 0) {
      console.info(`[KnowledgeGraphService] 前3条边:`);
      for (let i = 0; i < Math.min(3, edges.length); i++) {
        console.info(`  边${i}: ${edges[i].from} -> ${edges[i].to}, type=${edges[i].type}, weight=${edges[i].weight}`);
      }
    }
    
    // 统计节点位置分布和类型分布
    let zeroPositionCount = 0;
    let nonZeroPositionCount = 0;
    const typeCount: Record<string, number> = {};
    
    nodes.forEach(node => {
      // 统计位置
      if (node.x === 0 && node.y === 0 && node.z === 0) {
        zeroPositionCount++;
      } else {
        nonZeroPositionCount++;
      }
      
      // 统计类型
      const nodeType = node.type || 'unknown';
      typeCount[nodeType] = (typeCount[nodeType] || 0) + 1;
    });
    
    console.info(`[KnowledgeGraphService] 位置统计: 原点=${zeroPositionCount}, 非原点=${nonZeroPositionCount}`);
    console.info(`[KnowledgeGraphService] 类型统计: ${JSON.stringify(typeCount)}`);
    
    return {
      nodes: nodes,
      edges: edges,
      layers: ['我', '技能', '岗位', '公司']
    };
  }
  
  /**
   * 转换后端数据格式为StarMapData
   * 处理后端返回的edges字段（不是links）
   */
  private convertBackendDataToStarMap(backendResponse: GraphDataWrapper, type: string): StarMapData {
    // 后端返回格式：{ success: true, data: { nodes: [...], edges: [...] }, message: "..." }
    console.info('[KnowledgeGraphService] 开始转换数据');
    
    // 提取data字段
    const dataField = backendResponse.data as Record<string, Object> | null;
    if (!dataField) {
      console.error('[KnowledgeGraphService] 后端返回数据为空');
      return {
        nodes: [],
        edges: [],
        layers: []
      };
    }
    
    console.info('[KnowledgeGraphService] data字段存在');
    
    // 提取nodes和edges
    const nodesArray = dataField.nodes as Object[] | null;
    const edgesArray = dataField.edges as Object[] | null;
    const linksArray = dataField.links as Object[] | null;
    
    console.info(`[KnowledgeGraphService] 转换${type}图谱数据:`, 
      'hasNodes=' + (!!nodesArray) + 
      ', nodesCount=' + (nodesArray?.length || 0) + 
      ', hasEdges=' + (!!edgesArray) + 
      ', edgesCount=' + (edgesArray?.length || 0) + 
      ', hasLinks=' + (!!linksArray) + 
      ', linksCount=' + (linksArray?.length || 0));
    
    // 提取节点
    const nodes: KnowledgeNode[] = (nodesArray || []).map((nodeObj: Object): KnowledgeNode => {
      const node = nodeObj as Record<string, Object>;
      const position = node.position as Record<string, number> | null;
      const metadata = node.metadata as Record<string, string> | null;
      
      return KnowledgeNode.create(
        node.id as string || '',
        (node.name as string) || (node.label as string) || '',
        (node.type as string) || 'default',
        (node.category as string) || (node.type as string) || '',
        position?.x || 0,
        position?.y || 0,
        position?.z || 0,
        10,  // size
        this.getNodeColorFromRecord(node, type)
      );
    });
    
    // 提取连线 - 注意：后端返回的是edges，不是links
    const edgesData = (edgesArray && edgesArray.length > 0) ? edgesArray : (linksArray || []);
    
    // 构建edgesData详情日志
    console.info(`[KnowledgeGraphService] edgesData详情: ` +
      `edgesArrayExists=${!!edgesArray}, ` +
      `edgesArrayLength=${edgesArray?.length || 0}, ` +
      `linksArrayExists=${!!linksArray}, ` +
      `linksArrayLength=${linksArray?.length || 0}, ` +
      `usingEdges=${edgesArray && edgesArray.length > 0}, ` +
      `finalEdgesDataLength=${edgesData.length}`);
    
    // 打印前3条边的详细信息
    if (edgesData.length > 0) {
      console.info('[KnowledgeGraphService] 前3条边示例:', 
        JSON.stringify(edgesData.slice(0, 3)));
    }
    
    const edges: KnowledgeEdge[] = edgesData.map((edgeObj: Object): KnowledgeEdge => {
      const edge = edgeObj as Record<string, Object>;
      const createdEdge = KnowledgeEdge.create(
        edge.source as string || '',
        edge.target as string || '',
        (edge.type as string) || 'RELATED',
        (edge.weight as number) || (edge.strength as number) || 1.0
      );
      return createdEdge;
    });
    
    // 构建日志信息
    let logMessage = `[KnowledgeGraphService] 转换完成: nodes=${nodes.length}, edges=${edges.length}`;
    if (edges.length > 0) {
      logMessage += `, firstEdge={from=${edges[0].from}, to=${edges[0].to}, type=${edges[0].type}, weight=${edges[0].weight}}`;
    } else {
      logMessage += `, firstEdge=none`;
    }
    console.info(logMessage);
    
    // 提取层级信息
    const layers: string[] = this.extractLayers(nodes, type);
    
    return {
      nodes: nodes,
      edges: edges,
      layers: layers
    };
  }
  
  /**
   * 从Record对象获取节点颜色
   */
  private getNodeColorFromRecord(node: Record<string, Object>, type: string): string {
    const nodeType = node.type as string || '';
    const isSelf = node.is_self as boolean || false;
    const metadata = node.metadata as Record<string, string> | null;
    
    if (type === 'career') {
      if (nodeType === 'center') return '#FFD700';
      if (nodeType === 'skill') {
        const status = metadata?.status || '';
        if (status === 'mastered') return '#4CAF50';
        if (status === 'partial') return '#FFC107';
        if (status === 'missing') return '#F44336';
        return '#4CAF50';
      }
      if (nodeType === 'job') return '#2196F3';
      if (nodeType === 'company') return '#9C27B0';
      return '#A0C4FF';
    } else if (type === 'education') {
      if (nodeType === 'center') return '#FFD700';
      if (nodeType === 'school') return '#4ECDC4';
      if (nodeType === 'major') return '#95E1D3';
      if (nodeType === 'action') return '#FA709A';
      return '#A0C4FF';
    } else {
      // relationship
      if (nodeType === 'person' && isSelf) return '#FFD700';
      if (nodeType === 'person') return '#4D9EFF';
      if (nodeType === 'relationship') return '#9575FF';
      return '#A0C4FF';
    }
  }
  
  /**
   * 提取层级信息
   */
  private extractLayers(nodes: KnowledgeNode[], type: string): string[] {
    if (type === 'career') {
      return ['我', '技能', '岗位', '公司'];
    } else if (type === 'education') {
      return ['我', '学业', '目标院校', '行动计划'];
    } else {
      return ['我', '家人', '朋友', '同事'];
    }
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
