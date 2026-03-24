/**
 * 决策副本2D地图
 * 支持同步结果展示，也预留实时流式节点接入能力
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import promptAction from '@ohos.promptAction'
import { ApiConfig } from '../config/ApiConfig'
import { WebSocketUtil } from '../utils/WebSocketUtil'

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

interface DungeonOption {
  option_id: string
  title: string
  description: string
  timeline: TimelineEvent[]
  final_score: number
  risk_level: number
}

interface DungeonData {
  dungeon_id: string
  user_id: string
  title: string
  description: string
  options: DungeonOption[]
  recommendation: string
  created_at: string
}

interface NodePosition {
  x: number
  y: number
}

interface MapNode {
  id: string
  parentId: string
  title: string
  description: string
  month: number
  probability: number
  position: NodePosition
  optionIndex: number
  optionTitle: string
  color: string
  riskTag: string
  opportunityTag: string
  eventType: string
  impact: Record<string, number>
}

interface StreamRequestOption {
  title: string
  description: string
}

interface StreamRequestPayload {
  session_id: string
  options: StreamRequestOption[]
}

@Entry
@Component
struct DecisionDungeon2DMap {
  @State dungeonData: DungeonData | null = null
  @State isLoading: boolean = false
  @State mapNodes: MapNode[] = []
  @State selectedNodeId: string = ''
  @State streamStatus: string = ''
  private dungeonId: string = ''
  private userId: string = ''
  private ws: WebSocketUtil | null = null
  private canvasWidth: number = 1400
  private canvasHeight: number = 1100

  aboutToAppear() {
    const params = router.getParams() as Record<string, string>
    if (params?.simulationData) {
      try {
        const simData = JSON.parse(params.simulationData) as Record<string, Object>
        this.dungeonData = this.convertSimulationToDungeon(simData, params.question || '')
        this.generateMapNodes()
      } catch (error) {
        console.error('解析模拟数据失败:', (error as Error).message)
      }
      return
    }

    if (params?.dungeonId) {
      this.dungeonId = params.dungeonId
      this.loadDungeonData()
    }
    if (params?.userId) {
      this.userId = params.userId
    }
  }

  aboutToDisappear() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private convertSimulationToDungeon(simData: Record<string, Object>, question: string): DungeonData {
    return {
      dungeon_id: simData.simulation_id as string || 'temp_dungeon',
      user_id: simData.user_id as string || this.userId,
      title: question,
      description: '基于个性化推演生成的决策副本',
      options: simData.options as DungeonOption[],
      recommendation: simData.recommendation as string || '',
      created_at: simData.created_at as string || new Date().toISOString()
    }
  }

  private async startStreamSimulation() {
    if (!this.dungeonId) {
      this.streamStatus = '缺少会话信息，无法启动实时推演'
      return
    }

    this.streamStatus = '正在连接实时推演通道'
    this.mapNodes = []
    this.selectedNodeId = ''

    try {
      this.ws = new WebSocketUtil()

      this.ws.onMessage((data: string) => {
        setTimeout(() => {
          try {
            const event = JSON.parse(data) as Record<string, Object>
            const type = event.type as string
            if (type === 'start') {
              this.streamStatus = '正在生成副本节点'
            } else if (type === 'option_start') {
              this.streamStatus = `正在推演 ${event.title as string}`
            } else if (type === 'node') {
              const node = event.node as Record<string, Object>
              const optionId = event.option_id as string
              const optionTitle = event.option_title as string
              const optionIndex = this.findOptionIndex(optionId, optionTitle)
              this.ensureOptionRoot(optionIndex, optionTitle)
              const eventIndex = this.countOptionNodes(optionIndex)
              const baseY = 160 + optionIndex * 220
              const mapNode: MapNode = {
                id: (node.event_id as string) || `${optionId}_${eventIndex}`,
                parentId: (node.parent_event_id as string) || `root_${optionIndex}`,
                title: `第${node.month as number}月`,
                description: (node.event as string) || '',
                month: node.month as number,
                probability: (node.probability as number) || 0,
                position: {
                  x: 140 + (eventIndex + 1) * 250,
                  y: baseY + ((eventIndex % 2 === 0) ? -34 : 34)
                },
                optionIndex,
                optionTitle,
                color: this.getOptionColor(optionIndex),
                riskTag: (node.risk_tag as string) || 'medium',
                opportunityTag: (node.opportunity_tag as string) || 'medium',
                eventType: (node.event_type as string) || 'general',
                impact: node.impact as Record<string, number>
              }
              this.mapNodes = [...this.mapNodes, mapNode]
              this.selectedNodeId = mapNode.id
            } else if (type === 'recommendation') {
              if (this.dungeonData) {
                this.dungeonData = {
                  dungeon_id: this.dungeonData.dungeon_id,
                  user_id: this.dungeonData.user_id,
                  title: this.dungeonData.title,
                  description: this.dungeonData.description,
                  options: this.dungeonData.options,
                  recommendation: (event.content as string) || '',
                  created_at: this.dungeonData.created_at
                }
              }
              this.streamStatus = '正在收束世界线'
            } else if (type === 'done') {
              this.streamStatus = '推演完成'
              if (this.ws) {
                this.ws.close()
                this.ws = null
              }
            } else if (type === 'error') {
              this.streamStatus = '推演失败'
              promptAction.showToast({ message: event.content as string, duration: 2500 })
              if (this.ws) {
                this.ws.close()
                this.ws = null
              }
            }
          } catch (err) {
            console.error('实时推演事件解析失败: ' + (err as Error).message)
          }
        }, 0)
      })

      this.ws.onError((error: string) => {
        this.streamStatus = '连接失败'
        console.error('实时推演 WebSocket 错误: ' + error)
      })

      this.ws.onClose(() => {
        console.info('实时推演 WebSocket 已关闭')
      })

      await this.ws.connect('/api/decision/enhanced/ws/simulate')
      const streamOptions: StreamRequestOption[] = this.dungeonData ? this.dungeonData.options.map((item: DungeonOption): StreamRequestOption => {
        return { title: item.title, description: item.description }
      }) : []
      const payload: StreamRequestPayload = {
        session_id: this.dungeonId,
        options: streamOptions
      }
      this.ws.send(payload)
    } catch (error) {
      this.streamStatus = '实时推演启动失败'
      console.error('实时推演启动失败: ' + (error as Error).message)
    }
  }

  private ensureOptionRoot(optionIndex: number, optionTitle: string) {
    const rootId = `root_${optionIndex}`
    const exists = this.mapNodes.some((item: MapNode) => item.id === rootId)
    if (!exists) {
      const rootNode: MapNode = {
        id: rootId,
        parentId: '',
        title: optionTitle,
        description: '推演起点',
        month: 0,
        probability: 1,
        position: { x: 140, y: 160 + optionIndex * 220 },
        optionIndex,
        optionTitle,
        color: this.getOptionColor(optionIndex),
        riskTag: 'medium',
        opportunityTag: 'medium',
        eventType: 'origin',
        impact: {}
      }
      this.mapNodes = this.mapNodes.concat([rootNode])
    }
  }

  private findOptionIndex(optionId: string, optionTitle: string): number {
    const existing = this.mapNodes.find((item: MapNode) => item.optionTitle === optionTitle)
    if (existing) {
      return existing.optionIndex
    }
    const match = optionId.match(/option_(\d+)/)
    if (match && match[1]) {
      return Number(match[1]) - 1
    }
    return 0
  }

  private countOptionNodes(optionIndex: number): number {
    let count = 0
    this.mapNodes.forEach((item: MapNode) => {
      if (item.optionIndex === optionIndex && !item.id.startsWith('root_')) {
        count += 1
      }
    })
    return count
  }

  private async loadDungeonData() {
    this.isLoading = true
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        ApiConfig.getApiUrl(`/api/decision/result/${this.dungeonId}`),
        {
          method: http.RequestMethod.GET,
          header: { 'Content-Type': 'application/json' },
          connectTimeout: 30000,
          readTimeout: 30000
        }
      )
      httpRequest.destroy()
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if (result.code === 200 && result.data) {
          const simData = result.data as Record<string, Object>
          this.dungeonData = this.convertSimulationToDungeon(simData, this.dungeonId)
          this.generateMapNodes()
        }
      }
    } catch (error) {
      console.error('加载副本失败:', (error as Error).message)
      promptAction.showToast({ message: '加载副本失败', duration: 2000 })
    }
    this.isLoading = false
  }

  private generateMapNodes() {
    if (!this.dungeonData) return

    const nodes: MapNode[] = []
    const topY = 160
    const laneGap = 220
    const startX = 140
    const stepX = 250

    this.dungeonData.options.forEach((option: DungeonOption, optionIndex: number) => {
      const color = this.getOptionColor(optionIndex)
      const baseY = topY + optionIndex * laneGap
      let previousId = `root_${optionIndex}`

      nodes.push({
        id: previousId,
        parentId: '',
        title: option.title,
        description: option.description,
        month: 0,
        probability: 1,
        position: { x: startX, y: baseY },
        optionIndex,
        optionTitle: option.title,
        color,
        riskTag: this.getRiskTag(option.risk_level),
        opportunityTag: 'medium',
        eventType: 'origin',
        impact: {}
      })

      option.timeline.forEach((event: TimelineEvent, eventIndex: number) => {
        const nodeId = event.event_id ? event.event_id : `${option.option_id}_${eventIndex}`
        nodes.push({
          id: nodeId,
          parentId: event.parent_event_id ? event.parent_event_id : previousId,
          title: `第${event.month}月`,
          description: event.event,
          month: event.month,
          probability: event.probability,
          position: {
            x: startX + (eventIndex + 1) * stepX,
            y: baseY + ((eventIndex % 2 === 0) ? -34 : 34)
          },
          optionIndex,
          optionTitle: option.title,
          color,
          riskTag: event.risk_tag ? event.risk_tag : 'medium',
          opportunityTag: event.opportunity_tag ? event.opportunity_tag : 'medium',
          eventType: event.event_type ? event.event_type : 'general',
          impact: event.impact
        })
        previousId = nodeId
      })
    })

    this.mapNodes = nodes
    this.canvasHeight = Math.max(1000, topY + this.dungeonData.options.length * laneGap + 120)
    if (nodes.length > 0) {
      this.selectedNodeId = nodes[0].id
    }
  }

  build() {
    Column() {
      this.HeaderView()
      if (this.isLoading) {
        Column({ space: 14 }) {
          LoadingProgress()
            .width(40)
            .height(40)
            .color('#7AC7FF')
          Text('正在构建副本地图')
            .fontSize(18)
            .fontWeight(700)
            .fontColor('#F4F7FB')
        }
        .layoutWeight(1)
        .width('100%')
        .justifyContent(FlexAlign.Center)
      } else {
        Row() {
          this.GraphCanvas()
          this.DetailPanel()
        }
        .layoutWeight(1)
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
        Text('决策副本地图')
          .fontSize(20)
          .fontWeight(700)
          .fontColor('#F4F7FB')
        Text(this.dungeonData ? this.dungeonData.title : '等待数据')
          .fontSize(12)
          .fontColor('#7F8A9A')
        if (this.streamStatus !== '') {
          Text(this.streamStatus)
            .fontSize(11)
            .fontColor('#7AC7FF')
        }
      }
      .alignItems(HorizontalAlign.Start)
      .layoutWeight(1)
      .margin({ left: 12 })
    }
    .width('100%')
    .padding({ left: 16, right: 16, top: 18, bottom: 14 })
    .backgroundColor('rgba(9,17,31,0.96)')
  }

  @Builder
  GraphCanvas() {
    Scroll() {
      Stack() {
        Column()
          .width(this.canvasWidth)
          .height(this.canvasHeight)
          .backgroundColor('#09111F')

        ForEach(this.mapNodes, (node: MapNode) => {
          this.GraphNodeView(node)
        })
      }
      .width(this.canvasWidth)
      .height(this.canvasHeight)
    }
    .layoutWeight(1)
    .scrollBar(BarState.Auto)
  }

  @Builder
  GraphNodeView(node: MapNode) {
    Column({ space: 8 }) {
      Stack() {
        Column()
          .width(node.id.startsWith('root_') ? 56 : 42)
          .height(node.id.startsWith('root_') ? 56 : 42)
          .backgroundColor(node.color)
          .opacity(node.id === this.selectedNodeId ? 0.95 : 0.78)
          .borderRadius(node.id.startsWith('root_') ? 14 : 21)
          .border({ width: node.id === this.selectedNodeId ? 2 : 1, color: node.id === this.selectedNodeId ? '#FFFFFF' : 'rgba(255,255,255,0.18)' })

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
        Text(node.description)
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
    .position({ x: node.position.x, y: node.position.y })
    .width(190)
    .onClick(() => {
      this.selectedNodeId = node.id
    })
  }

  @Builder
  DetailPanel() {
    Column({ space: 14 }) {
      if (this.dungeonData) {
        Column({ space: 8 }) {
          Text('副本概览')
            .fontSize(12)
            .fontColor('#7F8A9A')
          Text(this.dungeonData.description)
            .fontSize(14)
            .fontColor('#DCE5F1')
            .lineHeight(22)
        }
        .width('100%')
        .alignItems(HorizontalAlign.Start)
        .padding(14)
        .backgroundColor('rgba(255,255,255,0.04)')
        .borderRadius(16)

        ForEach(this.mapNodes, (item: MapNode) => {
          if (item.id === this.selectedNodeId) {
            Column({ space: 10 }) {
              Text('当前节点')
                .fontSize(12)
                .fontColor('#7F8A9A')
              Text(item.title)
                .fontSize(16)
                .fontWeight(700)
                .fontColor('#F4F7FB')
              Text(item.description)
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
          Text(this.dungeonData.recommendation)
            .fontSize(13)
            .fontColor('#DCE5F1')
            .lineHeight(21)
        }
        .width('100%')
        .padding(14)
        .backgroundColor('rgba(122,199,255,0.08)')
        .borderRadius(16)
        .alignItems(HorizontalAlign.Start)

        Button('实时推演模式')
          .width('100%')
          .height(42)
          .fontSize(14)
          .fontWeight(600)
          .fontColor('#09111F')
          .backgroundColor('#7AC7FF')
          .borderRadius(12)
          .onClick(() => {
            this.startStreamSimulation()
          })
      }
    }
    .width(320)
    .height('100%')
    .padding(16)
    .backgroundColor('rgba(255,255,255,0.03)')
  }

  private getOptionColor(index: number): string {
    const colors = ['#5B8FF9', '#5AD8A6', '#F6BD16', '#E8684A']
    return colors[index % colors.length]
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
}
