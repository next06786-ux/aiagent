/**
 *  - HarmonyOS 6 
 *  vs AI
 */
import router from '@ohos.router'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'

interface ApiResponse<T> {
  success: boolean
  data: T
}

class ComparisonData {
  total_decisions: number = 0
  user_success_rate: number = 0
  ai_would_success_rate: number = 0
  alignment_rate: number = 0
  average_outcome_score: number = 0
  domain_stats: Record<string, DomainStat> = {}
}

class DomainStat {
  count: number = 0
  success_rate: number = 0
  alignment_rate: number = 0
}

class PendingDecision {
  id: string = ''
  domain: string = ''
  situation: string = ''
  user_decision: string = ''
  ai_recommendation: string = ''
  timestamp: string = ''
}

class RecentDecision {
  id: string = ''
  domain: string = ''
  situation: string = ''
  user_decision: string = ''
  ai_recommendation: string = ''
  is_aligned: boolean = false
  ai_confidence: number = 0
  timestamp: string = ''
}

@Entry
@Component
struct DecisionComparison {
  @State comparisonData: ComparisonData = new ComparisonData()
  @State pendingDecisions: PendingDecision[] = []
  @State recentDecisions: RecentDecision[] = []
  @State isLoading: boolean = true
  @State selectedDays: number = 30
  @State showRecordDialog: boolean = false
  @State showContent: boolean = false
  private userId: string = 'default_user'

  aboutToAppear() {
    this.loadComparisonData()
    this.loadPendingDecisions()
    this.loadRecentDecisions()
    setTimeout(() => {
      this.showContent = true
    }, 100)
  }

