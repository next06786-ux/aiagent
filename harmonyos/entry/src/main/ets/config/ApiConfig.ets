/**
 * API 
 *  API 
 */

export class ApiConfig {
  //  API 
  // 
  // 本地调试默认走 6006，云端部署时可再统一替换
  // - 模拟器: 'http://10.0.2.2:6006'
  // - 真机联调: 改成局域网 IP，例如 'http://192.168.x.x:6006'
  private static BASE_URL: string = 'http://localhost:6006';
  
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
    endpoints['HYBRID_INSIGHTS'] = '/api/v2/hybrid/status';
    endpoints['HYBRID_PROCESS'] = '/api/v2/hybrid/process-task';
    endpoints['HYBRID_FEEDBACK'] = '/api/v2/hybrid/feedback';
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
    endpoints['DECISION_ENHANCED_COLLECT_START'] = '/api/decision/enhanced/collect/start';
    endpoints['DECISION_ENHANCED_COLLECT_CONTINUE'] = '/api/decision/enhanced/collect/continue';
    endpoints['DECISION_ENHANCED_SESSION'] = '/api/decision/enhanced/collect/session';
    endpoints['DECISION_ENHANCED_SIMULATE'] = '/api/decision/enhanced/simulate/with-collection';
    endpoints['DECISION_ENHANCED_FULL_PROCESS'] = '/api/decision/enhanced/full-process';
    endpoints['FUTURE_OS_KNOWLEDGE'] = '/api/v5/future-os/knowledge';
    endpoints['FUTURE_OS_CONTEXT'] = '/api/v5/future-os/context';
    endpoints['FUTURE_OS_ROUTE'] = '/api/v5/future-os/route';
    endpoints['FUTURE_OS_SIMULATE'] = '/api/v5/future-os/simulate';
    endpoints['FUTURE_OS_HISTORY'] = '/api/v5/future-os/history';
    endpoints['FUTURE_OS_PARALLEL_BRANCH'] = '/api/v5/future-os/parallel-life/branch';
    endpoints['FUTURE_OS_PARALLEL_COMPLETE'] = '/api/v5/future-os/parallel-life/complete';
    return endpoints;
  }
}
