import type {
  ApiEnvelope,
  CollectedInfo,
  DecisionGraph,
  DecisionHistoryRecord,
  DecisionOption,
  DecisionRecordPayload,
  FollowUpReview,
  FollowUpSummary,
  LegacyDungeonPayload,
  LegacyDungeonRecord,
  LoraProgressInfo,
  LoraStatusInfo,
  OptionInput,
  RiskDimension,
  TimelineEvent,
  VerifiabilityReport,
} from '../types/api';
import { ApiError, createSocket, postJson, requestJson } from './api';
import {
  buildDecisionGraphEdges,
  buildDecisionGraphSummary,
  buildFallbackDecisionGraph,
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

function asStringMap(value: unknown) {
  const source = asObject(value);
  if (!source) {
    return {};
  }

  return Object.entries(source).reduce<Record<string, string>>((result, entry) => {
    const [key, item] = entry;
    const next = asString(item).trim();
    if (key && next) {
      result[key] = next;
    }
    return result;
  }, {});
}

function hasMeaningfulContent(value: CollectedInfo) {
  return (
    Object.keys(value.decision_scenario).length > 0 ||
    Object.keys(value.constraints).length > 0 ||
    Object.keys(value.priorities).length > 0 ||
    value.concerns.length > 0 ||
    value.mentioned_options.length > 0
  );
}

function normalizeCollectedInfo(value: unknown) {
  const normalized: CollectedInfo = {
    decision_scenario: asStringMap(asObject(value)?.decision_scenario),
    constraints: asStringMap(asObject(value)?.constraints),
    priorities: asStringMap(asObject(value)?.priorities),
    concerns: asStringArray(asObject(value)?.concerns),
    mentioned_options: asStringArray(asObject(value)?.mentioned_options),
  };

  return hasMeaningfulContent(normalized) ? normalized : undefined;
}

function normalizeTimelineEvent(value: unknown, index: number): TimelineEvent {
  return normalizeDecisionGraphNode((asObject(value) || {}) as Partial<TimelineEvent>, index);
}

function normalizeDecisionGraph(
  value: unknown,
  optionId: string,
  title: string,
  timeline: TimelineEvent[],
): DecisionGraph {
  const source = asObject(value);
  if (!source) {
    return buildFallbackDecisionGraph(optionId, title, timeline);
  }

  const nodes = Array.isArray(source.nodes)
    ? source.nodes.map((item, nodeIndex) =>
        normalizeDecisionGraphNode((asObject(item) || {}) as Partial<TimelineEvent>, nodeIndex),
      )
    : timeline.map((item, nodeIndex) => normalizeDecisionGraphNode(item, nodeIndex));

  const edges = Array.isArray(source.edges)
    ? source.edges.reduce<DecisionGraph['edges']>((result, item, edgeIndex) => {
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
          edge_id: asString(payload.edge_id) || `edge_${edgeIndex + 1}`,
          source: sourceId,
          target: targetId,
          relation: asString(payload.relation) || 'next',
          strength: asNumber(payload.strength) || 0,
          label: asString(payload.label) || undefined,
        });
        return result;
      }, [])
    : buildDecisionGraphEdges(nodes);

  const summarySource = asObject(source.graph_summary);
  const graphSummary = summarySource
    ? {
        title: asString(summarySource.title) || title,
        node_count: asNumber(summarySource.node_count) || nodes.length,
        edge_count: asNumber(summarySource.edge_count) || edges.length,
        high_risk_nodes: asNumber(summarySource.high_risk_nodes) || 0,
        dominant_axes: asStringArray(summarySource.dominant_axes),
        agent_stance_mix: Object.entries(asObject(summarySource.agent_stance_mix) || {}).reduce<
          Record<string, number>
        >((result, [key, item]) => {
          const next = asNumber(item);
          if (key && next !== undefined) {
            result[key] = next;
          }
          return result;
        }, {}),
        review_mode: asString(summarySource.review_mode) || undefined,
      }
    : buildDecisionGraphSummary(nodes, edges, title);

  return {
    graph_id: asString(source.graph_id) || `${optionId}_decision_graph`,
    schema_version: asNumber(source.schema_version) || 1,
    layout_hint: asString(source.layout_hint) || undefined,
    graph_summary: graphSummary,
    nodes,
    edges,
  };
}
/*
  const impact = Object.entries(impactSource || {}).reduce<Record<string, number>>(
    (result, entry) => {
      const [key, item] = entry;
      const next = asNumber(item);
      if (key && next !== undefined) {
        result[key] = next;
      }
      return result;
    },
    {},
  );

  return {
    event_id: asString(source.event_id) || `event_${index + 1}`,
    parent_event_id:
      source.parent_event_id === null || source.parent_event_id === undefined
        ? null
        : asString(source.parent_event_id),
    month: asNumber(source.month) || index + 1,
    event: asString(source.event) || `事件 ${index + 1}`,
    event_type: asString(source.event_type) || undefined,
    branch_group: asString(source.branch_group) || undefined,
    node_level: asNumber(source.node_level),
    risk_tag: asString(source.risk_tag) || undefined,
    opportunity_tag: asString(source.opportunity_tag) || undefined,
    visual_weight: asNumber(source.visual_weight),
    impact,
    probability: asNumber(source.probability) || 0,
  };
}
*/

