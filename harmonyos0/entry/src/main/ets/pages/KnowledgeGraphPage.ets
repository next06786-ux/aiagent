/**
 * 知识星图页面
 * 显示职业、教育、人际关系三个星图
 */
import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { KnowledgeGraphService } from '../services/KnowledgeGraphService';
import { AuthService } from '../services/AuthService';
import { StarMapData, KnowledgeNode } from '../models/KnowledgeNode';
import { AppConstants } from '../constants/AppConstants';

@Entry
@Component
struct KnowledgeGraphPage {
  @State currentTab: number = 0;
  @State isLoading: boolean = true;
  @State careerStarMap: StarMapData | null = null;
  @State educationStarMap: StarMapData | null = null;
  @State relationshipStarMap: StarMapData | null = null;
  
  private kgService = new KnowledgeGraphService();
  private authService = new AuthService();
  private userId: string = '';
  
  private tabs = ['职业星图', '教育星图', '人际关系'];
  
  aboutToAppear() {
    this.initPage();
  }
  
  async initPage() {
    const userInfo = await this.authService.getUserInfo();
    if (userInfo) {
      this.userId = userInfo.user_id;
      await this.loadStarMaps();
    }
  }
  
  /**
   * 加载星图数据
   */
  async loadStarMaps() {
    this.isLoading = true;
    
    try {
      const results = await Promise.all([
        this.kgService.getCareerStarMap(this.userId),
        this.kgService.getEducationStarMap(this.userId),
        this.kgService.getRelationshipStarMap(this.userId)
      ]);
      
      this.careerStarMap = results[0];
      this.educationStarMap = results[1];
      this.relationshipStarMap = results[2];
    } catch (error) {
      console.error('加载星图失败:', error);
      promptAction.showToast({ message: '加载星图失败' });
    } finally {
      this.isLoading = false;
    }
  }
  
  /**
   * 获取当前星图
   */
  getCurrentStarMap(): StarMapData | null {
    switch (this.currentTab) {
      case 0:
        return this.careerStarMap;
      case 1:
        return this.educationStarMap;
      case 2:
        return this.relationshipStarMap;
      default:
        return null;
    }
  }
  
  build() {
    Column() {
      // 顶部导航
      Row() {
        Button('返回')
          .fontSize(14)
          .backgroundColor(Color.Transparent)
          .fontColor('#1A1A1A')
          .onClick(() => {
            router.back();
          })
        
        Blank()
        
        Text('知识星图')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
      }
      .width('100%')
      .padding(16)
      .backgroundColor(Color.White)
      
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
      .onChange((index: number) => {
        this.currentTab = index;
      })
      .layoutWeight(1)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#0A1929')
  }
  
  /**
   * 构建星图视图
   */
  @Builder
  buildStarMapView() {
    const currentMap = this.getCurrentStarMap();
    
    if (!currentMap || currentMap.nodes.length === 0) {
      Column() {
        Text('暂无数据')
          .fontSize(16)
          .fontColor('#999')
      }
      .width('100%')
      .height('100%')
      .justifyContent(FlexAlign.Center)
    } else {
      Column() {
        // 图例
        Row() {
          Text('图例：')
            .fontSize(12)
            .fontColor(Color.White)
            .margin({ right: 12 })
          
          ForEach(currentMap.layers, (layer: string, index: number) => {
            Row() {
              Circle()
                .width(12)
                .height(12)
                .fill(this.getLayerColor(index))
              
              Text(layer)
                .fontSize(12)
                .fontColor(Color.White)
                .margin({ left: 4 })
            }
            .margin({ right: 12 })
          })
        }
        .width('100%')
        .padding(16)
        
        // 星图Canvas
        Canvas(this.context)
          .width('100%')
          .layoutWeight(1)
          .onReady(() => {
            if (currentMap) {
              this.drawStarMap(currentMap);
            }
          })
        
        // 节点统计
        Row() {
          Text(`节点数: ${currentMap.nodes.length}`)
            .fontSize(12)
            .fontColor(Color.White)
            .margin({ right: 16 })
          
          Text(`连接数: ${currentMap.edges.length}`)
            .fontSize(12)
            .fontColor(Color.White)
        }
        .width('100%')
        .padding(16)
      }
      .width('100%')
      .height('100%')
    }
  }
  
  private settings: RenderingContextSettings = new RenderingContextSettings(true);
  private context: CanvasRenderingContext2D = new CanvasRenderingContext2D(this.settings);
  
  /**
   * 绘制星图
   */
  private drawStarMap(starMap: StarMapData) {
    const width = this.context.width;
    const height = this.context.height;
    const centerX = width / 2;
    const centerY = height / 2;
    
    // 清空画布
    this.context.clearRect(0, 0, width, height);
    
    // 绘制连线
    starMap.edges.forEach(edge => {
      const fromNode = starMap.nodes.find(n => n.id === edge.from);
      const toNode = starMap.nodes.find(n => n.id === edge.to);
      
      if (fromNode && toNode) {
        this.context.beginPath();
        this.context.moveTo(
          centerX + fromNode.x,
          centerY + fromNode.y
        );
        this.context.lineTo(
          centerX + toNode.x,
          centerY + toNode.y
        );
        this.context.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        this.context.lineWidth = 1;
        this.context.stroke();
      }
    });
    
    // 绘制节点
    starMap.nodes.forEach(node => {
      const x = centerX + node.x;
      const y = centerY + node.y;
      
      // 节点光晕
      const haloGradient = this.context.createRadialGradient(
        x, y, 0,
        x, y, node.size * 2
      );
      haloGradient.addColorStop(0, this.hexToRgba(node.color, 0.3));
      haloGradient.addColorStop(1, this.hexToRgba(node.color, 0));
      
      this.context.beginPath();
      this.context.arc(x, y, node.size * 2, 0, Math.PI * 2);
      this.context.fillStyle = haloGradient;
      this.context.fill();
      
      // 节点主体
      const gradient = this.context.createRadialGradient(
        x - node.size * 0.3, y - node.size * 0.3, 0,
        x, y, node.size
      );
      gradient.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
      gradient.addColorStop(1, node.color);
      
      this.context.beginPath();
      this.context.arc(x, y, node.size, 0, Math.PI * 2);
      this.context.fillStyle = gradient;
      this.context.fill();
      
      // 节点边框
      this.context.beginPath();
      this.context.arc(x, y, node.size, 0, Math.PI * 2);
      this.context.strokeStyle = node.color;
      this.context.lineWidth = 2;
      this.context.stroke();
      
      // 节点标签
      this.context.fillStyle = 'white';
      this.context.font = '12px sans-serif';
      this.context.textAlign = 'center';
      this.context.fillText(node.label, x, y + node.size + 16);
    });
  }
  
  /**
   * 获取层级颜色
   */
  private getLayerColor(index: number): string {
    const colors = ['#0A59F7', '#34C759', '#FF9500', '#FF3B30'];
    return colors[index % colors.length];
  }
  
  /**
   * 十六进制转RGBA
   */
  private hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
}
