/**
 * 决策副本2D地图 — 分页式思维导图可视化
 *
 * 每个决策选项独立一个 Tab 页，各自拥有 Canvas 2D 节点绘图
 * 实时推演时节点逐个出现在对应 Tab 的画布上
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
  color: string
  riskTag: string
  opportunityTag: string
  eventType: string
  impact: Record<string, number>
  isBranch: boolean
  revealed: boolean
}

interface EdgeLine {
  fromX: number
  fromY: number
  toX: number
  toY: number
  color: string
}

interface OptionTab {
  index: number
  title: string
  color: string
  nodes: MapNode[]
  edges: EdgeLine[]
  finalScore: number
  riskLevel: number
  status: string
}

interface StreamRequestPayload {
  session_id: string
  options: StreamRequestOption[]
}

interface StreamRequestOption {
  title: string
  description: string
}

// ==================== 页面组件 ====================

@Entry
@Component
struct DecisionDungeon2DMap {
  @State dungeonData: DungeonData | null = null
  @State isLoading: boolean = false
  @State optionTabs: OptionTab[] = []
  @State activeTabIndex: number = 0
  @State selectedNodeId: string = ''
  @State streamStatus: string = ''
  @State showRecommendation: boolean = false
  private dungeonId: string = ''
  private userId: string = ''
  private ws: WebSocketUtil | null = null
  private canvasWidth: number = 1400
  private canvasHeight: number = 800
  private canvasContexts: Map<number, CanvasRenderingContext2D> = new Map()
  private renderSettings: RenderingContextSettings = new RenderingContextSettings(true)

  aboutToAppear() {
    const params = router.getParams() as Record<string, string>
    if (params?.simulationData) {
      try {
        const simData = JSON.parse(params.simulationData) as Record<string, Object>
        const options = simData.options as DungeonOption[]
        const hasTimeline = options && options.length > 0 &&
          options[0].timeline && options[0].timeline.length > 0

        if (hasTimeline) {
          this.dungeonData = this.convertSimulationToDungeon(simData, params.question || '')
          this.buildTabsFromDungeon()
        } else {
          this.dungeonId = (simData.simulation_id as string) || (params.dungeonId || '')
          this.userId = (simData.user_id as string) || (params.userId || '')
          const fullOptions: DungeonOption[] = []
          if (options) {
            for (let i = 0; i < options.length; i++) {
              const opt = options[i]
              const fullOpt: DungeonOption = {
                option_id: opt.option_id || `option_${i + 1}`,
                title: opt.title || `选项${i + 1}`,
                description: opt.description || '',
                timeline: [],
                final_score: 0,
                risk_level: 0
              }
              fullOptions.push(fullOpt)
            }
          }
          this.dungeonData = {
            dungeon_id: this.dungeonId,
            user_id: this.userId,
            title: params.question || '决策推演',
            description: '正在启动实时推演...',
            options: fullOptions,
            recommendation: '',
            created_at: new Date().toISOString()
          }
          this.initEmptyTabs(fullOptions)
          this.startStreamSimulation()
        }
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
  }

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

  // ==================== Tab 构建 ====================

  private initEmptyTabs(options: DungeonOption[]) {
    const tabs: OptionTab[] = []
    for (let i = 0; i < options.length; i++) {
      const tab: OptionTab = {
        index: i,
        title: options[i].title,
        color: this.getOptionColor(i),
        nodes: [],
        edges: [],
        finalScore: 0,
        riskLevel: 0,
        status: '等待推演'
      }
      tabs.push(tab)
    }
    this.optionTabs = tabs
  }

  private buildTabsFromDungeon() {
    if (!this.dungeonData) return
    const tabs: OptionTab[] = []
    this.dungeonData.options.forEach((option: DungeonOption, i: number) => {
      const color = this.getOptionColor(i)
      const nodes: MapNode[] = []
      const edges: EdgeLine[] = []
      const startX = 100
      const stepX = 220
      const baseY = 260

      // 根节点
      const rootId = `root_${i}`
      const rootNode: MapNode = {
        id: rootId, parentId: '', title: option.title,
        description: option.description || '起点',
        month: 0, probability: 1,
        position: { x: startX, y: baseY },
        color, riskTag: 'medium', opportunityTag: 'medium',
        eventType: 'origin', impact: {},
        isBranch: false, revealed: true
      }
      nodes.push(rootNode)

      let previousId = rootId
      const mainEvents = option.timeline.filter(
        (e: TimelineEvent) => !e.branch_group || !e.branch_group.includes('fork')
      )
      const branchEvents = option.timeline.filter(
        (e: TimelineEvent) => e.branch_group && e.branch_group.includes('fork')
      )

      mainEvents.forEach((event: TimelineEvent, idx: number) => {
        const nodeId = event.event_id || `opt${i}_main_${idx}`
        const nx = startX + (idx + 1) * stepX
        const ny = baseY + (idx % 2 === 0 ? -30 : 30)
        const pid = event.parent_event_id || previousId
        nodes.push({
          id: nodeId, parentId: pid,
          title: `第${event.month}月`, description: event.event,
          month: event.month, probability: event.probability,
          position: { x: nx, y: ny },
          color, riskTag: event.risk_tag || 'medium',
          opportunityTag: event.opportunity_tag || 'medium',
          eventType: event.event_type || 'general',
          impact: event.impact, isBranch: false, revealed: true
        })
        const pNode = nodes.find((n: MapNode) => n.id === pid)
        if (pNode) {
          const edge: EdgeLine = {
            fromX: pNode.position.x + 85, fromY: pNode.position.y + 30,
            toX: nx, toY: ny + 30, color
          }
          edges.push(edge)
        }
        previousId = nodeId
      })

      branchEvents.forEach((event: TimelineEvent, bIdx: number) => {
        const nodeId = event.event_id || `opt${i}_branch_${bIdx}`
        const pid = event.parent_event_id || previousId
        const pNode = nodes.find((n: MapNode) => n.id === pid)
        const isPos = event.risk_tag === 'low' || event.opportunity_tag === 'high'
        const px = pNode ? pNode.position.x : startX + 400
        const py = pNode ? pNode.position.y : baseY
        const nx = px + 200
        const ny = py + (isPos ? -100 : 100)
        const bColor = isPos ? '#4DD0A8' : '#FF6B6B'
        nodes.push({
          id: nodeId, parentId: pid,
          title: `第${event.month}月`, description: event.event,
          month: event.month, probability: event.probability,
          position: { x: nx, y: ny },
          color: bColor, riskTag: event.risk_tag || 'medium',
          opportunityTag: event.opportunity_tag || 'medium',
          eventType: event.event_type || 'general',
          impact: event.impact, isBranch: true, revealed: true
        })
        if (pNode) {
          const edge: EdgeLine = {
            fromX: pNode.position.x + 85, fromY: pNode.position.y + 30,
            toX: nx, toY: ny + 30, color: bColor
          }
          edges.push(edge)
        }
      })

      const tab: OptionTab = {
        index: i, title: option.title, color,
        nodes, edges,
        finalScore: option.final_score,
        riskLevel: option.risk_level,
        status: '推演完成'
      }
      tabs.push(tab)
    })
    this.optionTabs = tabs
    this.showRecommendation = true
  }

  // ==================== Canvas 绘制 ====================

  private drawTabEdges(tabIndex: number) {
    const ctx = this.canvasContexts.get(tabIndex)
    if (!ctx) return
    ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight)
    if (tabIndex >= this.optionTabs.length) return
    const tab = this.optionTabs[tabIndex]
    tab.edges.forEach((edge: EdgeLine) => {
      ctx.beginPath()
      ctx.strokeStyle = edge.color
      ctx.lineWidth = 2.5
      ctx.globalAlpha = 0.7
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
    this.showRecommendation = false

    try {
      this.ws = new WebSocketUtil()

      this.ws.onMessage((data: string) => {
        setTimeout(() => {
          try {
            const event = JSON.parse(data) as Record<string, Object>
            const type = event.type as string
            if (type === 'start') {
              this.streamStatus = '推演已启动'
            } else if (type === 'option_start') {
              const title = event.title as string
              const tabIdx = this.findTabByTitle(title)
              if (tabIdx >= 0) {
                this.updateTabStatus(tabIdx, '推演中...')
                this.activeTabIndex = tabIdx
                // 添加根节点
                this.addRootNodeToTab(tabIdx, title)
              }
            } else if (type === 'node') {
              this.handleStreamNode(event)
            } else if (type === 'option_complete') {
              const title = event.title as string
              const score = event.final_score as number
              const risk = event.risk_level as number
              const tabIdx = this.findTabByTitle(title)
              if (tabIdx >= 0) {
                this.updateTabScore(tabIdx, score, risk)
                this.updateTabStatus(tabIdx, '推演完成')
              }
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
              this.showRecommendation = true
              this.streamStatus = '推演完成'
            } else if (type === 'done') {
              this.streamStatus = '全部推演完成'
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
      const payload: StreamRequestPayload = {
        session_id: this.dungeonId,
        options: streamOptions
      }
      this.ws.send(payload)
    } catch (error) {
      this.streamStatus = '推演启动失败'
      console.error('推演启动失败: ' + (error as Error).message)
    }
  }

  private handleStreamNode(event: Record<string, Object>) {
    const node = event.node as Record<string, Object>
    const optionTitle = event.option_title as string
    const tabIdx = this.findTabByTitle(optionTitle)
    if (tabIdx < 0 || tabIdx >= this.optionTabs.length) return

    const tab = this.optionTabs[tabIdx]
    const isBranch = ((node.branch_group as string) || '').includes('fork')
    const parentId = (node.parent_event_id as string) || `root_${tabIdx}`
    const parentNode = tab.nodes.find((n: MapNode) => n.id === parentId)
    const nodeCount = tab.nodes.filter((n: MapNode) => !n.id.startsWith('root_')).length
    const baseY = 260
    const startX = 100
    const stepX = 220

    let nx: number
    let ny: number
    if (isBranch && parentNode) {
      const isPos = (node.risk_tag as string) === 'low'
      nx = parentNode.position.x + 200
      ny = parentNode.position.y + (isPos ? -100 : 100)
    } else {
      nx = startX + (nodeCount + 1) * stepX
      ny = baseY + (nodeCount % 2 === 0 ? -30 : 30)
    }

    const color = isBranch
      ? ((node.risk_tag as string) === 'low' ? '#4DD0A8' : '#FF6B6B')
      : tab.color
    const mapNode: MapNode = {
      id: (node.event_id as string) || `stream_${tabIdx}_${nodeCount}`,
      parentId,
      title: `第${node.month as number}月`,
      description: (node.event as string) || '',
      month: node.month as number,
      probability: (node.probability as number) || 0,
      position: { x: nx, y: ny },
      color,
      riskTag: (node.risk_tag as string) || 'medium',
      opportunityTag: (node.opportunity_tag as string) || 'medium',
      eventType: (node.event_type as string) || 'general',
      impact: node.impact as Record<string, number>,
      isBranch,
      revealed: true
    }

    // 更新 tab 数据（触发 UI 刷新）
    const updatedTabs = this.optionTabs.map((t: OptionTab, idx: number): OptionTab => {
      if (idx !== tabIdx) return t
      const newNodes = t.nodes.concat([mapNode])
      const newEdges: EdgeLine[] = [...t.edges]
      if (parentNode) {
        const edge: EdgeLine = {
          fromX: parentNode.position.x + 85,
          fromY: parentNode.position.y + 30,
          toX: nx, toY: ny + 30,
          color
        }
        newEdges.push(edge)
      }
      const updated: OptionTab = {
        index: t.index, title: t.title, color: t.color,
        nodes: newNodes, edges: newEdges,
        finalScore: t.finalScore, riskLevel: t.riskLevel,
        status: t.status
      }
      return updated
    })
    this.optionTabs = updatedTabs
    this.selectedNodeId = mapNode.id

    // 自动切到有新节点的 tab
    this.activeTabIndex = tabIdx
    this.drawTabEdges(tabIdx)
  }

  private addRootNodeToTab(tabIdx: number, title: string) {
    const rootNode: MapNode = {
      id: `root_${tabIdx}`, parentId: '', title: title,
      description: '推演起点', month: 0, probability: 1,
      position: { x: 100, y: 260 },
      color: this.getOptionColor(tabIdx),
      riskTag: 'medium', opportunityTag: 'medium',
      eventType: 'origin', impact: {},
      isBranch: false, revealed: true
    }
    const updatedTabs = this.optionTabs.map((t: OptionTab, idx: number): OptionTab => {
      if (idx !== tabIdx) return t
      const hasRoot = t.nodes.some((n: MapNode) => n.id === `root_${tabIdx}`)
      if (hasRoot) return t
      const updated: OptionTab = {
        index: t.index, title: t.title, color: t.color,
        nodes: t.nodes.concat([rootNode]), edges: t.edges,
        finalScore: t.finalScore, riskLevel: t.riskLevel,
        status: t.status
      }
      return updated
    })
    this.optionTabs = updatedTabs
  }

  private findTabByTitle(title: string): number {
    for (let i = 0; i < this.optionTabs.length; i++) {
      if (this.optionTabs[i].title === title) return i
    }
    return -1
  }

  private updateTabStatus(tabIdx: number, status: string) {
    const updatedTabs = this.optionTabs.map((t: OptionTab, idx: number): OptionTab => {
      if (idx !== tabIdx) return t
      const updated: OptionTab = {
        index: t.index, title: t.title, color: t.color,
        nodes: t.nodes, edges: t.edges,
        finalScore: t.finalScore, riskLevel: t.riskLevel,
        status: status
      }
      return updated
    })
    this.optionTabs = updatedTabs
  }

  private updateTabScore(tabIdx: number, score: number, risk: number) {
    const updatedTabs = this.optionTabs.map((t: OptionTab, idx: number): OptionTab => {
      if (idx !== tabIdx) return t
      const updated: OptionTab = {
        index: t.index, title: t.title, color: t.color,
        nodes: t.nodes, edges: t.edges,
        finalScore: score, riskLevel: risk,
        status: t.status
      }
      return updated
    })
    this.optionTabs = updatedTabs
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
          this.buildTabsFromDungeon()
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
      } else if (this.optionTabs.length > 0) {
        // 分页 Tab 栏
        Row({ space: 0 }) {
          ForEach(this.optionTabs, (tab: OptionTab, idx: number) => {
            this.TabButton(tab, idx)
          })
        }
        .width('100%')
        .padding({ left: 16, right: 16, top: 8, bottom: 4 })
        .backgroundColor('rgba(10,15,30,0.95)')

        // 当前 Tab 内容
        Stack() {
          ForEach(this.optionTabs, (tab: OptionTab, idx: number) => {
            if (idx === this.activeTabIndex) {
              Row() {
                this.TabCanvasView(tab)
                this.TabDetailPanel(tab)
              }
              .width('100%')
              .height('100%')
            }
          })
        }
        .layoutWeight(1)
      } else {
        Column({ space: 12 }) {
          Text('等待推演数据...').fontSize(16).fontColor('#6B7A90')
          if (this.streamStatus !== '') {
            Text(this.streamStatus).fontSize(13).fontColor('#7AC7FF')
          }
        }
        .layoutWeight(1).width('100%').justifyContent(FlexAlign.Center)
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
      }
      .alignItems(HorizontalAlign.Start).layoutWeight(1).margin({ left: 12 })

      Row({ space: 10 }) {
        this.LegendDot('#5B8FF9', '主线')
        this.LegendDot('#4DD0A8', '乐观')
        this.LegendDot('#FF6B6B', '风险')
      }
    }
    .width('100%')
    .padding({ left: 16, right: 16, top: 16, bottom: 10 })
    .backgroundColor('rgba(10,15,30,0.95)')
  }

  @Builder
  LegendDot(dotColor: string, label: string) {
    Row({ space: 4 }) {
      Column().width(10).height(10).borderRadius(5).backgroundColor(dotColor)
      Text(label).fontSize(10).fontColor('#8899AA')
    }
  }

  @Builder
  TabButton(tab: OptionTab, idx: number) {
    Column({ space: 4 }) {
      Text(tab.title)
        .fontSize(13).fontWeight(600).maxLines(1)
        .fontColor(idx === this.activeTabIndex ? '#F0F4FA' : '#6B7A90')
      Row({ space: 6 }) {
        if (tab.finalScore > 0) {
          Text(`${tab.finalScore.toFixed(0)}分`).fontSize(10).fontColor(tab.color)
        }
        Text(tab.status).fontSize(10)
          .fontColor(tab.status === '推演中...' ? '#F5B041' : '#5B8FF9')
      }
      Column()
        .width('100%').height(2).borderRadius(1)
        .backgroundColor(idx === this.activeTabIndex ? tab.color : 'transparent')
    }
    .layoutWeight(1)
    .padding({ top: 8, bottom: 6, left: 8, right: 8 })
    .onClick(() => {
      this.activeTabIndex = idx
      this.drawTabEdges(idx)
    })
  }

  // ==================== Tab Canvas 视图 ====================

  @Builder
  TabCanvasView(tab: OptionTab) {
    Scroll() {
      Stack() {
        Canvas(this.getOrCreateContext(tab.index))
          .width(this.canvasWidth)
          .height(this.canvasHeight)
          .backgroundColor('#0A0F1E')
          .onReady(() => {
            this.drawTabEdges(tab.index)
          })

        ForEach(tab.nodes, (node: MapNode) => {
          if (node.revealed) {
            this.MapNodeView(node, tab.color)
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
  MapNodeView(node: MapNode, tabColor: string) {
    Column({ space: 6 }) {
      Stack() {
        Column()
          .width(node.id.startsWith('root_') ? 52 : (node.isBranch ? 36 : 42))
          .height(node.id.startsWith('root_') ? 52 : (node.isBranch ? 36 : 42))
          .backgroundColor(node.color)
          .opacity(node.id === this.selectedNodeId ? 1.0 : 0.8)
          .borderRadius(node.id.startsWith('root_') ? 12 : 21)
          .border({
            width: node.id === this.selectedNodeId ? 2.5 : 1,
            color: node.id === this.selectedNodeId ? '#FFFFFF' : 'rgba(255,255,255,0.15)'
          })
          .shadow({
            radius: node.id === this.selectedNodeId ? 16 : 6,
            color: node.color,
            offsetX: 0, offsetY: 0
          })

        Text(node.month > 0 ? `${node.month}` : '起')
          .fontSize(node.id.startsWith('root_') ? 14 : 12)
          .fontWeight(700).fontColor('#FFFFFF')
      }

      Column({ space: 4 }) {
        Text(node.title)
          .fontSize(12).fontWeight(700).fontColor('#E8ECF3').maxLines(1)
        Text(node.description)
          .fontSize(10).fontColor('#8899AA').lineHeight(14)
          .maxLines(node.isBranch ? 2 : 3)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
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
          ? 'rgba(122,199,255,0.12)' : 'rgba(255,255,255,0.04)'
      )
      .borderRadius(12)
      .border({
        width: 1,
        color: node.id === this.selectedNodeId
          ? 'rgba(122,199,255,0.3)' : 'rgba(255,255,255,0.06)'
      })
      .alignItems(HorizontalAlign.Start)
    }
    .position({ x: node.position.x, y: node.position.y })
    .width(node.isBranch ? 160 : 180)
    .onClick(() => { this.selectedNodeId = node.id })
    .animation({ duration: 300, curve: Curve.EaseOut })
  }

  // ==================== 右侧详情面板 ====================

  @Builder
  TabDetailPanel(tab: OptionTab) {
    Column({ space: 12 }) {
      // 选项概览
      Column({ space: 6 }) {
        Row({ space: 8 }) {
          Column().width(10).height(10).borderRadius(5).backgroundColor(tab.color)
          Text(tab.title).fontSize(14).fontWeight(600).fontColor('#DCE5F1').maxLines(2).layoutWeight(1)
        }
        Row({ space: 12 }) {
          if (tab.finalScore > 0) {
            Text(`综合 ${tab.finalScore.toFixed(0)}分`).fontSize(12).fontColor(tab.color)
          }
          Text(`节点 ${tab.nodes.length}`).fontSize(11).fontColor('#6B7A90')
          Text(tab.status).fontSize(11)
            .fontColor(tab.status === '推演中...' ? '#F5B041' : '#5B8FF9')
        }
      }
      .width('100%').padding(12)
      .backgroundColor('rgba(255,255,255,0.04)').borderRadius(14)
      .alignItems(HorizontalAlign.Start)

      // 选中节点详情
      ForEach(tab.nodes, (node: MapNode) => {
        if (node.id === this.selectedNodeId) {
          Column({ space: 8 }) {
            Text('当前节点').fontSize(11).fontColor('#6B7A90')
            Text(node.title).fontSize(16).fontWeight(700).fontColor('#F0F4FA')
            Text(node.description).fontSize(12).fontColor('#A0B0C0').lineHeight(18)

            if (Object.keys(node.impact).length > 0) {
              Column({ space: 4 }) {
                Text('影响维度').fontSize(10).fontColor('#6B7A90')
                ForEach(Object.keys(node.impact), (key: string) => {
                  Row({ space: 6 }) {
                    Text(key).fontSize(11).fontColor('#8899AA').width(36)
                    Row() {
                      Column()
                        .width(`${Math.abs(node.impact[key]) * 100}%`)
                        .height(6).borderRadius(3)
                        .backgroundColor(node.impact[key] >= 0 ? '#4DD0A8' : '#FF6B6B')
                    }
                    .width(80).height(6).borderRadius(3)
                    .backgroundColor('rgba(255,255,255,0.06)')
                    Text(`${node.impact[key] > 0 ? '+' : ''}${node.impact[key].toFixed(1)}`)
                      .fontSize(10)
                      .fontColor(node.impact[key] >= 0 ? '#4DD0A8' : '#FF6B6B')
                  }
                  .width('100%')
                })
              }
              .width('100%')
            }

            Row({ space: 6 }) {
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
      if (this.showRecommendation && this.dungeonData && this.dungeonData.recommendation) {
        Column({ space: 8 }) {
          Text('AI 推荐结论').fontSize(11).fontColor('#6B7A90')
          Text(this.dungeonData.recommendation)
            .fontSize(12).fontColor('#DCE5F1').lineHeight(19)
        }
        .width('100%').padding(12)
        .backgroundColor('rgba(122,199,255,0.08)').borderRadius(14)
        .alignItems(HorizontalAlign.Start)
      }
    }
    .width(280)
    .height('100%')
    .padding(12)
    .backgroundColor('rgba(255,255,255,0.02)')
  }

  // ==================== 工具方法 ====================

  private getOrCreateContext(tabIndex: number): CanvasRenderingContext2D {
    let ctx = this.canvasContexts.get(tabIndex)
    if (!ctx) {
      ctx = new CanvasRenderingContext2D(this.renderSettings)
      this.canvasContexts.set(tabIndex, ctx)
    }
    return ctx
  }

  private getOptionColor(index: number): string {
    const colors: string[] = ['#5B8FF9', '#5AD8A6', '#F6BD16', '#E8684A', '#9270CA']
    return colors[index % colors.length]
  }

  private getRiskColor(tag: string): string {
    if (tag === 'low') return '#4DD0A8'
    if (tag === 'high') return '#FF6B6B'
    return '#F5B041'
  }
}
