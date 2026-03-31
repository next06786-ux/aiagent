/**
 * 平行人生 · 决策游戏 v2
 * 事件链 + 属性系统 + 倒计时 + 游戏化结局
 */
import { Theme } from '../common/Theme'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { getAuthService } from '../service/AuthService'

interface StatDelta { emotion: number; finance: number; social: number }

interface GameOption {
  id: string
  text: string
  sub: string
  delta: StatDelta
  next: string
}

interface GameNode {
  id: string
  type: string
  text: string
  options: GameOption[]
  next: string  // free_input 节点的下一节点
}

interface Ending {
  condition: string
  title: string
  text: string
  badge: string
}

interface Chapter {
  id: string
  title: string
  subtitle: string
  theme: string
  accent: string
  cover_emoji: string
  intro: string
  nodes: GameNode[]
  endings: Ending[]
}

interface ChoiceRecord {
  node_id: string
  option_id: string
  choice_time_ms: number
}

interface Stats { emotion: number; finance: number; social: number }

@Entry
@Component
struct ParallelLifeGame {
  // ── 状态 ──────────────────────────────────────────────────────────────
  @State phase: string = 'loading'   // loading | chapters | intro | playing | result
  @State chapters: Chapter[] = []
  @State currentChapter: Chapter | null = null
  @State currentNodeId: string = ''
  @State stats: Stats = { emotion: 50, finance: 50, social: 50 }
  @State lastDelta: StatDelta = { emotion: 0, finance: 0, social: 0 }
  @State showDelta: boolean = false
  @State choices: ChoiceRecord[] = []
  @State ending: Record<string, string> = {}
  @State finalStats: Stats = { emotion: 50, finance: 50, social: 50 }
  @State freeInputText: string = ''

  // 动效
  @State introOpacity: number = 0
  @State nodeOpacity: number = 0
  @State nodeTranslateY: number = 30
  @State optAOpacity: number = 0
  @State optBOpacity: number = 0
  @State optATranslateX: number = -40
  @State optBTranslateX: number = 40
  @State resultOpacity: number = 0
  @State statBarEmotion: number = 50
  @State statBarFinance: number = 50
  @State statBarSocial: number = 50

  // 倒计时
  @State countdown: number = 15
  @State countdownActive: boolean = false
  private countdownTimer: number = -1

  // 选择时间记录
  private nodeStartTime: number = 0

  private authService = getAuthService()

  aboutToAppear() { this.loadChapters() }
  aboutToDisappear() { this.stopCountdown() }

  // ── 数据加载 ──────────────────────────────────────────────────────────
  async loadChapters() {
    try {
      const req = http.createHttp()
      const res = await req.request(`${ApiConfig.getBaseUrl()}/api/game/parallel-life/chapters`,
        { method: http.RequestMethod.GET })
      req.destroy()
      if (res.responseCode === 200) {
        const body = JSON.parse(res.result as string) as Record<string, Object>
        this.chapters = body['data'] as Chapter[]
        if (this.chapters.length > 0) {
          this.phase = 'chapters'
        }
      }
    } catch (e) { console.error('加载关卡失败:', e) }
  }

  async loadChapter(chapterId: string) {
    try {
      const req = http.createHttp()
      const res = await req.request(`${ApiConfig.getBaseUrl()}/api/game/parallel-life/chapter/${chapterId}`,
        { method: http.RequestMethod.GET })
      req.destroy()
      if (res.responseCode === 200) {
        const body = JSON.parse(res.result as string) as Record<string, Object>
        this.currentChapter = body['data'] as Chapter
        this.phase = 'intro'
        this.animateIntroIn()
      }
    } catch (e) { console.error('加载关卡详情失败:', e) }
  }

