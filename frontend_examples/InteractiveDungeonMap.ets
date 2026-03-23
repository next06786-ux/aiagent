/**
 * 交互式副本地图 - 带有路径连接和动画效果
 * 类似游戏地图的可视化闯关系统
 */
import { DecisionOption } from '../models/DecisionModels'

interface MapNode {
  id: number
  x: number // 相对位置 0-100
  y: number // 相对位置 0-100
  name: string
  difficulty: 'easy' | 'normal' | 'hard' | 'nightmare'
  status: 'locked' | 'unlocked' | 'completed' | 'current'
  connections: number[] // 连接到的节点ID
  rewards: string[]
  universeType: string
  icon: string
}

@Component
export struct InteractiveDungeonMap {
  @State nodes: MapNode[] = []
  @State selectedNode: number | null = null
  @State hoveredNode: number | null = null
  @State mapScale: number = 1.0
  @State mapOffsetX: number = 0
  @State mapOffsetY: number = 0
  @State animationFrame: number = 0
  @State showPathAnimation: boolean = true

  aboutToAppear() {
    this.initializeMapNodes()
    this.startPathAnimation()
  }

  build() {
    Stack() {
      // 背景星空效果
      this.StarfieldBackground()

      // 地图容器
      Column() {
        // 顶部工具栏
        this.MapToolbar()

        // 地图画布
        Stack() {
          // 连接线层
          Canvas(this.canvasContext)
            .width('100%')
            .height('100%')
            .onReady(() => {
              this.drawConnections()
            })

          // 节点层
          Stack() {
            ForEach(this.nodes, (node: MapNode) => {
              this.MapNode(node)
            })
          }
          .width('100%')
          .height('100%')
        }
        .layoutWeight(1)
        .backgroundColor('rgba(0, 0, 0, 0.3)')
        .borderRadius(10)
        .clip(true)
      }
      .width('100%')
      .height('100%')
      .padding(15)

      // 节点详情面板
      if (this.selectedNode !== null) {
        this.NodeDetailPanel()
      }
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  StarfieldBackground() {
    Column()
      .width('100%')
      .height('100%')
      .backgroundColor('#0A0E1A')
      .backgroundImage($r('app.media.starfield'))
      .backgroundImageSize(ImageSize.Cover)
  }

  @Builder
  MapToolbar() {
    Row({ space: 10 }) {
      Text('🗺️ 平行宇宙副本地图')
        .fontSize(20)
        .fontWeight(FontWeight.Bold)
        .fontColor('#FFFFFF')

      Blank()

      // 缩放控制
      Button('-')
        .width(36)
        .height(36)
        .fontSize(20)
        .backgroundColor('#2A2E3A')
        .fontColor('#FFFFFF')
        .onClick(() => {
          this.mapScale = Math.max(0.5, this.mapScale - 0.1)
        })

      Text(`${Math.round(this.mapScale * 100)}%`)
        .fontSize(14)
        .fontColor('#AAAAAA')
        .width(50)
        .textAlign(TextAlign.Center)

      Button('+')
        .width(36)
        .height(36)
        .fontSize(20)
        .backgroundColor('#2A2E3A')
        .fontColor('#FFFFFF')
        .onClick(() => {
          this.mapScale = Math.min(2.0, this.mapScale + 0.1)
        })

      // 重置视图
      Button('🎯 重置')
        .height(36)
        .fontSize(14)
        .backgroundColor('#2A2E3A')
        .fontColor('#FFFFFF')
        .onClick(() => {
          this.mapScale = 1.0
          this.mapOffsetX = 0
          this.mapOffsetY = 0
        })
    }
    .width('100%')
    .padding(15)
    .backgroundColor('#1A1E2E')
    .borderRadius(10)
    .margin({ bottom: 10 })
  }

  @Builder
  MapNode(node: MapNode) {
    Stack() {
      // 节点光晕效果
      if (node.status === 'current' || this.hoveredNode === node.id) {
        Column()
          .width(100)
          .height(100)
          .backgroundColor(this.getNodeGlowColor(node))
          .borderRadius(50)
          .blur(20)
          .opacity(0.6)
      }

      // 节点主体
      Column({ space: 6 }) {
        // 图标
        Text(node.icon)
          .fontSize(32)
          .opacity(node.status === 'locked' ? 0.3 : 1.0)

        // 名称
        Text(node.name)
          .fontSize(12)
          .fontColor('#FFFFFF')
          .maxLines(2)
          .textAlign(TextAlign.Center)
          .width(80)
          .opacity(node.status === 'locked' ? 0.5 : 1.0)

        // 状态指示器
        if (node.status === 'completed') {
          Text('✓')
            .fontSize(16)
            .fontColor('#4CAF50')
            .fontWeight(FontWeight.Bold)
        } else if (node.status === 'current') {
          Text('▶')
            .fontSize(14)
            .fontColor('#00D4FF')
        } else if (node.status === 'locked') {
          Text('🔒')
            .fontSize(14)
        }
      }
      .width(90)
      .height(90)
      .padding(8)
      .backgroundColor(this.getNodeBackgroundColor(node))
      .borderRadius(45)
      .border({
        width: 3,
        color: this.getNodeBorderColor(node)
      })
      .shadow({
        radius: 15,
        color: this.getNodeShadowColor(node),
        offsetX: 0,
        offsetY: 0
      })
      .onClick(() => {
        if (node.status !== 'locked') {
          this.selectedNode = node.id
        }
      })
      .onTouch((event: TouchEvent) => {
        if (event.type === TouchType.Down) {
          this.hoveredNode = node.id
        } else if (event.type === TouchType.Up) {
          this.hoveredNode = null
        }
      })
    }
    .position({
      x: `${node.x}%`,
      y: `${node.y}%`
    })
    .scale({
      x: this.mapScale,
      y: this.mapScale
    })
  }

  @Builder
  NodeDetailPanel() {
    Column() {
      Blank()

      Column({ space: 15 }) {
        let node = this.nodes.find(n => n.id === this.selectedNode)
        if (node) {
          // 关闭按钮
          Row() {
            Text(node.icon + ' ' + node.name)
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .fontColor('#FFFFFF')

            Blank()

            Button('✕')
              .width(32)
              .height(32)
              .fontSize(18)
              .backgroundColor('#2A2E3A')
              .fontColor('#FFFFFF')
              .onClick(() => {
                this.selectedNode = null
              })
          }
          .width('100%')

          // 难度和状态
          Row({ space: 10 }) {
            Text(`难度: ${this.getDifficultyLabel(node.difficulty)}`)
              .fontSize(14)
              .fontColor(this.getDifficultyColor(node.difficulty))
              .padding({ left: 10, right: 10, top: 5, bottom: 5 })
              .backgroundColor(this.getDifficultyBgColor(node.difficulty))
              .borderRadius(5)

            Text(`状态: ${this.getStatusLabel(node.status)}`)
              .fontSize(14)
              .fontColor(this.getStatusColor(node.status))
              .padding({ left: 10, right: 10, top: 5, bottom: 5 })
              .backgroundColor('#2A2E3A')
              .borderRadius(5)
          }

          // 宇宙类型
          Text(`宇宙类型: ${node.universeType}`)
            .fontSize(14)
            .fontColor('#AAAAAA')

          // 奖励列表
          Column({ space: 8 }) {
            Text('副本奖励:')
              .fontSize(14)
              .fontColor('#FFFFFF')
              .fontWeight(FontWeight.Bold)

            ForEach(node.rewards, (reward: string) => {
              Row({ space: 8 }) {
                Text('⭐')
                  .fontSize(14)

                Text(reward)
                  .fontSize(13)
                  .fontColor('#CCCCCC')
              }
            })
          }
          .alignItems(HorizontalAlign.Start)
          .width('100%')

          // 操作按钮
          if (node.status === 'unlocked' || node.status === 'current') {
            Button('🚀 开始挑战')
              .width('100%')
              .height(44)
              .fontSize(16)
              .fontColor('#FFFFFF')
              .backgroundColor('#00D4FF')
              .borderRadius(8)
              .onClick(() => {
                // 开始副本逻辑
              })
          } else if (node.status === 'completed') {
            Row({ space: 10 }) {
              Button('📊 查看记录')
                .layoutWeight(1)
                .height(40)
                .fontSize(14)
                .fontColor('#FFFFFF')
                .backgroundColor('#2A2E3A')
                .borderRadius(8)

              Button('🔄 重新挑战')
                .layoutWeight(1)
                .height(40)
                .fontSize(14)
                .fontColor('#FFFFFF')
                .backgroundColor('#FF9800')
                .borderRadius(8)
            }
            .width('100%')
          }
        }
      }
      .width('90%')
      .padding(20)
      .backgroundColor('#1A1E2E')
      .borderRadius(15)
      .shadow({
        radius: 20,
        color: '#00000080',
        offsetX: 0,
        offsetY: 10
      })
    }
    .width('100%')
    .height('100%')
    .backgroundColor('rgba(0, 0, 0, 0.7)')
    .onClick(() => {
      this.selectedNode = null
    })
  }

  // Canvas绘制连接线
  private canvasContext = new RenderingContext()

  private drawConnections() {
    const ctx = this.canvasContext
    ctx.clearRect(0, 0, ctx.width, ctx.height)

    this.nodes.forEach(node => {
      node.connections.forEach(targetId => {
        const targetNode = this.nodes.find(n => n.id === targetId)
        if (targetNode) {
          this.drawPath(ctx, node, targetNode)
        }
      })
    })
  }

  private drawPath(ctx: CanvasRenderingContext2D, from: MapNode, to: MapNode) {
    const fromX = (from.x / 100) * ctx.width
    const fromY = (from.y / 100) * ctx.height
    const toX = (to.x / 100) * ctx.width
    const toY = (to.y / 100) * ctx.height

    // 绘制路径
    ctx.beginPath()
    ctx.moveTo(fromX, fromY)

    // 贝塞尔曲线
    const controlX = (fromX + toX) / 2
    const controlY = Math.min(fromY, toY) - 50
    ctx.quadraticCurveTo(controlX, controlY, toX, toY)

    // 路径样式
    if (from.status === 'completed' && to.status !== 'locked') {
      ctx.strokeStyle = '#00D4FF'
      ctx.lineWidth = 3
      ctx.setLineDash([])
    } else {
      ctx.strokeStyle = '#2A2E3A'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 5])
    }

    ctx.stroke()

    // 动画效果
    if (this.showPathAnimation && from.status === 'completed') {
      this.drawPathParticle(ctx, fromX, fromY, toX, toY)
    }
  }

