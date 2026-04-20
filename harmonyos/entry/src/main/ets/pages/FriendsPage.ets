/**
 * 好友页面 - 对标Web端FriendsPage
 * 包含好友列表和树洞入口
 */
import router from '@ohos.router';
import { SocialService } from '../services/SocialService';
import { Friend, Post, Comment } from '../models/Social';
import { AppConstants } from '../constants/AppConstants';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorToast } from '../components/common/ErrorToast';

@Entry
@Component
struct FriendsPage {
  @State selectedTab: number = 0;
  @State friends: Friend[] = [];
  @State posts: Post[] = [];
  @State isLoading: boolean = false;
  @State errorMessage: string = '';
  @State showError: boolean = false;
  @State showPostDialog: boolean = false;
  @State newPostContent: string = '';

  private tabs: string[] = ['好友列表', '好友请求', '添加好友'];

  aboutToAppear() {
    this.loadData();
  }

  async loadData() {
    this.isLoading = true;
    this.errorMessage = '';

    try {
      const socialService = new SocialService();
      if (this.selectedTab === 0) {
        this.friends = await socialService.getFriends();
      } else {
        this.posts = await socialService.getTreeHolePosts();
      }
    } catch (error) {
      this.errorMessage = (error as Error).message || '加载数据失败';
      this.showError = true;
    } finally {
      this.isLoading = false;
    }
  }

  onTabChange(index: number) {
    if (this.selectedTab !== index) {
      this.selectedTab = index;
      this.loadData();
    }
  }

