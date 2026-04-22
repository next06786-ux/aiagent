/**
 * 主页 - 功能球体网格
 * 显示7大功能模块的入口
 */
import router from '@ohos.router';
import { AuthService } from '../services/AuthService';
import { DataPreloader } from '../utils/DataPreloader';
import { User } from '../models/User';
import { SphereView } from '../components/sphere/SphereView';
import { AppConstants } from '../constants/AppConstants';

@Entry
@Component
struct IndexNew {
  @State currentUser: User | null = null;
  @State isLoading: boolean = true;
  
  private authService = new AuthService();
  private dataPreloader = new DataPreloader();
  
  aboutToAppear() {
    this.checkLoginStatus();
  }
  
  /**
   * 检查登录状态
   */
  async checkLoginStatus() {
    const isLoggedIn = await this.authService.isLoggedIn();
    
    if (!isLoggedIn) {
      router.replaceUrl({ url: 'pages/LoginPage' });
      return;
    }
    
    // 获取用户信息
    this.currentUser = await this.authService.getUserInfo();
    
    // 预加载用户数据
    if (this.currentUser) {
      await this.dataPreloader.preloadUserData(this.currentUser.user_id);
    }
    
    this.isLoading = false;
  }
  
  build() {
    Column() {
      // 顶部导航栏
      Row() {
        Text(AppConstants.APP_NAME)
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
          .fontColor('#1A1A1A')
        
        Blank()
        
        // 用户头像
        Row() {
          Text(this.currentUser?.nickname?.charAt(0) || 'U')
            .fontSize(16)
            .fontColor(Color.White)
            .fontWeight(FontWeight.Bold)
        }
        .width(40)
        .height(40)
        .borderRadius(20)
        .backgroundColor(AppConstants.COLORS.PRIMARY)
        .justifyContent(FlexAlign.Center)
        .onClick(() => {
          router.pushUrl({ url: 'pages/UserProfile' });
        })
      }
      .width('100%')
      .padding(16)
      .backgroundColor(Color.White)
      .shadow({
        radius: 8,
        color: 'rgba(0, 0, 0, 0.05)',
        offsetX: 0,
        offsetY: 2
      })
      
      if (this.isLoading) {
        // 加载状态
        Column() {
          LoadingProgress()
            .width(50)
            .height(50)
            .color(AppConstants.COLORS.PRIMARY)
          
          Text('加载中...')
            .fontSize(14)
            .fontColor('#999')
            .margin({ top: 16 })
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
      } else {
        // 功能球体网格
        Grid() {
          GridItem() {
            FunctionSphere({
              title: '决策副本',
              color: AppConstants.COLORS.DECISION,
              onTapHandler: () => {
                router.pushUrl({ url: 'pages/DecisionSimulationPage' });
              }
            })
          }
          
          GridItem() {
            FunctionSphere({
              title: '知识星图',
              color: AppConstants.COLORS.KNOWLEDGE,
              onTapHandler: () => {
                router.pushUrl({ url: 'pages/KnowledgeGraphPage' });
              }
            })
          }
          
          GridItem() {
            FunctionSphere({
              title: '智慧洞察',
              color: AppConstants.COLORS.INSIGHTS,
              onTapHandler: () => {
                router.pushUrl({ url: 'pages/InsightsPage' });
              }
            })
          }
          
          GridItem() {
            FunctionSphere({
              title: '平行人生',
              color: AppConstants.COLORS.PARALLEL,
              onTapHandler: () => {
                router.pushUrl({ url: 'pages/ParallelLifePage' });
              }
            })
          }
          
          GridItem() {
            FunctionSphere({
              title: '树洞世界',
              color: AppConstants.COLORS.SOCIAL,
              onTapHandler: () => {
                router.pushUrl({ url: 'pages/SocialPage' });
              }
            })
          }
          
          GridItem() {
            FunctionSphere({
              title: '智能日程',
              color: AppConstants.COLORS.SCHEDULE,
              onTapHandler: () => {
                router.pushUrl({ url: 'pages/SchedulePage' });
              }
            })
          }
        }
        .columnsTemplate('1fr 1fr')
        .rowsTemplate('1fr 1fr 1fr')
        .columnsGap(16)
        .rowsGap(16)
        .width('100%')
        .layoutWeight(1)
        .padding(16)
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }
}

/**
 * 功能球体组件
 */
@Component
struct FunctionSphere {
  @Prop title: string;
  @Prop color: string;
  @Prop onTapHandler: () => void;
  
  build() {
    Column() {
      // 球体
      SphereView({
        title: '',
        sizeValue: 120,
        color: this.color,
        status: 'idle'
      })
      
      // 标题
      Text(this.title)
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .fontColor('#1A1A1A')
        .margin({ top: 12 })
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .backgroundColor(Color.White)
    .borderRadius(16)
    .shadow({
      radius: 20,
      color: 'rgba(0, 0, 0, 0.1)',
      offsetX: 0,
      offsetY: 4
    })
    .onClick(this.onTapHandler)
  }
}