  private drawPathParticle(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number) {
    const progress = (this.animationFrame % 100) / 100
    const x = x1 + (x2 - x1) * progress
    const y = y1 + (y2 - y1) * progress

    ctx.beginPath()
    ctx.arc(x, y, 4, 0, Math.PI * 2)
    ctx.fillStyle = '#00D4FF'
    ctx.fill()
  }

  // 初始化地图节点
  private initializeMapNodes() {
    this.nodes = [
      // 第一层 - 起点
      {
        id: 1,
        x: 50,
        y: 10,
        name: '起始之地',
        difficulty: 'easy',
        status: 'completed',
        connections: [2, 3],
        rewards: ['新手礼包', '经验 +100'],
        universeType: '原始宇宙',
        icon: '🌟'
      },
      // 第二层 - 分支
      {
        id: 2,
        x: 30,
        y: 25,
        name: '技术之路',
        difficulty: 'normal',
        status: 'completed',
        connections: [4, 5],
        rewards: ['技术徽章', '技能点 +5'],
        universeType: '科技宇宙',
        icon: '⚙️'
      },
      {
        id: 3,
        x: 70,
        y: 25,
        name: '创意之路',
        difficulty: 'normal',
        status: 'current',
        connections: [5, 6],
        rewards: ['创意徽章', '灵感 +10'],
        universeType: '艺术宇宙',
        icon: '🎨'
      },
      // 第三层 - 中期挑战
      {
        id: 4,
        x: 20,
        y: 45,
        name: '深度学习',
        difficulty: 'hard',
        status: 'unlocked',
        connections: [7],
        rewards: ['专家认证', '知识库'],
        universeType: '学术宇宙',
        icon: '📚'
      },
      {
        id: 5,
        x: 50,
        y: 45,
        name: '团队协作',
        difficulty: 'hard',
        status: 'unlocked',
        connections: [7, 8],
        rewards: ['领导力 +20', '团队加成'],
        universeType: '社交宇宙',
        icon: '👥'
      },
      {
        id: 6,
        x: 80,
        y: 45,
        name: '创新突破',
        difficulty: 'hard',
        status: 'locked',
        connections: [8],
        rewards: ['创新奖励', '突破徽章'],
        universeType: '未来宇宙',
        icon: '💡'
      },
      // 第四层 - 高级挑战
      {
        id: 7,
        x: 35,
        y: 65,
        name: '市场竞争',
        difficulty: 'nightmare',
        status: 'locked',
        connections: [9],
        rewards: ['竞争力 +50', '市场洞察'],
        universeType: '商业宇宙',
        icon: '📈'
      },
      {
        id: 8,
        x: 65,
        y: 65,
        name: '资源整合',
        difficulty: 'nightmare',
        status: 'locked',
        connections: [9],
        rewards: ['资源大师', '效率 +100%'],
        universeType: '战略宇宙',
        icon: '💎'
      },
      // 第五层 - 终极挑战
      {
        id: 9,
        x: 50,
        y: 85,
        name: '宇宙融合',
        difficulty: 'nightmare',
        status: 'locked',
        connections: [],
        rewards: ['终极成就', '宇宙之心', '无限可能'],
        universeType: '多元宇宙',
        icon: '🌌'
      }
    ]
  }

