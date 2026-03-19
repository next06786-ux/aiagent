/**
 * 增强决策结果详情页
 * 展示完整的决策分析结果，包括时间线、风险评估等
 */
import router from '@ohos.router'

interface TimelineEvent {
  month: number
  event: string
  impact: Record<string, number>
  probability: number
}

interface RiskDimension {
  name: string
  score: number
  level: string
  factors: string[]
  mitigation: string[]
}

interface RiskAssessment {
  overall_risk: number
  overall_level: string
  high_risk_count: number
  dimensions: Record<string, RiskDimension>
  recommendations: string[]
}

interface DecisionOption {
  option_id: string
  title: string
  description: string
  timeline: TimelineEvent[]
  final_score: number
  risk_level: number
  risk_assessment: RiskAssessment | null
}

interface SimulationData {
  simulation_id: string
  question: string
  options: DecisionOption[]
  recommendation: string
}

@Entry
@Component
struct EnhancedDecisionResult {
  @State simulationData: SimulationData | null = null
  @State selectedOptionIndex: number = 0
  @State showTimeline: boolean = true
  @State showRiskDetail: boolean = false

  aboutToAppear() {
    const params = router.getParams() as Record<string, Object>
    if (params?.simulationData) {
      this.simulationData = params.simulationData as SimulationData
    }
  }

