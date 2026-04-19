/**
 * HarmonyOS 6 Design System - Theme Configuration
 * "Celestial" & "Fluid" Design Language
 * 灵动流体 · 星空美学
 */

// 色彩系统
interface ColorScheme {
  Primary: string
  Secondary: string
  Accent: string
  Warning: string
  Destructive: string
  BackgroundPrimary: string
  BackgroundSecondary: string
  BackgroundTertiary: string
  TextPrimary: string
  TextSecondary: string
  TextTertiary: string
  TextWhite: string
  GlassLight: string
  GlassMedium: string
  GlassHeavy: string
  GlassUltra: string
  BorderLight: string
  BorderMedium: string
  BorderHeavy: string
  OverlayLight: string
  OverlayMedium: string
  OverlayHeavy: string
}

// 渐变系统
interface GradientScheme {
  Aurora: string[]
  Sunrise: string[]
  Ocean: string[]
  Mint: string[]
  Mystic: string[]
  Glass: string[]
  Nebula: string[]
  Cosmic: string[]
  Twilight: string[]
  Emerald: string[]
}

// 间距系统
interface SpacingScheme {
  xs: number
  s: number
  m: number
  l: number
  xl: number
  xxl: number
  xxxl: number
}

// 圆角系统
interface RadiusScheme {
  xs: number
  s: number
  m: number
  l: number
  xl: number
  xxl: number
  round: number
}

// 字体系统
interface TypographyStyle {
  size: number
  weight: number
  lineHeight?: number
  letterSpacing?: number
}

interface TypographyScheme {
  DisplayLarge: TypographyStyle
  DisplayMedium: TypographyStyle
  DisplaySmall: TypographyStyle
  HeadingLarge: TypographyStyle
  HeadingMedium: TypographyStyle
  HeadingSmall: TypographyStyle
  BodyLarge: TypographyStyle
  BodyMedium: TypographyStyle
  BodySmall: TypographyStyle
  Caption: TypographyStyle
  Overline: TypographyStyle
}

// 阴影系统
interface ShadowStyle {
  radius: number
  color: string
  offsetY: number
  offsetX: number
}

interface ShadowScheme {
  Soft: ShadowStyle
  Medium: ShadowStyle
  Floating: ShadowStyle
  Elevated: ShadowStyle
  Glow: ShadowStyle
  GlowPrimary: ShadowStyle
  GlowAccent: ShadowStyle
  GlowWarning: ShadowStyle
}

// 动画系统
interface AnimationStyle {
  duration: number
  curve: string
}

interface AnimationScheme {
  Spring: AnimationStyle
  SpringBouncy: AnimationStyle
  Smooth: AnimationStyle
  Fast: AnimationStyle
  Slow: AnimationStyle
  Elastic: AnimationStyle
}

// 模糊系统
interface BlurScheme {
  Light: number
  Medium: number
  Heavy: number
  Ultra: number
}

export class Theme {
  // Colors - HarmonyOS 6 Celestial Theme
  static readonly Color: ColorScheme = {
    // Primary Brand Colors
    Primary: '#0A59F7', // 鸿蒙蓝
    Secondary: '#6B48FF', // 星空紫
    Accent: '#00C853', // 生机绿
    Warning: '#FF9500', // 警示橙
    Destructive: '#FF3B30', // 危险红

    // Backgrounds - 层次化背景
    BackgroundPrimary: '#F5F7FA', // 主背景
    BackgroundSecondary: '#FFFFFF', // 卡片背景
    BackgroundTertiary: '#FAFBFC', // 次级背景

    // Text - 文字层次
    TextPrimary: '#1A1A1A', // 主文字
    TextSecondary: '#666666', // 次要文字
    TextTertiary: '#999999', // 辅助文字
    TextWhite: '#FFFFFF',

    // Glass/Translucency - 毛玻璃效果
    GlassLight: 'rgba(255, 255, 255, 0.65)',
    GlassMedium: 'rgba(255, 255, 255, 0.80)',
    GlassHeavy: 'rgba(255, 255, 255, 0.92)',
    GlassUltra: 'rgba(255, 255, 255, 0.98)',
    
    // Borders - 边框
    BorderLight: 'rgba(0, 0, 0, 0.04)',
    BorderMedium: 'rgba(0, 0, 0, 0.08)',
    BorderHeavy: 'rgba(0, 0, 0, 0.12)',
    
    // Overlay - 遮罩层
    OverlayLight: 'rgba(0, 0, 0, 0.2)',
    OverlayMedium: 'rgba(0, 0, 0, 0.4)',
    OverlayHeavy: 'rgba(0, 0, 0, 0.6)',
  }

