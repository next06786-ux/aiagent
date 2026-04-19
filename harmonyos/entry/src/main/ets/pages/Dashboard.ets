/**
 * 智能洞察仪表盘 - HarmonyOS 6 流体设计
 * 数据可视化 · 预测分析
 */
import router from '@ohos.router';
import { curves } from '@kit.ArkUI';
import { Theme } from '../common/Theme';
import { SimpleIcon } from '../components/IconRenderer';

interface InsightItem {
  id: string;
  title: string;
  description: string;
  type: 'prediction' | 'anomaly' | 'suggestion';
  confidence: number;
  timestamp: number;
}

interface MetricCard {
  title: string;
  value: string;
  trend: string;
  trendUp: boolean;
  icon: string;
  color: string;
  gradient: string[];
}

@Entry
@Component
struct Dashboard {
  @State insights: InsightItem[] = [];
  @State metrics: MetricCard[] = [];
  @State showContent: boolean = false;
  @State selectedTab: number = 0;
  @State animatedValues: number[] = [0, 0, 0, 0]; // 数字动画
  private scroller: Scroller = new Scroller();

  aboutToAppear() {
    this.loadData();
    setTimeout(() => {
      this.showContent = true;
      this.animateMetrics();
    }, 100);
  }

  loadData() {
    this.metrics = [
      { 
        title: '感知数据', 
        value: '12,450', 
        trend: '+12%', 
        trendUp: true, 
        icon: 'analytics', 
        color: Theme.Color.Primary,
        gradient: Theme.Gradient.Aurora
      },
      { 
        title: '预测准确率', 
        value: '94.2%', 
        trend: '+2.1%', 
        trendUp: true, 
        icon: 'ai', 
        color: Theme.Color.Accent,
        gradient: Theme.Gradient.Mint
      },
      { 
        title: '异常检测', 
        value: '3', 
        trend: '-1', 
        trendUp: false, 
        icon: 'insight', 
        color: Theme.Color.Warning,
        gradient: Theme.Gradient.Sunrise
      },
      { 
        title: '知识节点', 
        value: '856', 
        trend: '+45', 
        trendUp: true, 
        icon: 'network', 
        color: Theme.Color.Secondary,
        gradient: Theme.Gradient.Nebula
      }
    ];

    this.insights = [
      {
        id: '1',
        title: '睡眠质量预警',
        description: '根据最近3天的活动数据，预测今晚睡眠质量可能下降，建议提前1小时休息。',
        type: 'prediction',
        confidence: 0.85,
        timestamp: Date.now() - 3600000
      },
      {
        id: '2',
        title: '工作效率高峰',
        description: '检测到您在上午10:00-11:30期间专注度最高，建议安排重要任务。',
        type: 'suggestion',
        confidence: 0.92,
        timestamp: Date.now() - 7200000
      },
      {
        id: '3',
        title: '异常心率波动',
        description: '昨日下午运动后心率恢复较慢，建议关注心血管健康。',
        type: 'anomaly',
        confidence: 0.78,
        timestamp: Date.now() - 86400000
      }
    ];
  }

