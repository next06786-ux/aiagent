/**
 * 数据预加载工具
 * 在应用启动时预加载常用数据
 */
import { KnowledgeGraphService } from '../services/KnowledgeGraphService';
import { ScheduleService } from '../services/ScheduleService';
import { SocialService } from '../services/SocialService';
import { OfflineCache } from './OfflineCache';
import { AppConstants } from '../constants/AppConstants';

export class DataPreloader {
  private cache = new OfflineCache();
  private kgService = new KnowledgeGraphService();
  private scheduleService = new ScheduleService();
  private socialService = new SocialService();
  
  /**
   * 预加载用户数据
   */
  async preloadUserData(userId: string): Promise<void> {
    console.log('开始预加载用户数据...');
    
    const startTime = Date.now();
    
    // 并行加载多个数据
    const promises = [
      this.preloadKnowledgeGraph(userId),
      this.preloadSchedules(userId),
      this.preloadFriends(userId),
      this.preloadRecentConversations(userId)
    ];
    
    try {
      await Promise.all(promises);
      const duration = Date.now() - startTime;
      console.log(`数据预加载完成，耗时: ${duration}ms`);
    } catch (error) {
      console.error('数据预加载失败:', error);
    }
  }
  
  /**
   * 预加载知识图谱
   */
  private async preloadKnowledgeGraph(userId: string): Promise<void> {
    try {
      console.log('预加载知识图谱...');
      
      const starMaps = await Promise.all([
        this.kgService.getCareerStarMap(userId),
        this.kgService.getEducationStarMap(userId),
        this.kgService.getRelationshipStarMap(userId)
      ]);
      
      // 缓存到本地
      await this.cache.cacheData(
        `${AppConstants.CACHE_KEYS.STAR_MAPS}_${userId}`,
        {
          career: starMaps[0],
          education: starMaps[1],
          relationship: starMaps[2],
          timestamp: Date.now()
        }
      );
      
      console.log('知识图谱预加载完成');
    } catch (error) {
      console.error('知识图谱预加载失败:', error);
    }
  }
  
  /**
   * 预加载日程
   */
  private async preloadSchedules(userId: string): Promise<void> {
    try {
      console.log('预加载日程...');
      
      const schedules = await this.scheduleService.getTodaySchedule(userId);
      
      // 缓存到本地
      await this.cache.cacheData(
        `schedules_today_${userId}`,
        {
          schedules,
          timestamp: Date.now()
        }
      );
      
      console.log('日程预加载完成');
    } catch (error) {
      console.error('日程预加载失败:', error);
    }
  }
  
  /**
   * 预加载好友列表
   */
  private async preloadFriends(userId: string): Promise<void> {
    try {
      console.log('预加载好友列表...');
      
      const friends = await this.socialService.getFriendsList(userId);
      
      // 缓存到本地
      await this.cache.cacheData(
        `friends_${userId}`,
        {
          friends,
          timestamp: Date.now()
        }
      );
      
      console.log('好友列表预加载完成');
    } catch (error) {
      console.error('好友列表预加载失败:', error);
    }
  }
  
  /**
   * 预加载最近对话
   */
  private async preloadRecentConversations(userId: string): Promise<void> {
    try {
      console.log('预加载最近对话...');
      
      // TODO: 实现对话历史API后添加
      // const conversations = await conversationService.getRecentConversations(userId);
      
      // 缓存到本地
      await this.cache.cacheData(
        `${AppConstants.CACHE_KEYS.RECENT_CONVERSATIONS}_${userId}`,
        {
          conversations: [],
          timestamp: Date.now()
        }
      );
      
      console.log('最近对话预加载完成');
    } catch (error) {
      console.error('最近对话预加载失败:', error);
    }
  }
  
  /**
   * 清除用户缓存
   */
  async clearUserCache(userId: string): Promise<void> {
    await this.cache.removeCache(`${AppConstants.CACHE_KEYS.STAR_MAPS}_${userId}`);
    await this.cache.removeCache(`schedules_today_${userId}`);
    await this.cache.removeCache(`friends_${userId}`);
    await this.cache.removeCache(`${AppConstants.CACHE_KEYS.RECENT_CONVERSATIONS}_${userId}`);
  }
  
  /**
   * 检查缓存是否过期（默认1小时）
   */
  isCacheExpired(timestamp: number, maxAge: number = 3600000): boolean {
    return Date.now() - timestamp > maxAge;
  }
}
