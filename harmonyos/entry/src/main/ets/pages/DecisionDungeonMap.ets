/**
 * 旧版决策地图兼容页
 * 已统一迁移到新的 2D 推演详情页
 */
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'

interface LegacyMapParams {
  dungeonId?: string
  userId?: string
  simulationData?: string
  question?: string
  recommendation?: string
  isHistory?: string
}

@Entry
@Component
struct DecisionDungeonMap {
  aboutToAppear() {
    const params = router.getParams() as LegacyMapParams

    promptAction.showToast({ message: '旧版地图已升级，正在进入新版推演详情' })

    setTimeout(() => {
      router.replaceUrl({
        url: 'pages/DecisionDungeon2DMap',
        params: {
          dungeonId: params?.dungeonId || '',
          userId: params?.userId || '',
          simulationData: params?.simulationData || '',
          question: params?.question || '',
          recommendation: params?.recommendation || '',
          isHistory: params?.isHistory || ''
        }
      })
    }, 200)
  }

  build() {
    Column({ space: 16 }) {
      LoadingProgress()
        .width(36)
        .height(36)

      Text('正在切换到新版推演详情...')
        .fontSize(16)
        .fontWeight(600)
        .fontColor('#1A1A1A')
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .alignItems(HorizontalAlign.Center)
    .padding(24)
    .backgroundColor('#F6F7FB')
  }
}
