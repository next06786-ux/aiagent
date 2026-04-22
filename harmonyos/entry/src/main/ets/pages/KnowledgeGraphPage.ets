/**
 * 知识星图页面 - OpenGL ES 3D渲染版本
 * 显示职业、教育、人际关系三个星图
 */
import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { KnowledgeGraphService } from '../services/KnowledgeGraphService';
import { AuthService } from '../services/AuthService';
import { StarMapData, KnowledgeNode, KnowledgeEdge } from '../models/KnowledgeNode';
import { AppConstants } from '../constants/AppConstants';
import { StarMapNative, StarNode3D, StarLink3D, NodeScreenPosition } from '../utils/StarMapNative';

// 定义对象字面量接口
class StarNode3DImpl implements StarNode3D {
  id: string = '';
  name: string = '';
  category: string = '';
  x: number = 0;
  y: number = 0;
  z: number = 0;
  connections: number = 0;
}

class StarLink3DImpl implements StarLink3D {
  sourceIdx: number = 0;
  targetIdx: number = 0;
  strength: number = 1.0;
}

@Entry
@Component
struct KnowledgeGraphPage {
  @State currentTab: number = 0;
  @State isLoading: boolean = true;
  @State careerStarMap: StarMapData | null = null;
  @State educationStarMap: StarMapData | null = null;
  @State relationshipStarMap: StarMapData | null = null;
  @State selectedNodeIndex: number = -1;
  @State nodePositions: NodeScreenPosition[] = [];
  
  private kgService = new KnowledgeGraphService();
  private authService = new AuthService();
  private userId: string = '';
  private starMapNative: StarMapNative = new StarMapNative();
  private xComponentId: string = 'starmap_xcomponent';
  
  // 触摸控制
  private lastTouchX: number = 0;
  private lastTouchY: number = 0;
  private rotationX: number = 0.3;
  private rotationY: number = 0.0;
  private zoom: number = 1.0;
  private animationTimer: number = -1;
  private lastFrameTime: number = 0;
  
  private tabs = ['职业星图', '人际关系', '教育星图'];
  
  aboutToAppear() {
    console.info('[KnowledgeGraphPage] aboutToAppear - 页面初始化');
    this.initPage();
    this.startAnimation();
  }
  
  aboutToDisappear() {
    console.info('[KnowledgeGraphPage] aboutToDisappear - 页面销毁');
    this.stopAnimation();
    this.starMapNative.destroy();
  }
  
  async initPage() {
    console.info('[KnowledgeGraphPage] initPage - 开始初始化');
    try {
      const userInfo = await this.authService.getUserInfo();
      if (userInfo) {
        this.userId = userInfo.user_id;
        console.info('[KnowledgeGraphPage] 获取到userId:', this.userId);
      } else {
        console.warn('[KnowledgeGraphPage] 未获取到用户信息，使用测试userId');
        this.userId = 'test_user_001';
      }
    } catch (error) {
      console.error('[KnowledgeGraphPage] 获取用户信息失败:', error);
      this.userId = 'test_user_001';
    }
    
    // 无论如何都加载数据
    await this.loadStarMaps();
  }
  
  /**
   * 启动动画循环
   */
  startAnimation() {
    this.lastFrameTime = Date.now();
    this.animationTimer = setInterval(() => {
      const now = Date.now();
      const deltaTime = (now - this.lastFrameTime) / 1000.0;
      this.lastFrameTime = now;
      
      // 更新动画
      this.starMapNative.updateAnimation(deltaTime);
      
      // 渲染
      this.starMapNative.renderFrame();
      
      // 更新节点屏幕位置（用于标签）
      this.nodePositions = this.starMapNative.getNodeScreenPositions();
    }, 16); // 60 FPS
  }
  
  /**
   * 停止动画循环
   */
  stopAnimation() {
    if (this.animationTimer !== -1) {
      clearInterval(this.animationTimer);
      this.animationTimer = -1;
    }
  }
  
