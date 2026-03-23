import { Task, TaskStatus, AgentState } from '../model/Task';
import http from '@ohos.net.http';

interface AgentStateResponse {
  is_running: boolean
  completed_tasks: number
}

interface TaskSubmitRequest {
  task_type: string
  input_data: ESObject
  priority: number
  metadata: ESObject
}

interface TaskResponse {
  task_id: string
  task_type: string
  status: string
}

/**
 * Agent - 
 */
export class AgentService {
  private baseUrl: string = 'http://192.168.43.6:8000';
  
  /**
   * Agent
   */
  async getAgentState(): Promise<AgentState> {
    try {
      const response = await this.request('/api/v4/meta-agent/analyze', http.RequestMethod.GET);
      const data = JSON.parse(response.result as string) as AgentStateResponse;
      
      const state = new AgentState();
      state.isRunning = data.is_running;
      state.totalTasks = data.completed_tasks;
      state.successRate = 0.95; // TODO: 
      
      return state;
    } catch (error) {
      console.error('Get agent state failed:', JSON.stringify(error));
      return new AgentState();
    }
  }

  /**
   * Agent
   */
  async startAgent(): Promise<boolean> {
    try {
      await this.request('/api/v4/meta-agent/analyze', http.RequestMethod.POST);
      return true;
    } catch (error) {
      console.error('Start agent failed:', JSON.stringify(error));
      return false;
    }
  }

  /**
   * Agent
   */
  async stopAgent(): Promise<boolean> {
    try {
      await this.request('/api/v4/meta-agent/feedback', http.RequestMethod.POST);
      return true;
    } catch (error) {
      console.error('Stop agent failed:', JSON.stringify(error));
      return false;
    }
  }

  /**
 * 服务类
 */
  async submitTask(task: Task): Promise<string> {
    try {
      const taskData: TaskSubmitRequest = {
        task_type: task.type,
        input_data: task.inputData,
        priority: Number(task.priority),
        metadata: task.metadata
      };
      
      const response = await this.request('/api/v4/conversations/' + task.type + '/list', http.RequestMethod.POST, taskData);
      
      const data = JSON.parse(response.result as string) as TaskResponse;
      return data.task_id;
    } catch (error) {
      const err = error as Error;
      console.error('Submit task failed:', err.message);
      throw err;
    }
  }

  /**
 * 服务类
 */
  async getTaskStatus(taskId: string): Promise<Task | null> {
    try {
      const response = await this.request(`/api/v4/conversations/${taskId}/list`, http.RequestMethod.GET);
      const data = JSON.parse(response.result as string) as TaskResponse;
      
      const task = new Task(data.task_id, data.task_type);
      task.status = data.status as TaskStatus;
      // TODO: 
      
      return task;
    } catch (error) {
      console.error('Get task status failed:', JSON.stringify(error));
      return null;
    }
  }

  /**
 * 服务类
 */
  async getAllTasks(): Promise<Task[]> {
    try {
      // TODO: API
      // 处理逻辑
      return [
        new Task('task_1', 'IMAGE_RECOGNITION', TaskStatus.COMPLETED),
        new Task('task_2', 'VIDEO_ANALYSIS', TaskStatus.RUNNING),
        new Task('task_3', 'IMAGE_ENHANCEMENT', TaskStatus.PENDING)
      ];
    } catch (error) {
      console.error('Get all tasks failed:', JSON.stringify(error));
      return [];
    }
  }

  /**
 * 服务类
 */
  async cancelTask(taskId: string): Promise<boolean> {
    try {
      await this.request(`/api/decision/feedback`, http.RequestMethod.POST);
      return true;
    } catch (error) {
      console.error('Cancel task failed:', JSON.stringify(error));
      return false;
    }
  }

  /**
   * HTTP
   */
  private async request(
    path: string,
    method: http.RequestMethod,
    data?: ESObject
  ): Promise<http.HttpResponse> {
    return new Promise((resolve, reject) => {
      const httpRequest = http.createHttp();
      
      httpRequest.request(
        `${this.baseUrl}${path}`,
        {
          method: method,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: data ? JSON.stringify(data) : undefined,
          expectDataType: http.HttpDataType.STRING,
          connectTimeout: 60000,
          readTimeout: 60000
        },
        (err, data) => {
          if (!err) {
            resolve(data);
          } else {
            reject(err);
          }
          httpRequest.destroy();
        }
      );
    });
  }
}
