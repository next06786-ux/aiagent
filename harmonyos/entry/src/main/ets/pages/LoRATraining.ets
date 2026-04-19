/**
 * 个性模型训练页面 - HarmonyOS 6 流体设计
 * 显示储备模型状态、触发训练、查看模型信息
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { Theme } from '../common/Theme'
import { SimpleIcon } from '../components/IconRenderer'
import promptAction from '@ohos.promptAction'

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

@Entry
@Component
struct LoRATraining {
  @State userId: string = 'test_user_001'
  @State trainingStatus: TrainingStatus | null = null
  @State isLoading: boolean = false
  @State isTraining: boolean = false
  @State errorMessage: string = ''
  @State showContent: boolean = false

  aboutToAppear() {
    this.loadTrainingStatus()
    setTimeout(() => { this.showContent = true }, 50)
  }

  build() {
    Column() {
      // 顶部导航栏
      Row() {
        Text('←')
          .fontSize(24).fontColor(Theme.Color.Primary)
          .onClick(() => { router.back() })

        Text('个性模型训练')
          .fontSize(18).fontWeight(FontWeight.Medium).fontColor(Theme.Color.TextPrimary)
          .layoutWeight(1).margin({ left: 12 })

        Stack() {
          Circle({ width: 40, height: 40 }).fill(Theme.Color.GlassMedium)
          SimpleIcon({ iconName: 'refresh', iconSize: 20, color: Theme.Color.TextSecondary })
        }.width(40).height(40)
        .onClick(() => { this.loadTrainingStatus() })
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 12, bottom: 12 })
      .backgroundColor(Theme.Color.BackgroundPrimary)

      if (this.isLoading) {
        Column({ space: 16 }) {
          LoadingProgress().width(48).height(48).color(Theme.Color.Primary)
          Text('加载中...').fontSize(14).fontColor(Theme.Color.TextTertiary)
        }.width('100%').layoutWeight(1).justifyContent(FlexAlign.Center).alignItems(HorizontalAlign.Center)
      } else if (this.trainingStatus) {
        Scroll() {
          Column({ space: 20 }) {
            this.buildModelStatusCard()
            this.buildTrainingDataCard()
            this.buildTrainingInfoCard()
            this.buildActionButtons()
          }
          .width('100%')
          .padding({ left: 16, right: 16, bottom: 60 })
        }
        .scrollBar(BarState.Off)
        .edgeEffect(EdgeEffect.Spring)
        .layoutWeight(1)
      } else if (this.errorMessage) {
        Column({ space: 16 }) {
          Text('😔').fontSize(48)
          Text(this.errorMessage).fontSize(14).fontColor(Theme.Color.Destructive)
          Button('重试').fontSize(14).fontColor('#FFFFFF').backgroundColor(Theme.Color.Primary)
            .borderRadius(Theme.Radius.round).padding({ left: 24, right: 24, top: 10, bottom: 10 })
            .onClick(() => { this.loadTrainingStatus() })
        }.width('100%').layoutWeight(1).justifyContent(FlexAlign.Center).alignItems(HorizontalAlign.Center)
      }
    }
    .width('100%').height('100%')
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }

  @Builder
  buildModelStatusCard() {
    Stack({ alignContent: Alignment.BottomStart }) {
      Column().width('100%').height('100%')
        .linearGradient({ angle: 135, colors: [['#667eea', 0], ['#764ba2', 1]] })
        .opacity(0.1)
      Circle({ width: 100, height: 100 }).fill('#667eea').opacity(0.15).blur(50).position({ x: -20, y: -20 })

      Column({ space: 14 }) {
        Row({ space: 12 }) {
          Stack() {
            Circle({ width: 48, height: 48 }).fill(Theme.Color.Secondary).opacity(0.15)
            SimpleIcon({ iconName: 'brain', iconSize: 24, color: Theme.Color.Secondary })
          }.width(48).height(48)
          Text('储备模型状态').fontSize(18).fontWeight(700).fontColor(Theme.Color.TextPrimary)
        }

        Row() {
          Column({ space: 4 }) {
            Text('当前版本').fontSize(12).fontColor(Theme.Color.TextTertiary)
            Text(this.trainingStatus?.model_version || '未训练')
              .fontSize(20).fontWeight(700)
              .fontColor(this.trainingStatus?.has_model ? Theme.Color.Accent : Theme.Color.TextTertiary)
          }.alignItems(HorizontalAlign.Start)
          Blank()
          Column({ space: 4 }) {
            Text('训练次数').fontSize(12).fontColor(Theme.Color.TextTertiary)
            Text(`${this.trainingStatus?.total_trainings || 0} 次`)
              .fontSize(20).fontWeight(700).fontColor(Theme.Color.TextPrimary)
          }.alignItems(HorizontalAlign.End)
        }.width('100%')

        if (this.trainingStatus?.last_train_time) {
          Divider().color(Theme.Color.BorderLight)
          Row() {
            Text('上次训练').fontSize(12).fontColor(Theme.Color.TextTertiary)
            Blank()
            Text(this.formatTime(this.trainingStatus!.last_train_time!))
              .fontSize(12).fontColor(Theme.Color.TextPrimary)
          }.width('100%')
        }

        if (this.trainingStatus?.is_training) {
          Row({ space: 8 }) {
            LoadingProgress().width(16).height(16).color(Theme.Color.Primary)
            Text('训练中...').fontSize(14).fontColor(Theme.Color.Primary)
          }
        }
      }.padding(20).width('100%')
    }
    .width('100%')
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.xl)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Medium)
    .opacity(this.showContent ? 1 : 0)
    .scale({ x: this.showContent ? 1 : 0.95, y: this.showContent ? 1 : 0.95 })
    .animation({ duration: 700, curve: Curve.Smooth, delay: 0 })
  }

  @Builder
  buildTrainingDataCard() {
    Column({ space: 14 }) {
      Text('训练样本').fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
      Row() {
        Column({ space: 4 }) {
          Text('当前数据量').fontSize(12).fontColor(Theme.Color.TextTertiary)
          Text(`${this.trainingStatus?.current_data_size || 0} 条`)
            .fontSize(20).fontWeight(700).fontColor(Theme.Color.Primary)
        }.alignItems(HorizontalAlign.Start)
        Blank()
        Column({ space: 4 }) {
          Text('最小要求').fontSize(12).fontColor(Theme.Color.TextTertiary)
          Text(`${this.trainingStatus?.min_data_size || 20} 条`)
            .fontSize(20).fontWeight(700).fontColor(Theme.Color.TextSecondary)
        }.alignItems(HorizontalAlign.End)
      }.width('100%')

      Progress({ value: this.trainingStatus?.current_data_size || 0, total: this.trainingStatus?.min_data_size || 20, type: ProgressType.Linear })
        .width('100%').color(Theme.Color.Primary)

      Text(this.trainingStatus?.can_train ? '✅ 样本充足，可以开始训练储备模型' : `⚠️ 还需要 ${(this.trainingStatus?.min_data_size || 20) - (this.trainingStatus?.current_data_size || 0)} 条对话样本`)
        .fontSize(12).fontColor(this.trainingStatus?.can_train ? Theme.Color.Accent : Theme.Color.Warning)
    }
    .width('100%').padding(20)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 100 })
  }

  @Builder
  buildTrainingInfoCard() {
    Column({ space: 14 }) {
      Text('训练说明').fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
      Text('这里保留个性模型训练能力，当前决策推演默认走云端/API 主链；训练完成后可作为后续可切换的储备能力。')
        .fontSize(14).fontColor(Theme.Color.TextSecondary).lineHeight(22)
      Divider().color(Theme.Color.BorderLight)

      Column({ space: 10 }) {
        this.buildInfoRow('🎯', '训练条件：至少 20 条对话样本')
        this.buildInfoRow('☁️', '当前推演主链：云端/API 推理')
        this.buildInfoRow('⚡', '训练执行：后台 GPU 服务器，约 3-5 分钟')
      }
    }
    .width('100%').padding(20)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 200 })
  }

  @Builder
  buildInfoRow(icon: string, text: string) {
    Row({ space: 10 }) {
      Text(icon).fontSize(16)
      Text(text).fontSize(13).fontColor(Theme.Color.TextSecondary)
    }.width('100%')
  }

  @Builder
  buildActionButtons() {
    Column({ space: 14 }) {
      Button(this.trainingStatus?.is_training ? '训练中...' : '训练储备模型')
        .width('100%').height(52).fontSize(16).fontWeight(600)
        .fontColor('#FFFFFF')
        .backgroundColor(this.trainingStatus?.can_train && !this.trainingStatus?.is_training ? Theme.Color.Primary : '#CCCCCC')
        .borderRadius(Theme.Radius.l)
        .shadow(this.trainingStatus?.can_train ? Theme.Shadow.GlowPrimary : Theme.Shadow.Soft)
        .enabled(this.trainingStatus?.can_train === true && !this.trainingStatus?.is_training)
        .onClick(() => { this.startTraining() })

      if (this.trainingStatus?.has_model) {
        Button('查看模型详情')
          .width('100%').height(52).fontSize(16).fontWeight(600)
          .fontColor(Theme.Color.Primary)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.Primary })
          .onClick(() => { promptAction.showToast({ message: '模型详情开发中' }) })
      }
    }
    .width('100%').padding({ top: 8 })
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 300 })
  }

  async loadTrainingStatus() {
    this.isLoading = true
    this.errorMessage = ''
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/lora/status/${this.userId}`,
        { method: http.RequestMethod.GET, header: { 'Content-Type': 'application/json' } }
      )
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if ((result.code as number) === 200) {
          this.trainingStatus = result.data as TrainingStatus
        } else { this.errorMessage = result.message as string }
      } else { this.errorMessage = `请求失败: ${response.responseCode}` }
      httpRequest.destroy()
    } catch (error) {
      this.errorMessage = `加载失败`
    } finally { this.isLoading = false }
  }

  async startTraining() {
    this.isTraining = true
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/lora/train/${this.userId}`,
        { method: http.RequestMethod.POST, header: { 'Content-Type': 'application/json' } }
      )
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if ((result.code as number) === 200) {
          promptAction.showToast({ message: '储备模型训练已启动，约需3-5分钟' })
          this.loadTrainingStatus()
        } else {
          promptAction.showToast({ message: (result.message as string) || '训练失败' })
        }
      }
      httpRequest.destroy()
    } catch (error) {
      promptAction.showToast({ message: '启动训练失败' })
    } finally { this.isTraining = false }
  }

  formatTime(isoString: string): string {
    const date = new Date(isoString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)
    if (minutes < 60) return `${minutes} 分钟前`
    else if (hours < 24) return `${hours} 小时前`
    else return `${days} 天前`
  }
}
