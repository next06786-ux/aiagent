/**
 * 用户个人资料页面
 */
import router from '@ohos.router';
import { AuthService } from '../services/AuthService';
import { AppConstants } from '../constants/AppConstants';
import { ErrorToast } from '../components/common/ErrorToast';

@Entry
@Component
struct UserProfilePage {
  @State username: string = '';
  @State email: string = '';
  @State avatar: string = '';
  @State errorMessage: string = '';
  @State showError: boolean = false;

  aboutToAppear() {
    this.loadUserInfo();
  }

  async loadUserInfo() {
    // 从本地存储加载用户信息
    const userInfo = AppStorage.get<Record<string, string>>('userInfo');
    if (userInfo) {
      this.username = userInfo['username'] || '';
      this.email = userInfo['email'] || '';
      this.avatar = userInfo['avatar'] || '';
    }
  }

  async logout() {
    try {
      const authService = new AuthService();
      await authService.logout();
      router.replaceUrl({ url: 'pages/LoginPage' });
    } catch (error) {
      this.errorMessage = (error as Error).message || '退出登录失败';
      this.showError = true;
    }
  }

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

        Text('个人资料')
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

      Scroll() {
        Column() {
          // 头像
          Column() {
            Text(this.username?.charAt(0) || '👤')
              .width(80)
              .height(80)
              .borderRadius(40)
              .backgroundColor('#E8F4FF')
              .fontSize(40)
              .fontColor('#0A59F7')
              .textAlign(TextAlign.Center)
              .padding({ top: 18 })
              .margin({ bottom: 12 })

            Text(this.username)
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .fontColor('#333333')
              .margin({ bottom: 4 })

            Text(this.email)
              .fontSize(14)
              .fontColor('#999999')
          }
          .width('100%')
          .padding(24)
          .backgroundColor(Color.White)
          .margin({ bottom: 12 })

          // 设置项
          this.SettingItem('账号设置', () => {})
          this.SettingItem('隐私设置', () => {})
          this.SettingItem('通知设置', () => {})
          this.SettingItem('关于我们', () => {})

          // 退出登录按钮
          Button('退出登录')
            .width('90%')
            .height(48)
            .fontSize(16)
            .fontColor(Color.White)
            .backgroundColor('#F44336')
            .borderRadius(24)
            .margin({ top: 24, bottom: 24 })
            .onClick(() => {
              this.logout();
            })
        }
        .width('100%')
      }
      .layoutWeight(1)

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
  SettingItem(title: string, onClick: () => void) {
    Row() {
      Text(title)
        .fontSize(16)
        .fontColor('#333333')
        .layoutWeight(1)

      Text('→')
        .width(20)
        .height(20)
        .fontSize(20)
        .fontColor('#999')
        .textAlign(TextAlign.Center)
    }
    .width('100%')
    .height(56)
    .padding({ left: 16, right: 16 })
    .backgroundColor(Color.White)
    .margin({ bottom: 1 })
    .onClick(onClick)
  }
}
