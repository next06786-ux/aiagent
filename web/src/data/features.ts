export interface FeatureModule {
  slug: string;
  title: string;
  summary: string;
  route?: string;
  status: 'live' | 'preview' | 'planned';
  group: '核心闭环' | '图谱与洞察' | '代理与成长';
  gradient: [string, string];
}

export const featureModules: FeatureModule[] = [
  {
    slug: 'decision-dungeon',
    title: '决策副本',
    summary: '信息采集、AI 选项生成、WebSocket 推演、可验证报告与回访校准。',
    route: '/decision',
    status: 'live',
    group: '核心闭环',
    gradient: ['#0A59F7', '#6B48FF'],
  },
  {
    slug: 'decision-history',
    title: '预测历史',
    summary: '查看历史推演记录，回放 recommendation、prediction trace 与 follow-up。',
    route: '/decision/history',
    status: 'live',
    group: '核心闭环',
    gradient: ['#6B48FF', '#8E2DE2'],
  },
  {
    slug: 'ai-chat',
    title: 'AI 对话',
    summary: '复刻 Harmony 端实时聊天和会话历史，继续复用同一套 /ws/chat 能力。',
    route: '/chat',
    status: 'live',
    group: '核心闭环',
    gradient: ['#4FACFE', '#00F2FE'],
  },
  {
    slug: 'profile',
    title: '个人中心',
    summary: '账号信息、资料维护与密码修改。',
    route: '/profile',
    status: 'live',
    group: '核心闭环',
    gradient: ['#56AB2F', '#A8E063'],
  },
  {
    slug: 'knowledge-graph',
    title: '知识图谱画布',
    summary: '对应 Harmony 中 KnowledgeGraphCanvas 与 KnowledgeStarMap 系列能力。',
    route: '/knowledge-graph',
    status: 'live',
    group: '图谱与洞察',
    gradient: ['#667EEA', '#764BA2'],
  },
  {
    slug: 'dashboard',
    title: '洞察仪表盘',
    summary: 'Dashboard、SmartInsights、EmergenceDashboard、LifeDomainInsights 的 Web 化入口。',
    route: '/dashboard',
    status: 'live',
    group: '图谱与洞察',
    gradient: ['#FF6B9D', '#FEC163'],
  },
  {
    slug: 'agent-home',
    title: 'Agent Home',
    summary: 'AgentHome、MetaAgentCoordination、ParallelLifeGame 等代理实验工作台。',
    route: '/parallel-life',
    status: 'live',
    group: '代理与成长',
    gradient: ['#7F7FD5', '#86A8E7'],
  },
  {
    slug: 'learning-progress',
    title: '学习与成长',
    summary: 'LearningProgress、个性模型训练、EmergencePatterns 等成长反馈模块。',
    route: '/learning-progress',
    status: 'live',
    group: '代理与成长',
    gradient: ['#43E97B', '#38F9D7'],
  },
  {
    slug: 'lora-training',
    title: '个性模型训练',
    summary: '管理储备中的个性化模型训练、查看进度与版本，不影响当前云端推演主链。',
    route: '/lora-training',
    status: 'live',
    group: '代理与成长',
    gradient: ['#F093FB', '#F5576C'],
  },
  {
    slug: 'camera-multimodal',
    title: '多模态输入',
    summary: 'Camera、图像上传、语音与感知数据入口的 Web 映射。',
    status: 'planned',
    group: '代理与成长',
    gradient: ['#FA709A', '#FEE140'],
  },
  {
    slug: 'emergence-patterns',
    title: '涌现模式检测',
    summary: '级联效应、反馈环、临界点、协同效应的跨域关联模式可视化。',
    route: '/emergence-patterns',
    status: 'live',
    group: '图谱与洞察',
    gradient: ['#4FACFE', '#00F2FE'],
  },
  {
    slug: 'life-domain-insights',
    title: '生活领域洞察',
    summary: '多维感知数据综合分析，生成健康、时间、情绪、财务等跨域洞察报告。',
    route: '/life-domain-insights',
    status: 'live',
    group: '图谱与洞察',
    gradient: ['#43E97B', '#38F9D7'],
  },
  {
    slug: 'meta-agent',
    title: '多智能体协调',
    summary: '6个专项智能体并行分析，Meta 智能体汇总协调，输出综合健康评分。',
    route: '/meta-agent',
    status: 'live',
    group: '代理与成长',
    gradient: ['#F093FB', '#F5576C'],
  },
];
