/**
 * 日程服务
 * 处理日程管理、推荐、自动生成
 */
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { Schedule, ScheduleInput, ScheduleRecommendation } from '../models/Schedule';
import {
  GetSchedulesParams,
  AddScheduleRequest,
  GetRecommendationsRequest,
  AutoGenerateRequest,
  EmptyObject
} from '../types/RequestInterfaces';

/**
 * 日期范围接口
 */
export interface DateRange {
  start: string;
  end: string;
}

export class ScheduleService {
  private httpClient = HttpClient.getInstance();
  
  /**
   * 获取日程列表
   */
  async getScheduleList(userId: string, date?: string): Promise<Schedule[]> {
    const paramsObj: Record<string, Object> = {};
    if (date) {
      paramsObj['date'] = date;
    }
    
    const result = await this.httpClient.get<Schedule[]>(
      `${ApiConstants.SCHEDULE.LIST}/${userId}`,
      paramsObj
    );
    
    return result.data;
  }
  
  /**
   * 获取日程（按时间范围）
   */
  async getSchedules(startTime: number, endTime: number): Promise<Schedule[]> {
    const paramsObj: Record<string, Object> = {};
    paramsObj['start_time'] = startTime.toString();
    paramsObj['end_time'] = endTime.toString();
    
    const result = await this.httpClient.get<Schedule[]>(
      ApiConstants.SCHEDULE.LIST,
      paramsObj
    );
    
    return result.data || [];
  }
  
  /**
   * 添加日程
   */
  async addSchedule(schedule: ScheduleInput): Promise<Schedule> {
    const scheduleData: AddScheduleRequest = {
      user_id: schedule.user_id,
      title: schedule.title,
      start_time: schedule.start_time,
      end_time: schedule.end_time,
      description: schedule.description || '',
      location: schedule.location || '',
      priority: schedule.priority || ''
    };
    
    const result = await this.httpClient.post<Schedule>(
      ApiConstants.SCHEDULE.ADD,
      scheduleData
    );
    
    return result.data;
  }
  
  /**
   * 更新日程
   */
  async updateSchedule(scheduleId: string, updates: Record<string, Object>): Promise<Schedule> {
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
    await this.httpClient.delete<Object>(
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
    const requestData: GetRecommendationsRequest = {
      user_id: userId,
      date: date,
      preferences: preferences || new EmptyObject()
    };
    
    const result = await this.httpClient.post<ScheduleRecommendation[]>(
      ApiConstants.SCHEDULE.RECOMMEND,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 自动生成日程
   */
  async autoGenerateSchedule(
    userId: string,
    dateRange: DateRange,
    goals?: string[]
  ): Promise<Schedule[]> {
    const requestData: AutoGenerateRequest = {
      user_id: userId,
      date_range: dateRange as Object,
      goals: goals || []
    };
    
    const result = await this.httpClient.post<Schedule[]>(
      ApiConstants.SCHEDULE.AUTO_GENERATE,
      requestData
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
    
    const paramsObj: Record<string, Object> = {};
    paramsObj['start_date'] = startOfWeek.toISOString().split('T')[0];
    paramsObj['end_date'] = endOfWeek.toISOString().split('T')[0];
    
    const result = await this.httpClient.get<Schedule[]>(
      `${ApiConstants.SCHEDULE.LIST}/${userId}`,
      paramsObj
    );
    
    return result.data;
  }
}
