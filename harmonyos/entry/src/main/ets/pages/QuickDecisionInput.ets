/**
 * 快速决策输入 - 语音+AI对话式
 * 让用户更轻松地创建决策副本
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import promptAction from '@ohos.promptAction'
import { ApiConfig } from '../config/ApiConfig'
import { getUserId } from '../service/UserSessionManager'
import { Theme } from '../common/Theme'

interface QuickTemplate {
  id: string
  icon: string
  title: string
  description: string
  prompt: string
}

@Entry
@Component
struct QuickDecisionInput {
  @State userInput: string = ''
  @State isListening: boolean = false
  @State isProcessing: boolean = false
  @State aiSuggestion: string = ''
  @State showTemplates: boolean = true
  @State selectedTemplate: QuickTemplate | null = null
  private userId: string = ''

  async aboutToAppear() {
    // 获取真实用户ID
    this.userId = await getUserId()
    console.info('[QuickDecisionInput] 获取到用户ID:', this.userId)
    
    // 如果是 default_user，说明未登录，跳转到登录页
    if (this.userId === 'default_user' || this.userId === '') {
      console.warn('[QuickDecisionInput] 用户未登录，跳转到登录页')
      promptAction.showToast({ message: '请先登录使用决策功能' })
      router.replaceUrl({ url: 'pages/Login' })
      return
    }
    
    // 处理路由参数
    const params = router.getParams() as Record<string, string>
    if (params?.userId) {
      this.userId = params.userId
    }
  }
  
  private templates: QuickTemplate[] = [
    {
      id: 'career',
      icon: '💼',
      title: '职业选择',
      description: '工作、跳槽、转行',
      prompt: '我在考虑职业发展的问题'
    },
    {
      id: 'study',
      icon: '📚',
      title: '学习深造',
      description: '考研、留学、培训',
      prompt: '我在考虑是否继续学习深造'
    },
    {
      id: 'life',
      icon: '🏠',
      title: '生活规划',
      description: '买房、结婚、搬家',
      prompt: '我在考虑生活方面的重大决定'
    },
    {
      id: 'invest',
      icon: '💰',
      title: '投资理财',
      description: '创业、投资、理财',
      prompt: '我在考虑投资或理财的问题'
    }
  ]

  // 语音输入（模拟）
  private startVoiceInput() {
    this.isListening = true
    // TODO: 集成HarmonyOS语音识别API
    setTimeout(() => {
      this.isListening = false
      this.userInput = '我不知道毕业后应该考研还是工作'
      // 直接跳转到智能决策流程
      router.replaceUrl({
        url: 'pages/EnhancedDecisionFlow',
        params: {
          userId: this.userId,
          initialQuestion: this.userInput
        }
      })
    }, 2000)
  }

  // AI处理用户输入 - 直接跳转到智能决策流程
  private async processUserInput() {
    if (!this.userInput.trim()) return
    
    // 直接跳转到智能决策流程页面
    router.replaceUrl({
      url: 'pages/EnhancedDecisionFlow',
      params: {
        userId: this.userId,
        initialQuestion: this.userInput
      }
    })
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
      }
      .width('100%')
      .height(56)
      .padding({ left: 16, right: 16 })
      .backgroundColor('rgba(255,255,255,0.95)')

      Scroll() {
        Column({ space: 24 }) {
          // 标题
          Column({ space: 20 }) {
            // 对话图标
            Stack() {
              Circle({ width: 72, height: 72 })
                .fill('linear-gradient(135deg, #667eea, #764ba2)')
                .opacity(0.15)
              
              Circle({ width: 56, height: 56 })
                .fill('linear-gradient(135deg, #667eea, #764ba2)')
                .opacity(0.25)
              
              Text('说')
                .fontSize(24)
                .fontWeight(700)
                .fontColor('#667eea')
            }
            .width(72)
            .height(72)

            Column({ space: 8 }) {
              Text('说出你的困惑')
                .fontSize(28)
                .fontWeight(700)
                .fontColor('#1A1A1A')

              Text('用语音或文字描述，AI会帮你分析')
                .fontSize(14)
                .fontColor('#666')
            }
          }
          .width('100%')
          .padding({ left: 20, right: 20, top: 20 })
          .alignItems(HorizontalAlign.Start)

          // 语音输入按钮
          Column({ space: 16 }) {
            Button() {
              Column({ space: 12 }) {
                Stack() {
                  Circle({ width: 80, height: 80 })
                    .fill(this.isListening ? '#FF3B30' : '#007AFF')
                    .opacity(0.15)
                  
                  Circle({ width: 64, height: 64 })
                    .fill(this.isListening ? '#FF3B30' : '#007AFF')
                    .opacity(0.25)
                  
                  Text('🎙')
                    .fontSize(36)
                }
                .width(80)
                .height(80)
                .animation({
                  duration: 1000,
                  iterations: -1
                })

                Text(this.isListening ? '正在聆听...' : '点击说话')
                  .fontSize(16)
                  .fontWeight(600)
                  .fontColor(this.isListening ? '#FF3B30' : '#007AFF')
              }
            }
            .width(160)
            .height(160)
            .backgroundColor(this.isListening ? 'rgba(255,59,48,0.1)' : 'rgba(0,122,255,0.1)')
            .borderRadius(80)
            .onClick(() => {
              if (!this.isListening) {
                this.startVoiceInput()
              }
            })

            Text('或者')
              .fontSize(14)
              .fontColor('#999')
          }
          .width('100%')
          .padding(20)
          .justifyContent(FlexAlign.Center)

          // 文字输入
          Column({ space: 12 }) {
            TextArea({ placeholder: '输入你的困惑，比如：\n"我不知道毕业后该做什么"\n"要不要换工作"' })
              .width('100%')
              .height(120)
              .padding(16)
              .fontSize(16)
              .fontColor('#1A1A1A')
              .backgroundColor('#F5F7FA')
              .borderRadius(16)
              .onChange((value: string) => {
                this.userInput = value
              })

            Button('开始智能分析')
              .width('100%')
              .height(48)
              .fontSize(16)
              .fontWeight(600)
              .fontColor(Color.White)
              .backgroundColor('#007AFF')
              .borderRadius(12)
              .enabled(!this.isProcessing && this.userInput.trim().length > 0)
              .onClick(() => {
                this.processUserInput()
              })
          }
          .width('100%')
          .padding({ left: 20, right: 20 })

          // AI建议
          if (this.aiSuggestion) {
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

                Text('AI分析')
                  .fontSize(16)
                  .fontWeight(700)
                  .fontColor('#007AFF')
              }

              Text(this.aiSuggestion)
                .fontSize(14)
                .fontColor('#333')
                .lineHeight(22)
            }
            .width('100%')
            .padding(16)
            .backgroundColor('rgba(0,122,255,0.05)')
            .borderRadius(16)
            .margin({ left: 20, right: 20 })
            .alignItems(HorizontalAlign.Start)
          }

          // 快速模板
          if (this.showTemplates) {
            Column({ space: 16 }) {
              Row({ space: 12 }) {
                Stack() {
                  Circle({ width: 32, height: 32 })
                    .fill('linear-gradient(135deg, #667eea, #764ba2)')
                    .opacity(0.15)
                  
                  Text('📋')
                    .fontSize(16)
                }
                .width(32)
                .height(32)

                Text('或选择常见场景')
                  .fontSize(18)
                  .fontWeight(700)
                  .fontColor('#1A1A1A')
              }

              ForEach(this.templates, (template: QuickTemplate) => {
                this.TemplateCard(template)
              })
            }
            .width('100%')
            .padding({ left: 20, right: 20 })
            .alignItems(HorizontalAlign.Start)
          }
        }
        .width('100%')
        .padding({ bottom: 40 })
      }
      .layoutWeight(1)
      .scrollBar(BarState.Off)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#FAFBFC')
  }

  @Builder
  TemplateCard(template: QuickTemplate) {
    Row({ space: 16 }) {
      Stack() {
        Circle({ width: 48, height: 48 })
          .fill('linear-gradient(135deg, #667eea, #764ba2)')
          .opacity(0.15)
        
        Text(template.icon)
          .fontSize(24)
      }
      .width(48)
      .height(48)

      Column({ space: 4 }) {
        Text(template.title)
          .fontSize(16)
          .fontWeight(700)
          .fontColor('#1A1A1A')

        Text(template.description)
          .fontSize(13)
          .fontColor('#666')
      }
      .alignItems(HorizontalAlign.Start)
      .layoutWeight(1)

      Text('→')
        .fontSize(24)
        .fontColor('#007AFF')
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(16)
    .shadow({ radius: 4, color: 'rgba(0,0,0,0.05)', offsetY: 2 })
    .onClick(() => {
      this.userInput = template.prompt
      // 直接跳转到智能决策流程
      router.replaceUrl({
        url: 'pages/EnhancedDecisionFlow',
        params: {
          userId: this.userId,
          initialQuestion: template.prompt
        }
      })
    })
  }
}