  /**
   * 加载星图数据 - 直接从后端加载，不使用测试数据
   * 按照Web端逻辑：职业星图优先
   */
  async loadStarMaps() {
    console.info('[KnowledgeGraphPage] loadStarMaps - 开始加载, userId:', this.userId);
    this.isLoading = true;
    
    try {
      // 按照Web端顺序：职业、人际关系、教育
      const results = await Promise.all([
        this.kgService.getCareerStarMap(this.userId),
        this.kgService.getRelationshipStarMap(this.userId),
        this.kgService.getEducationStarMap(this.userId)
      ]);
      
      this.careerStarMap = results[0];
      this.relationshipStarMap = results[1];
      this.educationStarMap = results[2];
      
      console.info('[KnowledgeGraphPage] 星图数据加载完成:', {
        career: this.careerStarMap?.nodes.length || 0,
        relationship: this.relationshipStarMap?.nodes.length || 0,
        education: this.educationStarMap?.nodes.length || 0
      });
      
      // 加载当前标签页的星图到Native渲染器
      this.loadCurrentStarMapToNative();
    } catch (error) {
      console.error('[KnowledgeGraphPage] 加载星图失败:', error);
      promptAction.showToast({ 
        message: '加载星图失败: ' + (error.message || '未知错误')
      });
      
      // 不再使用测试数据，直接显示错误
      this.careerStarMap = null;
      this.relationshipStarMap = null;
      this.educationStarMap = null;
    } finally {
      // 确保一定会设置为false
      this.isLoading = false;
      console.info('[KnowledgeGraphPage] isLoading设置为false');
    }
  }
  
  /**
   * 加载当前星图到Native渲染器
   * 职业视图使用后端返回的position（同心圆布局），不使用力导向
   */
  loadCurrentStarMapToNative() {
    console.info('[KnowledgeGraphPage] loadCurrentStarMapToNative - 开始');
    
    // 检查Native模块是否就绪
    if (!this.starMapNative.isNativeReady()) {
      console.warn('[KnowledgeGraphPage] Native模块未就绪，延迟加载');
      setTimeout(() => {
        this.loadCurrentStarMapToNative();
      }, 200);
      return;
    }
    
    const starMap = this.getCurrentStarMap();
    
    if (!starMap) {
      console.error('[KnowledgeGraphPage] getCurrentStarMap返回null');
      return;
    }
    
    if (starMap.nodes.length === 0) {
      console.warn('[KnowledgeGraphPage] 星图节点数为0');
      return;
    }
    
    console.info('[KnowledgeGraphPage] 当前星图:', {
      tab: this.currentTab,
      nodes: starMap.nodes.length,
      edges: starMap.edges.length,
      layers: starMap.layers.length
    });
    
    // 判断是否为职业视图
    const isCareerView = this.currentTab === 0;
    
    // 转换节点数据为3D格式
    const nodes3D: StarNode3D[] = starMap.nodes.map((node, index) => {
      // 计算连接数
      const connections = starMap.edges.filter(e => 
        e.from === node.id || e.to === node.id
      ).length;
      
      const node3d = new StarNode3DImpl();
      node3d.id = node.id;
      node3d.name = node.label;
      node3d.category = node.layer || 'default';
      
      // 职业视图：直接使用后端返回的position（同心圆布局）
      // 其他视图：使用随机位置，后续用力导向布局
      if (isCareerView && node.x !== undefined && node.y !== undefined && node.z !== undefined) {
        node3d.x = node.x;
        node3d.y = node.y;
        node3d.z = node.z;
      } else {
        node3d.x = (Math.random() - 0.5) * 100;
        node3d.y = (Math.random() - 0.5) * 100;
        node3d.z = (Math.random() - 0.5) * 100;
      }
      
      node3d.connections = connections;
      return node3d;
    });
    
    // 转换连线数据
    const links3D: StarLink3D[] = starMap.edges.map(edge => {
      const sourceIdx = starMap.nodes.findIndex(n => n.id === edge.from);
      const targetIdx = starMap.nodes.findIndex(n => n.id === edge.to);
      
      const link = new StarLink3DImpl();
      link.sourceIdx = sourceIdx;
      link.targetIdx = targetIdx;
      link.strength = edge.weight || 1.0;
      return link;
    }).filter(link => link.sourceIdx >= 0 && link.targetIdx >= 0);
    
    console.info(`[KnowledgeGraphPage] 加载星图到Native: ${nodes3D.length}个节点, ${links3D.length}条连线`);
    
    // 设置数据到Native渲染器
    this.starMapNative.setNodes(nodes3D);
    this.starMapNative.setLinks(links3D);
    
    // 职业视图：不使用力导向布局（已有同心圆布局）
    // 其他视图：使用力导向布局
    if (!isCareerView) {
      console.info('[KnowledgeGraphPage] 开始力导向布局计算');
      for (let i = 0; i < 50; i++) {
        this.starMapNative.updateForceLayout();
      }
    } else {
      console.info('[KnowledgeGraphPage] 职业视图使用后端同心圆布局，跳过力导向计算');
    }
    
    // 重置相机
    this.starMapNative.resetTarget();
    
    // 立即渲染一帧
    this.starMapNative.renderFrame();
    
    console.info('[KnowledgeGraphPage] 星图加载完成');
  }
  
