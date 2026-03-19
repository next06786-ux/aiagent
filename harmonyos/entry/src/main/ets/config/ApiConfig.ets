/**
 * API 
 *  API 
 */

export class ApiConfig {
  //  API 
  // 
  // - : 'http://localhost:8000'  'http://10.0.2.2:8000'
  // - : IP 'http://192.168.1.192:8000'
  private static BASE_URL: string = 'http://192.168.1.192:8000';
  
  /**
   *  API 
   */
  static getBaseUrl(): string {
    return ApiConfig.BASE_URL;
  }
  
  /**
   *  API 
   */
  static getApiUrl(path: string): string {
    if (!path.startsWith('/')) {
      path = '/' + path;
    }
    return `${ApiConfig.BASE_URL}${path}`;
  }
  
  // API  - 
  static getEndpoints(): Record<string, string> {
    const endpoints: Record<string, string> = {};
    endpoints['HEALTH'] = '/health';
    endpoints['CHAT'] = '/api/chat';
    endpoints['CHAT_HISTORY'] = '/api/chat/history';
    endpoints['CHAT_FEEDBACK'] = '/api/chat/feedback';
    endpoints['CHAT_ANALYZE_HEALTH'] = '/api/chat/analyze_health';
    endpoints['META_AGENT_ANALYZE'] = '/api/v4/meta-agent/analyze';
    endpoints['META_AGENT_FEEDBACK'] = '/api/v4/meta-agent/feedback';
    endpoints['KNOWLEDGE_GRAPH_QUERY'] = '/api/v4/knowledge-graph';
    endpoints['KNOWLEDGE_GRAPH_STATS'] = '/api/v4/knowledge-graph';
    endpoints['LEARNING_PROGRESS'] = '/api/v4/learning/progress';
    endpoints['HYBRID_INSIGHTS'] = '/api/hybrid/insights';
    endpoints['HYBRID_PROCESS'] = '/api/hybrid/process';
    endpoints['HYBRID_FEEDBACK'] = '/api/hybrid/feedback';
    endpoints['HYBRID_STRATEGY'] = '/api/hybrid/strategy';
    endpoints['PREDICTIONS'] = '/api/predictions';
    endpoints['DATA_INPUT'] = '/api/data/input';
    endpoints['MULTIMODAL_DATA'] = '/api/v4/multimodal/data';
    endpoints['MULTIMODAL_STATUS'] = '/api/v4/multimodal/status';
    endpoints['IMAGE_UPLOAD'] = '/api/image/upload';
    endpoints['IMAGE_ANALYZE'] = '/api/image/analyze';
    endpoints['IMAGE_RECENT'] = '/api/image/recent';
    endpoints['SYSTEM_STATUS'] = '/api/v4/system/status';
    endpoints['LLM_STATUS'] = '/api/llm/status';
    endpoints['USER_CONFIG'] = '/api/config';
    endpoints['DOMAINS'] = '/api/domains';
    endpoints['DECISION_SIMULATE'] = '/api/decision/simulate';
    endpoints['DECISION_COMPARE'] = '/api/decision/compare';
    endpoints['DECISION_CREATE_DUNGEON'] = '/api/decision/create-dungeon';
    endpoints['DECISION_GET_DUNGEON'] = '/api/decision/dungeon';
    endpoints['DECISION_LIST_DUNGEONS'] = '/api/decision/dungeons';
    return endpoints;
  }
}
