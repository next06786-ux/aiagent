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
import { getFutureOSService } from '../service/FutureOSService'
import router from '@ohos.router'

interface StatDelta { emotion: number; finance: number; social: number; health: number; growth: number; confidence: number; stress: number }

interface Stats { emotion: number; finance: number; social: number; health: number; growth: number; confidence: number; stress: number }

interface StatLabel { k: string; l: string }

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

@Entry
@Component
struct ParallelLifeGame {
  // ── 状态 ──────────────────────────────────────────────────────────────
  @State phase: string = 'loading'
  @State chapters: Chapter[] = []
  @State currentChapter: Chapter | null = null
  @State currentNodeId: string = ''
  @State stats: Stats = { emotion: 50, finance: 50, social: 50, health: 50, growth: 50, confidence: 50, stress: 30 }
  @State lastDelta: StatDelta = { emotion: 0, finance: 0, social: 0, health: 0, growth: 0, confidence: 0, stress: 0 }
  @State showDelta: boolean = false
  @State choices: ChoiceRecord[] = []
  @State ending: Record<string, string> = {}
  @State finalStats: Stats = { emotion: 50, finance: 50, social: 50, health: 50, growth: 50, confidence: 50, stress: 30 }
  @State freeInputText: string = ''
  @State reflectionText: string = ''
  @State showContent: boolean = false
  @State sourceMode: string = 'legacy'
  @State resultHint: string = ''
  @State currentScenarioId: string = ''
  @State currentSimulationId: string = ''
  @State currentBranchId: string = ''
  @State sourceQuestion: string = ''

  // 塔罗牌抽卡动画状态
  @State tarotDrawn: boolean = false          // 是否已抽牌
  @State tarotSelectedIdx: number = -1        // 选中的牌索引
  @State tarotFlipped: boolean = false        // 是否已翻转
  @State tarotCardScales: number[] = []       // 每张牌的缩放
  @State tarotCardOpacities: number[] = []    // 每张牌的透明度
  @State tarotSelectedY: number = 0           // 选中牌的Y偏移
  @State tarotSelectedScale: number = 1       // 选中牌的放大
  @State tarotRotateY: number = 0             // 翻转角度 0=背面 180=正面
  @State tarotGlowOpacity: number = 0         // 光效透明度

  // 动效
  @State nodeOpacity: number = 0
  @State nodeTranslateY: number = 30
  @State resultOpacity: number = 0
  @State statBarEmotion: number = 50
  @State statBarFinance: number = 50
  @State statBarSocial: number = 50
  @State statBarHealth: number = 50
  @State statBarGrowth: number = 50
  @State statBarConfidence: number = 50
  @State statBarStress: number = 30

  // 倒计时
  @State countdown: number = 15
  @State countdownActive: boolean = false
  private countdownTimer: number = -1
  private nodeStartTime: number = 0

  private authService = getAuthService()
  private futureOSService = getFutureOSService()

  aboutToAppear() {
    const params = router.getParams() as Record<string, string>
    if (params?.simulationId && params?.branchId) {
      this.loadFutureScenario(params.simulationId, params.branchId, params.sourceQuestion ?? '')
    } else {
      this.loadChapters()
    }
    setTimeout(() => { this.showContent = true }, 50)
  }
  aboutToDisappear() { this.stopCountdown() }

  private resetFutureScenarioMeta() {
    this.sourceMode = 'legacy'
    this.resultHint = ''
    this.currentScenarioId = ''
    this.currentSimulationId = ''
    this.currentBranchId = ''
    this.sourceQuestion = ''
    this.reflectionText = ''
  }

  private isFutureScenario(): boolean {
    return this.sourceMode === 'future_os' && this.currentScenarioId.length > 0
  }

  private toChapter(payload: Record<string, Object>): Chapter {
    return {
      id: String(payload['scenario_id'] ?? payload['id'] ?? ''),
      title: String(payload['title'] ?? '平行人生分支体验'),
      subtitle: String(payload['subtitle'] ?? ''),
      theme: String(payload['theme'] ?? '#0b1830'),
      accent: String(payload['accent'] ?? '#5AA9FF'),
      cover_emoji: String(payload['cover_emoji'] ?? '◎'),
      intro: String(payload['intro'] ?? ''),
      nodes: (payload['nodes'] as unknown as GameNode[]) ?? [],
      endings: (payload['endings'] as unknown as Ending[]) ?? []
    }
  }

