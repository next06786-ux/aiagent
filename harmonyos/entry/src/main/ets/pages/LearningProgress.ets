/**
 * 学习进度页面 - HarmonyOS 6 现代化设计
 * 展示强化学习系统的训练进度和性能指标
 */
import { router } from '@kit.ArkUI';
import { HttpUtil } from '../utils/HttpUtil';

/**
 * 学习进度数据接口
 */
interface LearningProgressData {
  total_interactions: number;
  positive_feedback: number;
  negative_feedback: number;
  neutral_feedback: number;
  average_reward: number;
  learning_rate: number;
  agent_performance: Record<string, number>;
  recent_improvements: string[];
}

@Entry
@Component
struct LearningProgress {
  @State userId: string = 'default_user';
  @State progress: LearningProgressData | null = null;
  @State isLoading: boolean = true;
  @State showContent: boolean = false;
  
  aboutToAppear(): void {
    this.loadProgress();
    setTimeout(() => {
      this.showContent = true;
    }, 100);
  }
  
  /**
   * 加载学习进度数据
   */
  private async loadProgress(): Promise<void> {
    this.isLoading = true;
    
    try {
      const response = await HttpUtil.get(`/api/v4/learning/progress/${this.userId}`);
      
      if (response.responseCode === 200) {
        const data = HttpUtil.parseResponse<Record<string, Object>>(response);
        
        if (data.success) {
          this.progress = data.progress as LearningProgressData;
        }
      }
      
    } catch (error) {
      console.error('LearningProgress', 'Load failed:', error);
      // 使用模拟数据
      this.progress = {
        total_interactions: 1250,
        positive_feedback: 850,
        negative_feedback: 50,
        neutral_feedback: 350,
        average_reward: 0.78,
        learning_rate: 0.01,
        agent_performance: {
          'health': 0.85,
          'time': 0.92,
          'emotion': 0.76
        },
        recent_improvements: [
          '健康管理智能体准确率提升5%',
          '时间管理预测精度提升8%',
          '情绪识别召回率提升3%'
        ]
      };
    } finally {
      this.isLoading = false;
    }
  }
  
