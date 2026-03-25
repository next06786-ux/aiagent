/**
 * 智能体主界面 - LifeSwarm Agent
 * 🌌 星云对话流 - 真正的3D空间
 * 
 * 设计：
 * - 全屏3D星空，中心是AI核心
 * - 消息星云围绕AI核心漂浮
 * - 点击星云显示消息内容
 * - 输入框在底部
 */
import { curves } from '@kit.ArkUI';
import { Theme } from '../common/Theme';
import { getAIConversationService, ChatMessage } from '../service/AIConversationService';
import { MarkdownParser, MarkdownBlock, InlinePart } from '../utils/MarkdownParser';
import { SimpleIcon } from '../components/IconRenderer';
import http from '@ohos.net.http';
import { ApiConfig } from '../config/ApiConfig';
import { getAuthService, UserInfo } from '../service/AuthService';
import display from '@ohos.display';

// Native模块接口
interface NebulaChatNative {
  nebulaRender(): boolean;
  nebulaAddMessage(id: string, isUser: boolean): boolean;
  nebulaClearMessages(): boolean;
  nebulaScroll(deltaY: number): void;
  nebulaRotateCamera(deltaX: number, deltaY: number): void;
  nebulaZoom(delta: number): void;
  nebulaDestroy(): boolean;
  nebulaHitTest(screenX: number, screenY: number): number;
  nebulaAddFeatureOrb(id: string, r: number, g: number, b: number): boolean;
  nebulaClearFeatureOrbs(): boolean;
  nebulaHitTestFeature(screenX: number, screenY: number): number;
}

// 功能卡片接口
interface FeatureCard {
  id: string;
  title: string;
  subtitle: string;
  route: string;
  gradient: string[];
  iconName: string;
}

// 对话会话接口
interface ConversationItem {
  id: string;
  title: string;
  preview: string;
  message_count: number;
  last_message_time: string;
}

interface ConversationsResponse {
  success: boolean;
  data: ConversationItem[];
}

interface MessagesResponse {
  success: boolean;
  data: MessageData[];
}

interface MessageData {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  thinking?: string;
}

interface CreateConversationData {
  conversation_id: string;
}

interface CreateConversationResponse {
  success: boolean;
  data: CreateConversationData;
}

// 功能球体位置信息（伪3D）
interface FeatureOrbPosition {
  id: string;
  x: number;
  y: number;
  z: number;  // 深度，用于3D效果
  scale: number;
  opacity: number;
  angle: number;
  rotateX: number;
  rotateY: number;
  title: string;
  icon: string;
  gradient: string[];
  route: string;
}

@Entry
@Component
struct AgentHome {
  @State messages: ChatMessage[] = [];
  @State inputText: string = '';
  @State isLoading: boolean = false;
  @State inputFocused: boolean = false;
  @State showContent: boolean = false;
  @State processingProgress: string = '';
  @State dotAnimation1: number = 1;
  @State dotAnimation2: number = 1;
  @State dotAnimation3: number = 1;
  private animationTimer: number = -1;
  
  @State showFunctionPanel: boolean = false;
  @State showHistoryPanel: boolean = false;
  @State showAiCorePanel: boolean = false;
  @State conversations: ConversationItem[] = [];
  @State currentSessionId: string = '';
  @State isLoadingHistory: boolean = false;
  @State userInfo: UserInfo | null = null;
  
  // 选中的消息（点击气泡后显示完整内容）
  @State selectedMessageId: string = '';
  @State showMessageDetail: boolean = false;
  
  // 功能球体位置状态（伪3D）
  @State featureOrbPositions: FeatureOrbPosition[] = [];
  @State screenWidth: number = 360;
  @State screenHeight: number = 780;
  @State centerX: number = 180;
  @State centerY: number = 340;
  
  // 3D渲染相关
  private xComponentId: string = 'nebulaChatXComponent';
  private renderAnimId: number = -1;
  @State isRendererReady: boolean = false;
  @State rendererStatus: string = '等待加载...';
  private nativeModule: NebulaChatNative | null = null;
  
  // 触摸交互
  private lastTouchX: number = 0;
  private lastTouchY: number = 0;
  private isTouching: boolean = false;
  
  // 像素密度 (vp to px conversion)
  private pixelDensity: number = 3.0;
  
