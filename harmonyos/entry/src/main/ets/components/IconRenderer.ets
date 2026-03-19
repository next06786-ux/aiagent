/**
 * 图标渲染组件 - HarmonyOS 6
 * 用于在 UI 中显示专业 SVG 图标
 */
import { Icons, IconConfig } from '../common/Icons';
import { Theme } from '../common/Theme';

/**
 * 图标渲染器组件
 */
@Component
export struct IconRenderer {
  @Prop iconName: string; // 图标名称
  @Prop iconSize: number = 24; // 图标大小
  @Prop color: string = Theme.Color.Primary; // 图标颜色
  @Prop strokeWidth: number = 2; // 笔画宽度

  build() {
    this.renderIcon();
  }

  @Builder
  renderIcon() {
    Stack() {
      Web({ src: this.getSvgDataUrl(), controller: new WebController() })
        .width(this.iconSize)
        .height(this.iconSize)
        .hitTestBehavior(HitTestMode.Transparent)
    }
    .width(this.iconSize)
    .height(this.iconSize)
  }

  /**
   * 获取 SVG 数据 URL
   */
  private getSvgDataUrl(): string {
    const config: IconConfig = {
      size: this.iconSize,
      color: this.color,
      strokeWidth: this.strokeWidth
    };

    let svgContent = '';
    
    switch (this.iconName) {
      case 'chat':
        svgContent = Icons.ChatIcon(config);
        break;
      case 'network':
        svgContent = Icons.NetworkIcon(config);
        break;
      case 'analytics':
        svgContent = Icons.AnalyticsIcon(config);
        break;
      case 'agent':
        svgContent = Icons.AgentIcon(config);
        break;
      case 'camera':
        svgContent = Icons.CameraIcon(config);
        break;
      case 'learning':
        svgContent = Icons.LearningIcon(config);
        break;
      case 'life':
        svgContent = Icons.LifeIcon(config);
        break;
      case 'comparison':
        svgContent = Icons.ComparisonIcon(config);
        break;
      case 'home':
        svgContent = Icons.HomeIcon(config);
        break;
      case 'insight':
        svgContent = Icons.InsightIcon(config);
        break;
      case 'ai':
        svgContent = Icons.AIIcon(config);
        break;
      case 'user':
        svgContent = Icons.UserIcon(config);
        break;
      case 'back':
        svgContent = Icons.BackIcon(config);
        break;
      case 'settings':
        svgContent = Icons.SettingsIcon(config);
        break;
      case 'calendar':
        svgContent = Icons.CalendarIcon(config);
        break;
      default:
        svgContent = Icons.HomeIcon(config);
    }

    // 转换为 Data URL
    const encoded = encodeURIComponent(svgContent);
    return `data:image/svg+xml;charset=utf-8,${encoded}`;
  }
}

/**
 * 简化的图标显示组件 - 使用 Canvas 绘制
 */
@Component
export struct SimpleIcon {
  @Prop iconName: string;
  @Prop iconSize: number = 24;
  @Prop color: string = Theme.Color.Primary;

  private settings: RenderingContextSettings = new RenderingContextSettings(true);
  private canvasContext: CanvasRenderingContext2D = new CanvasRenderingContext2D(this.settings);

  build() {
    Canvas(this.canvasContext)
      .width(this.iconSize)
      .height(this.iconSize)
      .onReady(() => {
        this.drawIcon();
      })
  }

