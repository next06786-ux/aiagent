/**
 * 决策副本输入页面 - HarmonyOS 6 流体设计
 * 用户输入决策问题，系统生成个性化副本
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { Theme } from '../common/Theme'
import { SimpleIcon } from '../components/IconRenderer'

interface DecisionInput {
  title: string
  description: string
  context: string
  urgency: 'low' | 'medium' | 'high'
  options: string[]
}

interface RouterParams {
  userId?: string
}

interface ApiResponse {
  code: number
  message: string
  data: DungeonData | null
}

interface DungeonData {
  dungeon_id: string
  user_id: string
  title: string
}

@Entry
@Component
struct DecisionDungeonInput {
  @State decisionTitle: string = ''
  @State decisionDescription: string = ''
  @State decisionContext: string = ''
  @State urgency: 'low' | 'medium' | 'high' = 'medium'
  @State options: string[] = ['', '', '']
  @State isLoading: boolean = false
  @State showContent: boolean = false
  @State currentStep: number = 0 // 0: 标题, 1: 描述, 2: 选项, 3: 确认
  @State focusedOptionIndex: number = -1
  @State errorMessage: string = ''
  @State debugInfo: string = '' // 调试信息
  private userId: string = 'default_user'
  private scroller: Scroller = new Scroller()

  aboutToAppear() {
    const params = router.getParams() as RouterParams
    if (params?.userId) {
      this.userId = params.userId
    }

    setTimeout(() => {
      this.showContent = true
    }, 100)
  }

  private async submitDecision() {
    this.debugInfo = '开始提交...'
    console.info('=== submitDecision 开始 ===')
    console.info('decisionTitle:', this.decisionTitle)
    console.info('decisionDescription:', this.decisionDescription)
    console.info('options:', JSON.stringify(this.options))
    
    // 验证输入
    if (!this.decisionTitle.trim()) {
      console.error('验证失败: 标题为空')
      this.debugInfo = '错误: 标题为空'
      this.showToast('请输入决策标题')
      return
    }

    if (!this.decisionDescription.trim()) {
      console.error('验证失败: 描述为空')
      this.debugInfo = '错误: 描述为空'
      this.showToast('请输入决策描述')
      return
    }

    const validOptions = this.options.filter(opt => opt.trim())
    console.info('validOptions:', JSON.stringify(validOptions))
    
    if (validOptions.length < 2) {
      console.error('验证失败: 选项少于2个')
      this.debugInfo = `错误: 只有${validOptions.length}个选项`
      this.showToast('至少需要2个选项')
      return
    }

    console.info('验证通过，开始提交...')
    this.debugInfo = '验证通过，正在连接服务器...'
    this.isLoading = true

    try {
      const httpRequest = http.createHttp()
      const requestData: Record<string, Object> = {
        'user_id': this.userId,
        'title': this.decisionTitle,
        'description': this.decisionDescription,
        'context': this.decisionContext,
        'urgency': this.urgency,
        'options': validOptions,
        'use_lora': true  // 启用LoRA，使用本地Qwen模型
      }

      console.info('Submitting decision:', JSON.stringify(requestData))
      this.debugInfo = '正在发送请求...'

      const response = await httpRequest.request(
        ApiConfig.getApiUrl('/api/decision/create-dungeon'),
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: JSON.stringify(requestData),
          connectTimeout: 30000,
          readTimeout: 30000
        }
      )

      httpRequest.destroy()

      console.info('Response code:', response.responseCode)
      console.info('Response result:', response.result)
      this.debugInfo = `收到响应: ${response.responseCode}`

      if (response.responseCode === 200) {
        this.debugInfo = '开始解析响应...'
        const resultStr = response.result as string
        console.info('Response string:', resultStr)
        
        const result = JSON.parse(resultStr) as ApiResponse

        console.info('Parsed result:', JSON.stringify(result))
        this.debugInfo = `解析结果: code=${result.code}`

        if (result.code === 200 && result.data) {
          console.info('创建成功，准备导航到2D副本地图')
          console.info('dungeon_id:', result.data.dungeon_id)
          this.debugInfo = `成功! ID: ${result.data.dungeon_id.substring(0, 20)}...`
          
          const dungeonId = result.data.dungeon_id
          
          // 延迟一下让用户看到成功信息
          setTimeout(() => {
            this.debugInfo = '正在跳转...'
            console.info('开始导航，dungeonId:', dungeonId)
            
            // 跳转到2D地图页面
            router.replaceUrl({
              url: 'pages/DecisionDungeon2DMap',
              params: {
                dungeonId: dungeonId,
                userId: this.userId
              }
            }).then(() => {
              console.info('✅ 导航成功')
            }).catch((err: Error) => {
              console.error('❌ 导航失败:', err.message)
              this.debugInfo = `导航失败: ${err.message}`
              this.showToast('页面跳转失败: ' + err.message)
              this.isLoading = false
            })
          }, 800)
        } else {
          console.error('创建失败:', result.message)
          this.debugInfo = `失败: ${result.message}`
          this.showToast('创建副本失败: ' + result.message)
        }
      } else {
        console.error('HTTP请求失败:', response.responseCode)
        this.debugInfo = `HTTP错误: ${response.responseCode}`
        this.showToast('请求失败，请检查网络')
      }
    } catch (error) {
      const err = error as Error
      console.error('Error:', err.message)
      console.error('Error stack:', err.stack)
      this.debugInfo = `异常: ${err.message}`
      this.showToast('出错: ' + err.message)
    }

    this.isLoading = false
    console.info('=== submitDecision 结束 ===')
  }

  private showToast(message: string) {
    console.info('Toast:', message)
    console.error('⚠️ 用户提示:', message)
    // 显示错误信息
    this.errorMessage = message
    // 3秒后清除错误信息
    setTimeout(() => {
      this.errorMessage = ''
    }, 3000)
  }

  private addOption() {
    if (this.options.length < 5) {
      // 创建新数组以触发状态更新
      this.options = [...this.options, '']
    }
  }

  private removeOption(index: number) {
    if (this.options.length > 2) {
      // 创建新数组以触发状态更新
      const newOptions = [...this.options]
      newOptions.splice(index, 1)
      this.options = newOptions
    }
  }

  build() {
    Stack() {
      // 背景
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor(Theme.Color.BackgroundPrimary)

      // 主内容
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

          Text('创建决策副本')
            .fontSize(20)
            .fontWeight(700)
            .fontColor(Theme.Color.TextPrimary)
            .layoutWeight(1)
            .margin({ left: 12 })

          // 进度指示
          Text(`${this.currentStep + 1}/4`)
            .fontSize(14)
            .fontColor(Theme.Color.TextSecondary)
            .padding({ left: 12, right: 12, top: 6, bottom: 6 })
            .backgroundColor(Theme.Color.GlassMedium)
            .borderRadius(Theme.Radius.round)
        }
        .width('100%')
        .height(56)
        .padding({ left: 16, right: 16 })
        .backgroundColor('rgba(255, 255, 255, 0.6)')
        .backdropBlur(20)

        // 进度条
        Row()
          .width(`${(this.currentStep + 1) * 25}%`)
          .height(3)
          .backgroundColor(Theme.Color.Primary)
          .animation({
            duration: 500,
            curve: Curve.Smooth
          })

        // 错误提示
        if (this.errorMessage) {
          Row() {
            Text('⚠️ ' + this.errorMessage)
              .fontSize(14)
              .fontColor(Color.White)
              .padding({ left: 16, right: 16, top: 12, bottom: 12 })
          }
          .width('100%')
          .backgroundColor('#FF3B30')
          .justifyContent(FlexAlign.Center)
          .transition({ type: TransitionType.Insert, opacity: 0, translate: { y: -20 } })
          .transition({ type: TransitionType.Delete, opacity: 0, translate: { y: -20 } })
        }

        if (this.isLoading) {
          Column() {
            LoadingProgress()
              .width(40)
              .height(40)
              .color(Theme.Color.Primary)
            Text('正在创建副本...')
              .fontSize(14)
              .fontColor(Theme.Color.TextSecondary)
              .margin({ top: 12 })
            
            // 调试信息
            if (this.debugInfo) {
              Text(this.debugInfo)
                .fontSize(12)
                .fontColor('#007AFF')
                .margin({ top: 8 })
                .padding(8)
                .backgroundColor('rgba(0,122,255,0.1)')
                .borderRadius(8)
            }
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        } else {
          // 内容区域
          Scroll(this.scroller) {
            Column({ space: 24 }) {
              // 第一步：标题
              if (this.currentStep === 0) {
                this.StepTitle()
              }

              // 第二步：描述
              if (this.currentStep === 1) {
                this.StepDescription()
              }

              // 第三步：选项
              if (this.currentStep === 2) {
                this.StepOptions()
              }

              // 第四步：确认
              if (this.currentStep === 3) {
                this.StepConfirm()
              }
            }
            .width('100%')
            .padding({ left: 20, right: 20, top: 24, bottom: 120 })
          }
          .layoutWeight(1)
          .scrollBar(BarState.Off)
          .edgeEffect(EdgeEffect.Spring)
        }

        // 底部按钮
        Row({ space: 12 }) {
          if (this.currentStep > 0) {
            Button('上一步')
              .layoutWeight(1)
              .height(48)
              .fontSize(16)
              .fontWeight(600)
              .fontColor(Theme.Color.Primary)
              .backgroundColor(Theme.Color.GlassMedium)
              .borderRadius(Theme.Radius.l)
              .onClick(() => {
                this.currentStep--
              })
          }

          Button(this.currentStep === 3 ? '创建副本' : '下一步')
            .layoutWeight(1)
            .height(48)
            .fontSize(16)
            .fontWeight(600)
            .fontColor(Color.White)
            .backgroundColor(Theme.Color.Primary)
            .borderRadius(Theme.Radius.l)
            .onClick(() => {
              if (this.currentStep === 3) {
                this.submitDecision()
              } else {
                this.currentStep++
              }
            })
        }
        .width('100%')
        .padding({ left: 20, right: 20, bottom: 20 })
      }
      .width('100%')
      .height('100%')
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  StepTitle() {
    Column({ space: 16 }) {
      // 标题
      Column({ space: 8 }) {
        Text('🎯 你面临什么决策？')
          .fontSize(24)
          .fontWeight(700)
          .fontColor(Theme.Color.TextPrimary)

        Text('简洁地描述你的决策问题')
          .fontSize(14)
          .fontColor(Theme.Color.TextSecondary)
      }
      .width('100%')
      .alignItems(HorizontalAlign.Start)

      // 输入框
      Column() {
        TextInput({ placeholder: '例如：毕业后应该选择什么？' })
          .width('100%')
          .height(120)
          .padding(16)
          .fontSize(16)
          .fontColor(Theme.Color.TextPrimary)
          .placeholderColor(Theme.Color.TextTertiary)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .onChange((value: string) => {
            this.decisionTitle = value
          })
      }
      .width('100%')

      // 提示
      Row({ space: 8 }) {
        Text('💡')
          .fontSize(16)
        Text('好的标题应该清晰、具体，避免过于宽泛')
          .fontSize(13)
          .fontColor(Theme.Color.TextSecondary)
          .layoutWeight(1)
      }
      .width('100%')
      .padding(12)
      .backgroundColor('rgba(0, 122, 255, 0.05)')
      .borderRadius(Theme.Radius.m)
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 500,
      curve: Curve.Smooth
    })
  }

  @Builder
  StepDescription() {
    Column({ space: 16 }) {
      Column({ space: 8 }) {
        Text('📝 详细背景信息')
          .fontSize(24)
          .fontWeight(700)
          .fontColor(Theme.Color.TextPrimary)

        Text('提供更多上下文，帮助AI更好地理解')
          .fontSize(14)
          .fontColor(Theme.Color.TextSecondary)
      }
      .width('100%')
      .alignItems(HorizontalAlign.Start)

      // 描述输入
      Column() {
        TextInput({ placeholder: '描述你的情况、背景和考虑因素...' })
          .width('100%')
          .height(140)
          .padding(16)
          .fontSize(16)
          .fontColor(Theme.Color.TextPrimary)
          .placeholderColor(Theme.Color.TextTertiary)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .onChange((value: string) => {
            this.decisionDescription = value
          })
      }
      .width('100%')

      // 上下文输入
      Column() {
        TextInput({ placeholder: '其他相关信息（可选）' })
          .width('100%')
          .height(100)
          .padding(16)
          .fontSize(16)
          .fontColor(Theme.Color.TextPrimary)
          .placeholderColor(Theme.Color.TextTertiary)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .onChange((value: string) => {
            this.decisionContext = value
          })
      }
      .width('100%')

      // 紧急程度
      Column({ space: 12 }) {
        Text('⏰ 紧急程度')
          .fontSize(14)
          .fontWeight(600)
          .fontColor(Theme.Color.TextPrimary)

        Row({ space: 12 }) {
          ForEach(['low', 'medium', 'high'], (level: string) => {
            Button(level === 'low' ? '不急' : level === 'medium' ? '中等' : '紧急')
              .layoutWeight(1)
              .height(40)
              .fontSize(14)
              .fontWeight(600)
              .fontColor(this.urgency === level ? Color.White : Theme.Color.Primary)
              .backgroundColor(this.urgency === level ? Theme.Color.Primary : Theme.Color.GlassMedium)
              .borderRadius(Theme.Radius.m)
              .onClick(() => {
                this.urgency = level as 'low' | 'medium' | 'high'
              })
          })
        }
        .width('100%')
      }
      .width('100%')
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 500,
      curve: Curve.Smooth
    })
  }

  @Builder
  StepOptions() {
    Column({ space: 16 }) {
      Column({ space: 8 }) {
        Text('🎮 添加决策选项')
          .fontSize(24)
          .fontWeight(700)
          .fontColor(Theme.Color.TextPrimary)

        Text('至少2个，最多5个选项')
          .fontSize(14)
          .fontColor(Theme.Color.TextSecondary)
      }
      .width('100%')
      .alignItems(HorizontalAlign.Start)

      // 选项列表
      ForEach(this.options, (option: string, index: number) => {
        Row({ space: 12 }) {
          // 编号
          Stack() {
            Circle({ width: 36, height: 36 })
              .fill(Theme.Color.Primary)
              .opacity(0.15)

            Text(`${index + 1}`)
              .fontSize(16)
              .fontWeight(700)
              .fontColor(Theme.Color.Primary)
          }
          .width(36)
          .height(36)

          // 输入框
          TextInput({ text: this.options[index], placeholder: `选项 ${index + 1}` })
            .layoutWeight(1)
            .height(44)
            .padding({ left: 12, right: 12 })
            .fontSize(16)
            .fontColor(Theme.Color.TextPrimary)
            .placeholderColor(Theme.Color.TextTertiary)
            .backgroundColor(Theme.Color.BackgroundSecondary)
            .borderRadius(Theme.Radius.m)
            .border({ width: 1, color: Theme.Color.BorderLight })
            .onChange((value: string) => {
              // 创建新数组以触发状态更新
              const newOptions = [...this.options]
              newOptions[index] = value
              this.options = newOptions
            })

          // 删除按钮
          if (this.options.length > 2) {
            Button({ type: ButtonType.Circle }) {
              Text('×')
                .fontSize(24)
                .fontColor('#FF3B30')
            }
            .width(40)
            .height(40)
            .backgroundColor('rgba(255, 59, 48, 0.1)')
            .onClick(() => {
              this.removeOption(index)
            })
          }
        }
        .width('100%')
      })

      // 添加选项按钮
      if (this.options.length < 5) {
        Button('+ 添加选项')
          .width('100%')
          .height(44)
          .fontSize(16)
          .fontWeight(600)
          .fontColor(Theme.Color.Primary)
          .backgroundColor(Theme.Color.GlassMedium)
          .borderRadius(Theme.Radius.m)
          .border({ width: 1, color: Theme.Color.Primary })
          .onClick(() => {
            this.addOption()
          })
      }
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 500,
      curve: Curve.Smooth
    })
  }

  @Builder
  StepConfirm() {
    Column({ space: 20 }) {
      Column({ space: 8 }) {
        Text('✨ 确认信息')
          .fontSize(24)
          .fontWeight(700)
          .fontColor(Theme.Color.TextPrimary)

        Text('检查信息无误后创建副本')
          .fontSize(14)
          .fontColor(Theme.Color.TextSecondary)
      }
      .width('100%')
      .alignItems(HorizontalAlign.Start)

      // 信息卡片
      Column({ space: 16 }) {
        this.ConfirmItem('决策问题', this.decisionTitle)
        this.ConfirmItem('背景描述', this.decisionDescription)
        this.ConfirmItem('紧急程度', this.urgency === 'low' ? '不急' : this.urgency === 'medium' ? '中等' : '紧急')

        Column({ space: 8 }) {
          Text('选择选项')
            .fontSize(14)
            .fontWeight(600)
            .fontColor(Theme.Color.TextSecondary)

          ForEach(this.options.filter(opt => opt.trim()), (option: string) => {
            Row({ space: 8 }) {
              Text('✓')
                .fontSize(16)
                .fontColor(Theme.Color.Accent)

              Text(option)
                .fontSize(14)
                .fontColor(Theme.Color.TextPrimary)
                .layoutWeight(1)
            }
            .width('100%')
            .padding(12)
            .backgroundColor(Theme.Color.BackgroundSecondary)
            .borderRadius(Theme.Radius.m)
          })
        }
        .width('100%')
      }
      .width('100%')
      .padding(16)
      .backgroundColor(Theme.Color.GlassHeavy)
      .backdropBlur(Theme.Blur.Heavy)
      .borderRadius(Theme.Radius.l)
      .border({ width: 1, color: Theme.Color.BorderLight })

      // 提示
      Row({ space: 8 }) {
        Text('🚀')
          .fontSize(16)
        Text('系统将基于你的个性化模型生成3-4个副本，每个副本代表不同的选择路线')
          .fontSize(13)
          .fontColor(Theme.Color.TextSecondary)
          .layoutWeight(1)
      }
      .width('100%')
      .padding(12)
      .backgroundColor('rgba(0, 122, 255, 0.05)')
      .borderRadius(Theme.Radius.m)
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 500,
      curve: Curve.Smooth
    })
  }

  @Builder
  ConfirmItem(label: string, value: string) {
    Column({ space: 4 }) {
      Text(label)
        .fontSize(12)
        .fontColor(Theme.Color.TextSecondary)

      Text(value)
        .fontSize(14)
        .fontColor(Theme.Color.TextPrimary)
        .fontWeight(600)
        .maxLines(2)
        .textOverflow({ overflow: TextOverflow.Ellipsis })
    }
    .width('100%')
    .alignItems(HorizontalAlign.Start)
  }
}




