/**
 *  - LifeSwarm AI
 *  - HarmonyOS 6
 * 
 */
import { router } from '@kit.ArkUI';
import { curves } from '@kit.ArkUI';
import promptAction from '@ohos.promptAction';
import { MultimodalDataCollector } from '../service/MultimodalDataCollector';
import { SensorService } from '../service/SensorService';
import { ContextService } from '../service/ContextService';
import { BackgroundSensorService } from '../service/BackgroundSensorService';
import { ConversationHistoryService } from '../service/ConversationHistoryService';
import { Theme } from '../common/Theme';
import { SimpleIcon } from '../components/IconRenderer';
import { getAuthService, UserInfo } from '../service/AuthService';
import { getUserSessionManager } from '../service/UserSessionManager';

/**
 * 页面组件
 */
interface AnimationConfig {
  duration: number;
  delay?: number;
  curve?: Curve | ICurve;
}

/**
 * 页面组件
 */
interface FeatureCard {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  route: string;
  gradient: string[];
  iconPath?: string;
}

/**
 * 页面组件
 */
interface SystemStatus {
  isCollecting: boolean;
  dataQuality: number;
  lastUpdate: number;
}

/**
 * 个人中心菜单项
 */
interface ProfileMenuItem {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
  color: string;
  route?: string;
  action?: () => void;
}


@Entry
@Component
struct Index {
  @State currentUser: string = 'default_user';
  @State systemStatus: SystemStatus = {
    isCollecting: false,
    dataQuality: 0,
    lastUpdate: 0
  };
  @State userInfo: UserInfo | null = null;
  @State profileShowContent: boolean = false;
  @State profileSelectedMenu: number = -1;
  
  private dataCollector: MultimodalDataCollector = MultimodalDataCollector.getInstance();
  private sensorService: SensorService = SensorService.getInstance();
  private contextService: ContextService = ContextService.getInstance();
  private backgroundSensorService: BackgroundSensorService = BackgroundSensorService.getInstance();
  private conversationHistoryService: ConversationHistoryService = ConversationHistoryService.getInstance();
  private authService = getAuthService();
  private profileScroller: Scroller = new Scroller();
  
  @State scrollOffset: number = 0;
  @State selectedFeature: number = -1;
  @State currentTabIndex: number = 0;
  @State showContent: boolean = false;
  @State playEnterAnimation: boolean = false;
  @State animationKey: number = 0; // 处理逻辑
  @State isAtTop: boolean = true; // 处理逻辑
  private homeScroller: Scroller = new Scroller(); // 处理逻辑
  // 3D
  private navCanvasReady: boolean = false
  private settings: RenderingContextSettings = new RenderingContextSettings(true)
  private navCanvasContext: CanvasRenderingContext2D = new CanvasRenderingContext2D(this.settings)
  
  //  - 
  private springCurve: ICurve = curves.springCurve(10, 1, 328, 34);
  
  //  - 
  private pageAnimationTimer: number = -1;
  
  private profileMenuItems: ProfileMenuItem[] = [
    {
      id: 'change_password',
      title: '修改密码',
      subtitle: '保护账号安全',
      icon: 'lock',
      color: '#764ba2',
      action: () => {
        promptAction.showToast({ message: '修改密码功能开发中' });
      }
    },
    {
      id: 'notification',
      title: '通知设置',
      subtitle: '管理消息提醒',
      icon: 'bell',
      color: '#f093fb',
      action: () => {
        promptAction.showToast({ message: '通知设置功能开发中' });
      }
    },
    {
      id: 'privacy',
      title: '隐私设置',
      subtitle: '控制数据共享',
      icon: 'shield',
      color: '#f5576c',
      action: () => {
        promptAction.showToast({ message: '隐私设置功能开发中' });
      }
    },
    {
      id: 'about',
      title: '关于应用',
      subtitle: '版本信息与帮助',
      icon: 'info',
      color: '#4facfe',
      action: () => {
        promptAction.showToast({ message: '关于应用功能开发中' });
      }
    }
  ];
  
  private features: FeatureCard[] = [
    {
      id: 'ai_chat',
      title: 'AI ',
      subtitle: ' AI ',
      description: ' Qwen3.5-Plus ',
      route: 'pages/AIChat',
      gradient: Theme.Gradient.Aurora
    },
    {
      id: 'meta_agent',
      title: '',
      subtitle: '',
      description: '',
      route: 'pages/MetaAgentCoordination',
      gradient: Theme.Gradient.Sunrise
    },
    {
      id: 'knowledge_graph',
      title: '',
      subtitle: '',
      description: '',
      route: 'pages/KnowledgeGraphCanvas',
      gradient: Theme.Gradient.Ocean
    },
    {
      id: 'learning',
      title: '',
      subtitle: '',
      description: '',
      route: 'pages/LearningProgress',
      gradient: Theme.Gradient.Mint
    },
    {
      id: 'dashboard',
      title: '',
      subtitle: '',
      description: '',
      route: 'pages/Dashboard',
      gradient: Theme.Gradient.Sunrise // Or another gradient if needed, e.g. create a new one in Theme
    },
    {
      id: 'camera',
      title: '',
      subtitle: '',
      description: 'AI ',
      route: 'pages/Camera',
      gradient: Theme.Gradient.Mystic
    },
    {
      id: 'life_insights',
      title: ' ',
      subtitle: '6',
      description: '56',
      route: 'pages/LifeDomainInsights',
      gradient: Theme.Gradient.Aurora
    },
    {
      id: 'perception_test',
      title: ' ',
      subtitle: '',
      description: '',
      route: 'pages/PerceptionLayerTest',
      gradient: ['#FF6B6B', '#4ECDC4'] // Keep custom for test
    },
    {
      id: 'decision_comparison',
      title: ' ',
      subtitle: '',
      description: 'AI',
      route: 'pages/DecisionComparison',
      gradient: Theme.Gradient.Mint
    },
    {
      id: 'parallel_universe',
      title: '平行宇宙模拟',
      subtitle: '未来12个月',
      description: '模拟不同决策选项的未来时间线，6维风险评估',
      route: 'pages/ParallelUniverseSimulation',
      gradient: Theme.Gradient.Mystic
    },
    {
      id: 'decision_dungeon',
      title: '决策副本',
      subtitle: '个性化闯关',
      description: '描述你的决策问题，AI生成个性化副本，像游戏一样探索未来',
      route: 'pages/QuickDecisionInput',
      gradient: ['#9C27B0', '#E91E63']
    }
  ];
  