  // Gradients - 渐变色系
  static readonly Gradient: GradientScheme = {
    Aurora: ['#0A59F7', '#6B48FF'], // 极光
    Sunrise: ['#FF6B9D', '#FEC163'], // 日出
    Ocean: ['#4FACFE', '#00F2FE'], // 海洋
    Mint: ['#43E97B', '#38F9D7'], // 薄荷
    Mystic: ['#7F7FD5', '#86A8E7', '#91EAE4'], // 神秘
    Glass: ['rgba(255,255,255,0.8)', 'rgba(255,255,255,0.4)'], // 玻璃
    Nebula: ['#8E2DE2', '#4A00E0'], // 星云
    Cosmic: ['#667eea', '#764ba2'], // 宇宙
    Twilight: ['#fa709a', '#fee140'], // 暮光
    Emerald: ['#56ab2f', '#a8e063'], // 翡翠
  }

  // Spacing - 间距系统
  static readonly Spacing: SpacingScheme = {
    xs: 4,
    s: 8,
    m: 16,
    l: 24,
    xl: 32,
    xxl: 48,
    xxxl: 64,
  }

  // Corner Radius - 圆角系统
  static readonly Radius: RadiusScheme = {
    xs: 4,
    s: 8,
    m: 16,
    l: 24,
    xl: 32,
    xxl: 40,
    round: 999,
  }

  // Typography - 字体系统
  static readonly Typography: TypographyScheme = {
    DisplayLarge: { size: 48, weight: 900, lineHeight: 56, letterSpacing: -0.5 } as TypographyStyle,
    DisplayMedium: { size: 40, weight: 800, lineHeight: 48, letterSpacing: -0.3 } as TypographyStyle,
    DisplaySmall: { size: 32, weight: 700, lineHeight: 40, letterSpacing: 0 } as TypographyStyle,
    HeadingLarge: { size: 28, weight: 700, lineHeight: 36, letterSpacing: 0 } as TypographyStyle,
    HeadingMedium: { size: 24, weight: 600, lineHeight: 32, letterSpacing: 0 } as TypographyStyle,
    HeadingSmall: { size: 20, weight: 600, lineHeight: 28, letterSpacing: 0 } as TypographyStyle,
    BodyLarge: { size: 17, weight: 400, lineHeight: 26, letterSpacing: 0 } as TypographyStyle,
    BodyMedium: { size: 15, weight: 400, lineHeight: 24, letterSpacing: 0 } as TypographyStyle,
    BodySmall: { size: 13, weight: 400, lineHeight: 20, letterSpacing: 0 } as TypographyStyle,
    Caption: { size: 12, weight: 400, lineHeight: 18, letterSpacing: 0 } as TypographyStyle,
    Overline: { size: 11, weight: 600, lineHeight: 16, letterSpacing: 1 } as TypographyStyle,
  }

  // Shadows - 阴影系统
  static readonly Shadow: ShadowScheme = {
    Soft: { radius: 12, color: 'rgba(0,0,0,0.04)', offsetY: 4, offsetX: 0 } as ShadowStyle,
    Medium: { radius: 20, color: 'rgba(0,0,0,0.06)', offsetY: 8, offsetX: 0 } as ShadowStyle,
    Floating: { radius: 32, color: 'rgba(0,0,0,0.08)', offsetY: 16, offsetX: 0 } as ShadowStyle,
    Elevated: { radius: 40, color: 'rgba(0,0,0,0.12)', offsetY: 24, offsetX: 0 } as ShadowStyle,
    Glow: { radius: 24, color: 'rgba(10, 89, 247, 0.25)', offsetY: 0, offsetX: 0 } as ShadowStyle,
    GlowPrimary: { radius: 20, color: 'rgba(10, 89, 247, 0.3)', offsetY: 4, offsetX: 0 } as ShadowStyle,
    GlowAccent: { radius: 20, color: 'rgba(0, 200, 83, 0.3)', offsetY: 4, offsetX: 0 } as ShadowStyle,
    GlowWarning: { radius: 20, color: 'rgba(255, 149, 0, 0.3)', offsetY: 4, offsetX: 0 } as ShadowStyle,
  }

  // Animation - 动画系统
  static readonly Animation: AnimationScheme = {
    Spring: { duration: 450, curve: 'spring' } as AnimationStyle,
    SpringBouncy: { duration: 600, curve: 'spring-bouncy' } as AnimationStyle,
    Smooth: { duration: 350, curve: 'ease-in-out' } as AnimationStyle,
    Fast: { duration: 200, curve: 'ease-out' } as AnimationStyle,
    Slow: { duration: 500, curve: 'ease-in-out' } as AnimationStyle,
    Elastic: { duration: 800, curve: 'elastic' } as AnimationStyle,
  }

  // Blur - 模糊系统
  static readonly Blur: BlurScheme = {
    Light: 10,
    Medium: 20,
    Heavy: 40,
    Ultra: 60,
  }
}


