/**
 *  - HarmonyOS 6 
 * 
 */
import { router } from '@kit.ArkUI';
import { curves } from '@kit.ArkUI';
import { HttpUtil } from '../utils/HttpUtil';
import { Theme } from '../common/Theme';
import { SimpleIcon } from '../components/IconRenderer';

// 数据类型定义
class HealthRequestData {
  sleep_hours: number = 0;
  exercise_minutes: number = 0;
  stress_level: number = 0;
}

class ContextRequestData {
  time_slot: string = '';
  location: string = '';
}

class UserRequestData {
  health: HealthRequestData = new HealthRequestData();
  context: ContextRequestData = new ContextRequestData();
}

class AnalysisRequestData {
  user_id: string = '';
  user_data: UserRequestData = new UserRequestData();
}

/**
 * 页面组件
 */
interface AgentStatus {
  id: string;
  name: string;
  status: 'idle' | 'thinking' | 'done';
  progress: number;
  result?: number;
  confidence?: number;
}

/**
 * 页面组件
 */
type CoordinationPhase = 'input' | 'analyzing' | 'coordinating' | 'result';

@Entry
@Component
struct MetaAgentCoordination {
  @State currentPhase: CoordinationPhase = 'input';
  @State agents: AgentStatus[] = [];
  @State finalResult: number = 0;
  @State finalConfidence: number = 0;
  @State reasoning: string = '';
  @State showContent: boolean = false;
  
  // 处理逻辑
  @State sleepHours: number = 7;
  @State exerciseMinutes: number = 30;
  @State stressLevel: number = 5;
  
  aboutToAppear(): void {
    this.initializeAgents();
    setTimeout(() => {
      this.showContent = true;
    }, 100);
  }
  
  /**
   * 初始化智能体
   */
  private initializeAgents(): void {
    this.agents = [
      { id: 'sleep_agent', name: '睡眠分析', status: 'idle', progress: 0 },
      { id: 'exercise_agent', name: '运动评估', status: 'idle', progress: 0 },
      { id: 'stress_agent', name: '压力监测', status: 'idle', progress: 0 },
      { id: 'llm_agent_1', name: 'AI推理-1', status: 'idle', progress: 0 },
      { id: 'llm_agent_2', name: 'AI推理-2', status: 'idle', progress: 0 },
      { id: 'llm_agent_3', name: 'AI推理-3', status: 'idle', progress: 0 }
    ];
  }
  
  /**
 * 页面组件
 */
  private async startAnalysis(): Promise<void> {
    // 1
    this.currentPhase = 'input';
    await this.delay(500);
    
    // 2
    this.currentPhase = 'analyzing';
    await this.simulateAgentAnalysis();
    
    // 3
    this.currentPhase = 'coordinating';
    await this.delay(1000);
    
    // API
    await this.callMetaAgentAPI();
    
    // 4
    this.currentPhase = 'result';
  }
  
  /**
 * 页面组件
 */
  private async simulateAgentAnalysis(): Promise<void> {
    // 处理逻辑
    const promises = this.agents.map(async (agent, index) => {
      agent.status = 'thinking';
      
      // 处理逻辑
      for (let i = 0; i <= 100; i += 10) {
        agent.progress = i;
        await this.delay(100 + index * 20);
      }
      
      agent.status = 'done';
      agent.result = 7 + Math.random() * 2;
      agent.confidence = 0.7 + Math.random() * 0.2;
    });
    
    await Promise.all(promises);
  }
  
