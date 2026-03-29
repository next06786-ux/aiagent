/**
 * 平行人生 · 决策游戏
 * 通过情景模拟收集用户决策偏好，用于个性化 LoRA 训练
 */
import { Theme } from '../common/Theme'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { getAuthService } from '../service/AuthService'

// ── 数据类型 ──────────────────────────────────────────────────────────────

interface GameOption {
  id: string
  label: string
  detail: string
  color: string
  icon: string
}

interface OutcomeCard {
  month: number
  text: string
}

interface FollowupQuestion {
  id: string
  text: string
  type: string
  left_label: string
  right_label: string
}

interface Scenario {
  id: string
  type: string
  title: string
  theme_color: string
  bg_gradient: string[]
  scene_text: string
  options: GameOption[]
  followups: FollowupQuestion[]
}

interface OutcomeData {
  chosen: string
  outcomes: Record<string, OutcomeCard[]>
}

interface GamePayload {
  user_id: string
  scenario_id: string
  scenario_type: string
  initial_choice: string
  choice_time_ms: number
  regret_triggered: boolean
  final_choice: string
  followup_answers: Record<string, number>
}

interface DimBar {
  key: string
  val: number
}

@Entry
@Component
struct ParallelLifeGame {
  @State phase: string = 'loading'
  @State scenarios: Scenario[] = []
  @State currentIndex: number = 0
  @State chosenId: string = ''
  @State finalChoiceId: string = ''
  @State outcomeData: OutcomeData | null = null
  @State followupAnswers: Record<string, number> = {}
  @State currentFollowupIndex: number = 0
  @State sliderValue: number = 0.5
  @State cardAOpacity: number = 0
  @State cardBOpacity: number = 0
  @State cardATranslateY: number = 40
  @State cardBTranslateY: number = 40
  @State sceneTextOpacity: number = 0
  @State outcomeRevealA: boolean = false
  @State outcomeRevealB: boolean = false
  @State resultOpacity: number = 0
  @State dimBars: DimBar[] = []

  private choiceStartTime: number = 0
  private choiceTimeMs: number = 0
  private regretTriggered: boolean = false
  private authService = getAuthService()

  aboutToAppear() {
    this.loadScenarios()
  }

  async loadScenarios() {
    try {
      const req = http.createHttp()
      const res = await req.request(`${ApiConfig.getBaseUrl()}/api/game/parallel-life/scenarios`,
        { method: http.RequestMethod.GET })
      req.destroy()
      if (res.responseCode === 200) {
        const body = JSON.parse(res.result as string) as Record<string, Object>
        this.scenarios = body['data'] as Scenario[]
        this.phase = 'scene'
        this.animateSceneIn()
      }
    } catch (e) {
      console.error('加载场景失败:', e)
    }
  }

  async loadOutcomes() {
    const s = this.safeScenario()
    if (!s) return
    try {
      const req = http.createHttp()
      const res = await req.request(
        `${ApiConfig.getBaseUrl()}/api/game/parallel-life/scenario/${s.id}/outcomes?chosen=${this.chosenId}`,
        { method: http.RequestMethod.GET })
      req.destroy()
      if (res.responseCode === 200) {
        const body = JSON.parse(res.result as string) as Record<string, Object>
        this.outcomeData = body['data'] as OutcomeData
        this.phase = 'outcome'
        this.animateOutcomeIn()
      }
    } catch (e) {
      console.error('加载结局失败:', e)
    }
  }

  async submitResult() {
    const s = this.safeScenario()
    if (!s) return
    try {
      const userId = this.authService.getCurrentUserId()
      const payload: GamePayload = {
        user_id: userId,
        scenario_id: s.id,
        scenario_type: s.type,
        initial_choice: this.chosenId,
        choice_time_ms: this.choiceTimeMs,
        regret_triggered: this.regretTriggered,
        final_choice: this.finalChoiceId || this.chosenId,
        followup_answers: this.followupAnswers
      }
      const req = http.createHttp()
      await req.request(`${ApiConfig.getBaseUrl()}/api/game/parallel-life/result`, {
        method: http.RequestMethod.POST,
        header: { 'Content-Type': 'application/json' },
        extraData: JSON.stringify(payload)
      })
      req.destroy()
    } catch (e) {
      console.error('提交结果失败:', e)
    }
  }

  safeScenario(): Scenario | null {
    return this.scenarios.length > this.currentIndex ? this.scenarios[this.currentIndex] : null
  }

