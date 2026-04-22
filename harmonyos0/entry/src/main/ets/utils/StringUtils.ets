/**
 * 字符串工具类
 */
export class StringUtils {
  /**
   * 截断字符串
   */
  static truncate(str: string, maxLength: number): string {
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
  }
  
  /**
   * 判断字符串是否为空
   */
  static isEmpty(str: string | null | undefined): boolean {
    return !str || str.trim().length === 0;
  }
  
  /**
   * 验证邮箱格式
   */
  static isEmail(email: string): boolean {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return regex.test(email);
  }
  
  /**
   * 验证用户名格式（3-20个字符，字母数字下划线）
   */
  static isUsername(username: string): boolean {
    const regex = /^[a-zA-Z0-9_]{3,20}$/;
    return regex.test(username);
  }
  
  /**
   * 验证密码强度（至少6个字符）
   */
  static isValidPassword(password: string): boolean {
    return password.length >= 6;
  }
  
  /**
   * 首字母大写
   */
  static capitalize(str: string): string {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
  
  /**
   * 移除HTML标签
   */
  static stripHtml(html: string): string {
    return html.replace(/<[^>]*>/g, '');
  }
}
