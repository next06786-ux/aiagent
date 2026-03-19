/**
 * 
 */
export enum TaskStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED'
}

/**
 * 
 */
export enum TaskType {
  IMAGE_RECOGNITION = 'IMAGE_RECOGNITION',
  IMAGE_ENHANCEMENT = 'IMAGE_ENHANCEMENT',
  IMAGE_SEGMENTATION = 'IMAGE_SEGMENTATION',
  VIDEO_ANALYSIS = 'VIDEO_ANALYSIS',
  VIDEO_ENHANCEMENT = 'VIDEO_ENHANCEMENT',
  OBJECT_DETECTION = 'OBJECT_DETECTION',
  POSE_ESTIMATION = 'POSE_ESTIMATION',
  CUSTOM = 'CUSTOM'
}

/**
 * 
 */
export enum TaskPriority {
  LOW = 'LOW',
  NORMAL = 'NORMAL',
  HIGH = 'HIGH',
  URGENT = 'URGENT'
}

/**
 * 
 */
export class Task {
  id: string;
  type: string;
  status: TaskStatus;
  priority: TaskPriority;
  inputData: Record<string, Object>;
  outputData?: Record<string, Object>;
  createdAt: number;
  startedAt?: number;
  completedAt?: number;
  error?: string;
  metadata: Record<string, string>;

  constructor(
    id: string,
    type: string,
    status: TaskStatus = TaskStatus.PENDING,
    priority: TaskPriority = TaskPriority.NORMAL
  ) {
    this.id = id;
    this.type = type;
    this.status = status;
    this.priority = priority;
    this.inputData = {};
    this.createdAt = Date.now();
    this.metadata = {};
  }
}

/**
 * Agent
 */
export class AgentState {
  isRunning: boolean;
  currentTask?: Task;
  pendingTasks: Task[];
  completedTasks: Task[];
  totalTasks: number;
  successRate: number;

  constructor() {
    this.isRunning = false;
    this.pendingTasks = [];
    this.completedTasks = [];
    this.totalTasks = 0;
    this.successRate = 0;
  }
}
