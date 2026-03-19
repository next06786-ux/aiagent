/**
 *  - HarmonyOS 6 
 * 56
 */
import { router } from '@kit.ArkUI'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'

interface PerceptionData {
  quality: number
  modalities: ESObject
}

interface ReasoningData {
  confidence: number
  selected_agents: string[]
}

interface KnowledgeData {
  entities: number
  relations: number
  patterns: number
}

interface LearningData {
  episodes: number
  average_reward: number
}

interface DomainInsight {
  domain: string
  insights: string[]
  predictions: string[]
  recommendations: string[]
  confidence: number
}

interface ProcessResult {
  perception: PerceptionData
  reasoning: ReasoningData
  knowledge: KnowledgeData
  learning: LearningData
  domain_insights: DomainInsight[]
}

interface ApiResponse<T> {
  success: boolean
  data: T
}

interface DomainConfig {
  name: string
  icon: string
  color: string
}

interface ProcessRequest {
  user_id: string
  text: string
  sensors: SensorData
}

interface SensorData {
  steps: number
  location: LocationData
}

interface LocationData {
  latitude: number
  longitude: number
}

@Entry
@Component
struct LifeDomainInsights {
  @State isLoading: boolean = false
  @State result: ProcessResult | null = null
  @State errorMessage: string = ''
  @State selectedDomain: string = 'all'
  @State showContent: boolean = false
  
  // 处理逻辑
  get filteredDomainInsights(): DomainInsight[] {
    if (!this.result) {
      return []
    }
    if (this.selectedDomain === 'all') {
      return this.result.domain_insights
    }
    return this.result.domain_insights.filter(insight => insight.domain === this.selectedDomain)
  }
  
  // 处理逻辑
  private domainConfig: Record<string, DomainConfig> = {
    'time': { name: '', icon: '⏰', color: '#FF6B6B' },
    'social': { name: '', icon: '', color: '#4ECDC4' },
    'learning': { name: '', icon: '', color: '#45B7D1' },
    'emotion': { name: '', icon: '', color: '#FFA07A' },
    'finance': { name: '', icon: '', color: '#98D8C8' },
    'health': { name: '', icon: '', color: '#F7DC6F' }
  }

  aboutToAppear() {
    this.processCurrentData()
    setTimeout(() => {
      this.showContent = true
    }, 100)
  }

