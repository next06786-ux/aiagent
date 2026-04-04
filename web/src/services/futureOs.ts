import type {
  DecisionGraph,
  DecisionOption,
  DecisionRecordPayload,
  DecisionHistoryRecord,
  FutureOsContext,
  FutureOsRouteSuggestion,
  KnowledgeGraphView,
  ParallelLifeCompletionResult,
  ParallelLifeScenario,
  SuccessEnvelope,
  TimelineEvent,
} from '../types/api';
import { ApiError, postJson, requestJson } from './api';
import {
  buildDecisionGraphEdges,
  buildDecisionGraphSummary,
  normalizeDecisionGraphNode,
} from '../utils/decisionGraph';

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

function normalizeGraphNode(value: unknown) {
  const payload = asObject(value) || {};
  return {
    id: asString(payload.id),
    name: asString(payload.name) || '未命名节点',
    type: asString(payload.type) || 'Information',
    category: asString(payload.category) || undefined,
    view_role: asString(payload.view_role) === 'person' ? 'person' : 'signal',
    weight: asNumber(payload.weight) || 0,
    influence_score: asNumber(payload.influence_score) || 0,
    connections: asNumber(payload.connections) || 0,
    insight_tags: asStringArray(payload.insight_tags),
  } as KnowledgeGraphView['nodes'][number];
}

function normalizeGraphView(value: unknown): KnowledgeGraphView {
  const source = asObject(value) || {};
  const nodes = Array.isArray(source.nodes)
    ? source.nodes.map((item) => normalizeGraphNode(item))
    : [];

  const links = Array.isArray(source.links)
    ? source.links.map((item) => {
        const payload = asObject(item) || {};
        return {
          source: asString(payload.source),
          target: asString(payload.target),
          type: asString(payload.type) || 'RELATED',
          strength: asNumber(payload.strength) || 0,
          description: asString(payload.description) || undefined,
        };
      })
    : [];

  const summarySource = asObject(source.summary) || {};

  return {
    view_mode: ['people', 'signals', 'career'].includes(asString(source.view_mode)) 
      ? asString(source.view_mode) as 'people' | 'signals' | 'career'
      : 'people',
    title: asString(source.title) || '知识星图',
    nodes,
    links,
    summary: {
      user_id: asString(summarySource.user_id),
      view_mode: ['people', 'signals', 'career'].includes(asString(summarySource.view_mode))
        ? asString(summarySource.view_mode) as 'people' | 'signals' | 'career'
        : 'people',
      node_count: asNumber(summarySource.node_count) || nodes.length,
      link_count: asNumber(summarySource.link_count) || links.length,
      top_nodes: asStringArray(summarySource.top_nodes),
    },
  };
}

function normalizeDecisionGraph(value: unknown, option: DecisionOption): DecisionGraph {
  const source = asObject(value) || {};
  const nodes = Array.isArray(source.nodes)
    ? source.nodes.map((item, index) =>
        normalizeDecisionGraphNode(
          (asObject(item) || {}) as unknown as Partial<TimelineEvent>,
          index,
        ),
      )
    : option.timeline.map((item, index) => normalizeDecisionGraphNode(item, index));
  const edges = Array.isArray(source.edges)
    ? source.edges.reduce<DecisionGraph['edges']>((result, item, index) => {
        const payload = asObject(item);
        if (!payload) {
          return result;
        }

        const sourceId = asString(payload.source);
        const targetId = asString(payload.target);
        if (!sourceId || !targetId) {
          return result;
        }

        result.push({
          edge_id: asString(payload.edge_id) || `edge_${index + 1}`,
          source: sourceId,
          target: targetId,
          relation: asString(payload.relation) || 'next',
          strength: asNumber(payload.strength) || 0,
          label: asString(payload.label) || undefined,
        });
        return result;
      }, [])
    : buildDecisionGraphEdges(nodes);

  return {
    graph_id: asString(source.graph_id) || `${option.option_id}_graph`,
    schema_version: asNumber(source.schema_version) || 1,
    layout_hint: asString(source.layout_hint) || 'future-state-stage',
    graph_summary: asObject(source.graph_summary)
      ? {
          title: asString(asObject(source.graph_summary)?.title) || option.title,
          node_count:
            asNumber(asObject(source.graph_summary)?.node_count) || nodes.length,
          edge_count:
            asNumber(asObject(source.graph_summary)?.edge_count) || edges.length,
          high_risk_nodes:
            asNumber(asObject(source.graph_summary)?.high_risk_nodes) || 0,
          dominant_axes: asStringArray(
            asObject(source.graph_summary)?.dominant_axes,
          ),
          agent_stance_mix: Object.entries(
            asObject(asObject(source.graph_summary)?.agent_stance_mix) || {},
          ).reduce<Record<string, number>>((result, [key, item]) => {
            const next = asNumber(item);
            if (key && next !== undefined) {
              result[key] = next;
            }
            return result;
          }, {}),
          review_mode:
            asString(asObject(source.graph_summary)?.review_mode) || undefined,
        }
      : buildDecisionGraphSummary(nodes, edges, option.title),
    nodes,
    edges,
  };
}

