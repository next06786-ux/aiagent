/**
 * LoRA系统数据模型
 */

// LoRA状态
export interface LoRAStatus {
  has_lora: boolean
  model_version: number
  is_loaded: boolean
  last_train_time?: string
  training_data_size: number
}

// 调度器状态
export interface SchedulerStatus {
  is_running: boolean
  active_users: number
  training_queue: number
  next_profile_update: string
  next_lora_training: string
}

// 训练任务
export interface TrainingTask {
  user_id: string
  priority: string
  added_time: string
}
