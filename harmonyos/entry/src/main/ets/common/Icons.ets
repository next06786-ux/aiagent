/**
 * HarmonyOS 6 Professional Icon System
 * 专业矢量图标库 - SVG + 自定义绘制
 */

/**
 * 图标配置接口
 */
export interface IconConfig {
  size: number
  color: string
  strokeWidth?: number
}

/**
 * 专业图标组件库
 */
export class Icons {
  /**
   * AI 对话图标 - 对话气泡
   */
  static ChatIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 6C4 4.89543 4.89543 4 6 4H18C19.1046 4 20 4.89543 20 6V14C20 15.1046 19.1046 16 18 16H8L4 20V6Z" 
              fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="8" cy="10" r="1" fill="${color}"/>
        <circle cx="12" cy="10" r="1" fill="${color}"/>
        <circle cx="16" cy="10" r="1" fill="${color}"/>
      </svg>
    `
  }

  /**
   * 知识图谱图标 - 网络节点
   */
  static NetworkIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="6" cy="6" r="2" fill="${color}"/>
        <circle cx="18" cy="6" r="2" fill="${color}"/>
        <circle cx="12" cy="16" r="2" fill="${color}"/>
        <line x1="8" y1="7" x2="16" y2="15" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <line x1="16" y1="7" x2="14" y2="15" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <line x1="6" y1="8" x2="12" y2="14" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
      </svg>
    `
  }

  /**
   * 智能洞察图标 - 数据分析
   */
  static AnalyticsIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <rect x="3" y="12" width="3" height="8" fill="${color}"/>
        <rect x="10" y="6" width="3" height="14" fill="${color}"/>
        <rect x="17" y="9" width="3" height="11" fill="${color}"/>
        <line x1="2" y1="20" x2="22" y2="20" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
      </svg>
    `
  }

  /**
   * 元智能体图标 - 协同齿轮
   */
  static AgentIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="8" cy="12" r="3" fill="none" stroke="${color}" stroke-width="${strokeWidth}"/>
        <circle cx="16" cy="12" r="3" fill="none" stroke="${color}" stroke-width="${strokeWidth}"/>
        <path d="M11 12H13" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <path d="M8 9V6M8 15V18" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <path d="M16 9V6M16 15V18" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
      </svg>
    `
  }

  /**
   * 视觉识别图标 - 相机镜头
   */
  static CameraIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 6C4 4.89543 4.89543 4 6 4H14C15.1046 4 16 4.89543 16 6V14C16 15.1046 15.1046 16 14 16H6C4.89543 16 4 15.1046 4 14V6Z" 
              fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="10" cy="10" r="3" fill="none" stroke="${color}" stroke-width="${strokeWidth}"/>
        <circle cx="14" cy="6" r="1" fill="${color}"/>
      </svg>
    `
  }

  /**
   * 学习进化图标 - 上升箭头
   */
  static LearningIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 16L8 12L12 14L20 6" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M16 6H20V10" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `
  }

  /**
   * 生活领域图标 - 六边形
   */
  static LifeIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L20 6V14L12 18L4 14V6L12 2Z" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
        <line x1="12" y1="2" x2="12" y2="18" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <line x1="4" y1="10" x2="20" y2="10" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
      </svg>
    `
  }

  /**
   * 决策对比图标 - 天平
   */
  static ComparisonIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <line x1="12" y1="2" x2="12" y2="6" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <path d="M4 6L12 6L20 6" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
        <rect x="2" y="6" width="4" height="6" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
        <rect x="18" y="6" width="4" height="6" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
        <line x1="4" y1="18" x2="20" y2="18" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
      </svg>
    `
  }

  /**
   * 首页图标 - 房子
   */
  static HomeIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 12L12 3L21 12V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V12Z" 
              fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
        <rect x="9" y="12" width="6" height="9" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `
  }

  /**
   * 洞察图标 - 灯泡
   */
  static InsightIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <path d="M9 2C5.13401 2 2 5.13401 2 9C2 12.5 4 14 4 16C4 17.1046 4.89543 18 6 18H14C15.1046 18 16 17.1046 16 16C16 14 18 12.5 18 9C18 5.13401 14.866 2 11 2C10.4477 2 9.5 2 9 2Z" 
              fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
        <line x1="8" y1="18" x2="12" y2="18" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <line x1="7" y1="21" x2="13" y2="21" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
      </svg>
    `
  }

  /**
   * AI 图标 - 芯片
   */
  static AIIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <rect x="4" y="4" width="16" height="16" rx="2" fill="none" stroke="${color}" stroke-width="${strokeWidth}"/>
        <rect x="7" y="7" width="10" height="10" rx="1" fill="none" stroke="${color}" stroke-width="${strokeWidth}"/>
        <circle cx="12" cy="12" r="2" fill="${color}"/>
        <line x1="4" y1="12" x2="2" y2="12" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <line x1="20" y1="12" x2="22" y2="12" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <line x1="12" y1="4" x2="12" y2="2" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <line x1="12" y1="20" x2="12" y2="22" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
      </svg>
    `
  }

  /**
   * 用户图标 - 人物
   */
  static UserIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="7" r="4" fill="none" stroke="${color}" stroke-width="${strokeWidth}"/>
        <path d="M4 20C4 16.134 7.582 13 12 13C16.418 13 20 16.134 20 20" 
              fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `
  }

  /**
   * 返回图标 - 左箭头
   */
  static BackIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 12H6M6 12L12 18M6 12L12 6" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `
  }

  /**
   * 设置图标 - 齿轮
   */
  static SettingsIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="3" fill="none" stroke="${color}" stroke-width="${strokeWidth}"/>
        <path d="M12 2V4M12 20V22M22 12H20M4 12H2M19.07 4.93L17.65 6.35M6.35 17.65L4.93 19.07M19.07 19.07L17.65 17.65M6.35 6.35L4.93 4.93" 
              stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `
  }

  /**
   * 日期图标 - 日历
   */
  static CalendarIcon(config: IconConfig): string {
    const size = config.size
    const color = config.color
    const strokeWidth = config.strokeWidth || 2
    const viewBox = `0 0 ${size} ${size}`
    return `
      <svg viewBox="${viewBox}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <rect x="3" y="4" width="18" height="16" rx="2" fill="none" stroke="${color}" stroke-width="${strokeWidth}"/>
        <line x1="3" y1="10" x2="21" y2="10" stroke="${color}" stroke-width="${strokeWidth}"/>
        <line x1="7" y1="1" x2="7" y2="7" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
        <line x1="17" y1="1" x2="17" y2="7" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"/>
      </svg>
    `
  }
}

/**
 * 图标映射表接口
 */
interface IconMapType {
  chat: string
  network: string
  analytics: string
  agent: string
  camera: string
  learning: string
  life: string
  comparison: string
  home: string
  insight: string
  ai: string
  user: string
  back: string
  settings: string
  calendar: string
}

/**
 * 图标映射表 - 用于快速查找
 */
export const IconMap: IconMapType = {
  chat: 'ChatIcon',
  network: 'NetworkIcon',
  analytics: 'AnalyticsIcon',
  agent: 'AgentIcon',
  camera: 'CameraIcon',
  learning: 'LearningIcon',
  life: 'LifeIcon',
  comparison: 'ComparisonIcon',
  home: 'HomeIcon',
  insight: 'InsightIcon',
  ai: 'AIIcon',
  user: 'UserIcon',
  back: 'BackIcon',
  settings: 'SettingsIcon',
  calendar: 'CalendarIcon'
}