  async loadRandomChapter() {
    try {
      const req = http.createHttp()
      const res = await req.request(`${ApiConfig.getBaseUrl()}/api/game/parallel-life/random`,
        { method: http.RequestMethod.GET })
      req.destroy()
      if (res.responseCode === 200) {
        const body = JSON.parse(res.result as string) as Record<string, Object>
        this.currentChapter = body['data'] as Chapter
        this.phase = 'intro'
        this.animateIntroIn()
      }
    } catch (e) { console.error('加载随机关卡失败:', e) }
  }

  // ── 游戏逻辑 ──────────────────────────────────────────────────────────
  startGame() {
    const ch = this.currentChapter
    if (!ch || ch.nodes.length === 0) return
    this.stats = { emotion: 50, finance: 50, social: 50 }
    this.statBarEmotion = 50; this.statBarFinance = 50; this.statBarSocial = 50
    this.choices = []
    this.currentNodeId = ch.nodes[0].id
    this.phase = 'playing'
    this.animateNodeIn()
    this.startCountdown()
  }

  currentNode(): GameNode | null {
    const ch = this.currentChapter
    if (!ch) return null
    return ch.nodes.find(n => n.id === this.currentNodeId) ?? null
  }

  async onChoose(opt: GameOption) {
    this.stopCountdown()
    const timeMs = Date.now() - this.nodeStartTime
    this.choices.push({ node_id: this.currentNodeId, option_id: opt.id, choice_time_ms: timeMs })

    // 显示属性变化
    this.lastDelta = opt.delta
    this.showDelta = true

    // 更新属性值
    const newEmotion = Math.max(-100, Math.min(100, this.stats.emotion + opt.delta.emotion))
    const newFinance = Math.max(-100, Math.min(100, this.stats.finance + opt.delta.finance))
    const newSocial  = Math.max(-100, Math.min(100, this.stats.social  + opt.delta.social))
    this.stats = { emotion: newEmotion, finance: newFinance, social: newSocial }
    animateTo({ duration: 600, curve: Curve.Smooth }, () => {
      this.statBarEmotion = newEmotion
      this.statBarFinance = newFinance
      this.statBarSocial  = newSocial
    })

    setTimeout(() => { this.showDelta = false }, 1500)

    // 跳转下一节点
    setTimeout(() => {
      if (opt.next === 'ending') {
        this.finishGame()
      } else {
        this.currentNodeId = opt.next
        this.animateNodeIn()
        if (this.currentNode()?.type !== 'free_input') {
          this.startCountdown()
        }
      }
    }, 800)
  }

  async submitFreeInput() {
    const text = this.freeInputText.trim()
    if (!text) return
    const ch = this.currentChapter
    const node = this.currentNode()
    if (!ch || !node) return
    this.choices.push({ node_id: this.currentNodeId, option_id: 'free', choice_time_ms: Date.now() - this.nodeStartTime })
    try {
      const userId = this.authService.getCurrentUserId()
      const req = http.createHttp()
      await req.request(`${ApiConfig.getBaseUrl()}/api/game/parallel-life/free-input`, {
        method: http.RequestMethod.POST,
        header: { 'Content-Type': 'application/json' },
        extraData: JSON.stringify({
          user_id: userId, chapter_id: ch.id, node_id: node.id,
          user_text: text, current_stats: this.stats
        })
      })
      req.destroy()
    } catch (e) { console.error('提交自由输入失败:', e) }
    this.freeInputText = ''
    const nextId = node.next ?? 'ending'
    if (nextId === 'ending') { this.finishGame() }
    else { this.currentNodeId = nextId; this.animateNodeIn(); this.startCountdown() }
  }

  async finishGame() {
    const ch = this.currentChapter
    if (!ch) return
    this.finalStats = { emotion: this.stats.emotion, finance: this.stats.finance, social: this.stats.social }
    try {
      const userId = this.authService.getCurrentUserId()
      const req = http.createHttp()
      const res = await req.request(`${ApiConfig.getBaseUrl()}/api/game/parallel-life/finish`, {
        method: http.RequestMethod.POST,
        header: { 'Content-Type': 'application/json' },
        extraData: JSON.stringify({
          user_id: userId,
          chapter_id: ch.id,
          final_stats: this.finalStats,
          choices: this.choices
        })
      })
      req.destroy()
      if (res.responseCode === 200) {
        const body = JSON.parse(res.result as string) as Record<string, Object>
        const data = body['data'] as Record<string, Object>
        this.ending = data['ending'] as Record<string, string>
      }
    } catch (e) { console.error('提交结果失败:', e) }
    this.phase = 'result'
    this.animateResultIn()
  }

