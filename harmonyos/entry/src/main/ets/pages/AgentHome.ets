/**
 * 智能体主界面 - LifeSwarm Agent
 * HarmonyOS 6 流体设计 · 功能球体环绕AI核心
 */
import { Theme } from '../common/Theme';
import { getAIConversationService, ChatMessage } from '../service/AIConversationService';
import { SimpleIcon } from '../components/IconRenderer';
import http from '@ohos.net.http';
import { ApiConfig } from '../config/ApiConfig';
import { getAuthService, UserInfo } from '../service/AuthService';

interface FeatureCard {
  id: string;
  title: string;
  subtitle: string;
  route: string;
  color: string;
  iconName: string;
}

interface OrbPos {
  x: number;
  y: number;
  title: string;
  icon: string;
  color: string;
  route: string;
}

interface ConversationItem {
  id: string;
  title: string;
  preview: string;
  message_count: number;
  last_message_time: string;
}

@Entry
@Component
struct AgentHome {
  @State messages: ChatMessage[] = [];
  @State inputText: string = '';
  @State isLoading: boolean = false;
  @State showContent: boolean = false;
  @State processingProgress: string = '';
  @State dotAnimation1: number = 1;
  @State dotAnimation2: number = 1;
  @State dotAnimation3: number = 1;
  private animationTimer: number = -1;

  @State showHistoryPanel: boolean = false;
  @State showAiCorePanel: boolean = false;
  @State conversations: ConversationItem[] = [];
  @State currentSessionId: string = '';
  @State isLoadingHistory: boolean = false;
  @State userInfo: UserInfo | null = null;

  // 布局
  @State screenWidth: number = 360;
  @State screenHeight: number = 780;
  @State centerX: number = 180;
  @State centerY: number = 360;

  // 功能球体漂浮位置
  @State orbPositions: OrbPos[] = [];
  private orbAnimTimer: number = -1;

  // AI核心球体动画
  @State aiCoreBreath: number = 1.0;
  @State aiCoreRing1: number = 0;
  @State aiCoreRing2: number = 0;
  @State aiCoreInnerRotate: number = 0;
  private aiCoreAnimTimer: number = -1;

  private aiService = getAIConversationService();
  private authService = getAuthService();

  private features: FeatureCard[] = [
    { id: 'starmap', title: '知识星图', subtitle: '3D知识图谱', route: 'pages/KnowledgeStarMapGL', color: '#0A59F7', iconName: 'network' },
    { id: 'decision', title: '决策副本', subtitle: '探索未来', route: 'pages/QuickDecisionInput', color: '#6B48FF', iconName: 'comparison' },
    { id: 'dashboard', title: '智能洞察', subtitle: '涌现发现', route: 'pages/SmartInsights', color: '#FF9500', iconName: 'analytics' },
    { id: 'profile', title: '我的账号', subtitle: '个人中心', route: 'pages/UserProfile', color: '#00C853', iconName: 'user' },
  ];

  aboutToAppear() {
    this.messages = this.aiService.getConversationHistory();
    if (this.messages.length === 0) this.addWelcomeMessage();
    this.loadUserInfo();
    this.loadConversations().catch(() => {});
    this.initOrbPositions();
    this.startOrbAnimation();
    this.startAiCoreAnimation();
    setTimeout(() => { this.showContent = true; }, 50);
  }

  aboutToDisappear() {
    this.stopLoadingAnimation();
    this.stopOrbAnimation();
    this.stopAiCoreAnimation();
  }

  onPageShow() {
    this.showContent = true;
    this.initOrbPositions();
    this.startOrbAnimation();
    this.startAiCoreAnimation();
  }

  onPageHide() {
    this.stopOrbAnimation();
    this.stopAiCoreAnimation();
  }

