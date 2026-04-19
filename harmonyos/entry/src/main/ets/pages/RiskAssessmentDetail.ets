/**
 * 风险评估详情页面
 * 展示6大风险维度的雷达图和详细分析
 */
import router from '@ohos.router'
import { util } from '@kit.ArkTS'

interface RiskDimension {
  name: string
  score: number
  level: string
  factors: string[]
  mitigation: string[]
}

interface RiskAssessment {
  overall_risk: number
  overall_level: string
  high_risk_count: number
  dimensions: Record<string, RiskDimension>
  recommendations: string[]
}

interface DecisionOption {
  option_id: string
  title: string
  description: string
  final_score: number
  risk_level: number
  risk_assessment?: RiskAssessment
}

interface RiskRouterParams {
  option?: string
}

@Entry
@Component
struct RiskAssessmentDetail {
  @State option: DecisionOption | null = null
  @State selectedDimension: string = ''
  @State showContent: boolean = false
  private canvasContext: CanvasRenderingContext2D | null = null

  private dimensions: string[] = ['health', 'finance', 'social', 'time', 'emotion', 'learning']
  private dimensionNames: Record<string, string> = {
    'health': '健康',
    'finance': '财务',
    'social': '社交',
    'time': '时间',
    'emotion': '情绪',
    'learning': '学习'
  }

  aboutToAppear() {
    const params = router.getParams() as RiskRouterParams
    if (params && params.option) {
      this.option = JSON.parse(params.option) as DecisionOption
    }
    
    setTimeout(() => {
      this.showContent = true
    }, 100)
  }

