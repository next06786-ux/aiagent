/**
 * 涌现模式检测页面
 * 展示系统检测到的级联效应、反馈环、临界点和协同效应
 */
import { HttpUtil } from '../utils/HttpUtil'
import { ApiConfig } from '../config/ApiConfig'

interface EmergentPattern {
  id: string
  type: string
  domains: string[]
  description: string
  confidence: number
  impact_score: number
  recommendations: string[]
}

interface PatternSummary {
  total_patterns: number
  by_type: Record<string, number>
  high_impact: number
  patterns: EmergentPattern[]
}

@Entry
@Component
struct EmergencePatterns {
  @State userId: string = 'default_user'
  @State patterns: EmergentPattern[] = []
  @State summary: PatternSummary | null = null
  @State loading: boolean = false
  @State selectedTab: string = 'all'
  @State expandedPatternId: string = ''

  aboutToAppear() {
    this.loadPatterns()
  }

  async loadPatterns() {
    this.loading = true
    try {
      const response = await HttpUtil.get(`/api/emergence/patterns/${this.userId}`)
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        this.summary = result['data'] as PatternSummary
        this.patterns = (result['data'] as Record<string, Object>)['patterns'] as EmergentPattern[] || []
        console.info('[EmergencePatterns] Patterns loaded:', this.patterns.length)
      }
    } catch (error) {
      console.error('[EmergencePatterns] Failed to load patterns:', error)
    } finally {
      this.loading = false
    }
  }

  getPatternTypeColor(type: string): string {
    switch (type) {
      case 'cascade':
        return '#FF6B6B'
      case 'feedback_loop':
        return '#4ECDC4'
      case 'tipping_point':
        return '#FFE66D'
      case 'synergy':
        return '#95E1D3'
      default:
        return '#999999'
    }
  }

  getPatternTypeLabel(type: string): string {
    switch (type) {
      case 'cascade':
        return '级联效应'
      case 'feedback_loop':
        return '反馈环'
      case 'tipping_point':
        return '临界点'
      case 'synergy':
        return '协同效应'
      default:
        return '未知'
    }
  }

  getImpactLevel(score: number): string {
    if (score > 0.8) return '极高'
    if (score > 0.6) return '高'
    if (score > 0.4) return '中'
    return '低'
  }

  getImpactColor(score: number): string {
    if (score > 0.8) return '#FF4444'
    if (score > 0.6) return '#FF8844'
    if (score > 0.4) return '#FFAA44'
    return '#44AA44'
  }

  @Builder
  PatternCard(pattern: EmergentPattern) {
    Column() {
      // 头部
      Row() {
        // 类型标签
        Text(this.getPatternTypeLabel(pattern.type))
          .fontSize(12)
          .fontColor('#FFFFFF')
          .backgroundColor(this.getPatternTypeColor(pattern.type))
          .padding({ left: 8, right: 8, top: 4, bottom: 4 })
          .borderRadius(4)

        Blank()

        // 影响程度
        Row() {
          Text(this.getImpactLevel(pattern.impact_score))
            .fontSize(12)
            .fontColor(this.getImpactColor(pattern.impact_score))
            .fontWeight(FontWeight.Bold)

          Text(`${(pattern.impact_score * 100).toFixed(0)}%`)
            .fontSize(11)
            .fontColor('#999999')
            .margin({ left: 4 })
        }
      }
      .width('100%')
      .margin({ bottom: 12 })

      // 描述
      Text(pattern.description)
        .fontSize(14)
        .fontColor('#333333')
        .lineHeight(1.5)
        .margin({ bottom: 12 })

      // 涉及领域
      Row() {
        Text('涉及领域:')
          .fontSize(12)
          .fontColor('#666666')

        Flex({ wrap: FlexWrap.Wrap }) {
          ForEach(pattern.domains, (domain: string) => {
            Text(domain)
              .fontSize(11)
              .fontColor('#666666')
              .backgroundColor('#E0E0E0')
              .padding({ left: 6, right: 6, top: 2, bottom: 2 })
              .borderRadius(3)
              .margin({ right: 8, bottom: 8 })
          })
        }
        .width('100%')
      }
      .width('100%')
      .margin({ bottom: 12 })

      // 置信度
      Row() {
        Text('置信度:')
          .fontSize(12)
          .fontColor('#666666')

        Progress({
          value: pattern.confidence * 100,
          total: 100,
          type: ProgressType.Linear
        })
        .width('60%')
        .margin({ left: 8 })

        Text(`${(pattern.confidence * 100).toFixed(0)}%`)
          .fontSize(11)
          .fontColor('#999999')
          .margin({ left: 8 })
      }
      .width('100%')
      .margin({ bottom: 12 })

      // 建议（可展开）
      if (this.expandedPatternId === pattern.id) {
        Column() {
          Text('建议:')
            .fontSize(12)
            .fontColor('#333333')
            .fontWeight(FontWeight.Bold)
            .margin({ bottom: 8 })

          ForEach(pattern.recommendations, (rec: string, index: number) => {
            Row() {
              Text(`${index + 1}.`)
                .fontSize(12)
                .fontColor('#666666')
                .width(20)

              Text(rec)
                .fontSize(12)
                .fontColor('#666666')
                .lineHeight(1.4)
                .layoutWeight(1)
            }
            .width('100%')
            .margin({ bottom: index < pattern.recommendations.length - 1 ? 6 : 0 })
          })
        }
        .width('100%')
        .padding(10)
        .backgroundColor('#F5F5F5')
        .borderRadius(6)
        .margin({ top: 12 })
      }
    }
    .width('100%')
    .padding(12)
    .backgroundColor('#FFFFFF')
    .borderRadius(8)
    .border({
      width: 1,
      color: this.getPatternTypeColor(pattern.type) + '33'
    })
    .onClick(() => {
      this.expandedPatternId = this.expandedPatternId === pattern.id ? '' : pattern.id
    })
  }

  @Builder
  SummaryCard() {
    if (this.summary) {
      Column() {
        Text('检测摘要')
          .fontSize(16)
          .fontColor('#333333')
          .fontWeight(FontWeight.Bold)
          .margin({ bottom: 16 })

        // 总体统计
        Grid() {
          GridItem() {
            Column() {
              Text(this.summary.total_patterns.toString())
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
              Text(this.summary.high_impact.toString())
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
              Text((this.summary.by_type['cascade'] as number).toString())
                .fontSize(24)
              .fontColor('#4ECDC4')
              .fontWeight(FontWeight.Bold)

            Text('级联')
              .fontSize(12)
              .fontColor('#999999')
              .margin({ top: 4 })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Center)
        }

        GridItem() {
          Column() {
            Text((this.summary.by_type['feedback_loop'] as number).toString())
              .fontSize(24)
              .fontColor('#95E1D3')
              .fontWeight(FontWeight.Bold)

            Text('反馈环')
              .fontSize(12)
              .fontColor('#999999')
              .margin({ top: 4 })
          }
          .width('100%')
          .alignItems(HorizontalAlign.Center)
        }
      }
      .columnsTemplate('1fr 1fr')
      .rowsGap(12)
      .columnsGap(12)
      .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor('#F9F9F9')
    .borderRadius(8)
    }
  }

  build() {
    Column() {
      // 顶部栏
      Row() {
        Text('涌现模式检测')
          .fontSize(20)
          .fontColor('#333333')
          .fontWeight(FontWeight.Bold)

        Blank()

        Button('刷新')
          .fontSize(12)
          .height(32)
          .onClick(() => this.loadPatterns())
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 12, bottom: 12 })
      .backgroundColor('#FFFFFF')

      // 内容
      if (this.loading) {
        Column() {
          LoadingProgress()
            .width(40)
            .height(40)
            .margin({ bottom: 12 })

          Text('正在检测涌现模式...')
            .fontSize(14)
            .fontColor('#999999')
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      } else if (this.patterns.length === 0) {
        Column() {
          Text('暂无检测到的涌现模式')
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
            // 摘要卡片
            Column() {
              this.SummaryCard()
            }
            .margin({ bottom: 16 })

            // 模式列表
            ForEach(this.patterns, (pattern: EmergentPattern) => {
              Column() {
                this.PatternCard(pattern)
              }
              .margin({ bottom: 12 })
            })
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