  safeChosenOpt(): GameOption | null {
    const s = this.safeScenario()
    if (!s) return null
    return s.options.find(o => o.id === this.chosenId) ?? null
  }

  safeOtherOpt(): GameOption | null {
    const s = this.safeScenario()
    if (!s) return null
    return s.options.find(o => o.id !== this.chosenId) ?? null
  }

  safeChosenOutcomes(): OutcomeCard[] {
    if (!this.outcomeData) return []
    return this.outcomeData.outcomes[this.chosenId] ?? []
  }

  safeOtherOutcomes(): OutcomeCard[] {
    if (!this.outcomeData) return []
    const s = this.safeScenario()
    if (!s) return []
    const otherId = s.options.find(o => o.id !== this.chosenId)?.id ?? ''
    return this.outcomeData.outcomes[otherId] ?? []
  }

  safeFollowup(): FollowupQuestion | null {
    const s = this.safeScenario()
    if (!s || this.currentFollowupIndex >= s.followups.length) return null
    return s.followups[this.currentFollowupIndex]
  }

  onChoose(optionId: string) {
    this.choiceTimeMs = Date.now() - this.choiceStartTime
    this.chosenId = optionId
    this.phase = 'choosing'
    this.loadOutcomes()
  }

  onRegret() {
    this.regretTriggered = true
    this.phase = 'scene'
    this.chosenId = ''
    this.animateSceneIn()
  }

  onConfirmChoice() {
    this.finalChoiceId = this.chosenId
    this.currentFollowupIndex = 0
    this.sliderValue = 0.5
    this.phase = 'followup'
  }

  onFollowupNext() {
    const s = this.safeScenario()
    if (!s) return
    const q = this.safeFollowup()
    if (!q) return
    this.followupAnswers[q.id] = this.sliderValue
    this.sliderValue = 0.5
    if (this.currentFollowupIndex < s.followups.length - 1) {
      this.currentFollowupIndex++
    } else {
      this.submitResult()
      // 构建维度条数据（避免在 @Builder 里用 Object.keys）
      const bars: DimBar[] = []
      const keys = Object.keys(this.followupAnswers)
      for (let i = 0; i < keys.length; i++) {
        bars.push({ key: keys[i], val: (this.followupAnswers[keys[i]] as number) * 100 })
      }
      this.dimBars = bars
      this.phase = 'result'
      this.animateResultIn()
    }
  }

  onNextScenario() {
    if (this.currentIndex < this.scenarios.length - 1) {
      this.currentIndex++
      this.chosenId = ''
      this.finalChoiceId = ''
      this.outcomeData = null
      this.followupAnswers = {}
      this.regretTriggered = false
      this.phase = 'scene'
      this.animateSceneIn()
    } else {
      this.navigateBack()
    }
  }

  private navigateBack() {
    try { this.getUIContext().getRouter().back() } catch (e) {}
  }

  animateSceneIn() {
    this.sceneTextOpacity = 0
    this.cardAOpacity = 0; this.cardBOpacity = 0
    this.cardATranslateY = 40; this.cardBTranslateY = 40
    this.choiceStartTime = Date.now()
    setTimeout(() => {
      animateTo({ duration: 600, curve: Curve.Smooth }, () => { this.sceneTextOpacity = 1 })
    }, 100)
    setTimeout(() => {
      animateTo({ duration: 500, curve: Curve.Smooth }, () => { this.cardAOpacity = 1; this.cardATranslateY = 0 })
    }, 500)
    setTimeout(() => {
      animateTo({ duration: 500, curve: Curve.Smooth }, () => { this.cardBOpacity = 1; this.cardBTranslateY = 0 })
    }, 700)
  }

  animateOutcomeIn() {
    this.outcomeRevealA = false; this.outcomeRevealB = false
    setTimeout(() => { this.outcomeRevealA = true }, 300)
    setTimeout(() => { this.outcomeRevealB = true }, 600)
  }

  animateResultIn() {
    this.resultOpacity = 0
    setTimeout(() => {
      animateTo({ duration: 700, curve: Curve.Smooth }, () => { this.resultOpacity = 1 })
    }, 200)
  }

  getRiskLabel(): string {
    const vals = Object.values(this.followupAnswers) as number[]
    if (vals.length === 0) return '均衡型决策者'
    const avg = vals.reduce((a, b) => a + b, 0) / vals.length
    if (avg < 0.35) return '果断型决策者'
    if (avg > 0.65) return '谨慎型决策者'
    return '均衡型决策者'
  }