  async processCurrentData() {
    this.isLoading = true
    this.errorMessage = ''

    try {
      const httpRequest = http.createHttp()
      
      const requestData: ProcessRequest = {
        user_id: 'user_001',
        text: '',
        sensors: {
          steps: 5000,
          location: { latitude: 39.9, longitude: 116.4 }
        }
      }
      
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/v4/process`,
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: JSON.stringify(requestData)
        }
      )

      if (response.responseCode === 200) {
        const data = JSON.parse(response.result as string) as ApiResponse<ProcessResult>
        if (data.success) {
          this.result = data.data
        } else {
          // 处理逻辑
          this.useMockData()
        }
      } else {
        this.useMockData()
      }

      httpRequest.destroy()
    } catch (error) {
      this.useMockData()
    } finally {
      this.isLoading = false
    }
  }

  useMockData() {
    this.result = {
      perception: { quality: 0.95, modalities: {} },
      reasoning: { confidence: 0.88, selected_agents: [] },
      knowledge: { entities: 120, relations: 350, patterns: 15 },
      learning: { episodes: 45, average_reward: 0.82 },
      domain_insights: [
        {
          domain: 'health',
          insights: ['', ''],
          predictions: [''],
          recommendations: ['20', ''],
          confidence: 0.92
        },
        {
          domain: 'time',
          insights: [''],
          predictions: [''],
          recommendations: [''],
          confidence: 0.85
        },
        {
          domain: 'emotion',
          insights: [''],
          predictions: [''],
          recommendations: [''],
          confidence: 0.88
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
      Circle({ width: 350, height: 350 })
        .fill('rgba(152, 216, 200, 0.1)')
        .blur(60)
        .position({ x: '60%', y: -50 })

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
            .onClick(() => router.back())
            
            Column({ space: 2 }) {
              Text('')
                .fontSize(20)
                .fontWeight(700)
                .fontColor('#1A1A1A')
              
              Text('')
                .fontSize(12)
                .fontColor('#666666')
            }
            .alignItems(HorizontalAlign.Start)
          }
          
          Blank()
          
          Button({ type: ButtonType.Circle, stateEffect: true }) {
            Text('')
              .fontSize(24)
              .fontColor('#007AFF')
          }
          .width(40)
          .height(40)
          .backgroundColor('rgba(255, 255, 255, 0.0)')
          .onClick(() => {
            this.processCurrentData()
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
              .fontColor('#999999')
              .margin({ top: 16 })
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        } else if (this.errorMessage) {
          Column() {
            Text('')
              .fontSize(48)
            Text(this.errorMessage)
              .fontSize(14)
              .fontColor('#FF3B30')
              .margin({ top: 12 })
            Button('')
              .margin({ top: 20 })
              .backgroundColor('#007AFF')
              .onClick(() => {
                this.processCurrentData()
              })
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
        } else if (this.result) {
          Scroll() {
            Column({ space: 24 }) {
              // 3. 5
              this.buildArchitectureOverview()
              
              // 4. 
              this.buildDomainSelector()
              
              // 5. 
              Column({ space: 16 }) {
                ForEach(this.filteredDomainInsights, (insight: DomainInsight, index: number) => {
                  this.InsightCard(insight, index)
                })
              }
              .padding({ left: 16, right: 16, bottom: 40 })
            }
            .padding({ top: 20 })
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
  buildArchitectureOverview(): void {
    Column({ space: 16 }) {
      Text(' 5')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')
        .padding({ left: 8 })
      
      Column({ space: 12 }) {
        // 1
        this.ArchitectureItem('1', '', `: ${(this.result!.perception.quality * 100).toFixed(1)}%`, '#FF6B6B')
        
        // 2
        this.ArchitectureItem('2', '', `: ${(this.result!.reasoning.confidence * 100).toFixed(1)}%`, '#4ECDC4')
        
        // 3
        this.ArchitectureItem('3', '', `${this.result!.knowledge.entities} ${this.result!.knowledge.relations}`, '#45B7D1')
        
        // 4
        this.ArchitectureItem('4', '', `${this.result!.learning.episodes}`, '#FFA07A')
        
        // 5
        this.ArchitectureItem('5', '', `${this.result!.domain_insights.length}`, '#98D8C8')
      }
      .padding(20)
      .backgroundColor('rgba(255, 255, 255, 0.8)')
      .backdropBlur(20)
      .borderRadius(24)
      .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
    }
    .width('100%')
    .padding({ left: 16, right: 16 })
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 600,
      delay: 100,
      curve: Curve.Friction
    })
  }
  
  @Builder
  ArchitectureItem(layer: string, title: string, desc: string, color: string) {
    Row() {
      Text(layer)
        .fontSize(12)
        .fontColor('#FFFFFF')
        .fontWeight(600)
        .backgroundColor(color)
        .padding({ left: 8, right: 8, top: 4, bottom: 4 })
        .borderRadius(6)
      
      Text(title)
        .fontSize(15)
        .fontWeight(600)
        .fontColor('#1A1A1A')
        .margin({ left: 12 })
      
      Blank()
      
      Text(desc)
        .fontSize(12)
        .fontColor('#666666')
    }
    .width('100%')
    .padding(12)
    .backgroundColor('rgba(255, 255, 255, 0.5)')
    .borderRadius(12)
  }

  @Builder
  buildDomainSelector(): void {
    Column({ space: 12 }) {
      Text('')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')
        .padding({ left: 8 })
      
      Scroll() {
        Row({ space: 12 }) {
          this.DomainPill('', 'all', '#007AFF')
          ForEach(Object.keys(this.domainConfig), (key: string) => {
            this.DomainPill(
              `${this.domainConfig[key].icon} ${this.domainConfig[key].name}`,
              key,
              this.domainConfig[key].color
            )
          })
        }
        .padding({ left: 4, right: 4 })
      }
      .scrollable(ScrollDirection.Horizontal)
      .scrollBar(BarState.Off)
      .width('100%')
    }
    .width('100%')
    .padding({ left: 16, right: 16 })
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 600,
      delay: 200,
      curve: Curve.Friction
    })
  }
  
  @Builder
  DomainPill(label: string, key: string, color: string) {
    Text(label)
      .fontSize(14)
      .fontWeight(500)
      .fontColor(this.selectedDomain === key ? '#FFFFFF' : '#666666')
      .backgroundColor(this.selectedDomain === key ? color : 'rgba(255, 255, 255, 0.8)')
      .padding({ left: 16, right: 16, top: 10, bottom: 10 })
      .borderRadius(20)
      .shadow(this.selectedDomain === key ? { radius: 8, color: color + '40', offsetY: 4 } : undefined)
      .onClick(() => {
        animateTo({ duration: 300, curve: Curve.EaseInOut }, () => {
          this.selectedDomain = key
        })
      })
  }
  
  @Builder
  InsightCard(insight: DomainInsight, index: number) {
    Column({ space: 16 }) {
      // 处理逻辑
      Row() {
        Row({ space: 8 }) {
          Text(this.domainConfig[insight.domain].icon)
            .fontSize(24)
          Text(this.domainConfig[insight.domain].name)
            .fontSize(18)
            .fontWeight(700)
            .fontColor('#1A1A1A')
        }
        
        Blank()
        
        Text(`${(insight.confidence * 100).toFixed(0)}% `)
          .fontSize(12)
          .fontColor(this.domainConfig[insight.domain].color)
          .fontWeight(600)
          .padding({ left: 8, right: 8, top: 4, bottom: 4 })
          .backgroundColor(this.domainConfig[insight.domain].color + '15') // 10% opacity
          .borderRadius(6)
      }
      .width('100%')
      
      Divider().color('rgba(0,0,0,0.05)')
      
      // 处理逻辑
      if (insight.insights.length > 0) {
        Column({ space: 8 }) {
          Text(' ')
            .fontSize(14)
            .fontWeight(700)
            .fontColor(this.domainConfig[insight.domain].color)
          
          Column({ space: 4 }) {
            ForEach(insight.insights, (item: string) => {
              Text(`• ${item}`)
                .fontSize(14)
                .fontColor('#333333')
                .lineHeight(20)
            })
          }
        }
        .width('100%')
        .alignItems(HorizontalAlign.Start)
      }
      
      // 处理逻辑
      if (insight.predictions.length > 0) {
        Column({ space: 8 }) {
          Text(' ')
            .fontSize(14)
            .fontWeight(700)
            .fontColor(this.domainConfig[insight.domain].color)
          
          Column({ space: 4 }) {
            ForEach(insight.predictions, (item: string) => {
              Text(`• ${item}`)
                .fontSize(14)
                .fontColor('#333333')
                .lineHeight(20)
            })
          }
        }
        .width('100%')
        .alignItems(HorizontalAlign.Start)
      }
      
      // 处理逻辑
      if (insight.recommendations.length > 0) {
        Column({ space: 8 }) {
          Text(' ')
            .fontSize(14)
            .fontWeight(700)
            .fontColor(this.domainConfig[insight.domain].color)
          
          Column({ space: 8 }) {
            ForEach(insight.recommendations, (item: string) => {
              Row() {
                Text('•')
                  .fontSize(14)
                  .fontColor(this.domainConfig[insight.domain].color)
                  .fontWeight(800)
                  .margin({ right: 8 })
                
                Text(item)
                  .fontSize(14)
                  .fontColor('#333333')
                  .layoutWeight(1)
                  .lineHeight(20)
              }
              .width('100%')
              .padding(12)
              .backgroundColor('rgba(0,0,0,0.03)')
              .borderRadius(8)
            })
          }
        }
        .width('100%')
        .alignItems(HorizontalAlign.Start)
      }
    }
    .width('100%')
    .padding(24)
    .backgroundColor('rgba(255, 255, 255, 0.9)')
    .backdropBlur(20)
    .borderRadius(24)
    .shadow({ radius: 10, color: 'rgba(0,0,0,0.05)', offsetY: 4 })
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 600,
      delay: 300 + index * 100,
      curve: Curve.Friction
    })
  }
}
