/**
 * LoRA模型状态卡片组件
 * 显示用户的LoRA模型训练状态
 */
import { LoRAStatus } from '../models/LoRAModels'

@Component
export struct LoRAStatusCard {
  @State loraStatus: LoRAStatus | null = null
  @State isTraining: boolean = false

  build() {
    Column() {
      // 标题
      Row() {
        Text('个性化AI模型')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)

        Blank()

        // 状态指示器
        Row() {
          Circle({ width: 8, height: 8 })
            .fill(this.getStatusColor())

          Text(this.getStatusText())
            .fontSize(12)
            .fontColor('#666')
            .margin({ left: 5 })
        }
      }
      .width('100%')
      .margin({ bottom: 15 })

      if (this.loraStatus) {
        if (this.loraStatus.has_lora) {
          // 有LoRA模型
          Column() {
            // 模型版本
            Row() {
              Text('模型版本:')
                .fontSize(14)
                .fontColor('#666')

              Text(`v${this.loraStatus.model_version}`)
                .fontSize(16)
                .fontWeight(FontWeight.Bold)
                .margin({ left: 10 })
            }
            .width('100%')
            .margin({ bottom: 10 })

            // 训练数据量
            Row() {
              Text('训练数据:')
                .fontSize(14)
                .fontColor('#666')

              Text(`${this.loraStatus.training_data_size} 条对话`)
                .fontSize(14)
                .margin({ left: 10 })
            }
            .width('100%')
            .margin({ bottom: 10 })

            // 上次训练时间
            if (this.loraStatus.last_train_time) {
              Row() {
                Text('上次训练:')
                  .fontSize(14)
                  .fontColor('#666')

                Text(this.formatTime(this.loraStatus.last_train_time))
                  .fontSize(14)
                  .margin({ left: 10 })
              }
              .width('100%')
              .margin({ bottom: 10 })
            }

            // 个性化程度
            Column() {
              Row() {
                Text('个性化程度')
                  .fontSize(14)
                  .fontColor('#666')

                Blank()

                Text(`${this.calculatePersonalization()}%`)
                  .fontSize(14)
                  .fontWeight(FontWeight.Bold)
                  .fontColor('#4CAF50')
              }
              .width('100%')
              .margin({ bottom: 5 })

              Progress({
                value: this.calculatePersonalization(),
                total: 100,
                type: ProgressType.Linear
              })
                .width('100%')
                .color('#4CAF50')
            }
            .width('100%')
            .margin({ bottom: 15 })

            // 操作按钮
            Row() {
              Button('手动训练')
                .fontSize(14)
                .backgroundColor('#007AFF')
                .enabled(!this.isTraining)
                .onClick(() => {
                  this.triggerTraining()
                })

              Button('查看详情')
                .fontSize(14)
                .backgroundColor(Color.White)
                .fontColor('#007AFF')
                .border({ width: 1, color: '#007AFF' })
                .onClick(() => {
                  // 导航到详情页
                })
            }
            .width('100%')
            .justifyContent(FlexAlign.SpaceBetween)
          }
        } else {
          // 没有LoRA模型
          Column() {
            Image($r('app.media.ic_lora_empty'))
              .width(80)
              .height(80)
              .margin({ bottom: 15 })

            Text('还没有专属AI模型')
              .fontSize(16)
              .fontColor('#666')
              .margin({ bottom: 10 })

            Text('继续使用系统，积累更多对话数据后，系统会自动为你训练专属模型')
              .fontSize(12)
              .fontColor('#999')
              .textAlign(TextAlign.Center)
              .margin({ bottom: 20 })

            // 进度提示
            Row() {
              Text(`当前数据: ${this.loraStatus.training_data_size}/20`)
                .fontSize(12)
                .fontColor('#666')

              Blank()

              Text(`${Math.min(100, (this.loraStatus.training_data_size / 20 * 100)).toFixed(0)}%`)
                .fontSize(12)
                .fontColor('#666')
            }
            .width('100%')
            .margin({ bottom: 5 })

            Progress({
              value: this.loraStatus.training_data_size,
              total: 20,
              type: ProgressType.Linear
            })
              .width('100%')
              .color('#007AFF')
          }
          .width('100%')
          .alignItems(HorizontalAlign.Center)
        }
      } else {
        // 加载中
        Column() {
          LoadingProgress()
            .width(40)
            .height(40)
            .margin({ bottom: 10 })

          Text('加载中...')
            .fontSize(14)
            .fontColor('#999')
        }
        .width('100%')
        .height(150)
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      }
    }
    .width('100%')
    .padding(20)
    .backgroundColor(Color.White)
    .borderRadius(15)
    .shadow({
      radius: 10,
      color: '#00000015',
      offsetX: 0,
      offsetY: 3
    })
  }

  // 获取状态颜色
  getStatusColor(): string {
    if (!this.loraStatus) return '#999'
    if (this.isTraining) return '#FFC107' // 训练中-黄色
    if (this.loraStatus.has_lora) return '#4CAF50' // 已训练-绿色
    return '#999' // 未训练-灰色
  }

  // 获取状态文本
  getStatusText(): string {
    if (!this.loraStatus) return '加载中'
    if (this.isTraining) return '训练中'
    if (this.loraStatus.has_lora) return '已激活'
    return '未训练'
  }

  // 计算个性化程度
  calculatePersonalization(): number {
    if (!this.loraStatus || !this.loraStatus.has_lora) return 0

    // 基于训练数据量和模型版本计算
    const dataScore = Math.min(100, (this.loraStatus.training_data_size / 100) * 60)
    const versionScore = Math.min(40, this.loraStatus.model_version * 10)

    return Math.round(dataScore + versionScore)
  }

  // 格式化时间
  formatTime(isoString: string): string {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return '今天'
    if (diffDays === 1) return '昨天'
    if (diffDays < 7) return `${diffDays}天前`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}周前`
    return `${Math.floor(diffDays / 30)}个月前`
  }

  // 触发训练
  async triggerTraining() {
    this.isTraining = true

    try {
      // 调用API触发训练
      const response = await fetch('https://u821458-a197-3cecd37e.westc.seetacloud.com:8443/api/lora/train/user_001?priority=high', {
        method: 'POST'
      })

      const result = await response.json()

      if (result.code === 200) {
        // 显示成功提示
        promptAction.showToast({
          message: '训练任务已添加到队列',
          duration: 2000
        })

        // 刷新状态
        setTimeout(() => {
          this.loadLoRAStatus()
        }, 2000)
      } else {
        promptAction.showToast({
          message: '训练失败: ' + result.message,
          duration: 2000
        })
      }
    } catch (error) {
      promptAction.showToast({
        message: '网络错误',
        duration: 2000
      })
    } finally {
      this.isTraining = false
    }
  }

  // 加载LoRA状态
  async loadLoRAStatus() {
    try {
      const response = await fetch('https://u821458-a197-3cecd37e.westc.seetacloud.com:8443/api/lora/status/user_001')
      const result = await response.json()

      if (result.code === 200) {
        this.loraStatus = result.data
      }
    } catch (error) {
      console.error('加载LoRA状态失败:', error)
    }
  }

  aboutToAppear() {
    this.loadLoRAStatus()
  }
}
