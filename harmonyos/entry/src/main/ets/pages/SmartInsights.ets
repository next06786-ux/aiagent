/**
 * 智能洞察页面 - HarmonyOS 6 流体设计
 * 展示涌现发现：级联效应、协同增益、临界点预警、反馈环路
 */
import { Theme } from '../common/Theme';
import { SimpleIcon } from '../components/IconRenderer';
import http from '@ohos.net.http';
import { ApiConfig } from '../config/ApiConfig';
import { getAuthService } from '../service/AuthService';

interface SmartInsight {
  insight_id: string;
  category: string;
  level: string;
  title: string;
  description: string;
  evidence: string[];
  recommendations: string[];
  confidence: number;
  impact_score: number;
  created_at: string;
  related_metrics: string[];
  visualization_data: VisualizationData;
}

interface VisualizationData {
  type: string;
  nodes?: string[];
  trend?: EmotionTrendItem[];
  value?: number;
  threshold?: number;
}

interface EmotionTrendItem {
  date: string;
  avg_emotion: number;
  count: number;
}

interface TopicItem {
  topic: string;
  count: number;
}

interface DashboardData {
  user_id: string;
  generated_at: string;
  summary: DashboardSummary;
  emotion_trend: EmotionTrendItem[];
  topic_distribution: TopicItem[];
  top_insights: SmartInsight[];
  emergence_stats: EmergenceStats;
}

interface DashboardSummary {
  total_insights: number;
  critical_count: number;
  warning_count: number;
  suggestion_count: number;
}

interface EmergenceStats {
  total_events: number;
  pattern_events: number;
  synergy_events: number;
  feedback_loop_events: number;
  threshold_events: number;
}

interface DashboardResponse {
  success: boolean;
  data: DashboardData;
}

interface InsightsListResponse {
  success: boolean;
  total: number;
  insights: SmartInsight[];
}

interface CategoryConfig {
  id: string;
  name: string;
  icon: string;
  color: string;
}

@Entry
@Component
struct SmartInsights {
  @State isLoading: boolean = true;
  @State dashboardData: DashboardData | null = null;
  @State allInsights: SmartInsight[] = [];
  @State selectedCategory: string = 'all';
  @State selectedInsight: SmartInsight | null = null;
  @State showDetail: boolean = false;
  @State errorMessage: string = '';
  @State showContent: boolean = false;

  private authService = getAuthService();

  private categories: CategoryConfig[] = [
    { id: 'all', name: '全部', icon: 'grid', color: '#6B48FF' },
    { id: 'cascade', name: '级联效应', icon: 'flow', color: '#FF9500' },
    { id: 'synergy', name: '协同增益', icon: 'link', color: '#00C853' },
    { id: 'tipping_point', name: '临界点', icon: 'alert', color: '#FF3B30' },
    { id: 'feedback_loop', name: '反馈环路', icon: 'refresh', color: '#0A59F7' },
    { id: 'pattern', name: '行为模式', icon: 'chart', color: '#6B48FF' },
  ];

  aboutToAppear() {
    this.loadDashboard();
    this.loadInsights();
    setTimeout(() => { this.showContent = true }, 50);
  }