  // 数字动画效果
  private animateMetrics() {
    const targetValues = [12450, 94.2, 3, 856];
    const duration = 1500;
    const steps = 60;
    const interval = duration / steps;
    
    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep++;
      const progress = currentStep / steps;
      const easeProgress = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      
      this.animatedValues = targetValues.map(target => target * easeProgress);
      
      if (currentStep >= steps) {
        clearInterval(timer);
        this.animatedValues = targetValues;
      }
    }, interval);
  }

  build() {
    Stack() {
      // 1. 背景层 - 动态渐变
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor(Theme.Color.BackgroundPrimary)

      // 装饰性光晕 - 左上
      Circle({ width: 350, height: 350 })
        .fill('rgba(10, 89, 247, 0.08)')
        .blur(80)
        .position({ x: -100, y: -100 })

      // 装饰性光晕 - 右下
      Circle({ width: 280, height: 280 })
        .fill('rgba(255, 154, 158, 0.08)')
        .blur(70)
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
            .onClick(() => {
              router.back();
            })

            Column({ space: 4 }) {
              Text('智能洞察')
                .fontSize(Theme.Typography.HeadingMedium.size)
                .fontWeight(Theme.Typography.HeadingMedium.weight)
                .fontColor(Theme.Color.TextPrimary)
              
              Text('预见未来 · 主动发现')
                .fontSize(Theme.Typography.Caption.size)
                .fontColor(Theme.Color.TextSecondary)
                .opacity(0.8)
            }
            .alignItems(HorizontalAlign.Start)
          }
          
          Blank()
          
          Button({ type: ButtonType.Circle, stateEffect: true }) {
            SimpleIcon({
              iconName: 'calendar',
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
        .height(72)
        .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m, top: Theme.Spacing.s })
        .backgroundColor(Theme.Color.GlassLight)
        .backdropBlur(Theme.Blur.Heavy)
        .zIndex(100)
        .opacity(this.showContent ? 1 : 0)
        .translate({ y: this.showContent ? 0 : -20 })
        .animation({
          duration: 600,
          curve: Curve.Friction
        })

        // 3. 主内容区域
        Scroll(this.scroller) {
          Column({ space: Theme.Spacing.l }) {
            // 3.1 指标卡片网格 (Grid)
            Grid() {
              ForEach(this.metrics, (item: MetricCard, index: number) => {
                GridItem() {
                  this.EnhancedMetricCard(item, index)
                }
              })
            }
            .columnsTemplate('1fr 1fr')
            .rowsGap(Theme.Spacing.m)
            .columnsGap(Theme.Spacing.m)
            .height(280)
            .width('100%')

            // 3.2 趋势图表卡片
            Column({ space: Theme.Spacing.m }) {
              Row() {
                Text('趋势分析')
                  .fontSize(Theme.Typography.HeadingMedium.size)
                  .fontWeight(Theme.Typography.HeadingMedium.weight)
                  .fontColor(Theme.Color.TextPrimary)
                
                Blank()
                
                Text('近7天')
                  .fontSize(Theme.Typography.Caption.size)
                  .fontColor(Theme.Color.Primary)
                  .fontWeight(600)
                  .backgroundColor('rgba(10, 89, 247, 0.1)')
                  .padding({ left: 12, right: 12, top: 6, bottom: 6 })
                  .borderRadius(Theme.Radius.m)
              }
              .width('100%')
              
              // 图表容器
              Stack({ alignContent: Alignment.BottomStart }) {
                // 背景网格线
                Column() {
                  Divider().color('rgba(0, 0, 0, 0.04)').margin({ bottom: 35 })
                  Divider().color('rgba(0, 0, 0, 0.04)').margin({ bottom: 35 })
                  Divider().color('rgba(0, 0, 0, 0.04)').margin({ bottom: 35 })
                  Divider().color('rgba(0, 0, 0, 0.04)')
                }
                .width('100%')
                .height(160)
                .justifyContent(FlexAlign.SpaceBetween)
                
                // 折线图
                Polyline({ width: '100%', height: 160 })
                  .points([[0, 130], [50, 105], [100, 115], [150, 65], [200, 85], [250, 45], [300, 25]])
                  .fill('none')
                  .stroke(Theme.Color.Primary)
                  .strokeWidth(3)
                  .shadow({ radius: 8, color: 'rgba(10, 89, 247, 0.4)', offsetY: 2 })
                
                // 渐变填充区域
                Polygon({ width: '100%', height: 160 })
                  .points([[0, 160], [0, 130], [50, 105], [100, 115], [150, 65], [200, 85], [250, 45], [300, 25], [300, 160]])
                  .fill('rgba(10, 89, 247, 0.08)')
                
                // 数据点
                ForEach([
                  { x: 0, y: 130 },
                  { x: 50, y: 105 },
                  { x: 100, y: 115 },
                  { x: 150, y: 65 },
                  { x: 200, y: 85 },
                  { x: 250, y: 45 },
                  { x: 300, y: 25 }
                ], (point: Record<string, number>, idx: number) => {
                  Circle({ width: 8, height: 8 })
                    .fill(Theme.Color.Primary)
                    .position({ x: point.x - 4, y: point.y - 4 })
                    .shadow({ radius: 4, color: 'rgba(10, 89, 247, 0.5)', offsetY: 0 })
                    .opacity(this.showContent ? 1 : 0)
                    .scale({ 
                      x: this.showContent ? 1 : 0, 
                      y: this.showContent ? 1 : 0 
                    })
                    .animation({
                      duration: 400,
                      curve: curves.springMotion(),
                      delay: 400 + idx * 50
                    })
                })
              }
              .width('100%')
              .height(220)
              .padding(Theme.Spacing.l)
              .backgroundColor(Theme.Color.GlassHeavy)
              .backdropBlur(Theme.Blur.Heavy)
              .borderRadius(Theme.Radius.xl)
              .border({ width: 1, color: Theme.Color.BorderLight })
              .shadow(Theme.Shadow.Medium)
              .opacity(this.showContent ? 1 : 0)
              .translate({ y: this.showContent ? 0 : 30 })
              .animation({
                duration: 700,
                curve: Curve.Friction,
                delay: 300
              })
            }

            // 3.3 洞察列表
            Column({ space: Theme.Spacing.m }) {
              Text('AI 洞察')
                .fontSize(Theme.Typography.HeadingMedium.size)
                .fontWeight(Theme.Typography.HeadingMedium.weight)
                .fontColor(Theme.Color.TextPrimary)
                .width('100%')
              
              ForEach(this.insights, (item: InsightItem, index: number) => {
                this.EnhancedInsightItem(item, index)
              })
            }
            .padding({ bottom: 60 })
          }
          .padding({ left: Theme.Spacing.m, right: Theme.Spacing.m, top: Theme.Spacing.m })
        }
        .scrollBar(BarState.Off)
        .edgeEffect(EdgeEffect.Spring)
        .layoutWeight(1)
      }
      .width('100%')
      .height('100%')
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  EnhancedMetricCard(item: MetricCard, index: number) {
    Stack() {
      // 渐变背景
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 135,
          colors: [
            [item.gradient[0], 0.0],
            [item.gradient[1], 1.0]
          ]
        })
        .opacity(0.1)
        .borderRadius(Theme.Radius.l)
      
      Column({ space: 12 }) {
        Row() {
          SimpleIcon({
            iconName: item.icon,
            iconSize: 32,
            color: item.color
          })
          Blank()
          Text(item.trend)
            .fontSize(Theme.Typography.Caption.size)
            .fontColor(item.trendUp ? Theme.Color.Accent : Theme.Color.Destructive)
            .fontWeight(600)
            .padding({ left: 8, right: 8, top: 4, bottom: 4 })
            .backgroundColor(item.trendUp 
              ? 'rgba(0, 200, 83, 0.12)' 
              : 'rgba(255, 59, 48, 0.12)')
            .borderRadius(Theme.Radius.s)
        }
        .width('100%')
        
        Text(item.value)
          .fontSize(Theme.Typography.DisplaySmall.size)
          .fontWeight(Theme.Typography.DisplaySmall.weight)
          .fontColor(Theme.Color.TextPrimary)
        
        Text(item.title)
          .fontSize(Theme.Typography.BodySmall.size)
          .fontColor(Theme.Color.TextSecondary)
      }
      .width('100%')
      .height('100%')
      .padding(Theme.Spacing.m)
      .alignItems(HorizontalAlign.Start)
      .justifyContent(FlexAlign.SpaceBetween)
    }
    .width('100%')
    .height(130)
    .backgroundColor(Theme.Color.GlassHeavy)
    .backdropBlur(Theme.Blur.Heavy)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 25 })
    .scale({ 
      x: this.showContent ? 1 : 0.95, 
      y: this.showContent ? 1 : 0.95 
    })
    .animation({
      duration: 600,
      curve: curves.springMotion(),
      delay: index * 80
    })
  }

  @Builder
  EnhancedInsightItem(item: InsightItem, index: number) {
    Row({ space: Theme.Spacing.m }) {
      // 类型指示条
      Column()
        .width(4)
        .height(48)
        .backgroundColor(this.getInsightColor(item.type))
        .borderRadius(2)
        .shadow({ 
          radius: 8, 
          color: this.getInsightColor(item.type) + '40', 
          offsetY: 0 
        })
      
      Column({ space: 8 }) {
        Row() {
          Text(item.title)
            .fontSize(Theme.Typography.BodyLarge.size)
            .fontWeight(600)
            .fontColor(Theme.Color.TextPrimary)
          
          Blank()
          
          Row({ space: 4 }) {
            Circle({ width: 6, height: 6 })
              .fill(this.getInsightColor(item.type))
            Text(`${(item.confidence * 100).toFixed(0)}%`)
              .fontSize(Theme.Typography.Caption.size)
              .fontColor(Theme.Color.TextTertiary)
              .fontWeight(500)
          }
        }
        .width('100%')
        
        Text(item.description)
          .fontSize(Theme.Typography.BodyMedium.size)
          .fontColor(Theme.Color.TextSecondary)
          .lineHeight(22)
          .maxLines(3)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
      }
      .layoutWeight(1)
      .alignItems(HorizontalAlign.Start)
    }
    .width('100%')
    .padding(Theme.Spacing.m)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .opacity(this.showContent ? 1 : 0)
    .translate({ x: this.showContent ? 0 : 30 })
    .animation({
      duration: 600,
      curve: Curve.Friction,
      delay: 500 + index * 100
    })
  }

  getInsightColor(type: string): string {
    switch (type) {
      case 'prediction': return Theme.Color.Primary;
      case 'anomaly': return Theme.Color.Warning;
      case 'suggestion': return Theme.Color.Accent;
      default: return Theme.Color.TextTertiary;
    }
  }
}

