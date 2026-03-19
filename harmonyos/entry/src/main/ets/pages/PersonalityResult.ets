/**
 * 心理测评结果页面
 */
import router from '@ohos.router'

@Entry
@Component
struct PersonalityResult {
  @State profile: any = null
  @State summary: any = null
  
  aboutToAppear() {
    const params = router.getParams() as any
    this.profile = params?.profile
    this.summary = params?.summary
  }
  
  build() {
    Column() {
      // 顶部导航
      Row() {
        Image($r('app.media.back'))
          .width(24)
          .height(24)
          .onClick(() => router.back())
        
        Text('测评结果')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .layoutWeight(1)
          .textAlign(TextAlign.Center)
        
        Text('完成')
          .fontSize(16)
          .fontColor('#007DFF')
          .onClick(() => {
            router.clear()
            router.pushUrl({ url: 'pages/Index' })
          })
      }
      .width('100%')
      .padding(16)
      .justifyContent(FlexAlign.SpaceBetween)
      
      Scroll() {
        Column() {
          // 总体摘要
          Column() {
            Text('🎯 你的性格画像')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .margin({ bottom: 15 })
            
            if (this.summary) {
              Text(this.summary.personality_type)
                .fontSize(18)
                .fontColor('#007DFF')
                .margin({ bottom: 10 })
              
              Text(this.summary.description)
                .fontSize(14)
                .fontColor('#666')
                .lineHeight(22)
            }
          }
          .width('100%')
          .padding(20)
          .backgroundColor('#F8F9FA')
          .borderRadius(12)
          .margin({ bottom: 15 })
          
          // 决策风格
          this.buildCard('决策风格', this.getDecisionStyleText(this.summary?.decision_style))
          
          // 风险偏好
          this.buildCard('风险偏好', this.getRiskPreferenceText(this.summary?.risk_preference))
          
          // 生活优先级
          this.buildCard('生活优先级', this.getLifePriorityText(this.summary?.life_priority))
          
          // 详细数据
          if (this.profile) {
            Column() {
              Text('📊 详细分析')
                .fontSize(18)
                .fontWeight(FontWeight.Bold)
                .margin({ bottom: 15 })
              
              // 大五人格
              this.buildScoreItem('开放性', this.profile.openness)
              this.buildScoreItem('尽责性', this.profile.conscientiousness)
              this.buildScoreItem('外向性', this.profile.extraversion)
              this.buildScoreItem('宜人性', this.profile.agreeableness)
              this.buildScoreItem('情绪稳定性', 5 - this.profile.neuroticism)
            }
            .width('100%')
            .padding(20)
            .backgroundColor('#FFFFFF')
            .borderRadius(12)
            .border({ width: 1, color: '#E5E5E5' })
          }
        }
        .padding(16)
      }
      .layoutWeight(1)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }
  
  @Builder buildCard(title: string, content: string) {
    Column() {
      Text(title)
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .margin({ bottom: 8 })
      
      Text(content)
        .fontSize(14)
        .fontColor('#666')
        .lineHeight(20)
    }
    .width('100%')
    .padding(15)
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
    .border({ width: 1, color: '#E5E5E5' })
    .margin({ bottom: 15 })
    .alignItems(HorizontalAlign.Start)
  }
  
  @Builder buildScoreItem(label: string, score: number) {
    Row() {
      Text(label)
        .fontSize(14)
        .width('30%')
      
      Progress({
        value: score,
        total: 4,
        type: ProgressType.Linear
      })
        .width('50%')
        .margin({ left: 10, right: 10 })
      
      Text(score.toFixed(1))
        .fontSize(14)
        .fontColor('#007DFF')
    }
    .width('100%')
    .margin({ bottom: 12 })
  }
  
  getDecisionStyleText(style: string): string {
    const map = {
      'rational': '理性分析型 - 你倾向于通过逻辑分析和数据来做决策',
      'intuitive': '直觉感受型 - 你更相信自己的直觉和感觉',
      'balanced': '平衡综合型 - 你会综合理性和直觉来做决策'
    }
    return map[style] || '未知'
  }
  
  getRiskPreferenceText(preference: string): string {
    const map = {
      'risk_seeking': '风险偏好型 - 你愿意承担风险以追求更大回报',
      'risk_averse': '风险规避型 - 你倾向于规避风险，追求稳定',
      'risk_neutral': '风险中性型 - 你对风险持中性态度'
    }
    return map[preference] || '未知'
  }
  
  getLifePriorityText(priority: string): string {
    const map = {
      'health_first': '健康优先 - 你最看重身心健康',
      'career_first': '事业优先 - 你最看重职业发展',
      'relationship_first': '关系优先 - 你最看重人际关系',
      'freedom_first': '自由优先 - 你最看重个人自由',
      'wealth_first': '财富优先 - 你最看重财务状况',
      'balanced': '平衡发展 - 你追求各方面的平衡'
    }
    return map[priority] || '未知'
  }
}