  // 功能球体动画定时器
  private orbAnimTimer: number = -1;
  
  private aiService = getAIConversationService();
  private authService = getAuthService();
  
  // 功能定义 - 每个功能一个球体
  private features: FeatureCard[] = [
    { id: 'starmap', title: '知识星图', subtitle: '3D人脉', route: 'pages/KnowledgeStarMapGL', gradient: ['#00D4FF', '#0099CC'], iconName: 'network' },
    { id: 'decision', title: '决策副本', subtitle: '探索未来', route: 'pages/QuickDecisionInput', gradient: ['#FF6B9D', '#C44569'], iconName: 'comparison' },
    { id: 'dashboard', title: '智能洞察', subtitle: '涌现发现', route: 'pages/SmartInsights', gradient: ['#F59E0B', '#D97706'], iconName: 'analytics' },
    { id: 'profile', title: '我的账号', subtitle: '个人中心', route: 'pages/UserProfile', gradient: ['#10B981', '#059669'], iconName: 'user' },
  ];
  
  aboutToAppear() {
    this.initPixelDensity();
    this.messages = this.aiService.getConversationHistory();
    if (this.messages.length === 0) this.addWelcomeMessage();
    this.loadUserInfo();
    this.loadConversations().catch(() => {});
    this.initFeatureOrbPositions();
    this.startOrbAnimation();
  }
  
  private initPixelDensity() {
    try {
      const displayInfo = display.getDefaultDisplaySync();
      this.pixelDensity = displayInfo.densityPixels;
      console.info(`Nebula: pixelDensity = ${this.pixelDensity}`);
    } catch (e) {
      this.pixelDensity = 3.0;
      console.info('Nebula: using default pixelDensity = 3.0');
    }
  }
  
  // 初始化功能球体位置 - 固定在AI核心周围
  private initFeatureOrbPositions() {
    const positions: FeatureOrbPosition[] = [];
    const count = this.features.length;
    const radius = 125;  // 稍微增大半径，给更大的球体留空间
    
    for (let i = 0; i < count; i++) {
      const feature = this.features[i];
      // 从顶部开始，顺时针均匀分布，稍微偏移让布局更自然
      const angle = (i / count) * Math.PI * 2 - Math.PI / 2 + 0.1;
      
      // 固定的基础位置
      const baseX = this.centerX + Math.cos(angle) * radius;
      const baseY = this.centerY + Math.sin(angle) * radius;
      
      positions.push({
        id: feature.id,
        x: baseX,
        y: baseY,
        z: 0,
        scale: 1,
        opacity: 1,
        angle: angle,
        rotateX: 0,
        rotateY: 0,
        title: feature.title,
        icon: feature.iconName,
        gradient: feature.gradient,
        route: feature.route
      });
    }
    
    this.featureOrbPositions = positions;
  }
  
  // 启动功能球体动画
  private startOrbAnimation() {
    if (this.orbAnimTimer !== -1) return;
    
    this.orbAnimTimer = setInterval(() => {
      this.updateOrbPositions();
    }, 50);  // 20fps
  }
  
  private stopOrbAnimation() {
    if (this.orbAnimTimer !== -1) {
      clearInterval(this.orbAnimTimer);
      this.orbAnimTimer = -1;
    }
  }
  
  // 更新功能球体位置 - 原地小幅漂浮
  private updateOrbPositions() {
    const time = Date.now() / 1000;
    const newPositions: FeatureOrbPosition[] = [];
    const count = this.features.length;
    const radius = 125;
    
    for (let i = 0; i < count; i++) {
      const feature = this.features[i];
      const angle = (i / count) * Math.PI * 2 - Math.PI / 2 + 0.1;
      
      // 固定的基础位置
      const baseX = this.centerX + Math.cos(angle) * radius;
      const baseY = this.centerY + Math.sin(angle) * radius;
      
      // 小幅上下漂浮 + 轻微左右摆动，每个球体相位不同
      const floatY = Math.sin(time * 1.0 + i * 1.3) * 5;
      const floatX = Math.cos(time * 0.8 + i * 1.5) * 2;
      
      newPositions.push({
        id: feature.id,
        x: baseX + floatX,
        y: baseY + floatY,
        z: 0,
        scale: 1,
        opacity: 1,
        angle: angle,
        rotateX: 0,
        rotateY: 0,
        title: feature.title,
        icon: feature.iconName,
        gradient: feature.gradient,
        route: feature.route
      });
    }
    
    this.featureOrbPositions = newPositions;
  }
  
