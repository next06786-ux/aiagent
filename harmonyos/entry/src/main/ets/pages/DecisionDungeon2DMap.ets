/**
 * 决策副本 2D 地图
 * 白色极简版：每个选项独立地图 + 左侧可收起时间轴 + 单地图箭头链路
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
  fromId?: string
  toId?: string
  isBranch?: boolean
}

interface OptionSummary {
  index: number
  title: string
  color: string
  finalScore: number
  riskLevel: number
  status: string
  progress: number
}

interface StreamRequestPayload {
  session_id: string
  options: StreamRequestOption[]
}

interface StreamRequestOption {
  title: string
  description: string
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
  running?: boolean
}

@Entry
@Component
struct DecisionDungeon2DMap {
  @State dungeonData: DungeonData | null = null
  @State isLoading: boolean = false
  @State optionSummaries: OptionSummary[] = []
  @State nodes: MapNode[] = []
  @State edges: EdgeLine[] = []
  @State activeOptionIndex: number = 0
  @State selectedNodeId: string = ''
  @State processingNodeId: string = ''
  @State streamStatus: string = ''
  @State showRecommendation: boolean = false
  @State timelineCollapsed: boolean = false
  @State liveThinkingText: string = ''
  @State liveRecommendationText: string = ''
  @State structuredRecommendation: RecommendationData | null = null
  @State activityLogs: ActivityLogItem[] = []
  @State zoomScale: number = 1
  @State isUpdatingModel: boolean = false

  private dungeonId: string = ''
  private userId: string = ''
  private ws: WebSocketUtil | null = null
  private canvasWidth: number = 3600
  private canvasHeight: number = 2200
  private canvasContext: CanvasRenderingContext2D = new CanvasRenderingContext2D(new RenderingContextSettings(true))


  aboutToAppear() {
    const params = router.getParams() as Record<string, string>
    if (params?.simulationData) {
      try {
        const simData = JSON.parse(params.simulationData) as Record<string, Object>
        const options = simData.options as DungeonOption[]
        const hasTimeline = options && options.length > 0 && options[0].timeline && options[0].timeline.length > 0
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
        status: '等待推演',
        progress: 0.05
      })
    }
    this.optionSummaries = summaries
  }

  private buildGraphFromDungeon() {
    if (!this.dungeonData) return
    const allNodes: MapNode[] = []
    const allEdges: EdgeLine[] = []
    const summaries: OptionSummary[] = []

    this.dungeonData.options.forEach((option: DungeonOption, optionIndex: number) => {
      const optionColor = this.getOptionColor(optionIndex)
      const rootId = `root_${optionIndex}`
      const rootY = 320
      const startX = 240
      const stepX = 360

      summaries.push({
        index: optionIndex,
        title: option.title,
        color: optionColor,
        finalScore: option.final_score,
        riskLevel: option.risk_level,
        status: '推演完成',
        progress: 1
      })

      allNodes.push({
        id: rootId,
        parentId: '',
        title: this.getShortNodeTitle(option.title),
        description: option.description || '推演起点',
        month: 0,
        probability: 1,
        position: { x: 120, y: rootY },
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
        const parentId = event.parent_event_id || previousId
        const parentNode = allNodes.find((item: MapNode) => item.id === parentId)
        const x = startX + idx * stepX
        const y = rootY + (((idx % 2) === 0) ? -120 : 120)

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
            color: optionColor,
            fromId: parentNode.id,
            toId: nodeId,
            isBranch: false
          })
        }
        previousId = nodeId
      })

      branchEvents.forEach((event: TimelineEvent, idx: number) => {
        const nodeId = event.event_id || `opt${optionIndex}_branch_${idx}`
        const parentId = event.parent_event_id || previousId
        const parentNode = allNodes.find((item: MapNode) => item.id === parentId)
        const isPositive = event.risk_tag === 'low' || event.opportunity_tag === 'high'
        const x = (parentNode ? parentNode.position.x : startX + 300) + 280
        const y = (parentNode ? parentNode.position.y : rootY) + (isPositive ? -(240 + idx * 80) : (240 + idx * 80))
        const color = isPositive ? '#5AD8A6' : '#E8684A'

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
            color,
            fromId: parentNode.id,
            toId: nodeId,
            isBranch: true
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


  private getVisibleNodes(): MapNode[] {
    return this.nodes.filter((item: MapNode) => item.optionIndex === this.activeOptionIndex)
  }

  private getVisibleEdges(): EdgeLine[] {
    return this.edges.filter((item: EdgeLine) => {
      const fromNode = this.nodes.find((node: MapNode) => node.id === item.fromId)
      return !!fromNode && fromNode.optionIndex === this.activeOptionIndex
    })
  }

  private drawEdges() {
    this.canvasContext.clearRect(0, 0, this.canvasWidth, this.canvasHeight)
    this.getVisibleEdges().forEach((edge: EdgeLine) => {
      const isActivePath = this.processingNodeId !== '' && (edge.toId === this.processingNodeId || edge.fromId === this.processingNodeId)
      this.canvasContext.beginPath()
      this.canvasContext.strokeStyle = isActivePath ? '#3B82F6' : edge.color
      this.canvasContext.lineWidth = isActivePath ? 4 : (edge.isBranch ? 2 : 3)
      this.canvasContext.globalAlpha = isActivePath ? 0.95 : (edge.isBranch ? 0.55 : 0.82)
      if (Math.abs(edge.fromY - edge.toY) < 90) {
        this.canvasContext.moveTo(edge.fromX, edge.fromY)
        this.canvasContext.lineTo(edge.toX, edge.toY)
      } else {
        const midX = (edge.fromX + edge.toX) / 2
        this.canvasContext.moveTo(edge.fromX, edge.fromY)
        this.canvasContext.bezierCurveTo(midX, edge.fromY, midX, edge.toY, edge.toX, edge.toY)
      }
      this.canvasContext.stroke()
      this.canvasContext.globalAlpha = 1
      const angle = Math.atan2(edge.toY - edge.fromY, edge.toX - edge.fromX)
      const arrowLen = isActivePath ? 14 : 12
      this.canvasContext.beginPath()
      this.canvasContext.fillStyle = isActivePath ? '#3B82F6' : edge.color
      this.canvasContext.moveTo(edge.toX, edge.toY)
      this.canvasContext.lineTo(edge.toX - arrowLen * Math.cos(angle - Math.PI / 6), edge.toY - arrowLen * Math.sin(angle - Math.PI / 6))
      this.canvasContext.lineTo(edge.toX - arrowLen * Math.cos(angle + Math.PI / 6), edge.toY - arrowLen * Math.sin(angle + Math.PI / 6))
      this.canvasContext.closePath()
      this.canvasContext.fill()
    })
  }

  private async startStreamSimulation() {
    if (!this.dungeonId) {
      this.streamStatus = '缺少会话信息'
      return
    }
    this.streamStatus = '正在准备推演...'
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
                this.activeOptionIndex = optionIndex
                this.updateOptionStatus(optionIndex, '推演中...')
                this.addRootNode(optionIndex, title)
                this.processingNodeId = `root_${optionIndex}`
                this.pushActivityLog('option', `开始推演 ${title}`)
                this.drawEdges()
              }
            } else if (type === 'node') {
              this.handleStreamNode(event)
            } else if (type === 'option_complete') {
              const title = event.title as string
              const optionIndex = this.findOptionIndexByTitle(title)
              if (optionIndex >= 0) {
                this.updateOptionScore(optionIndex, event.final_score as number, event.risk_level as number)
                this.updateOptionStatus(optionIndex, '推演完成')
                this.processingNodeId = ''
                this.pushActivityLog('option', `${title} 推演完成，已完成评分与风险计算`)
                this.drawEdges()
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
      this.ws.onError((_error: string) => { this.streamStatus = '连接失败' })
      this.ws.onClose(() => { console.info('推演 WebSocket 已关闭') })
      await this.ws.connect('/api/decision/enhanced/ws/simulate')
      this.streamStatus = '推演通道已建立，等待模型响应...'
      const streamOptions: StreamRequestOption[] = this.dungeonData ? this.dungeonData.options.map((item: DungeonOption): StreamRequestOption => {
        return { title: item.title, description: item.description }
      }) : []
      const payload: StreamRequestPayload = { session_id: this.dungeonId, options: streamOptions }
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

    const parentId = (node.parent_event_id as string) || `root_${optionIndex}`
    const parentNode = this.nodes.find((item: MapNode) => item.id === parentId)
    const optionNodes = this.nodes.filter((item: MapNode) => item.optionIndex === optionIndex && !item.id.startsWith('root_'))
    const nodeCount = optionNodes.length
    const isBranch = ((node.branch_group as string) || '').includes('fork')
    const month = (node.month as number) || (nodeCount + 1)

    let x: number
    let y: number
    if (isBranch && parentNode) {
      const isPositive = (node.risk_tag as string) === 'low' || (node.opportunity_tag as string) === 'high'
      const branchSiblings = this.nodes.filter((item: MapNode) => item.parentId === parentId && item.isBranch).length
      x = parentNode.position.x + 320
      y = parentNode.position.y + (isPositive ? -(220 + branchSiblings * 90) : (220 + branchSiblings * 90))
    } else {
      x = 320 + month * 320
      y = 320 + (((month - 1) % 2 === 0) ? -140 : 140)
    }

    const color = isBranch
      ? (((node.risk_tag as string) === 'low' || (node.opportunity_tag as string) === 'high') ? '#5AD8A6' : '#E8684A')
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
        color,
        fromId: parentNode.id,
        toId: mapNode.id,
        isBranch
      })
    }

    this.nodes = nextNodes
    this.edges = nextEdges
    this.activeOptionIndex = optionIndex
    this.selectedNodeId = mapNode.id
    this.processingNodeId = mapNode.id
    this.pushActivityLog('node', `${optionTitle} 新增节点：${mapNode.title}`)
    this.drawEdges()
  }

  private addRootNode(optionIndex: number, title: string) {
    const rootId = `root_${optionIndex}`
    const exists = this.nodes.some((item: MapNode) => item.id === rootId)
    if (exists) return
    this.nodes = this.nodes.concat([{ id: rootId, parentId: '', title, description: '推演起点', month: 0, probability: 1, position: { x: 120, y: 320 }, color: this.getOptionColor(optionIndex), riskTag: 'medium', opportunityTag: 'medium', eventType: 'origin', impact: {}, isBranch: false, revealed: true, optionIndex, optionTitle: title }])
    if (this.selectedNodeId === '') this.selectedNodeId = rootId
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
      return { index: item.index, title: item.title, color: item.color, finalScore: item.finalScore, riskLevel: item.riskLevel, status, progress: status === '推演中...' ? Math.max(item.progress, 0.35) : item.progress }
    })
  }

  private updateOptionScore(optionIndex: number, score: number, risk: number) {
    this.optionSummaries = this.optionSummaries.map((item: OptionSummary) => {
      if (item.index !== optionIndex) return item
      return { index: item.index, title: item.title, color: item.color, finalScore: score, riskLevel: risk, status: item.status, progress: 1 }
    })
  }

  private async loadDungeonData() {
    this.isLoading = true
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(ApiConfig.getApiUrl(`/api/decision/result/${this.dungeonId}`), {
        method: http.RequestMethod.GET,
        header: { 'Content-Type': 'application/json' },
        connectTimeout: 30000,
        readTimeout: 30000
      })
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
    const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
    return colors[index % colors.length]
  }

  private getRiskColor(tag: string): string {
    if (tag === 'low') return '#10B981'
    if (tag === 'high') return '#EF4444'
    return '#F59E0B'
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
    text = text.replace(/\s+/g, ' ').trim()
    return text.length > 20 ? text.slice(0, 20) + '...' : (text === '' ? '新事件' : text)
  }

  private pushActivityLog(kind: string, text: string, running: boolean = false) {
    const next = this.activityLogs.concat([{ id: `${Date.now()}_${this.activityLogs.length}`, kind, text, running }])
    this.activityLogs = next.length > 14 ? next.slice(next.length - 14) : next
  }

  private getNodeInterpretation(node: MapNode | null): string {
    if (!node) return ''
    const impacts = Object.keys(node.impact).filter((key: string) => Math.abs(node.impact[key]) > 0.05).map((key: string) => `${key}${node.impact[key] > 0 ? '提升' : '承压'}`)
    const impactSummary = impacts.length > 0 ? impacts.join('、') : '整体影响较平稳'
    return node.isBranch
      ? `这是一个分支事件，表示主路径在这里出现了新的变化方向，主要影响 ${impactSummary}。`
      : `这是主路径上的关键事件，表示该选项在这个阶段出现了新的推进或反馈，主要影响 ${impactSummary}。`
  }

  private getNodeImportance(node: MapNode): number {
    const impactScore = Object.keys(node.impact).reduce((sum: number, key: string) => sum + Math.abs(node.impact[key]), 0)
    if (node.id.startsWith('root_')) return 3
    if (impactScore >= 1.2 || node.riskTag === 'high' || node.opportunityTag === 'high') return 3
    if (impactScore >= 0.5) return 2
    return 1
  }

  private resetZoom() {
    this.zoomScale = 1
    this.drawEdges()
  }

  private fitCurrentOption() {
    const visible = this.getVisibleNodes()
    if (visible.length <= 0) {
      this.zoomScale = 1
    } else if (visible.length <= 4) {
      this.zoomScale = 1.1
    } else if (visible.length <= 8) {
      this.zoomScale = 0.9
    } else {
      this.zoomScale = 0.75
    }
    this.drawEdges()
  }


  build() {
    Column() {
      this.HeaderBar()
      if (this.isLoading) {
        Column({ space: 16 }) {
          LoadingProgress().width(42).height(42).color('#3B82F6')
          Text('正在准备推演').fontSize(16).fontWeight(700).fontColor('#111827')
          Text('系统正在读取信息并准备地图').fontSize(12).fontColor('#6B7280')
        }.layoutWeight(1).width('100%').justifyContent(FlexAlign.Center)
      } else if (this.optionSummaries.length > 0) {
        Column({ space: 0 }) {
          this.TopOptionTabs()
          if (this.structuredRecommendation) {
            this.DecisionRecommendationCard()
          }
          Row() {
            this.ActivitySidebar()
            Stack() {
              this.OptionCanvasView()
              this.NodeDetailOverlay()
            }
            .layoutWeight(1)
          }
          .layoutWeight(1)
        }
        .layoutWeight(1)
      } else {
        Column({ space: 12 }) {
          Text('等待推演数据...').fontSize(16).fontColor('#6B7280')
          Text(this.streamStatus).fontSize(12).fontColor('#3B82F6')
        }.layoutWeight(1).width('100%').justifyContent(FlexAlign.Center)
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F8FAFC')
  }

  @Builder
  HeaderBar() {
    Row() {
      Button({ type: ButtonType.Circle }) { Text('←').fontSize(22).fontColor('#111827').fontWeight(700) }
        .width(40).height(40).backgroundColor('#FFFFFF').onClick(() => router.back())
      Column({ space: 2 }) {
        Text('决策推演地图').fontSize(20).fontWeight(700).fontColor('#111827')
        if (this.dungeonData) { Text(this.dungeonData.title).fontSize(12).fontColor('#6B7280').maxLines(1) }
      }
      .alignItems(HorizontalAlign.Start)
      .layoutWeight(1)
      .margin({ left: 12 })
      Row({ space: 8 }) {
        Button(this.isUpdatingModel ? '更新中' : '更新用户模型')
          .fontSize(11)
          .fontColor('#10B981')
          .backgroundColor('#FFFFFF')
          .enabled(!this.isUpdatingModel)
          .onClick(() => { this.triggerModelUpdate() })
        Button('适配').fontSize(11).fontColor('#3B82F6').backgroundColor('#FFFFFF').onClick(() => { this.fitCurrentOption() })
        Button('重置').fontSize(11).fontColor('#374151').backgroundColor('#FFFFFF').onClick(() => { this.resetZoom() })
      }
    }
    .width('100%')
    .padding({ left: 16, right: 16, top: 16, bottom: 12 })
    .backgroundColor('#F8FAFC')
  }

  @Builder
  TopOptionTabs() {
    Scroll() {
      Row({ space: 10 }) {
        ForEach(this.optionSummaries, (item: OptionSummary) => {
          Column({ space: 6 }) {
            Text(item.title).fontSize(12).fontWeight(600).fontColor(this.activeOptionIndex === item.index ? '#111827' : '#6B7280')
            Text(item.status).fontSize(10).fontColor(item.color)
            Row() {
              Column().width(`${item.progress * 100}%`).height(4).borderRadius(2).backgroundColor(item.color)
            }
            .width(120)
            .height(4)
            .backgroundColor('#E5E7EB')
            .borderRadius(2)
          }
          .padding(10)
          .backgroundColor(this.activeOptionIndex === item.index ? '#FFFFFF' : '#F3F4F6')
          .borderRadius(12)
          .border({ width: 1, color: this.activeOptionIndex === item.index ? '#D1D5DB' : 'transparent' })
          .onClick(() => {
            this.activeOptionIndex = item.index
            this.fitCurrentOption()
          })
        })
      }
    }
    .scrollable(ScrollDirection.Horizontal)
    .scrollBar(BarState.Off)
    .width('100%')
    .padding({ left: 14, right: 14, top: 6, bottom: 10 })
  }

  @Builder
  DecisionRecommendationCard() {
    if (this.structuredRecommendation) {
      Column({ space: 6 }) {
        Text(`建议选择：${this.structuredRecommendation!.recommended_option}`).fontSize(14).fontWeight(700).fontColor('#111827')
        Text(this.structuredRecommendation!.summary).fontSize(11).fontColor('#4B5563').maxLines(3).textOverflow({ overflow: TextOverflow.Ellipsis })
      }
      .width('100%')
      .padding({ left: 14, right: 14, top: 10, bottom: 10 })
      .backgroundColor('#FFFFFF')
      .border({ width: 1, color: '#E5E7EB' })
    }
  }

  @Builder
  ActivitySidebar() {
    Column({ space: 10 }) {
      if (!this.timelineCollapsed) {
        Column({ space: 10 }) {
          Row() {
            Text('推演时间轴').fontSize(12).fontWeight(700).fontColor('#111827').layoutWeight(1)
            Button('收起')
              .fontSize(10)
              .fontColor('#3B82F6')
              .backgroundColor('#FFFFFF')
              .onClick(() => { this.timelineCollapsed = true })
          }
          .width('100%')

          Column({ space: 6 }) {
            Row({ space: 6 }) { LoadingProgress().width(10).height(10).color('#3B82F6'); Text('1. 主链生成').fontSize(10).fontColor('#6B7280') }
            Row({ space: 6 }) { LoadingProgress().width(10).height(10).color('#F59E0B'); Text('2. 分支补全').fontSize(10).fontColor('#6B7280') }
            Row({ space: 6 }) { LoadingProgress().width(10).height(10).color('#10B981'); Text('3. 推荐汇总').fontSize(10).fontColor('#6B7280') }
          }
          .width('100%')
          .padding(8)
          .backgroundColor('#FFFFFF')
          .borderRadius(10)

          Scroll() {
            Column({ space: 10 }) {
              ForEach(this.activityLogs, (item: ActivityLogItem) => {
                Row({ space: 8 }) {
                  if (item.running) {
                    LoadingProgress().width(10).height(10).color('#3B82F6')
                  } else {
                    Column().width(6).height(6).borderRadius(3).backgroundColor(item.kind === 'thinking' ? '#F59E0B' : (item.kind === 'node' ? '#10B981' : '#3B82F6')).margin({ top: 6 })
                  }
                  Text(item.text).fontSize(10).fontColor('#374151').maxLines(4).textOverflow({ overflow: TextOverflow.Ellipsis }).layoutWeight(1)
                }.width('100%')
              })
              if (this.liveThinkingText !== '') {
                Column({ space: 4 }) {
                  Text('模型实时输出').fontSize(10).fontColor('#F59E0B')
                  Text(this.liveThinkingText).fontSize(10).fontColor('#92400E').maxLines(12).textOverflow({ overflow: TextOverflow.Ellipsis })
                }
                .width('100%').padding(8).backgroundColor('#FEF3C7').borderRadius(10)
              }
            }
            .width('100%')
          }
          .height('100%')
          .scrollBar(BarState.Off)
        }
        .width('100%')
      } else {
        Button('展开')
          .fontSize(11)
          .fontColor('#3B82F6')
          .backgroundColor('#FFFFFF')
          .onClick(() => { this.timelineCollapsed = false })
      }
    }
    .width(this.timelineCollapsed ? 68 : 220)
    .height('100%')
    .padding(10)
    .backgroundColor('#F3F4F6')
  }

  @Builder
  OptionCanvasView() {
    Scroll() {
      Scroll() {
        Stack() {
          Column().width(this.canvasWidth * this.zoomScale).height(this.canvasHeight * this.zoomScale).backgroundColor('#FFFFFF')
          Canvas(this.canvasContext)
            .width(this.canvasWidth * this.zoomScale)
            .height(this.canvasHeight * this.zoomScale)
            .backgroundColor('transparent')
            .onReady(() => { this.drawEdges() })
          ForEach(this.getVisibleNodes(), (node: MapNode) => {
            if (node.revealed) {
              this.MapNodeView(node)
            }
          })
        }
        .width(this.canvasWidth * this.zoomScale)
        .height(this.canvasHeight * this.zoomScale)
      }
      .scrollable(ScrollDirection.Horizontal)
      .scrollBar(BarState.Off)
    }
    .scrollable(ScrollDirection.Vertical)
    .scrollBar(BarState.Auto)
  }

  @Builder
  MapNodeView(node: MapNode) {
    Row({ space: 10 }) {
      Stack() {
        Column().width(node.id.startsWith('root_') ? 56 : 30).height(node.id.startsWith('root_') ? 56 : 30)
          .backgroundColor(node.color)
          .borderRadius(node.id.startsWith('root_') ? 16 : 15)
          .border({ width: node.id === this.selectedNodeId ? 2.5 : 1, color: node.id === this.selectedNodeId ? '#111827' : '#D1D5DB' })
        if (this.processingNodeId === node.id) {
          Column().width(node.id.startsWith('root_') ? 66 : 40).height(node.id.startsWith('root_') ? 66 : 40)
            .border({ width: 2, color: '#3B82F6' }).borderRadius(20).opacity(0.85)
            .animation({ duration: 700, curve: Curve.EaseInOut, iterations: -1, playMode: PlayMode.Alternate })
        }
        Text(node.id.startsWith('root_') ? '起' : `${node.month}`).fontSize(11).fontWeight(700).fontColor('#FFFFFF')
      }
      Column({ space: 4 }) {
        Text(node.title).fontSize(12).fontWeight(600).fontColor('#111827').maxLines(2).textOverflow({ overflow: TextOverflow.Ellipsis }).width(170)
        Row({ space: 6 }) {
          Text(node.isBranch ? '分支' : '主链').fontSize(9).fontColor(node.isBranch ? '#B45309' : '#2563EB')
            .padding({ left: 6, right: 6, top: 2, bottom: 2 }).backgroundColor(node.isBranch ? '#FEF3C7' : '#DBEAFE').borderRadius(6)
          if (this.processingNodeId === node.id) {
            Row({ space: 4 }) { LoadingProgress().width(10).height(10).color('#3B82F6'); Text('处理中').fontSize(9).fontColor('#3B82F6') }
          }
        }
      }.alignItems(HorizontalAlign.Start)
    }
    .padding({ left: 8, right: 12, top: 8, bottom: 8 })
    .backgroundColor(node.id === this.selectedNodeId ? '#EFF6FF' : '#FFFFFF')
    .borderRadius(18)
    .border({ width: 1, color: node.isBranch ? '#FDE68A' : '#E5E7EB' })
    .position({ x: node.position.x * this.zoomScale, y: node.position.y * this.zoomScale })
    .onClick(() => { this.selectedNodeId = node.id })
  }


  @Builder
  NodeDetailOverlay() {
    if (this.selectedNodeId !== '') {
      Column() {
        Blank().layoutWeight(1)
        Column({ space: 10 }) {
          Row() {
            Text(this.getSelectedNode() ? this.getSelectedNode()!.title : '').fontSize(17).fontWeight(700).fontColor('#111827').layoutWeight(1)
            Button('关闭').fontSize(11).fontColor('#374151').backgroundColor('#FFFFFF').onClick(() => { this.selectedNodeId = '' })
          }
          Text(this.getSelectedNode() ? this.getSelectedNode()!.description : '').fontSize(13).fontColor('#4B5563').lineHeight(20)
          Text(this.getNodeInterpretation(this.getSelectedNode())).fontSize(11).fontColor('#2563EB').lineHeight(18).padding(10).backgroundColor('#EFF6FF').borderRadius(10).width('100%')
        }
        .width('100%')
        .padding(16)
        .backgroundColor('#FFFFFF')
        .border({ width: 1, color: '#E5E7EB' })
      }
      .width('100%')
      .height('100%')
    }
  }

  private async triggerModelUpdate() {
    if (!this.dungeonData || this.isUpdatingModel) return
    this.isUpdatingModel = true
    const userId = this.dungeonData.user_id
    this.pushActivityLog('system', '正在更新用户模型...', true)
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        ApiConfig.getApiUrl(`/api/lora/train/${userId}`),
        {
          method: http.RequestMethod.POST,
          header: { 'Content-Type': 'application/json' },
          connectTimeout: 30000,
          readTimeout: 30000
        }
      )
      httpRequest.destroy()
      if (response.responseCode === 200) {
        promptAction.showToast({ message: '已触发用户模型更新', duration: 2000 })
        this.pushActivityLog('system', '用户模型更新任务已触发')
      } else {
        promptAction.showToast({ message: '模型更新触发失败', duration: 2000 })
      }
    } catch (error) {
      promptAction.showToast({ message: '模型更新失败', duration: 2000 })
    }
    this.isUpdatingModel = false
  }
}
