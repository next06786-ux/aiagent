/**
 * 副本系统配置和数据管理
 * 用于管理副本的难度、奖励、进度等数据
 */

// 副本难度配置
export const DifficultyConfig = {
  easy: {
    label: '简单',
    color: '#4CAF50',
    bgColor: '#1B5E20',
    multiplier: 1.0,
    minLevel: 1,
    maxLevel: 10
  },
  normal: {
    label: '普通',
    color: '#2196F3',
    bgColor: '#0D47A1',
    multiplier: 1.5,
    minLevel: 10,
    maxLevel: 30
  },
  hard: {
    label: '困难',
    color: '#FF9800',
    bgColor: '#E65100',
    multiplier: 2.0,
    minLevel: 30,
    maxLevel: 50
  },
  nightmare: {
    label: '噩梦',
    color: '#F44336',
    bgColor: '#B71C1C',
    multiplier: 3.0,
    minLevel: 50,
    maxLevel: 100
  }
}

// 副本奖励配置
export const RewardConfig = {
  experience: {
    easy: 100,
    normal: 250,
    hard: 500,
    nightmare: 1000
  },
  gold: {
    easy: 50,
    normal: 150,
    hard: 400,
    nightmare: 1000
  },
  items: {
    easy: ['初级装备', '基础材料'],
    normal: ['中级装备', '稀有材料'],
    hard: ['高级装备', '传奇材料'],
    nightmare: ['传奇装备', '神秘碎片']
  }
}

// 副本进度状态
export enum DungeonStatus {
  LOCKED = 'locked',
  UNLOCKED = 'unlocked',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CURRENT = 'current'
}

// 副本类型
export enum DungeonType {
  STORY = 'story',           // 故事副本
  CHALLENGE = 'challenge',   // 挑战副本
  SURVIVAL = 'survival',     // 生存副本
  PUZZLE = 'puzzle',         // 谜题副本
  BOSS = 'boss'              // Boss副本
}

// 副本数据结构
export interface DungeonData {
  id: number
  name: string
  description: string
  type: DungeonType
  difficulty: 'easy' | 'normal' | 'hard' | 'nightmare'
  status: DungeonStatus
  progress: number
  estimatedTime: number
  rewards: {
    experience: number
    gold: number
    items: string[]
    achievements: string[]
  }
  requirements: {
    minLevel: number
    requiredItems: string[]
    previousDungeons: number[]
  }
  statistics: {
    attempts: number
    completions: number
    bestTime: number
    averageTime: number
  }
}

// 副本章节数据
export interface ChapterData {
  id: number
  title: string
  description: string
  dungeons: DungeonData[]
  progress: number
  unlockCondition: string
}

// 玩家副本进度
export interface PlayerDungeonProgress {
  playerId: string
  completedDungeons: number[]
  currentDungeon: number | null
  totalProgress: number
  achievements: string[]
  statistics: {
    totalAttempts: number
    totalCompletions: number
    totalPlayTime: number
    averageCompletionTime: number
  }
}

// 副本管理器
export class DungeonManager {
  private dungeons: Map<number, DungeonData> = new Map()
  private chapters: Map<number, ChapterData> = new Map()
  private playerProgress: PlayerDungeonProgress

  constructor(playerId: string) {
    this.playerProgress = {
      playerId,
      completedDungeons: [],
      currentDungeon: null,
      totalProgress: 0,
      achievements: [],
      statistics: {
        totalAttempts: 0,
        totalCompletions: 0,
        totalPlayTime: 0,
        averageCompletionTime: 0
      }
    }
  }

  // 添加副本
  addDungeon(dungeon: DungeonData): void {
    this.dungeons.set(dungeon.id, dungeon)
  }

  // 添加章节
  addChapter(chapter: ChapterData): void {
    this.chapters.set(chapter.id, chapter)
  }

  // 获取副本
  getDungeon(id: number): DungeonData | undefined {
    return this.dungeons.get(id)
  }

  // 获取章节
  getChapter(id: number): ChapterData | undefined {
    return this.chapters.get(id)
  }

  // 获取所有副本
  getAllDungeons(): DungeonData[] {
    return Array.from(this.dungeons.values())
  }

  // 获取所有章节
  getAllChapters(): ChapterData[] {
    return Array.from(this.chapters.values())
  }

  // 开始副本
  startDungeon(dungeonId: number): boolean {
    const dungeon = this.getDungeon(dungeonId)
    if (!dungeon) return false

    if (dungeon.status === DungeonStatus.LOCKED) {
      return false
    }

    this.playerProgress.currentDungeon = dungeonId
    dungeon.statistics.attempts++
    return true
  }