  aboutToAppear(): void {
    console.info('LifeSwarm', 'Main page loaded');
    // 处理逻辑
    this.showContent = false;
    this.playEnterAnimation = false;
    this.initializeSystem();
    this.loadProfileUserInfo();
    // 处理逻辑
    setTimeout(() => {
      this.playEnterAnimation = true;
      this.showContent = true;
      this.profileShowContent = true;
    }, 50);
  }
  
  onPageShow(): void {
    // 处理逻辑
    if (!this.showContent) {
      return;
    }
    this.triggerPageAnimation();
  }
  
  /**
 * 页面组件
 */
  private triggerPageAnimation(delay: number = 0): void {
    // 处理逻辑
    try {
      const offset = this.homeScroller.currentOffset();
      this.isAtTop = !offset || offset.yOffset < 10; // 10px
    } catch (e) {
      this.isAtTop = true; // 处理逻辑
    }
    
    // 处理逻辑
    this.playEnterAnimation = true;
    this.showContent = true;
  }
  
  private buildEnterAnimation(duration: number, delay: number = 0, curve?: Curve | ICurve): AnimationConfig {
    if (!this.playEnterAnimation) {
      return {
        duration: 0
      };
    }
    
    // 处理逻辑
    const animCurve = curve !== undefined ? curve : this.springCurve;
    
    return {
      duration: duration,
      delay: delay,
      curve: animCurve
    };
  }
  
  aboutToDisappear(): void {
    // 处理逻辑
    if (this.pageAnimationTimer !== -1) {
      clearTimeout(this.pageAnimationTimer);
      this.pageAnimationTimer = -1;
    }
    this.dataCollector.stopCollection();
    
    // 处理逻辑
    this.backgroundSensorService.stopBackgroundCollection();
  }
  
  /**
   *  - 
   */
  private drawBackgroundParticles(ctx: CanvasRenderingContext2D, width: number, height: number): void {
    // 处理逻辑
    for (let layer = 0; layer < 3; layer++) {
      let layerDepth = layer / 3
      let particleCount = 15 - layer * 3  // 处理逻辑
      for (let i = 0; i < particleCount; i++) {
        // 处理逻辑
        let angle = (i / particleCount) * Math.PI * 2
        let distance = 120 + layer * 40 + Math.sin(angle * 3) * 30
        let x = width / 2 + Math.cos(angle) * distance
        let y = height / 2 + Math.sin(angle) * distance * 0.6
        
        // 处理逻辑
        let size = (2.5 - layer * 0.5) + Math.sin(angle * 5) * 0.5
        let alpha = (0.15 - layer * 0.04) + Math.sin(angle * 7) * 0.05
        
        // 处理逻辑
        ctx.shadowColor = `rgba(103, 126, 234, ${alpha * 2})`
        ctx.shadowBlur = 4 - layer
        
        ctx.beginPath()
        ctx.arc(x, y, size, 0, 2 * Math.PI)
        ctx.fillStyle = `rgba(103, 126, 234, ${alpha})`
        ctx.fill()
      }
    }
    
    // 处理逻辑
    ctx.shadowColor = 'transparent'
    ctx.shadowBlur = 0
  }
  
  
  
  /**
   *  (3D)
   */
  private drawFluidBackground(ctx: CanvasRenderingContext2D, width: number, height: number): void {
    // 处理逻辑
    ctx.clearRect(0, 0, width, height)
    
    // 处理逻辑
    // 处理逻辑
    // 1
    let gradient1 = ctx.createRadialGradient(
      width * 0.2, height * 0.2, 0,
      width * 0.2, height * 0.2, width * 0.8
    )
    gradient1.addColorStop(0, 'rgba(103, 126, 234, 0.4)')
    gradient1.addColorStop(1, 'rgba(103, 126, 234, 0)')
    
    ctx.fillStyle = gradient1
    ctx.fillRect(0, 0, width, height)
    
    // 2
    let gradient2 = ctx.createRadialGradient(
      width * 0.8, height * 0.8, 0,
      width * 0.8, height * 0.8, width * 0.9
    )
    gradient2.addColorStop(0, 'rgba(118, 75, 162, 0.3)')
    gradient2.addColorStop(1, 'rgba(118, 75, 162, 0)')
    
    ctx.fillStyle = gradient2
    ctx.fillRect(0, 0, width, height)
    
    //  ()
    this.drawBackgroundParticles(ctx, width, height)
  }
  
  
  /**
 * 页面组件
 */
  private async initializeSystem(): Promise<void> {
    try {
      // 处理逻辑
      const stats = this.dataCollector.getCollectionStats();
      this.systemStatus.isCollecting = stats.isCollecting;
      
      // 处理逻辑
      await this.backgroundSensorService.startBackgroundCollection(this.currentUser);
      
      // 处理逻辑
      await this.conversationHistoryService.restoreFromLocal();
      
      console.info('LifeSwarm', 'System initialized with background services');
    } catch (error) {
      console.error('LifeSwarm', 'Initialization failed:', error);
    }
  }
  
