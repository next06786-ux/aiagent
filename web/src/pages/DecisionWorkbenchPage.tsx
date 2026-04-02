import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';
import { MetricCard } from '../components/common/MetricCard';
import { StatusPill } from '../components/common/StatusPill';
import { AppShell } from '../components/shell/AppShell';
import { useAuth } from '../hooks/useAuth';
import {
  continueDecisionCollection,
  generateDecisionOptions,
  getDecisionHistory,
  getLoraProgress,
  getLoraStatus,
  startDecisionCollection,
  triggerLoraTraining,
} from '../services/decision';
import type {
  CollectedInfo,
  DecisionHistoryRecord,
  DecisionMessage,
  LoraStatusInfo,
  OptionInput,
} from '../types/api';

type WorkbenchPhase = 'idle' | 'collecting' | 'ask_options' | 'ready';

function parseHints(text: string) {
  return text
    .split(/[\n,，；;]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinText(values?: string[]) {
  return values && values.length > 0 ? values.join(' / ') : '暂无';
}

function hasCollectedInfo(value: CollectedInfo | null) {
  if (!value) {
    return false;
  }

  return (
    Object.keys(value.decision_context || {}).length > 0 ||
    Object.keys(value.user_constraints || {}).length > 0 ||
    Object.keys(value.priorities || {}).length > 0 ||
    (value.concerns || []).length > 0 ||
    (value.options_mentioned || []).length > 0
  );
}

function formatDateTime(value: string) {
  if (!value) {
    return '未知时间';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(
    2,
    '0',
  )}-${String(date.getDate()).padStart(2, '0')} ${String(
    date.getHours(),
  ).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

function phaseTitle(phase: WorkbenchPhase) {
  if (phase === 'idle') return '准备开始';
  if (phase === 'collecting') return '信息采集中';
  if (phase === 'ask_options') return '确认选项方向';
  return '可以开始推演';
}

export function DecisionWorkbenchPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [phase, setPhase] = useState<WorkbenchPhase>('idle');
  const [initialQuestion, setInitialQuestion] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState<DecisionMessage[]>([]);
  const [reply, setReply] = useState('');
  const [optionHints, setOptionHints] = useState('');
  const [generatedOptions, setGeneratedOptions] = useState<OptionInput[]>([]);
  const [collectedInfo, setCollectedInfo] = useState<CollectedInfo | null>(null);
  const [history, setHistory] = useState<DecisionHistoryRecord[]>([]);
  const [loraStatus, setLoraStatus] = useState<LoraStatusInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [trainingStage, setTrainingStage] = useState('');
  const [isTraining, setIsTraining] = useState(false);
  const trainingTimerRef = useRef<number | null>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const readyOptionCount = generatedOptions.filter((item) => item.title.trim()).length;

  useEffect(() => {
    if (!user?.user_id) {
      return;
    }

    Promise.allSettled([
      getDecisionHistory(user.user_id),
      getLoraStatus(user.user_id),
    ]).then((results) => {
      const [historyResult, loraResult] = results;
      if (historyResult.status === 'fulfilled') {
        setHistory(historyResult.value);
      }
      if (loraResult.status === 'fulfilled') {
        setLoraStatus(loraResult.value);
      }
    });
  }, [user]);

  useEffect(() => {
    return () => {
      if (trainingTimerRef.current) {
        window.clearInterval(trainingTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!transcriptRef.current) {
      return;
    }

    transcriptRef.current.scrollTo({
      top: transcriptRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages]);

  async function handleStartCollection() {
    if (!user?.user_id || !initialQuestion.trim()) {
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      const result = await startDecisionCollection({
        user_id: user.user_id,
        initial_question: initialQuestion.trim(),
      });
      setSessionId(result.session_id);
      setMessages([
        {
          role: 'system',
          content: result.message,
          timestamp: new Date().toISOString(),
        },
      ]);
      setGeneratedOptions([]);
      setCollectedInfo(null);
      setOptionHints('');
      setPhase('collecting');
    } catch (startError) {
      setError(startError instanceof Error ? startError.message : '启动失败');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCollectionReply() {
    if (!reply.trim() || !sessionId || isLoading) {
      return;
    }

    const userMessage = reply.trim();
    setReply('');
    setError('');
    setIsLoading(true);
    setMessages((current) => [
      ...current,
      {
        role: 'user',
        content: userMessage,
        timestamp: new Date().toISOString(),
      },
    ]);

    try {
      const result = await continueDecisionCollection({
        session_id: sessionId,
        user_response: userMessage,
      });

      if (result.is_complete) {
        setCollectedInfo(result.collected_info || null);
        setMessages((current) => [
          ...current,
          {
            role: 'assistant',
            content: result.summary
              ? `信息采集完成。\n\n${result.summary}`
              : '信息采集完成，请确认选项方向。',
            timestamp: new Date().toISOString(),
          },
        ]);
        setPhase('ask_options');
      } else if (result.ai_question) {
        setMessages((current) => [
          ...current,
          {
            role: 'assistant',
            content: result.ai_question || '请继续补充。',
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (replyError) {
      setError(replyError instanceof Error ? replyError.message : '继续采集失败');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleGenerateOptions() {
    if (!sessionId) {
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      const aiOptions = await generateDecisionOptions({
        session_id: sessionId,
        user_options: parseHints(optionHints),
      });
      if (aiOptions.length === 0) {
        setGeneratedOptions([]);
        setError('当前没有生成出可用选项，请补充更多上下文或手动输入选项。');
        return;
      }
      setGeneratedOptions(aiOptions);
      setPhase('ready');
    } catch (generateError) {
      setError(generateError instanceof Error ? generateError.message : '生成选项失败');
    } finally {
      setIsLoading(false);
    }
  }

  function updateOption(index: number, key: keyof OptionInput, value: string) {
    setGeneratedOptions((current) =>
      current.map((item, itemIndex) =>
        itemIndex === index ? { ...item, [key]: value } : item,
      ),
    );
  }

  function addOption() {
    setGeneratedOptions((current) =>
      current.length >= 5
        ? current
        : [...current, { title: `备选项 ${current.length + 1}`, description: '' }],
    );
  }

  function removeOption(index: number) {
    setGeneratedOptions((current) =>
      current.length <= 2 ? current : current.filter((_, itemIndex) => itemIndex !== index),
    );
  }

  function launchSimulation() {
    const options = generatedOptions
      .map((item) => ({
        title: item.title.trim(),
        description: item.description.trim(),
      }))
      .filter((item) => item.title);

    if (!user?.user_id || !sessionId || options.length < 2) {
      setError('至少保留 2 个选项后才能开始推演。');
      return;
    }

    navigate('/decision/simulation', {
      state: {
        mode: 'stream',
        sessionId,
        question: initialQuestion,
        userId: user.user_id,
        options,
        collectedInfo,
      },
    });
  }

  async function handleStartTraining() {
    if (!user?.user_id || isTraining) {
      return;
    }

    setIsTraining(true);
    setTrainingProgress(5);
    setTrainingStage('已触发训练任务，正在轮询进度...');
    setError('');

    try {
      await triggerLoraTraining(user.user_id);
      trainingTimerRef.current = window.setInterval(() => {
        void getLoraProgress(user.user_id)
          .then((progress) => {
            setTrainingProgress(Number(progress.progress || 0));
            setTrainingStage(progress.stage || '');

            if (!progress.is_training && Number(progress.progress || 0) >= 100) {
              if (trainingTimerRef.current) {
                window.clearInterval(trainingTimerRef.current);
                trainingTimerRef.current = null;
              }
              setIsTraining(false);
              setTrainingStage('训练完成');
              void getLoraStatus(user.user_id).then(setLoraStatus).catch(() => undefined);
            }

            if (progress.error) {
              if (trainingTimerRef.current) {
                window.clearInterval(trainingTimerRef.current);
                trainingTimerRef.current = null;
              }
              setIsTraining(false);
              setError(progress.error);
            }
          })
          .catch(() => {
            if (trainingTimerRef.current) {
              window.clearInterval(trainingTimerRef.current);
              trainingTimerRef.current = null;
            }
            setIsTraining(false);
            setError('轮询个性模型训练进度失败');
          });
      }, 2500);
    } catch (trainingError) {
      setIsTraining(false);
      setError(trainingError instanceof Error ? trainingError.message : '个性模型训练启动失败');
    }
  }

  return (
    <AppShell
      title="决策副本"
      subtitle="以 Harmony 端增强流程为蓝本，把采集、选项生成、储备模型状态和推演入口组织成一个完整工作台。"
      actions={
        <>
          <StatusPill tone={readyOptionCount >= 2 ? 'success' : 'neutral'}>
            {readyOptionCount >= 2 ? `已准备 ${readyOptionCount} 个选项` : '等待至少 2 个选项'}
          </StatusPill>
          <button
            className="button button-primary"
            onClick={launchSimulation}
            disabled={phase !== 'ready' || readyOptionCount < 2}
          >
            开始推演
          </button>
        </>
      }
    >
      <div className="stack-layout">
        <section className="hero-card decision-hero-card">
          <div className="hero-copy">
            <p className="eyebrow">Decision Flow</p>
            <h2>先把问题说清，再让系统生成真正可推演的未来分支。</h2>
            <p>
              这里不是一次性表单，而是 Harmony 风格的渐进采集流程。系统会先帮你整理约束、
              顾虑和优先级，再生成适合推演的候选路径。
            </p>
            <div className="hero-actions">
              <StatusPill
                tone={
                  phase === 'idle'
                    ? 'neutral'
                    : phase === 'collecting'
                      ? 'primary'
                      : phase === 'ask_options'
                        ? 'warning'
                        : 'success'
                }
              >
                {phaseTitle(phase)}
              </StatusPill>
              {sessionId ? <span className="stream-status">session: {sessionId}</span> : null}
            </div>
          </div>

          <div className="hero-side">
            <GlassCard title="快速引导" subtitle="先用自然语言描述，再逐步收束">
              <div className="status-stack">
                <div className="status-row">
                  <span>1. 问题输入</span>
                  <StatusPill tone={phase === 'idle' ? 'primary' : 'success'}>问题定义</StatusPill>
                </div>
                <div className="status-row">
                  <span>2. 约束采集</span>
                  <StatusPill tone={phase === 'collecting' ? 'primary' : phase === 'idle' ? 'neutral' : 'success'}>
                    信息收集
                  </StatusPill>
                </div>
                <div className="status-row">
                  <span>3. 选项确认</span>
                  <StatusPill tone={phase === 'ask_options' ? 'warning' : phase === 'ready' ? 'success' : 'neutral'}>
                    候选路径
                  </StatusPill>
                </div>
                <div className="status-row">
                  <span>4. 流式推演</span>
                  <StatusPill tone={phase === 'ready' ? 'success' : 'neutral'}>准备完成</StatusPill>
                </div>
              </div>
            </GlassCard>
          </div>
        </section>

        <GlassCard title="起始问题" subtitle="可以是一段自由描述，不要求一开始就结构化。">
          <div className="hero-input-strip">
            <textarea
              className="textarea"
              value={initialQuestion}
              onChange={(event) => setInitialQuestion(event.target.value)}
              placeholder="例如：我现在在两个 offer 之间犹豫，怎么选更适合我未来 12 个月的发展？"
              rows={4}
            />
            <div className="composer-actions">
              <button
                className="button button-primary"
                onClick={() => void handleStartCollection()}
                disabled={isLoading || !initialQuestion.trim()}
              >
                {isLoading && phase === 'idle' ? '启动中...' : '开始信息采集'}
              </button>
            </div>
          </div>
        </GlassCard>

        <section className="two-column-grid decision-workbench-grid">
          <GlassCard
            title="采集对话"
            subtitle="对应 Harmony 的 EnhancedDecisionFlow 前半段，通过多轮问答收束问题边界。"
          >
            <div className="decision-transcript" ref={transcriptRef}>
              {messages.length === 0 ? (
                <div className="empty-state-block">
                  <strong>尚未开始采集</strong>
                  <p>启动后，AI 会先帮你梳理上下文、限制条件和你真正重视的结果。</p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <article
                    key={`${message.timestamp}_${index}`}
                    className={`decision-msg decision-msg-${message.role}`}
                  >
                    <strong>
                      {message.role === 'user'
                        ? '你'
                        : message.role === 'assistant'
                          ? 'AI'
                          : '系统'}
                    </strong>
                    <p>{message.content}</p>
                  </article>
                ))
              )}
            </div>

            {phase === 'collecting' ? (
              <div className="chat-composer">
                <textarea
                  className="textarea"
                  value={reply}
                  onChange={(event) => setReply(event.target.value)}
                  placeholder="继续补充你的真实情况、顾虑、限制条件和你在意的东西..."
                  rows={4}
                />
                <div className="composer-actions">
                  <button
                    className="button button-primary"
                    onClick={() => void handleCollectionReply()}
                    disabled={isLoading || !reply.trim()}
                  >
                    {isLoading ? '提交中...' : '继续采集'}
                  </button>
                </div>
              </div>
            ) : null}

            {(phase === 'ask_options' || phase === 'ready') ? (
              <div className="chat-composer">
                <textarea
                  className="textarea"
                  value={optionHints}
                  onChange={(event) => setOptionHints(event.target.value)}
                  placeholder="如果你已有明确选项，就每行写一个；如果没有，也可以直接点“AI 生成选项”。"
                  rows={4}
                />
                <div className="composer-actions">
                  <button
                    className="button button-secondary"
                    onClick={() => void handleGenerateOptions()}
                    disabled={isLoading}
                  >
                    {isLoading ? '生成中...' : 'AI 生成选项'}
                  </button>
                </div>
              </div>
            ) : null}

            {error ? <div className="form-error">{error}</div> : null}
          </GlassCard>

          <div className="stack-layout">
            <GlassCard title="个性模型储备" subtitle="当前推演默认走云端/API，这里保留训练与版本管理能力">
              <div className="metrics-grid compact-grid">
                <MetricCard
                  label="储备模型已加载"
                  value={loraStatus?.is_loaded ? '是' : '否'}
                  helper="当前主链未默认接入"
                  tone="secondary"
                />
                <MetricCard
                  label="训练样本"
                  value={String(loraStatus?.training_data_size || 0)}
                  helper="用于后续个性化训练"
                  tone="accent"
                />
                <MetricCard
                  label="最近训练"
                  value={
                    loraStatus?.last_train_time ? formatDateTime(loraStatus.last_train_time) : '--'
                  }
                  helper="后台记录时间"
                  tone="primary"
                />
              </div>
              <div className="composer-actions">
                <button
                  className="button button-ghost"
                  onClick={() => void handleStartTraining()}
                  disabled={isTraining}
                >
                  {isTraining ? '训练中...' : '训练储备模型'}
                </button>
              </div>
              {isTraining ? (
                <div className="progress-panel">
                  <div className="progress-bar">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${Math.max(4, trainingProgress)}%` }}
                    />
                  </div>
                  <span>{trainingStage || '训练进行中...'}</span>
                </div>
              ) : null}
            </GlassCard>

            <GlassCard title="采集摘要" subtitle="可验证报告的输入基础">
              {hasCollectedInfo(collectedInfo) ? (
                <div className="summary-groups">
                  <div>
                    <strong>顾虑</strong>
                    <p>{joinText(collectedInfo?.concerns)}</p>
                  </div>
                  <div>
                    <strong>优先级</strong>
                    <p>{joinText(Object.keys(collectedInfo?.priorities || {}))}</p>
                  </div>
                  <div>
                    <strong>已提及选项</strong>
                    <p>{joinText(collectedInfo?.options_mentioned)}</p>
                  </div>
                  <div>
                    <strong>上下文维度</strong>
                    <p>{joinText(Object.keys(collectedInfo?.decision_context || {}))}</p>
                  </div>
                  <div>
                    <strong>限制条件</strong>
                    <p>{joinText(Object.keys(collectedInfo?.user_constraints || {}))}</p>
                  </div>
                </div>
              ) : (
                <p className="empty-copy">采集完成后，这里会显示约束、优先级和已提及选项。</p>
              )}
            </GlassCard>

            <GlassCard
              title="待推演选项"
              subtitle={
                readyOptionCount > 0
                  ? `当前可推演 ${readyOptionCount} 个选项，可继续手动微调`
                  : 'AI 生成后可继续手动微调'
              }
            >
              {generatedOptions.length === 0 ? (
                <div className="empty-state-block">
                  <strong>尚未生成选项</strong>
                  <p>完成采集后可让 AI 自动拆出候选路径，也可以手动补充。</p>
                </div>
              ) : (
                <div className="option-editor-list">
                  {generatedOptions.map((option, index) => (
                    <article key={`${option.title}_${index}`} className="option-editor-card">
                      <span className="metric-label">选项 {index + 1}</span>
                      <input
                        className="input"
                        value={option.title}
                        onChange={(event) => updateOption(index, 'title', event.target.value)}
                      />
                      <textarea
                        className="textarea"
                        value={option.description}
                        onChange={(event) =>
                          updateOption(index, 'description', event.target.value)
                        }
                        rows={3}
                      />
                      <button className="button button-ghost" onClick={() => removeOption(index)}>
                        删除
                      </button>
                    </article>
                  ))}
                  <button className="button button-secondary" onClick={addOption}>
                    添加一个选项
                  </button>
                </div>
              )}
            </GlassCard>

            <GlassCard title="最近推演" subtitle="快速回到历史记录">
              {history.length === 0 ? (
                <p className="empty-copy">还没有历史推演。</p>
              ) : (
                <div className="mini-history-list">
                  {history.slice(0, 4).map((record) => (
                    <button
                      key={record.session_id}
                      className="mini-history-item"
                      onClick={() =>
                        navigate(
                          `/decision/simulation?simulationId=${encodeURIComponent(
                            record.session_id,
                          )}`,
                          {
                            state: {
                              mode: 'history',
                              simulationId: record.session_id,
                              question: record.question,
                              userId: user?.user_id || '',
                            },
                          },
                        )
                      }
                    >
                      <strong>{record.question}</strong>
                      <span>{formatDateTime(record.created_at)}</span>
                    </button>
                  ))}
                </div>
              )}
            </GlassCard>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
