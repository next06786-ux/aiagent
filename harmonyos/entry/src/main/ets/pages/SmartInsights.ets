/**
 * 智能洞察页面
 * 展示涌现发现：级联效应、协同增益、临界点预警、反馈环路
 */
import { Theme } from '../common/Theme';
import { SimpleIcon } from '../components/IconRenderer';
import http from '@ohos.net.http';
import { ApiConfig } from '../config/ApiConfig';
import { getAuthService } from '../service/AuthService';

// 洞察数据接口
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
  
  private authService = getAuthService();
  
  // 分类配置
  private categories: CategoryConfig[] = [
    { id: 'all', name: '全部', icon: 'grid', color: '#8B5CF6' },
    { id: 'cascade', name: '级联效应', icon: 'flow', color: '#F59E0B' },
    { id: 'synergy', name: '协同增益', icon: 'link', color: '#10B981' },
    { id: 'tipping_point', name: '临界点', icon: 'alert', color: '#EF4444' },
    { id: 'feedback_loop', name: '反馈环路', icon: 'refresh', color: '#3B82F6' },
    { id: 'pattern', name: '行为模式', icon: 'chart', color: '#8B5CF6' },
  ];
  
  aboutToAppear() {
    this.loadDashboard();
    this.loadInsights();
  }
  
  async loadDashboard() {
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const url = `${ApiConfig.getBaseUrl()}/api/v1/insights/dashboard/${userId}`;
      
      const response = await httpRequest.request(url, {
        method: http.RequestMethod.GET
      });
      
      httpRequest.destroy();
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as DashboardResponse;
        if (result.success) {
          this.dashboardData = result.data;
        }
      }
    } catch (err) {
      console.error('加载仪表盘失败:', err);
      this.errorMessage = '加载数据失败';
    }
  }
  
  async loadInsights() {
    this.isLoading = true;
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      
      let url = `${ApiConfig.getBaseUrl()}/api/v1/insights/list/${userId}?limit=50`;
      if (this.selectedCategory !== 'all') {
        url += `&category=${this.selectedCategory}`;
      }
      
      const response = await httpRequest.request(url, {
        method: http.RequestMethod.GET
      });
      
      httpRequest.destroy();
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as InsightsListResponse;
        if (result.success) {
          this.allInsights = result.insights;
        }
      }
    } catch (err) {
      console.error('加载洞察列表失败:', err);
    } finally {
      this.isLoading = false;
    }
  }
  
  async generateInsights() {
    this.isLoading = true;
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const url = `${ApiConfig.getBaseUrl()}/api/v1/insights/generate`;
      
      const response = await httpRequest.request(url, {
        method: http.RequestMethod.POST,
        header: { 'Content-Type': 'application/json' },
        extraData: JSON.stringify({ user_id: userId })
      });
      
      httpRequest.destroy();
      
      if (response.responseCode === 200) {
        // 重新加载数据
        await this.loadDashboard();
        await this.loadInsights();
      }
    } catch (err) {
      console.error('生成洞察失败:', err);
    } finally {
      this.isLoading = false;
    }
  }
  
  getLevelColor(level: string): string {
    if (level === 'critical') return '#EF4444';
    if (level === 'warning') return '#F59E0B';
    if (level === 'suggestion') return '#3B82F6';
    return '#6B7280';
  }
  
  getLevelIcon(level: string): string {
    if (level === 'critical') return '🚨';
    if (level === 'warning') return '⚠️';
    if (level === 'suggestion') return '💡';
    return 'ℹ️';
  }
  
  getCategoryIcon(category: string): string {
    if (category === 'cascade') return '🌊';
    if (category === 'synergy') return '🤝';
    if (category === 'tipping_point') return '⚡';
    if (category === 'feedback_loop') return '🔄';
    if (category === 'pattern') return '📊';
    if (category === 'trend') return '📈';
    if (category === 'anomaly') return '🔍';
    return '💡';
  }
  
  getCategoryColor(category: string): string {
    const config = this.categories.find(c => c.id === category);
    return config?.color || '#8B5CF6';
  }
  
  private navigateBack(): void {
    try {
      this.getUIContext().getRouter().back();
    } catch (e) {
      console.error('返回失败:', e);
    }
  }

  build() {
    Stack() {
      // 背景
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 180,
          colors: [['#0F0A1F', 0], ['#1A1035', 0.5], ['#0D0820', 1]]
        })
      
      Column() {
        // 顶部栏
        this.TopBar()
        
        if (this.isLoading && !this.dashboardData) {
          this.LoadingView()
        } else if (this.errorMessage) {
          this.ErrorView()
        } else {
          Scroll() {
            Column({ space: 20 }) {
              // 概览卡片
              if (this.dashboardData) {
                this.SummaryCards()
              }
              
              // 情绪趋势图
              if (this.dashboardData?.emotion_trend && this.dashboardData.emotion_trend.length > 0) {
                this.EmotionTrendChart()
              }
              
              // 分类筛选
              this.CategoryFilter()
              
              // 洞察列表
              this.InsightsList()
            }
            .padding({ left: 16, right: 16, bottom: 100 })
          }
          .scrollBar(BarState.Off)
          .layoutWeight(1)
        }
      }
      .width('100%')
      .height('100%')
      
      // 详情弹窗
      if (this.showDetail && this.selectedInsight) {
        this.InsightDetailPanel()
      }
    }
    .width('100%')
    .height('100%')
  }
  
  @Builder
  TopBar() {
    Row() {
      Button({ type: ButtonType.Circle }) {
        Text('←').fontSize(20).fontColor('#FFFFFF')
      }
      .width(40)
      .height(40)
      .backgroundColor('rgba(100, 80, 180, 0.3)')
      .onClick(() => this.navigateBack())
      
      Column({ space: 2 }) {
        Text('智能洞察')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor('#FFFFFF')
        Text('涌现发现 · 深度分析')
          .fontSize(12)
          .fontColor('rgba(180, 160, 255, 0.7)')
      }
      .layoutWeight(1)
      .alignItems(HorizontalAlign.Center)
      
      Button({ type: ButtonType.Circle }) {
        Text('🔄').fontSize(18)
      }
      .width(40)
      .height(40)
      .backgroundColor('rgba(100, 80, 180, 0.3)')
      .onClick(() => this.generateInsights())
    }
    .width('100%')
    .height(64)
    .padding({ left: 16, right: 16 })
  }
  
  @Builder
  SummaryCards() {
    Column({ space: 12 }) {
      Text('洞察概览')
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .fontColor('rgba(255, 255, 255, 0.9)')
        .alignSelf(ItemAlign.Start)
      
      Row({ space: 12 }) {
        // 关键洞察
        this.SummaryCard(
          '关键',
          this.dashboardData?.summary.critical_count || 0,
          '#EF4444',
          '🚨'
        )
        
        // 警告
        this.SummaryCard(
          '警告',
          this.dashboardData?.summary.warning_count || 0,
          '#F59E0B',
          '⚠️'
        )
        
        // 建议
        this.SummaryCard(
          '建议',
          this.dashboardData?.summary.suggestion_count || 0,
          '#3B82F6',
          '💡'
        )
        
        // 总计
        this.SummaryCard(
          '总计',
          this.dashboardData?.summary.total_insights || 0,
          '#8B5CF6',
          '📊'
        )
      }
      .width('100%')
      .justifyContent(FlexAlign.SpaceBetween)
    }
  }
  
  @Builder
  SummaryCard(title: string, count: number, color: string, icon: string) {
    Column({ space: 6 }) {
      Text(icon)
        .fontSize(24)
      
      Text(count.toString())
        .fontSize(24)
        .fontWeight(FontWeight.Bold)
        .fontColor(color)
      
      Text(title)
        .fontSize(12)
        .fontColor('rgba(255, 255, 255, 0.6)')
    }
    .width('22%')
    .padding(12)
    .backgroundColor('rgba(30, 20, 60, 0.6)')
    .borderRadius(12)
    .border({ width: 1, color: `${color}33` })
  }
  
  @Builder
  EmotionTrendChart() {
    Column({ space: 12 }) {
      Row() {
        Text('情绪趋势')
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
          .fontColor('rgba(255, 255, 255, 0.9)')
        
        Blank()
        
        Text('近14天')
          .fontSize(12)
          .fontColor('rgba(150, 130, 200, 0.6)')
      }
      .width('100%')
      
      // 简化的趋势图
      Row({ space: 4 }) {
        ForEach(this.dashboardData?.emotion_trend || [], (item: EmotionTrendItem, index: number) => {
          Column() {
            // 柱状图
            Column()
              .width(16)
              .height(`${Math.max(item.avg_emotion * 10, 10)}%`)
              .backgroundColor(item.avg_emotion >= 6 ? '#10B981' : 
                             item.avg_emotion >= 4 ? '#F59E0B' : '#EF4444')
              .borderRadius(4)
            
            // 日期
            Text(item.date.slice(5))
              .fontSize(8)
              .fontColor('rgba(150, 130, 200, 0.5)')
              .margin({ top: 4 })
          }
          .height(120)
          .justifyContent(FlexAlign.End)
          .alignItems(HorizontalAlign.Center)
        })
      }
      .width('100%')
      .height(140)
      .padding(12)
      .backgroundColor('rgba(30, 20, 60, 0.4)')
      .borderRadius(12)
      .justifyContent(FlexAlign.SpaceAround)
    }
  }
  
  @Builder
  CategoryFilter() {
    Scroll() {
      Row({ space: 10 }) {
        ForEach(this.categories, (cat: CategoryConfig) => {
          Button(cat.name)
            .fontSize(13)
            .fontColor(this.selectedCategory === cat.id ? '#FFFFFF' : 'rgba(200, 180, 255, 0.8)')
            .backgroundColor(this.selectedCategory === cat.id ? cat.color : 'rgba(60, 40, 100, 0.4)')
            .borderRadius(16)
            .padding({ left: 14, right: 14, top: 8, bottom: 8 })
            .onClick(() => {
              this.selectedCategory = cat.id;
              this.loadInsights();
            })
        })
      }
      .padding({ left: 4, right: 4 })
    }
    .scrollable(ScrollDirection.Horizontal)
    .scrollBar(BarState.Off)
    .width('100%')
  }
  
  @Builder
  InsightsList() {
    Column({ space: 12 }) {
      if (this.allInsights.length === 0) {
        Column({ space: 16 }) {
          Text('🔮')
            .fontSize(48)
          Text('暂无洞察')
            .fontSize(16)
            .fontColor('rgba(150, 130, 200, 0.6)')
          Text('继续与AI对话，系统会自动分析并生成洞察')
            .fontSize(13)
            .fontColor('rgba(150, 130, 200, 0.4)')
            .textAlign(TextAlign.Center)
          
          Button('生成洞察')
            .fontSize(14)
            .fontColor('#FFFFFF')
            .backgroundColor('#8B5CF6')
            .borderRadius(20)
            .padding({ left: 24, right: 24, top: 10, bottom: 10 })
            .margin({ top: 12 })
            .onClick(() => this.generateInsights())
        }
        .width('100%')
        .padding(40)
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
      } else {
        ForEach(this.allInsights, (insight: SmartInsight) => {
          this.InsightCard(insight)
        })
      }
    }
  }
  
  @Builder
  InsightCard(insight: SmartInsight) {
    Column({ space: 10 }) {
      // 头部：级别图标 + 标题 + 分类
      Row() {
        Text(this.getLevelIcon(insight.level))
          .fontSize(20)
        
        Column({ space: 2 }) {
          Text(insight.title)
            .fontSize(15)
            .fontWeight(FontWeight.Medium)
            .fontColor('#FFFFFF')
          
          Text(this.getCategoryIcon(insight.category) + ' ' + insight.category)
            .fontSize(11)
            .fontColor(this.getCategoryColor(insight.category))
        }
        .layoutWeight(1)
        .alignItems(HorizontalAlign.Start)
        .margin({ left: 10 })
        
        // 影响力分数
        Column() {
          Text(Math.round(insight.impact_score).toString())
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .fontColor(this.getLevelColor(insight.level))
          Text('影响力')
            .fontSize(9)
            .fontColor('rgba(150, 130, 200, 0.5)')
        }
        .alignItems(HorizontalAlign.Center)
      }
      .width('100%')
      
      // 描述
      Text(insight.description)
        .fontSize(13)
        .fontColor('rgba(200, 180, 255, 0.8)')
        .lineHeight(20)
        .maxLines(3)
        .textOverflow({ overflow: TextOverflow.Ellipsis })
      
      // 底部：置信度 + 查看详情
      Row() {
        Text(`置信度: ${Math.round(insight.confidence * 100)}%`)
          .fontSize(11)
          .fontColor('rgba(150, 130, 200, 0.5)')
        
        Blank()
        
        Text('查看详情 →')
          .fontSize(12)
          .fontColor('#8B5CF6')
      }
      .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor('rgba(30, 20, 60, 0.6)')
    .borderRadius(16)
    .border({ width: 1, color: `${this.getLevelColor(insight.level)}33` })
    .onClick(() => {
      this.selectedInsight = insight;
      this.showDetail = true;
    })
  }
  
  @Builder
  InsightDetailPanel() {
    Stack() {
      // 背景遮罩
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('rgba(0, 0, 0, 0.7)')
        .onClick(() => { this.showDetail = false; })
      
      // 详情卡片
      Column({ space: 16 }) {
        // 头部
        Row() {
          Text(this.getLevelIcon(this.selectedInsight!.level))
            .fontSize(28)
          
          Column({ space: 4 }) {
            Text(this.selectedInsight!.title)
              .fontSize(18)
              .fontWeight(FontWeight.Bold)
              .fontColor('#FFFFFF')
            
            Row({ space: 8 }) {
              Text(this.getCategoryIcon(this.selectedInsight!.category))
                .fontSize(14)
              Text(this.selectedInsight!.category)
                .fontSize(12)
                .fontColor(this.getCategoryColor(this.selectedInsight!.category))
            }
          }
          .layoutWeight(1)
          .alignItems(HorizontalAlign.Start)
          .margin({ left: 12 })
          
          Button({ type: ButtonType.Circle }) {
            Text('✕').fontSize(18).fontColor('rgba(200, 180, 255, 0.9)')
          }
          .width(32)
          .height(32)
          .backgroundColor('rgba(100, 60, 180, 0.4)')
          .onClick(() => { this.showDetail = false; })
        }
        .width('100%')
        
        Divider().color('rgba(100, 80, 180, 0.3)')
        
        Scroll() {
          Column({ space: 16 }) {
            // 描述
            Text(this.selectedInsight!.description)
              .fontSize(14)
              .fontColor('rgba(220, 200, 255, 0.9)')
              .lineHeight(22)
            
            // 证据
            if (this.selectedInsight!.evidence.length > 0) {
              Column({ space: 8 }) {
                Text('📋 支撑证据')
                  .fontSize(14)
                  .fontWeight(FontWeight.Medium)
                  .fontColor('#F59E0B')
                
                ForEach(this.selectedInsight!.evidence, (evidence: string) => {
                  Row({ space: 8 }) {
                    Text('•')
                      .fontSize(14)
                      .fontColor('rgba(150, 130, 200, 0.6)')
                    Text(evidence)
                      .fontSize(13)
                      .fontColor('rgba(200, 180, 255, 0.8)')
                      .layoutWeight(1)
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Top)
                })
              }
              .width('100%')
              .padding(12)
              .backgroundColor('rgba(245, 158, 11, 0.1)')
              .borderRadius(12)
            }
            
            // 建议
            if (this.selectedInsight!.recommendations.length > 0) {
              Column({ space: 8 }) {
                Text('💡 建议行动')
                  .fontSize(14)
                  .fontWeight(FontWeight.Medium)
                  .fontColor('#10B981')
                
                ForEach(this.selectedInsight!.recommendations, (rec: string, index: number) => {
                  Row({ space: 8 }) {
                    Text(`${index + 1}.`)
                      .fontSize(13)
                      .fontColor('#10B981')
                    Text(rec)
                      .fontSize(13)
                      .fontColor('rgba(200, 180, 255, 0.8)')
                      .layoutWeight(1)
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Top)
                })
              }
              .width('100%')
              .padding(12)
              .backgroundColor('rgba(16, 185, 129, 0.1)')
              .borderRadius(12)
            }
            
            // 指标信息
            Row({ space: 20 }) {
              Column({ space: 4 }) {
                Text('影响力')
                  .fontSize(11)
                  .fontColor('rgba(150, 130, 200, 0.5)')
                Text(`${Math.round(this.selectedInsight!.impact_score)}`)
                  .fontSize(20)
                  .fontWeight(FontWeight.Bold)
                  .fontColor(this.getLevelColor(this.selectedInsight!.level))
              }
              .alignItems(HorizontalAlign.Center)
              
              Column({ space: 4 }) {
                Text('置信度')
                  .fontSize(11)
                  .fontColor('rgba(150, 130, 200, 0.5)')
                Text(`${Math.round(this.selectedInsight!.confidence * 100)}%`)
                  .fontSize(20)
                  .fontWeight(FontWeight.Bold)
                  .fontColor('#8B5CF6')
              }
              .alignItems(HorizontalAlign.Center)
              
              Column({ space: 4 }) {
                Text('相关指标')
                  .fontSize(11)
                  .fontColor('rgba(150, 130, 200, 0.5)')
                Text(`${this.selectedInsight!.related_metrics.length}`)
                  .fontSize(20)
                  .fontWeight(FontWeight.Bold)
                  .fontColor('#3B82F6')
              }
              .alignItems(HorizontalAlign.Center)
            }
            .width('100%')
            .justifyContent(FlexAlign.SpaceAround)
            .padding(16)
            .backgroundColor('rgba(30, 20, 60, 0.4)')
            .borderRadius(12)
          }
        }
        .layoutWeight(1)
        .scrollBar(BarState.Off)
      }
      .width('90%')
      .height('75%')
      .padding(20)
      .backgroundColor('rgba(20, 10, 40, 0.95)')
      .borderRadius(20)
      .border({ width: 1, color: 'rgba(100, 80, 180, 0.3)' })
    }
    .width('100%')
    .height('100%')
  }
  
  @Builder
  LoadingView() {
    Column({ space: 16 }) {
      LoadingProgress()
        .width(48)
        .height(48)
        .color('#8B5CF6')
      
      Text('正在分析数据...')
        .fontSize(14)
        .fontColor('rgba(150, 130, 200, 0.6)')
    }
    .width('100%')
    .layoutWeight(1)
    .justifyContent(FlexAlign.Center)
    .alignItems(HorizontalAlign.Center)
  }
  
  @Builder
  ErrorView() {
    Column({ space: 16 }) {
      Text('😔')
        .fontSize(48)
      
      Text(this.errorMessage)
        .fontSize(14)
        .fontColor('rgba(200, 100, 100, 0.8)')
      
      Button('重试')
        .fontSize(14)
        .fontColor('#FFFFFF')
        .backgroundColor('#8B5CF6')
        .borderRadius(20)
        .padding({ left: 24, right: 24, top: 10, bottom: 10 })
        .onClick(() => {
          this.errorMessage = '';
          this.loadDashboard();
          this.loadInsights();
        })
    }
    .width('100%')
    .layoutWeight(1)
    .justifyContent(FlexAlign.Center)
    .alignItems(HorizontalAlign.Center)
  }
}

// 分类配置接口
interface CategoryConfig {
  id: string;
  name: string;
  icon: string;
  color: string;
}