  build() {
    Stack() {
      Column() {
        // 顶部导航栏
        Row() {
          Text('←')
            .fontSize(24)
            .fontColor('#333')
            .onClick(() => {
              router.back();
            })

          Text('好友')
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

        // Tab切换
        Row() {
          ForEach(this.tabs, (tab: string, index: number) => {
            Column() {
              Text(tab)
                .fontSize(16)
                .fontColor(this.selectedTab === index ? AppConstants.COLORS.PRIMARY : Color.Gray)
                .fontWeight(this.selectedTab === index ? FontWeight.Bold : FontWeight.Normal)

              if (this.selectedTab === index) {
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
        .backgroundColor(Color.White)

        // 树洞入口卡片（对标Web端）
        this.TreeHoleEntryCard()

        // 内容区域
        if (this.isLoading) {
          LoadingSpinner()
        } else {
          if (this.selectedTab === 0) {
            this.FriendsList()
          } else if (this.selectedTab === 1) {
            this.FriendRequestsList()
          } else {
            this.AddFriendView()
          }
        }

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
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }

  @Builder
  TreeHoleEntryCard() {
    // 树洞入口卡片（对标Web端）
    Column() {
      Row() {
        // 树洞图标
        Text('🌳')
          .width(48)
          .height(48)
          .fontSize(32)
          .textAlign(TextAlign.Center)
          .margin({ right: 16 })

        // 内容
        Column() {
          Text('树洞世界')
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .fontColor('#1A1A1A')
            .margin({ bottom: 4 })

          Text('匿名分享你的心情、秘密和梦想')
            .fontSize(14)
            .fontColor('#666666')
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)

        // 箭头
        Text('→')
          .fontSize(24)
          .fontColor(AppConstants.COLORS.PRIMARY)
      }
      .width('100%')
      .padding(20)
      .backgroundColor(Color.White)
      .borderRadius(16)
      .onClick(() => {
        router.pushUrl({ url: 'pages/TreeHolePage' });
      })
    }
    .width('100%')
    .padding({ left: 16, right: 16, bottom: 12 })
  }

  @Builder
  FriendsList() {
    List({ space: 12 }) {
      ForEach(this.friends, (friend: Friend) => {
        ListItem() {
          this.FriendCard(friend)
        }
      })
    }
    .width('100%')
    .layoutWeight(1)
    .padding(16)
  }

  @Builder
  FriendCard(friend: Friend) {
    Row() {
      // 头像
      Text(friend.nickname?.charAt(0) || '👤')
        .width(48)
        .height(48)
        .borderRadius(24)
        .backgroundColor('#E8F4FF')
        .fontSize(24)
        .fontColor('#0A59F7')
        .textAlign(TextAlign.Center)
        .padding({ top: 10 })
        .margin({ right: 12 })

      // 信息
      Column() {
        Text(friend.nickname)
          .fontSize(16)
          .fontWeight(FontWeight.Bold)
          .fontColor('#333333')
          .margin({ bottom: 4 })

        Text(friend.bio || friend.nickname || '这个人很懒，什么都没写')
          .fontSize(14)
          .fontColor('#999999')
          .maxLines(1)
          .textOverflow({ overflow: TextOverflow.Ellipsis })
      }
      .alignItems(HorizontalAlign.Start)
      .layoutWeight(1)

      // 操作按钮
      Button('聊天')
        .fontSize(14)
        .fontColor(AppConstants.COLORS.PRIMARY)
        .backgroundColor(AppConstants.COLORS.PRIMARY + '20')
        .borderRadius(16)
        .padding({ left: 16, right: 16, top: 6, bottom: 6 })
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(12)
  }

  @Builder
  FriendRequestsList() {
    // 好友请求列表
    List({ space: 12 }) {
      ListItem() {
        Column() {
          Text('暂无好友请求')
            .fontSize(14)
            .fontColor('#999999')
            .textAlign(TextAlign.Center)
        }
        .width('100%')
        .padding(40)
      }
    }
    .width('100%')
    .layoutWeight(1)
    .padding(16)
  }

  @Builder
  AddFriendView() {
    // 添加好友视图
    Column() {
      Text('搜索用户')
        .fontSize(16)
        .fontWeight(FontWeight.Bold)
        .fontColor('#333333')
        .margin({ bottom: 16 })

      TextInput({ placeholder: '输入用户名搜索...' })
        .width('100%')
        .height(48)
        .fontSize(15)
        .backgroundColor('#F5F5F5')
        .borderRadius(12)
        .margin({ bottom: 16 })

      Button('搜索')
        .width('100%')
        .height(48)
        .fontSize(16)
        .fontColor(Color.White)
        .backgroundColor(AppConstants.COLORS.PRIMARY)
        .borderRadius(12)
    }
    .width('100%')
    .padding(16)
  }

  @Builder
  TreeHoleList() {
    List({ space: 12 }) {
      ForEach(this.posts, (post: Post) => {
        ListItem() {
          this.PostCard(post)
        }
      })
    }
    .width('100%')
    .layoutWeight(1)
    .padding(16)
  }

  @Builder
  PostCard(post: Post) {
    Column() {
      // 内容
      Text(post.content)
        .fontSize(15)
        .fontColor('#333333')
        .lineHeight(24)
        .margin({ bottom: 12 })

      // 底部信息
      Row() {
        Text(this.formatDate(post.created_at))
          .fontSize(12)
          .fontColor('#999999')

        Blank()

        Row({ space: 16 }) {
          Row({ space: 4 }) {
            Text('❤️')
              .width(16)
              .height(16)
              .fontSize(14)
            Text(`${post.likes_count}`)
              .fontSize(12)
              .fontColor('#999999')
          }

          Row({ space: 4 }) {
            Text('💬')
              .width(16)
              .height(16)
              .fontSize(14)
            Text(`${post.comments_count}`)
              .fontSize(12)
              .fontColor('#999999')
          }
        }
      }
      .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(12)
    .onClick(() => {
      // 跳转到帖子详情
    })
  }

  private formatDate(timestamp: number): string {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));

    if (minutes < 1) {
      return '刚刚';
    } else if (minutes < 60) {
      return `${minutes}分钟前`;
    } else if (minutes < 1440) {
      return `${Math.floor(minutes / 60)}小时前`;
    } else {
      return `${Math.floor(minutes / 1440)}天前`;
    }
  }
}
