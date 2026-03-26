/**
 * 快速决策输入 - HarmonyOS 6 流体设计
 * 让用户更轻松地创建决策副本
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import promptAction from '@ohos.promptAction'
import { ApiConfig } from '../config/ApiConfig'
import { getUserId } from '../service/UserSessionManager'
import { Theme } from '../common/Theme'
import { SimpleIcon } from '../components/IconRenderer'

interface QuickTemplate {
  id: string
  icon: string
  title: string
  description: string
  prompt: string
  color: string
}

interface LoraStatusInfo {
  has_lora: boolean
  lora_path: string | null
  model_version: number
  last_train_time: string | null
  training_data_size: number
  is_loaded: boolean
}

interface DecisionRecord {
  session_id: string
  question: string
  options_count: number
  created_at: string
}

@Entry
@Component
struct QuickDecisionInput {
  @State userInput: string = ''
  @State isListening: boolean = false
  @State isProcessing: boolean = false
  @State aiSuggestion: string = ''
  @State showContent: boolean = false
  @State selectedTemplate: QuickTemplate | null = null
  @State loraStatus: LoraStatusInfo | null = null
  @State isLoadingLora: boolean = false
  @State isTrainingLora: boolean = false
  @State trainingProgress: number = 0
  @State trainingStage: string = ''
  @State decisionHistory: DecisionRecord[] = []
  private trainingPollTimer: number = -1
  @State selectedMenuIdx: number = -1
  private userId: string = ''

  async aboutToAppear() {
    this.userId = await getUserId()
    if (this.userId === 'default_user' || this.userId === '') {
      promptAction.showToast({ message: '请先登录使用决策功能' })
      router.replaceUrl({ url: 'pages/Login' })
      return
    }
    const params = router.getParams() as Record<string, string>
    if (params?.userId) { this.userId = params.userId }
    this.loadLoraStatus()
    this.loadDecisionHistory()
    setTimeout(() => { this.showContent = true }, 50)
  }

  private async loadLoraStatus() {
    this.isLoadingLora = true
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/lora/status/${this.userId}`,
        { method: http.RequestMethod.GET, connectTimeout: 5000, readTimeout: 5000 }
      )
      httpRequest.destroy()
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if ((result.code as number) === 200 && result.data) {
          this.loraStatus = result.data as LoraStatusInfo
        }
      }
    } catch (err) {
      console.error('[QuickDecisionInput] 加载LoRA状态失败:', err)
    } finally { this.isLoadingLora = false }
  }

  private async startLoraTraining() {
    this.isTrainingLora = true
    this.trainingProgress = 0
    this.trainingStage = '提交训练任务...'
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/lora/train/${this.userId}`,
        { method: http.RequestMethod.POST }
      )
      httpRequest.destroy()
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if ((result.code as number) === 200) {
          this.trainingStage = '准备训练数据...'
          this.trainingProgress = 5
          this.startTrainingProgressPoll()
        } else {
          promptAction.showToast({ message: (result.message as string) || '训练启动失败' })
          this.isTrainingLora = false
          this.trainingProgress = 0
          this.trainingStage = ''
        }
      }
    } catch (err) {
      promptAction.showToast({ message: '训练启动失败' })
      this.isTrainingLora = false
      this.trainingProgress = 0
      this.trainingStage = ''
    }
  }

  private startTrainingProgressPoll() {
    if (this.trainingPollTimer !== -1) return
    this.trainingPollTimer = setInterval(() => {
      this.pollTrainingProgress()
    }, 2000)
  }

  private async pollTrainingProgress() {
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/lora/progress/${this.userId}`,
        { method: http.RequestMethod.GET, connectTimeout: 3000, readTimeout: 3000 }
      )
      httpRequest.destroy()
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if ((result.code as number) === 200 && result.data) {
          const data = result.data as Record<string, Object>
          this.trainingProgress = (data.progress as number) || 0
          this.trainingStage = (data.stage as string) || ''
          const isTraining = data.is_training as boolean
          const error = data.error as string | null

          if (!isTraining && this.trainingProgress >= 100) {
            // 训练完成
            this.stopTrainingPoll()
            setTimeout(() => {
              this.isTrainingLora = false
              this.trainingProgress = 0
              this.trainingStage = ''
              this.loadLoraStatus()
              promptAction.showToast({ message: '模型训练完成' })
            }, 1500)
          } else if (!isTraining && error) {
            // 训练失败
            this.stopTrainingPoll()
            this.isTrainingLora = false
            this.trainingProgress = 0
            this.trainingStage = ''
            promptAction.showToast({ message: `训练失败: ${error}` })
          }
        }
      }
    } catch (err) {
      // 轮询失败不中断
    }
  }

  private async checkTrainingComplete() {
    // 已合并到 pollTrainingProgress
  }

  private stopTrainingPoll() {
    if (this.trainingPollTimer !== -1) {
      clearInterval(this.trainingPollTimer)
      this.trainingPollTimer = -1
    }
  }

  private async loadDecisionHistory() {
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/decision/enhanced/history/${this.userId}`,
        { method: http.RequestMethod.GET, connectTimeout: 5000, readTimeout: 5000 }
      )
      httpRequest.destroy()
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if ((result.code as number) === 200 && result.data) {
          this.decisionHistory = (result.data as DecisionRecord[]) || []
        }
      }
    } catch (err) {
      console.error('加载决策历史失败:', err)
    }
  }

  private templates: QuickTemplate[] = [
    { id: 'career', icon: 'briefcase', title: '职业选择', description: '工作、跳槽、转行', prompt: '我在考虑职业发展的问题', color: '#0A59F7' },
    { id: 'study', icon: 'learning', title: '学习深造', description: '考研、留学、培训', prompt: '我在考虑是否继续学习深造', color: '#6B48FF' },
    { id: 'life', icon: 'home', title: '生活规划', description: '买房、结婚、搬家', prompt: '我在考虑生活方面的重大决定', color: '#00C853' },
    { id: 'invest', icon: 'chart', title: '投资理财', description: '创业、投资、理财', prompt: '我在考虑投资或理财的问题', color: '#FF9500' },
  ]

  private startVoiceInput() {
    this.isListening = true
    setTimeout(() => {
      this.isListening = false
      this.userInput = '我不知道毕业后应该考研还是工作'
      router.replaceUrl({ url: 'pages/EnhancedDecisionFlow', params: { userId: this.userId, initialQuestion: this.userInput } })
    }, 2000)
  }

  private async processUserInput() {
    if (!this.userInput.trim()) return
    router.replaceUrl({ url: 'pages/EnhancedDecisionFlow', params: { userId: this.userId, initialQuestion: this.userInput } })
  }

  build() {
    Column() {
      // 顶部导航栏
      Row() {
        Text('←')
          .fontSize(24)
          .fontColor(Theme.Color.Primary)
          .onClick(() => router.back())

        Text('智能决策助手')
          .fontSize(18)
          .fontWeight(FontWeight.Medium)
          .fontColor(Theme.Color.TextPrimary)
          .layoutWeight(1)
          .margin({ left: 12 })
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 12, bottom: 12 })
      .backgroundColor(Theme.Color.BackgroundPrimary)

      Scroll() {
        Column({ space: 20 }) {
          // Hero 区域
          this.buildHeroCard()
          // LoRA 模型卡片
          this.buildLoraCard()
          // 语音输入
          this.buildVoiceSection()
          // 文字输入
          this.buildTextInput()
          // 快速模板
          this.buildTemplateSection()
          // 决策历史记录
          if (this.decisionHistory.length > 0) { this.buildDecisionHistory() }
        }
        .width('100%')
        .padding({ left: 16, right: 16, bottom: 60 })
      }
      .scrollBar(BarState.Off)
      .edgeEffect(EdgeEffect.Spring)
      .layoutWeight(1)
    }
    .width('100%')
    .height('100%')
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }

  @Builder
  buildHeroCard() {
    Stack({ alignContent: Alignment.BottomStart }) {
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({ angle: 135, colors: [['#667eea', 0], ['#764ba2', 1]] })
        .opacity(0.12)

      Circle({ width: 120, height: 120 })
        .fill('#667eea').opacity(0.18).blur(50)
        .position({ x: -30, y: -30 })

      Circle({ width: 80, height: 80 })
        .fill('#764ba2').opacity(0.12).blur(40)
        .position({ x: '75%', y: '55%' })

      Column({ space: 10 }) {
        Stack() {
          Circle({ width: 64, height: 64 })
            .fill(Theme.Color.Primary).opacity(0.15)
          SimpleIcon({ iconName: 'comparison', iconSize: 32, color: Theme.Color.Primary })
        }.width(64).height(64)

        Text('说出你的困惑')
          .fontSize(24)
          .fontWeight(700)
          .fontColor(Theme.Color.TextPrimary)

        Text('用语音或文字描述，AI会帮你深度分析')
          .fontSize(14)
          .fontColor(Theme.Color.TextSecondary)
      }
      .padding(24)
      .width('100%')
      .alignItems(HorizontalAlign.Start)
    }
    .width('100%')
    .height(180)
    .backgroundColor(Theme.Color.GlassHeavy)
    .backdropBlur(Theme.Blur.Heavy)
    .borderRadius(Theme.Radius.xl)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Medium)
    .opacity(this.showContent ? 1 : 0)
    .scale({ x: this.showContent ? 1 : 0.95, y: this.showContent ? 1 : 0.95 })
    .animation({ duration: 700, curve: Curve.Smooth, delay: 0 })
  }

  @Builder
  buildLoraCard() {
    Column({ space: 14 }) {
      Row({ space: 12 }) {
        Stack() {
          Circle({ width: 44, height: 44 }).fill(Theme.Color.Secondary).opacity(0.15)
          SimpleIcon({ iconName: 'brain', iconSize: 22, color: Theme.Color.Secondary })
        }.width(44).height(44)

        Column({ space: 4 }) {
          Text('个性化决策模型')
            .fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
          Text('LoRA微调 · 让AI更懂你的决策风格')
            .fontSize(12).fontColor(Theme.Color.TextTertiary)
        }.alignItems(HorizontalAlign.Start).layoutWeight(1)
      }

      if (this.isLoadingLora) {
        Row() {
          LoadingProgress().width(20).height(20).color(Theme.Color.Primary)
          Text('加载模型状态...').fontSize(13).fontColor(Theme.Color.TextTertiary).margin({ left: 8 })
        }.width('100%').justifyContent(FlexAlign.Center).padding(12)
      } else if (this.loraStatus) {
        Row() {
          Column({ space: 4 }) {
            Text('模型状态').fontSize(11).fontColor(Theme.Color.TextTertiary)
            Text(this.loraStatus.has_lora ? `v${this.loraStatus.model_version}` : '未训练')
              .fontSize(16).fontWeight(600)
              .fontColor(this.loraStatus.has_lora ? Theme.Color.Accent : Theme.Color.TextTertiary)
          }.alignItems(HorizontalAlign.Start)
          Blank()
          Column({ space: 4 }) {
            Text('对话数据').fontSize(11).fontColor(Theme.Color.TextTertiary)
            Text(`${this.loraStatus.training_data_size || 0} / 20`)
              .fontSize(16).fontWeight(600)
              .fontColor((this.loraStatus.training_data_size || 0) >= 20 ? Theme.Color.Primary : Theme.Color.Warning)
          }.alignItems(HorizontalAlign.End)
        }.width('100%')

        Progress({ value: this.loraStatus.training_data_size || 0, total: 20, type: ProgressType.Linear })
          .width('100%')
          .color((this.loraStatus.training_data_size || 0) >= 20 ? Theme.Color.Primary : Theme.Color.Warning)

        Button(this.isTrainingLora ? '训练中...' : '更新模型')
          .width('100%').height(44).fontSize(15).fontWeight(600).fontColor('#FFFFFF')
          .backgroundColor((this.loraStatus.training_data_size || 0) >= 20 && !this.isTrainingLora ? Theme.Color.Secondary : '#CCCCCC')
          .borderRadius(Theme.Radius.l)
          .shadow((this.loraStatus.training_data_size || 0) >= 20 ? Theme.Shadow.GlowPrimary : Theme.Shadow.Soft)
          .enabled((this.loraStatus.training_data_size || 0) >= 20 && !this.isTrainingLora)
          .onClick(() => { this.startLoraTraining() })

        // 训练进度条
        if (this.isTrainingLora) {
          Column({ space: 8 }) {
            Row() {
              Text(this.trainingStage).fontSize(12).fontColor(Theme.Color.Primary).layoutWeight(1)
              Text(`${Math.round(this.trainingProgress)}%`).fontSize(12).fontWeight(600).fontColor(Theme.Color.Primary)
            }.width('100%')
            Progress({ value: this.trainingProgress, total: 100, type: ProgressType.Linear })
              .width('100%').color(Theme.Color.Primary)
          }
          .width('100%').padding(12)
          .backgroundColor('rgba(10, 89, 247, 0.04)')
          .borderRadius(Theme.Radius.m)
          .border({ width: 1, color: 'rgba(10, 89, 247, 0.1)' })
        }

        if ((this.loraStatus.training_data_size || 0) < 20) {
          Text(`还需 ${20 - (this.loraStatus.training_data_size || 0)} 条对话数据才能训练`)
            .fontSize(12).fontColor(Theme.Color.Warning)
        }
      } else {
        Text('模型状态加载失败').fontSize(13).fontColor(Theme.Color.TextTertiary).padding(12)
      }
    }
    .width('100%')
    .padding(20)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 100 })
  }

  @Builder
  buildVoiceSection() {
    Column({ space: 12 }) {
      Button() {
        Column({ space: 10 }) {
          Stack() {
            Circle({ width: 72, height: 72 })
              .fill(this.isListening ? Theme.Color.Destructive : Theme.Color.Primary)
              .opacity(0.12)
            Circle({ width: 56, height: 56 })
              .fill(this.isListening ? Theme.Color.Destructive : Theme.Color.Primary)
              .opacity(0.2)
            SimpleIcon({ iconName: 'mic', iconSize: 28, color: this.isListening ? Theme.Color.Destructive : Theme.Color.Primary })
          }.width(72).height(72)

          Text(this.isListening ? '正在聆听...' : '点击说话')
            .fontSize(15).fontWeight(600)
            .fontColor(this.isListening ? Theme.Color.Destructive : Theme.Color.Primary)
        }
      }
      .width(140).height(140)
      .backgroundColor(this.isListening ? 'rgba(255,59,48,0.06)' : 'rgba(10,89,247,0.06)')
      .borderRadius(70)
      .border({ width: 1, color: this.isListening ? 'rgba(255,59,48,0.15)' : Theme.Color.BorderLight })
      .onClick(() => { if (!this.isListening) this.startVoiceInput() })

      Text('或者')
        .fontSize(13).fontColor(Theme.Color.TextTertiary)
    }
    .width('100%')
    .alignItems(HorizontalAlign.Center)
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 200 })
  }

  @Builder
  buildTextInput() {
    Column({ space: 14 }) {
      TextArea({ placeholder: '输入你的困惑，比如：\n"我不知道毕业后该做什么"\n"要不要换工作"' })
        .width('100%').height(120).padding(16)
        .fontSize(15).fontColor(Theme.Color.TextPrimary)
        .placeholderColor(Theme.Color.TextTertiary)
        .backgroundColor(Theme.Color.BackgroundTertiary)
        .borderRadius(Theme.Radius.l)
        .border({ width: 1, color: Theme.Color.BorderLight })
        .onChange((value: string) => { this.userInput = value })

      Button('开始智能分析')
        .width('100%').height(52).fontSize(16).fontWeight(600)
        .fontColor('#FFFFFF')
        .backgroundColor(this.userInput.trim().length > 0 ? Theme.Color.Primary : '#CCCCCC')
        .borderRadius(Theme.Radius.l)
        .shadow(this.userInput.trim().length > 0 ? Theme.Shadow.GlowPrimary : Theme.Shadow.Soft)
        .enabled(!this.isProcessing && this.userInput.trim().length > 0)
        .onClick(() => { this.processUserInput() })
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 300 })
  }

  @Builder
  buildTemplateSection() {
    Column({ space: 14 }) {
      Text('常见决策场景')
        .fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
        .padding({ left: 4 })
        .opacity(this.showContent ? 1 : 0)
        .translate({ x: this.showContent ? 0 : -20 })
        .animation({ duration: 600, curve: Curve.Smooth, delay: 350 })

      ForEach(this.templates, (template: QuickTemplate, index: number) => {
        this.buildTemplateItem(template, index)
      }, (item: QuickTemplate) => item.id)
    }
    .width('100%')
  }

  @Builder
  buildTemplateItem(template: QuickTemplate, index: number) {
    Row({ space: 14 }) {
      Stack() {
        Circle({ width: 48, height: 48 }).fill(template.color).opacity(0.12)
        SimpleIcon({ iconName: template.icon, iconSize: 24, color: template.color })
      }.width(48).height(48)

      Column({ space: 4 }) {
        Text(template.title)
          .fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
        Text(template.description)
          .fontSize(12).fontColor(Theme.Color.TextTertiary)
      }.alignItems(HorizontalAlign.Start).layoutWeight(1)

      Text('→')
        .fontSize(20).fontColor(Theme.Color.TextTertiary)
        .translate({ x: this.selectedMenuIdx === index ? 4 : 0 })
        .animation({ duration: 300, curve: Curve.Smooth })
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .onClick(() => {
      this.selectedMenuIdx = index
      router.replaceUrl({ url: 'pages/EnhancedDecisionFlow', params: { userId: this.userId, initialQuestion: template.prompt } })
      setTimeout(() => { this.selectedMenuIdx = -1 }, 300)
    })
    .opacity(this.showContent ? 1 : 0)
    .translate({ x: this.showContent ? 0 : -30 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 400 + index * 80 })
    .stateStyles({
      pressed: {
        .scale({ x: 0.98, y: 0.98 })
        .backgroundColor('#F8F9FA')
      },
      normal: {
        .scale({ x: 1, y: 1 })
        .backgroundColor(Theme.Color.BackgroundSecondary)
      }
    })
  }

  @Builder
  buildDecisionHistory() {
    Column({ space: 12 }) {
      Text('决策记录')
        .fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
        .padding({ left: 4 })

      ForEach(this.decisionHistory, (record: DecisionRecord, index: number) => {
        Row({ space: 12 }) {
          Stack() {
            Circle({ width: 40, height: 40 }).fill(Theme.Color.Secondary).opacity(0.12)
            Text(`${index + 1}`).fontSize(14).fontWeight(600).fontColor(Theme.Color.Secondary)
          }.width(40).height(40)

          Column({ space: 4 }) {
            Text(record.question).fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
              .maxLines(1).textOverflow({ overflow: TextOverflow.Ellipsis })
            Text(`${record.options_count} 个选项 · ${record.created_at.slice(0, 10)}`)
              .fontSize(12).fontColor(Theme.Color.TextTertiary)
          }.alignItems(HorizontalAlign.Start).layoutWeight(1)

          Text('查看').fontSize(12).fontColor(Theme.Color.Primary)
        }
        .width('100%').padding(14)
        .backgroundColor(Theme.Color.BackgroundSecondary)
        .borderRadius(Theme.Radius.l)
        .border({ width: 1, color: Theme.Color.BorderLight })
        .shadow(Theme.Shadow.Soft)
        .onClick(() => {
          router.pushUrl({
            url: 'pages/DecisionDungeon2DMap',
            params: { dungeonId: record.session_id, userId: this.userId }
          })
        })
        .opacity(this.showContent ? 1 : 0)
        .translate({ y: this.showContent ? 0 : 20 })
        .animation({ duration: 600, curve: Curve.Smooth, delay: 500 + index * 60 })
      })
    }.width('100%')
  }
}
