/**
 * 旧版决策副本列表兼容页
 * 新流程已统一在 2D 推演详情中展示选项与历史
 */
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'

interface LegacyListParams {
  userId?: string
  simulationData?: string
  question?: string
  dungeonId?: string
}

@Entry
@Component
struct DecisionDungeonList {
  aboutToAppear() {
    const params = router.getParams() as LegacyListParams

    promptAction.showToast({ message: '旧版副本列表已合并到新版推演详情' })

    setTimeout(() => {
      if (params?.simulationData) {
        router.replaceUrl({
          url: 'pages/DecisionDungeon2DMap',
          params: {
            userId: params?.userId || '',
            simulationData: params.simulationData,
            question: params?.question || ''
          }
        })
        return
      }

      router.replaceUrl({
        url: 'pages/QuickDecisionInput',
        params: {
          userId: params?.userId || ''
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
