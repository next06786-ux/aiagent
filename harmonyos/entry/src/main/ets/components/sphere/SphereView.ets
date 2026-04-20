/**
 * 3D球体组件
 * 模仿Web端的玻璃态球体效果
 */
import { ColorUtils } from '../../utils/ColorUtils';
import { AppConstants } from '../../constants/AppConstants';

@Component
export struct SphereView {
  @Prop title: string = '';
  @Prop sizeValue: number = 120;
  @Prop color: string = AppConstants.COLORS.PRIMARY;
  @Prop status: 'idle' | 'thinking' | 'complete' = 'idle';
  @State private animationProgress: number = 0;
  
  private settings: RenderingContextSettings = new RenderingContextSettings(true);
  private context: CanvasRenderingContext2D = new CanvasRenderingContext2D(this.settings);
  private animationTimer: number = -1;
  
  build() {
    Stack() {
      Canvas(this.context)
        .width(this.sizeValue)
        .height(this.sizeValue)
        .onReady(() => {
          this.drawSphere();
          if (this.status === 'thinking') {
            this.startAnimation();
          }
        })
      
      if (this.title) {
        Text(this.title)
          .fontSize(14)
          .fontWeight(FontWeight.Bold)
          .fontColor('#1A1A1A')
          .maxLines(2)
          .textAlign(TextAlign.Center)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
          .width('80%')
      }
    }
    .width(this.sizeValue)
    .height(this.sizeValue)
  }
  
  /**
   * 绘制球体
   */
  private drawSphere(): void {
    const centerX = this.sizeValue / 2;
    const centerY = this.sizeValue / 2;
    const radius = this.sizeValue / 2 - 10;
    
    // 清空画布
    this.context.clearRect(0, 0, this.sizeValue, this.sizeValue);
    
    // 1. 绘制外部光晕
    const haloGradient = this.context.createRadialGradient(
      centerX, centerY, radius * 0.8,
      centerX, centerY, radius * 1.3
    );
    haloGradient.addColorStop(0, ColorUtils.hexToRgba(this.color, 0.2));
    haloGradient.addColorStop(1, ColorUtils.hexToRgba(this.color, 0));
    
    this.context.beginPath();
    this.context.arc(centerX, centerY, radius * 1.3, 0, Math.PI * 2);
    this.context.fillStyle = haloGradient;
    this.context.fill();
    
    // 2. 绘制球体主体（玻璃态渐变）
    const gradient = this.context.createRadialGradient(
      centerX - radius * 0.3, centerY - radius * 0.3, 0,
      centerX, centerY, radius
    );
    gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
    gradient.addColorStop(0.3, 'rgba(255, 255, 255, 0.95)');
    gradient.addColorStop(0.7, ColorUtils.hexToRgba(this.color, 0.9));
    gradient.addColorStop(1, ColorUtils.hexToRgba(this.color, 0.85));
    
    this.context.beginPath();
    this.context.arc(centerX, centerY, radius, 0, Math.PI * 2);
    this.context.fillStyle = gradient;
    this.context.fill();
    
    // 3. 绘制高光效果
    const highlightGradient = this.context.createRadialGradient(
      centerX - radius * 0.4, centerY - radius * 0.4, 0,
      centerX - radius * 0.4, centerY - radius * 0.4, radius * 0.35
    );
    highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.7)');
    highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
    
    this.context.beginPath();
    this.context.arc(centerX - radius * 0.4, centerY - radius * 0.4, radius * 0.35, 0, Math.PI * 2);
    this.context.fillStyle = highlightGradient;
    this.context.fill();
    
    // 4. 绘制次高光
    const secondHighlight = this.context.createRadialGradient(
      centerX + radius * 0.3, centerY + radius * 0.4, 0,
      centerX + radius * 0.3, centerY + radius * 0.4, radius * 0.2
    );
    secondHighlight.addColorStop(0, 'rgba(255, 255, 255, 0.3)');
    secondHighlight.addColorStop(1, 'rgba(255, 255, 255, 0)');
    
    this.context.beginPath();
    this.context.arc(centerX + radius * 0.3, centerY + radius * 0.4, radius * 0.2, 0, Math.PI * 2);
    this.context.fillStyle = secondHighlight;
    this.context.fill();
    
    // 5. 绘制边框
    this.context.beginPath();
    this.context.arc(centerX, centerY, radius, 0, Math.PI * 2);
    this.context.strokeStyle = ColorUtils.hexToRgba(this.color, 0.6);
    this.context.lineWidth = 2;
    this.context.stroke();
    
    // 6. 思考状态的脉冲效果
    if (this.status === 'thinking') {
      const pulseRadius = radius + Math.sin(this.animationProgress) * 5;
      this.context.beginPath();
      this.context.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
      this.context.strokeStyle = ColorUtils.hexToRgba(this.color, 0.3);
      this.context.lineWidth = 3;
      this.context.stroke();
    }
  }
  
  /**
   * 开始动画
   */
  private startAnimation(): void {
    this.animationTimer = setInterval(() => {
      this.animationProgress += 0.1;
      if (this.animationProgress >= Math.PI * 2) {
        this.animationProgress = 0;
      }
      this.drawSphere();
    }, 50);
  }
  
  /**
   * 停止动画
   */
  private stopAnimation(): void {
    if (this.animationTimer !== -1) {
      clearInterval(this.animationTimer);
      this.animationTimer = -1;
    }
  }
  
  aboutToDisappear() {
    this.stopAnimation();
  }
}
