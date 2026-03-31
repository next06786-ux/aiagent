/**
 * 修改密码页面
 */
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'
import { getAuthService } from '../service/AuthService'
import { Theme } from '../common/Theme'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'

@Entry
@Component
struct ChangePassword {
  @State oldPwd: string = ''
  @State newPwd: string = ''
  @State confirmPwd: string = ''
  @State isSaving: boolean = false
  private authService = getAuthService()

  private async changePassword() {
    if (!this.oldPwd || !this.newPwd || !this.confirmPwd) {
      promptAction.showToast({ message: '请填写所有字段' }); return
    }
    if (this.newPwd.length < 6) {
      promptAction.showToast({ message: '新密码至少6位' }); return
    }
    if (this.newPwd !== this.confirmPwd) {
      promptAction.showToast({ message: '两次密码不一致' }); return
    }
    this.isSaving = true
    try {
      const userId = this.authService.getCurrentUserId()
      const req = http.createHttp()
      const res = await req.request(`${ApiConfig.getBaseUrl()}/api/auth/change-password`, {
        method: http.RequestMethod.POST,
        header: { 'Content-Type': 'application/json' },
        extraData: JSON.stringify({ user_id: userId, old_password: this.oldPwd, new_password: this.newPwd })
      })
      req.destroy()
      const result = JSON.parse(res.result as string) as Record<string, Object>
      if ((result.code as number) === 200) {
        promptAction.showToast({ message: '密码修改成功' })
        router.back()
      } else {
        promptAction.showToast({ message: (result.message as string) || '修改失败' })
      }
    } catch (e) {
      promptAction.showToast({ message: '网络错误' })
    } finally { this.isSaving = false }
  }

  build() {
    Column() {
      Row() {
        Text('←').fontSize(24).fontColor(Theme.Color.Primary).onClick(() => router.back())
        Text('修改密码').fontSize(18).fontWeight(FontWeight.Medium).fontColor(Theme.Color.TextPrimary)
          .layoutWeight(1).margin({ left: 12 })
      }.width('100%').padding({ left: 16, right: 16, top: 12, bottom: 12 })
      .backgroundColor(Theme.Color.BackgroundPrimary)

      Scroll() {
        Column({ space: 16 }) {
          Column({ space: 8 }) {
            Text('当前密码').fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
            TextInput({ placeholder: '请输入当前密码' })
              .type(InputType.Password).fontSize(15).fontColor(Theme.Color.TextPrimary)
              .backgroundColor(Theme.Color.BackgroundTertiary).borderRadius(Theme.Radius.m).padding(14)
              .onChange((v: string) => { this.oldPwd = v })
          }.width('100%').padding(16)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l).border({ width: 1, color: Theme.Color.BorderLight })

          Column({ space: 8 }) {
            Text('新密码').fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
            TextInput({ placeholder: '至少6位' })
              .type(InputType.Password).fontSize(15).fontColor(Theme.Color.TextPrimary)
              .backgroundColor(Theme.Color.BackgroundTertiary).borderRadius(Theme.Radius.m).padding(14)
              .onChange((v: string) => { this.newPwd = v })
            TextInput({ placeholder: '再次输入新密码' })
              .type(InputType.Password).fontSize(15).fontColor(Theme.Color.TextPrimary)
              .backgroundColor(Theme.Color.BackgroundTertiary).borderRadius(Theme.Radius.m).padding(14)
              .onChange((v: string) => { this.confirmPwd = v })
          }.width('100%').padding(16)
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .borderRadius(Theme.Radius.l).border({ width: 1, color: Theme.Color.BorderLight })

          Button(this.isSaving ? '修改中...' : '确认修改')
            .width('100%').height(52).fontSize(16).fontWeight(600).fontColor('#FFFFFF')
            .backgroundColor(Theme.Color.Primary).borderRadius(Theme.Radius.l)
            .enabled(!this.isSaving).onClick(() => this.changePassword())
        }.padding({ left: 16, right: 16, bottom: 60 })
      }.scrollBar(BarState.Off).edgeEffect(EdgeEffect.Spring).layoutWeight(1)
    }.width('100%').height('100%').backgroundColor(Theme.Color.BackgroundPrimary)
  }
}