  /**
 * 页面组件
 */
  private toggleDataCollection(): void {
    if (this.systemStatus.isCollecting) {
      this.dataCollector.stopCollection();
      this.systemStatus.isCollecting = false;
    } else {
      this.dataCollector.startCollection(this.currentUser);
      this.systemStatus.isCollecting = true;
    }
  }
  
  /**
 * 页面组件
 */
  private async triggerCollection(): Promise<void> {
    try {
      const data = await this.dataCollector.triggerCollection(this.currentUser);
      this.systemStatus.dataQuality = data.metadata.dataQuality;
      this.systemStatus.lastUpdate = Date.now();
      
      console.info('LifeSwarm', 'Data collected:', data);
    } catch (error) {
      console.error('LifeSwarm', 'Collection failed:', error);
    }
  }
  
  /**
   * 加载个人中心用户信息
   */
  private async loadProfileUserInfo() {
    try {
      this.userInfo = await this.authService.getCurrentUserAsync();
    } catch (err) {
      console.error('Failed to load user info:', err);
    }
  }
  
  /**
   * 处理登出
   */
  private async handleLogout() {
    try {
      // 调用认证服务登出
      const authService = getAuthService();
      await authService.logout();
      
      // 更新用户会话管理器
      const sessionManager = getUserSessionManager();
      await sessionManager.onUserLogout();
      
      console.info('[Index] 用户已登出');
      
      promptAction.showToast({ message: '已退出登录' });
      
      // 跳转到登录页
      router.replaceUrl({ url: 'pages/Login' });
      
    } catch (err) {
      const error = err as Error;
      console.error('[Index] 登出失败:', error.message);
      promptAction.showToast({ message: error.message });
    }
  }
  
  /**
 * 页面组件
 */
  private navigateTo(route: string): void {
    try {
      this.getUIContext().getRouter().pushUrl({ url: route });
    } catch (error) {
      console.error('LifeSwarm', 'Navigation failed:', error);
    }
  }
  
  build() {
    Tabs({ index: this.currentTabIndex }) {
      // 首页 Tab
      TabContent() {
        this.HomeTab()
      }
      .tabBar(this.TabBuilder(0, '首页', 'home'))
      
      // 洞察 Tab
      TabContent() {
        this.InsightsTab()
      }
      .tabBar(this.TabBuilder(1, '洞察', 'insight'))
      
      // AI Tab
      TabContent() {
        this.AITab()
      }
      .tabBar(this.TabBuilder(2, 'AI', 'ai'))
      
      // 我的 Tab
      TabContent() {
        this.ProfileTab()
      }
      .tabBar(this.TabBuilder(3, '我的', 'user'))
    }
    .width('100%')
    .height('100%')
    .barMode(BarMode.Fixed)
    .barPosition(BarPosition.End)
    .barBackgroundColor(Theme.Color.GlassHeavy)
    .barBackgroundBlurStyle(BlurStyle.Thin)
    .onChange((index: number) => {
      const previousIndex = this.currentTabIndex;
      this.currentTabIndex = index;
      
      if (previousIndex === 0 && index !== 0) {
        this.playEnterAnimation = false;
        this.showContent = false;
      }
      
      if (index === 0) {
        this.showContent = false;
        this.animationKey = Date.now();
        setTimeout(() => {
          this.playEnterAnimation = true;
          this.showContent = true;
        }, 50);
      }
    })
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }
  
  /**
   * Tab构建器 - HarmonyOS 6流体设计
   */
  @Builder
  TabBuilder(index: number, title: string, iconName: string) {
    Column({ space: 6 }) {
      // 图标容器
      Stack() {
        // 激活态背景
        if (this.currentTabIndex === index) {
          Circle({ width: 48, height: 48 })
            .fill(`linear-gradient(135deg, ${Theme.Gradient.Aurora[0]}, ${Theme.Gradient.Aurora[1]})`)
            .opacity(0.12)
            .scale({ x: 1, y: 1 })
        }
        
        // 专业图标
        SimpleIcon({
          iconName: iconName,
          iconSize: 24,
          color: this.currentTabIndex === index ? Theme.Color.Primary : Theme.Color.TextTertiary
        })
      }
      .width(48)
      .height(48)
      .alignContent(Alignment.Center)
      .scale({ 
        x: this.currentTabIndex === index ? 1.15 : 1, 
        y: this.currentTabIndex === index ? 1.15 : 1 
      })
      
      Text(title)
        .fontSize(Theme.Typography.Caption.size)
        .fontColor(this.currentTabIndex === index ? Theme.Color.Primary : Theme.Color.TextTertiary)
        .fontWeight(this.currentTabIndex === index ? 600 : 400)
        .opacity(this.currentTabIndex === index ? 1 : 0.7)
    }
    .width('100%')
    .height(68)
    .justifyContent(FlexAlign.Center)
    .animation({
      duration: Theme.Animation.Smooth.duration,
      curve: curves.springMotion()
    })
    .stateStyles({
      pressed: {
        .scale({ x: 0.92, y: 0.92 })
      },
      normal: {
        .scale({ x: 1, y: 1 })
      }
    })
  }