  getRiskDesc(): string {
    const label = this.getRiskLabel()
    if (label === '果断型决策者') return '你倾向于快速行动，接受不确定性，愿意用短期风险换取长期机会。'
    if (label === '谨慎型决策者') return '你重视稳定性，倾向于在充分评估后再行动，对损失比较敏感。'
    return '你在风险与稳定之间保持平衡，能根据具体情境灵活调整决策策略。'
  }

  build() {
    Stack() {
      Column()
        .width('100%').height('100%')
        .backgroundColor(this.safeScenario()?.bg_gradient[0] ?? '#1a1a2e')

      Row() {
        Text('←')
          .fontSize(24).fontColor('#FFFFFF').opacity(0.8)
          .onClick(() => this.navigateBack())
        Text('平行人生')
          .fontSize(17).fontWeight(600).fontColor('#FFFFFF')
          .margin({ left: 12 })
        Blank()
        if (this.scenarios.length > 0) {
          Text(`${this.currentIndex + 1} / ${this.scenarios.length}`)
            .fontSize(13).fontColor('rgba(255,255,255,0.5)')
        }
      }
      .width('100%').height(56)
      .padding({ left: 16, right: 20 })
      .position({ x: 0, y: 0 }).zIndex(10)

      if (this.phase === 'loading') {
        this.buildLoading()
      } else if (this.phase === 'scene' || this.phase === 'choosing') {
        this.buildScene()
      } else if (this.phase === 'outcome') {
        this.buildOutcome()
      } else if (this.phase === 'followup') {
        this.buildFollowup()
      } else if (this.phase === 'result') {
        this.buildResult()
      }
    }
    .width('100%').height('100%')
  }

  @Builder buildLoading() {
    Column({ space: 16 }) {
      LoadingProgress().width(48).height(48).color('#FFFFFF')
      Text('加载场景中...').fontSize(14).fontColor('rgba(255,255,255,0.6)')
    }
    .width('100%').height('100%')
    .justifyContent(FlexAlign.Center).alignItems(HorizontalAlign.Center)
  }

  @Builder buildScene() {
    Scroll() {
      Column({ space: 0 }) {
        Column({ space: 8 }) {
          Text(this.safeScenario()?.title ?? '')
            .fontSize(13).fontColor(this.safeScenario()?.theme_color ?? '#FFFFFF')
            .fontWeight(600).letterSpacing(2)
            .padding({ left: 12, right: 12, top: 5, bottom: 5 })
            .backgroundColor('rgba(255,255,255,0.08)')
            .borderRadius(Theme.Radius.round)
          Text(this.safeScenario()?.scene_text ?? '')
            .fontSize(20).fontWeight(700)
            .fontColor('#FFFFFF').lineHeight(32)
            .textAlign(TextAlign.Center)
            .opacity(this.sceneTextOpacity)
            .animation({ duration: 600, curve: Curve.Smooth })
        }
        .width('100%')
        .padding({ top: 80, left: 24, right: 24, bottom: 32 })
        .alignItems(HorizontalAlign.Center)

        Column({ space: 14 }) {
          ForEach(this.safeScenario()?.options ?? [], (opt: GameOption, idx: number) => {
            Column({ space: 10 }) {
              Row({ space: 12 }) {
                Column()
                  .width(4).height(48)
                  .backgroundColor(opt.color)
                  .borderRadius(2)
                Column({ space: 4 }) {
                  Text(opt.label).fontSize(17).fontWeight(700).fontColor('#FFFFFF')
                  Text(opt.detail).fontSize(13).fontColor('rgba(255,255,255,0.6)').lineHeight(20)
                }
                .layoutWeight(1).alignItems(HorizontalAlign.Start)
                Text('→').fontSize(20).fontColor(opt.color)
              }
              .width('100%').alignItems(VerticalAlign.Center)
            }
            .width('100%').padding(20)
            .backgroundColor('rgba(255,255,255,0.07)')
            .borderRadius(Theme.Radius.l)
            .border({ width: 1, color: 'rgba(255,255,255,0.1)' })
            .opacity(idx === 0 ? this.cardAOpacity : this.cardBOpacity)
            .translate({ y: idx === 0 ? this.cardATranslateY : this.cardBTranslateY })
            .animation({ duration: 500, curve: Curve.Smooth })
            .onClick(() => this.onChoose(opt.id))
            .stateStyles({
              pressed: { .scale({ x: 0.97, y: 0.97 }).backgroundColor('rgba(255,255,255,0.12)') },
              normal:  { .scale({ x: 1, y: 1 }).backgroundColor('rgba(255,255,255,0.07)') }
            })
          })
        }
        .padding({ left: 20, right: 20, bottom: 40 })
      }
    }
    .scrollBar(BarState.Off).width('100%').height('100%')
  }