  async loadDashboard() {
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/v1/insights/dashboard/${userId}`,
        { method: http.RequestMethod.GET }
      );
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as DashboardResponse;
        if (result.success) { this.dashboardData = result.data; }
      }
    } catch (err) {
      this.errorMessage = '加载数据失败';
    }
  }

  async loadInsights() {
    this.isLoading = true;
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      let url = `${ApiConfig.getBaseUrl()}/api/v1/insights/list/${userId}?limit=50`;
      if (this.selectedCategory !== 'all') { url += `&category=${this.selectedCategory}`; }
      const response = await httpRequest.request(url, { method: http.RequestMethod.GET });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as InsightsListResponse;
        if (result.success) { this.allInsights = result.insights; }
      }
    } catch (err) {
      console.error('加载洞察列表失败:', err);
    } finally { this.isLoading = false; }
  }

  async generateInsights() {
    this.isLoading = true;
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/v1/insights/generate`,
        { method: http.RequestMethod.POST, header: { 'Content-Type': 'application/json' }, extraData: JSON.stringify({ user_id: userId }) }
      );
      httpRequest.destroy();
      if (response.responseCode === 200) {
        await this.loadDashboard();
        await this.loadInsights();
      }
    } catch (err) {
      console.error('生成洞察失败:', err);
    } finally { this.isLoading = false; }
  }

  getLevelColor(level: string): string {
    if (level === 'critical') return Theme.Color.Destructive;
    if (level === 'warning') return Theme.Color.Warning;
    if (level === 'suggestion') return Theme.Color.Primary;
    return Theme.Color.TextTertiary;
  }

  getLevelIcon(level: string): string {
    if (level === 'critical') return '!!';
    if (level === 'warning') return '!';
    if (level === 'suggestion') return '*';
    return 'i';
  }

  getCategoryColor(category: string): string {
    const config = this.categories.find(c => c.id === category);
    return config?.color || '#6B48FF';
  }

  getCategoryIcon(category: string): string {
    if (category === 'cascade') return 'C';
    if (category === 'synergy') return 'S';
    if (category === 'tipping_point') return 'T';
    if (category === 'feedback_loop') return 'L';
    if (category === 'pattern') return 'P';
    return '*';
  }

  private navigateBack(): void {
    try { this.getUIContext().getRouter().back(); } catch (e) { console.error('返回失败:', e); }
  }

  build() {
    Stack() {
      Column()
        .width('100%').height('100%')
        .backgroundColor(Theme.Color.BackgroundPrimary)

      Column() {
        this.TopBar()

        if (this.isLoading && !this.dashboardData) {
          this.LoadingView()
        } else if (this.errorMessage) {
          this.ErrorView()
        } else {
          Scroll() {
            Column({ space: 20 }) {
              if (this.dashboardData) { this.SummaryCards() }
              if (this.dashboardData?.emotion_trend && this.dashboardData.emotion_trend.length > 0) {
                this.EmotionTrendChart()
              }
              this.CategoryFilter()
              this.InsightsList()
            }
            .padding({ left: 16, right: 16, bottom: 80 })
          }
          .scrollBar(BarState.Off)
          .edgeEffect(EdgeEffect.Spring)
          .layoutWeight(1)
        }
      }
      .width('100%').height('100%')

      if (this.showDetail && this.selectedInsight) { this.InsightDetailPanel() }
    }
    .width('100%').height('100%')
  }

  @Builder
  TopBar() {
    Row() {
      Text('←')
        .fontSize(24)
        .fontColor(Theme.Color.Primary)
        .onClick(() => this.navigateBack())

      Column({ space: 2 }) {
        Text('智能洞察')
          .fontSize(18).fontWeight(FontWeight.Medium).fontColor(Theme.Color.TextPrimary)
        Text('涌现发现 · 深度分析')
          .fontSize(12).fontColor(Theme.Color.TextTertiary)
      }.layoutWeight(1).margin({ left: 12 }).alignItems(HorizontalAlign.Start)

      Stack() {
        Circle({ width: 40, height: 40 }).fill(Theme.Color.GlassMedium)
        SimpleIcon({ iconName: 'refresh', iconSize: 20, color: Theme.Color.TextSecondary })
      }.width(40).height(40)
      .onClick(() => this.generateInsights())
    }
    .width('100%')
    .padding({ left: 16, right: 16, top: 12, bottom: 12 })
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }

  @Builder
  SummaryCards() {
    Column({ space: 14 }) {
      Text('洞察概览')
        .fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
        .padding({ left: 4 })
        .opacity(this.showContent ? 1 : 0)
        .translate({ x: this.showContent ? 0 : -20 })
        .animation({ duration: 600, curve: Curve.Smooth, delay: 0 })

      Row({ space: 12 }) {
        this.SummaryCard('关键', this.dashboardData?.summary.critical_count || 0, Theme.Color.Destructive, '!!', 0)
        this.SummaryCard('警告', this.dashboardData?.summary.warning_count || 0, Theme.Color.Warning, '!', 1)
        this.SummaryCard('建议', this.dashboardData?.summary.suggestion_count || 0, Theme.Color.Primary, '*', 2)
        this.SummaryCard('总计', this.dashboardData?.summary.total_insights || 0, Theme.Color.Secondary, '#', 3)
      }.width('100%').justifyContent(FlexAlign.SpaceBetween)
    }
  }

  @Builder
  SummaryCard(title: string, count: number, color: string, icon: string, index: number) {
    Column({ space: 6 }) {
      Text(icon).fontSize(22)
      Text(count.toString())
        .fontSize(22).fontWeight(700).fontColor(color)
      Text(title)
        .fontSize(12).fontColor(Theme.Color.TextTertiary)
    }
    .width('22%')
    .padding(14)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .alignItems(HorizontalAlign.Center)
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 50 + index * 60 })
  }

  @Builder
  EmotionTrendChart() {
    Column({ space: 12 }) {
      Row() {
        Text('情绪趋势').fontSize(16).fontWeight(600).fontColor(Theme.Color.TextPrimary)
        Blank()
        Text('近14天').fontSize(12).fontColor(Theme.Color.TextTertiary)
      }.width('100%')

      Row({ space: 4 }) {
        ForEach(this.dashboardData?.emotion_trend || [], (item: EmotionTrendItem) => {
          Column() {
            Column()
              .width(16)
              .height(`${Math.max(item.avg_emotion * 10, 10)}%`)
              .backgroundColor(item.avg_emotion >= 6 ? Theme.Color.Accent : item.avg_emotion >= 4 ? Theme.Color.Warning : Theme.Color.Destructive)
              .borderRadius(Theme.Radius.xs)
            Text(item.date.slice(5))
              .fontSize(8).fontColor(Theme.Color.TextTertiary).margin({ top: 4 })
          }.height(120).justifyContent(FlexAlign.End).alignItems(HorizontalAlign.Center)
        })
      }
      .width('100%').height(140).padding(14)
      .backgroundColor(Theme.Color.BackgroundSecondary)
      .borderRadius(Theme.Radius.l)
      .border({ width: 1, color: Theme.Color.BorderLight })
      .justifyContent(FlexAlign.SpaceAround)
    }
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 300 })
  }

  @Builder
  CategoryFilter() {
    Scroll() {
      Row({ space: 10 }) {
        ForEach(this.categories, (cat: CategoryConfig) => {
          Button(cat.name)
            .fontSize(13)
            .fontColor(this.selectedCategory === cat.id ? '#FFFFFF' : Theme.Color.TextSecondary)
            .backgroundColor(this.selectedCategory === cat.id ? cat.color : Theme.Color.BackgroundSecondary)
            .borderRadius(Theme.Radius.round)
            .border({ width: 1, color: this.selectedCategory === cat.id ? 'transparent' : Theme.Color.BorderLight })
            .padding({ left: 16, right: 16, top: 8, bottom: 8 })
            .shadow(this.selectedCategory === cat.id ? Theme.Shadow.GlowPrimary : Theme.Shadow.Soft)
            .onClick(() => { this.selectedCategory = cat.id; this.loadInsights(); })
        })
      }.padding({ left: 4, right: 4 })
    }
    .scrollable(ScrollDirection.Horizontal)
    .scrollBar(BarState.Off)
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .animation({ duration: 600, curve: Curve.Smooth, delay: 400 })
  }

  @Builder
  InsightsList() {
    Column({ space: 12 }) {
      if (this.allInsights.length === 0) {
        Column({ space: 16 }) {
          Text('--').fontSize(48).fontColor(Theme.Color.TextTertiary)
          Text('暂无洞察').fontSize(16).fontColor(Theme.Color.TextSecondary)
          Text('继续与AI对话，系统会自动分析并生成洞察')
            .fontSize(13).fontColor(Theme.Color.TextTertiary).textAlign(TextAlign.Center)
          Button('生成洞察')
            .fontSize(14).fontColor('#FFFFFF').backgroundColor(Theme.Color.Secondary)
            .borderRadius(Theme.Radius.round).padding({ left: 24, right: 24, top: 10, bottom: 10 })
            .shadow(Theme.Shadow.GlowPrimary).margin({ top: 12 })
            .onClick(() => this.generateInsights())
        }.width('100%').padding(40).justifyContent(FlexAlign.Center).alignItems(HorizontalAlign.Center)
      } else {
        ForEach(this.allInsights, (insight: SmartInsight, index: number) => {
          this.InsightCard(insight, index)
        })
      }
    }
  }

  @Builder
  InsightCard(insight: SmartInsight, index: number) {
    Column({ space: 10 }) {
      Row() {
        Text(this.getLevelIcon(insight.level)).fontSize(20)
        Column({ space: 2 }) {
          Text(insight.title).fontSize(15).fontWeight(600).fontColor(Theme.Color.TextPrimary)
          Text(this.getCategoryIcon(insight.category) + ' ' + insight.category)
            .fontSize(11).fontColor(this.getCategoryColor(insight.category))
        }.layoutWeight(1).alignItems(HorizontalAlign.Start).margin({ left: 10 })
        Column() {
          Text(Math.round(insight.impact_score).toString())
            .fontSize(18).fontWeight(700).fontColor(this.getLevelColor(insight.level))
          Text('影响力').fontSize(9).fontColor(Theme.Color.TextTertiary)
        }.alignItems(HorizontalAlign.Center)
      }.width('100%')

      Text(insight.description)
        .fontSize(13).fontColor(Theme.Color.TextSecondary).lineHeight(20)
        .maxLines(3).textOverflow({ overflow: TextOverflow.Ellipsis })

      Row() {
        Text(`置信度: ${Math.round(insight.confidence * 100)}%`)
          .fontSize(11).fontColor(Theme.Color.TextTertiary)
        Blank()
        Text('查看详情 →').fontSize(12).fontColor(Theme.Color.Primary)
      }.width('100%')
    }
    .width('100%').padding(16)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .onClick(() => { this.selectedInsight = insight; this.showDetail = true; })
    .opacity(this.showContent ? 1 : 0)
    .translate({ x: this.showContent ? 0 : -30 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 450 + index * 60 })
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
  InsightDetailPanel() {
    Stack() {
      Column()
        .width('100%').height('100%')
        .backgroundColor(Theme.Color.OverlayMedium)
        .onClick(() => { this.showDetail = false; })

      Column({ space: 16 }) {
        Row() {
          Text(this.getLevelIcon(this.selectedInsight!.level)).fontSize(28)
          Column({ space: 4 }) {
            Text(this.selectedInsight!.title)
              .fontSize(18).fontWeight(700).fontColor(Theme.Color.TextPrimary)
            Row({ space: 8 }) {
              Text(this.getCategoryIcon(this.selectedInsight!.category)).fontSize(14)
              Text(this.selectedInsight!.category)
                .fontSize(12).fontColor(this.getCategoryColor(this.selectedInsight!.category))
            }
          }.layoutWeight(1).alignItems(HorizontalAlign.Start).margin({ left: 12 })

          Stack() {
            Circle({ width: 32, height: 32 }).fill(Theme.Color.GlassMedium)
            Text('✕').fontSize(16).fontColor(Theme.Color.TextSecondary)
          }.width(32).height(32)
          .onClick(() => { this.showDetail = false; })
        }.width('100%')

        Divider().color(Theme.Color.BorderLight)

        Scroll() {
          Column({ space: 16 }) {
            Text(this.selectedInsight!.description)
              .fontSize(14).fontColor(Theme.Color.TextPrimary).lineHeight(22)

            if (this.selectedInsight!.evidence.length > 0) {
              Column({ space: 8 }) {
                Text('// 支撑证据').fontSize(14).fontWeight(600).fontColor(Theme.Color.Warning)
                ForEach(this.selectedInsight!.evidence, (evidence: string) => {
                  Row({ space: 8 }) {
                    Text('•').fontSize(14).fontColor(Theme.Color.TextTertiary)
                    Text(evidence).fontSize(13).fontColor(Theme.Color.TextSecondary).layoutWeight(1)
                  }.width('100%').alignItems(VerticalAlign.Top)
                })
              }
              .width('100%').padding(14)
              .backgroundColor('rgba(255, 149, 0, 0.06)')
              .borderRadius(Theme.Radius.l)
              .border({ width: 1, color: 'rgba(255, 149, 0, 0.12)' })
            }

            if (this.selectedInsight!.recommendations.length > 0) {
              Column({ space: 8 }) {
                Text('* 建议行动').fontSize(14).fontWeight(600).fontColor(Theme.Color.Accent)
                ForEach(this.selectedInsight!.recommendations, (rec: string, idx: number) => {
                  Row({ space: 8 }) {
                    Text(`${idx + 1}.`).fontSize(13).fontColor(Theme.Color.Accent)
                    Text(rec).fontSize(13).fontColor(Theme.Color.TextSecondary).layoutWeight(1)
                  }.width('100%').alignItems(VerticalAlign.Top)
                })
              }
              .width('100%').padding(14)
              .backgroundColor('rgba(0, 200, 83, 0.06)')
              .borderRadius(Theme.Radius.l)
              .border({ width: 1, color: 'rgba(0, 200, 83, 0.12)' })
            }

            Row({ space: 20 }) {
              Column({ space: 4 }) {
                Text('影响力').fontSize(11).fontColor(Theme.Color.TextTertiary)
                Text(`${Math.round(this.selectedInsight!.impact_score)}`)
                  .fontSize(20).fontWeight(700).fontColor(this.getLevelColor(this.selectedInsight!.level))
              }.alignItems(HorizontalAlign.Center)
              Column({ space: 4 }) {
                Text('置信度').fontSize(11).fontColor(Theme.Color.TextTertiary)
                Text(`${Math.round(this.selectedInsight!.confidence * 100)}%`)
                  .fontSize(20).fontWeight(700).fontColor(Theme.Color.Secondary)
              }.alignItems(HorizontalAlign.Center)
              Column({ space: 4 }) {
                Text('相关指标').fontSize(11).fontColor(Theme.Color.TextTertiary)
                Text(`${this.selectedInsight!.related_metrics.length}`)
                  .fontSize(20).fontWeight(700).fontColor(Theme.Color.Primary)
              }.alignItems(HorizontalAlign.Center)
            }
            .width('100%').justifyContent(FlexAlign.SpaceAround)
            .padding(16)
            .backgroundColor(Theme.Color.BackgroundTertiary)
            .borderRadius(Theme.Radius.l)
          }
        }.layoutWeight(1).scrollBar(BarState.Off)
      }
      .width('90%')
      .height('75%')
      .padding(24)
      .backgroundColor(Theme.Color.BackgroundSecondary)
      .borderRadius(Theme.Radius.xl)
      .border({ width: 1, color: Theme.Color.BorderLight })
      .shadow(Theme.Shadow.Elevated)
    }
    .width('100%').height('100%')
  }

  @Builder
  LoadingView() {
    Column({ space: 16 }) {
      LoadingProgress().width(48).height(48).color(Theme.Color.Primary)
      Text('正在分析数据...').fontSize(14).fontColor(Theme.Color.TextTertiary)
    }
    .width('100%').layoutWeight(1)
    .justifyContent(FlexAlign.Center).alignItems(HorizontalAlign.Center)
  }

  @Builder
  ErrorView() {
    Column({ space: 16 }) {
      Text('😔').fontSize(48)
      Text(this.errorMessage).fontSize(14).fontColor(Theme.Color.Destructive)
      Button('重试')
        .fontSize(14).fontColor('#FFFFFF').backgroundColor(Theme.Color.Primary)
        .borderRadius(Theme.Radius.round).padding({ left: 24, right: 24, top: 10, bottom: 10 })
        .onClick(() => { this.errorMessage = ''; this.loadDashboard(); this.loadInsights(); })
    }
    .width('100%').layoutWeight(1)
    .justifyContent(FlexAlign.Center).alignItems(HorizontalAlign.Center)
  }
}
