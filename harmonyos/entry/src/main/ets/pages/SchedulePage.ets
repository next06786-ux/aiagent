/**
 * 日程管理页面
 */
import router from '@ohos.router';
import { ScheduleService } from '../services/ScheduleService';
import { Schedule } from '../models/Schedule';
import { AppConstants } from '../constants/AppConstants';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorToast } from '../components/common/ErrorToast';

@Entry
@Component
struct SchedulePage {
  @State schedules: Schedule[] = [];
  @State selectedDate: Date = new Date();
  @State isLoading: boolean = false;
  @State errorMessage: string = '';
  @State showError: boolean = false;
  @State showAddDialog: boolean = false;

  aboutToAppear() {
    this.loadSchedules();
  }

  async loadSchedules() {
    this.isLoading = true;
    this.errorMessage = '';

    try {
      const startDate = new Date(this.selectedDate);
      startDate.setHours(0, 0, 0, 0);
      const endDate = new Date(this.selectedDate);
      endDate.setHours(23, 59, 59, 999);

      const scheduleService = new ScheduleService();
      this.schedules = await scheduleService.getSchedules(
        Math.floor(startDate.getTime() / 1000),
        Math.floor(endDate.getTime() / 1000)
      );
    } catch (error) {
      this.errorMessage = (error as Error).message || '加载日程失败';
      this.showError = true;
    } finally {
      this.isLoading = false;
    }
  }

  build() {
    Stack() {
      Column() {
        // 顶部导航栏
        Row() {
          Text('←')
            .fontSize(24)
            .fontColor(Color.White)
            .onClick(() => {
              router.back();
            })

          Text('日程管理')
            .fontSize(20)
            .fontWeight(FontWeight.Bold)
            .fontColor(Color.White)
            .margin({ left: 16 })

          Blank()

          Text('+')
            .fontSize(28)
            .fontColor(Color.White)
            .onClick(() => {
              this.showAddDialog = true;
            })
        }
        .width('100%')
        .height(56)
        .padding({ left: 16, right: 16 })
        .backgroundColor(AppConstants.COLORS.PRIMARY)

        // 日期选择器
        Row() {
          Text('◀')
            .fontSize(20)
            .fontColor('#333333')
            .onClick(() => {
              this.changeDate(-1);
            })

          Text(this.formatDateHeader(this.selectedDate))
            .fontSize(16)
            .fontWeight(FontWeight.Bold)
            .fontColor('#333333')
            .layoutWeight(1)
            .textAlign(TextAlign.Center)

          Text('▶')
            .fontSize(20)
            .fontColor('#333333')
            .onClick(() => {
              this.changeDate(1);
            })
        }
        .width('100%')
        .height(48)
        .padding({ left: 16, right: 16 })
        .backgroundColor(Color.White)

        // 日程列表
        if (this.isLoading) {
          LoadingSpinner()
        } else {
          this.ScheduleList()
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

      // 添加日程对话框
      if (this.showAddDialog) {
        this.AddScheduleDialog()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }

  @Builder
  ScheduleList() {
    if (this.schedules.length === 0) {
      Column() {
        Text('📅')
          .fontSize(64)
          .margin({ bottom: 16 })

        Text('暂无日程')
          .fontSize(16)
          .fontColor('#999999')
      }
      .width('100%')
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
    } else {
      List({ space: 12 }) {
        ForEach(this.schedules, (schedule: Schedule) => {
          ListItem() {
            this.ScheduleCard(schedule)
          }
        })
      }
      .width('100%')
      .layoutWeight(1)
      .padding(16)
    }
  }

  @Builder
  ScheduleCard(schedule: Schedule) {
    Row() {
      // 时间线
      Column() {
        Text(this.formatTime(schedule.start_time))
          .fontSize(14)
          .fontWeight(FontWeight.Bold)
          .fontColor(AppConstants.COLORS.PRIMARY)

        Divider()
          .vertical(true)
          .height(40)
          .width(2)
          .color(AppConstants.COLORS.PRIMARY)
          .margin({ top: 4, bottom: 4 })

        Text(this.formatTime(schedule.end_time))
          .fontSize(14)
          .fontColor('#999999')
      }
      .width(60)
      .margin({ right: 12 })

      // 内容
      Column() {
        Text(schedule.title)
          .fontSize(16)
          .fontWeight(FontWeight.Bold)
          .fontColor('#333333')
          .margin({ bottom: 4 })

        if (schedule.description) {
          Text(schedule.description)
            .fontSize(14)
            .fontColor('#666666')
            .maxLines(2)
            .textOverflow({ overflow: TextOverflow.Ellipsis })
            .margin({ bottom: 8 })
        }

        if (schedule.location) {
          Row({ space: 4 }) {
            Text('📍')
              .fontSize(14)

            Text(schedule.location)
              .fontSize(12)
              .fontColor('#999999')
          }
        }
      }
      .alignItems(HorizontalAlign.Start)
      .layoutWeight(1)
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(12)
  }

  @Builder
  AddScheduleDialog() {
    Column() {
      Text('添加日程')
        .fontSize(18)
        .fontWeight(FontWeight.Bold)
        .fontColor('#333333')
        .margin({ bottom: 16 })

      // 这里可以添加表单字段

      Row({ space: 12 }) {
        Button('取消')
          .fontSize(16)
          .fontColor('#666666')
          .backgroundColor('#F5F5F5')
          .borderRadius(8)
          .layoutWeight(1)
          .onClick(() => {
            this.showAddDialog = false;
          })

        Button('保存')
          .fontSize(16)
          .fontColor(Color.White)
          .backgroundColor(AppConstants.COLORS.PRIMARY)
          .borderRadius(8)
          .layoutWeight(1)
          .onClick(() => {
            this.saveSchedule();
          })
      }
      .width('100%')
    }
    .width('90%')
    .padding(20)
    .backgroundColor(Color.White)
    .borderRadius(16)
    .position({ x: '5%', y: '20%' })
  }

  private changeDate(days: number) {
    const newDate = new Date(this.selectedDate);
    newDate.setDate(newDate.getDate() + days);
    this.selectedDate = newDate;
    this.loadSchedules();
  }

  private formatDateHeader(date: Date): string {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    const weekday = weekdays[date.getDay()];

    return `${year}年${month}月${day}日 星期${weekday}`;
  }

  private formatTime(timestamp: number): string {
    const date = new Date(timestamp * 1000);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  }

  private async saveSchedule() {
    // 实现保存逻辑
    this.showAddDialog = false;
  }
}
