/**
 * 决策系统数据模型
 */

// 时间线事件
export interface TimelineEvent {
  month: number
  event: string
  impact: Record<string, number>
  probability: number
}

// 风险维度
export interface RiskDimension {
  name: string
  score: number
  level: string
  factors: string[]
  mitigation: string[]
}

// 风险评估
export interface RiskAssessment {
  overall_risk: number
  overall_level: string
  high_risk_count: number
  dimensions: Record<string, RiskDimension>
  recommendations: string[]
}

// 决策选项
export interface DecisionOption {
  option_id: string
  title: string
  description: string
  final_score: number
  risk_level: number
  risk_assessment?: RiskAssessment
  timeline: TimelineEvent[]
}

// 模拟结果
export interface SimulationResult {
  simulation_id: string
  question: string
  options: DecisionOption[]
  recommendation: string
  created_at: string
}

// API响应
export interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
}