function normalizeRiskAssessment(value: unknown): DecisionOption['risk_assessment'] {
  const source = asObject(value);
  if (!source) {
    return null;
  }

  const overallRisk = asNumber(source.overall_risk);
  const overallLevel = asString(source.overall_level);
  const recommendations = asStringArray(source.recommendations);
  const topDimensions = asStringArray(source.top_dimensions);

  const dimensionsSource = asObject(source.dimensions);
  const dimensions = dimensionsSource
    ? Object.entries(dimensionsSource).reduce<Record<string, RiskDimension>>(
        (result, entry) => {
        const [key, item] = entry;
        const payload = asObject(item);
        if (!payload) {
          return result;
        }

        result[key] = {
          name: asString(payload.name) || key,
          score: asNumber(payload.score) || 0,
          level: asString(payload.level) || 'unknown',
          factors: asStringArray(payload.factors),
          mitigation: asStringArray(payload.mitigation),
        };
          return result;
        },
        {},
      )
    : undefined;

  const hasDimensions = dimensions && Object.keys(dimensions).length > 0;
  if (
    overallRisk === undefined &&
    !overallLevel &&
    recommendations.length === 0 &&
    topDimensions.length === 0 &&
    !hasDimensions
  ) {
    return null;
  }

  return {
    option_title: asString(source.option_title) || undefined,
    overall_risk: overallRisk || 0,
    overall_level: overallLevel || 'unknown',
    high_risk_count: asNumber(source.high_risk_count),
    top_dimensions: topDimensions,
    dimensions: hasDimensions ? dimensions : undefined,
    recommendations,
  };
}

function normalizePredictionTrace(value: unknown): DecisionOption['prediction_trace'] {
  const source = asObject(value);
  if (!source) {
    return null;
  }

  const predictionConfidence = asNumber(source.prediction_confidence);
  const contextCoverage = asNumber(source.context_coverage);
  const eventSpecificity = asNumber(source.event_specificity);
  const evidenceSources = asStringArray(source.evidence_sources);
  const assumptions = asStringArray(source.assumptions);

  if (
    predictionConfidence === undefined &&
    contextCoverage === undefined &&
    eventSpecificity === undefined &&
    evidenceSources.length === 0 &&
    assumptions.length === 0
  ) {
    return null;
  }

  return {
    prediction_confidence: predictionConfidence || 0,
    base_prediction_confidence: asNumber(source.base_prediction_confidence),
    confidence_level: asString(source.confidence_level) || 'unknown',
    context_coverage: contextCoverage || 0,
    event_specificity: eventSpecificity || 0,
    facts_used: asNumber(source.facts_used) || 0,
    main_event_count: asNumber(source.main_event_count) || 0,
    evidence_sources: evidenceSources,
    assumptions,
    calibration_review_count: asNumber(source.calibration_review_count),
    calibration_adjustment: asNumber(source.calibration_adjustment),
    calibration_bias: asString(source.calibration_bias) || undefined,
    calibration_note: asString(source.calibration_note) || undefined,
    calibration_applied:
      typeof source.calibration_applied === 'boolean'
        ? source.calibration_applied
        : undefined,
  };
}

