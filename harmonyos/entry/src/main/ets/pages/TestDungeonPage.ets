/**
 * 测试页面 - 验证路由是否工作
 */
import router from '@ohos.router'

@Entry
@Component
struct TestDungeonPage {
  @State message: string = '测试页面加载成功！'
  private dungeonId: string = ''

  aboutToAppear() {
    const params = router.getParams() as Record<string, string>
    if (params?.dungeonId) {
      this.dungeonId = params.dungeonId
      this.message = `收到参数: ${this.dungeonId}`
    }
    console.info('TestDungeonPage loaded with dungeonId:', this.dungeonId)
  }

  build() {
    Column() {
      Text(this.message)
        .fontSize(20)
        .fontWeight(700)
        .margin({ top: 100 })

      Text(`Dungeon ID: ${this.dungeonId}`)
        .fontSize(16)
        .margin({ top: 20 })

      Button('返回')
        .margin({ top: 40 })
        .onClick(() => {
          router.back()
        })
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }
}