  // ===== 球体位置与动画 =====
  private initOrbPositions() {
    const count = this.features.length;
    const radius = 145;
    const cy = this.centerY + 10;
    const positions: OrbPos[] = [];
    for (let i = 0; i < count; i++) {
      const f = this.features[i];
      const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
      positions.push({
        x: this.centerX + Math.cos(angle) * radius,
        y: cy + Math.sin(angle) * radius,
        title: f.title, icon: f.iconName, color: f.color, route: f.route
      });
    }
    this.orbPositions = positions;
  }

  private startOrbAnimation() {
    if (this.orbAnimTimer !== -1) return;
    this.orbAnimTimer = setInterval(() => {
      const time = Date.now() / 1000;
      const count = this.features.length;
      const radius = 145;
      const cy = this.centerY + 10;
      const newPos: OrbPos[] = [];
      for (let i = 0; i < count; i++) {
        const f = this.features[i];
        const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
        const baseX = this.centerX + Math.cos(angle) * radius;
        const baseY = cy + Math.sin(angle) * radius;
        newPos.push({
          x: baseX + Math.cos(time * 0.7 + i * 1.6) * 3,
          y: baseY + Math.sin(time * 0.9 + i * 1.2) * 4,
          title: f.title, icon: f.iconName, color: f.color, route: f.route
        });
      }
      this.orbPositions = newPos;
    }, 50);
  }

  private stopOrbAnimation() {
    if (this.orbAnimTimer !== -1) { clearInterval(this.orbAnimTimer); this.orbAnimTimer = -1; }
  }

  private startAiCoreAnimation() {
    if (this.aiCoreAnimTimer !== -1) return;
    let t = 0;
    this.aiCoreAnimTimer = setInterval(() => {
      t += 0.05;
      animateTo({ duration: 50, curve: Curve.Linear }, () => {
        this.aiCoreBreath = 1.0 + Math.sin(t * 1.2) * 0.05;
        this.aiCoreRing1 = (t * 18) % 360;
        this.aiCoreRing2 = (t * -12 + 120) % 360;
        this.aiCoreInnerRotate = (t * 25) % 360;
      });
    }, 50);
  }

  private stopAiCoreAnimation() {
    if (this.aiCoreAnimTimer !== -1) { clearInterval(this.aiCoreAnimTimer); this.aiCoreAnimTimer = -1; }
  }

  // ===== 业务方法 =====
  private async loadUserInfo() {
    try { this.userInfo = await this.authService.getCurrentUserAsync(); }
    catch (err) { console.error('加载用户信息失败:', err); }
  }

