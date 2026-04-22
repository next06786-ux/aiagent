/**
 * 应用主题配置
 */

/**
 * 颜色主题
 */
export interface ColorTheme {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  error: string;
  success: string;
  warning: string;
}

/**
 * 默认亮色主题
 */
export const lightTheme: ColorTheme = {
  primary: '#0A59F7',
  secondary: '#00D4AA',
  background: '#F5F5F5',
  surface: '#FFFFFF',
  text: '#333333',
  textSecondary: '#666666',
  border: '#E0E0E0',
  error: '#FF3B30',
  success: '#34C759',
  warning: '#FF9500'
};

/**
 * 默认暗色主题
 */
export const darkTheme: ColorTheme = {
  primary: '#0A59F7',
  secondary: '#00D4AA',
  background: '#1C1C1E',
  surface: '#2C2C2E',
  text: '#FFFFFF',
  textSecondary: '#AEAEB2',
  border: '#38383A',
  error: '#FF453A',
  success: '#32D74B',
  warning: '#FF9F0A'
};

/**
 * 获取当前主题
 */
export function getCurrentTheme(): ColorTheme {
  return lightTheme;
}