  build() {
    Stack() {
      // 1. 背景层
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('#F1F3F5')
        
      // 装饰性渐变圆
      Circle({ width: 400, height: 400 })
        .fill('rgba(255, 87, 34, 0.05)')
        .blur(80)
        .position({ x: '50%', y: -100 })
        .translate({ x: '-50%' })

      Column() {
        // 2. 顶部导航栏
        Row() {
          Row({ space: 12 }) {
            Button({ type: ButtonType.Circle, stateEffect: true }) {
              Text('←')
                .fontSize(24)
                .fontColor('#1A1A1A')
                .fontWeight(600)
            }
            .width(40)
            .height(40)
            .backgroundColor('rgba(255, 255, 255, 0.0)')
            .onClick(() => router.back())
            
            Column({ space: 2 }) {
              Text('学习进度')
                .fontSize(20)
                .fontWeight(700)
                .fontColor('#1A1A1A')
              
              Text('强化学习 · 持续优化')
                .fontSize(12)
                .fontColor('#666666')
            }
            .alignItems(HorizontalAlign.Start)
          }
          
          Blank()
          
          Button({ type: ButtonType.Circle, stateEffect: true }) {
            Text('📈')
              .fontSize(20)
              .fontColor('#FF5722')
          }
          .width(40)
          .height(40)
          .backgroundColor('rgba(255, 255, 255, 0.0)')
          .onClick(() => {
            router.pushUrl({ url: 'pages/LearningEvolution' });
          })
        }
        .width('100%')
        .height(56)
        .padding({ left: 16, right: 16 })
        .backgroundColor('rgba(255, 255, 255, 0.6)')
        .backdropBlur(20)
        .zIndex(100)
        .opacity(this.showContent ? 1 : 0)
        .translate({ y: this.showContent ? 0 : -20 })
        .animation({
          duration: 600,
          curve: Curve.Friction
        })
        
        if (this.isLoading) {
          Column() {
            LoadingProgress()
              .width(40)
              .height(40)
              .color('#FF5722')
            Text('加载中...')
              .fontSize(14)
              .fontColor('#999999')
              .margin({ top: 16 })
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        } else if (this.progress) {
          Scroll() {
            Column({ space: 24 }) {
              // 3. 核心指标卡片
              Column({ space: 16 }) {
                Text('核心指标')
                  .fontSize(18)
                  .fontWeight(700)
                  .fontColor('#1A1A1A')
                  .width('100%')
                  .padding({ left: 8 })
                
                Grid() {
                  GridItem() {
                    this.StatCard('总交互次数', this.progress.total_interactions.toString(), '#FF5722')
                  }
                  
                  GridItem() {
                    this.StatCard('平均奖励', this.progress.average_reward.toFixed(2), '#4CAF50')
                  }
                }
                .columnsTemplate('1fr 1fr')
                .rowsGap(16)
                .columnsGap(16)
                .width('100%')
                .height(100)
              }
              .padding({ left: 16, right: 16 })
              .opacity(this.showContent ? 1 : 0)
              .translate({ y: this.showContent ? 0 : 20 })
              .animation({
                duration: 600,
                delay: 100,
                curve: Curve.Friction
              })
              
              // 4. 反馈分布
              Column({ space: 16 }) {
                Text('反馈分布')
                  .fontSize(18)
                  .fontWeight(700)
                  .fontColor('#1A1A1A')
                  .width('100%')
                  .padding({ left: 8 })
                
                Column({ space: 16 }) {
                  this.FeedbackBar('正面反馈', this.progress.positive_feedback, this.progress.total_interactions, '#4CAF50')
                  this.FeedbackBar('中性反馈', this.progress.neutral_feedback, this.progress.total_interactions, '#FFC107')
                  this.FeedbackBar('负面反馈', this.progress.negative_feedback, this.progress.total_interactions, '#F44336')
                }
                .padding(24)
                .backgroundColor('rgba(255, 255, 255, 0.8)')
                .backdropBlur(20)
                .borderRadius(24)
                .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
              }
              .padding({ left: 16, right: 16 })
              .opacity(this.showContent ? 1 : 0)
              .translate({ y: this.showContent ? 0 : 20 })
              .animation({
                duration: 600,
                delay: 200,
                curve: Curve.Friction
              })
              
              // 5. 智能体性能
              Column({ space: 16 }) {
                Text('智能体性能')
                  .fontSize(18)
                  .fontWeight(700)
                  .fontColor('#1A1A1A')
                  .width('100%')
                  .padding({ left: 8 })
                
                Column({ space: 12 }) {
                  ForEach(Object.keys(this.progress.agent_performance), (agentId: string) => {
                    this.AgentPerformanceItem(agentId, this.progress!.agent_performance[agentId])
                  })
                }
                .padding(24)
                .backgroundColor('rgba(255, 255, 255, 0.8)')
                .backdropBlur(20)
                .borderRadius(24)
                .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
              }
              .padding({ left: 16, right: 16 })
              .opacity(this.showContent ? 1 : 0)
              .translate({ y: this.showContent ? 0 : 20 })
              .animation({
                duration: 600,
                delay: 300,
                curve: Curve.Friction
              })
              
              // 6. 最近改进
              if (this.progress.recent_improvements.length > 0) {
                Column({ space: 16 }) {
                  Text('最近改进')
                    .fontSize(18)
                    .fontWeight(700)
                    .fontColor('#1A1A1A')
                    .width('100%')
                    .padding({ left: 8 })
                  
                  Column({ space: 12 }) {
                    ForEach(this.progress.recent_improvements, (improvement: string) => {
                      Row({ space: 12 }) {
                        Circle({ width: 8, height: 8 })
                          .fill('#4CAF50')
                          .margin({ top: 6 })
                        
                        Text(improvement)
                          .fontSize(15)
                          .fontColor('#333333')
                          .lineHeight(22)
                          .layoutWeight(1)
                      }
                      .alignItems(VerticalAlign.Top)
                      .width('100%')
                      .padding(12)
                      .backgroundColor('rgba(255, 255, 255, 0.5)')
                      .borderRadius(12)
                    })
                  }
                  .padding(24)
                  .backgroundColor('rgba(255, 255, 255, 0.8)')
                  .backdropBlur(20)
                  .borderRadius(24)
                  .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
                }
                .padding({ left: 16, right: 16 })
                .opacity(this.showContent ? 1 : 0)
                .translate({ y: this.showContent ? 0 : 20 })
                .animation({
                  duration: 600,
                  delay: 400,
                  curve: Curve.Friction
                })
              }
              
              // 7. 提示信息
              Column({ space: 8 }) {
                Text('💡 学习提示')
                  .fontSize(14)
                  .fontWeight(600)
                  .fontColor('#666666')
                
                Text('系统会根据您的反馈持续优化决策模型，提供更精准的建议。')
                  .fontSize(13)
                  .fontColor('#999999')
                  .lineHeight(20)
              }
              .width('100%')
              .padding(24)
              .backgroundColor('rgba(255, 243, 224, 0.6)') // 温暖的提示背景
              .backdropBlur(10)
              .borderRadius(20)
              .margin({ left: 16, right: 16, bottom: 40 })
              .opacity(this.showContent ? 1 : 0)
              .translate({ y: this.showContent ? 0 : 20 })
              .animation({
                duration: 600,
                delay: 500,
                curve: Curve.Friction
              })
            }
            .width('100%')
            .padding({ top: 20 })
          }
          .layoutWeight(1)
          .scrollBar(BarState.Off)
          .edgeEffect(EdgeEffect.Spring)
        }
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F1F3F5')
  }
  
  @Builder
  StatCard(label: string, value: string, color: string) {
    Column({ space: 8 }) {
      Text(value)
        .fontSize(32)
        .fontWeight(800)
        .fontColor(color)
      Text(label)
        .fontSize(14)
        .fontColor('#666666')
        .fontWeight(500)
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .backgroundColor('rgba(255, 255, 255, 0.8)')
    .backdropBlur(20)
    .borderRadius(24)
    .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
  }
  
  @Builder
  FeedbackBar(label: string, value: number, total: number, color: string) {
    Column({ space: 8 }) {
      Row() {
        Text(label)
          .fontSize(14)
          .fontColor('#333333')
          .fontWeight(500)
        Blank()
        Text(value.toString())
          .fontSize(14)
          .fontColor(color)
          .fontWeight(600)
      }
      .width('100%')
      
      Progress({
        value: value,
        total: total,
        type: ProgressType.Linear
      })
        .width('100%')
        .height(8)
        .color(color)
        .backgroundColor('rgba(0,0,0,0.05)')
        .style({ strokeWidth: 8, enableSmoothEffect: true })
    }
  }
  
  @Builder
  AgentPerformanceItem(name: string, value: number) {
    Column({ space: 8 }) {
      Row() {
        Text(name)
          .fontSize(14)
          .fontColor('#333333')
          .fontWeight(500)
        Blank()
        Text(`${(value * 100).toFixed(0)}%`)
          .fontSize(14)
          .fontColor('#1E88E5')
          .fontWeight(600)
      }
      .width('100%')
      
      Progress({
        value: value,
        total: 1,
        type: ProgressType.Linear
      })
        .width('100%')
        .height(8)
        .color('#1E88E5')
        .backgroundColor('rgba(0,0,0,0.05)')
        .style({ strokeWidth: 8, enableSmoothEffect: true })
    }
    .padding({ top: 4, bottom: 4 })
  }
}
