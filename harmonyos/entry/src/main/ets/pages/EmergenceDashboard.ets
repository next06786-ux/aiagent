/**
 * 涌现模式分析仪表板
 * 综合展示涌现检测、报告、风险评估等信息
 */
import { HttpUtil } from '../utils/HttpUtil'
import { ApiConfig } from '../config/ApiConfig'

interface ExecutiveSummary {
  status: string
  message: string
  total_patterns: number
  high_impact_patterns: number
  top_concern: TopConcern
}

interface TopConcern {
  type: string
  impact: number
}

interface ActionItem {
  timeframe: string
  actions: string[]
}

interface ActionPlan {
  immediate_actions: ActionItem
  short_term_actions: ActionItem
  long_term_actions: ActionItem
}

interface RiskItem {
  description: string
}

interface RiskDistribution {
  critical: RiskItem[]
  high: RiskItem[]
}

interface RiskAssessment {
  overall_risk_level: string
  risk_distribution: RiskDistribution
}

interface Changes {
  health_change: number
  mood_change: number
  stress_change: number
}

interface ProgressTracking {
  trend: string
  changes: Changes
}

interface Report {
  user_id: string
  report_date: string
  executive_summary: ExecutiveSummary
  pattern_analysis: Record<string, Object>[]
  cross_domain_insights: Record<string, Object>
  risk_assessment: RiskAssessment
  action_plan: ActionPlan
  progress_tracking: ProgressTracking
  recommendations: string[]
}

@Entry
@Component
struct EmergenceDashboard {
  @State userId: string = 'default_user'
  @State report: Report | null = null
  @State loading: boolean = false
  @State activeTab: string = 'summary'
  @State expandedSection: string = ''

  aboutToAppear() {
    this.loadReport()
  }

