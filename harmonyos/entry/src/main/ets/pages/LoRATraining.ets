/**
 * LoRA 个性化训练页面
 * 显示训练状态、触发训练、查看模型信息
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { API_CONFIG } from '../config/ApiConfig'

@Entry
@Component
struct LoRATraining {
  @State userId: string = 'test_user_001'
  @State trainingStatus: TrainingStatus | null = null
  @State isLoading: boolean = false
  @State isTraining: boolean = false
  @State errorMessage: string = ''

  aboutToAppear() {
    this.loadTrainingStatus()
  }

  build() {
    Column() {
      // 顶部导航栏
      Row() {
        Image($r('app.media.ic_back'))
          .width(24)
          .height(24)
          .onClick(() => {
            router.back()
          })

        Text('个性化模型训练')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .margin({ left: 12 })

        Blank()

        Image($r('app.media.ic_refresh'))
          .width(24)
          .height(24)
          .onClick(() => {
            this.loadTrainingStatus()
          })
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#FFFFFF')

      if (this.isLoading) {
        // 加载中
        Column() {
          LoadingProgress()
            .width(50)
            .height(50)
            .color('#007DFF')

          Text('加载中...')
            .fontSize(14)
            .fontColor('#999999')
            .margin({ top: 12 })
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
      } else if (this.trainingStatus) {
        // 显示训练状态
        Scroll() {
          Column({ space: 16 }) {
            // 模型状态卡片
            this.ModelStatusCard()

            // 训练数据卡片
            this.TrainingDataCard()

            // 训练历史卡片
            this.TrainingHistoryCard()

            // 操作按钮
            this.ActionButtons()
          }
          .width('100%')
          .padding(16)
        }
        .width('100%')
        .layoutWeight(1)
      } else if (this.errorMessage) {
        // 错误提示
        Column() {
          Text('❌')
            .fontSize(48)

          Text(this.errorMessage)
            .fontSize(14)
            .fontColor('#FF0000')
            .margin({ top: 12 })

          Button('重试')
            .margin({ top: 24 })
            .onClick(() => {
              this.loadTrainingStatus()
            })
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }

  @Builder
  ModelStatusCard() {
    Column({ space: 12 }) {
      Text('模型状态')
        .fontSize(16)
        .fontWeight(FontWeight.Bold)

      Row() {
        Column({ space: 4 }) {
          Text('当前版本')
            .fontSize(12)
            .fontColor('#666666')

          Text(this.trainingStatus?.model_version || '未训练')
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .fontColor(this.trainingStatus?.has_model ? '#00C853' : '#999999')
        }
        .alignItems(HorizontalAlign.Start)

        Blank()

        Column({ space: 4 }) {
          Text('训练次数')
            .fontSize(12)
            .fontColor('#666666')

          Text(`${this.trainingStatus?.total_trainings || 0} 次`)
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
        }
        .alignItems(HorizontalAlign.End)
      }
      .width('100%')

      if (this.trainingStatus?.last_train_time) {
        Divider()

        Row() {
          Text('上次训练')
            .fontSize(12)
            .fontColor('#666666')

          Blank()

          Text(this.formatTime(this.trainingStatus.last_train_time))
            .fontSize(12)
            .fontColor('#333333')
        }
        .width('100%')
      }

      if (this.trainingStatus?.is_training) {
        Divider()

        Row() {
          LoadingProgress()
            .width(16)
            .height(16)
            .color('#007DFF')

          Text('训练中...')
            .fontSize(14)
            .fontColor('#007DFF')
            .margin({ left: 8 })
        }
      }
    }
    .width('100%')
    .padding(16)
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
  }

  @Builder
  TrainingDataCard() {
    Column({ space: 12 }) {
      Text('训练数据')
        .fontSize(16)
        .fontWeight(FontWeight.Bold)

      Row() {
        Column({ space: 4 }) {
          Text('当前数据量')
            .fontSize(12)
            .fontColor('#666666')

          Text(`${this.trainingStatus?.current_data_size || 0} 条`)
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .fontColor('#007DFF')
        }
        .alignItems(HorizontalAlign.Start)

        Blank()

        Column({ space: 4 }) {
          Text('最小要求')
            .fontSize(12)
            .fontColor('#666666')

          Text(`${this.trainingStatus?.min_data_size || 20} 条`)
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .fontColor('#666666')
        }
        .alignItems(HorizontalAlign.End)
      }
      .width('100%')

      // 进度条
      Progress({
        value: this.trainingStatus?.current_data_size || 0,
        total: this.trainingStatus?.min_data_size || 20,
        type: ProgressType.Linear
      })
        .width('100%')
        .color('#007DFF')

      if (this.trainingStatus?.can_train) {
        Text('✅ 数据充足，可以开始训练')
          .fontSize(12)
          .fontColor('#00C853')
      } else {
        Text(`⚠️ 还需要 ${(this.trainingStatus?.min_data_size || 20) - (this.trainingStatus?.current_data_size || 0)} 条对话`)
          .fontSize(12)
          .fontColor('#FF9800')
      }
    }
    .width('100%')
    .padding(16)
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
  }

  @Builder
  TrainingHistoryCard() {
    Column({ space: 12 }) {
      Text('训练说明')
        .fontSize(16)
        .fontWeight(FontWeight.Bold)

      Text('个性化模型会根据你的对话习惯自动训练，让 AI 更懂你。')
        .fontSize(14)
        .fontColor('#666666')
        .lineHeight(22)

      Divider()

      Row({ space: 8 }) {
        Text('🎯')
          .fontSize(16)

        Text('训练条件：至少 20 条对话')
          .fontSize(12)
          .fontColor('#666666')
      }
      .width('100%')

      Row({ space: 8 }) {
        Text('⏰')
          .fontSize(16)

        Text('训练频率：每 7 天自动训练一次')
          .fontSize(12)
          .fontColor('#666666')
      }
      .width('100%')

      Row({ space: 8 }) {
        Text('⚡')
          .fontSize(16)

        Text('训练时长：约 3-5 分钟')
          .fontSize(12)
          .fontColor('#666666')
      }
      .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
  }

  @Builder
  ActionButtons() {
    Column({ space: 12 }) {
      Button(this.trainingStatus?.is_training ? '训练中...' : '立即训练')
        .width('100%')
        .height(48)
        .fontSize(16)
        .fontColor('#FFFFFF')
        .backgroundColor(this.trainingStatus?.can_train && !this.trainingStatus?.is_training ? '#007DFF' : '#CCCCCC')
        .enabled(this.trainingStatus?.can_train && !this.trainingStatus?.is_training)
        .onClick(() => {
          this.startTraining()
        })

      if (this.trainingStatus?.has_model) {
        Button('查看模型详情')
          .width('100%')
          .height(48)
          .fontSize(16)
          .fontColor('#007DFF')
          .backgroundColor('#FFFFFF')
          .border({ width: 1, color: '#007DFF' })
          .onClick(() => {
            // TODO: 跳转到模型详情页
          })
      }
    }
    .width('100%')
  }

  // 加载训练状态
  async loadTrainingStatus() {
    this.isLoading = true
    this.errorMessage = ''

    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${API_CONFIG.BASE_URL}/api/lora/status/${this.userId}`,
        {
          method: http.RequestMethod.GET,
          header: {
            'Content-Type': 'application/json'
          }
        }
      )

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string)
        if (result.code === 200) {
          this.trainingStatus = result.data
        } else {
          this.errorMessage = result.message
        }
      } else {
        this.errorMessage = `请求失败: ${response.responseCode}`
      }

      httpRequest.destroy()
    } catch (error) {
      console.error('加载训练状态失败:', error)
      this.errorMessage = `加载失败: ${error.message}`
    } finally {
      this.isLoading = false
    }
  }

  // 开始训练
  async startTraining() {
    this.isTraining = true

    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${API_CONFIG.BASE_URL}/api/lora/train/${this.userId}`,
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json'
          }
        }
      )

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string)
        if (result.code === 200) {
          // 训练已启动
          AlertDialog.show({
            title: '训练已启动',
            message: '模型训练需要 3-5 分钟，请稍后查看结果',
            confirm: {
              value: '确定',
              action: () => {
                this.loadTrainingStatus()
              }
            }
          })
        } else {
          AlertDialog.show({
            title: '训练失败',
            message: result.message
          })
        }
      }

      httpRequest.destroy()
    } catch (error) {
      console.error('启动训练失败:', error)
      AlertDialog.show({
        title: '错误',
        message: `启动训练失败: ${error.message}`
      })
    } finally {
      this.isTraining = false
    }
  }

  // 格式化时间
  formatTime(isoString: string): string {
    const date = new Date(isoString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 60) {
      return `${minutes} 分钟前`
    } else if (hours < 24) {
      return `${hours} 小时前`
    } else {
      return `${days} 天前`
    }
  }
}

// 训练状态接口
interface TrainingStatus {
  user_id: string
  has_model: boolean
  model_path: string | null
  model_version: string
  last_train_time: string | null
  total_trainings: number
  current_data_size: number
  min_data_size: number
  is_training: boolean
  can_train: boolean
}
