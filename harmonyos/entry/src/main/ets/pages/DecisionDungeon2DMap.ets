/**
 * 决策副本2D地图 - 思维导图式可视化
 * 以2D平面展示决策路线，节点式布局
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { Theme } from '../common/Theme'

interface TimelineEvent {
  month: number
  event: string
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

interface NodePosition {
  x: number
  y: number
}

interface MapNode {
  id: string
  title: string
  description: string
  month: number
  impact: Record<string, number>
  probability: number
  position: NodePosition
  optionIndex: number
  color: string
}

@Entry
@Component
struct DecisionDungeon2DMap {
  @State dungeonData: DungeonData | null = null
  @State isLoading: boolean = false
  @State mapNodes: MapNode[] = []
  @State selectedNode: MapNode | null = null
  @State mapScale: number = 1.0
  @State offsetX: number = 0
  @State offsetY: number = 0
  @State showNodeDetail: boolean = false
  private dungeonId: string = ''
  private userId: string = 'default_user'
  private scroller: Scroller = new Scroller()
  private canvasWidth: number = 800
  private canvasHeight: number = 1200

  aboutToAppear() {
    const params = router.getParams() as Record<string, string>
    
    // 优先使用新的模拟数据
    if (params?.simulationData) {
      try {
        const simData = JSON.parse(params.simulationData) as Record<string, Object>
        this.dungeonData = this.convertSimulationToDungeon(simData, params.question || '')
        this.generateMapNodes()
      } catch (error) {
        console.error('解析模拟数据失败:', (error as Error).message)
      }
    } else if (params?.dungeonId) {
      // 降级：使用旧的副本ID加载
      this.dungeonId = params.dungeonId
      this.loadDungeonData()
    }
    
    if (params?.userId) {
      this.userId = params.userId
    }
  }

  // 将模拟结果转换为副本数据格式
  private convertSimulationToDungeon(simData: Record<string, Object>, question: string): DungeonData {
    const simulationId = simData.simulation_id as string
    const userId = simData.user_id as string
    const options = simData.options as DungeonOption[]
    const recommendation = simData.recommendation as string
    const createdAt = simData.created_at as string
    
    return {
      dungeon_id: simulationId || 'temp_dungeon',
      user_id: userId || this.userId,
      title: question,
      description: '基于AI分析的决策模拟',
      options: options,
      recommendation: recommendation || '',
      created_at: createdAt || new Date().toISOString()
    }
  }

  private async loadDungeonData() {
    this.isLoading = true
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        ApiConfig.getApiUrl(`/api/decision/dungeon/${this.dungeonId}`),
        {
          method: http.RequestMethod.GET,
          header: { 'Content-Type': 'application/json' },
          connectTimeout: 30000,
          readTimeout: 30000
        }
      )
      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if (result.code === 200 && result.data) {
          this.dungeonData = result.data as DungeonData
          this.generateMapNodes()
        }
      }
    } catch (error) {
      console.error('Error loading dungeon:', (error as Error).message)
    }
    this.isLoading = false
  }

  private generateMapNodes() {
    if (!this.dungeonData) return

    const nodes: MapNode[] = []
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    const startY = 120
    const verticalSpacing = 160
    const optionCount = this.dungeonData.options.length

    // 添加起点节点（中心）
    nodes.push({
      id: 'start',
      title: '决策起点',
      description: this.dungeonData.title,
      month: 0,
      impact: {},
      probability: 1.0,
      position: { x: this.canvasWidth / 2, y: startY },
      optionIndex: -1,
      color: '#9C27B0'
    })

    // 为每个选项生成分支节点（思维导图式布局）
    this.dungeonData.options.forEach((option, optionIndex) => {
      // 计算每个选项分支的X位置（均匀分布）
      const sectionWidth = this.canvasWidth / optionCount
      const baseX = sectionWidth * optionIndex + sectionWidth / 2
      const color = colors[optionIndex % colors.length]

      // 选项起始节点（第一层分支）
      const startNodeY = startY + verticalSpacing
      nodes.push({
        id: `option_${optionIndex}_start`,
        title: option.title,
        description: option.description,
        month: 0,
        impact: {},
        probability: 1.0,
        position: { x: baseX, y: startNodeY },
        optionIndex: optionIndex,
        color: color
      })

      // 时间线事件节点（蛇形布局）
      option.timeline.forEach((event, eventIndex) => {
        // 蛇形偏移：奇数向左，偶数向右
        const horizontalOffset = (eventIndex % 2 === 0 ? -60 : 60)
        const nodeX = baseX + horizontalOffset
        const nodeY = startNodeY + verticalSpacing * (eventIndex + 1)

        nodes.push({
          id: `option_${optionIndex}_event_${eventIndex}`,
          title: `第${event.month}月`,
          description: event.event,
          month: event.month,
          impact: event.impact,
          probability: event.probability,
          position: { x: nodeX, y: nodeY },
          optionIndex: optionIndex,
          color: color
        })
      })

      // 结果节点（最后一个节点）
      const lastEventIndex = option.timeline.length
      nodes.push({
        id: `option_${optionIndex}_result`,
        title: '结果',
        description: `综合得分: ${option.final_score.toFixed(1)}`,
        month: 12,
        impact: {},
        probability: 1.0,
        position: {
          x: baseX,
          y: startNodeY + verticalSpacing * (lastEventIndex + 1)
        },
        optionIndex: optionIndex,
        color: color
      })
    })

    this.mapNodes = nodes
    console.info(`生成了 ${nodes.length} 个地图节点`)
  }

  private getImpactIcon(key: string): string {
    const icons: Record<string, string> = {
      '健康': '💪', '财务': '💰', '社交': '👥',
      '情绪': '😊', '学习': '📚', '时间': '⏰'
    }
    return icons[key] || '📊'
  }

  build() {
    Stack() {
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('#F5F7FA')

      Column() {
        // 顶部导航
        Row() {
          Button({ type: ButtonType.Circle }) {
            Text('←')
              .fontSize(24)
              .fontColor('#1A1A1A')
              .fontWeight(600)
          }
          .width(40)
          .height(40)
          .backgroundColor('rgba(0,0,0,0)')
          .onClick(() => router.back())

          Text('决策地图')
            .fontSize(20)
            .fontWeight(700)
            .fontColor('#1A1A1A')
            .layoutWeight(1)
            .margin({ left: 12 })

          // 缩放控制
          Row({ space: 8 }) {
            Button('-')
              .width(36)
              .height(36)
              .fontSize(20)
              .fontColor('#007AFF')
              .backgroundColor('rgba(0,122,255,0.1)')
              .onClick(() => {
                this.mapScale = Math.max(0.5, this.mapScale - 0.1)
              })

            Text(`${(this.mapScale * 100).toFixed(0)}%`)
              .fontSize(14)
              .fontColor('#666')
              .width(50)
              .textAlign(TextAlign.Center)

            Button('+')
              .width(36)
              .height(36)
              .fontSize(20)
              .fontColor('#007AFF')
              .backgroundColor('rgba(0,122,255,0.1)')
              .onClick(() => {
                this.mapScale = Math.min(2.0, this.mapScale + 0.1)
              })
          }
          .margin({ right: 8 })

          // 切换到列表视图
          Button('列表')
            .height(36)
            .fontSize(14)
            .fontWeight(600)
            .fontColor('#007AFF')
            .backgroundColor('rgba(0,122,255,0.1)')
            .onClick(() => {
              router.back()
            })
        }
        .width('100%')
        .height(56)
        .padding({ left: 16, right: 16 })
        .backgroundColor('rgba(255,255,255,0.95)')
        .backdropBlur(20)

        // 图例
        if (!this.isLoading && this.dungeonData) {
          Row({ space: 16 }) {
            Row({ space: 6 }) {
              Circle({ width: 12, height: 12 })
                .fill('#9C27B0')
              Text('起点')
                .fontSize(12)
                .fontColor('#666')
            }
            
            Row({ space: 6 }) {
              Circle({ width: 12, height: 12 })
                .fill('#FF6B6B')
              Text('选项')
                .fontSize(12)
                .fontColor('#666')
            }
            
            Row({ space: 6 }) {
              Circle({ width: 12, height: 12 })
                .fill('#4ECDC4')
              Text('事件')
                .fontSize(12)
                .fontColor('#666')
            }
            
            Row({ space: 6 }) {
              Circle({ width: 12, height: 12 })
                .fill('#45B7D1')
              Text('结果')
                .fontSize(12)
                .fontColor('#666')
            }
          }
          .width('100%')
          .padding({ left: 16, right: 16, top: 8, bottom: 8 })
          .backgroundColor('rgba(255,255,255,0.9)')
          .justifyContent(FlexAlign.SpaceAround)
        }

        if (this.isLoading) {
          Column() {
            LoadingProgress()
              .width(40)
              .height(40)
              .color('#007AFF')
            Text('正在生成地图...')
              .fontSize(14)
              .fontColor('#999')
              .margin({ top: 12 })
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        } else {
          this.MapCanvas()
        }
      }
      .width('100%')
      .height('100%')

      // 节点详情弹窗
      if (this.showNodeDetail && this.selectedNode) {
        this.NodeDetailPanel()
      }
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  MapCanvas() {
    Scroll(this.scroller) {
      Stack() {
        // 背景和节点层
        Column() {
          Stack() {
            // 节点层
            ForEach(this.mapNodes, (node: MapNode) => {
              this.MapNodeView(node)
            })
          }
          .width(this.canvasWidth)
          .height(this.canvasHeight)
        }
        .width(this.canvasWidth)
        .height(this.canvasHeight)
        .backgroundColor('#FAFBFC')
        .scale({ x: this.mapScale, y: this.mapScale })
        .translate({ x: this.offsetX, y: this.offsetY })
      }
      .width('100%')
      .height('100%')
    }
    .layoutWeight(1)
    .scrollBar(BarState.Auto)
    .edgeEffect(EdgeEffect.Spring)
  }

  @Builder
  MapNodeView(node: MapNode) {
    Column({ space: 6 }) {
      // 节点卡片
      Column({ space: 8 }) {
        // 节点圆圈或图标
        Stack() {
          if (node.id === 'start') {
            // 起点节点 - 渐变圆圈
            Circle({ width: 70, height: 70 })
              .fill('#667eea')
              .opacity(0.2)
            Circle({ width: 60, height: 60 })
              .linearGradient({
                angle: 135,
                colors: [['#667eea', 0.0], ['#764ba2', 1.0]]
              })
            
            // 使用文字代替 emoji
            Text('起点')
              .fontSize(14)
              .fontWeight(700)
              .fontColor(Color.White)
          } else if (node.id.includes('_result')) {
            // 结果节点 - 渐变圆圈
            Circle({ width: 65, height: 65 })
              .fill(node.color)
              .opacity(0.15)
            Circle({ width: 55, height: 55 })
              .fill(node.color)
            
            Text('结果')
              .fontSize(14)
              .fontWeight(700)
              .fontColor(Color.White)
          } else if (node.id.includes('_start')) {
            // 选项起始节点 - 渐变方形
            Column()
              .width(60)
              .height(60)
              .backgroundColor(node.color)
              .opacity(0.15)
              .borderRadius(12)
            Column()
              .width(50)
              .height(50)
              .linearGradient({
                angle: 135,
                colors: [[node.color, 0.0], [node.color, 1.0]]
              })
              .borderRadius(10)
            
            Text('选项')
              .fontSize(14)
              .fontWeight(700)
              .fontColor(Color.White)
          } else {
            // 事件节点 - 渐变圆形
            Circle({ width: 55, height: 55 })
              .fill(node.color)
              .opacity(0.2)
            Circle({ width: 45, height: 45 })
              .fill(node.color)
            if (node.month > 0) {
              Text(`${node.month}`)
                .fontSize(16)
                .fontWeight(700)
                .fontColor(Color.White)
            }
          }
        }

        // 节点标题卡片
        Column({ space: 4 }) {
          Text(node.title)
            .fontSize(13)
            .fontWeight(700)
            .fontColor('#1A1A1A')
            .maxLines(2)
            .textOverflow({ overflow: TextOverflow.Ellipsis })
            .textAlign(TextAlign.Center)

          if (node.probability < 1.0) {
            Text(`${(node.probability * 100).toFixed(0)}%`)
              .fontSize(11)
              .fontColor('#666')
          }
        }
        .width(110)
        .padding(8)
        .backgroundColor(Color.White)
        .borderRadius(8)
        .shadow({ radius: 4, color: 'rgba(0,0,0,0.1)', offsetY: 2 })
      }
    }
    .width(120)
    .position({ x: node.position.x - 60, y: node.position.y - 35 })
    .onClick(() => {
      this.selectedNode = node
      this.showNodeDetail = true
    })
  }

  @Builder
  NodeDetailPanel() {
    Column() {
      // 遮罩层
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('rgba(0,0,0,0.5)')
        .onClick(() => {
          this.showNodeDetail = false
        })

      // 详情面板
      Column({ space: 16 }) {
        // 头部
        Row() {
          Column({ space: 4 }) {
            Text(this.selectedNode!.title)
              .fontSize(20)
              .fontWeight(700)
              .fontColor('#1A1A1A')

            if (this.selectedNode!.month > 0) {
              Text(`第${this.selectedNode!.month}月`)
                .fontSize(14)
                .fontColor('#666')
            }
          }
          .alignItems(HorizontalAlign.Start)
          .layoutWeight(1)

          Button({ type: ButtonType.Circle }) {
            Text('×')
              .fontSize(24)
              .fontColor('#666')
          }
          .width(36)
          .height(36)
          .backgroundColor('rgba(0,0,0,0)')
          .onClick(() => {
            this.showNodeDetail = false
          })
        }
        .width('100%')

        // 描述
        Text(this.selectedNode!.description)
          .fontSize(14)
          .fontColor('#333')
          .lineHeight(22)

        // 概率
        if (this.selectedNode!.probability < 1.0) {
          Row({ space: 8 }) {
            Text('发生概率:')
              .fontSize(13)
              .fontColor('#666')

            Text(`${(this.selectedNode!.probability * 100).toFixed(0)}%`)
              .fontSize(16)
              .fontWeight(700)
              .fontColor('#007AFF')
          }
          .width('100%')
        }

        // 影响指标
        if (Object.keys(this.selectedNode!.impact).length > 0) {
          Column({ space: 8 }) {
            Text('影响指标')
              .fontSize(14)
              .fontWeight(600)
              .fontColor('#1A1A1A')

            Flex({ wrap: FlexWrap.Wrap }) {
              ForEach(Object.keys(this.selectedNode!.impact), (key: string) => {
                if (Math.abs(this.selectedNode!.impact[key]) > 0.01) {
                  Text(`${this.getImpactIcon(key)} ${key} ${this.selectedNode!.impact[key] > 0 ? '+' : ''}${(this.selectedNode!.impact[key] * 100).toFixed(0)}%`)
                    .fontSize(12)
                    .fontColor(this.selectedNode!.impact[key] > 0 ? '#4CAF50' : '#FF3B30')
                    .padding({ left: 10, right: 10, top: 6, bottom: 6 })
                    .backgroundColor(this.selectedNode!.impact[key] > 0 ? 'rgba(76,175,80,0.1)' : 'rgba(255,59,48,0.1)')
                    .borderRadius(8)
                    .margin({ right: 8, bottom: 8 })
                }
              })
            }
          }
          .width('100%')
          .alignItems(HorizontalAlign.Start)
        }
      }
      .width('90%')
      .padding(20)
      .backgroundColor(Color.White)
      .borderRadius(20)
      .shadow({ radius: 20, color: 'rgba(0,0,0,0.2)', offsetY: 10 })
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .alignItems(HorizontalAlign.Center)
  }
}