function normalizeDecisionOption(value: unknown, index: number): DecisionOption {
  const source = asObject(value) || {};
  const optionId = asString(source.option_id) || `option_${index + 1}`;
  const title = asString(source.title) || `选项 ${index + 1}`;
  source.title = asString(source.title) || title || `Option ${index + 1}`;
  const timeline = Array.isArray(source.timeline)
    ? source.timeline.map((item, itemIndex) =>
        normalizeTimelineEvent(item, itemIndex),
      )
    : [];

  return {
    option_id: optionId,
    title: asString(source.title) || `选项 ${index + 1}`,
    description: asString(source.description),
    timeline,
    decision_graph: normalizeDecisionGraph(
      source.decision_graph,
      optionId,
      asString(source.title) || `Option ${index + 1}`,
      timeline,
    ),
    final_score: asNumber(source.final_score) || 0,
    risk_level: asNumber(source.risk_level) || 0,
    risk_assessment: normalizeRiskAssessment(source.risk_assessment),
    prediction_trace: normalizePredictionTrace(source.prediction_trace),
    execution_confidence: asNumber(source.execution_confidence),
    dropout_risk_month: asNumber(source.dropout_risk_month) ?? null,
    personal_note: asString(source.personal_note),
  };
}

function normalizeVerifiabilityReport(value: unknown): VerifiabilityReport | undefined {
  const source = asObject(value);
  if (!source) {
    return undefined;
  }

  const engineMode = asString(source.engine_mode);
  const missingInputs = asStringArray(source.missing_key_inputs);
  const collectedCoverage = asNumber(source.collected_info_coverage);
  const avgConfidence = asNumber(source.average_prediction_confidence);

  if (
    !engineMode &&
    missingInputs.length === 0 &&
    collectedCoverage === undefined &&
    avgConfidence === undefined &&
    !asString(source.note)
  ) {
    return undefined;
  }

  return {
    schema_version: asNumber(source.schema_version) || 1,
    engine_mode: engineMode || 'unknown',
    collected_info_coverage: collectedCoverage || 0,
    average_prediction_confidence: avgConfidence || 0,
    missing_key_inputs: missingInputs,
    note: asString(source.note),
    historical_review_count: asNumber(source.historical_review_count),
    calibration_bias: asString(source.calibration_bias) || undefined,
    confidence_adjustment: asNumber(source.confidence_adjustment),
    calibration_quality: asString(source.calibration_quality) || undefined,
    calibration_note: asString(source.calibration_note) || undefined,
  };
}

function normalizeDecisionRecord(value: unknown): DecisionRecordPayload {
  const source = asObject(value) || {};

  return {
    simulation_id: asString(source.simulation_id),
    user_id: asString(source.user_id),
    question: asString(source.question) || '未命名推演',
    options_count: asNumber(source.options_count),
    recommendation: asString(source.recommendation),
    schema_version: asNumber(source.schema_version),
    collected_info_summary: normalizeCollectedInfo(source.collected_info_summary),
    verifiability_report: normalizeVerifiabilityReport(source.verifiability_report),
    options: Array.isArray(source.options)
      ? source.options.map((item, index) => normalizeDecisionOption(item, index))
      : [],
    created_at: asString(source.created_at) || new Date().toISOString(),
  };
}

function normalizeFollowUpReview(value: unknown): FollowUpReview | null {
  const source = asObject(value);
  if (!source) {
    return null;
  }

  return {
    simulation_id: asString(source.simulation_id),
    user_id: asString(source.user_id),
    option_id: asString(source.option_id),
    option_title: asString(source.option_title),
    predicted_score: asNumber(source.predicted_score) || 0,
    predicted_risk_level: asNumber(source.predicted_risk_level) || 0,
    predicted_confidence: asNumber(source.predicted_confidence) || 0,
    actual_score: asNumber(source.actual_score) || 0,
    elapsed_months: asNumber(source.elapsed_months) || 0,
    bias_label: asString(source.bias_label) || 'unknown',
    bias_note: asString(source.bias_note),
    score_gap: asNumber(source.score_gap) || 0,
    absolute_error: asNumber(source.absolute_error) || 0,
    confidence_alignment: asString(source.confidence_alignment),
    risk_alignment: asString(source.risk_alignment),
    actual_summary: asString(source.actual_summary),
    updated_at: asString(source.updated_at),
  };
}