  // 倒计时超时自动选第一个选项
  startCountdown() {
    this.countdown = 15
    this.countdownActive = true
    this.nodeStartTime = Date.now()
    this.countdownTimer = setInterval(() => {
      this.countdown--
      if (this.countdown <= 0) {
        this.stopCountdown()
        const node = this.currentNode()
        if (node && node.options.length > 0) {
          this.onChoose(node.options[0])
        }
      }
    }, 1000)
  }

  stopCountdown() {
    if (this.countdownTimer !== -1) {
      clearInterval(this.countdownTimer)
      this.countdownTimer = -1
    }
    this.countdownActive = false
  }

  private navigateBack() {
    this.stopCountdown()
    try { this.getUIContext().getRouter().back() } catch (e) {}
  }

  // ── 动效 ──────────────────────────────────────────────────────────────
  animateIntroIn() {
    this.introOpacity = 0
    setTimeout(() => {
      animateTo({ duration: 800, curve: Curve.Smooth }, () => { this.introOpacity = 1 })
    }, 200)
  }

  animateNodeIn() {
    this.nodeOpacity = 0; this.nodeTranslateY = 30
    this.optAOpacity = 0; this.optBOpacity = 0
    this.optATranslateX = -40; this.optBTranslateX = 40
    setTimeout(() => {
      animateTo({ duration: 400, curve: Curve.Smooth }, () => {
        this.nodeOpacity = 1; this.nodeTranslateY = 0
      })
    }, 100)
    setTimeout(() => {
      animateTo({ duration: 400, curve: Curve.Smooth }, () => {
        this.optAOpacity = 1; this.optATranslateX = 0
      })
    }, 400)
    setTimeout(() => {
      animateTo({ duration: 400, curve: Curve.Smooth }, () => {
        this.optBOpacity = 1; this.optBTranslateX = 0
      })
    }, 550)
  }

  animateResultIn() {
    this.resultOpacity = 0
    setTimeout(() => {
      animateTo({ duration: 700, curve: Curve.Smooth }, () => { this.resultOpacity = 1 })
    }, 300)
  }

  // ── 辅助 ──────────────────────────────────────────────────────────────
  statColor(val: number): string {
    if (val >= 60) return '#34d399'
    if (val >= 30) return '#fbbf24'
    return '#f87171'
  }

  deltaText(v: number): string {
    return v > 0 ? `+${v}` : `${v}`
  }

  accentColor(): string {
    return this.currentChapter?.accent ?? '#7C3AED'
  }

  themeColor(): string {
    return this.currentChapter?.theme ?? '#1a1a2e'
  }

