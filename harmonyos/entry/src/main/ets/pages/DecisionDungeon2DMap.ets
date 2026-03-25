/**
 * 决策副本 2D 地图
 * 单画布动态推演版：近似无限平面 + 实时节点更新 + 点击查看详情
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
  color: string
  riskTag: string
  opportunityTag: string
  eventType: string
  impact: Record<string, number>
  isBranch: boolean
  revealed: boolean
  optionIndex: number
  optionTitle: string
}

interface EdgeLine {
  fromX: number
  fromY: number
  toX: number
  toY: number
  color: string
}

interface OptionSummary {
  index: number
  title: string
  color: string
  finalScore: number
  riskLevel: number
  status: string
}

interface StreamRequestPayload {
  session_id: string
  options: StreamRequestOption[]
}

interface RecommendationData {
  summary: string
  recommended_option: string
  reasons: string[]
  risks: string[]
  actions: string[]
}

interface ActivityLogItem {
  id: string
  kind: string
  text: string
}

interface StreamRequestOption {
  title: string
  description: string
}

@Entry
@Component
struct DecisionDungeon2DMap {
  @State dungeonData: DungeonData | null = null
  @State isLoading: boolean = false
  @State optionSummaries: OptionSummary[] = []
  @State nodes: MapNode[] = []
  @State edges: EdgeLine[] = []
  @State selectedNodeId: string = ''
  @State streamStatus: string = ''
  @State showRecommendation: boolean = false
  @State viewportScale: number = 1
  @State viewportOffsetX: number = 0
  @State viewportOffsetY: number = 0
  @State dragHintVisible: boolean = true
  @State activityLogs: ActivityLogItem[] = []
  @State liveThinkingText: string = ''
  @State liveRecommendationText: string = ''
  @State structuredRecommendation: RecommendationData | null = null

  private dungeonId: string = ''
  private userId: string = ''
  private ws: WebSocketUtil | null = null
  private canvasWidth: number = 5200
  private canvasHeight: number = 3600
  private canvasContext: CanvasRenderingContext2D = new CanvasRenderingContext2D(new RenderingContextSettings(true))


  aboutToAppear() {
    const params = router.getParams() as Record<string, string>
    this.viewportOffsetX = 480
    this.viewportOffsetY = 900

    if (params?.simulationData) {
      try {
        const simData = JSON.parse(params.simulationData) as Record<string, Object>
        const options = simData.options as DungeonOption[]
        const hasTimeline = options && options.length > 0 &&
          options[0].timeline && options[0].timeline.length > 0

        if (hasTimeline) {
          this.dungeonData = this.convertSimulationToDungeon(simData, params.question || '')
          this.buildGraphFromDungeon()
        } else {
          this.dungeonId = (simData.simulation_id as string) || (params.dungeonId || '')
          this.userId = (simData.user_id as string) || (params.userId || '')
          const fullOptions: DungeonOption[] = []
          if (options) {
            for (let i = 0; i < options.length; i++) {
              const opt = options[i]
              fullOptions.push({
                option_id: opt.option_id || `option_${i + 1}`,
                title: opt.title || `选项${i + 1}`,
                description: opt.description || '',
                timeline: [],
                final_score: 0,
                risk_level: 0
              })
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
          this.initOptionSummaries(fullOptions)
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

  private initOptionSummaries(options: DungeonOption[]) {
    const summaries: OptionSummary[] = []
    for (let i = 0; i < options.length; i++) {
      summaries.push({
        index: i,
        title: options[i].title,
        color: this.getOptionColor(i),
        finalScore: 0,
        riskLevel: 0,
        status: '等待推演'
      })
    }
    this.optionSummaries = summaries
  }

  private buildGraphFromDungeon() {
    if (!this.dungeonData) return

    const allNodes: MapNode[] = []
    const allEdges: EdgeLine[] = []
    const summaries: OptionSummary[] = []
    const laneGap = 560
    const startX = 280
    const rootX = 260
    const baseY = 520
    const mainStepX = 300

    this.dungeonData.options.forEach((option: DungeonOption, optionIndex: number) => {
      const optionColor = this.getOptionColor(optionIndex)
      const laneY = baseY + optionIndex * laneGap
      const rootId = `root_${optionIndex}`

      summaries.push({
        index: optionIndex,
        title: option.title,
        color: optionColor,
        finalScore: option.final_score,
        riskLevel: option.risk_level,
        status: '推演完成'
      })

      allNodes.push({
        id: rootId,
        parentId: '',
        title: this.getShortNodeTitle(option.title),
        description: option.description || '推演起点',
        month: 0,
        probability: 1,
        position: { x: rootX, y: laneY },
        color: optionColor,
        riskTag: 'medium',
        opportunityTag: 'medium',
        eventType: 'origin',
        impact: {},
        isBranch: false,
        revealed: true,
        optionIndex,
        optionTitle: option.title
      })

      let previousId = rootId
      const mainEvents = option.timeline.filter((e: TimelineEvent) => !e.branch_group || !e.branch_group.includes('fork'))
      const branchEvents = option.timeline.filter((e: TimelineEvent) => e.branch_group && e.branch_group.includes('fork'))

      mainEvents.forEach((event: TimelineEvent, idx: number) => {
        const nodeId = event.event_id || `opt${optionIndex}_main_${idx}`
        const x = startX + (idx + 1) * mainStepX
        const y = laneY + (idx % 2 === 0 ? -90 : 90)
        const parentId = event.parent_event_id || previousId
        const parentNode = allNodes.find((item: MapNode) => item.id === parentId)

        allNodes.push({
          id: nodeId,
          parentId,
          title: this.getShortNodeTitle(event.event),
          description: event.event,
          month: event.month,
          probability: event.probability,
          position: { x, y },
          color: optionColor,
          riskTag: event.risk_tag || 'medium',
          opportunityTag: event.opportunity_tag || 'medium',
          eventType: event.event_type || 'general',
          impact: event.impact,
          isBranch: false,
          revealed: true,
          optionIndex,
          optionTitle: option.title
        })

        if (parentNode) {
          allEdges.push({
            fromX: parentNode.position.x,
            fromY: parentNode.position.y,
            toX: x,
            toY: y,
            color: optionColor
          })
        }
        previousId = nodeId
      })

      branchEvents.forEach((event: TimelineEvent, idx: number) => {
        const nodeId = event.event_id || `opt${optionIndex}_branch_${idx}`
        const parentId = event.parent_event_id || previousId
        const parentNode = allNodes.find((item: MapNode) => item.id === parentId)
        const isPositive = event.risk_tag === 'low' || event.opportunity_tag === 'high'
        const x = (parentNode ? parentNode.position.x : startX + 400) + 220
        const y = (parentNode ? parentNode.position.y : laneY) + (isPositive ? -200 : 200)
        const color = isPositive ? '#4DD0A8' : '#FF6B6B'

        allNodes.push({
          id: nodeId,
          parentId,
          title: this.getShortNodeTitle(event.event),
          description: event.event,
          month: event.month,
          probability: event.probability,
          position: { x, y },
          color,
          riskTag: event.risk_tag || 'medium',
          opportunityTag: event.opportunity_tag || 'medium',
          eventType: event.event_type || 'general',
          impact: event.impact,
          isBranch: true,
          revealed: true,
          optionIndex,
          optionTitle: option.title
        })

        if (parentNode) {
          allEdges.push({
            fromX: parentNode.position.x,
            fromY: parentNode.position.y,
            toX: x,
            toY: y,
            color
          })
        }
      })
    })

    this.optionSummaries = summaries
    this.nodes = allNodes
    this.edges = allEdges
    this.selectedNodeId = allNodes.length > 0 ? allNodes[0].id : ''
    this.showRecommendation = true
    this.drawEdges()
  }


  private drawEdges() {
    this.canvasContext.clearRect(0, 0, this.canvasWidth, this.canvasHeight)
    this.edges.forEach((edge: EdgeLine) => {
      this.canvasContext.beginPath()
      this.canvasContext.strokeStyle = edge.color
      this.canvasContext.lineWidth = 2.5
      this.canvasContext.globalAlpha = 0.72
      const midX = (edge.fromX + edge.toX) / 2
      this.canvasContext.moveTo(edge.fromX, edge.fromY)
      this.canvasContext.bezierCurveTo(midX, edge.fromY, midX, edge.toY, edge.toX, edge.toY)
      this.canvasContext.stroke()
      this.canvasContext.globalAlpha = 1

      const angle = Math.atan2(edge.toY - edge.fromY, edge.toX - edge.fromX)
      const arrowLen = 12
      this.canvasContext.beginPath()
      this.canvasContext.fillStyle = edge.color
      this.canvasContext.moveTo(edge.toX, edge.toY)
      this.canvasContext.lineTo(
        edge.toX - arrowLen * Math.cos(angle - Math.PI / 6),
        edge.toY - arrowLen * Math.sin(angle - Math.PI / 6)
      )
      this.canvasContext.lineTo(
        edge.toX - arrowLen * Math.cos(angle + Math.PI / 6),
        edge.toY - arrowLen * Math.sin(angle + Math.PI / 6)
      )
      this.canvasContext.closePath()
      this.canvasContext.fill()
    })
  }

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
              this.pushActivityLog('system', '推演已启动，系统正在准备实时路径图')
            } else if (type === 'thinking_chunk') {
              const chunk = (event.content as string) || ''
              if (chunk !== '') {
                this.liveThinkingText = (this.liveThinkingText + chunk).slice(-1200)
                this.streamStatus = '模型正在生成推演内容...'
              }
            } else if (type === 'recommendation_chunk') {
              const chunk = (event.content as string) || ''
              if (chunk !== '') {
                this.liveRecommendationText = (this.liveRecommendationText + chunk).slice(-1200)
                this.streamStatus = '模型正在生成推荐结论...'
              }
            } else if (type === 'status' || type === 'thinking') {
              const content = (event.content as string) || ''
              if (content !== '') {
                this.streamStatus = content
                this.pushActivityLog(type === 'thinking' ? 'thinking' : 'system', content)
              }
            } else if (type === 'option_start') {
              const title = event.title as string
              const optionIndex = this.findOptionIndexByTitle(title)
              if (optionIndex >= 0) {
                this.updateOptionStatus(optionIndex, '推演中...')
                this.addRootNode(optionIndex, title)
                this.pushActivityLog('option', `开始推演 ${title}`)
              }
            } else if (type === 'node') {
              this.handleStreamNode(event)
            } else if (type === 'option_complete') {
              const title = event.title as string
              const optionIndex = this.findOptionIndexByTitle(title)
              if (optionIndex >= 0) {
                this.updateOptionScore(optionIndex, event.final_score as number, event.risk_level as number)
                this.updateOptionStatus(optionIndex, '推演完成')
                this.pushActivityLog('option', `${title} 推演完成，已完成评分与风险计算`)
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
              try {
                this.structuredRecommendation = JSON.parse((event.content as string) || '') as RecommendationData
              } catch (_err) {
                this.structuredRecommendation = null
              }
              this.showRecommendation = true
              this.streamStatus = '推演完成'
              this.liveRecommendationText = (event.content as string) || this.liveRecommendationText
              this.pushActivityLog('system', '个性化推荐结论已生成')
            } else if (type === 'done') {
              this.streamStatus = '全部推演完成'
              this.pushActivityLog('system', '全部推演完成，决策副本已构建完成')
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
            console.error('推演事件解析失败: ' + (err as Error).message)
          }
        }, 0)
      })

      this.ws.onError((_error: string) => {
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
    const optionIndex = this.findOptionIndexByTitle(optionTitle)
    if (optionIndex < 0) return

    const laneY = 520 + optionIndex * 560
    const parentId = (node.parent_event_id as string) || `root_${optionIndex}`
    const parentNode = this.nodes.find((item: MapNode) => item.id === parentId)
    const optionNodes = this.nodes.filter((item: MapNode) => item.optionIndex === optionIndex && !item.id.startsWith('root_'))
    const nodeCount = optionNodes.length
    const isBranch = ((node.branch_group as string) || '').includes('fork')

    let x: number
    let y: number
    if (isBranch && parentNode) {
      const isPositive = (node.risk_tag as string) === 'low' || (node.opportunity_tag as string) === 'high'
      x = parentNode.position.x + 220
      y = parentNode.position.y + (isPositive ? -200 : 200)
    } else {
      x = 280 + (nodeCount + 1) * 300
      y = laneY + (nodeCount % 2 === 0 ? -90 : 90)
    }

    const color = isBranch
      ? (((node.risk_tag as string) === 'low' || (node.opportunity_tag as string) === 'high') ? '#4DD0A8' : '#FF6B6B')
      : this.getOptionColor(optionIndex)

    const mapNode: MapNode = {
      id: (node.event_id as string) || `stream_${optionIndex}_${nodeCount}`,
      parentId,
      title: this.getShortNodeTitle((node.event as string) || `第${node.month as number}月事件`),
      description: (node.event as string) || '',
      month: node.month as number,
      probability: (node.probability as number) || 0,
      position: { x, y },
      color,
      riskTag: (node.risk_tag as string) || 'medium',
      opportunityTag: (node.opportunity_tag as string) || 'medium',
      eventType: (node.event_type as string) || 'general',
      impact: node.impact as Record<string, number>,
      isBranch,
      revealed: true,
      optionIndex,
      optionTitle
    }

    const nextNodes = this.nodes.concat([mapNode])
    const nextEdges: EdgeLine[] = [...this.edges]
    if (parentNode) {
      nextEdges.push({
        fromX: parentNode.position.x,
        fromY: parentNode.position.y,
        toX: x,
        toY: y,
        color
      })
    }

    this.nodes = nextNodes
    this.edges = nextEdges
    this.selectedNodeId = mapNode.id
    this.pushActivityLog('node', `${optionTitle} 新增节点：${mapNode.title}`)
    this.centerOnNode(mapNode)
    this.drawEdges()
  }


  private addRootNode(optionIndex: number, title: string) {
    const rootId = `root_${optionIndex}`
    const exists = this.nodes.some((item: MapNode) => item.id === rootId)
    if (exists) return

    this.nodes = this.nodes.concat([{
      id: rootId,
      parentId: '',
      title,
      description: '推演起点',
      month: 0,
      probability: 1,
      position: { x: 260, y: 520 + optionIndex * 560 },
      color: this.getOptionColor(optionIndex),
      riskTag: 'medium',
      opportunityTag: 'medium',
      eventType: 'origin',
      impact: {},
      isBranch: false,
      revealed: true,
      optionIndex,
      optionTitle: title
    }])
    if (this.selectedNodeId === '') {
      this.selectedNodeId = rootId
    }
  }

  private findOptionIndexByTitle(title: string): number {
    for (let i = 0; i < this.optionSummaries.length; i++) {
      if (this.optionSummaries[i].title === title) return i
    }
    if (this.dungeonData) {
      for (let i = 0; i < this.dungeonData.options.length; i++) {
        if (this.dungeonData.options[i].title === title) return i
      }
    }
    return -1
  }

  private updateOptionStatus(optionIndex: number, status: string) {
    this.optionSummaries = this.optionSummaries.map((item: OptionSummary) => {
      if (item.index !== optionIndex) return item
      return {
        index: item.index,
        title: item.title,
        color: item.color,
        finalScore: item.finalScore,
        riskLevel: item.riskLevel,
        status
      }
    })
  }

  private updateOptionScore(optionIndex: number, score: number, risk: number) {
    this.optionSummaries = this.optionSummaries.map((item: OptionSummary) => {
      if (item.index !== optionIndex) return item
      return {
        index: item.index,
        title: item.title,
        color: item.color,
        finalScore: score,
        riskLevel: risk,
        status: item.status
      }
    })
  }

  private centerOnNode(node: MapNode) {
    this.viewportOffsetX = Math.max(0, node.position.x - 500)
    this.viewportOffsetY = Math.max(0, node.position.y - 800)
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
          this.buildGraphFromDungeon()
        }
      }
    } catch (error) {
      console.error('加载副本失败:', (error as Error).message)
      promptAction.showToast({ message: '加载副本失败', duration: 2000 })
    }
    this.isLoading = false
  }

  private getOptionColor(index: number): string {
    const colors = ['#5B8FF9', '#5AD8A6', '#F6BD16', '#E8684A', '#9270CA']
    return colors[index % colors.length]
  }

  private getRiskColor(tag: string): string {
    if (tag === 'low') return '#4DD0A8'
    if (tag === 'high') return '#FF6B6B'
    return '#F5B041'
  }

  private getSelectedNode(): MapNode | null {
    const found = this.nodes.find((item: MapNode) => item.id === this.selectedNodeId)
    return found ? found : null
  }

  private getShortNodeTitle(raw: string): string {
    let text = raw || ''
    text = text.replace(/（乐观分支）/g, '')
    text = text.replace(/（风险分支）/g, '')
    text = text.replace(/\(乐观分支\)/g, '')
    text = text.replace(/\(风险分支\)/g, '')
    text = text.replace(/进展顺利，带来额外机遇/g, '带来机遇')
    text = text.replace(/遇到阻碍，需要调整策略/g, '遇到阻碍')
    text = text.replace(/开始围绕/g, '')
    text = text.replace(/系统正在/g, '')
    text = text.replace(/\s+/g, ' ').trim()
    if (text.length > 22) {
      return text.slice(0, 22) + '...'
    }
    return text === '' ? '新事件' : text
  }

  private pushActivityLog(kind: string, text: string) {
    const next = this.activityLogs.concat([{ id: `${Date.now()}_${this.activityLogs.length}`, kind, text }])
    this.activityLogs = next.length > 10 ? next.slice(next.length - 10) : next
  }

  private getNodeInterpretation(node: MapNode | null): string {
    if (!node) return ''
    const impacts = Object.keys(node.impact)
      .filter((key: string) => Math.abs(node.impact[key]) > 0.05)
      .map((key: string) => `${key}${node.impact[key] > 0 ? '提升' : '承压'}`)
    const impactSummary = impacts.length > 0 ? impacts.join('、') : '整体影响较平稳'
    if (node.isBranch) {
      return `这是一个分支事件，表示主路径在这里出现了新的变化方向，当前更偏向 ${node.riskTag === 'high' ? '风险上升' : (node.opportunityTag === 'high' ? '机会增加' : '中性波动')}，主要影响 ${impactSummary}。`
    }
    return `这是主路径上的关键事件，表示该选项在这个阶段出现了新的推进或反馈，当前主要影响 ${impactSummary}。`
  }

  private getNodeImportance(node: MapNode): number {
    const impactScore = Object.keys(node.impact).reduce((sum: number, key: string) => {
      return sum + Math.abs(node.impact[key])
    }, 0)
    if (node.id.startsWith('root_')) return 3
    if (impactScore >= 1.2 || node.riskTag === 'high' || node.opportunityTag === 'high') return 3
    if (impactScore >= 0.5) return 2
    return 1
  }

  build() {
    Column() {
      this.HeaderBar()

      if (this.isLoading) {
        Column({ space: 18 }) {
          LoadingProgress().width(48).height(48).color('#7AC7FF')
          Text('正在准备基座 + LoRA 决策推演').fontSize(17).fontWeight(700).fontColor('#E7EEF8')
          Text('系统正在读取用户画像、收集信息摘要并构建初始推演平面')
            .fontSize(12)
            .fontColor('#8EA3B7')
            .textAlign(TextAlign.Center)
            .lineHeight(18)
        }
        .layoutWeight(1)
        .width('100%')
        .justifyContent(FlexAlign.Center)
      } else if (this.optionSummaries.length > 0) {
        Column({ space: 0 }) {
          this.TopPinnedSummary()
          if (this.structuredRecommendation) {
            this.DecisionRecommendationCard()
          }
          Stack() {
            this.InfiniteCanvasView()
            this.ActivityOverlay()
            this.NodeDetailOverlay()
          }
          .layoutWeight(1)
        }
        .layoutWeight(1)
      } else {
        Column({ space: 12 }) {
          Text('等待推演数据...').fontSize(16).fontColor('#6B7A90')
          if (this.streamStatus !== '') {
            Text(this.streamStatus).fontSize(13).fontColor('#7AC7FF')
          }
        }
        .layoutWeight(1)
        .width('100%')
        .justifyContent(FlexAlign.Center)
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#0A0F1E')
  }


  @Builder
  HeaderBar() {
    Row() {
      Button({ type: ButtonType.Circle }) {
        Text('←').fontSize(22).fontColor('#E0E8F5').fontWeight(700)
      }
      .width(40)
      .height(40)
      .backgroundColor('rgba(255,255,255,0.06)')
      .onClick(() => router.back())

      Column({ space: 2 }) {
        Text('决策动态推演平面').fontSize(20).fontWeight(700).fontColor('#F0F4FA')
        if (this.dungeonData) {
          Text(this.dungeonData.title).fontSize(12).fontColor('#6B7A90').maxLines(1)
        }
        if (this.streamStatus !== '') {
          Text(this.streamStatus).fontSize(11).fontColor('#7AC7FF')
        }
      }
      .alignItems(HorizontalAlign.Start)
      .layoutWeight(1)
      .margin({ left: 12 })

      Row({ space: 10 }) {
        this.LegendDot('#5B8FF9', '主线')
        this.LegendDot('#4DD0A8', '机遇')
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
  InfiniteCanvasView() {
    Scroll() {
      Scroll() {
        Stack() {
          Column()
            .width(this.canvasWidth)
            .height(this.canvasHeight)
            .backgroundColor('#09111F')
            .backgroundImage('/resources/base/media/grid_bg.png')
            .opacity(0.98)

          Canvas(this.canvasContext)
            .width(this.canvasWidth)
            .height(this.canvasHeight)
            .backgroundColor('transparent')
            .onReady(() => {
              this.drawEdges()
            })

          ForEach(this.nodes, (node: MapNode) => {
            if (node.revealed) {
              this.MapNodeView(node)
            }
          })

          if (this.dragHintVisible) {
            Column({ space: 6 }) {
              Text('可双向拖动画布查看全部路径')
                .fontSize(12)
                .fontColor('#C8D4E3')
              Text('点击节点查看详情')
                .fontSize(10)
                .fontColor('#7AC7FF')
            }
            .padding(12)
            .backgroundColor('rgba(8,16,30,0.78)')
            .borderRadius(12)
            .position({ x: 24, y: 24 })
          }
        }
        .width(this.canvasWidth)
        .height(this.canvasHeight)
      }
      .scrollable(ScrollDirection.Horizontal)
      .scrollBar(BarState.Off)
      .onScroll(() => { this.dragHintVisible = false })
    }
    .scrollable(ScrollDirection.Vertical)
    .scrollBar(BarState.Auto)
    .onScroll(() => { this.dragHintVisible = false })
    .edgeEffect(EdgeEffect.Spring)
  }

  @Builder
  MapNodeView(node: MapNode) {
    Row({ space: 10 }) {
      Stack() {
        Column()
          .width(node.id.startsWith('root_') ? 56 : (this.getNodeImportance(node) === 3 ? 34 : (this.getNodeImportance(node) === 2 ? 30 : 26)))
          .height(node.id.startsWith('root_') ? 56 : (this.getNodeImportance(node) === 3 ? 34 : (this.getNodeImportance(node) === 2 ? 30 : 26)))
          .backgroundColor(node.color)
          .borderRadius(node.id.startsWith('root_') ? 16 : 14)
          .border({
            width: node.id === this.selectedNodeId ? 2.5 : (this.getNodeImportance(node) === 3 ? 1.5 : 1),
            color: node.id === this.selectedNodeId ? '#FFFFFF' : 'rgba(255,255,255,0.16)'
          })
          .shadow({
            radius: node.id === this.selectedNodeId ? 18 : (this.getNodeImportance(node) === 3 ? 12 : 8),
            color: node.color,
            offsetX: 0,
            offsetY: 0
          })

        Text(node.id.startsWith('root_') ? '起' : `${node.month}`)
          .fontSize(node.id.startsWith('root_') ? 15 : (this.getNodeImportance(node) === 3 ? 11 : 10))
          .fontWeight(700)
          .fontColor('#FFFFFF')
      }

      Column({ space: 4 }) {
        Text(node.title)
          .fontSize(node.id.startsWith('root_') ? 14 : 12)
          .fontWeight(node.id === this.selectedNodeId ? 700 : 600)
          .fontColor(node.id === this.selectedNodeId ? '#F8FBFF' : '#D7E0EA')
          .maxLines(2)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
          .width(node.id.startsWith('root_') ? 200 : 170)
        if (!node.id.startsWith('root_') && this.getNodeImportance(node) === 3) {
          Text('关键节点')
            .fontSize(9)
            .fontColor('#FFD166')
            .padding({ left: 6, right: 6, top: 2, bottom: 2 })
            .backgroundColor('rgba(255,209,102,0.12)')
            .borderRadius(6)
        }
      }
      .alignItems(HorizontalAlign.Start)
    }
    .padding({ left: 8, right: 12, top: 8, bottom: 8 })
    .backgroundColor(node.id === this.selectedNodeId ? 'rgba(122,199,255,0.14)' : 'rgba(255,255,255,0.04)')
    .borderRadius(18)
    .border({
      width: 1,
      color: node.id === this.selectedNodeId ? 'rgba(122,199,255,0.36)' : (this.getNodeImportance(node) === 3 ? 'rgba(255,209,102,0.18)' : 'rgba(255,255,255,0.06)')
    })
    .position({ x: node.position.x, y: node.position.y })
    .onClick(() => {
      this.selectedNodeId = node.id
      this.dragHintVisible = false
    })
    .animation({ duration: 260, curve: Curve.EaseOut })
  }


  @Builder
  TopPinnedSummary() {
    Column({ space: 8 }) {
      Scroll() {
        Row({ space: 10 }) {
          ForEach(this.optionSummaries, (item: OptionSummary) => {
            Column({ space: 6 }) {
              Row({ space: 6 }) {
                Column().width(8).height(8).borderRadius(4).backgroundColor(item.color)
                Text(item.title)
                  .fontSize(12)
                  .fontWeight(600)
                  .fontColor('#E6EDF5')
                  .maxLines(1)
              }
              Row({ space: 8 }) {
                Text(item.status)
                  .fontSize(10)
                  .fontColor(item.status === '推演中...' ? '#F5B041' : '#7AC7FF')
                if (item.finalScore > 0) {
                  Text(`${item.finalScore.toFixed(0)}分`)
                    .fontSize(10)
                    .fontColor(item.color)
                }
              }
            }
            .width(150)
            .padding(10)
            .backgroundColor('rgba(8,16,30,0.92)')
            .borderRadius(12)
            .border({ width: 1, color: 'rgba(255,255,255,0.06)' })
            .alignItems(HorizontalAlign.Start)
          })
        }
      }
      .scrollable(ScrollDirection.Horizontal)
      .scrollBar(BarState.Off)
    }
    .width('100%')
    .padding({ left: 14, right: 14, top: 10, bottom: 10 })
    .backgroundColor('rgba(10,15,30,0.90)')
  }

  @Builder
  DecisionRecommendationCard() {
    if (this.structuredRecommendation) {
      Column({ space: 8 }) {
        Row({ space: 8 }) {
          Column().width(10).height(10).borderRadius(5).backgroundColor('#5AD8A6')
          Text(`当前建议：${this.structuredRecommendation!.recommended_option}`)
            .fontSize(14)
            .fontWeight(700)
            .fontColor('#F0F6FC')
        }
        Text(this.structuredRecommendation!.summary)
          .fontSize(11)
          .fontColor('#C9D7E5')
          .lineHeight(18)
          .maxLines(3)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
      }
      .width('100%')
      .padding({ left: 14, right: 14, top: 10, bottom: 10 })
      .backgroundColor('rgba(90,216,166,0.10)')
      .border({ width: 1, color: 'rgba(90,216,166,0.18)' })
    }
  }

  @Builder
  ActivityOverlay() {
    Column({ space: 10 }) {
      Row({ space: 8 }) {
        Column().width(8).height(8).borderRadius(4).backgroundColor('#7AC7FF')
        Text('推演时间轴')
          .fontSize(12)
          .fontWeight(700)
          .fontColor('#EAF2FA')
      }
      if (this.streamStatus !== '') {
        Row({ space: 8 }) {
          LoadingProgress().width(14).height(14).color('#7AC7FF')
          Text(this.streamStatus)
            .fontSize(11)
            .fontColor('#7AC7FF')
            .maxLines(2)
        }
      }

      Scroll() {
        Column({ space: 10 }) {
          ForEach(this.activityLogs, (item: ActivityLogItem) => {
            Row({ space: 8 }) {
              Column()
                .width(8)
                .height(8)
                .borderRadius(4)
                .backgroundColor(item.kind === 'thinking' ? '#F6D06F' : (item.kind === 'node' ? '#4DD0A8' : '#7AC7FF'))
                .margin({ top: 5 })
              Text(item.text)
                .fontSize(10)
                .fontColor(item.kind === 'thinking' ? '#F6D06F' : '#D7E3EF')
                .maxLines(3)
                .textOverflow({ overflow: TextOverflow.Ellipsis })
                .layoutWeight(1)
            }
            .width('100%')
          })

          if (this.liveThinkingText !== '') {
            Column({ space: 4 }) {
              Text('模型实时输出')
                .fontSize(10)
                .fontColor('#F6D06F')
              Text(this.liveThinkingText)
                .fontSize(10)
                .fontColor('#F6D06F')
                .maxLines(8)
                .textOverflow({ overflow: TextOverflow.Ellipsis })
            }
            .width('100%')
            .padding(10)
            .backgroundColor('rgba(246,208,111,0.08)')
            .borderRadius(10)
          }

          if (this.liveRecommendationText !== '') {
            Column({ space: 4 }) {
              Text('推荐结论生成中')
                .fontSize(10)
                .fontColor('#9FD3FF')
              Text(this.liveRecommendationText)
                .fontSize(10)
                .fontColor('#9FD3FF')
                .maxLines(6)
                .textOverflow({ overflow: TextOverflow.Ellipsis })
            }
            .width('100%')
            .padding(10)
            .backgroundColor('rgba(122,199,255,0.08)')
            .borderRadius(10)
          }

          if (this.structuredRecommendation) {
            Column({ space: 8 }) {
              Text('结构化推荐')
                .fontSize(10)
                .fontColor('#7AC7FF')
              Text(`建议选择：${this.structuredRecommendation!.recommended_option}`)
                .fontSize(11)
                .fontWeight(700)
                .fontColor('#EAF2FA')
              Text(this.structuredRecommendation!.summary)
                .fontSize(10)
                .fontColor('#C8D6E5')
                .maxLines(3)
                .textOverflow({ overflow: TextOverflow.Ellipsis })

              if (this.structuredRecommendation!.reasons.length > 0) {
                Column({ space: 4 }) {
                  Text('推荐原因').fontSize(10).fontColor('#9FD3FF')
                  ForEach(this.structuredRecommendation!.reasons, (reason: string) => {
                    Text(`• ${reason}`)
                      .fontSize(10)
                      .fontColor('#D7E3EF')
                      .maxLines(2)
                      .textOverflow({ overflow: TextOverflow.Ellipsis })
                  })
                }
                .width('100%')
              }

              if (this.structuredRecommendation!.risks.length > 0) {
                Column({ space: 4 }) {
                  Text('风险提醒').fontSize(10).fontColor('#FFB3A7')
                  ForEach(this.structuredRecommendation!.risks, (risk: string) => {
                    Text(`• ${risk}`)
                      .fontSize(10)
                      .fontColor('#FFD6CF')
                      .maxLines(2)
                      .textOverflow({ overflow: TextOverflow.Ellipsis })
                  })
                }
                .width('100%')
              }

              if (this.structuredRecommendation!.actions.length > 0) {
                Column({ space: 4 }) {
                  Text('建议动作').fontSize(10).fontColor('#5AD8A6')
                  ForEach(this.structuredRecommendation!.actions, (action: string) => {
                    Text(`• ${action}`)
                      .fontSize(10)
                      .fontColor('#D8F5EA')
                      .maxLines(2)
                      .textOverflow({ overflow: TextOverflow.Ellipsis })
                  })
                }
                .width('100%')
              }
            }
            .width('100%')
            .padding(10)
            .backgroundColor('rgba(90,216,166,0.10)')
            .borderRadius(10)
          }
        }
        .width('100%')
      }
      .height(260)
      .scrollBar(BarState.Off)
    }
    .width(300)
    .padding(12)
    .backgroundColor('rgba(8,16,30,0.88)')
    .borderRadius(14)
    .border({ width: 1, color: 'rgba(255,255,255,0.06)' })
    .alignItems(HorizontalAlign.Start)
    .position({ x: 16, y: 16 })
  }

  @Builder
  NodeDetailOverlay() {
    if (this.selectedNodeId !== '') {
      Column() {
        Blank().layoutWeight(1)

        Column({ space: 10 }) {
          Row() {
            Row({ space: 8 }) {
              Column()
                .width(12)
                .height(12)
                .borderRadius(6)
                .backgroundColor(this.getSelectedNode() ? this.getSelectedNode()!.color : '#5B8FF9')
              Text(this.getSelectedNode() ? this.getSelectedNode()!.title : '')
                .fontSize(17)
                .fontWeight(700)
                .fontColor('#F2F6FB')
                .layoutWeight(1)
            }
            .layoutWeight(1)

            Button('关闭')
              .fontSize(11)
              .fontColor('#D7E4F3')
              .backgroundColor('rgba(255,255,255,0.06)')
              .borderRadius(10)
              .onClick(() => { this.selectedNodeId = '' })
          }
          .width('100%')

          Text(this.getSelectedNode() ? this.getSelectedNode()!.description : '')
            .fontSize(13)
            .fontColor('#B8C5D4')
            .lineHeight(20)

          Text(this.getNodeInterpretation(this.getSelectedNode()))
            .fontSize(11)
            .fontColor('#9FD3FF')
            .lineHeight(18)
            .padding(10)
            .backgroundColor('rgba(122,199,255,0.08)')
            .borderRadius(10)
            .width('100%')

          Row({ space: 8 }) {
            Text(this.getSelectedNode() ? this.getSelectedNode()!.optionTitle : '')
              .fontSize(11)
              .fontColor(this.getSelectedNode() ? this.getSelectedNode()!.color : '#5B8FF9')
              .padding({ left: 8, right: 8, top: 4, bottom: 4 })
              .backgroundColor('rgba(255,255,255,0.05)')
              .borderRadius(8)
            Text(`月 ${this.getSelectedNode() ? this.getSelectedNode()!.month : 0}`)
              .fontSize(11)
              .fontColor('#DCE7F2')
              .padding({ left: 8, right: 8, top: 4, bottom: 4 })
              .backgroundColor('rgba(255,255,255,0.05)')
              .borderRadius(8)
            Text(`概率 ${this.getSelectedNode() ? (this.getSelectedNode()!.probability * 100).toFixed(0) : '0'}%`)
              .fontSize(11)
              .fontColor('#7AC7FF')
              .padding({ left: 8, right: 8, top: 4, bottom: 4 })
              .backgroundColor('rgba(255,255,255,0.05)')
              .borderRadius(8)
          }

          Row({ space: 8 }) {
            Text(`风险 ${this.getSelectedNode() ? this.getSelectedNode()!.riskTag : 'medium'}`)
              .fontSize(11)
              .fontColor(this.getRiskColor(this.getSelectedNode() ? this.getSelectedNode()!.riskTag : 'medium'))
              .padding({ left: 8, right: 8, top: 4, bottom: 4 })
              .backgroundColor('rgba(255,255,255,0.05)')
              .borderRadius(8)
            if (this.getSelectedNode() && this.getSelectedNode()!.isBranch) {
              Text('分支节点')
                .fontSize(11)
                .fontColor('#F5B041')
                .padding({ left: 8, right: 8, top: 4, bottom: 4 })
                .backgroundColor('rgba(255,255,255,0.05)')
                .borderRadius(8)
            }
          }

          if (this.getSelectedNode() && Object.keys(this.getSelectedNode()!.impact).length > 0) {
            Column({ space: 6 }) {
              Text('影响维度')
                .fontSize(11)
                .fontColor('#7F91A5')
                .width('100%')
                .textAlign(TextAlign.Start)

              ForEach(Object.keys(this.getSelectedNode()!.impact), (key: string) => {
                Row({ space: 8 }) {
                  Text(key).fontSize(11).fontColor('#B9C6D4').width(52)
                  Row() {
                    Column()
                      .width(`${Math.min(Math.abs(this.getSelectedNode()!.impact[key]) * 100, 100)}%`)
                      .height(6)
                      .borderRadius(3)
                      .backgroundColor(this.getSelectedNode()!.impact[key] >= 0 ? '#4DD0A8' : '#FF6B6B')
                  }
                  .layoutWeight(1)
                  .height(6)
                  .backgroundColor('rgba(255,255,255,0.06)')
                  .borderRadius(3)

                  Text(`${this.getSelectedNode()!.impact[key] > 0 ? '+' : ''}${this.getSelectedNode()!.impact[key].toFixed(1)}`)
                    .fontSize(10)
                    .fontColor(this.getSelectedNode()!.impact[key] >= 0 ? '#4DD0A8' : '#FF6B6B')
                }
                .width('100%')
              })
            }
            .width('100%')
          }
        }
        .width('100%')
        .padding(16)
        .backgroundColor('rgba(8,15,28,0.96)')
        .borderRadius({ topLeft: 20, topRight: 20, bottomLeft: 0, bottomRight: 0 })
        .border({ width: 1, color: 'rgba(255,255,255,0.08)' })
      }
      .width('100%')
      .height('100%')
    }
  }
}
