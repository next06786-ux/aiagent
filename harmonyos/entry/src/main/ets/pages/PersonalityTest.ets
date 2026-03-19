/**
 * 心理测评页面
 */
import router from '@ohos.router'
import { HttpUtil } from '../utils/HttpUtil'

interface Question {
  id: number
  text: string
  dimension: string
  subdimension: string
  options: Array<{ value: number, text: string }>
}

@Entry
@Component
struct PersonalityTest {
  @State questions: Question[] = []
  @State currentIndex: number = 0
  @State answers: Record<number, number> = {}
  @State isLoading: boolean = true
  @State isSubmitting: boolean = false
  @State testInfo: any = null
  
  aboutToAppear() {
    this.loadQuestions()
  }
  
  async loadQuestions() {
    try {
      const response = await HttpUtil.get('/api/personality/questions')
      if (response.code === 200) {
        this.questions = response.data.questions
        this.testInfo = response.data.test_info
        this.isLoading = false
      }
    } catch (error) {
      console.error('加载题目失败:', error)
    }
  }
  
  selectAnswer(questionId: number, value: number) {
    this.answers[questionId] = value
  }
  
  canGoNext(): boolean {
    const currentQuestion = this.questions[this.currentIndex]
    return this.answers[currentQuestion?.id] !== undefined
  }
  
  goNext() {
    if (this.currentIndex < this.questions.length - 1) {
      this.currentIndex++
    }
  }
  
  goPrevious() {
    if (this.currentIndex > 0) {
      this.currentIndex--
    }
  }
  
  async submitTest() {
    if (Object.keys(this.answers).length < this.questions.length) {
      return
    }
    
    this.isSubmitting = true
    
    try {
      const userId = AppStorage.Get('userId') || 'default_user'
      const response = await HttpUtil.post('/api/personality/submit', {
        user_id: userId,
        answers: this.answers
      })
      
      if (response.code === 200) {
        // 跳转到结果页面
        router.pushUrl({
          url: 'pages/PersonalityResult',
          params: {
            profile: response.data.profile,
            summary: response.data.summary
          }
        })
      }
    } catch (error) {
      console.error('提交测评失败:', error)
    } finally {
      this.isSubmitting = false
    }
  }
  
  build() {
    Column() {
      // 顶部导航
      Row() {
        Image($r('app.media.back'))
          .width(24)
          .height(24)
          .onClick(() => router.back())
        
        Text('心理测评')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .layoutWeight(1)
          .textAlign(TextAlign.Center)
        
        Text('')
          .width(24)
      }
      .width('100%')
      .padding(16)
      .justifyContent(FlexAlign.SpaceBetween)
      
      if (this.isLoading) {
        // 加载中
        Column() {
          LoadingProgress()
            .width(50)
            .height(50)
          Text('加载中...')
            .fontSize(14)
            .margin({ top: 10 })
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
      } else {
        // 进度条
        Row() {
          Text(`${this.currentIndex + 1}/${this.questions.length}`)
            .fontSize(14)
            .fontColor('#666')
          
          Progress({
            value: this.currentIndex + 1,
            total: this.questions.length,
            type: ProgressType.Linear
          })
            .width('70%')
            .margin({ left: 10, right: 10 })
          
          Text(`${Math.round((this.currentIndex + 1) / this.questions.length * 100)}%`)
            .fontSize(14)
            .fontColor('#666')
        }
        .width('100%')
        .padding({ left: 16, right: 16, top: 10, bottom: 10 })
        
        // 题目内容
        Column() {
          if (this.questions[this.currentIndex]) {
            const question = this.questions[this.currentIndex]
            
            Text(question.text)
              .fontSize(18)
              .fontWeight(FontWeight.Medium)
              .margin({ bottom: 30 })
              .textAlign(TextAlign.Center)
            
            // 选项
            ForEach(question.options, (option: any) => {
              Button(option.text)
                .width('100%')
                .height(50)
                .fontSize(16)
                .backgroundColor(
                  this.answers[question.id] === option.value ? '#007DFF' : '#F5F5F5'
                )
                .fontColor(
                  this.answers[question.id] === option.value ? '#FFFFFF' : '#333333'
                )
                .margin({ bottom: 15 })
                .onClick(() => {
                  this.selectAnswer(question.id, option.value)
                })
            })
          }
        }
        .layoutWeight(1)
        .padding(20)
        .justifyContent(FlexAlign.Center)
        
        // 底部按钮
        Row() {
          if (this.currentIndex > 0) {
            Button('上一题')
              .width('45%')
              .height(45)
              .backgroundColor('#F5F5F5')
              .fontColor('#333')
              .onClick(() => this.goPrevious())
          }
          
          if (this.currentIndex < this.questions.length - 1) {
            Button('下一题')
              .width(this.currentIndex > 0 ? '45%' : '100%')
              .height(45)
              .enabled(this.canGoNext())
              .onClick(() => this.goNext())
          } else {
            Button(this.isSubmitting ? '提交中...' : '提交测评')
              .width(this.currentIndex > 0 ? '45%' : '100%')
              .height(45)
              .enabled(!this.isSubmitting && Object.keys(this.answers).length === this.questions.length)
              .onClick(() => this.submitTest())
          }
        }
        .width('100%')
        .padding(16)
        .justifyContent(FlexAlign.SpaceBetween)
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#FFFFFF')
  }
}
