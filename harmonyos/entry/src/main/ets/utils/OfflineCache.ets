/**
 * 离线缓存工具
 * 使用Preferences存储离线数据
 */
import dataPreferences from '@ohos.data.preferences';

export class OfflineCache {
  private preferences: dataPreferences.Preferences | null = null;
  private preferencesName: string = 'offline_cache';
  
  /**
   * 初始化
   */
  async init(): Promise<void> {
    this.preferences = await dataPreferences.getPreferences(
      getContext(this),
      this.preferencesName
    );
  }
  
  /**
   * 缓存数据
   */
  async cacheData(key: string, data: Object): Promise<void> {
    if (!this.preferences) {
      await this.init();
    }
    
    await this.preferences?.put(key, JSON.stringify(data));
    await this.preferences?.flush();
  }
  
  /**
   * 获取缓存数据
   */
  async getCachedData<T>(key: string): Promise<T | null> {
    if (!this.preferences) {
      await this.init();
    }
    
    const data = await this.preferences?.get(key, '');
    
    if (data && typeof data === 'string' && data.length > 0) {
      try {
        return JSON.parse(data) as T;
      } catch (error) {
        console.error('解析缓存数据失败:', error);
        return null;
      }
    }
    
    return null;
  }
  
  /**
   * 检查缓存是否存在
   */
  async hasCache(key: string): Promise<boolean> {
    if (!this.preferences) {
      await this.init();
    }
    
    const data = await this.preferences?.get(key, '');
    return data !== '';
  }
  
  /**
   * 删除缓存
   */
  async removeCache(key: string): Promise<void> {
    if (!this.preferences) {
      await this.init();
    }
    
    await this.preferences?.delete(key);
    await this.preferences?.flush();
  }
  
  /**
   * 清除所有缓存
   */
  async clearCache(): Promise<void> {
    if (!this.preferences) {
      await this.init();
    }
    
    await this.preferences?.clear();
    await this.preferences?.flush();
  }
  
  /**
   * 获取所有缓存键
   */
  async getAllKeys(): Promise<string[]> {
    if (!this.preferences) {
      await this.init();
    }
    
    // HarmonyOS Preferences没有直接获取所有键的方法
    // 需要维护一个键列表
    const keysData = await this.preferences?.get('__cache_keys__', '');
    
    if (keysData && typeof keysData === 'string' && keysData.length > 0) {
      try {
        return JSON.parse(keysData) as string[];
      } catch (error) {
        return [];
      }
    }
    
    return [];
  }
  
  /**
   * 添加键到列表
   */
  private async addKeyToList(key: string): Promise<void> {
    const keys = await this.getAllKeys();
    if (!keys.includes(key)) {
      keys.push(key);
      await this.preferences?.put('__cache_keys__', JSON.stringify(keys));
      await this.preferences?.flush();
    }
  }
  
  /**
   * 从列表移除键
   */
  private async removeKeyFromList(key: string): Promise<void> {
    const keys = await this.getAllKeys();
    const index = keys.indexOf(key);
    if (index > -1) {
      keys.splice(index, 1);
      await this.preferences?.put('__cache_keys__', JSON.stringify(keys));
      await this.preferences?.flush();
    }
  }
}
