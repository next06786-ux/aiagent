/**
 * 用户个人中心 - HarmonyOS 6 流体设计
 * User Profile Page
 */
import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { getAuthService, UserInfo } from '../service/AuthService';
import { Theme } from '../common/Theme';
import { SimpleIcon } from '../components/IconRenderer';

interface ProfileMenuItem {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
  color: string;
  route?: string;
  action?: () => void;
}

@Entry
@Component
struct UserProfile {
  @State userInfo: UserInfo | null = null;
  @State isLoading: boolean = false;
  @State showContent: boolean = false;
  @State selectedMenu: number = -1;
  
  private authService = getAuthService();
  private profileScroller: Scroller = new Scroller();
  
  private menuItems: ProfileMenuItem[] = [
    {
      id: 'edit_profile',
      title: '编辑资料',
      subtitle: '更新个人信息',
      icon: 'user',
      color: '#667eea',
      route: 'pages/EditProfile'
    },
    {
      id: 'change_password',
      title: '修改密码',
      subtitle: '保护账号安全',
      icon: 'lock',
      color: '#764ba2',
      route: 'pages/ChangePassword'
    },
    {
      id: 'notification',
      title: '通知设置',
      subtitle: '管理消息提醒',
      icon: 'bell',
      color: '#f093fb'
    },
    {
      id: 'privacy',
      title: '隐私设置',
      subtitle: '控制数据共享',
      icon: 'shield',
      color: '#f5576c'
    },
    {
      id: 'about',
      title: '关于应用',
      subtitle: '版本信息与帮助',
      icon: 'info',
      color: '#4facfe'
    }
  ];
  
  aboutToAppear() {
    this.loadUserInfo();
    setTimeout(() => {
      this.showContent = true;
    }, 50);
  }
  
