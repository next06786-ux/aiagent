/**
 * Agent智慧洞察服务
 * 三个专业Agent：人际关系、教育升学、职业规划
 * 跨领域综合分析：多Agent协作
 */
import { API_BASE_URL } from './api'

export interface AgentInsightReport {
  insight_id: string
  agent_type: string
  title: string
  summary: string
  key_findings: Array<{
    type: string
    title: string
    description: string
    importance: string
  }>
  ml_evaluation?: {
    risk_level: string
    trend: string
    match_score: number
    model_version: string
  }
  recommendations: Array<{
    priority: string
    category: string
    action: string
    expected_impact: string
    timeline: string
    reasoning?: string
  }>
  decision_logic: {
    reasoning_path: Array<{
      step: number
      description: string
    }>
    influence_factors: Record<string, number>
    data_quality: Record<string, number>
  }
  data_sources: Record<string, any>
  confidence_score: number
  generated_at: string
  layer_timing?: {
    layer1_ms: number
    layer2_ms: number
    layer3_ms: number
  }
}

export interface CrossDomainPattern {
  pattern_type: string
  title: string
  description: string
  domains: string[]
  strength: string
}

export interface Synergy {
  synergy_type: string
  title: string
  description: string
  involved_domains: string[]
  potential_benefit: string
}

export interface Conflict {
  conflict_type: string
  title: string
  description: string
  involved_domains: string[]
  severity: string
  resolution_suggestion: string
}

export interface CrossDomainAnalysisResult {
  query: string
  analysis_type: string
  domain_results: {
    relationship?: any
    education?: any
    career?: any
  }
  cross_domain_analysis: {
    summary: string
    cross_domain_patterns: CrossDomainPattern[]
    synergies: Synergy[]
    conflicts: Conflict[]
    strategic_recommendations: Array<{
      priority: string
      category: string
      action: string
      expected_impact: string
      timeline: string
      involved_domains: string[]
    }>
    integrated_insights: Array<{
      title: string
      description: string
      domains: string[]
      importance: string
    }>
    action_plan: {
      short_term: string[]
      medium_term: string[]
      long_term: string[]
    }
  }
  execution_summary: {
    total_agents: number
    execution_time: number
    shared_context_size: number
  }
  timestamp: string
}

/**
 * 生成人际关系洞察报告
 */
export async function generateRelationshipInsight(
  token: string,
  query?: string,
  focusArea?: string
): Promise<AgentInsightReport> {
  const response = await fetch(`${API_BASE_URL}/api/insights/realtime/relationship/insight`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      query: query || '分析我的人际关系网络',
      focus_area: focusArea
    })
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`人际关系洞察生成失败 (${response.status}): ${errorText}`)
  }

  const data = await response.json()
  return data.report
}

/**
 * 生成教育升学洞察报告
 */
export async function generateEducationInsight(
  token: string,
  query?: string,
  targetSchool?: string,
  targetMajor?: string
): Promise<AgentInsightReport> {
  const response = await fetch(`${API_BASE_URL}/api/insights/realtime/education/insight`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      query: query || '分析我的升学路径',
      target_school: targetSchool,
      target_major: targetMajor
    })
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`教育升学洞察生成失败 (${response.status}): ${errorText}`)
  }

  const data = await response.json()
  return data.report
}

/**
 * 生成职业规划洞察报告
 */
export async function generateCareerInsight(
  token: string,
  query?: string,
  targetPosition?: string,
  targetIndustry?: string
): Promise<AgentInsightReport> {
  const response = await fetch(`${API_BASE_URL}/api/insights/realtime/career/insight`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      query: query || '分析我的职业发展路径',
      target_position: targetPosition,
      target_industry: targetIndustry
    })
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`职业规划洞察生成失败 (${response.status}): ${errorText}`)
  }

  const data = await response.json()
  return data.report
}

/**
 * 获取所有Agent状态
 */
export async function getAgentsStatus(token: string) {
  const response = await fetch(`${API_BASE_URL}/api/insights/realtime/agents/status`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })

  if (!response.ok) {
    throw new Error('获取Agent状态失败')
  }

  return response.json()
}

/**
 * 跨领域综合分析 - 多Agent协作
 * 
 * 功能：
 * 1. 整合三个领域Agent的输出
 * 2. 发现跨领域的关联和模式
 * 3. 生成综合性的战略建议
 * 4. 识别领域间的协同效应和冲突
 */
export async function generateCrossDomainAnalysis(
  token: string,
  query: string,
  agentChain?: string[],
  initialContext?: Record<string, any>
): Promise<CrossDomainAnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/insights/realtime/cross-domain/comprehensive-analysis`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      query,
      agent_chain: agentChain || ['relationship', 'education', 'career', 'cross_domain'],
      initial_context: initialContext
    })
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`跨领域综合分析失败 (${response.status}): ${errorText}`)
  }

  const data = await response.json()
  return data
}

/**
 * 多Agent协作洞察（通用接口）
 */
export async function generateMultiAgentInsight(
  token: string,
  query: string,
  agentChain: string[],
  initialContext?: Record<string, any>
) {
  const response = await fetch(`${API_BASE_URL}/api/insights/realtime/multi-agent/insight`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      query,
      agent_chain: agentChain,
      initial_context: initialContext
    })
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`多Agent协作失败 (${response.status}): ${errorText}`)
  }

  return response.json()
}