  // ── build ──────────────────────────────────────────────────────────────
  build() {
    Stack() {
      // 背景
      Column().width('100%').height('100%').backgroundColor(this.themeColor())

      // 顶部栏
      Row() {
        Text('←').fontSize(22).fontColor('rgba(255,255,255,0.7)')
          .onClick(() => this.navigateBack())
        Text(this.currentChapter?.title ?? '平行人生')
          .fontSize(16).fontWeight(600).fontColor('#FFFFFF').margin({ left: 12 })
        Blank()
        if (this.phase === 'playing') {
          // 倒计时圆圈
          Stack() {
            Circle({ width: 36, height: 36 }).fill('rgba(255,255,255,0.1)')
            Text(`${this.countdown}`)
              .fontSize(14).fontWeight(700)
              .fontColor(this.countdown <= 5 ? '#f87171' : '#FFFFFF')
          }.width(36).height(36)
        }
      }
      .width('100%').height(56).padding({ left: 16, right: 16 })
      .position({ x: 0, y: 0 }).zIndex(10)

      // 属性条（游戏中显示）
      if (this.phase === 'playing') {
        Column({ space: 6 }) {
          this.StatBar('情绪', this.statBarEmotion, 'E')
          this.StatBar('财务', this.statBarFinance, 'F')
          this.StatBar('社交', this.statBarSocial, 'S')
        }
        .width('100%').padding({ left: 16, right: 16, top: 64, bottom: 0 })
        .position({ x: 0, y: 0 }).zIndex(9)
      }

      // 属性变化浮层
      if (this.showDelta) {
        Column({ space: 4 }) {
          if (this.lastDelta.emotion !== 0) {
            Text(`情绪 ${this.deltaText(this.lastDelta.emotion)}`)
              .fontSize(14).fontWeight(700)
              .fontColor(this.lastDelta.emotion > 0 ? '#34d399' : '#f87171')
          }
          if (this.lastDelta.finance !== 0) {
            Text(`财务 ${this.deltaText(this.lastDelta.finance)}`)
              .fontSize(14).fontWeight(700)
              .fontColor(this.lastDelta.finance > 0 ? '#34d399' : '#f87171')
          }
          if (this.lastDelta.social !== 0) {
            Text(`社交 ${this.deltaText(this.lastDelta.social)}`)
              .fontSize(14).fontWeight(700)
              .fontColor(this.lastDelta.social > 0 ? '#34d399' : '#f87171')
          }
        }
        .position({ x: 0, y: 160 }).width('100%')
        .alignItems(HorizontalAlign.Center).zIndex(20)
      }

      // 内容区
      if (this.phase === 'loading') { this.buildLoading() }
      else if (this.phase === 'chapters') { this.buildChapterSelect() }
      else if (this.phase === 'intro') { this.buildIntro() }
      else if (this.phase === 'playing') { this.buildPlaying() }
      else if (this.phase === 'result') { this.buildResult() }
    }
    .width('100%').height('100%')
  }

  @Builder
  StatBar(label: string, val: number, icon: string) {
    Row({ space: 6 }) {
      Stack() {
        Circle({ width: 16, height: 16 }).fill(this.statColor(val)).opacity(0.2)
        Text(icon).fontSize(9).fontWeight(700).fontColor(this.statColor(val))
      }.width(16).height(16)
      Text(label).fontSize(11).fontColor('rgba(255,255,255,0.6)').width(28)
      Row() {
        Column()
          .height(4)
          .width(`${Math.max(0, (val + 100) / 2)}%`)
          .backgroundColor(this.statColor(val))
          .borderRadius(2)
        Blank()
      }
      .layoutWeight(1).backgroundColor('rgba(255,255,255,0.1)').borderRadius(2)
      Text(`${val}`).fontSize(11).fontColor('rgba(255,255,255,0.5)').width(28).textAlign(TextAlign.End)
    }.width('100%').alignItems(VerticalAlign.Center)
  }

  @Builder buildLoading() {
    Column({ space: 16 }) {
      LoadingProgress().width(48).height(48).color('#FFFFFF')
      Text('加载中...').fontSize(14).fontColor('rgba(255,255,255,0.6)')
    }
    .width('100%').height('100%')
    .justifyContent(FlexAlign.Center).alignItems(HorizontalAlign.Center)
  }

