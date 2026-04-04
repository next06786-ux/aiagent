/**
 * 知识星图 - 诗云星图风格
 * 深空背景 + 星点粒子 + 发光节点 + 流光连线
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { Theme } from '../common/Theme'
import { SimpleIcon } from '../components/IconRenderer'
import { getAuthService } from '../service/AuthService'
import { getFutureOSService } from '../service/FutureOSService'

// 星点粒子
interface Star {
  x: number
  y: number
  size: number
  opacity: number
  twinkleSpeed: number
  twinklePhase: number
}

// 流光粒子
interface FlowParticle {
  x: number
  y: number
  progress: number  // 0-1 沿连线的进度
  speed: number
  sourceId: string
  targetId: string
}

// 图谱节点
interface GraphNode {
  id: string
  name: string
  type: string
  category?: string
  x: number
  y: number
  z: number           // Z轴深度（伪3D）
  vx: number
  vy: number
  vz: number          // Z轴速度
  radius: number
  glowPhase: number
  connections: number
}

// 图谱连线
interface GraphLink {
  source: string
  target: string
  type: string
  strength: number
}

// 3D投影结果
interface Projection3D {
  screenX: number
  screenY: number
  scale: number
  depth: number
}

// 投影后的节点
interface ProjectedNode {
  node: GraphNode
  screenX: number
  screenY: number
  scale: number
  depth: number
}

// API响应
interface ApiResponse {
  success: boolean
  data: GraphData
  message?: string
}

interface SummaryData {
  bootstrap?: boolean
  user_id?: string
  node_count?: number
  link_count?: number
}

interface GraphData {
  nodes?: NodeData[]
  links?: LinkData[]
  information?: NodeData[]
  sources?: NodeData[]
  relationships?: LinkData[]
  summary?: SummaryData
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
  strength?: number
}

// 分组后的节点
interface CategoryGroup {
  category: string
  nodes: GraphNode[]
}

// 类型颜色映射 - 按社交圈层分色
const TYPE_COLORS: Record<string, string> = {
  // 按圈层分色
  '自己': '#FFD700',        // 金色 - 我自己
  'family': '#FF6B6B',      // 红色 - 家人
  'close_friends': '#4ECDC4', // 青色 - 好友
  'colleagues': '#45B7D1',  // 蓝色 - 同事
  'friends': '#96CEB4',     // 绿色 - 普通朋友
  'weak_ties': '#9B9B9B',   // 灰色 - 弱关系
  // 兼容旧类型
  'Person': '#FF6B9D',
  'Concept': '#00BFFF',
  'Event': '#FFD700',
  'Location': '#00FF7F',
  'Entity': '#00FFFF',
  'default': '#87CEEB'
}

@Entry
@Component
struct KnowledgeStarMap {
  @State userId: string = ''
  @State nodes: GraphNode[] = []
  @State links: GraphLink[] = []
  @State isLoading: boolean = false
  @State loadError: string = ''
  @State isBootstrap: boolean = false
  
  // 人物列表面板
  @State showPersonList: boolean = true
  @State viewMode: string = 'people'
  
  // 3D视角控制
  @State rotationX: number = 0.3    // 俯仰角
  @State rotationY: number = 0      // 水平旋转角
  @State autoRotate: boolean = true // 自动旋转
  
  // 视图控制
  @State offsetX: number = 0
  @State offsetY: number = 0
  @State zoomScale: number = 1.0
  @State isDragging: boolean = false
  @State dragStartX: number = 0
  @State dragStartY: number = 0
  
  // 选中状态
  @State selectedNode: GraphNode | null = null
  @State draggedNode: GraphNode | null = null
  
  // 星空背景
  @State stars: Star[] = []
  @State flowParticles: FlowParticle[] = []
  
  // Canvas
  private settings: RenderingContextSettings = new RenderingContextSettings(true)
  private context: CanvasRenderingContext2D = new CanvasRenderingContext2D(this.settings)
  @State canvasWidth: number = 360
  @State canvasHeight: number = 700
  
  // 3D参数
  private readonly PERSPECTIVE = 500  // 透视距离
  // 动画
  private animationTimer: number = -1
  private frameCount: number = 0
  
  // 力导向参数
  private readonly REPULSION = 2500
  private readonly ATTRACTION = 0.03
  private readonly DAMPING = 0.85
  private readonly CENTER_GRAVITY = 0.01
  private futureOSService = getFutureOSService()

  async aboutToAppear() {
    try {
      const authService = getAuthService()
      this.userId = authService.getCurrentUserId()
    } catch (e) {
      this.userId = 'default_user'
    }
    
    this.initStars()
    this.loadFutureGraphData()
  }

  aboutToDisappear() {
    this.stopAnimation()
  }

  // 初始化星空背景 - 大量微弱星点营造星河感
  initStars() {
    this.stars = []
    const starCount = 200  // 增加星星数量
    
    for (let i = 0; i < starCount; i++) {
      const star: Star = {
        x: Math.random() * 1600 - 800,
        y: Math.random() * 1600 - 800,
        size: Math.random() * 1.2 + 0.3,  // 更小的星点
        opacity: Math.random() * 0.4 + 0.1,  // 更微弱
        twinkleSpeed: 0.015 + Math.random() * 0.01,
        twinklePhase: Math.random() * Math.PI * 2
      }
      this.stars.push(star)
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
          this.startAnimation()
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

  // 解析图谱数据
  async loadFutureGraphData() {
    this.isLoading = true
    this.loadError = ''
    this.isBootstrap = false

    try {
      const result = await this.futureOSService.getKnowledgeView(this.userId, this.viewMode)
      const graphData = result as GraphData
      // 检测后端是否返回的是引导（bootstrap）占位数据
      if (graphData.summary && graphData.summary.bootstrap === true) {
        this.isBootstrap = true
      }
      this.parseGraphData(graphData)
      this.startAnimation()
    } catch (error) {
      const detail = (error as Error).message || '知识星图加载失败'
      this.loadError =
        `无法连接到后端服务\n` +
        `当前后端地址: ${ApiConfig.getBaseUrl()}\n` +
        `请求接口: /api/v5/future-os/knowledge/${this.userId}?view=${this.viewMode}\n` +
        `详细信息: ${detail}\n` +
        `建议检查: 后端是否已启动、端口是否一致、/health 是否可访问`
    } finally {
      this.isLoading = false
    }
  }

  parseGraphData(data: GraphData) {
    // 统计每个节点的连接数
    const connectionCount: Map<string, number> = new Map()
    const linkData = data.links || data.relationships || []
    
    linkData.forEach(link => {
      connectionCount.set(link.source, (connectionCount.get(link.source) || 0) + 1)
      connectionCount.set(link.target, (connectionCount.get(link.target) || 0) + 1)
    })
    
    // 解析节点
    const nodeData = data.nodes || data.information || []
    const layoutRadius = 200
    
    this.nodes = nodeData.map((node, index) => {
      const angle = (index / nodeData.length) * Math.PI * 2
      const connections = connectionCount.get(node.id) || 1
      
      // 随机Z深度 (-100 到 100)
      const z = (Math.random() - 0.5) * 200
      
      return {
        id: node.id,
        name: node.name,
        type: node.type,
        category: node.category,
        x: Math.cos(angle) * layoutRadius + (Math.random() - 0.5) * 100,
        y: Math.sin(angle) * layoutRadius + (Math.random() - 0.5) * 100,
        z: z,
        vx: 0,
        vy: 0,
        vz: 0,
        radius: 3,
        glowPhase: Math.random() * Math.PI * 2,
        connections: connections
      } as GraphNode
    })
    
    // 解析连线
    this.links = linkData.map(link => {
      const graphLink: GraphLink = {
        source: link.source,
        target: link.target,
        type: link.type,
        strength: link.strength || 1
      }
      return graphLink
    })
    
    // 初始化流光粒子
    this.initFlowParticles()
  }

  // 初始化流光粒子 - 大幅减少数量
  initFlowParticles() {
    this.flowParticles = []
    
    // 只在部分连线上放置粒子（最多20个）
    const maxParticles = 15
    const step = Math.max(1, Math.floor(this.links.length / maxParticles))
    
    for (let i = 0; i < this.links.length && this.flowParticles.length < maxParticles; i += step) {
      const link = this.links[i]
      const particle: FlowParticle = {
        x: 0,
        y: 0,
        progress: Math.random(),
        speed: 0.008,
        sourceId: link.source,
        targetId: link.target
      }
      this.flowParticles.push(particle)
    }
  }

  // 启动动画 - 优化帧率
  startAnimation() {
    this.stopAnimation()
    this.frameCount = 0
    
    const animate = () => {
      this.frameCount++
      
      // 前60帧进行力导向布局
      if (this.frameCount <= 60) {
        this.updateForces()
        this.updatePositions()
      }
      
      // 布局完成后降低帧率，只更新动画
      if (this.frameCount > 60) {
        this.updateAnimations()
      }
      
      this.render()
      
      // 布局完成后停止高频动画，改用低频
      if (this.frameCount === 60) {
        this.stopAnimation()
        // 切换到低频动画（每100ms一帧）
        this.animationTimer = setInterval(() => {
          this.updateAnimations()
          this.render()
        }, 100)
      }
    }
    
    this.animationTimer = setInterval(animate, 32)  // 从16ms改为32ms (~30fps)
  }

  stopAnimation() {
    if (this.animationTimer !== -1) {
      clearInterval(this.animationTimer)
      this.animationTimer = -1
    }
  }

  // 更新力导向
  updateForces() {
    // 重置速度
    this.nodes.forEach(node => {
      node.vx = 0
      node.vy = 0
    })

    // 节点间斥力
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const n1 = this.nodes[i]
        const n2 = this.nodes[j]
        
        const dx = n2.x - n1.x
        const dy = n2.y - n1.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        
        const force = this.REPULSION / (dist * dist)
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        
        n1.vx -= fx
        n1.vy -= fy
        n2.vx += fx
        n2.vy += fy
      }
    }

    // 连线引力
    this.links.forEach(link => {
      const source = this.nodes.find(n => n.id === link.source)
      const target = this.nodes.find(n => n.id === link.target)
      
      if (source && target) {
        const dx = target.x - source.x
        const dy = target.y - source.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        
        const force = dist * this.ATTRACTION
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        
        source.vx += fx
        source.vy += fy
        target.vx -= fx
        target.vy -= fy
      }
    })

    // 中心引力
    this.nodes.forEach(node => {
      node.vx -= node.x * this.CENTER_GRAVITY
      node.vy -= node.y * this.CENTER_GRAVITY
    })
  }

  updatePositions() {
    this.nodes.forEach(node => {
      // 速度限制
      const speed = Math.sqrt(node.vx * node.vx + node.vy * node.vy)
      if (speed > 8) {
        node.vx = (node.vx / speed) * 8
        node.vy = (node.vy / speed) * 8
      }
      
      // 更新位置
      node.x += node.vx
      node.y += node.vy
      
      // 阻尼
      node.vx *= this.DAMPING
      node.vy *= this.DAMPING
    })
  }

  // 更新动画效果
  updateAnimations() {
    // 自动旋转
    if (this.autoRotate) {
      this.rotationY += 0.005
    }
    
    // 更新星星闪烁
    this.stars.forEach(star => {
      star.twinklePhase += star.twinkleSpeed
    })
    
    // 更新节点发光
    this.nodes.forEach(node => {
      node.glowPhase += 0.03
    })
    
    // 更新流光粒子
    this.flowParticles.forEach(particle => {
      particle.progress += particle.speed
      if (particle.progress > 1) {
        particle.progress = 0
      }
      
      // 计算粒子位置
      const source = this.nodes.find(n => n.id === particle.sourceId)
      const target = this.nodes.find(n => n.id === particle.targetId)
      
      if (source && target) {
        particle.x = source.x + (target.x - source.x) * particle.progress
        particle.y = source.y + (target.y - source.y) * particle.progress
      }
    })
  }

  // 3D投影：将3D坐标转换为2D屏幕坐标
  project3D(x: number, y: number, z: number): Projection3D {
    // 绕Y轴旋转
    const cosY = Math.cos(this.rotationY)
    const sinY = Math.sin(this.rotationY)
    const x1 = x * cosY - z * sinY
    const z1 = x * sinY + z * cosY
    
    // 绕X轴旋转
    const cosX = Math.cos(this.rotationX)
    const sinX = Math.sin(this.rotationX)
    const y1 = y * cosX - z1 * sinX
    const z2 = y * sinX + z1 * cosX
    
    // 透视投影
    const depth = z2 + this.PERSPECTIVE
    const scale = this.PERSPECTIVE / Math.max(depth, 100)
    
    const result: Projection3D = {
      screenX: x1 * scale,
      screenY: y1 * scale,
      scale: scale,
      depth: depth
    }
    return result
  }

  // 渲染
  render() {
    if (!this.context) return

    const ctx = this.context
    const w = this.canvasWidth
    const h = this.canvasHeight

    // 深空背景
    ctx.fillStyle = '#050510'
    ctx.fillRect(0, 0, w, h)

    ctx.save()
    ctx.translate(w / 2 + this.offsetX, h / 2 + this.offsetY)
    ctx.scale(this.zoomScale, this.zoomScale)

    // 绘制星空背景
    this.drawStars(ctx)
    
    // 绘制连线（3D）
    this.drawLinks3D(ctx)
    
    // 绘制流光粒子
    this.drawFlowParticles(ctx)
    
    // 绘制节点（3D）
    this.drawNodes3D(ctx)

    ctx.restore()
  }

  // 绘制星空
  drawStars(ctx: CanvasRenderingContext2D) {
    this.stars.forEach(star => {
      const twinkle = Math.sin(star.twinklePhase) * 0.3 + 0.7
      const opacity = star.opacity * twinkle
      
      ctx.beginPath()
      ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`
      ctx.fill()
    })
  }

  // 3D连线绘制 - 神经网络风格，彩色发光线条
  drawLinks3D(ctx: CanvasRenderingContext2D) {
    // 先画所有连线的光晕（底层）
    this.links.forEach(link => {
      const source = this.nodes.find(n => n.id === link.source)
      const target = this.nodes.find(n => n.id === link.target)
      
      if (!source || !target) return
      
      const p1 = this.project3D(source.x, source.y, source.z)
      const p2 = this.project3D(target.x, target.y, target.z)
      
      // 根据深度调整透明度
      const avgDepth = (p1.depth + p2.depth) / 2
      const baseAlpha = Math.max(0.02, Math.min(0.15, this.PERSPECTIVE / avgDepth * 0.08))
      
      // 使用源节点的颜色（按社交圈层）
      const color = this.getNodeColor(source.type, source)
      
      // 光晕效果（粗线，低透明度）
      ctx.beginPath()
      ctx.moveTo(p1.screenX, p1.screenY)
      ctx.lineTo(p2.screenX, p2.screenY)
      ctx.strokeStyle = this.hexToRgba(color, baseAlpha * 0.5)
      ctx.lineWidth = 4
      ctx.stroke()
    })
    
    // 再画连线本身（上层，更细更亮）
    this.links.forEach(link => {
      const source = this.nodes.find(n => n.id === link.source)
      const target = this.nodes.find(n => n.id === link.target)
      
      if (!source || !target) return
      
      const p1 = this.project3D(source.x, source.y, source.z)
      const p2 = this.project3D(target.x, target.y, target.z)
      
      const avgDepth = (p1.depth + p2.depth) / 2
      const alpha = Math.max(0.1, Math.min(0.5, this.PERSPECTIVE / avgDepth * 0.2))
      
      const color = this.getNodeColor(source.type, source)
      
      ctx.beginPath()
      ctx.moveTo(p1.screenX, p1.screenY)
      ctx.lineTo(p2.screenX, p2.screenY)
      ctx.strokeStyle = this.hexToRgba(color, alpha)
      ctx.lineWidth = 0.8
      ctx.stroke()
    })
  }

  // 绘制流光粒子（3D）
  drawFlowParticles(ctx: CanvasRenderingContext2D) {
    this.flowParticles.forEach(particle => {
      const source = this.nodes.find(n => n.id === particle.sourceId)
      const target = this.nodes.find(n => n.id === particle.targetId)
      
      if (!source || !target) return
      
      // 计算粒子的3D位置（在连线上插值）
      const px = source.x + (target.x - source.x) * particle.progress
      const py = source.y + (target.y - source.y) * particle.progress
      const pz = source.z + (target.z - source.z) * particle.progress
      
      const proj = this.project3D(px, py, pz)
      
      // 根据深度调整大小和透明度
      const size = 2 * proj.scale
      const alpha = Math.min(0.9, proj.scale * 0.8)
      
      ctx.beginPath()
      ctx.arc(proj.screenX, proj.screenY, size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`
      ctx.fill()
    })
  }

  // 3D节点绘制
  drawNodes3D(ctx: CanvasRenderingContext2D) {
    // 计算所有节点的投影并排序
    const projectedNodes: ProjectedNode[] = []
    
    this.nodes.forEach(node => {
      const proj = this.project3D(node.x, node.y, node.z)
      const pn: ProjectedNode = {
        node: node,
        screenX: proj.screenX,
        screenY: proj.screenY,
        scale: proj.scale,
        depth: proj.depth
      }
      projectedNodes.push(pn)
    })
    
    // 按深度排序，远的先画
    projectedNodes.sort((a, b) => b.depth - a.depth)
    
    // 绘制节点 - 星星风格，多层发光
    projectedNodes.forEach(pn => {
      const node = pn.node
      const color = this.getNodeColor(node.type, node)
      const isSelected = this.selectedNode?.id === node.id
      
      // 根据深度计算大小和透明度
      const baseSize = 2.5
      const pointSize = baseSize * pn.scale
      const alpha = Math.max(0.3, Math.min(1.0, pn.scale))
      
      // 最外层光晕（大范围，很淡）
      ctx.beginPath()
      ctx.arc(pn.screenX, pn.screenY, pointSize * 6, 0, Math.PI * 2)
      ctx.fillStyle = this.hexToRgba(color, 0.05 * alpha)
      ctx.fill()
      
      // 中层光晕
      ctx.beginPath()
      ctx.arc(pn.screenX, pn.screenY, pointSize * 3, 0, Math.PI * 2)
      ctx.fillStyle = this.hexToRgba(color, 0.15 * alpha)
      ctx.fill()
      
      // 内层光晕
      ctx.beginPath()
      ctx.arc(pn.screenX, pn.screenY, pointSize * 1.5, 0, Math.PI * 2)
      ctx.fillStyle = this.hexToRgba(color, 0.4 * alpha)
      ctx.fill()
      
      // 核心亮点
      ctx.beginPath()
      ctx.arc(pn.screenX, pn.screenY, pointSize, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.fill()
      
      // 中心白点（最亮）
      ctx.beginPath()
      ctx.arc(pn.screenX, pn.screenY, pointSize * 0.5, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.9})`
      ctx.fill()
      
      // 选中状态 - 脉冲光环
      if (isSelected) {
        ctx.beginPath()
        ctx.arc(pn.screenX, pn.screenY, pointSize * 8, 0, Math.PI * 2)
        ctx.strokeStyle = this.hexToRgba(color, 0.6)
        ctx.lineWidth = 1.5
        ctx.stroke()
      }
    })
    
    // 绘制文字（只显示近处的）
    ctx.font = '11px sans-serif'
    ctx.textBaseline = 'middle'
    
    projectedNodes.forEach(pn => {
      // 只有近处的节点显示文字
      if (pn.scale < 0.7) return
      
      const node = pn.node
      const color = this.getNodeColor(node.type, node)
      const isSelected = this.selectedNode?.id === node.id
      const alpha = Math.min(1.0, pn.scale)
      
      ctx.fillStyle = isSelected ? '#FFFFFF' : this.hexToRgba(color, alpha * 0.9)
      ctx.textAlign = 'left'
      ctx.fillText(node.name, pn.screenX + 10, pn.screenY)
    })
  }

  // 保留旧函数以防需要
  drawLinks(ctx: CanvasRenderingContext2D) {
    this.drawLinks3D(ctx)
  }

  drawNodes(ctx: CanvasRenderingContext2D) {
    this.drawNodes3D(ctx)
  }

  // 获取节点颜色 - 优先使用category（社交圈层）
  getNodeColor(typeOrCategory: string, node?: GraphNode): string {
    // 如果传入了node，优先使用category
    if (node && node.category) {
      return TYPE_COLORS[node.category] || TYPE_COLORS[node.type] || TYPE_COLORS['default']
    }
    return TYPE_COLORS[typeOrCategory] || TYPE_COLORS['default']
  }

  // 颜色工具函数
  hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }

  lightenColor(hex: string, percent: number): string {
    const num = parseInt(hex.slice(1), 16)
    const amt = Math.round(2.55 * percent)
    const R = Math.min(255, (num >> 16) + amt)
    const G = Math.min(255, (num >> 8 & 0x00FF) + amt)
    const B = Math.min(255, (num & 0x0000FF) + amt)
    return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)
  }

  darkenColor(hex: string, percent: number): string {
    const num = parseInt(hex.slice(1), 16)
    const amt = Math.round(2.55 * percent)
    const R = Math.max(0, (num >> 16) - amt)
    const G = Math.max(0, (num >> 8 & 0x00FF) - amt)
    const B = Math.max(0, (num & 0x0000FF) - amt)
    return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)
  }


  // 触摸事件处理
  handleTouchStart(event: TouchEvent) {
    if (event.touches.length === 1) {
      const touch = event.touches[0]
      // 转换为相对于画布中心的坐标
      const screenX = (touch.x - this.canvasWidth / 2 - this.offsetX) / this.zoomScale
      const screenY = (touch.y - this.canvasHeight / 2 - this.offsetY) / this.zoomScale
      
      // 检测点击节点（使用屏幕坐标）
      const clickedNode = this.findNodeAt(screenX, screenY)
      
      if (clickedNode) {
        this.selectedNode = clickedNode
        this.autoRotate = false  // 点击节点时停止自动旋转
      } else {
        this.isDragging = true
        this.dragStartX = touch.x
        this.dragStartY = touch.y
        this.selectedNode = null
      }
    }
  }

  handleTouchMove(event: TouchEvent) {
    if (event.touches.length === 1) {
      const touch = event.touches[0]
      
      if (this.draggedNode) {
        // 拖动节点（暂时禁用，3D模式下复杂）
      } else if (this.isDragging) {
        // 拖动旋转3D视角
        const dx = touch.x - this.dragStartX
        const dy = touch.y - this.dragStartY
        
        this.rotationY += dx * 0.01
        this.rotationX += dy * 0.01
        
        // 限制俯仰角
        this.rotationX = Math.max(-1.2, Math.min(1.2, this.rotationX))
        
        this.dragStartX = touch.x
        this.dragStartY = touch.y
        
        // 拖动时停止自动旋转
        this.autoRotate = false
        
        // 立即渲染
        this.render()
      }
    }
  }

  handleTouchEnd() {
    this.draggedNode = null
    this.isDragging = false
  }

  findNodeAt(x: number, y: number): GraphNode | null {
    // 3D模式下需要检查投影后的位置
    for (const node of this.nodes) {
      const proj = this.project3D(node.x, node.y, node.z)
      const dx = x - proj.screenX
      const dy = y - proj.screenY
      const dist = Math.sqrt(dx * dx + dy * dy)
      
      // 点击范围根据缩放调整
      if (dist <= 25 * proj.scale) {
        return node
      }
    }
    return null
  }

  // 缩放控制
  zoomIn() {
    this.zoomScale = Math.min(this.zoomScale * 1.3, 3.0)
  }

  zoomOut() {
    this.zoomScale = Math.max(this.zoomScale / 1.3, 0.3)
  }

  resetView() {
    this.offsetX = 0
    this.offsetY = 0
    this.zoomScale = 1.0
    this.rotationX = 0.3
    this.rotationY = 0
    this.autoRotate = true
  }

  switchView(nextView: string) {
    if (this.viewMode === nextView) {
      return
    }
    this.viewMode = nextView
    this.selectedNode = null
    this.loadFutureGraphData()
  }

  // 获取连接的节点
  getConnectedNodes(nodeId: string): GraphNode[] {
    const connectedIds: Set<string> = new Set()
    
    this.links.forEach(link => {
      if (link.source === nodeId) {
        connectedIds.add(link.target)
      } else if (link.target === nodeId) {
        connectedIds.add(link.source)
      }
    })
    
    return this.nodes.filter(n => connectedIds.has(n.id))
  }

  build() {
    Stack() {
      // Canvas 画布
      Canvas(this.context)
        .width('100%')
        .height('100%')
        .backgroundColor('#0a0a1a')
        .onReady(() => {
          this.canvasWidth = 360
          this.canvasHeight = 700
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
            .onClick(() => this.loadFutureGraphData())
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .backgroundColor('rgba(10, 10, 26, 0.95)')
      }

      // 顶部导航栏
      Row() {
        Button({ type: ButtonType.Circle }) {
          SimpleIcon({ iconName: 'back', iconSize: 20, color: '#FFFFFF' })
        }
        .width(40)
        .height(40)
        .backgroundColor('rgba(255, 255, 255, 0.1)')
        .onClick(() => router.back())

        Column({ space: 2 }) {
          Text('知识星图')
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .fontColor('#FFFFFF')
          
          if (this.nodes.length > 0) {
            Text(this.isBootstrap
              ? `引导模式 · 当前账号暂无图谱数据`
              : `${this.nodes.length} 个知识节点 · ${this.links.length} 条关联`)
              .fontSize(11)
              .fontColor(this.isBootstrap ? 'rgba(255, 200, 100, 0.9)' : 'rgba(255, 255, 255, 0.5)')
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
        .onClick(() => this.loadFutureGraphData())
      }
      .width('100%')
      .height(56)
      .padding({ left: 16, right: 16 })
      .backgroundColor('rgba(10, 10, 26, 0.8)')
      .backdropBlur(20)
      .position({ x: 0, y: 0 })

      Row({ space: 10 }) {
        Button(this.viewMode === 'people' ? '人物关系视图' : '切到人物视图')
          .height(32)
          .fontSize(12)
          .fontColor('#FFFFFF')
          .backgroundColor(this.viewMode === 'people' ? 'rgba(90, 169, 255, 0.35)' : 'rgba(255,255,255,0.08)')
          .borderRadius(16)
          .onClick(() => this.switchView('people'))

        Button(this.viewMode === 'signals' ? '其它节点视图' : '切到其它节点')
          .height(32)
          .fontSize(12)
          .fontColor('#FFFFFF')
          .backgroundColor(this.viewMode === 'signals' ? 'rgba(72, 187, 120, 0.32)' : 'rgba(255,255,255,0.08)')
          .borderRadius(16)
          .onClick(() => this.switchView('signals'))
      }
      .padding({ left: 16, right: 16, top: 64 })
      .position({ x: 0, y: 0 })

      // 左侧人物列表面板
      if (this.nodes.length > 0) {
        Column() {
          // 面板头部 - 可点击展开/收起
          Row({ space: 8 }) {
            Text(this.showPersonList ? '◀' : '▶')
              .fontSize(12)
              .fontColor('rgba(255, 255, 255, 0.6)')
            
            if (this.showPersonList) {
              Text(this.viewMode === 'people' ? '人物列表' : '节点列表')
                .fontSize(13)
                .fontWeight(FontWeight.Medium)
                .fontColor('#FFFFFF')
              
              Blank()
              
              Text(`${this.nodes.length}个`)
                .fontSize(11)
                .fontColor('rgba(255, 255, 255, 0.5)')
            }
          }
          .width('100%')
          .padding({ left: 12, right: 12, top: 10, bottom: 10 })
          .onClick(() => {
            this.showPersonList = !this.showPersonList
          })

          // 人物列表内容
          if (this.showPersonList) {
            Scroll() {
              Column({ space: 4 }) {
                ForEach(this.getGroupedNodes(), (group: CategoryGroup) => {
                  // 分组标题
                  Row({ space: 6 }) {
                    Circle({ width: 8, height: 8 })
                      .fill(this.getNodeColor(group.category))
                    Text(this.getCategoryDisplayName(group.category))
                      .fontSize(11)
                      .fontColor(this.getNodeColor(group.category))
                    Text(`(${group.nodes.length})`)
                      .fontSize(10)
                      .fontColor('rgba(255, 255, 255, 0.4)')
                  }
                  .width('100%')
                  .padding({ left: 12, right: 12, top: 8, bottom: 4 })

                  // 该分组的人物
                  ForEach(group.nodes, (node: GraphNode) => {
                    Row({ space: 8 }) {
                      // 小圆点
                      Circle({ width: 6, height: 6 })
                        .fill(this.getNodeColor(node.type, node))
                      
                      Text(node.name)
                        .fontSize(12)
                        .fontColor(this.selectedNode?.id === node.id ? '#FFFFFF' : 'rgba(255, 255, 255, 0.8)')
                        .maxLines(1)
                        .textOverflow({ overflow: TextOverflow.Ellipsis })
                        .layoutWeight(1)
                      
                      // 关联数
                      Text(`${node.connections}`)
                        .fontSize(10)
                        .fontColor('rgba(255, 255, 255, 0.4)')
                    }
                    .width('100%')
                    .padding({ left: 20, right: 12, top: 6, bottom: 6 })
                    .backgroundColor(this.selectedNode?.id === node.id ? 'rgba(255, 255, 255, 0.15)' : 'transparent')
                    .borderRadius(4)
                    .onClick(() => {
                      this.selectedNode = node
                      this.autoRotate = false
                    })
                  })
                })
              }
              .padding({ bottom: 20 })
            }
            .scrollBar(BarState.Off)
            .layoutWeight(1)
          }
        }
        .width(this.showPersonList ? 140 : 36)
        .height(this.showPersonList ? '60%' : 40)
        .backgroundColor('rgba(10, 10, 30, 0.85)')
        .backdropBlur(20)
        .borderRadius(12)
        .position({ x: 12, y: 130 })
        .animation({ duration: 200, curve: Curve.EaseOut })
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

      // 底部节点详情面板
      if (this.selectedNode) {
        Column({ space: 12 }) {
          // 拖动条
          Row()
            .width(40)
            .height(4)
            .backgroundColor('rgba(255, 255, 255, 0.2)')
            .borderRadius(2)

          Row({ space: 16 }) {
            // 节点颜色圆
            Stack() {
              Circle({ width: 50, height: 50 })
                .fill(this.getNodeColor(this.selectedNode.type, this.selectedNode))
                .shadow({ radius: 12, color: this.getNodeColor(this.selectedNode.type, this.selectedNode), offsetY: 0 })
              
              Text(this.selectedNode.name.substring(0, 1))
                .fontSize(20)
                .fontWeight(FontWeight.Bold)
                .fontColor('#FFFFFF')
            }

            Column({ space: 4 }) {
              Text(this.selectedNode.name)
                .fontSize(18)
                .fontWeight(FontWeight.Bold)
                .fontColor('#FFFFFF')
              
              Row({ space: 8 }) {
                Text(this.selectedNode.category || this.selectedNode.type)
                  .fontSize(12)
                  .fontColor(this.getNodeColor(this.selectedNode.type, this.selectedNode))
                  .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                  .backgroundColor('rgba(255, 255, 255, 0.1)')
                  .borderRadius(4)
                
                Text(`${this.selectedNode.connections} 个关联`)
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
            .onClick(() => { this.selectedNode = null })
          }
          .width('100%')

          // 关联节点
          if (this.getConnectedNodes(this.selectedNode.id).length > 0) {
            Column({ space: 8 }) {
              Text('关联节点')
                .fontSize(13)
                .fontColor('rgba(255, 255, 255, 0.5)')
                .alignSelf(ItemAlign.Start)

              Flex({ wrap: FlexWrap.Wrap }) {
                ForEach(this.getConnectedNodes(this.selectedNode.id).slice(0, 6), (node: GraphNode) => {
                  Row({ space: 6 }) {
                    Circle({ width: 8, height: 8 })
                      .fill(this.getNodeColor(node.type, node))
                    Text(node.name)
                      .fontSize(12)
                      .fontColor('#FFFFFF')
                  }
                  .padding({ left: 10, right: 10, top: 6, bottom: 6 })
                  .margin({ right: 8, bottom: 8 })
                  .backgroundColor('rgba(255, 255, 255, 0.08)')
                  .borderRadius(14)
                  .onClick(() => { this.selectedNode = node })
                })
              }
            }
            .width('100%')
          }
        }
        .width('100%')
        .padding(20)
        .backgroundColor('rgba(20, 20, 40, 0.95)')
        .backdropBlur(30)
        .borderRadius({ topLeft: 24, topRight: 24 })
        .position({ x: 0, y: '100%' })
        .translate({ y: -200 })
      }

      // 图例 - 按社交圈层显示
      Column({ space: 6 }) {
        ForEach(this.getUsedCategories(), (category: string) => {
          Row({ space: 6 }) {
            Circle({ width: 8, height: 8 })
              .fill(this.getNodeColor(category))
            Text(this.getCategoryDisplayName(category))
              .fontSize(10)
              .fontColor('rgba(255, 255, 255, 0.6)')
          }
        })
      }
      .padding(10)
      .backgroundColor('rgba(0, 0, 0, 0.3)')
      .borderRadius(8)
      .position({ x: 12, y: 70 })
    }
    .width('100%')
    .height('100%')
  }

  // 获取使用的类别列表（社交圈层）
  getUsedCategories(): string[] {
    const categories: Set<string> = new Set()
    this.nodes.forEach(node => {
      if (node.category) {
        categories.add(node.category)
      } else {
        categories.add(node.type)
      }
    })
    return Array.from(categories).slice(0, 8)
  }

  // 按社交圈层分组节点
  getGroupedNodes(): CategoryGroup[] {
    const categoryOrder = ['自己', 'family', 'close_friends', 'colleagues', 'friends', 'weak_ties']
    const groups: Map<string, GraphNode[]> = new Map()
    
    // 初始化分组
    categoryOrder.forEach(cat => groups.set(cat, []))
    
    // 分配节点到分组
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
    
    // 转换为数组，过滤空分组
    const result: CategoryGroup[] = []
    categoryOrder.forEach(cat => {
      const nodes = groups.get(cat)
      if (nodes && nodes.length > 0) {
        const group: CategoryGroup = {
          category: cat,
          nodes: nodes
        }
        result.push(group)
      }
    })
    
    // 添加其他未知分类
    groups.forEach((nodes, cat) => {
      if (!categoryOrder.includes(cat) && nodes.length > 0) {
        const group: CategoryGroup = {
          category: cat,
          nodes: nodes
        }
        result.push(group)
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

  // 获取使用的类型列表（保留兼容）
  getUsedTypes(): string[] {
    const types: Set<string> = new Set()
    this.nodes.forEach(node => types.add(node.type))
    return Array.from(types).slice(0, 8)
  }
}
