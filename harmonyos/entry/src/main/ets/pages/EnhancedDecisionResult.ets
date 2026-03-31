/**
 * 增强决策结果详情页 v2
 * 12 节点时间线 + 点击展开 + 纠错反馈 + 双指缩放
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { getAuthService } from '../service/AuthService'

interface TimelineEvent {
  month: number
  event: string
  impact: Record<string, number>
  probability: number
  event_id: string
  risk_tag: string
  branch_group: string
}

interface RiskAssessment {
  overall_risk: number
  overall_level: string
  recommendations: string[]
}

interface DecisionOption {
  option_id: string
  title: string
  description: string
  timeline: TimelineEvent[]
  final_score: number
  risk_level: number
  risk_assessment: RiskAssessment | null
}

interface SimulationData {
  simulation_id: string
  question: string
  options: DecisionOption[]
  recommendation: string
}

@Entry
@Component
struct EnhancedDecisionResult {
  @State simulationData: SimulationData | null = null
  @State selectedOptionIndex: number = 0
  @State expandedNodeId: string = ''
  @State feedbackSent: Record<string, string> = {}
  @State mapScale: number = 1.0
  @State mapOffsetX: number = 0
  @State mapOffsetY: number = 0

  private authService = getAuthService()

  aboutToAppear() {
    const params = router.getParams() as Record<string, Object>
    if (params?.simulationData) {
      this.simulationData = params.simulationData as SimulationData
    }
  }

  selectedOption(): DecisionOption | null {
    if (!this.simulationData) return null
    return this.simulationData.options[this.selectedOptionIndex] ?? null
  }

  mainNodes(): TimelineEvent[] {
    const opt = this.selectedOption()
    if (!opt) return []
    return opt.timeline.filter(e => e.branch_group === 'main' || !e.branch_group.includes('fork'))
  }

  branchNodes(parentMonth: number): TimelineEvent[] {
    const opt = this.selectedOption()
    if (!opt) return []
    return opt.timeline.filter(e =>
      e.branch_group.includes('fork') && e.month === parentMonth + 1
    )
  }

  // ── 反馈 ──────────────────────────────────────────────────────────────
  async sendFeedback(event: TimelineEvent, feedbackType: string) {
    if (!this.simulationData) return
    const key = `${event.event_id}_${feedbackType}`
    if (this.feedbackSent[key]) return
    this.feedbackSent[key] = feedbackType

    try {
      const userId = this.authService.getCurrentUserId()
      const req = http.createHttp()
      await req.request(`${ApiConfig.getBaseUrl()}/api/decision/enhanced/timeline-feedback`, {
        method: http.RequestMethod.POST,
        header: { 'Content-Type': 'application/json' },
        extraData: JSON.stringify({
          user_id: userId,
          simulation_id: this.simulationData.simulation_id,
          event_month: event.month,
          event_text: event.event,
          feedback_type: feedbackType,
          comment: ''
        })
      })
      req.destroy()
    } catch (e) {
      console.error('反馈发送失败:', e)
    }
  }

  // ── 辅助 ──────────────────────────────────────────────────────────────
  riskColor(tag: string): string {
    if (tag === 'high') return '#FF3B30'
    if (tag === 'low') return '#34C759'
    return '#FF9500'
  }

  scoreColor(score: number): string {
    if (score >= 70) return '#34C759'
    if (score >= 40) return '#FF9500'
    return '#FF3B30'
  }

  impactText(impact: Record<string, number>): string {
    const parts: string[] = []
    const keys = Object.keys(impact)
    for (let i = 0; i < keys.length; i++) {
      const k = keys[i]
      const v = impact[k] as number
      if (v > 0) parts.push(`${k}+`)
      else if (v < 0) parts.push(`${k}-`)
    }
    return parts.join(' ')
  }

  private navigateBack() {
    try { router.back() } catch (e) {}
  }

  // ── build ──────────────────────────────────────────────────────────────
  build() {
    Column() {
      // 顶部栏
      Row() {
        Text('←').fontSize(24).fontColor('#1A1A1A').fontWeight(600)
          .onClick(() => this.navigateBack())
        Text('决策分析').fontSize(18).fontWeight(700).fontColor('#1A1A1A')
          .margin({ left: 12 }).layoutWeight(1)
      }
      .width('100%').height(56).padding({ left: 16, right: 16 })
      .backgroundColor('rgba(255,255,255,0.95)')

      if (this.simulationData) {
        Scroll() {
          Column({ space: 16 }) {
            // 问题
            Text(this.simulationData.question)
              .fontSize(17).fontWeight(700).fontColor('#1A1A1A').lineHeight(26)
              .padding({ left: 20, right: 20, top: 12 })

            // 选项切换
            Scroll() {
              Row({ space: 10 }) {
                ForEach(this.simulationData.options, (opt: DecisionOption, idx: number) => {
                  Column({ space: 4 }) {
                    Text(opt.title)
                      .fontSize(14).fontWeight(600)
                      .fontColor(this.selectedOptionIndex === idx ? '#FFFFFF' : '#007AFF')
                    Text(`${opt.final_score.toFixed(0)}分`)
                      .fontSize(11)
                      .fontColor(this.selectedOptionIndex === idx ? 'rgba(255,255,255,0.8)' : '#999')
                  }
                  .padding({ left: 16, right: 16, top: 10, bottom: 10 })
                  .backgroundColor(this.selectedOptionIndex === idx ? '#007AFF' : 'rgba(0,122,255,0.08)')
                  .borderRadius(16)
                  .onClick(() => { this.selectedOptionIndex = idx; this.expandedNodeId = '' })
                })
              }.padding({ left: 20, right: 20 })
            }
            .scrollable(ScrollDirection.Horizontal).scrollBar(BarState.Off)

            // 时间线地图（支持双指缩放）
            Column() {
              Column({ space: 0 }) {
                ForEach(this.mainNodes(), (node: TimelineEvent, idx: number) => {
                  this.NodeCard(node, idx)
                })
              }
              .width('100%')
              .scale({ x: this.mapScale, y: this.mapScale })
              .translate({ x: this.mapOffsetX, y: this.mapOffsetY })
            }
            .width('100%')
            .clip(true)
            .gesture(
              PinchGesture({ fingers: 2 })
                .onActionUpdate((event: GestureEvent) => {
                  this.mapScale = Math.max(0.5, Math.min(3.0, event.scale))
                })
            )
            .gesture(
              PanGesture()
                .onActionUpdate((event: GestureEvent) => {
                  this.mapOffsetX += event.offsetX
                  this.mapOffsetY += event.offsetY
                })
            )

            // AI 推荐
            Column({ space: 10 }) {
              Text('AI 综合推荐').fontSize(16).fontWeight(700).fontColor('#007AFF')
              Text(this.simulationData.recommendation)
                .fontSize(14).fontColor('#333').lineHeight(22)
            }
            .width('100%').padding(20)
            .backgroundColor('rgba(0,122,255,0.04)')
            .borderRadius(16).margin({ left: 16, right: 16 })
            .alignItems(HorizontalAlign.Start)

            // 底部间距
            Column().height(40)
          }
        }
        .layoutWeight(1).scrollBar(BarState.Off)
      }
    }
    .width('100%').height('100%').backgroundColor('#F5F7FA')
  }

  // ── 节点卡片 ──────────────────────────────────────────────────────────
  @Builder
  NodeCard(node: TimelineEvent, idx: number) {
    Column({ space: 0 }) {
      // 连接线
      if (idx > 0) {
        Column().width(2).height(20).backgroundColor('#DDD').margin({ left: 30 })
      }

      // 节点主体
      Row({ space: 12 }) {
        // 月份圆点
        Column({ space: 2 }) {
          Circle({ width: 28, height: 28 })
            .fill(this.riskColor(node.risk_tag ?? 'medium'))
            .opacity(0.15)
          Text(`${node.month}月`).fontSize(10).fontColor('#999')
        }
        .width(40).alignItems(HorizontalAlign.Center)

        // 内容区（折叠/展开）
        Column({ space: 6 }) {
          // 标题行（始终显示）
          Row() {
            Text(node.event.length > 25 && this.expandedNodeId !== (node.event_id ?? `n${idx}`)
              ? node.event.substring(0, 25) + '...'
              : node.event)
              .fontSize(14).fontWeight(500).fontColor('#1A1A1A').lineHeight(20)
              .layoutWeight(1)
            Text(`${(node.probability * 100).toFixed(0)}%`)
              .fontSize(11).fontColor('#999')
          }.width('100%')

          // 展开详情
          if (this.expandedNodeId === (node.event_id ?? `n${idx}`)) {
            Column({ space: 8 }) {
              // 完整事件描述
              if (node.event.length > 25) {
                Text(node.event)
                  .fontSize(13).fontColor('#444').lineHeight(20)
              }

              // 影响维度
              Text(this.impactText(node.impact))
                .fontSize(12).fontColor('#666')
                .padding({ left: 8, right: 8, top: 4, bottom: 4 })
                .backgroundColor('#F5F7FA').borderRadius(8)

              // 反馈按钮
              Row({ space: 10 }) {
                Button('很准')
                  .height(30).fontSize(12).fontWeight(600)
                  .fontColor(this.feedbackSent[`${node.event_id}_accurate`] ? '#FFFFFF' : '#34C759')
                  .backgroundColor(this.feedbackSent[`${node.event_id}_accurate`] ? '#34C759' : 'rgba(52,199,89,0.1)')
                  .borderRadius(15)
                  .onClick(() => this.sendFeedback(node, 'accurate'))

                Button('不太可能')
                  .height(30).fontSize(12).fontWeight(600)
                  .fontColor(this.feedbackSent[`${node.event_id}_unlikely`] ? '#FFFFFF' : '#FF3B30')
                  .backgroundColor(this.feedbackSent[`${node.event_id}_unlikely`] ? '#FF3B30' : 'rgba(255,59,48,0.1)')
                  .borderRadius(15)
                  .onClick(() => this.sendFeedback(node, 'unlikely'))
              }
            }
          }
        }
        .layoutWeight(1)
        .padding(12)
        .backgroundColor(Color.White)
        .borderRadius(12)
        .border({ width: this.expandedNodeId === (node.event_id ?? `n${idx}`) ? 1.5 : 0.5,
          color: this.expandedNodeId === (node.event_id ?? `n${idx}`) ? '#007AFF' : '#E8E8E8' })
        .onClick(() => {
          const nid = node.event_id ?? `n${idx}`
          this.expandedNodeId = this.expandedNodeId === nid ? '' : nid
        })
      }
      .width('100%').padding({ left: 16, right: 16 })
    }
  }
}