function normalizeFollowUpSummary(value: unknown): FollowUpSummary {
  const source = asObject(value) || {};
  const calibrationSource = asObject(source.user_calibration_profile);

  return {
    review_count: asNumber(source.review_count) || 0,
    average_predicted_score: asNumber(source.average_predicted_score) || 0,
    average_actual_score: asNumber(source.average_actual_score) || 0,
    average_absolute_error: asNumber(source.average_absolute_error) || 0,
    optimistic_count: asNumber(source.optimistic_count) || 0,
    conservative_count: asNumber(source.conservative_count) || 0,
    calibrated_count: asNumber(source.calibrated_count) || 0,
    user_calibration_profile: calibrationSource
      ? {
          review_count: asNumber(calibrationSource.review_count) || 0,
          average_absolute_error:
            asNumber(calibrationSource.average_absolute_error) || 0,
          optimistic_rate: asNumber(calibrationSource.optimistic_rate) || 0,
          conservative_rate: asNumber(calibrationSource.conservative_rate) || 0,
          calibrated_rate: asNumber(calibrationSource.calibrated_rate) || 0,
          overconfident_rate:
            asNumber(calibrationSource.overconfident_rate) || 0,
          bias_tendency:
            asString(calibrationSource.bias_tendency) || 'unknown',
          confidence_adjustment:
            asNumber(calibrationSource.confidence_adjustment) || 0,
          calibration_quality:
            asString(calibrationSource.calibration_quality) || 'unknown',
          note: asString(calibrationSource.note),
        }
      : undefined,
    reviews: Array.isArray(source.reviews)
      ? source.reviews
          .map((item) => normalizeFollowUpReview(item))
          .filter((item): item is FollowUpReview => Boolean(item))
      : [],
  };
}

export async function getDecisionHistory(userId: string) {
  const result = await requestJson<ApiEnvelope<DecisionHistoryRecord[]>>(
    `/api/decision/enhanced/history/${encodeURIComponent(userId)}`,
  );

  if (result.code !== 200) {
    throw new ApiError(result.message || '获取预测历史失败', result.code, result);
  }

  return Array.isArray(result.data)
    ? result.data.map((item) => ({
        simulation_id: asString(asObject(item)?.session_id) || asString(asObject(item)?.simulation_id),
        question: asString(asObject(item)?.question) || '未命名推演',
        options_count: asNumber(asObject(item)?.options_count) || 0,
        recommendation: asString(asObject(item)?.recommendation),
        created_at: asString(asObject(item)?.created_at),
      }))
    : [];
}

export async function getDecisionRecord(simulationId: string) {
  const result = await requestJson<ApiEnvelope<DecisionRecordPayload>>(
    `/api/decision/enhanced/record/${encodeURIComponent(simulationId)}`,
  );

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '获取推演详情失败', result.code, result);
  }

  return normalizeDecisionRecord(result.data);
}

export async function getDecisionFollowUp(simulationId: string) {
  const result = await requestJson<ApiEnvelope<FollowUpSummary>>(
    `/api/decision/enhanced/follow-up/${encodeURIComponent(simulationId)}`,
  );

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '获取回访结果失败', result.code, result);
  }

  return normalizeFollowUpSummary(result.data);
}

export async function submitDecisionFollowUp(payload: {
  user_id: string;
  simulation_id: string;
  option_id: string;
  option_title: string;
  actual_score: number;
  elapsed_months: number;
  actual_summary: string;
}) {
  const result = await postJson<
    ApiEnvelope<{
      review: unknown;
      summary: FollowUpSummary;
    }>
  >('/api/decision/enhanced/follow-up', payload);

  if (result.code !== 200 || !result.data?.summary) {
    throw new ApiError(result.message || '提交回访失败', result.code, result);
  }

  return normalizeFollowUpSummary(result.data.summary);
}

export async function startDecisionCollection(payload: {
  user_id: string;
  initial_question: string;
  decision_type?: 'career' | 'relationship' | 'education' | 'general';
}) {
  const result = await postJson<
    ApiEnvelope<{ session_id: string; message: string }>
  >('/api/decision/enhanced/collect/start', payload);

  if (result.code !== 200 || !result.data?.session_id) {
    throw new ApiError(result.message || '启动信息采集失败', result.code, result);
  }

  return {
    session_id: asString(result.data.session_id),
    message: asString(result.data.message),
  };
}

/**
 * 流式版本：开始决策信息收集，实时推送状态
 */
