/**
 * 连线组件 - 用于连接球体上的节点
 */
export interface LinePoint {
  x: number;
  y: number;
}

@Component
export struct ConnectionLine {
  @Prop startPoint: LinePoint = { x: 0, y: 0 };
  @Prop endPoint: LinePoint = { x: 0, y: 0 };
  @Prop color: string = '#FFFFFF';
  @Prop lineWidth: number = 2;
  @Prop lineOpacity: number = 0.3;
  @Prop animated: boolean = false;
  @State dashOffset: number = 0;

  aboutToAppear() {
    if (this.animated) {
      this.startAnimation();
    }
  }

  startAnimation() {
    setInterval(() => {
      this.dashOffset = (this.dashOffset + 1) % 20;
    }, 50);
  }

  build() {
    Canvas(this.canvasContext)
      .width('100%')
      .height('100%')
      .onReady(() => {
        this.drawLine();
      })
  }

  private canvasContext = new CanvasRenderingContext2D();

  private drawLine() {
    const ctx = this.canvasContext;
    
    ctx.clearRect(0, 0, ctx.width, ctx.height);
    ctx.beginPath();
    ctx.moveTo(this.startPoint.x, this.startPoint.y);
    ctx.lineTo(this.endPoint.x, this.endPoint.y);
    
    ctx.strokeStyle = this.color;
    ctx.lineWidth = this.lineWidth;
    ctx.globalAlpha = this.lineOpacity;
    
    if (this.animated) {
      ctx.setLineDash([10, 10]);
      ctx.lineDashOffset = this.dashOffset;
    }
    
    ctx.stroke();
  }
}