  async loadComparisonData() {
    this.isLoading = true

    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/v4/decision/compare/${this.userId}?days=${this.selectedDays}`,
        {
          method: http.RequestMethod.GET
        }
      )

      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as ApiResponse<ComparisonData>
        if (result.success) {
          this.comparisonData = result.data
        }
      } else {
        // Mock data
        this.mockData()
      }
    } catch (error) {
      console.error('Failed to load comparison data:', error)
      this.mockData()
    }

    this.isLoading = false
  }

  mockData() {
    this.comparisonData = {
      total_decisions: 42,
      user_success_rate: 0.78,
      ai_would_success_rate: 0.85,
      alignment_rate: 0.65,
      average_outcome_score: 8.2,
      domain_stats: {
        'health': { count: 15, success_rate: 0.8, alignment_rate: 0.7 },
        'time': { count: 12, success_rate: 0.75, alignment_rate: 0.6 },
        'finance': { count: 8, success_rate: 0.85, alignment_rate: 0.8 }
      }
    }
  }

  async loadPendingDecisions() {
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/v4/decision/pending/${this.userId}`,
        {
          method: http.RequestMethod.GET
        }
      )

      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as ApiResponse<PendingDecision[]>
        if (result.success) {
          this.pendingDecisions = result.data
        }
      } else {
        this.pendingDecisions = [
          {
            id: '1',
            domain: 'health',
            situation: '',
            user_decision: '',
            ai_recommendation: '20',
            timestamp: new Date().toISOString()
          }
        ]
      }
    } catch (error) {
      console.error('Failed to load pending decisions:', error)
      this.pendingDecisions = [
        {
          id: '1',
          domain: 'health',
          situation: '',
          user_decision: '',
          ai_recommendation: '20',
          timestamp: new Date().toISOString()
        }
      ]
    }
  }

  async loadRecentDecisions() {
    try {
      const httpRequest = http.createHttp()
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/v4/decision/recent/${this.userId}?limit=5`,
        {
          method: http.RequestMethod.GET
        }
      )

      httpRequest.destroy()

      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as ApiResponse<RecentDecision[]>
        if (result.success) {
          this.recentDecisions = result.data
        }
      } else {
        this.recentDecisions = [
          {
            id: '101',
            domain: 'finance',
            situation: '',
            user_decision: '',
            ai_recommendation: '',
            is_aligned: false,
            ai_confidence: 0.88,
            timestamp: new Date(Date.now() - 86400000).toISOString()
          },
          {
            id: '102',
            domain: 'time',
            situation: '',
            user_decision: '',
            ai_recommendation: '',
            is_aligned: true,
            ai_confidence: 0.92,
            timestamp: new Date(Date.now() - 172800000).toISOString()
          }
        ]
      }
    } catch (error) {
      console.error('Failed to load recent decisions:', error)
      this.recentDecisions = [
        {
          id: '101',
          domain: 'finance',
          situation: '',
          user_decision: '',
          ai_recommendation: '',
          is_aligned: false,
          ai_confidence: 0.88,
          timestamp: new Date(Date.now() - 86400000).toISOString()
        },
        {
          id: '102',
          domain: 'time',
          situation: '',
          user_decision: '',
          ai_recommendation: '',
          is_aligned: true,
          ai_confidence: 0.92,
          timestamp: new Date(Date.now() - 172800000).toISOString()
        }
      ]
    }
  }

  build() {
    Stack() {
      // 1. 
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('#F1F3F5')
        
      // 处理逻辑
      Circle({ width: 300, height: 300 })
        .fill('rgba(168, 230, 207, 0.1)')
        .blur(60)
        .position({ x: -50, y: -50 })
        
      Circle({ width: 250, height: 250 })
        .fill('rgba(255, 211, 182, 0.1)')
        .blur(50)
        .position({ x: '80%', y: '80%' })

      Column() {
        // 2. 
        Row() {
          Row({ space: 12 }) {
            Button({ type: ButtonType.Circle, stateEffect: true }) {
              Text('←')
                .fontSize(24)
                .fontColor('#1A1A1A')
                .fontWeight(600)
            }
            .width(40)
            .height(40)
            .backgroundColor('rgba(255, 255, 255, 0.0)')
            .onClick(() => {
              router.back()
            })

            Column({ space: 2 }) {
              Text('')
                .fontSize(20)
                .fontWeight(700)
                .fontColor('#1A1A1A')
              
              Text(' · ')
                .fontSize(12)
                .fontColor('#666666')
            }
            .alignItems(HorizontalAlign.Start)
          }

          Blank()

          // 处理逻辑
          Row() {
            Text(`${this.selectedDays}`)
              .fontSize(14)
              .fontColor('#007AFF')
              .fontWeight(600)
          }
          .padding({ left: 16, right: 16, top: 8, bottom: 8 })
          .backgroundColor('rgba(0, 122, 255, 0.1)')
          .borderRadius(20)
          .onClick(() => {
            // 处理逻辑
            this.selectedDays = this.selectedDays === 30 ? 90 : 30
            this.loadComparisonData()
          })
        }
        .width('100%')
        .height(56)
        .padding({ left: 16, right: 16 })
        .backgroundColor('rgba(255, 255, 255, 0.6)')
        .backdropBlur(20)
        .zIndex(100)
        .opacity(this.showContent ? 1 : 0)
        .translate({ y: this.showContent ? 0 : -20 })
        .animation({
          duration: 600,
          curve: Curve.Friction
        })

        if (this.isLoading) {
          Column() {
            LoadingProgress()
              .width(40)
              .height(40)
              .color('#007AFF')
            Text('加载中...')
              .fontSize(14)
              .fontColor('#999')
              .margin({ top: 12 })
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        } else {
          Scroll() {
            Column({ space: 24 }) {
              // 3. 
              this.OverallComparisonCard()

              // 4. 
              if (this.recentDecisions.length > 0) {
                this.RecentDecisionsCard()
              }

              // 5. 
              this.SuccessRateCard()

              // 6. 
              this.DomainStatsCard()

              // 7. 
              if (this.pendingDecisions.length > 0) {
                this.PendingDecisionsCard()
              }

              // 8. 
              Button('+ ')
                .width('100%')
                .height(56)
                .fontSize(18)
                .fontWeight(600)
                .fontColor(Color.White)
                .backgroundColor('#007AFF')
                .borderRadius(28)
                .shadow({ radius: 10, color: 'rgba(0, 122, 255, 0.3)', offsetY: 4 })
                .onClick(() => {
                  this.showRecordDialog = true
                })
                .margin({ bottom: 40 })
            }
            .width('100%')
            .padding({ left: 16, right: 16, top: 20 })
          }
          .layoutWeight(1)
          .scrollBar(BarState.Off)
          .edgeEffect(EdgeEffect.Spring)
        }
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F1F3F5')
  }

  @Builder
  OverallComparisonCard() {
    Column({ space: 16 }) {
      Text('')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')
        .padding({ left: 8 })

      Row() {
        Column() {
          Text(`${this.comparisonData.total_decisions}`)
            .fontSize(36)
            .fontWeight(800)
            .fontColor('#007AFF')
          Text('')
            .fontSize(14)
            .fontColor('#666')
            .margin({ top: 4 })
        }
        .layoutWeight(1)
        .alignItems(HorizontalAlign.Center)

        Divider().vertical(true).height(40).color('#E0E0E0')

        Column() {
          Text(`${(this.comparisonData.alignment_rate * 100).toFixed(0)}%`)
            .fontSize(36)
            .fontWeight(800)
            .fontColor('#34C759')
          Text('')
            .fontSize(14)
            .fontColor('#666')
            .margin({ top: 4 })
        }
        .layoutWeight(1)
        .alignItems(HorizontalAlign.Center)
      }
      .width('100%')
      .padding(24)
      .backgroundColor('rgba(255, 255, 255, 0.8)')
      .backdropBlur(20)
      .borderRadius(24)
      .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 600,
      delay: 100,
      curve: Curve.Friction
    })
  }

  @Builder
  RecentDecisionsCard() {
    Column({ space: 16 }) {
      Row() {
        Text('')
          .fontSize(18)
          .fontWeight(700)
          .fontColor('#1A1A1A')
        Blank()
        Text(`${this.recentDecisions.length}`)
          .fontSize(14)
          .fontColor('#999')
      }
      .width('100%')
      .padding({ left: 8 })

      Column({ space: 12 }) {
        ForEach(this.recentDecisions, (decision: RecentDecision) => {
          this.RecentDecisionItem(decision)
        })
      }
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 600,
      delay: 200,
      curve: Curve.Friction
    })
  }

  @Builder
  RecentDecisionItem(decision: RecentDecision): void {
    Column({ space: 12 }) {
      //  + 
      Row() {
        Text(this.getDomainName(decision.domain))
          .fontSize(12)
          .fontColor('#007AFF')
          .fontWeight(600)
          .padding({ left: 10, right: 10, top: 4, bottom: 4 })
          .backgroundColor('rgba(0, 122, 255, 0.1)')
          .borderRadius(8)

        if (decision.is_aligned) {
          Text(' ')
            .fontSize(12)
            .fontColor('#34C759')
            .fontWeight(600)
            .padding({ left: 10, right: 10, top: 4, bottom: 4 })
            .backgroundColor('rgba(52, 199, 89, 0.1)')
            .borderRadius(8)
            .margin({ left: 8 })
        } else {
          Text(' ')
            .fontSize(12)
            .fontColor('#FF3B30')
            .fontWeight(600)
            .padding({ left: 10, right: 10, top: 4, bottom: 4 })
            .backgroundColor('rgba(255, 59, 48, 0.1)')
            .borderRadius(8)
            .margin({ left: 8 })
        }

        Blank()

        Text(this.formatDate(decision.timestamp))
          .fontSize(12)
          .fontColor('#999')
      }
      .width('100%')

      // 处理逻辑
      Text(decision.situation)
        .fontSize(16)
        .fontWeight(600)
        .fontColor('#1A1A1A')
        .maxLines(2)
        .textOverflow({ overflow: TextOverflow.Ellipsis })

      // 处理逻辑
      Row({ space: 12 }) {
        // 处理逻辑
        Column({ space: 8 }) {
          Text('')
            .fontSize(12)
            .fontColor('#666')
          Text(decision.user_decision)
            .fontSize(14)
            .fontColor('#1A1A1A')
            .fontWeight(500)
            .maxLines(2)
            .textOverflow({ overflow: TextOverflow.Ellipsis })
        }
        .layoutWeight(1)
        .padding(12)
        .backgroundColor('#F5F5F5')
        .borderRadius(12)
        .alignItems(HorizontalAlign.Start)

        // AI
        Column({ space: 8 }) {
          Row() {
            Text('AI')
              .fontSize(12)
              .fontColor('#666')
            Blank()
            Text(`${(decision.ai_confidence * 100).toFixed(0)}%`)
              .fontSize(10)
              .fontColor('#007AFF')
              .fontWeight(600)
          }
          .width('100%')
          
          Text(decision.ai_recommendation)
            .fontSize(14)
            .fontColor('#1A1A1A')
            .fontWeight(500)
            .maxLines(2)
            .textOverflow({ overflow: TextOverflow.Ellipsis })
        }
        .layoutWeight(1)
        .padding(12)
        .backgroundColor('rgba(52, 199, 89, 0.1)')
        .borderRadius(12)
        .alignItems(HorizontalAlign.Start)
      }
      .width('100%')
    }
    .width('100%')
    .padding(20)
    .backgroundColor('rgba(255, 255, 255, 0.9)')
    .backdropBlur(20)
    .borderRadius(20)
    .shadow({ radius: 8, color: 'rgba(0,0,0,0.03)', offsetY: 2 })
  }

  @Builder
  SuccessRateCard() {
    Column({ space: 16 }) {
      Text('')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')
        .padding({ left: 8 })

      Column({ space: 20 }) {
        // 处理逻辑
        Column({ space: 8 }) {
          Row() {
            Text('')
              .fontSize(14)
              .fontColor('#666')
            Blank()
            Text(`${(this.comparisonData.user_success_rate * 100).toFixed(1)}%`)
              .fontSize(16)
              .fontWeight(700)
              .fontColor('#007AFF')
          }
          .width('100%')

          Progress({
            value: this.comparisonData.user_success_rate * 100,
            total: 100,
            type: ProgressType.Linear
          })
            .width('100%')
            .height(8)
            .color('#007AFF')
            .backgroundColor('rgba(0,0,0,0.05)')
            .style({ strokeWidth: 8, enableSmoothEffect: true })
        }

        // AI
        Column({ space: 8 }) {
          Row() {
            Text('AI')
              .fontSize(14)
              .fontColor('#666')
            Blank()
            Text(`${(this.comparisonData.ai_would_success_rate * 100).toFixed(1)}%`)
              .fontSize(16)
              .fontWeight(700)
              .fontColor('#34C759')
          }
          .width('100%')

          Progress({
            value: this.comparisonData.ai_would_success_rate * 100,
            total: 100,
            type: ProgressType.Linear
          })
            .width('100%')
            .height(8)
            .color('#34C759')
            .backgroundColor('rgba(0,0,0,0.05)')
            .style({ strokeWidth: 8, enableSmoothEffect: true })
        }

        Divider().color('#F0F0F0')

        // 处理逻辑
        Text(this.getComparisonInsight())
          .fontSize(14)
          .fontColor('#666')
          .lineHeight(20)
      }
      .padding(24)
      .backgroundColor('rgba(255, 255, 255, 0.8)')
      .backdropBlur(20)
      .borderRadius(24)
      .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 600,
      delay: 300,
      curve: Curve.Friction
    })
  }

  @Builder
  DomainStatsCard() {
    Column({ space: 16 }) {
      Text('')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')
        .padding({ left: 8 })

      Column({ space: 12 }) {
        ForEach(Object.keys(this.comparisonData.domain_stats), (domain: string) => {
          this.DomainStatItem(domain, this.comparisonData.domain_stats[domain])
        })
      }
      .padding(24)
      .backgroundColor('rgba(255, 255, 255, 0.8)')
      .backdropBlur(20)
      .borderRadius(24)
      .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 600,
      delay: 400,
      curve: Curve.Friction
    })
  }

  @Builder
  DomainStatItem(domain: string, stat: DomainStat) {
    Column({ space: 12 }) {
      Row() {
        Text(this.getDomainName(domain))
          .fontSize(16)
          .fontWeight(600)
          .fontColor('#1A1A1A')
        Blank()
        Text(`${stat.count}`)
          .fontSize(14)
          .fontColor('#999')
      }
      .width('100%')

      Row() {
        Column() {
          Text('')
            .fontSize(12)
            .fontColor('#999')
          Text(`${(stat.success_rate * 100).toFixed(0)}%`)
            .fontSize(18)
            .fontWeight(700)
            .fontColor('#007AFF')
            .margin({ top: 2 })
        }
        .layoutWeight(1)

        Column() {
          Text('')
            .fontSize(12)
            .fontColor('#999')
          Text(`${(stat.alignment_rate * 100).toFixed(0)}%`)
            .fontSize(18)
            .fontWeight(700)
            .fontColor('#34C759')
            .margin({ top: 2 })
        }
        .layoutWeight(1)
      }
      .width('100%')
      
      Divider().color('#F5F5F5')
    }
    .width('100%')
    .padding({ top: 4, bottom: 4 })
  }

  @Builder
  PendingDecisionsCard() {
    Column({ space: 16 }) {
      Text(` (${this.pendingDecisions.length})`)
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')
        .padding({ left: 8 })

      ForEach(this.pendingDecisions, (decision: PendingDecision) => {
        this.PendingDecisionItem(decision)
      })
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 600,
      delay: 500,
      curve: Curve.Friction
    })
  }

  @Builder
  PendingDecisionItem(decision: PendingDecision) {
    Column({ space: 12 }) {
      Row() {
        Text(this.getDomainName(decision.domain))
          .fontSize(12)
          .fontColor('#007AFF')
          .fontWeight(600)
          .padding({ left: 10, right: 10, top: 4, bottom: 4 })
          .backgroundColor('rgba(0, 122, 255, 0.1)')
          .borderRadius(8)

        Blank()

        Text(this.formatDate(decision.timestamp))
          .fontSize(12)
          .fontColor('#999')
      }
      .width('100%')

      Text(decision.situation)
        .fontSize(16)
        .fontWeight(600)
        .fontColor('#1A1A1A')
        .maxLines(2)
        .textOverflow({ overflow: TextOverflow.Ellipsis })

      Row() {
        Button('')
          .fontSize(14)
          .height(36)
          .fontWeight(600)
          .fontColor('#FFFFFF')
          .backgroundColor('#007AFF')
          .borderRadius(18)
          .onClick(() => {
            // 处理逻辑
            router.pushUrl({
              url: 'pages/VerifyDecision',
              params: { decisionId: decision.id }
            })
          })
      }
      .width('100%')
      .justifyContent(FlexAlign.End)
    }
    .width('100%')
    .padding(20)
    .backgroundColor('rgba(255, 255, 255, 0.9)')
    .backdropBlur(20)
    .borderRadius(20)
    .shadow({ radius: 8, color: 'rgba(0,0,0,0.03)', offsetY: 2 })
  }

  getDomainName(domain: string): string {
    const domainMap: Record<string, string> = {
      'time': '',
      'social': '',
      'learning': '',
      'emotion': '',
      'finance': '',
      'health': ''
    }
    return domainMap[domain] || domain
  }

  getComparisonInsight(): string {
    const diff = this.comparisonData.ai_would_success_rate - this.comparisonData.user_success_rate

    if (Math.abs(diff) < 0.05) {
      return 'AI'
    } else if (diff > 0) {
      return `AI${(diff * 100).toFixed(1)}%AI`
    } else {
      return ``
    }
  }

  formatDate(timestamp: string): string {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) {
      return ''
    } else if (days === 1) {
      return ''
    } else if (days < 7) {
      return `${days}`
    } else {
      return `${Math.floor(days / 7)}`
    }
  }
}
