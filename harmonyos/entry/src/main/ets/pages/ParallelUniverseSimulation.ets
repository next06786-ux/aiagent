/**
 * 平行宇宙模拟页面
 * 2D 动态决策链条 / 副本地图体验
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { getUserId } from '../service/UserSessionManager'
import promptAction from '@ohos.promptAction'

interface TimelineEvent {
  event_id?: string
  parent_event_id?: string | null
  month: number
  event: string
  event_type?: string
  branch_group?: string
  node_level?: number
  risk_tag?: string
  opportunity_tag?: string
  visual_weight?: number
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
  risk_assessment?: RiskAssessment
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
  category: string
  description: string
  options: string[]
  question: string
}

interface GraphNode {
  id: string
  parentId: string
  title: string
  detail: string
  month: number
  optionTitle: string
  optionIndex: number
  x: number
  y: number
  riskTag: string
  opportunityTag: string
  probability: number
  impact: Record<string, number>
  eventType: string
  revealed: boolean
}

@Entry
@Component
struct ParallelUniverseSimulation {
  @State simulationResult: SimulationResult | null = null
  @State isLoading: boolean = false
  @State isPlaying: boolean = false
  @State revealedCount: number = 0
  @State showContent: boolean = false
  @State scenarios: ScenarioData[] = []
  @State selectedNodeId: string = ''
  @State graphNodes: GraphNode[] = []
  @State graphHeight: number = 1100
  @State selectedOption: number = 0
  private userId: string = ''
  private question: string = ''
  private animationTimer: number = -1

  async aboutToAppear() {
    this.userId = await getUserId()
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

  aboutToDisappear() {
    if (this.animationTimer !== -1) {
      clearInterval(this.animationTimer)
      this.animationTimer = -1
    }
  }

  private initializeScenarios() {
    this.scenarios = [
      {
        title: '毕业去向决策',
        category: '人生路径',
        description: '围绕毕业后的选择，生成多条个人化世界线。',
        options: ['直接工作', '继续深造', '小规模试错'],
        question: '毕业后干嘛'
      },
      {
        title: '职业转换决策',
        category: '职业发展',
        description: '模拟转岗、跳槽、继续积累三类路径。',
        options: ['转岗', '跳槽', '继续积累'],
        question: '工作几年后要不要换方向'
      },
      {
        title: '长期投入决策',
        category: '学习成长',
        description: '比较深度学习、实践迭代和组合方案。',
        options: ['系统学习', '实践积累', '组合推进'],
        question: '我接下来应该怎么投入自己'
      }
    ]
  }

  async startSimulation(question: string, options: DecisionOptionInput[]) {
    if (!this.userId || this.userId === '') {
      this.showErrorMessage('请先登录，再使用个性化决策模拟')
      return
    }

    try {
      const optionPayload: Array<Record<string, Object>> = options.map((item: DecisionOptionInput, index: number): Record<string, Object> => {
        return {
          option_id: `option_${index + 1}`,
          title: item.title,
          description: item.description,
          timeline: [],
          final_score: 0,
          risk_level: 0
        }
      })
      const simulationData: Record<string, Object> = {
        simulation_id: `stream_${Date.now()}`,
        user_id: this.userId,
        question: question,
        options: optionPayload,
        recommendation: '',
        created_at: new Date().toISOString()
      }

      router.pushUrl({
        url: 'pages/DecisionDungeon2DMap',
        params: {
          dungeonId: `stream_${Date.now()}`,
          question: question,
          userId: this.userId,
          simulationData: JSON.stringify(simulationData)
        }
      }).then(() => {
        console.info('[ParallelUniverseSimulation] navigate to DecisionDungeon2DMap success')
      }).catch((err: Error) => {
        console.error('[ParallelUniverseSimulation] navigate failed: ' + err.message)
        this.showErrorMessage('页面跳转失败：' + err.message)
      })
    } catch (error) {
      const err = error as Error
      this.showErrorMessage('模拟出错：' + err.message)
    }
  }

  private buildGraphNodes(result: SimulationResult) {
    const nodes: GraphNode[] = []
    const topY = 150
    const laneGap = 220
    const startX = 140
    const stepX = 250

    result.options.forEach((option: DecisionOption, optionIndex: number) => {
      const baseY = topY + optionIndex * laneGap
      let previousId = `root_${optionIndex}`

      nodes.push({
        id: previousId,
        parentId: '',
        title: option.title,
        detail: option.description,
        month: 0,
        optionTitle: option.title,
        optionIndex,
        x: startX,
        y: baseY,
        riskTag: this.getRiskTag(option.risk_level),
        opportunityTag: 'medium',
        probability: 1,
        impact: {},
        eventType: 'origin',
        revealed: false
      })

      option.timeline.forEach((event: TimelineEvent, eventIndex: number) => {
        const nodeId = event.event_id ? event.event_id : `${option.option_id}_${eventIndex}`
        nodes.push({
          id: nodeId,
          parentId: event.parent_event_id ? event.parent_event_id : previousId,
          title: `第${event.month}月`,
          detail: event.event,
          month: event.month,
          optionTitle: option.title,
          optionIndex,
          x: startX + (eventIndex + 1) * stepX,
          y: baseY + ((eventIndex % 2 === 0) ? -36 : 36),
          riskTag: event.risk_tag ? event.risk_tag : 'medium',
          opportunityTag: event.opportunity_tag ? event.opportunity_tag : 'medium',
          probability: event.probability,
          impact: event.impact,
          eventType: event.event_type ? event.event_type : 'general',
          revealed: false
        })
        previousId = nodeId
      })
    })

    this.graphNodes = nodes
    this.graphHeight = Math.max(900, topY + result.options.length * laneGap + 120)
    if (nodes.length > 0) {
      this.selectedNodeId = nodes[0].id
    }
  }

  private playGraphReveal() {
    if (this.animationTimer !== -1) {
      clearInterval(this.animationTimer)
      this.animationTimer = -1
    }

    this.isPlaying = true
    this.revealedCount = 0

    this.animationTimer = setInterval(() => {
      if (this.revealedCount >= this.graphNodes.length) {
        clearInterval(this.animationTimer)
        this.animationTimer = -1
        this.isPlaying = false
        return
      }
      this.revealedCount += 1
      const nextNodes: GraphNode[] = []
      this.graphNodes.forEach((node: GraphNode, index: number) => {
        nextNodes.push({
          id: node.id,
          parentId: node.parentId,
          title: node.title,
          detail: node.detail,
          month: node.month,
          optionTitle: node.optionTitle,
          optionIndex: node.optionIndex,
          x: node.x,
          y: node.y,
          riskTag: node.riskTag,
          opportunityTag: node.opportunityTag,
          probability: node.probability,
          impact: node.impact,
          eventType: node.eventType,
          revealed: index < this.revealedCount
        })
      })
      this.graphNodes = nextNodes
      const current = nextNodes[this.revealedCount - 1]
      if (current) {
        this.selectedNodeId = current.id
      }
    }, 450)
  }

  private showErrorMessage(message: string) {
    promptAction.showToast({ message, duration: 2500 })
  }

  private getRiskTag(risk: number): string {
    if (risk < 0.3) return 'low'
    if (risk < 0.6) return 'medium'
    return 'high'
  }

  private getRiskColor(tag: string): string {
    if (tag === 'low') return '#4DD0A8'
    if (tag === 'high') return '#FF6B6B'
    return '#F5B041'
  }

  private getOptionColor(index: number): string {
    const colors = ['#5B8FF9', '#5AD8A6', '#F6BD16', '#E8684A']
    return colors[index % colors.length]
  }

  build() {
    Column() {
      this.HeaderView()

      if (this.isLoading) {
        this.LoadingView()
      } else {
        this.ScenarioSelectionView()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#09111F')
  }

  @Builder
  HeaderView() {
    Row() {
      Button({ type: ButtonType.Circle }) {
        Text('←')
          .fontSize(22)
          .fontColor('#E8ECF3')
          .fontWeight(700)
      }
      .width(40)
      .height(40)
      .backgroundColor('rgba(255,255,255,0.04)')
      .onClick(() => router.back())

      Column({ space: 2 }) {
        Text('决策副本推演')
          .fontSize(20)
          .fontWeight(700)
          .fontColor('#F4F7FB')
        Text('动态构建个人化世界线')
          .fontSize(12)
          .fontColor('#7F8A9A')
      }
      .alignItems(HorizontalAlign.Start)
      .layoutWeight(1)
      .margin({ left: 12 })

      if (this.simulationResult) {
        Text(`${this.revealedCount}/${this.graphNodes.length}`)
          .fontSize(12)
          .fontColor('#7AC7FF')
          .padding({ left: 10, right: 10, top: 6, bottom: 6 })
          .backgroundColor('rgba(122,199,255,0.10)')
          .borderRadius(10)
      }
    }
    .width('100%')
    .padding({ left: 16, right: 16, top: 18, bottom: 14 })
    .backgroundColor('rgba(9,17,31,0.96)')
  }

  @Builder
  LoadingView() {
    Column({ space: 16 }) {
      LoadingProgress()
        .width(42)
        .height(42)
        .color('#6EA8FF')
      Text('正在构建决策副本')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#F4F7FB')
      Text('模型正在推演关键节点与分支链路')
        .fontSize(13)
        .fontColor('#7F8A9A')
    }
    .width('100%')
    .layoutWeight(1)
    .justifyContent(FlexAlign.Center)
  }

  @Builder
  ScenarioSelectionView() {
    Scroll() {
      Column({ space: 16 }) {
        Column({ space: 8 }) {
          Text('选择一个决策场景')
            .fontSize(28)
            .fontWeight(700)
            .fontColor('#F4F7FB')
          Text('系统将生成多条个人化世界线，并在二维平面上逐步推演。')
            .fontSize(14)
            .fontColor('#7F8A9A')
            .lineHeight(22)
        }
        .width('100%')
        .alignItems(HorizontalAlign.Start)
        .padding({ left: 20, right: 20, top: 20, bottom: 8 })

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

  @Builder
  ScenarioCard(scenario: ScenarioData) {
    Column({ space: 14 }) {
      Row() {
        Column({ space: 4 }) {
          Text(scenario.title)
            .fontSize(18)
            .fontWeight(700)
            .fontColor('#F4F7FB')
          Text(scenario.category)
            .fontSize(12)
            .fontColor('#7AC7FF')
          Text(scenario.description)
            .fontSize(13)
            .fontColor('#93A0B3')
            .lineHeight(20)
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)
      }
      .width('100%')

      Flex({ wrap: FlexWrap.Wrap }) {
        ForEach(scenario.options, (option: string) => {
          Text(option)
            .fontSize(12)
            .fontColor('#D8E2F0')
            .padding({ left: 10, right: 10, top: 5, bottom: 5 })
            .backgroundColor('rgba(255,255,255,0.06)')
            .borderRadius(8)
            .margin({ right: 8, bottom: 8 })
        })
      }
      .width('100%')

      Button('开始模拟')
        .width('100%')
        .height(44)
        .fontSize(15)
        .fontWeight(600)
        .fontColor('#09111F')
        .backgroundColor('#7AC7FF')
        .borderRadius(12)
        .onClick(() => {
          const optionInputs: DecisionOptionInput[] = scenario.options.map((opt: string): DecisionOptionInput => {
            return {
              title: opt,
              description: `围绕${opt}展开的个人化行动路径`
            }
          })
          this.startSimulation(scenario.question, optionInputs)
        })
    }
    .width('100%')
    .padding(18)
    .backgroundColor('rgba(255,255,255,0.04)')
    .borderRadius(18)
    .border({ width: 1, color: 'rgba(255,255,255,0.06)' })
    .margin({ left: 16, right: 16 })
  }

  @Builder
  DynamicGraphView() {
    Row() {
      Scroll() {
        Stack() {
          Column()
            .width(1200)
            .height(this.graphHeight)
            .backgroundColor('#09111F')

          ForEach(this.graphNodes, (node: GraphNode) => {
            if (node.revealed) {
              this.GraphNodeView(node)
            }
          })
        }
        .width(1200)
        .height(this.graphHeight)
      }
      .layoutWeight(1)
      .scrollBar(BarState.Auto)
      .edgeEffect(EdgeEffect.Spring)

      this.SidePanel()
    }
    .layoutWeight(1)
  }

  @Builder
  GraphNodeView(node: GraphNode) {
    Column({ space: 8 }) {
      Stack() {
        Column()
          .width(node.id.startsWith('root_') ? 54 : 42)
          .height(node.id.startsWith('root_') ? 54 : 42)
          .backgroundColor(this.getOptionColor(node.optionIndex))
          .opacity(node.id === this.selectedNodeId ? 0.95 : 0.75)
          .borderRadius(node.id.startsWith('root_') ? 14 : 21)
          .border({
            width: node.id === this.selectedNodeId ? 2 : 1,
            color: node.id === this.selectedNodeId ? '#FFFFFF' : 'rgba(255,255,255,0.18)'
          })

        Text(node.month > 0 ? `${node.month}` : '起')
          .fontSize(13)
          .fontWeight(700)
          .fontColor('#F7FAFF')
      }

      Column({ space: 6 }) {
        Text(node.title)
          .fontSize(13)
          .fontWeight(700)
          .fontColor('#F4F7FB')
          .textAlign(TextAlign.Center)
          .maxLines(1)
        Text(node.detail)
          .fontSize(11)
          .fontColor('#97A4B5')
          .lineHeight(16)
          .maxLines(3)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
      }
      .width(180)
      .padding(12)
      .backgroundColor(node.id === this.selectedNodeId ? 'rgba(122,199,255,0.10)' : 'rgba(255,255,255,0.04)')
      .borderRadius(14)
      .border({ width: 1, color: 'rgba(255,255,255,0.06)' })
      .alignItems(HorizontalAlign.Start)
    }
    .position({ x: node.x, y: node.y })
    .width(190)
    .onClick(() => {
      this.selectedNodeId = node.id
    })
  }

  @Builder
  SidePanel() {
    Column({ space: 14 }) {
      if (this.simulationResult) {
        Column({ space: 8 }) {
          Text('决策问题')
            .fontSize(12)
            .fontColor('#7F8A9A')
          Text(this.simulationResult.question)
            .fontSize(18)
            .fontWeight(700)
            .fontColor('#F4F7FB')
            .lineHeight(26)
        }
        .width('100%')
        .alignItems(HorizontalAlign.Start)

        ForEach(this.graphNodes, (item: GraphNode) => {
          if (item.id === this.selectedNodeId) {
            Column({ space: 10 }) {
              Text('当前节点')
                .fontSize(12)
                .fontColor('#7F8A9A')
              Text(item.title)
                .fontSize(16)
                .fontWeight(700)
                .fontColor('#F4F7FB')
              Text(item.detail)
                .fontSize(13)
                .fontColor('#B7C2D0')
                .lineHeight(20)
              Row({ space: 8 }) {
                Text(`风险 ${item.riskTag}`)
                  .fontSize(11)
                  .fontColor(this.getRiskColor(item.riskTag))
                  .padding({ left: 8, right: 8, top: 4, bottom: 4 })
                  .backgroundColor('rgba(255,255,255,0.04)')
                  .borderRadius(8)
                Text(`概率 ${(item.probability * 100).toFixed(0)}%`)
                  .fontSize(11)
                  .fontColor('#7AC7FF')
                  .padding({ left: 8, right: 8, top: 4, bottom: 4 })
                  .backgroundColor('rgba(255,255,255,0.04)')
                  .borderRadius(8)
              }
            }
            .width('100%')
            .padding(14)
            .backgroundColor('rgba(255,255,255,0.04)')
            .borderRadius(16)
            .alignItems(HorizontalAlign.Start)
          }
        })

        Column({ space: 10 }) {
          Text('推荐结论')
            .fontSize(12)
            .fontColor('#7F8A9A')
          Text(this.simulationResult.recommendation)
            .fontSize(13)
            .fontColor('#DCE5F1')
            .lineHeight(21)
        }
        .width('100%')
        .padding(14)
        .backgroundColor('rgba(122,199,255,0.08)')
        .borderRadius(16)
        .alignItems(HorizontalAlign.Start)

        Button(this.isPlaying ? '推演中' : '重新播放')
          .width('100%')
          .height(42)
          .fontSize(14)
          .fontWeight(600)
          .fontColor('#09111F')
          .backgroundColor('#7AC7FF')
          .borderRadius(12)
          .enabled(!this.isPlaying)
          .onClick(() => {
            const resetNodes: GraphNode[] = []
            this.graphNodes.forEach((node: GraphNode) => {
              resetNodes.push({
                id: node.id,
                parentId: node.parentId,
                title: node.title,
                detail: node.detail,
                month: node.month,
                optionTitle: node.optionTitle,
                optionIndex: node.optionIndex,
                x: node.x,
                y: node.y,
                riskTag: node.riskTag,
                opportunityTag: node.opportunityTag,
                probability: node.probability,
                impact: node.impact,
                eventType: node.eventType,
                revealed: false
              })
            })
            this.graphNodes = resetNodes
            this.playGraphReveal()
          })
      }
    }
    .width(320)
    .height('100%')
    .padding(16)
    .backgroundColor('rgba(255,255,255,0.03)')
  }
}