  private drawIcon() {
    const ctx = this.canvasContext;
    const size = this.iconSize;
    const color = this.color;

    ctx.clearRect(0, 0, size, size);
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    const scale = size / 24; // 基准大小为 24

    switch (this.iconName) {
      case 'chat':
        this.drawChatIcon(ctx, scale);
        break;
      case 'network':
        this.drawNetworkIcon(ctx, scale);
        break;
      case 'analytics':
        this.drawAnalyticsIcon(ctx, scale);
        break;
      case 'agent':
        this.drawAgentIcon(ctx, scale);
        break;
      case 'camera':
        this.drawCameraIcon(ctx, scale);
        break;
      case 'learning':
        this.drawLearningIcon(ctx, scale);
        break;
      case 'life':
        this.drawLifeIcon(ctx, scale);
        break;
      case 'comparison':
        this.drawComparisonIcon(ctx, scale);
        break;
      case 'home':
        this.drawHomeIcon(ctx, scale);
        break;
      case 'insight':
        this.drawInsightIcon(ctx, scale);
        break;
      case 'ai':
        this.drawAIIcon(ctx, scale);
        break;
      case 'user':
        this.drawUserIcon(ctx, scale);
        break;
      case 'back':
        this.drawBackIcon(ctx, scale);
        break;
      case 'settings':
        this.drawSettingsIcon(ctx, scale);
        break;
      case 'calendar':
        this.drawCalendarIcon(ctx, scale);
        break;
    }
  }

  private drawChatIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 对话气泡
    ctx.beginPath();
    ctx.moveTo(4 * s, 6 * s);
    ctx.lineTo(18 * s, 6 * s);
    ctx.quadraticCurveTo(20 * s, 6 * s, 20 * s, 8 * s);
    ctx.lineTo(20 * s, 14 * s);
    ctx.quadraticCurveTo(20 * s, 16 * s, 18 * s, 16 * s);
    ctx.lineTo(8 * s, 16 * s);
    ctx.lineTo(4 * s, 20 * s);
    ctx.lineTo(4 * s, 16 * s);
    ctx.quadraticCurveTo(4 * s, 16 * s, 4 * s, 14 * s);
    ctx.lineTo(4 * s, 8 * s);
    ctx.quadraticCurveTo(4 * s, 6 * s, 6 * s, 6 * s);
    ctx.stroke();
    
