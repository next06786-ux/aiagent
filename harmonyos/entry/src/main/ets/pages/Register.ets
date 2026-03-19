/**
 * 注册页面
 * Register Page
 */
import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { getAuthService } from '../service/AuthService';

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
  
  private authService = getAuthService();
  
  build() {
    Column() {
      // 顶部导航
      Row() {
        Text('←')
          .fontSize(24)
          .fontColor('#007AFF')
          .onClick(() => {
            router.back();
          })
        
        Text('注册账号')
          .fontSize(18)
          .fontWeight(FontWeight.Medium)
          .margin({ left: 12 })
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 16, bottom: 16 })
      
      // 注册表单
      Scroll() {
        Column() {
          // 用户名
          Column() {
            Text('用户名 *')
              .fontSize(14)
              .fontColor('#333333')
              .alignSelf(ItemAlign.Start)
              .margin({ bottom: 8 })
            
            TextInput({ placeholder: '3-20个字符，字母数字下划线' })
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
          
          // 邮箱
          Column() {
            Text('邮箱 *')
              .fontSize(14)
              .fontColor('#333333')
              .alignSelf(ItemAlign.Start)
              .margin({ bottom: 8 })
            
            TextInput({ placeholder: '请输入邮箱地址' })
              .width('100%')
              .height(48)
              .fontSize(16)
              .type(InputType.Email)
              .backgroundColor('#f5f5f5')
              .borderRadius(8)
              .onChange((value: string) => {
                this.email = value;
              })
          }
          .width('100%')
          .margin({ bottom: 20 })
          
          // 昵称
          Column() {
            Text('昵称')
              .fontSize(14)
              .fontColor('#333333')
              .alignSelf(ItemAlign.Start)
              .margin({ bottom: 8 })
            
            TextInput({ placeholder: '选填，默认使用用户名' })
              .width('100%')
              .height(48)
              .fontSize(16)
              .backgroundColor('#f5f5f5')
              .borderRadius(8)
              .onChange((value: string) => {
                this.nickname = value;
              })
          }
          .width('100%')
          .margin({ bottom: 20 })
          
          // 密码
          Column() {
            Text('密码 *')
              .fontSize(14)
              .fontColor('#333333')
              .alignSelf(ItemAlign.Start)
              .margin({ bottom: 8 })
            
            TextInput({ placeholder: '至少6位字符' })
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
          .width('100%')
          .margin({ bottom: 20 })
          
          // 确认密码
          Column() {
            Text('确认密码 *')
              .fontSize(14)
              .fontColor('#333333')
              .alignSelf(ItemAlign.Start)
              .margin({ bottom: 8 })
            
            TextInput({ placeholder: '请再次输入密码' })
              .width('100%')
              .height(48)
              .fontSize(16)
              .type(this.showPassword ? InputType.Normal : InputType.Password)
              .backgroundColor('#f5f5f5')
              .borderRadius(8)
              .onChange((value: string) => {
                this.confirmPassword = value;
              })
          }
          .width('100%')
          .margin({ bottom: 32 })
          
          // 注册按钮
          Button(this.isLoading ? '注册中...' : '注册')
            .width('100%')
            .height(48)
            .fontSize(16)
            .fontColor('#ffffff')
            .backgroundColor('#007AFF')
            .borderRadius(8)
            .enabled(!this.isLoading)
            .onClick(() => {
              this.handleRegister();
            })
          
          // 登录链接
          Row() {
            Text('已有账号? ')
              .fontSize(14)
              .fontColor('#666666')
            
            Text('立即登录')
              .fontSize(14)
              .fontColor('#007AFF')
              .onClick(() => {
                router.back();
              })
          }
          .margin({ top: 20 })
        }
        .width('100%')
        .padding({ left: 32, right: 32, top: 20, bottom: 40 })
      }
      .layoutWeight(1)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#ffffff')
  }
  
  /**
   * 处理注册
   */
  private async handleRegister() {
    // 验证输入
    if (!this.username.trim()) {
      promptAction.showToast({ message: '请输入用户名' });
      return;
    }
    
    // 验证用户名格式
    const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
    if (!usernameRegex.test(this.username.trim())) {
      promptAction.showToast({ message: '用户名格式不正确（3-20个字符，仅支持字母、数字、下划线）' });
      return;
    }
    
    if (!this.email.trim()) {
      promptAction.showToast({ message: '请输入邮箱' });
      return;
    }
    
    // 验证邮箱格式
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(this.email.trim())) {
      promptAction.showToast({ message: '邮箱格式不正确' });
      return;
    }
    
    if (!this.password) {
      promptAction.showToast({ message: '请输入密码' });
      return;
    }
    
    if (this.password.length < 6) {
      promptAction.showToast({ message: '密码长度不能少于6位' });
      return;
    }
    
    if (this.password !== this.confirmPassword) {
      promptAction.showToast({ message: '两次输入的密码不一致' });
      return;
    }
    
    this.isLoading = true;
    
    try {
      await this.authService.register(
        this.username.trim(),
        this.email.trim(),
        this.password,
        this.nickname.trim() || undefined
      );
      
      promptAction.showToast({ message: '注册成功' });
      
      // 跳转到主页
      router.replaceUrl({ url: 'pages/Index' });
      
    } catch (err) {
      const error = err as Error;
      promptAction.showToast({ message: error.message });
    } finally {
      this.isLoading = false;
    }
  }
}
