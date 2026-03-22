/**
 * 登录页面
 * Login Page
 */
import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { getAuthService } from '../service/AuthService';
import { getUserSessionManager } from '../service/UserSessionManager';

@Entry
@Component
struct Login {
  @State username: string = '';
  @State password: string = '';
  @State isLoading: boolean = false;
  @State showPassword: boolean = false;
  
  private authService = getAuthService();
  
  build() {
    Column() {
      // 顶部Logo区域
      Column() {
        // Logo占位符
        Column() {
          Text('LS')
            .fontSize(36)
            .fontWeight(FontWeight.Bold)
            .fontColor('#ffffff')
        }
        .width(80)
        .height(80)
        .backgroundColor('#007AFF')
        .borderRadius(40)
        .justifyContent(FlexAlign.Center)
        .margin({ bottom: 16 })
        
        Text('LifeSwarm')
          .fontSize(32)
          .fontWeight(FontWeight.Bold)
          .fontColor('#1a1a1a')
          .margin({ bottom: 8 })
        
        Text('智能生活助手')
          .fontSize(16)
          .fontColor('#666666')
      }
      .width('100%')
      .padding({ top: 60, bottom: 40 })
      
      // 登录表单
      Column() {
        // 用户名输入框
        Column() {
          Text('用户名/邮箱')
            .fontSize(14)
            .fontColor('#333333')
            .alignSelf(ItemAlign.Start)
            .margin({ bottom: 8 })
          
          TextInput({ placeholder: '请输入用户名或邮箱' })
            .width('100%')
            .height(48)
            .fontSize(16)
            .backgroundColor('#f5f5f5')
            .borderRadius(8)
            .onChange((value: string) => {
              this.username = value;
            })
        }
        .width('100%')
        .margin({ bottom: 20 })
        
        // 密码输入框
        Column() {
          Text('密码')
            .fontSize(14)
            .fontColor('#333333')
            .alignSelf(ItemAlign.Start)
            .margin({ bottom: 8 })
          
          Row() {
            TextInput({ placeholder: '请输入密码' })
              .width('100%')
              .height(48)
              .fontSize(16)
              .type(this.showPassword ? InputType.Normal : InputType.Password)
              .backgroundColor('#f5f5f5')
              .borderRadius(8)
              .onChange((value: string) => {
                this.password = value;
              })
          }
        }
        .width('100%')
        .margin({ bottom: 12 })
        
        // 忘记密码
        Row() {
          Text('忘记密码?')
            .fontSize(14)
            .fontColor('#007AFF')
            .onClick(() => {
              promptAction.showToast({ message: '请联系管理员重置密码' });
            })
        }
        .width('100%')
        .justifyContent(FlexAlign.End)
        .margin({ bottom: 32 })
        
        // 登录按钮
        Button(this.isLoading ? '登录中...' : '登录')
          .width('100%')
          .height(48)
          .fontSize(16)
          .fontColor('#ffffff')
          .backgroundColor('#007AFF')
          .borderRadius(8)
          .enabled(!this.isLoading)
          .onClick(() => {
            this.handleLogin();
          })
        
        // 注册链接
        Row() {
          Text('还没有账号? ')
            .fontSize(14)
            .fontColor('#666666')
          
          Text('立即注册')
            .fontSize(14)
            .fontColor('#007AFF')
            .onClick(() => {
              router.pushUrl({ url: 'pages/Register' });
            })
        }
        .margin({ top: 20 })
      }
      .width('100%')
      .padding({ left: 32, right: 32 })
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#ffffff')
  }
  
  /**
   * 处理登录
   */
  private async handleLogin() {
    // 验证输入
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
      
      // 更新用户会话管理器
      const sessionManager = getUserSessionManager();
      await sessionManager.onUserLogin(loginResult.user_id);
      
      console.info('[Login] 登录成功，用户ID:', loginResult.user_id);
      
      promptAction.showToast({ message: '登录成功' });
      
      // 跳转到主页
      router.replaceUrl({ url: 'pages/AgentHome' });
      
    } catch (err) {
      const error = err as Error;
      promptAction.showToast({ message: error.message });
    } finally {
      this.isLoading = false;
    }
  }
}
