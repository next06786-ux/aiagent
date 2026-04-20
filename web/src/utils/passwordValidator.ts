/**
 * 密码验证工具
 */

export interface PasswordStrength {
  score: number; // 0-4
  level: 'weak' | 'medium' | 'strong' | 'very-strong';
  message: string;
  suggestions: string[];
}

export function validatePassword(password: string): PasswordStrength {
  const suggestions: string[] = [];
  let score = 0;

  // 长度检查
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  else if (password.length < 8) {
    suggestions.push('密码长度至少8个字符');
  }

  // 包含小写字母
  if (/[a-z]/.test(password)) {
    score++;
  } else {
    suggestions.push('包含小写字母');
  }

  // 包含大写字母
  if (/[A-Z]/.test(password)) {
    score++;
  } else {
    suggestions.push('包含大写字母');
  }

  // 包含数字
  if (/\d/.test(password)) {
    score++;
  } else {
    suggestions.push('包含数字');
  }

  // 包含特殊字符
  if (/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(password)) {
    score++;
  } else {
    suggestions.push('包含特殊字符');
  }

  // 计算最终分数（最高4分）
  const finalScore = Math.min(score, 4);

  let level: PasswordStrength['level'];
  let message: string;

  if (finalScore === 0 || password.length < 6) {
    level = 'weak';
    message = '密码太弱';
  } else if (finalScore <= 2) {
    level = 'weak';
    message = '密码强度较弱';
  } else if (finalScore === 3) {
    level = 'medium';
    message = '密码强度中等';
  } else if (finalScore === 4 && password.length >= 12) {
    level = 'very-strong';
    message = '密码强度很好';
  } else {
    level = 'strong';
    message = '密码强度良好';
  }

  return {
    score: finalScore,
    level,
    message,
    suggestions,
  };
}

export function validateEmail(email: string): boolean {
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailRegex.test(email);
}

export function validateUsername(username: string): {
  valid: boolean;
  message?: string;
} {
  if (username.length < 3) {
    return { valid: false, message: '用户名至少3个字符' };
  }
  if (username.length > 50) {
    return { valid: false, message: '用户名最多50个字符' };
  }
  
  // 支持邮箱格式登录
  if (username.includes('@')) {
    if (!validateEmail(username)) {
      return { valid: false, message: '邮箱格式不正确' };
    }
    return { valid: true };
  }
  
  // 支持中文、字母、数字和下划线
  // 移除了严格的字母数字下划线限制，允许中文等字符
  return { valid: true };
}