  build() {
    Stack() {
      // 背景
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor(Theme.Color.BackgroundPrimary)
      
      // 主内容
      Column() {
        // 顶部导航栏
        Row() {
          Text('←')
            .fontSize(24)
            .fontColor(Theme.Color.Primary)
            .onClick(() => {
              router.back();
            })
          
          Text('个人中心')
            .fontSize(18)
            .fontWeight(FontWeight.Medium)
            .fontColor(Theme.Color.TextPrimary)
            .layoutWeight(1)
            .margin({ left: 12 })
          
          // 设置按钮
          Stack() {
            Circle({ width: 40, height: 40 })
              .fill(Theme.Color.GlassMedium)
            
            SimpleIcon({
              iconName: 'settings',
              iconSize: 20,
              color: Theme.Color.TextSecondary
            })
          }
          .width(40)
          .height(40)
          .onClick(() => {
            promptAction.showToast({ message: '设置功能开发中' });
          })
        }
        .width('100%')
        .padding({ left: 16, right: 16, top: 12, bottom: 12 })
        .backgroundColor(Theme.Color.BackgroundPrimary)
        
        if (this.userInfo) {
          Scroll(this.profileScroller) {
            Column({ space: 24 }) {
              // 用户卡片 - Hero区域
              this.buildUserCard()
              
              // 统计数据区域
              this.buildStatsSection()
              
              // 功能菜单
              this.buildMenuSection()
              
              // 底部操作
              this.buildActionButtons()
            }
            .width('100%')
            .padding({ left: 16, right: 16, bottom: 100 })
          }
          .scrollBar(BarState.Off)
          .edgeEffect(EdgeEffect.Spring)
          .layoutWeight(1)
        } else {
          // 未登录状态
          Column() {
            SimpleIcon({
              iconName: 'user',
              iconSize: 64,
              color: Theme.Color.TextTertiary
            })
            
            Text('未登录')
              .fontSize(18)
              .fontColor(Theme.Color.TextSecondary)
              .margin({ top: 16, bottom: 20 })
            
            Button('去登录')
              .width(200)
              .height(48)
              .fontSize(16)
              .fontColor('#ffffff')
              .backgroundColor(Theme.Color.Primary)
              .borderRadius(Theme.Radius.l)
              .onClick(() => {
                router.pushUrl({ url: 'pages/Login' });
              })
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
          .alignItems(HorizontalAlign.Center)
        }
      }
      .width('100%')
      .height('100%')
    }
    .width('100%')
    .height('100%')
  }
  
  /**
   * 用户卡片 - HarmonyOS 6 流体设计
   */
  @Builder
  buildUserCard() {
    Stack({ alignContent: Alignment.BottomStart }) {
      // 渐变背景
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 135,
          colors: [
            ['#667eea', 0.0],
            ['#764ba2', 1.0]
          ]
        })
        .opacity(0.12)
      
      // 光晕效果
      Circle({ width: 150, height: 150 })
        .fill('#667eea')
        .opacity(0.2)
        .blur(60)
        .position({ x: -40, y: -40 })
      
      Circle({ width: 100, height: 100 })
        .fill('#764ba2')
        .opacity(0.15)
        .blur(50)
        .position({ x: '80%', y: '60%' })
      
      // 内容
      Row({ space: 16 }) {
        // 头像
        Stack() {
          Circle({ width: 80, height: 80 })
            .fill(`linear-gradient(135deg, #667eea, #764ba2)`)
          
          Text(this.userInfo!.nickname.substring(0, 1).toUpperCase())
            .fontSize(36)
            .fontWeight(FontWeight.Bold)
            .fontColor('#ffffff')
        }
        .width(80)
        .height(80)
        
        // 用户信息
        Column({ space: 8 }) {
          Text(this.userInfo!.nickname)
            .fontSize(24)
            .fontWeight(700)
            .fontColor(Theme.Color.TextPrimary)
          
          Text(`@${this.userInfo!.username}`)
            .fontSize(14)
            .fontColor(Theme.Color.TextSecondary)
          
          Row({ space: 8 }) {
            Circle({ width: 8, height: 8 })
              .fill('#00C853')
            
            Text('在线')
              .fontSize(12)
              .fontColor(Theme.Color.TextTertiary)
          }
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)
      }
      .padding(20)
      .width('100%')
    }
    .width('100%')
    .height(160)
    .backgroundColor(Theme.Color.GlassHeavy)
    .backdropBlur(Theme.Blur.Heavy)
    .borderRadius(Theme.Radius.xl)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Medium)
    .opacity(this.showContent ? 1 : 0)
    .scale({ x: this.showContent ? 1 : 0.95, y: this.showContent ? 1 : 0.95 })
    .animation({
      duration: 700,
      curve: Curve.Smooth,
      delay: 0
    })
  }
  
  /**
   * 统计数据区域
   */
  @Builder
  buildStatsSection() {
    Row({ space: 12 }) {
      this.buildStatItem('数据收集', '已启用', '#00C853')
      this.buildStatItem('账号等级', 'VIP', '#FFB800')
      this.buildStatItem('连续登录', '7天', '#FF6B6B')
    }
    .width('100%')
    .opacity(this.showContent ? 1 : 0)
    .translate({ y: this.showContent ? 0 : 20 })
    .animation({
      duration: 600,
      curve: Curve.Smooth,
      delay: 100
    })
  }
  
  /**
   * 统计项
   */
  @Builder
  buildStatItem(label: string, value: string, color: string) {
    Column({ space: 8 }) {
      Text(value)
        .fontSize(18)
        .fontWeight(700)
        .fontColor(color)
      
      Text(label)
        .fontSize(12)
        .fontColor(Theme.Color.TextTertiary)
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .alignItems(HorizontalAlign.Center)
  }
  
  /**
   * 功能菜单区域
   */
  @Builder
  buildMenuSection() {
    Column({ space: 12 }) {
      Text('功能设置')
        .fontSize(16)
        .fontWeight(600)
        .fontColor(Theme.Color.TextPrimary)
        .padding({ left: 8 })
        .opacity(this.showContent ? 1 : 0)
        .translate({ x: this.showContent ? 0 : -20 })
        .animation({
          duration: 600,
          curve: Curve.Smooth,
          delay: 200
        })
      
      ForEach(this.menuItems, (item: ProfileMenuItem, index: number) => {
        this.buildMenuItem(item, index)
      }, (item: ProfileMenuItem) => item.id)
    }
    .width('100%')
  }
  
  /**
   * 菜单项
   */
  @Builder
  buildMenuItem(item: ProfileMenuItem, index: number) {
    Row({ space: 12 }) {
      // 图标容器
      Stack() {
        Circle({ width: 48, height: 48 })
          .fill(item.color)
          .opacity(0.15)
        
        SimpleIcon({
          iconName: item.icon,
          iconSize: 24,
          color: item.color
        })
      }
      .width(48)
      .height(48)
      
      // 文本内容
      Column({ space: 4 }) {
        Text(item.title)
          .fontSize(16)
          .fontWeight(600)
          .fontColor(Theme.Color.TextPrimary)
        
        Text(item.subtitle)
          .fontSize(12)
          .fontColor(Theme.Color.TextTertiary)
      }
      .alignItems(HorizontalAlign.Start)
      .layoutWeight(1)
      
      // 箭头
      Text('→')
        .fontSize(20)
        .fontColor(Theme.Color.TextTertiary)
        .translate({ x: this.selectedMenu === index ? 4 : 0 })
        .animation({
          duration: 300,
          curve: Curve.Smooth
        })
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Theme.Color.BackgroundSecondary)
    .borderRadius(Theme.Radius.l)
    .border({ width: 1, color: Theme.Color.BorderLight })
    .shadow(Theme.Shadow.Soft)
    .onClick(() => {
      this.selectedMenu = index;
      if (item.route) {
        router.pushUrl({ url: item.route });
      } else if (item.action) {
        item.action();
      }
      setTimeout(() => {
        this.selectedMenu = -1;
      }, 300);
    })
    .opacity(this.showContent ? 1 : 0)
    .translate({ x: this.showContent ? 0 : -30 })
    .animation({
      duration: 600,
      curve: Curve.Smooth,
      delay: 300 + index * 80
    })
    .stateStyles({
      pressed: {
        .scale({ x: 0.98, y: 0.98 })
        .backgroundColor('#F8F9FA')
      },
      normal: {
        .scale({ x: 1, y: 1 })
        .backgroundColor(Theme.Color.BackgroundSecondary)
      }
    })
  }
  
  /**
   * 底部操作按钮
   */
  @Builder
  buildActionButtons() {
    Column({ space: 12 }) {
      // 退出登录按钮
      Button('退出登录')
        .width('100%')
        .height(52)
        .fontSize(16)
        .fontWeight(600)
        .fontColor('#ffffff')
        .backgroundColor('#FF3B30')
        .borderRadius(Theme.Radius.l)
        .shadow({
          radius: 8,
          color: 'rgba(255, 59, 48, 0.3)',
          offsetY: 4
        })
        .onClick(() => {
          this.handleLogout();
        })
        .opacity(this.showContent ? 1 : 0)
        .translate({ y: this.showContent ? 0 : 30 })
        .animation({
          duration: 600,
          curve: Curve.Smooth,
          delay: 500
        })
      
      // 版本信息
      Row() {
        Text('LifeSwarm v1.0.0')
          .fontSize(12)
          .fontColor(Theme.Color.TextTertiary)
      }
      .width('100%')
      .height(40)
      .justifyContent(FlexAlign.Center)
      .opacity(this.showContent ? 1 : 0)
      .animation({
        duration: 600,
        curve: Curve.Smooth,
        delay: 550
      })
    }
    .width('100%')
    .padding({ top: 20 })
  }
  
  /**
   * 加载用户信息
   */
  private async loadUserInfo() {
    try {
      this.userInfo = await this.authService.getCurrentUserAsync();
    } catch (err) {
      console.error('Failed to load user info:', err);
    }
  }
  
  /**
   * 处理登出
   */
  private async handleLogout() {
    this.isLoading = true;
    
    try {
      await this.authService.logout();
      
      promptAction.showToast({ message: '已退出登录' });
      
      // 跳转到登录页
      router.replaceUrl({ url: 'pages/Login' });
      
    } catch (err) {
      const error = err as Error;
      promptAction.showToast({ message: error.message });
    } finally {
      this.isLoading = false;
    }
  }
}
