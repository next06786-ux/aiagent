/**
 * 注册页面 - HarmonyOS 6 流体设计
 * Register Page
 */
import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { getAuthService } from '../service/AuthService';
import { Theme } from '../common/Theme';

interface FormField {
  label: string;
  placeholder: string;
  required: boolean;
  isPassword: boolean;
}

@Entry
@Component
struct Register {
  @State username: string = '';
  @State email: string = '';
  @State password: string = '';
  @State confirmPassword: string = '';
  @State nickname: string = '';
  @State isLoading: boolean = false;
  @State showPassword: boolean = false;
  @State showContent: boolean = false;

  private authService = getAuthService();

  aboutToAppear() {
    setTimeout(() => { this.showContent = true; }, 50);
  }

  build() {
    Column() {
      // 顶部导航
      Row() {
        Text('←')
          .fontSize(24)
          .fontColor(Theme.Color.Primary)
          .onClick(() => { router.back(); })

        Text('注册账号')
          .fontSize(18).fontWeight(FontWeight.Medium).fontColor(Theme.Color.TextPrimary)
          .layoutWeight(1).margin({ left: 12 })
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 12, bottom: 12 })
      .backgroundColor(Theme.Color.BackgroundPrimary)

      Scroll() {
        Column({ space: 18 }) {
          // 用户名
          this.buildField('用户名 *', '3-20个字符，字母数字下划线', false, 0,
            (v: string) => { this.username = v; })
          // 邮箱
          this.buildField('邮箱 *', '请输入邮箱地址', false, 1,
            (v: string) => { this.email = v; })
          // 昵称
          this.buildField('昵称', '选填，默认使用用户名', false, 2,
            (v: string) => { this.nickname = v; })
          // 密码
          this.buildField('密码 *', '至少6位字符', true, 3,
            (v: string) => { this.password = v; })
          // 确认密码
          this.buildField('确认密码 *', '请再次输入密码', true, 4,
            (v: string) => { this.confirmPassword = v; })

          // 注册按钮
          Button(this.isLoading ? '注册中...' : '注册')
            .width('100%').height(52).fontSize(16).fontWeight(600)
            .fontColor('#FFFFFF')
            .backgroundColor(Theme.Color.Primary)
            .borderRadius(Theme.Radius.l)
            .shadow(Theme.Shadow.GlowPrimary)
            .enabled(!this.isLoading)
            .onClick(() => { this.handleRegister(); })
            .opacity(this.showContent ? 1 : 0)
            .translate({ y: this.showContent ? 0 : 20 })
            .animation({ duration: 600, curve: Curve.Smooth, delay: 400 })

          // 登录链接
          Row() {
            Text('已有账号? ').fontSize(14).fontColor(Theme.Color.TextSecondary)
            Text('立即登录').fontSize(14).fontWeight(600).fontColor(Theme.Color.Primary)
              .onClick(() => { router.back(); })
          }
          .opacity(this.showContent ? 1 : 0)
          .animation({ duration: 600, curve: Curve.Smooth, delay: 450 })
        }
        .width('100%')
        .padding({ left: 28, right: 28, top: 20, bottom: 60 })
      }
      .scrollBar(BarState.Off)
      .edgeEffect(EdgeEffect.Spring)
      .layoutWeight(1)
    }
    .width('100%')
    .height('100%')
    .backgroundColor(Theme.Color.BackgroundPrimary)
  }

  @Builder
  buildField(label: string, placeholder: string, isPassword: boolean, index: number,
    onChange: (value: string) => void) {
    Column({ space: 8 }) {
      Text(label)
        .fontSize(14).fontWeight(500).fontColor(Theme.Color.TextPrimary)
        .alignSelf(ItemAlign.Start)

      TextInput({ placeholder: placeholder })
        .width('100%').height(52).fontSize(16)
        .type(isPassword && !this.showPassword ? InputType.Password : InputType.Normal)
        .fontColor(Theme.Color.TextPrimary)
        .placeholderColor(Theme.Color.TextTertiary)
        .backgroundColor(Theme.Color.BackgroundTertiary)
        .borderRadius(Theme.Radius.l)
        .border({ width: 1, color: Theme.Color.BorderLight })
        .padding({ left: 16, right: 16 })
        .onChange(onChange)
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({ duration: 600, curve: Curve.Smooth, delay: 50 + index * 70 })
  }

  private async handleRegister() {
    if (!this.username.trim()) {
      promptAction.showToast({ message: '请输入用户名' }); return;
    }
    const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
    if (!usernameRegex.test(this.username.trim())) {
      promptAction.showToast({ message: '用户名格式不正确（3-20个字符，仅支持字母、数字、下划线）' }); return;
    }
    if (!this.email.trim()) {
      promptAction.showToast({ message: '请输入邮箱' }); return;
    }
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(this.email.trim())) {
      promptAction.showToast({ message: '邮箱格式不正确' }); return;
    }
    if (!this.password) {
      promptAction.showToast({ message: '请输入密码' }); return;
    }
    if (this.password.length < 6) {
      promptAction.showToast({ message: '密码长度不能少于6位' }); return;
    }
    if (this.password !== this.confirmPassword) {
      promptAction.showToast({ message: '两次输入的密码不一致' }); return;
    }
    this.isLoading = true;
    try {
      await this.authService.register(
        this.username.trim(), this.email.trim(), this.password,
        this.nickname.trim() || undefined
      );
      promptAction.showToast({ message: '注册成功' });
      router.replaceUrl({ url: 'pages/AgentHome' });
    } catch (err) {
      const error = err as Error;
      promptAction.showToast({ message: error.message });
    } finally { this.isLoading = false; }
  }
}