  // 完成副本
  completeDungeon(dungeonId: number, timeSpent: number): boolean {
    const dungeon = this.getDungeon(dungeonId)
    if (!dungeon) return false

    dungeon.status = DungeonStatus.COMPLETED
    dungeon.statistics.completions++
    dungeon.statistics.bestTime = Math.min(
      dungeon.statistics.bestTime || timeSpent,
      timeSpent
    )

    this.playerProgress.completedDungeons.push(dungeonId)
    this.playerProgress.currentDungeon = null
    this.playerProgress.statistics.totalCompletions++
    this.playerProgress.statistics.totalPlayTime += timeSpent

    // 解锁后续副本
    this.unlockNextDungeons(dungeonId)

    // 更新总进度
    this.updateTotalProgress()

    return true
  }

  // 解锁后续副本
  private unlockNextDungeons(dungeonId: number): void {
    this.dungeons.forEach(dungeon => {
      if (dungeon.requirements.previousDungeons.includes(dungeonId)) {
        if (dungeon.status === DungeonStatus.LOCKED) {
          dungeon.status = DungeonStatus.UNLOCKED
        }
      }
    })
  }

  // 更新总进度
  private updateTotalProgress(): void {
    const totalDungeons = this.dungeons.size
    const completedCount = this.playerProgress.completedDungeons.length
    this.playerProgress.totalProgress = Math.round((completedCount / totalDungeons) * 100)
  }

  // 获取玩家进度
  getPlayerProgress(): PlayerDungeonProgress {
    return this.playerProgress
  }

  // 获取可用副本列表
  getAvailableDungeons(): DungeonData[] {
    return this.getAllDungeons().filter(
      d => d.status === DungeonStatus.UNLOCKED || d.status === DungeonStatus.CURRENT
    )
  }

  // 获取已完成副本列表
  getCompletedDungeons(): DungeonData[] {
    return this.getAllDungeons().filter(
      d => d.status === DungeonStatus.COMPLETED
    )
  }

  // 计算奖励
  calculateRewards(dungeonId: number): any {
    const dungeon = this.getDungeon(dungeonId)
    if (!dungeon) return null

    return {
      experience: dungeon.rewards.experience,
      gold: dungeon.rewards.gold,
      items: dungeon.rewards.items,
      achievements: dungeon.rewards.achievements
    }
  }

  // 检查是否满足副本要求
  canAccessDungeon(dungeonId: number, playerLevel: number): boolean {
    const dungeon = this.getDungeon(dungeonId)
    if (!dungeon) return false

    if (dungeon.status === DungeonStatus.LOCKED) return false

    if (playerLevel < dungeon.requirements.minLevel) return false

    // 检查前置副本
    for (const prevId of dungeon.requirements.previousDungeons) {
      if (!this.playerProgress.completedDungeons.includes(prevId)) {
        return false
      }
    }

    return true
  }

  // 获取副本统计信息
  getDungeonStatistics(dungeonId: number): any {
    const dungeon = this.getDungeon(dungeonId)
    if (!dungeon) return null

    return {
      attempts: dungeon.statistics.attempts,
      completions: dungeon.statistics.completions,
      successRate: dungeon.statistics.attempts > 0
        ? Math.round((dungeon.statistics.completions / dungeon.statistics.attempts) * 100)
        : 0,
      bestTime: dungeon.statistics.bestTime,
      averageTime: dungeon.statistics.averageTime
    }
  }
}

// 副本工厂 - 快速创建副本
export class DungeonFactory {
  static createDungeon(
    id: number,
    name: string,
    difficulty: 'easy' | 'normal' | 'hard' | 'nightmare',
    type: DungeonType = DungeonType.STORY
  ): DungeonData {
    const config = DifficultyConfig[difficulty]
    const rewards = RewardConfig

    return {
      id,
      name,
      description: `${name} - ${config.label}难度副本`,
      type,
      difficulty,
      status: DungeonStatus.LOCKED,
      progress: 0,
      estimatedTime: 15 + (Object.keys(DifficultyConfig).indexOf(difficulty) * 10),
      rewards: {
        experience: rewards.experience[difficulty],
        gold: rewards.gold[difficulty],
        items: rewards.items[difficulty],
        achievements: []
      },
      requirements: {
        minLevel: config.minLevel,
        requiredItems: [],
        previousDungeons: []
      },
      statistics: {
        attempts: 0,
        completions: 0,
        bestTime: 0,
        averageTime: 0
      }
    }
  }

  static createChapter(
    id: number,
    title: string,
    dungeons: DungeonData[]
  ): ChapterData {
    return {
      id,
      title,
      description: `${title} - 包含${dungeons.length}个副本`,
      dungeons,
      progress: 0,
      unlockCondition: '完成前一章节'
    }
  }
}






