/**
 * 主页 - 五角星导航
 * 对标 web/src/pages/HomePage.tsx
 */
import router from '@ohos.router';
import { AuthService } from '../services/AuthService';
import { AppConstants } from '../constants/AppConstants';
import preferences from '@ohos.data.preferences';

interface PentagramNode {
  id: string;
  title: string;
  subtitle: string;
  route: string;
  top: string;
  left: string;
  color: string;
}

@Entry
@Component
struct HomePage {
  @State currentUser: string = '';
  @State showUserMenu: boolean = false;
  @State isLoading: boolean = true;

  private authService = new AuthService();

  // 五角星节点配置（对标Web端）
  private pentagramNodes: PentagramNode[] = [
    {
      id: 'decision',
      title: '决策副本',
      subtitle: '分析入口',
      route: 'pages/DecisionSimulationPage',
      top: '15%',      // 顶部
      left: '50%',
      color: '#B8DCFF'
    },
    {
      id: 'insights',
      title: '智慧洞察',
      subtitle: '决策分析',
      route: 'pages/InsightsPage',
      top: '30%',      // 右上
      left: '75%',
      color: '#A8D5FF'
    },
    {
      id: 'parallel-life',
      title: '平行人生',
      subtitle: '塔罗游戏',
      route: 'pages/ParallelLifePage',
      top: '65%',      // 右下
      left: '70%',
      color: '#8FC8FF'
    },
    {
      id: 'friends',
      title: '好友',
      subtitle: '社交互动',
      route: 'pages/FriendsPage',
      top: '65%',      // 左下
      left: '30%',
      color: '#7DBDFF'
    },
    {
      id: 'knowledge-graph',
      title: '知识星图',
      subtitle: '记忆星空',
      route: 'pages/KnowledgeGraphPage',
      top: '30%',      // 左上
      left: '25%',
      color: '#C8E2FF'
    }
  ];

  aboutToAppear() {
    this.checkLoginStatus();
  }

  /**
   * 检查登录状态
   */
  async checkLoginStatus() {
    try {
      const prefs = await preferences.getPreferences(getContext(this), 'lifeswarm_auth');
      const token = await prefs.get('token', '') as string;
      const username = await prefs.get('username', '') as string;

      if (!token) {
        // 未登录，跳转到认证页
        router.replaceUrl({ url: 'pages/AuthPage' });
        return;
      }

      this.currentUser = username;
      this.isLoading = false;
    } catch (error) {
      console.error('检查登录状态失败:', error);
      router.replaceUrl({ url: 'pages/AuthPage' });
    }
  }

  /**
   * 退出登录
   */
  async handleLogout() {
    try {
      const prefs = await preferences.getPreferences(getContext(this), 'lifeswarm_auth');
      await prefs.clear();
      await prefs.flush();

      router.replaceUrl({ url: 'pages/AuthPage' });
    } catch (error) {
      console.error('退出登录失败:', error);
    }
  }

  /**
   * 节点点击
   */
  private onNodeClick(node: PentagramNode) {
    console.log(`[HomePage] 点击节点: ${node.title}`);
    router.pushUrl({ url: node.route });
  }

  build() {
    Stack() {
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
        Column() {
          // 顶部导航栏
          Row() {
            Text('择境')
              .fontSize(24)
              .fontWeight(FontWeight.Bold)
              .fontColor('#1A1A1A')

            Blank()

            // 用户头像按钮
            Stack() {
              Row() {
                Text(this.currentUser.charAt(0).toUpperCase())
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
                this.showUserMenu = !this.showUserMenu;
              })

              // 用户菜单
              if (this.showUserMenu) {
                Column() {
                  Text(this.currentUser)
                    .fontSize(12)
                    .fontColor('#999')
                    .padding({ top: 8, bottom: 8, left: 16, right: 16 })
                    .borderRadius({ topLeft: 12, topRight: 12 })

                  Divider()
                    .color('#F0F0F0')

                  Button('个人中心')
                    .fontSize(14)
                    .fontColor('#333')
                    .backgroundColor(Color.Transparent)
                    .width('100%')
                    .onClick(() => {
                      this.showUserMenu = false;
                      router.pushUrl({ url: 'pages/UserProfilePage' });
                    })

                  Button('退出登录')
                    .fontSize(14)
                    .fontColor('#FF3B30')
                    .backgroundColor(Color.Transparent)
                    .width('100%')
                    .onClick(() => {
                      this.showUserMenu = false;
                      this.handleLogout();
                    })
                }
                .width(140)
                .backgroundColor(Color.White)
                .borderRadius(12)
                .shadow({
                  radius: 20,
                  color: 'rgba(0, 0, 0, 0.15)',
                  offsetX: 0,
                  offsetY: 4
                })
                .position({ x: -100, y: 50 })
              }
            }
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

          // 五角星导航区域
          Stack() {
            // 背景装饰
            Column()
              .width('100%')
              .height('100%')
              .linearGradient({
                angle: 135,
                colors: [
                  ['#F0F7FF', 0.0],
                  ['#E8F4FF', 1.0]
                ]
              })

            // 五角星节点
            Stack() {
              ForEach(this.pentagramNodes, (node: PentagramNode) => {
                this.PentagramNodeView(node)
              })

              // 中心AI核心按钮
              this.CenterCoreButton()
            }
            .width('100%')
            .height('100%')
          }
          .layoutWeight(1)
        }
        .width('100%')
        .height('100%')
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }

  /**
   * 五角星节点视图
   */
  @Builder
  PentagramNodeView(node: PentagramNode) {
    Column() {
      // 球体
      Column()
        .width(80)
        .height(80)
        .borderRadius(40)
        .backgroundColor(node.color)
        .shadow({
          radius: 20,
          color: `${node.color}80`,
          offsetX: 0,
          offsetY: 4
        })

      // 标题
      Column() {
        Text(node.subtitle)
          .fontSize(12)
          .fontColor('#999')
          .margin({ bottom: 4 })

        Text(node.title)
          .fontSize(16)
          .fontWeight(FontWeight.Bold)
          .fontColor('#1A1A1A')
      }
      .margin({ top: 12 })
    }
    .position({
      x: node.left,
      y: node.top
    })
    .markAnchor({
      x: '50%',
      y: '50%'
    })
    .onClick(() => {
      this.onNodeClick(node);
    })
  }

  /**
   * 中心AI核心按钮
   */
  @Builder
  CenterCoreButton() {
    Column() {
      // 外圈光晕
      Column()
        .width(140)
        .height(140)
        .borderRadius(70)
        .backgroundColor('rgba(10, 89, 247, 0.1)')
        .position({ x: '50%', y: '50%' })
        .markAnchor({ x: '50%', y: '50%' })

      // 核心球体
      Column() {
        Text('🌟')
          .fontSize(32)
          .margin({ bottom: 8 })

        Text('AI 核心')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
          .margin({ bottom: 4 })

        Text('感知 / 分析 / 决策')
          .fontSize(11)
          .fontColor('rgba(255, 255, 255, 0.8)')
      }
      .width(100)
      .height(100)
      .borderRadius(50)
      .backgroundColor(AppConstants.COLORS.PRIMARY)
      .justifyContent(FlexAlign.Center)
      .shadow({
        radius: 30,
        color: 'rgba(10, 89, 247, 0.4)',
        offsetX: 0,
        offsetY: 4
      })
      .position({ x: '50%', y: '50%' })
      .markAnchor({ x: '50%', y: '50%' })
      .onClick(() => {
        // TODO: 打开AI对话
        console.log('[HomePage] 点击AI核心');
      })
    }
  }
}
