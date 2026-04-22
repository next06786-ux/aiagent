/**
 * 登录页
 */
import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { AuthService } from '../services/AuthService';
import { StringUtils } from '../utils/StringUtils';
import { AppConstants } from '../constants/AppConstants';

@Entry
@Component
struct LoginPage {
  @State username: string = '';
  @State password: string = '';
  @State isLoading: boolean = false;
  @State showPassword: boolean = false;
  
  private authService = new AuthService();
  
  build() {
    Column() {
      // Logo和标题
      Column() {
        Text(AppConstants.APP_NAME)
          .fontSize(32)
          .fontWeight(FontWeight.Bold)
          .fontColor(AppConstants.COLORS.PRIMARY)
          .margin({ bottom: 8 })
        
        Text('智能生活助手')
          .fontSize(14)
          .fontColor('#999')
      }
      .margin({ top: 80, bottom: 60 })
      
      // 登录表单
      Column() {
        // 用户名输入
        Column() {
          Row() {
            Text('📧')
              .fontSize(20)
              .margin({ right: 12 })
            
            TextInput({ placeholder: '用户名或邮箱' })
              .layoutWeight(1)
              .backgroundColor(Color.Transparent)
              .onChange((value: string) => {
                this.username = value;
              })
          }
          .width('100%')
          .padding(16)
          .backgroundColor(Color.White)
          .borderRadius(12)
          .border({ width: 1, color: '#E0E0E0' })
        }
        .margin({ bottom: 16 })
        
        // 密码输入
        Column() {
          Row() {
            Text('🔒')
              .fontSize(20)
              .margin({ right: 12 })
            
            TextInput({
              placeholder: '密码'
            })
              .type(this.showPassword ? InputType.Normal : InputType.Password)
              .layoutWeight(1)
              .backgroundColor(Color.Transparent)
              .onChange((value: string) => {
                this.password = value;
              })
            
            Text(this.showPassword ? '👁️' : '👁️‍🗨️')
              .fontSize(20)
              .onClick(() => {
                this.showPassword = !this.showPassword;
              })
          }
          .width('100%')
          .padding(16)
          .backgroundColor(Color.White)
          .borderRadius(12)
          .border({ width: 1, color: '#E0E0E0' })
        }
        .margin({ bottom: 24 })
        
        // 登录按钮
        Button(this.isLoading ? '登录中...' : '登录')
          .width('100%')
          .height(50)
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
          .backgroundColor(AppConstants.COLORS.PRIMARY)
          .borderRadius(12)
          .enabled(!this.isLoading)
          .onClick(() => {
            this.handleLogin();
          })
        
        // 注册链接
        Row() {
          Text('还没有账号？')
            .fontSize(14)
            .fontColor('#999')
          
          Text('立即注册')
            .fontSize(14)
            .fontColor(AppConstants.COLORS.PRIMARY)
            .fontWeight(FontWeight.Medium)
            .onClick(() => {
              router.pushUrl({ url: 'pages/RegisterPage' });
            })
        }
        .margin({ top: 16 })
      }
      .width('100%')
      .padding(24)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }
  
  /**
   * 处理登录
   */
  async handleLogin() {
    // 验证输入
    if (StringUtils.isEmpty(this.username)) {
      promptAction.showToast({ message: '请输入用户名或邮箱' });
      return;
    }
    
    if (StringUtils.isEmpty(this.password)) {
      promptAction.showToast({ message: '请输入密码' });
      return;
    }
    
    this.isLoading = true;
    
    try {
      const result = await this.authService.login(this.username, this.password);
      
      promptAction.showToast({ message: '登录成功' });
      // 跳转到主页
      router.replaceUrl({ url: 'pages/IndexNew' });
    } catch (error) {
      console.error('登录失败:', error);
      promptAction.showToast({ message: '登录失败，请检查网络连接' });
    } finally {
      this.isLoading = false;
    }
  }
}