  async loadReport() {
    this.loading = true
    try {
      const response = await HttpUtil.get(`/api/emergence/report/${this.userId}`)
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        this.report = result['data'] as Report
        console.info('[EmergenceDashboard] Report loaded')
      }
    } catch (error) {
      console.error('[EmergenceDashboard] Failed to load report:', error)
    } finally {
      this.loading = false
    }
  }

  getStatusColor(status: string): string {
    switch (status) {
      case 'critical':
        return '#FF4444'
      case 'warning':
        return '#FF8844'
      case 'caution':
        return '#FFAA44'
      case 'healthy':
        return '#44AA44'
      default:
        return '#999999'
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'critical':
        return '严重'
      case 'warning':
        return '警告'
      case 'caution':
        return '注意'
      case 'healthy':
        return '健康'
      default:
        return '未知'
    }
  }

  @Builder
  ExecutiveSummarySection() {
    if (this.report?.executive_summary) {
      Column() {
        // 状态卡片
        Row() {
          Column() {
            Text(this.getStatusLabel((this.report.executive_summary as ExecutiveSummary).status))
              .fontSize(14)
              .fontColor('#FFFFFF')
              .fontWeight(FontWeight.Bold)

            Text((this.report.executive_summary as ExecutiveSummary).status.toUpperCase())
              .fontSize(12)
              .fontColor('#FFFFFF')
              .opacity(0.8)
              .margin({ top: 4 })
          }
          .padding(16)
          .backgroundColor(this.getStatusColor((this.report.executive_summary as ExecutiveSummary).status))
          .borderRadius(8)
          .width('30%')

          Column() {
            Text((this.report.executive_summary as ExecutiveSummary).message)
              .fontSize(13)
              .fontColor('#333333')
              .lineHeight(1.5)
          }
          .padding(16)
          .backgroundColor('#F5F5F5')
          .borderRadius(8)
          .layoutWeight(1)
          .margin({ left: 12 })
        }
        .width('100%')
        .margin({ bottom: 16 })

        // 关键指标
        Grid() {
          GridItem() {
            Column() {
              Text((this.report.executive_summary as ExecutiveSummary).total_patterns.toString())
                .fontSize(24)
                .fontColor('#FF6B6B')
                .fontWeight(FontWeight.Bold)

              Text('总模式数')
                .fontSize(12)
                .fontColor('#999999')
                .margin({ top: 4 })
            }
            .width('100%')
            .alignItems(HorizontalAlign.Center)
          }

          GridItem() {
            Column() {
              Text((this.report.executive_summary as ExecutiveSummary).high_impact_patterns.toString())
                .fontSize(24)
                .fontColor('#FFE66D')
                .fontWeight(FontWeight.Bold)

              Text('高影响')
                .fontSize(12)
                .fontColor('#999999')
                .margin({ top: 4 })
            }
            .width('100%')
            .alignItems(HorizontalAlign.Center)
          }

          GridItem() {
            Column() {
              Text(((this.report.executive_summary as ExecutiveSummary).top_concern as TopConcern)?.type || 'N/A')
                .fontSize(14)
                .fontColor('#4ECDC4')
                .fontWeight(FontWeight.Bold)

              Text('主要关注')
                .fontSize(12)
                .fontColor('#999999')
                .margin({ top: 4 })
            }
            .width('100%')
            .alignItems(HorizontalAlign.Center)
          }
        }
        .columnsTemplate('1fr 1fr 1fr')
        .rowsGap(12)
        .columnsGap(12)
        .width('100%')
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#FFFFFF')
      .borderRadius(8)
    }
  }

  @Builder
  ActionPlanSection() {
    if (this.report?.action_plan) {
      Column() {
        Text('行动计划')
          .fontSize(16)
          .fontColor('#333333')
          .fontWeight(FontWeight.Bold)
          .margin({ bottom: 16 })

        // 立即行动
        Column() {
          Row() {
            Text('🔴')
              .fontSize(16)
              .margin({ right: 8 })

            Column() {
              Text('立即行动')
                .fontSize(13)
                .fontColor('#333333')
                .fontWeight(FontWeight.Bold)

              Text((this.report.action_plan as ActionPlan).immediate_actions.timeframe)
                .fontSize(11)
                .fontColor('#999999')
                .margin({ top: 2 })
            }
            .layoutWeight(1)
          }
          .width('100%')
          .padding(12)
          .backgroundColor('#FFE6E6')
          .borderRadius(6)
          .margin({ bottom: 12 })

          ForEach(((this.report.action_plan as ActionPlan).immediate_actions.actions) || [], (action: string) => {
            Row() {
              Text('•')
                .fontSize(14)
                .fontColor('#FF6B6B')
                .margin({ right: 8 })

              Text(action)
                .fontSize(12)
                .fontColor('#666666')
                .lineHeight(1.4)
                .layoutWeight(1)
            }
            .width('100%')
            .margin({ bottom: 8 })
          })
        }
        .width('100%')
        .margin({ bottom: 16 })

        // 短期行动
        Column() {
          Row() {
            Text('🟡')
              .fontSize(16)
              .margin({ right: 8 })

            Column() {
              Text('短期行动')
                .fontSize(13)
                .fontColor('#333333')
                .fontWeight(FontWeight.Bold)

              Text((this.report.action_plan as ActionPlan).short_term_actions.timeframe)
                .fontSize(11)
                .fontColor('#999999')
                .margin({ top: 2 })
            }
            .layoutWeight(1)
          }
          .width('100%')
          .padding(12)
          .backgroundColor('#FFF5E6')
          .borderRadius(6)
          .margin({ bottom: 12 })

          ForEach(((this.report.action_plan as ActionPlan).short_term_actions.actions) || [], (action: string) => {
            Row() {
              Text('•')
                .fontSize(14)
                .fontColor('#FFB84D')
                .margin({ right: 8 })

              Text(action)
                .fontSize(12)
                .fontColor('#666666')
                .lineHeight(1.4)
                .layoutWeight(1)
            }
            .width('100%')
            .margin({ bottom: 8 })
          })
        }
        .width('100%')
        .margin({ bottom: 16 })

        // 长期行动
        Column() {
          Row() {
            Text('🟢')
              .fontSize(16)
              .margin({ right: 8 })

            Column() {
              Text('长期行动')
                .fontSize(13)
                .fontColor('#333333')
                .fontWeight(FontWeight.Bold)

              Text((this.report.action_plan as ActionPlan).long_term_actions.timeframe)
                .fontSize(11)
                .fontColor('#999999')
                .margin({ top: 2 })
            }
            .layoutWeight(1)
          }
          .width('100%')
          .padding(12)
          .backgroundColor('#E6F5E6')
          .borderRadius(6)
          .margin({ bottom: 12 })

          ForEach(((this.report.action_plan as ActionPlan).long_term_actions.actions) || [], (action: string) => {
            Row() {
              Text('•')
                .fontSize(14)
                .fontColor('#44AA44')
                .margin({ right: 8 })

              Text(action)
                .fontSize(12)
                .fontColor('#666666')
                .lineHeight(1.4)
                .layoutWeight(1)
            }
            .width('100%')
            .margin({ bottom: 8 })
          })
        }
        .width('100%')
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#FFFFFF')
      .borderRadius(8)
    }
  }

  @Builder
  RiskAssessmentSection() {
    if (this.report?.risk_assessment) {
      Column() {
        Text('风险评估')
          .fontSize(16)
          .fontColor('#333333')
          .fontWeight(FontWeight.Bold)
          .margin({ bottom: 16 })

        // 总体风险
        Row() {
          Text('总体风险等级:')
            .fontSize(13)
            .fontColor('#666666')

          Text(((this.report.risk_assessment as RiskAssessment).overall_risk_level as string)?.toUpperCase() || 'UNKNOWN')
            .fontSize(13)
            .fontColor(this.getStatusColor((this.report.risk_assessment as RiskAssessment).overall_risk_level as string))
            .fontWeight(FontWeight.Bold)
            .margin({ left: 8 })
        }
        .width('100%')
        .padding(12)
        .backgroundColor('#F5F5F5')
        .borderRadius(6)
        .margin({ bottom: 16 })

        // 风险分布
        if ((this.report.risk_assessment as RiskAssessment).risk_distribution) {
          Column() {
            if ((this.report.risk_assessment as RiskAssessment).risk_distribution.critical) {
              Column() {
                Text(`严重风险 (${((this.report.risk_assessment as RiskAssessment).risk_distribution.critical).length})`)
                  .fontSize(12)
                  .fontColor('#FF4444')
                  .fontWeight(FontWeight.Bold)
                  .margin({ bottom: 8 })

                ForEach(((this.report.risk_assessment as RiskAssessment).risk_distribution.critical), (risk: RiskItem) => {
                  Text(risk.description)
                    .fontSize(11)
                    .fontColor('#666666')
                    .lineHeight(1.4)
                    .margin({ bottom: 6 })
                })
              }
              .width('100%')
              .padding(12)
              .backgroundColor('#FFE6E6')
              .borderRadius(6)
              .margin({ bottom: 12 })
            }

            if ((this.report.risk_assessment as RiskAssessment).risk_distribution.high) {
              Column() {
                Text(`高风险 (${((this.report.risk_assessment as RiskAssessment).risk_distribution.high).length})`)
                  .fontSize(12)
                  .fontColor('#FF8844')
                  .fontWeight(FontWeight.Bold)
                  .margin({ bottom: 8 })

                ForEach(((this.report.risk_assessment as RiskAssessment).risk_distribution.high), (risk: RiskItem) => {
                  Text(risk.description)
                    .fontSize(11)
                    .fontColor('#666666')
                    .lineHeight(1.4)
                    .margin({ bottom: 6 })
                })
              }
              .width('100%')
              .padding(12)
              .backgroundColor('#FFF5E6')
              .borderRadius(6)
              .margin({ bottom: 12 })
            }
          }
          .width('100%')
        }
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#FFFFFF')
      .borderRadius(8)
    }
  }

  @Builder
  ProgressTrackingSection() {
    if (this.report?.progress_tracking) {
      Column() {
        Text('进度跟踪')
          .fontSize(16)
          .fontColor('#333333')
          .fontWeight(FontWeight.Bold)
          .margin({ bottom: 16 })

        // 趋势指示
        Row() {
          Text('总体趋势:')
            .fontSize(13)
            .fontColor('#666666')

          Text((this.report.progress_tracking as ProgressTracking).trend === 'improving' ? '📈 改善中' : '📉 下降中')
            .fontSize(13)
            .fontColor((this.report.progress_tracking as ProgressTracking).trend === 'improving' ? '#44AA44' : '#FF6B6B')
            .fontWeight(FontWeight.Bold)
            .margin({ left: 8 })
        }
        .width('100%')
        .padding(12)
        .backgroundColor('#F5F5F5')
        .borderRadius(6)
        .margin({ bottom: 16 })

        // 指标变化
        Grid() {
          GridItem() {
            Column() {
              Text('健康分数')
                .fontSize(11)
                .fontColor('#999999')

              Text(`${((this.report.progress_tracking as ProgressTracking).changes.health_change) > 0 ? '+' : ''}${((this.report.progress_tracking as ProgressTracking).changes.health_change) || 0}`)
                .fontSize(16)
                .fontColor(((this.report.progress_tracking as ProgressTracking).changes.health_change) > 0 ? '#44AA44' : '#FF6B6B')
                .fontWeight(FontWeight.Bold)
                .margin({ top: 4 })
            }
            .width('100%')
            .alignItems(HorizontalAlign.Center)
          }

          GridItem() {
            Column() {
              Text('心情')
                .fontSize(11)
                .fontColor('#999999')

              Text(`${((this.report.progress_tracking as ProgressTracking).changes.mood_change) > 0 ? '+' : ''}${((this.report.progress_tracking as ProgressTracking).changes.mood_change) || 0}`)
                .fontSize(16)
                .fontColor(((this.report.progress_tracking as ProgressTracking).changes.mood_change) > 0 ? '#44AA44' : '#FF6B6B')
                .fontWeight(FontWeight.Bold)
                .margin({ top: 4 })
            }
            .width('100%')
            .alignItems(HorizontalAlign.Center)
          }

          GridItem() {
            Column() {
              Text('压力')
                .fontSize(11)
                .fontColor('#999999')

              Text(`${((this.report.progress_tracking as ProgressTracking).changes.stress_change) > 0 ? '+' : ''}${((this.report.progress_tracking as ProgressTracking).changes.stress_change) || 0}`)
                .fontSize(16)
                .fontColor(((this.report.progress_tracking as ProgressTracking).changes.stress_change) > 0 ? '#FF6B6B' : '#44AA44')
                .fontWeight(FontWeight.Bold)
                .margin({ top: 4 })
            }
            .width('100%')
            .alignItems(HorizontalAlign.Center)
          }
        }
        .columnsTemplate('1fr 1fr 1fr')
        .rowsGap(12)
        .columnsGap(12)
        .width('100%')
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#FFFFFF')
      .borderRadius(8)
    }
  }

  build() {
    Column() {
      // 顶部栏
      Row() {
        Text('涌现分析仪表板')
          .fontSize(20)
          .fontColor('#333333')
          .fontWeight(FontWeight.Bold)

        Blank()

        Button('刷新')
          .fontSize(12)
          .height(32)
          .onClick(() => this.loadReport())
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 12, bottom: 12 })
      .backgroundColor('#FFFFFF')

      // 标签栏
      Row() {
        Button('摘要')
          .fontSize(12)
          .height(32)
          .backgroundColor(this.activeTab === 'summary' ? '#4ECDC4' : '#E0E0E0')
          .fontColor(this.activeTab === 'summary' ? '#FFFFFF' : '#666666')
          .onClick(() => this.activeTab = 'summary')
          .margin({ right: 8 })

        Button('行动计划')
          .fontSize(12)
          .height(32)
          .backgroundColor(this.activeTab === 'action' ? '#4ECDC4' : '#E0E0E0')
          .fontColor(this.activeTab === 'action' ? '#FFFFFF' : '#666666')
          .onClick(() => this.activeTab = 'action')
          .margin({ right: 8 })

        Button('风险评估')
          .fontSize(12)
          .height(32)
          .backgroundColor(this.activeTab === 'risk' ? '#4ECDC4' : '#E0E0E0')
          .fontColor(this.activeTab === 'risk' ? '#FFFFFF' : '#666666')
          .onClick(() => this.activeTab = 'risk')
          .margin({ right: 8 })

        Button('进度')
          .fontSize(12)
          .height(32)
          .backgroundColor(this.activeTab === 'progress' ? '#4ECDC4' : '#E0E0E0')
          .fontColor(this.activeTab === 'progress' ? '#FFFFFF' : '#666666')
          .onClick(() => this.activeTab = 'progress')
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 8, bottom: 8 })
      .backgroundColor('#F5F5F5')

      // 内容
      if (this.loading) {
        Column() {
          LoadingProgress()
            .width(40)
            .height(40)
            .margin({ bottom: 12 })

          Text('正在加载报告...')
            .fontSize(14)
            .fontColor('#999999')
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      } else {
        Scroll() {
          Column() {
            if (this.activeTab === 'summary') {
              this.ExecutiveSummarySection()
            } else if (this.activeTab === 'action') {
              this.ActionPlanSection()
            } else if (this.activeTab === 'risk') {
              this.RiskAssessmentSection()
            } else if (this.activeTab === 'progress') {
              this.ProgressTrackingSection()
            }
          }
          .width('100%')
          .padding({ left: 16, right: 16, top: 12, bottom: 12 })
        }
        .width('100%')
        .layoutWeight(1)
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }
}
