/**
 * 决策推演地图 - HarmonyOS 6 流体设计
 * 横向时间线 + 节点逐个出现 + 点击查看详情
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import promptAction from '@ohos.promptAction'
import { ApiConfig } from '../config/ApiConfig'
import { WebSocketUtil } from '../utils/WebSocketUtil'
import { Theme } from '../common/Theme'

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
  eventType: string
  impact: Record<string, number>
  isBranch: boolean
  optionIndex: number
  optionTitle: string
}

interface NodePosition {
  x: number
  y: number
}

interface EdgeLine {
  fromX: number
  fromY: number
  toX: number
  toY: number
  color: string
  fromId: string
  toId: string
  isBranch: boolean
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
  @State showDetail: boolean = false
  @State structuredRecommendation: RecommendationData | null = null
  @State liveThinkingText: string = ''
  @State isUpdatingModel: boolean = false
  @State showContent: boolean = false
  @State zoomScale: number = 1

  private dungeonId: string = ''
  private userId: string = ''
  private ws: WebSocketUtil | null = null
  private canvasWidth: number = 3600
  private canvasHeight: number = 1600
  private canvasCtx: CanvasRenderingContext2D = new CanvasRenderingContext2D(new RenderingContextSettings(true))

  aboutToAppear() {
    const params = router.getParams() as Record<string, string>
    if (params?.simulationData) {
      try {
        const simData = JSON.parse(params.simulationData) as Record<string, Object>
        const options = simData.options as DungeonOption[]
        const hasTimeline = options && options.length > 0 && options[0].timeline && options[0].timeline.length > 0
        if (hasTimeline) {
          this.dungeonData = {
            dungeon_id: simData.simulation_id as string || 'temp',
            user_id: simData.user_id as string || this.userId,
            title: params.question || '决策推演',
            description: '',
            options: options,
            recommendation: simData.recommendation as string || '',
            created_at: simData.created_at as string || new Date().toISOString()
          }
          this.buildFromExisting()
        } else {
          this.dungeonId = (simData.simulation_id as string) || (params.dungeonId || '')
          this.userId = (simData.user_id as string) || (params.userId || '')
          const fullOptions: DungeonOption[] = []
          if (options) {
            for (let i = 0; i < options.length; i++) {
              fullOptions.push({
                option_id: options[i].option_id || `option_${i + 1}`,
                title: options[i].title || `选项${i + 1}`,
                description: options[i].description || '',
                timeline: [], final_score: 0, risk_level: 0
              })
            }
          }
          this.dungeonData = {
            dungeon_id: this.dungeonId, user_id: this.userId,
            title: params.question || '决策推演', description: '正在启动推演...',
            options: fullOptions, recommendation: '', created_at: new Date().toISOString()
          }
          this.initSummaries(fullOptions)
          this.startStreamSimulation()
        }
      } catch (e) { console.error('解析失败:', (e as Error).message) }
      return
    }
    if (params?.dungeonId) {
      this.dungeonId = params.dungeonId
      this.userId = params.userId || ''
      // 历史记录查看模式：从后端加载已保存的推演数据
      if (params.isHistory === 'true') {
        this.loadHistoryRecord(params.dungeonId, params.question || '', params.recommendation || '')
      }
    }
    setTimeout(() => { this.showContent = true }, 50)
  }

  aboutToDisappear() {
    if (this.ws) { this.ws.close(); this.ws = null }
  }

  // ===== 数据方法 =====
  private buildFromExisting() {
    if (!this.dungeonData) return
    const allNodes: MapNode[] = []
    const allEdges: EdgeLine[] = []
    const summaries: OptionSummary[] = []
    this.dungeonData.options.forEach((opt: DungeonOption, oi: number) => {
      summaries.push({ index: oi, title: opt.title, color: this.optColor(oi),
        finalScore: opt.final_score, riskLevel: opt.risk_level, status: '推演完成', progress: 1 })
      const rootId = `root_${oi}`
      allNodes.push({ id: rootId, parentId: '', title: opt.title, description: '起点',
        month: 0, probability: 1, position: { x: 120, y: 400 },
        color: this.optColor(oi), riskTag: 'medium', eventType: 'origin',
        impact: {}, isBranch: false, optionIndex: oi, optionTitle: opt.title })
      let prevId = rootId
      opt.timeline.forEach((ev: TimelineEvent, ei: number) => {
        const nodeId = ev.event_id || `opt${oi}_${ei}`
        const isBranch = !!(ev.branch_group && ev.branch_group.includes('fork'))
        const x = 360 + ei * 340
        const y = isBranch ? (400 + (ei % 2 === 0 ? -220 : 220)) : (400 + (ei % 2 === 0 ? -120 : 120))
        const color = isBranch ? (ev.risk_tag === 'low' ? '#10B981' : '#EF4444') : this.optColor(oi)
        allNodes.push({ id: nodeId, parentId: prevId, title: this.shortTitle(ev.event),
          description: ev.event, month: ev.month, probability: ev.probability,
          position: { x, y }, color, riskTag: ev.risk_tag || 'medium',
          eventType: ev.event_type || 'general', impact: ev.impact,
          isBranch, optionIndex: oi, optionTitle: opt.title })
        const parentNode = allNodes.find((n: MapNode) => n.id === prevId)
        if (parentNode) {
          allEdges.push({ fromX: parentNode.position.x, fromY: parentNode.position.y,
            toX: x, toY: y, color, fromId: prevId, toId: nodeId, isBranch })
        }
        if (!isBranch) prevId = nodeId
      })
    })
    this.optionSummaries = summaries
    this.nodes = allNodes
    this.edges = allEdges
    this.showContent = true
    this.drawCanvas()
  }

  private initSummaries(options: DungeonOption[]) {
    this.optionSummaries = options.map((opt: DungeonOption, i: number): OptionSummary => ({
      index: i, title: opt.title, color: this.optColor(i),
      finalScore: 0, riskLevel: 0, status: '等待推演', progress: 0.05
    }))
  }

  private async startStreamSimulation() {
    if (!this.dungeonId) { this.streamStatus = '缺少会话信息'; return }
    this.streamStatus = '正在初始化推演引擎...'
    this.showContent = true

    // 限制选项数量不超过4个
    const opts: StreamRequestOption[] = this.dungeonData
      ? this.dungeonData.options.slice(0, 4).map((o: DungeonOption): StreamRequestOption => ({ title: o.title, description: o.description }))
      : []

    if (opts.length === 0) {
      this.streamStatus = '没有可推演的选项'
      return
    }

    this.streamStatus = `准备推演 ${opts.length} 个决策方向，正在建立连接...`

    // 先尝试 WebSocket，失败后自动降级到 HTTP
    let httpFallbackTriggered = false
    let wsEverReceivedMessage = false  // 是否曾经收到过消息

    const triggerHttpFallback = () => {
      if (httpFallbackTriggered) return
      httpFallbackTriggered = true
      if (this.ws) { try { this.ws.close() } catch (_) {} this.ws = null }
      this.fallbackToHttp(opts)
    }

    try {
      this.ws = new WebSocketUtil()
      this.ws.onMessage((data: string) => {
        wsEverReceivedMessage = true
        setTimeout(() => {
          try {
            const ev = JSON.parse(data) as Record<string, Object>
            const type = ev.type as string
            if (type === 'start') { this.streamStatus = '推演已启动' }
            else if (type === 'thinking_chunk') {
              this.liveThinkingText = (this.liveThinkingText + ((ev.content as string) || '')).slice(-800)
              this.streamStatus = '模型推演中...'
            }
            else if (type === 'status' || type === 'thinking') { this.streamStatus = (ev.content as string) || '' }
            else if (type === 'option_start') {
              const title = ev.title as string
              const idx = this.findOptIdx(title)
              if (idx >= 0) {
                this.activeOptionIndex = idx
                this.updateStatus(idx, '推演中...')
                this.addRootNode(idx, title)
                this.processingNodeId = `root_${idx}`
              }
            }
            else if (type === 'node') { this.handleNode(ev) }
            else if (type === 'option_complete') {
              const title = ev.title as string
              const idx = this.findOptIdx(title)
              if (idx >= 0) {
                this.updateScore(idx, ev.final_score as number, ev.risk_level as number)
                this.updateStatus(idx, '推演完成')
                this.processingNodeId = ''
              }
            }
            else if (type === 'recommendation') {
              try { this.structuredRecommendation = JSON.parse((ev.content as string) || '') as RecommendationData }
              catch (_) { this.structuredRecommendation = null }
              this.streamStatus = '推演完成'
            }
            else if (type === 'done') {
              this.streamStatus = '全部推演完成'
              if (this.ws) { this.ws.close(); this.ws = null }
            }
            else if (type === 'error') {
              this.streamStatus = `推演出错: ${(ev.content as string) || '未知错误'}`
              if (this.ws) { this.ws.close(); this.ws = null }
            }
          } catch (err) { console.error('事件解析失败') }
        }, 0)
      })
      this.ws.onError(() => {
        if (!wsEverReceivedMessage) {
          console.info('[DecisionMap] WebSocket 连接阶段失败，降级到 HTTP')
          triggerHttpFallback()
        } else {
          // 已经收到过消息，中途断开
          console.info('[DecisionMap] WebSocket 推演中途断开，尝试HTTP继续')
          // 如果已经有节点数据，说明部分推演成功了，用HTTP补完剩余
          if (this.nodes.length > 0) {
            this.streamStatus = '连接中断，正在用HTTP补完推演...'
            triggerHttpFallback()
          } else {
            this.streamStatus = '推演连接中断，正在重试...'
            triggerHttpFallback()
          }
        }
      })
      this.ws.onClose(() => {
        // WebSocket 正常关闭（非 done 触发的关闭）也尝试 HTTP 补完
        if (wsEverReceivedMessage && this.streamStatus !== '全部推演完成' && this.streamStatus !== '推演完成') {
          console.info('[DecisionMap] WebSocket 意外关闭，HTTP补完')
          if (this.nodes.length > 0) {
            this.streamStatus = '连接关闭，正在用HTTP补完...'
          }
          triggerHttpFallback()
        }
      })
      await this.ws.connect('/ws/decision-simulate')
      this.streamStatus = '连接成功，正在加载LoRA模型和用户画像...'
      this.ws.send({ session_id: this.dungeonId, options: opts } as StreamRequestPayload)
    } catch (e) {
      console.info('[DecisionMap] WebSocket 连接异常，降级到 HTTP:', (e as Error).message)
      triggerHttpFallback()
    }
  }

  // HTTP 降级方案：当 WebSocket 不可用时（如云平台不支持 WS），使用 HTTP 接口完成推演
  private async fallbackToHttp(opts: StreamRequestOption[]) {
    this.streamStatus = '正在切换到HTTP模式...'
    promptAction.showToast({ message: 'WebSocket不可用，已切换HTTP模式' })

    // 模拟进度提示
    const statusMessages = [
      '正在加载LoRA个性化模型...',
      '正在分析用户画像和决策上下文...',
      '正在为各选项生成12个月推演时间线...',
      '模型推演中，请耐心等待（约1-3分钟）...'
    ]
    let msgIdx = 0
    const progressTimer = setInterval(() => {
      if (msgIdx < statusMessages.length) {
        this.streamStatus = statusMessages[msgIdx]
        msgIdx++
      }
    }, 8000)
    this.streamStatus = statusMessages[0]
    msgIdx = 1
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/decision/enhanced/simulate/with-collection`,
        {
          method: http.RequestMethod.POST,
          header: { 'Content-Type': 'application/json' },
          extraData: JSON.stringify({
            session_id: this.dungeonId,
            options: opts,
            use_lora: true
          }),
          connectTimeout: 120000,
          readTimeout: 300000
        }
      )
      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if ((result.code as number) === 200 && result.data) {
          clearInterval(progressTimer)
          this.streamStatus = '推演完成，正在渲染时间线...'
          const data = result.data as Record<string, Object>
          // 用 HTTP 返回的完整数据构建地图
          this.dungeonData = {
            dungeon_id: (data.simulation_id as string) || this.dungeonId,
            user_id: (data.user_id as string) || this.userId,
            title: this.dungeonData?.title || '决策推演',
            description: '',
            options: (data.options as DungeonOption[]) || [],
            recommendation: (data.recommendation as string) || '',
            created_at: (data.created_at as string) || new Date().toISOString()
          }
          if (this.dungeonData.options.length > 0) {
            this.buildFromExisting()
          }
          // 解析推荐
          const rec = data.recommendation as string
          if (rec) {
            try { this.structuredRecommendation = JSON.parse(rec) as RecommendationData }
            catch (_) { this.structuredRecommendation = null }
          }
          this.streamStatus = '全部推演完成'
          return
        }
      }
      // HTTP 也失败了
      clearInterval(progressTimer)
      const errBody = response.result ? (response.result as string).substring(0, 200) : '无响应'
      this.streamStatus = `推演失败(HTTP ${response.responseCode})`
      console.error('[DecisionMap] HTTP 推演失败:', errBody)
    } catch (e) {
      clearInterval(progressTimer)
      this.streamStatus = '推演失败，请检查网络后返回重试'
      console.error('[DecisionMap] HTTP 推演异常:', (e as Error).message)
    }
  }

  private handleNode(ev: Record<string, Object>) {
    const node = ev.node as Record<string, Object>
    const optTitle = ev.option_title as string
    const oi = this.findOptIdx(optTitle)
    if (oi < 0) return
    const isBranch = ((node.branch_group as string) || '').includes('fork')
    const parentId = (node.parent_event_id as string) || `root_${oi}`
    const parentNode = this.nodes.find((n: MapNode) => n.id === parentId)
    const optNodes = this.nodes.filter((n: MapNode) => n.optionIndex === oi && !n.id.startsWith('root_'))
    const count = optNodes.length
    const month = (node.month as number) || (count + 1)

    let x: number
    let y: number
    if (isBranch && parentNode) {
      x = parentNode.position.x + 300
      y = parentNode.position.y + (((node.risk_tag as string) === 'low') ? -(200 + count * 60) : (200 + count * 60))
    } else {
      x = 360 + month * 320
      y = 400 + ((month % 2 === 0) ? -130 : 130)
    }

    const color = isBranch ? (((node.risk_tag as string) === 'low') ? '#10B981' : '#EF4444') : this.optColor(oi)
    const mapNode: MapNode = {
      id: (node.event_id as string) || `s_${oi}_${this.nodes.length}`,
      parentId,
      title: this.shortTitle((node.event as string) || ''),
      description: (node.event as string) || '',
      month, probability: (node.probability as number) || 0,
      position: { x, y }, color,
      riskTag: (node.risk_tag as string) || 'medium',
      eventType: (node.event_type as string) || 'general',
      impact: (node.impact as Record<string, number>) || {},
      isBranch, optionIndex: oi, optionTitle: optTitle
    }

    const newEdges: EdgeLine[] = [...this.edges]
    if (parentNode) {
      newEdges.push({ fromX: parentNode.position.x, fromY: parentNode.position.y,
        toX: x, toY: y, color, fromId: parentNode.id, toId: mapNode.id, isBranch })
    }

    this.nodes = this.nodes.concat([mapNode])
    this.edges = newEdges
    this.processingNodeId = mapNode.id
    this.activeOptionIndex = oi
    this.drawCanvas()
  }

  private findOptIdx(title: string): number {
    for (let i = 0; i < this.optionSummaries.length; i++) {
      if (this.optionSummaries[i].title === title) return i
    }
    return this.dungeonData ? this.dungeonData.options.findIndex((o: DungeonOption) => o.title === title) : -1
  }

  private updateStatus(idx: number, status: string) {
    this.optionSummaries = this.optionSummaries.map((s: OptionSummary): OptionSummary =>
      s.index === idx ? { index: s.index, title: s.title, color: s.color, finalScore: s.finalScore,
        riskLevel: s.riskLevel, status, progress: status.includes('中') ? 0.5 : s.progress } : s)
  }

  private updateScore(idx: number, score: number, risk: number) {
    this.optionSummaries = this.optionSummaries.map((s: OptionSummary): OptionSummary =>
      s.index === idx ? { index: s.index, title: s.title, color: s.color, finalScore: score,
        riskLevel: risk, status: s.status, progress: 1 } : s)
  }

  private optColor(i: number): string {
    const c = ['#0A59F7', '#00C853', '#FF9500', '#FF3B30', '#6B48FF']
    return c[i % c.length]
  }

  private shortTitle(raw: string): string {
    let t = (raw || '').replace(/（[^）]*）/g, '').replace(/\([^)]*\)/g, '').trim()
    return t.length > 16 ? t.slice(0, 16) + '...' : (t || '新事件')
  }

  private getSelectedNode(): MapNode | null {
    return this.nodes.find((n: MapNode) => n.id === this.selectedNodeId) || null
  }

  private addRootNode(optionIndex: number, title: string) {
    const rootId = `root_${optionIndex}`
    if (this.nodes.some((n: MapNode) => n.id === rootId)) return
    this.nodes = this.nodes.concat([{
      id: rootId, parentId: '', title, description: '推演起点',
      month: 0, probability: 1, position: { x: 120, y: 400 },
      color: this.optColor(optionIndex), riskTag: 'medium', eventType: 'origin',
      impact: {}, isBranch: false, optionIndex, optionTitle: title
    }])
    this.drawCanvas()
  }

  private drawCanvas() {
    this.canvasCtx.clearRect(0, 0, this.canvasWidth, this.canvasHeight)
    const visibleEdges = this.edges.filter((e: EdgeLine) => {
      const from = this.nodes.find((n: MapNode) => n.id === e.fromId)
      return !!from && from.optionIndex === this.activeOptionIndex
    })
    visibleEdges.forEach((e: EdgeLine) => {
      const z = this.zoomScale
      this.canvasCtx.beginPath()
      this.canvasCtx.strokeStyle = e.color
      this.canvasCtx.lineWidth = e.isBranch ? 2 : 3
      this.canvasCtx.globalAlpha = e.isBranch ? 0.5 : 0.8
      const midX = (e.fromX + e.toX) / 2
      this.canvasCtx.moveTo(e.fromX * z, e.fromY * z)
      this.canvasCtx.bezierCurveTo(midX * z, e.fromY * z, midX * z, e.toY * z, e.toX * z, e.toY * z)
      this.canvasCtx.stroke()
      this.canvasCtx.globalAlpha = 1
      // 箭头
      const angle = Math.atan2(e.toY - e.fromY, e.toX - e.fromX)
      this.canvasCtx.beginPath()
      this.canvasCtx.fillStyle = e.color
      this.canvasCtx.moveTo(e.toX * z, e.toY * z)
      this.canvasCtx.lineTo(e.toX * z - 12 * Math.cos(angle - 0.5), e.toY * z - 12 * Math.sin(angle - 0.5))
      this.canvasCtx.lineTo(e.toX * z - 12 * Math.cos(angle + 0.5), e.toY * z - 12 * Math.sin(angle + 0.5))
      this.canvasCtx.closePath()
      this.canvasCtx.fill()
    })
  }

  private getImpactText(node: MapNode): string {
    const items = Object.keys(node.impact).filter((k: string) => Math.abs(node.impact[k]) > 0.05)
      .map((k: string) => `${k}${node.impact[k] > 0 ? '+' : '-'}`)
    return items.length > 0 ? items.join(' ') : '影响平稳'
  }

  private async loadHistoryRecord(simulationId: string, question: string, recommendation: string) {
    this.streamStatus = '加载历史推演数据...'
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/decision/enhanced/record/${simulationId}`,
        { method: http.RequestMethod.GET, connectTimeout: 10000, readTimeout: 10000 }
      )
      httpRequest.destroy()
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if ((result.code as number) === 200 && result.data) {
          const data = result.data as Record<string, Object>
          const simData = data as Record<string, Object>
          simData.simulation_id = simulationId
          simData.user_id = this.userId
          const options = (simData.options as DungeonOption[]) || []
          this.dungeonData = {
            dungeon_id: simulationId, user_id: this.userId,
            title: question, description: '',
            options: options,
            recommendation: recommendation,
            created_at: (simData.created_at as string) || ''
          }
          if (options.length > 0 && options[0].timeline && options[0].timeline.length > 0) {
            this.buildFromExisting()
          } else {
            // 后端未存储推演节点数据，构建摘要视图让用户看到历史结论
            const optCount = (simData.options_count as number) || options.length || 0
            this.buildHistorySummaryView(question, recommendation, optCount)
          }
          if (recommendation) {
            try {
              this.structuredRecommendation = JSON.parse(recommendation) as RecommendationData
            } catch (_) {
              this.structuredRecommendation = null
            }
          }
          this.streamStatus = '历史推演已加载'
          return
        }
      }
    } catch (err) {
      console.error('加载历史记录失败:', err)
    }
    // 加载失败时也构建摘要视图
    this.buildHistorySummaryView(question, recommendation, 0)
    this.streamStatus = '历史推演已加载'
  }

  private buildHistorySummaryView(question: string, recommendation: string, optCount: number) {
    // 即使后端没有存储完整的推演节点，也构建一个可展示的摘要
    // 确保 optionSummaries 不为空，避免 UI 卡在"等待推演数据"
    this.dungeonData = this.dungeonData || {
      dungeon_id: this.dungeonId, user_id: this.userId,
      title: question, description: '历史推演记录',
      options: [], recommendation: recommendation, created_at: ''
    }
    // 创建一个虚拟的摘要选项，让 UI 能正常渲染
    const summaryCount = Math.max(optCount, 1)
    const summaries: OptionSummary[] = []
    for (let i = 0; i < summaryCount; i++) {
      summaries.push({
        index: i,
        title: `选项 ${i + 1}`,
        color: this.optColor(i),
        finalScore: 0,
        riskLevel: 0,
        status: '历史记录',
        progress: 1
      })
    }
    this.optionSummaries = summaries
    this.showContent = true
  }

  private async triggerModelUpdate() {
    if (!this.dungeonData || this.isUpdatingModel) return
    this.isUpdatingModel = true
    try {
      const httpRequest = http.createHttp()
      await httpRequest.request(ApiConfig.getApiUrl(`/api/lora/train/${this.dungeonData.user_id}`),
        { method: http.RequestMethod.POST, connectTimeout: 10000, readTimeout: 10000 })
      httpRequest.destroy()
      promptAction.showToast({ message: '模型更新已触发' })
    } catch (e) { promptAction.showToast({ message: '更新失败' }) }
    this.isUpdatingModel = false
  }

  // ===== UI =====
  build() {
    Column() {
      this.buildHeader()

      if (this.isLoading) {
        Column({ space: 14 }) {
          LoadingProgress().width(40).height(40).color(Theme.Color.Primary)
          Text('正在准备推演').fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
          Text(this.streamStatus).fontSize(12).fontColor(Theme.Color.TextTertiary)
        }.layoutWeight(1).width('100%').justifyContent(FlexAlign.Center)
      } else if (this.optionSummaries.length > 0) {
        // 选项标签页
        this.buildOptionTabs()
        // 推荐卡片
        if (this.structuredRecommendation) { this.buildRecommendation() }
        // 顶部迷你时间线条
        this.buildMiniTimeline()
        // 状态条 - 推演进行中时始终显示
        if (this.streamStatus) { this.buildStatusBar() }
        // 中间主节点卡片区
        this.buildNodeCards()
        // 底部详情面板
        if (this.showDetail && this.selectedNodeId) { this.buildDetailPanel() }
      } else {
        Column({ space: 10 }) {
          Text('等待推演数据...').fontSize(15).fontColor(Theme.Color.TextSecondary)
          Text(this.streamStatus).fontSize(12).fontColor(Theme.Color.Primary)
        }.layoutWeight(1).width('100%').justifyContent(FlexAlign.Center)
      }
    }
    .width('100%').height('100%')
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }

  @Builder
  buildHeader() {
    Row() {
      Text('←').fontSize(24).fontColor(Theme.Color.Primary)
        .onClick(() => router.back())
      Column({ space: 2 }) {
        Text('决策推演').fontSize(18).fontWeight(FontWeight.Medium).fontColor(Theme.Color.TextPrimary)
        if (this.dungeonData) {
          Text(this.dungeonData.title).fontSize(11).fontColor(Theme.Color.TextTertiary).maxLines(1)
        }
      }.alignItems(HorizontalAlign.Start).layoutWeight(1).margin({ left: 12 })
    }
    .width('100%').padding({ left: 16, right: 16, top: 12, bottom: 12 })
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }

  @Builder
  buildOptionTabs() {
    Scroll() {
      Row({ space: 10 }) {
        ForEach(this.optionSummaries, (item: OptionSummary) => {
          Column({ space: 4 }) {
            Text(item.title).fontSize(13).fontWeight(600)
              .fontColor(this.activeOptionIndex === item.index ? Theme.Color.TextPrimary : Theme.Color.TextTertiary)
            Row({ space: 6 }) {
              Text(item.status).fontSize(10).fontColor(item.color)
              if (item.finalScore > 0) {
                Text(`${item.finalScore.toFixed(0)}分`).fontSize(10).fontWeight(600).fontColor(item.color)
              }
            }
            // 进度条
            Row() {
              Column().width(`${item.progress * 100}%`).height(3).borderRadius(2).backgroundColor(item.color)
            }.width(100).height(3).backgroundColor(Theme.Color.BorderLight).borderRadius(2)
          }
          .padding({ left: 14, right: 14, top: 10, bottom: 10 })
          .backgroundColor(this.activeOptionIndex === item.index ? Theme.Color.BackgroundSecondary : Theme.Color.BackgroundTertiary)
          .borderRadius(Theme.Radius.m)
          .border({ width: 1, color: this.activeOptionIndex === item.index ? Theme.Color.BorderMedium : 'transparent' })
          .shadow(this.activeOptionIndex === item.index ? Theme.Shadow.Soft : { radius: 0, color: 'transparent', offsetY: 0, offsetX: 0 })
          .onClick(() => { this.activeOptionIndex = item.index; this.showDetail = false; this.selectedNodeId = '' })
        })
      }.padding({ left: 16, right: 16 })
    }
    .scrollable(ScrollDirection.Horizontal).scrollBar(BarState.Off)
    .width('100%').padding({ top: 6, bottom: 10 })
  }

  @Builder
  buildRecommendation() {
    if (this.structuredRecommendation) {
      Column({ space: 4 }) {
        Text(`建议: ${this.structuredRecommendation!.recommended_option}`)
          .fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
        Text(this.structuredRecommendation!.summary)
          .fontSize(12).fontColor(Theme.Color.TextSecondary).maxLines(2)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
      }
      .width('100%').padding({ left: 16, right: 16, top: 10, bottom: 10 })
      .backgroundColor('rgba(10, 89, 247, 0.04)')
      .border({ width: { bottom: 0.5 }, color: Theme.Color.BorderLight })
    }
  }

  @Builder
  buildStatusBar() {
    Column({ space: 4 }) {
      Row({ space: 8 }) {
        LoadingProgress().width(14).height(14).color(Theme.Color.Primary)
        Text(this.streamStatus).fontSize(11).fontColor(Theme.Color.Primary).layoutWeight(1)
      }.width('100%')
      if (this.liveThinkingText) {
        Text(this.liveThinkingText.slice(-200))
          .fontSize(10).fontColor(Theme.Color.TextTertiary)
          .maxLines(2).textOverflow({ overflow: TextOverflow.Ellipsis }).width('100%')
      }
    }
    .width('100%').padding({ left: 16, right: 16, top: 6, bottom: 6 })
    .backgroundColor('rgba(10, 89, 247, 0.03)')
  }

  @Builder
  buildMiniTimeline() {
    // 顶部迷你时间线条 - 小圆点 + 可左右滑动
    Scroll() {
      Row({ space: 2 }) {
        // 起点
        Circle({ width: 8, height: 8 }).fill(this.optColor(this.activeOptionIndex))
        ForEach(this.nodes.filter((n: MapNode) => n.optionIndex === this.activeOptionIndex), (node: MapNode) => {
          Column().width(16).height(1.5).backgroundColor(node.color).opacity(0.4)
          Circle({ width: this.selectedNodeId === node.id ? 10 : 6, height: this.selectedNodeId === node.id ? 10 : 6 })
            .fill(node.color)
            .opacity(this.selectedNodeId === node.id ? 1 : 0.5)
            .onClick(() => { this.selectedNodeId = node.id; this.showDetail = true })
        })
        // 正在生成的占位
        if (this.processingNodeId) {
          Column().width(16).height(1.5).backgroundColor(Theme.Color.Primary).opacity(0.3)
          LoadingProgress().width(8).height(8).color(Theme.Color.Primary)
        }
      }
      .padding({ left: 16, right: 16 })
      .alignItems(VerticalAlign.Center)
    }
    .scrollable(ScrollDirection.Horizontal).scrollBar(BarState.Off)
    .width('100%').height(28)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .border({ width: { bottom: 0.5 }, color: Theme.Color.BorderLight })
  }

  @Builder
  buildNodeCards() {
    // 2D可视化画布 - 可拖拽缩放
    Scroll() {
      Scroll() {
        Stack() {
          // 画布背景
          Column().width(this.canvasWidth * this.zoomScale).height(this.canvasHeight * this.zoomScale)
            .backgroundColor(Theme.Color.BackgroundSecondary)
          // Canvas绘制连线和箭头
          Canvas(this.canvasCtx)
            .width(this.canvasWidth * this.zoomScale)
            .height(this.canvasHeight * this.zoomScale)
            .backgroundColor('transparent')
            .onReady(() => { this.drawCanvas() })
          // 节点
          ForEach(this.nodes.filter((n: MapNode) => n.optionIndex === this.activeOptionIndex), (node: MapNode) => {
            Row({ space: 8 }) {
              // 月份圆
              Stack() {
                Column().width(node.id.startsWith('root_') ? 48 : 32)
                  .height(node.id.startsWith('root_') ? 48 : 32)
                  .backgroundColor(node.color)
                  .borderRadius(node.id.startsWith('root_') ? 14 : 16)
                  .border({ width: this.selectedNodeId === node.id ? 2.5 : 1,
                    color: this.selectedNodeId === node.id ? Theme.Color.TextPrimary : Theme.Color.BorderMedium })
                if (this.processingNodeId === node.id) {
                  Column().width(node.id.startsWith('root_') ? 58 : 42)
                    .height(node.id.startsWith('root_') ? 58 : 42)
                    .border({ width: 2, color: Theme.Color.Primary }).borderRadius(20).opacity(0.7)
                }
                Text(node.id.startsWith('root_') ? '起' : `${node.month}`)
                  .fontSize(11).fontWeight(700).fontColor('#FFFFFF')
              }
              // 标题
              Column({ space: 2 }) {
                Text(node.title).fontSize(11).fontWeight(600).fontColor(Theme.Color.TextPrimary)
                  .maxLines(2).textOverflow({ overflow: TextOverflow.Ellipsis }).constraintSize({ maxWidth: 140 })
                Text(node.isBranch ? '分支' : '主链').fontSize(8)
                  .fontColor(node.isBranch ? '#B45309' : '#2563EB')
                  .padding({ left: 4, right: 4, top: 1, bottom: 1 })
                  .backgroundColor(node.isBranch ? '#FEF3C7' : '#DBEAFE').borderRadius(4)
              }.alignItems(HorizontalAlign.Start)
            }
            .padding({ left: 8, right: 10, top: 6, bottom: 6 })
            .backgroundColor(this.selectedNodeId === node.id ? 'rgba(10, 89, 247, 0.08)' : Theme.Color.BackgroundSecondary)
            .borderRadius(Theme.Radius.m)
            .border({ width: 1, color: this.selectedNodeId === node.id ? 'rgba(10, 89, 247, 0.2)' : Theme.Color.BorderLight })
            .shadow(Theme.Shadow.Soft)
            .position({ x: node.position.x * this.zoomScale - 20, y: node.position.y * this.zoomScale - 20 })
            .onClick(() => { this.selectedNodeId = node.id; this.showDetail = true })
          })
        }
        .width(this.canvasWidth * this.zoomScale)
        .height(this.canvasHeight * this.zoomScale)
        .gesture(
          PinchGesture({ fingers: 2 })
            .onActionUpdate((event: GestureEvent) => {
              const newScale = Math.max(0.3, Math.min(2.5, this.zoomScale * event.scale))
              this.zoomScale = newScale
              this.drawCanvas()
            })
        )
      }
      .scrollable(ScrollDirection.Horizontal).scrollBar(BarState.Off)
    }
    .scrollable(ScrollDirection.Vertical).scrollBar(BarState.Auto)
    .layoutWeight(1)
  }

  @Builder
  buildDetailPanel() {
    Column() {
      Blank().layoutWeight(1)
        .onClick(() => { this.showDetail = false; this.selectedNodeId = '' })

      Column({ space: 12 }) {
        // 拖拽条
        Row().width(40).height(4).backgroundColor(Theme.Color.BorderMedium).borderRadius(2)

        if (this.getSelectedNode()) {
          // 标题行
          Row() {
            Circle({ width: 12, height: 12 }).fill(this.getSelectedNode()!.color).margin({ right: 10 })
            Text(this.getSelectedNode()!.title)
              .fontSize(17).fontWeight(700).fontColor(Theme.Color.TextPrimary).layoutWeight(1)
            Text('关闭').fontSize(12).fontColor(Theme.Color.TextTertiary)
              .onClick(() => { this.showDetail = false; this.selectedNodeId = '' })
          }.width('100%')

          // 描述
          Text(this.getSelectedNode()!.description)
            .fontSize(14).fontColor(Theme.Color.TextSecondary).lineHeight(22)

          // 指标
          Row({ space: 16 }) {
            Column({ space: 2 }) {
              Text('概率').fontSize(11).fontColor(Theme.Color.TextTertiary)
              Text(`${(this.getSelectedNode()!.probability * 100).toFixed(0)}%`)
                .fontSize(16).fontWeight(600).fontColor(Theme.Color.Primary)
            }.alignItems(HorizontalAlign.Center)
            Column({ space: 2 }) {
              Text('月份').fontSize(11).fontColor(Theme.Color.TextTertiary)
              Text(`第${this.getSelectedNode()!.month}月`)
                .fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
            }.alignItems(HorizontalAlign.Center)
            Column({ space: 2 }) {
              Text('影响').fontSize(11).fontColor(Theme.Color.TextTertiary)
              Text(this.getImpactText(this.getSelectedNode()!))
                .fontSize(13).fontColor(Theme.Color.Warning)
            }.alignItems(HorizontalAlign.Center)
          }
          .width('100%').justifyContent(FlexAlign.SpaceAround)
          .padding(14).backgroundColor(Theme.Color.BackgroundTertiary)
          .borderRadius(Theme.Radius.m)

          // 类型标签
          Row({ space: 8 }) {
            Text(this.getSelectedNode()!.isBranch ? '分支事件' : '主链事件')
              .fontSize(11).fontColor(this.getSelectedNode()!.isBranch ? '#B45309' : '#2563EB')
              .padding({ left: 8, right: 8, top: 3, bottom: 3 })
              .backgroundColor(this.getSelectedNode()!.isBranch ? '#FEF3C7' : '#DBEAFE')
              .borderRadius(Theme.Radius.round)
            Text(this.getSelectedNode()!.riskTag === 'high' ? '高风险' : this.getSelectedNode()!.riskTag === 'low' ? '低风险' : '中等风险')
              .fontSize(11).fontColor(this.getSelectedNode()!.riskTag === 'high' ? Theme.Color.Destructive : Theme.Color.Accent)
              .padding({ left: 8, right: 8, top: 3, bottom: 3 })
              .backgroundColor(this.getSelectedNode()!.riskTag === 'high' ? 'rgba(255,59,48,0.08)' : 'rgba(0,200,83,0.08)')
              .borderRadius(Theme.Radius.round)
          }
        }
      }
      .width('100%')
      .padding(20)
      .backgroundColor(Theme.Color.BackgroundSecondary)
      .borderRadius({ topLeft: Theme.Radius.xl, topRight: Theme.Radius.xl })
      .border({ width: { top: 0.5 }, color: Theme.Color.BorderLight })
      .shadow(Theme.Shadow.Floating)
    }
    .width('100%').height('100%')
  }
}
