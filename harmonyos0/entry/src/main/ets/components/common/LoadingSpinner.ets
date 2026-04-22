/**
 * 加载动画组件
 */
import { AppConstants } from '../../constants/AppConstants';

@Component
export struct LoadingSpinner {
  @Prop message: string = '加载中...';
  @State rotateAngle: number = 0;

  aboutToAppear() {
    this.startAnimation();
  }

  startAnimation() {
    setInterval(() => {
      this.rotateAngle = (this.rotateAngle + 10) % 360;
    }, 16);
  }

  build() {
    Column() {
      // 旋转圆圈
      Circle()
        .width(40)
        .height(40)
        .fill(Color.Transparent)
        .stroke(AppConstants.COLORS.PRIMARY)
        .strokeWidth(3)
        .strokeDashArray([10, 5])
        .rotate({ angle: this.rotateAngle })
        .margin({ bottom: 12 })

      Text(this.message)
        .fontSize(14)
        .fontColor('#999999')
    }
    .width('100%')
    .layoutWeight(1)
    .justifyContent(FlexAlign.Center)
  }
}
