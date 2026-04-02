/**
 * 旧版决策副本入口兼容页
 * 已统一迁移到增强决策流
 */
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'

interface LegacyParams {
  userId?: string
  initialQuestion?: string
}

@Entry
@Component
struct DecisionDungeonInput {
  @State redirecting: boolean = true

  aboutToAppear() {
    const params = router.getParams() as LegacyParams

    promptAction.showToast({ message: '旧版决策副本已升级，正在进入增强决策流' })

    setTimeout(() => {
      router.replaceUrl({
        url: 'pages/QuickDecisionInput',
        params: {
          userId: params?.userId || '',
          initialQuestion: params?.initialQuestion || ''
        }
      })
    }, 200)
  }

  build() {
    Column({ space: 16 }) {
      LoadingProgress()
        .width(36)
        .height(36)

      Text('正在切换到增强决策流...')
        .fontSize(16)
        .fontWeight(600)
        .fontColor('#1A1A1A')

      Text('新版流程会先收集信息，再进入可验证推演。')
        .fontSize(13)
        .fontColor('#666666')
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .alignItems(HorizontalAlign.Center)
    .padding(24)
    .backgroundColor('#F6F7FB')
  }
}