    // 三个点
    ctx.beginPath();
    ctx.arc(8 * s, 10 * s, 1 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(12 * s, 10 * s, 1 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(16 * s, 10 * s, 1 * s, 0, Math.PI * 2);
    ctx.fill();
  }

  private drawNetworkIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 三个节点
    ctx.beginPath();
    ctx.arc(6 * s, 6 * s, 2 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(18 * s, 6 * s, 2 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(12 * s, 16 * s, 2 * s, 0, Math.PI * 2);
    ctx.fill();
    
    // 连接线
    ctx.beginPath();
    ctx.moveTo(8 * s, 7 * s);
    ctx.lineTo(16 * s, 15 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(16 * s, 7 * s);
    ctx.lineTo(14 * s, 15 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(6 * s, 8 * s);
    ctx.lineTo(12 * s, 14 * s);
    ctx.stroke();
  }

  private drawAnalyticsIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 三个柱子
    ctx.fillRect(3 * s, 12 * s, 3 * s, 8 * s);
    ctx.fillRect(10 * s, 6 * s, 3 * s, 14 * s);
    ctx.fillRect(17 * s, 9 * s, 3 * s, 11 * s);
    
    // 底线
    ctx.beginPath();
    ctx.moveTo(2 * s, 20 * s);
    ctx.lineTo(22 * s, 20 * s);
    ctx.stroke();
  }

  private drawAgentIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 两个圆
    ctx.beginPath();
    ctx.arc(8 * s, 12 * s, 3 * s, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(16 * s, 12 * s, 3 * s, 0, Math.PI * 2);
    ctx.stroke();
    
    // 连接线
    ctx.beginPath();
    ctx.moveTo(11 * s, 12 * s);
    ctx.lineTo(13 * s, 12 * s);
    ctx.stroke();
    
    // 竖线
    ctx.beginPath();
    ctx.moveTo(8 * s, 9 * s);
    ctx.lineTo(8 * s, 6 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(8 * s, 15 * s);
    ctx.lineTo(8 * s, 18 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(16 * s, 9 * s);
    ctx.lineTo(16 * s, 6 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(16 * s, 15 * s);
    ctx.lineTo(16 * s, 18 * s);
    ctx.stroke();
  }

  private drawCameraIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 相机框
    ctx.beginPath();
    ctx.moveTo(4 * s, 6 * s);
    ctx.lineTo(14 * s, 6 * s);
    ctx.quadraticCurveTo(16 * s, 6 * s, 16 * s, 8 * s);
    ctx.lineTo(16 * s, 14 * s);
    ctx.quadraticCurveTo(16 * s, 16 * s, 14 * s, 16 * s);
    ctx.lineTo(6 * s, 16 * s);
    ctx.quadraticCurveTo(4 * s, 16 * s, 4 * s, 14 * s);
    ctx.lineTo(4 * s, 8 * s);
    ctx.quadraticCurveTo(4 * s, 6 * s, 6 * s, 6 * s);
    ctx.stroke();
    
    // 镜头
    ctx.beginPath();
    ctx.arc(10 * s, 10 * s, 3 * s, 0, Math.PI * 2);
    ctx.stroke();
    
    // 闪光灯
    ctx.beginPath();
    ctx.arc(14 * s, 6 * s, 1 * s, 0, Math.PI * 2);
    ctx.fill();
  }

  private drawLearningIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 折线图
    ctx.beginPath();
    ctx.moveTo(4 * s, 16 * s);
    ctx.lineTo(8 * s, 12 * s);
    ctx.lineTo(12 * s, 14 * s);
    ctx.lineTo(20 * s, 6 * s);
    ctx.stroke();
    
    // 箭头
    ctx.beginPath();
    ctx.moveTo(16 * s, 6 * s);
    ctx.lineTo(20 * s, 6 * s);
    ctx.lineTo(20 * s, 10 * s);
    ctx.stroke();
  }

  private drawLifeIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 六边形
    ctx.beginPath();
    ctx.moveTo(12 * s, 2 * s);
    ctx.lineTo(20 * s, 6 * s);
    ctx.lineTo(20 * s, 14 * s);
    ctx.lineTo(12 * s, 18 * s);
    ctx.lineTo(4 * s, 14 * s);
    ctx.lineTo(4 * s, 6 * s);
    ctx.closePath();
    ctx.stroke();
    
    // 中心线
    ctx.beginPath();
    ctx.moveTo(12 * s, 2 * s);
    ctx.lineTo(12 * s, 18 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(4 * s, 10 * s);
    ctx.lineTo(20 * s, 10 * s);
    ctx.stroke();
  }

  private drawComparisonIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 天平杆
    ctx.beginPath();
    ctx.moveTo(12 * s, 2 * s);
    ctx.lineTo(12 * s, 6 * s);
    ctx.stroke();
    
    // 天平横杆
    ctx.beginPath();
    ctx.moveTo(4 * s, 6 * s);
    ctx.lineTo(20 * s, 6 * s);
    ctx.stroke();
    
    // 左盘
    ctx.strokeRect(2 * s, 6 * s, 4 * s, 6 * s);
    
    // 右盘
    ctx.strokeRect(18 * s, 6 * s, 4 * s, 6 * s);
    
    // 底座
    ctx.beginPath();
    ctx.moveTo(4 * s, 18 * s);
    ctx.lineTo(20 * s, 18 * s);
    ctx.stroke();
  }

  private drawHomeIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 房子
    ctx.beginPath();
    ctx.moveTo(3 * s, 12 * s);
    ctx.lineTo(12 * s, 3 * s);
    ctx.lineTo(21 * s, 12 * s);
    ctx.lineTo(21 * s, 19 * s);
    ctx.quadraticCurveTo(21 * s, 21 * s, 19 * s, 21 * s);
    ctx.lineTo(5 * s, 21 * s);
    ctx.quadraticCurveTo(3 * s, 21 * s, 3 * s, 19 * s);
    ctx.closePath();
    ctx.stroke();
    
    // 门
    ctx.strokeRect(9 * s, 12 * s, 6 * s, 9 * s);
  }

  private drawInsightIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 灯泡
    ctx.beginPath();
    ctx.arc(12 * s, 8 * s, 5 * s, 0, Math.PI, true);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(9 * s, 13 * s);
    ctx.lineTo(9 * s, 16 * s);
    ctx.quadraticCurveTo(9 * s, 18 * s, 11 * s, 18 * s);
    ctx.lineTo(13 * s, 18 * s);
    ctx.quadraticCurveTo(15 * s, 18 * s, 15 * s, 16 * s);
    ctx.lineTo(15 * s, 13 * s);
    ctx.stroke();
    
    // 底座
    ctx.beginPath();
    ctx.moveTo(8 * s, 18 * s);
    ctx.lineTo(16 * s, 18 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(7 * s, 21 * s);
    ctx.lineTo(17 * s, 21 * s);
    ctx.stroke();
  }

  private drawAIIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 芯片外框
    ctx.strokeRect(4 * s, 4 * s, 16 * s, 16 * s);
    
    // 内框
    ctx.strokeRect(7 * s, 7 * s, 10 * s, 10 * s);
    
    // 中心点
    ctx.beginPath();
    ctx.arc(12 * s, 12 * s, 2 * s, 0, Math.PI * 2);
    ctx.fill();
    
    // 引脚
    ctx.beginPath();
    ctx.moveTo(4 * s, 12 * s);
    ctx.lineTo(2 * s, 12 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(20 * s, 12 * s);
    ctx.lineTo(22 * s, 12 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(12 * s, 4 * s);
    ctx.lineTo(12 * s, 2 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(12 * s, 20 * s);
    ctx.lineTo(12 * s, 22 * s);
    ctx.stroke();
  }

  private drawUserIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 头部
    ctx.beginPath();
    ctx.arc(12 * s, 7 * s, 4 * s, 0, Math.PI * 2);
    ctx.stroke();
    
    // 身体
    ctx.beginPath();
    ctx.moveTo(4 * s, 20 * s);
    ctx.quadraticCurveTo(4 * s, 13 * s, 12 * s, 13 * s);
    ctx.quadraticCurveTo(20 * s, 13 * s, 20 * s, 20 * s);
    ctx.stroke();
  }

  private drawBackIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 箭头
    ctx.beginPath();
    ctx.moveTo(18 * s, 12 * s);
    ctx.lineTo(6 * s, 12 * s);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(6 * s, 12 * s);
    ctx.lineTo(12 * s, 18 * s);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(6 * s, 12 * s);
    ctx.lineTo(12 * s, 6 * s);
    ctx.stroke();
  }

  private drawSettingsIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 中心圆
    ctx.beginPath();
    ctx.arc(12 * s, 12 * s, 3 * s, 0, Math.PI * 2);
    ctx.stroke();
    
    // 齿轮齿
    const teeth = [
      [12 * s, 2 * s, 12 * s, 4 * s],
      [12 * s, 20 * s, 12 * s, 22 * s],
      [22 * s, 12 * s, 20 * s, 12 * s],
      [4 * s, 12 * s, 2 * s, 12 * s],
    ];
    
    teeth.forEach(tooth => {
      ctx.beginPath();
      ctx.moveTo(tooth[0], tooth[1]);
      ctx.lineTo(tooth[2], tooth[3]);
      ctx.stroke();
    });
  }

  private drawCalendarIcon(ctx: CanvasRenderingContext2D, scale: number) {
    const s = scale;
    // 日历框
    ctx.strokeRect(3 * s, 4 * s, 18 * s, 16 * s);
    
    // 分割线
    ctx.beginPath();
    ctx.moveTo(3 * s, 10 * s);
    ctx.lineTo(21 * s, 10 * s);
    ctx.stroke();
    
    // 日期标记
    ctx.beginPath();
    ctx.moveTo(7 * s, 1 * s);
    ctx.lineTo(7 * s, 7 * s);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(17 * s, 1 * s);
    ctx.lineTo(17 * s, 7 * s);
    ctx.stroke();
  }
}

