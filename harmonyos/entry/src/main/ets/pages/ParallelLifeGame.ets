/**
 * 平行人生 · 决策游戏 v3
 * HarmonyOS 6 流体设计 · 模仿"我的账号"鸿蒙化UI
 * 事件链 + 属性系统 + 倒计时 + 游戏化结局
 */
import { Theme } from '../common/Theme'
import { SimpleIcon } from '../components/IconRenderer'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { getAuthService } from '../service/AuthService'
import router from '@ohos.router'

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
  next: string
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
  @State phase: string = 'loading'
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
  @State showContent: boolean = false

  // 动效
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
  private nodeStartTime: number = 0

  private authService = getAuthService()

  aboutToAppear() {
    this.loadChapters()
    setTimeout(() => { this.showContent = true }, 50)
  }
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
        if (this.chapters.length > 0) { this.phase = 'chapters' }
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
    this.lastDelta = opt.delta
    this.showDelta = true
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
    setTimeout(() => {
      if (opt.next === 'ending') { this.finishGame() }
      else {
        this.currentNodeId = opt.next
        this.animateNodeIn()
        if (this.currentNode()?.type !== 'free_input') { this.startCountdown() }
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
        extraData: JSON.stringify({ user_id: userId, chapter_id: ch.id, node_id: node.id, user_text: text, current_stats: this.stats })
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
        extraData: JSON.stringify({ user_id: userId, chapter_id: ch.id, final_stats: this.finalStats, choices: this.choices })
      })
      req.destroy()
      if (res.responseCode === 200) {
        const body = JSON.parse(res.result as string) as Record<string, Object>
        const data = body['data'] as Record<string, Object>
        this.ending = data['ending'] as Record<string, string>
      }
    } catch (e) { console.error('提交结果失败:', e) }
    this.phase = 'result'
    this.resultOpacity = 0
    setTimeout(() => {
      animateTo({ duration: 700, curve: Curve.Smooth }, () => { this.resultOpacity = 1 })
    }, 300)
  }

  startCountdown() {
    this.countdown = 15
    this.countdownActive = true
    this.nodeStartTime = Date.now()
    this.countdownTimer = setInterval(() => {
      this.countdown--
      if (this.countdown <= 0) {
        this.stopCountdown()
        const node = this.currentNode()
        if (node && node.options.length > 0) { this.onChoose(node.options[0]) }
      }
    }, 1000)
  }

  stopCountdown() {
    if (this.countdownTimer !== -1) { clearInterval(this.countdownTimer); this.countdownTimer = -1 }
    this.countdownActive = false
  }

  private navigateBack() {
    this.stopCountdown()
    try { router.back() } catch (e) {}
  }

  animateNodeIn() {
    this.nodeOpacity = 0; this.nodeTranslateY = 30
    this.optAOpacity = 0; this.optBOpacity = 0
    this.optATranslateX = -40; this.optBTranslateX = 40
    setTimeout(() => { animateTo({ duration: 400, curve: Curve.Smooth }, () => { this.nodeOpacity = 1; this.nodeTranslateY = 0 }) }, 100)
    setTimeout(() => { animateTo({ duration: 400, curve: Curve.Smooth }, () => { this.optAOpacity = 1; this.optATranslateX = 0 }) }, 400)
    setTimeout(() => { animateTo({ duration: 400, curve: Curve.Smooth }, () => { this.optBOpacity = 1; this.optBTranslateX = 0 }) }, 550)
  }

  statColor(val: number): string {
    if (val >= 60) return '#00C853'
    if (val >= 30) return '#FF9500'
    return '#FF3B30'
  }
  deltaText(v: number): string { return v > 0 ? `+${v}` : `${v}` }
  accentColor(): string { return this.currentChapter?.accent ?? '#6B48FF' }

  // ── build ──────────────────────────────────────────────────────────────
  build() {
    Stack() {
      Column().width('100%').height('100%').backgroundColor(Theme.Color.BackgroundPrimary)

      Column() {
        // 顶部导航栏 - 与UserProfile一致
        Row() {
          Text('<-')
            .fontSize(24)
            .fontColor(Theme.Color.Primary)
            .onClick(() => this.navigateBack())

          Text(this.currentChapter?.title ?? '平行人生')
            .fontSize(18)
            .fontWeight(FontWeight.Medium)
            .fontColor(Theme.Color.TextPrimary)
            .layoutWeight(1)
            .margin({ left: 12 })

          if (this.phase === 'playing') {
            // 倒计时
            Stack() {
              Circle({ width: 40, height: 40 })
                .fill(this.countdown <= 5 ? 'rgba(255,59,48,0.1)' : Theme.Color.GlassMedium)
              Text(`${this.countdown}`)
                .fontSize(16).fontWeight(700)
                .fontColor(this.countdown <= 5 ? Theme.Color.Destructive : Theme.Color.TextSecondary)
            }.width(40).height(40)
          }
        }
        .width('100%')
        .padding({ left: 16, right: 16, top: 12, bottom: 12 })
        .backgroundColor(Theme.Color.BackgroundPrimary)

        // 属性条（游戏中显示）
        if (this.phase === 'playing') {
          Column({ space: 8 }) {
            this.StatBar('情绪', this.statBarEmotion, 'heart')
            this.StatBar('财务', this.statBarFinance, 'chart')
            this.StatBar('社交', this.statBarSocial, 'user')
          }
          .width('100%').padding({ left: 16, right: 16, top: 8, bottom: 12 })
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .border({ width: { bottom: 0.5 }, color: Theme.Color.BorderLight })
        }

        // 属性变化浮层
        if (this.showDelta) {
          Row({ space: 12 }) {
            if (this.lastDelta.emotion !== 0) {
              Text(`情绪 ${this.deltaText(this.lastDelta.emotion)}`)
                .fontSize(13).fontWeight(600)
                .fontColor(this.lastDelta.emotion > 0 ? Theme.Color.Accent : Theme.Color.Destructive)
                .padding({ left: 10, right: 10, top: 4, bottom: 4 })
                .backgroundColor(this.lastDelta.emotion > 0 ? 'rgba(0,200,83,0.08)' : 'rgba(255,59,48,0.08)')
                .borderRadius(Theme.Radius.round)
            }
            if (this.lastDelta.finance !== 0) {
              Text(`财务 ${this.deltaText(this.lastDelta.finance)}`)
                .fontSize(13).fontWeight(600)
                .fontColor(this.lastDelta.finance > 0 ? Theme.Color.Accent : Theme.Color.Destructive)
                .padding({ left: 10, right: 10, top: 4, bottom: 4 })
                .backgroundColor(this.lastDelta.finance > 0 ? 'rgba(0,200,83,0.08)' : 'rgba(255,59,48,0.08)')
                .borderRadius(Theme.Radius.round)
            }
            if (this.lastDelta.social !== 0) {
              Text(`社交 ${this.deltaText(this.lastDelta.social)}`)
                .fontSize(13).fontWeight(600)
                .fontColor(this.lastDelta.social > 0 ? Theme.Color.Accent : Theme.Color.Destructive)
                .padding({ left: 10, right: 10, top: 4, bottom: 4 })
                .backgroundColor(this.lastDelta.social > 0 ? 'rgba(0,200,83,0.08)' : 'rgba(255,59,48,0.08)')
                .borderRadius(Theme.Radius.round)
            }
          }.width('100%').justifyContent(FlexAlign.Center).padding(8)
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
    .width('100%').height('100%')
  }

  @Builder
  StatBar(label: string, val: number, iconName: string) {
    Row({ space: 8 }) {
      Stack() {
        Circle({ width: 28, height: 28 }).fill(this.statColor(val)).opacity(0.15)
        SimpleIcon({ iconName: iconName, iconSize: 14, color: this.statColor(val) })
      }.width(28).height(28)
      Text(label).fontSize(12).fontColor(Theme.Color.TextSecondary).width(28)
      Row() {
        Column()
          .height(6)
          .width(`${Math.max(0, (val + 100) / 2)}%`)
          .backgroundColor(this.statColor(val))
          .borderRadius(3)
        Blank()
      }.layoutWeight(1).height(6).backgroundColor(Theme.Color.BorderLight).borderRadius(3)
      Text(`${val}`).fontSize(12).fontWeight(600).fontColor(this.statColor(val)).width(32).textAlign(TextAlign.End)
    }.width('100%').alignItems(VerticalAlign.Center)
  }

  @Builder buildLoading() {
    Column({ space: 16 }) {
      LoadingProgress().width(48).height(48).color(Theme.Color.Primary)
      Text('加载中...').fontSize(14).fontColor(Theme.Color.TextTertiary)
    }
    .width('100%').layoutWeight(1)
    .justifyContent(FlexAlign.Center).alignItems(HorizontalAlign.Center)
  }

  @Builder buildChapterSelect() {
    Scroll() {
      Column({ space: 20 }) {
        // Hero卡片 - 与UserProfile的buildUserCard一致
        Stack({ alignContent: Alignment.BottomStart }) {
          Column().width('100%').height('100%')
            .linearGradient({ angle: 135, colors: [['#FF6B9D', 0], ['#6B48FF', 1]] })
            .opacity(0.12)
          Circle({ width: 150, height: 150 }).fill('#FF6B9D').opacity(0.2).blur(60)
            .position({ x: -40, y: -40 })
          Circle({ width: 100, height: 100 }).fill('#6B48FF').opacity(0.15).blur(50)
            .position({ x: '80%', y: '60%' })
          Column({ space: 10 }) {
            Stack() {
              Circle({ width: 64, height: 64 }).fill('#FF6B9D').opacity(0.15)
              SimpleIcon({ iconName: 'life', iconSize: 32, color: '#FF6B9D' })
            }.width(64).height(64)
            Text('平行人生').fontSize(24).fontWeight(700).fontColor(Theme.Color.TextPrimary)
            Text('每一个选择，都通向不同的人生').fontSize(14).fontColor(Theme.Color.TextSecondary)
          }.padding(24).width('100%').alignItems(HorizontalAlign.Start)
        }
        .width('100%').height(180)
        .backgroundColor(Theme.Color.GlassHeavy)
        .backdropBlur(Theme.Blur.Heavy)
        .borderRadius(Theme.Radius.xl)
        .border({ width: 1, color: Theme.Color.BorderLight })
        .shadow(Theme.Shadow.Medium)
        .opacity(this.showContent ? 1 : 0)
        .scale({ x: this.showContent ? 1 : 0.95, y: this.showContent ? 1 : 0.95 })
        .animation({ duration: 700, curve: Curve.Smooth, delay: 0 })

        // 随机开始按钮
        Button('随机开始')
          .width('100%').height(52).fontSize(16).fontWeight(600).fontColor('#FFFFFF')
          .backgroundColor(Theme.Color.Secondary)
          .borderRadius(Theme.Radius.l)
          .shadow(Theme.Shadow.GlowPrimary)
          .onClick(() => this.loadRandomChapter())
          .opacity(this.showContent ? 1 : 0)
          .translate({ y: this.showContent ? 0 : 20 })
          .animation({ duration: 600, curve: Curve.Smooth, delay: 100 })

        // 关卡列表标题
        Text('选择关卡')
          .fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
          .padding({ left: 8 })
          .opacity(this.showContent ? 1 : 0)
          .translate({ x: this.showContent ? 0 : -20 })
          .animation({ duration: 600, curve: Curve.Smooth, delay: 200 })

        // 关卡列表 - 与UserProfile的buildMenuItem一致
        ForEach(this.chapters, (ch: Chapter, index: number) => {
          Row({ space: 12 }) {
            Stack() {
              Circle({ width: 48, height: 48 }).fill(ch.accent || '#6B48FF').opacity(0.15)
              SimpleIcon({ iconName: 'life', iconSize: 24, color: ch.accent || '#6B48FF' })
            }.width(48).height(48)
            Column({ space: 4 }) {
              Text(ch.title).fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
              Text(ch.subtitle).fontSize(12).fontColor(Theme.Color.TextTertiary)
            }.alignItems(HorizontalAlign.Start).layoutWeight(1)
            Text('->')
              .fontSize(20).fontColor(Theme.Color.TextTertiary)
          }
          .width('100%').padding(16)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)
          .onClick(() => this.loadChapter(ch.id))
          .opacity(this.showContent ? 1 : 0)
          .translate({ x: this.showContent ? 0 : -30 })
          .animation({ duration: 600, curve: Curve.Smooth, delay: 300 + index * 80 })
          .stateStyles({
            pressed: { .scale({ x: 0.98, y: 0.98 }).backgroundColor('#F8F9FA') },
            normal:  { .scale({ x: 1, y: 1 }).backgroundColor(Theme.Color.BackgroundSecondary) }
          })
        })

        Column().height(40)
      }.padding({ left: 16, right: 16, bottom: 60 })
    }.scrollBar(BarState.Off).edgeEffect(EdgeEffect.Spring).layoutWeight(1)
  }

  @Builder buildIntro() {
    Column({ space: 0 }) {
      Scroll() {
        Column({ space: 24 }) {
          // 关卡Hero卡片
          Stack({ alignContent: Alignment.BottomStart }) {
            Column().width('100%').height('100%')
              .linearGradient({ angle: 135, colors: [[this.accentColor(), 0], ['#764ba2', 1]] })
              .opacity(0.12)
            Circle({ width: 120, height: 120 }).fill(this.accentColor()).opacity(0.18).blur(50)
              .position({ x: -30, y: -30 })
            Column({ space: 12 }) {
              Stack() {
                Circle({ width: 64, height: 64 }).fill(this.accentColor()).opacity(0.15)
                SimpleIcon({ iconName: 'life', iconSize: 32, color: this.accentColor() })
              }.width(64).height(64)
              Text(this.currentChapter?.title ?? '').fontSize(24).fontWeight(700).fontColor(Theme.Color.TextPrimary)
              Text(this.currentChapter?.subtitle ?? '').fontSize(14).fontColor(Theme.Color.TextSecondary)
            }.padding(24).width('100%').alignItems(HorizontalAlign.Start)
          }
          .width('100%').height(180)
          .backgroundColor(Theme.Color.GlassHeavy)
          .backdropBlur(Theme.Blur.Heavy)
          .borderRadius(Theme.Radius.xl)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Medium)

          // 简介卡片
          Column({ space: 12 }) {
            Text('关卡简介').fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
            Text(this.currentChapter?.intro ?? '')
              .fontSize(15).fontColor(Theme.Color.TextSecondary).lineHeight(24)
          }
          .width('100%').padding(20)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)

          // 属性说明
          Row({ space: 12 }) {
            this.buildStatPreview('情绪', 'heart', '#00C853')
            this.buildStatPreview('财务', 'chart', '#FF9500')
            this.buildStatPreview('社交', 'user', '#0A59F7')
          }.width('100%')

          // 提示
          Text('每次选择都会影响你的情绪、财务和社交')
            .fontSize(13).fontColor(Theme.Color.TextTertiary).textAlign(TextAlign.Center)
            .width('100%')
        }
        .padding({ left: 16, right: 16, bottom: 120 })
      }
      .scrollBar(BarState.Off).edgeEffect(EdgeEffect.Spring).layoutWeight(1)

      // 底部按钮
      Column() {
        Button('开始游戏')
          .width('100%').height(52).fontSize(16).fontWeight(600).fontColor('#FFFFFF')
          .backgroundColor(this.accentColor())
          .borderRadius(Theme.Radius.l)
          .shadow({ radius: 16, color: this.accentColor(), offsetY: 4, offsetX: 0 })
          .onClick(() => this.startGame())
      }
      .width('100%').padding({ left: 16, right: 16, bottom: 32, top: 12 })
      .backgroundColor(Theme.Color.BackgroundPrimary)
    }
    .width('100%').layoutWeight(1)
  }

  @Builder
  buildStatPreview(label: string, iconName: string, color: string) {
    Column({ space: 8 }) {
      Stack() {
        Circle({ width: 40, height: 40 }).fill(color).opacity(0.15)
        SimpleIcon({ iconName: iconName, iconSize: 20, color: color })
      }.width(40).height(40)
      Text(label).fontSize(12).fontColor(Theme.Color.TextTertiary)
    }
    .layoutWeight(1).padding(16)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .alignItems(HorizontalAlign.Center)
  }

  @Builder buildPlaying() {
    Column({ space: 0 }) {
      Scroll() {
        Column({ space: 20 }) {
          // 事件卡片
          Column({ space: 12 }) {
            Row({ space: 10 }) {
              Stack() {
                Circle({ width: 40, height: 40 }).fill(this.accentColor()).opacity(0.15)
                SimpleIcon({ iconName: 'comparison', iconSize: 20, color: this.accentColor() })
              }.width(40).height(40)
              Text('当前事件').fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
            }
            Text(this.currentNode()?.text ?? '')
              .fontSize(17).fontWeight(500).fontColor(Theme.Color.TextPrimary)
              .lineHeight(28)
          }
          .width('100%').padding(20)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)
          .opacity(this.nodeOpacity)
          .translate({ y: this.nodeTranslateY })
          .animation({ duration: 400, curve: Curve.Smooth })

          // 自由输入节点
          if (this.currentNode()?.type === 'free_input') {
            Column({ space: 16 }) {
              TextArea({ placeholder: '写下你的真实想法...' })
                .width('100%').height(100).fontSize(15)
                .fontColor(Theme.Color.TextPrimary)
                .backgroundColor(Theme.Color.BackgroundTertiary)
                .borderRadius(Theme.Radius.l)
                .placeholderColor(Theme.Color.TextTertiary)
                .onChange((val: string) => { this.freeInputText = val })
              Button('继续')
                .width('100%').height(48).fontSize(15).fontWeight(600).fontColor('#FFFFFF')
                .backgroundColor(this.accentColor())
                .borderRadius(Theme.Radius.l)
                .enabled(this.freeInputText.trim().length > 0)
                .onClick(() => this.submitFreeInput())
            }
          } else {
            // 选项列表 - 与UserProfile菜单项风格一致
            Column({ space: 12 }) {
              Text('做出你的选择').fontSize(14).fontWeight(600).fontColor(Theme.Color.TextTertiary)
                .padding({ left: 4 })

              ForEach(this.currentNode()?.options ?? [], (opt: GameOption, idx: number) => {
                Row({ space: 12 }) {
                  Stack() {
                    Circle({ width: 48, height: 48 }).fill(this.accentColor()).opacity(0.15)
                    Text(`${idx + 1}`).fontSize(18).fontWeight(700).fontColor(this.accentColor())
                  }.width(48).height(48)
                  Column({ space: 4 }) {
                    Text(opt.text).fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
                    Text(opt.sub).fontSize(12).fontColor(Theme.Color.TextTertiary).maxLines(2)
                    // 属性预览标签
                    Row({ space: 8 }) {
                      if (opt.delta.emotion !== 0) {
                        Text(`情绪${this.deltaText(opt.delta.emotion)}`)
                          .fontSize(11).fontColor(opt.delta.emotion > 0 ? Theme.Color.Accent : Theme.Color.Destructive)
                          .padding({ left: 6, right: 6, top: 2, bottom: 2 })
                          .backgroundColor(opt.delta.emotion > 0 ? 'rgba(0,200,83,0.08)' : 'rgba(255,59,48,0.08)')
                          .borderRadius(Theme.Radius.round)
                      }
                      if (opt.delta.finance !== 0) {
                        Text(`财务${this.deltaText(opt.delta.finance)}`)
                          .fontSize(11).fontColor(opt.delta.finance > 0 ? Theme.Color.Accent : Theme.Color.Destructive)
                          .padding({ left: 6, right: 6, top: 2, bottom: 2 })
                          .backgroundColor(opt.delta.finance > 0 ? 'rgba(0,200,83,0.08)' : 'rgba(255,59,48,0.08)')
                          .borderRadius(Theme.Radius.round)
                      }
                      if (opt.delta.social !== 0) {
                        Text(`社交${this.deltaText(opt.delta.social)}`)
                          .fontSize(11).fontColor(opt.delta.social > 0 ? Theme.Color.Accent : Theme.Color.Destructive)
                          .padding({ left: 6, right: 6, top: 2, bottom: 2 })
                          .backgroundColor(opt.delta.social > 0 ? 'rgba(0,200,83,0.08)' : 'rgba(255,59,48,0.08)')
                          .borderRadius(Theme.Radius.round)
                      }
                    }.margin({ top: 4 })
                  }.alignItems(HorizontalAlign.Start).layoutWeight(1)
                  Text('->')
                    .fontSize(20).fontColor(Theme.Color.TextTertiary)
                }
                .width('100%').padding(16)
                .backgroundColor(Theme.Color.BackgroundSecondary)
                .borderRadius(Theme.Radius.l)
                .border({ width: 1, color: Theme.Color.BorderLight })
                .shadow(Theme.Shadow.Soft)
                .onClick(() => this.onChoose(opt))
                .opacity(idx === 0 ? this.optAOpacity : this.optBOpacity)
                .translate({ x: idx === 0 ? this.optATranslateX : this.optBTranslateX })
                .animation({ duration: 400, curve: Curve.Smooth })
                .stateStyles({
                  pressed: { .scale({ x: 0.98, y: 0.98 }).backgroundColor('#F8F9FA') },
                  normal:  { .scale({ x: 1, y: 1 }).backgroundColor(Theme.Color.BackgroundSecondary) }
                })
              })
            }
          }
        }
        .padding({ left: 16, right: 16, bottom: 60 })
      }
      .scrollBar(BarState.Off).edgeEffect(EdgeEffect.Spring).layoutWeight(1)
    }
    .width('100%').layoutWeight(1)
  }

  @Builder buildResult() {
    Scroll() {
      Column({ space: 24 }) {
        // 结果Hero卡片
        Stack({ alignContent: Alignment.BottomStart }) {
          Column().width('100%').height('100%')
            .linearGradient({ angle: 135, colors: [[this.accentColor(), 0], ['#764ba2', 1]] })
            .opacity(0.12)
          Circle({ width: 150, height: 150 }).fill(this.accentColor()).opacity(0.2).blur(60)
            .position({ x: -40, y: -40 })
          Column({ space: 10 }) {
            Stack() {
              Circle({ width: 64, height: 64 }).fill(this.accentColor()).opacity(0.15)
              SimpleIcon({ iconName: 'life', iconSize: 32, color: this.accentColor() })
            }.width(64).height(64)
            Text(this.ending['title'] ?? '游戏结束')
              .fontSize(24).fontWeight(700).fontColor(Theme.Color.TextPrimary)
            Text(this.ending['badge'] ?? '完成')
              .fontSize(13).fontColor(this.accentColor()).fontWeight(600)
              .padding({ left: 16, right: 16, top: 5, bottom: 5 })
              .backgroundColor(`${this.accentColor()}18`)
              .borderRadius(Theme.Radius.round)
          }.padding(24).width('100%').alignItems(HorizontalAlign.Start)
        }
        .width('100%').height(200)
        .backgroundColor(Theme.Color.GlassHeavy)
        .backdropBlur(Theme.Blur.Heavy)
        .borderRadius(Theme.Radius.xl)
        .border({ width: 1, color: Theme.Color.BorderLight })
        .shadow(Theme.Shadow.Medium)
        .opacity(this.resultOpacity)
        .animation({ duration: 700, curve: Curve.Smooth })

        // 结局描述
        if (this.ending['text']) {
          Column({ space: 8 }) {
            Text('结局').fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
            Text(this.ending['text'] ?? '')
              .fontSize(15).fontColor(Theme.Color.TextSecondary).lineHeight(24)
          }
          .width('100%').padding(20)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)
          .opacity(this.resultOpacity)
          .animation({ duration: 700, curve: Curve.Smooth })
        }

        // 最终属性 - 与UserProfile的buildStatsSection一致
        Row({ space: 12 }) {
          this.FinalStatItem('情绪', this.finalStats.emotion, 'heart')
          this.FinalStatItem('财务', this.finalStats.finance, 'chart')
          this.FinalStatItem('社交', this.finalStats.social, 'user')
        }
        .width('100%')
        .opacity(this.resultOpacity)
        .animation({ duration: 700, curve: Curve.Smooth })

        // 选择统计
        Column({ space: 8 }) {
          Text(`共做了 ${this.choices.length} 次选择`)
            .fontSize(14).fontColor(Theme.Color.TextSecondary)
          Text('你的选择已用于优化专属 AI 模型')
            .fontSize(12).fontColor(Theme.Color.TextTertiary)
        }
        .width('100%').padding(16)
        .backgroundColor(Theme.Color.BackgroundSecondary)
        .borderRadius(Theme.Radius.l)
        .border({ width: 1, color: Theme.Color.BorderLight })
        .alignItems(HorizontalAlign.Center)

        // 操作按钮
        Column({ space: 12 }) {
          Button('进入决策副本')
            .width('100%').height(52).fontSize(16).fontWeight(600).fontColor('#FFFFFF')
            .backgroundColor(this.accentColor())
            .borderRadius(Theme.Radius.l)
            .shadow({ radius: 16, color: this.accentColor(), offsetY: 4, offsetX: 0 })
            .onClick(() => {
              try { router.pushUrl({ url: 'pages/QuickDecisionInput' }) }
              catch (e) { this.navigateBack() }
            })
          Button('再玩一次')
            .width('100%').height(44).fontSize(14).fontWeight(600)
            .fontColor(Theme.Color.TextSecondary)
            .backgroundColor(Theme.Color.BackgroundSecondary)
            .borderRadius(Theme.Radius.l)
            .border({ width: 1, color: Theme.Color.BorderLight })
            .onClick(() => { this.phase = 'intro' })
        }
        .width('100%')

        // 版本信息
        Text('ParaLife v1.0.0')
          .fontSize(12).fontColor(Theme.Color.TextTertiary)
          .width('100%').textAlign(TextAlign.Center)

        Column().height(40)
      }
      .padding({ left: 16, right: 16, bottom: 60 })
    }
    .scrollBar(BarState.Off).edgeEffect(EdgeEffect.Spring).layoutWeight(1)
  }

  @Builder
  FinalStatItem(label: string, val: number, iconName: string) {
    Column({ space: 8 }) {
      Stack() {
        Circle({ width: 40, height: 40 }).fill(this.statColor(val)).opacity(0.15)
        SimpleIcon({ iconName: iconName, iconSize: 20, color: this.statColor(val) })
      }.width(40).height(40)
      Text(`${val}`).fontSize(20).fontWeight(700).fontColor(this.statColor(val))
      Text(label).fontSize(12).fontColor(Theme.Color.TextTertiary)
    }
    .layoutWeight(1).padding(16)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .alignItems(HorizontalAlign.Center)
  }
}