  /**
   * 获取当前星图 - 按照新的标签页顺序
   */
  getCurrentStarMap(): StarMapData | null {
    switch (this.currentTab) {
      case 0:
        return this.careerStarMap;      // 职业星图
      case 1:
        return this.relationshipStarMap; // 人际关系
      case 2:
        return this.educationStarMap;    // 教育星图
      default:
        return null;
    }
  }
  
  /**
   * 处理触摸事件
   */
  handleTouch(event: TouchEvent) {
    if (event.type === TouchType.Down) {
      this.lastTouchX = event.touches[0].x;
      this.lastTouchY = event.touches[0].y;
      
      // 点击测试
      const hitIndex = this.starMapNative.hitTest(event.touches[0].x, event.touches[0].y);
      if (hitIndex >= 0) {
        console.info(`点击节点: ${hitIndex}`);
        this.selectedNodeIndex = hitIndex;
        this.starMapNative.selectNode(hitIndex);
        this.starMapNative.focusOnNode(hitIndex);
        
        // 显示节点信息
        const relations = this.starMapNative.getNodeRelations(hitIndex);
        console.info(`节点关系: ${JSON.stringify(relations)}`);
      }
    } else if (event.type === TouchType.Move) {
      const deltaX = event.touches[0].x - this.lastTouchX;
      const deltaY = event.touches[0].y - this.lastTouchY;
      
      // 旋转控制
      this.rotationY += deltaX * 0.01;
      this.rotationX += deltaY * 0.01;
      
      // 限制X轴旋转范围
      this.rotationX = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, this.rotationX));
      
      this.starMapNative.setRotation(this.rotationX, this.rotationY);
      
