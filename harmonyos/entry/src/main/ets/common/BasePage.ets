/**
 * 基础页面类
 * 提供通用的用户ID管理功能
 */
import { getUserSessionManager, UserSessionManager } from '../service/UserSessionManager';

/**
 * 页面基类接口
 * 所有需要用户ID的页面都应该实现这个接口
 */
export interface IBasePage {
  userId: string;
  onUserIdChanged(userId: string): void;
}

/**
 * 页面初始化辅助函数
 * 在 aboutToAppear 中调用
 */
export async function initializePageWithUserId(page: IBasePage): Promise<void> {
  try {
    const sessionManager = getUserSessionManager();
    
    // 获取当前用户ID
    const userId = await sessionManager.getUserId();
    page.userId = userId;
    
    console.info('[BasePage] 页面初始化，用户ID:', userId);
    
    // 添加监听器，当用户ID变化时更新
    const listener = (newUserId: string) => {
      console.info('[BasePage] 用户ID变化:', newUserId);
      page.userId = newUserId;
      if (page.onUserIdChanged) {
        page.onUserIdChanged(newUserId);
      }
    };
    
    sessionManager.addListener(listener);
    
  } catch (err) {
    console.error('[BasePage] 初始化失败:', err);
    page.userId = 'default_user';
  }
}

/**
 * 快速获取用户ID的辅助函数
 * 用于不需要监听变化的场景
 */
export async function getPageUserId(): Promise<string> {
  try {
    const sessionManager = getUserSessionManager();
    return await sessionManager.getUserId();
  } catch (err) {
    console.error('[BasePage] 获取用户ID失败:', err);
    return 'default_user';
  }
}
