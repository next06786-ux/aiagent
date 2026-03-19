/**
 * 风险雷达图组件
 * 展示6大风险维度
 */
import { RiskAssessment, RiskDimension } from '../models/DecisionModels'

@Component
export struct RiskRadarChart {
  @State riskAssessment: RiskAssessment | null = null
  @State selectedDimension: string = ''

  // 6大风险维度
  private dimensions: string[] = [
    'health',    // 健康风险
    'finance',   // 财务风险
    'social',    // 社交风险
    'time',      // 时间风险
    'emotion',   // 情绪风险
    'learning'   // 学习风险
  ]

  private dimensionNames: Record<string, string> = {
    'health': '健康',
    'finance': '财务',
    'social': '社交',
    'time': '时间',
    'emotion': '情绪',
    'learning': '学习'
  }

  build() {
    Column() {
      // 标题
      Text('风险评估')
        .fontSize(24)
        .fontWeight(FontWeight.Bold)
        .margin({ bottom: 20 })

      if (this.riskAssessment) {
        // 总体风险
        Row() {
          Text('总体风险:')
            .fontSize(18)

          Text(`${this.riskAssessment.overall_risk.toFixed(1)}/10`)
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .fontColor(this.getRiskColor(this.riskAssessment.overall_risk / 10))
            .margin({ left: 10 })

          Text(this.getRiskLevelText(this.riskAssessment.overall_level))
            .fontSize(16)
            .fontColor(this.getRiskColor(this.riskAssessment.overall_risk / 10))
            .padding({ left: 10, right: 10, top: 5, bottom: 5 })
            .backgroundColor(this.getRiskColor(this.riskAssessment.overall_risk / 10) + '20')
            .borderRadius(5)
            .margin({ left: 10 })
        }
        .width('100%')
        .margin({ bottom: 30 })

        // 雷达图（使用Canvas绘制）
        Canvas(this.canvasContext)
          .width('100%')
          .height(300)
          .onReady(() => {
            this.drawRadarChart()
          })
          .margin({ bottom: 20 })

        // 维度详情列表
        List({ space: 10 }) {
          ForEach(this.dimensions, (dimKey: string) => {
            ListItem() {
              this.DimensionCard(dimKey, this.riskAssessment.dimensions[dimKey])
            }
          })
        }
        .width('100%')
        .layoutWeight(1)

        // 总体建议
        Column() {
          Text('总体建议')
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .margin({ bottom: 10 })

          ForEach(this.riskAssessment.recommendations, (rec: string) => {
            Text(rec)
              .fontSize(14)
              .lineHeight(22)
              .margin({ bottom: 5 })
          })
        }
        .width('100%')
        .padding(15)
        .backgroundColor('#FFF3E0')
        .borderRadius(10)
        .margin({ top: 20 })
      } else {
        Text('暂无风险评估数据')
          .fontSize(16)
          .fontColor('#999')
          .margin({ top: 50 })
      }
    }
    .width('100%')
    .height('100%')
    .padding(20)
    .backgroundColor('#F5F5F5')
  }