  async loadFutureScenario(simulationId: string, branchId: string, sourceQuestion: string) {
    try {
      this.phase = 'loading'
      const userId = this.authService.getCurrentUserId()
      const scenario = await this.futureOSService.createParallelLifeBranch(userId, simulationId, branchId) as Record<string, Object>
      this.currentChapter = this.toChapter(scenario)
      this.sourceMode = 'future_os'
      this.currentScenarioId = String(scenario['scenario_id'] ?? '')
      this.currentSimulationId = String(scenario['simulation_id'] ?? simulationId)
      this.currentBranchId = String(scenario['branch_id'] ?? branchId)
      this.sourceQuestion = sourceQuestion || String(scenario['source_question'] ?? '')
      this.resultHint = ''
      this.phase = 'intro'
    } catch (e) {
      console.error('加载 Future OS 分支体验失败:', e)
      this.resetFutureScenarioMeta()
      this.loadChapters()
    }
  }

  // ── 数据加载 ──────────────────────────────────────────────────────────
  async loadChapters() {
    try {
      this.resetFutureScenarioMeta()
      const req = http.createHttp()
      const res = await req.request(`${ApiConfig.getBaseUrl()}/api/game/parallel-life/chapters`,
        { method: http.RequestMethod.GET })
      req.destroy()
      if (res.responseCode === 200) {
        const body = JSON.parse(res.result as string) as Record<string, Object>
        this.chapters = body['data'] as Chapter[]
        if (this.chapters.length > 0) {
          this.initTarotCards()
          this.phase = 'chapters'
        }
      }
    } catch (e) { console.error('加载关卡失败:', e) }
  }

