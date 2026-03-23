/**
 * 平行宇宙模拟页面 - 游戏化副本地图
 * 展示多个决策选项的未来时间线对比
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { getUserId } from '../service/UserSessionManager'
import { util } from '@kit.ArkTS'

interface TimelineEvent {
  month: number
  event: string
  impact: Record<string, number>
  probability: number
}

interface DecisionOption {
  option_id: string
  title: string
  description: string
  timeline: TimelineEvent[]
  final_score: number
  risk_level: number
  risk_assessment?: RiskAssessment
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

interface DecisionOptionInput {
  title: string
  description: string
}

interface SimulationApiResponse {
  code: number
  message: string
  data: SimulationResult | null
}

interface SimulationResult {
  simulation_id: string
  user_id: string
  question: string
  options: DecisionOption[]
  recommendation: string
  created_at: string
}

interface RouterParams {
  userId?: string
  question?: string
  option?: string
}

interface ScenarioData {
  title: string
  icon: string
  description: string
  options: string[]
  question: string
}

@Entry
@Component
struct ParallelUniverseSimulation {
  @State simulationResult: SimulationResult | null = null
  @State selectedOption: number = 0
  @State currentMonth: number = 1
  @State isAnimating: boolean = false
  @State isLoading: boolean = false
  @State showContent: boolean = false
  @State scenarios: ScenarioData[] = []
  private userId: string = ''
  private question: string = ''

  async aboutToAppear() {
    // 获取真实用户ID
    this.userId = await getUserId()
    console.info('[ParallelUniverseSimulation] 获取到用户ID:', this.userId)

    // 获取路由参数
    const params = router.getParams() as RouterParams
    if (params) {
      if (params.userId) {
        this.userId = params.userId
      }
      if (params.question) {
        this.question = params.question
      }
    }

    this.initializeScenarios()
    
    setTimeout(() => {
      this.showContent = true
    }, 100)
  }

  private initializeScenarios() {
    const scenario1: ScenarioData = {
      title: '🎓 毕业选择',
      icon: '🎓',
      description: '大三学生的人生分岔路口',
      options: ['考研', '工作', '创业'],
      question: '大三学生，毕业后应该选择什么？'
    }
    
    const scenario2: ScenarioData = {
      title: '💼 职业转换',
      icon: '💼',
      description: '在职业发展中做出重要决策',
      options: ['继续深造', '跳槽机会', '创业'],
      question: '工作5年，是否应该转换职业方向？'
    }
    
    const scenario3: ScenarioData = {
      title: '🏠 生活规划',
      icon: '🏠',
      description: '人生重大决策的模拟',
      options: ['留在城市', '回到家乡', '出国发展'],
      question: '是否应该改变现有的生活方式？'
    }
    
    const scenario4: ScenarioData = {
      title: '📚 学习投资',
      icon: '📚',
      description: '教育和自我提升的选择',
      options: ['系统学习', '实践积累', '混合模式'],
      question: '应该如何投资自己的未来？'
    }
    
    this.scenarios = [scenario1, scenario2, scenario3, scenario4]
  }

  async startSimulation(question: string, options: DecisionOptionInput[]) {
    this.isLoading = true

    try {
      const httpRequest = http.createHttp()
      const requestData: Record<string, Object> = {
        'user_id': this.userId,
        'question': question,
        'options': options
      }

      console.info('Starting simulation with data:', JSON.stringify(requestData))

      const response = await httpRequest.request(
        ApiConfig.getApiUrl('/api/decision/simulate'),
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: JSON.stringify(requestData),
          connectTimeout: 30000,
          readTimeout: 30000
        }
      )

      httpRequest.destroy()

      console.info('Response code:', response.responseCode)
      console.info('Response result:', response.result)

      if (response.responseCode === 200) {
        const resultStr = response.result as string
        const result = JSON.parse(resultStr) as SimulationApiResponse
        
        if (result.code === 200 && result.data) {
          this.simulationResult = result.data
          this.currentMonth = 1
          console.info('Simulation completed successfully')
        } else if (result.code === 404) {
          this.showErrorMessage('你还没有训练专属 LoRA，先去完成个性化训练')
        } else if (result.code === 409) {
          this.showErrorMessage('你的 LoRA 正在训练中，请稍后再试')
        } else if (result.code === 503) {
          this.showErrorMessage('推理服务暂时不可用，请稍后重试')
        } else {
          console.error('Simulation failed: ' + result.message)
          this.showErrorMessage('模拟失败: ' + result.message)
        }
      } else if (response.responseCode === 503) {
        console.error('Simulation failed: HTTP ' + response.responseCode)
        this.showErrorMessage('GPU推理服务未就绪，请稍后重试')
      } else {
        console.error('Simulation failed: HTTP ' + response.responseCode)
        this.showErrorMessage('请求失败，请检查网络连接')
      }
    } catch (error) {
      const err = error as Error
      console.error('Failed to start simulation:', err.message)
      this.showErrorMessage('模拟出错: ' + err.message)
    }

    this.isLoading = false
  }

  private showErrorMessage(message: string) {
    console.error('Error:', message)
  }

  build() {
    Stack() {
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('#F1F3F5')

      Column() {
        // 顶部导航栏
        Row() {
          Button({ type: ButtonType.Circle }) {
            Text('←')
              .fontSize(24)
              .fontColor('#1A1A1A')
              .fontWeight(600)
          }
          .width(40)
          .height(40)
          .backgroundColor('rgba(255, 255, 255, 0.0)')
          .onClick(() => {
            router.back()
          })

          Text('平行宇宙副本地图')
            .fontSize(20)
            .fontWeight(700)
            .fontColor('#1A1A1A')
            .margin({ left: 12 })

          Blank()

          if (this.simulationResult) {
            Text(`${this.currentMonth}/12月`)
              .fontSize(14)
              .fontColor('#007AFF')
              .fontWeight(600)
              .padding({ left: 12, right: 12, top: 6, bottom: 6 })
              .backgroundColor('rgba(0, 122, 255, 0.1)')
              .borderRadius(12)
          }
        }
        .width('100%')
        .height(56)
        .padding({ left: 16, right: 16 })
        .backgroundColor('rgba(255, 255, 255, 0.6)')
        .backdropBlur(20)

        if (this.isLoading) {
          Column() {
            LoadingProgress()
              .width(40)
              .height(40)
              .color('#007AFF')
            Text('正在生成平行宇宙...')
              .fontSize(14)
              .fontColor('#999')
              .margin({ top: 12 })
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        } else if (this.simulationResult) {
          // 游戏化地图视图
          this.UniverseMapView()
        } else {
          // 副本选择界面
          this.DungeonSelectionView()
        }
      }
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  DungeonSelectionView() {
    Column() {
      Scroll() {
        Column({ space: 16 }) {
          // 标题区域
          Column({ space: 12 }) {
            Text('🌌 平行宇宙副本地图')
              .fontSize(28)
              .fontWeight(700)
              .fontColor('#1A1A1A')

            Text('选择一个决策场景，探索不同选择的未来')
              .fontSize(14)
              .fontColor('#666')
              .lineHeight(22)
          }
          .width('100%')
          .padding({ left: 20, right: 20, top: 20 })
          .alignItems(HorizontalAlign.Start)

          // 场景卡片列表
          ForEach(this.scenarios, (scenario: ScenarioData) => {
            this.ScenarioCard(scenario)
          })
        }
        .width('100%')
        .padding({ bottom: 20 })
      }
      .layoutWeight(1)
      .scrollBar(BarState.Off)
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  ScenarioCard(scenario: ScenarioData) {
    Column({ space: 12 }) {
      Row({ space: 12 }) {
        Column({ space: 4 }) {
          Text(scenario.title)
            .fontSize(18)
            .fontWeight(700)
            .fontColor('#1A1A1A')

          Text(scenario.description)
            .fontSize(13)
            .fontColor('#666')
        }
        .layoutWeight(1)
        .alignItems(HorizontalAlign.Start)

        Text('→')
          .fontSize(24)
          .fontColor('#007AFF')
      }
      .width('100%')

      // 选项标签
      Flex({ wrap: FlexWrap.Wrap }) {
        ForEach(scenario.options, (option: string) => {
          Text(option)
            .fontSize(12)
            .fontColor('#007AFF')
            .padding({ left: 10, right: 10, top: 4, bottom: 4 })
            .backgroundColor('rgba(0, 122, 255, 0.1)')
            .borderRadius(6)
            .margin({ right: 8, bottom: 8 })
        })
      }
      .width('100%')

      // 开始按钮
      Button('开始探索')
        .width('100%')
        .height(44)
        .fontSize(15)
        .fontWeight(600)
        .fontColor(Color.White)
        .backgroundColor('#007AFF')
        .borderRadius(12)
        .onClick(() => {
          const optionInputs: DecisionOptionInput[] = scenario.options.map((opt: string): DecisionOptionInput => {
            return {
              title: opt,
              description: `选择${opt}的发展路径`
            }
          })

          this.startSimulation(scenario.question, optionInputs).catch((error: Error) => {
            console.error('Simulation error:', error.message)
          })
        })
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(16)
    .shadow({ radius: 8, color: 'rgba(0,0,0,0.05)', offsetY: 2 })
    .margin({ left: 16, right: 16 })
  }

  @Builder
  UniverseMapView() {
    Column() {
      // 问题描述卡片
      Column({ space: 8 }) {
        Text('🎯 决策挑战')
          .fontSize(14)
          .fontColor('#666')
          .fontWeight(600)
        
        Text(this.simulationResult?.question || '')
          .fontSize(16)
          .fontColor('#1A1A1A')
          .fontWeight(700)
          .lineHeight(24)
      }
      .width('100%')
      .padding(16)
      .backgroundColor('rgba(255, 255, 255, 0.9)')
      .borderRadius(16)
      .margin({ left: 16, right: 16, top: 16 })
      .alignItems(HorizontalAlign.Start)

      // 平行宇宙地图（可滚动）
      Scroll() {
        Column({ space: 40 }) {
          if (this.simulationResult) {
            ForEach(this.simulationResult.options, (option: DecisionOption, index: number) => {
              this.UniversePathCard(option, index)
            })
          }

          // AI推荐卡片
          if (this.simulationResult) {
            this.AIRecommendationCard()
          }
        }
        .width('100%')
        .padding({ left: 16, right: 16, top: 20, bottom: 100 })
      }
      .layoutWeight(1)
      .scrollBar(BarState.Off)
      .edgeEffect(EdgeEffect.Spring)

      // 底部时间线控制器
      this.TimelineController()
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  UniversePathCard(option: DecisionOption, index: number) {
    Column({ space: 0 }) {
      // 宇宙标题卡片
      Row({ space: 16 }) {
        // 宇宙编号徽章
        Stack() {
          Circle({ width: 60, height: 60 })
            .fill(this.getUniverseColor(index))
            .opacity(0.15)
          
          Text(String.fromCharCode(65 + index)) // A, B, C, D
            .fontSize(28)
            .fontWeight(800)
            .fontColor(this.getUniverseColor(index))
        }

        Column({ space: 4 }) {
          Text(`宇宙 ${String.fromCharCode(65 + index)}`)
            .fontSize(14)
            .fontColor('#666')
            .fontWeight(600)
          
          Text(option.title)
            .fontSize(20)
            .fontColor('#1A1A1A')
            .fontWeight(700)
          
          Text(option.description)
            .fontSize(14)
            .fontColor('#666')
            .maxLines(2)
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)

        // 综合得分
        Column({ space: 4 }) {
          Text(`${option.final_score.toFixed(0)}`)
            .fontSize(32)
            .fontWeight(800)
            .fontColor(this.getScoreColor(option.final_score))
          
          Text('综合分')
            .fontSize(12)
            .fontColor('#999')
        }
      }
      .width('100%')
      .padding(20)
      .backgroundColor('rgba(255, 255, 255, 0.95)')
      .borderRadius(20)
      .shadow({ radius: 10, color: 'rgba(0,0,0,0.08)', offsetY: 4 })

      // 时间线路径（游戏关卡式）
      Column({ space: 0 }) {
        ForEach(option.timeline, (event: TimelineEvent, eventIndex: number) => {
          if (event.month <= this.currentMonth) {
            this.TimelineNode(event, eventIndex, option.timeline.length, this.getUniverseColor(index))
          }
        })
      }
      .width('100%')
      .margin({ top: -10 })

      // 风险评估按钮
      Button('查看风险雷达图')
        .width('100%')
        .height(44)
        .fontSize(15)
        .fontWeight(600)
        .fontColor(this.getUniverseColor(index))
        .backgroundColor(this.getUniverseColor(index) + '15')
        .borderRadius(12)
        .margin({ top: 16 })
        .onClick(() => {
          router.pushUrl({
            url: 'pages/RiskAssessmentDetail',
            params: {
              option: JSON.stringify(option)
            }
          })
        })
    }
    .width('100%')
  }

  @Builder
  TimelineNode(event: TimelineEvent, index: number, total: number, color: string) {
    Row({ space: 0 }) {
      // 左侧时间线
      Column({ space: 0 }) {
        // 连接线（上）
        if (index > 0) {
          Column()
            .width(4)
            .height(20)
            .backgroundColor(color)
            .opacity(0.3)
        }

        // 节点圆圈
        Stack() {
          Circle({ width: 32, height: 32 })
            .fill(color)
            .opacity(0.2)
          
          Circle({ width: 20, height: 20 })
            .fill(color)
          
          Text(`${event.month}`)
            .fontSize(12)
            .fontWeight(700)
            .fontColor(Color.White)
        }

        // 连接线（下）
        if (index < total - 1) {
          Column()
            .width(4)
            .height(40)
            .backgroundColor(color)
            .opacity(0.3)
        }
      }
      .width(60)
      .alignItems(HorizontalAlign.Center)

      // 右侧事件卡片
      Column({ space: 8 }) {
        Text(event.event)
          .fontSize(14)
          .fontColor('#1A1A1A')
          .fontWeight(600)
          .lineHeight(20)
        
        // 影响指标
        Row({ space: 8 }) {
          ForEach(Object.keys(event.impact), (key: string) => {
            if (Math.abs(event.impact[key]) > 0.1) {
              Text(`${this.getImpactIcon(key)} ${event.impact[key] > 0 ? '+' : ''}${(event.impact[key] * 100).toFixed(0)}%`)
                .fontSize(12)
                .fontColor(event.impact[key] > 0 ? '#4CAF50' : '#FF3B30')
                .padding({ left: 8, right: 8, top: 4, bottom: 4 })
                .backgroundColor(event.impact[key] > 0 ? 'rgba(76, 175, 80, 0.1)' : 'rgba(255, 59, 48, 0.1)')
                .borderRadius(8)
            }
          })
        }
        .width('100%')
        
        Text(`发生概率: ${(event.probability * 100).toFixed(0)}%`)
          .fontSize(12)
          .fontColor('#999')
      }
      .layoutWeight(1)
      .padding(16)
      .backgroundColor('rgba(255, 255, 255, 0.9)')
      .borderRadius(12)
      .alignItems(HorizontalAlign.Start)
    }
    .width('100%')
    .alignItems(VerticalAlign.Top)
  }

  @Builder
  AIRecommendationCard() {
    Column({ space: 16 }) {
      Row({ space: 12 }) {
        Text('🤖')
          .fontSize(32)
        
        Column({ space: 4 }) {
          Text('AI 智能推荐')
            .fontSize(18)
            .fontWeight(700)
            .fontColor('#007AFF')
          
          Text('基于你的性格和历史数据分析')
            .fontSize(12)
            .fontColor('#666')
        }
        .alignItems(HorizontalAlign.Start)
      }
      .width('100%')

      Text(this.simulationResult?.recommendation || '')
        .fontSize(14)
        .fontColor('#333')
        .lineHeight(22)
    }
    .width('100%')
    .padding(20)
    .backgroundColor('rgba(0, 122, 255, 0.05)')
    .borderRadius(20)
    .alignItems(HorizontalAlign.Start)
  }

  @Builder
  TimelineController() {
    Column({ space: 12 }) {
      Row({ space: 16 }) {
        Button(this.isAnimating ? '⏸ 暂停' : '▶ 播放')
          .width(100)
          .height(44)
          .fontSize(15)
          .fontWeight(600)
          .fontColor(Color.White)
          .backgroundColor('#007AFF')
          .borderRadius(12)
          .onClick(() => {
            if (this.isAnimating) {
              this.isAnimating = false
            } else {
              this.playAnimation()
            }
          })

        Slider({
          value: this.currentMonth,
          min: 1,
          max: 12,
          step: 1,
          style: SliderStyle.InSet
        })
          .layoutWeight(1)
          .blockColor('#007AFF')
          .trackColor('rgba(0, 122, 255, 0.2)')
          .selectedColor('#007AFF')
          .onChange((value: number) => {
            this.currentMonth = Math.round(value)
          })
      }
      .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor('rgba(255, 255, 255, 0.95)')
    .backdropBlur(20)
    .shadow({ radius: 10, color: 'rgba(0,0,0,0.1)', offsetY: -4 })
  }

  playAnimation() {
    this.isAnimating = true
    this.currentMonth = 1

    const interval = setInterval(() => {
      if (!this.isAnimating || this.currentMonth >= 12) {
        clearInterval(interval)
        this.isAnimating = false
      } else {
        this.currentMonth++
      }
    }, 500)
  }

  getUniverseColor(index: number): string {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']
    return colors[index % colors.length]
  }

  getImpactIcon(key: string): string {
    const icons: Record<string, string> = {
      '健康': '💪',
      '财务': '💰',
      '社交': '👥',
      '情绪': '😊',
      '学习': '📚',
      '时间': '⏰'
    }
    return icons[key] || '📊'
  }

  getScoreColor(score: number): string {
    if (score >= 80) return '#4CAF50'
    if (score >= 60) return '#FFC107'
    if (score >= 40) return '#FF9800'
    return '#F44336'
  }

  getRiskColor(risk: number): string {
    if (risk < 0.3) return '#4CAF50'
    if (risk < 0.5) return '#FFC107'
    if (risk < 0.7) return '#FF9800'
    return '#F44336'
  }

  getRiskLabel(risk: number): string {
    if (risk < 0.3) return '低风险'
    if (risk < 0.5) return '中风险'
    if (risk < 0.7) return '高风险'
    return '极高风险'
  }
}
