/**
 * 副本地图组件 - 平行宇宙闯关系统
 * 展示多个副本关卡，支持进度追踪和难度选择
 */
import { DecisionOption } from '../models/DecisionModels'

interface DungeonLevel {
  id: number
  name: string
  description: string
  difficulty: 'easy' | 'normal' | 'hard' | 'nightmare'
  status: 'locked' | 'unlocked' | 'completed'
  progress: number // 0-100
  rewards: string[]
  estimatedTime: number // 分钟
  universeVariant: DecisionOption
}

interface DungeonChapter {
  id: number
  title: string
  description: string
  levels: DungeonLevel[]
  chapterProgress: number // 0-100
}

@Component
export struct DungeonMap {
  @State chapters: DungeonChapter[] = []
  @State selectedChapter: number = 0
  @State selectedLevel: number | null = null
  @State isDetailViewOpen: boolean = false
  @State totalProgress: number = 0
  @State animationProgress: number = 0

  aboutToAppear() {
    this.initializeDungeons()
  }

  build() {
    Column() {
      // 顶部进度条
      this.ProgressHeader()

      if (this.isDetailViewOpen && this.selectedLevel !== null) {
        // 副本详情视图
        this.LevelDetailView()
      } else {
        // 副本地图视图
        this.DungeonMapView()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#0F1419')
  }

  @Builder
  ProgressHeader() {
    Column() {
      Row() {
        Text('平行宇宙副本')
          .fontSize(28)
          .fontWeight(FontWeight.Bold)
          .fontColor('#FFFFFF')

        Blank()

        Text(`总进度: ${this.totalProgress}%`)
          .fontSize(14)
          .fontColor('#888888')
      }
      .width('100%')
      .padding({ bottom: 15 })

      // 总进度条
      Progress({
        value: this.totalProgress,
        total: 100,
        type: ProgressType.Linear
      })
      .width('100%')
      .height(6)
      .color('#00D4FF')
      .backgroundColor('#2A2E3A')
      .borderRadius(3)
    }
    .width('100%')
    .padding(20)
    .backgroundColor('#1A1E2E')
  }

  @Builder
  DungeonMapView() {
    Column() {
      // 章节选择器
      this.ChapterSelector()

      // 副本关卡网格
      this.LevelGrid()
    }
    .width('100%')
    .layoutWeight(1)
    .padding(20)
  }

  @Builder
  ChapterSelector() {
    Column() {
      Text('选择章节')
        .fontSize(16)
        .fontColor('#AAAAAA')
        .margin({ bottom: 12 })

      Scroll() {
        Row({ space: 10 }) {
          ForEach(this.chapters, (chapter: DungeonChapter, index: number) => {
            this.ChapterButton(chapter, index)
          })
        }
      }
      .scrollable(ScrollDirection.Horizontal)
      .width('100%')
    }
    .width('100%')
    .margin({ bottom: 25 })
  }

  @Builder
  ChapterButton(chapter: DungeonChapter, index: number) {
    Column() {
      Text(chapter.title)
        .fontSize(14)
        .fontWeight(FontWeight.Bold)
        .fontColor(this.selectedChapter === index ? '#00D4FF' : '#FFFFFF')

      Progress({
        value: chapter.chapterProgress,
        total: 100,
        type: ProgressType.Linear
      })
      .width(80)
      .height(3)
      .color('#00D4FF')
      .backgroundColor('#2A2E3A')
      .margin({ top: 8 })
    }
    .width(100)
    .padding(12)
    .backgroundColor(this.selectedChapter === index ? '#1E2A3A' : '#2A2E3A')
    .borderRadius(8)
    .border({
      width: this.selectedChapter === index ? 2 : 0,
      color: '#00D4FF'
    })
    .onClick(() => {
      this.selectedChapter = index
    })
  }

  @Builder
  LevelGrid() {
    Column() {
      if (this.chapters.length > 0) {
        let currentChapter = this.chapters[this.selectedChapter]
        
        Grid() {
          ForEach(currentChapter.levels, (level: DungeonLevel, index: number) => {
            GridItem() {
              this.LevelCard(level, index)
            }
          })
        }
        .columnsTemplate('1fr 1fr')
        .rowsGap(15)
        .columnsGap(15)
        .width('100%')
      }
    }
    .layoutWeight(1)
  }

  @Builder
  LevelCard(level: DungeonLevel, index: number) {
    Column() {
      // 锁定状态
      if (level.status === 'locked') {
        Stack() {
          Column()
            .width('100%')
            .height('100%')
            .backgroundColor('#2A2E3A')
            .borderRadius(12)
            .opacity(0.5)

          Column({ space: 10 }) {
            Text('🔒')
              .fontSize(32)

            Text('已锁定')
              .fontSize(14)
              .fontColor('#888888')
          }
          .width('100%')
          .height('100%')
          .justifyContent(FlexAlign.Center)
          .alignItems(ItemAlign.Center)
        }
        .width('100%')
        .height(180)
      } else {
        // 可用或已完成
        Column({ space: 10 }) {
          // 难度标签
          Row() {
            Text(`第${level.id}关`)
              .fontSize(16)
              .fontWeight(FontWeight.Bold)
              .fontColor('#FFFFFF')

            Blank()

            Text(this.getDifficultyLabel(level.difficulty))
              .fontSize(12)
              .fontColor(this.getDifficultyColor(level.difficulty))
              .backgroundColor(this.getDifficultyBgColor(level.difficulty))
              .padding({ left: 8, right: 8, top: 4, bottom: 4 })
              .borderRadius(4)
          }
          .width('100%')

          // 副本名称
          Text(level.name)
            .fontSize(14)
            .fontColor('#CCCCCC')
            .maxLines(2)
            .textOverflow({ overflow: TextOverflow.Ellipsis })

          // 进度条
          if (level.status === 'completed') {
            Progress({
              value: 100,
              total: 100,
              type: ProgressType.Linear
            })
            .width('100%')
            .height(4)
            .color('#4CAF50')
            .backgroundColor('#2A2E3A')
          } else {
            Progress({
              value: level.progress,
              total: 100,
              type: ProgressType.Linear
            })
            .width('100%')
            .height(4)
            .color('#00D4FF')
            .backgroundColor('#2A2E3A')
          }

          // 奖励和时间
          Row({ space: 8 }) {
            Text(`⏱ ${level.estimatedTime}分钟`)
              .fontSize(12)
              .fontColor('#888888')

            Blank()

            if (level.status === 'completed') {
              Text('✓ 已完成')
                .fontSize(12)
                .fontColor('#4CAF50')
            }
          }
          .width('100%')

          // 进入按钮
          Button(level.status === 'completed' ? '重新挑战' : '进入副本')
            .width('100%')
            .height(36)
            .fontSize(14)
            .fontColor('#FFFFFF')
            .backgroundColor(level.status === 'completed' ? '#FF9800' : '#00D4FF')
            .borderRadius(6)
            .onClick(() => {
              this.selectedLevel = index
              this.isDetailViewOpen = true
            })
        }
        .width('100%')
        .height(180)
        .padding(12)
        .backgroundColor('#1E2A3A')
        .borderRadius(12)
        .border({
          width: 1,
          color: level.status === 'completed' ? '#4CAF50' : '#00D4FF'
        })
      }
    }
  }

  @Builder
  LevelDetailView() {
    Column() {
      // 返回按钮
      Row() {
        Button('← 返回')
          .width(80)
          .height(36)
          .fontSize(14)
          .backgroundColor('#2A2E3A')
          .fontColor('#FFFFFF')
          .onClick(() => {
            this.isDetailViewOpen = false
          })

        Blank()

        Text('副本详情')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor('#FFFFFF')

        Blank()
      }
      .width('100%')
      .margin({ bottom: 20 })

      if (this.selectedLevel !== null && this.chapters.length > 0) {
        let level = this.chapters[this.selectedChapter].levels[this.selectedLevel]

        Scroll() {
          Column({ space: 15 }) {
            // 副本信息卡片
            this.LevelInfoCard(level)

            // 宇宙变体信息
            this.UniverseVariantCard(level.universeVariant)

            // 奖励信息
            this.RewardsCard(level)

            // 操作按钮
            Row({ space: 10 }) {
              Button('开始挑战')
                .layoutWeight(1)
                .height(44)
                .fontSize(16)
                .fontColor('#FFFFFF')
                .backgroundColor('#00D4FF')
                .borderRadius(8)
                .onClick(() => {
                  // 开始副本逻辑
                })

              Button('查看攻略')
                .layoutWeight(1)
                .height(44)
                .fontSize(16)
                .fontColor('#00D4FF')
                .backgroundColor('#2A2E3A')
                .borderRadius(8)
                .border({
                  width: 1,
                  color: '#00D4FF'
                })
            }
            .width('100%')
            .margin({ top: 20 })
          }
        }
        .layoutWeight(1)
      }
    }
    .width('100%')
    .height('100%')
    .padding(20)
  }

  @Builder
  LevelInfoCard(level: DungeonLevel) {
    Column({ space: 12 }) {
      Text(level.name)
        .fontSize(24)
        .fontWeight(FontWeight.Bold)
        .fontColor('#FFFFFF')

      Text(level.description)
        .fontSize(14)
        .fontColor('#AAAAAA')
        .lineHeight(1.6)

      Row({ space: 20 }) {
        Column({ space: 4 }) {
          Text('难度')
            .fontSize(12)
            .fontColor('#888888')

          Text(this.getDifficultyLabel(level.difficulty))
            .fontSize(16)
            .fontWeight(FontWeight.Bold)
            .fontColor(this.getDifficultyColor(level.difficulty))
        }

        Column({ space: 4 }) {
          Text('预计时间')
            .fontSize(12)
            .fontColor('#888888')

          Text(`${level.estimatedTime}分钟`)
            .fontSize(16)
            .fontWeight(FontWeight.Bold)
            .fontColor('#FFFFFF')
        }

        Column({ space: 4 }) {
          Text('进度')
            .fontSize(12)
            .fontColor('#888888')

          Text(`${level.progress}%`)
            .fontSize(16)
            .fontWeight(FontWeight.Bold)
            .fontColor('#00D4FF')
        }
      }
      .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor('#1E2A3A')
    .borderRadius(10)
    .border({
      width: 1,
      color: '#2A3A4A'
    })
  }

  @Builder
  UniverseVariantCard(variant: DecisionOption) {
    Column({ space: 12 }) {
      Text('宇宙变体')
        .fontSize(16)
        .fontWeight(FontWeight.Bold)
        .fontColor('#FFFFFF')

      Column({ space: 8 }) {
        Row() {
          Text('决策方案:')
            .fontSize(14)
            .fontColor('#AAAAAA')

          Text(variant.title)
            .fontSize(14)
            .fontColor('#00D4FF')
            .fontWeight(FontWeight.Bold)
        }

        Row() {
          Text('综合评分:')
            .fontSize(14)
            .fontColor('#AAAAAA')

          Text(`${variant.final_score.toFixed(1)}/100`)
            .fontSize(14)
            .fontColor('#FFFFFF')
            .fontWeight(FontWeight.Bold)
        }

        Row() {
          Text('风险等级:')
            .fontSize(14)
            .fontColor('#AAAAAA')

          Text(this.getRiskLabel(variant.risk_level))
            .fontSize(14)
            .fontColor(this.getRiskColor(variant.risk_level))
            .fontWeight(FontWeight.Bold)
        }
      }
    }
    .width('100%')
    .padding(16)
    .backgroundColor('#1E2A3A')
    .borderRadius(10)
    .border({
      width: 1,
      color: '#2A3A4A'
    })
  }

  @Builder
  RewardsCard(level: DungeonLevel) {
    Column({ space: 12 }) {
      Text('副本奖励')
        .fontSize(16)
        .fontWeight(FontWeight.Bold)
        .fontColor('#FFFFFF')

      Flex({ wrap: FlexWrap.Wrap, space: { main: Space.Between } }) {
        ForEach(level.rewards, (reward: string) => {
          Text(reward)
            .fontSize(12)
            .fontColor('#FFFFFF')
            .padding({ left: 12, right: 12, top: 6, bottom: 6 })
            .backgroundColor('#2A3A4A')
            .borderRadius(6)
            .border({
              width: 1,
              color: '#00D4FF'
            })
        })
      }
      .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor('#1E2A3A')
    .borderRadius(10)
    .border({
      width: 1,
      color: '#2A3A4A'
    })
  }

  // 初始化副本数据
  private initializeDungeons() {
    this.chapters = [
      {
        id: 1,
        title: '第一章：初始决策',
        description: '开始你的平行宇宙之旅',
        chapterProgress: 66,
        levels: [
          {
            id: 1,
            name: '职业选择的分岔路口',
            description: '在三个职业方向中做出选择，每个选择都会开启不同的宇宙线',
            difficulty: 'easy',
            status: 'completed',
            progress: 100,
            rewards: ['基础经验 +100', '职业徽章', '初始资源包'],
            estimatedTime: 15,
            universeVariant: {
              title: '技术路线',
              final_score: 85,
              risk_level: 0.3,
              timeline: []
            }
          },
          {
            id: 2,
            name: '学习路径的优化',
            description: '选择最适合的学习方法和资源配置',
            difficulty: 'normal',
            status: 'completed',
            progress: 100,
            rewards: ['学习加速 +50%', '知识库解锁', '导师推荐'],
            estimatedTime: 20,
            universeVariant: {
              title: '深度学习',
              final_score: 78,
              risk_level: 0.45,
              timeline: []
            }
          },
          {
            id: 3,
            name: '资源分配的困境',
            description: '在有限的资源中做出最优分配决策',
            difficulty: 'normal',
            status: 'unlocked',
            progress: 45,
            rewards: ['资源管理技能', '效率提升 +30%', '高级工具'],
            estimatedTime: 25,
            universeVariant: {
              title: '均衡发展',
              final_score: 72,
              risk_level: 0.55,
              timeline: []
            }
          }
        ]
      },
      {
        id: 2,
        title: '第二章：中期挑战',
        description: '面对更复杂的决策场景',
        chapterProgress: 33,
        levels: [
          {
            id: 4,
            name: '团队协作的考验',
            description: '在团队中做出影响全局的决策',
            difficulty: 'hard',
            status: 'unlocked',
            progress: 0,
            rewards: ['领导力 +50', '团队加成 +25%', '协作徽章'],
            estimatedTime: 30,
            universeVariant: {
              title: '团队优先',
              final_score: 88,
              risk_level: 0.35,
              timeline: []
            }
          },
          {
            id: 5,
            name: '市场竞争的博弈',
            description: '在激烈的竞争中制定策略',
            difficulty: 'hard',
            status: 'locked',
            progress: 0,
            rewards: ['竞争力 +60', '市场洞察', '战略手册'],
            estimatedTime: 35,
            universeVariant: {
              title: '竞争策略',
              final_score: 81,
              risk_level: 0.62,
              timeline: []
            }
          },
          {
            id: 6,
            name: '创新突破的机遇',
            description: '抓住创新的机会实现突破',
            difficulty: 'nightmare',
            status: 'locked',
            progress: 0,
            rewards: ['创新奖励 +100', '突破徽章', '传奇装备'],
            estimatedTime: 45,
            universeVariant: {
              title: '创新路线',
              final_score: 92,
              risk_level: 0.75,
              timeline: []
            }
          }
        ]
      },
      {
        id: 3,
        title: '第三章：终极抉择',
        description: '决定你的最终命运',
        chapterProgress: 0,
        levels: [
          {
            id: 7,
            name: '多元宇宙的融合',
            description: '整合所有平行宇宙的力量',
            difficulty: 'nightmare',
            status: 'locked',
            progress: 0,
            rewards: ['宇宙融合', '无限可能', '终极成就'],
            estimatedTime: 60,
            universeVariant: {
              title: '完美融合',
              final_score: 95,
              risk_level: 0.85,
              timeline: []
            }
          }
        ]
      }
    ]

    this.calculateTotalProgress()
  }

  // 计算总进度
  private calculateTotalProgress() {
    let totalLevels = 0
    let completedLevels = 0

    this.chapters.forEach(chapter => {
      chapter.levels.forEach(level => {
        totalLevels++
        if (level.status === 'completed') {
          completedLevels++
        }
      })
    })

    this.totalProgress = totalLevels > 0 ? Math.round((completedLevels / totalLevels) * 100) : 0
  }

  // 获取难度标签
  private getDifficultyLabel(difficulty: string): string {
    const labels: Record<string, string> = {
      'easy': '简单',
      'normal': '普通',
      'hard': '困难',
      'nightmare': '噩梦'
    }
    return labels[difficulty] || difficulty
  }

  // 获取难度颜色
  private getDifficultyColor(difficulty: string): string {
    const colors: Record<string, string> = {
      'easy': '#4CAF50',
      'normal': '#2196F3',
      'hard': '#FF9800',
      'nightmare': '#F44336'
    }
    return colors[difficulty] || '#FFFFFF'
  }

  // 获取难度背景色
  private getDifficultyBgColor(difficulty: string): string {
    const colors: Record<string, string> = {
      'easy': '#1B5E20',
      'normal': '#0D47A1',
      'hard': '#E65100',
      'nightmare': '#B71C1C'
    }
    return colors[difficulty] || '#2A2E3A'
  }

  // 获取风险标签
  private getRiskLabel(risk: number): string {
    if (risk < 0.3) return '低风险'
    if (risk < 0.5) return '中风险'
    if (risk < 0.7) return '高风险'
    return '极高风险'
  }

  // 获取风险颜色
  private getRiskColor(risk: number): string {
    if (risk < 0.3) return '#4CAF50'
    if (risk < 0.5) return '#FFC107'
    if (risk < 0.7) return '#FF9800'
    return '#F44336'
  }
}






