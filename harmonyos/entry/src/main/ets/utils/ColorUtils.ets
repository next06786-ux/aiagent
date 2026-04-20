/**
 * 颜色工具类
 */
import { AppConstants } from '../constants/AppConstants';

export class ColorUtils {
  /**
   * 十六进制颜色转RGBA
   */
  static hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  
  /**
   * 根据分数获取颜色
   */
  static getScoreColor(score: number): string {
    if (score >= 70) return AppConstants.COLORS.SUCCESS;
    if (score >= 40) return AppConstants.COLORS.WARNING;
    return AppConstants.COLORS.DANGER;
  }
  
  /**
   * 根据立场获取颜色
   */
  static getStanceColor(stance: string): string {
    if (stance === '支持') return AppConstants.COLORS.SUCCESS;
    if (stance === '反对') return AppConstants.COLORS.DANGER;
    return AppConstants.COLORS.GRAY;
  }
  
  /**
   * 根据立场获取背景色
   */
  static getStanceBackground(stance: string): string {
    if (stance === '支持') return 'rgba(52, 199, 89, 0.1)';
    if (stance === '反对') return 'rgba(255, 59, 48, 0.1)';
    return 'rgba(142, 142, 147, 0.1)';
  }
  
  /**
   * 根据Agent ID获取颜色
   */
  static getAgentColor(agentId: string): string {
    const persona = AppConstants.PERSONAS.find(p => p.id === agentId);
    return persona ? persona.color : AppConstants.COLORS.PRIMARY;
  }
  
  /**
   * 根据优先级获取颜色
   */
  static getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high':
        return AppConstants.COLORS.DANGER;
      case 'medium':
        return AppConstants.COLORS.WARNING;
      case 'low':
        return AppConstants.COLORS.GRAY;
      default:
        return AppConstants.COLORS.PRIMARY;
    }
  }
}
