/**
 * 社交页面 - 好友和树洞
 */
import router from '@ohos.router';
import { SocialService } from '../services/SocialService';
import { Friend, Post, Comment } from '../models/Social';
import { AppConstants } from '../constants/AppConstants';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorToast } from '../components/common/ErrorToast';

@Entry
@Component
struct SocialPage {
  @State selectedTab: number = 0;
  @State friends: Friend[] = [];
  @State posts: Post[] = [];
  @State isLoading: boolean = false;
  @State errorMessage: string = '';
  @State showError: boolean = false;
  @State showPostDialog: boolean = false;
  @State newPostContent: string = '';

  private tabs: string[] = ['好友', '树洞'];

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

          Text('社交')
            .fontSize(20)
            .fontWeight(FontWeight.Bold)
            .fontColor(Color.White)
            .margin({ left: 16 })

          Blank()

          if (this.selectedTab === 1) {
            Text('+')
              .width(24)
              .height(24)
              .fontSize(28)
              .fontColor('#fff')
              .fontWeight(FontWeight.Bold)
              .textAlign(TextAlign.Center)
              .onClick(() => {
                this.showPostDialog = true;
              })
          }
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

        // 内容区域
        if (this.isLoading) {
          LoadingSpinner()
        } else {
          if (this.selectedTab === 0) {
            this.FriendsList()
          } else {
            this.TreeHoleList()
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

      // 发帖对话框
      if (this.showPostDialog) {
        this.PostDialog()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
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

  @Builder
  PostDialog() {
    Column() {
      // 遮罩
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('#00000080')
        .onClick(() => {
          this.showPostDialog = false;
        })

      // 对话框
      Column() {
        Text('发布树洞')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor('#333333')
          .margin({ bottom: 16 })

        TextArea({ placeholder: '说说你的想法...' })
          .width('100%')
          .height(150)
          .fontSize(15)
          .backgroundColor('#F5F5F5')
          .borderRadius(8)
          .onChange((value: string) => {
            this.newPostContent = value;
          })
          .margin({ bottom: 16 })

        Row({ space: 12 }) {
          Button('取消')
            .fontSize(16)
            .fontColor('#666666')
            .backgroundColor('#F5F5F5')
            .borderRadius(8)
            .layoutWeight(1)
            .onClick(() => {
              this.showPostDialog = false;
              this.newPostContent = '';
            })

          Button('发布')
            .fontSize(16)
            .fontColor(Color.White)
            .backgroundColor(AppConstants.COLORS.PRIMARY)
            .borderRadius(8)
            .layoutWeight(1)
            .enabled(this.newPostContent.trim().length > 0)
            .onClick(() => {
              this.publishPost();
            })
        }
        .width('100%')
      }
      .width('90%')
      .padding(20)
      .backgroundColor(Color.White)
      .borderRadius(16)
      .position({ x: '5%', y: '30%' })
    }
    .width('100%')
    .height('100%')
    .position({ x: 0, y: 0 })
  }

  private async publishPost() {
    this.isLoading = true;
    this.errorMessage = '';

    try {
      const socialService = new SocialService();
      await socialService.createTreeHolePost(this.newPostContent);
      this.showPostDialog = false;
      this.newPostContent = '';
      await this.loadData();
    } catch (error) {
      this.errorMessage = (error as Error).message || '发布失败';
      this.showError = true;
    } finally {
      this.isLoading = false;
    }
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