  @Builder buildChapterSelect() {
    Scroll() {
      Column({ space: 20 }) {
        Column({ space: 8 }) {
          Text('平行人生').fontSize(28).fontWeight(800).fontColor('#FFFFFF')
          Text('每一个选择，都通向不同的人生')
            .fontSize(14).fontColor('rgba(255,255,255,0.5)')
        }
        .width('100%').padding({ top: 80, bottom: 8 }).alignItems(HorizontalAlign.Center)

        // 随机开始按钮
        Button('随机开始')
          .width('80%').height(50)
          .fontSize(16).fontWeight(700).fontColor('#FFFFFF')
          .backgroundColor('rgba(255,255,255,0.12)')
          .borderRadius(Theme.Radius.round)
          .border({ width: 1, color: 'rgba(255,255,255,0.2)' })
          .onClick(() => this.loadRandomChapter())

        Text('或选择一个关卡').fontSize(12).fontColor('rgba(255,255,255,0.35)')

        ForEach(this.chapters, (ch: Chapter) => {
          Column({ space: 10 }) {
            Text(ch.cover_emoji || '').fontSize(36)
            Text(ch.title).fontSize(18).fontWeight(700).fontColor('#FFFFFF')
            Text(ch.subtitle).fontSize(13).fontColor('rgba(255,255,255,0.6)')
          }
          .width('100%').padding(24)
          .backgroundColor('rgba(255,255,255,0.06)')
          .borderRadius(Theme.Radius.xl)
          .border({ width: 1, color: 'rgba(255,255,255,0.1)' })
          .alignItems(HorizontalAlign.Center)
          .onClick(() => this.loadChapter(ch.id))
          .stateStyles({
            pressed: { .scale({ x: 0.97, y: 0.97 }).backgroundColor('rgba(255,255,255,0.12)') },
            normal:  { .scale({ x: 1, y: 1 }).backgroundColor('rgba(255,255,255,0.06)') }
          })
        })

        Column().height(40)
      }
      .padding({ left: 20, right: 20 })
    }
    .scrollBar(BarState.Off).width('100%').height('100%')
  }

  @Builder buildIntro() {
    Column({ space: 0 }) {
      Blank().layoutWeight(1)
      Column({ space: 24 }) {
        Stack() {
          Circle({ width: 80, height: 80 }).fill(this.accentColor()).opacity(0.12)
          Circle({ width: 60, height: 60 }).fill(this.accentColor()).opacity(0.08)
          Text(this.currentChapter?.cover_emoji ?? 'P')
            .fontSize(28).fontWeight(800).fontColor(this.accentColor())
        }.width(80).height(80)
        Text(this.currentChapter?.title ?? '')
          .fontSize(28).fontWeight(800).fontColor('#FFFFFF').textAlign(TextAlign.Center)
        Text(this.currentChapter?.subtitle ?? '')
          .fontSize(15).fontColor('rgba(255,255,255,0.6)').textAlign(TextAlign.Center)
        Column()
          .width(40).height(2)
          .backgroundColor(this.accentColor())
          .borderRadius(1)
        Text(this.currentChapter?.intro ?? '')
          .fontSize(15).fontColor('rgba(255,255,255,0.8)')
          .lineHeight(26).textAlign(TextAlign.Center)
          .padding({ left: 32, right: 32 })
      }
      .opacity(this.introOpacity)
      .animation({ duration: 800, curve: Curve.Smooth })
      Blank().layoutWeight(1)
      Column({ space: 12 }) {
        Button('开始游戏')
          .width('80%').height(54)
          .fontSize(17).fontWeight(700).fontColor('#FFFFFF')
          .backgroundColor(this.accentColor())
          .borderRadius(Theme.Radius.round)
          .shadow({ radius: 20, color: this.accentColor(), offsetY: 6, offsetX: 0 })
          .onClick(() => this.startGame())
        Text('每次选择都会影响你的情绪、财务和社交')
          .fontSize(12).fontColor('rgba(255,255,255,0.35)').textAlign(TextAlign.Center)
      }
      .width('100%').alignItems(HorizontalAlign.Center).margin({ bottom: 48 })
    }
    .width('100%').height('100%').alignItems(HorizontalAlign.Center)
  }

