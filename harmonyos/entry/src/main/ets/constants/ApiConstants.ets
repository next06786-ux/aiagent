/**
 * API常量定义
 * 包含所有后端API端点
 */

// API端点接口定义
interface AuthEndpoints {
  REGISTER: string;
  LOGIN: string;
  LOGOUT: string;
}

interface AICoreEndpoints {
  INTENT: string;
  NAVIGATE: string;
}

interface KnowledgeEndpoints {
  ADD_INFO: string;
  QUERY: string;
  RELATIONSHIPS: string;
  STATS: string;
}

interface VerticalEndpoints {
  CAREER_STAR_MAP: string;
  EDUCATION_STAR_MAP: string;
  RELATIONSHIP_STAR_MAP: string;
}

interface DecisionEndpoints {
  START_COLLECTION: string;
  CONTINUE_COLLECTION: string;
  GENERATE_OPTIONS: string;
  SESSION: string;
  UPDATE_OUTCOME: string;
}

interface InsightsEndpoints {
  RELATIONSHIP: string;
  EDUCATION: string;
  CAREER: string;
  AGENTS_STATUS: string;
}

interface ParallelLifeEndpoints {
  START_GAME: string;
  SUBMIT_CHOICE: string;
  DECISION_PROFILE: string;
}

interface SocialEndpoints {
  FRIENDS_LIST: string;
  FRIENDS_ADD: string;
  FRIENDS_REMOVE: string;
  FRIENDS_REQUESTS: string;
  TREE_HOLE_POSTS: string;
  TREE_HOLE_POST: string;
  TREE_HOLE_COMMENT: string;
  TREE_HOLE_LIKE: string;
}

interface ScheduleEndpoints {
  LIST: string;
  ADD: string;
  UPDATE: string;
  DELETE: string;
  RECOMMEND: string;
  AUTO_GENERATE: string;
}

interface WSEndpoints {
  CHAT: string;
  DECISION_SIMULATE: string;
}

export class ApiConstants {
  // 后端地址
  // 生产服务器
  static readonly BASE_URL: string = 'http://82.157.195.238';
  
  // API端点
  static readonly AUTH: AuthEndpoints = {
    REGISTER: '/api/auth/register',
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout'
  };
  
  static readonly AI_CORE: AICoreEndpoints = {
    INTENT: '/api/v5/ai-core/intent',
    NAVIGATE: '/api/v5/ai-core/navigate'
  };
  
  static readonly KNOWLEDGE: KnowledgeEndpoints = {
    ADD_INFO: '/api/knowledge/add-info',
    QUERY: '/api/knowledge/query',
    RELATIONSHIPS: '/api/knowledge/relationships',
    STATS: '/api/knowledge/stats'
  };
  
  static readonly VERTICAL: VerticalEndpoints = {
    CAREER_STAR_MAP: '/api/v5/future-os/career-graph',
    EDUCATION_STAR_MAP: '/api/v5/future-os/education-graph',
    RELATIONSHIP_STAR_MAP: '/api/v5/future-os/people-graph'
  };
  
  static readonly DECISION: DecisionEndpoints = {
    START_COLLECTION: '/api/decision/persona/collect/start',
    CONTINUE_COLLECTION: '/api/decision/persona/collect/continue',
    GENERATE_OPTIONS: '/api/decision/persona/generate-options',
    SESSION: '/api/decision/persona/collect/session',
    UPDATE_OUTCOME: '/api/decision/persona/update-outcome'
  };
  
  static readonly INSIGHTS: InsightsEndpoints = {
    RELATIONSHIP: '/api/insights/realtime/relationship/insight',
    EDUCATION: '/api/insights/realtime/education/insight',
    CAREER: '/api/insights/realtime/career/insight',
    AGENTS_STATUS: '/api/insights/realtime/agents/status'
  };
  
  static readonly PARALLEL_LIFE: ParallelLifeEndpoints = {
    START_GAME: '/api/v5/parallel-life/start-game',
    SUBMIT_CHOICE: '/api/v5/parallel-life/submit-choice',
    DECISION_PROFILE: '/api/v5/parallel-life/decision-profile'
  };
  
  static readonly SOCIAL: SocialEndpoints = {
    FRIENDS_LIST: '/api/friends/list',
    FRIENDS_ADD: '/api/friends/add',
    FRIENDS_REMOVE: '/api/friends/remove',
    FRIENDS_REQUESTS: '/api/friends/requests',
    TREE_HOLE_POSTS: '/api/tree-hole/posts',
    TREE_HOLE_POST: '/api/tree-hole/post',
    TREE_HOLE_COMMENT: '/api/tree-hole/comment',
    TREE_HOLE_LIKE: '/api/tree-hole/like'
  };
  
  static readonly SCHEDULE: ScheduleEndpoints = {
    LIST: '/api/v5/schedule/list',
    ADD: '/api/v5/schedule/add',
    UPDATE: '/api/v5/schedule/update',
    DELETE: '/api/v5/schedule/delete',
    RECOMMEND: '/api/v5/schedule/recommend',
    AUTO_GENERATE: '/api/v5/schedule/auto-generate'
  };
  
  // WebSocket端点
  static readonly WS: WSEndpoints = {
    CHAT: 'ws://82.157.195.238/ws/chat',
    DECISION_SIMULATE: 'ws://82.157.195.238/api/decision/persona/ws/simulate-option'
  };
}
