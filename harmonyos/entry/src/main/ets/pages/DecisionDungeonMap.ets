/**
 * 决策副本地图页面 - HarmonyOS 6 游戏化闯关
 * 展示不同决策选项的副本路线，支持交互式探索
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { Theme } from '../common/Theme'
import { SimpleIcon } from '../components/IconRenderer'

interface TimelineEvent {
  month: number
  event: string
  impact: Record<string, number>
  probability: number
}

interface DungeonOption {
  option_id: string
  title: string
  description: string
  timeline: TimelineEvent[]
  final_score: number
  risk_level: number
}

interface DungeonData {
  dungeon_id: string
  user_id: string
  title: string
  description: string
  options: DungeonOption[]
  recommendation: string
  created_at: string
}

interface RouterParams {
  dungeonId?: string
  userId?: string
}

interface ApiResponse {
  code: number
  message: string
  data: DungeonData | null
}

@Entry
@Component
struct DecisionDungeonMap {
  @State dungeonData: DungeonData | null = null
  @State isLoading: boolean = false
  @State showContent: boolean = false
  @State selectedDungeon: number = -1
  @State currentMonth: number = 1
  @State isAnimating: boolean = false
  @State expandedDungeon: number = -1
  private dungeonId: string = ''
  private userId: string = 'default_user'
  private scroller: Scroller = new Scroller()

  aboutToAppear() {
    const params = router.getParams() as RouterParams
    if (params?.dungeonId) {
      this.dungeonId = params.dungeonId
    }
    if (params?.userId) {
      this.userId = params.userId
    }

    this.loadDungeonData()
  }

  private async loadDungeonData() {
    this.isLoading = true

    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        ApiConfig.getApiUrl(`/api/decision/dungeon/${this.dungeonId}`),
        {
          method: http.RequestMethod.GET,
          header: {
            'Content-Type': 'application/json'
          },
          connectTimeout: 30000,
          readTimeout: 30000
        }
      )

      httpRequest.destroy()

      if (response.responseCode === 200) {
        const resultStr = response.result as string
        const result = JSON.parse(resultStr) as ApiResponse

        if (result.code === 200 && result.data) {
          this.dungeonData = result.data
          console.info('Dungeon loaded:', this.dungeonData)
        }
      }
    } catch (error) {
      const err = error as Error
      console.error('Error loading dungeon:', err.message)
    }

    this.isLoading = false

    setTimeout(() => {
      this.showContent = true
    }, 100)
  }

  private playAnimation() {
    this.isAnimating = true
    this.currentMonth = 1

    const interval = setInterval(() => {
      if (!this.isAnimating || this.currentMonth >= 12) {
        clearInterval(interval)
        this.isAnimating = false
      } else {
        this.currentMonth++
      }
    }, 300)
  }

  private getUniverseColor(index: number): string {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    return colors[index % colors.length]
  }

  private getScoreColor(score: number): string {
    if (score >= 80) return '#4CAF50'
    if (score >= 60) return '#FFC107'
    if (score >= 40) return '#FF9800'
    return '#F44336'
  }

  private getRiskColor(risk: number): string {
    if (risk < 0.3) return '#4CAF50'
    if (risk < 0.5) return '#FFC107'
    if (risk < 0.7) return '#FF9800'
    return '#F44336'
  }

  private getRiskLabel(risk: number): string {
    if (risk < 0.3) return '低风险'
    if (risk < 0.5) return '中风险'
    if (risk < 0.7) return '高风险'
    return '极高风险'
  }

  private getImpactIcon(key: string): string {
    const icons: Record<string, string> = {
      '健康': '💪',
      '财务': '💰',
      '社交': '👥',
      '情绪': '😊',
      '学习': '📚',
      '时间': '⏰'
    }
    return icons[key] || '📊'
  }

  build() {
    Stack() {
      // 背景
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor(Theme.Color.BackgroundPrimary)

      Column() {
        // 顶部导航
        Row() {
          Button({ type: ButtonType.Circle }) {
            Text('←')
              .fontSize(24)
              .fontColor(Theme.Color.TextPrimary)
              .fontWeight(600)
          }
          .width(40)
          .height(40)
          .backgroundColor('rgba(0, 0, 0, 0)')
          .onClick(() => {
            router.back()
          })

          Text('决策副本地图')
            .fontSize(20)
            .fontWeight(700)
            .fontColor(Theme.Color.TextPrimary)
            .layoutWeight(1)
            .margin({ left: 12 })

          // 切换到2D视图按钮
          Button('2D地图')
            .height(36)
            .fontSize(14)
            .fontWeight(600)
            .fontColor(Theme.Color.Primary)
            .backgroundColor(Theme.Color.GlassMedium)
            .borderRadius(Theme.Radius.m)
            .margin({ right: 8 })
            .onClick(() => {
              router.pushUrl({
                url: 'pages/DecisionDungeon2DMap',
                params: {
                  dungeonId: this.dungeonId,
                  userId: this.userId
                }
              })
            })

          if (this.dungeonData) {
            Text(`${this.currentMonth}/12月`)
              .fontSize(14)
              .fontColor(Theme.Color.Primary)
              .fontWeight(600)
              .padding({ left: 12, right: 12, top: 6, bottom: 6 })
              .backgroundColor(Theme.Color.GlassMedium)
              .borderRadius(Theme.Radius.round)
          }
        }
        .width('100%')
        .height(56)
        .padding({ left: 16, right: 16 })
        .backgroundColor('rgba(255, 255, 255, 0.6)')
        .backdropBlur(20)

        if (this.isLoading) {
          Column() {
            LoadingProgress()
              .width(40)
              .height(40)
              .color(Theme.Color.Primary)
            Text('正在加载副本...')
              .fontSize(14)
              .fontColor(Theme.Color.TextSecondary)
              .margin({ top: 12 })
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        } else if (this.dungeonData) {
          Scroll(this.scroller) {
            Column({ space: 32 }) {
              // 副本标题
              Column({ space: 12 }) {
                Text('🎯 ' + this.dungeonData.title)
                  .fontSize(24)
                  .fontWeight(700)
                  .fontColor(Theme.Color.TextPrimary)

                Text(this.dungeonData.description)
                  .fontSize(14)
                  .fontColor(Theme.Color.TextSecondary)
                  .lineHeight(22)
              }
              .width('100%')
              .padding(20)
              .backgroundColor(Theme.Color.GlassHeavy)
              .backdropBlur(Theme.Blur.Heavy)
              .borderRadius(Theme.Radius.l)
              .border({ width: 1, color: Theme.Color.BorderLight })
              .margin({ left: 16, right: 16, top: 16 })
              .alignItems(HorizontalAlign.Start)

              // 副本选项卡片
              ForEach(this.dungeonData.options, (option: DungeonOption, index: number) => {
                this.DungeonCard(option, index)
              })

              // AI推荐
              Column({ space: 12 }) {
                Row({ space: 12 }) {
                  Text('🤖')
                    .fontSize(32)

                  Column({ space: 4 }) {
                    Text('AI 智能推荐')
                      .fontSize(18)
                      .fontWeight(700)
                      .fontColor(Theme.Color.Primary)

                    Text('基于你的个性化模型分析')
                      .fontSize(12)
                      .fontColor(Theme.Color.TextSecondary)
                  }
                  .alignItems(HorizontalAlign.Start)
                }
                .width('100%')

                Text(this.dungeonData.recommendation)
                  .fontSize(14)
                  .fontColor(Theme.Color.TextPrimary)
                  .lineHeight(22)
              }
              .width('100%')
              .padding(20)
              .backgroundColor('rgba(0, 122, 255, 0.05)')
              .borderRadius(Theme.Radius.l)
              .margin({ left: 16, right: 16, bottom: 120 })
              .alignItems(HorizontalAlign.Start)
            }
            .width('100%')
          }
          .layoutWeight(1)
          .scrollBar(BarState.Off)
          .edgeEffect(EdgeEffect.Spring)
        }

        // 底部时间线控制
        if (this.dungeonData) {
          Row({ space: 12 }) {
            Button(this.isAnimating ? '⏸ 暂停' : '▶ 播放')
              .width(100)
              .height(44)
              .fontSize(14)
              .fontWeight(600)
              .fontColor(Color.White)
              .backgroundColor(Theme.Color.Primary)
              .borderRadius(Theme.Radius.m)
              .onClick(() => {
                if (this.isAnimating) {
                  this.isAnimating = false
                } else {
                  this.playAnimation()
                }
              })

            Slider({
              value: this.currentMonth,
              min: 1,
              max: 12,
              step: 1,
              style: SliderStyle.InSet
            })
              .layoutWeight(1)
              .blockColor(Theme.Color.Primary)
              .trackColor('rgba(0, 122, 255, 0.2)')
              .selectedColor(Theme.Color.Primary)
              .onChange((value: number) => {
                this.currentMonth = Math.round(value)
              })
          }
          .width('100%')
          .padding(16)
          .backgroundColor('rgba(255, 255, 255, 0.95)')
          .backdropBlur(20)
          .shadow({ radius: 10, color: 'rgba(0,0,0,0.1)', offsetY: -4 })
        }
      }
      .width('100%')
      .height('100%')
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  DungeonCard(option: DungeonOption, index: number) {
    Column({ space: 0 }) {
      // 卡片头部
      Row({ space: 16 }) {
        Stack() {
          Circle({ width: 60, height: 60 })
            .fill(this.getUniverseColor(index))
            .opacity(0.15)

          Text(String.fromCharCode(65 + index))
            .fontSize(28)
            .fontWeight(800)
            .fontColor(this.getUniverseColor(index))
        }

        Column({ space: 4 }) {
          Text(`副本 ${String.fromCharCode(65 + index)}`)
            .fontSize(12)
            .fontColor(Theme.Color.TextSecondary)
            .fontWeight(600)

          Text(option.title)
            .fontSize(18)
            .fontColor(Theme.Color.TextPrimary)
            .fontWeight(700)

          Text(option.description)
            .fontSize(12)
            .fontColor(Theme.Color.TextSecondary)
            .maxLines(1)
            .textOverflow({ overflow: TextOverflow.Ellipsis })
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)

        Column({ space: 4 }) {
          Text(`${option.final_score.toFixed(0)}`)
            .fontSize(28)
            .fontWeight(800)
            .fontColor(this.getScoreColor(option.final_score))

          Text('综合分')
            .fontSize(11)
            .fontColor(Theme.Color.TextSecondary)
        }
      }
      .width('100%')
      .padding(20)
      .backgroundColor(Theme.Color.GlassHeavy)
      .backdropBlur(Theme.Blur.Heavy)
      .borderRadius({ topLeft: 20, topRight: 20 })
      .border({ width: 1, color: Theme.Color.BorderLight })

      // 时间线
      if (this.expandedDungeon === index) {
        Column({ space: 0 }) {
          ForEach(option.timeline, (event: TimelineEvent, eventIndex: number) => {
            if (event.month <= this.currentMonth) {
              this.TimelineNode(event, eventIndex, option.timeline.length, this.getUniverseColor(index))
            }
          })
        }
        .width('100%')
        .padding({ left: 20, right: 20, top: 16, bottom: 16 })
        .backgroundColor('rgba(255, 255, 255, 0.5)')
      }

      // 风险和操作
      Row({ space: 12 }) {
        Column({ space: 4 }) {
          Text('风险等级')
            .fontSize(11)
            .fontColor(Theme.Color.TextSecondary)

          Text(this.getRiskLabel(option.risk_level))
            .fontSize(14)
            .fontWeight(600)
            .fontColor(this.getRiskColor(option.risk_level))
        }
        .layoutWeight(1)

        Button(this.expandedDungeon === index ? '收起' : '展开')
          .height(36)
          .fontSize(13)
          .fontWeight(600)
          .fontColor(this.getUniverseColor(index))
          .backgroundColor(this.getUniverseColor(index) + '20')
          .borderRadius(Theme.Radius.m)
          .onClick(() => {
            this.expandedDungeon = this.expandedDungeon === index ? -1 : index
          })
      }
      .width('100%')
      .padding(16)
      .backgroundColor(Theme.Color.BackgroundSecondary)
      .borderRadius({ bottomLeft: 20, bottomRight: 20 })
      .border({ width: { left: 1, right: 1, bottom: 1, top: 0 }, color: Theme.Color.BorderLight })
    }
    .width('100%')
    .margin({ left: 16, right: 16, bottom: 16 })
    .opacity(this.showContent ? 1 : 0)
    .scale({ x: this.showContent ? 1 : 0.95, y: this.showContent ? 1 : 0.95 })
    .animation({
      duration: 600,
      curve: Curve.Smooth,
      delay: index * 100
    })
  }

  @Builder
  TimelineNode(event: TimelineEvent, index: number, total: number, color: string) {
    Row({ space: 12 }) {
      // 时间标记
      Column({ space: 4 }) {
        Text(`第${event.month}月`)
          .fontSize(12)
          .fontWeight(600)
          .fontColor(color)

        Text(`${(event.probability * 100).toFixed(0)}%`)
          .fontSize(10)
          .fontColor(Theme.Color.TextSecondary)
      }
      .width(50)

      // 事件内容
      Column({ space: 8 }) {
        Text(event.event)
          .fontSize(13)
          .fontColor(Theme.Color.TextPrimary)
          .fontWeight(600)
          .lineHeight(18)

        // 影响指标
        Flex({ wrap: FlexWrap.Wrap }) {
          ForEach(Object.keys(event.impact), (key: string) => {
            if (Math.abs(event.impact[key]) > 0.1) {
              Text(`${this.getImpactIcon(key)} ${event.impact[key] > 0 ? '+' : ''}${(event.impact[key] * 100).toFixed(0)}%`)
                .fontSize(11)
                .fontColor(event.impact[key] > 0 ? '#4CAF50' : '#FF3B30')
                .padding({ left: 6, right: 6, top: 2, bottom: 2 })
                .backgroundColor(event.impact[key] > 0 ? 'rgba(76, 175, 80, 0.1)' : 'rgba(255, 59, 48, 0.1)')
                .borderRadius(4)
                .margin({ right: 4, bottom: 4 })
            }
          })
        }
        .width('100%')
      }
      .layoutWeight(1)
      .alignItems(HorizontalAlign.Start)
    }
    .width('100%')
    .padding(12)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.m)
    .margin({ bottom: 8 })
  }
}