  @Builder buildPlaying() {
    Column({ space: 0 }) {
      Blank().height(160)

      // 事件文字
      Column({ space: 0 }) {
        Text(this.currentNode()?.text ?? '')
          .fontSize(18).fontWeight(600).fontColor('#FFFFFF')
          .lineHeight(30).textAlign(TextAlign.Center)
          .padding({ left: 24, right: 24 })
      }
      .opacity(this.nodeOpacity)
      .translate({ y: this.nodeTranslateY })
      .animation({ duration: 400, curve: Curve.Smooth })

      Blank().layoutWeight(1)

      // 自由输入节点
      if (this.currentNode()?.type === 'free_input') {
        Column({ space: 16 }) {
          TextArea({ placeholder: '写下你的真实想法...' })
            .width('100%').height(100)
            .fontSize(15).fontColor('#FFFFFF')
            .backgroundColor('rgba(255,255,255,0.08)')
            .borderRadius(Theme.Radius.l)
            .placeholderColor('rgba(255,255,255,0.3)')
            .onChange((val: string) => { this.freeInputText = val })

          Button('继续')
            .width('100%').height(48)
            .fontSize(15).fontWeight(600).fontColor('#FFFFFF')
            .backgroundColor(this.accentColor())
            .borderRadius(Theme.Radius.round)
            .enabled(this.freeInputText.trim().length > 0)
            .onClick(() => this.submitFreeInput())
        }
        .padding({ left: 20, right: 20, bottom: 48 })
      } else {
      // 选项卡片
      Column({ space: 14 }) {
        ForEach(this.currentNode()?.options ?? [], (opt: GameOption, idx: number) => {
          Column({ space: 8 }) {
            Text(opt.text)
              .fontSize(16).fontWeight(700).fontColor('#FFFFFF')
            Text(opt.sub)
              .fontSize(12).fontColor('rgba(255,255,255,0.55)').lineHeight(18)
            // 属性预览
            Row({ space: 12 }) {
              if (opt.delta.emotion !== 0) {
                Text(`情绪${this.deltaText(opt.delta.emotion)}`)
                  .fontSize(11).fontColor(opt.delta.emotion > 0 ? '#34d399' : '#f87171')
                  .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                  .backgroundColor(opt.delta.emotion > 0 ? 'rgba(52,211,153,0.12)' : 'rgba(248,113,113,0.12)')
                  .borderRadius(Theme.Radius.round)
              }
              if (opt.delta.finance !== 0) {
                Text(`财务${this.deltaText(opt.delta.finance)}`)
                  .fontSize(11).fontColor(opt.delta.finance > 0 ? '#34d399' : '#f87171')
                  .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                  .backgroundColor(opt.delta.finance > 0 ? 'rgba(52,211,153,0.12)' : 'rgba(248,113,113,0.12)')
                  .borderRadius(Theme.Radius.round)
              }
              if (opt.delta.social !== 0) {
                Text(`社交${this.deltaText(opt.delta.social)}`)
                  .fontSize(11).fontColor(opt.delta.social > 0 ? '#34d399' : '#f87171')
                  .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                  .backgroundColor(opt.delta.social > 0 ? 'rgba(52,211,153,0.12)' : 'rgba(248,113,113,0.12)')
                  .borderRadius(Theme.Radius.round)
              }
            }
          }
          .width('100%').padding(18)
          .backgroundColor('rgba(255,255,255,0.07)')
          .borderRadius(Theme.Radius.l)
          .border({ width: 1.5, color: idx === 0 ? `${this.accentColor()}66` : 'rgba(255,255,255,0.1)' })
          .opacity(idx === 0 ? this.optAOpacity : this.optBOpacity)
          .translate({ x: idx === 0 ? this.optATranslateX : this.optBTranslateX })
          .animation({ duration: 400, curve: Curve.Smooth })
          .onClick(() => this.onChoose(opt))
          .stateStyles({
            pressed: { .scale({ x: 0.97, y: 0.97 }).backgroundColor('rgba(255,255,255,0.13)') },
            normal:  { .scale({ x: 1, y: 1 }).backgroundColor('rgba(255,255,255,0.07)') }
          })
        })
      }
      .padding({ left: 20, right: 20, bottom: 48 })
      } // end else (choice nodes)
    }
    .width('100%').height('100%').alignItems(HorizontalAlign.Center)
  }

