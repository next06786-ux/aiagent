/**
 * 登录页面 - HarmonyOS 6 流体设计
 * Login Page
 */
import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { getAuthService } from '../service/AuthService';
import { getUserSessionManager } from '../service/UserSessionManager';
import { Theme } from '../common/Theme';

@Entry
@Component
struct Login {
  @State username: string = '';
  @State password: string = '';
  @State isLoading: boolean = false;
  @State showPassword: boolean = false;
  @State showContent: boolean = false;

  private authService = getAuthService();

  aboutToAppear() {
    setTimeout(() => { this.showContent = true; }, 50);
  }

  build() {
    Column() {
      // 顶部 Hero 区域
      Stack({ alignContent: Alignment.Center }) {
        Column()
          .width('100%').height('100%')
          .linearGradient({ angle: 135, colors: [['#667eea', 0], ['#764ba2', 1]] })
          .opacity(0.1)

        Circle({ width: 160, height: 160 })
          .fill('#667eea').opacity(0.15).blur(60)
          .position({ x: -40, y: -20 })

        Circle({ width: 100, height: 100 })
          .fill('#764ba2').opacity(0.1).blur(50)
          .position({ x: '70%', y: '60%' })

        Column({ space: 12 }) {
          Stack() {
            Circle({ width: 80, height: 80 })
              .fill(Theme.Color.Primary).opacity(0.15)
            Circle({ width: 64, height: 64 })
              .linearGradient({ angle: 135, colors: [['#667eea', 0], ['#764ba2', 1]] })
            Text('LS')
              .fontSize(28).fontWeight(800).fontColor('#FFFFFF')
          }.width(80).height(80)

          Text('LifeSwarm')
            .fontSize(28).fontWeight(700).fontColor(Theme.Color.TextPrimary)
          Text('智能生活助手')
            .fontSize(14).fontColor(Theme.Color.TextSecondary)
        }
      }
      .width('100%')
      .height(260)
      .opacity(this.showContent ? 1 : 0)
      .scale({ x: this.showContent ? 1 : 0.95, y: this.showContent ? 1 : 0.95 })
      .animation({ duration: 700, curve: Curve.Smooth, delay: 0 })

      // 登录表单
      Column({ space: 20 }) {
        Column({ space: 8 }) {
          Text('用户名/邮箱')
            .fontSize(14).fontWeight(500).fontColor(Theme.Color.TextPrimary)
            .alignSelf(ItemAlign.Start)
          TextInput({ placeholder: '请输入用户名或邮箱' })
            .width('100%').height(52).fontSize(16)
            .fontColor(Theme.Color.TextPrimary)
            .placeholderColor(Theme.Color.TextTertiary)
            .backgroundColor(Theme.Color.BackgroundTertiary)
            .borderRadius(Theme.Radius.l)
            .border({ width: 1, color: Theme.Color.BorderLight })
            .padding({ left: 16, right: 16 })
            .onChange((value: string) => { this.username = value; })
        }
        .opacity(this.showContent ? 1 : 0)
        .translate({ y: this.showContent ? 0 : 20 })
        .animation({ duration: 600, curve: Curve.Smooth, delay: 100 })

        Column({ space: 8 }) {
          Text('密码')
            .fontSize(14).fontWeight(500).fontColor(Theme.Color.TextPrimary)
            .alignSelf(ItemAlign.Start)
          TextInput({ placeholder: '请输入密码' })
            .width('100%').height(52).fontSize(16)
            .type(this.showPassword ? InputType.Normal : InputType.Password)
            .fontColor(Theme.Color.TextPrimary)
            .placeholderColor(Theme.Color.TextTertiary)
            .backgroundColor(Theme.Color.BackgroundTertiary)
            .borderRadius(Theme.Radius.l)
            .border({ width: 1, color: Theme.Color.BorderLight })
            .padding({ left: 16, right: 16 })
            .onChange((value: string) => { this.password = value; })
        }
        .opacity(this.showContent ? 1 : 0)
        .translate({ y: this.showContent ? 0 : 20 })
        .animation({ duration: 600, curve: Curve.Smooth, delay: 200 })

        Row() {
          Blank()
          Text('忘记密码?')
            .fontSize(13).fontColor(Theme.Color.Primary)
            .onClick(() => { promptAction.showToast({ message: '请联系管理员重置密码' }); })
        }
        .width('100%')
        .opacity(this.showContent ? 1 : 0)
        .animation({ duration: 600, curve: Curve.Smooth, delay: 250 })

        Button(this.isLoading ? '登录中...' : '登录')
          .width('100%').height(52).fontSize(16).fontWeight(600)
          .fontColor('#FFFFFF')
          .backgroundColor(Theme.Color.Primary)
          .borderRadius(Theme.Radius.l)
          .shadow(Theme.Shadow.GlowPrimary)
          .enabled(!this.isLoading)
          .onClick(() => { this.handleLogin(); })
          .opacity(this.showContent ? 1 : 0)
          .translate({ y: this.showContent ? 0 : 20 })
          .animation({ duration: 600, curve: Curve.Smooth, delay: 300 })

        Row() {
          Text('还没有账号? ').fontSize(14).fontColor(Theme.Color.TextSecondary)
          Text('立即注册').fontSize(14).fontWeight(600).fontColor(Theme.Color.Primary)
            .onClick(() => { router.pushUrl({ url: 'pages/Register' }); })
        }
        .opacity(this.showContent ? 1 : 0)
        .animation({ duration: 600, curve: Curve.Smooth, delay: 350 })
      }
      .width('100%')
      .padding({ left: 28, right: 28 })
      .layoutWeight(1)
    }
    .width('100%')
    .height('100%')
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }

  private async handleLogin() {
    if (!this.username.trim()) {
      promptAction.showToast({ message: '请输入用户名或邮箱' });
      return;
    }
    if (!this.password) {
      promptAction.showToast({ message: '请输入密码' });
      return;
    }
    this.isLoading = true;
    try {
      const loginResult = await this.authService.login(this.username.trim(), this.password);
      const sessionManager = getUserSessionManager();
      await sessionManager.onUserLogin(loginResult.user_id);
      promptAction.showToast({ message: '登录成功' });
      router.replaceUrl({ url: 'pages/AgentHome' });
    } catch (err) {
      const error = err as Error;
      promptAction.showToast({ message: error.message });
    } finally {
      this.isLoading = false;
    }
  }
}