  onPageShow() {
    setTimeout(() => { this.showContent = true; }, 50);
    if (this.isRendererReady && this.renderAnimId === -1) {
      this.startRenderLoop();
    }
  }
  
  aboutToDisappear() {
    this.stopLoadingAnimation();
    this.stopRenderLoop();
    this.destroyRenderer();
    this.stopOrbAnimation();
  }
  
  // 添加新消息
  private addMessageWithAnimation(msg: ChatMessage) {
    this.messages.push(msg);
  }
  
  private initRenderer(context: object) {
    try {
      console.info('Nebula: initRenderer called, context type:', typeof context);
      this.rendererStatus = '正在初始化...';
      this.nativeModule = context as NebulaChatNative;
      
      const hasRender = this.nativeModule && typeof this.nativeModule.nebulaRender === 'function';
      
      if (hasRender) {
        console.info('Nebula: Native module loaded successfully');
        this.isRendererReady = true;
        this.rendererStatus = '3D渲染已启动';
        this.startRenderLoop();
      } else {
        console.error('Nebula: Native module methods not available');
        this.rendererStatus = '渲染器方法不可用';
      }
    } catch (err) {
      console.error('Nebula: Init error:', (err as Error).message);
      this.rendererStatus = '初始化错误: ' + (err as Error).message;
    }
  }
  
  private startRenderLoop() {
    if (this.renderAnimId !== -1) return;
    
    console.info('Nebula: Starting render loop...');
    let frameCount = 0;
    
    this.renderAnimId = setInterval(() => {
      if (this.isRendererReady && this.nativeModule) {
        this.nativeModule.nebulaRender();
        frameCount++;
        if (frameCount % 90 === 0) {
          console.info(`Nebula: Render loop running, frame ${frameCount}`);
        }
      }
    }, 33);
    
    console.info('Nebula: Render loop started, timer id:', this.renderAnimId);
  }
  
  private stopRenderLoop() {
    if (this.renderAnimId !== -1) {
      clearInterval(this.renderAnimId);
      this.renderAnimId = -1;
    }
  }
  
  private destroyRenderer() {
    if (this.isRendererReady && this.nativeModule) {
      this.nativeModule.nebulaDestroy();
      this.isRendererReady = false;
      this.nativeModule = null;
    }
  }

  private async loadUserInfo() {
    try { this.userInfo = await this.authService.getCurrentUserAsync(); }
    catch (err) { console.error('加载用户信息失败:', err); }
  }
  
