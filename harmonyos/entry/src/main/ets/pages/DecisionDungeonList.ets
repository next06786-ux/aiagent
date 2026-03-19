/**
 * 决策副本列表页面
 * 展示所有生成的决策副本，每个选项一个副本
 */
import router from '@ohos.router'
import { getUserId } from '../service/UserSessionManager'

interface TimelineEvent {
  month: number
  event: string
  impact: Record<string, number>
  probability: number
}

interface DungeonOption {
  option_id: string
  title: string
  description: string
  timeline: TimelineEvent[]
  final_score: number
  risk_level: number
  risk_assessment: RiskAssessment | null
}

interface RiskAssessment {
  overall_risk: number
  overall_level: string
  recommendations: string[]
}

interface SimulationData {
  simulation_id: string
  user_id: string
  question: string
  options: DungeonOption[]
  recommendation: string
  created_at: string
}

@Entry
@Component
struct DecisionDungeonList {
  @State simulationData: SimulationData | null = null
  @State selectedDungeonIndex: number = -1
  private userId: string = ''

  async aboutToAppear() {
    // 获取真实用户ID
    this.userId = await getUserId()
    console.info('[DecisionDungeonList] 获取到用户ID:', this.userId)

    // 获取路由参数
    const params = router.getParams() as Record<string, string>
    if (params?.userId) {
      this.userId = params.userId
    }
    if (params?.simulationData) {
      try {
        this.simulationData = JSON.parse(params.simulationData) as SimulationData
      } catch (error) {
        console.error('解析模拟数据失败:', (error as Error).message)
      }
    }
  }

  // 进入单个副本
  private enterDungeon(optionIndex: number): void {
    if (!this.simulationData) return

    const option = this.simulationData.options[optionIndex]
    
    // 创建单个副本的数据
    const singleDungeonData: SimulationData = {
      simulation_id: `${this.simulationData.simulation_id}_${option.option_id}`,
      user_id: this.simulationData.user_id,
      question: this.simulationData.question,
      options: [option],  // 只包含当前选项
      recommendation: `你选择了「${option.title}」`,
      created_at: this.simulationData.created_at
    }

    router.pushUrl({
      url: 'pages/DecisionDungeon2DMap',
      params: {
        userId: this.userId,
        simulationData: JSON.stringify(singleDungeonData),
        question: this.simulationData.question
      }
    })
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

        Text('决策副本')
          .fontSize(20)
          .fontWeight(700)
          .fontColor('#1A1A1A')
          .layoutWeight(1)
          .margin({ left: 12 })

        Text(`${this.simulationData?.options.length || 0}个`)
          .fontSize(14)
          .fontColor('#666')
      }
      .width('100%')
      .height(56)
      .padding({ left: 16, right: 16 })
      .backgroundColor('rgba(255,255,255,0.95)')

