/**
 * 平行人生页面 - 塔罗牌游戏
 */
import router from '@ohos.router';
import { ParallelLifeService } from '../services/ParallelLifeService';
import { AppConstants } from '../constants/AppConstants';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorToast } from '../components/common/ErrorToast';

interface TarotCard {
  id: string;
  name: string;
  description: string;
  image_url: string;
  position: string;
  interpretation: string;
}

interface TarotReading {
  session_id: string;
  question: string;
  cards: TarotCard[];
  overall_interpretation: string;
  advice: string;
}

@Entry
@Component
struct ParallelLifePage {
  @State currentStep: number = 0; // 0: 输入问题, 1: 抽牌, 2: 结果
  @State question: string = '';
  @State reading: TarotReading | null = null;
  @State selectedCards: number[] = [];
  @State isLoading: boolean = false;
  @State errorMessage: string = '';
  @State showError: boolean = false;

  private cardCount: number = 3; // 三张牌

  build() {
    Column() {
      // 顶部导航栏
      Row() {
        Text('←')
          .fontSize(24)
          .fontColor('#333')
          .onClick(() => {
            router.back();
          })

        Text('平行人生')
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

      // 内容区域
      if (this.isLoading) {
        LoadingSpinner()
      } else {
        if (this.currentStep === 0) {
          this.QuestionInput()
        } else if (this.currentStep === 1) {
          this.CardSelection()
        } else {
          this.ReadingResult()
        }
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
  QuestionInput() {
    Column() {
      // 标题
      Text('探索你的平行人生')
        .fontSize(24)
        .fontWeight(FontWeight.Bold)
        .fontColor('#333333')
        .margin({ top: 40, bottom: 16 })

      Text('请输入你想要探索的问题')
        .fontSize(16)
        .fontColor('#666666')
        .margin({ bottom: 32 })

      // 输入框
      TextArea({ placeholder: '例如：我应该选择哪个职业方向？' })
        .width('100%')
        .height(120)
        .fontSize(16)
        .backgroundColor(Color.White)
        .borderRadius(12)
        .padding(16)
        .onChange((value: string) => {
          this.question = value;
        })
        .margin({ bottom: 32 })

      // 开始按钮
      Button('开始探索')
        .width('100%')
        .height(48)
        .fontSize(16)
        .fontColor(Color.White)
        .backgroundColor(AppConstants.COLORS.PRIMARY)
        .borderRadius(24)
        .enabled(this.question.trim().length > 0)
        .onClick(() => {
          this.startReading();
        })
    }
    .width('100%')
    .padding(24)
  }

  @Builder
  CardSelection() {
    Column() {
      Text('请选择三张牌')
        .fontSize(20)
        .fontWeight(FontWeight.Bold)
        .fontColor('#333333')
        .margin({ top: 24, bottom: 32 })

      // 卡牌网格
      Grid() {
        ForEach(Array.from({ length: 12 }, (_, i) => i), (index: number) => {
          GridItem() {
            this.CardBack(index)
          }
        })
      }
      .columnsTemplate('1fr 1fr 1fr')
      .rowsGap(16)
      .columnsGap(16)
      .width('100%')
      .layoutWeight(1)
      .padding(24)

      // 已选择的牌
      Text(`已选择 ${this.selectedCards.length}/${this.cardCount} 张`)
        .fontSize(16)
        .fontColor('#666666')
        .margin({ bottom: 16 })

      // 确认按钮
      Button('确认选择')
        .width('90%')
        .height(48)
        .fontSize(16)
        .fontColor(Color.White)
        .backgroundColor(AppConstants.COLORS.PRIMARY)
        .borderRadius(24)
        .enabled(this.selectedCards.length === this.cardCount)
        .margin({ bottom: 24 })
        .onClick(() => {
          this.confirmSelection();
        })
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  CardBack(index: number) {
    Column() {
      Text('🔮')
        .fontSize(48)
    }
    .width('100%')
    .aspectRatio(0.7)
    .backgroundColor(this.selectedCards.includes(index) ? AppConstants.COLORS.PRIMARY : '#E0E0E0')
    .borderRadius(12)
    .justifyContent(FlexAlign.Center)
    .onClick(() => {
      this.selectCard(index);
    })
  }

  @Builder
  ReadingResult() {
    Scroll() {
      Column() {
        // 问题
        Column() {
          Text('你的问题')
            .fontSize(16)
            .fontColor('#999999')
            .margin({ bottom: 8 })

          Text(this.reading?.question || '')
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .fontColor('#333333')
        }
        .width('100%')
        .padding(16)
        .backgroundColor(Color.White)
        .borderRadius(12)
        .margin({ bottom: 16 })

        // 卡牌
        Text('你抽到的牌')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor('#333333')
          .margin({ bottom: 12 })

        ForEach(this.reading?.cards || [], (card: TarotCard) => {
          this.TarotCardView(card)
        })

        // 总体解读
        Column() {
          Text('总体解读')
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .fontColor('#333333')
            .margin({ bottom: 12 })

          Text(this.reading?.overall_interpretation || '')
            .fontSize(14)
            .fontColor('#666666')
            .lineHeight(22)
            .margin({ bottom: 16 })

          Text('建议')
            .fontSize(16)
            .fontWeight(FontWeight.Bold)
            .fontColor('#333333')
            .margin({ bottom: 8 })

          Text(this.reading?.advice || '')
            .fontSize(14)
            .fontColor('#666666')
            .lineHeight(22)
        }
        .width('100%')
        .padding(16)
        .backgroundColor(Color.White)
        .borderRadius(12)
        .margin({ top: 16, bottom: 16 })

        // 重新开始按钮
        Button('重新开始')
          .width('100%')
          .height(48)
          .fontSize(16)
          .fontColor(Color.White)
          .backgroundColor(AppConstants.COLORS.PRIMARY)
          .borderRadius(24)
          .margin({ bottom: 24 })
          .onClick(() => {
            this.reset();
          })
      }
      .width('100%')
      .padding(16)
    }
    .width('100%')
    .layoutWeight(1)
  }

  @Builder
  TarotCardView(card: TarotCard) {
    Column() {
      Row() {
        Column() {
          Text(card.name)
            .fontSize(16)
            .fontWeight(FontWeight.Bold)
            .fontColor('#333333')
            .margin({ bottom: 4 })

          Text(card.position)
            .fontSize(12)
            .fontColor('#999999')
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)

        Text('🎴')
          .fontSize(48)
      }
      .width('100%')
      .margin({ bottom: 12 })

      Text(card.interpretation)
        .fontSize(14)
        .fontColor('#666666')
        .lineHeight(22)
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(12)
    .margin({ bottom: 12 })
  }

  private async startReading() {
    this.currentStep = 1;
    this.selectedCards = [];
  }

  private selectCard(index: number) {
    const cardIndex = this.selectedCards.indexOf(index);
    if (cardIndex > -1) {
      this.selectedCards.splice(cardIndex, 1);
    } else if (this.selectedCards.length < this.cardCount) {
      this.selectedCards.push(index);
    }
  }

  private async confirmSelection() {
    this.isLoading = true;
    this.errorMessage = '';

    try {
      const parallelLifeService = new ParallelLifeService();
      const gameSession = await parallelLifeService.getTarotReading('test_user');
      
      // 创建TarotCard数组
      const cards: TarotCard[] = this.selectedCards.map((cardIndex: number) => ({
        id: `card_${cardIndex}`,
        name: `塔罗牌 ${cardIndex + 1}`,
        description: '塔罗牌描述',
        image_url: '',
        position: '位置',
        interpretation: '解读'
      }));
      
      this.reading = {
        session_id: gameSession.game_id,
        question: this.question,
        cards: cards,
        overall_interpretation: '整体解读',
        advice: '建议'
      };
      this.currentStep = 2;
    } catch (error) {
      this.errorMessage = (error as Error).message || '获取解读失败';
      this.showError = true;
    } finally {
      this.isLoading = false;
    }
  }

  private reset() {
    this.currentStep = 0;
    this.question = '';
    this.reading = null;
    this.selectedCards = [];
  }
}