  private async loadConversations() {
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const url = `${ApiConfig.getBaseUrl()}/api/chat/sessions/${userId}`;
      const response = await httpRequest.request(url, { method: http.RequestMethod.GET });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, Object>;
        const sessions = (data.sessions as Array<Record<string, Object>>) || [];
        this.conversations = sessions.map((item: Record<string, Object>): ConversationItem => {
          return {
            id: item.session_id as string,
            title: item.title as string || '新对话',
            preview: item.preview as string || '',
            message_count: item.message_count as number || 0,
            last_message_time: item.last_time as string || ''
          }
        });
      }
    } catch (err) { console.error('加载历史对话失败:', err); }
  }
  
  private addWelcomeMessage() {
    const welcomeMsg = new ChatMessage(
      Date.now().toString(), 'assistant',
      `✨ 欢迎来到 LifeSwarm 星云空间\n\n我是漂浮在中心的AI核心\n\n🌌 你的每句话都会化作蓝色星云\n🔮 我的回应凝聚成紫色光芒\n✦ 点击星云查看消息内容\n\n向星空诉说你的想法吧`,
      Date.now()
    );
    this.messages.push(welcomeMsg);
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
    
    const userMsg = new ChatMessage(Date.now().toString(), 'user', userMessage, Date.now());
    this.addMessageWithAnimation(userMsg);
    
    if (this.isRendererReady && this.nativeModule) {
      this.nativeModule.nebulaAddMessage(userMsg.id, true);
    }
    
    const aiMsgId = (Date.now() + 1).toString();
    const aiMsg = new ChatMessage(aiMsgId, 'assistant', '', Date.now(), '');
    this.addMessageWithAnimation(aiMsg);
    
    if (this.isRendererReady && this.nativeModule) {
      this.nativeModule.nebulaAddMessage(aiMsgId, false);
    }
    
    try {
      await this.aiService.chatStreamWebSocket(
        userMessage,
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
      console.error('发送消息失败:', (err as Error).message);
      const idx = this.messages.findIndex(m => m.id === aiMsgId);
      if (idx >= 0) this.messages.splice(idx, 1);
      this.isLoading = false; this.stopLoadingAnimation();
    }
  }

  private async triggerModelUpdate() {
    if (!this.userInfo) return;
    try {
      const httpRequest = http.createHttp();
      const url = `${ApiConfig.getBaseUrl()}/api/lora/train/${this.userInfo.user_id}`;
      const response = await httpRequest.request(url, { method: http.RequestMethod.POST });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        this.processingProgress = '用户模型训练已触发';
      }
    } catch (err) {
      console.error('触发用户模型训练失败:', err);
    }
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
      const url = `${ApiConfig.getBaseUrl()}/api/chat/session/${userId}/${sessionId}`;
      const response = await httpRequest.request(url, { method: http.RequestMethod.GET });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, Object>;
        const history = (data.history as Array<Record<string, string>>) || [];
        this.messages = history.map((m: Record<string, string>) => new ChatMessage(
          m.id || Date.now().toString(),
          m.role as 'user' | 'assistant',
          m.content || '',
          m.timestamp ? new Date(m.timestamp).getTime() : Date.now(),
          m.thinking
        ));
        this.currentSessionId = sessionId;
        this.showHistoryPanel = false;
        this.showAiCorePanel = true;
      }
    } catch (err) { console.error('加载对话消息失败:', err); }
    finally { this.isLoadingHistory = false; }
  }
  
  async createNewConversation() {
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const url = `${ApiConfig.getBaseUrl()}/api/chat/session/new/${userId}`;
      const response = await httpRequest.request(url, { method: http.RequestMethod.POST });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, string>;
        if (data && data.session_id) {
          this.currentSessionId = data.session_id;
          this.messages = [];
          this.addWelcomeMessage();
          this.showHistoryPanel = false;
          this.showAiCorePanel = true;
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
  
  private parseMarkdownBlocks(content: string): MarkdownBlock[] { return MarkdownParser.parse(content); }
  private parseInlineParts(text: string): InlinePart[] { return MarkdownParser.parseInline(text); }
  
  // 获取选中的消息
  private getSelectedMessage(): ChatMessage | null {
    return this.messages.find(m => m.id === this.selectedMessageId) || null;
  }


  build() {
    Stack() {
      // 1. 全屏3D星云空间 - OpenGL ES (最底层)
      XComponent({
        id: this.xComponentId,
        type: XComponentType.SURFACE,
        libraryname: 'nebulachat'
      })
        .width('100%')
        .height('100%')
        .zIndex(0)
        .onLoad((context?: object) => {
          console.info('Nebula: XComponent onLoad triggered, context exists:', context !== undefined && context !== null);
          if (context) {
            console.info('Nebula: Context received, initializing renderer...');
            this.rendererStatus = 'Context已接收';
            this.initRenderer(context);
          } else {
            console.error('Nebula: XComponent onLoad - context is null/undefined!');
            this.rendererStatus = 'Native库加载失败';
          }
        })
        .onDestroy(() => {
          console.info('Nebula: XComponent onDestroy');
          this.stopRenderLoop();
          this.destroyRenderer();
        })
      
      // 2. 功能球体层 - 直接渲染在Stack中
      this.FeatureOrbsLayer()
      
      // 调试信息
      Text(this.rendererStatus)
        .fontSize(12)
        .fontColor(this.isRendererReady ? '#00FF00' : '#FF6600')
        .padding(8)
        .backgroundColor('rgba(0, 0, 0, 0.4)')
        .borderRadius(8)
        .position({ x: 10, y: 70 })
        .zIndex(10)
      
      // 3. 顶部栏
      this.TopBar()
      
      // 4. 加载指示器
      if (this.isLoading) {
        this.LoadingIndicator()
      }
      
      // 5. 中心AI核心交互入口
      this.AICoreEntry()

      // 6. AI对话面板
      if (this.showAiCorePanel) {
        this.AICorePanel()
      }

      // 7. 历史面板
      if (this.showHistoryPanel) { this.HistoryPanel() }
    }
    .width('100%')
    .height('100%')
    .onAreaChange((oldArea: Area, newArea: Area) => {
      this.screenWidth = newArea.width as number;
      this.screenHeight = newArea.height as number;
      this.centerX = this.screenWidth / 2;
      this.centerY = this.screenHeight / 2;  // 屏幕正中心，与OpenGL AI核心对齐
      this.initFeatureOrbPositions();
    })
    .onTouch((event: TouchEvent) => {
      if (event.type === TouchType.Down) {
        if (event.touches.length === 1) {
          this.isTouching = true;
          this.lastTouchX = event.touches[0].x;
          this.lastTouchY = event.touches[0].y;
        }
      } else if (event.type === TouchType.Move) {
        if (this.isTouching && this.isRendererReady && this.nativeModule && event.touches.length === 1) {
          const deltaX = event.touches[0].x - this.lastTouchX;
          const deltaY = event.touches[0].y - this.lastTouchY;
          // 只有移动距离大于阈值才旋转
          if (Math.abs(deltaX) > 3 || Math.abs(deltaY) > 3) {
            this.nativeModule.nebulaRotateCamera(deltaX, deltaY);
          }
          this.lastTouchX = event.touches[0].x;
          this.lastTouchY = event.touches[0].y;
        }
      } else if (event.type === TouchType.Up) {
        this.isTouching = false;
      }
    })
  }
  
  @Builder
  FeatureOrbsLayer() {
    // 功能球体 - 精致的玻璃质感设计
    ForEach(this.featureOrbPositions, (orb: FeatureOrbPosition) => {
      Column({ space: 6 }) {
        // 发光球体容器
        Stack() {
          // 最外层 - 柔和光晕
          Circle({ width: 76, height: 76 })
            .fill(orb.gradient[0])
            .opacity(0.15)
            .blur(20)
          
          // 外环 - 呼吸光环
          Circle({ width: 66, height: 66 })
            .fill('transparent')
            .border({ width: 1.5, color: orb.gradient[0] })
            .opacity(0.4)
          
          // 球体主体 - 玻璃质感渐变
          Circle({ width: 54, height: 54 })
            .linearGradient({
              angle: 145,
              colors: [
                [orb.gradient[0], 0],
                [orb.gradient[1], 0.6],
                ['rgba(0, 0, 0, 0.3)', 1]
              ]
            })
            .shadow({ radius: 16, color: orb.gradient[0], offsetX: 0, offsetY: 6 })
          
          // 内部深色层 - 增加立体感
          Circle({ width: 46, height: 46 })
            .linearGradient({
              angle: 145,
              colors: [
                ['rgba(255, 255, 255, 0.1)', 0],
                ['rgba(0, 0, 0, 0.2)', 1]
              ]
            })
          
          // 顶部高光 - 玻璃反射
          Ellipse({ width: 24, height: 12 })
            .fill('rgba(255, 255, 255, 0.45)')
            .position({ x: 12, y: 8 })
            .blur(4)
          
          // 底部反光
          Ellipse({ width: 16, height: 6 })
            .fill('rgba(255, 255, 255, 0.15)')
            .position({ x: 28, y: 52 })
            .blur(3)
          
          // 图标 - 带阴影
          Column() {
            SimpleIcon({
              iconName: orb.icon,
              iconSize: 24,
              color: '#FFFFFF'
            })
          }
          .shadow({ radius: 8, color: 'rgba(0, 0, 0, 0.3)', offsetX: 0, offsetY: 2 })
        }
        .width(76)
        .height(76)
        
        // 标题 - 带背景模糊
        Text(orb.title)
          .fontSize(12)
          .fontWeight(FontWeight.Medium)
          .fontColor('#FFFFFF')
          .padding({ left: 10, right: 10, top: 4, bottom: 4 })
          .backgroundColor('rgba(0, 0, 0, 0.35)')
          .borderRadius(10)
          .shadow({ radius: 6, color: 'rgba(0, 0, 0, 0.4)', offsetX: 0, offsetY: 2 })
      }
      .width(100)
      .height(115)
      .justifyContent(FlexAlign.Center)
      .position({
        x: orb.x - 50,
        y: orb.y - 57
      })
      .zIndex(100)
      .hitTestBehavior(HitTestMode.Block)
      .onTouch((event: TouchEvent) => {
        if (event.type === TouchType.Up) {
          console.info(`Orb touched: ${orb.id} -> ${orb.route}`);
          this.navigateTo(orb.route);
          event.stopPropagation();
        }
      })
    })
  }

  @Builder
  TopBar() {
    Row() {
      Row({ space: 10 }) {
        Stack() {
          Circle({ width: 44, height: 44 }).fill('rgba(140, 100, 255, 0.2)').blur(12)
          Circle({ width: 36, height: 36 }).fill('rgba(102, 126, 234, 0.8)')
          Text('✦').fontSize(18).fontColor('#FFFFFF')
        }.width(44).height(44)
        
        Column({ space: 1 }) {
          Text('LifeSwarm').fontSize(18).fontWeight(700).fontColor('#FFFFFF')
          Text('3D星云空间').fontSize(11).fontColor('rgba(180, 160, 255, 0.7)')
        }.alignItems(HorizontalAlign.Start)
      }
      
      Blank()
      
      Row({ space: 8 }) {
        Button({ type: ButtonType.Circle }) { Text('📜').fontSize(16) }
          .width(38).height(38).backgroundColor('rgba(100, 80, 180, 0.3)')
          .onClick(() => { this.showHistoryPanel = true; })
      }
    }
    .width('100%')
    .height(64)
    .padding({ left: 16, right: 16 })
    .backgroundColor('rgba(5, 0, 20, 0.5)')  // 更透明
    .position({ x: 0, y: 0 })
    .zIndex(10)
  }
  
  @Builder
  CenterHint() {
    Column({ space: 12 }) {
      Text('✦').fontSize(40).fontColor('rgba(150, 120, 255, 0.6)')
      Text('AI核心在中心').fontSize(14).fontColor('rgba(180, 160, 220, 0.6)')
      Text('拖动旋转 · 双指缩放').fontSize(12).fontColor('rgba(150, 130, 200, 0.5)')
    }
    .position({ x: '50%', y: '45%' })
    .translate({ x: '-50%', y: '-50%' })
  }
  
  @Builder
  LoadingIndicator() {
    Column({ space: 12 }) {
      if (this.processingProgress) {
        Text(this.processingProgress)
          .fontSize(12)
          .fontColor('rgba(180, 140, 255, 0.9)')
          .padding({ left: 14, right: 14, top: 8, bottom: 8 })
          .backgroundColor('rgba(100, 60, 180, 0.3)')
          .borderRadius(14)
      }
      
      Row({ space: 12 }) {
        Circle({ width: 10, height: 10 }).fill('rgba(100, 180, 255, 0.8)').scale({ x: this.dotAnimation1, y: this.dotAnimation1 })
        Circle({ width: 10, height: 10 }).fill('rgba(150, 130, 255, 0.8)').scale({ x: this.dotAnimation2, y: this.dotAnimation2 })
        Circle({ width: 10, height: 10 }).fill('rgba(200, 100, 255, 0.8)').scale({ x: this.dotAnimation3, y: this.dotAnimation3 })
      }
    }
    .position({ x: '50%', y: '55%' })
    .translate({ x: '-50%' })
    .zIndex(15)
  }
  
  @Builder
  InputArea() {
    Row({ space: 10 }) {
      TextInput({ placeholder: '向星云诉说...', text: this.inputText })
        .layoutWeight(1)
        .height(50)
        .fontSize(15)
        .fontColor('#FFFFFF')
        .placeholderColor('rgba(180, 160, 220, 0.5)')
        .backgroundColor('rgba(30, 15, 60, 0.6)')
        .borderRadius(25)
        .padding({ left: 20, right: 20 })
        .border({ width: 1, color: this.inputFocused ? 'rgba(150, 120, 255, 0.6)' : 'rgba(120, 80, 200, 0.3)' })
        .onChange((v: string) => { this.inputText = v; })
        .onFocus(() => { this.inputFocused = true; })
        .onBlur(() => { this.inputFocused = false; })
        .onSubmit(() => { this.sendMessage(); })
      
      Button({ type: ButtonType.Circle }) {
        Text('✦').fontSize(20).fontColor('#FFFFFF')
      }
      .width(50)
      .height(50)
      .backgroundColor(this.inputText.trim() && !this.isLoading 
        ? 'rgba(124, 58, 237, 0.9)' 
        : 'rgba(60, 40, 100, 0.5)')
      .enabled(this.inputText.trim().length > 0 && !this.isLoading)
      .onClick(() => { this.sendMessage(); })
    }
    .width('100%')
    .padding({ left: 16, right: 16, bottom: 20, top: 12 })
    .backgroundColor('rgba(5, 0, 20, 0.6)')  // 更透明
    .position({ x: 0, y: '100%' })
    .translate({ y: '-100%' })
    .zIndex(10)
  }
  
  @Builder
  FloatingButtons() {
    Column() {}
      .position({ x: '85%', y: '75%' })
      .zIndex(10)
  }
  
  @Builder
  MessageDetailPanel() {
    Column() {}
  }
  
  @Builder
  SingleMessageDetail() {
    Column() {}
  }
  
  @Builder
  AllMessagesPanel() {
    Column() {}
  }

  @Builder
  HistoryPanel() {
    Stack() {
      Column().width('100%').height('100%').backgroundColor('rgba(5, 0, 20, 0.8)')
        .onClick(() => { this.showHistoryPanel = false; })
      
      Column() {
        Row() {
          Text('📜 历史对话').fontSize(16).fontWeight(600).fontColor('#FFFFFF')
          Blank()
          Button('新对话').fontSize(11).fontColor('rgba(180, 140, 255, 0.9)')
            .backgroundColor('rgba(100, 60, 180, 0.3)').height(30).borderRadius(15)
            .onClick(() => { this.createNewConversation(); })
          Button({ type: ButtonType.Circle }) { Text('✕').fontSize(16).fontColor('rgba(200, 180, 255, 0.7)') }
            .width(30).height(30).backgroundColor('transparent').margin({ left: 10 })
            .onClick(() => { this.showHistoryPanel = false; })
        }.width('100%').padding({ left: 16, right: 16, top: 14, bottom: 10 })
        
        if (this.conversations.length === 0) {
          Column() { Text('暂无历史').fontSize(13).fontColor('rgba(150, 130, 200, 0.5)') }
            .width('100%').height(150).justifyContent(FlexAlign.Center)
        } else {
          List({ space: 10 }) {
            ForEach(this.conversations, (c: ConversationItem) => {
              ListItem() {
                Column({ space: 6 }) {
                  Text(c.title).fontSize(13).fontWeight(600).fontColor('rgba(220, 210, 250, 0.95)')
                    .maxLines(1).textOverflow({ overflow: TextOverflow.Ellipsis })
                  Text(c.preview).fontSize(11).fontColor('rgba(180, 170, 220, 0.7)')
                    .maxLines(1).textOverflow({ overflow: TextOverflow.Ellipsis })
                }
                .width('100%')
                .padding(12)
                .backgroundColor(this.currentSessionId === c.id ? 'rgba(100, 60, 180, 0.3)' : 'rgba(40, 25, 80, 0.4)')
                .borderRadius(12)
                .onClick(() => { this.loadConversationMessages(c.id); })
              }
            })
          }.width('100%').layoutWeight(1).padding({ left: 12, right: 12 })
        }
      }
      .width('85%')
      .height('65%')
      .backgroundColor('rgba(15, 8, 40, 0.95)')
      .borderRadius(20)
      .border({ width: 1, color: 'rgba(150, 100, 255, 0.25)' })
      .position({ x: '7.5%', y: '17.5%' })
    }.width('100%').height('100%').zIndex(150)
  }
}


  @Builder
  AICoreEntry() {
    Column({ space: 8 }) {
      Stack() {
        Circle({ width: 110, height: 110 }).fill('rgba(120, 100, 255, 0.18)').blur(24)
        Circle({ width: 84, height: 84 }).fill('rgba(102, 126, 234, 0.85)')
        Text('AI').fontSize(20).fontWeight(700).fontColor('#FFFFFF')
      }
      Text('AI核心').fontSize(13).fontWeight(600).fontColor('#FFFFFF')
      Text('点击展开对话').fontSize(10).fontColor('rgba(200, 190, 255, 0.7)')
    }
    .position({ x: this.centerX - 55, y: this.centerY - 70 })
    .zIndex(120)
    .onClick(() => {
      this.showAiCorePanel = true;
      this.showHistoryPanel = false;
    })
  }

  @Builder
  AICorePanel() {
    Stack() {
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('rgba(5, 0, 20, 0.78)')
        .onClick(() => { this.showAiCorePanel = false; })

      Column({ space: 12 }) {
        Row() {
          Column({ space: 2 }) {
            Text('AI核心').fontSize(18).fontWeight(700).fontColor('#FFFFFF')
            Text('对话会沉淀为用户信息，并可触发用户模型更新').fontSize(11).fontColor('rgba(200, 190, 255, 0.7)')
          }
          .alignItems(HorizontalAlign.Start)
          .layoutWeight(1)

          Button('更新用户模型')
            .fontSize(11)
            .fontColor('#10B981')
            .backgroundColor('rgba(255,255,255,0.08)')
            .borderRadius(14)
            .onClick(() => { this.triggerModelUpdate(); })

          Button({ type: ButtonType.Circle }) { Text('✕').fontSize(18).fontColor('rgba(200, 180, 255, 0.8)') }
            .width(34)
            .height(34)
            .backgroundColor('transparent')
            .onClick(() => { this.showAiCorePanel = false; })
        }
        .width('100%')

        Scroll() {
          Column({ space: 10 }) {
            ForEach(this.messages, (msg: ChatMessage) => {
              Column({ space: 6 }) {
                Row() {
                  Text(msg.role === 'user' ? '你' : 'AI').fontSize(11).fontColor(msg.role === 'user' ? 'rgba(150, 200, 255, 0.8)' : 'rgba(200, 150, 255, 0.8)')
                  Blank()
                  Text(this.formatTime(msg.timestamp)).fontSize(10).fontColor('rgba(150, 130, 200, 0.5)')
                }
                .width('100%')
                if (msg.thinking) {
                  Text(msg.thinking)
                    .fontSize(11)
                    .fontColor('rgba(255, 210, 160, 0.85)')
                    .padding(10)
                    .backgroundColor('rgba(255, 180, 100, 0.08)')
                    .borderRadius(8)
                    .width('100%')
                }
                Text(msg.content)
                  .fontSize(13)
                  .fontColor('#F3F4F6')
                  .lineHeight(20)
                  .width('100%')
              }
              .width('100%')
              .padding(12)
              .backgroundColor(msg.role === 'user' ? 'rgba(60, 100, 180, 0.22)' : 'rgba(100, 60, 160, 0.22)')
              .borderRadius(12)
            })
          }
          .width('100%')
          .padding({ bottom: 8 })
        }
        .layoutWeight(1)
        .scrollBar(BarState.Auto)

        Row({ space: 10 }) {
          TextInput({ placeholder: '和AI核心对话，系统会据此持续理解你...', text: this.inputText })
            .layoutWeight(1)
            .height(48)
            .fontSize(14)
            .fontColor('#FFFFFF')
            .placeholderColor('rgba(180, 160, 220, 0.5)')
            .backgroundColor('rgba(30, 15, 60, 0.6)')
            .borderRadius(24)
            .padding({ left: 18, right: 18 })
            .onChange((v: string) => { this.inputText = v; })
            .onSubmit(() => { this.sendMessage(); })

          Button({ type: ButtonType.Circle }) {
            Text('✦').fontSize(18).fontColor('#FFFFFF')
          }
          .width(48)
          .height(48)
          .backgroundColor(this.inputText.trim() && !this.isLoading ? 'rgba(124, 58, 237, 0.9)' : 'rgba(60, 40, 100, 0.5)')
          .enabled(this.inputText.trim().length > 0 && !this.isLoading)
          .onClick(() => { this.sendMessage(); })
        }
        .width('100%')
      }
      .width('88%')
      .height('72%')
      .padding(16)
      .backgroundColor('rgba(15, 8, 40, 0.96)')
      .borderRadius(24)
      .border({ width: 1, color: 'rgba(150, 100, 255, 0.25)' })
      .position({ x: '6%', y: '14%' })
    }
    .width('100%')
    .height('100%')
    .zIndex(180)
  }
