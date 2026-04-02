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
import { SimpleIcon } from '../components/IconRenderer'

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
  // LoRA 自我预测字段
  executionConfidence: number   // 执行意志强度 0-1
  dropoutRiskMonth: number      // 预测最可能动摇的月份（0=无风险）
  personalNote: string          // 第一人称自我评估
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

interface ImpactItem {
  key: string
  value: number
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
  @State pulseOpacity: number = 1
  private zoomScaleBase: number = 1
  private pulseTimer: number = -1

  private dungeonId: string = ''
  private userId: string = ''
  private ws: WebSocketUtil | null = null
  private canvasWidth: number = 3000
  private canvasHeight: number = 740
  private canvasCtx: CanvasRenderingContext2D = new CanvasRenderingContext2D(new RenderingContextSettings(true))
  @State tokenCount: number = 0
  @State tokensPerSec: number = 0
  @State parsedEventCount: number = 0
  private tokenTimestamps: number[] = []

  aboutToAppear() {
    AppStorage.setOrCreate('activeSimulation', '')
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
      if (params.isHistory === 'true') {
        this.loadHistoryRecord(params.dungeonId, params.question || '', params.recommendation || '')
      }
    }
    setTimeout(() => { this.showContent = true }, 50)
  }

  aboutToDisappear() {
    if (this.ws) { this.ws.close(); this.ws = null }
    if (this.pulseTimer !== -1) { clearInterval(this.pulseTimer); this.pulseTimer = -1 }
  }

  // ===== 数据方法 =====
  private buildFromExisting() {
    if (!this.dungeonData) return
    const allNodes: MapNode[] = []
    const allEdges: EdgeLine[] = []
    const summaries: OptionSummary[] = []
    this.dungeonData.options.forEach((opt: DungeonOption, oi: number) => {
      summaries.push({ index: oi, title: opt.title, color: this.optColor(oi),
        finalScore: opt.final_score || 0, riskLevel: opt.risk_level || 0, status: '推演完成', progress: 1,
        executionConfidence: 0, dropoutRiskMonth: 0, personalNote: '' })
      const rootId = `root_${oi}`
      allNodes.push({ id: rootId, parentId: '', title: opt.title, description: '起点',
        month: 0, probability: 1, position: { x: this.MAIN_START_X, y: this.MAIN_Y },
        color: this.optColor(oi), riskTag: 'medium', eventType: 'origin',
        impact: {}, isBranch: false, optionIndex: oi, optionTitle: opt.title })
      let prevId = rootId
      let mainSeq = 0
      opt.timeline.forEach((ev: TimelineEvent, ei: number) => {
        const nodeId = ev.event_id || `opt${oi}_${ei}`
        const isBranch = !!(ev.branch_group && ev.branch_group.includes('fork'))
        const riskTag = ev.risk_tag || 'medium'
        let x: number
        let y: number
        if (isBranch) {
          const parentInAll = allNodes.find((n: MapNode) => n.id === (ev.parent_event_id || prevId))
          const parentX = parentInAll ? parentInAll.position.x : (this.MAIN_START_X + mainSeq * this.MAIN_SPACING)
          x = parentX + this.BRANCH_X_OFFSET
          y = riskTag === 'low' ? this.BRANCH_Y_UP : (riskTag === 'high' ? this.BRANCH_Y_DOWN : this.BRANCH_Y_UP - 40)
        } else {
          x = this.MAIN_START_X + (mainSeq + 1) * this.MAIN_SPACING
          y = this.MAIN_Y
          mainSeq++
        }
        const color = isBranch ? (riskTag === 'low' ? '#10B981' : '#EF4444') : this.optColor(oi)
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
      finalScore: 0, riskLevel: 0, status: '等待推演', progress: 0.05,
      executionConfidence: 0, dropoutRiskMonth: 0, personalNote: ''
    }))
  }

  private async startStreamSimulation() {
    if (!this.dungeonId) { this.streamStatus = '缺少会话信息'; return }
    this.streamStatus = '正在初始化推演引擎...'
    this.showContent = true

    const opts: StreamRequestOption[] = this.dungeonData
      ? this.dungeonData.options.slice(0, 4).map((o: DungeonOption): StreamRequestOption => ({ title: o.title, description: o.description }))
      : []

    if (opts.length === 0) { this.streamStatus = '没有可推演的选项'; return }

    this.streamStatus = `准备推演 ${opts.length} 个决策方向，正在建立连接...`
    AppStorage.setOrCreate('activeSimulation', this.dungeonId)
    AppStorage.setOrCreate('activeSimulationQuestion', this.dungeonData?.title || '决策推演')

    try {
      this.ws = new WebSocketUtil()
      this.ws.onMessage((data: string) => {
        setTimeout(() => {
          try {
            const ev = JSON.parse(data) as Record<string, Object>
            const type = ev.type as string
            if (type === 'start') { this.streamStatus = '推演已启动' }
            else if (type === 'thinking_chunk') {
              this.liveThinkingText = (this.liveThinkingText + ((ev.content as string) || '')).slice(-800)
              const chunkLen = ((ev.content as string) || '').length
              this.tokenCount += chunkLen
              this.tokenTimestamps.push(Date.now())
              const now = Date.now()
              this.tokenTimestamps = this.tokenTimestamps.filter(t => now - t < 3000)
              this.tokensPerSec = Math.round(this.tokenTimestamps.length / 3)
              this.streamStatus = `模型推演中 · ${this.tokenCount} tokens · ${this.tokensPerSec} tok/s`
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
                const sp = ev.self_prediction as Record<string, Object> | null
                const execConf = sp ? (sp.execution_confidence as number) || 0 : 0
                const dropMonth = sp ? (sp.dropout_risk_month as number) || 0 : 0
                const note = sp ? (sp.personal_note as string) || '' : ''
                this.updateScore(idx, ev.final_score as number, ev.risk_level as number,
                  execConf, dropMonth, note)
                this.updateStatus(idx, '推演完成')
                this.processingNodeId = ''
                this.stopPulse()
                this.drawCanvas()
              }
            }
            else if (type === 'recommendation') {
              try { this.structuredRecommendation = JSON.parse((ev.content as string) || '') as RecommendationData }
              catch (_) { this.structuredRecommendation = null }
              this.streamStatus = '推演完成'
            }
            else if (type === 'done') {
              this.streamStatus = '全部推演完成'
              AppStorage.setOrCreate('activeSimulation', '')
              this.processingNodeId = ''
              this.stopPulse()
              if (this.ws) { this.ws.close(); this.ws = null }
              this.drawCanvas()
            }
            else if (type === 'error') {
              this.streamStatus = `推演出错: ${(ev.content as string) || '未知错误'}`
              this.stopPulse()
              if (this.ws) { this.ws.close(); this.ws = null }
            }
          } catch (err) { console.error('事件解析失败') }
        }, 0)
      })
      this.ws.onError(() => { this.streamStatus = '推演连接出错，请返回重试' })
      this.ws.onClose(() => {
        if (this.streamStatus !== '全部推演完成' && this.streamStatus !== '推演完成') {
          this.streamStatus = '推演连接已断开'
        }
      })
      await this.ws.connect('/ws/decision-simulate')
      this.streamStatus = '连接成功，正在加载LoRA模型和用户画像...'
      this.ws.send({ session_id: this.dungeonId, options: opts } as StreamRequestPayload)
    } catch (e) {
      this.streamStatus = '推演连接失败，请返回重试'
    }
  }

  // ── 布局常量 ──────────────────────────────────────────────────────────────
  private readonly MAIN_Y: number = 360
  private readonly MAIN_SPACING: number = 210
  private readonly MAIN_START_X: number = 100
  private readonly BRANCH_Y_UP: number = 175
  private readonly BRANCH_Y_DOWN: number = 545
  private readonly BRANCH_X_OFFSET: number = 90

  private handleNode(ev: Record<string, Object>) {
    this.parsedEventCount++
    const node = ev.node as Record<string, Object>
    const optTitle = ev.option_title as string
    const oi = this.findOptIdx(optTitle)
    if (oi < 0) return
    const isBranch = ((node.branch_group as string) || '').includes('fork')
    const parentId = (node.parent_event_id as string) || `root_${oi}`
    const parentNode = this.nodes.find((n: MapNode) => n.id === parentId)
    const month = (node.month as number) || 1
    const riskTag = (node.risk_tag as string) || 'medium'

    let x: number
    let y: number
    if (isBranch && parentNode) {
      x = parentNode.position.x + this.BRANCH_X_OFFSET
      if (riskTag === 'low') {
        y = this.BRANCH_Y_UP
      } else if (riskTag === 'high') {
        y = this.BRANCH_Y_DOWN
      } else {
        const siblingBranches = this.nodes.filter(
          (n: MapNode) => n.parentId === parentId && n.isBranch
        )
        y = siblingBranches.length % 2 === 0 ? this.BRANCH_Y_UP - 40 : this.BRANCH_Y_DOWN + 40
      }
    } else {
      const mainNodes = this.nodes.filter(
        (n: MapNode) => n.optionIndex === oi && !n.isBranch && !n.id.startsWith('root_')
      )
      const seq = mainNodes.length
      x = this.MAIN_START_X + (seq + 1) * this.MAIN_SPACING
      y = this.MAIN_Y
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
    this.startPulse()
    this.drawCanvas()
  }

  // ── 脉冲动画 ─────────────────────────────────────────────────────────────
  private startPulse() {
    if (this.pulseTimer !== -1) return
    let increasing = false
    this.pulseOpacity = 1
    this.pulseTimer = setInterval(() => {
      if (increasing) {
        this.pulseOpacity = Math.min(1, this.pulseOpacity + 0.08)
        if (this.pulseOpacity >= 1) increasing = false
      } else {
        this.pulseOpacity = Math.max(0.25, this.pulseOpacity - 0.08)
        if (this.pulseOpacity <= 0.25) increasing = true
      }
    }, 80) as number
  }

  private stopPulse() {
    if (this.pulseTimer !== -1) {
      clearInterval(this.pulseTimer)
      this.pulseTimer = -1
    }
    this.pulseOpacity = 1
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

  private updateScore(idx: number, score: number, risk: number,
    execConf: number = 0, dropMonth: number = 0, note: string = '') {
    this.optionSummaries = this.optionSummaries.map((s: OptionSummary): OptionSummary =>
      s.index === idx ? {
        index: s.index, title: s.title, color: s.color,
        finalScore: score, riskLevel: risk, status: s.status, progress: 1,
        executionConfidence: execConf, dropoutRiskMonth: dropMonth, personalNote: note
      } : s)
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
      month: 0, probability: 1, position: { x: this.MAIN_START_X, y: this.MAIN_Y },
      color: this.optColor(optionIndex), riskTag: 'medium', eventType: 'origin',
      impact: {}, isBranch: false, optionIndex, optionTitle: title
    }])
    this.drawCanvas()
  }

  // ── Canvas 绘制 ───────────────────────────────────────────────────────────
  private drawCanvas() {
    const ctx = this.canvasCtx
    const z = this.zoomScale
    ctx.clearRect(0, 0, this.canvasWidth * z, this.canvasHeight * z)

    // 区域背景 — 机遇区（绿色）
    ctx.fillStyle = 'rgba(16, 185, 129, 0.035)'
    ctx.fillRect(0, 0, this.canvasWidth * z, (this.BRANCH_Y_UP + 90) * z)

    // 区域背景 — 风险区（红色）
    ctx.fillStyle = 'rgba(239, 68, 68, 0.035)'
    ctx.fillRect(0, (this.BRANCH_Y_DOWN - 90) * z, this.canvasWidth * z, this.canvasHeight * z)

    // 主链虚线轴
    ctx.beginPath()
    ctx.setLineDash([3, 9])
    ctx.strokeStyle = 'rgba(150, 150, 150, 0.18)'
    ctx.lineWidth = 1
    ctx.moveTo(60 * z, this.MAIN_Y * z)
    ctx.lineTo(this.canvasWidth * z, this.MAIN_Y * z)
    ctx.stroke()
    ctx.setLineDash([])

    // 区域标签
    ctx.font = `${Math.round(10 * z)}px sans-serif`
    ctx.fillStyle = 'rgba(16, 185, 129, 0.55)'
    ctx.fillText('↑ 机遇分支', 16 * z, 32 * z)
    ctx.fillStyle = 'rgba(239, 68, 68, 0.55)'
    ctx.fillText('↓ 风险分支', 16 * z, (this.canvasHeight - 14) * z)
    ctx.fillStyle = 'rgba(120, 120, 120, 0.35)'
    ctx.fillText('主推演链', 16 * z, (this.MAIN_Y - 16) * z)

    // 连线
    const visibleEdges = this.edges.filter((e: EdgeLine) => {
      const from = this.nodes.find((n: MapNode) => n.id === e.fromId)
      return !!from && from.optionIndex === this.activeOptionIndex
    })

    visibleEdges.forEach((e: EdgeLine) => {
      ctx.beginPath()
      if (e.isBranch) {
        ctx.setLineDash([6, 3])
        ctx.lineWidth = 1.5 * z
        ctx.globalAlpha = 0.5
      } else {
        ctx.setLineDash([])
        ctx.lineWidth = 3 * z
        ctx.globalAlpha = 0.82
      }
      ctx.strokeStyle = e.color
      const midX = (e.fromX + e.toX) / 2
      ctx.moveTo(e.fromX * z, e.fromY * z)
      ctx.bezierCurveTo(midX * z, e.fromY * z, midX * z, e.toY * z, e.toX * z, e.toY * z)
      ctx.stroke()
      ctx.setLineDash([])

      // 箭头
      const angle = Math.atan2(e.toY - e.fromY, e.toX - e.fromX)
      ctx.beginPath()
      ctx.fillStyle = e.color
      ctx.moveTo(e.toX * z, e.toY * z)
      ctx.lineTo(e.toX * z - 10 * Math.cos(angle - 0.45), e.toY * z - 10 * Math.sin(angle - 0.45))
      ctx.lineTo(e.toX * z - 10 * Math.cos(angle + 0.45), e.toY * z - 10 * Math.sin(angle + 0.45))
      ctx.closePath()
      ctx.fill()
      ctx.globalAlpha = 1
    })
  }

  // ── 辅助方法 ─────────────────────────────────────────────────────────────
  private getImpactText(node: MapNode): string {
    const items = Object.keys(node.impact).filter((k: string) => Math.abs(node.impact[k]) > 0.05)
      .map((k: string) => `${k}${node.impact[k] > 0 ? '+' : '-'}`)
    return items.length > 0 ? items.join(' ') : '影响平稳'
  }

  private getTopImpacts(node: MapNode): ImpactItem[] {
    const keys = Object.keys(node.impact).filter((k: string) => Math.abs(node.impact[k]) > 0.04)
    keys.sort((a: string, b: string) => Math.abs(node.impact[b]) - Math.abs(node.impact[a]))
    return keys.slice(0, 2).map((k: string): ImpactItem => ({ key: k, value: node.impact[k] }))
  }

  private getAllImpacts(node: MapNode): ImpactItem[] {
    const keys = Object.keys(node.impact).filter((k: string) => Math.abs(node.impact[k]) > 0.01)
    keys.sort((a: string, b: string) => Math.abs(node.impact[b]) - Math.abs(node.impact[a]))
    return keys.map((k: string): ImpactItem => ({ key: k, value: node.impact[k] }))
  }

  private riskColor(riskTag: string): string {
    if (riskTag === 'high') return '#EF4444'
    if (riskTag === 'low') return '#10B981'
    return '#F59E0B'
  }

  private nodeAccentColor(node: MapNode): string {
    return node.isBranch ? this.riskColor(node.riskTag) : node.color
  }

  private shortImpactKey(key: string): string {
    if (key === '财务' || key === '财务状况') return '财'
    if (key === '健康' || key === '健康状况') return '健'
    if (key === '事业' || key === '职业发展') return '事'
    if (key === '人际关系' || key === '人际') return '人'
    if (key === '心情' || key === '情绪') return '情'
    if (key === '生活质量' || key === '生活') return '活'
    if (key === '压力' || key === '心理压力') return '压'
    if (key === '自信' || key === '自信心') return '信'
    return key.length > 1 ? key.slice(0, 1) : key
  }

  private riskLevelLabel(riskLevel: number): string {
    if (riskLevel > 0.6) return '高风险'
    if (riskLevel > 0.3) return '中风险'
    return '低风险'
  }

  private riskLevelColor(riskLevel: number): string {
    if (riskLevel > 0.6) return '#EF4444'
    if (riskLevel > 0.3) return '#F59E0B'
    return '#10B981'
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
            const optCount = (simData.options_count as number) || options.length || 0
            this.buildHistorySummaryView(question, recommendation, optCount)
          }
          if (recommendation) {
            try { this.structuredRecommendation = JSON.parse(recommendation) as RecommendationData }
            catch (_) { this.structuredRecommendation = null }
          }
          this.streamStatus = '历史推演已加载'
          return
        }
      }
    } catch (err) { console.error('加载历史记录失败:', err) }
    this.buildHistorySummaryView(question, recommendation, 0)
    this.streamStatus = '历史推演已加载'
  }

  private buildHistorySummaryView(question: string, recommendation: string, optCount: number) {
    this.dungeonData = this.dungeonData || {
      dungeon_id: this.dungeonId, user_id: this.userId,
      title: question, description: '历史推演记录',
      options: [], recommendation: recommendation, created_at: ''
    }
    const summaryCount = Math.max(optCount, 1)
    const summaries: OptionSummary[] = []
    for (let i = 0; i < summaryCount; i++) {
      summaries.push({ index: i, title: `选项 ${i + 1}`, color: this.optColor(i),
        finalScore: 0, riskLevel: 0, status: '历史记录', progress: 1,
        executionConfidence: 0, dropoutRiskMonth: 0, personalNote: '' })
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
        this.buildOptionTabs()
        if (this.structuredRecommendation) { this.buildRecommendation() }
        this.buildMiniTimeline()
        if (this.streamStatus) { this.buildStatusBar() }
        this.buildNodeCards()
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
          Column({ space: 5 }) {
            // 选项标题
            Text(item.title)
              .fontSize(12).fontWeight(600)
              .fontColor(this.activeOptionIndex === item.index ? Theme.Color.TextPrimary : Theme.Color.TextTertiary)
              .maxLines(1).textOverflow({ overflow: TextOverflow.Ellipsis })
              .constraintSize({ maxWidth: 110 })

            // 状态 + 风险等级
            Row({ space: 5 }) {
              Text(item.status).fontSize(9).fontColor(item.color)
              if (item.riskLevel > 0) {
                Row({ space: 2 }) {
                  Column().width(5).height(5)
                    .backgroundColor(this.riskLevelColor(item.riskLevel))
                    .borderRadius(3)
                  Text(this.riskLevelLabel(item.riskLevel))
                    .fontSize(9).fontColor(this.riskLevelColor(item.riskLevel))
                }
              }
            }

            // 分数（大）
            if (item.finalScore > 0) {
              Row({ space: 1 }) {
                Text(`${item.finalScore.toFixed(0)}`).fontSize(22).fontWeight(800).fontColor(item.color)
                Text('分').fontSize(10).fontColor(item.color).margin({ top: 8 })
              }.alignItems(VerticalAlign.Bottom)
            }

            // 执行意志条（LoRA 预测）
            if (item.executionConfidence > 0) {
              Column({ space: 2 }) {
                Row({ space: 4 }) {
                  Text('执行意志').fontSize(9).fontColor(Theme.Color.TextTertiary)
                  Text(`${(item.executionConfidence * 100).toFixed(0)}%`).fontSize(9).fontWeight(600)
                    .fontColor(item.executionConfidence > 0.7 ? '#10B981' : item.executionConfidence > 0.45 ? '#F59E0B' : '#EF4444')
                  if (item.dropoutRiskMonth > 0) {
                    Text(`⚠ 第${item.dropoutRiskMonth}月`).fontSize(8)
                      .fontColor('#F59E0B')
                      .padding({ left: 3, right: 3, top: 1, bottom: 1 })
                      .backgroundColor('rgba(245,158,11,0.1)')
                      .borderRadius(3)
                  }
                }.width(110)
                Row() {
                  Column()
                    .width(`${item.executionConfidence * 100}%`)
                    .height(3).borderRadius(2)
                    .backgroundColor(item.executionConfidence > 0.7 ? '#10B981' : item.executionConfidence > 0.45 ? '#F59E0B' : '#EF4444')
                }.width(110).height(3).backgroundColor(Theme.Color.BorderLight).borderRadius(2)
              }.alignItems(HorizontalAlign.Start)
            }

            // 推演进度条
            Row() {
              Column().width(`${item.progress * 100}%`).height(3).borderRadius(2).backgroundColor(item.color)
            }.width(110).height(3).backgroundColor(Theme.Color.BorderLight).borderRadius(2)
          }
          .padding({ left: 12, right: 12, top: 10, bottom: 10 })
          .alignItems(HorizontalAlign.Start)
          .backgroundColor(this.activeOptionIndex === item.index ? Theme.Color.BackgroundSecondary : Theme.Color.BackgroundTertiary)
          .borderRadius(Theme.Radius.m)
          .border({
            width: 1,
            color: this.activeOptionIndex === item.index ? item.color : 'transparent'
          })
          .shadow(this.activeOptionIndex === item.index ? Theme.Shadow.Soft : { radius: 0, color: 'transparent', offsetY: 0, offsetX: 0 })
          .onClick(() => {
            this.activeOptionIndex = item.index
            this.showDetail = false
            this.selectedNodeId = ''
            this.drawCanvas()
          })
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
    Column({ space: 6 }) {
      Row({ space: 8 }) {
        LoadingProgress().width(14).height(14).color(Theme.Color.Primary)
        Text(this.streamStatus).fontSize(11).fontColor(Theme.Color.Primary).layoutWeight(1)
      }.width('100%')

      if (this.tokenCount > 0 || this.processingNodeId) {
        Column({ space: 8 }) {
          Row({ space: 16 }) {
            Column({ space: 2 }) {
              Text(`${this.tokenCount}`).fontSize(16).fontWeight(700).fontColor(Theme.Color.Primary)
              Text('tokens').fontSize(9).fontColor(Theme.Color.TextTertiary)
            }.alignItems(HorizontalAlign.Center)
            Column({ space: 2 }) {
              Text(`${this.tokensPerSec}`).fontSize(16).fontWeight(700).fontColor(Theme.Color.Secondary)
              Text('tok/s').fontSize(9).fontColor(Theme.Color.TextTertiary)
            }.alignItems(HorizontalAlign.Center)
            Column({ space: 2 }) {
              Text(`${this.parsedEventCount}`).fontSize(16).fontWeight(700).fontColor(Theme.Color.Accent)
              Text('事件').fontSize(9).fontColor(Theme.Color.TextTertiary)
            }.alignItems(HorizontalAlign.Center)
            Column({ space: 2 }) {
              Text(`${this.nodes.filter(n => n.optionIndex === this.activeOptionIndex && !n.id.startsWith('root_')).length}`)
                .fontSize(16).fontWeight(700).fontColor(Theme.Color.Warning)
              Text('节点').fontSize(9).fontColor(Theme.Color.TextTertiary)
            }.alignItems(HorizontalAlign.Center)
          }.width('100%').justifyContent(FlexAlign.SpaceAround)

          Row() {
            Column()
              .height(3)
              .width(`${Math.min(100, this.tokensPerSec * 5)}%`)
              .backgroundColor(Theme.Color.Primary)
              .borderRadius(2)
          }.width('100%').height(3).backgroundColor(Theme.Color.BorderLight).borderRadius(2)

          if (this.liveThinkingText) {
            Text(this.liveThinkingText.slice(-150))
              .fontSize(9).fontColor(Theme.Color.TextTertiary)
              .fontFamily('monospace')
              .maxLines(2).textOverflow({ overflow: TextOverflow.Ellipsis })
              .width('100%').padding(6)
              .backgroundColor(Theme.Color.BackgroundTertiary).borderRadius(4)
          }
        }
        .width('100%').padding(10)
        .backgroundColor(Theme.Color.BackgroundSecondary)
        .borderRadius(Theme.Radius.m)
        .border({ width: 0.5, color: Theme.Color.BorderLight })
      }
    }
    .width('100%').padding({ left: 16, right: 16, top: 6, bottom: 6 })
    .backgroundColor('rgba(10, 89, 247, 0.03)')
  }

  @Builder
  buildMiniTimeline() {
    Scroll() {
      Row({ space: 2 }) {
        Circle({ width: 8, height: 8 }).fill(this.optColor(this.activeOptionIndex))
        ForEach(this.nodes.filter((n: MapNode) => n.optionIndex === this.activeOptionIndex), (node: MapNode) => {
          Column().width(16).height(1.5).backgroundColor(node.color).opacity(0.4)
          Circle({
            width: this.selectedNodeId === node.id ? 10 : (node.isBranch ? 5 : 6),
            height: this.selectedNodeId === node.id ? 10 : (node.isBranch ? 5 : 6)
          })
            .fill(node.isBranch ? this.riskColor(node.riskTag) : node.color)
            .opacity(this.selectedNodeId === node.id ? 1 : 0.55)
            .onClick(() => { this.selectedNodeId = node.id; this.showDetail = true })
        })
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
    if (this.nodes.length === 0) {
      Column({ space: 16 }) {
        SimpleIcon({ iconName: 'comparison', iconSize: 40, color: Theme.Color.TextTertiary })
        Text('历史推演节点数据未保存').fontSize(15).fontColor(Theme.Color.TextSecondary)
        if (this.dungeonData?.recommendation) {
          Column({ space: 8 }) {
            Text('AI 推荐结论').fontSize(14).fontWeight(600).fontColor(Theme.Color.Primary)
            Text(this.dungeonData.recommendation)
              .fontSize(14).fontColor(Theme.Color.TextSecondary).lineHeight(22)
          }
          .width('100%').padding(16)
          .backgroundColor('rgba(10,89,247,0.04)')
          .borderRadius(Theme.Radius.l)
        }
        Text('新的推演会保存完整节点数据').fontSize(12).fontColor(Theme.Color.TextTertiary)
      }
      .width('100%').layoutWeight(1).padding(32)
      .justifyContent(FlexAlign.Center).alignItems(HorizontalAlign.Center)
    } else {
      Scroll() {
        Scroll() {
          Stack() {
            // 画布背景
            Column()
              .width(this.canvasWidth * this.zoomScale)
              .height(this.canvasHeight * this.zoomScale)
              .backgroundColor(Theme.Color.BackgroundSecondary)

            // Canvas — 连线 + 区域背景
            Canvas(this.canvasCtx)
              .width(this.canvasWidth * this.zoomScale)
              .height(this.canvasHeight * this.zoomScale)
              .backgroundColor('transparent')
              .onReady(() => { this.drawCanvas() })

            // 月份轴标签（主链节点正下方）
            ForEach(
              this.nodes.filter((n: MapNode) => n.optionIndex === this.activeOptionIndex && !n.isBranch && !n.id.startsWith('root_')),
              (node: MapNode) => {
                Text(`第${node.month}月`)
                  .fontSize(Math.round(9 * this.zoomScale))
                  .fontColor('rgba(120,120,120,0.5)')
                  .position({
                    x: node.position.x * this.zoomScale - 16,
                    y: (this.MAIN_Y + 52) * this.zoomScale
                  })
              },
              (node: MapNode) => `axis_${node.id}`
            )

            // 节点卡片
            ForEach(
              this.nodes.filter((n: MapNode) => n.optionIndex === this.activeOptionIndex),
              (node: MapNode) => {
                Column() {
                  // 内容行
                  Row({ space: 6 }) {
                    // 月份/类型徽章
                    Column({ space: 1 }) {
                      Text(node.id.startsWith('root_') ? '起' : `${node.month}`)
                        .fontSize(node.id.startsWith('root_') ? 14 : 12)
                        .fontWeight(700)
                        .fontColor(node.id.startsWith('root_') ? '#FFFFFF' : this.nodeAccentColor(node))
                      if (!node.id.startsWith('root_') && node.isBranch) {
                        Text(node.riskTag === 'low' ? '↑' : '↓')
                          .fontSize(9).fontColor(this.nodeAccentColor(node))
                      }
                    }
                    .width(node.id.startsWith('root_') ? 44 : 34)
                    .height(node.id.startsWith('root_') ? 44 : 34)
                    .backgroundColor(node.id.startsWith('root_')
                      ? node.color
                      : `${this.nodeAccentColor(node)}1A`)
                    .borderRadius(node.id.startsWith('root_') ? 12 : 8)
                    .justifyContent(FlexAlign.Center)
                    .border({
                      width: node.id.startsWith('root_') ? 0 : 1,
                      color: `${this.nodeAccentColor(node)}40`
                    })

                    // 标题 + 影响 pills
                    Column({ space: 4 }) {
                      Text(node.title)
                        .fontSize(11).fontWeight(600)
                        .fontColor(node.id.startsWith('root_') ? '#FFFFFF' : Theme.Color.TextPrimary)
                        .maxLines(2).textOverflow({ overflow: TextOverflow.Ellipsis })
                        .constraintSize({ maxWidth: 130 })

                      // 影响 pills（top 2）
                      if (this.getTopImpacts(node).length > 0) {
                        Row({ space: 3 }) {
                          ForEach(this.getTopImpacts(node), (item: ImpactItem) => {
                            Text(`${this.shortImpactKey(item.key)}${item.value > 0 ? '+' : ''}${(item.value * 100).toFixed(0)}%`)
                              .fontSize(8)
                              .fontColor(item.value > 0 ? '#059669' : '#DC2626')
                              .padding({ left: 4, right: 4, top: 1, bottom: 1 })
                              .backgroundColor(item.value > 0 ? '#D1FAE5' : '#FEE2E2')
                              .borderRadius(3)
                          }, (item: ImpactItem) => item.key)
                        }
                      }
                    }
                    .alignItems(HorizontalAlign.Start)
                    .layoutWeight(1)
                  }
                  .padding({ left: 8, right: 10, top: 8, bottom: 8 })
                  .alignItems(VerticalAlign.Center)
                }
                .backgroundColor(
                  node.id.startsWith('root_') ? node.color
                    : (this.selectedNodeId === node.id ? 'rgba(10, 89, 247, 0.05)' : '#FFFFFF')
                )
                .borderRadius(12)
                .shadow(this.selectedNodeId === node.id ? Theme.Shadow.Floating : Theme.Shadow.Soft)
                .opacity(this.processingNodeId === node.id ? this.pulseOpacity : 1)
                // 放弃风险月标记：橙色外圈
                .border(
                  this.optionSummaries.some((s: OptionSummary) =>
                    s.index === node.optionIndex && s.dropoutRiskMonth > 0 &&
                    s.dropoutRiskMonth === node.month && !node.isBranch
                  ) ? { width: 2, color: '#F59E0B' }
                    : (node.id.startsWith('root_') ? { width: 0, color: 'transparent' }
                      : {
                          width: { left: 3, top: 0.5, right: 0.5, bottom: 0.5 },
                          color: {
                            left: this.nodeAccentColor(node),
                            top: this.selectedNodeId === node.id ? 'rgba(10,89,247,0.2)' : Theme.Color.BorderLight,
                            right: this.selectedNodeId === node.id ? 'rgba(10,89,247,0.2)' : Theme.Color.BorderLight,
                            bottom: this.selectedNodeId === node.id ? 'rgba(10,89,247,0.2)' : Theme.Color.BorderLight
                          }
                        })
                )
                .position({
                  x: node.position.x * this.zoomScale - 22,
                  y: node.position.y * this.zoomScale - 28
                })
                .scale({ x: this.zoomScale, y: this.zoomScale, centerX: 0, centerY: 0 })
                .onClick(() => { this.selectedNodeId = node.id; this.showDetail = true })
              },
              (node: MapNode) => node.id
            )
          }
          .width(this.canvasWidth * this.zoomScale)
          .height(this.canvasHeight * this.zoomScale)
          .gesture(
            PinchGesture({ fingers: 2 })
              .onActionStart(() => { this.zoomScaleBase = this.zoomScale })
              .onActionUpdate((event: GestureEvent) => {
                const newScale = Math.max(0.5, Math.min(1.8, this.zoomScaleBase * event.scale))
                animateTo({ duration: 50, curve: Curve.Linear }, () => { this.zoomScale = newScale })
                this.drawCanvas()
              })
          )
        }
        .scrollable(ScrollDirection.Horizontal).scrollBar(BarState.Off)
      }
      .scrollable(ScrollDirection.Vertical).scrollBar(BarState.Auto)
      .layoutWeight(1)
    }
  }

  @Builder
  buildDetailPanel() {
    Column({ space: 12 }) {
      // 拖拽条
      Row() {
        Row().width(40).height(4).backgroundColor(Theme.Color.BorderMedium).borderRadius(2)
      }.width('100%').justifyContent(FlexAlign.Center).padding({ top: 8 })

      if (this.getSelectedNode()) {
        Scroll() {
          Column({ space: 14 }) {
            // 标题行
            Row() {
              // 风险色点
              Column().width(12).height(12)
                .backgroundColor(this.nodeAccentColor(this.getSelectedNode()!))
                .borderRadius(6)
                .margin({ right: 10 })
              Text(this.getSelectedNode()!.title)
                .fontSize(17).fontWeight(700).fontColor(Theme.Color.TextPrimary).layoutWeight(1)
              Text('关闭').fontSize(12).fontColor(Theme.Color.TextTertiary)
                .onClick(() => { this.showDetail = false; this.selectedNodeId = '' })
            }.width('100%')

            // 描述
            Text(this.getSelectedNode()!.description)
              .fontSize(14).fontColor(Theme.Color.TextSecondary).lineHeight(22)

            // 核心指标行
            Row({ space: 0 }) {
              Column({ space: 3 }) {
                Text('发生概率').fontSize(10).fontColor(Theme.Color.TextTertiary)
                Text(`${(this.getSelectedNode()!.probability * 100).toFixed(0)}%`)
                  .fontSize(20).fontWeight(700).fontColor(Theme.Color.Primary)
              }
              .alignItems(HorizontalAlign.Center).layoutWeight(1)

              // 分隔线
              Column().width(0.5).height(36).backgroundColor(Theme.Color.BorderLight)

              Column({ space: 3 }) {
                Text('时间节点').fontSize(10).fontColor(Theme.Color.TextTertiary)
                Text(this.getSelectedNode()!.month === 0 ? '起点' : `第${this.getSelectedNode()!.month}月`)
                  .fontSize(20).fontWeight(700).fontColor(Theme.Color.TextPrimary)
              }
              .alignItems(HorizontalAlign.Center).layoutWeight(1)

              Column().width(0.5).height(36).backgroundColor(Theme.Color.BorderLight)

              Column({ space: 3 }) {
                Text('风险等级').fontSize(10).fontColor(Theme.Color.TextTertiary)
                Text(this.getSelectedNode()!.riskTag === 'high' ? '高' : this.getSelectedNode()!.riskTag === 'low' ? '低' : '中')
                  .fontSize(20).fontWeight(700)
                  .fontColor(this.riskColor(this.getSelectedNode()!.riskTag))
              }
              .alignItems(HorizontalAlign.Center).layoutWeight(1)
            }
            .width('100%')
            .padding({ top: 10, bottom: 10 })
            .backgroundColor(Theme.Color.BackgroundTertiary)
            .borderRadius(Theme.Radius.m)

            // 多维度影响条形图
            if (this.getAllImpacts(this.getSelectedNode()!).length > 0) {
              Column({ space: 8 }) {
                Text('多维度影响分析').fontSize(12).fontWeight(600).fontColor(Theme.Color.TextPrimary)

                ForEach(this.getAllImpacts(this.getSelectedNode()!), (item: ImpactItem) => {
                  Row({ space: 8 }) {
                    // 维度名
                    Text(item.key)
                      .fontSize(12).fontColor(Theme.Color.TextSecondary)
                      .width(60).textAlign(TextAlign.Start)

                    // 进度条
                    Row() {
                      Column()
                        .height(6)
                        .width(`${Math.min(100, Math.abs(item.value) * 120)}%`)
                        .backgroundColor(item.value > 0 ? '#10B981' : '#EF4444')
                        .borderRadius(3)
                    }
                    .height(6)
                    .layoutWeight(1)
                    .backgroundColor(Theme.Color.BackgroundTertiary)
                    .borderRadius(3)

                    // 数值
                    Text(`${item.value > 0 ? '+' : ''}${(item.value * 100).toFixed(0)}%`)
                      .fontSize(12).fontWeight(600)
                      .fontColor(item.value > 0 ? '#10B981' : '#EF4444')
                      .width(46).textAlign(TextAlign.End)
                  }
                  .width('100%').alignItems(VerticalAlign.Center)
                }, (item: ImpactItem) => item.key)
              }
              .width('100%').padding(12)
              .backgroundColor(Theme.Color.BackgroundTertiary)
              .borderRadius(Theme.Radius.m)
            }

            // 事件类型标签
            Row({ space: 8 }) {
              Text(this.getSelectedNode()!.isBranch ? '分支事件' : '主链事件')
                .fontSize(11)
                .fontColor(this.getSelectedNode()!.isBranch ? '#B45309' : '#2563EB')
                .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                .backgroundColor(this.getSelectedNode()!.isBranch ? '#FEF3C7' : '#DBEAFE')
                .borderRadius(Theme.Radius.round)
              Text(this.getSelectedNode()!.eventType)
                .fontSize(11).fontColor(Theme.Color.TextTertiary)
                .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                .backgroundColor(Theme.Color.BackgroundTertiary)
                .borderRadius(Theme.Radius.round)
            }
          }.padding({ left: 20, right: 20, bottom: 20 })
        }.constraintSize({ maxHeight: 300 }).scrollBar(BarState.Off)
      }
    }
    .width('100%')
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius({ topLeft: Theme.Radius.xl, topRight: Theme.Radius.xl })
    .border({ width: { top: 0.5 }, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Floating)
  }
}