  build() {
    Column() {
      // 顶部导航
      Row() {
        Button({ type: ButtonType.Circle }) {
          Text('←')
            .fontSize(24)
            .fontColor('#1A1A1A')
            .fontWeight(600)
        }
        .width(40)
        .height(40)
        .backgroundColor('rgba(0,0,0,0)')
        .onClick(() => router.back())

        Text('决策分析详情')
          .fontSize(20)
          .fontWeight(700)
          .fontColor('#1A1A1A')
          .layoutWeight(1)
          .margin({ left: 12 })

        Button('分享')
          .height(36)
          .fontSize(14)
          .fontWeight(600)
          .fontColor('#007AFF')
          .backgroundColor('rgba(0,122,255,0.1)')
          .borderRadius(18)
      }
      .width('100%')
      .height(56)
      .padding({ left: 16, right: 16 })
      .backgroundColor('rgba(255,255,255,0.95)')

      if (this.simulationData) {
        Scroll() {
          Column({ space: 20 }) {
            // 问题标题
            Column({ space: 8 }) {
              Text('你的决策问题')
                .fontSize(14)
                .fontColor('#999')
              Text(this.simulationData.question)
                .fontSize(18)
                .fontWeight(700)
                .fontColor('#1A1A1A')
                .lineHeight(26)
            }
            .width('100%')
            .padding(20)
            .backgroundColor(Color.White)
            .borderRadius(16)
            .alignItems(HorizontalAlign.Start)

            // 选项切换标签
            Row({ space: 12 }) {
              ForEach(this.simulationData.options, (option: DecisionOption, index: number) => {
                Button(option.title)
                  .height(40)
                  .fontSize(15)
                  .fontWeight(600)
                  .fontColor(this.selectedOptionIndex === index ? Color.White : '#007AFF')
                  .backgroundColor(this.selectedOptionIndex === index ? '#007AFF' : 'rgba(0,122,255,0.1)')
                  .borderRadius(20)
                  .padding({ left: 20, right: 20 })
                  .onClick(() => {
                    this.selectedOptionIndex = index
                  })
              })
            }
            .width('100%')
            .padding({ left: 20, right: 20 })

            // 当前选项详情
            this.OptionDetailView(this.simulationData.options[this.selectedOptionIndex])

            // AI推荐
            Column({ space: 12 }) {
              Row({ space: 12 }) {
                Stack() {
                  Circle({ width: 40, height: 40 })
                    .fill('linear-gradient(135deg, #007AFF, #5856D6)')
                    .opacity(0.15)
                  
                  Text('AI')
                    .fontSize(14)
                    .fontWeight(700)
                    .fontColor('#007AFF')
                }
                .width(40)
                .height(40)

                Text('AI综合推荐')
                  .fontSize(18)
                  .fontWeight(700)
                  .fontColor('#007AFF')
              }

              Text(this.simulationData.recommendation)
                .fontSize(15)
                .fontColor('#333')
                .lineHeight(24)
            }
            .width('100%')
            .padding(20)
            .backgroundColor('rgba(0,122,255,0.05)')
            .borderRadius(16)
            .margin({ left: 20, right: 20 })
            .alignItems(HorizontalAlign.Start)

            // 底部操作
            Row({ space: 12 }) {
              Button('保存分析')
                .layoutWeight(1)
                .height(48)
                .fontSize(16)
                .fontWeight(600)
                .fontColor('#007AFF')
                .backgroundColor('rgba(0,122,255,0.1)')
                .borderRadius(12)

              Button('开始执行')
                .layoutWeight(1)
                .height(48)
                .fontSize(16)
                .fontWeight(600)
                .fontColor(Color.White)
                .backgroundColor('#007AFF')
                .borderRadius(12)
            }
            .width('100%')
            .padding({ left: 20, right: 20, bottom: 20 })
          }
          .width('100%')
        }
        .layoutWeight(1)
        .scrollBar(BarState.Auto)
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F7FA')
  }

  // 选项详情视图
  @Builder
  OptionDetailView(option: DecisionOption) {
    Column({ space: 16 }) {
      // 得分卡片
      Row({ space: 20 }) {
        Column({ space: 4 }) {
          Text('综合得分')
            .fontSize(14)
            .fontColor('#666')
          Text(`${option.final_score.toFixed(1)}`)
            .fontSize(32)
            .fontWeight(700)
            .fontColor('#007AFF')
        }

        Column({ space: 4 }) {
          Text('风险等级')
            .fontSize(14)
            .fontColor('#666')
          Text(this.getRiskText(option.risk_level))
            .fontSize(20)
            .fontWeight(700)
            .fontColor(this.getRiskColor(option.risk_level))
        }
      }
      .width('100%')
      .padding(20)
      .backgroundColor(Color.White)
      .borderRadius(16)
      .justifyContent(FlexAlign.SpaceAround)

      // 时间线
      Column({ space: 12 }) {
        Row() {
          Row({ space: 8 }) {
            Stack() {
              Circle({ width: 28, height: 28 })
                .fill('linear-gradient(135deg, #34C759, #30D158)')
                .opacity(0.15)
              
              Text('📅')
                .fontSize(14)
            }
            .width(28)
            .height(28)

            Text('未来时间线')
              .fontSize(16)
              .fontWeight(700)
              .fontColor('#1A1A1A')
          }
          .layoutWeight(1)

          Button(this.showTimeline ? '收起' : '展开')
            .height(28)
            .fontSize(12)
            .fontColor('#007AFF')
            .backgroundColor('rgba(0,122,255,0.1)')
            .borderRadius(14)
            .onClick(() => {
              this.showTimeline = !this.showTimeline
            })
        }
        .width('100%')

        if (this.showTimeline) {
          ForEach(option.timeline, (event: TimelineEvent, index: number) => {
            this.TimelineEventCard(event, index)
          })
        }
      }
      .width('100%')
      .padding(16)
      .backgroundColor(Color.White)
      .borderRadius(16)
      .alignItems(HorizontalAlign.Start)

      // 风险评估详情
      if (option.risk_assessment) {
        Column({ space: 12 }) {
          Row() {
            Row({ space: 8 }) {
              Stack() {
                Circle({ width: 28, height: 28 })
                  .fill('linear-gradient(135deg, #FF9500, #FF6B00)')
                  .opacity(0.15)
                
                Text('⚠')
                  .fontSize(14)
              }
              .width(28)
              .height(28)

              Text('风险评估')
                .fontSize(16)
                .fontWeight(700)
                .fontColor('#1A1A1A')
            }
            .layoutWeight(1)

            Button(this.showRiskDetail ? '收起' : '展开')
              .height(28)
              .fontSize(12)
              .fontColor('#FF9500')
              .backgroundColor('rgba(255,149,0,0.1)')
              .borderRadius(14)
              .onClick(() => {
                this.showRiskDetail = !this.showRiskDetail
              })
          }
          .width('100%')

          if (this.showRiskDetail) {
            this.RiskDetailView(option.risk_assessment)
          }
        }
        .width('100%')
        .padding(16)
        .backgroundColor(Color.White)
        .borderRadius(16)
        .alignItems(HorizontalAlign.Start)
      }
    }
    .width('100%')
    .padding({ left: 20, right: 20 })
  }

  // 时间线事件卡片
  @Builder
  TimelineEventCard(event: TimelineEvent, index: number) {
    Row({ space: 12 }) {
      // 时间轴
      Column() {
        Text(`${event.month}月`)
          .fontSize(12)
          .fontWeight(600)
          .fontColor('#007AFF')
          .padding(4)
          .backgroundColor('rgba(0,122,255,0.1)')
          .borderRadius(8)
      }
      .width(50)

      // 事件内容
      Column({ space: 8 }) {
        Text(event.event)
          .fontSize(14)
          .fontColor('#1A1A1A')
          .lineHeight(20)

        Row({ space: 8 }) {
          Text(`概率: ${(event.probability * 100).toFixed(0)}%`)
            .fontSize(12)
            .fontColor('#666')

          Text('|')
            .fontSize(12)
            .fontColor('#DDD')

          Text(this.getImpactSummary(event.impact))
            .fontSize(12)
            .fontColor('#666')
        }
      }
      .layoutWeight(1)
      .alignItems(HorizontalAlign.Start)
    }
    .width('100%')
    .padding(12)
    .backgroundColor('#F5F7FA')
    .borderRadius(12)
  }

  // 风险详情视图
  @Builder
  RiskDetailView(riskAssessment: RiskAssessment) {
    Column({ space: 12 }) {
      Text(`总体风险: ${(riskAssessment.overall_risk * 100).toFixed(0)}%`)
        .fontSize(14)
        .fontColor('#666')

      if (riskAssessment.recommendations && riskAssessment.recommendations.length > 0) {
        Column({ space: 8 }) {
          Text('风险缓解建议:')
            .fontSize(14)
            .fontWeight(600)
            .fontColor('#1A1A1A')

          ForEach(riskAssessment.recommendations, (rec: string) => {
            Row({ space: 8 }) {
              Text('•')
                .fontSize(14)
                .fontColor('#FF9500')
              Text(rec)
                .fontSize(13)
                .fontColor('#666')
                .lineHeight(20)
                .layoutWeight(1)
            }
            .width('100%')
          })
        }
        .width('100%')
        .alignItems(HorizontalAlign.Start)
      }
    }
    .width('100%')
    .padding(12)
    .backgroundColor('#FFF9F0')
    .borderRadius(12)
    .alignItems(HorizontalAlign.Start)
  }

  // 辅助方法
  private getRiskColor(risk: number): string {
    if (risk < 0.3) return '#34C759'
    if (risk < 0.6) return '#FF9500'
    return '#FF3B30'
  }

  private getRiskText(risk: number): string {
    if (risk < 0.3) return '低风险'
    if (risk < 0.6) return '中风险'
    return '高风险'
  }

  private getImpactSummary(impact: Record<string, number>): string {
    const positive = Object.values(impact).filter(v => v > 0).length
    const negative = Object.values(impact).filter(v => v < 0).length
    return `${positive}项提升 ${negative}项下降`
  }
}
