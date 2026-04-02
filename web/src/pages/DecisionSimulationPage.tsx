import { startTransition, useEffect, useRef, useState } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';
import { MetricCard } from '../components/common/MetricCard';
import { StatusPill } from '../components/common/StatusPill';
import { TimelineMap } from '../components/decision/TimelineMap';
import { AppShell } from '../components/shell/AppShell';
import { useAuth } from '../hooks/useAuth';
import {
  getDecisionFollowUp,
  getDecisionRecord,
  getLegacyDungeon,
  openDecisionSimulationSocket,
  submitDecisionFollowUp,
} from '../services/decision';
import type {
  DecisionOption,
  DecisionRecordPayload,
  DecisionSimulationRouteState,
  FollowUpReview,
  FollowUpSummary,
  OptionInput,
  TimelineEvent,
} from '../types/api';

const optionPalette = ['#0A59F7', '#6B48FF', '#00C853', '#FF9500', '#FF6B9D'];

function toOptionalNumber(value: unknown) {
  const next = Number(value);
  return Number.isFinite(next) ? next : undefined;
}

function toneForRisk(risk: number) {
  if (risk >= 0.7) return 'danger';
  if (risk >= 0.45) return 'warning';
  return 'success';
}

function riskLabel(risk: number) {
  if (risk >= 0.7) return '高风险';
  if (risk >= 0.45) return '中风险';
  return '低风险';
}

function confidenceLabel(value: number) {
  if (value >= 0.75) return '高置信';
  if (value >= 0.5) return '中置信';
  return '低置信';
}

function formatPercent(value?: number | null) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '--';
  }
  return `${(value * 100).toFixed(0)}%`;
}

function joinText(values?: string[]) {
  return values && values.length > 0 ? values.join(' / ') : '暂无';
}

function hasCollectedInfo(record: DecisionRecordPayload | null) {
  const summary = record?.collected_info_summary;
  if (!summary) {
    return false;
  }

  return (
    Object.keys(summary.decision_context || {}).length > 0 ||
    Object.keys(summary.user_constraints || {}).length > 0 ||
    Object.keys(summary.priorities || {}).length > 0 ||
    (summary.concerns || []).length > 0 ||
    (summary.options_mentioned || []).length > 0
  );
}

function buildEmptyRecord(
  userId: string,
  question: string,
  options: OptionInput[],
  collectedInfo?: DecisionRecordPayload['collected_info_summary'] | null,
): DecisionRecordPayload {
  return {
    simulation_id: '',
    user_id: userId,
    question,
    recommendation: '',
    collected_info_summary: collectedInfo || undefined,
    options: options.map((option, index) => ({
      option_id: `option_${index + 1}`,
      title: option.title,
      description: option.description,
      timeline: [],
      final_score: 0,
      risk_level: 0,
    })),
    created_at: new Date().toISOString(),
  };
}

function mapLegacyRecord(payload: {
  dungeon_id: string;
  user_id: string;
  title: string;
  recommendation: string;
  created_at: string;
  options: DecisionOption[];
}): DecisionRecordPayload {
  return {
    simulation_id: payload.dungeon_id,
    user_id: payload.user_id,
    question: payload.title,
    recommendation: payload.recommendation,
    options: payload.options || [],
    created_at: payload.created_at,
  };
}

function getReviewForOption(summary: FollowUpSummary | null, optionId?: string): FollowUpReview | null {
  if (!summary || !optionId) {
    return null;
  }
  return summary.reviews.find((item) => item.option_id === optionId) || null;
}

function parseRouteState(
  state: unknown,
  fallbackUserId: string,
  searchParams: URLSearchParams,
): DecisionSimulationRouteState {
  const routeState = (state || {}) as Partial<DecisionSimulationRouteState>;
  return {
    mode:
      routeState.mode ||
      (searchParams.get('simulationId')
        ? 'history'
        : searchParams.get('dungeonId')
          ? 'legacy'
          : 'stream'),
    sessionId: routeState.sessionId || searchParams.get('sessionId') || undefined,
    simulationId: routeState.simulationId || searchParams.get('simulationId') || undefined,
    dungeonId: routeState.dungeonId || searchParams.get('dungeonId') || undefined,
    question: routeState.question || searchParams.get('question') || '决策推演',
    userId: routeState.userId || fallbackUserId,
    options: routeState.options || [],
    collectedInfo: routeState.collectedInfo || null,
    record: routeState.record,
  };
}