  build() {
    Stack() {
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('#F1F3F5')

      Column() {
        // 顶部导航栏
        Row() {
          Button({ type: ButtonType.Circle }) {
            Text('←')
              .fontSize(24)
              .fontColor('#1A1A1A')
              .fontWeight(600)
          }
          .width(40)
          .height(40)
          .backgroundColor('rgba(255, 255, 255, 0.0)')
          .onClick(() => {
            router.back()
          })

          Column({ space: 2 }) {
            Text('风险评估')
              .fontSize(20)
              .fontWeight(700)
              .fontColor('#1A1A1A')
            
            if (this.option) {
              Text(this.option.title)
                .fontSize(14)
                .fontColor('#666')
            }
          }
          .margin({ left: 12 })
          .alignItems(HorizontalAlign.Start)

          Blank()
        }
        .width('100%')
        .height(56)
        .padding({ left: 16, right: 16 })
        .backgroundColor('rgba(255, 255, 255, 0.6)')
        .backdropBlur(20)

        if (this.option && this.option.risk_assessment) {
          Scroll() {
            Column({ space: 24 }) {
              // 总体风险卡片
              this.OverallRiskCard()

              // 雷达图
              this.RadarChartCard()

              // 维度详情列表
              this.DimensionsList()

              // 总体建议
              this.RecommendationsCard()
            }
            .width('100%')
            .padding({ left: 16, right: 16, top: 20, bottom: 40 })
          }
          .layoutWeight(1)
          .scrollBar(BarState.Off)
          .edgeEffect(EdgeEffect.Spring)
        } else {
          Column() {
            Text('暂无风险评估数据')
              .fontSize(16)
              .fontColor('#999')
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        }
      }
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  OverallRiskCard() {
    Column({ space: 16 }) {
      Text('总体风险')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')

      Row({ space: 20 }) {
        Column({ space: 8 }) {
          Text(`${this.option?.risk_assessment?.overall_risk.toFixed(1) || '0'}`)
            .fontSize(48)
            .fontWeight(800)
            .fontColor(this.getRiskColor(this.option?.risk_assessment?.overall_risk || 0))
          
          Text('/ 10')
            .fontSize(16)
            .fontColor('#999')
        }

        Divider().vertical(true).height(60).color('#E0E0E0')

        Column({ space: 12 }) {
          Row({ space: 8 }) {
            Text('风险等级:')
              .fontSize(14)
              .fontColor('#666')
            
            Text(this.getRiskLevelText(this.option?.risk_assessment?.overall_level || ''))
              .fontSize(16)
              .fontWeight(700)
              .fontColor(this.getRiskColor(this.option?.risk_assessment?.overall_risk || 0))
              .padding({ left: 12, right: 12, top: 4, bottom: 4 })
              .backgroundColor(this.getRiskColor(this.option?.risk_assessment?.overall_risk || 0) + '20')
              .borderRadius(8)
          }

          Row({ space: 8 }) {
            Text('高风险维度:')
              .fontSize(14)
              .fontColor('#666')
            
            Text(`${this.option?.risk_assessment?.high_risk_count || 0} 个`)
              .fontSize(16)
              .fontWeight(700)
              .fontColor('#FF3B30')
          }
        }
        .alignItems(HorizontalAlign.Start)
      }
      .width('100%')
      .justifyContent(FlexAlign.Center)
    }
    .width('100%')
    .padding(24)
    .backgroundColor('rgba(255, 255, 255, 0.9)')
    .borderRadius(20)
    .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
  }

  @Builder
  RadarChartCard() {
    Column({ space: 16 }) {
      Text('风险雷达图')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')

      Canvas(this.canvasContext)
        .width('100%')
        .height(320)
        .onReady(() => {
          this.drawRadarChart()
        })
    }
    .width('100%')
    .padding(24)
    .backgroundColor('rgba(255, 255, 255, 0.9)')
    .borderRadius(20)
    .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
  }

  @Builder
  DimensionsList() {
    Column({ space: 12 }) {
      Text('维度详情')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')
        .padding({ left: 8, bottom: 8 })

      if (this.option?.risk_assessment?.dimensions) {
        Column({ space: 12 }) {
          ForEach(this.dimensions, (dimKey: string) => {
            if (this.option!.risk_assessment!.dimensions[dimKey]) {
              this.DimensionCard(dimKey, this.option!.risk_assessment!.dimensions[dimKey])
            }
          })
        }
        .width('100%')
      }
    }
    .width('100%')
  }

  @Builder
  DimensionCard(dimKey: string, dimension: RiskDimension) {
    Column({ space: 16 }) {
      // 维度名称和得分
      Row() {
        Text(dimension.name)
          .fontSize(18)
          .fontWeight(700)
          .fontColor('#1A1A1A')

        Blank()

        Column({ space: 4 }) {
          Text(`${dimension.score.toFixed(1)}`)
            .fontSize(24)
            .fontWeight(800)
            .fontColor(this.getRiskColor(dimension.score))
          
          Text(this.getRiskLevelText(dimension.level))
            .fontSize(12)
            .fontColor(this.getRiskColor(dimension.score))
        }
        .alignItems(HorizontalAlign.End)
      }
      .width('100%')

      // 风险等级进度条
      Progress({
        value: dimension.score * 10,
        total: 100,
        type: ProgressType.Linear
      })
        .width('100%')
        .height(8)
        .color(this.getRiskColor(dimension.score))
        .style({ strokeWidth: 8, enableSmoothEffect: true })

      // 风险因素
      if (dimension.factors && dimension.factors.length > 0) {
        Column({ space: 8 }) {
          Text('风险因素')
            .fontSize(14)
            .fontWeight(600)
            .fontColor('#666')

          ForEach(dimension.factors, (factor: string) => {
            Row({ space: 8 }) {
              Text('•')
                .fontSize(16)
                .fontColor('#FF9800')
              
              Text(factor)
                .fontSize(14)
                .fontColor('#333')
                .layoutWeight(1)
            }
            .width('100%')
          })
        }
        .width('100%')
        .padding(12)
        .backgroundColor('#FFF3E0')
        .borderRadius(8)
        .alignItems(HorizontalAlign.Start)
      }

      // 缓解建议（可展开）
      if (dimension.mitigation && dimension.mitigation.length > 0) {
        Column({ space: 8 }) {
          Row() {
            Text('缓解建议')
              .fontSize(14)
              .fontWeight(600)
              .fontColor('#4CAF50')
            
            Blank()
            
            Text(this.selectedDimension === dimKey ? '收起 ▲' : '展开 ▼')
              .fontSize(12)
              .fontColor('#007AFF')
          }
          .width('100%')
          .onClick(() => {
            this.selectedDimension = this.selectedDimension === dimKey ? '' : dimKey
          })

          if (this.selectedDimension === dimKey) {
            ForEach(dimension.mitigation, (mit: string) => {
              Row({ space: 8 }) {
                Text('✓')
                  .fontSize(16)
                  .fontColor('#4CAF50')
                
                Text(mit)
                  .fontSize(14)
                  .fontColor('#333')
                  .layoutWeight(1)
              }
              .width('100%')
            })
          }
        }
        .width('100%')
        .padding(12)
        .backgroundColor('#E8F5E9')
        .borderRadius(8)
        .alignItems(HorizontalAlign.Start)
      }
    }
    .width('100%')
    .padding(20)
    .backgroundColor('rgba(255, 255, 255, 0.9)')
    .borderRadius(16)
    .shadow({ radius: 5, color: 'rgba(0,0,0,0.03)', offsetY: 2 })
  }

  @Builder
  RecommendationsCard() {
    Column({ space: 16 }) {
      Text('总体建议')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')

      if (this.option?.risk_assessment?.recommendations) {
        ForEach(this.option.risk_assessment.recommendations, (rec: string, index: number) => {
          Row({ space: 12 }) {
            Text(`${index + 1}`)
              .fontSize(14)
              .fontWeight(700)
              .fontColor(Color.White)
              .width(24)
              .height(24)
              .textAlign(TextAlign.Center)
              .backgroundColor('#007AFF')
              .borderRadius(12)
            
            Text(rec)
              .fontSize(14)
              .fontColor('#333')
              .lineHeight(22)
              .layoutWeight(1)
          }
          .width('100%')
        })
      }
    }
    .width('100%')
    .padding(20)
    .backgroundColor('rgba(0, 122, 255, 0.05)')
    .borderRadius(16)
    .alignItems(HorizontalAlign.Start)
  }

  drawRadarChart() {
    if (!this.canvasContext || !this.option?.risk_assessment) return

    const ctx = this.canvasContext
    const centerX = 160
    const centerY = 160
    const maxRadius = 120
    const levels = 5

    // 清空画布
    ctx.clearRect(0, 0, 320, 320)

    // 绘制背景圆圈
    for (let i = 1; i <= levels; i++) {
      const radius = (maxRadius / levels) * i
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI)
      ctx.strokeStyle = '#E0E0E0'
      ctx.lineWidth = 1
      ctx.stroke()
    }

    // 绘制6条轴线和标签
    const angleStep = (2 * Math.PI) / 6
    for (let i = 0; i < 6; i++) {
      const angle = angleStep * i - Math.PI / 2
      const x = centerX + maxRadius * Math.cos(angle)
      const y = centerY + maxRadius * Math.sin(angle)

      // 轴线
      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      ctx.lineTo(x, y)
      ctx.strokeStyle = '#E0E0E0'
      ctx.stroke()

      // 标签
      const labelX = centerX + (maxRadius + 30) * Math.cos(angle)
      const labelY = centerY + (maxRadius + 30) * Math.sin(angle)
      ctx.fillStyle = '#333'
      ctx.font = '14px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(this.dimensionNames[this.dimensions[i]], labelX, labelY)
    }

    // 绘制风险数据多边形
    ctx.beginPath()
    for (let i = 0; i < 6; i++) {
      const dimKey = this.dimensions[i]
      const dimension = this.option.risk_assessment.dimensions[dimKey]
      const score = dimension ? dimension.score : 0
      const radius = (score / 10) * maxRadius

      const angle = angleStep * i - Math.PI / 2
      const x = centerX + radius * Math.cos(angle)
      const y = centerY + radius * Math.sin(angle)

      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    }
    ctx.closePath()
    ctx.fillStyle = 'rgba(255, 152, 0, 0.2)'
    ctx.fill()
    ctx.strokeStyle = '#FF9800'
    ctx.lineWidth = 2
    ctx.stroke()

    // 绘制数据点
    for (let i = 0; i < 6; i++) {
      const dimKey = this.dimensions[i]
      const dimension = this.option.risk_assessment.dimensions[dimKey]
      const score = dimension ? dimension.score : 0
      const radius = (score / 10) * maxRadius

      const angle = angleStep * i - Math.PI / 2
      const x = centerX + radius * Math.cos(angle)
      const y = centerY + radius * Math.sin(angle)

      ctx.beginPath()
      ctx.arc(x, y, 5, 0, 2 * Math.PI)
      ctx.fillStyle = '#FF9800'
      ctx.fill()
      ctx.strokeStyle = '#FFFFFF'
      ctx.lineWidth = 2
      ctx.stroke()
    }
  }

  getRiskColor(risk: number): string {
    if (risk < 3) return '#4CAF50'
    if (risk < 5) return '#FFC107'
    if (risk < 7) return '#FF9800'
    return '#F44336'
  }

  getRiskLevelText(level: string): string {
    const labels: Record<string, string> = {
      'low': '低风险',
      'medium': '中风险',
      'high': '高风险',
      'critical': '极高风险'
    }
    return labels[level] || level
  }
}
