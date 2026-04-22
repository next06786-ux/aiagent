/**
 * 智慧洞察页面
 * 展示三个专业Agent的洞察分析
 */
import router from '@ohos.router';
import { InsightsService } from '../services/InsightsService';
import { Insight, InsightType } from '../models/Insight';
import { AppConstants } from '../constants/AppConstants';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorToast } from '../components/common/ErrorToast';

@Entry
@Component
struct InsightsPage {
  @State selectedTab: number = 0;
  @State insights: Insight[] = [];
  @State isLoading: boolean = false;
  @State errorMessage: string = '';
  @State showError: boolean = false;

  private tabs: string[] = ['关系洞察', '教育洞察', '职业洞察'];
  private insightTypes: InsightType[] = ['relationship', 'education', 'career'];

  aboutToAppear() {
    this.loadInsights();
  }

  async loadInsights() {
    this.isLoading = true;
    this.errorMessage = '';

    try {
      const type = this.insightTypes[this.selectedTab];
      const insightsService = new InsightsService();
      this.insights = await insightsService.getInsights(type);
    } catch (error) {
      this.errorMessage = (error as Error).message || '加载洞察失败';
      this.showError = true;
    } finally {
      this.isLoading = false;
    }
  }

  onTabChange(index: number) {
    if (this.selectedTab !== index) {
      this.selectedTab = index;
      this.loadInsights();
    }
  }

  build() {
    Column() {
      // 顶部导航栏
      Row() {
        Text('←')
          .fontSize(24)
          .fontColor(Color.White)
          .onClick(() => {
            router.back();
          })

        Text('智慧洞察')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
          .margin({ left: 16 })

        Blank()
      }
      .width('100%')
      .height(56)
      .padding({ left: 16, right: 16 })
      .backgroundColor(AppConstants.COLORS.PRIMARY)

      // Tab切换
      Row() {
        ForEach(this.tabs, (tab: string, index: number) => {
          Column() {
            Text(tab)
              .fontSize(16)
              .fontColor(this.selectedTab === index ? AppConstants.COLORS.PRIMARY : Color.Gray)
              .fontWeight(this.selectedTab === index ? FontWeight.Bold : FontWeight.Normal)

            if (this.selectedTab === index) {
              Divider()
                .width(40)
                .height(3)
                .color(AppConstants.COLORS.PRIMARY)
                .margin({ top: 4 })
            }
          }
          .width(`${100 / this.tabs.length}%`)
          .height(48)
          .justifyContent(FlexAlign.Center)
          .onClick(() => {
            this.onTabChange(index);
          })
        })
      }
      .width('100%')
      .backgroundColor(Color.White)

      // 内容区域
      if (this.isLoading) {
        LoadingSpinner()
      } else {
        List({ space: 12 }) {
          ForEach(this.insights, (insight: Insight) => {
            ListItem() {
              this.InsightCard(insight)
            }
          })
        }
        .width('100%')
        .layoutWeight(1)
        .padding(16)
        .backgroundColor('#F5F5F5')
      }

      // 错误提示
      if (this.showError) {
        ErrorToast({
          message: this.errorMessage,
          onClose: () => {
            this.showError = false;
          }
        })
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }

  @Builder
  InsightCard(insight: Insight) {
    Column() {
      // 标题和时间
      Row() {
        Text(insight.title)
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor('#333333')
          .maxLines(2)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
          .layoutWeight(1)

        Text(this.formatDate(insight.created_at))
          .fontSize(12)
          .fontColor('#999999')
          .margin({ left: 8 })
      }
      .width('100%')
      .margin({ bottom: 8 })

      // 内容
      Text(insight.content)
        .fontSize(14)
        .fontColor('#666666')
        .lineHeight(22)
        .maxLines(5)
        .textOverflow({ overflow: TextOverflow.Ellipsis })
        .margin({ bottom: 12 })

      // 标签和置信度
      Row() {
        ForEach(insight.tags, (tag: string) => {
          Text(tag)
            .fontSize(12)
            .fontColor(AppConstants.COLORS.PRIMARY)
            .padding({ left: 8, right: 8, top: 4, bottom: 4 })
            .backgroundColor(AppConstants.COLORS.PRIMARY + '20')
            .borderRadius(4)
            .margin({ right: 8 })
        })

        Blank()

        Row() {
          Text('置信度: ')
            .fontSize(12)
            .fontColor('#999999')

          Text(`${(insight.confidence * 100).toFixed(0)}%`)
            .fontSize(12)
            .fontColor(this.getConfidenceColor(insight.confidence))
            .fontWeight(FontWeight.Bold)
        }
      }
      .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(12)
    .shadow({
      radius: 8,
      color: '#00000010',
      offsetX: 0,
      offsetY: 2
    })
  }

  private formatDate(timestamp: number): string {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return '今天';
    } else if (days === 1) {
      return '昨天';
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      return `${date.getMonth() + 1}月${date.getDate()}日`;
    }
  }

  private getConfidenceColor(confidence: number): ResourceColor {
    if (confidence >= 0.8) {
      return '#4CAF50';
    } else if (confidence >= 0.6) {
      return '#FF9800';
    } else {
      return '#F44336';
    }
  }
}