export function DecisionSimulationPage() {
  const { user } = useAuth();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const configRef = useRef(parseRouteState(location.state, user?.user_id || '', searchParams));
  const config = configRef.current;

  const [record, setRecord] = useState<DecisionRecordPayload | null>(() => {
    if (config.record) {
      return config.record;
    }
    if (config.mode === 'stream') {
      return buildEmptyRecord(
        config.userId,
        config.question,
        config.options || [],
        config.collectedInfo || null,
      );
    }
    return null;
  });
  const [selectedOptionIndex, setSelectedOptionIndex] = useState(0);
  const [selectedEventId, setSelectedEventId] = useState('');
  const [streamStatus, setStreamStatus] = useState(config.mode === 'stream' ? '准备连接推演引擎...' : '');
  const [liveThinking, setLiveThinking] = useState('');
  const [followUpSummary, setFollowUpSummary] = useState<FollowUpSummary | null>(null);
  const [isLoading, setIsLoading] = useState(config.mode !== 'stream' && !config.record);
  const [isStreaming, setIsStreaming] = useState(config.mode === 'stream');
  const [error, setError] = useState('');
  const [followUpActualScore, setFollowUpActualScore] = useState(60);
  const [followUpElapsedMonths, setFollowUpElapsedMonths] = useState(3);
  const [followUpText, setFollowUpText] = useState('');
  const [isSubmittingFollowUp, setIsSubmittingFollowUp] = useState(false);
  const socketCloseRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    return () => {
      socketCloseRef.current?.();
      socketCloseRef.current = null;
    };
  }, []);

  const activeOption = record?.options[selectedOptionIndex] || null;
  const activeReview = getReviewForOption(followUpSummary, activeOption?.option_id);
  const selectedEvent =
    activeOption?.timeline.find(
      (event, index) =>
        (event.event_id || `event_${event.month}_${index}`) === selectedEventId ||
        `${event.month}_${event.event}` === selectedEventId,
    ) || null;
  const riskDimensions = activeOption?.risk_assessment?.dimensions
    ? Object.entries(activeOption.risk_assessment.dimensions)
    : [];

  useEffect(() => {
    if (activeOption && !activeReview && activeOption.final_score) {
      setFollowUpActualScore(Math.round(activeOption.final_score));
    }
  }, [activeOption, activeReview]);

  useEffect(() => {
    if (!record?.options.length) {
      if (selectedOptionIndex !== 0) {
        setSelectedOptionIndex(0);
      }
      return;
    }

    if (selectedOptionIndex > record.options.length - 1) {
      setSelectedOptionIndex(0);
    }
  }, [record, selectedOptionIndex]);

  useEffect(() => {
    if (!activeOption) {
      if (selectedEventId) {
        setSelectedEventId('');
      }
      return;
    }

    const eventStillExists = activeOption.timeline.some(
      (event, index) =>
        (event.event_id || `event_${event.month}_${index}`) === selectedEventId ||
        `${event.month}_${event.event}` === selectedEventId,
    );

    if (eventStillExists) {
      return;
    }

    const firstEvent = activeOption.timeline[0];
    setSelectedEventId(firstEvent ? firstEvent.event_id || `${firstEvent.month}_${firstEvent.event}` : '');
  }, [activeOption, selectedEventId]);

  useEffect(() => {
    async function bootstrap() {
      try {
        if (config.mode === 'stream' && config.sessionId && (config.options || []).length > 0) {
          socketCloseRef.current = openDecisionSimulationSocket(
            {
              session_id: config.sessionId,
              options: config.options || [],
            },
            {
              onError: (message) => {
                setError(message);
                setIsStreaming(false);
              },
              onEvent: (event) => {
                const type = String(event.type || '');
                if (type === 'start') {
                  setStreamStatus('推演已启动');
                  return;
                }
                if (type === 'status') {
                  setStreamStatus(String(event.content || ''));
                  return;
                }
                if (type === 'thinking_chunk') {
                  setLiveThinking((current) => `${current}${String(event.content || '')}`.slice(-2400));
                  return;
                }
                if (type === 'thinking') {
                  setLiveThinking(String(event.content || '').slice(-2400));
                  return;
                }
                if (type === 'node') {
                  const optionId = String(event.option_id || '');
                  const node = event.node as TimelineEvent;
                  startTransition(() => {
                    setRecord((current) =>
                      current
                        ? {
                            ...current,
                            options: current.options.map((option) =>
                              option.option_id === optionId
                                ? { ...option, timeline: [...option.timeline, node] }
                                : option,
                            ),
                          }
                        : current,
                    );
                  });
                  if (node?.event_id) {
                    setSelectedEventId(node.event_id);
                  }
                  return;
                }
                if (type === 'option_complete') {
                  const optionId = String(event.option_id || '');
                  startTransition(() => {
                    setRecord((current) =>
                      current
                        ? {
                            ...current,
                            options: current.options.map((option) =>
                              option.option_id === optionId
                                ? {
                                    ...option,
                                    title: String(event.title || option.title),
                                    final_score: Number(event.final_score || 0),
                                    risk_level: Number(event.risk_level || 0),
                                    risk_assessment:
                                      (event.risk_assessment as DecisionOption['risk_assessment']) || null,
                                    prediction_trace:
                                      (event.prediction_trace as DecisionOption['prediction_trace']) || null,
                                    execution_confidence: toOptionalNumber(event.execution_confidence),
                                    dropout_risk_month: toOptionalNumber(event.dropout_risk_month) ?? null,
                                    personal_note: String(event.personal_note || option.personal_note || ''),
                                  }
                                : option,
                            ),
                          }
                        : current,
                    );
                  });
                  return;
                }
                if (type === 'recommendation_chunk') {
                  setRecord((current) =>
                    current
                      ? {
                          ...current,
                          recommendation: `${current.recommendation || ''}${String(event.content || '')}`,
                        }
                      : current,
                  );
                  return;
                }
                if (type === 'recommendation') {
                  setRecord((current) =>
                    current ? { ...current, recommendation: String(event.content || '') } : current,
                  );
                  setStreamStatus('推荐生成完成');
                  return;
                }
                if (type === 'verifiability_report') {
                  setRecord((current) =>
                    current
                      ? {
                          ...current,
                          verifiability_report:
                            event.content as DecisionRecordPayload['verifiability_report'],
                        }
                      : current,
                  );
                  return;
                }
                if (type === 'done') {
                  const nextSimulationId = String(event.simulation_id || '');
                  setRecord((current) =>
                    current
                      ? {
                          ...current,
                          simulation_id: nextSimulationId || current.simulation_id,
                          user_id: String(event.user_id || current.user_id),
                          question: String(event.question || current.question),
                        }
                      : current,
                  );
                  setStreamStatus('全部推演完成');
                  setIsStreaming(false);
                  if (nextSimulationId) {
                    void getDecisionFollowUp(nextSimulationId).then(setFollowUpSummary).catch(() => undefined);
                  }
                }
              },
            },
          );
          return;
        }

        if (config.simulationId) {
          const payload = await getDecisionRecord(config.simulationId);
          setRecord(payload);
          if (payload.simulation_id) {
            const summary = await getDecisionFollowUp(payload.simulation_id);
            setFollowUpSummary(summary);
          }
          return;
        }

        if (config.dungeonId) {
          const payload = await getLegacyDungeon(config.dungeonId);
          setRecord(mapLegacyRecord(payload));
        }
      } catch (bootstrapError) {
        setError(bootstrapError instanceof Error ? bootstrapError.message : '加载推演详情失败');
      } finally {
        setIsLoading(false);
      }
    }

    void bootstrap();
  }, [config]);

  async function handleSubmitFollowUp() {
    if (!record?.simulation_id || !activeOption || isSubmittingFollowUp) {
      return;
    }

    setIsSubmittingFollowUp(true);
    setError('');
    try {
      const summary = await submitDecisionFollowUp({
        user_id: record.user_id || user?.user_id || '',
        simulation_id: record.simulation_id,
        option_id: activeOption.option_id,
        option_title: activeOption.title,
        actual_score: followUpActualScore,
        elapsed_months: followUpElapsedMonths,
        actual_summary: followUpText,
      });
      setFollowUpSummary(summary);
      setFollowUpText('');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '提交回访失败');
    } finally {
      setIsSubmittingFollowUp(false);
    }
  }

  return (
    <AppShell
      title="推演详情"
      subtitle="把 recommendation、prediction trace、risk assessment、时间线和回访校准放在同一个结果面板里。"
      actions={
        streamStatus ? (
          <StatusPill tone={isStreaming ? 'primary' : 'success'}>{streamStatus}</StatusPill>
        ) : null
      }
    >
      {isLoading || !record ? (
        <GlassCard title="正在加载" subtitle="拉取推演详情或连接 WebSocket">
          <p className="empty-copy">请稍候...</p>
        </GlassCard>
      ) : (
        <div className="stack-layout">
          <section className="hero-card simulation-hero-card">
            <div className="hero-copy">
              <p className="eyebrow">Simulation Result</p>
              <h2>{record.question}</h2>
              <p>
                当前展示的是一个完整的推演结果面板。你可以在不同选项间切换，查看时间线、
                风险结构、预测证据和后续校准情况。
              </p>
            </div>
            <div className="hero-side">
              <div className="metrics-grid compact-grid">
                <MetricCard
                  label="方案数量"
                  value={String(record.options.length)}
                  helper={record.simulation_id || 'streaming'}
                  tone="primary"
                />
                <MetricCard
                  label="当前模式"
                  value={config.mode === 'stream' ? '流式' : config.mode === 'legacy' ? 'Legacy' : '历史'}
                  helper="route mode"
                  tone="secondary"
                />
                <MetricCard
                  label="当前选中"
                  value={activeOption ? `${selectedOptionIndex + 1}` : '--'}
                  helper={activeOption?.title || '暂无'}
                  tone="accent"
                />
              </div>
            </div>
          </section>

          <GlassCard title="选项总览" subtitle={`simulation_id: ${record.simulation_id || 'streaming'}`}>
            <div className="option-tab-list">
              {record.options.map((option, index) => (
                <button
                  key={option.option_id}
                  className={`option-tab${index === selectedOptionIndex ? ' is-active' : ''}`}
                  onClick={() => setSelectedOptionIndex(index)}
                >
                  <span>{option.title}</span>
                  <small>{option.final_score ? option.final_score.toFixed(0) : '--'} 分</small>
                </button>
              ))}
            </div>

            {activeOption ? (
              <>
                <div className="metrics-grid">
                  <MetricCard
                    label="最终分数"
                    value={activeOption.final_score ? activeOption.final_score.toFixed(0) : '--'}
                    helper={activeOption.description}
                    tone="primary"
                  />
                  <MetricCard
                    label="风险等级"
                    value={riskLabel(activeOption.risk_level || 0)}
                    helper={`risk=${(activeOption.risk_level || 0).toFixed(2)}`}
                    tone="warning"
                  />
                  <MetricCard
                    label="执行信心"
                    value={formatPercent(activeOption.execution_confidence)}
                    helper="self prediction"
                    tone="secondary"
                  />
                  <MetricCard
                    label="掉线风险月"
                    value={activeOption.dropout_risk_month ? `${activeOption.dropout_risk_month}` : '--'}
                    helper="dropout_risk_month"
                    tone="accent"
                  />
                </div>

                {activeOption.personal_note ? (
                  <div className="insight-banner">
                    <strong>用户自我预判</strong>
                    <p>{activeOption.personal_note}</p>
                  </div>
                ) : null}
              </>
            ) : null}
          </GlassCard>

          <section className="two-column-grid simulation-main-grid">
            <GlassCard title="时间线地图" subtitle="主链节点与分叉事件会在这里可视化。">
              {activeOption ? (
                <>
                  <TimelineMap
                    events={activeOption.timeline || []}
                    accent={optionPalette[selectedOptionIndex % optionPalette.length]}
                    selectedEventId={selectedEventId}
                    onSelect={(event) =>
                      setSelectedEventId(event.event_id || `${event.month}_${event.event}`)
                    }
                  />
                  {selectedEvent ? (
                    <div className="event-detail">
                      <strong>{selectedEvent.event}</strong>
                      <p>
                        月份 {selectedEvent.month} / 概率 {(selectedEvent.probability * 100).toFixed(0)}% /
                        影响字段 {Object.keys(selectedEvent.impact || {}).join(', ') || '暂无'}
                      </p>
                    </div>
                  ) : null}
                </>
              ) : (
                <p className="empty-copy">当前选项还没有时间线节点。</p>
              )}
            </GlassCard>

            <div className="stack-layout">
              <GlassCard title="风险评估" subtitle="risk_assessment">
                {activeOption?.risk_assessment ? (
                  <>
                    <div className="status-row">
                      <span>总体风险</span>
                      <StatusPill tone={toneForRisk((activeOption.risk_assessment.overall_risk || 0) / 10)}>
                        {activeOption.risk_assessment.overall_level || 'unknown'}
                      </StatusPill>
                    </div>
                    <ul className="plain-list">
                      {(activeOption.risk_assessment.top_dimensions || []).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                    {riskDimensions.length > 0 ? (
                      <div className="summary-groups">
                        {riskDimensions.slice(0, 4).map(([key, dimension]) => (
                          <div key={key}>
                            <strong>
                              {dimension.name} / {dimension.level} / {dimension.score.toFixed(1)}
                            </strong>
                            <p>风险因素：{joinText(dimension.factors)}</p>
                            <p>缓解动作：{joinText(dimension.mitigation)}</p>
                          </div>
                        ))}
                      </div>
                    ) : null}
                    <div className="summary-groups">
                      {(activeOption.risk_assessment.recommendations || []).map((item, index) => (
                        <div key={`${item}_${index}`}>
                          <strong>缓解建议 {index + 1}</strong>
                          <p>{item}</p>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="empty-copy">当前选项暂无结构化风险评估。</p>
                )}
              </GlassCard>

              <GlassCard title="预测轨迹" subtitle="prediction_trace">
                {activeOption?.prediction_trace ? (
                  <>
                    <div className="metrics-grid compact-grid">
                      <MetricCard
                        label="预测置信"
                        value={formatPercent(activeOption.prediction_trace.prediction_confidence)}
                        helper={confidenceLabel(activeOption.prediction_trace.prediction_confidence)}
                        tone="secondary"
                      />
                      <MetricCard
                        label="上下文覆盖"
                        value={formatPercent(activeOption.prediction_trace.context_coverage)}
                        helper="context_coverage"
                        tone="accent"
                      />
                      <MetricCard
                        label="事件具体度"
                        value={formatPercent(activeOption.prediction_trace.event_specificity)}
                        helper="event_specificity"
                        tone="primary"
                      />
                    </div>
                    <div className="summary-groups">
                      <div>
                        <strong>证据来源</strong>
                        <p>{joinText(activeOption.prediction_trace.evidence_sources)}</p>
                      </div>
                      <div>
                        <strong>关键假设</strong>
                        <p>{joinText(activeOption.prediction_trace.assumptions)}</p>
                      </div>
                      {activeOption.prediction_trace.calibration_review_count ? (
                        <div>
                          <strong>历史校准</strong>
                          <p>{activeOption.prediction_trace.calibration_note || '已纳入历史回访修正'}</p>
                        </div>
                      ) : null}
                      {activeOption.prediction_trace.calibration_bias ? (
                        <div>
                          <strong>偏差倾向</strong>
                          <p>{activeOption.prediction_trace.calibration_bias}</p>
                        </div>
                      ) : null}
                    </div>
                  </>
                ) : (
                  <p className="empty-copy">当前选项暂无 prediction trace。</p>
                )}
              </GlassCard>
            </div>
          </section>

          <section className="two-column-grid simulation-main-grid">
            <GlassCard title="推荐与可验证性" subtitle="recommendation + verifiability_report">
              <div className="recommendation-block">
                {record.recommendation || '推荐内容生成中...'}
              </div>
              {record.verifiability_report ? (
                <div className="summary-groups">
                  <div>
                    <strong>引擎模式</strong>
                    <p>{record.verifiability_report.engine_mode}</p>
                  </div>
                  <div>
                    <strong>覆盖率</strong>
                    <p>{formatPercent(record.verifiability_report.collected_info_coverage)}</p>
                  </div>
                  <div>
                    <strong>平均置信度</strong>
                    <p>{formatPercent(record.verifiability_report.average_prediction_confidence)}</p>
                  </div>
                  <div>
                    <strong>缺失输入</strong>
                    <p>{joinText(record.verifiability_report.missing_key_inputs)}</p>
                  </div>
                  {record.verifiability_report.calibration_quality ? (
                    <div>
                      <strong>校准质量</strong>
                      <p>{record.verifiability_report.calibration_quality}</p>
                    </div>
                  ) : null}
                  {record.verifiability_report.note ? (
                    <div>
                      <strong>引擎说明</strong>
                      <p>{record.verifiability_report.note}</p>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </GlassCard>

            <GlassCard title="预测后回访校准" subtitle="follow-up / calibration loop">
              {followUpSummary?.review_count ? (
                <>
                  <div className="metrics-grid compact-grid">
                    <MetricCard
                      label="历史回访"
                      value={String(followUpSummary.review_count)}
                      helper="review_count"
                      tone="primary"
                    />
                    <MetricCard
                      label="平均绝对误差"
                      value={followUpSummary.average_absolute_error.toFixed(1)}
                      helper="absolute_error"
                      tone="warning"
                    />
                    <MetricCard
                      label="偏差倾向"
                      value={followUpSummary.user_calibration_profile?.bias_tendency || 'unknown'}
                      helper={followUpSummary.user_calibration_profile?.calibration_quality || ''}
                      tone="secondary"
                    />
                  </div>
                  {followUpSummary.user_calibration_profile?.note ? (
                    <div className="insight-banner">
                      <strong>校准画像</strong>
                      <p>{followUpSummary.user_calibration_profile.note}</p>
                    </div>
                  ) : null}
                </>
              ) : (
                <p className="empty-copy">还没有回访记录，你可以在这里录入真实结果。</p>
              )}

              {activeReview ? (
                <div className="summary-groups">
                  <div>
                    <strong>已录入结果</strong>
                    <p>
                      实际 {activeReview.actual_score.toFixed(0)} 分，{activeReview.elapsed_months} 个月后，
                      {activeReview.bias_label}
                    </p>
                  </div>
                  <div>
                    <strong>偏差说明</strong>
                    <p>{activeReview.bias_note}</p>
                  </div>
                  <div>
                    <strong>对齐情况</strong>
                    <p>
                      置信度 {activeReview.confidence_alignment || 'unknown'} / 风险判断{' '}
                      {activeReview.risk_alignment || 'unknown'}
                    </p>
                  </div>
                  {activeReview.actual_summary ? (
                    <div>
                      <strong>真实结果摘要</strong>
                      <p>{activeReview.actual_summary}</p>
                    </div>
                  ) : null}
                </div>
              ) : activeOption ? (
                <div className="stack-form">
                  <label>
                    <span>实际结果评分</span>
                    <input
                      className="input"
                      type="number"
                      min={0}
                      max={100}
                      value={followUpActualScore}
                      onChange={(event) => setFollowUpActualScore(Number(event.target.value))}
                    />
                  </label>
                  <label>
                    <span>经过月份</span>
                    <input
                      className="input"
                      type="number"
                      min={1}
                      max={36}
                      value={followUpElapsedMonths}
                      onChange={(event) => setFollowUpElapsedMonths(Number(event.target.value))}
                    />
                  </label>
                  <label>
                    <span>真实结果摘要</span>
                    <textarea
                      className="textarea"
                      rows={4}
                      value={followUpText}
                      onChange={(event) => setFollowUpText(event.target.value)}
                      placeholder="几个月后实际发生了什么？哪些地方和预测一致，哪些地方不一致？"
                    />
                  </label>
                  <button
                    className="button button-primary"
                    onClick={() => void handleSubmitFollowUp()}
                    disabled={isSubmittingFollowUp || !followUpText.trim()}
                  >
                    {isSubmittingFollowUp ? '提交中...' : '提交回访结果'}
                  </button>
                </div>
              ) : null}
            </GlassCard>
          </section>

          {hasCollectedInfo(record) ? (
            <GlassCard title="采集输入摘要" subtitle="让结论和证据之间真正可追溯。">
              <div className="summary-groups">
                <div>
                  <strong>顾虑</strong>
                  <p>{joinText(record.collected_info_summary?.concerns)}</p>
                </div>
                <div>
                  <strong>优先级</strong>
                  <p>{joinText(Object.keys(record.collected_info_summary?.priorities || {}))}</p>
                </div>
                <div>
                  <strong>候选项</strong>
                  <p>{joinText(record.collected_info_summary?.options_mentioned)}</p>
                </div>
                <div>
                  <strong>上下文字段</strong>
                  <p>{joinText(Object.keys(record.collected_info_summary?.decision_context || {}))}</p>
                </div>
                <div>
                  <strong>限制条件</strong>
                  <p>{joinText(Object.keys(record.collected_info_summary?.user_constraints || {}))}</p>
                </div>
              </div>
            </GlassCard>
          ) : null}

          {isStreaming && liveThinking ? (
            <GlassCard title="流式推演轨迹" subtitle="WebSocket 增量输出">
              <pre className="thinking-preview">{liveThinking}</pre>
            </GlassCard>
          ) : null}

          {error ? <div className="form-error">{error}</div> : null}
        </div>
      )}
    </AppShell>
  );
}