  @Builder buildOutcome() {
    Scroll() {
      Column({ space: 20 }) {
        Text('两条路的走向')
          .fontSize(16).fontWeight(600).fontColor('rgba(255,255,255,0.7)')
          .margin({ top: 72, bottom: 4 })

        Row({ space: 12 }) {
          Column({ space: 10 }) {
            Text('你的选择')
              .fontSize(11).fontColor(this.safeChosenOpt()?.color ?? '#FFFFFF')
              .fontWeight(600).letterSpacing(1)
            Text(this.safeChosenOpt()?.label ?? '')
              .fontSize(14).fontWeight(700).fontColor('#FFFFFF')
            ForEach(this.safeChosenOutcomes(), (card: OutcomeCard, idx: number) => {
              Column({ space: 4 }) {
                Text(`第 ${card.month} 个月`).fontSize(10).fontColor('rgba(255,255,255,0.4)')
                Text(card.text).fontSize(13).fontColor('rgba(255,255,255,0.85)').lineHeight(20)
              }
              .width('100%').padding(12)
              .backgroundColor('rgba(255,255,255,0.06)')
              .borderRadius(Theme.Radius.m)
              .opacity(this.outcomeRevealA ? 1 : 0)
              .translate({ y: this.outcomeRevealA ? 0 : 20 })
              .animation({ duration: 500, curve: Curve.Smooth, delay: idx * 150 })
            })
          }
          .layoutWeight(1).alignItems(HorizontalAlign.Start)

          Column().width(1).height('100%').backgroundColor('rgba(255,255,255,0.1)')

          Column({ space: 10 }) {
            Text('另一条路')
              .fontSize(11).fontColor('rgba(255,255,255,0.4)')
              .fontWeight(600).letterSpacing(1)
            Text(this.safeOtherOpt()?.label ?? '')
              .fontSize(14).fontWeight(700).fontColor('rgba(255,255,255,0.5)')
            ForEach(this.safeOtherOutcomes(), (card: OutcomeCard, idx: number) => {
              Column({ space: 4 }) {
                Text(`第 ${card.month} 个月`).fontSize(10).fontColor('rgba(255,255,255,0.3)')
                Text(card.text).fontSize(13).fontColor('rgba(255,255,255,0.45)').lineHeight(20)
              }
              .width('100%').padding(12)
              .backgroundColor('rgba(255,255,255,0.03)')
              .borderRadius(Theme.Radius.m)
              .opacity(this.outcomeRevealB ? 1 : 0)
              .translate({ y: this.outcomeRevealB ? 0 : 20 })
              .animation({ duration: 500, curve: Curve.Smooth, delay: idx * 150 })
            })
          }
          .layoutWeight(1).alignItems(HorizontalAlign.Start)
        }
        .width('100%').padding({ left: 20, right: 20 })
        .alignItems(VerticalAlign.Top)

        Column({ space: 12 }) {
          Button('就这样，继续')
            .width('100%').height(50)
            .fontSize(15).fontWeight(600).fontColor('#FFFFFF')
            .backgroundColor(this.safeChosenOpt()?.color ?? Theme.Color.Primary)
            .borderRadius(Theme.Radius.round)
            .onClick(() => this.onConfirmChoice())
          Button('我想反悔')
            .width('100%').height(44)
            .fontSize(14).fontColor('rgba(255,255,255,0.5)')
            .backgroundColor('rgba(255,255,255,0.06)')
            .borderRadius(Theme.Radius.round)
            .onClick(() => this.onRegret())
        }
        .padding({ left: 20, right: 20, bottom: 40 })
      }
      .width('100%')
    }
    .scrollBar(BarState.Off).width('100%').height('100%')
  }