  /**
   * Tab - HarmonyOS 6 流体设计
   */
  @Builder
  HomeTab() {
    Stack() {
      // 1. 动态流体背景 - 3D粒子系统
      Canvas(this.navCanvasContext)
        .width('100%')
        .height('100%')
        .onReady(() => {
          this.navCanvasReady = true
          this.drawFluidBackground(this.navCanvasContext, 360, 800)
        })
        .opacity(0.5)
        .hitTestBehavior(HitTestMode.None)
      // 2. 主内容区域
      Scroll(this.homeScroller) {
        Column({ space: 32 }) {
          // 2.1 Hero区域 - 增强版
          Column({ space: 12 }) {
            // 主标题 - 渐变文字效果
            Text('LifeSwarm')
              .fontSize(Theme.Typography.DisplayLarge.size)
              .fontWeight(Theme.Typography.DisplayLarge.weight)
              .fontColor(Theme.Color.TextPrimary)
              .letterSpacing(Theme.Typography.DisplayLarge.letterSpacing)
              .lineHeight(Theme.Typography.DisplayLarge.lineHeight)
              .opacity(this.showContent ? 1 : 0)
              .scale({ x: this.showContent ? 1 : 0.9, y: this.showContent ? 1 : 0.9 })
              .animation({
                duration: 800,
                curve: curves.springMotion(),
                delay: 0
              })
            
            // 副标题 - 流体动画
            Text('智能生活 · 进化未来')
              .fontSize(Theme.Typography.HeadingSmall.size)
              .fontWeight(Theme.Typography.HeadingSmall.weight)
              .fontColor(Theme.Color.TextSecondary)
              .opacity(this.showContent ? 0.85 : 0)
              .translate({ y: this.showContent ? 0 : 10 })
              .animation({
                duration: 700,
                curve: Curve.Friction,
                delay: 150
              })
            
            // 状态指示器 - 呼吸动画
            Row({ space: 10 }) {
              Stack() {
                // 外圈呼吸光晕
                Circle({ width: 20, height: 20 })
                  .fill(this.systemStatus.isCollecting 
                    ? 'rgba(0, 200, 83, 0.2)' 
                    : 'rgba(189, 189, 189, 0.2)')
                  .scale({ 
                    x: this.showContent ? 1.5 : 1, 
                    y: this.showContent ? 1.5 : 1 
                  })
                  .opacity(this.showContent ? 0.5 : 0)
                  .animation({
                    duration: 1500,
                    curve: Curve.EaseInOut,
                    iterations: -1,
                    playMode: PlayMode.Alternate
                  })
                
                // 内圈状态点
                Circle({ width: 10, height: 10 })
                  .fill(this.systemStatus.isCollecting ? Theme.Color.Accent : '#BDBDBD')
              }
              .width(20)
              .height(20)
              
              Text(this.systemStatus.isCollecting ? '智能感知中' : '待机模式')
                .fontSize(Theme.Typography.BodySmall.size)
                .fontColor(Theme.Color.TextSecondary)
                .fontWeight(600)
            }
            .padding({ left: 16, right: 16, top: 8, bottom: 8 })
            .backgroundColor(Theme.Color.GlassMedium)
            .backdropBlur(Theme.Blur.Medium)
            .borderRadius(Theme.Radius.round)
            .margin({ top: 20 })
            .shadow(Theme.Shadow.Soft)
            .opacity(this.showContent ? 1 : 0)
            .translate({ y: this.showContent ? 0 : 15 })
            .animation({
              duration: 600,
              curve: Curve.Friction,
              delay: 300
            })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Start)
          .padding({ top: 64, left: Theme.Spacing.l, right: Theme.Spacing.l, bottom: 8 })

          // 2.2 Bento Grid布局 - 增强版卡片
          Grid() {
            // AI对话 (大卡片 - 2列宽)
            GridItem() {
              this.EnhancedBentoCard(
                'AI 对话',
                '智能助手',
                '基于 Qwen3.5-Plus 大模型',
                'pages/AIChat',
                Theme.Gradient.Aurora,
                'ai',
                true
              )
            }
            .columnStart(0)
            .columnEnd(1)
            .rowStart(0)
            .rowEnd(0)
            
            // 知识图谱
            GridItem() {
              this.EnhancedBentoCard(
                '知识图谱',
                '关系网络',
                '可视化知识结构',
                'pages/KnowledgeGraphCanvas',
                Theme.Gradient.Ocean,
                'network'
              )
            }
            .rowStart(1)
            .rowEnd(1)

            // 智能洞察
            GridItem() {
              this.EnhancedBentoCard(
                '智能洞察',
                '数据分析',
                '预测与建议',
                'pages/Dashboard',
                Theme.Gradient.Sunrise,
                'analytics'
              )
            }
            .rowStart(1)
            .rowEnd(1)

            // 元智能体
            GridItem() {
              this.EnhancedBentoCard(
                '元智能体',
                '协同进化',
                '多智能体协作',
                'pages/MetaAgentCoordination',
                Theme.Gradient.Nebula,
                'agent'
              )
            }
            .rowStart(2)
            .rowEnd(2)

            // 视觉识别
            GridItem() {
              this.EnhancedBentoCard(
                '视觉识别',
                'AI相机',
                '智能场景分析',
                'pages/Camera',
                Theme.Gradient.Mystic,
                'camera'
              )
            }
            .rowStart(2)
            .rowEnd(2)

            // 决策副本 (大卡片 - 2列宽)
            GridItem() {
              this.EnhancedBentoCard(
                '决策副本',
                '个性化闯关',
                '描述你的决策问题，AI生成个性化副本，像游戏一样探索未来',
                'pages/QuickDecisionInput',
                ['#9C27B0', '#E91E63'],
                'universe',
                true
              )
            }
            .columnStart(0)
            .columnEnd(1)
            .rowStart(3)
            .rowEnd(3)
          }
          .columnsTemplate('1fr 1fr')
          .rowsGap(Theme.Spacing.m)
          .columnsGap(Theme.Spacing.m)
          .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m })
          // 2.3 更多功能列表
          Column({ space: Theme.Spacing.m }) {
            Text('更多功能')
              .fontSize(Theme.Typography.HeadingMedium.size)
              .fontWeight(Theme.Typography.HeadingMedium.weight)
              .fontColor(Theme.Color.TextPrimary)
              .width('100%')
              .padding({ left: Theme.Spacing.s })
              .opacity(this.showContent ? 1 : 0)
              .translate({ x: this.showContent ? 0 : -20 })
              .animation({
                duration: 600,
                curve: Curve.Friction,
                delay: 500
              })

            this.EnhancedListCard('学习进化', '强化学习系统', 'pages/LearningProgress', Theme.Color.Accent, 'learning', 0)
            this.EnhancedListCard('生活领域', '6大维度洞察', 'pages/LifeDomainInsights', Theme.Color.Secondary, 'life', 1)
            this.EnhancedListCard('决策对比', '智能决策分析', 'pages/DecisionComparison', Theme.Color.Warning, 'comparison', 2)
            this.EnhancedListCard('平行宇宙', '未来12个月模拟', 'pages/ParallelUniverseSimulation', '#9C27B0', 'universe', 3)
          }
          .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m, bottom: 120 })
        }
        .width('100%')
      }
      .scrollBar(BarState.Off)
      .edgeEffect(EdgeEffect.Spring)
      .width('100%')
      .height('100%')
    }
    .width('100%')
    .height('100%')
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }

  /**
   * 增强版Bento卡片 - HarmonyOS 6流体设计
   */
  @Builder
  EnhancedBentoCard(
    title: string, 
    subtitle: string, 
    desc: string, 
    route: string, 
    colors: string[], 
    iconName: string,
    isLarge: boolean = false
  ) {
    Stack({ alignContent: Alignment.BottomStart }) {
      // 渐变背景层
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 135,
          colors: [
            [colors[0], 0.0],
            [colors[1], 1.0]
          ]
        })
        .opacity(0.12)
      
      // 动态光晕效果 - 左上角
      Circle({ width: 120, height: 120 })
        .fill(colors[0])
        .opacity(0.25)
        .blur(50)
        .position({ x: -30, y: -30 })
      
      // 动态光晕效果 - 右下角
      Circle({ width: 90, height: 90 })
        .fill(colors[1])
        .opacity(0.2)
        .blur(40)
        .position({ x: '75%', y: '70%' })

      // 内容层
      Column({ space: isLarge ? 12 : 8 }) {
        // 专业图标
        SimpleIcon({
          iconName: iconName,
          iconSize: isLarge ? 40 : 32,
          color: colors[0]
        })
        
        Column({ space: 4 }) {
          Text(title)
            .fontSize(isLarge ? Theme.Typography.HeadingLarge.size : Theme.Typography.HeadingMedium.size)
            .fontWeight(700)
            .fontColor(Theme.Color.TextPrimary)
          
          Text(subtitle)
            .fontSize(isLarge ? Theme.Typography.BodyLarge.size : Theme.Typography.BodyMedium.size)
            .fontWeight(500)
            .fontColor(Theme.Color.TextSecondary)
            .opacity(0.8)
          
          if (isLarge) {
            Text(desc)
              .fontSize(Theme.Typography.BodySmall.size)
              .fontColor(Theme.Color.TextTertiary)
              .margin({ top: 4 })
              .maxLines(2)
              .textOverflow({ overflow: TextOverflow.Ellipsis })
          }
        }
        .alignItems(HorizontalAlign.Start)
      }
      .padding(Theme.Spacing.l)
      .width('100%')
      .height('100%')
      .alignItems(HorizontalAlign.Start)
      .justifyContent(FlexAlign.End)
      
      // 箭头指示器
      Row() {
        Text('→')
          .fontSize(24)
          .fontColor(colors[1])
          .fontWeight(600)
      }
      .width(40)
      .height(40)
      .backgroundColor('rgba(255, 255, 255, 0.5)')
      .borderRadius(Theme.Radius.round)
      .justifyContent(FlexAlign.Center)
      .position({ x: '85%', y: '8%' })
      .translate({ x: '-50%' })
      .opacity(0.8)
    }
    .width('100%')
    .height(isLarge ? 200 : 160)
    .backgroundColor(Theme.Color.GlassHeavy)
    .backdropBlur(Theme.Blur.Heavy)
    .borderRadius(Theme.Radius.xl)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Medium)
    .onClick(() => {
      this.navigateTo(route)
    })
    .opacity(this.showContent ? 1 : 0)
    .scale({ 
      x: this.showContent ? 1 : 0.95, 
      y: this.showContent ? 1 : 0.95 
    })
    .animation({
      duration: 700,
      curve: curves.springMotion(),
      delay: 400
    })
    .stateStyles({
      pressed: {
        .scale({ x: 0.97, y: 0.97 })
        .opacity(0.9)
      },
      normal: {
        .scale({ x: 1, y: 1 })
        .opacity(1)
      }
    })
  }

  /**
   * 增强版列表卡片 - HarmonyOS 6设计
   */
  @Builder
  EnhancedListCard(title: string, desc: string, route: string, accentColor: string, iconName: string, index: number) {
    Row({ space: Theme.Spacing.m }) {
      // 图标容器
      Stack() {
        // 背景光晕
        Circle({ width: 56, height: 56 })
          .fill(accentColor)
          .opacity(0.15)
        
        // 专业图标
        SimpleIcon({
          iconName: iconName,
          iconSize: 28,
          color: accentColor
        })
      }
      .width(56)
      .height(56)

      Column({ space: 6 }) {
        Text(title)
          .fontSize(Theme.Typography.BodyLarge.size)
          .fontWeight(600)
          .fontColor(Theme.Color.TextPrimary)
        
        Text(desc)
          .fontSize(Theme.Typography.BodySmall.size)
          .fontColor(Theme.Color.TextTertiary)
      }
      .layoutWeight(1)
      .alignItems(HorizontalAlign.Start)

      // 箭头
      Row() {
        Text('→')
          .fontSize(20)
          .fontColor(Theme.Color.TextTertiary)
      }
      .width(32)
      .height(32)
      .backgroundColor('rgba(0, 0, 0, 0.03)')
      .borderRadius(Theme.Radius.round)
      .justifyContent(FlexAlign.Center)
    }
    .width('100%')
    .padding(Theme.Spacing.m)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .onClick(() => {
      this.navigateTo(route)
    })
    .opacity(this.showContent ? 1 : 0)
    .translate({ x: this.showContent ? 0 : -30 })
    .animation({
      duration: 600,
      curve: Curve.Friction,
      delay: 600 + index * 100
    })
    .stateStyles({
      pressed: {
        .scale({ x: 0.98, y: 0.98 })
        .backgroundColor('#F8F9FA')
      },
      normal: {
        .scale({ x: 1, y: 1 })
        .backgroundColor(Theme.Color.BackgroundSecondary)
      }
    })
  }
  
  /**
   * Tab - 6
   */
  @Builder
  InsightsTab() {
    Stack() {
      // 处理逻辑
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor(Theme.Color.BackgroundPrimary)
      
      Scroll() {
        Column({ space: 24 }) {
          // 处理逻辑
          Text('')
            .fontSize(32)
            .fontWeight(800)
            .fontColor(Theme.Color.TextPrimary)
            .width('100%')
            .padding({ left: 24, top: 24 })
          
          // 处理逻辑
          Flex({ wrap: FlexWrap.Wrap, justifyContent: FlexAlign.SpaceBetween }) {
            //  ()
            Column() {
              this.InsightCard(
                '',
                '',
                '',
                'pages/Dashboard',
                Theme.Gradient.Sunrise
              )
            }
            .width('100%')
            .margin({ bottom: 16 })
            
            //  ()
            Column() {
              this.InsightCard(
                '',
                '6',
                '',
                'pages/LifeDomainInsights',
                Theme.Gradient.Aurora
              )
            }
            .width('48%')
            .margin({ bottom: 16 })
            
            //  ()
            Column() {
              this.InsightCard(
                '',
                '',
                '',
                'pages/DecisionComparison',
                Theme.Gradient.Mint
              )
            }
            .width('48%')
            .margin({ bottom: 16 })
            
            //  ()
            Column() {
              this.InsightCard(
                '',
                '',
                '',
                'pages/LearningProgress',
                Theme.Gradient.Mint
              )
            }
            .width('100%')
            .margin({ bottom: 100 })
          }
          .padding({ left: 16, right: 16 })
        }
        .width('100%')
      }
      .scrollBar(BarState.Off)
      .edgeEffect(EdgeEffect.Spring)
    }
    .width('100%')
    .height('100%')
  }
  
  /**
   * AITab - 流式AI对话
   */
  @Builder
  AITab() {
    Column() {
      // AI对话快捷入口
      Button('开始 AI 对话')
        .width('90%')
        .height(56)
        .fontSize(18)
        .fontColor(Theme.Color.TextWhite)
        .backgroundColor(Theme.Color.Primary)
        .borderRadius(Theme.Radius.l)
        .margin({ top: 100 })
        .onClick(() => {
          router.pushUrl({ url: 'pages/AIChat' });
        })
      
      Text('点击开始与 AI 助手对话')
        .fontSize(14)
        .fontColor(Theme.Color.TextSecondary)
        .margin({ top: 16 })
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
  }
  
  /**
   * Tab - 个人中心 - HarmonyOS 6 流体设计（完整版）
   */
  @Builder
  ProfileTab() {
    Stack() {
      // 背景
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor(Theme.Color.BackgroundPrimary)
      
      // 主内容
      if (this.userInfo) {
        Scroll(this.profileScroller) {
          Column({ space: 24 }) {
            // 用户卡片 - Hero区域
            this.buildUserCard()
            
            // 统计数据区域
            this.buildStatsSection()
            
            // 功能菜单
            this.buildMenuSection()
            
            // 底部操作
            this.buildActionButtons()
          }
          .width('100%')
          .padding({ left: 16, right: 16, bottom: 100 })
        }
        .scrollBar(BarState.Off)
        .edgeEffect(EdgeEffect.Spring)
        .layoutWeight(1)
      } else {
        // 未登录状态
        Column() {
          SimpleIcon({
            iconName: 'user',
            iconSize: 64,
            color: Theme.Color.TextTertiary
          })
          
          Text('未登录')
            .fontSize(18)
            .fontColor(Theme.Color.TextSecondary)
            .margin({ top: 16, bottom: 20 })
          
          Button('去登录')
            .width(200)
            .height(48)
            .fontSize(16)
            .fontColor('#ffffff')
            .backgroundColor(Theme.Color.Primary)
            .borderRadius(Theme.Radius.l)
            .onClick(() => {
              router.pushUrl({ url: 'pages/Login' });
            })
        }
        .width('100%')
        .layoutWeight(1)
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      }
    }
    .width('100%')
    .height('100%')
  }
  
  /**
   * 用户卡片 - HarmonyOS 6 流体设计
   */
  @Builder
  buildUserCard() {
    Stack({ alignContent: Alignment.BottomStart }) {
      // 渐变背景
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 135,
          colors: [
            ['#667eea', 0.0],
            ['#764ba2', 1.0]
          ]
        })
        .opacity(0.12)
      
      // 光晕效果
      Circle({ width: 150, height: 150 })
        .fill('#667eea')
        .opacity(0.2)
        .blur(60)
        .position({ x: -40, y: -40 })
      
      Circle({ width: 100, height: 100 })
        .fill('#764ba2')
        .opacity(0.15)
        .blur(50)
        .position({ x: '80%', y: '60%' })
      
      // 内容
      Row({ space: 16 }) {
        // 头像
        Stack() {
          Circle({ width: 80, height: 80 })
            .fill(`linear-gradient(135deg, #667eea, #764ba2)`)
          
          Text(this.userInfo!.nickname.substring(0, 1).toUpperCase())
            .fontSize(36)
            .fontWeight(FontWeight.Bold)
            .fontColor('#ffffff')
        }
        .width(80)
        .height(80)
        
        // 用户信息
        Column({ space: 8 }) {
          Text(this.userInfo!.nickname)
            .fontSize(24)
            .fontWeight(700)
            .fontColor(Theme.Color.TextPrimary)
          
          Text(`@${this.userInfo!.username}`)
            .fontSize(14)
            .fontColor(Theme.Color.TextSecondary)
          
          Row({ space: 8 }) {
            Circle({ width: 8, height: 8 })
              .fill('#00C853')
            
            Text('在线')
              .fontSize(12)
              .fontColor(Theme.Color.TextTertiary)
          }
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)
      }
      .padding(20)
      .width('100%')
    }
    .width('100%')
    .height(160)
    .backgroundColor(Theme.Color.GlassHeavy)
    .backdropBlur(Theme.Blur.Heavy)
    .borderRadius(Theme.Radius.xl)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Medium)
    .opacity(this.profileShowContent ? 1 : 0)
    .scale({ x: this.profileShowContent ? 1 : 0.95, y: this.profileShowContent ? 1 : 0.95 })
    .animation({
      duration: 700,
      curve: Curve.Smooth,
      delay: 0
    })
  }
  
  /**
   * 统计数据区域
   */
  @Builder
  buildStatsSection() {
    Row({ space: 12 }) {
      this.buildStatItem('数据收集', '已启用', '#00C853')
      this.buildStatItem('账号等级', 'VIP', '#FFB800')
      this.buildStatItem('连续登录', '7天', '#FF6B6B')
    }
    .width('100%')
    .opacity(this.profileShowContent ? 1 : 0)
    .translate({ y: this.profileShowContent ? 0 : 20 })
    .animation({
      duration: 600,
      curve: Curve.Smooth,
      delay: 100
    })
  }
  
  /**
   * 统计项
   */
  @Builder
  buildStatItem(label: string, value: string, color: string) {
    Column({ space: 8 }) {
      Text(value)
        .fontSize(18)
        .fontWeight(700)
        .fontColor(color)
      
      Text(label)
        .fontSize(12)
        .fontColor(Theme.Color.TextTertiary)
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .alignItems(HorizontalAlign.Center)
  }
  
  /**
   * 功能菜单区域
   */
  @Builder
  buildMenuSection() {
    Column({ space: 12 }) {
      Text('功能设置')
        .fontSize(16)
        .fontWeight(600)
        .fontColor(Theme.Color.TextPrimary)
        .padding({ left: 8 })
        .opacity(this.profileShowContent ? 1 : 0)
        .translate({ x: this.profileShowContent ? 0 : -20 })
        .animation({
          duration: 600,
          curve: Curve.Smooth,
          delay: 200
        })
      
      ForEach(this.profileMenuItems, (item: ProfileMenuItem, index: number) => {
        this.buildMenuItem(item, index)
      }, (item: ProfileMenuItem) => item.id)
    }
    .width('100%')
  }
  
  /**
   * 菜单项
   */
  @Builder
  buildMenuItem(item: ProfileMenuItem, index: number) {
    Row({ space: 12 }) {
      // 图标容器
      Stack() {
        Circle({ width: 48, height: 48 })
          .fill(item.color)
          .opacity(0.15)
        
        SimpleIcon({
          iconName: item.icon,
          iconSize: 24,
          color: item.color
        })
      }
      .width(48)
      .height(48)
      
      // 文本内容
      Column({ space: 4 }) {
        Text(item.title)
          .fontSize(16)
          .fontWeight(600)
          .fontColor(Theme.Color.TextPrimary)
        
        Text(item.subtitle)
          .fontSize(12)
          .fontColor(Theme.Color.TextTertiary)
      }
      .alignItems(HorizontalAlign.Start)
      .layoutWeight(1)
      
      // 箭头
      Text('→')
        .fontSize(20)
        .fontColor(Theme.Color.TextTertiary)
        .translate({ x: this.profileSelectedMenu === index ? 4 : 0 })
        .animation({
          duration: 300,
          curve: Curve.Smooth
        })
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .onClick(() => {
      this.profileSelectedMenu = index;
      if (item.action) {
        item.action();
      }
      setTimeout(() => {
        this.profileSelectedMenu = -1;
      }, 300);
    })
    .opacity(this.profileShowContent ? 1 : 0)
    .translate({ x: this.profileShowContent ? 0 : -30 })
    .animation({
      duration: 600,
      curve: Curve.Smooth,
      delay: 300 + index * 80
    })
    .stateStyles({
      pressed: {
        .scale({ x: 0.98, y: 0.98 })
        .backgroundColor('#F8F9FA')
      },
      normal: {
        .scale({ x: 1, y: 1 })
        .backgroundColor(Theme.Color.BackgroundSecondary)
      }
    })
  }
  
  /**
   * 底部操作按钮
   */
  @Builder
  buildActionButtons() {
    Column({ space: 12 }) {
      // 退出登录按钮
      Button('退出登录')
        .width('100%')
        .height(52)
        .fontSize(16)
        .fontWeight(600)
        .fontColor('#ffffff')
        .backgroundColor('#FF3B30')
        .borderRadius(Theme.Radius.l)
        .shadow({
          radius: 8,
          color: 'rgba(255, 59, 48, 0.3)',
          offsetY: 4
        })
        .onClick(() => {
          this.handleLogout();
        })
        .opacity(this.profileShowContent ? 1 : 0)
        .translate({ y: this.profileShowContent ? 0 : 30 })
        .animation({
          duration: 600,
          curve: Curve.Smooth,
          delay: 500
        })
      
      // 版本信息
      Row() {
        Text('LifeSwarm v1.0.0')
          .fontSize(12)
          .fontColor(Theme.Color.TextTertiary)
      }
      .width('100%')
      .height(40)
      .justifyContent(FlexAlign.Center)
      .opacity(this.profileShowContent ? 1 : 0)
      .animation({
        duration: 600,
        curve: Curve.Smooth,
        delay: 550
      })
    }
    .width('100%')
    .padding({ top: 20 })
  }
  
  /**
   *  - 6
   */
  @Builder
  InsightCard(title: string, subtitle: string, description: string, route: string, gradient: string[]) {
    Stack({ alignContent: Alignment.TopStart }) {
      // 处理逻辑
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 135,
          colors: [
            [gradient[0], 0.0],
            [gradient[1], 1.0]
          ]
        })
        .opacity(0.08) // 处理逻辑
        .borderRadius(20)

      // 处理逻辑
      Circle({ width: 60, height: 60 })
        .fill(gradient[0])
        .opacity(0.15)
        .blur(30)
        .position({ x: -10, y: -10 })

      Column({ space: 12 }) {
        Row() {
          Column({ space: 4 }) {
            Text(title)
              .fontSize(20)
              .fontWeight(700)
              .fontColor('#1A1A1A')
            
            Text(subtitle)
              .fontSize(14)
              .fontWeight(500)
              .fontColor(gradient[0]) // 处理逻辑
              .opacity(0.8)
          }
          .alignItems(HorizontalAlign.Start)
          .layoutWeight(1)
          
          // 处理逻辑
          Text('→')
            .fontSize(24)
            .fontColor(gradient[1])
            .opacity(0.8)
        }
        .width('100%')
        
        Text(description)
          .fontSize(15)
          .fontColor('#555555')
          .lineHeight(24)
          .opacity(0.9)
      }
      .padding(24)
      .width('100%')
    }
    .width('100%')
    .backgroundColor('rgba(255, 255, 255, 0.9)')
    .backdropBlur(20)
    .borderRadius(20)
    .shadow({
      radius: 10,
      color: 'rgba(0, 0, 0, 0.04)',
      offsetX: 0,
      offsetY: 4
    })
    .onClick(() => {
      this.navigateTo(route)
    })
    .animation({
      duration: 300,
      curve: Curve.Smooth
    })
  }
  
  /**
   *  - 6
   */
  @Builder
  SettingItem(title: string, route: string, isTop: boolean) {
    Row() {
      Text(title)
        .fontSize(16)
        .fontWeight(500)
        .fontColor('#1A1A1A')
        .layoutWeight(1)
      
      Text('→')
        .fontSize(20)
        .fontColor('#CCCCCC')
    }
    .width('100%')
    .height(60)
    .padding({ left: 20, right: 20 })
    .backgroundColor('transparent') // 处理逻辑
    .onClick(() => {
      this.navigateTo(route)
    })
    .stateStyles({
      pressed: {
        .backgroundColor('rgba(0, 0, 0, 0.05)')
      },
      normal: {
        .backgroundColor('transparent')
      }
    })
  }
  
  /**
   *  - 6 + 
   */
  @Builder
  MinimalFeatureCard(feature: FeatureCard, index: number) {
    Column({ space: 12 }) {
      Row() {
        Column({ space: 4 }) {
          Text(feature.title)
            .fontSize(20)
            .fontWeight(600)
            .fontColor('#000000')
          
          Text(feature.subtitle)
            .fontSize(14)
            .fontColor('#999999')
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)
        
        Text('→')
          .fontSize(24)
          .fontColor('#007AFF')
          .translate({ x: this.selectedFeature === index ? 5 : 0 })
          .animation({
            duration: 300,
            curve: Curve.Smooth
          })
      }
      .width('100%')
      
      Text(feature.description)
        .fontSize(14)
        .fontColor('#666666')
        .lineHeight(22)
    }
    .width('100%')
    .padding(20)
    .backgroundColor(this.selectedFeature === index ? '#F8F8F8' : '#FFFFFF')
    .borderRadius(12)
    .border({
      width: 1,
      color: this.selectedFeature === index ? '#007AFF' : '#E0E0E0'
    })
    .scale({ 
      x: this.selectedFeature === index ? 0.98 : 1, 
      y: this.selectedFeature === index ? 0.98 : 1 
    })
    .shadow({
      radius: this.selectedFeature === index ? 8 : 0,
      color: 'rgba(0, 122, 255, 0.1)',
      offsetX: 0,
      offsetY: 4
    })
    .opacity(this.showContent ? 1 : 0)
    .translate({ x: this.showContent ? 0 : -30 })
    .animation(this.buildEnterAnimation(800, 0))
    .onClick(() => {
      this.selectedFeature = index;
      setTimeout(() => {
        this.navigateTo(feature.route);
        this.selectedFeature = -3;
      }, 200);
    })
  }
}