  async loadChapter(chapterId: string) {
    try {
      this.resetFutureScenarioMeta()
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
      this.resetFutureScenarioMeta()
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
    this.stats = { emotion: 50, finance: 50, social: 50, health: 50, growth: 50, confidence: 50, stress: 30 }
    this.statBarEmotion = 50; this.statBarFinance = 50; this.statBarSocial = 50
    this.statBarHealth = 50; this.statBarGrowth = 50; this.statBarConfidence = 50; this.statBarStress = 30
    this.choices = []
    this.freeInputText = ''
    this.reflectionText = ''
    this.resultHint = ''
    this.currentNodeId = ch.nodes[0].id
    this.phase = 'playing'
    this.animateNodeIn()
    if (ch.nodes[0].type !== 'free_input') {
      this.startCountdown()
    }
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
    const newEmotion = Math.max(-100, Math.min(100, this.stats.emotion + (opt.delta.emotion || 0)))
    const newFinance = Math.max(-100, Math.min(100, this.stats.finance + (opt.delta.finance || 0)))
    const newSocial  = Math.max(-100, Math.min(100, this.stats.social  + (opt.delta.social || 0)))
    const newHealth  = Math.max(-100, Math.min(100, this.stats.health  + (opt.delta.health || 0)))
    const newGrowth  = Math.max(-100, Math.min(100, this.stats.growth  + (opt.delta.growth || 0)))
    const newConf    = Math.max(-100, Math.min(100, this.stats.confidence + (opt.delta.confidence || 0)))
    const newStress  = Math.max(-100, Math.min(100, this.stats.stress  + (opt.delta.stress || 0)))
    this.stats = { emotion: newEmotion, finance: newFinance, social: newSocial, health: newHealth, growth: newGrowth, confidence: newConf, stress: newStress }
    animateTo({ duration: 600, curve: Curve.Smooth }, () => {
      this.statBarEmotion = newEmotion
      this.statBarFinance = newFinance
      this.statBarSocial  = newSocial
      this.statBarHealth  = newHealth
      this.statBarGrowth  = newGrowth
      this.statBarConfidence = newConf
      this.statBarStress  = newStress
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
    this.reflectionText = text
    this.choices.push({ node_id: this.currentNodeId, option_id: 'free', choice_time_ms: Date.now() - this.nodeStartTime })
    if (!this.isFutureScenario()) {
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
    }
    this.freeInputText = ''
    const nextId = node.next ?? 'ending'
    if (nextId === 'ending') { this.finishGame() }
    else { this.currentNodeId = nextId; this.animateNodeIn(); this.startCountdown() }
  }

  async finishGame() {
    const ch = this.currentChapter
    if (!ch) return
    this.finalStats = { emotion: this.stats.emotion, finance: this.stats.finance, social: this.stats.social, health: this.stats.health, growth: this.stats.growth, confidence: this.stats.confidence, stress: this.stats.stress }
    if (this.isFutureScenario()) {
      const fallbackEnding = ch.endings[0] ?? { condition: 'fallback', title: '分支体验完成', text: '你已经完成这条分支体验。', badge: '已完成' }
      const balancedEnding = ch.endings[1] ?? fallbackEnding
      this.ending = (this.finalStats.growth >= 60 && this.finalStats.confidence >= 60 && this.finalStats.stress <= 55)
        ? fallbackEnding as unknown as Record<string, string>
        : balancedEnding as unknown as Record<string, string>

      try {
        const userId = this.authService.getCurrentUserId()
        const payload = await this.futureOSService.completeParallelLife({
          user_id: userId,
          scenario_id: this.currentScenarioId,
          simulation_id: this.currentSimulationId,
          branch_id: this.currentBranchId,
          final_stats: this.finalStats,
          choices: this.choices,
          emotion_feedback: '',
          free_text: this.reflectionText
        }) as Record<string, Object>

        this.resultHint = String(payload['next_hint'] ?? '')
      } catch (e) {
        console.error('提交 Future OS 分支体验结果失败:', e)
      }
    } else {
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
    }
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
    this.showContent = false
    setTimeout(() => { animateTo({ duration: 400, curve: Curve.Smooth }, () => { this.nodeOpacity = 1; this.nodeTranslateY = 0 }) }, 100)
    setTimeout(() => { this.showContent = true }, 300)
  }

  statColor(val: number): string {
    if (val >= 60) return '#00C853'
    if (val >= 30) return '#FF9500'
    return '#FF3B30'
  }
  deltaText(v: number): string { return v > 0 ? `+${v}` : `${v}` }
  accentColor(): string { return this.currentChapter?.accent ?? '#6B48FF' }

  // 获取 delta 中某个维度的值
  getDeltaVal(delta: StatDelta, key: string): number {
    if (key === 'emotion') return delta.emotion
    if (key === 'finance') return delta.finance
    if (key === 'social') return delta.social
    if (key === 'health') return delta.health
    if (key === 'growth') return delta.growth
    if (key === 'confidence') return delta.confidence
    if (key === 'stress') return delta.stress
    return 0
  }

  private statLabels: StatLabel[] = [
    { k: 'emotion', l: '情绪' }, { k: 'finance', l: '财务' }, { k: 'social', l: '社交' },
    { k: 'health', l: '健康' }, { k: 'growth', l: '成长' }, { k: 'confidence', l: '自信' }, { k: 'stress', l: '压力' }
  ]

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
          Column({ space: 6 }) {
            this.StatBar('情绪', this.statBarEmotion, 'heart')
            this.StatBar('财务', this.statBarFinance, 'chart')
            this.StatBar('社交', this.statBarSocial, 'user')
            this.StatBar('健康', this.statBarHealth, 'shield')
            this.StatBar('成长', this.statBarGrowth, 'learning')
            this.StatBar('自信', this.statBarConfidence, 'brain')
            this.StatBar('压力', this.statBarStress, 'alert')
          }
          .width('100%').padding({ left: 16, right: 16, top: 6, bottom: 10 })
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .border({ width: { bottom: 0.5 }, color: Theme.Color.BorderLight })
        }

        // 属性变化浮层
        if (this.showDelta) {
          Scroll() {
            Row({ space: 8 }) {
              ForEach(
                this.statLabels.filter((d: StatLabel) => this.getDeltaVal(this.lastDelta, d.k) !== 0),
                (d: StatLabel) => {
                  Text(`${d.l}${this.deltaText(this.getDeltaVal(this.lastDelta, d.k))}`)
                    .fontSize(12).fontWeight(600)
                    .fontColor(this.getDeltaVal(this.lastDelta, d.k) > 0 ? Theme.Color.Accent : Theme.Color.Destructive)
                    .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                    .backgroundColor(this.getDeltaVal(this.lastDelta, d.k) > 0 ? 'rgba(0,200,83,0.08)' : 'rgba(255,59,48,0.08)')
                    .borderRadius(Theme.Radius.round)
                }
              )
            }
          }.scrollable(ScrollDirection.Horizontal).scrollBar(BarState.Off)
          .width('100%').padding(6)
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

  // 初始化塔罗牌状态
  private initTarotCards() {
    const count = this.chapters.length
    this.tarotCardScales = new Array(count).fill(1)
    this.tarotCardOpacities = new Array(count).fill(1)
    this.tarotDrawn = false
    this.tarotSelectedIdx = -1
    this.tarotFlipped = false
    this.tarotSelectedY = 0
    this.tarotSelectedScale = 1
    this.tarotRotateY = 0
    this.tarotGlowOpacity = 0
  }

  // 抽牌动画序列 — 所有牌都走 AI 生成
  private drawTarotCard(index: number) {
    if (this.tarotDrawn) return
    this.tarotDrawn = true
    this.tarotSelectedIdx = index

    const newScales = [...this.tarotCardScales]
    const newOpacities = [...this.tarotCardOpacities]
    for (let i = 0; i < this.chapters.length; i++) {
      if (i !== index) { newScales[i] = 0.8; newOpacities[i] = 0 }
    }
    animateTo({ duration: 400, curve: Curve.Smooth }, () => {
      this.tarotCardScales = newScales
      this.tarotCardOpacities = newOpacities
    })

    setTimeout(() => {
      animateTo({ duration: 500, curve: Curve.Smooth }, () => {
        this.tarotSelectedY = -120
        this.tarotSelectedScale = 1.3
      })
    }, 350)

    setTimeout(() => {
      animateTo({ duration: 600, curve: Curve.Smooth }, () => {
        this.tarotRotateY = 180
        this.tarotGlowOpacity = 0.6
      })
    }, 900)

    setTimeout(() => {
      this.tarotFlipped = true
      animateTo({ duration: 400, curve: Curve.Smooth }, () => { this.tarotGlowOpacity = 0 })
    }, 1500)

    // 调用 AI 生成关卡（和动画并行）
    this.generateAndLoadChapter(index)
  }

  private async generateAndLoadChapter(fallbackIndex: number) {
    try {
      const req = http.createHttp()
      const res = await req.request(`${ApiConfig.getBaseUrl()}/api/game/parallel-life/generate`,
        { method: http.RequestMethod.GET, connectTimeout: 30000, readTimeout: 30000 })
      req.destroy()
      if (res.responseCode === 200) {
        const body = JSON.parse(res.result as string) as Record<string, Object>
        if (body['success']) {
          this.currentChapter = body['data'] as Chapter
          setTimeout(() => { this.phase = 'intro' }, 2500)
          return
        }
      }
    } catch (e) {
      console.error('AI生成关卡失败:', e)
    }
    // 降级到预设关卡
    setTimeout(() => {
      if (fallbackIndex < this.chapters.length) {
        this.loadChapter(this.chapters[fallbackIndex].id)
      } else {
        this.loadRandomChapter()
      }
    }, 2500)
  }

  // 随机抽牌 — 调用大模型生成全新关卡
  private async drawRandomTarot() {
    if (this.chapters.length === 0) return
    // 先播放随机选牌动画
    const idx = Math.floor(Math.random() * this.chapters.length)
    this.tarotDrawn = true
    this.tarotSelectedIdx = idx

    // 动画：其他牌淡出
    const newScales = [...this.tarotCardScales]
    const newOpacities = [...this.tarotCardOpacities]
    for (let i = 0; i < this.chapters.length; i++) {
      if (i !== idx) { newScales[i] = 0.8; newOpacities[i] = 0 }
    }
    animateTo({ duration: 400, curve: Curve.Smooth }, () => {
      this.tarotCardScales = newScales
      this.tarotCardOpacities = newOpacities
    })

    // 选中牌上移
    setTimeout(() => {
      animateTo({ duration: 500, curve: Curve.Smooth }, () => {
        this.tarotSelectedY = -120
        this.tarotSelectedScale = 1.3
      })
    }, 350)

    // 翻转
    setTimeout(() => {
      animateTo({ duration: 600, curve: Curve.Smooth }, () => {
        this.tarotRotateY = 180
        this.tarotGlowOpacity = 0.6
      })
    }, 900)

    setTimeout(() => {
      this.tarotFlipped = true
      animateTo({ duration: 400, curve: Curve.Smooth }, () => { this.tarotGlowOpacity = 0 })
    }, 1500)

    // 调用 AI 生成关卡（和动画并行）
    try {
      const req = http.createHttp()
      const res = await req.request(`${ApiConfig.getBaseUrl()}/api/game/parallel-life/generate`,
        { method: http.RequestMethod.GET, connectTimeout: 30000, readTimeout: 30000 })
      req.destroy()
      if (res.responseCode === 200) {
        const body = JSON.parse(res.result as string) as Record<string, Object>
        if (body['success']) {
          this.currentChapter = body['data'] as Chapter
          // 等动画播完再跳转
          setTimeout(() => { this.phase = 'intro' }, 2500)
          return
        }
      }
    } catch (e) {
      console.error('AI生成关卡失败，使用预设关卡:', e)
    }
    // 降级：使用预设关卡
    setTimeout(() => { this.loadRandomChapter() }, 2500)
  }

  @Builder buildChapterSelect() {
    Column() {
      // 深色神秘背景
      Stack() {
        Column().width('100%').height('100%')
          .linearGradient({ angle: 180, colors: [['#0a0a1a', 0], ['#1a1a2e', 0.4], ['#16213e', 1]] })

        // 星空粒子装饰
        Circle({ width: 3, height: 3 }).fill('#FFFFFF').opacity(0.3)
          .position({ x: '15%', y: '10%' })
        Circle({ width: 2, height: 2 }).fill('#FFFFFF').opacity(0.2)
          .position({ x: '75%', y: '15%' })
        Circle({ width: 2, height: 2 }).fill('#FFFFFF').opacity(0.25)
          .position({ x: '45%', y: '8%' })
        Circle({ width: 3, height: 3 }).fill('#FFFFFF').opacity(0.15)
          .position({ x: '85%', y: '25%' })

        Column({ space: 0 }) {
          // 标题区
          Column({ space: 8 }) {
            Text('命运之牌').fontSize(28).fontWeight(800).fontColor('#FFFFFF')
              .opacity(this.tarotDrawn ? 0.3 : 1)
              .animation({ duration: 400, curve: Curve.Smooth })
            Text(this.tarotDrawn ? '命运已定...' : '选择一张牌，揭示你的平行旅程')
              .fontSize(14).fontColor('rgba(255,255,255,0.5)')
              .animation({ duration: 400, curve: Curve.Smooth })
          }
          .width('100%').alignItems(HorizontalAlign.Center)
          .padding({ top: 20, bottom: 24 })

          // 抽牌光效
          if (this.tarotGlowOpacity > 0) {
            Circle({ width: 200, height: 200 })
              .fill('#6B48FF')
              .opacity(this.tarotGlowOpacity * 0.15)
              .blur(60)
              .position({ x: '50%', y: '40%' })
              .translate({ x: -100, y: -100 })
          }

          // 塔罗牌区域
          if (!this.tarotDrawn) {
            // 未抽牌：扇形排列的牌背
            Column({ space: 16 }) {
              // 牌组 - 水平排列，微微扇形
              Row({ space: -20 }) {
                ForEach(this.chapters, (ch: Chapter, index: number) => {
                  this.TarotCardBack(ch, index)
                })
              }
              .width('100%')
              .justifyContent(FlexAlign.Center)
              .padding({ left: 20, right: 20 })

              // 随机抽牌按钮
              Button('随机抽取')
                .width(160).height(44).fontSize(15).fontWeight(600).fontColor('#FFFFFF')
                .backgroundColor('transparent')
                .border({ width: 1, color: 'rgba(107,72,255,0.4)' })
                .borderRadius(Theme.Radius.round)
                .onClick(() => this.drawRandomTarot())
                .margin({ top: 20 })

              Text('或点击任意一张牌').fontSize(12).fontColor('rgba(255,255,255,0.3)')
            }
            .layoutWeight(1)
            .justifyContent(FlexAlign.Center)
            .alignItems(HorizontalAlign.Center)
          } else {
            // 已抽牌：显示选中的牌
            Column() {
              Blank().layoutWeight(1)
              if (this.tarotSelectedIdx >= 0 && this.tarotSelectedIdx < this.chapters.length) {
                this.TarotCardDrawn(this.chapters[this.tarotSelectedIdx])
              }
              Blank().layoutWeight(1)

              if (this.tarotFlipped) {
                Text('即将进入关卡...')
                  .fontSize(14).fontColor('rgba(255,255,255,0.4)')
                  .margin({ bottom: 40 })
              }
            }
            .layoutWeight(1)
            .alignItems(HorizontalAlign.Center)
          }
        }
        .width('100%').height('100%')
      }
      .width('100%').layoutWeight(1)
    }
    .width('100%').layoutWeight(1)
  }

  // 牌背（未翻转）
  @Builder
  TarotCardBack(ch: Chapter, index: number) {
    Stack() {
      // 牌背主体
      Column()
        .width(75).height(110)
        .linearGradient({ angle: 180, colors: [['#2a1a4e', 0], ['#1a0a3e', 1]] })
        .borderRadius(8)
        .border({ width: 1.5, color: 'rgba(107,72,255,0.3)' })
        .shadow({ radius: 8, color: 'rgba(107,72,255,0.2)', offsetX: 0, offsetY: 4 })

      // 牌背花纹 - 内框
      Column()
        .width(63).height(98)
        .border({ width: 0.5, color: 'rgba(255,255,255,0.08)' })
        .borderRadius(5)

      // 牌背中心图案
      Column()
        .width(30).height(30)
        .border({ width: 0.5, color: 'rgba(107,72,255,0.25)' })
        .borderRadius(15)
        .rotate({ angle: 45 })

      // 牌背中心点
      Circle({ width: 8, height: 8 })
        .fill('#6B48FF').opacity(0.4)
    }
    .width(75).height(110)
    .scale({ x: this.tarotCardScales[index] || 1, y: this.tarotCardScales[index] || 1 })
    .opacity(this.tarotCardOpacities[index] ?? 1)
    .rotate({ angle: (index - Math.floor(this.chapters.length / 2)) * 6 })
    .animation({ duration: 400, curve: Curve.Smooth })
    .onClick(() => this.drawTarotCard(index))
    .stateStyles({
      pressed: { .translate({ y: -8 }).scale({ x: 1.05, y: 1.05 }) },
      normal: { .translate({ y: 0 }).scale({ x: this.tarotCardScales[index] || 1, y: this.tarotCardScales[index] || 1 }) }
    })
  }

  // 抽出的牌（翻转动画）
  @Builder
  TarotCardDrawn(ch: Chapter) {
    Stack() {
      // 牌背面（rotateY 0-90 可见）
      if (this.tarotRotateY < 90) {
        Stack() {
          Column()
            .width(140).height(210)
            .linearGradient({ angle: 180, colors: [['#2a1a4e', 0], ['#1a0a3e', 1]] })
            .borderRadius(12)
            .border({ width: 2, color: 'rgba(107,72,255,0.4)' })
          Column()
            .width(120).height(190)
            .border({ width: 0.5, color: 'rgba(255,255,255,0.1)' })
            .borderRadius(9)
          Column()
            .width(50).height(50)
            .border({ width: 0.5, color: 'rgba(107,72,255,0.3)' })
            .borderRadius(25)
            .rotate({ angle: 45 })
          Circle({ width: 14, height: 14 }).fill('#6B48FF').opacity(0.5)
        }.width(140).height(210)
      }

      // 牌正面（rotateY 90-180 可见）— 需要镜像翻转文字才正
      if (this.tarotRotateY >= 90) {
        Stack() {
          Column()
            .width(140).height(210)
            .linearGradient({ angle: 180, colors: [[ch.accent || '#6B48FF', 0], ['#1a1a2e', 1]] })
            .borderRadius(12)
            .border({ width: 2, color: 'rgba(255,255,255,0.2)' })
            .shadow({ radius: 16, color: `${ch.accent || '#6B48FF'}44`, offsetX: 0, offsetY: 8 })
          Column()
            .width(120).height(190)
            .border({ width: 0.5, color: 'rgba(255,255,255,0.12)' })
            .borderRadius(9)
          Column({ space: 8 }) {
            Text(ch.cover_emoji || '').fontSize(36)
            Text(ch.title).fontSize(16).fontWeight(700).fontColor('#FFFFFF').textAlign(TextAlign.Center)
            Text(ch.subtitle).fontSize(12).fontColor('rgba(255,255,255,0.6)').textAlign(TextAlign.Center)
          }.justifyContent(FlexAlign.Center)
          .scale({ x: -1 })  // 镜像翻转，抵消 rotateY 的镜像效果
        }.width(140).height(210)
      }
    }
    .width(140).height(210)
    .translate({ y: this.tarotSelectedY })
    .scale({ x: this.tarotSelectedScale, y: this.tarotSelectedScale })
    .rotate({ y: 1, angle: this.tarotRotateY })
    .animation({ duration: 500, curve: Curve.Smooth })
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

          if (this.isFutureScenario()) {
            Column({ space: 10 }) {
              Text('来自决策图谱舞台').fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
              Text(this.sourceQuestion || '这是一条从当前推演分支注入的平行人生体验。')
                .fontSize(14).fontColor(Theme.Color.TextSecondary).lineHeight(22)
            }
            .width('100%').padding(20)
            .backgroundColor(Theme.Color.BackgroundSecondary)
            .borderRadius(Theme.Radius.l)
            .border({ width: 1, color: Theme.Color.BorderLight })
            .shadow(Theme.Shadow.Soft)
          }

          // 属性说明
          Flex({ wrap: FlexWrap.Wrap, justifyContent: FlexAlign.SpaceBetween }) {
            this.buildStatPreview('情绪', 'heart', '#00C853')
            this.buildStatPreview('财务', 'chart', '#FF9500')
            this.buildStatPreview('社交', 'user', '#0A59F7')
            this.buildStatPreview('健康', 'shield', '#E91E63')
            this.buildStatPreview('成长', 'learning', '#6B48FF')
            this.buildStatPreview('自信', 'brain', '#009688')
            this.buildStatPreview('压力', 'alert', '#FF3B30')
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
        Button(this.isFutureScenario() ? '开始分支体验' : '开始游戏')
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
    Column({ space: 6 }) {
      Stack() {
        Circle({ width: 32, height: 32 }).fill(color).opacity(0.15)
        SimpleIcon({ iconName: iconName, iconSize: 16, color: color })
      }.width(32).height(32)
      Text(label).fontSize(11).fontColor(Theme.Color.TextTertiary)
    }
    .width('30%').padding(10).margin({ bottom: 8 })
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
                    // 属性预览标签 — 显示所有非零维度
                    Scroll() {
                      Row({ space: 6 }) {
                        ForEach(
                          this.statLabels.filter((d: StatLabel) => this.getDeltaVal(opt.delta, d.k) !== 0),
                          (d: StatLabel) => {
                            Text(`${d.l}${this.deltaText(this.getDeltaVal(opt.delta, d.k))}`)
                              .fontSize(10).fontColor(this.getDeltaVal(opt.delta, d.k) > 0 ? Theme.Color.Accent : Theme.Color.Destructive)
                              .padding({ left: 5, right: 5, top: 2, bottom: 2 })
                              .backgroundColor(this.getDeltaVal(opt.delta, d.k) > 0 ? 'rgba(0,200,83,0.08)' : 'rgba(255,59,48,0.08)')
                              .borderRadius(Theme.Radius.round)
                          }
                        )
                      }
                    }.scrollable(ScrollDirection.Horizontal).scrollBar(BarState.Off).margin({ top: 4 })
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
                .opacity(this.showContent ? 1 : 0)
                .translate({ x: this.showContent ? 0 : -30 })
                .animation({ duration: 400, curve: Curve.Smooth, delay: 100 + idx * 80 })
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

        // 最终属性
        Flex({ wrap: FlexWrap.Wrap, justifyContent: FlexAlign.SpaceBetween }) {
          this.FinalStatItem('情绪', this.finalStats.emotion, 'heart')
          this.FinalStatItem('财务', this.finalStats.finance, 'chart')
          this.FinalStatItem('社交', this.finalStats.social, 'user')
          this.FinalStatItem('健康', this.finalStats.health, 'shield')
          this.FinalStatItem('成长', this.finalStats.growth, 'learning')
          this.FinalStatItem('自信', this.finalStats.confidence, 'brain')
          this.FinalStatItem('压力', this.finalStats.stress, 'alert')
        }.width('100%')
        .opacity(this.resultOpacity)
        .animation({ duration: 700, curve: Curve.Smooth })

        // 选择统计
        Column({ space: 8 }) {
          Text(`共做了 ${this.choices.length} 次选择`)
            .fontSize(14).fontColor(Theme.Color.TextSecondary)
          Text(this.isFutureScenario()
            ? '你的选择已回写到 Future OS 的决策画像与知识星图。'
            : '你的选择已用于优化后续决策体验。')
            .fontSize(12).fontColor(Theme.Color.TextTertiary)
        }
        .width('100%').padding(16)
        .backgroundColor(Theme.Color.BackgroundSecondary)
        .borderRadius(Theme.Radius.l)
        .border({ width: 1, color: Theme.Color.BorderLight })
        .alignItems(HorizontalAlign.Center)

        if (this.resultHint) {
          Column({ space: 8 }) {
            Text('下一步建议')
              .fontSize(16)
              .fontWeight(600)
              .fontColor(Theme.Color.TextPrimary)
            Text(this.resultHint)
              .fontSize(14)
              .fontColor(Theme.Color.TextSecondary)
              .lineHeight(22)
          }
          .width('100%').padding(16)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l)
          .border({ width: 1, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)
        }

        // 操作按钮
        Column({ space: 12 }) {
          Button(this.isFutureScenario() ? '返回推演详情' : '进入决策副本')
            .width('100%').height(52).fontSize(16).fontWeight(600).fontColor('#FFFFFF')
            .backgroundColor(this.accentColor())
            .borderRadius(Theme.Radius.l)
            .shadow({ radius: 16, color: this.accentColor(), offsetY: 4, offsetX: 0 })
            .onClick(() => {
              if (this.isFutureScenario()) {
                this.navigateBack()
              } else {
                try { router.pushUrl({ url: 'pages/EnhancedDecisionFlow' }) }
                catch (e) { this.navigateBack() }
              }
            })
          Button(this.isFutureScenario() ? '重新体验该分支' : '再玩一次')
            .width('100%').height(44).fontSize(14).fontWeight(600)
            .fontColor(Theme.Color.TextSecondary)
            .backgroundColor(Theme.Color.BackgroundSecondary)
            .borderRadius(Theme.Radius.l)
            .border({ width: 1, color: Theme.Color.BorderLight })
            .onClick(() => { this.phase = 'intro'; this.resultHint = '' })
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
    Column({ space: 6 }) {
      Stack() {
        Circle({ width: 36, height: 36 }).fill(this.statColor(val)).opacity(0.15)
        SimpleIcon({ iconName: iconName, iconSize: 16, color: this.statColor(val) })
      }.width(36).height(36)
      Text(`${val}`).fontSize(18).fontWeight(700).fontColor(this.statColor(val))
      Text(label).fontSize(11).fontColor(Theme.Color.TextTertiary)
    }
    .width('30%').padding(12).margin({ bottom: 10 })
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .alignItems(HorizontalAlign.Center)
  }
}