  @Builder buildFollowup() {
    Column({ space: 0 }) {
      Blank().height(80)
      Row({ space: 8 }) {
        ForEach(this.safeScenario()?.followups ?? [], (_: FollowupQuestion, idx: number) => {
          Circle({ width: 6, height: 6 })
            .fill(idx === this.currentFollowupIndex ? '#FFFFFF' : 'rgba(255,255,255,0.25)')
        })
      }.margin({ bottom: 40 })

      Text(this.safeFollowup()?.text ?? '')
        .fontSize(22).fontWeight(700).fontColor('#FFFFFF')
        .lineHeight(34).textAlign(TextAlign.Center)
        .padding({ left: 28, right: 28 })
        .margin({ bottom: 48 })

      Column({ space: 16 }) {
        Slider({ value: this.sliderValue * 100, min: 0, max: 100, step: 1, style: SliderStyle.OutSet })
          .width('80%')
          .trackColor('rgba(255,255,255,0.2)')
          .selectedColor('#FFFFFF')
          .blockColor('#FFFFFF')
          .onChange((val: number) => { this.sliderValue = val / 100 })
        Row() {
          Text(this.safeFollowup()?.left_label ?? '').fontSize(12).fontColor('rgba(255,255,255,0.5)')
          Blank()
          Text(this.safeFollowup()?.right_label ?? '').fontSize(12).fontColor('rgba(255,255,255,0.5)')
        }.width('80%')
      }
      .width('100%').alignItems(HorizontalAlign.Center)

      Blank().layoutWeight(1)

      Button(this.currentFollowupIndex < (this.safeScenario()?.followups.length ?? 1) - 1 ? '下一题' : '查看我的画像')
        .width('80%').height(52)
        .fontSize(16).fontWeight(600).fontColor('#1a1a2e')
        .backgroundColor('#FFFFFF')
        .borderRadius(Theme.Radius.round)
        .margin({ bottom: 48 })
        .onClick(() => this.onFollowupNext())
    }
    .width('100%').height('100%').alignItems(HorizontalAlign.Center)
  }

  @Builder buildResult() {
    Column({ space: 0 }) {
      Blank().height(80)
      Column({ space: 24 }) {
        Text(this.getRiskLabel())
          .fontSize(28).fontWeight(800).fontColor('#FFFFFF').textAlign(TextAlign.Center)
        Text(this.getRiskDesc())
          .fontSize(15).fontColor('rgba(255,255,255,0.7)')
          .lineHeight(26).textAlign(TextAlign.Center)
          .padding({ left: 32, right: 32 })

        Column({ space: 12 }) {
          ForEach(this.dimBars, (bar: DimBar) => {
            Column({ space: 6 }) {
              Row() {
                Text(bar.key).fontSize(12).fontColor('rgba(255,255,255,0.5)')
                Blank()
                Text(`${Math.round(bar.val)}%`).fontSize(12).fontColor('rgba(255,255,255,0.5)')
              }.width('100%')
              Row() {
                Column()
                  .height(4).width(`${bar.val}%`)
                  .backgroundColor(this.safeScenario()?.theme_color ?? Theme.Color.Primary)
                  .borderRadius(2)
                Blank()
              }
              .width('100%').backgroundColor('rgba(255,255,255,0.1)').borderRadius(2)
            }
          })
        }
        .width('80%').padding(20)
        .backgroundColor('rgba(255,255,255,0.06)')
        .borderRadius(Theme.Radius.l)
      }
      .opacity(this.resultOpacity)
      .animation({ duration: 700, curve: Curve.Smooth })

      Blank().layoutWeight(1)

      Column({ space: 12 }) {
        Button(this.currentIndex < this.scenarios.length - 1 ? '下一个场景' : '完成，进入决策副本')
          .width('80%').height(52)
          .fontSize(15).fontWeight(600).fontColor('#1a1a2e')
          .backgroundColor('#FFFFFF')
          .borderRadius(Theme.Radius.round)
          .onClick(() => {
            if (this.currentIndex < this.scenarios.length - 1) {
              this.onNextScenario()
            } else {
              try {
                this.getUIContext().getRouter().pushUrl({ url: 'pages/QuickDecisionInput' })
              } catch (e) { this.navigateBack() }
            }
          })
        Text('数据已用于优化你的专属 AI 模型')
          .fontSize(12).fontColor('rgba(255,255,255,0.3)').margin({ bottom: 8 })
      }
      .width('100%').alignItems(HorizontalAlign.Center).margin({ bottom: 40 })
    }
    .width('100%').height('100%').alignItems(HorizontalAlign.Center)
  }
}
