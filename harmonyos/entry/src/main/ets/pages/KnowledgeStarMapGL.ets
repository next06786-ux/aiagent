/**
 * 知识星图 - OpenGL ES GPU渲染版本
 * 使用XComponent + Native C++ 实现高性能3D渲染
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import image from '@ohos.multimedia.image'
import display from '@ohos.display'
import { ApiConfig } from '../config/ApiConfig'
import { Theme } from '../common/Theme'
import { SimpleIcon } from '../components/IconRenderer'
import { getAuthService } from '../service/AuthService'

// Native模块接口
interface StarMapNative {
  setNodes(nodes: NativeNode[]): void
  setLinks(links: NativeLink[]): void
  setRotation(rotX: number, rotY: number): void
  setZoom(zoom: number): void
  resetTarget(): void  // 重置相机目标点到原点
  renderFrame(): void
  updateAnimation(deltaTime: number): void
  updateForceLayout(): void
  hitTest(x: number, y: number): number
  selectNode(index: number): void
  focusOnNode(index: number): void  // 新增：聚焦到节点
  getNodeScreenPositions(): NodeScreenPos[]
  getNodeRelations(nodeIdx: number): NodeRelation[]
  setTextTexture(nodeIdx: number, pixels: ArrayBuffer, width: number, height: number): void
  destroyRenderer(): boolean  // 销毁渲染器
}

// 节点关系
interface NodeRelation {
  name: string
  category: string
  strength: number
  targetIdx: number
}

// 故事弹窗数据
interface StoryData {
  personName: string
  category: string
  stories: string[]
}

// 节点屏幕位置
interface NodeScreenPos {
  x: number
  y: number
  scale: number
  nodeSize: number
  name: string
  category: string
  connections: number
  distFromCenter: number
  distFromTarget: number  // 距离相机目标点的3D距离（归一化，0=在目标点，1=最远）
  labelX: number
  labelY: number
}

// Native节点数据
interface NativeNode {
  id: string
  name: string
  category: string
  x: number
  y: number
  z: number
  connections: number
}

// Native连线数据
interface NativeLink {
  sourceIdx: number
  targetIdx: number
  strength: number
}

// 图谱节点
interface GraphNode {
  id: string
  name: string
  type: string
  category: string
  connections: number
}

// API响应
interface ApiResponse {
  success: boolean
  data: GraphData
  message?: string
}

interface GraphData {
  information?: NodeData[]
  relationships?: LinkData[]
}

interface NodeData {
  id: string
  name: string
  type: string
  category?: string
}

interface LinkData {
  source: string
  target: string
  type: string
}

// 分组
interface CategoryGroup {
  category: string
  nodes: GraphNode[]
}

// 标签显示属性
interface LabelProps {
  show: boolean
  fontSize: number
  opacity: number
  bold: boolean
}

// 颜色映射
const TYPE_COLORS: Record<string, string> = {
  '自己': '#FFD700',
  'family': '#FF6B6B',
  'close_friends': '#4ECDC4',
  'colleagues': '#45B7D1',
  'friends': '#96CEB4',
  'weak_ties': '#9B9B9B',
  'default': '#87CEEB'
}

@Entry
@Component
struct KnowledgeStarMapGL {
  @State userId: string = ''
  @State nodes: GraphNode[] = []
  @State isLoading: boolean = false
  @State loadError: string = ''
  @State selectedNodeIdx: number = -1
  @State showPersonList: boolean = false
  @State showCategoryList: boolean = false
  @State zoomScale: number = 1.0
  @State nodeScreenPositions: NodeScreenPos[] = []
  @State selectedNodeRelations: NodeRelation[] = []
  @State showStoryPanel: boolean = false
  @State storyData: StoryData | null = null
  @State isLoadingStory: boolean = false
  
  // 触摸状态
  @State isDragging: boolean = false
  private dragStartX: number = 0
  private dragStartY: number = 0
  private rotationX: number = 0.3
  private rotationY: number = 0
  
  // 像素密度 (vp to px conversion)
  private pixelDensity: number = 3.0
  
  // Native模块
  private nativeModule: StarMapNative | null = null
  private xComponentId: string = 'starmap_xcomponent'
  
  // 动画
  private animationTimer: number = -1
  private lastFrameTime: number = 0
  private frameCount: number = 0

  async aboutToAppear() {
    try {
      const authService = getAuthService()
      // 确保 AuthService 已初始化，然后获取用户ID
      await authService.ensureInitialized()
      this.userId = authService.getCurrentUserId()
      console.info(`StarMap: userId = ${this.userId}`)
    } catch (e) {
      this.userId = 'default_user'
      console.info('StarMap: using default_user due to error')
    }
    
    // 获取像素密度
    try {
      const displayInfo = display.getDefaultDisplaySync()
      this.pixelDensity = displayInfo.densityPixels
      console.info(`StarMap: pixelDensity = ${this.pixelDensity}`)
    } catch (e) {
      this.pixelDensity = 3.0  // 默认值
      console.info('StarMap: using default pixelDensity = 3.0')
    }
  }

  aboutToDisappear() {
    this.stopAnimation()
    // 显式销毁渲染器，避免 OpenGL 状态残留
    if (this.nativeModule) {
      try {
        this.nativeModule.destroyRenderer()
        console.info('StarMap: Renderer destroyed on page exit')
      } catch (e) {
        console.error('StarMap: Failed to destroy renderer', e)
      }
      this.nativeModule = null
    }
    // 清空节点数据，防止残留状态
    this.nodes = []
    this.nodeScreenPositions = []
    this.selectedNodeRelations = []
    this.selectedNodeIdx = -1
  }

  // 加载Native模块
  loadNativeModule(xcomponentContext: object) {
    console.info('StarMap: loadNativeModule called')
    try {
      this.nativeModule = xcomponentContext as StarMapNative
      console.info('StarMap: Native module cast successful')
      
      // 检查模块方法是否存在
      if (this.nativeModule && typeof this.nativeModule.renderFrame === 'function') {
        console.info('StarMap: Native module methods available')
        this.loadGraphData()
      } else {
        console.error('StarMap: Native module methods not available')
        this.loadError = 'Native模块方法不可用'
      }
    } catch (e) {
      console.error('StarMap: Failed to load native module', JSON.stringify(e))
      this.loadError = '加载渲染模块失败'
    }
  }

  // 加载图谱数据
  async loadGraphData() {
    this.isLoading = true
    this.loadError = ''

    try {
      let httpRequest = http.createHttp()
      let url = `${ApiConfig.getBaseUrl()}/api/v4/knowledge-graph/${this.userId}/export`
      
      let response = await httpRequest.request(url, {
        method: http.RequestMethod.GET,
        connectTimeout: 10000,
        readTimeout: 10000
      })

      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as ApiResponse
        
        if (result.success && result.data) {
          this.parseGraphData(result.data)
        } else {
          this.loadError = result.message || '知识图谱为空'
        }
      } else {
        this.loadError = `服务器错误 (${response.responseCode})`
      }
    } catch (error) {
      this.loadError = '无法连接服务器'
    } finally {
      this.isLoading = false
    }
  }

  // 解析图谱数据并发送到Native
  parseGraphData(data: GraphData) {
    if (!this.nativeModule) return
    
    const nodeData = data.information || []
    const linkData = data.relationships || []
    
    // 构建节点ID到索引的映射
    const nodeIdToIdx: Map<string, number> = new Map()
    
    // 统计连接数
    const connectionCount: Map<string, number> = new Map()
    linkData.forEach(link => {
      connectionCount.set(link.source, (connectionCount.get(link.source) || 0) + 1)
      connectionCount.set(link.target, (connectionCount.get(link.target) || 0) + 1)
    })
    
    // 转换节点 - 增大坐标范围让整体更大
    const nativeNodes: NativeNode[] = []
    this.nodes = []
    
    nodeData.forEach((node, index) => {
      nodeIdToIdx.set(node.id, index)
      
      const angle = (index / nodeData.length) * Math.PI * 2
      const radius = 70 + Math.random() * 50  // 增大半径范围
      
      const nativeNode: NativeNode = {
        id: node.id,
        name: node.name,
        category: node.category || node.type,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        z: (Math.random() - 0.5) * 90,  // 增大Z范围，更有立体感
        connections: connectionCount.get(node.id) || 1
      }
      nativeNodes.push(nativeNode)
      
      // 保存到本地用于UI显示
      const graphNode: GraphNode = {
        id: node.id,
        name: node.name,
        type: node.type,
        category: node.category || node.type,
        connections: connectionCount.get(node.id) || 1
      }
      this.nodes.push(graphNode)
    })
    
    // 转换连线
    const nativeLinks: NativeLink[] = []
    linkData.forEach(link => {
      const sourceIdx = nodeIdToIdx.get(link.source)
      const targetIdx = nodeIdToIdx.get(link.target)
      
      if (sourceIdx !== undefined && targetIdx !== undefined) {
        const nativeLink: NativeLink = {
          sourceIdx: sourceIdx,
          targetIdx: targetIdx,
          strength: 1.0
        }
        nativeLinks.push(nativeLink)
      }
    })
    
    // 发送到Native
    console.info(`StarMap: Sending ${nativeNodes.length} nodes, ${nativeLinks.length} links to native`)
    this.nativeModule.setNodes(nativeNodes)
    this.nativeModule.setLinks(nativeLinks)
    
    console.info('StarMap: Data sent to native, starting animation')
    
    // 启动动画
    this.startAnimation()
  }

  // 启动动画循环
  startAnimation() {
    this.stopAnimation()
    this.frameCount = 0
    this.lastFrameTime = Date.now()
    
    console.info('StarMap: startAnimation called')
    
    const animate = () => {
      if (!this.nativeModule) {
        console.error('StarMap: nativeModule is null in animate')
        return
      }
      
      const now = Date.now()
      const deltaTime = (now - this.lastFrameTime) / 1000.0
      this.lastFrameTime = now
      this.frameCount++
      
      // 前100帧进行力导向布局
      if (this.frameCount <= 100) {
        this.nativeModule.updateForceLayout()
      }
      
      // 更新动画
      this.nativeModule.updateAnimation(deltaTime)
      
      // 渲染
      this.nativeModule.renderFrame()
      
      // 每5帧更新一次标签位置（减少性能开销）
      if (this.frameCount % 5 === 0) {
        this.nodeScreenPositions = this.nativeModule.getNodeScreenPositions()
      }
      
      if (this.frameCount === 1) {
        console.info('StarMap: First frame rendered')
      }
    }
    
    // 立即渲染第一帧
    animate()
    
    // 60fps
    this.animationTimer = setInterval(animate, 16)
    console.info('StarMap: Animation timer started')
  }

  stopAnimation() {
    if (this.animationTimer !== -1) {
      clearInterval(this.animationTimer)
      this.animationTimer = -1
    }
  }

  // 触摸处理
  handleTouchStart(event: TouchEvent) {
    console.info(`StarMap: TouchStart touches=${event.touches.length}`)
    if (event.touches.length === 1) {
      const touch = event.touches[0]
      this.isDragging = false  // 先设为false，移动时再设为true
      this.dragStartX = touch.x
      this.dragStartY = touch.y
      console.info(`StarMap: TouchStart at (${touch.x}, ${touch.y})`)
    }
  }

  handleTouchMove(event: TouchEvent) {
    if (!this.nativeModule) return
    
    if (event.touches.length === 1) {
      const touch = event.touches[0]
      const dx = touch.x - this.dragStartX
      const dy = touch.y - this.dragStartY
      
      // 移动超过阈值才算拖动
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
        this.isDragging = true
      }
      
      if (this.isDragging) {
        this.rotationY += dx * 0.01
        this.rotationX += dy * 0.01
        this.rotationX = Math.max(-1.2, Math.min(1.2, this.rotationX))
        
        console.info(`StarMap: Dragging rotX=${this.rotationX.toFixed(2)} rotY=${this.rotationY.toFixed(2)}`)
        this.nativeModule.setRotation(this.rotationX, this.rotationY)
      }
      
      this.dragStartX = touch.x
      this.dragStartY = touch.y
    }
  }

  handleTouchEnd(event: TouchEvent) {
    console.info(`StarMap: TouchEnd isDragging=${this.isDragging}`)
    if (!this.nativeModule) return
    
    // 检测点击（没有拖动）
    if (!this.isDragging && event.changedTouches.length > 0) {
      const touch = event.changedTouches[0]
      // 触摸坐标是 vp 单位，需要转换为像素
      const pixelX = touch.x * this.pixelDensity
      const pixelY = touch.y * this.pixelDensity
      console.info(`StarMap: Click at vp(${touch.x.toFixed(1)}, ${touch.y.toFixed(1)}) -> px(${pixelX.toFixed(1)}, ${pixelY.toFixed(1)}), density=${this.pixelDensity}`)
      const hitIdx = this.nativeModule.hitTest(pixelX, pixelY)
      console.info(`StarMap: hitTest returned ${hitIdx}`)
      if (hitIdx >= 0) {
        this.selectedNodeIdx = hitIdx
        // 使用 focusOnNode 实现丝滑空间切换效果（同时会调用 selectNode）
        this.nativeModule.focusOnNode(hitIdx)
        // 获取节点关系
        this.selectedNodeRelations = this.nativeModule.getNodeRelations(hitIdx)
        console.info(`StarMap: Focusing on node ${hitIdx}, relations: ${this.selectedNodeRelations.length}`)
      } else {
        this.selectedNodeIdx = -1
        this.selectedNodeRelations = []
        this.nativeModule.selectNode(-1)
      }
    }
    
    this.isDragging = false
  }

  // 缩放
  zoomIn() {
    this.zoomScale = Math.min(this.zoomScale * 1.3, 3.0)
    if (this.nativeModule) {
      this.nativeModule.setZoom(this.zoomScale)
    }
  }

  zoomOut() {
    this.zoomScale = Math.max(this.zoomScale / 1.3, 0.3)
    if (this.nativeModule) {
      this.nativeModule.setZoom(this.zoomScale)
    }
  }

  resetView() {
    this.zoomScale = 1.0
    this.rotationX = 0.3
    this.rotationY = 0
    this.selectedNodeIdx = -1
    this.selectedNodeRelations = []
    if (this.nativeModule) {
      // 使用 resetTarget 平滑动画回到原点
      this.nativeModule.resetTarget()
    }
  }

  // 计算标签显示属性
  getLabelProps(pos: NodeScreenPos): LabelProps {
    let result: LabelProps = { show: false, fontSize: 12, opacity: 0.5, bold: false }
    
    if (this.nodeScreenPositions.length === 0) {
      return result
    }
    
    // 计算最大连接数
    let maxConn = 1
    for (let p of this.nodeScreenPositions) {
      if (p.connections > maxConn) maxConn = p.connections
    }
    
    // 连接数归一化 (0.3 - 1.0)
    const connRatio = 0.3 + (pos.connections / maxConn) * 0.7
    
    // 距离相机目标点越近，显示优先级越高（这是关键！）
    // distFromTarget: 0 = 在目标点（视角中心），1 = 最远
    const targetProximity = 1.0 - pos.distFromTarget  // 反转：越近值越大
    
    // 深度缩放也影响显示（近处的节点更应该显示）
    const depthBonus = pos.scale
    
    // 综合计算显示权重
    // 主要基于距离目标点的远近，其次是连接数和深度
    const displayWeight = targetProximity * 0.5 + connRatio * 0.3 + depthBonus * 0.2
    
    // 是否显示：
    // 1. 距离目标点很近的节点（distFromTarget < 0.3）总是显示
    // 2. 连接数很多的节点（>= 50% 最大连接数）总是显示
    // 3. 其他节点根据权重决定
    result.show = pos.distFromTarget < 0.3 || 
                  pos.connections >= maxConn * 0.5 || 
                  displayWeight > 0.45
    
    // 字体大小：基于距离目标点的远近和连接数
    // 越近字体越大
    const proximitySize = (1.0 - pos.distFromTarget) * 8  // 0-8
    result.fontSize = 10 + connRatio * 8 + proximitySize + pos.scale * 2
    
    // 透明度：距离目标点越近越不透明
    result.opacity = Math.min(0.95, targetProximity * 0.5 + connRatio * 0.3 + depthBonus * 0.2)
    
    // 是否粗体：距离目标点很近或连接数很多
    result.bold = pos.distFromTarget < 0.15 || pos.connections >= maxConn * 0.7
    
    return result
  }

  // 获取节点颜色
  getNodeColor(category: string): string {
    return TYPE_COLORS[category] || TYPE_COLORS['default']
  }

  // 获取分组节点
  getGroupedNodes(): CategoryGroup[] {
    const categoryOrder = ['自己', 'family', 'close_friends', 'colleagues', 'friends', 'weak_ties']
    const groups: Map<string, GraphNode[]> = new Map()
    
    categoryOrder.forEach(cat => groups.set(cat, []))
    
    this.nodes.forEach(node => {
      const category = node.category || node.type
      if (!groups.has(category)) {
        groups.set(category, [])
      }
      const nodeList = groups.get(category)
      if (nodeList) {
        nodeList.push(node)
      }
    })
    
    const result: CategoryGroup[] = []
    categoryOrder.forEach(cat => {
      const nodes = groups.get(cat)
      if (nodes && nodes.length > 0) {
        result.push({ category: cat, nodes: nodes })
      }
    })
    
    groups.forEach((nodes, cat) => {
      if (!categoryOrder.includes(cat) && nodes.length > 0) {
        result.push({ category: cat, nodes: nodes })
      }
    })
    
    return result
  }

  // 获取类别显示名称
  getCategoryDisplayName(category: string): string {
    const displayNames: Record<string, string> = {
      '自己': '我',
      'family': '家人',
      'close_friends': '好友',
      'colleagues': '同事',
      'friends': '朋友',
      'weak_ties': '弱关系'
    }
    return displayNames[category] || category
  }

  build() {
    Stack() {
      // XComponent - GPU渲染
      XComponent({
        id: this.xComponentId,
        type: XComponentType.SURFACE,
        libraryname: 'starmap_render'
      })
        .width('100%')
        .height('100%')
        .onLoad((context?: object) => {
          console.info('StarMap: XComponent onLoad triggered')
          if (context) {
            console.info('StarMap: context received')
            this.loadNativeModule(context)
          } else {
            console.error('StarMap: context is null')
            this.loadError = 'Native模块加载失败'
          }
        })
        .onDestroy(() => {
          console.info('StarMap: XComponent onDestroy')
          this.stopAnimation()
        })

      // 文字标签 - 显示在 OpenGL 绘制的锚点位置，与节点通过连接线关联
      // 注意：pos.labelX/labelY 是像素坐标，需要转换为 vp
      ForEach(this.nodeScreenPositions, (pos: NodeScreenPos, index: number) => {
        if (pos.scale > 0.2 && this.getLabelProps(pos).show) {
          // 将像素坐标转换为 vp
          Text(pos.name)
            .fontSize(this.getLabelProps(pos).fontSize * pos.scale * 0.85)
            .fontColor(this.getNodeColor(pos.category))
            .fontWeight(this.getLabelProps(pos).bold ? FontWeight.Bold : FontWeight.Medium)
            .opacity(this.getLabelProps(pos).opacity * pos.scale)
            .position({ 
              x: pos.labelX / this.pixelDensity + 2,  // 像素转vp，锚点右侧
              y: pos.labelY / this.pixelDensity - (this.getLabelProps(pos).fontSize * pos.scale * 0.85) * 0.45
            })
            .hitTestBehavior(HitTestMode.Transparent)
        }
      })

      // 加载状态
      if (this.isLoading) {
        Column({ space: 16 }) {
          LoadingProgress()
            .width(48)
            .height(48)
            .color('#64B5F6')
          
          Text('探索知识星空...')
            .fontSize(16)
            .fontColor('rgba(255, 255, 255, 0.8)')
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .backgroundColor('rgba(10, 10, 26, 0.9)')
      }

      // 错误状态
      if (this.loadError !== '' && !this.isLoading) {
        Column({ space: 20 }) {
          Text('✦')
            .fontSize(48)
            .fontColor('rgba(255, 255, 255, 0.3)')
          
          Text(this.loadError)
            .fontSize(14)
            .fontColor('rgba(255, 255, 255, 0.6)')
            .textAlign(TextAlign.Center)
          
          Button('重新加载')
            .width(120)
            .height(40)
            .fontSize(14)
            .fontColor('#FFF')
            .backgroundColor('rgba(100, 181, 246, 0.3)')
            .borderRadius(20)
            .onClick(() => this.loadGraphData())
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .backgroundColor('rgba(10, 10, 26, 0.95)')
      }

      // 顶部导航栏
      Row() {
        Button({ type: ButtonType.Circle }) {
          Text('←').fontSize(22).fontWeight(700).fontColor('#FFFFFF')
        }
        .width(40)
        .height(40)
        .backgroundColor('rgba(255, 255, 255, 0.15)')
        .onClick(() => {
          this.stopAnimation()
          if (this.nativeModule) {
            try { this.nativeModule.destroyRenderer() } catch (e) {}
            this.nativeModule = null
          }
          router.back()
        })

        Column({ space: 2 }) {
          Text('知识星图')
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .fontColor('#FFFFFF')
          
          if (this.nodes.length > 0) {
            Text(`${this.nodes.length} 个节点 · GPU渲染`)
              .fontSize(11)
              .fontColor('rgba(255, 255, 255, 0.5)')
          }
        }
        .alignItems(HorizontalAlign.Start)
        .margin({ left: 12 })

        Blank()

        Button({ type: ButtonType.Circle }) {
          SimpleIcon({ iconName: 'learning', iconSize: 20, color: '#FFFFFF' })
        }
        .width(40)
        .height(40)
        .backgroundColor('rgba(255, 255, 255, 0.1)')
        .onClick(() => this.loadGraphData())
      }
      .width('100%')
      .height(56)
      .padding({ left: 16, right: 16 })
      .backgroundColor('rgba(10, 10, 26, 0.8)')
      .position({ x: 0, y: 0 })
      .zIndex(999)
      .hitTestBehavior(HitTestMode.Block)


      // 右上角：类型筛选 + 人物列表（紧贴顶部栏）
      if (this.nodes.length > 0) {
        Row({ space: 6 }) {
          // 类型列表按钮（在人物列表左侧）
          Column() {
            // 触发按钮
            Button({ type: ButtonType.Normal }) {
              Row({ space: 4 }) {
                Text('分类').fontSize(12).fontColor('#FFFFFF').fontWeight(600)
                Text(this.showCategoryList ? '▲' : '▼').fontSize(10).fontColor('rgba(255,255,255,0.6)')
              }.padding({ left: 10, right: 10 })
            }
            .height(32)
            .backgroundColor('rgba(10, 10, 30, 0.85)')
            .borderRadius(16)
            .border({ width: 1, color: 'rgba(255,255,255,0.15)' })
            .onClick(() => {
              this.showCategoryList = !this.showCategoryList
              if (this.showCategoryList) this.showPersonList = false
            })

            // 下拉面板
            if (this.showCategoryList) {
              Column({ space: 2 }) {
                ForEach(this.getGroupedNodes(), (group: CategoryGroup) => {
                  Row({ space: 8 }) {
                    Circle({ width: 8, height: 8 }).fill(this.getNodeColor(group.category))
                    Text(this.getCategoryDisplayName(group.category))
                      .fontSize(12).fontColor('#FFFFFF')
                    Text(`${group.nodes.length}`)
                      .fontSize(10).fontColor('rgba(255,255,255,0.5)')
                  }
                  .width('100%')
                  .padding({ left: 12, right: 12, top: 6, bottom: 6 })
                })
              }
              .width(110)
              .padding({ top: 6, bottom: 6 })
              .backgroundColor('rgba(10, 10, 30, 0.92)')
              .borderRadius(10)
              .border({ width: 1, color: 'rgba(255,255,255,0.1)' })
              .margin({ top: 4 })
            }
          }
          .alignItems(HorizontalAlign.End)

          // 人物列表按钮
          Column() {
            // 触发按钮
            Button({ type: ButtonType.Normal }) {
              Row({ space: 4 }) {
                Text('人物').fontSize(12).fontColor('#FFFFFF').fontWeight(600)
                Text(this.showPersonList ? '▲' : '▼').fontSize(10).fontColor('rgba(255,255,255,0.6)')
                if (!this.showPersonList) {
                  Text(`${this.nodes.length}`).fontSize(10).fontColor('rgba(255,255,255,0.5)')
                }
              }.padding({ left: 10, right: 10 })
            }
            .height(32)
            .backgroundColor('rgba(10, 10, 30, 0.85)')
            .borderRadius(16)
            .border({ width: 1, color: 'rgba(255,255,255,0.15)' })
            .onClick(() => {
              this.showPersonList = !this.showPersonList
              if (this.showPersonList) this.showCategoryList = false
            })

            // 下拉面板
            if (this.showPersonList) {
              Scroll() {
                Column({ space: 0 }) {
                  ForEach(this.getGroupedNodes(), (group: CategoryGroup) => {
                    // 分组标题
                    Row({ space: 6 }) {
                      Circle({ width: 7, height: 7 }).fill(this.getNodeColor(group.category))
                      Text(this.getCategoryDisplayName(group.category))
                        .fontSize(11).fontColor(this.getNodeColor(group.category)).fontWeight(600)
                      Text(`(${group.nodes.length})`).fontSize(10).fontColor('rgba(255,255,255,0.4)')
                    }
                    .width('100%')
                    .padding({ left: 12, right: 12, top: 8, bottom: 4 })

                    // 节点列表
                    ForEach(group.nodes, (node: GraphNode) => {
                      Row({ space: 8 }) {
                        Circle({ width: 5, height: 5 }).fill(this.getNodeColor(node.category))
                        Text(node.name)
                          .fontSize(12).fontColor('rgba(255,255,255,0.85)')
                          .maxLines(1).textOverflow({ overflow: TextOverflow.Ellipsis })
                          .layoutWeight(1)
                        Text(`${node.connections}`)
                          .fontSize(10).fontColor('rgba(255,255,255,0.4)')
                      }
                      .width('100%')
                      .padding({ left: 20, right: 12, top: 5, bottom: 5 })
                      .backgroundColor(
                        this.selectedNodeIdx === this.nodes.findIndex(n => n.id === node.id)
                          ? 'rgba(255,255,255,0.12)' : 'transparent'
                      )
                      .borderRadius(4)
                      .onClick(() => {
                        const globalIdx = this.nodes.findIndex(n => n.id === node.id)
                        if (globalIdx >= 0 && this.nativeModule) {
                          this.nativeModule.focusOnNode(globalIdx)
                          this.selectedNodeIdx = globalIdx
                          this.selectedNodeRelations = this.nativeModule.getNodeRelations(globalIdx)
                          this.showPersonList = false
                        }
                      })
                    })
                  })
                }
                .padding({ bottom: 8 })
              }
              .scrollBar(BarState.Off)
              .constraintSize({ maxHeight: 320 })
              .width(150)
              .backgroundColor('rgba(10, 10, 30, 0.92)')
              .borderRadius(10)
              .border({ width: 1, color: 'rgba(255,255,255,0.1)' })
              .margin({ top: 4 })
            }
          }
          .alignItems(HorizontalAlign.End)
        }
        .position({ x: '100%', y: 8 })
        .translate({ x: -16 })
        .alignItems(VerticalAlign.Top)
        .zIndex(1000)
        .hitTestBehavior(HitTestMode.Block)
      }

      // 右侧控制按钮
      Column({ space: 12 }) {
        Button({ type: ButtonType.Circle }) {
          Text('+').fontSize(24).fontColor('#FFF')
        }
        .width(44)
        .height(44)
        .backgroundColor('rgba(255, 255, 255, 0.15)')
        .onClick(() => this.zoomIn())

        Button({ type: ButtonType.Circle }) {
          Text('−').fontSize(24).fontColor('#FFF')
        }
        .width(44)
        .height(44)
        .backgroundColor('rgba(255, 255, 255, 0.15)')
        .onClick(() => this.zoomOut())

        Button({ type: ButtonType.Circle }) {
          Text('⟲').fontSize(20).fontColor('#FFF')
        }
        .width(44)
        .height(44)
        .backgroundColor('rgba(255, 255, 255, 0.15)')
        .onClick(() => this.resetView())
      }
      .position({ x: '100%', y: '50%' })
      .translate({ x: -60, y: -80 })

      // 底部节点详情
      if (this.selectedNodeIdx >= 0 && this.selectedNodeIdx < this.nodes.length) {
        Column({ space: 12 }) {
          Row()
            .width(40)
            .height(4)
            .backgroundColor('rgba(255, 255, 255, 0.2)')
            .borderRadius(2)

          Row({ space: 16 }) {
            Stack() {
              Circle({ width: 50, height: 50 })
                .fill(this.getNodeColor(this.nodes[this.selectedNodeIdx].category))
              
              Text(this.nodes[this.selectedNodeIdx].name.substring(0, 1))
                .fontSize(20)
                .fontWeight(FontWeight.Bold)
                .fontColor('#FFFFFF')
            }

            Column({ space: 4 }) {
              Text(this.nodes[this.selectedNodeIdx].name)
                .fontSize(18)
                .fontWeight(FontWeight.Bold)
                .fontColor('#FFFFFF')
              
              Row({ space: 8 }) {
                Text(this.getCategoryDisplayName(this.nodes[this.selectedNodeIdx].category))
                  .fontSize(12)
                  .fontColor(this.getNodeColor(this.nodes[this.selectedNodeIdx].category))
                  .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                  .backgroundColor('rgba(255, 255, 255, 0.1)')
                  .borderRadius(8)
                
                Text(`${this.nodes[this.selectedNodeIdx].connections} 个关联`)
                  .fontSize(12)
                  .fontColor('rgba(255, 255, 255, 0.5)')
              }
            }
            .alignItems(HorizontalAlign.Start)
            .layoutWeight(1)

            Button({ type: ButtonType.Circle }) {
              Text('×').fontSize(20).fontColor('rgba(255, 255, 255, 0.6)')
            }
            .width(32)
            .height(32)
            .backgroundColor('transparent')
            .onClick(() => {
              this.selectedNodeIdx = -1
              this.selectedNodeRelations = []
              if (this.nativeModule) {
                this.nativeModule.selectNode(-1)
              }
            })
          }
          .width('100%')

          // 关系列表 - 人物之间的关联与故事
          if (this.selectedNodeRelations.length > 0) {
            Column({ space: 4 }) {
              Text('人物关系')
                .fontSize(13)
                .fontColor('rgba(255, 255, 255, 0.6)')
                .width('100%')
              
              Scroll() {
                Column({ space: 6 }) {
                  ForEach(this.selectedNodeRelations, (rel: NodeRelation) => {
                    Row({ space: 8 }) {
                      // 头像圆
                      Stack() {
                        Circle({ width: 32, height: 32 })
                          .fill(this.getNodeColor(rel.category))
                        Text(rel.name.substring(0, 1))
                          .fontSize(14).fontWeight(FontWeight.Bold).fontColor('#FFFFFF')
                      }.width(32).height(32)
                      
                      Column({ space: 2 }) {
                        Text(rel.name)
                          .fontSize(14)
                          .fontColor('#FFFFFF')
                        Text(this.getCategoryDisplayName(rel.category))
                          .fontSize(11)
                          .fontColor(this.getNodeColor(rel.category))
                      }
                      .alignItems(HorizontalAlign.Start)
                      .layoutWeight(1)

                      // 故事按钮
                      Button('故事')
                        .fontSize(10).fontColor('#F59E0B').height(26)
                        .backgroundColor('rgba(245, 158, 11, 0.15)')
                        .borderRadius(13).padding({ left: 10, right: 10 })
                        .onClick(() => {
                          this.loadStory(
                            this.nodes[this.selectedNodeIdx]?.name || '我',
                            rel.name, rel.category
                          )
                        })

                      // 跳转按钮
                      Button('跳转')
                        .fontSize(10).fontColor('#64B5F6').height(26)
                        .backgroundColor('rgba(100, 181, 246, 0.15)')
                        .borderRadius(13).padding({ left: 10, right: 10 })
                        .onClick(() => {
                          if (this.nativeModule && rel.targetIdx >= 0) {
                            this.nativeModule.focusOnNode(rel.targetIdx)
                            this.selectedNodeIdx = rel.targetIdx
                            this.selectedNodeRelations = this.nativeModule.getNodeRelations(rel.targetIdx)
                          }
                        })
                    }
                    .width('100%')
                    .padding({ top: 8, bottom: 8, left: 10, right: 10 })
                    .backgroundColor('rgba(255, 255, 255, 0.05)')
                    .borderRadius(10)
                  })
                }
              }
              .scrollBar(BarState.Off)
              .constraintSize({ maxHeight: 180 })
            }
            .width('100%')
            .margin({ top: 8 })
          }
        }
        .width('100%')
        .padding(20)
        .backgroundColor('rgba(20, 20, 40, 0.95)')
        .borderRadius({ topLeft: 24, topRight: 24 })
        .position({ x: 0, y: '100%' })
        .translate({ y: this.selectedNodeRelations.length > 0 ? -280 : -180 })
      }

      // 图例（左下角，不遮挡操作区）
      Column({ space: 6 }) {
        ForEach(this.getGroupedNodes().slice(0, 6), (group: CategoryGroup) => {
          Row({ space: 6 }) {
            Circle({ width: 8, height: 8 })
              .fill(this.getNodeColor(group.category))
            Text(this.getCategoryDisplayName(group.category))
              .fontSize(10)
              .fontColor('rgba(255, 255, 255, 0.6)')
          }
        })
      }
      .padding(10)
      .backgroundColor('rgba(0, 0, 0, 0.3)')
      .borderRadius(8)
      .position({ x: 12, y: '100%' })
      .translate({ y: -180 })
      .hitTestBehavior(HitTestMode.Transparent)

      // 故事弹窗
      if (this.showStoryPanel && this.storyData) {
        Stack() {
          Column().width('100%').height('100%')
            .backgroundColor('rgba(0, 0, 0, 0.6)')
            .onClick(() => { this.showStoryPanel = false })

          Column({ space: 14 }) {
            Row() {
              Stack() {
                Circle({ width: 36, height: 36 })
                  .fill(this.getNodeColor(this.storyData.category))
                Text(this.storyData.personName.substring(0, 1))
                  .fontSize(16).fontWeight(FontWeight.Bold).fontColor('#FFFFFF')
              }.width(36).height(36)

              Text(`与 ${this.storyData.personName} 的故事`)
                .fontSize(17).fontWeight(FontWeight.Bold).fontColor('#FFFFFF')
                .margin({ left: 10 }).layoutWeight(1)

              Button('关闭').fontSize(11).fontColor('rgba(255,255,255,0.6)')
                .backgroundColor('rgba(255,255,255,0.1)').height(28).borderRadius(14)
                .onClick(() => { this.showStoryPanel = false })
            }.width('100%')

            Divider().color('rgba(255, 255, 255, 0.1)')

            if (this.isLoadingStory) {
              Column() {
                LoadingProgress().width(32).height(32).color('#64B5F6')
                Text('加载中...').fontSize(12).fontColor('rgba(255,255,255,0.5)').margin({ top: 8 })
              }.width('100%').height(120).justifyContent(FlexAlign.Center)
            } else if (this.storyData.stories.length === 0) {
              Text('暂无故事记录，继续和AI对话会自动积累')
                .fontSize(13).fontColor('rgba(255,255,255,0.4)')
                .padding(20).textAlign(TextAlign.Center).width('100%')
            } else {
              Scroll() {
                Column({ space: 8 }) {
                  ForEach(this.storyData.stories, (story: string, idx: number) => {
                    Row({ space: 8 }) {
                      Circle({ width: 6, height: 6 }).fill('#F59E0B').margin({ top: 6 })
                      Text(story).fontSize(13).fontColor('rgba(255,255,255,0.85)')
                        .lineHeight(20).layoutWeight(1)
                    }.width('100%').padding(10)
                    .backgroundColor('rgba(255,255,255,0.04)').borderRadius(8)
                  })
                }
              }.scrollBar(BarState.Off).constraintSize({ maxHeight: 300 })
            }
          }
          .width('85%')
          .padding(20)
          .backgroundColor('rgba(20, 15, 45, 0.96)')
          .borderRadius(20)
          .border({ width: 1, color: 'rgba(150, 100, 255, 0.2)' })
        }
        .width('100%').height('100%')
      }
    }
    .width('100%')
    .height('100%')
    .onTouch((event) => {
      if (event.type === TouchType.Down) {
        this.handleTouchStart(event)
      } else if (event.type === TouchType.Move) {
        this.handleTouchMove(event)
      } else if (event.type === TouchType.Up) {
        this.handleTouchEnd(event)
      }
    })
  }

  // 加载两个人物之间的故事
  async loadStory(personA: string, personB: string, category: string) {
    this.storyData = { personName: personB, category: category, stories: [] }
    this.showStoryPanel = true
    this.isLoadingStory = true

    try {
      const httpRequest = http.createHttp()
      const url = `${ApiConfig.getBaseUrl()}/api/v4/knowledge-graph/${this.userId}/stories/${encodeURIComponent(personA)}/${encodeURIComponent(personB)}`
      const response = await httpRequest.request(url, {
        method: http.RequestMethod.GET,
        connectTimeout: 10000,
        readTimeout: 10000
      })
      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if (result.success) {
          const data = result.data as Record<string, Object>
          this.storyData = {
            personName: personB,
            category: category,
            stories: (data.stories as string[]) || []
          }
        }
      }
    } catch (err) {
      console.error('加载故事失败:', err)
    } finally {
      this.isLoadingStory = false
    }
  }
}