function normalizeDecisionOption(value: unknown, index: number): DecisionOption {
  const source = asObject(value) || {};
  const timeline = Array.isArray(source.timeline)
    ? source.timeline.map((item, itemIndex) =>
        normalizeDecisionGraphNode(
          (asObject(item) || {}) as unknown as Partial<TimelineEvent>,
          itemIndex,
        ),
      )
    : [];

  const option: DecisionOption = {
    option_id: asString(source.option_id) || `option_${index + 1}`,
    title: asString(source.title) || `分支 ${index + 1}`,
    description: asString(source.description),
    branch_strategy: asString(source.branch_strategy) || undefined,
    branch_agent_id: asString(source.branch_agent_id) || undefined,
    key_people: asStringArray(source.key_people),
    timeline,
    final_score: asNumber(source.final_score) || 0,
    risk_level: asNumber(source.risk_level) || 0,
    decision_graph: null,
    risk_assessment: null,
    prediction_trace: null,
    execution_confidence: asNumber(source.execution_confidence),
    dropout_risk_month: asNumber(source.dropout_risk_month) ?? null,
    personal_note: asString(source.personal_note),
  };

  option.decision_graph = normalizeDecisionGraph(source.decision_graph, option);
  return option;
}

function normalizeContext(value: unknown): FutureOsContext {
  const source = asObject(value) || {};
  const profileSource = asObject(source.profile) || {};
  const briefSource = asObject(source.brief) || {};

  return {
    question: asString(source.question),
    recommended_view: ['people', 'signals', 'career'].includes(asString(source.recommended_view))
      ? asString(source.recommended_view) as 'people' | 'signals' | 'career'
      : 'people',
    profile: {
      risk_tolerance: asNumber(profileSource.risk_tolerance) || 0,
      delay_discount: asNumber(profileSource.delay_discount) || 0,
      social_dependency: asNumber(profileSource.social_dependency) || 0,
      execution_stability: asNumber(profileSource.execution_stability) || 0,
      growth_bias: asNumber(profileSource.growth_bias) || 0,
      loss_aversion: asNumber(profileSource.loss_aversion) || 0,
      ambiguity_tolerance: asNumber(profileSource.ambiguity_tolerance) || 0,
    },
    top_people: Array.isArray(source.top_people)
      ? source.top_people.map((item) => normalizeGraphNode(item))
      : [],
    top_signals: Array.isArray(source.top_signals)
      ? source.top_signals.map((item) => normalizeGraphNode(item))
      : [],
    brief: {
      current_focus: asString(briefSource.current_focus),
      people_count: asNumber(briefSource.people_count) || 0,
      signal_count: asNumber(briefSource.signal_count) || 0,
      key_people: asStringArray(briefSource.key_people),
      key_signals: asStringArray(briefSource.key_signals),
    },
  };
}

function normalizeRecord(value: unknown): DecisionRecordPayload {
  const source = asObject(value) || {};
  return {
    simulation_id: asString(source.simulation_id),
    user_id: asString(source.user_id),
    question: asString(source.question) || '未命名推演',
    options_count: asNumber(source.options_count),
    recommendation: asString(source.recommendation),
    schema_version: asNumber(source.schema_version),
    engine_mode: asString(source.engine_mode) || undefined,
    context_snapshot: source.context_snapshot
      ? normalizeContext(source.context_snapshot)
      : undefined,
    collected_info_summary: undefined,
    verifiability_report: undefined,
    options: Array.isArray(source.options)
      ? source.options.map((item, index) => normalizeDecisionOption(item, index))
      : [],
    created_at: asString(source.created_at) || new Date().toISOString(),
  };
}

function normalizeHistory(value: unknown): DecisionHistoryRecord[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.map((item) => {
    const payload = asObject(item) || {};
    return {
      simulation_id: asString(payload.simulation_id),
      question: asString(payload.question) || '未命名推演',
      options_count: asNumber(payload.options_count) || 0,
      recommendation: asString(payload.recommendation),
      created_at: asString(payload.created_at),
    };
  });
}

