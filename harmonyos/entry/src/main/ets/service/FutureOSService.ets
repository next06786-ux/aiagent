import { HttpUtil } from '../utils/HttpUtil'

interface FutureEnvelope<T> {
  success: boolean
  message?: string
  data: T
}

export interface FutureOSContextBrief {
  current_focus: string
  people_count: number
  signal_count: number
  key_people: string[]
  key_signals: string[]
}

export interface FutureOSRouteSuggestion {
  recommended_module: string
  recommended_view: string
  reason: string
  context_brief: FutureOSContextBrief
}

export interface FutureOSGraphNode {
  id: string
  name: string
  type: string
  category?: string
  view_role: string
  weight: number
  influence_score: number
  connections: number
  insight_tags: string[]
}

export interface FutureOSGraphLink {
  source: string
  target: string
  type: string
  strength: number
}

export interface FutureOSGraphSummary {
  bootstrap?: boolean
  user_id?: string
  node_count?: number
  link_count?: number
}

export interface FutureOSGraphView {
  view_mode: string
  title: string
  nodes: FutureOSGraphNode[]
  links: FutureOSGraphLink[]
  summary?: FutureOSGraphSummary
}

export interface FutureOSSimulationOption {
  option_id: string
  title: string
  description: string
  branch_strategy?: string
  branch_agent_id?: string
  key_people?: string[]
  timeline: Array<Record<string, Object | string | number | boolean>>
  final_score: number
  risk_level: number
  execution_confidence?: number
}

export interface FutureOSSimulation {
  simulation_id: string
  user_id: string
  question: string
  recommendation: string
  created_at: string
  options: FutureOSSimulationOption[]
  context_snapshot?: Object
}

export interface FutureOSScenario {
  scenario_id: string
  simulation_id: string
  branch_id: string
  source_question: string
  title: string
  subtitle: string
  theme: string
  accent: string
  cover_emoji: string
  intro: string
  nodes: Array<Record<string, Object | string | number | boolean>>
  endings: Array<Record<string, string>>
  branch_context?: Object
}

function ensureSuccess<T>(payload: FutureEnvelope<T>, fallbackMessage: string): T {
  if (!payload.success) {
    throw new Error(payload.message || fallbackMessage)
  }
  return payload.data
}

export class FutureOSService {
  private static instance: FutureOSService

  static getInstance(): FutureOSService {
    if (!FutureOSService.instance) {
      FutureOSService.instance = new FutureOSService()
    }
    return FutureOSService.instance
  }

  async getKnowledgeView(userId: string, viewMode: string, question?: string): Promise<FutureOSGraphView> {
    const response = await HttpUtil.get(`/api/v5/future-os/knowledge/${userId}`, {
      view: viewMode,
      question: question || ''
    })
    const result = HttpUtil.parseResponse<FutureEnvelope<FutureOSGraphView>>(response)
    return ensureSuccess(result, '知识星图加载失败')
  }

  async buildContext(userId: string, question: string): Promise<Object> {
    const response = await HttpUtil.post('/api/v5/future-os/context', {
      user_id: userId,
      question: question
    })
    const result = HttpUtil.parseResponse<FutureEnvelope<Object>>(response)
    return ensureSuccess(result, '上下文构建失败')
  }

  async routeMessage(userId: string, message: string): Promise<FutureOSRouteSuggestion> {
    const response = await HttpUtil.post('/api/v5/future-os/route', {
      user_id: userId,
      message: message
    })
    const result = HttpUtil.parseResponse<FutureEnvelope<FutureOSRouteSuggestion>>(response)
    return ensureSuccess(result, 'AI 核心路由失败')
  }

  async simulate(userId: string, question: string, options: string[] = []): Promise<FutureOSSimulation> {
    const response = await HttpUtil.post('/api/v5/future-os/simulate', {
      user_id: userId,
      question: question,
      options: options
    })
    const result = HttpUtil.parseResponse<FutureEnvelope<FutureOSSimulation>>(response)
    return ensureSuccess(result, '决策图谱推演失败')
  }

  async getSimulation(simulationId: string): Promise<FutureOSSimulation> {
    const response = await HttpUtil.get(`/api/v5/future-os/simulations/${simulationId}`)
    const result = HttpUtil.parseResponse<FutureEnvelope<FutureOSSimulation>>(response)
    return ensureSuccess(result, '推演详情加载失败')
  }

  async createParallelLifeBranch(userId: string, simulationId: string, branchId: string): Promise<FutureOSScenario> {
    const response = await HttpUtil.post('/api/v5/future-os/parallel-life/branch', {
      user_id: userId,
      simulation_id: simulationId,
      branch_id: branchId
    })
    const result = HttpUtil.parseResponse<FutureEnvelope<FutureOSScenario>>(response)
    return ensureSuccess(result, '平行人生分支创建失败')
  }

  async completeParallelLife(payload: Object): Promise<Object> {
    const response = await HttpUtil.post('/api/v5/future-os/parallel-life/complete', payload)
    const result = HttpUtil.parseResponse<FutureEnvelope<Object>>(response)
    return ensureSuccess(result, '平行人生结果回写失败')
  }
}

export function getFutureOSService(): FutureOSService {
  return FutureOSService.getInstance()
}