  private async loadConversations() {
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/chat/sessions/${userId}`, { method: http.RequestMethod.GET });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, Object>;
        const sessions = (data.sessions as Array<Record<string, Object>>) || [];
        this.conversations = sessions.map((item: Record<string, Object>): ConversationItem => ({
          id: item.session_id as string, title: item.title as string || '新对话',
          preview: item.preview as string || '', message_count: item.message_count as number || 0,
          last_message_time: item.last_time as string || ''
        }));
      }
    } catch (err) { console.error('加载历史对话失败:', err); }
  }

  private addWelcomeMessage() {
    this.messages.push(new ChatMessage(Date.now().toString(), 'assistant',
      '欢迎来到 LifeSwarm\n\n我是你的AI助手，可以帮你分析问题、辅助决策。\n\n点击中心AI核心开始对话，或选择周围的功能球体探索更多。',
      Date.now()));
  }

  private startLoadingAnimation() {
    let step = 0;
    this.animationTimer = setInterval(() => {
      step = (step + 1) % 3;
      animateTo({ duration: 300, curve: Curve.EaseInOut }, () => {
        this.dotAnimation1 = step === 0 ? 1.5 : 1;
        this.dotAnimation2 = step === 1 ? 1.5 : 1;
        this.dotAnimation3 = step === 2 ? 1.5 : 1;
      });
    }, 300);
  }

  private stopLoadingAnimation() {
    if (this.animationTimer !== -1) { clearInterval(this.animationTimer); this.animationTimer = -1; }
    this.dotAnimation1 = 1; this.dotAnimation2 = 1; this.dotAnimation3 = 1;
  }

  async sendMessage() {
    if (!this.inputText.trim() || this.isLoading) return;
    const userMessage = this.inputText;
    this.inputText = '';
    this.isLoading = true;
    this.startLoadingAnimation();
    this.showAiCorePanel = true;
    this.messages.push(new ChatMessage(Date.now().toString(), 'user', userMessage, Date.now()));
    const aiMsgId = (Date.now() + 1).toString();
    this.messages.push(new ChatMessage(aiMsgId, 'assistant', '', Date.now(), ''));
    try {
      await this.aiService.chatStreamWebSocket(userMessage,
        (progress: string) => { this.processingProgress = progress; },
        (thinking: string) => { this.processingProgress = ''; this.updateMessage(aiMsgId, 'thinking', thinking); },
        (answer: string) => { this.updateMessage(aiMsgId, 'content', answer); },
        () => { this.processingProgress = ''; this.stopLoadingAnimation(); this.isLoading = false; this.loadConversations(); },
        (error: string) => {
          this.processingProgress = ''; this.stopLoadingAnimation(); this.isLoading = false;
          const idx = this.messages.findIndex(m => m.id === aiMsgId);
          if (idx >= 0) this.messages.splice(idx, 1);
        },
        null, this.currentSessionId || null,
        (sessionId: string) => { this.currentSessionId = sessionId; }
      );
    } catch (err) {
      const idx = this.messages.findIndex(m => m.id === aiMsgId);
      if (idx >= 0) this.messages.splice(idx, 1);
      this.isLoading = false; this.stopLoadingAnimation();
    }
  }

  private async triggerModelUpdate() {
    if (!this.userInfo) return;
    try {
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/lora/train/${this.userInfo.user_id}`, { method: http.RequestMethod.POST });
      httpRequest.destroy();
      if (response.responseCode === 200) { this.processingProgress = '模型训练已触发'; }
    } catch (err) { console.error('触发模型训练失败:', err); }
  }

  private updateMessage(messageId: string, field: 'thinking' | 'content', value: string): void {
    const idx = this.messages.findIndex(m => m.id === messageId);
    if (idx >= 0) {
      const msg = this.messages[idx];
      const updated = new ChatMessage(msg.id, msg.role,
        field === 'content' ? value : msg.content, msg.timestamp,
        field === 'thinking' ? value : msg.thinking);
      const newMsgs: ChatMessage[] = [];
      for (let i = 0; i < this.messages.length; i++) newMsgs.push(i === idx ? updated : this.messages[i]);
      this.messages = newMsgs;
    }
  }

  async loadConversationMessages(sessionId: string) {
    this.isLoadingHistory = true;
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/chat/session/${userId}/${sessionId}`, { method: http.RequestMethod.GET });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, Object>;
        const history = (data.history as Array<Record<string, string>>) || [];
        this.messages = history.map((m: Record<string, string>) => new ChatMessage(
          m.id || Date.now().toString(), m.role as 'user' | 'assistant',
          m.content || '', m.timestamp ? new Date(m.timestamp).getTime() : Date.now(), m.thinking));
        this.currentSessionId = sessionId;
        this.showHistoryPanel = false; this.showAiCorePanel = true;
      }
    } catch (err) { console.error('加载对话消息失败:', err); }
    finally { this.isLoadingHistory = false; }
  }

  async createNewConversation() {
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/chat/session/new/${userId}`, { method: http.RequestMethod.POST });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, string>;
        if (data?.session_id) {
          this.currentSessionId = data.session_id;
          this.messages = []; this.addWelcomeMessage();
          this.showHistoryPanel = false; this.showAiCorePanel = true;
          this.loadConversations();
        }
      }
    } catch (err) { console.error('创建新对话失败:', err); }
  }

  private navigateTo(route: string): void {
    try { this.getUIContext().getRouter().pushUrl({ url: route }); }
    catch (e) { console.error('导航失败:', e); }
  }

  formatTime(ts: number): string {
    const d = new Date(ts);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  }

  // ===== UI 构建 =====
  build() {
    Stack() {
      // 浅色背景
      Column().width('100%').height('100%').backgroundColor(Theme.Color.BackgroundPrimary)

      // 装饰光晕 - 跟随AI核心呼吸
      Circle({ width: 320, height: 320 }).fill('#667eea').opacity(0.035).blur(80)
        .position({ x: this.centerX - 160, y: this.centerY - 140 })
        .scale({ x: this.aiCoreBreath, y: this.aiCoreBreath })
      Circle({ width: 200, height: 200 }).fill('#764ba2').opacity(0.025).blur(60)
        .position({ x: this.centerX + 30, y: this.centerY + 60 })

      // 功能球体层
      this.buildOrbsLayer()

      // 顶部栏
      this.buildTopBar()

      // 中心AI核心
      this.buildAICore()

      if (this.isLoading && !this.showAiCorePanel) { this.buildLoadingIndicator() }
      // 始终渲染对话面板，关闭时只隐藏不销毁，避免中断WebSocket
      this.buildAICorePanel()
      // 历史面板在对话面板之上
      if (this.showHistoryPanel) { this.buildHistoryPanel() }
    }
    .width('100%').height('100%')
    .onAreaChange((oldArea: Area, newArea: Area) => {
      this.screenWidth = newArea.width as number;
      this.screenHeight = newArea.height as number;
      this.centerX = this.screenWidth / 2;
      this.centerY = this.screenHeight / 2;
      this.initOrbPositions();
    })
  }

  @Builder
  buildTopBar() {
    Row() {
      Row({ space: 10 }) {
        Stack() {
          Circle({ width: 40, height: 40 }).fill(Theme.Color.Primary).opacity(0.12)
          Circle({ width: 32, height: 32 })
            .linearGradient({ angle: 135, colors: [['#667eea', 0], ['#764ba2', 1]] })
          Text('LS').fontSize(13).fontWeight(700).fontColor('#FFFFFF')
        }.width(40).height(40)

        Column({ space: 2 }) {
          Text('LifeSwarm').fontSize(17).fontWeight(700).fontColor(Theme.Color.TextPrimary)
          Text(this.userInfo ? `${this.userInfo.nickname}，你好` : '智能生活助手')
            .fontSize(11).fontColor(Theme.Color.TextTertiary)
        }.alignItems(HorizontalAlign.Start)
      }
      Blank()
      Stack() {
        Circle({ width: 40, height: 40 }).fill(Theme.Color.GlassMedium)
        SimpleIcon({ iconName: 'history', iconSize: 20, color: Theme.Color.TextSecondary })
      }.width(40).height(40)
      .onClick(() => { this.showHistoryPanel = true; })
    }
    .width('100%').height(60)
    .padding({ left: 16, right: 16 })
    .backgroundColor(Theme.Color.GlassHeavy)
    .backdropBlur(Theme.Blur.Medium)
    .border({ width: 0.5, color: Theme.Color.BorderLight })
    .position({ x: 0, y: 0 }).zIndex(10)
  }

  @Builder
  buildAICore() {
    Column({ space: 8 }) {
      Stack() {
        // 最外层脉冲光晕
        Circle({ width: 140, height: 140 })
          .fill(Theme.Color.Primary).opacity(0.04).blur(30)
          .scale({ x: this.aiCoreBreath * 1.15, y: this.aiCoreBreath * 1.15 })

        // 外层呼吸环
        Circle({ width: 118, height: 118 }).fill('transparent')
          .border({ width: 0.8, color: 'rgba(102, 126, 234, 0.12)' })
          .scale({ x: this.aiCoreBreath, y: this.aiCoreBreath })

        // 轨道环1 - 水平椭圆
        Circle({ width: 104, height: 104 }).fill('transparent')
          .border({ width: 1.2, color: 'rgba(10, 89, 247, 0.16)' })
          .rotate({ angle: this.aiCoreRing1 }).scale({ x: 1, y: 0.35 })

        // 轨道环2 - 垂直椭圆
        Circle({ width: 96, height: 96 }).fill('transparent')
          .border({ width: 1, color: 'rgba(107, 72, 255, 0.13)' })
          .rotate({ angle: this.aiCoreRing2 }).scale({ x: 0.35, y: 1 })

        // 轨道环3 - 倾斜
        Circle({ width: 88, height: 88 }).fill('transparent')
          .border({ width: 0.8, color: 'rgba(100, 180, 255, 0.1)' })
          .rotate({ angle: this.aiCoreRing1 * 0.6 + 60 })
          .scale({ x: 0.65, y: 0.45 })

        // 核心发光底 - 加大加深
        Circle({ width: 76, height: 76 })
          .fill(Theme.Color.Primary).opacity(0.1).blur(18)
          .scale({ x: this.aiCoreBreath, y: this.aiCoreBreath })

        // 核心球体 - 用多层线性渐变模拟径向光照，避免方形边界
        Circle({ width: 66, height: 66 })
          .linearGradient({ angle: 150 + this.aiCoreInnerRotate * 0.2,
            colors: [['#8B7CF6', 0], ['#6B5BD4', 0.35], ['#4A3BB0', 0.7], ['#2E1F8A', 1]] })
          .shadow({ radius: 24, color: 'rgba(91, 78, 212, 0.45)', offsetX: 0, offsetY: 8 })

        // 球体上半高光层 - 模拟顶部光照
        Circle({ width: 66, height: 66 })
          .linearGradient({ angle: 170,
            colors: [['rgba(255,255,255,0.25)', 0], ['rgba(255,255,255,0.05)', 0.3], ['rgba(0,0,0,0)', 0.5], ['rgba(0,0,0,0.1)', 1]] })

        // 边缘菲涅尔高光环
        Circle({ width: 64, height: 64 }).fill('transparent')
          .border({ width: 1.5, color: 'rgba(255, 255, 255, 0.12)' })

        // 顶部高光弧 - 更柔和
        Ellipse({ width: 28, height: 11 })
          .fill('rgba(255, 255, 255, 0.25)')
          .blur(4)
          .position({ x: 50, y: 46 })

        // 底部反光
        Ellipse({ width: 18, height: 6 })
          .fill('rgba(180, 170, 255, 0.1)')
          .blur(3)
          .position({ x: 60, y: 92 })

        // AI文字 - 圆形容器融入球体
        Stack() {
          Circle({ width: 36, height: 36 })
            .fill('rgba(255, 255, 255, 0.08)')
          Text('AI').fontSize(16).fontWeight(700)
            .fontColor('rgba(255, 255, 255, 0.75)')
        }
        .width(36)
        .height(36)
        .clip(new Circle({ width: 36, height: 36 }))
      }.width(140).height(140)

      Text('AI核心').fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
        .padding({ left: 14, right: 14, top: 5, bottom: 5 })
        .backgroundColor(Theme.Color.GlassHeavy)
        .borderRadius(Theme.Radius.round)
        .border({ width: 0.5, color: Theme.Color.BorderLight })
        .shadow(Theme.Shadow.Soft)

      if (this.isLoading && !this.showAiCorePanel) {
        Text('回复中...').fontSize(11).fontColor(Theme.Color.Primary)
          .padding({ left: 10, right: 10, top: 3, bottom: 3 })
          .backgroundColor('rgba(10, 89, 247, 0.08)')
          .borderRadius(Theme.Radius.round)
      } else {
        Text('点击展开对话').fontSize(11).fontColor(Theme.Color.TextTertiary)
      }
    }
    .position({ x: this.centerX - 70, y: this.centerY - 75 })
    .zIndex(90)
    .onClick(() => { this.showAiCorePanel = true; this.showHistoryPanel = false; })
    .opacity(this.showContent ? 1 : 0)
    .scale({ x: this.showContent ? 1 : 0.85, y: this.showContent ? 1 : 0.85 })
    .animation({ duration: 800, curve: Curve.Smooth, delay: 0 })
  }

  @Builder
  buildOrbsLayer() {
    ForEach(this.orbPositions, (orb: OrbPos, index: number) => {
      Column({ space: 8 }) {
        Stack() {
          // 柔和光晕
          Circle({ width: 74, height: 74 }).fill(orb.color).opacity(0.06).blur(18)
          // 外环
          Circle({ width: 64, height: 64 }).fill('transparent')
            .border({ width: 0.8, color: orb.color }).opacity(0.18)
          // 球体底色
          Circle({ width: 54, height: 54 }).fill(orb.color).opacity(0.12)
          // 球体主体渐变
          Circle({ width: 54, height: 54 })
            .linearGradient({ angle: 145, colors: [[orb.color, 0], ['rgba(0,0,0,0.08)', 1]] })
            .shadow({ radius: 14, color: orb.color, offsetX: 0, offsetY: 5 })
          // 高光
          Circle({ width: 46, height: 46 })
            .linearGradient({ angle: 145, colors: [['rgba(255,255,255,0.22)', 0], ['rgba(255,255,255,0.02)', 0.5], ['rgba(0,0,0,0.04)', 1]] })
          // 图标
          SimpleIcon({ iconName: orb.icon, iconSize: 22, color: '#FFFFFF' })
        }.width(74).height(74)

        Text(orb.title)
          .fontSize(12).fontWeight(500).fontColor(Theme.Color.TextPrimary)
          .padding({ left: 10, right: 10, top: 4, bottom: 4 })
          .backgroundColor(Theme.Color.GlassHeavy)
          .borderRadius(Theme.Radius.round)
          .border({ width: 0.5, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)
      }
      .width(92).height(110)
      .justifyContent(FlexAlign.Center)
      .position({ x: orb.x - 46, y: orb.y - 55 })
      .zIndex(100)
      .hitTestBehavior(HitTestMode.Block)
      .onTouch((event: TouchEvent) => {
        if (event.type === TouchType.Up) {
          this.navigateTo(orb.route);
          event.stopPropagation();
        }
      })
      .opacity(this.showContent ? 1 : 0)
      .scale({ x: this.showContent ? 1 : 0.7, y: this.showContent ? 1 : 0.7 })
      .animation({ duration: 700, curve: Curve.Smooth, delay: 150 + index * 100 })
      .stateStyles({
        pressed: {
          .scale({ x: 0.9, y: 0.9 })
          .opacity(0.85)
        },
        normal: {
          .scale({ x: 1, y: 1 })
          .opacity(1)
        }
      })
    })
  }

  @Builder
  buildLoadingIndicator() {
    Column({ space: 10 }) {
      if (this.processingProgress) {
        Text(this.processingProgress).fontSize(12).fontColor(Theme.Color.Primary)
          .padding({ left: 14, right: 14, top: 8, bottom: 8 })
          .backgroundColor('rgba(10, 89, 247, 0.06)').borderRadius(Theme.Radius.round)
      }
      Row({ space: 10 }) {
        Circle({ width: 8, height: 8 }).fill(Theme.Color.Primary).scale({ x: this.dotAnimation1, y: this.dotAnimation1 })
        Circle({ width: 8, height: 8 }).fill(Theme.Color.Secondary).scale({ x: this.dotAnimation2, y: this.dotAnimation2 })
        Circle({ width: 8, height: 8 }).fill(Theme.Color.Accent).scale({ x: this.dotAnimation3, y: this.dotAnimation3 })
      }
    }.position({ x: '50%', y: '60%' }).translate({ x: '-50%' }).zIndex(15)
  }

  @Builder
  buildAICorePanel() {
    Stack() {
      Column().width('100%').height('100%')
        .backgroundColor(Theme.Color.OverlayMedium)
        .onClick(() => { this.showAiCorePanel = false; })

      Column({ space: 0 }) {
        Row() {
          Column({ space: 3 }) {
            Row({ space: 8 }) {
              Stack() {
                Circle({ width: 32, height: 32 })
                  .linearGradient({ angle: 135, colors: [['#667eea', 0], ['#764ba2', 1]] })
                Text('AI').fontSize(12).fontWeight(700).fontColor('#FFFFFF')
              }.width(32).height(32)
              Text('AI核心').fontSize(18).fontWeight(700).fontColor(Theme.Color.TextPrimary)
            }
            Text('对话会沉淀为用户信息，并可触发模型更新')
              .fontSize(11).fontColor(Theme.Color.TextTertiary)
          }.alignItems(HorizontalAlign.Start).layoutWeight(1)

          // 历史消息按钮
          Stack() {
            Circle({ width: 34, height: 34 }).fill(Theme.Color.GlassMedium)
            SimpleIcon({ iconName: 'history', iconSize: 16, color: Theme.Color.TextSecondary })
          }.width(34).height(34)
          .onClick(() => {
            this.showAiCorePanel = false;
            this.showHistoryPanel = true;
          })

          Stack() {
            Circle({ width: 34, height: 34 }).fill(Theme.Color.GlassMedium)
            Text('✕').fontSize(16).fontColor(Theme.Color.TextSecondary)
          }.width(34).height(34).margin({ left: 8 })
          .onClick(() => { this.showAiCorePanel = false; })
        }.width('100%').padding({ left: 20, right: 20, top: 18, bottom: 14 })

        Divider().color(Theme.Color.BorderLight).margin({ left: 20, right: 20 })

        Scroll() {
          Column({ space: 10 }) {
            ForEach(this.messages, (msg: ChatMessage) => {
              Column({ space: 6 }) {
                Row() {
                  Row({ space: 6 }) {
                    Circle({ width: 6, height: 6 })
                      .fill(msg.role === 'user' ? Theme.Color.Primary : Theme.Color.Secondary)
                    Text(msg.role === 'user' ? '你' : 'AI').fontSize(12).fontWeight(500)
                      .fontColor(msg.role === 'user' ? Theme.Color.Primary : Theme.Color.Secondary)
                  }
                  Blank()
                  Text(this.formatTime(msg.timestamp)).fontSize(10).fontColor(Theme.Color.TextTertiary)
                }.width('100%')
                if (msg.thinking) {
                  Text(msg.thinking).fontSize(12).fontColor(Theme.Color.Warning)
                    .padding(10).backgroundColor('rgba(255, 149, 0, 0.06)')
                    .borderRadius(Theme.Radius.m)
                    .border({ width: 1, color: 'rgba(255, 149, 0, 0.1)' }).width('100%')
                }
                Text(msg.content).fontSize(14).fontColor(Theme.Color.TextPrimary).lineHeight(22).width('100%')
              }.width('100%').padding(14)
              .backgroundColor(msg.role === 'user' ? 'rgba(10, 89, 247, 0.05)' : Theme.Color.BackgroundTertiary)
              .borderRadius(Theme.Radius.l)
              .border({ width: 1, color: msg.role === 'user' ? 'rgba(10, 89, 247, 0.1)' : Theme.Color.BorderLight })
            })
          }.width('100%').padding({ left: 16, right: 16, top: 12, bottom: 8 })
        }.layoutWeight(1).scrollBar(BarState.Auto)

        Row({ space: 10 }) {
          TextInput({ placeholder: '和AI核心对话...', text: this.inputText })
            .layoutWeight(1).height(48).fontSize(14)
            .fontColor(Theme.Color.TextPrimary).placeholderColor(Theme.Color.TextTertiary)
            .backgroundColor(Theme.Color.BackgroundTertiary)
            .borderRadius(Theme.Radius.round)
            .border({ width: 1, color: Theme.Color.BorderLight })
            .padding({ left: 18, right: 18 })
            .onChange((v: string) => { this.inputText = v; })
            .onSubmit(() => { this.sendMessage(); })
          Button({ type: ButtonType.Circle }) {
            SimpleIcon({ iconName: 'send', iconSize: 20, color: '#FFFFFF' })
          }.width(48).height(48)
          .backgroundColor(this.inputText.trim() && !this.isLoading ? Theme.Color.Primary : '#CCCCCC')
          .shadow(this.inputText.trim() && !this.isLoading ? Theme.Shadow.GlowPrimary : Theme.Shadow.Soft)
          .enabled(this.inputText.trim().length > 0 && !this.isLoading)
          .onClick(() => { this.sendMessage(); })
        }.width('100%').padding({ left: 16, right: 16, top: 10, bottom: 16 })
        .border({ width: { top: 0.5 }, color: Theme.Color.BorderLight })
      }
      .width('90%').height('75%')
      .backgroundColor(Theme.Color.BackgroundSecondary)
      .borderRadius(Theme.Radius.xl)
      .border({ width: 1, color: Theme.Color.BorderLight })
      .shadow(Theme.Shadow.Elevated)
      .position({ x: '5%', y: '12.5%' })
    }.width('100%').height('100%').zIndex(180)
    .visibility(this.showAiCorePanel ? Visibility.Visible : Visibility.Hidden)
    .hitTestBehavior(this.showAiCorePanel ? HitTestMode.Default : HitTestMode.None)
  }

  @Builder
  buildHistoryPanel() {
    Stack() {
      Column().width('100%').height('100%').backgroundColor(Theme.Color.OverlayMedium)
        .onClick(() => { this.showHistoryPanel = false; this.showAiCorePanel = true; })
      Column() {
        Row() {
          Text('历史对话').fontSize(17).fontWeight(600).fontColor(Theme.Color.TextPrimary)
          Blank()
          Button('新对话').fontSize(12).fontColor(Theme.Color.Primary)
            .backgroundColor(Theme.Color.GlassMedium).height(32).borderRadius(Theme.Radius.round)
            .padding({ left: 14, right: 14 })
            .onClick(() => { this.createNewConversation(); })
          Stack() {
            Circle({ width: 32, height: 32 }).fill(Theme.Color.GlassMedium)
            Text('✕').fontSize(15).fontColor(Theme.Color.TextSecondary)
          }.width(32).height(32).margin({ left: 10 })
          .onClick(() => { this.showHistoryPanel = false; this.showAiCorePanel = true; })
        }.width('100%').padding({ left: 20, right: 20, top: 18, bottom: 14 })
        Divider().color(Theme.Color.BorderLight).margin({ left: 20, right: 20 })
        if (this.conversations.length === 0) {
          Column({ space: 8 }) {
            SimpleIcon({ iconName: 'chat', iconSize: 36, color: Theme.Color.TextTertiary })
            Text('暂无历史对话').fontSize(14).fontColor(Theme.Color.TextTertiary)
          }.width('100%').height(150).justifyContent(FlexAlign.Center)
        } else {
          List({ space: 8 }) {
            ForEach(this.conversations, (c: ConversationItem) => {
              ListItem() {
                Column({ space: 6 }) {
                  Text(c.title).fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
                    .maxLines(1).textOverflow({ overflow: TextOverflow.Ellipsis })
                  Text(c.preview).fontSize(12).fontColor(Theme.Color.TextTertiary)
                    .maxLines(1).textOverflow({ overflow: TextOverflow.Ellipsis })
                }.width('100%').padding(14)
                .backgroundColor(this.currentSessionId === c.id ? 'rgba(10, 89, 247, 0.08)' : Theme.Color.BackgroundTertiary)
                .borderRadius(Theme.Radius.m)
                .border({ width: 1, color: this.currentSessionId === c.id ? 'rgba(10, 89, 247, 0.2)' : Theme.Color.BorderLight })
                .onClick(() => { this.loadConversationMessages(c.id); })
              }
            })
          }.width('100%').layoutWeight(1).padding({ left: 16, right: 16, top: 8 })
        }
      }
      .width('85%').height('60%')
      .backgroundColor(Theme.Color.BackgroundSecondary)
      .borderRadius(Theme.Radius.xl)
      .border({ width: 1, color: Theme.Color.BorderLight })
      .shadow(Theme.Shadow.Elevated)
      .position({ x: '7.5%', y: '20%' })
    }.width('100%').height('100%').zIndex(200)
  }
}