export async function* streamStartDecisionCollection(payload: {
  user_id: string;
  initial_question: string;
  decision_type?: 'career' | 'relationship' | 'education' | 'general';
}): AsyncGenerator<{
  type: 'status' | 'complete' | 'error';
  content?: string;
  data?: { session_id: string; message: string };
}> {
  const response = await fetch('/api/decision/persona/collect/start-stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    throw new ApiError('启动信息采集失败', response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const chunk = JSON.parse(line.slice(6));
            yield chunk;
          } catch (e) {
            console.error('解析SSE数据失败:', e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export async function continueDecisionCollection(payload: {
  session_id: string;
  user_response: string;
}) {
  const result = await postJson<
    ApiEnvelope<{
      round?: number;
      phase?: string;
      ai_question?: string;
      is_complete?: boolean;
      summary?: string;
      collected_info?: CollectedInfo;
    }>
  >('/api/decision/enhanced/collect/continue', payload);

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '继续采集失败', result.code, result);
  }

  return {
    round: asNumber(result.data.round),
    phase: asString(result.data.phase),
    ai_question: asString(result.data.ai_question) || undefined,
    is_complete: Boolean(result.data.is_complete),
    summary: asString(result.data.summary) || undefined,
    collected_info: normalizeCollectedInfo(result.data.collected_info) || null,
  };
}

export async function generateDecisionOptions(payload: {
  session_id: string;
  user_options: string[];
}) {
  const result = await postJson<
    ApiEnvelope<{ ai_options: OptionInput[] }>
  >('/api/decision/enhanced/generate-options', payload);

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '生成选项失败', result.code, result);
  }

  return Array.isArray(result.data.ai_options)
    ? result.data.ai_options
        .map((item, index) => ({
          title: asString(asObject(item)?.title).trim() || `选项 ${index + 1}`,
          description: asString(asObject(item)?.description).trim(),
        }))
        .filter((item) => item.title)
    : [];
}

export async function getLoraStatus(userId: string) {
  const result = await requestJson<ApiEnvelope<LoraStatusInfo>>(
    `/api/lora/status/${encodeURIComponent(userId)}`,
  );

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '获取个性模型状态失败', result.code, result);
  }

  return {
    has_lora: Boolean(result.data.has_lora),
    lora_path: result.data.lora_path || null,
    model_version: asNumber(result.data.model_version) || 0,
    last_train_time: result.data.last_train_time || null,
    training_data_size: asNumber(result.data.training_data_size) || 0,
    is_loaded: Boolean(result.data.is_loaded),
  };
}

export async function triggerLoraTraining(userId: string) {
  const result = await postJson<ApiEnvelope<unknown>>(
    `/api/lora/train/${encodeURIComponent(userId)}`,
  );

  if (result.code !== 200) {
    throw new ApiError(result.message || '触发个性模型训练失败', result.code, result);
  }
}

export async function getLoraProgress(userId: string) {
  const result = await requestJson<ApiEnvelope<LoraProgressInfo>>(
    `/api/lora/progress/${encodeURIComponent(userId)}`,
  );

  if (result.code !== 200) {
    throw new ApiError(result.message || '获取个性模型训练进度失败', result.code, result);
  }

  return {
    progress: asNumber(result.data?.progress) || 0,
    stage: asString(result.data?.stage),
    is_training: Boolean(result.data?.is_training),
    error: asString(result.data?.error) || null,
  };
}

export async function listLegacyDungeons(userId: string) {
  const result = await requestJson<
    ApiEnvelope<{ user_id: string; dungeons: LegacyDungeonRecord[]; total: number }>
  >(`/api/decision/dungeons/${encodeURIComponent(userId)}`);

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '获取旧版副本失败', result.code, result);
  }

  return Array.isArray(result.data.dungeons)
    ? result.data.dungeons.map((item) => ({
        dungeon_id: asString(asObject(item)?.dungeon_id),
        title: asString(asObject(item)?.title) || '未命名副本',
        description: asString(asObject(item)?.description),
        options_count: asNumber(asObject(item)?.options_count) || 0,
        created_at: asString(asObject(item)?.created_at),
        lora_trained: Boolean(asObject(item)?.lora_trained),
      }))
    : [];
}

export async function getLegacyDungeon(dungeonId: string) {
  const result = await requestJson<ApiEnvelope<LegacyDungeonPayload>>(
    `/api/decision/dungeon/${encodeURIComponent(dungeonId)}`,
  );

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '获取旧版副本详情失败', result.code, result);
  }

  const source = asObject(result.data) || {};
  return {
    dungeon_id: asString(source.dungeon_id),
    user_id: asString(source.user_id),
    title: asString(source.title) || '未命名副本',
    description: asString(source.description),
    context: asString(source.context) || undefined,
    urgency: asString(source.urgency) || undefined,
    options: Array.isArray(source.options)
      ? source.options.map((item, index) => normalizeDecisionOption(item, index))
      : [],
    recommendation: asString(source.recommendation),
    created_at: asString(source.created_at),
  };
}