  // 启动路径动画
  private startPathAnimation() {
    setInterval(() => {
      this.animationFrame++
      if (this.showPathAnimation) {
        this.drawConnections()
      }
    }, 50)
  }

  // 辅助方法
  private getNodeBackgroundColor(node: MapNode): string {
    if (node.status === 'locked') return '#1A1E2E'
    if (node.status === 'completed') return '#1B3A1B'
    if (node.status === 'current') return '#1A2E3E'
    return '#2A2E3A'
  }

  private getNodeBorderColor(node: MapNode): string {
    if (node.status === 'locked') return '#2A2E3A'
    if (node.status === 'completed') return '#4CAF50'
    if (node.status === 'current') return '#00D4FF'
    return '#00D4FF'
  }

  private getNodeShadowColor(node: MapNode): string {
    if (node.status === 'completed') return '#4CAF5080'
    if (node.status === 'current') return '#00D4FF80'
    return '#00000040'
  }

  private getNodeGlowColor(node: MapNode): string {
    if (node.status === 'completed') return '#4CAF50'
    if (node.status === 'current') return '#00D4FF'
    return '#FFFFFF'
  }

  private getDifficultyLabel(difficulty: string): string {
    const labels: Record<string, string> = {
      'easy': '简单',
      'normal': '普通',
      'hard': '困难',
      'nightmare': '噩梦'
    }
    return labels[difficulty] || difficulty
  }

  private getDifficultyColor(difficulty: string): string {
    const colors: Record<string, string> = {
      'easy': '#4CAF50',
      'normal': '#2196F3',
      'hard': '#FF9800',
      'nightmare': '#F44336'
    }
    return colors[difficulty] || '#FFFFFF'
  }

  private getDifficultyBgColor(difficulty: string): string {
    const colors: Record<string, string> = {
      'easy': '#1B5E20',
      'normal': '#0D47A1',
      'hard': '#E65100',
      'nightmare': '#B71C1C'
    }
    return colors[difficulty] || '#2A2E3A'
  }

  private getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      'locked': '已锁定',
      'unlocked': '可挑战',
      'completed': '已完成',
      'current': '进行中'
    }
    return labels[status] || status
  }

  private getStatusColor(status: string): string {
    const colors: Record<string, string> = {
      'locked': '#888888',
      'unlocked': '#00D4FF',
      'completed': '#4CAF50',
      'current': '#FFC107'
    }
    return colors[status] || '#FFFFFF'
  }
}






