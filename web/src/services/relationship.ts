import type { SuccessEnvelope } from '../types/api';
import { ApiError, postJson, requestJson } from './api';

function asObject(value: unknown) {
  return typeof value === 'object' && value !== null
    ? (value as Record<string, unknown>)
    : null;
}

function asString(value: unknown, fallback = '') {
  return typeof value === 'string'
    ? value
    : typeof value === 'number'
      ? String(value)
      : fallback;
}

function asNumber(value: unknown) {
  const next = Number(value);
  return Number.isFinite(next) ? next : undefined;
}

function asStringArray(value: unknown) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => asString(item).trim()).filter(Boolean);
}

function assertSuccess<T>(response: SuccessEnvelope<T>, fallbackMessage: string) {
  if (!response.success) {
    throw new ApiError(response.message || fallbackMessage, 500, response);
  }
  return response.data;
}

// ==================== 类型定义 ====================

export interface PersonInput {
  id: string;
  name: string;
  type: 'family' | 'friend' | 'colleague' | 'partner' | 'mentor';
  closeness: number;
  trust_level: number;
  support_level: number;
  influence_weight: number;
  emotional_bond: number;
  key_concerns: string[];
  shared_experiences: string[];
  communication_frequency: number;
  last_interaction_days?: number;
}

export interface RelationshipInfluenceScore {
  total_influence: number;
  trust_amplifier: number;
  intimacy_factor: number;
  emotional_factor: number;
  time_factor: number;
  frequency_factor: number;
}

export interface RelationshipPerson {
  person_id: string;
  person_name: string;
  relationship_type: string;
  influence_score: RelationshipInfluenceScore;
  influence_weight: number;
}

export interface ConflictAnalysis {
  conflict_type: string;
  base_severity: number;
  affected_people: number;
  duration_months: number;
  total_impact: number;
  recovery_difficulty: number;
  recovery_time_estimate: number;
}

export interface KeyConflict {
  person_id: string;
  person_name: string;
  relationship_type: string;
  severity: number;
  concerns: string[];
}

export interface CommunicationStrategy {
  person_name: string;
  relationship_type: string;
  channel: string;
  channel_confidence: number;
  timing: {
    duration: string;
    best_moment: string;
    time_score: number;
  };
  tone: string;
  strategy: {
    approach: string;
    steps?: string[];
    activities?: string[];
    principles?: string[];
    avoid?: string[];
  };
  key_points: string[];
  expected_outcome: string;
  backup_plan: {
    if_refused: string;
    if_hostile: string;
    if_unresponsive: string;
    emergency: string;
  };
}

export interface EmotionalAccountBalance {
  person_id: string;
  person_name: string;
  relationship_type: string;
  account_analysis: {
    current_balance: number;
    total_deposits: number;
    total_withdrawals: number;
    status: 'healthy' | 'normal' | 'warning' | 'critical';
    health_text: string;
    deposits_needed_for_health: number;
    recommendation: string;
  };
}

export interface AgentState {
  month: number;
  score: number;
  status: string;
  key_metrics: Record<string, unknown>;
  changes: string[];
  risks: string[];
  opportunities: string[];
}

export interface RelationshipDecisionResult {
  decision_topic: string;
  influence_analysis: Record<string, {
    total_influence: number;
    person_name: string;
    relationship_type: string;
  }>;
  total_influence: number;
  support_opposition_ratio: {
    support: number;
    oppose: number;
    net: number;
  };
  conflict_analysis: ConflictAnalysis;
  relationship_evolution: {
    final_avg_closeness: number;
    final_avg_trust: number;
    final_avg_emotional: number;
    relationship_trend: string;
    critical_relationships: string[];
  };
  communication_strategies: Record<string, CommunicationStrategy>;
  recommendation: {
    action: string;
    text: string;
    risk_level: string;
    next_steps: string[];
  };
}

export interface RelationshipSimulationResult {
  timeline: Array<{
    month: number;
    agents_state: Record<string, AgentState>;
    interactions: Array<{
      month: number;
      agents: string[];
      type: string;
      description: string;
      impact: string;
    }>;
    decision_points: Array<{
      month: number;
      trigger: string;
      description: string;
      options: string[];
      recommendation: string;
      votes: Record<string, string>;
    }>;
    overall_assessment: {
      overall_score: number;
      overall_status: string;
      status_text: string;
      weakest_dimension: {
        name: string;
        score: number;
        status: string;
      };
      strongest_dimension: {
        name: string;
        score: number;
        status: string;
      };
      total_risks: number;
      total_opportunities: number;
      key_risks: string[];
      key_opportunities: string[];
    };
  }>;
  summary: {
    overall_trend: string;
    score_change: number;
    final_score: number;
    agent_trends: Record<string, {
      trend: string;
      change: number;
      final_score: number;
    }>;
    total_interactions: number;
    total_decision_points: number;
    key_milestones: Array<{
      month: number;
      description: string;
      recommendation: string;
    }>;
    success_probability: number;
  };
  total_interactions: number;
  total_decision_points: number;
}

export interface RelationshipSummary {
  user_id: string;
  total_relationships: number;
  by_type: Record<string, number>;
  average_closeness: number;
  average_trust: number;
  key_relationships: Array<{
    id: string;
    name: string;
    type: string;
  }>;
  relationship_health_score: number;
  recommendations: string[];
}