      if (this.simulationData) {
        Scroll() {
          Column({ space: 20 }) {
            // 问题卡片
            Column({ space: 12 }) {
              Row({ space: 12 }) {
                // 使用渐变圆形图标代替 emoji
                Stack() {
                  Circle({ width: 48, height: 48 })
                    .linearGradient({
                      angle: 135,
                      colors: [['#667eea', 0.0], ['#764ba2', 1.0]]
                    })
                  
                  Text('问')
                    .fontSize(18)
                    .fontWeight(700)
                    .fontColor(Color.White)
                }
                
                Text('你的决策问题')
                  .fontSize(16)
                  .fontWeight(700)
                  .fontColor('#1A1A1A')
              }

              Text(this.simulationData.question)
                .fontSize(15)
                .fontColor('#333')
                .lineHeight(24)
            }
            .width('100%')
            .padding(20)
            .backgroundColor(Color.White)
            .borderRadius(16)
            .alignItems(HorizontalAlign.Start)

            // 副本列表
            Column({ space: 12 }) {
              Text('选择一个副本进入探索')
                .fontSize(14)
                .fontColor('#666')
                .alignSelf(ItemAlign.Start)

              ForEach(this.simulationData.options, (option: DungeonOption, index: number) => {
                this.DungeonCard(option, index)
              })
            }
            .width('100%')

            // AI 推荐
            if (this.simulationData.recommendation) {
              Column({ space: 12 }) {
                Row({ space: 12 }) {
                  // AI 图标 - 使用渐变圆形
                  Stack() {
                    Circle({ width: 48, height: 48 })
                      .linearGradient({
                        angle: 135,
                        colors: [['#4facfe', 0.0], ['#00f2fe', 1.0]]
                      })
                    
                    Text('AI')
                      .fontSize(16)
                      .fontWeight(700)
                      .fontColor(Color.White)
                  }
                  
                  Text('AI 综合推荐')
                    .fontSize(16)
                    .fontWeight(700)
                    .fontColor('#007AFF')
                }

                Text(this.simulationData.recommendation)
                  .fontSize(14)
                  .fontColor('#333')
                  .lineHeight(22)
              }
              .width('100%')
              .padding(20)
              .backgroundColor('rgba(0,122,255,0.05)')
              .borderRadius(16)
              .alignItems(HorizontalAlign.Start)
            }
          }
          .width('100%')
          .padding(20)
        }
        .layoutWeight(1)
        .scrollBar(BarState.Auto)
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F7FA')
  }

  @Builder
  DungeonCard(option: DungeonOption, index: number) {
    Column({ space: 16 }) {
      // 头部
      Row() {
        Column({ space: 4 }) {
          Text(option.title)
            .fontSize(18)
            .fontWeight(700)
            .fontColor('#1A1A1A')

          Text(option.description)
            .fontSize(13)
            .fontColor('#666')
            .maxLines(2)
            .textOverflow({ overflow: TextOverflow.Ellipsis })
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)

        // 得分徽章
        Column({ space: 2 }) {
          Text(`${option.final_score.toFixed(0)}`)
            .fontSize(24)
            .fontWeight(700)
            .fontColor('#007AFF')
          Text('综合分')
            .fontSize(11)
            .fontColor('#666')
        }
        .width(70)
        .height(70)
        .backgroundColor('rgba(0,122,255,0.1)')
        .borderRadius(35)
        .justifyContent(FlexAlign.Center)
      }
      .width('100%')

      // 统计信息
      Row({ space: 20 }) {
        Column({ space: 4 }) {
          Text(`${option.timeline.length}`)
            .fontSize(20)
            .fontWeight(700)
            .fontColor('#1A1A1A')
          Text('关键节点')
            .fontSize(12)
            .fontColor('#666')
        }

        Column({ space: 4 }) {
          Text(this.getRiskText(option.risk_level))
            .fontSize(16)
            .fontWeight(700)
            .fontColor(this.getRiskColor(option.risk_level))
          Text('风险等级')
            .fontSize(12)
            .fontColor('#666')
        }

        Column({ space: 4 }) {
          Text('12月')
            .fontSize(20)
            .fontWeight(700)
            .fontColor('#1A1A1A')
          Text('模拟周期')
            .fontSize(12)
            .fontColor('#666')
        }
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#F5F7FA')
      .borderRadius(12)
      .justifyContent(FlexAlign.SpaceAround)

      // 进入按钮
      Button('进入副本探索 →')
        .width('100%')
        .height(44)
        .fontSize(15)
        .fontWeight(600)
        .fontColor(Color.White)
        .backgroundColor('#007AFF')
        .borderRadius(22)
        .onClick(() => {
          this.enterDungeon(index)
        })
    }
    .width('100%')
    .padding(20)
    .backgroundColor(Color.White)
    .borderRadius(16)
    .shadow({ radius: 8, color: 'rgba(0,0,0,0.08)', offsetY: 4 })
  }

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
}
