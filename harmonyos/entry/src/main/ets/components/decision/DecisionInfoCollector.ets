/**
 * 决策信息收集组件
 */
import { AppConstants } from '../../constants/AppConstants';

export interface DecisionInfo {
  question: string;
  options: string[];
  context: string;
}

@Component
export struct DecisionInfoCollector {
  @Link info: DecisionInfo;
  onSubmit: (info: DecisionInfo) => void = () => {};
  onCancel: () => void = () => {};

  @State currentStep: number = 0;
  @State optionInput: string = '';

  build() {
    Column() {
      // 标题
      Text(this.getStepTitle())
        .fontSize(20)
        .fontWeight(FontWeight.Bold)
        .fontColor('#333333')
        .margin({ bottom: 24 })

      // 步骤内容
      if (this.currentStep === 0) {
        this.QuestionStep()
      } else if (this.currentStep === 1) {
        this.OptionsStep()
      } else {
        this.ContextStep()
      }

      // 按钮
      Row({ space: 12 }) {
        if (this.currentStep > 0) {
          Button('上一步')
            .fontSize(16)
            .fontColor('#666666')
            .backgroundColor('#F5F5F5')
            .borderRadius(8)
            .layoutWeight(1)
            .onClick(() => {
              this.currentStep--;
            })
        }

        Button(this.currentStep === 2 ? '开始推演' : '下一步')
          .fontSize(16)
          .fontColor(Color.White)
          .backgroundColor(AppConstants.COLORS.PRIMARY)
          .borderRadius(8)
          .layoutWeight(1)
          .enabled(this.canProceed())
          .onClick(() => {
            if (this.currentStep === 2) {
              this.onSubmit(this.info);
            } else {
              this.currentStep++;
            }
          })
      }
      .width('100%')
      .margin({ top: 24 })
    }
    .width('90%')
    .padding(24)
    .backgroundColor(Color.White)
    .borderRadius(16)
    .shadow({
      radius: 16,
      color: '#00000030',
      offsetX: 0,
      offsetY: 4
    })
  }

  @Builder
  QuestionStep() {
    Column() {
      Text('请描述你的决策问题')
        .fontSize(14)
        .fontColor('#666666')
        .margin({ bottom: 12 })

      TextArea({ placeholder: '例如：我应该选择哪个工作机会？' })
        .width('100%')
        .height(120)
        .fontSize(15)
        .backgroundColor('#F5F5F5')
        .borderRadius(8)
        .onChange((value: string) => {
          this.info.question = value;
        })
    }
    .width('100%')
  }

  @Builder
  OptionsStep() {
    Column() {
      Text('添加你的选项（至少2个）')
        .fontSize(14)
        .fontColor('#666666')
        .margin({ bottom: 12 })

      // 已添加的选项
      ForEach(this.info.options, (option: string, index: number) => {
        Row() {
          Text(`${index + 1}. ${option}`)
            .fontSize(15)
            .fontColor('#333333')
            .layoutWeight(1)

          Text('🗑️')
            .fontSize(20)
            .onClick(() => {
              this.info.options.splice(index, 1);
            })
        }
        .width('100%')
        .padding(12)
        .backgroundColor('#F5F5F5')
        .borderRadius(8)
        .margin({ bottom: 8 })
      })

      // 添加选项输入框
      Row({ space: 8 }) {
        TextInput({ placeholder: '输入选项' })
          .layoutWeight(1)
          .fontSize(15)
          .backgroundColor('#F5F5F5')
          .borderRadius(8)
          .onChange((value: string) => {
            this.optionInput = value;
          })

        Button('添加')
          .fontSize(14)
          .fontColor(Color.White)
          .backgroundColor(AppConstants.COLORS.PRIMARY)
          .borderRadius(8)
          .enabled(this.optionInput.trim().length > 0)
          .onClick(() => {
            if (this.optionInput.trim()) {
              this.info.options.push(this.optionInput.trim());
              this.optionInput = '';
            }
          })
      }
      .width('100%')
      .margin({ top: 12 })
    }
    .width('100%')
  }

  @Builder
  ContextStep() {
    Column() {
      Text('补充背景信息（可选）')
        .fontSize(14)
        .fontColor('#666666')
        .margin({ bottom: 12 })

      TextArea({ placeholder: '例如：我的职业背景、个人偏好等' })
        .width('100%')
        .height(150)
        .fontSize(15)
        .backgroundColor('#F5F5F5')
        .borderRadius(8)
        .onChange((value: string) => {
          this.info.context = value;
        })
    }
    .width('100%')
  }

  private getStepTitle(): string {
    const titles = ['描述问题', '添加选项', '补充信息'];
    return titles[this.currentStep];
  }

  private canProceed(): boolean {
    if (this.currentStep === 0) {
      return this.info.question.trim().length > 0;
    } else if (this.currentStep === 1) {
      return this.info.options.length >= 2;
    }
    return true;
  }
}
