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

interface RiskDimension {
  name: string
  score: number
  level: string
  factors: string[]
  mitigation: string[]
}

interface RiskAssessment {
  option_title?: string
  overall_risk: number
  overall_level: string
  high_risk_count?: number
  top_dimensions?: string[]
  dimensions?: Record<string, RiskDimension>
  recommendations: string[]
}

interface PredictionTrace {
  prediction_confidence: number
  base_prediction_confidence?: number
  confidence_level: string
  context_coverage: number
  event_specificity: number
  facts_used: number
  main_event_count: number
  evidence_sources: string[]
  assumptions: string[]
  calibration_review_count?: number
  calibration_adjustment?: number
  calibration_bias?: string
  calibration_note?: string
  calibration_applied?: boolean
}

interface VerifiabilityReport {
  schema_version: number
  engine_mode: string
  collected_info_coverage: number
  average_prediction_confidence: number
  missing_key_inputs: string[]
  note: string
  historical_review_count?: number
  calibration_bias?: string
  confidence_adjustment?: number
  calibration_quality?: string
  calibration_note?: string
}

interface CalibrationProfile {
  review_count: number
  average_absolute_error: number
  optimistic_rate: number
  conservative_rate: number
  calibrated_rate: number
  overconfident_rate: number
  bias_tendency: string
  confidence_adjustment: number
  calibration_quality: string
  note: string
}

interface FollowUpReview {
  simulation_id: string
  user_id: string
  option_id: string
  option_title: string
  predicted_score: number
  predicted_risk_level: number
  predicted_confidence: number
  actual_score: number
  elapsed_months: number
  bias_label: string
  bias_note: string
  score_gap: number
  absolute_error: number
  confidence_alignment: string
  risk_alignment: string
  actual_summary: string
  updated_at: string
}

interface FollowUpSummary {
  review_count: number
  average_predicted_score: number
  average_actual_score: number
  average_absolute_error: number
  optimistic_count: number
  conservative_count: number
  calibrated_count: number
  user_calibration_profile?: CalibrationProfile
  reviews: FollowUpReview[]
}

interface DungeonOption {
  option_id: string
  title: string
  description: string
  timeline: TimelineEvent[]
  final_score: number
  risk_level: number
  risk_assessment?: RiskAssessment | null
  prediction_trace?: PredictionTrace | null
  execution_confidence?: number
  dropout_risk_month?: number
  personal_note?: string
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
  // 个性化自我预测字段
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
  confidence_note?: string
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
  @State verifiabilityReport: VerifiabilityReport | null = null
  @State followUpSummary: FollowUpSummary | null = null
  @State followUpActualScore: number = 60
  @State followUpElapsedMonths: number = 3
  @State followUpText: string = ''
  @State isSubmittingFollowUp: boolean = false
  private zoomScaleBase: number = 1
  private pulseTimer: number = -1

