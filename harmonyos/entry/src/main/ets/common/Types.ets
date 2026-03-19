/**
 * 服务类
 */

// 处理逻辑
export interface PredictionData {
  domain: string;
  domain_name: string;
  domain_icon: string;
  description: string;
  confidence: number;
  time_horizon: string;
}

// 处理逻辑
export interface EmergentPattern {
  type: string;
  type_name: string;
  description: string;
  confidence: number;
  impact_score?: number;
}

// 处理逻辑
export interface Suggestion {
  id: string;
  domain: string;
  domain_name: string;
  domain_icon: string;
  reason: string;
  benefit: string;
  confidence: number;
}

//  - Record
export class DomainIcons {
  health: string = '';
  time: string = '⏰';
  emotion: string = '';
  social: string = '';
  finance: string = '';
  learning: string = '';
}

//  - Record
export class DomainNames {
  health: string = '';
  time: string = '';
  emotion: string = '';
  social: string = '';
  finance: string = '';
  learning: string = '';
}

// HTTP
export interface HttpResponse {
  responseCode: number;
  result: string | Record<string, string> | ArrayBuffer;
}

// 处理逻辑
export interface HealthData {
  sleep_hours: number;
  exercise_minutes: number;
  stress_level: number;
}

// 处理逻辑
export interface TimeData {
  work_hours: number;
  task_count: number;
}

// 处理逻辑
export interface EmotionData {
  mood_score: number;
  anxiety_level: number;
}

// 处理逻辑
export interface SocialData {
  social_hours: number;
  friends_met: number;
}

// 处理逻辑
export interface FinanceData {
  spending: number;
  income: number;
}

// 处理逻辑
export interface LearningData {
  study_hours: number;
  courses_completed: number;
}

// data
export interface SubmitDataFields {
  health?: HealthData;
  time?: TimeData;
  emotion?: EmotionData;
  social?: SocialData;
  finance?: FinanceData;
  learning?: LearningData;
}

// 处理逻辑
export interface SubmitDataRequest {
  user_id: string;
  timestamp: string;
  data: SubmitDataFields;
}

// 处理逻辑
export interface LocationInfo {
  latitude: number;
  longitude: number;
  address?: string;
}

// 处理逻辑
export interface ContextInfo {
  location?: LocationInfo;
  time: string;
  weather?: string;
}

// API
export interface PredictionsResponse {
  predictions: PredictionData[];
  emergent_patterns: EmergentPattern[];
  suggestions: Suggestion[];
}

// API
export interface PredictionsRequest {
  user_id: string;
  enabled_domains: string[];
  time_horizon: string;
}

// 处理逻辑
export interface DomainStatus {
  score: string;
  scoreColor: string;
  statusText: string;
  statusColor: string;
  trend: string;
  trendColor: string;
}

// 处理逻辑
export class TimeHorizonMap {
  '1_day': string = '';
  '3_days': string = '3';
  '1_week': string = '';
  '1_month': string = '';
}

// 处理逻辑
export class PatternIconMap {
  'cascade': string = '';
  'feedback_loop': string = '';
  'tipping_point': string = '';
  'synergy': string = '';
}
