/**
 * Welcome Page - 欢迎页面
 * 应用启动时的欢迎和引导页面
 */

import router from '@ohos.router';

@Entry
@Component
struct Welcome {
  @State currentStep: number = 0;
  @State animationOpacity: number = 0;
  @State animationScale: number = 0.8;
  @State showContent: boolean = false;

  aboutToAppear() {
    // 初始化

    // 启动欢迎动画
    this.startWelcomeAnimation();
  }

  private startWelcomeAnimation() {
    // 延迟显示内容
    setTimeout(() => {
      this.showContent = true;
      animateTo({
        duration: 800,
        curve: Curve.EaseInOut
      }, () => {
        this.animationOpacity = 1;
        this.animationScale = 1;
      });
    }, 500);
  }

  private navigateToNext() {
    if (this.currentStep < 3) {
      this.currentStep++;
    } else {
      // 进入主应用
      router.replaceUrl({
        url: 'pages/Index'
      });
    }
  }

  private skipWelcome() {
    router.replaceUrl({
      url: 'pages/Index'
    });
  }

  build() {
    Stack() {
      // 背景渐变
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 45,
          colors: [['#667eea', 0.0], ['#764ba2', 1.0]]
        })

      Column() {
        // 顶部空间
        Blank()
          .height('10%')

        // 欢迎内容
        if (this.showContent) {
          Column() {
            // 标题
            Text('LifeSwarm')
              .fontSize(48)
              .fontWeight(FontWeight.Bold)
              .fontColor(Color.White)
              .textAlign(TextAlign.Center)
              .margin({ bottom: 16 })

            // 副标题
            Text('智能生活助手')
              .fontSize(20)
              .fontColor('rgba(255, 255, 255, 0.8)')
              .textAlign(TextAlign.Center)
              .margin({ bottom: 40 })

            // 步骤指示器
            Row() {
              ForEach([0, 1, 2, 3], (index: number) => {
                Circle()
                  .width(12)
                  .height(12)
                  .fill(index <= this.currentStep ? Color.White : 'rgba(255, 255, 255, 0.3)')
                  .margin({ right: 8 })
              })
            }
            .justifyContent(FlexAlign.Center)
            .margin({ bottom: 40 })

            // 步骤内容
            this.renderStepContent()

            // 底部空间
            Blank()
              .height('15%')

            // 按钮
            Row() {
              // 跳过按钮
              Button('跳过')
                .width('45%')
                .height(48)
                .backgroundColor('rgba(255, 255, 255, 0.2)')
                .fontColor(Color.White)
                .fontSize(16)
                .onClick(() => this.skipWelcome())

              Blank()
                .width('10%')

              // 下一步/开始按钮
              Button(this.currentStep === 3 ? '开始使用' : '下一步')
                .width('45%')
                .height(48)
                .backgroundColor(Color.White)
                .fontColor('#667eea')
                .fontSize(16)
                .fontWeight(FontWeight.Bold)
                .onClick(() => this.navigateToNext())
            }
            .width('100%')
            .padding({ left: 24, right: 24 })
          }
          .width('100%')
          .opacity(this.animationOpacity)
          .scale({ x: this.animationScale, y: this.animationScale })
        }
      }
      .width('100%')
      .height('100%')
      .padding({ left: 24, right: 24 })
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  renderStepContent() {
    Column() {
      if (this.currentStep === 0) {
        // 步骤1: 功能介绍
        Column() {
          Image($r('app.media.icon'))
            .width(80)
            .height(80)
            .margin({ bottom: 24 })

          Text('全面的健康监测')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .fontColor(Color.White)
            .textAlign(TextAlign.Center)
            .margin({ bottom: 12 })

          Text('实时监测心率、步数、睡眠等多维度健康数据')
            .fontSize(14)
            .fontColor('rgba(255, 255, 255, 0.7)')
            .textAlign(TextAlign.Center)
        }
      } else if (this.currentStep === 1) {
        // 步骤2: AI功能
        Column() {
          Text('🤖')
            .fontSize(60)
            .margin({ bottom: 24 })

          Text('智能AI助手')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .fontColor(Color.White)
            .textAlign(TextAlign.Center)
            .margin({ bottom: 12 })

          Text('与AI对话，获取个性化的健康建议和生活指导')
            .fontSize(14)
            .fontColor('rgba(255, 255, 255, 0.7)')
            .textAlign(TextAlign.Center)
        }
      } else if (this.currentStep === 2) {
        // 步骤3: 知识图谱
        Column() {
          Text('🧠')
            .fontSize(60)
            .margin({ bottom: 24 })

          Text('知识图谱')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .fontColor(Color.White)
            .textAlign(TextAlign.Center)
            .margin({ bottom: 12 })

          Text('可视化展示生活各领域的关系和洞察')
            .fontSize(14)
            .fontColor('rgba(255, 255, 255, 0.7)')
            .textAlign(TextAlign.Center)
        }
      } else {
        // 步骤4: 开始使用
        Column() {
          Text('✨')
            .fontSize(60)
            .margin({ bottom: 24 })

          Text('准备好了吗？')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .fontColor(Color.White)
            .textAlign(TextAlign.Center)
            .margin({ bottom: 12 })

          Text('点击"开始使用"进入应用，开启智能生活之旅')
            .fontSize(14)
            .fontColor('rgba(255, 255, 255, 0.7)')
            .textAlign(TextAlign.Center)
        }
      }
    }
    .width('100%')
    .alignItems(HorizontalAlign.Center)
  }
}

