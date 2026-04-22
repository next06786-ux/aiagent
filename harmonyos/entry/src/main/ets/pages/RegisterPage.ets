/**
 * 注册页
 */
import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { AuthService } from '../services/AuthService';
import { HttpClient } from '../utils/HttpClient';
import { StringUtils } from '../utils/StringUtils';
import { AppConstants } from '../constants/AppConstants';
import { common } from '@kit.AbilityKit';

@Entry
@Component
struct RegisterPage {
  @State username: string = '';
  @State email: string = '';
  @State password: string = '';
  @State confirmPassword: string = '';
  @State nickname: string = '';
  @State isLoading: boolean = false;
  @State showPassword: boolean = false;
  
  private authService = new AuthService();
  private context: common.UIAbilityContext | null = null;
  
  aboutToAppear() {
    try {
      // 安全地获取context
      this.context = getContext(this) as common.UIAbilityContext;
      
      if (this.context) {
        // 设置context
        this.authService.setContext(this.context);
        HttpClient.getInstance().setContext(this.context);
        console.info('RegisterPage: Context设置成功');
      } else {
        console.error('RegisterPage: 无法获取Context');
      }
    } catch (error) {
      console.error('RegisterPage: 初始化失败', JSON.stringify(error));
    }
  }
  
  build() {
    Column() {
      // 顶部导航
      Row() {
        Button('返回')
          .fontSize(14)
          .backgroundColor(Color.Transparent)
          .fontColor(AppConstants.COLORS.PRIMARY)
          .onClick(() => {
            router.back();
          })
        
        Blank()
        
        Text('注册账号')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
      }
      .width('100%')
      .padding(16)
      
      Scroll() {
        Column() {
          // 用户名
          Column() {
            Text('用户名')
              .fontSize(14)
              .fontColor('#666')
              .alignSelf(ItemAlign.Start)
              .margin({ bottom: 8 })
            
            TextInput({ placeholder: '3-20个字符，字母数字下划线' })
              .width('100%')
              .padding(16)
              .backgroundColor(Color.White)
              .borderRadius(12)
              .border({ width: 1, color: '#E0E0E0' })
              .onChange((value: string) => {
                this.username = value;
              })
          }
          .width('100%')
          .margin({ bottom: 16 })
          
          // 邮箱
          Column() {
            Text('邮箱')
              .fontSize(14)
              .fontColor('#666')
              .alignSelf(ItemAlign.Start)
              .margin({ bottom: 8 })
            
            TextInput({ placeholder: '请输入邮箱地址' })
              .width('100%')
              .padding(16)
              .backgroundColor(Color.White)
              .borderRadius(12)
              .border({ width: 1, color: '#E0E0E0' })
              .type(InputType.Email)
              .onChange((value: string) => {
                this.email = value;
              })
          }
          .width('100%')
          .margin({ bottom: 16 })
          
          // 昵称
          Column() {
            Text('昵称')
              .fontSize(14)
              .fontColor('#666')
              .alignSelf(ItemAlign.Start)
              .margin({ bottom: 8 })
            
            TextInput({ placeholder: '请输入昵称' })
              .width('100%')
              .padding(16)
              .backgroundColor(Color.White)
              .borderRadius(12)
              .border({ width: 1, color: '#E0E0E0' })
              .onChange((value: string) => {
                this.nickname = value;
              })
          }
          .width('100%')
          .margin({ bottom: 16 })
          
          // 密码
          Column() {
            Text('密码')
              .fontSize(14)
              .fontColor('#666')
              .alignSelf(ItemAlign.Start)
              .margin({ bottom: 8 })
            
            TextInput({ placeholder: '至少6个字符' })
              .width('100%')
              .padding(16)
              .backgroundColor(Color.White)
              .borderRadius(12)
              .border({ width: 1, color: '#E0E0E0' })
              .type(this.showPassword ? InputType.Normal : InputType.Password)
              .onChange((value: string) => {
                this.password = value;
              })
          }
          .width('100%')
          .margin({ bottom: 16 })
          
          // 确认密码
          Column() {
            Text('确认密码')
              .fontSize(14)
              .fontColor('#666')
              .alignSelf(ItemAlign.Start)
              .margin({ bottom: 8 })
            
            TextInput({ placeholder: '请再次输入密码' })
              .width('100%')
              .padding(16)
              .backgroundColor(Color.White)
              .borderRadius(12)
              .border({ width: 1, color: '#E0E0E0' })
              .type(this.showPassword ? InputType.Normal : InputType.Password)
              .onChange((value: string) => {
                this.confirmPassword = value;
              })
          }
          .width('100%')
          .margin({ bottom: 24 })
          
          // 注册按钮
          Button(this.isLoading ? '注册中...' : '注册')
            .width('100%')
            .height(50)
            .fontSize(16)
            .fontWeight(FontWeight.Medium)
            .backgroundColor(AppConstants.COLORS.PRIMARY)
            .borderRadius(12)
            .enabled(!this.isLoading)
            .onClick(() => {
              this.handleRegister();
            })
        }
        .padding(24)
      }
      .layoutWeight(1)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }
  
  /**
   * 处理注册
   */
  async handleRegister() {
    // 验证输入
    if (StringUtils.isEmpty(this.username)) {
      promptAction.showToast({ message: '请输入用户名' });
      return;
    }
    
    if (!StringUtils.isUsername(this.username)) {
      promptAction.showToast({ message: '用户名格式不正确' });
      return;
    }
    
    if (StringUtils.isEmpty(this.email)) {
      promptAction.showToast({ message: '请输入邮箱' });
      return;
    }
    
    if (!StringUtils.isEmail(this.email)) {
      promptAction.showToast({ message: '邮箱格式不正确' });
      return;
    }
    
    if (StringUtils.isEmpty(this.nickname)) {
      promptAction.showToast({ message: '请输入昵称' });
      return;
    }
    
    if (StringUtils.isEmpty(this.password)) {
      promptAction.showToast({ message: '请输入密码' });
      return;
    }
    
    if (!StringUtils.isValidPassword(this.password)) {
      promptAction.showToast({ message: '密码至少6个字符' });
      return;
    }
    
    if (this.password !== this.confirmPassword) {
      promptAction.showToast({ message: '两次密码输入不一致' });
      return;
    }
    
    this.isLoading = true;
    
    try {
      const result = await this.authService.register(
        this.username,
        this.email,
        this.password,
        this.nickname
      );
      
      promptAction.showToast({ message: '注册成功' });
      // 跳转到主页
      router.replaceUrl({ url: 'pages/IndexNew' });
    } catch (error) {
      console.error('注册失败:', error);
      promptAction.showToast({ message: '注册失败，请检查网络连接' });
    } finally {
      this.isLoading = false;
    }
  }
}
