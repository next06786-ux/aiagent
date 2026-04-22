/**
 * 错误提示组件
 */
@Component
export struct ErrorToast {
  @Prop message: string = '';
  onClose: () => void = () => {};
  @State visible: boolean = true;

  aboutToAppear() {
    // 3秒后自动关闭
    setTimeout(() => {
      this.visible = false;
      this.onClose();
    }, 3000);
  }

  build() {
    if (this.visible) {
      Column() {
        Row() {
          Text('❌')
            .fontSize(20)
            .margin({ right: 8 })

          Text(this.message)
            .fontSize(14)
            .fontColor(Color.White)
            .layoutWeight(1)

          Text('✕')
            .fontSize(16)
            .fontColor(Color.White)
            .onClick(() => {
              this.visible = false;
              this.onClose();
            })
        }
        .width('90%')
        .padding(16)
        .backgroundColor('#F44336')
        .borderRadius(8)
        .shadow({
          radius: 8,
          color: '#00000030',
          offsetX: 0,
          offsetY: 2
        })
      }
      .width('100%')
      .position({ x: 0, y: 80 })
      .zIndex(1000)
    }
  }
}
