/**
 * 平行宇宙地图组件
 * 展示多个决策选项的时间线对比
 */
import { DecisionOption, TimelineEvent } from '../models/DecisionModels'

@Component
export struct ParallelUniverseMap {
  @State options: DecisionOption[] = []
  @State selectedOption: number = 0
  @State isAnimating: boolean = false
  @State currentMonth: number = 1

  build() {
    Column() {
      // 标题
      Text('平行宇宙模拟')
        .fontSize(24)
        .fontWeight(FontWeight.Bold)
        .margin({ bottom: 20 })

      // 选项卡片列表
      List({ space: 15 }) {
        ForEach(this.options, (option: DecisionOption, index: number) => {
          ListItem() {
            this.OptionCard(option, index)
          }
        })
      }
      .width('100%')
      .layoutWeight(1)

      // 时间线控制
      Row() {
        Button('播放动画')
          .onClick(() => {
            this.playAnimation()
          })
          .enabled(!this.isAnimating)

        Slider({
          value: this.currentMonth,
          min: 1,
          max: 12,
          step: 1
        })
          .width('60%')
          .onChange((value: number) => {
            this.currentMonth = Math.round(value)
          })

        Text(`第${this.currentMonth}月`)
          .fontSize(16)
      }
      .width('100%')
      .justifyContent(FlexAlign.SpaceBetween)
      .padding(15)
    }
    .width('100%')
    .height('100%')
    .padding(20)
    .backgroundColor('#F5F5F5')
  }

  @Builder
  OptionCard(option: DecisionOption, index: number) {
    Column() {
      // 选项标题
      Row() {
        Text(option.title)
          .fontSize(20)
          .fontWeight(FontWeight.Bold)

        Blank()

        // 得分徽章
        Text(`${option.final_score.toFixed(1)}分`)
          .fontSize(16)
          .fontColor(Color.White)
          .backgroundColor(this.getScoreColor(option.final_score))
          .padding({ left: 10, right: 10, top: 5, bottom: 5 })
          .borderRadius(15)
      }
      .width('100%')
      .margin({ bottom: 10 })

      // 风险等级
      Row() {
        Text('风险等级:')
          .fontSize(14)
          .fontColor('#666')

        Progress({
          value: option.risk_level * 100,
          total: 100,
          type: ProgressType.Linear
        })
          .width(100)
          .color(this.getRiskColor(option.risk_level))

        Text(this.getRiskLabel(option.risk_level))
          .fontSize(14)
          .fontColor(this.getRiskColor(option.risk_level))
      }
      .width('100%')
      .margin({ bottom: 15 })

      // 时间线预览
      Column() {
        ForEach(option.timeline.slice(0, 3), (event: TimelineEvent) => {
          Row() {
            Text(`第${event.month}月`)
              .fontSize(12)
              .fontColor('#999')
              .width(60)

            Text(event.event)
              .fontSize(14)
              .maxLines(1)
              .textOverflow({ overflow: TextOverflow.Ellipsis })
              .layoutWeight(1)
          }
          .width('100%')
          .margin({ bottom: 8 })
        })

        Text('查看完整时间线 >')
          .fontSize(12)
          .fontColor('#007AFF')
          .alignSelf(ItemAlign.End)
          .onClick(() => {
            this.selectedOption = index
            // 导航到详情页
          })
      }
      .width('100%')
    }
    .width('100%')
    .padding(15)
    .backgroundColor(Color.White)
    .borderRadius(10)
    .shadow({
      radius: 5,
      color: '#00000010',
      offsetX: 0,
      offsetY: 2
    })
  }

  // 播放时间线动画
  playAnimation() {
    this.isAnimating = true
    this.currentMonth = 1

    const interval = setInterval(() => {
      if (this.currentMonth >= 12) {
        clearInterval(interval)
        this.isAnimating = false
      } else {
        this.currentMonth++
      }
    }, 500) // 每0.5秒前进一个月
  }

  // 根据得分获取颜色
  getScoreColor(score: number): string {
    if (score >= 80) return '#4CAF50' // 绿色
    if (score >= 60) return '#FFC107' // 黄色
    if (score >= 40) return '#FF9800' // 橙色
    return '#F44336' // 红色
  }

  // 根据风险等级获取颜色
  getRiskColor(risk: number): string {
    if (risk < 0.3) return '#4CAF50' // 低风险-绿色
    if (risk < 0.5) return '#FFC107' // 中风险-黄色
    if (risk < 0.7) return '#FF9800' // 高风险-橙色
    return '#F44336' // 极高风险-红色
  }

  // 获取风险标签
  getRiskLabel(risk: number): string {
    if (risk < 0.3) return '低风险'
    if (risk < 0.5) return '中风险'
    if (risk < 0.7) return '高风险'
    return '极高风险'
  }
}
