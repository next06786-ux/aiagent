/**
 * 编辑资料页面
 */
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'
import { getAuthService, UserInfo } from '../service/AuthService'
import { Theme } from '../common/Theme'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'

@Entry
@Component
struct EditProfile {
  @State userInfo: UserInfo | null = null
  @State nickname: string = ''
  @State bio: string = ''
  @State isSaving: boolean = false
  @State showContent: boolean = false
  private authService = getAuthService()

  aboutToAppear() {
    this.loadUserInfo()
    setTimeout(() => { this.showContent = true }, 50)
  }

  private async loadUserInfo() {
    try {
      this.userInfo = await this.authService.getCurrentUserAsync()
      if (this.userInfo) {
        this.nickname = this.userInfo.nickname || ''
        this.bio = (this.userInfo as Record<string, string>)['bio'] || ''
      }
    } catch (e) {}
  }

  private async saveProfile() {
    if (!this.nickname.trim()) {
      promptAction.showToast({ message: '昵称不能为空' })
      return
    }
    this.isSaving = true
    try {
      const userId = this.authService.getCurrentUserId()
      const req = http.createHttp()
      const res = await req.request(`${ApiConfig.getBaseUrl()}/api/auth/user/${userId}`, {
        method: http.RequestMethod.PUT,
        header: { 'Content-Type': 'application/json' },
        extraData: JSON.stringify({ nickname: this.nickname.trim(), bio: this.bio.trim() })
      })
      req.destroy()
      if (res.responseCode === 200) {
        promptAction.showToast({ message: '保存成功' })
        router.back()
      } else {
        promptAction.showToast({ message: '保存失败，请重试' })
      }
    } catch (e) {
      promptAction.showToast({ message: '网络错误' })
    } finally { this.isSaving = false }
  }

  build() {
    Column() {
      Row() {
        Text('←').fontSize(24).fontColor(Theme.Color.Primary).onClick(() => router.back())
        Text('编辑资料').fontSize(18).fontWeight(FontWeight.Medium).fontColor(Theme.Color.TextPrimary)
          .layoutWeight(1).margin({ left: 12 })
        Button(this.isSaving ? '保存中...' : '保存')
          .fontSize(14).fontColor('#FFFFFF').backgroundColor(Theme.Color.Primary)
          .borderRadius(Theme.Radius.round).padding({ left: 16, right: 16, top: 8, bottom: 8 })
          .enabled(!this.isSaving).onClick(() => this.saveProfile())
      }.width('100%').padding({ left: 16, right: 16, top: 12, bottom: 12 })
      .backgroundColor(Theme.Color.BackgroundPrimary)

      Scroll() {
        Column({ space: 20 }) {
          // 头像区域
          Column({ space: 12 }) {
            Stack() {
              Circle({ width: 80, height: 80 })
                .linearGradient({ angle: 135, colors: [['#667eea', 0], ['#764ba2', 1]] })
              Text(this.nickname.substring(0, 1).toUpperCase() || 'U')
                .fontSize(32).fontWeight(700).fontColor('#FFFFFF')
            }.width(80).height(80)
            Text('点击更换头像').fontSize(12).fontColor(Theme.Color.TextTertiary)
          }.width('100%').alignItems(HorizontalAlign.Center).padding(20)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l).border({ width: 1, color: Theme.Color.BorderLight })

          // 昵称
          Column({ space: 8 }) {
            Text('昵称').fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
            TextInput({ placeholder: '请输入昵称', text: this.nickname })
              .fontSize(15).fontColor(Theme.Color.TextPrimary)
              .backgroundColor(Theme.Color.BackgroundTertiary)
              .borderRadius(Theme.Radius.m).padding(14)
              .onChange((v: string) => { this.nickname = v })
          }.width('100%').padding(16)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l).border({ width: 1, color: Theme.Color.BorderLight })

          // 个人简介
          Column({ space: 8 }) {
            Text('个人简介').fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
            TextArea({ placeholder: '介绍一下自己...', text: this.bio })
              .fontSize(15).fontColor(Theme.Color.TextPrimary)
              .backgroundColor(Theme.Color.BackgroundTertiary)
              .borderRadius(Theme.Radius.m).height(100)
              .onChange((v: string) => { this.bio = v })
          }.width('100%').padding(16)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l).border({ width: 1, color: Theme.Color.BorderLight })
        }.padding({ left: 16, right: 16, bottom: 60 })
      }.scrollBar(BarState.Off).edgeEffect(EdgeEffect.Spring).layoutWeight(1)
    }.width('100%').height('100%').backgroundColor(Theme.Color.BackgroundPrimary)
  }
}
