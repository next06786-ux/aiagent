/**
 * 涌现模式可视化组件
 * 使用Canvas绘制涌现模式的关系图
 */

interface PatternNode {
  id: string
  label: string
  x: number
  y: number
  radius: number
  color: string
  type: string
}

interface PatternEdge {
  from: string
  to: string
  strength: number
  color: string
}

interface PatternData {
  id: string
  type: string
  domains: string[]
  impact_score: number
}

@Component
export struct EmergenceVisualization {
  @Prop patterns: PatternData[] = []
  @State canvasContext: CanvasRenderingContext2D | null = null
  @State nodes: PatternNode[] = []
  @State edges: PatternEdge[] = []

  aboutToAppear() {
    this.initializeVisualization()
  }

  initializeVisualization() {
    // 根据模式类型创建节点
    const typeColors: Record<string, string> = {
      'cascade': '#FF6B6B',
      'feedback_loop': '#4ECDC4',
      'tipping_point': '#FFE66D',
      'synergy': '#95E1D3'
    }

    const typeLabels: Record<string, string> = {
      'cascade': '级联',
      'feedback_loop': '反馈',
      'tipping_point': '临界',
      'synergy': '协同'
    }

    // 创建节点
    this.nodes = this.patterns.map((pattern: PatternData, index: number): PatternNode => {
      const angle = (index / this.patterns.length) * 2 * Math.PI
      const radius = 80
      const centerX = 150
      const centerY = 150

      const node: PatternNode = {
        id: pattern.id,
        label: typeLabels[pattern.type] || '未知',
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        radius: 20 + pattern.impact_score * 10,
        color: typeColors[pattern.type] || '#999999',
        type: pattern.type
      }
      return node
    })

    // 创建边（连接相关的模式）
    this.edges = []
    for (let i: number = 0; i < this.nodes.length; i++) {
      for (let j: number = i + 1; j < this.nodes.length; j++) {
        // 如果两个模式共享领域，则连接
        const pattern1: PatternData = this.patterns[i]
        const pattern2: PatternData = this.patterns[j]
        const sharedDomains: number = pattern1.domains.filter((d: string) =>
          pattern2.domains.includes(d)
        ).length

        if (sharedDomains > 0) {
          const edge: PatternEdge = {
            from: pattern1.id,
            to: pattern2.id,
            strength: sharedDomains / Math.max(pattern1.domains.length, pattern2.domains.length),
            color: '#CCCCCC'
          }
          this.edges.push(edge)
        }
      }
    }
  }

  drawVisualization(context: CanvasRenderingContext2D): void {
    const width: number = 300
    const height: number = 300

    // 清空画布
    context.fillStyle = '#FFFFFF'
    context.fillRect(0, 0, width, height)

    // 绘制边
    context.strokeStyle = '#CCCCCC'
    context.lineWidth = 1
    for (const edge of this.edges) {
      const fromNode: PatternNode | undefined = this.nodes.find((n: PatternNode) => n.id === edge.from)
      const toNode: PatternNode | undefined = this.nodes.find((n: PatternNode) => n.id === edge.to)

      if (fromNode && toNode) {
        context.beginPath()
        context.moveTo(fromNode.x, fromNode.y)
        context.lineTo(toNode.x, toNode.y)
        context.stroke()
      }
    }

    // 绘制节点
    for (const node of this.nodes) {
      // 节点圆形
      context.fillStyle = node.color
      context.beginPath()
      context.arc(node.x, node.y, node.radius, 0, 2 * Math.PI)
      context.fill()

      // 节点边框
      context.strokeStyle = '#FFFFFF'
      context.lineWidth = 2
      context.stroke()

      // 节点标签
      context.fillStyle = '#FFFFFF'
      context.font = 'bold 12px Arial'
      context.textAlign = 'center'
      context.textBaseline = 'middle'
      context.fillText(node.label, node.x, node.y)
    }

    // 绘制中心标签
    context.fillStyle = '#333333'
    context.font = 'bold 14px Arial'
    context.textAlign = 'center'
    context.textBaseline = 'middle'
    context.fillText('涌现模式网络', width / 2, 20)
  }

  build() {
    Column() {
      Canvas(this.canvasContext)
        .width('100%')
        .height(300)
        .backgroundColor('#F9F9F9')
        .border({
          width: 1,
          color: '#E0E0E0'
        })
        .borderRadius(8)
        .onReady(() => {
          const context = this.canvasContext
          if (context) {
            this.drawVisualization(context)
          }
        })

      // 图例
      Row() {
        Row() {
          Circle({ width: 12, height: 12 })
            .fill('#FF6B6B')

          Text('级联效应')
            .fontSize(12)
            .fontColor('#666666')
            .margin({ left: 6 })
        }
        .margin({ right: 16 })

        Row() {
          Circle({ width: 12, height: 12 })
            .fill('#4ECDC4')

          Text('反馈环')
            .fontSize(12)
            .fontColor('#666666')
            .margin({ left: 6 })
        }
        .margin({ right: 16 })

        Row() {
          Circle({ width: 12, height: 12 })
            .fill('#FFE66D')

          Text('临界点')
            .fontSize(12)
            .fontColor('#666666')
            .margin({ left: 6 })
        }
        .margin({ right: 16 })

        Row() {
          Circle({ width: 12, height: 12 })
            .fill('#95E1D3')

          Text('协同效应')
            .fontSize(12)
            .fontColor('#666666')
            .margin({ left: 6 })
        }
      }
      .width('100%')
      .padding(12)
      .backgroundColor('#F5F5F5')
      .borderRadius(6)
      .margin({ top: 12 })
    }
    .width('100%')
    .padding(16)
  }
}

