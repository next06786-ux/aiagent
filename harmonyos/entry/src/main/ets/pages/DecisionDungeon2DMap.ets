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
  title: string
  description: string
  month: number
  probability: number
  color: string
  riskTag: string
  eventType: string
  impact: Record<string, number>
  isBranch: boolean
  optionIndex: number
  optionTitle: string
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
  @State activeOptionIndex: number = 0
  @State selectedNodeId: string = ''
  @State processingNodeId: string = ''
  @State streamStatus: string = ''
  @State showDetail: boolean = false
  @State structuredRecommendation: RecommendationData | null = null
  @State liveThinkingText: string = ''
  @State isUpdatingModel: boolean = false
  @State showContent: boolean = false

  private dungeonId: string = ''
  private userId: string = ''
  private ws: WebSocketUtil | null = null

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
    const summaries: OptionSummary[] = []
    this.dungeonData.options.forEach((opt: DungeonOption, oi: number) => {
      summaries.push({ index: oi, title: opt.title, color: this.optColor(oi),
        finalScore: opt.final_score, riskLevel: opt.risk_level, status: '推演完成', progress: 1 })
      opt.timeline.forEach((ev: TimelineEvent, ei: number) => {
        allNodes.push({
          id: ev.event_id || `opt${oi}_${ei}`, title: this.shortTitle(ev.event),
          description: ev.event, month: ev.month, probability: ev.probability,
          color: (ev.branch_group && ev.branch_group.includes('fork'))
            ? (ev.risk_tag === 'low' ? '#10B981' : '#EF4444') : this.optColor(oi),
          riskTag: ev.risk_tag || 'medium', eventType: ev.event_type || 'general',
          impact: ev.impact, isBranch: !!(ev.branch_group && ev.branch_group.includes('fork')),
          optionIndex: oi, optionTitle: opt.title
        })
      })
    })
    this.optionSummaries = summaries
    this.nodes = allNodes
    this.showContent = true
  }

  private initSummaries(options: DungeonOption[]) {
    this.optionSummaries = options.map((opt: DungeonOption, i: number): OptionSummary => ({
      index: i, title: opt.title, color: this.optColor(i),
      finalScore: 0, riskLevel: 0, status: '等待推演', progress: 0.05
    }))
  }

  private async startStreamSimulation() {
    if (!this.dungeonId) { this.streamStatus = '缺少会话信息'; return }
    this.streamStatus = '正在准备推演...'
    this.showContent = true
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
              this.streamStatus = '模型推演中...'
            }
            else if (type === 'status' || type === 'thinking') { this.streamStatus = (ev.content as string) || '' }
            else if (type === 'option_start') {
              const title = ev.title as string
              const idx = this.findOptIdx(title)
              if (idx >= 0) { this.activeOptionIndex = idx; this.updateStatus(idx, '推演中...') }
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
              this.streamStatus = '推演失败'
              promptAction.showToast({ message: ev.content as string })
              if (this.ws) { this.ws.close(); this.ws = null }
            }
          } catch (err) { console.error('事件解析失败') }
        }, 0)
      })
      this.ws.onError(() => { this.streamStatus = '连接失败' })
      this.ws.onClose(() => {})
      await this.ws.connect('/api/decision/enhanced/ws/simulate')
      this.streamStatus = '等待模型响应...'
      const opts: StreamRequestOption[] = this.dungeonData ? this.dungeonData.options.map((o: DungeonOption): StreamRequestOption => ({ title: o.title, description: o.description })) : []
      this.ws.send({ session_id: this.dungeonId, options: opts } as StreamRequestPayload)
    } catch (e) { this.streamStatus = '推演启动失败' }
  }

  private handleNode(ev: Record<string, Object>) {
    const node = ev.node as Record<string, Object>
    const optTitle = ev.option_title as string
    const oi = this.findOptIdx(optTitle)
    if (oi < 0) return
    const isBranch = ((node.branch_group as string) || '').includes('fork')
    const mapNode: MapNode = {
      id: (node.event_id as string) || `s_${oi}_${this.nodes.length}`,
      title: this.shortTitle((node.event as string) || ''),
      description: (node.event as string) || '',
      month: (node.month as number) || 0,
      probability: (node.probability as number) || 0,
      color: isBranch ? ((node.risk_tag as string) === 'low' ? '#10B981' : '#EF4444') : this.optColor(oi),
      riskTag: (node.risk_tag as string) || 'medium',
      eventType: (node.event_type as string) || 'general',
      impact: (node.impact as Record<string, number>) || {},
      isBranch, optionIndex: oi, optionTitle: optTitle
    }
    this.nodes = this.nodes.concat([mapNode])
    this.processingNodeId = mapNode.id
    this.activeOptionIndex = oi
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

  private getImpactText(node: MapNode): string {
    const items = Object.keys(node.impact).filter((k: string) => Math.abs(node.impact[k]) > 0.05)
      .map((k: string) => `${k}${node.impact[k] > 0 ? '+' : '-'}`)
    return items.length > 0 ? items.join(' ') : '影响平稳'
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
    // 中间主节点卡片区 - 可上下滚动
    Scroll() {
      Column({ space: 12 }) {
        ForEach(this.nodes.filter((n: MapNode) => n.optionIndex === this.activeOptionIndex), (node: MapNode, index: number) => {
          Row({ space: 14 }) {
            // 左侧月份圆
            Stack() {
              Circle({ width: 40, height: 40 }).fill(node.color).opacity(0.12)
              Text(`${node.month}`).fontSize(14).fontWeight(600).fontColor(node.color)
            }.width(40).height(40)

            // 右侧内容
            Column({ space: 4 }) {
              Row({ space: 6 }) {
                Text(node.title).fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary).layoutWeight(1)
                Text(node.isBranch ? '分支' : '主链').fontSize(9)
                  .fontColor(node.isBranch ? '#B45309' : '#2563EB')
                  .padding({ left: 6, right: 6, top: 2, bottom: 2 })
                  .backgroundColor(node.isBranch ? '#FEF3C7' : '#DBEAFE')
                  .borderRadius(Theme.Radius.round)
              }
              Text(node.description).fontSize(12).fontColor(Theme.Color.TextTertiary)
                .maxLines(2).textOverflow({ overflow: TextOverflow.Ellipsis })
            }.layoutWeight(1)
          }
          .width('100%').padding(14)
          .backgroundColor(this.selectedNodeId === node.id ? 'rgba(10, 89, 247, 0.05)' : Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: this.selectedNodeId === node.id ? 'rgba(10, 89, 247, 0.15)' : Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)
          .onClick(() => { this.selectedNodeId = node.id; this.showDetail = true })
          .stateStyles({
            pressed: { .scale({ x: 0.98, y: 0.98 }) },
            normal: { .scale({ x: 1, y: 1 }) }
          })
        })

        // 正在生成的节点占位
        if (this.processingNodeId) {
          Row({ space: 14 }) {
            LoadingProgress().width(28).height(28).color(Theme.Color.Primary)
            Text('正在推演下一个节点...').fontSize(13).fontColor(Theme.Color.Primary)
          }
          .width('100%').padding(14)
          .backgroundColor('rgba(10, 89, 247, 0.03)')
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: 'rgba(10, 89, 247, 0.1)' })
        }
      }
      .padding({ left: 16, right: 16, top: 8, bottom: 20 })
    }
    .scrollBar(BarState.Auto)
    .edgeEffect(EdgeEffect.Spring)
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
