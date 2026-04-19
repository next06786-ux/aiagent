/**
 * 智能日程推荐服务
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:6006';

export interface Task {
  task_id: string;
  title: string;
  task_type: 'work' | 'study' | 'exercise' | 'social' | 'rest';
  duration_minutes: number;
  priority: 'high' | 'medium' | 'low';
  deadline?: string;
  flexibility?: number;
  energy_required?: number;
  focus_required?: number;
}

export interface TimeSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
}

export interface TaskRecommendation {
  task: {
    task_id: string;
    title: string;
    type: string;
  };
  recommended_slot: TimeSlot;
  score: number;
  reason: string;
  alternatives: Array<{
    slot: TimeSlot;
    score: number;
    reason: string;
  }>;
}

export interface DailySchedule {
  date: string;
  schedule: Array<{
    task: Task;
    time_slot: TimeSlot;
    reason: string;
  }>;
  timeline: Array<{
    start: string;
    end: string;
    title: string;
    type: string;
    priority: string;
    duration: number;
  }>;
  summary: {
    total_tasks: number;
    total_work_minutes: number;
    total_break_minutes: number;
    work_break_ratio: number;
  };
  optimization_tips: string[];
}

export interface ProductivityPattern {
  hour: number;
  productivity: number;
  focus: number;
  energy: number;
  activities: string[];
}

export interface UserPatterns {
  productivity_curve: ProductivityPattern[];
  peak_hours: TimeSlot[];
  low_hours: TimeSlot[];
  typical_schedule: {
    wake_time: string;
    sleep_time: string;
    work_start: string;
    work_end: string;
    lunch_time: string;
    dinner_time: string;
    exercise_time: string;
    learning_time: string;
  };
  habits: {
    morning_person: boolean;
    night_owl: boolean;
    exercise_frequency: string;
    learning_frequency: string;
    social_frequency: string;
    preferred_work_duration: number;
    preferred_break_duration: number;
  };
}

class ScheduleService {
  protected baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v5/schedule`;
  }

  /**
   * 推荐单个任务的最佳时间
   */
  async recommendOptimalTime(
    userId: string,
    task: Task,
    date?: string,
    numAlternatives: number = 3
  ): Promise<TaskRecommendation> {
    const response = await fetch(`${API_BASE_URL}/api/v5/schedule/recommend-time`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        task,
        date,
        num_alternatives: numAlternatives,
      }),
    });

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '推荐失败');
    }

    return result.data;
  }

  /**
   * 生成每日完整日程
   */
  async recommendDailySchedule(
    userId: string,
    tasks: Task[],
    date?: string
  ): Promise<DailySchedule> {
    const response = await fetch(`${API_BASE_URL}/api/v5/schedule/recommend-daily`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        tasks,
        date,
      }),
    });

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '生成日程失败');
    }

    return result.data;
  }

  /**
   * 生成每周日程
   */
  async recommendWeeklySchedule(
    userId: string,
    tasks: Task[],
    startDate?: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v5/schedule/recommend-weekly`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        tasks,
        start_date: startDate,
      }),
    });

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '生成周日程失败');
    }

    return result.data;
  }

  /**
   * 获取用户时间使用模式
   */
  async getUserPatterns(userId: string): Promise<UserPatterns> {
    const response = await fetch(`${API_BASE_URL}/api/v5/schedule/patterns/${userId}`);
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '获取模式失败');
    }

    return result.data;
  }

  /**
   * 时间决策 - 智能决策系统
   * 
   * 将日程安排视为决策问题，生成多个方案并推荐最佳选择
   */
  async makeTimeDecision(request: TimeDecisionRequest): Promise<TimeDecisionResult> {
    const response = await fetch(`${API_BASE_URL}/api/v5/schedule/time-decision`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '时间决策失败');
    }

    return result.data;
  }

  /**
   * 获取决策历史
   */
  async getDecisionHistory(userId: string, limit: number = 10): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/v5/schedule/decision-history/${userId}?limit=${limit}`
    );
    
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '获取决策历史失败');
    }

    return result.data;
  }
}

