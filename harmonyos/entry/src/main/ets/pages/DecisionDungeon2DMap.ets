/**
 * 决策副本2D地图 — 思维导图式闯关可视化
 *
 * 特性：
 *   - 以思维导图/链条方式展示决策路径
 *   - 节点逐个动画出现（闯关感）
 *   - Canvas 绘制连线（贝塞尔曲线）
 *   - 分支节点从父节点分叉
 *   - 点击节点查看详情面板
 *   - 支持 WebSocket 实时流式推演
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import promptAction from '@ohos.promptAction'
import { ApiConfig } from '../config/ApiConfig'
import { WebSocketUtil } from '../utils/WebSocketUtil'

// ==================== 数据接口 ====================

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
  isBranch: boolean
  revealed: boolean
  finalScore: number
}

interface EdgeLine {
  fromX: number
  fromY: number
  toX: number
  toY: number
  color: string
  revealed: boolean
}

interface StreamRequestOption {
  title: string
  description: string
}

interface StreamRequestPayload {
  session_id: string
  options: StreamRequestOption[]
}

// ==================== 页面组件 ====================

@Entry
@Component
struct DecisionDungeon2DMap {
  @State dungeonData: DungeonData | null = null
  @State isLoading: boolean = false
  @State mapNodes: MapNode[] = []
  @State edges: EdgeLine[] = []
  @State selectedNodeId: string = ''
  @State streamStatus: string = ''
  @State revealIndex: number = 0
  @State isRevealing: boolean = false
  @State showRecommendation: boolean = false
  private dungeonId: string = ''
  private userId: string = ''
  private ws: WebSocketUtil | null = null
  private canvasWidth: number = 1600
  private canvasHeight: number = 1200
  private revealTimer: number = -1
  private canvasContext: CanvasRenderingContext2D = new CanvasRenderingContext2D(
    new RenderingContextSettings(true)
  )

  aboutToAppear() {
    const params = router.getParams() as Record<string, string>
    if (params?.simulationData) {
      try {
        const simData = JSON.parse(params.simulationData) as Record<string, Object>
        this.dungeonData = this.convertSimulationToDungeon(simData, params.question || '')
        this.generateMapNodes()
        this.startRevealAnimation()
      } catch (error) {
        console.error('解析模拟数据失败:', (error as Error).message)
      }
      return
    }
    if (params?.dungeonId) {
      this.dungeonId = params.dungeonId
      this.userId = params.userId || ''
      this.loadDungeonData()
    }
  }

  aboutToDisappear() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    if (this.revealTimer !== -1) {
      clearInterval(this.revealTimer)
      this.revealTimer = -1
    }
  }

  // ==================== 数据转换 ====================

  private convertSimulationToDungeon(simData: Record<string, Object>, question: string): DungeonData {
    return {
      dungeon_id: simData.simulation_id as string || 'temp_dungeon',
      user_id: simData.user_id as string || this.userId,
      title: question,
      description: '基于个性化 LoRA 推演生成的决策副本',
      options: simData.options as DungeonOption[],
      recommendation: simData.recommendation as string || '',
      created_at: simData.created_at as string || new Date().toISOString()
    }
  }

  // ==================== 节点布局 ====================

  private generateMapNodes() {
    if (!this.dungeonData) return

    const nodes: MapNode[] = []
    const edgeLines: EdgeLine[] = []
    const originX = 120
    const laneGap = 280
    const stepX = 220
    const topY = 180

    this.dungeonData.options.forEach((option: DungeonOption, optionIndex: number) => {
      const color = this.getOptionColor(optionIndex)
      const baseY = topY + optionIndex * laneGap
      const rootId = `root_${optionIndex}`

      // 根节点
      nodes.push({
        id: rootId,
        parentId: '',
        title: option.title,
        description: option.description || '推演起点',
        month: 0,
        probability: 1,
        position: { x: originX, y: baseY },
        optionIndex,
        optionTitle: option.title,
        color,
        riskTag: this.getRiskTag(option.risk_level),
        opportunityTag: 'medium',
        eventType: 'origin',
        impact: {},
        isBranch: false,
        revealed: false,
        finalScore: option.final_score
      })

      // 主时间线节点
      let mainIndex = 0
      let previousId = rootId
      const mainEvents = option.timeline.filter(
        (e: TimelineEvent) => !e.branch_group || e.branch_group === 'main' || !e.branch_group.includes('fork')
      )
      const branchEvents = option.timeline.filter(
        (e: TimelineEvent) => e.branch_group && e.branch_group.includes('fork')
      )

      mainEvents.forEach((event: TimelineEvent, eventIndex: number) => {
        const nodeId = event.event_id || `${option.option_id}_main_${eventIndex}`
        const nx = originX + (eventIndex + 1) * stepX
        const ny = baseY + (eventIndex % 2 === 0 ? -28 : 28)
        const parentNodeId = event.parent_event_id || previousId

        nodes.push({
          id: nodeId,
          parentId: parentNodeId,
          title: `第${event.month}月`,
          description: event.event,
          month: event.month,
          probability: event.probability,
          position: { x: nx, y: ny },
          optionIndex,
          optionTitle: option.title,
          color,
          riskTag: event.risk_tag || 'medium',
          opportunityTag: event.opportunity_tag || 'medium',
          eventType: event.event_type || 'general',
          impact: event.impact,
          isBranch: false,
          revealed: false,
          finalScore: option.final_score
        })

        // 连线
        const parentNode = nodes.find((n: MapNode) => n.id === parentNodeId)
        if (parentNode) {
          edgeLines.push({
            fromX: parentNode.position.x + 85,
            fromY: parentNode.position.y + 30,
            toX: nx,
            toY: ny + 30,
            color,
            revealed: false
          })
        }

        previousId = nodeId
        mainIndex = eventIndex
      })

      // 分支节点 — 从父节点分叉出去
      branchEvents.forEach((event: TimelineEvent, bIdx: number) => {
        const nodeId = event.event_id || `${option.option_id}_branch_${bIdx}`
        const parentNodeId = event.parent_event_id || previousId
        const parentNode = nodes.find((n: MapNode) => n.id === parentNodeId)
        const isPositive = (event.opportunity_tag === 'high' || event.risk_tag === 'low')
        const forkOffsetY = isPositive ? -90 : 90
        const px = parentNode ? parentNode.position.x : originX + (mainIndex + 1) * stepX
        const py = parentNode ? parentNode.position.y : baseY
        const nx = px + 200
        const ny = py + forkOffsetY

        nodes.push({
          id: nodeId,
          parentId: parentNodeId,
          title: `第${event.month}月`,
          description: event.event,
          month: event.month,
          probability: event.probability,
          position: { x: nx, y: ny },
          optionIndex,
          optionTitle: option.title,
          color: isPositive ? '#4DD0A8' : '#FF6B6B',
          riskTag: event.risk_tag || 'medium',
          opportunityTag: event.opportunity_tag || 'medium',
          eventType: event.event_type || 'general',
          impact: event.impact,
          isBranch: true,
          revealed: false,
          finalScore: option.final_score
        })

        if (parentNode) {
          edgeLines.push({
            fromX: parentNode.position.x + 85,
            fromY: parentNode.position.y + 30,
            toX: nx,
            toY: ny + 30,
            color: isPositive ? '#4DD0A8' : '#FF6B6B',
            revealed: false
          })
        }
      })
    })

    this.mapNodes = nodes
    this.edges = edgeLines
    // 动态画布大小
    const maxX = Math.max(...nodes.map((n: MapNode) => n.position.x)) + 300
    const maxY = Math.max(...nodes.map((n: MapNode) => n.position.y)) + 200
    this.canvasWidth = Math.max(1400, maxX)
    this.canvasHeight = Math.max(1000, maxY)
  }

  // ==================== 逐步揭示动画 ====================

  private startRevealAnimation() {
    this.isRevealing = true
    this.revealIndex = 0
    this.showRecommendation = false

    this.revealTimer = setInterval(() => {
      if (this.revealIndex < this.mapNodes.length) {
        // 揭示当前节点
        const updatedNodes = this.mapNodes.map((n: MapNode, idx: number): MapNode => {
          if (idx === this.revealIndex) {
            return {
              id: n.id, parentId: n.parentId, title: n.title, description: n.description,
              month: n.month, probability: n.probability, position: n.position,
              optionIndex: n.optionIndex, optionTitle: n.optionTitle, color: n.color,
              riskTag: n.riskTag, opportunityTag: n.opportunityTag, eventType: n.eventType,
              impact: n.impact, isBranch: n.isBranch, revealed: true, finalScore: n.finalScore
            }
          }
          return n
        })
        this.mapNodes = updatedNodes

        // 揭示对应连线
        if (this.revealIndex > 0 && this.revealIndex - 1 < this.edges.length) {
          const updatedEdges = this.edges.map((e: EdgeLine, idx: number): EdgeLine => {
            if (idx === this.revealIndex - 1) {
              return {
                fromX: e.fromX, fromY: e.fromY, toX: e.toX, toY: e.toY,
                color: e.color, revealed: true
              }
            }
            return e
          })
          this.edges = updatedEdges
        }

        // 自动选中当前节点
        this.selectedNodeId = this.mapNodes[this.revealIndex].id
        this.revealIndex++
        // 重绘连线
        this.drawEdges()
      } else {
        // 动画结束
        clearInterval(this.revealTimer)
        this.revealTimer = -1
        this.isRevealing = false
        this.showRecommendation = true
        // 确保所有边都揭示
        this.edges = this.edges.map((e: EdgeLine): EdgeLine => {
          return { fromX: e.fromX, fromY: e.fromY, toX: e.toX, toY: e.toY, color: e.color, revealed: true }
        })
        this.drawEdges()
      }
    }, 650)
  }

  // ==================== Canvas 连线绘制 ====================

  private drawEdges() {
    const ctx = this.canvasContext
    ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight)

    this.edges.forEach((edge: EdgeLine) => {
      if (!edge.revealed) return
      ctx.beginPath()
      ctx.strokeStyle = edge.color
      ctx.lineWidth = 2.5
      ctx.globalAlpha = 0.7
      // 贝塞尔曲线连线
      const midX = (edge.fromX + edge.toX) / 2
      ctx.moveTo(edge.fromX, edge.fromY)
      ctx.bezierCurveTo(midX, edge.fromY, midX, edge.toY, edge.toX, edge.toY)
      ctx.stroke()
      ctx.globalAlpha = 1.0

      // 箭头
      const angle = Math.atan2(edge.toY - edge.fromY, edge.toX - edge.fromX)
      const arrowLen = 8
      ctx.beginPath()
      ctx.fillStyle = edge.color
      ctx.moveTo(edge.toX, edge.toY)
      ctx.lineTo(
        edge.toX - arrowLen * Math.cos(angle - Math.PI / 6),
        edge.toY - arrowLen * Math.sin(angle - Math.PI / 6)
      )
      ctx.lineTo(
        edge.toX - arrowLen * Math.cos(angle + Math.PI / 6),
        edge.toY - arrowLen * Math.sin(angle + Math.PI / 6)
      )
      ctx.closePath()
      ctx.fill()
    })
  }

  // ==================== WebSocket 实时推演 ====================

  private async startStreamSimulation() {
    if (!this.dungeonId) {
      this.streamStatus = '缺少会话信息'
      return
    }
    this.streamStatus = '正在连接推演通道...'
    this.mapNodes = []
    this.edges = []
    this.selectedNodeId = ''
    this.showRecommendation = false

    try {
      this.ws = new WebSocketUtil()

      this.ws.onMessage((data: string) => {
        setTimeout(() => {
          try {
            const event = JSON.parse(data) as Record<string, Object>
            const type = event.type as string
            if (type === 'start') {
              this.streamStatus = '正在生成副本节点...'
            } else if (type === 'option_start') {
              this.streamStatus = `推演中: ${event.title as string}`
            } else if (type === 'node') {
              const node = event.node as Record<string, Object>
              const optionTitle = event.option_title as string
              const optionIndex = this.findOptionIndex(event.option_id as string, optionTitle)
              this.ensureOptionRoot(optionIndex, optionTitle)
              const eventIndex = this.countOptionNodes(optionIndex)
              const baseY = 180 + optionIndex * 280
              const isBranch = ((node.branch_group as string) || '').includes('fork')
              const parentId = (node.parent_event_id as string) || `root_${optionIndex}`
              const parentNode = this.mapNodes.find((n: MapNode) => n.id === parentId)
              let nx: number
              let ny: number
              if (isBranch && parentNode) {
                const isPositive = (node.risk_tag as string) === 'low'
                nx = parentNode.position.x + 200
                ny = parentNode.position.y + (isPositive ? -90 : 90)
              } else {
                nx = 120 + (eventIndex + 1) * 220
                ny = baseY + (eventIndex % 2 === 0 ? -28 : 28)
              }
              const color = isBranch
                ? ((node.risk_tag as string) === 'low' ? '#4DD0A8' : '#FF6B6B')
                : this.getOptionColor(optionIndex)
              const mapNode: MapNode = {
                id: (node.event_id as string) || `stream_${optionIndex}_${eventIndex}`,
                parentId,
                title: `第${node.month as number}月`,
                description: (node.event as string) || '',
                month: node.month as number,
                probability: (node.probability as number) || 0,
                position: { x: nx, y: ny },
                optionIndex,
                optionTitle,
                color,
                riskTag: (node.risk_tag as string) || 'medium',
                opportunityTag: (node.opportunity_tag as string) || 'medium',
                eventType: (node.event_type as string) || 'general',
                impact: node.impact as Record<string, number>,
                isBranch,
                revealed: true,
                finalScore: 0
              }
              this.mapNodes = [...this.mapNodes, mapNode]
              // 添加连线
              if (parentNode) {
                this.edges = [...this.edges, {
                  fromX: parentNode.position.x + 85,
                  fromY: parentNode.position.y + 30,
                  toX: nx,
                  toY: ny + 30,
                  color,
                  revealed: true
                }]
              }
              this.selectedNodeId = mapNode.id
              this.drawEdges()
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
              this.streamStatus = '正在收束世界线...'
              this.showRecommendation = true
            } else if (type === 'done') {
              this.streamStatus = '推演完成'
              if (this.ws) { this.ws.close(); this.ws = null }
            } else if (type === 'error') {
              this.streamStatus = '推演失败'
              promptAction.showToast({ message: event.content as string, duration: 2500 })
              if (this.ws) { this.ws.close(); this.ws = null }
            }
          } catch (err) {
            console.error('推演事件解析失败: ' + (err as Error).message)
          }
        }, 0)
      })

      this.ws.onError((error: string) => {
        this.streamStatus = '连接失败'
        console.error('WebSocket 错误: ' + error)
      })

      this.ws.onClose(() => {
        console.info('推演 WebSocket 已关闭')
      })

      await this.ws.connect('/api/decision/enhanced/ws/simulate')
      const streamOptions: StreamRequestOption[] = this.dungeonData
        ? this.dungeonData.options.map((item: DungeonOption): StreamRequestOption => {
          return { title: item.title, description: item.description }
        })
        : []
      this.ws.send({ session_id: this.dungeonId, options: streamOptions } as Object)
    } catch (error) {
      this.streamStatus = '推演启动失败'
      console.error('推演启动失败: ' + (error as Error).message)
    }
  }

  private ensureOptionRoot(optionIndex: number, optionTitle: string) {
    const rootId = `root_${optionIndex}`
    if (this.mapNodes.some((n: MapNode) => n.id === rootId)) return
    const rootNode: MapNode = {
      id: rootId, parentId: '', title: optionTitle, description: '推演起点',
      month: 0, probability: 1,
      position: { x: 120, y: 180 + optionIndex * 280 },
      optionIndex, optionTitle, color: this.getOptionColor(optionIndex),
      riskTag: 'medium', opportunityTag: 'medium', eventType: 'origin',
      impact: {}, isBranch: false, revealed: true, finalScore: 0
    }
    this.mapNodes = [...this.mapNodes, rootNode]
  }

  private findOptionIndex(optionId: string, optionTitle: string): number {
    const existing = this.mapNodes.find((n: MapNode) => n.optionTitle === optionTitle)
    if (existing) return existing.optionIndex
    const match = optionId.match(/option_(\d+)/)
    return match && match[1] ? Number(match[1]) - 1 : 0
  }

  private countOptionNodes(optionIndex: number): number {
    let count = 0
    this.mapNodes.forEach((n: MapNode) => {
      if (n.optionIndex === optionIndex && !n.id.startsWith('root_')) count++
    })
    return count
  }

  // ==================== 数据加载 ====================

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
          this.startRevealAnimation()
        }
      }
    } catch (error) {
      console.error('加载副本失败:', (error as Error).message)
      promptAction.showToast({ message: '加载副本失败', duration: 2000 })
    }
    this.isLoading = false
  }

  // ==================== UI 构建 ====================

  build() {
    Column() {
      this.HeaderBar()

      if (this.isLoading) {
        Column({ space: 16 }) {
          LoadingProgress().width(44).height(44).color('#7AC7FF')
          Text('正在构建决策副本...').fontSize(16).fontWeight(600).fontColor('#B0C4DE')
        }
        .layoutWeight(1).width('100%').justifyContent(FlexAlign.Center)
      } else {
        Row() {
          this.MindMapCanvas()
          this.SidePanel()
        }
        .layoutWeight(1)
      }
    }
    .width('100%').height('100%').backgroundColor('#0A0F1E')
  }

  @Builder
  HeaderBar() {
    Row() {
      Button({ type: ButtonType.Circle }) {
        Text('←').fontSize(22).fontColor('#E0E8F5').fontWeight(700)
      }
      .width(40).height(40)
      .backgroundColor('rgba(255,255,255,0.06)')
      .onClick(() => router.back())

      Column({ space: 2 }) {
        Text('决策副本').fontSize(20).fontWeight(700).fontColor('#F0F4FA')
        if (this.dungeonData) {
          Text(this.dungeonData.title).fontSize(12).fontColor('#6B7A90').maxLines(1)
        }
        if (this.streamStatus !== '') {
          Text(this.streamStatus).fontSize(11).fontColor('#7AC7FF')
        }
        if (this.isRevealing) {
          Text('节点展开中...').fontSize(11).fontColor('#F5B041')
        }
      }
      .alignItems(HorizontalAlign.Start).layoutWeight(1).margin({ left: 12 })

      // 图例
      Row({ space: 10 }) {
        this.LegendDot('#5B8FF9', '主线')
        this.LegendDot('#4DD0A8', '乐观')
        this.LegendDot('#FF6B6B', '风险')
      }
    }
    .width('100%')
    .padding({ left: 16, right: 16, top: 16, bottom: 12 })
    .backgroundColor('rgba(10,15,30,0.95)')
  }

  @Builder
  LegendDot(color: string, label: string) {
    Row({ space: 4 }) {
      Column().width(10).height(10).borderRadius(5).backgroundColor(color)
      Text(label).fontSize(10).fontColor('#8899AA')
    }
  }

  @Builder
  MindMapCanvas() {
    Scroll() {
      Stack() {
        // Canvas 连线层
        Canvas(this.canvasContext)
          .width(this.canvasWidth)
          .height(this.canvasHeight)
          .backgroundColor('#0A0F1E')
          .onReady(() => {
            this.drawEdges()
          })

        // 节点层
        ForEach(this.mapNodes, (node: MapNode) => {
          if (node.revealed) {
            this.MindMapNode(node)
          }
        })
      }
      .width(this.canvasWidth)
      .height(this.canvasHeight)
    }
    .layoutWeight(1)
    .scrollBar(BarState.Auto)
  }

  @Builder
  MindMapNode(node: MapNode) {
    Column({ space: 6 }) {
      // 节点圆形头
      Stack() {
        Column()
          .width(node.id.startsWith('root_') ? 52 : (node.isBranch ? 36 : 40))
          .height(node.id.startsWith('root_') ? 52 : (node.isBranch ? 36 : 40))
          .backgroundColor(node.color)
          .opacity(node.id === this.selectedNodeId ? 1.0 : 0.8)
          .borderRadius(node.id.startsWith('root_') ? 12 : 20)
          .border({
            width: node.id === this.selectedNodeId ? 2.5 : 1,
            color: node.id === this.selectedNodeId ? '#FFFFFF' : 'rgba(255,255,255,0.15)'
          })
          .shadow({
            radius: node.id === this.selectedNodeId ? 16 : 6,
            color: node.color,
            offsetX: 0,
            offsetY: 0
          })

        Text(node.month > 0 ? `${node.month}` : '起')
          .fontSize(node.id.startsWith('root_') ? 14 : 12)
          .fontWeight(700)
          .fontColor('#FFFFFF')
      }

      // 节点信息卡片
      Column({ space: 4 }) {
        Text(node.title)
          .fontSize(12).fontWeight(700).fontColor('#E8ECF3')
          .maxLines(1)
        Text(node.description)
          .fontSize(10).fontColor('#8899AA').lineHeight(14)
          .maxLines(node.isBranch ? 2 : 3)
          .textOverflow({ overflow: TextOverflow.Ellipsis })

        // 标签行
        Row({ space: 4 }) {
          if (node.riskTag === 'high') {
            Text('⚠ 高风险').fontSize(9).fontColor('#FF6B6B')
              .padding({ left: 4, right: 4, top: 2, bottom: 2 })
              .backgroundColor('rgba(255,107,107,0.12)').borderRadius(4)
          }
          if (node.opportunityTag === 'high') {
            Text('✦ 机遇').fontSize(9).fontColor('#4DD0A8')
              .padding({ left: 4, right: 4, top: 2, bottom: 2 })
              .backgroundColor('rgba(77,208,168,0.12)').borderRadius(4)
          }
          Text(`${(node.probability * 100).toFixed(0)}%`)
            .fontSize(9).fontColor('#6B7A90')
        }
      }
      .width(node.isBranch ? 150 : 170)
      .padding(10)
      .backgroundColor(
        node.id === this.selectedNodeId
          ? 'rgba(122,199,255,0.12)'
          : 'rgba(255,255,255,0.04)'
      )
      .borderRadius(12)
      .border({
        width: 1,
        color: node.id === this.selectedNodeId
          ? 'rgba(122,199,255,0.3)'
          : 'rgba(255,255,255,0.06)'
      })
      .alignItems(HorizontalAlign.Start)
    }
    .position({ x: node.position.x, y: node.position.y })
    .width(node.isBranch ? 160 : 180)
    .onClick(() => {
      this.selectedNodeId = node.id
    })
    .animation({ duration: 350, curve: Curve.EaseOut })
  }

  // ==================== 右侧详情面板 ====================

  @Builder
  SidePanel() {
    Column({ space: 14 }) {
      if (this.dungeonData) {
        // 副本概览
        Column({ space: 6 }) {
          Text('副本概览').fontSize(11).fontColor('#6B7A90')
          Text(this.dungeonData.title).fontSize(14).fontWeight(600).fontColor('#DCE5F1').maxLines(2)
          Text(`${this.dungeonData.options.length} 条世界线`)
            .fontSize(11).fontColor('#5B8FF9')
        }
        .width('100%').padding(12)
        .backgroundColor('rgba(255,255,255,0.04)').borderRadius(14)
        .alignItems(HorizontalAlign.Start)

        // 选项得分概览
        ForEach(this.dungeonData.options, (option: DungeonOption, idx: number) => {
          Row({ space: 8 }) {
            Column()
              .width(8).height(8).borderRadius(4)
              .backgroundColor(this.getOptionColor(idx))
            Text(option.title).fontSize(12).fontColor('#B0C4DE').layoutWeight(1).maxLines(1)
            Text(`${option.final_score.toFixed(0)}分`).fontSize(12).fontWeight(600)
              .fontColor(this.getOptionColor(idx))
          }
          .width('100%').padding({ left: 12, right: 12, top: 6, bottom: 6 })
        })

        // 当前选中节点详情
        ForEach(this.mapNodes, (node: MapNode) => {
          if (node.id === this.selectedNodeId) {
            Column({ space: 8 }) {
              Text('当前节点').fontSize(11).fontColor('#6B7A90')
              Text(node.title).fontSize(16).fontWeight(700).fontColor('#F0F4FA')
              Text(node.description).fontSize(12).fontColor('#A0B0C0').lineHeight(18)

              // 影响维度
              if (Object.keys(node.impact).length > 0) {
                Column({ space: 4 }) {
                  Text('影响维度').fontSize(10).fontColor('#6B7A90')
                  ForEach(Object.entries(node.impact), (entry: [string, number]) => {
                    Row({ space: 6 }) {
                      Text(entry[0]).fontSize(11).fontColor('#8899AA').width(36)
                      // 简单条形图
                      Row() {
                        Column()
                          .width(`${Math.abs(entry[1]) * 100}%`)
                          .height(6)
                          .borderRadius(3)
                          .backgroundColor(entry[1] >= 0 ? '#4DD0A8' : '#FF6B6B')
                      }
                      .width(80).height(6).borderRadius(3)
                      .backgroundColor('rgba(255,255,255,0.06)')
                      Text(`${entry[1] > 0 ? '+' : ''}${entry[1].toFixed(1)}`)
                        .fontSize(10)
                        .fontColor(entry[1] >= 0 ? '#4DD0A8' : '#FF6B6B')
                    }
                    .width('100%')
                  })
                }
                .width('100%')
              }

              Row({ space: 8 }) {
                Text(`风险 ${node.riskTag}`)
                  .fontSize(10).fontColor(this.getRiskColor(node.riskTag))
                  .padding({ left: 6, right: 6, top: 3, bottom: 3 })
                  .backgroundColor('rgba(255,255,255,0.04)').borderRadius(6)
                Text(`概率 ${(node.probability * 100).toFixed(0)}%`)
                  .fontSize(10).fontColor('#7AC7FF')
                  .padding({ left: 6, right: 6, top: 3, bottom: 3 })
                  .backgroundColor('rgba(255,255,255,0.04)').borderRadius(6)
                if (node.isBranch) {
                  Text('分支').fontSize(10).fontColor('#F5B041')
                    .padding({ left: 6, right: 6, top: 3, bottom: 3 })
                    .backgroundColor('rgba(245,176,65,0.1)').borderRadius(6)
                }
              }
            }
            .width('100%').padding(12)
            .backgroundColor('rgba(255,255,255,0.04)').borderRadius(14)
            .alignItems(HorizontalAlign.Start)
          }
        })

        // 推荐结论
        if (this.showRecommendation && this.dungeonData.recommendation) {
          Column({ space: 8 }) {
            Text('推荐结论').fontSize(11).fontColor('#6B7A90')
            Text(this.dungeonData.recommendation)
              .fontSize(12).fontColor('#DCE5F1').lineHeight(19)
          }
          .width('100%').padding(12)
          .backgroundColor('rgba(122,199,255,0.08)').borderRadius(14)
          .alignItems(HorizontalAlign.Start)
        }

        // 操作按钮
        if (!this.isRevealing) {
          Button('实时推演模式')
            .width('100%').height(40).fontSize(13).fontWeight(600)
            .fontColor('#0A0F1E').backgroundColor('#7AC7FF').borderRadius(10)
            .onClick(() => { this.startStreamSimulation() })
        }
      }
    }
    .width(300)
    .height('100%')
    .padding(14)
    .backgroundColor('rgba(255,255,255,0.02)')
  }

  // ==================== 工具方法 ====================

  private getOptionColor(index: number): string {
    const colors: string[] = ['#5B8FF9', '#5AD8A6', '#F6BD16', '#E8684A', '#9270CA']
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