  private dungeonId: string = ''
  private simulationId: string = ''
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
    this.verifiabilityReport = null
    this.followUpSummary = null
    this.followUpText = ''
    this.simulationId = ''
    const params = router.getParams() as Record<string, string>
    if (params?.simulationData) {
      try {
        const simData = JSON.parse(params.simulationData) as Record<string, Object>
        const options = simData.options as DungeonOption[]
        const hasTimeline = options && options.length > 0 && options[0].timeline && options[0].timeline.length > 0
        if (hasTimeline) {
          this.simulationId = simData.simulation_id as string || ''
          this.userId = simData.user_id as string || params.userId || ''
          this.dungeonData = {
            dungeon_id: simData.simulation_id as string || 'temp',
            user_id: simData.user_id as string || this.userId,
            title: params.question || '决策推演',
            description: '',
            options: options,
            recommendation: simData.recommendation as string || '',
            created_at: simData.created_at as string || new Date().toISOString()
          }
          this.verifiabilityReport = simData.verifiability_report as VerifiabilityReport || null
          this.buildFromExisting()
          this.loadFollowUpSummary()
        } else {
          this.dungeonId = (simData.simulation_id as string) || (params.dungeonId || '')
          this.userId = (simData.user_id as string) || (params.userId || '')
          this.simulationId = ''
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
        this.simulationId = params.dungeonId
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
        executionConfidence: opt.execution_confidence || 0,
        dropoutRiskMonth: opt.dropout_risk_month || 0,
        personalNote: opt.personal_note || '' })
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
    if (this.dungeonData.options.length > 0) {
      this.followUpActualScore = this.dungeonData.options[this.activeOptionIndex].final_score || 60
    }
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
                const riskAssessment = (ev.risk_assessment as RiskAssessment) || null
                const predictionTrace = (ev.prediction_trace as PredictionTrace) || null
                this.updateScore(idx, ev.final_score as number, ev.risk_level as number,
                  execConf, dropMonth, note)
                this.updateOptionArtifacts(idx, ev.final_score as number, ev.risk_level as number,
                  riskAssessment, predictionTrace, execConf, dropMonth, note)
                if (this.activeOptionIndex === idx && !this.getCurrentFollowUpReview()) {
                  this.followUpActualScore = ev.final_score as number
                }
                this.updateStatus(idx, '推演完成')
                this.processingNodeId = ''
                this.stopPulse()
                this.drawCanvas()
              }
            }
            else if (type === 'recommendation') {
              this.applyRecommendationContent((ev.content as string) || '')
              this.streamStatus = '推演完成'
            }
            else if (type === 'verifiability_report') {
              this.verifiabilityReport = (ev.content as VerifiabilityReport) || null
            }
            else if (type === 'done') {
              this.simulationId = (ev.simulation_id as string) || this.simulationId
              this.loadFollowUpSummary()
              if (!this.verifiabilityReport && ev.verifiability_report) {
                this.verifiabilityReport = ev.verifiability_report as VerifiabilityReport
              }
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
      this.streamStatus = '连接成功，正在加载用户画像与推演上下文...'
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
    this.optionSummaries = this.optionSummaries.map((s: OptionSummary): OptionSummary => {
      if (s.index !== idx) {
        return s
      }

      const updated: OptionSummary = {
        index: s.index,
        title: s.title,
        color: s.color,
        finalScore: s.finalScore,
        riskLevel: s.riskLevel,
        status: status,
        progress: status.includes('中') ? 0.5 : s.progress,
        executionConfidence: s.executionConfidence,
        dropoutRiskMonth: s.dropoutRiskMonth,
        personalNote: s.personalNote
      }

      return updated
    })
  }

  private updateScore(idx: number, score: number, risk: number,
    execConf: number = 0, dropMonth: number = 0, note: string = '') {
    this.optionSummaries = this.optionSummaries.map((s: OptionSummary): OptionSummary => {
      if (s.index !== idx) {
        return s
      }

      const updated: OptionSummary = {
        index: s.index,
        title: s.title,
        color: s.color,
        finalScore: score,
        riskLevel: risk,
        status: s.status,
        progress: 1,
        executionConfidence: execConf,
        dropoutRiskMonth: dropMonth,
        personalNote: note
      }

      return updated
    })
  }

  private currentSimulationId(): string {
    return this.simulationId
  }

  private getActiveOption(): DungeonOption | null {
    if (!this.dungeonData || this.activeOptionIndex < 0 || this.activeOptionIndex >= this.dungeonData.options.length) {
      return null
    }
    return this.dungeonData.options[this.activeOptionIndex]
  }

  private getCurrentFollowUpReview(): FollowUpReview | null {
    const option = this.getActiveOption()
    if (!option || !this.followUpSummary) return null
    for (let i = 0; i < this.followUpSummary.reviews.length; i++) {
      const review = this.followUpSummary.reviews[i]
      if (review.option_id === option.option_id || review.option_title === option.title) {
        return review
      }
    }
    return null
  }

  private getActivePredictionTrace(): PredictionTrace | null {
    const option = this.getActiveOption()
    if (!option || !option.prediction_trace) {
      return null
    }
    return option.prediction_trace
  }

  private getActiveRiskAssessment(): RiskAssessment | null {
    const option = this.getActiveOption()
    if (!option || !option.risk_assessment) {
      return null
    }
    return option.risk_assessment
  }

  private hasEvidencePanels(): boolean {
    return !!(this.verifiabilityReport || this.getActivePredictionTrace() || this.getActiveRiskAssessment())
  }

  private getActiveNodes(): MapNode[] {
    return this.nodes.filter((node: MapNode) => node.optionIndex === this.activeOptionIndex && !node.id.startsWith('root_'))
  }

  private getActiveMainNodeCount(): number {
    return this.getActiveNodes().filter((node: MapNode) => !node.isBranch).length
  }

  private getActiveBranchNodeCount(): number {
    return this.getActiveNodes().filter((node: MapNode) => node.isBranch).length
  }

  private getActiveAverageProbability(): number {
    const option = this.getActiveOption()
    if (!option || option.timeline.length === 0) return 0
    let total = 0
    option.timeline.forEach((event: TimelineEvent) => {
      total += event.probability || 0
    })
    return total / option.timeline.length
  }

  private getSelectedOrFirstNode(): MapNode | null {
    const selected = this.getSelectedNode()
    if (selected) return selected
    const nodes = this.getActiveNodes()
    return nodes.length > 0 ? nodes[0] : null
  }

  private updateOptionArtifacts(
    idx: number,
    score: number,
    riskLevel: number,
    riskAssessment: RiskAssessment | null,
    predictionTrace: PredictionTrace | null,
    execConf: number,
    dropMonth: number,
    note: string
  ) {
    if (!this.dungeonData) return
    const updatedOptions: DungeonOption[] = this.dungeonData.options.map((opt: DungeonOption, index: number): DungeonOption => {
      if (index !== idx) return opt
      return {
        option_id: opt.option_id,
        title: opt.title,
        description: opt.description,
        timeline: opt.timeline,
        final_score: score,
        risk_level: riskLevel,
        risk_assessment: riskAssessment,
        prediction_trace: predictionTrace,
        execution_confidence: execConf,
        dropout_risk_month: dropMonth,
        personal_note: note
      } as DungeonOption
    })
    this.dungeonData = {
      dungeon_id: this.dungeonData.dungeon_id,
      user_id: this.dungeonData.user_id,
      title: this.dungeonData.title,
      description: this.dungeonData.description,
      options: updatedOptions,
      recommendation: this.dungeonData.recommendation,
      created_at: this.dungeonData.created_at
    }
  }

  private applyRecommendationContent(content: string) {
    if (this.dungeonData) {
      this.dungeonData = {
        dungeon_id: this.dungeonData.dungeon_id,
        user_id: this.dungeonData.user_id,
        title: this.dungeonData.title,
        description: this.dungeonData.description,
        options: this.dungeonData.options,
        recommendation: content,
        created_at: this.dungeonData.created_at
      }
    }

    if (!content) {
      this.structuredRecommendation = null
      return
    }

    try {
      this.structuredRecommendation = JSON.parse(content) as RecommendationData
    } catch (_) {
      this.structuredRecommendation = null
    }
  }

  private confidenceColor(value: number): string {
    if (value >= 0.75) return '#10B981'
    if (value >= 0.5) return '#F59E0B'
    return '#EF4444'
  }

  private biasLabelText(label: string): string {
    if (label === 'too_optimistic') return '偏乐观'
    if (label === 'too_conservative') return '偏保守'
    return '较贴近'
  }

  private calibrationBiasText(label: string): string {
    if (label === 'too_optimistic') return '系统偏乐观'
    if (label === 'too_conservative') return '系统偏保守'
    if (label === 'balanced') return '整体较平衡'
    return '样本不足'
  }

  private calibrationQualityText(level: string): string {
    if (level === 'strong') return '校准稳定'
    if (level === 'moderate') return '校准中等'
    if (level === 'weak') return '仍需校准'
    return '待积累'
  }

  private async loadFollowUpSummary() {
    const simulationId = this.currentSimulationId()
    if (!simulationId) return
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/decision/enhanced/follow-up/${simulationId}`,
        { method: http.RequestMethod.GET, connectTimeout: 10000, readTimeout: 10000 }
      )
      httpRequest.destroy()
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if ((result.code as number) === 200 && result.data) {
          this.followUpSummary = result.data as FollowUpSummary
        }
      }
    } catch (err) {
      console.error('加载回访摘要失败:', err)
    }
  }

  private async submitFollowUp() {
    const simulationId = this.currentSimulationId()
    const option = this.getActiveOption()
    if (!simulationId || !option || this.isSubmittingFollowUp) return
    if (!this.followUpText.trim()) {
      promptAction.showToast({ message: '请先写一句真实结果' })
      return
    }

    this.isSubmittingFollowUp = true
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/decision/enhanced/follow-up`,
        {
          method: http.RequestMethod.POST,
          header: { 'Content-Type': 'application/json' },
          extraData: JSON.stringify({
            user_id: this.userId,
            simulation_id: simulationId,
            option_id: option.option_id,
            option_title: option.title,
            actual_score: this.followUpActualScore,
            elapsed_months: this.followUpElapsedMonths,
            actual_summary: this.followUpText
          }),
          connectTimeout: 10000,
          readTimeout: 10000
        }
      )
      httpRequest.destroy()
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if ((result.code as number) === 200 && result.data) {
          const data = result.data as Record<string, Object>
          this.followUpSummary = data.summary as FollowUpSummary
          this.followUpText = ''
          promptAction.showToast({ message: '回访已记录' })
        }
      }
    } catch (err) {
      console.error('提交回访失败:', err)
      promptAction.showToast({ message: '回访提交失败' })
    }
    this.isSubmittingFollowUp = false
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
          this.simulationId = simulationId
          this.verifiabilityReport = simData.verifiability_report as VerifiabilityReport || null
          const options = (simData.options as DungeonOption[]) || []
          const recordRecommendation = (simData.recommendation as string) || recommendation
          this.dungeonData = {
            dungeon_id: simulationId, user_id: this.userId,
            title: question, description: '',
            options: options,
            recommendation: recordRecommendation,
            created_at: (simData.created_at as string) || ''
          }
          this.applyRecommendationContent(recordRecommendation)
          if (options.length > 0 && options[0].timeline && options[0].timeline.length > 0) {
            this.buildFromExisting()
          } else {
            const optCount = (simData.options_count as number) || options.length || 0
            this.buildHistorySummaryView(question, recordRecommendation, optCount)
          }
          this.loadFollowUpSummary()
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
      promptAction.showToast({ message: '储备模型训练已触发，不影响当前云端推演' })
    } catch (e) { promptAction.showToast({ message: '储备模型训练启动失败' }) }
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
        this.buildSimulationOverview()
        this.buildEvidencePanels()
        this.buildCalibrationPanel()
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

            // 执行意志条（个性化预测）
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
            if (this.dungeonData && this.dungeonData.options[item.index]) {
              this.followUpActualScore = this.dungeonData.options[item.index].final_score || 60
            }
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
  buildSimulationOverview() {
    if (!this.getActiveOption()) {
      return
    }

    Column({ space: 10 }) {
      Row({ space: 10 }) {
        Column({ space: 6 }) {
          Text('推演总览舱')
            .fontSize(13).fontWeight(700).fontColor(Theme.Color.TextPrimary)
          Text('把轨迹、风险、执行和验证放在同一个观察面板')
            .fontSize(10).fontColor(Theme.Color.TextTertiary)
        }.alignItems(HorizontalAlign.Start).layoutWeight(1)

        Text(this.getActiveOption()!.title)
          .fontSize(11).fontWeight(600).fontColor(this.optColor(this.activeOptionIndex))
          .padding({ left: 8, right: 8, top: 4, bottom: 4 })
          .backgroundColor(`${this.optColor(this.activeOptionIndex)}14`)
          .borderRadius(Theme.Radius.round)
      }.width('100%')

      Row({ space: 10 }) {
        this.OverviewMetricCard('主链节点', `${this.getActiveMainNodeCount()}`, 'main path', Theme.Color.Primary)
        this.OverviewMetricCard('分支事件', `${this.getActiveBranchNodeCount()}`, 'forks', Theme.Color.Secondary)
        this.OverviewMetricCard('平均发生率', `${(this.getActiveAverageProbability() * 100).toFixed(0)}%`, 'timeline', Theme.Color.Accent)
      }.width('100%')

      Row({ space: 10 }) {
        this.OverviewInfoCard('当前状态', this.streamStatus === '' ? '已生成完整推演' : this.streamStatus)
        this.OverviewInfoCard(
          '高风险月份',
          option.dropout_risk_month && option.dropout_risk_month > 0
            ? `第 ${option.dropout_risk_month} 月更易摇摆`
            : '暂无明显掉线月'
        )
      }.width('100%')

      if (this.getSelectedOrFirstNode()) {
        Column({ space: 6 }) {
          Row() {
            Text('当前焦点事件').fontSize(11).fontWeight(600).fontColor(Theme.Color.TextPrimary)
            Blank()
            Text(`第 ${focusNode.month} 月`)
              .fontSize(10).fontColor(Theme.Color.TextTertiary)
          }.width('100%')
          Text(focusNode.description)
            .fontSize(11).lineHeight(18).fontColor(Theme.Color.TextSecondary)
          Row({ space: 6 }) {
            Text(`${(focusNode.probability * 100).toFixed(0)}% 概率`)
              .fontSize(10).fontColor(this.confidenceColor(focusNode.probability))
              .padding({ left: 6, right: 6, top: 3, bottom: 3 })
              .backgroundColor(Theme.Color.BackgroundTertiary)
              .borderRadius(Theme.Radius.round)
            Text(focusNode.isBranch ? '分支节点' : '主链节点')
              .fontSize(10).fontColor(focusNode.isBranch ? Theme.Color.Warning : Theme.Color.Primary)
              .padding({ left: 6, right: 6, top: 3, bottom: 3 })
              .backgroundColor(focusNode.isBranch ? 'rgba(245,158,11,0.10)' : 'rgba(10,89,247,0.08)')
              .borderRadius(Theme.Radius.round)
          }.width('100%')
        }
        .width('100%').padding(12)
        .backgroundColor(Theme.Color.BackgroundTertiary)
        .borderRadius(Theme.Radius.l)
        .alignItems(HorizontalAlign.Start)
      }
    }
    .width('100%').padding(12)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .alignItems(HorizontalAlign.Start)
    .margin({ left: 16, right: 16, top: 8, bottom: 6 })
  }

  @Builder
  OverviewMetricCard(label: string, value: string, helper: string, color: string) {
    Column({ space: 4 }) {
      Text(label).fontSize(10).fontColor(Theme.Color.TextTertiary)
      Text(value).fontSize(18).fontWeight(700).fontColor(color)
      Text(helper).fontSize(9).fontColor(Theme.Color.TextTertiary)
    }
    .layoutWeight(1)
    .padding(10)
    .backgroundColor(Theme.Color.BackgroundTertiary)
    .borderRadius(Theme.Radius.m)
    .alignItems(HorizontalAlign.Center)
  }

  @Builder
  OverviewInfoCard(label: string, value: string) {
    Column({ space: 6 }) {
      Text(label).fontSize(10).fontColor(Theme.Color.TextTertiary)
      Text(value)
        .fontSize(11).lineHeight(18).fontColor(Theme.Color.TextSecondary)
        .maxLines(2).textOverflow({ overflow: TextOverflow.Ellipsis })
    }
    .layoutWeight(1)
    .padding(12)
    .backgroundColor(Theme.Color.BackgroundTertiary)
    .borderRadius(Theme.Radius.l)
    .alignItems(HorizontalAlign.Start)
  }

  @Builder
  buildRecommendation() {
    if (this.structuredRecommendation) {
      Column({ space: 8 }) {
        Text(`建议: ${this.structuredRecommendation!.recommended_option}`)
          .fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
        Text(this.structuredRecommendation!.summary)
          .fontSize(12).fontColor(Theme.Color.TextSecondary).maxLines(2)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
        if (this.structuredRecommendation!.confidence_note) {
          Text(this.structuredRecommendation!.confidence_note as string)
            .fontSize(11).fontColor(Theme.Color.Warning).lineHeight(18)
        }
      }
      .width('100%').padding({ left: 16, right: 16, top: 10, bottom: 10 })
      .backgroundColor('rgba(10, 89, 247, 0.04)')
      .border({ width: { bottom: 0.5 }, color: Theme.Color.BorderLight })
    }
  }

  @Builder
  buildEvidencePanels() {
    if (this.hasEvidencePanels()) {
      Column({ space: 10 }) {
        if (this.verifiabilityReport) {
          Column({ space: 10 }) {
            Row() {
              Text('可验证性报告')
                .fontSize(13).fontWeight(700).fontColor(Theme.Color.TextPrimary)
              Blank()
              Text(`${(this.verifiabilityReport!.average_prediction_confidence * 100).toFixed(0)}% 置信`)
                .fontSize(11).fontWeight(600)
                .fontColor(this.confidenceColor(this.verifiabilityReport!.average_prediction_confidence))
            }.width('100%')

            Row({ space: 10 }) {
              Column({ space: 3 }) {
                Text('信息覆盖').fontSize(10).fontColor(Theme.Color.TextTertiary)
                Text(`${(this.verifiabilityReport!.collected_info_coverage * 100).toFixed(0)}%`)
                  .fontSize(16).fontWeight(700).fontColor(Theme.Color.Primary)
              }.layoutWeight(1).alignItems(HorizontalAlign.Center)
              Column({ space: 3 }) {
                Text('平均置信').fontSize(10).fontColor(Theme.Color.TextTertiary)
                Text(`${(this.verifiabilityReport!.average_prediction_confidence * 100).toFixed(0)}%`)
                  .fontSize(16).fontWeight(700)
                  .fontColor(this.confidenceColor(this.verifiabilityReport!.average_prediction_confidence))
              }.layoutWeight(1).alignItems(HorizontalAlign.Center)
            }.width('100%')

            if (this.verifiabilityReport!.historical_review_count && this.verifiabilityReport!.historical_review_count! > 0) {
              Column({ space: 8 }) {
                Row({ space: 10 }) {
                  Column({ space: 3 }) {
                    Text('历史回访').fontSize(10).fontColor(Theme.Color.TextTertiary)
                    Text(`${this.verifiabilityReport!.historical_review_count}`)
                      .fontSize(16).fontWeight(700).fontColor(Theme.Color.Secondary)
                  }.layoutWeight(1).alignItems(HorizontalAlign.Center)
                  Column({ space: 3 }) {
                    Text('偏差倾向').fontSize(10).fontColor(Theme.Color.TextTertiary)
                    Text(this.calibrationBiasText(this.verifiabilityReport!.calibration_bias as string))
                      .fontSize(12).fontWeight(700).fontColor(Theme.Color.Warning)
                  }.layoutWeight(1).alignItems(HorizontalAlign.Center)
                  Column({ space: 3 }) {
                    Text('置信修正').fontSize(10).fontColor(Theme.Color.TextTertiary)
                    Text(`${((this.verifiabilityReport!.confidence_adjustment || 0) >= 0 ? '+' : '')}${((this.verifiabilityReport!.confidence_adjustment || 0) * 100).toFixed(0)}%`)
                      .fontSize(12).fontWeight(700)
                      .fontColor((this.verifiabilityReport!.confidence_adjustment || 0) > 0 ? '#10B981' : '#F59E0B')
                  }.layoutWeight(1).alignItems(HorizontalAlign.Center)
                }.width('100%')

                if (this.verifiabilityReport!.calibration_note) {
                  Text(this.verifiabilityReport!.calibration_note as string)
                    .fontSize(10).lineHeight(16).fontColor(Theme.Color.TextSecondary)
                    .padding(8)
                    .backgroundColor(Theme.Color.BackgroundTertiary)
                    .borderRadius(Theme.Radius.m)
                }
              }.width('100%').alignItems(HorizontalAlign.Start)
            }

            if (this.verifiabilityReport!.missing_key_inputs.length > 0) {
              Column({ space: 6 }) {
                Text('还缺的关键输入').fontSize(11).fontWeight(600).fontColor(Theme.Color.TextPrimary)
                Row({ space: 6 }) {
                  ForEach(this.verifiabilityReport!.missing_key_inputs, (item: string) => {
                    Text(item)
                      .fontSize(10).fontColor('#B45309')
                      .padding({ left: 6, right: 6, top: 3, bottom: 3 })
                      .backgroundColor('#FEF3C7').borderRadius(Theme.Radius.round)
                  }, (item: string) => item)
                }.width('100%')
              }.width('100%').alignItems(HorizontalAlign.Start)
            }
          }
          .width('100%').padding(12)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)
          .alignItems(HorizontalAlign.Start)
        }

        if (this.getActivePredictionTrace()) {
          Column({ space: 10 }) {
            Row() {
              Text('当前选项证据链')
                .fontSize(13).fontWeight(700).fontColor(Theme.Color.TextPrimary)
              Blank()
              Text(`${(this.getActivePredictionTrace()!.prediction_confidence * 100).toFixed(0)}%`)
                .fontSize(12).fontWeight(700).fontColor(this.confidenceColor(this.getActivePredictionTrace()!.prediction_confidence))
            }.width('100%')

            Row({ space: 10 }) {
              Column({ space: 2 }) {
                Text('上下文覆盖').fontSize(10).fontColor(Theme.Color.TextTertiary)
                Text(`${(this.getActivePredictionTrace()!.context_coverage * 100).toFixed(0)}%`).fontSize(15).fontWeight(700)
                  .fontColor(Theme.Color.Primary)
              }.layoutWeight(1).alignItems(HorizontalAlign.Center)
              Column({ space: 2 }) {
                Text('事件具体度').fontSize(10).fontColor(Theme.Color.TextTertiary)
                Text(`${(this.getActivePredictionTrace()!.event_specificity * 100).toFixed(0)}%`).fontSize(15).fontWeight(700)
                  .fontColor(Theme.Color.Accent)
              }.layoutWeight(1).alignItems(HorizontalAlign.Center)
              Column({ space: 2 }) {
                Text('事实条数').fontSize(10).fontColor(Theme.Color.TextTertiary)
                Text(`${this.getActivePredictionTrace()!.facts_used}`).fontSize(15).fontWeight(700)
                  .fontColor(Theme.Color.Warning)
              }.layoutWeight(1).alignItems(HorizontalAlign.Center)
            }.width('100%')

            if (this.getActivePredictionTrace()!.calibration_review_count && this.getActivePredictionTrace()!.calibration_review_count! > 0) {
              Column({ space: 6 }) {
                Text('历史校准修正').fontSize(11).fontWeight(600).fontColor(Theme.Color.TextPrimary)
                Text(
                  `基础置信 ${(this.getActivePredictionTrace()!.base_prediction_confidence! * 100).toFixed(0)}% → ` +
                  `校准后 ${(this.getActivePredictionTrace()!.prediction_confidence * 100).toFixed(0)}%`
                )
                  .fontSize(10).fontColor(Theme.Color.TextSecondary)
                Text(this.getActivePredictionTrace()!.calibration_note as string)
                  .fontSize(10).lineHeight(16).fontColor(Theme.Color.TextSecondary)
                  .padding(8)
                  .backgroundColor(Theme.Color.BackgroundTertiary)
                  .borderRadius(Theme.Radius.m)
              }.width('100%').alignItems(HorizontalAlign.Start)
            }

            if (this.getActivePredictionTrace()!.evidence_sources.length > 0) {
              Column({ space: 6 }) {
                Text('证据来源').fontSize(11).fontWeight(600).fontColor(Theme.Color.TextPrimary)
                Row({ space: 6 }) {
                  ForEach(this.getActivePredictionTrace()!.evidence_sources, (item: string) => {
                    Text(item)
                      .fontSize(10).fontColor('#2563EB')
                      .padding({ left: 6, right: 6, top: 3, bottom: 3 })
                      .backgroundColor('#DBEAFE').borderRadius(Theme.Radius.round)
                  }, (item: string) => item)
                }.width('100%')
              }.width('100%').alignItems(HorizontalAlign.Start)
            }

            if (this.getActivePredictionTrace()!.assumptions.length > 0) {
              Column({ space: 4 }) {
                Text('当前仍在假设的部分').fontSize(11).fontWeight(600).fontColor(Theme.Color.TextPrimary)
                ForEach(this.getActivePredictionTrace()!.assumptions.slice(0, 3), (item: string) => {
                  Text(`• ${item}`).fontSize(10).lineHeight(16).fontColor(Theme.Color.TextSecondary)
                }, (item: string) => item)
              }.width('100%').alignItems(HorizontalAlign.Start)
            }

            if (this.getActiveOption() && this.getActiveOption()!.personal_note) {
              Column({ space: 4 }) {
                Text('执行自评').fontSize(11).fontWeight(600).fontColor(Theme.Color.TextPrimary)
                Text(this.getActiveOption()!.personal_note as string)
                  .fontSize(10).lineHeight(16).fontColor(Theme.Color.TextSecondary)
                  .padding(8)
                  .backgroundColor(Theme.Color.BackgroundTertiary)
                  .borderRadius(Theme.Radius.m)
              }.width('100%').alignItems(HorizontalAlign.Start)
            }
          }
          .width('100%').padding(12)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)
          .alignItems(HorizontalAlign.Start)
        }

        if (this.getActiveRiskAssessment()) {
          Column({ space: 10 }) {
            Row() {
              Text('风险引擎结论')
                .fontSize(13).fontWeight(700).fontColor(Theme.Color.TextPrimary)
              Blank()
              Text(`${this.getActiveRiskAssessment()!.overall_risk.toFixed(1)}/10`)
                .fontSize(12).fontWeight(700).fontColor(this.riskLevelColor(this.getActiveRiskAssessment()!.overall_risk / 10))
            }.width('100%')

            Row({ space: 6 }) {
              Text(this.getActiveRiskAssessment()!.overall_level)
                .fontSize(10).fontWeight(600)
                .fontColor(this.riskLevelColor(this.getActiveRiskAssessment()!.overall_risk / 10))
                .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                .backgroundColor('rgba(245,158,11,0.12)')
                .borderRadius(Theme.Radius.round)
              if (this.getActiveRiskAssessment()!.top_dimensions && this.getActiveRiskAssessment()!.top_dimensions!.length > 0) {
                ForEach(this.getActiveRiskAssessment()!.top_dimensions!.slice(0, 3), (item: string) => {
                  Text(item)
                    .fontSize(10).fontColor(Theme.Color.TextSecondary)
                    .padding({ left: 6, right: 6, top: 3, bottom: 3 })
                    .backgroundColor(Theme.Color.BackgroundTertiary)
                    .borderRadius(Theme.Radius.round)
                }, (item: string) => item)
              }
            }.width('100%')

            if (this.getActiveRiskAssessment()!.recommendations && this.getActiveRiskAssessment()!.recommendations.length > 0) {
              Column({ space: 4 }) {
                Text('缓解建议').fontSize(11).fontWeight(600).fontColor(Theme.Color.TextPrimary)
                ForEach(this.getActiveRiskAssessment()!.recommendations.slice(0, 3), (item: string) => {
                  Text(`• ${item}`).fontSize(10).lineHeight(16).fontColor(Theme.Color.TextSecondary)
                }, (item: string) => item)
              }.width('100%').alignItems(HorizontalAlign.Start)
            }
          }
          .width('100%').padding(12)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)
          .alignItems(HorizontalAlign.Start)
        }
      }
      .width('100%').padding({ left: 16, right: 16, top: 8, bottom: 6 })
    }
  }

  @Builder
  buildCalibrationPanel() {
    if (this.getActiveOption()) {
      Column({ space: 10 }) {
        Row() {
          Text('预测回访校准')
            .fontSize(13).fontWeight(700).fontColor(Theme.Color.TextPrimary)
          Blank()
          if (this.followUpSummary && this.followUpSummary.review_count > 0) {
            Text(`${this.followUpSummary.review_count} 条回访`)
              .fontSize(11).fontColor(Theme.Color.TextTertiary)
          }
        }.width('100%')

        if (this.followUpSummary && this.followUpSummary.review_count > 0) {
          Row({ space: 10 }) {
            Column({ space: 2 }) {
              Text('预测均分').fontSize(10).fontColor(Theme.Color.TextTertiary)
              Text(`${this.followUpSummary.average_predicted_score.toFixed(0)}`)
                .fontSize(15).fontWeight(700).fontColor(Theme.Color.Primary)
            }.layoutWeight(1).alignItems(HorizontalAlign.Center)
            Column({ space: 2 }) {
              Text('实际均分').fontSize(10).fontColor(Theme.Color.TextTertiary)
              Text(`${this.followUpSummary.average_actual_score.toFixed(0)}`)
                .fontSize(15).fontWeight(700).fontColor(Theme.Color.Accent)
            }.layoutWeight(1).alignItems(HorizontalAlign.Center)
            Column({ space: 2 }) {
              Text('平均误差').fontSize(10).fontColor(Theme.Color.TextTertiary)
              Text(`${this.followUpSummary.average_absolute_error.toFixed(0)}`)
                .fontSize(15).fontWeight(700).fontColor(Theme.Color.Warning)
            }.layoutWeight(1).alignItems(HorizontalAlign.Center)
          }.width('100%')

          Row({ space: 6 }) {
            Text(`偏乐观 ${this.followUpSummary.optimistic_count}`)
              .fontSize(10).fontColor('#B45309')
              .padding({ left: 8, right: 8, top: 4, bottom: 4 })
              .backgroundColor('#FEF3C7').borderRadius(Theme.Radius.round)
            Text(`偏保守 ${this.followUpSummary.conservative_count}`)
              .fontSize(10).fontColor('#1D4ED8')
              .padding({ left: 8, right: 8, top: 4, bottom: 4 })
              .backgroundColor('#DBEAFE').borderRadius(Theme.Radius.round)
            Text(`较贴近 ${this.followUpSummary.calibrated_count}`)
              .fontSize(10).fontColor('#047857')
              .padding({ left: 8, right: 8, top: 4, bottom: 4 })
              .backgroundColor('#D1FAE5').borderRadius(Theme.Radius.round)
          }.width('100%')
        }

        if (
          this.followUpSummary &&
          this.followUpSummary.user_calibration_profile &&
          this.followUpSummary.user_calibration_profile!.review_count > 0
        ) {
          Column({ space: 6 }) {
            Row() {
              Text('系统已学到的偏差').fontSize(11).fontWeight(600).fontColor(Theme.Color.TextPrimary)
              Blank()
              Text(this.calibrationQualityText(this.followUpSummary.user_calibration_profile!.calibration_quality))
                .fontSize(10).fontColor(Theme.Color.TextSecondary)
            }.width('100%')
            Text(
              `${this.calibrationBiasText(this.followUpSummary.user_calibration_profile!.bias_tendency)} · ` +
              `未来置信修正 ${(this.followUpSummary.user_calibration_profile!.confidence_adjustment >= 0 ? '+' : '')}` +
              `${(this.followUpSummary.user_calibration_profile!.confidence_adjustment * 100).toFixed(0)}%`
            )
              .fontSize(10).fontColor(Theme.Color.TextSecondary)
            Text(this.followUpSummary.user_calibration_profile!.note)
              .fontSize(10).lineHeight(16).fontColor(Theme.Color.TextSecondary)
              .padding(8)
              .backgroundColor(Theme.Color.BackgroundTertiary)
              .borderRadius(Theme.Radius.m)
          }.width('100%').alignItems(HorizontalAlign.Start)
        }

        if (!this.currentSimulationId()) {
          Text('推演完成并保存后，可以在这里记录真实结果，校准预测偏差。')
            .fontSize(11).lineHeight(18).fontColor(Theme.Color.TextTertiary)
        } else if (this.getCurrentFollowUpReview()) {
          Column({ space: 8 }) {
            Row({ space: 8 }) {
              Text(`实际 ${this.getCurrentFollowUpReview()!.actual_score.toFixed(0)} 分`)
                .fontSize(12).fontWeight(700).fontColor(Theme.Color.Accent)
              Text(`${this.biasLabelText(this.getCurrentFollowUpReview()!.bias_label)} · ${this.getCurrentFollowUpReview()!.elapsed_months}个月后`)
                .fontSize(11).fontColor(Theme.Color.TextSecondary)
            }
            Text(this.getCurrentFollowUpReview()!.bias_note)
              .fontSize(11).lineHeight(18).fontColor(Theme.Color.TextSecondary)
            if (this.getCurrentFollowUpReview()!.actual_summary) {
              Text(this.getCurrentFollowUpReview()!.actual_summary)
                .fontSize(11).lineHeight(18).fontColor(Theme.Color.TextSecondary)
                .padding(10)
                .backgroundColor(Theme.Color.BackgroundTertiary)
                .borderRadius(Theme.Radius.m)
            }
          }.width('100%').alignItems(HorizontalAlign.Start)
        } else {
          Column({ space: 10 }) {
            Column({ space: 6 }) {
              Row() {
                Text('经过多久回看').fontSize(11).fontColor(Theme.Color.TextSecondary)
                Blank()
                Text(`${this.followUpElapsedMonths.toFixed(0)} 个月`).fontSize(11).fontWeight(600).fontColor(Theme.Color.Primary)
              }.width('100%')
              Slider({ value: this.followUpElapsedMonths, min: 1, max: 12, step: 1 })
                .width('100%')
                .trackColor(Theme.Color.BackgroundTertiary)
                .selectedColor(Theme.Color.Primary)
                .blockColor(Theme.Color.BackgroundSecondary)
                .trackThickness(6)
                .blockSize({ width: 20, height: 20 })
                .onChange((value: number) => { this.followUpElapsedMonths = value })
            }.width('100%')

            Column({ space: 6 }) {
              Row() {
                Text('真实结果得分').fontSize(11).fontColor(Theme.Color.TextSecondary)
                Blank()
                Text(`${this.followUpActualScore.toFixed(0)} 分`).fontSize(11).fontWeight(600)
                  .fontColor(this.followUpActualScore >= 70 ? '#10B981' : this.followUpActualScore >= 45 ? '#F59E0B' : '#EF4444')
              }.width('100%')
              Slider({ value: this.followUpActualScore, min: 0, max: 100, step: 5 })
                .width('100%')
                .trackColor(Theme.Color.BackgroundTertiary)
                .selectedColor(this.followUpActualScore >= 70 ? '#10B981' : this.followUpActualScore >= 45 ? '#F59E0B' : '#EF4444')
                .blockColor(Theme.Color.BackgroundSecondary)
                .trackThickness(6)
                .blockSize({ width: 20, height: 20 })
                .onChange((value: number) => { this.followUpActualScore = value })
            }.width('100%')

            TextArea({ placeholder: '3-60字描述真实发生了什么，比如：收入比预期低，但身心状态更稳', text: this.followUpText })
              .width('100%')
              .height(84)
              .fontSize(12)
              .fontColor(Theme.Color.TextPrimary)
              .placeholderColor(Theme.Color.TextTertiary)
              .backgroundColor(Theme.Color.BackgroundTertiary)
              .borderRadius(Theme.Radius.m)
              .onChange((value: string) => { this.followUpText = value })

            Button(this.isSubmittingFollowUp ? '提交中...' : '提交真实结果')
              .width('100%')
              .height(40)
              .fontSize(13).fontWeight(600)
              .fontColor('#FFFFFF')
              .backgroundColor(this.isSubmittingFollowUp ? Theme.Color.TextTertiary : Theme.Color.Primary)
              .borderRadius(Theme.Radius.m)
              .enabled(!this.isSubmittingFollowUp)
              .onClick(() => this.submitFollowUp())
          }.width('100%')
        }
      }
      .width('100%').padding(12)
      .backgroundColor(Theme.Color.BackgroundSecondary)
      .borderRadius(Theme.Radius.l)
      .border({ width: 1, color: Theme.Color.BorderLight })
      .shadow(Theme.Shadow.Soft)
      .alignItems(HorizontalAlign.Start)
      .margin({ left: 16, right: 16, top: 8, bottom: 6 })
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