      this.lastTouchX = event.touches[0].x;
      this.lastTouchY = event.touches[0].y;
    }
  }
  
  /**
   * 处理缩放手势
   */
  handlePinch(event: GestureEvent) {
    if (event.scale) {
      this.zoom *= event.scale;
      this.zoom = Math.max(0.3, Math.min(3.0, this.zoom));
      this.starMapNative.setZoom(this.zoom);
    }
  }
  
  build() {
    Column() {
      // 顶部导航
      Row() {
        Button('返回')
          .fontSize(14)
          .backgroundColor(Color.Transparent)
          .fontColor(Color.White)
          .onClick(() => {
            router.back();
          })
        
        Blank()
        
        Text('知识星图')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
      }
      .width('100%')
      .padding(16)
      .backgroundColor('rgba(10, 25, 41, 0.8)')
      
      // 标签页
      Tabs({ index: this.currentTab }) {
        ForEach(this.tabs, (tab: string, index: number) => {
          TabContent() {
            if (this.isLoading) {
              Column() {
                LoadingProgress()
                  .width(50)
                  .height(50)
                  .color(AppConstants.COLORS.PRIMARY)
                
                Text('加载中...')
                  .fontSize(14)
                  .fontColor('#999')
                  .margin({ top: 16 })
              }
              .width('100%')
              .height('100%')
              .justifyContent(FlexAlign.Center)
            } else {
              this.buildStarMapView()
            }
          }
          .tabBar(tab)
        })
      }
      .barMode(BarMode.Fixed)
      .barBackgroundColor('rgba(10, 25, 41, 0.8)')
      .onChange((index: number) => {
        this.currentTab = index;
        this.loadCurrentStarMapToNative();
      })
      .layoutWeight(1)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#0A1929')
  }
  
  /**
   * 构建星图视图 - 使用 XComponent + OpenGL ES
   */
  @Builder
  buildStarMapView() {
    if (!this.getCurrentStarMap() || this.getCurrentStarMap()!.nodes.length === 0) {
      Column() {
        Text('暂无数据')
          .fontSize(16)
          .fontColor('#999')
      }
      .width('100%')
      .height('100%')
      .justifyContent(FlexAlign.Center)
    } else {
      Stack() {
        // OpenGL ES 渲染层
        XComponent({
          id: this.xComponentId,
          type: 'surface',
          libraryname: 'starmap_render'
        })
          .width('100%')
          .height('100%')
          .onLoad((context?: ESObject) => {
            console.info('[KnowledgeGraphPage] XComponent onLoad - Native模块已加载');
            if (context) {
              // 将Native模块引用传递给StarMapNative
              this.starMapNative.setNativeModule(context);
              console.info('[KnowledgeGraphPage] Native模块已设置到StarMapNative');
              
              // 延迟加载星图数据，确保OpenGL上下文已初始化
              setTimeout(() => {
                console.info('[KnowledgeGraphPage] 开始加载星图数据到Native');
                this.loadCurrentStarMapToNative();
              }, 100);
            } else {
              console.error('[KnowledgeGraphPage] XComponent context为空');
            }
          })
          .onDestroy(() => {
            console.info('[KnowledgeGraphPage] XComponent destroyed');
          })
        
        // 触摸控制层
        Column()
          .width('100%')
          .height('100%')
          .onTouch((event: TouchEvent) => {
            this.handleTouch(event);
          })
          .gesture(
            PinchGesture()
              .onActionUpdate((event: GestureEvent) => {
                this.handlePinch(event);
              })
          )
        
        // 节点标签层（Canvas 2D）
        Canvas(this.labelContext)
          .width('100%')
          .height('100%')
          .onReady(() => {
            console.info('[KnowledgeGraphPage] Label canvas ready');
          })
        
        // 控制按钮
        Column() {
          Button('重置视角')
            .fontSize(12)
            .padding({ left: 12, right: 12, top: 6, bottom: 6 })
            .backgroundColor('rgba(255, 255, 255, 0.2)')
            .fontColor(Color.White)
            .onClick(() => {
              this.rotationX = 0.3;
              this.rotationY = 0.0;
              this.zoom = 1.0;
              this.starMapNative.resetTarget();
            })
          
          Text(`节点: ${this.getCurrentStarMap()!.nodes.length}`)
            .fontSize(12)
            .fontColor('rgba(255, 255, 255, 0.7)')
            .margin({ top: 8 })
          
          Text(`连接: ${this.getCurrentStarMap()!.edges.length}`)
            .fontSize(12)
            .fontColor('rgba(255, 255, 255, 0.7)')
            .margin({ top: 4 })
          
          Text(this.starMapNative.isNativeReady() ? '✓ Native就绪' : '⚠ Native未就绪')
            .fontSize(10)
            .fontColor(this.starMapNative.isNativeReady() ? '#4CAF50' : '#FFC107')
            .margin({ top: 8 })
        }
        .alignItems(HorizontalAlign.End)
        .padding(16)
      }
      .width('100%')
      .height('100%')
      .alignContent(Alignment.TopEnd)
    }
  }
  
  private labelSettings: RenderingContextSettings = new RenderingContextSettings(true);
  private labelContext: CanvasRenderingContext2D = new CanvasRenderingContext2D(this.labelSettings);
}