  @Builder
  DimensionCard(dimKey: string, dimension: RiskDimension) {
    Column() {
      // 维度名称和得分
      Row() {
        Text(dimension.name)
          .fontSize(16)
          .fontWeight(FontWeight.Bold)

        Blank()

        Text(`${dimension.score.toFixed(1)}/10`)
          .fontSize(16)
          .fontColor(this.getRiskColor(dimension.score / 10))
      }
      .width('100%')
      .margin({ bottom: 10 })

      // 风险等级进度条
      Progress({
        value: dimension.score * 10,
        total: 100,
        type: ProgressType.Linear
      })
        .width('100%')
        .color(this.getRiskColor(dimension.score / 10))
        .margin({ bottom: 10 })

      // 风险因素
      if (dimension.factors && dimension.factors.length > 0) {
        Column() {
          Text('风险因素:')
            .fontSize(12)
            .fontColor('#666')
            .margin({ bottom: 5 })

          ForEach(dimension.factors, (factor: string) => {
            Text(`• ${factor}`)
              .fontSize(12)
              .fontColor('#333')
              .margin({ bottom: 3 })
          })
        }
        .width('100%')
        .alignItems(HorizontalAlign.Start)
        .margin({ bottom: 10 })
      }

      // 缓解建议（折叠）
      if (this.selectedDimension === dimKey && dimension.mitigation) {
        Column() {
          Text('缓解建议:')
            .fontSize(12)
            .fontColor('#666')
            .margin({ bottom: 5 })

          ForEach(dimension.mitigation, (mit: string) => {
            Text(`✓ ${mit}`)
              .fontSize(12)
              .fontColor('#4CAF50')
              .margin({ bottom: 3 })
          })
        }
        .width('100%')
        .alignItems(HorizontalAlign.Start)
        .padding(10)
        .backgroundColor('#E8F5E9')
        .borderRadius(5)
      }

      // 展开/收起按钮
      Text(this.selectedDimension === dimKey ? '收起建议 ▲' : '查看建议 ▼')
        .fontSize(12)
        .fontColor('#007AFF')
        .alignSelf(ItemAlign.End)
        .onClick(() => {
          this.selectedDimension = this.selectedDimension === dimKey ? '' : dimKey
        })
    }
    .width('100%')
    .padding(15)
    .backgroundColor(Color.White)
    .borderRadius(10)
    .shadow({
      radius: 3,
      color: '#00000010',
      offsetX: 0,
      offsetY: 1
    })
  }

  // 绘制雷达图
  private canvasContext: CanvasRenderingContext2D | null = null

  drawRadarChart() {
    if (!this.canvasContext || !this.riskAssessment) return

    const ctx = this.canvasContext
    const centerX = 150
    const centerY = 150
    const maxRadius = 120
    const levels = 5 // 5个等级圈

    // 清空画布
    ctx.clearRect(0, 0, 300, 300)

    // 绘制背景圆圈
    for (let i = 1; i <= levels; i++) {
      const radius = (maxRadius / levels) * i
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI)
      ctx.strokeStyle = '#E0E0E0'
      ctx.lineWidth = 1
      ctx.stroke()
    }

    // 绘制6条轴线
    const angleStep = (2 * Math.PI) / 6
    for (let i = 0; i < 6; i++) {
      const angle = angleStep * i - Math.PI / 2
      const x = centerX + maxRadius * Math.cos(angle)
      const y = centerY + maxRadius * Math.sin(angle)

      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      ctx.lineTo(x, y)
      ctx.strokeStyle = '#E0E0E0'
      ctx.stroke()

      // 绘制维度标签
      const labelX = centerX + (maxRadius + 20) * Math.cos(angle)
      const labelY = centerY + (maxRadius + 20) * Math.sin(angle)
      ctx.fillStyle = '#333'
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(this.dimensionNames[this.dimensions[i]], labelX, labelY)
    }

    // 绘制风险数据多边形
    ctx.beginPath()
    for (let i = 0; i < 6; i++) {
      const dimKey = this.dimensions[i]
      const dimension = this.riskAssessment.dimensions[dimKey]
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
    ctx.fillStyle = 'rgba(255, 152, 0, 0.3)'
    ctx.fill()
    ctx.strokeStyle = '#FF9800'
    ctx.lineWidth = 2
    ctx.stroke()

    // 绘制数据点
    for (let i = 0; i < 6; i++) {
      const dimKey = this.dimensions[i]
      const dimension = this.riskAssessment.dimensions[dimKey]
      const score = dimension ? dimension.score : 0
      const radius = (score / 10) * maxRadius

      const angle = angleStep * i - Math.PI / 2
      const x = centerX + radius * Math.cos(angle)
      const y = centerY + radius * Math.sin(angle)

      ctx.beginPath()
      ctx.arc(x, y, 4, 0, 2 * Math.PI)
      ctx.fillStyle = '#FF9800'
      ctx.fill()
    }
  }

  getRiskColor(risk: number): string {
    if (risk < 0.3) return '#4CAF50'
    if (risk < 0.5) return '#FFC107'
    if (risk < 0.7) return '#FF9800'
    return '#F44336'
  }

  getRiskLevelText(level: string): string {
    const labels = {
      'low': '低风险',
      'medium': '中风险',
      'high': '高风险',
      'critical': '极高风险'
    }
    return labels[level] || level
  }
}
