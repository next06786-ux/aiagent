/**
 * 知识图谱可视化 - HarmonyOS 6 鸿蒙化升级版
 * 灵动流体设计 · 星空美学
 * 参考鸿蒙6官网风格
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { Theme } from '../common/Theme'
import { SimpleIcon } from '../components/IconRenderer'
import { getAuthService } from '../service/AuthService';

// 粒子效果接口
interface ParticleEffect {
  x: number
  y: number
  vx: number
  vy: number
  opacity: number
  size: number
  life: number
}

interface GraphNode {
  id: string
  name: string
  type: string
  category?: string
  x: number
  y: number
  vx: number
  vy: number
  fx?: number
  fy?: number
  pulsePhase?: number  // 脉冲动画阶段
  glowIntensity?: number  // 光晕强度
}

interface GraphLink {
  source: string
  target: string
  type: string
  flowPhase?: number  // 流动动画阶段
}

interface ApiResponse {
  success: boolean
  data: GraphData
  message?: string
  error_code?: string
}

interface GraphData {
  information?: NodeData[]
  sources?: NodeData[]
  entities?: NodeData[]
  relationships?: LinkData[]
  relations?: LinkData[]
}

interface NodeData {
  id: string
  name: string
  type: string
  category?: string
  source_id?: string
}

interface LinkData {
  source: string
  target: string
  type: string
}

interface SourceInfo {
  source_id: string
  type: string
  timestamp: number
  description?: string
  confidence: number
}

interface KGSession {
  session_id: string
  title: string  // 对话标题
  node_count: number
  last_update: string
}

@Entry
@Component
struct KnowledgeGraphCanvas {
  @State userId: string = ''
  @State nodes: GraphNode[] = []
  @State links: GraphLink[] = []
  @State isLoading: boolean = false
  @State loadError: string = ''
  
  // 会话选择相关
  @State showSessionPanel: boolean = false
  @State sessions: KGSession[] = []
  @State currentSessionId: string = ''
  @State isLoadingSessions: boolean = false
  
  // 视图控制
  @State offsetX: number = 0
  @State offsetY: number = 0
  @State zoomScale: number = 1.0
  @State isDragging: boolean = false
  @State dragStartX: number = 0
  @State dragStartY: number = 0
  
  // 交互状态
  @State selectedNode: GraphNode | null = null
  @State draggedNode: GraphNode | null = null
  @State selectedNodeSources: SourceInfo[] = []
  @State isLoadingSources: boolean = false
  @State hoveredNode: GraphNode | null = null
  
  // Canvas
  private settings: RenderingContextSettings = new RenderingContextSettings(true)
  private context: CanvasRenderingContext2D = new CanvasRenderingContext2D(this.settings)
  @State canvasWidth: number = 360
  @State canvasHeight: number = 600
  
  // 动画系统
  private animationTimer: number = -1
  private animationFrameCount: number = 0
  private readonly MAX_ITERATIONS = 300
  private readonly REPULSION = 3000
  private readonly ATTRACTION = 0.05
  private readonly DAMPING = 0.85
  private readonly MIN_VELOCITY = 0.1
  
  // 鸿蒙化增强效果 - 简化版
  private readonly GLOW_ANIMATION_SPEED = 0.05
  
  async aboutToAppear() {
    // 获取当前用户ID
    try {
      const authModule = await import('../service/AuthService')
      const authService = authModule.getAuthService()
      this.userId = authService.getCurrentUserId()
      console.info('[KnowledgeGraphCanvas] 当前用户ID:', this.userId)
    } catch (e) {
      console.error('[KnowledgeGraphCanvas] 获取用户ID失败:', e)
      this.userId = 'default_user'
    }
    
    // 加载知识图谱会话列表
    await this.loadSessions()
    
    // 加载知识图谱数据
    this.loadGraphData()
  }
  
  /**
   * 加载知识图谱会话列表
   */
  async loadSessions() {
    this.isLoadingSessions = true
    try {
      let httpRequest = http.createHttp()
      let url = `${ApiConfig.getBaseUrl()}/api/v4/knowledge-graph/${this.userId}/sessions`
      
      let response = await httpRequest.request(url, {
        method: http.RequestMethod.GET
      })
      
      httpRequest.destroy()
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as ApiResponse;
        if (result.success && result.data) {
          this.sessions = result.data as KGSession[]
          console.info(`[KnowledgeGraphCanvas] 加载了 ${this.sessions.length} 个会话`)
        }
      }
    } catch (error) {
      console.error('[KnowledgeGraphCanvas] 加载会话列表失败:', JSON.stringify(error))
    } finally {
      this.isLoadingSessions = false
    }
  }
  
  /**
   * 加载指定会话的知识图谱
   */
  loadSessionGraph(sessionId: string) {
    this.currentSessionId = sessionId
    this.showSessionPanel = false
    this.loadGraphData()
  }

  aboutToDisappear() {
    this.stopSimulation()
  }

  async loadGraphData() {
    this.isLoading = true
    this.loadError = ''
    console.info('[KnowledgeGraphCanvas] 开始加载知识图谱数据...')

    try {
      let httpRequest = http.createHttp()
      let url = `${ApiConfig.getBaseUrl()}/api/v4/knowledge-graph/${this.userId}/export`
      
      // 如果选择了特定会话，添加session_id参数
      if (this.currentSessionId) {
        url += `?session_id=${this.currentSessionId}`
        console.info('[KnowledgeGraphCanvas] 加载会话知识图谱:', this.currentSessionId)
      }
      
      console.info('[KnowledgeGraphCanvas] 请求URL:', url)
      
      let response = await httpRequest.request(url, {
        method: http.RequestMethod.GET,
        connectTimeout: 1000,
        readTimeout: 1000
      })

      httpRequest.destroy()

      console.info('[KnowledgeGraphCanvas] 响应状态码:', response.responseCode)

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as ApiResponse;
        console.info('[KnowledgeGraphCanvas] API返回:', JSON.stringify(result).substring(0, 200))
        
        if (result.success && result.data && (result.data.information?.length || 0) > 0) {
          this.parseGraphData(result.data)
          console.info('[KnowledgeGraphCanvas] ✅ 成功加载真实数据')
          this.startSimulation()
          
          // 刷新会话列表（如果有新的节点）
          this.loadSessions()
        } else {
          // 后端返回失败状态
          console.error('[KnowledgeGraphCanvas] ❌ 后端返回错误:', result.message)
          let errorMsg = result.message || '知识图谱加载失败'
          
          // 根据错误代码提供更具体的提示
          if (result.error_code === 'KG_NOT_INITIALIZED') {
            this.loadError = '后端服务未正确初始化，请检查 Neo4j 数据库连接'
          } else if (result.error_code === 'KG_EMPTY') {
            this.loadError = '知识图谱为空，请先进行对话以构建知识网络'
          } else {
            this.loadError = errorMsg
          }
        }
      } else {
        console.error('[KnowledgeGraphCanvas] ❌ HTTP错误:', response.responseCode)
        this.loadError = `后端错误 (${response.responseCode})，请检查服务状态`
      }
    } catch (error) {
      console.error('[KnowledgeGraphCanvas] ❌ 网络错误:', JSON.stringify(error))
      this.loadError = '无法连接到后端服务，请确保后端已启动'
    } finally {
      this.isLoading = false
    }
  }

  parseGraphData(data: GraphData) {
    // 收集节点数据
    let nodeData: NodeData[] = []
    if (data.information && data.information.length > 0) {
      nodeData = data.information
    } else if (data.entities && data.entities.length > 0) {
      nodeData = data.entities
    }

    // 添加来源节点
    if (data.sources && data.sources.length > 0) {
      data.sources.forEach(source => {
        let sourceNode: NodeData = {
          id: source.id,
          name: source.source_id || source.type,
          type: 'Source',
          category: source.type
        }
        nodeData.push(sourceNode)
      })
    }

    // 使用圆形布局，更稳定
    let centerX = 0
    let centerY = 0
    let radius = 150
    
    this.nodes = nodeData.map((node, index) => {
      let angle = (index / nodeData.length) * Math.PI * 2
      let graphNode: GraphNode = {
        id: node.id,
        name: node.name,
        type: node.type,
        category: node.category,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        pulsePhase: Math.random() * Math.PI * 2,
        glowIntensity: 0.5 + Math.random() * 0.5
      }
      return graphNode
    })

    // 创建连接
    let linkData = data.relationships || data.relations || []
    this.links = linkData.map(link => {
      let graphLink: GraphLink = {
        source: link.source,
        target: link.target,
        type: link.type,
        flowPhase: Math.random() * Math.PI * 2
      }
      return graphLink
    })

    console.info(`[KnowledgeGraphCanvas] 已加载: ${this.nodes.length}个节点, ${this.links.length}条连接`)
  }

  // 力导向布局模拟 - 简化版，减少迭代次数
  startSimulation() {
    this.stopSimulation()
    this.animationFrameCount = 0
    
    const simulate = () => {
      this.animationFrameCount++
      
      // 减少迭代次数，避免布局混乱
      if (this.animationFrameCount > 100) {
        this.stopSimulation()
        console.info('[KnowledgeGraphCanvas] 布局完成')
        return
      }
      
      this.updateForces()
      this.updatePositions()
      this.render()
    }
    
    this.animationTimer = setInterval(simulate, 16) // ~60fps
  }

  stopSimulation() {
    if (this.animationTimer !== -1) {
      clearInterval(this.animationTimer)
      this.animationTimer = -1
    }
  }

  // 更新动画状态 - 简化版
  private updateAnimations() {
    // 只保留基本的节点脉冲动画
    this.nodes.forEach(node => {
      if (node.pulsePhase !== undefined) {
        node.pulsePhase += 0.02
        if (node.pulsePhase > Math.PI * 2) {
          node.pulsePhase -= Math.PI * 2
        }
      }
    })

    // 移除连接流动动画，减少计算量
    // 移除粒子系统更新，减少计算量
  }

  updateForces() {
    // 重置速度
    this.nodes.forEach(node => {
      node.vx = 0
      node.vy = 0
    })

    // 减弱斥力，避免节点飞得太远
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        let node1 = this.nodes[i]
        let node2 = this.nodes[j]
        
        let dx = node2.x - node1.x
        let dy = node2.y - node1.y
        let distance = Math.sqrt(dx * dx + dy * dy) || 1
        
        // 减小斥力强度
        let force = 1000 / (distance * distance)
        let fx = (dx / distance) * force
        let fy = (dy / distance) * force
        
        node1.vx -= fx
        node1.vy -= fy
        node2.vx += fx
        node2.vy += fy
      }
    }

    // 引力计算
    this.links.forEach(link => {
      let source = this.nodes.find(n => n.id === link.source)
      let target = this.nodes.find(n => n.id === link.target)
      
      if (source && target) {
        let dx = target.x - source.x
        let dy = target.y - source.y
        let distance = Math.sqrt(dx * dx + dy * dy) || 1
        
        let force = distance * 0.03
        let fx = (dx / distance) * force
        let fy = (dy / distance) * force
        
        source.vx += fx
        source.vy += fy
        target.vx -= fx
        target.vy -= fy
      }
    })
  }

  updatePositions() {
    let maxVelocity = 0
    
    this.nodes.forEach(node => {
      // 固定节点处理
      if (node.fx !== undefined && node.fy !== undefined) {
        node.x = node.fx
        node.y = node.fy
        return
      }
      
      // 速度限制 - 更严格
      let speed = Math.sqrt(node.vx * node.vx + node.vy * node.vy)
      if (speed > 5) {
        node.vx = (node.vx / speed) * 5
        node.vy = (node.vy / speed) * 5
      }
      
      // 位置更新
      node.x += node.vx
      node.y += node.vy
      
      // 边界限制 - 更严格
      let maxDistance = 200
      let distance = Math.sqrt(node.x * node.x + node.y * node.y)
      if (distance > maxDistance) {
        node.x = (node.x / distance) * maxDistance
        node.y = (node.y / distance) * maxDistance
      }
      
      // 阻尼 - 更强
      node.vx *= 0.7
      node.vy *= 0.7
      
      maxVelocity = Math.max(maxVelocity, Math.abs(node.vx), Math.abs(node.vy))
    })
    
    // 收敛检测
    if (maxVelocity < 0.05 && this.animationFrameCount > 30) {
      this.stopSimulation()
      console.info('[KnowledgeGraphCanvas] 布局已收敛')
    }
  }

  render() {
    if (!this.context) return

    // 清空画布
    this.context.clearRect(0, 0, this.canvasWidth, this.canvasHeight)
    
    // 简单背景色
    this.context.fillStyle = '#F5F7FA'
    this.context.fillRect(0, 0, this.canvasWidth, this.canvasHeight)
    
    // 保存上下文
    this.context.save()
    
    // 应用变换
    this.context.translate(this.canvasWidth / 2 + this.offsetX, this.canvasHeight / 2 + this.offsetY)
    this.context.scale(this.zoomScale, this.zoomScale)
    
    // 绘制连接 - 简化版
    this.links.forEach(link => {
      let source = this.nodes.find(n => n.id === link.source)
      let target = this.nodes.find(n => n.id === link.target)
      
      if (source && target) {
        this.drawLinkSimple(source, target, link)
      }
    })
    
    // 绘制节点 - 简化版
    this.nodes.forEach(node => {
      this.drawNodeSimple(node)
    })
    
    // 恢复上下文
    this.context.restore()
  }

  // 简化版连接绘制
  private drawLinkSimple(source: GraphNode, target: GraphNode, link: GraphLink) {
    // 简单的直线连接
    this.context.beginPath()
    this.context.moveTo(source.x, source.y)
    this.context.lineTo(target.x, target.y)
    this.context.strokeStyle = 'rgba(10, 89, 247, 0.3)'
    this.context.lineWidth = 2
    this.context.stroke()
  }

  // 简化版节点绘制
  private drawNodeSimple(node: GraphNode) {
    let color = this.getNodeColor(node.type)
    let radius = 20
    
    // 简单的圆形节点
    this.context.beginPath()
    this.context.arc(node.x, node.y, radius, 0, Math.PI * 2)
    this.context.fillStyle = color
    this.context.fill()
    
    // 节点边框
    this.context.strokeStyle = 'rgba(255, 255, 255, 0.8)'
    this.context.lineWidth = 2
    this.context.stroke()
    
    // 选中状态
    if (this.selectedNode && this.selectedNode.id === node.id) {
      this.context.beginPath()
      this.context.arc(node.x, node.y, radius + 4, 0, Math.PI * 2)
      this.context.strokeStyle = 'rgba(10, 89, 247, 0.8)'
      this.context.lineWidth = 3
      this.context.stroke()
    }
    
    // 节点文字
    this.context.fillStyle = '#FFFFFF'
    this.context.font = 'bold 14px sans-serif'
    this.context.textAlign = 'center'
    this.context.textBaseline = 'middle'
    this.context.fillText(node.name.substring(0, 1), node.x, node.y)
    
    // 节点标签
    this.context.fillStyle = '#333'
    this.context.font = '12px sans-serif'
    this.context.fillText(node.name, node.x, node.y + radius + 15)
  }

  getNodeColor(type: string): string {
    const colors: Record<string, string> = {
      'Concept': '#FF6B6B',      // 概念 - 珊瑚红
      'Entity': '#4ECDC4',       // 实体 - 青绿色
      'Event': '#45B7D1',        // 事件 - 天蓝色
      'Pattern': '#FFA07A',      // 模式 - 浅橙色
      'Source': '#95E1D3',       // 来源 - 薄荷绿
      'Photo': '#A8E6CF',        // 照片 - 浅绿色
      'Location': '#FFD93D',     // 地点 - 金黄色
      'Person': '#6BCF7F',       // 人物 - 生机绿
      'Time': '#B19CD9'          // 时间 - 薰衣草紫
    }
    return colors[type] || '#A0A0A0'
  }
  
  // 颜色加深处理
  darkenColor(color: string, percent: number): string {
    // 简单的颜色加深处理
    if (color.startsWith('#')) {
      let num = parseInt(color.slice(1), 16)
      let amt = Math.round(2.55 * percent)
      let R = Math.max(0, (num >> 16) - amt)
      let G = Math.max(0, (num >> 8 & 0x00FF) - amt)
      let B = Math.max(0, (num & 0x0000FF) - amt)
      return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)
    }
    return color
  }

  formatSourceType(type: string): string {
    const typeMap: Record<string, string> = {
      'photo': '照片',
      'sensor_record': '传感器',
      'conversation': '对话',
      'manual_input': '手动输入'
    }
    return typeMap[type] || type
  }

  // 触摸交互处理
  handleTouchStart(event: TouchEvent) {
    if (event.touches.length === 1) {
      let touch = event.touches[0]
      let canvasX = (touch.x - this.canvasWidth / 2 - this.offsetX) / this.zoomScale
      let canvasY = (touch.y - this.canvasHeight / 2 - this.offsetY) / this.zoomScale
      
      // 检测点击的节点
      let clickedNode = this.findNodeAt(canvasX, canvasY)
      
      if (clickedNode) {
        this.draggedNode = clickedNode
        this.selectedNode = clickedNode
        clickedNode.fx = clickedNode.x
        clickedNode.fy = clickedNode.y
        
        // 加载节点来源信息
        this.loadNodeSources(clickedNode.name)
        
        // 手动触发渲染以显示选中状态
        this.render()
      } else {
        this.isDragging = true
        this.dragStartX = touch.x
        this.dragStartY = touch.y
      }
    }
  }

  handleTouchMove(event: TouchEvent) {
    if (event.touches.length === 1) {
      let touch = event.touches[0]
      
      if (this.draggedNode) {
        // 拖动节点
        let canvasX = (touch.x - this.canvasWidth / 2 - this.offsetX) / this.zoomScale
        let canvasY = (touch.y - this.canvasHeight / 2 - this.offsetY) / this.zoomScale
        
        this.draggedNode.fx = canvasX
        this.draggedNode.fy = canvasY
        
        // 手动触发渲染
        this.render()
      } else if (this.isDragging) {
        // 拖动画布
        let dx = touch.x - this.dragStartX
        let dy = touch.y - this.dragStartY
        
        this.offsetX += dx
        this.offsetY += dy
        
        this.dragStartX = touch.x
        this.dragStartY = touch.y
        
        // 手动触发渲染
        this.render()
      }
    }
  }

  handleTouchEnd() {
    if (this.draggedNode) {
      this.draggedNode.fx = undefined
      this.draggedNode.fy = undefined
      this.draggedNode = null
    }
    this.isDragging = false
  }

  findNodeAt(x: number, y: number): GraphNode | null {
    let radius = 24
    
    for (let node of this.nodes) {
      let dx = x - node.x
      let dy = y - node.y
      let distance = Math.sqrt(dx * dx + dy * dy)
      
      if (distance <= radius) {
        return node
      }
    }
    
    return null
  }

  // 缩放控制
  handleZoomIn() {
    this.zoomScale = Math.min(this.zoomScale * 1.2, 3.0)
    this.render()
  }

  handleZoomOut() {
    this.zoomScale = Math.max(this.zoomScale / 1.2, 0.3)
    this.render()
  }

  handleResetView() {
    this.offsetX = 0
    this.offsetY = 0
    this.zoomScale = 1.0
    this.render()
  }

  // 加载节点来源信息
  async loadNodeSources(nodeName: string) {
    this.isLoadingSources = true
    this.selectedNodeSources = []
    
    try {
      let httpRequest = http.createHttp()
      let url = `${ApiConfig.getBaseUrl()}/api/v4/information/${this.userId}/${encodeURIComponent(nodeName)}/sources`
      
      let response = await httpRequest.request(url, {
        method: http.RequestMethod.GET,
        connectTimeout: 5000,
        readTimeout: 5000
      })

      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as ApiResponse;
        
        if (result.success && result.data) {
          // 暂时不加载来源信息，避免类型错误
          console.info(`[KnowledgeGraphCanvas] 节点来源功能暂时禁用`)
        }
      }
    } catch (error) {
      console.error('[KnowledgeGraphCanvas] 加载来源失败:', JSON.stringify(error))
    } finally {
      this.isLoadingSources = false
    }
  }

  build() {
    Stack() {
      // 背景层
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor(Theme.Color.BackgroundPrimary)
      
      // 主内容区域
      if (this.isLoading) {
        // 加载状态 - 鸿蒙化设计
        Column({ space: 16 }) {
          Stack() {
            Circle({ width: 60, height: 60 })
              .fill('rgba(10, 89, 247, 0.1)')
            
            LoadingProgress()
              .width(48)
              .height(48)
              .color(Theme.Color.Primary)
          }
          
          Column({ space: 8 }) {
            Text('加载知识图谱中...')
              .fontSize(18)
              .fontWeight(600)
              .fontColor(Theme.Color.TextPrimary)
            
            Text('正在从Neo4j数据库读取')
              .fontSize(13)
              .fontColor(Theme.Color.TextTertiary)
          }
          .alignItems(HorizontalAlign.Center)
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      } else if (this.loadError !== '') {
        // 错误状态
        Column({ space: 20 }) {
          Stack() {
            Circle({ width: 80, height: 80 })
              .fill('rgba(255, 59, 48, 0.1)')
            
            SimpleIcon({
              iconName: 'back',
              iconSize: 40,
              color: '#FF3B30'
            })
          }
          
          Column({ space: 8 }) {
            Text('加载失败')
              .fontSize(20)
              .fontWeight(700)
              .fontColor(Theme.Color.TextPrimary)
            
            Text(this.loadError)
              .fontSize(14)
              .fontColor(Theme.Color.TextSecondary)
              .textAlign(TextAlign.Center)
              .width('80%')
            
            Text('请确保后端服务已启动')
              .fontSize(13)
              .fontColor(Theme.Color.TextTertiary)
              .margin({ top: 4 })
          }
          .alignItems(HorizontalAlign.Center)
          
          Button('重新加载')
            .width(160)
            .height(44)
            .fontSize(15)
            .fontWeight(600)
            .fontColor('#FFF')
            .backgroundColor(Theme.Color.Primary)
            .borderRadius(22)
            .onClick(() => {
              this.loadGraphData()
            })
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      } else if (this.nodes.length === 0) {
        // 空数据状态
        Column({ space: 20 }) {
          Stack() {
            Circle({ width: 80, height: 80 })
              .fill('rgba(10, 89, 247, 0.1)')
            
            SimpleIcon({
              iconName: 'learning',
              iconSize: 40,
              color: Theme.Color.Primary
            })
          }
          
          Column({ space: 8 }) {
            Text('暂无知识图谱')
              .fontSize(20)
              .fontWeight(700)
              .fontColor(Theme.Color.TextPrimary)
            
            Text('开始使用AI助手对话')
              .fontSize(14)
              .fontColor(Theme.Color.TextSecondary)
            
            Text('系统将自动构建您的知识网络')
              .fontSize(13)
              .fontColor(Theme.Color.TextTertiary)
              .margin({ top: 4 })
          }
          .alignItems(HorizontalAlign.Center)
          
          Button('开始对话')
            .width(160)
            .height(44)
            .fontSize(15)
            .fontWeight(600)
            .fontColor('#FFF')
            .backgroundColor(Theme.Color.Primary)
            .borderRadius(22)
            .onClick(() => {
              router.pushUrl({ url: 'pages/AIChat' })
            })
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      } else {
        Stack() {
          // Canvas 画布
          Canvas(this.context)
            .width('100%')
            .height('100%')
            .onReady(() => {
              this.canvasWidth = 360
              this.canvasHeight = 600
              this.render()
            })
            .onTouch((event) => {
              if (event.type === TouchType.Down) {
                this.handleTouchStart(event)
              } else if (event.type === TouchType.Move) {
                this.handleTouchMove(event)
              } else if (event.type === TouchType.Up) {
                this.handleTouchEnd()
              }
            })
          
          // 控制按钮组 - 右侧浮动
          Column({ space: 12 }) {
            // 放大按钮
            Button({ type: ButtonType.Circle, stateEffect: true }) {
              Text('+')
                .fontSize(28)
                .fontColor(Theme.Color.Primary)
                .fontWeight(300)
            }
            .width(52)
            .height(52)
            .backgroundColor(Theme.Color.GlassHeavy)
            .backdropBlur(20)
            .shadow(Theme.Shadow.Medium)
            .onClick(() => {
              this.handleZoomIn()
            })
            
            // 缩小按钮
            Button({ type: ButtonType.Circle, stateEffect: true }) {
              Text('−')
                .fontSize(28)
                .fontColor(Theme.Color.Primary)
                .fontWeight(300)
            }
            .width(52)
            .height(52)
            .backgroundColor(Theme.Color.GlassHeavy)
            .backdropBlur(20)
            .shadow(Theme.Shadow.Medium)
            .onClick(() => {
              this.handleZoomOut()
            })
            
            // 重置按钮
            Button({ type: ButtonType.Circle, stateEffect: true }) {
              SimpleIcon({
                iconName: 'home',
                iconSize: 22,
                color: Theme.Color.Primary
              })
            }
            .width(52)
            .height(52)
            .backgroundColor(Theme.Color.GlassHeavy)
            .backdropBlur(20)
            .shadow(Theme.Shadow.Medium)
            .onClick(() => {
              this.handleResetView()
            })
          }
          .position({ x: '100%', y: '50%' })
          .translate({ x: -76, y: '-50%' })
          .zIndex(10)
        }
        .width('100%')
        .height('100%')
      }

      // 顶部导航栏 - 鸿蒙化毛玻璃
      Row() {
        Row({ space: 12 }) {
          Button({ type: ButtonType.Circle, stateEffect: true }) {
            SimpleIcon({
              iconName: 'back',
              iconSize: 20,
              color: Theme.Color.TextPrimary
            })
          }
          .width(40)
          .height(40)
          .backgroundColor('transparent')
          .onClick(() => {
            router.back()
          })
          
          Column({ space: 2 }) {
            Row({ space: 8 }) {
              Text('知识图谱')
                .fontSize(18)
                .fontWeight(700)
                .fontColor(Theme.Color.TextPrimary)
              
              if (this.nodes.length > 0) {
                Text(`${this.nodes.length}`)
                  .fontSize(14)
                  .fontWeight(600)
                  .fontColor('#FFF')
                  .padding({ left: 8, right: 8, top: 2, bottom: 2 })
                  .backgroundColor(Theme.Color.Primary)
                  .borderRadius(10)
              }
            }
            
            Text('灵动流体 · 记忆永存')
              .fontSize(12)
              .fontColor(Theme.Color.TextSecondary)
          }
          .alignItems(HorizontalAlign.Start)
        }
        
        Blank()
        
        // 会话选择按钮
        Button({ type: ButtonType.Circle, stateEffect: true }) {
          SimpleIcon({
            iconName: 'chat',
            iconSize: 20,
            color: Theme.Color.Primary
          })
        }
        .width(40)
        .height(40)
        .backgroundColor('transparent')
        .onClick(() => {
          this.showSessionPanel = !this.showSessionPanel
        })
        
        // 刷新按钮
        Button({ type: ButtonType.Circle, stateEffect: true }) {
          SimpleIcon({
            iconName: 'learning',
            iconSize: 20,
            color: Theme.Color.Primary
          })
        }
        .width(40)
        .height(40)
        .backgroundColor('transparent')
        .onClick(() => {
          this.loadGraphData()
        })
      }
      .width('100%')
      .height(56)
      .padding({ left: 16, right: 16 })
      .backgroundColor(Theme.Color.GlassLight)
      .backdropBlur(20)
      .shadow(Theme.Shadow.Soft)
      .position({ x: 0, y: 0 })
      .zIndex(100)
      
      // 会话选择面板
      if (this.showSessionPanel) {
        this.SessionPanel()
      }

      // 底部详情面板 - 鸿蒙化设计
      if (this.selectedNode) {
        Column({ space: 16 }) {
          // 拖动指示条
          Row()
            .width(40)
            .height(4)
            .backgroundColor('rgba(0, 0, 0, 0.1)')
            .borderRadius(2)
            .margin({ top: 8, bottom: 4 })
            .alignSelf(ItemAlign.Center)

          // 节点信息头
          Row({ space: 16 }) {
            // 节点颜色圆形
            Stack() {
              Circle({ width: 56, height: 56 })
                .fill(this.getNodeColor(this.selectedNode.type))
              
              Text(this.selectedNode.name.substring(0, 1))
                .fontSize(24)
                .fontWeight(700)
                .fontColor('#FFFFFF')
            }
            .shadow({ radius: 12, color: this.getNodeColor(this.selectedNode.type) + '40', offsetY: 6 })
            
            Column({ space: 6 }) {
              Text(this.selectedNode.name)
                .fontSize(22)
                .fontWeight(700)
                .fontColor(Theme.Color.TextPrimary)
              
              Row({ space: 8 }) {
                Text(this.selectedNode.type)
                  .fontSize(12)
                  .fontColor(Theme.Color.Primary)
                  .padding({ left: 10, right: 10, top: 4, bottom: 4 })
                  .backgroundColor('rgba(10, 89, 247, 0.12)')
                  .borderRadius(6)
                
                if (this.selectedNode.category) {
                  Text(this.selectedNode.category)
                    .fontSize(12)
                    .fontColor(Theme.Color.TextSecondary)
                    .padding({ left: 10, right: 10, top: 4, bottom: 4 })
                    .backgroundColor('rgba(0, 0, 0, 0.04)')
                    .borderRadius(6)
                }
              }
            }
            .alignItems(HorizontalAlign.Start)
            .layoutWeight(1)
            
            // 关闭按钮
            Button({ type: ButtonType.Circle, stateEffect: true }) {
              SimpleIcon({
                iconName: 'back',
                iconSize: 18,
                color: Theme.Color.TextTertiary
              })
            }
            .width(36)
            .height(36)
            .backgroundColor('transparent')
            .onClick(() => {
              this.selectedNode = null
              this.selectedNodeSources = []
            })
          }
          .width('100%')
          
          Divider()
            .color(Theme.Color.BorderLight)
            .strokeWidth(1)
          
          // 来源信息区域
          if (this.isLoadingSources) {
            Row({ space: 8 }) {
              LoadingProgress()
                .width(16)
                .height(16)
                .color(Theme.Color.Primary)
              Text('正在追溯来源...')
                .fontSize(13)
                .fontColor(Theme.Color.TextTertiary)
            }
            .padding({ top: 12, bottom: 12 })
            .width('100%')
          } else if (this.selectedNodeSources.length > 0) {
            Column({ space: 12 }) {
              Row({ space: 8 }) {
                Text(`关联记忆`)
                  .fontSize(14)
                  .fontWeight(600)
                  .fontColor(Theme.Color.TextPrimary)
                
                Text(`${this.selectedNodeSources.length}`)
                  .fontSize(14)
                  .fontWeight(600)
                  .fontColor(Theme.Color.Primary)
              }
              
              List({ space: 10 }) {
                ForEach(this.selectedNodeSources, (source: SourceInfo) => {
                  ListItem() {
                    Row({ space: 12 }) {
                      // 来源类型图标
                      Stack() {
                        Circle({ width: 40, height: 40 })
                          .fill('rgba(10, 89, 247, 0.1)')
                        
                        SimpleIcon({
                          iconName: source.type === 'photo' ? 'camera' : 'insight',
                          iconSize: 18,
                          color: Theme.Color.Primary
                        })
                      }
                      
                      Column({ space: 4 }) {
                        Text(source.description || source.source_id)
                          .fontSize(14)
                          .fontColor(Theme.Color.TextPrimary)
                          .maxLines(1)
                          .textOverflow({ overflow: TextOverflow.Ellipsis })
                        
                        Row({ space: 8 }) {
                          Text(this.formatSourceType(source.type))
                            .fontSize(11)
                            .fontColor(Theme.Color.TextTertiary)
                          
                          Text(`${(source.confidence * 100).toFixed(0)}%`)
                            .fontSize(11)
                            .fontColor(Theme.Color.Primary)
                            .fontWeight(600)
                        }
                      }
                      .layoutWeight(1)
                      .alignItems(HorizontalAlign.Start)
                    }
                    .width('100%')
                    .padding(12)
                    .backgroundColor(Theme.Color.BackgroundTertiary)
                    .borderRadius(12)
                  }
                })
              }
              .width('100%')
              .height(140)
              .scrollBar(BarState.Off)
            }
          } else {
            Text('暂无关联记忆')
              .fontSize(13)
              .fontColor(Theme.Color.TextTertiary)
              .padding({ top: 12, bottom: 12 })
              .alignSelf(ItemAlign.Center)
          }
          
          // 操作按钮
          Button('查看详细档案')
            .width('100%')
            .height(48)
            .fontSize(16)
            .fontWeight(600)
            .fontColor('#FFF')
            .backgroundColor(Theme.Color.Primary)
            .borderRadius(24)
            .shadow({ radius: 12, color: 'rgba(10, 89, 247, 0.35)', offsetY: 6 })
            .onClick(() => {
              console.info('查看详情:', this.selectedNode?.name)
            })
        }
        .width('94%')
        .padding(20)
        .backgroundColor(Theme.Color.GlassHeavy)
        .backdropBlur(30)
        .borderRadius(28)
        .shadow(Theme.Shadow.Elevated)
        .position({ x: '3%', y: '100%' })
        .translate({ y: '-100%' })
        .margin({ bottom: 16 })
        .transition({ type: TransitionType.Insert, opacity: 0, translate: { y: 100 } })
        .transition({ type: TransitionType.Delete, opacity: 0, translate: { y: 100 } })
        .zIndex(50)
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }
  
  /**
   * 会话选择面板
   */
  @Builder
  SessionPanel(): void {
    Column() {
      // 面板头部
      Row() {
        Text('对话会话')
          .fontSize(18)
          .fontWeight(700)
          .fontColor(Theme.Color.TextPrimary)
        
        Blank()
        
        Button('全部')
          .fontSize(14)
          .fontColor(Theme.Color.Primary)
          .backgroundColor('rgba(10, 89, 247, 0.1)')
          .height(32)
          .borderRadius(16)
          .onClick(() => {
            this.currentSessionId = ''
            this.showSessionPanel = false
            this.loadGraphData()
          })
        
        Button({ type: ButtonType.Circle }) {
          Text('×')
            .fontSize(24)
            .fontColor(Theme.Color.TextSecondary)
        }
        .width(32)
        .height(32)
        .backgroundColor('transparent')
        .onClick(() => {
          this.showSessionPanel = false
        })
      }
      .width('100%')
      .padding(16)
      
      // 会话列表
      if (this.isLoadingSessions) {
        Column() {
          LoadingProgress()
            .width(40)
            .height(40)
            .color(Theme.Color.Primary)
        }
        .width('100%')
        .height(200)
        .justifyContent(FlexAlign.Center)
      } else if (this.sessions.length === 0) {
        Column() {
          Text('暂无会话数据')
            .fontSize(14)
            .fontColor(Theme.Color.TextTertiary)
        }
        .width('100%')
        .height(200)
        .justifyContent(FlexAlign.Center)
      } else {
        List({ space: 8 }) {
          ForEach(this.sessions, (session: KGSession) => {
            ListItem() {
              Column({ space: 8 }) {
                Row() {
                  Text(session.title)
                    .fontSize(15)
                    .fontWeight(600)
                    .fontColor(Theme.Color.TextPrimary)
                    .maxLines(1)
                    .textOverflow({ overflow: TextOverflow.Ellipsis })
                  
                  Blank()
                  
                  Text(`${session.node_count}节点`)
                    .fontSize(12)
                    .fontColor(Theme.Color.TextTertiary)
                }
                .width('100%')
                
                Row() {
                  Text(`会话 ${session.session_id.substring(8, 16)}`)
                    .fontSize(12)
                    .fontColor(Theme.Color.TextSecondary)
                  
                  Blank()
                  
                  Text(session.last_update)
                    .fontSize(11)
                    .fontColor(Theme.Color.TextTertiary)
                }
                .width('100%')
              }
              .width('100%')
              .padding(12)
              .backgroundColor(this.currentSessionId === session.session_id 
                ? 'rgba(10, 89, 247, 0.1)' 
                : Theme.Color.BackgroundSecondary)
              .borderRadius(12)
              .onClick(() => {
                this.loadSessionGraph(session.session_id)
              })
            }
          })
        }
        .width('100%')
        .layoutWeight(1)
        .scrollBar(BarState.Auto)
      }
    }
    .width('85%')
    .height('70%')
    .backgroundColor(Theme.Color.GlassHeavy)
    .backdropBlur(30)
    .borderRadius(20)
    .shadow(Theme.Shadow.Elevated)
    .padding(8)
    .position({ x: '7.5%', y: '15%' })
    .zIndex(200)
    .transition({ type: TransitionType.Insert, opacity: 0, translate: { x: -100 } })
    .transition({ type: TransitionType.Delete, opacity: 0, translate: { x: -100 } })
  }
}
