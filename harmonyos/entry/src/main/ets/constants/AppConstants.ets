/**
 * 应用常量定义
 */
export class AppConstants {
  // 应用配置
  static readonly APP_NAME = 'LifeSwarm';
  static readonly APP_VERSION = '1.0.0';
  
  // 缓存键
  static readonly CACHE_KEYS = {
    USER_INFO: 'user_info',
    AUTH_TOKEN: 'auth_token',
    STAR_MAPS: 'star_maps',
    RECENT_CONVERSATIONS: 'recent_conversations',
    DECISION_SESSIONS: 'decision_sessions'
  };
  
  // 颜色主题
  static readonly COLORS = {
    PRIMARY: '#0A59F7',
    SUCCESS: '#34C759',
    WARNING: '#FF9500',
    DANGER: '#FF3B30',
    INFO: '#00C7BE',
    PURPLE: '#6B48FF',
    GRAY: '#8E8E93',
    
    // 功能模块颜色
    DECISION: '#667eea',
    KNOWLEDGE: '#764ba2',
    INSIGHTS: '#f093fb',
    PARALLEL: '#4facfe',
    SOCIAL: '#43e97b',
    SCHEDULE: '#fa709a'
  };
  
  // 动画时长
  static readonly ANIMATION = {
    FAST: 200,
    NORMAL: 300,
    SLOW: 500
  };
  
  // 7个决策人格
  static readonly PERSONAS = [
    { id: 'rational_analyst', name: '理性分析师', color: '#0A59F7' },
    { id: 'emotional_resonator', name: '情感共鸣者', color: '#FF3B30' },
    { id: 'risk_assessor', name: '风险评估师', color: '#FF9500' },
    { id: 'opportunity_explorer', name: '机会探索者', color: '#34C759' },
    { id: 'moral_guardian', name: '道德守护者', color: '#6B48FF' },
    { id: 'pragmatist', name: '实用主义者', color: '#8E8E93' },
    { id: 'innovator', name: '创新思考者', color: '#00C7BE' }
  ];
  
  // 决策类型
  static readonly DECISION_TYPES = {
    CAREER: 'career',
    EDUCATION: 'education',
    RELATIONSHIP: 'relationship',
    GENERAL: 'general'
  };
  
  // 星图层级
  static readonly STAR_MAP_LAYERS = {
    CAREER: ['技能层', '岗位层', '公司层'],
    EDUCATION: ['学业层', '学校层', '行动层'],
    RELATIONSHIP: ['家人层', '朋友层', '同事层', '其他层']
  };
}