  /**
   * API
   */
  private async callMetaAgentAPI(): Promise<void> {
    try {
      const healthData = new HealthRequestData();
      healthData.sleep_hours = this.sleepHours;
      healthData.exercise_minutes = this.exerciseMinutes;
      healthData.stress_level = this.stressLevel;
      
      const contextData = new ContextRequestData();
      contextData.time_slot = 'evening';
      contextData.location = 'home';
      
      const userData = new UserRequestData();
      userData.health = healthData;
      userData.context = contextData;
      
      const requestData = new AnalysisRequestData();
      requestData.user_id = 'default_user';
      requestData.user_data = userData;
      
      const response = await HttpUtil.post('/api/v4/meta-agent/analyze', requestData);
      
      if (response.responseCode === 200) {
        const data = HttpUtil.parseResponse<Record<string, Object>>(response);
        
        if (data.success) {
          const analysis = data.analysis as Record<string, Object>;
          this.finalResult = analysis.final_decision as number;
          this.finalConfidence = analysis.confidence as number;
          this.reasoning = analysis.reasoning as string;
        }
      }
      
    } catch (error) {
      console.error('MetaAgentCoordination', 'API call failed:', error);
      // 使用模拟数据
      this.finalResult = 7.5;
      this.finalConfidence = 0.85;
      this.reasoning = '基于当前睡眠、运动和压力水平，预测你的整体健康状态良好。建议保持当前的运动习惯，并适当增加深度睡眠时间。';
    }
  }
  
  /**
 * 页面组件
 */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  /**
 * 页面组件
 */
  private resetAnalysis(): void {
    this.currentPhase = 'input';
    this.initializeAgents();
    this.finalResult = 0;
    this.finalConfidence = 0;
    this.reasoning = '';
  }
  