// ==================== API 函数 ====================

export async function getRelationshipPeople(userId: string): Promise<{
  people: PersonInput[];
  summary: {
    total_count: number;
    by_type: Record<string, number>;
  };
}> {
  const response = await requestJson<SuccessEnvelope<{
    people: PersonInput[];
    summary: { total_count: number; by_type: Record<string, number> };
  }>>(`/api/v5/relationship/people/${encodeURIComponent(userId)}`);
  return assertSuccess(response, '获取人物关系失败');
}

export async function analyzeRelationshipDecision(payload: {
  user_id: string;
  topic: string;
  people: PersonInput[];
  involved_people: string[];
  current_conflicts?: string[];
  stakeholder_positions?: Record<string, number>;
  time_urgency?: number;
  relationship_health?: number;
}): Promise<RelationshipDecisionResult> {
  const response = await postJson<SuccessEnvelope<RelationshipDecisionResult>>(
    '/api/v5/relationship/analyze',
    payload,
  );
  return assertSuccess(response, '分析人际关系决策失败');
}

export async function generateCommunicationStrategy(payload: {
  user_id: string;
  person: PersonInput;
  goal: 'resolve_conflict' | 'strengthen_bond' | 'seek_support' | 'general';
}): Promise<CommunicationStrategy> {
  const response = await postJson<SuccessEnvelope<CommunicationStrategy>>(
    '/api/v5/relationship/strategy',
    payload,
  );
  return assertSuccess(response, '生成沟通策略失败');
}

export async function simulateRelationshipEvolution(payload: {
  user_id: string;
  people: PersonInput[];
  decision_topic: string;
  involved_people?: string[];
  current_conflicts?: string[];
  stakeholder_positions?: Record<string, number>;
  time_urgency?: number;
  months?: number;
}): Promise<RelationshipSimulationResult> {
  const response = await postJson<SuccessEnvelope<RelationshipSimulationResult>>(
    '/api/v5/relationship/simulate',
    payload,
  );
  return assertSuccess(response, '模拟关系演变失败');
}

export async function calculateInfluence(payload: {
  user_id: string;
  topic: string;
  people: PersonInput[];
  involved_people: string[];
  current_conflicts?: string[];
  stakeholder_positions?: Record<string, number>;
  time_urgency?: number;
  relationship_health?: number;
}): Promise<{
  influences: RelationshipPerson[];
  total_influence: number;
  key_supporters: RelationshipPerson[];
  key_opponents: RelationshipPerson[];
}> {
  const response = await postJson<SuccessEnvelope<{
    influences: RelationshipPerson[];
    total_influence: number;
    key_supporters: RelationshipPerson[];
    key_opponents: RelationshipPerson[];
  }>>('/api/v5/relationship/influence', payload);
  return assertSuccess(response, '计算影响力失败');
}

export async function analyzeConflicts(payload: {
  user_id: string;
  topic: string;
  people: PersonInput[];
  involved_people: string[];
  current_conflicts?: string[];
  stakeholder_positions?: Record<string, number>;
  time_urgency?: number;
  relationship_health?: number;
}): Promise<{
  conflict_analysis: ConflictAnalysis[];
  key_conflicts: KeyConflict[];
  total_affected: number;
  highest_priority: KeyConflict | null;
}> {
  const response = await postJson<SuccessEnvelope<{
    conflict_analysis: ConflictAnalysis[];
    key_conflicts: KeyConflict[];
    total_affected: number;
    highest_priority: KeyConflict | null;
  }>>('/api/v5/relationship/conflict', payload);
  return assertSuccess(response, '分析冲突失败');
}

export async function analyzeEmotionalAccounts(payload: {
  user_id: string;
  topic: string;
  people: PersonInput[];
  involved_people: string[];
  current_conflicts?: string[];
  stakeholder_positions?: Record<string, number>;
  time_urgency?: number;
  relationship_health?: number;
}): Promise<{
  accounts: EmotionalAccountBalance[];
  status_distribution: Record<string, number>;
  overall_health: number;
}> {
  const response = await postJson<SuccessEnvelope<{
    accounts: EmotionalAccountBalance[];
    status_distribution: Record<string, number>;
    overall_health: number;
  }>>('/api/v5/relationship/emotional-account', payload);
  return assertSuccess(response, '分析情感账户失败');
}

export async function updateRelationship(payload: {
  user_id: string;
  person_id: string;
  updates: Record<string, unknown>;
}): Promise<{
  person_id: string;
  updates_applied: Record<string, unknown>;
  message: string;
}> {
  const response = await postJson<SuccessEnvelope<{
    person_id: string;
    updates_applied: Record<string, unknown>;
    message: string;
  }>>('/api/v5/relationship/update', payload);
  return assertSuccess(response, '更新关系失败');
}

export async function getRelationshipSummary(userId: string): Promise<RelationshipSummary> {
  const response = await requestJson<SuccessEnvelope<RelationshipSummary>>(
    `/api/v5/relationship/summary/${encodeURIComponent(userId)}`,
  );
  return assertSuccess(response, '获取关系总览失败');
}