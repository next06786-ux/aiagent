/**
 * 日期工具类
 */
export class DateUtils {
  /**
   * 格式化日期 YYYY-MM-DD
   */
  static formatDate(timestamp: number | string): string {
    const date = new Date(timestamp);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
  
  /**
   * 格式化日期时间 YYYY-MM-DD HH:mm
   */
  static formatDateTime(timestamp: number | string): string {
    const date = new Date(timestamp);
    const dateStr = DateUtils.formatDate(timestamp);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${dateStr} ${hours}:${minutes}`;
  }
  
  /**
   * 格式化日期时间（秒） YYYY-MM-DD HH:mm:ss
   */
  static formatDateTimeWithSeconds(timestamp: number | string): string {
    const date = new Date(timestamp);
    const dateStr = DateUtils.formatDate(timestamp);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${dateStr} ${hours}:${minutes}:${seconds}`;
  }
  
  /**
   * 获取相对时间
   */
  static getRelativeTime(timestamp: number | string): string {
    const now = Date.now();
    const time = new Date(timestamp).getTime();
    const diff = now - time;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const months = Math.floor(days / 30);
    const years = Math.floor(days / 365);
    
    if (years > 0) return `${years}年前`;
    if (months > 0) return `${months}个月前`;
    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    return '刚刚';
  }
  
  /**
   * 获取今天的日期字符串
   */
  static getToday(): string {
    return DateUtils.formatDate(Date.now());
  }
  
  /**
   * 获取明天的日期字符串
   */
  static getTomorrow(): string {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return DateUtils.formatDate(tomorrow.getTime());
  }
}
