/**
 * API常量定义
 * 包含所有后端API端点
 */
export class ApiConstants {
  // 后端地址
  // 模拟器使用: http://10.0.2.2:6006
  // 本机测试使用: http://localhost:6006 或 http://127.0.0.1:6006
  // 真机测试使用: http://192.168.242.1:6006
  static readonly BASE_URL = 'http://192.168.242.1:6006';
  
  // API端点
  static readonly AUTH = {
    REGISTER: '/api/auth/register',
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout'
  };
  
  static readonly AI_CORE = {
    INTENT: '/api/v5/ai-core/intent',
    NAVIGATE: '/api/v5/ai-core/navigate'
  };
  
  static readonly KNOWLEDGE = {
    ADD_INFO: '/api/knowledge/add-info',
    QUERY: '/api/knowledge/query',
    RELATIONSHIPS: '/api/knowledge/relationships',
    STATS: '/api/knowledge/stats'
  };
  
  static readonly VERTICAL = {
    CAREER_STAR_MAP: '/api/v5/future-os/career-graph',
    EDUCATION_STAR_MAP: '/api/v5/future-os/education-graph',
    RELATIONSHIP_STAR_MAP: '/api/v5/future-os/people-graph'
  };
  
  static readonly DECISION = {
    START_COLLECTION: '/api/decision/persona/collect/start',
    CONTINUE_COLLECTION: '/api/decision/persona/collect/continue',
    GENERATE_OPTIONS: '/api/decision/persona/generate-options',
    SESSION: '/api/decision/persona/collect/session',
    UPDATE_OUTCOME: '/api/decision/persona/update-outcome'
  };
  
  static readonly INSIGHTS = {
    RELATIONSHIP: '/api/insights/realtime/relationship/insight',
    EDUCATION: '/api/insights/realtime/education/insight',
    CAREER: '/api/insights/realtime/career/insight',
    AGENTS_STATUS: '/api/insights/realtime/agents/status'
  };
  
  static readonly PARALLEL_LIFE = {
    START_GAME: '/api/v5/parallel-life/start-game',
    SUBMIT_CHOICE: '/api/v5/parallel-life/submit-choice',
    DECISION_PROFILE: '/api/v5/parallel-life/decision-profile'
  };
  
  static readonly SOCIAL = {
    FRIENDS_LIST: '/api/friends/list',
    FRIENDS_ADD: '/api/friends/add',
    FRIENDS_REMOVE: '/api/friends/remove',
    FRIENDS_REQUESTS: '/api/friends/requests',
    TREE_HOLE_POSTS: '/api/tree-hole/posts',
    TREE_HOLE_POST: '/api/tree-hole/post',
    TREE_HOLE_COMMENT: '/api/tree-hole/comment',
    TREE_HOLE_LIKE: '/api/tree-hole/like'
  };
  
  static readonly SCHEDULE = {
    LIST: '/api/v5/schedule/list',
    ADD: '/api/v5/schedule/add',
    UPDATE: '/api/v5/schedule/update',
    DELETE: '/api/v5/schedule/delete',
    RECOMMEND: '/api/v5/schedule/recommend',
    AUTO_GENERATE: '/api/v5/schedule/auto-generate'
  };
  
  // WebSocket端点
  static readonly WS = {
    CHAT: 'ws://192.168.242.1:6006/ws/chat',
    DECISION_SIMULATE: 'ws://192.168.242.1:6006/api/decision/persona/ws/simulate-option'
  };
}
