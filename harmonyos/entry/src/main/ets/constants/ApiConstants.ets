/**
 * API常量定义
 * 包含所有后端API端点
 */
export class ApiConstants {
  // 后端地址 - 生产服务器
  static readonly BASE_URL = 'http://82.157.195.238:6006';
  
  // WebSocket基础地址
  static readonly WS_BASE_URL = 'ws://82.157.195.238:6006';
  
  // API端点
  static readonly AUTH = {
    REGISTER: '/api/auth/register',
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    VERIFY_TOKEN: '/api/auth/verify-token',
    USER_INFO: '/api/auth/user'  // GET /api/auth/user/{user_id}
  };
  
  static readonly AI_CORE = {
    INTENT: '/api/v5/ai-core/intent',
    NAVIGATE: '/api/v5/ai-core/navigate',
    CHAT: '/api/chat/send'  // AI对话
  };
  
  static readonly KNOWLEDGE = {
    ADD_INFO: '/api/knowledge/add-info',
    QUERY: '/api/knowledge/query',
    RELATIONSHIPS: '/api/knowledge/relationships',
    STATS: '/api/knowledge/stats',
    // 知识图谱节点
    CAREER_NODES: '/api/kg/career/nodes',
    EDUCATION_NODES: '/api/kg/education/nodes',
    RELATIONSHIP_NODES: '/api/kg/relationship/nodes'
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
    UPDATE_OUTCOME: '/api/decision/persona/update-outcome',
    START_SESSION: '/api/decision/persona/start-session',  // 开始推演
    WORKBENCH: '/api/decision/workbench'  // 决策工作台
  };
  
  static readonly INSIGHTS = {
    RELATIONSHIP: '/api/insights/realtime/relationship/insight',
    EDUCATION: '/api/insights/realtime/education/insight',
    CAREER: '/api/insights/realtime/career/insight',
    AGENTS_STATUS: '/api/insights/realtime/agents/status',
    GENERATE: '/api/insights/generate',  // 生成洞察
    HISTORY: '/api/insights/history'  // 历史洞察
  };
  
  static readonly PARALLEL_LIFE = {
    START_GAME: '/api/v5/parallel-life/start-game',
    SUBMIT_CHOICE: '/api/v5/parallel-life/submit-choice',
    DECISION_PROFILE: '/api/v5/parallel-life/decision-profile',
    DRAW_CARDS: '/api/parallel-life/draw-cards',  // 抽牌
    INTERPRET: '/api/parallel-life/interpret'  // 解读
  };
  
  static readonly SOCIAL = {
    // 好友相关
    FRIENDS_LIST: '/api/social/friends',
    FRIEND_REQUEST_SEND: '/api/social/friend-request',
    FRIEND_REQUESTS: '/api/social/friend-requests',
    FRIEND_REQUEST_ACCEPT: '/api/social/friend-request/accept',
    FRIEND_REQUEST_REJECT: '/api/social/friend-request/reject',
    SEARCH_USERS: '/api/social/search',
    // 树洞相关
    TREE_HOLE_POSTS: '/api/social/tree-hole/posts',
    TREE_HOLE_POST: '/api/social/tree-hole/post',
    TREE_HOLE_COMMENT: '/api/social/tree-hole/comment',
    TREE_HOLE_LIKE: '/api/social/tree-hole/like'
  };
  
  static readonly SCHEDULE = {
    LIST: '/api/schedule/list',
    CREATE: '/api/schedule/create',
    UPDATE: '/api/schedule/update',
    DELETE: '/api/schedule/delete',
    RECOMMEND: '/api/schedule/recommend',
    AUTO_GENERATE: '/api/schedule/auto-generate'
  };
  
  // WebSocket端点
  static readonly WS = {
    CHAT: `${ApiConstants.WS_BASE_URL}/ws/chat`,
    DECISION_SIMULATE: `${ApiConstants.WS_BASE_URL}/ws/decision`  // WebSocket决策推演
  };
}