// ==================== 时间决策API类型定义 ====================

export interface TimeDecisionRequest {
  user_id: string;
  tasks: Task[];
  date?: string;
  available_hours?: number;
  current_energy?: number;
  current_stress?: number;
  goals?: Array<{ [key: string]: any }>;
}

export interface TimeDecisionOption {
  option_id: string;
  description: string;
  expected_completion_rate: number;
  expected_efficiency: number;
  expected_stress: number;
  expected_satisfaction?: number;
  risk_level: number;
  schedule?: any[];
}

export interface TimeDecisionResult {
  decision_id: string;
  timestamp: string;
  context: {
    available_hours: number;
    energy_level: number;
    stress_level: number;
    task_count: number;
  };
  recommended_option: TimeDecisionOption;
  alternative_options: TimeDecisionOption[];
  reasoning: string;
  trade_offs: {
    [key: string]: any;
  };
  confidence: number;
}

export const scheduleService = new ScheduleService();


// ==================== 异步任务系统 ====================

export interface TaskStatus {
  task_id: string;
  user_id: string;
  task_type: 'schedule_generation' | 'time_decision';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'no_data';
  progress: number;  // 0-100
  progress_message: string;
  result: any;
  error: string | null;
  message?: string;  // 用于no_data状态的消息
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

class ScheduleServiceExtended extends ScheduleService {
  /**
   * 创建异步日程生成任务
   */
  async createScheduleTask(
    userId: string,
    description?: string,
    tasks?: Task[]
  ): Promise<{ task_id: string; status: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/async/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        description,
        tasks: tasks?.map(t => ({
          task_id: t.task_id,
          title: t.title,
          task_type: t.task_type,
          duration_minutes: t.duration_minutes,
          priority: t.priority,
          flexibility: t.flexibility
        }))
      })
    });

    if (!response.ok) {
      throw new Error('创建日程任务失败');
    }

    return response.json();
  }

  /**
   * 创建异步时间决策任务
   */
  async createDecisionTask(
    userId: string,
    tasks: Task[],
    availableHours: number,
    energyLevel: number,
    stressLevel: number
  ): Promise<{ task_id: string; status: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/async/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        tasks: tasks.map(t => ({
          task_id: t.task_id,
          title: t.title,
          task_type: t.task_type,
          duration_minutes: t.duration_minutes,
          priority: t.priority,
          flexibility: t.flexibility
        })),
        available_hours: availableHours,
        energy_level: energyLevel,
        stress_level: stressLevel
      })
    });

    if (!response.ok) {
      throw new Error('创建决策任务失败');
    }

    return response.json();
  }

  /**
   * 查询任务状态
   */
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const response = await fetch(`${this.baseUrl}/task/${taskId}`);
    
    if (!response.ok) {
      throw new Error('查询任务状态失败');
    }

    return response.json();
  }

  /**
   * 获取用户最新的日程
   */
  async getLatestSchedule(userId: string): Promise<TaskStatus> {
    const response = await fetch(`${this.baseUrl}/user/${userId}/latest-schedule`);
    
    if (!response.ok) {
      throw new Error('获取最新日程失败');
    }

    return response.json();
  }

  /**
   * 获取用户最新的决策
   */
  async getLatestDecision(userId: string): Promise<TaskStatus> {
    const response = await fetch(`${this.baseUrl}/user/${userId}/latest-decision`);
    
    if (!response.ok) {
      throw new Error('获取最新决策失败');
    }

    return response.json();
  }

  /**
   * 轮询任务直到完成
   */
  async pollTaskUntilComplete(
    taskId: string,
    onProgress?: (status: TaskStatus) => void,
    maxAttempts: number = 60,
    interval: number = 2000
  ): Promise<TaskStatus> {
    for (let i = 0; i < maxAttempts; i++) {
      const status = await this.getTaskStatus(taskId);
      
      if (onProgress) {
        onProgress(status);
      }

      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }

      await new Promise(resolve => setTimeout(resolve, interval));
    }

    throw new Error('任务超时');
  }
}

export const scheduleServiceExtended = new ScheduleServiceExtended();
