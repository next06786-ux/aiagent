/**
 * 增强决策流程页面
 * 两阶段信息收集 + 个性化决策模拟
 * 阶段1: 用户自由表达 -> AI问"还有吗" -> 用户说"没了"
 * 阶段2: AI针对性提问收集信息
 * 阶段3: 本地模型+LoRA决策模拟
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import promptAction from '@ohos.promptAction'
import { ApiConfig } from '../config/ApiConfig'
import { getUserId } from '../service/UserSessionManager'
import picker from '@ohos.file.picker'
import media from '@ohos.multimedia.media'
import common from '@ohos.app.ability.common'
import fs from '@ohos.file.fs'
import abilityAccessCtrl from '@ohos.abilityAccessCtrl'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

interface CollectedInfo {
  decision_context: Record<string, string>
  user_constraints: Record<string, string>
  priorities: Record<string, string>
  concerns: string[]
  options_mentioned: string[]
}

interface OptionInput {
  title: string
  description: string
}

interface SimulationOption {
  option_id: string
  title: string
  description: string
  final_score: number
  risk_level: number
  timeline: TimelineEvent[]
}

interface TimelineEvent {
  month: number
  event: string
  impact: Record<string, number>
  probability: number
}

interface SimulationResult {
  simulation_id: string
  question: string
  options: SimulationOption[]
  recommendation: string
  used_lora: boolean
}

@Entry
@Component
struct EnhancedDecisionFlow {
  @State currentPhase: 'init' | 'user_free_talk' | 'ai_questioning' | 'ask_options' | 'simulation' | 'result' = 'init'
  @State sessionId: string = ''
  @State userId: string = ''
  @State initialQuestion: string = ''
  @State messages: Message[] = []
  @State userInput: string = ''
  @State isLoading: boolean = false
  @State collectedInfo: CollectedInfo | null = null
  @State simulationResult: SimulationResult | null = null
  @State currentRound: number = 0
  @State userOptions: string[] = []  // 用户提供的选项
  @State aiSuggestedOptions: OptionInput[] = []  // AI建议的选项
  @State allOptions: OptionInput[] = []  // 所有选项（用户+AI）
  @State isRecording: boolean = false
  @State isVoiceMode: boolean = false
  @State showPlusMenu: boolean = false
  @State isInCall: boolean = false
  @State callDurationText: string = '00:00'
  private callTimer: number = -1
  private callDuration: number = 0
  @State selectedImageUri: string = ''
  private audioRecorder: media.AVRecorder | null = null
  private recordFilePath: string = ''
  private inputController: TextInputController = new TextInputController()

  async aboutToAppear() {
    // 获取真实用户ID
    this.userId = await getUserId()
    console.info('[EnhancedDecisionFlow] 获取到用户ID:', this.userId)
    
    // 如果是 default_user，说明未登录，跳转到登录页
    if (this.userId === 'default_user' || this.userId === '') {
      console.warn('[EnhancedDecisionFlow] 用户未登录，跳转到登录页')
      promptAction.showToast({ message: '请先登录' })
      router.replaceUrl({ url: 'pages/Login' })
      return
    }

    // 处理路由参数
    const params = router.getParams() as Record<string, string>
    if (params?.userId) {
      this.userId = params.userId
    }
    if (params?.initialQuestion) {
      this.initialQuestion = params.initialQuestion
      // 如果有初始问题，自动开始收集
      setTimeout(() => {
        this.startCollection()
      }, 500)
    }
  }

  aboutToDisappear() {
    // 清理通话计时器
    if (this.callTimer !== -1) {
      clearInterval(this.callTimer)
      this.callTimer = -1
    }
    // 停止录音
    if (this.isRecording) {
      this.stopRecording()
    }
  }

  // 开始信息收集
  private async startCollection() {
    if (!this.initialQuestion.trim()) {
      return
    }

    // 确保用户ID已加载
    if (!this.userId || this.userId === '') {
      console.warn('[EnhancedDecisionFlow] 用户ID未加载，等待...')
      this.userId = await getUserId()
      console.info('[EnhancedDecisionFlow] 重新获取用户ID:', this.userId)
    }

    console.info('[EnhancedDecisionFlow] 开始收集，用户ID:', this.userId)

    this.isLoading = true

    try {
      const httpRequest = http.createHttp()
      
      console.info('[EnhancedDecisionFlow] 请求数据 - user_id:', this.userId, 'question:', this.initialQuestion)
      
      const response = await httpRequest.request(
        ApiConfig.getApiUrl('/api/decision/enhanced/collect/start'),
        {
          method: http.RequestMethod.POST,
          header: { 'Content-Type': 'application/json' },
          extraData: JSON.stringify({ user_id: this.userId, initial_question: this.initialQuestion }),
          connectTimeout: 30000,
          readTimeout: 30000
        }
      )
      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if (result.code === 200 && result.data) {
          const data = result.data as Record<string, string>
          this.sessionId = data.session_id
          this.currentPhase = 'user_free_talk'
          
          console.info('[EnhancedDecisionFlow] 会话创建成功:', this.sessionId)
          
          // 添加系统消息
          this.messages.push({
            role: 'system',
            content: data.message,
            timestamp: new Date().toISOString()
          })
        }
      }
    } catch (error) {
      console.error('开始收集失败:', (error as Error).message)
    }

    this.isLoading = false
  }

  // 继续信息收集
  private async continueCollection(overrideText?: string) {
    const msgText = overrideText ?? this.userInput
    if (!msgText.trim()) {
      return
    }
    if (overrideText) {
      this.userInput = overrideText
    }

    // 如果在询问选项阶段
    if (this.currentPhase === 'ask_options') {
      this.handleUserOptions()
      return
    }

    // 添加用户消息
    this.messages.push({
      role: 'user',
      content: this.userInput,
      timestamp: new Date().toISOString()
    })

    const userMessage = this.userInput
    this.userInput = ''
    this.isLoading = true

    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        ApiConfig.getApiUrl('/api/decision/enhanced/collect/continue'),
        {
          method: http.RequestMethod.POST,
          header: { 'Content-Type': 'application/json' },
          extraData: JSON.stringify({
            session_id: this.sessionId,
            user_response: userMessage
          }),
          connectTimeout: 30000,
          readTimeout: 30000
        }
      )
      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if (result.code === 200 && result.data) {
          const data = result.data as Record<string, Object>
          const round = data.round as number
          this.currentRound = round || this.currentRound + 1

          const isComplete = data.is_complete as boolean
          if (isComplete) {
            // 信息收集完成，询问用户选项
            this.collectedInfo = data.collected_info as CollectedInfo
            const summary = data.summary as string
            this.messages.push({
              role: 'assistant',
              content: `信息收集完成！\n\n${summary}`,
              timestamp: new Date().toISOString()
            })
            
            // 进入询问选项阶段
            this.currentPhase = 'ask_options'
            setTimeout(() => {
              this.messages.push({
                role: 'assistant',
                content: '你有明确的选择吗？如果有，请告诉我你考虑的选项（用逗号分隔，比如：考研,工作,创业）。如果没有，直接说"没有"，我会为你推荐一些选项。',
                timestamp: new Date().toISOString()
              })
            }, 500)
          } else {
            // 继续收集
            const phase = data.phase as string
            this.currentPhase = phase as 'user_free_talk' | 'ai_questioning'
            const aiQuestion = data.ai_question as string
            this.messages.push({
              role: 'assistant',
              content: aiQuestion,
              timestamp: new Date().toISOString()
            })
          }
        }
      }
    } catch (error) {
      console.error('继续收集失败:', (error as Error).message)
      this.messages.push({
        role: 'system',
        content: '抱歉，出现了错误，请重试',
        timestamp: new Date().toISOString()
      })
    }

    this.isLoading = false
  }

  // 处理用户选项输入
  private async handleUserOptions(): Promise<void> {
    const userResponse = this.userInput.trim()
    
    // 添加用户消息
    this.messages.push({
      role: 'user',
      content: userResponse,
      timestamp: new Date().toISOString()
    })
    
    this.userInput = ''
    this.isLoading = true

    // 检查用户是否有明确选项
    const hasNoOptions = userResponse.includes('没有') || 
                         userResponse.includes('不知道') || 
                         userResponse.includes('没想好') ||
                         userResponse.toLowerCase().includes('no')

    if (!hasNoOptions) {
      // 用户提供了选项，解析它们
      this.userOptions = userResponse.split(/[,，、]/).map(opt => opt.trim()).filter(opt => opt.length > 0)
    }

    // 请求 AI 生成建议选项
    await this.generateAISuggestions()
    
    this.isLoading = false
  }

  // 生成 AI 建议选项
  private async generateAISuggestions(): Promise<void> {
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        ApiConfig.getApiUrl('/api/decision/enhanced/generate-options'),
        {
          method: http.RequestMethod.POST,
          header: { 'Content-Type': 'application/json' },
          extraData: JSON.stringify({
            session_id: this.sessionId,
            user_options: this.userOptions
          }),
          connectTimeout: 30000,
          readTimeout: 30000
        }
      )
      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>
        if (result.code === 200 && result.data) {
          const data = result.data as Record<string, Object>
          const aiOptions = data.ai_options as OptionInput[]
          this.aiSuggestedOptions = aiOptions

          // 合并所有选项，优先用户选项，总数不超过4个
          this.allOptions = []
          
          // 添加用户选项（优先）
          for (const userOpt of this.userOptions) {
            if (this.allOptions.length >= 4) break
            const opt: OptionInput = { title: userOpt, description: `你提出的选择` }
            this.allOptions.push(opt)
          }
          
          // 添加 AI 建议（补充到4个以内）
          for (const aiOpt of this.aiSuggestedOptions) {
            if (this.allOptions.length >= 4) break
            this.allOptions.push(aiOpt)
          }

          // 也检查信息收集阶段提取到的选项
          if (this.collectedInfo && this.collectedInfo.options_mentioned.length > 0 && this.userOptions.length === 0) {
            // 用户没有明确给选项，但信息收集阶段提取到了
            const existingTitles = this.allOptions.map(o => o.title)
            for (const mentioned of this.collectedInfo.options_mentioned) {
              if (this.allOptions.length >= 4) break
              if (!existingTitles.includes(mentioned)) {
                this.allOptions.unshift({ title: mentioned, description: '信息收集中提到的选项' })
              }
            }
            // 再次限制到4个
            this.allOptions = this.allOptions.slice(0, 4)
          }

          // 显示选项确认
          this.showOptionsConfirmation()
        }
      }
    } catch (error) {
      console.error('生成AI建议失败:', (error as Error).message)
      // 降级：使用默认选项
      this.useDefaultOptions()
    }
  }

  // 显示选项确认
  private showOptionsConfirmation(): void {
    let optionsText = '我为你准备了以下选项：\n\n'
    for (let i = 0; i < this.allOptions.length; i++) {
      const opt = this.allOptions[i]
      optionsText += `${i + 1}. ${opt.title}\n`
    }
    optionsText += '\n点击"开始模拟"为每个选项创建决策副本。'

    this.messages.push({
      role: 'assistant',
      content: optionsText,
      timestamp: new Date().toISOString()
    })

    this.currentPhase = 'simulation'
  }

  // 使用默认选项
  private useDefaultOptions(): void {
    if (this.userOptions.length > 0) {
      // 只使用用户选项
      for (const userOpt of this.userOptions) {
        const opt: OptionInput = { title: userOpt, description: `你提出的选择` }
        this.allOptions.push(opt)
      }
    } else {
      // 使用通用默认选项
      const opt1: OptionInput = { title: '选项A', description: '第一个选择' }
      const opt2: OptionInput = { title: '选项B', description: '第二个选择' }
      this.allOptions = [opt1, opt2]
    }
    this.showOptionsConfirmation()
  }

  // 显示选项输入
  private showOptionsInput(): void {
    // 已废弃，使用新的流程
    this.startSimulation(this.allOptions)
  }

  // 开始决策模拟
  private async startSimulation(options: OptionInput[]): Promise<void> {
    try {
      router.replaceUrl({
        url: 'pages/DecisionDungeon2DMap',
        params: {
          dungeonId: this.sessionId,
          question: this.initialQuestion,
          userId: this.userId,
          simulationData: JSON.stringify({
            simulation_id: this.sessionId,
            user_id: this.userId,
            question: this.initialQuestion,
            options: options,
            recommendation: '',
            created_at: new Date().toISOString()
          })
        }
      })
    } catch (error) {
      console.error('跳转到决策地图失败:', (error as Error).message)
      promptAction.showToast({ message: '进入决策地图失败' })
    }
  }

  build() {
    Column() {
      // 顶部导航
      Row() {
        Button({ type: ButtonType.Circle }) {
          Text('←')
            .fontSize(24)
            .fontColor('#1A1A1A')
            .fontWeight(600)
        }
        .width(40)
        .height(40)
        .backgroundColor('rgba(0,0,0,0)')
        .onClick(() => router.back())

        Text('智能决策助手')
          .fontSize(20)
          .fontWeight(700)
          .fontColor('#1A1A1A')
          .layoutWeight(1)
          .margin({ left: 12 })

        // 阶段指示器
        Text(this.getPhaseText())
          .fontSize(12)
          .fontWeight(600)
          .fontColor('#007AFF')
          .padding({ left: 12, right: 12, top: 6, bottom: 6 })
          .backgroundColor('rgba(0,122,255,0.1)')
          .borderRadius(12)
      }
      .width('100%')
      .height(56)
      .padding({ left: 16, right: 16 })
      .backgroundColor('rgba(255,255,255,0.95)')

      // 主内容区
      if (this.currentPhase === 'init') {
        this.InitView()
      } else if (this.currentPhase === 'result') {
        this.ResultView()
      } else {
        this.ChatView()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F7FA')
  }

  // 初始化视图
  @Builder
  InitView() {
    Column({ space: 24 }) {
      // 标题
      Column({ space: 20 }) {
        // AI图标
        Stack() {
          Circle({ width: 80, height: 80 })
            .fill('linear-gradient(135deg, #667eea, #764ba2)')
            .opacity(0.15)
          
          Circle({ width: 64, height: 64 })
            .fill('linear-gradient(135deg, #667eea, #764ba2)')
            .opacity(0.25)
          
          Text('AI')
            .fontSize(28)
            .fontWeight(700)
            .fontColor('#667eea')
        }
        .width(80)
        .height(80)

        Column({ space: 8 }) {
          Text('AI决策助手')
            .fontSize(32)
            .fontWeight(700)
            .fontColor('#1A1A1A')

          Text('通过对话深入了解你的情况\n为你提供个性化的决策建议')
            .fontSize(16)
            .fontColor('#666')
            .textAlign(TextAlign.Center)
            .lineHeight(24)
        }
      }
      .width('100%')
      .padding({ top: 60 })

      // 输入框
      Column({ space: 16 }) {
        Text('你面临什么决策？')
          .fontSize(18)
          .fontWeight(600)
          .fontColor('#1A1A1A')
          .alignSelf(ItemAlign.Start)

        TextArea({ placeholder: '比如：我不知道毕业后该考研还是工作...' })
          .width('100%')
          .height(120)
          .padding(16)
          .fontSize(16)
          .fontColor('#1A1A1A')
          .backgroundColor(Color.White)
          .borderRadius(16)
          .onChange((value: string) => {
            this.initialQuestion = value
          })

        Button('开始对话')
          .width('100%')
          .height(48)
          .fontSize(16)
          .fontWeight(600)
          .fontColor(Color.White)
          .backgroundColor('#007AFF')
          .borderRadius(12)
          .enabled(!this.isLoading && this.initialQuestion.trim().length > 0)
          .onClick(() => {
            this.startCollection()
          })
      }
      .width('100%')
      .padding(20)
    }
    .width('100%')
    .layoutWeight(1)
  }

  // 对话视图
  @Builder
  ChatView() {
    Column() {
      // 消息列表
      Scroll() {
        Column({ space: 16 }) {
          // 显示初始问题
          Row() {
            Column({ space: 8 }) {
              Text('你的问题')
                .fontSize(12)
                .fontColor('#999')
              Text(this.initialQuestion)
                .fontSize(16)
                .fontColor('#1A1A1A')
                .fontWeight(600)
            }
            .alignItems(HorizontalAlign.Start)
            .layoutWeight(1)
          }
          .width('100%')
          .padding(16)
          .backgroundColor('rgba(0,122,255,0.05)')
          .borderRadius(12)

          // 消息列表
          ForEach(this.messages, (msg: Message, index: number) => {
            this.MessageBubble(msg)
          })

          // 加载指示器
          if (this.isLoading) {
            Row({ space: 8 }) {
              LoadingProgress()
                .width(20)
                .height(20)
                .color('#007AFF')
              Text('AI思考中...')
                .fontSize(14)
                .fontColor('#666')
            }
            .padding(16)
          }
        }
        .width('100%')
        .padding(16)
      }
      .layoutWeight(1)
      .scrollBar(BarState.Auto)

      // 输入框
      if (this.currentPhase !== 'simulation' && this.currentPhase !== 'result') {
        Column() {
          // 主输入栏
          Row({ space: 8 }) {
            // 左：拍照
            Button({ type: ButtonType.Circle }) {
              Text('+')
                .fontSize(18)
                .fontColor('#666')
            }
            .width(38).height(38)
            .backgroundColor('#F2F2F7')
            .border({ width: 0.5, color: '#E0E0E0' })
            .onClick(() => {
              this.showPlusMenu = false
              this.getUIContext().getRouter().pushUrl({ url: 'pages/Camera' })
            })

            // 中：输入框 或 按住说话
            if (this.isVoiceMode) {
              Column() {
                Text(this.isRecording ? '●' : '~')
                  .fontSize(16)
                  .fontColor(this.isRecording ? '#FF3B30' : '#666')
                Text(this.isRecording ? '松开发送' : '按住说话')
                  .fontSize(13).fontWeight(600)
                  .fontColor(this.isRecording ? '#FF3B30' : '#666')
              }
              .layoutWeight(1).height(40)
              .justifyContent(FlexAlign.Center)
              .backgroundColor(this.isRecording ? 'rgba(255,59,48,0.08)' : '#F2F2F7')
              .borderRadius(20)
              .border({ width: this.isRecording ? 1.5 : 0.5,
                color: this.isRecording ? '#FF3B30' : '#E0E0E0' })
              .onTouch((event: TouchEvent) => {
                if (event.type === TouchType.Down) { this.startRecording() }
                else if (event.type === TouchType.Up || event.type === TouchType.Cancel) {
                  if (this.isRecording) { this.stopRecording() }
                }
              })
            } else {
              TextInput({ placeholder: this.getInputPlaceholder(), text: this.userInput, controller: this.inputController })
                .layoutWeight(1).height(40).fontSize(15)
                .fontColor('#1A1A1A').placeholderColor('#999')
                .backgroundColor('#F2F2F7')
                .borderRadius(20)
                .border({ width: 0.5, color: '#E0E0E0' })
                .padding({ left: 14, right: 14 })
                .onChange((value: string) => { this.userInput = value; this.showPlusMenu = false })
            }

            // 右1：语音/文本切换
            Button({ type: ButtonType.Circle }) {
              Text(this.isVoiceMode ? 'Aa' : '~')
                .fontSize(this.isVoiceMode ? 14 : 18)
                .fontColor(this.isVoiceMode ? '#007AFF' : '#666')
            }
            .width(38).height(38)
            .backgroundColor(this.isVoiceMode ? 'rgba(0,122,255,0.08)' : '#F2F2F7')
            .border({ width: 0.5, color: this.isVoiceMode ? '#007AFF' : '#E0E0E0' })
            .onClick(() => {
              this.isVoiceMode = !this.isVoiceMode
              this.showPlusMenu = false
              if (!this.isVoiceMode) { this.userInput = '' }
            })

            // 右2：加号按钮 或 发送按钮（文本模式有内容时变发送）
            if (!this.isVoiceMode && this.userInput.trim().length > 0) {
              Button({ type: ButtonType.Circle }) {
                Text('>')
                  .fontSize(16)
                  .fontColor('#FFFFFF')
              }
              .width(38).height(38)
              .backgroundColor(this.isLoading ? '#CCCCCC' : '#007AFF')
              .enabled(!this.isLoading)
              .onClick(() => { this.continueCollection() })
            } else {
              Button({ type: ButtonType.Circle }) {
                Text(this.showPlusMenu ? '×' : '+')
                  .fontSize(22).fontWeight(300)
                  .fontColor(this.showPlusMenu ? '#FF3B30' : '#666')
              }
              .width(38).height(38)
              .backgroundColor(this.showPlusMenu ? 'rgba(255,59,48,0.08)' : '#F2F2F7')
              .border({ width: 0.5, color: this.showPlusMenu ? '#FF3B30' : '#E0E0E0' })
              .onClick(() => { this.showPlusMenu = !this.showPlusMenu })
            }
          }
          .width('100%').padding({ left: 12, right: 12, top: 8, bottom: 14 })
          .border({ width: { top: 0.5 }, color: '#E0E0E0' })

          // 加号展开菜单
          if (this.showPlusMenu) {
            Row({ space: 24 }) {
              // 相册
              Column({ space: 6 }) {
                Button({ type: ButtonType.Circle }) {
                  Text('Pic')
                    .fontSize(13)
                    .fontColor('#007AFF')
                }
                .width(52).height(52)
                .backgroundColor('rgba(0,122,255,0.08)')
                .border({ width: 1, color: 'rgba(0,122,255,0.15)' })
                .onClick(() => { this.showPlusMenu = false; this.pickImage() })
                Text('相册').fontSize(12).fontColor('#666')
              }.alignItems(HorizontalAlign.Center)

              // 通话
              Column({ space: 6 }) {
                Button({ type: ButtonType.Circle }) {
                  Text(this.isInCall ? 'x' : 'Tel')
                    .fontSize(this.isInCall ? 18 : 13)
                    .fontColor(this.isInCall ? '#FFFFFF' : '#00C853')
                }
                .width(52).height(52)
                .backgroundColor(this.isInCall ? '#FF3B30' : 'rgba(0,200,83,0.10)')
                .border({ width: 1, color: this.isInCall ? '#FF3B30' : 'rgba(0,200,83,0.2)' })
                .onClick(() => {
                  this.showPlusMenu = false
                  if (this.isInCall) { this.endCall() } else { this.startCall() }
                })
                Text(this.isInCall ? this.callDurationText : '通话')
                  .fontSize(12)
                  .fontColor(this.isInCall ? '#FF3B30' : '#666')
              }.alignItems(HorizontalAlign.Center)
            }
            .width('100%')
            .padding({ left: 24, right: 24, top: 12, bottom: 16 })
            .backgroundColor('#F8F8F8')
            .border({ width: { top: 0.5 }, color: '#E0E0E0' })
            .justifyContent(FlexAlign.Start)
            .animation({ duration: 200, curve: Curve.EaseOut })
          }
        }
        .width('100%')
        .backgroundColor(Color.White)
      } else if (this.currentPhase === 'simulation') {
        // 显示开始模拟按钮
        Row() {
          Button('开始模拟')
            .width('90%')
            .height(48)
            .fontSize(16)
            .fontWeight(600)
            .fontColor(Color.White)
            .backgroundColor('#007AFF')
            .borderRadius(24)
            .enabled(!this.isLoading)
            .onClick(() => {
              this.startSimulation(this.allOptions)
            })
        }
        .width('100%')
        .padding(16)
        .backgroundColor(Color.White)
        .justifyContent(FlexAlign.Center)
      }
    }
    .width('100%')
    .layoutWeight(1)
  }

  // 结果视图
  @Builder
  ResultView() {
    Scroll() {
      Column({ space: 20 }) {
        // 标题
        Row({ space: 12 }) {
          Stack() {
            Circle({ width: 48, height: 48 })
              .fill('linear-gradient(135deg, #667eea, #764ba2)')
              .opacity(0.15)
            
            Text('分析')
              .fontSize(14)
              .fontWeight(700)
              .fontColor('#667eea')
          }
          .width(48)
          .height(48)

          Text('决策分析结果')
            .fontSize(24)
            .fontWeight(700)
            .fontColor('#1A1A1A')
        }
        .width('100%')
        .padding({ left: 20, right: 20, top: 20 })

        // 选项卡片
        if (this.simulationResult && this.simulationResult.options) {
          ForEach(this.simulationResult.options, (option: SimulationOption) => {
            this.OptionCard(option)
          })
        }

        // AI推荐
        if (this.simulationResult && this.simulationResult.recommendation) {
          Column({ space: 12 }) {
            Row({ space: 12 }) {
              Stack() {
                Circle({ width: 40, height: 40 })
                  .fill('linear-gradient(135deg, #007AFF, #5856D6)')
                  .opacity(0.15)
                
                Text('AI')
                  .fontSize(14)
                  .fontWeight(700)
                  .fontColor('#007AFF')
              }
              .width(40)
              .height(40)

              Text('AI推荐')
                .fontSize(18)
                .fontWeight(700)
                .fontColor('#007AFF')
            }

            Text(this.simulationResult.recommendation)
              .fontSize(15)
              .fontColor('#333')
              .lineHeight(24)
          }
          .width('100%')
          .padding(20)
          .backgroundColor('rgba(0,122,255,0.05)')
          .borderRadius(16)
          .margin({ left: 20, right: 20 })
          .alignItems(HorizontalAlign.Start)
        }

        // 操作按钮
        Row({ space: 12 }) {
          Button('查看详情')
            .layoutWeight(1)
            .height(48)
            .fontSize(16)
            .fontWeight(600)
            .fontColor('#007AFF')
            .backgroundColor('rgba(0,122,255,0.1)')
            .borderRadius(12)

          Button('重新分析')
            .layoutWeight(1)
            .height(48)
            .fontSize(16)
            .fontWeight(600)
            .fontColor(Color.White)
            .backgroundColor('#007AFF')
            .borderRadius(12)
            .onClick(() => {
              this.resetFlow()
            })
        }
        .width('100%')
        .padding({ left: 20, right: 20, bottom: 20 })
      }
      .width('100%')
    }
    .layoutWeight(1)
    .scrollBar(BarState.Auto)
  }

  // 消息气泡
  @Builder
  MessageBubble(msg: Message) {
    Row() {
      if (msg.role === 'user') {
        Blank()
      }

      Column({ space: 4 }) {
        Text(msg.content)
          .fontSize(15)
          .fontColor(msg.role === 'user' ? Color.White : '#1A1A1A')
          .lineHeight(22)
          .padding(12)
          .backgroundColor(msg.role === 'user' ? '#007AFF' : Color.White)
          .borderRadius(12)
          .constraintSize({ maxWidth: '75%' })
      }
      .alignItems(msg.role === 'user' ? HorizontalAlign.End : HorizontalAlign.Start)

      if (msg.role === 'assistant' || msg.role === 'system') {
        Blank()
      }
    }
    .width('100%')
  }

  // 选项卡片
  @Builder
  OptionCard(option: SimulationOption) {
    Column({ space: 12 }) {
      Row() {
        Text(option.title)
          .fontSize(18)
          .fontWeight(700)
          .fontColor('#1A1A1A')
          .layoutWeight(1)

        Text(`${option.final_score.toFixed(1)}分`)
          .fontSize(20)
          .fontWeight(700)
          .fontColor('#007AFF')
      }
      .width('100%')

      // 风险等级
      Row({ space: 8 }) {
        Text('风险等级:')
          .fontSize(14)
          .fontColor('#666')
        
        Progress({ value: option.risk_level * 100, total: 100, type: ProgressType.Linear })
          .width(100)
          .height(6)
          .color(this.getRiskColor(option.risk_level))
        
        Text(this.getRiskText(option.risk_level))
          .fontSize(14)
          .fontColor(this.getRiskColor(option.risk_level))
          .fontWeight(600)
      }

      Text(option.description)
        .fontSize(14)
        .fontColor('#666')
        .lineHeight(20)
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(16)
    .margin({ left: 20, right: 20 })
    .alignItems(HorizontalAlign.Start)
  }

  // 辅助方法
  private getPhaseText(): string {
    switch (this.currentPhase) {
      case 'init':
        return '准备开始'
      case 'user_free_talk':
        return '自由表达'
      case 'ai_questioning':
        return 'AI提问'
      case 'ask_options':
        return '确认选项'
      case 'simulation':
        return '准备模拟'
      case 'result':
        return '完成'
      default:
        return ''
    }
  }

  private getInputPlaceholder(): string {
    if (this.currentPhase === 'user_free_talk') {
      return '详细描述你的情况...'
    } else if (this.currentPhase === 'ask_options') {
      return '输入你的选项，用逗号分隔...'
    } else {
      return '回答AI的问题...'
    }
  }

  private getRiskColor(risk: number): string {
    if (risk < 0.3) return '#34C759'
    if (risk < 0.6) return '#FF9500'
    return '#FF3B30'
  }

  private getRiskText(risk: number): string {
    if (risk < 0.3) return '低风险'
    if (risk < 0.6) return '中风险'
    return '高风险'
  }

  async pickImage() {
    try {
      const photoPicker = new picker.PhotoViewPicker()
      const result = await photoPicker.select({
        MIMEType: picker.PhotoViewMIMETypes.IMAGE_TYPE,
        maxSelectNumber: 1
      })
      if (result.photoUris && result.photoUris.length > 0) {
        this.selectedImageUri = result.photoUris[0]
        try {
          const context = getContext(this) as common.UIAbilityContext
          const sandboxPath = `${context.cacheDir}/upload_img.jpg`
          const srcFile = await fs.open(result.photoUris[0], fs.OpenMode.READ_ONLY)
          const destFile = await fs.open(sandboxPath, fs.OpenMode.READ_WRITE | fs.OpenMode.CREATE | fs.OpenMode.TRUNC)
          await fs.copyFile(srcFile.fd, destFile.fd)
          await fs.close(srcFile.fd)
          await fs.close(destFile.fd)
          const httpRequest = http.createHttp()
          const response = await httpRequest.request(
            `${ApiConfig.getApiUrl('/api/chat/upload-image')}?user_id=${this.userId}`,
            {
              method: http.RequestMethod.POST,
              header: { 'Content-Type': 'multipart/form-data' },
              multiFormDataList: [{
                name: 'file', contentType: 'image/jpeg',
                remoteFileName: 'image.jpg', filePath: sandboxPath
              }],
              connectTimeout: 30000, readTimeout: 30000
            }
          )
          httpRequest.destroy()
          if (response.responseCode === 200) {
            const res = JSON.parse(response.result as string) as Record<string, Object>
            const data = res.data as Record<string, string>
            this.userInput = data?.description ? `[图片: ${data.description}]` : '[图片已添加]'
          } else {
            this.userInput = '[图片已添加]'
          }
        } catch (uploadErr) {
          console.error('图片上传失败:', uploadErr)
          this.userInput = '[图片已添加]'
        }
      }
    } catch (err) {
      console.error('选择图片失败:', err)
    }
  }

  // ===== 通话功能 =====
  async startCall() {
    try {
      const atManager = abilityAccessCtrl.createAtManager()
      const context = getContext(this) as common.UIAbilityContext
      const result = await atManager.requestPermissionsFromUser(context, ['ohos.permission.MICROPHONE'])
      if (result.authResults[0] !== 0) {
        promptAction.showToast({ message: '需要麦克风权限才能通话' })
        return
      }
      this.isInCall = true
      this.callDuration = 0
      this.callDurationText = '00:00'
      // 开始录音（持续录制，每10秒发送一次）
      await this.startRecording()
      // 计时器
      this.callTimer = setInterval(() => {
        this.callDuration++
        const m = Math.floor(this.callDuration / 60).toString().padStart(2, '0')
        const s = (this.callDuration % 60).toString().padStart(2, '0')
        this.callDurationText = `${m}:${s}`
        // 每10秒自动发送一次语音
        if (this.callDuration % 10 === 0 && this.isRecording) {
          this.stopRecording()
          setTimeout(() => { if (this.isInCall) { this.startRecording() } }, 500)
        }
      }, 1000)
      promptAction.showToast({ message: '通话已开始，AI正在聆听' })
    } catch (err) {
      this.isInCall = false
      promptAction.showToast({ message: '通话启动失败' })
    }
  }

  endCall() {
    if (this.callTimer !== -1) { clearInterval(this.callTimer); this.callTimer = -1 }
    if (this.isRecording) { this.stopRecording() }
    this.isInCall = false
    this.callDuration = 0
    this.callDurationText = '00:00'
    promptAction.showToast({ message: '通话已结束' })
  }

  async startRecording() {
    try {
      const atManager = abilityAccessCtrl.createAtManager()
      const context = getContext(this) as common.UIAbilityContext
      const result = await atManager.requestPermissionsFromUser(context, ['ohos.permission.MICROPHONE'])
      if (result.authResults[0] !== 0) {
        this.userInput = '(需要麦克风权限)'
        return
      }
      this.recordFilePath = `${context.cacheDir}/voice_${Date.now()}.m4a`
      const file = await fs.open(this.recordFilePath, fs.OpenMode.READ_WRITE | fs.OpenMode.CREATE)
      const fd = file.fd
      this.audioRecorder = await media.createAVRecorder()
      const config: media.AVRecorderConfig = {
        audioSourceType: media.AudioSourceType.AUDIO_SOURCE_TYPE_MIC,
        profile: {
          audioBitrate: 48000,
          audioChannels: 1,
          audioCodec: media.CodecMimeType.AUDIO_AAC,
          audioSampleRate: 16000,
          fileFormat: media.ContainerFormatType.CFT_MPEG_4A,
        },
        url: `fd://${fd}`,
      }
      await this.audioRecorder.prepare(config)
      await this.audioRecorder.start()
      this.isRecording = true
      this.userInput = '录音中，再次点击停止...'
    } catch (err) {
      console.error('录音启动失败:', err)
      this.userInput = '(录音启动失败)'
      this.isRecording = false
    }
  }

  async stopRecording() {
    try {
      if (this.audioRecorder) {
        await this.audioRecorder.stop()
        await this.audioRecorder.release()
        this.audioRecorder = null
      }
      this.isRecording = false
      this.userInput = '识别中...'
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getApiUrl('/api/chat/speech-to-text')}`,
        {
          method: http.RequestMethod.POST,
          header: { 'Content-Type': 'multipart/form-data' },
          multiFormDataList: [{
            name: 'file', contentType: 'audio/mp4',
            remoteFileName: 'voice.m4a', filePath: this.recordFilePath
          }],
          connectTimeout: 30000, readTimeout: 30000
        }
      )
      httpRequest.destroy()
      if (response.responseCode === 200) {
        const res = JSON.parse(response.result as string) as Record<string, Object>
        const data = res.data as Record<string, string>
        const recognized = data?.text || ''
        if (recognized && recognized !== '(识别结果为空)') {
          this.userInput = recognized
          this.continueCollection(recognized)
        } else {
          this.userInput = '(识别结果为空)'
        }
      } else {
        this.userInput = '(语音识别失败)'
      }
    } catch (err) {
      console.error('停止录音失败:', err)
      this.userInput = '(录音处理失败)'
      this.isRecording = false
    }
  }

  private resetFlow() {
    this.currentPhase = 'init'
    this.sessionId = ''
    this.initialQuestion = ''
    this.messages = []
    this.userInput = ''
    this.collectedInfo = null
    this.simulationResult = null
    this.currentRound = 0
  }
}
