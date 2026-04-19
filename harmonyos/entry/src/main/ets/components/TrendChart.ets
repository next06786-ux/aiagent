/**
 * 
 * 
 */
@Component
export struct TrendChart {
  @Prop title: string = '';
  @Prop data: number[] = [];
  @Prop labels: string[] = [];
  @Prop color: string = '#007DFF';
  @Prop chartHeight: number = 200;
  
  build() {
    Column() {
      Text(this.title)
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .fontColor('#333333')
        .margin({ bottom: 10 })
      
      // 
      Row({ space: 5 }) {
        ForEach(this.data, (value: number, index: number) => {
          Column() {
            // 
            Column()
              .width(30)
              .height(`${value}%`)
              .backgroundColor(this.color)
              .borderRadius({ topLeft: 4, topRight: 4 })
            
            // 
            if (this.labels[index]) {
              Text(this.labels[index])
                .fontSize(12)
                .fontColor('#999999')
                .margin({ top: 5 })
            }
          }
          .height(this.chartHeight)
          .justifyContent(FlexAlign.End)
          .layoutWeight(1)
        })
      }
      .width('100%')
      .height(this.chartHeight + 30)
    }
    .width('100%')
    .padding(15)
    .backgroundColor('#F8F8F8')
    .borderRadius(8)
  }
}

/**
 * 
 * 
 */
@Component
export struct ScoreCard {
  @Prop icon: string = '';
  @Prop title: string = '';
  @Prop score: number = 0;
  @Prop maxScore: number = 100;
  @Prop trend: string = '→';
  @Prop trendColor: string = '#999999';
  
  build() {
    Column() {
      Row() {
        Text(this.icon)
          .fontSize(32)
          .margin({ right: 15 })
        
        Column({ space: 5 }) {
          Text(this.title)
            .fontSize(16)
            .fontColor('#333333')
          
          Row({ space: 5 }) {
            Text(`${this.score}`)
              .fontSize(28)
              .fontWeight(FontWeight.Bold)
              .fontColor(this.getScoreColor())
            
            Text(`/${this.maxScore}`)
              .fontSize(16)
              .fontColor('#999999')
            
            Text(this.trend)
              .fontSize(14)
              .fontColor(this.trendColor)
              .margin({ left: 5 })
          }
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)
        
        // 
        Progress({
          value: this.score,
          total: this.maxScore,
          type: ProgressType.Ring
        })
          .width(60)
          .height(60)
          .color(this.getScoreColor())
          .style({ strokeWidth: 6 })
      }
      .width('100%')
    }
    .width('100%')
    .padding(20)
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
  }
  
  private getScoreColor(): string {
    const percentage = (this.score / this.maxScore) * 100;
    if (percentage >= 80) {
      return '#52C41A';
    } else if (percentage >= 60) {
      return '#FA8C16';
    } else {
      return '#F5222D';
    }
  }
}