  @Builder buildResult() {
    Scroll() {
      Column({ space: 0 }) {
        Blank().height(72)
        Column({ space: 20 }) {
          // 徽章
          Column({ space: 8 }) {
            Stack() {
              Circle({ width: 56, height: 56 })
                .fill(this.accentColor()).opacity(0.15)
              Text('P').fontSize(24).fontWeight(800).fontColor(this.accentColor())
            }.width(56).height(56)
            Text(this.ending['badge'] ?? '完成')
              .fontSize(13).fontColor(this.accentColor()).fontWeight(600)
              .padding({ left: 16, right: 16, top: 5, bottom: 5 })
              .backgroundColor(`${this.accentColor()}22`)
              .borderRadius(Theme.Radius.round)
          }.alignItems(HorizontalAlign.Center)

          Text(this.ending['title'] ?? '游戏结束')
            .fontSize(26).fontWeight(800).fontColor('#FFFFFF').textAlign(TextAlign.Center)

          Text(this.ending['text'] ?? '')
            .fontSize(15).fontColor('rgba(255,255,255,0.75)')
            .lineHeight(26).textAlign(TextAlign.Center)
            .padding({ left: 28, right: 28 })

          // 最终属性
          Column({ space: 10 }) {
            Text('最终状态').fontSize(13).fontColor('rgba(255,255,255,0.4)').fontWeight(600)
            Row({ space: 0 }) {
              this.FinalStatBlock('情绪', this.finalStats.emotion, 'E')
              this.FinalStatBlock('财务', this.finalStats.finance, 'F')
              this.FinalStatBlock('社交', this.finalStats.social, 'S')
            }.width('100%')
          }
          .width('88%').padding(20)
          .backgroundColor('rgba(255,255,255,0.06)')
          .borderRadius(Theme.Radius.l)

          // 选择统计
          Text(`共做了 ${this.choices.length} 次选择`)
            .fontSize(13).fontColor('rgba(255,255,255,0.35)')

          Text('你的选择已用于优化专属 AI 模型')
            .fontSize(12).fontColor('rgba(255,255,255,0.25)')
        }
        .opacity(this.resultOpacity)
        .animation({ duration: 700, curve: Curve.Smooth })

        Blank().height(32)

        Column({ space: 12 }) {
          Button('进入决策副本')
            .width('80%').height(52)
            .fontSize(15).fontWeight(700).fontColor('#FFFFFF')
            .backgroundColor(this.accentColor())
            .borderRadius(Theme.Radius.round)
            .onClick(() => {
              try { this.getUIContext().getRouter().pushUrl({ url: 'pages/QuickDecisionInput' }) }
              catch (e) { this.navigateBack() }
            })
          Button('再玩一次')
            .width('80%').height(44)
            .fontSize(14).fontColor('rgba(255,255,255,0.5)')
            .backgroundColor('rgba(255,255,255,0.06)')
            .borderRadius(Theme.Radius.round)
            .onClick(() => {
              this.phase = 'intro'
              this.animateIntroIn()
            })
        }
        .width('100%').alignItems(HorizontalAlign.Center).margin({ bottom: 48 })
      }
      .width('100%').alignItems(HorizontalAlign.Center)
    }
    .scrollBar(BarState.Off).width('100%').height('100%')
  }

  @Builder
  FinalStatBlock(label: string, val: number, icon: string) {
    Column({ space: 6 }) {
      Stack() {
        Circle({ width: 32, height: 32 }).fill(this.statColor(val)).opacity(0.15)
        Text(icon).fontSize(14).fontWeight(800).fontColor(this.statColor(val))
      }.width(32).height(32)
      Text(`${val}`).fontSize(20).fontWeight(800).fontColor(this.statColor(val))
      Text(label).fontSize(11).fontColor('rgba(255,255,255,0.4)')
    }
    .layoutWeight(1).alignItems(HorizontalAlign.Center).padding(12)
  }
}
