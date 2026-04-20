/**
 * 认证页面 - 登录/注册合一
 * 对标 web/src/pages/AuthPage.tsx
 */
import router from '@ohos.router';
import { AuthService } from '../services/AuthService';
import { AppConstants } from '../constants/AppConstants';
import preferences from '@ohos.data.preferences';

@Entry
@Component
struct AuthPage {
  @State currentTab: number = 0; // 0=登录, 1=注册
  @State username: string = '';
  @State email: string = '';
  @State password: string = '';
  @State nickname: string = '';
  @State isLoading: boolean = false;
  @State errorMessage: string = '';
  @State showError: boolean = false;

  private authService = new AuthService();
  private tabs: string[] = ['登录', '注册'];

  /**
   * 表单验证
   */
  private validateForm(): boolean {
    // 验证用户名
    if (!this.username.trim()) {
      this.showErrorMessage('用户名不能为空');
      return false;
    }

    if (this.username.trim().length < 3) {
      this.showErrorMessage('用户名至少3个字符');
      return false;
    }

    // 注册模式验证邮箱
    if (this.currentTab === 1) {
      if (!this.email.trim()) {
        this.showErrorMessage('邮箱不能为空');
        return false;
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.email.trim())) {
        this.showErrorMessage('邮箱格式不正确');
        return false;
      }
    }

    // 验证密码
    if (!this.password) {
      this.showErrorMessage('密码不能为空');
      return false;
    }

    if (this.password.length < 6) {
      this.showErrorMessage('密码至少6个字符');
      return false;
    }

    return true;
  }

  /**
   * 提交表单
   */
  private async handleSubmit() {
    if (!this.validateForm()) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    try {
      if (this.currentTab === 0) {
        // 登录
        const result = await this.authService.login(
          this.username.trim(),
          this.password
        );

        // 保存登录状态
        const prefs = await preferences.getPreferences(getContext(this), 'lifeswarm_auth');
        await prefs.put('token', result.token);
        await prefs.put('user_id', result.user_id);
        await prefs.put('username', result.username);
        await prefs.flush();

        // 跳转到主页
        router.replaceUrl({ url: 'pages/HomePage' });
      } else {
        // 注册
        const result = await this.authService.register(
          this.username.trim(),
          this.email.trim(),
          this.password,
          this.nickname.trim() || this.username.trim()
        );

        // 保存登录状态
        const prefs = await preferences.getPreferences(getContext(this), 'lifeswarm_auth');
        await prefs.put('token', result.token);
        await prefs.put('user_id', result.user_id);
        await prefs.put('username', result.username);
        await prefs.flush();

        // 跳转到主页
        router.replaceUrl({ url: 'pages/HomePage' });
      }
    } catch (error) {
      this.showErrorMessage((error as Error).message || '操作失败，请稍后重试');
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * 显示错误消息
   */
  private showErrorMessage(message: string) {
    this.errorMessage = message;
    this.showError = true;

    // 3秒后自动隐藏
    setTimeout(() => {
      this.showError = false;
    }, 3000);
  }

  /**
   * 切换Tab
   */
  private onTabChange(index: number) {
    if (this.currentTab !== index) {
      this.currentTab = index;
      this.errorMessage = '';
      this.showError = false;
    }
  }

  build() {
    Stack() {
      Column() {
        // 顶部Logo和标题
        Column() {
          Text('择境')
            .fontSize(32)
            .fontWeight(FontWeight.Bold)
            .fontColor(Color.White)
            .margin({ bottom: 8 })

          Text('ChoiceRealm')
            .fontSize(16)
            .fontColor('rgba(255, 255, 255, 0.8)')
            .margin({ bottom: 24 })

          Text('智能决策支持系统')
            .fontSize(14)
            .fontColor('rgba(255, 255, 255, 0.6)')
        }
        .width('100%')
        .padding({ top: 60, bottom: 40 })
        .alignItems(HorizontalAlign.Center)

        // 认证卡片
        Column() {
          // Tab切换
          Row() {
            ForEach(this.tabs, (tab: string, index: number) => {
              Column() {
                Text(tab)
                  .fontSize(16)
                  .fontColor(this.currentTab === index ? AppConstants.COLORS.PRIMARY : '#666666')
                  .fontWeight(this.currentTab === index ? FontWeight.Bold : FontWeight.Normal)

                if (this.currentTab === index) {
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
          .margin({ bottom: 24 })

          // 表单
          Column({ space: 16 }) {
            // 用户名
            TextInput({ placeholder: '用户名' })
              .width('100%')
              .height(48)
              .fontSize(15)
              .backgroundColor('#F5F5F5')
              .borderRadius(12)
              .onChange((value: string) => {
                this.username = value;
              })

            // 邮箱（仅注册时显示）
            if (this.currentTab === 1) {
              TextInput({ placeholder: '邮箱' })
                .width('100%')
                .height(48)
                .fontSize(15)
                .type(InputType.Email)
                .backgroundColor('#F5F5F5')
                .borderRadius(12)
                .onChange((value: string) => {
                  this.email = value;
                })
            }

            // 昵称（仅注册时显示）
            if (this.currentTab === 1) {
              TextInput({ placeholder: '昵称（可选）' })
                .width('100%')
                .height(48)
                .fontSize(15)
                .backgroundColor('#F5F5F5')
                .borderRadius(12)
                .onChange((value: string) => {
                  this.nickname = value;
                })
            }

            // 密码
            TextInput({ placeholder: '密码' })
              .width('100%')
              .height(48)
              .fontSize(15)
              .type(InputType.Password)
              .backgroundColor('#F5F5F5')
              .borderRadius(12)
              .onChange((value: string) => {
                this.password = value;
              })

            // 提交按钮
            Button(this.isLoading ? '处理中...' : (this.currentTab === 0 ? '登录' : '注册'))
              .width('100%')
              .height(48)
              .fontSize(16)
              .fontColor(Color.White)
              .backgroundColor(AppConstants.COLORS.PRIMARY)
              .borderRadius(12)
              .enabled(!this.isLoading)
              .onClick(() => {
                this.handleSubmit();
              })
          }
          .width('100%')
        }
        .width('90%')
        .padding(24)
        .backgroundColor(Color.White)
        .borderRadius(20)
        .shadow({
          radius: 20,
          color: 'rgba(0, 0, 0, 0.1)',
          offsetX: 0,
          offsetY: 4
        })

        // 底部提示
        Text(this.currentTab === 0 ? '还没有账号？点击上方"注册"' : '已有账号？点击上方"登录"')
          .fontSize(14)
          .fontColor('rgba(255, 255, 255, 0.6)')
          .margin({ top: 24 })
      }
      .width('100%')
      .height('100%')
      .padding(20)
      .justifyContent(FlexAlign.Center)

      // 错误提示
      if (this.showError) {
        Column() {
          Text(this.errorMessage)
            .fontSize(14)
            .fontColor(Color.White)
            .padding(16)
            .backgroundColor('rgba(255, 59, 48, 0.9)')
            .borderRadius(12)
        }
        .width('90%')
        .position({ x: '5%', y: 100 })
      }
    }
    .width('100%')
    .height('100%')
    .linearGradient({
      angle: 135,
      colors: [
        [AppConstants.COLORS.PRIMARY, 0.0],
        ['#6B48FF', 1.0]
      ]
    })
  }
}