interface DecisionSocketHandlers {
  onEvent?: (event: Record<string, unknown>) => void;
  onError?: (message: string) => void;
}

export function openDecisionSimulationSocket(
  payload: { 
    session_id: string; 
    user_id: string;
    question: string;
    option: OptionInput;
    option_index: number;
    collected_info?: CollectedInfo;
    decision_type?: string;
  },
  handlers: DecisionSocketHandlers & { onOpen?: (socket: WebSocket) => void },
) {
  // 使用决策人格系统WebSocket端点
  const socket = createSocket('/api/decision/persona/ws/simulate-option');

  socket.addEventListener('open', () => {
    console.log('[WebSocket] 连接已建立');
    
    // 调用onOpen回调，传递socket实例
    if (handlers.onOpen) {
      handlers.onOpen(socket);
    }
    
    // 发送start_simulation消息
    socket.send(JSON.stringify({
      type: 'start_simulation',
      session_id: payload.session_id,
      user_id: payload.user_id,
      question: payload.question,
      option: payload.option,
      option_index: payload.option_index,
      collected_info: payload.collected_info || {},
      decision_type: payload.decision_type || 'general',
    }));
  });

  socket.addEventListener('message', (event) => {
    try {
      const parsed = JSON.parse(String(event.data)) as Record<string, unknown>;
      console.log('[WebSocket] 收到消息:', parsed.type, parsed);
      if (parsed.type === 'error') {
        handlers.onError?.(String(parsed.content || '推演流式连接异常'));
      }
      handlers.onEvent?.(parsed);
    } catch (error) {
      console.error('[WebSocket] 解析消息失败:', error, event.data);
      handlers.onError?.(
        error instanceof Error ? error.message : '解析推演事件失败',
      );
    }
  });

  socket.addEventListener('error', (event) => {
    console.error('[WebSocket] 连接错误:', event);
    handlers.onError?.('推演连接异常，请稍后重试');
  });

  socket.addEventListener('close', (event) => {
    console.log('[WebSocket] 连接已关闭:', event.code, event.reason);
    if (event.code !== 1000 && event.code !== 1001) {
      handlers.onError?.(`连接异常关闭 (${event.code}): ${event.reason || '未知原因'}`);
    }
  });

  return () => {
    if (
      socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING
    ) {
      socket.close();
    }
  };
}


// ── 流式信息采集 ──────────────────────────────────────────
export async function* streamDecisionCollection(payload: {
  session_id: string;
  user_response: string;
}): AsyncGenerator<{
  type: 'status' | 'progress' | 'message' | 'complete';
  content?: string;
  progress?: { current: number; total: number; stage: string };
  data?: {
    round?: number;
    phase?: string;
    ai_question?: string;
    is_complete?: boolean;
    collected_info?: CollectedInfo;
  };
}> {
  try {
    // 使用兼容路由
    const response = await fetch('/api/decision/enhanced/collect/continue-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new ApiError(`HTTP ${response.status}`, response.status);
    }

    if (!response.body) {
      throw new ApiError('No response body', 500);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim() || !line.startsWith('data: ')) continue;
        
        try {
          const data = JSON.parse(line.slice(6));
          yield data;
        } catch (e) {
          console.warn('Failed to parse SSE data:', line);
        }
      }
    }
  } catch (error) {
    console.error('Stream error:', error);
    throw error;
  }
}


// ── AI核心预热 ──────────────────────────────────────────
export async function warmupAICore(userId: string): Promise<void> {
  try {
    await postJson('/api/decision/persona/ai-core/warmup', { user_id: userId });
  } catch (error) {
    // 预热失败不影响使用
    console.warn('AI核心预热失败:', error);
  }
}

export async function getWarmupStatus(userId: string): Promise<{
  status: 'not_started' | 'warming' | 'ready' | 'error';
  stage: string;
  progress: number;
}> {
  try {
    const result = await requestJson<ApiEnvelope<{
      status: string;
      stage: string;
      progress: number;
    }>>(`/api/decision/persona/ai-core/warmup-status/${encodeURIComponent(userId)}`);
    
    if (result.code === 200 && result.data) {
      return {
        status: result.data.status as any,
        stage: result.data.stage || '未知',
        progress: result.data.progress || 0,
      };
    }
    
    return { status: 'ready', stage: '就绪', progress: 100 };
  } catch (error) {
    console.warn('获取预热状态失败:', error);
    return { status: 'ready', stage: '就绪', progress: 100 };
  }
}