  build() {
    Stack() {
      // 1. 背景层 - 动态渐变
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor(Theme.Color.BackgroundPrimary)
        
      // 装饰性光晕 - 左上
      Circle({ width: 320, height: 320 })
        .fill('rgba(10, 89, 247, 0.1)')
        .blur(70)
        .position({ x: -60, y: -60 })
        
      // 装饰性光晕 - 右中
      Circle({ width: 280, height: 280 })
        .fill('rgba(0, 200, 83, 0.08)')
        .blur(60)
        .position({ x: '85%', y: '25%' })

      Column() {
        // 2. 顶部导航栏
        Row() {
          Row({ space: 16 }) {
            Button({ type: ButtonType.Circle, stateEffect: true }) {
              SimpleIcon({
                iconName: 'back',
                iconSize: 20,
                color: Theme.Color.TextPrimary
              })
            }
            .width(44)
            .height(44)
            .backgroundColor(Theme.Color.GlassLight)
            .backdropBlur(Theme.Blur.Medium)
            .onClick(() => router.back())
            
            Column({ space: 4 }) {
              Text('元智能体')
                .fontSize(Theme.Typography.HeadingMedium.size)
                .fontWeight(Theme.Typography.HeadingMedium.weight)
                .fontColor(Theme.Color.TextPrimary)
              
              Text('多智能体协同进化')
                .fontSize(Theme.Typography.Caption.size)
                .fontColor(Theme.Color.TextSecondary)
            }
            .alignItems(HorizontalAlign.Start)
          }
          
          Blank()
          
          Button({ type: ButtonType.Circle, stateEffect: true }) {
            SimpleIcon({
              iconName: 'settings',
              iconSize: 20,
              color: Theme.Color.TextPrimary
            })
          }
          .width(44)
          .height(44)
          .backgroundColor(Theme.Color.GlassLight)
          .backdropBlur(Theme.Blur.Medium)
        }
        .width('100%')
        .height(64)
        .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m })
        .backgroundColor(Theme.Color.GlassHeavy)
        .backdropBlur(Theme.Blur.Heavy)
        .zIndex(100)
        .opacity(this.showContent ? 1 : 0)
        .translate({ y: this.showContent ? 0 : -20 })
        .animation({
          duration: 600,
          curve: Curve.Friction
        })
        
        Scroll() {
          Column({ space: Theme.Spacing.xl }) {
            // 3. 阶段指示器 - 增强版
            Row({ space: 6 }) {
              this.EnhancedPhaseIndicator('输入', this.currentPhase === 'input', 0)
              this.PhaseConnector(this.currentPhase !== 'input')
              this.EnhancedPhaseIndicator('分析', this.currentPhase === 'analyzing', 1)
              this.PhaseConnector(this.currentPhase === 'coordinating' || this.currentPhase === 'result')
              this.EnhancedPhaseIndicator('协调', this.currentPhase === 'coordinating', 2)
              this.PhaseConnector(this.currentPhase === 'result')
              this.EnhancedPhaseIndicator('结果', this.currentPhase === 'result', 3)
            }
            .width('100%')
            .padding({ top: Theme.Spacing.l, bottom: Theme.Spacing.s })
            .justifyContent(FlexAlign.Center)
            .opacity(this.showContent ? 1 : 0)
            .animation({
              duration: 600,
              delay: 100
            })
            
            // 4. 输入参数卡片
            if (this.currentPhase === 'input') {
              Column({ space: Theme.Spacing.l }) {
                Text('参数配置')
                  .fontSize(Theme.Typography.HeadingMedium.size)
                  .fontWeight(Theme.Typography.HeadingMedium.weight)
                  .fontColor(Theme.Color.TextPrimary)
                  .width('100%')
                
                Column({ space: Theme.Spacing.xl }) {
                  this.EnhancedInputSlider('睡眠时间', `${this.sleepHours.toFixed(1)} 小时`, this.sleepHours, 0, 12, 0.5, Theme.Gradient.Aurora, (val) => this.sleepHours = val)
                  this.EnhancedInputSlider('运动时间', `${this.exerciseMinutes.toFixed(0)} 分钟`, this.exerciseMinutes, 0, 120, 5, Theme.Gradient.Mint, (val) => this.exerciseMinutes = val)
                  this.EnhancedInputSlider('压力水平', `${this.stressLevel.toFixed(0)} / 10`, this.stressLevel, 0, 10, 1, Theme.Gradient.Sunrise, (val) => this.stressLevel = val)
                }
                .padding(Theme.Spacing.xl)
                .backgroundColor(Theme.Color.GlassHeavy)
                .backdropBlur(Theme.Blur.Heavy)
                .borderRadius(Theme.Radius.xl)
                .border({ width: 1, color: Theme.Color.BorderLight })
                .shadow(Theme.Shadow.Medium)
                
                Button('开始协同分析')
                  .width('100%')
                  .height(56)
                  .fontSize(Theme.Typography.HeadingSmall.size)
                  .fontWeight(Theme.Typography.HeadingSmall.weight)
                  .fontColor(Theme.Color.TextWhite)
                  .backgroundColor(Theme.Color.Primary)
                  .borderRadius(Theme.Radius.round)
                  .shadow(Theme.Shadow.GlowPrimary)
                  .onClick(() => this.startAnalysis())
                  .stateStyles({
                    pressed: {
                      .scale({ x: 0.98, y: 0.98 })
                    },
                    normal: {
                      .scale({ x: 1, y: 1 })
                    }
                  })
              }
              .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m })
              .transition({ type: TransitionType.Insert, opacity: 0, translate: { y: 20 } })
            }
            
            // 5. 智能体分析过程
            if (this.currentPhase === 'analyzing' || this.currentPhase === 'coordinating' || this.currentPhase === 'result') {
              Column({ space: Theme.Spacing.m }) {
                Text('智能体集群')
                  .fontSize(Theme.Typography.HeadingMedium.size)
                  .fontWeight(Theme.Typography.HeadingMedium.weight)
                  .fontColor(Theme.Color.TextPrimary)
                  .width('100%')
                  .padding({ left: Theme.Spacing.m })
                
                Grid() {
                  ForEach(this.agents, (agent: AgentStatus, idx: number) => {
                    GridItem() {
                      this.EnhancedAgentCard(agent, idx)
                    }
                  })
                }
                .columnsTemplate('1fr 1fr')
                .rowsGap(Theme.Spacing.m)
                .columnsGap(Theme.Spacing.m)
                .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m })
                .height(360)
              }
              .transition({ type: TransitionType.Insert, opacity: 0, translate: { y: 20 } })
            }
            
            // 6. 协调过程动画
            if (this.currentPhase === 'coordinating') {
              Column({ space: Theme.Spacing.l }) {
                Stack() {
                  // 外圈脉冲
                  Circle({ width: 80, height: 80 })
                    .fill('rgba(10, 89, 247, 0.1)')
                    .scale({ x: 1.5, y: 1.5 })
                    .opacity(0.5)
                    .animation({
                      duration: 1500,
                      curve: Curve.EaseInOut,
                      iterations: -1,
                      playMode: PlayMode.Alternate
                    })
                  
                  // 中圈
                  Circle({ width: 60, height: 60 })
                    .fill('rgba(10, 89, 247, 0.2)')
                  
                  // 加载指示器
                  LoadingProgress()
                    .width(48)
                    .height(48)
                    .color(Theme.Color.Primary)
                }
                .width(80)
                .height(80)
                
                Text('元智能体正在整合决策...')
                  .fontSize(Theme.Typography.BodyLarge.size)
                  .fontWeight(500)
                  .fontColor(Theme.Color.TextSecondary)
              }
              .width('100%')
              .height(180)
              .justifyContent(FlexAlign.Center)
              .transition({ type: TransitionType.Insert, opacity: 0, scale: { x: 0.9, y: 0.9 } })
            }
            
            // 7. 最终结果卡片
            if (this.currentPhase === 'result') {
              Column({ space: Theme.Spacing.xl }) {
                Text('最终决策')
                  .fontSize(Theme.Typography.HeadingMedium.size)
                  .fontWeight(Theme.Typography.HeadingMedium.weight)
                  .fontColor(Theme.Color.TextPrimary)
                  .width('100%')
                
                Column({ space: Theme.Spacing.l }) {
                  Row({ space: 48 }) {
                    Column({ space: 8 }) {
                      Text('综合评分')
                        .fontSize(Theme.Typography.BodySmall.size)
                        .fontColor(Theme.Color.TextSecondary)
                      Text(this.finalResult.toFixed(1))
                        .fontSize(52)
                        .fontWeight(900)
                        .fontColor(Theme.Color.Primary)
                    }
                    
                    Column({ space: 8 }) {
                      Text('置信度')
                        .fontSize(Theme.Typography.BodySmall.size)
                        .fontColor(Theme.Color.TextSecondary)
                      Text(`${(this.finalConfidence * 100).toFixed(0)}%`)
                        .fontSize(52)
                        .fontWeight(900)
                        .fontColor(Theme.Color.Accent)
                    }
                  }
                  .width('100%')
                  .justifyContent(FlexAlign.Center)
                  
                  Divider().color(Theme.Color.BorderLight)
                  
                  Text(this.reasoning)
                    .fontSize(Theme.Typography.BodyLarge.size)
                    .fontColor(Theme.Color.TextPrimary)
                    .lineHeight(28)
                    .width('100%')
                }
                .padding(Theme.Spacing.xl)
                .backgroundColor(Theme.Color.GlassHeavy)
                .backdropBlur(Theme.Blur.Heavy)
                .borderRadius(Theme.Radius.xl)
                .border({ width: 1, color: Theme.Color.BorderLight })
                .shadow(Theme.Shadow.Floating)
                
                Button('重新分析')
                  .width('100%')
                  .height(56)
                  .fontSize(Theme.Typography.HeadingSmall.size)
                  .fontWeight(Theme.Typography.HeadingSmall.weight)
                  .fontColor(Theme.Color.Primary)
                  .backgroundColor('rgba(10, 89, 247, 0.1)')
                  .borderRadius(Theme.Radius.round)
                  .onClick(() => this.resetAnalysis())
              }
              .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m, bottom: 60 })
              .transition({ type: TransitionType.Insert, opacity: 0, translate: { y: 50 } })
            }
          }
          .width('100%')
        }
        .layoutWeight(1)
        .scrollBar(BarState.Off)
        .edgeEffect(EdgeEffect.Spring)
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }
  
  @Builder
  EnhancedPhaseIndicator(label: string, active: boolean, index: number) {
    Column({ space: 8 }) {
      Stack() {
        // 外圈光晕
        if (active) {
          Circle({ width: 24, height: 24 })
            .fill(Theme.Color.Primary)
            .opacity(0.2)
            .scale({ x: 1.5, y: 1.5 })
            .animation({
              duration: 1200,
              curve: Curve.EaseInOut,
              iterations: -1,
              playMode: PlayMode.Alternate
            })
        }
        
        // 指示点
        Circle({ width: 14, height: 14 })
          .fill(active ? Theme.Color.Primary : Theme.Color.BorderMedium)
          .shadow(active ? Theme.Shadow.Glow : undefined)
      }
      .width(24)
      .height(24)
      
      Text(label)
        .fontSize(Theme.Typography.Caption.size)
        .fontWeight(active ? 600 : 400)
        .fontColor(active ? Theme.Color.Primary : Theme.Color.TextTertiary)
    }
    .opacity(this.showContent ? 1 : 0)
    .scale({ 
      x: this.showContent ? 1 : 0.8, 
      y: this.showContent ? 1 : 0.8 
    })
    .animation({
      duration: 500,
      curve: curves.springMotion(),
      delay: index * 100
    })
  }

  @Builder
  PhaseConnector(completed: boolean) {
    Divider()
      .width(28)
      .color(completed ? Theme.Color.Primary : Theme.Color.BorderMedium)
      .strokeWidth(2)
      .margin({ top: 8 })
      .animation({
        duration: 400,
        curve: Curve.EaseOut
      })
  }
  
  @Builder
  EnhancedInputSlider(
    label: string, 
    valueText: string, 
    value: number, 
    min: number, 
    max: number, 
    step: number, 
    gradient: string[], 
    onChange: (val: number) => void
  ) {
    Column({ space: 12 }) {
      Row() {
        Text(label)
          .fontSize(Theme.Typography.BodyLarge.size)
          .fontWeight(500)
          .fontColor(Theme.Color.TextPrimary)
        Blank()
        Text(valueText)
          .fontSize(Theme.Typography.BodyLarge.size)
          .fontWeight(700)
          .fontColor(gradient[0])
      }
      .width('100%')
      
      Slider({
        value: value,
        min: min,
        max: max,
        step: step
      })
        .width('100%')
        .trackColor(Theme.Color.BackgroundTertiary)
        .selectedColor(gradient[0])
        .blockColor(Theme.Color.BackgroundSecondary)
        .trackThickness(8)
        .blockSize({ width: 24, height: 24 })
        .onChange(onChange)
    }
  }
  
  @Builder
  EnhancedAgentCard(agent: AgentStatus, index: number) {
    Column({ space: 12 }) {
      Row() {
        Text(agent.name)
          .fontSize(Theme.Typography.BodyMedium.size)
          .fontWeight(600)
          .fontColor(Theme.Color.TextPrimary)
        Blank()
        if (agent.status === 'thinking') {
          LoadingProgress()
            .width(18)
            .height(18)
            .color(Theme.Color.Primary)
        } else if (agent.status === 'done') {
          Stack() {
            Circle({ width: 20, height: 20 })
              .fill(Theme.Color.Accent)
              .opacity(0.15)
            SimpleIcon({
              iconName: 'chat',
              iconSize: 12,
              color: Theme.Color.Accent
            })
          }
        }
      }
      .width('100%')
      
      if (agent.status !== 'idle') {
        Progress({
          value: agent.progress,
          total: 100,
          type: ProgressType.Linear
        })
          .width('100%')
          .height(6)
          .color(agent.status === 'done' ? Theme.Color.Accent : Theme.Color.Primary)
          .backgroundColor(Theme.Color.BackgroundTertiary)
          .borderRadius(Theme.Radius.xs)
        
        if (agent.result !== undefined) {
          Row() {
            Text(`评分: ${agent.result.toFixed(1)}`)
              .fontSize(Theme.Typography.BodySmall.size)
              .fontColor(Theme.Color.TextSecondary)
            Blank()
            Text(`${((agent.confidence || 0) * 100).toFixed(0)}%`)
              .fontSize(Theme.Typography.BodySmall.size)
              .fontColor(Theme.Color.TextTertiary)
          }
          .width('100%')
        }
      } else {
        Text('等待中...')
          .fontSize(Theme.Typography.BodySmall.size)
          .fontColor(Theme.Color.TextTertiary)
          .margin({ top: 8 })
      }
    }
    .width('100%')
    .height(110)
    .padding(Theme.Spacing.m)
    .backgroundColor(Theme.Color.GlassHeavy)
    .backdropBlur(Theme.Blur.Medium)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .alignItems(HorizontalAlign.Start)
    .justifyContent(FlexAlign.Center)
    .opacity(this.showContent ? 1 : 0)
    .scale({ 
      x: this.showContent ? 1 : 0.95, 
      y: this.showContent ? 1 : 0.95 
    })
    .animation({
      duration: 500,
      curve: curves.springMotion(),
      delay: 200 + index * 60
    })
  }
}
