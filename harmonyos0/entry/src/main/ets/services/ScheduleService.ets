/**
 * 日程服务
 * 处理日程管理、推荐、自动生成
 */
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { Schedule, ScheduleInput, ScheduleRecommendation } from '../models/Schedule';

export class ScheduleService {
  private httpClient = HttpClient.getInstance();
  
  /**
   * 获取日程列表
   */
  async getScheduleList(userId: string, date?: string): Promise<Schedule[]> {
    const params: Record<string, string> = {};
    if (date) {
      params.date = date;
    }
    
    const result = await this.httpClient.get<Schedule[]>(
      `${ApiConstants.SCHEDULE.LIST}/${userId}`,
      params
    );
    
    return result.data;
  }
  
  /**
   * 获取日程（按时间范围）
   */
  async getSchedules(startTime: number, endTime: number): Promise<Schedule[]> {
    const result = await this.httpClient.get<Schedule[]>(
      ApiConstants.SCHEDULE.LIST,
      {
        start_time: startTime.toString(),
        end_time: endTime.toString()
      }
    );
    
    return result.data || [];
  }
  
  /**
   * 添加日程
   */
  async addSchedule(schedule: ScheduleInput): Promise<Schedule> {
    const scheduleData: Record<string, Object> = {
      user_id: schedule.user_id,
      title: schedule.title,
      start_time: schedule.start_time,
      end_time: schedule.end_time
    };
    
    if (schedule.description) {
      scheduleData.description = schedule.description;
    }
    if (schedule.location) {
      scheduleData.location = schedule.location;
    }
    if (schedule.priority) {
      scheduleData.priority = schedule.priority;
    }
    
    const result = await this.httpClient.post<Schedule>(
      ApiConstants.SCHEDULE.ADD,
      scheduleData
    );
    
    return result.data;
  }
  
  /**
   * 更新日程
   */
  async updateSchedule(scheduleId: string, updates: Partial<Schedule>): Promise<Schedule> {
    const result = await this.httpClient.put<Schedule>(
      `${ApiConstants.SCHEDULE.UPDATE}/${scheduleId}`,
      updates
    );
    
    return result.data;
  }
  
  /**
   * 删除日程
   */
  async deleteSchedule(scheduleId: string): Promise<void> {
    await this.httpClient.delete(
      `${ApiConstants.SCHEDULE.DELETE}/${scheduleId}`
    );
  }
  
  /**
   * 获取日程推荐
   */
  async getRecommendations(
    userId: string,
    date: string,
    preferences?: Record<string, Object>
  ): Promise<ScheduleRecommendation[]> {
    const result = await this.httpClient.post<ScheduleRecommendation[]>(
      ApiConstants.SCHEDULE.RECOMMEND,
      {
        user_id: userId,
        date,
        preferences: preferences || {}
      }
    );
    
    return result.data;
  }
  
  /**
   * 自动生成日程
   */
  async autoGenerateSchedule(
    userId: string,
    dateRange: { start: string; end: string },
    goals?: string[]
  ): Promise<Schedule[]> {
    const result = await this.httpClient.post<Schedule[]>(
      ApiConstants.SCHEDULE.AUTO_GENERATE,
      {
        user_id: userId,
        date_range: dateRange,
        goals: goals || []
      }
    );
    
    return result.data;
  }
  
  /**
   * 获取今天的日程
   */
  async getTodaySchedule(userId: string): Promise<Schedule[]> {
    const today = new Date().toISOString().split('T')[0];
    return this.getScheduleList(userId, today);
  }
  
  /**
   * 获取本周的日程
   */
  async getWeekSchedule(userId: string): Promise<Schedule[]> {
    const today = new Date();
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - today.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    
    const result = await this.httpClient.get<Schedule[]>(
      `${ApiConstants.SCHEDULE.LIST}/${userId}`,
      {
        start_date: startOfWeek.toISOString().split('T')[0],
        end_date: endOfWeek.toISOString().split('T')[0]
      }
    );
    
    return result.data;
  }
}