function normalizeScenario(value: unknown): ParallelLifeScenario {
  const source = asObject(value) || {};
  return {
    scenario_id: asString(source.scenario_id),
    simulation_id: asString(source.simulation_id),
    branch_id: asString(source.branch_id),
    source_question: asString(source.source_question),
    title: asString(source.title) || '平行人生分支体验',
    subtitle: asString(source.subtitle),
    theme: asString(source.theme) || '#0b1830',
    accent: asString(source.accent) || '#5aa9ff',
    cover_emoji: asString(source.cover_emoji) || '◎',
    intro: asString(source.intro),
    nodes: Array.isArray(source.nodes)
      ? source.nodes.map((item) => {
          const payload = asObject(item) || {};
          return {
            id: asString(payload.id),
            type: asString(payload.type) === 'free_input' ? 'free_input' : 'choice',
            text: asString(payload.text),
            next: asString(payload.next) || undefined,
            options: Array.isArray(payload.options)
              ? payload.options.map((option) => {
                  const optionPayload = asObject(option) || {};
                  return {
                    id: asString(optionPayload.id),
                    text: asString(optionPayload.text),
                    sub: asString(optionPayload.sub),
                    delta: Object.entries(asObject(optionPayload.delta) || {}).reduce<
                      Record<string, number>
                    >((result, [key, item]) => {
                      const next = asNumber(item);
                      if (next !== undefined) {
                        result[key] = next;
                      }
                      return result;
                    }, {}),
                    next: asString(optionPayload.next),
                  };
                })
              : [],
          };
        })
      : [],
    endings: Array.isArray(source.endings)
      ? source.endings.map((item) => {
          const payload = asObject(item) || {};
          return {
            condition: asString(payload.condition),
            title: asString(payload.title),
            text: asString(payload.text),
            badge: asString(payload.badge),
          };
        })
      : [],
    branch_context: source.branch_context
      ? normalizeDecisionOption(source.branch_context, 0)
      : undefined,
  };
}

export async function getFutureOsGraphView(
  userId: string,
  options?: {
    view?: 'people' | 'signals';
    question?: string;
    sessionId?: string;
  },
) {
  const params = new URLSearchParams();
  params.set('view', options?.view || 'people');
  if (options?.question) {
    params.set('question', options.question);
  }
  if (options?.sessionId) {
    params.set('session_id', options.sessionId);
  }
  const response = await requestJson<SuccessEnvelope<unknown>>(
    `/api/v5/future-os/knowledge/${encodeURIComponent(userId)}?${params.toString()}`,
  );
  return normalizeGraphView(assertSuccess(response, '知识星图加载失败'));
}

export async function buildFutureOsContext(payload: {
  user_id: string;
  question: string;
  session_id?: string;
}) {
  const response = await postJson<SuccessEnvelope<unknown>>(
    '/api/v5/future-os/context',
    payload,
  );
  return normalizeContext(assertSuccess(response, 'AI 核心上下文构建失败'));
}

export async function routeFutureOsMessage(payload: {
  user_id: string;
  message: string;
}) {
  const response = await postJson<SuccessEnvelope<FutureOsRouteSuggestion>>(
    '/api/v5/future-os/route',
    payload,
  );
  return assertSuccess(response, 'AI 核心路由失败');
}

export async function simulateFutureOs(payload: {
  user_id: string;
  question: string;
  session_id?: string;
  options?: string[];
}) {
  const response = await postJson<SuccessEnvelope<unknown>>(
    '/api/v5/future-os/simulate',
    payload,
  );
  return normalizeRecord(assertSuccess(response, '决策图谱推演失败'));
}

export async function getFutureOsSimulation(simulationId: string) {
  const response = await requestJson<SuccessEnvelope<unknown>>(
    `/api/v5/future-os/simulations/${encodeURIComponent(simulationId)}`,
  );
  return normalizeRecord(assertSuccess(response, '推演详情加载失败'));
}

export async function getFutureOsHistory(userId: string, limit = 20) {
  const response = await requestJson<SuccessEnvelope<unknown>>(
    `/api/v5/future-os/history/${encodeURIComponent(userId)}?limit=${encodeURIComponent(
      String(limit),
    )}`,
  );
  return normalizeHistory(assertSuccess(response, '历史记录加载失败'));
}

export async function createParallelLifeBranch(payload: {
  user_id: string;
  simulation_id: string;
  branch_id: string;
}) {
  const response = await postJson<SuccessEnvelope<unknown>>(
    '/api/v5/future-os/parallel-life/branch',
    payload,
  );
  return normalizeScenario(assertSuccess(response, '平行人生分支创建失败'));
}

export async function completeParallelLifeBranch(payload: {
  user_id: string;
  scenario_id: string;
  simulation_id: string;
  branch_id: string;
  final_stats: Record<string, number>;
  choices: Array<Record<string, unknown>>;
  emotion_feedback?: string;
  free_text?: string;
}) {
  const response = await postJson<SuccessEnvelope<ParallelLifeCompletionResult>>(
    '/api/v5/future-os/parallel-life/complete',
    payload,
  );
  return assertSuccess(response, '平行人生结果提交失败');
}
